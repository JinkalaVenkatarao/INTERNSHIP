"""
Model Drift Detector — Real Estate Price Prediction
Monitors for statistical drift in predictions vs training distribution.
Can be run as a cron job or triggered post-deployment.

Usage: python drift_detector.py --window 7   # check last 7 days
"""

import os, sys, json, pickle, argparse, logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).parent.parent.parent          # project root
sys.path.insert(0, str(BASE / "ml-pipeline"))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger("drift_detector")


class DriftDetector:
    """
    Detects two types of drift:
    1. Data drift   — feature distribution has shifted
    2. Concept drift — model accuracy has degraded
    """

    THRESHOLDS = {
        "ks_pvalue":       0.05,   # KS test p-value threshold
        "psi":             0.20,   # Population Stability Index
        "mape_threshold":  0.15,   # 15% MAPE = potential concept drift
        "price_std_ratio": 2.0,    # Std ratio (current vs baseline)
    }

    def __init__(self, model_path: str, baseline_data_path: str):
        logger.info("Loading model bundle …")
        with open(model_path, "rb") as f:
            self.bundle = pickle.load(f)
        self.prep     = self.bundle["preprocessor"]
        self.baseline = pd.read_csv(baseline_data_path)
        self.baseline_prices = self.baseline["total_price_inr"].values
        self.results  = {}

    # ── Feature Drift (KS Test) ──────────────────────────────────────────────
    def check_feature_drift(self, current_df: pd.DataFrame) -> dict:
        logger.info("Running KS test for feature drift …")
        numeric_cols = ["area_sqft", "age_years", "bedrooms",
                        "amenities_score", "floor"]
        drift_report = {}
        for col in numeric_cols:
            if col not in current_df.columns:
                continue
            ks_stat, p_val = stats.ks_2samp(
                self.baseline[col].dropna().values,
                current_df[col].dropna().values
            )
            drifted = p_val < self.THRESHOLDS["ks_pvalue"]
            drift_report[col] = {
                "ks_statistic": round(ks_stat, 4),
                "p_value":      round(p_val, 4),
                "drifted":      drifted,
            }
            status = "⚠️  DRIFT" if drifted else "✅ OK"
            logger.info(f"  {col:<22} {status}  (KS={ks_stat:.3f}, p={p_val:.4f})")
        return drift_report

    # ── PSI (Population Stability Index) ─────────────────────────────────────
    def compute_psi(self, baseline_arr, current_arr, n_bins=10) -> float:
        bins = np.percentile(baseline_arr, np.linspace(0, 100, n_bins + 1))
        bins[0]  -= 1e-9
        bins[-1] += 1e-9
        base_pct = np.histogram(baseline_arr, bins=bins)[0] / len(baseline_arr)
        curr_pct = np.histogram(current_arr,  bins=bins)[0] / len(current_arr)
        base_pct = np.clip(base_pct, 1e-6, None)
        curr_pct = np.clip(curr_pct, 1e-6, None)
        return float(np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct)))

    # ── Concept Drift (MAPE on labelled sample) ──────────────────────────────
    def check_concept_drift(self, current_df: pd.DataFrame) -> dict:
        logger.info("Checking concept drift (MAPE on current data) …")
        if "total_price_inr" not in current_df.columns:
            return {"skipped": "No ground-truth labels in current data"}
        X      = self.prep.transform(current_df)
        y_true = current_df["total_price_inr"].values
        y_pred = np.expm1(self.bundle["xgb"].predict(X))
        mape   = np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None)))
        drifted = mape > self.THRESHOLDS["mape_threshold"]
        logger.info(f"  MAPE = {mape*100:.2f}%  {'⚠️  CONCEPT DRIFT' if drifted else '✅ OK'}")
        return {"mape": round(mape, 4), "drifted": drifted}

    # ── Price Distribution Drift ──────────────────────────────────────────────
    def check_price_distribution(self, current_df: pd.DataFrame) -> dict:
        if "total_price_inr" not in current_df.columns:
            return {}
        curr_prices = current_df["total_price_inr"].values
        psi = self.compute_psi(self.baseline_prices, curr_prices)
        logger.info(f"  Price PSI = {psi:.4f}  "
                    f"{'⚠️  SIGNIFICANT' if psi > self.THRESHOLDS['psi'] else '✅ OK'}")
        return {"psi": round(psi, 4), "significant": psi > self.THRESHOLDS["psi"]}

    # ── Full Drift Report ─────────────────────────────────────────────────────
    def run(self, current_df: pd.DataFrame) -> dict:
        logger.info(f"Drift detection on {len(current_df):,} current samples …")
        report = {
            "timestamp":        datetime.now().isoformat(),
            "baseline_n":       len(self.baseline),
            "current_n":        len(current_df),
            "feature_drift":    self.check_feature_drift(current_df),
            "concept_drift":    self.check_concept_drift(current_df),
            "price_psi":        self.check_price_distribution(current_df),
        }

        # Overall decision
        feature_drifted = any(v.get("drifted") for v in report["feature_drift"].values())
        concept_drifted = report["concept_drift"].get("drifted", False)
        price_drifted   = report["price_psi"].get("significant", False)

        report["action_required"] = feature_drifted or concept_drifted or price_drifted
        report["recommendation"]  = (
            "🔄 RETRAIN MODEL RECOMMENDED" if report["action_required"]
            else "✅ Model performance is stable"
        )

        logger.info(f"\n{'='*50}")
        logger.info(f"  {report['recommendation']}")
        logger.info(f"{'='*50}")
        return report


def main():
    parser = argparse.ArgumentParser(description="Real Estate Model Drift Detector")
    parser.add_argument("--window", type=int, default=30,
                        help="Days of recent data to check (default: 30)")
    parser.add_argument("--output", default="drift_report.json",
                        help="Output JSON file path")
    args = parser.parse_args()

    model_path    = str(BASE / "backend" / "models" / "production_model.pkl")
    baseline_path = str(BASE / "ml-pipeline" / "data" / "real_estate_india.csv")

    detector = DriftDetector(model_path, baseline_path)

    # Simulate "recent" data — last N days from dataset
    baseline = pd.read_csv(baseline_path)
    baseline["listed_date"] = pd.to_datetime(baseline["listed_date"])
    cutoff = baseline["listed_date"].max() - timedelta(days=args.window)
    current = baseline[baseline["listed_date"] >= cutoff].copy()

    if len(current) < 10:
        logger.warning(f"Only {len(current)} recent samples — using random 20% sample")
        current = baseline.sample(frac=0.2, random_state=99)

    logger.info(f"Checking drift on {len(current):,} samples from last {args.window} days")
    report = detector.run(current)

    # Convert numpy bools → Python bools for JSON serialisation
    def _convert(obj):
        if isinstance(obj, (np.bool_, np.integer)): return int(obj)
        if isinstance(obj, np.floating):            return float(obj)
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list): return [_convert(v) for v in obj]
        return obj

    out_path = BASE / "ml-pipeline" / "evaluation" / args.output
    with open(out_path, "w") as f:
        json.dump(_convert(report), f, indent=2)
    logger.info(f"Report saved → {out_path}")
    return report


if __name__ == "__main__":
    main()
