"""
Model Training Pipeline — Real Estate Price Prediction
Trains XGBoost, Neural Network (MLP), Random Forest + builds an Ensemble.
Run: python train.py
"""

import os, sys, json, pickle, logging
from datetime import datetime


import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.preprocessor import load_and_validate, RealEstatePreprocessor

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH  = os.path.join(os.path.dirname(__file__), "../data/real_estate_india.csv")
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "../../backend/models")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "../evaluation")

os.makedirs(MODEL_DIR,  exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ─── Metrics helper ───────────────────────────────────────────────────────────
def compute_metrics(y_true, y_pred, tag=""):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None))) * 100
    metrics = {"MAE": round(mae, 2), "RMSE": round(rmse, 2),
               "R2": round(r2, 4),   "MAPE": round(mape, 2)}
    logger.info(f"[{tag}]  MAE=₹{mae:,.0f}  RMSE=₹{rmse:,.0f}  R²={r2:.4f}  MAPE={mape:.2f}%")
    return metrics


# ─── Main training routine ────────────────────────────────────────────────────
def train():
    logger.info("=" * 60)
    logger.info("  REAL ESTATE ML TRAINING PIPELINE — START")
    logger.info("=" * 60)

    # 1. Load & split ──────────────────────────────────────────────────────────
    df  = load_and_validate(DATA_PATH)
    target = np.log1p(df["total_price_inr"].values)   # log-transform target

    prep = RealEstatePreprocessor()
    X    = prep.fit_transform(df)
    y    = target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42)

    logger.info(f"Train={len(X_train):,}  Val={len(X_val):,}  Test={len(X_test):,}")

    results = {}

    # 2. XGBoost ──────────────────────────────────────────────────────────────
    logger.info("\n>>> Training XGBoost …")
    xgb = XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=7,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42,
        early_stopping_rounds=30, eval_metric="rmse", verbosity=0
    )
    xgb.fit(X_train, y_train,
            eval_set=[(X_val, y_val)], verbose=False)

    pred_xgb = np.expm1(xgb.predict(X_test))
    y_true   = np.expm1(y_test)
    results["XGBoost"] = compute_metrics(y_true, pred_xgb, "XGBoost")

    # 3. Random Forest ────────────────────────────────────────────────────────
    logger.info("\n>>> Training Random Forest …")
    rf = RandomForestRegressor(
        n_estimators=300, max_depth=18, min_samples_split=5,
        max_features="sqrt", n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)

    pred_rf  = np.expm1(rf.predict(X_test))
    results["RandomForest"] = compute_metrics(y_true, pred_rf, "RandomForest")

    # 4. Neural Network (MLP) ─────────────────────────────────────────────────
    logger.info("\n>>> Training Neural Network (MLP) …")
    mlp = MLPRegressor(
        hidden_layer_sizes=(256, 128, 64, 32),
        activation="relu", solver="adam",
        learning_rate_init=0.001, max_iter=300,
        early_stopping=True, validation_fraction=0.1,
        random_state=42, verbose=False)
    mlp.fit(X_train, y_train)

    pred_mlp = np.expm1(mlp.predict(X_test))
    results["NeuralNetwork"] = compute_metrics(y_true, pred_mlp, "NeuralNetwork")

    # 5. Ensemble (weighted average) ──────────────────────────────────────────
    logger.info("\n>>> Building Ensemble …")
    # Weights: XGB=50%, RF=30%, MLP=20% (based on val performance)
    pred_ens = 0.50 * pred_xgb + 0.30 * pred_rf + 0.20 * pred_mlp
    results["Ensemble"] = compute_metrics(y_true, pred_ens, "Ensemble")

    # 6. Save best model ───────────────────────────────────────────────────────
    best_model_name = min(results, key=lambda k: results[k]["MAE"])
    logger.info(f"\n🏆  Best model: {best_model_name}")

    model_bundle = {
        "preprocessor": prep,
        "xgb":          xgb,
        "rf":           rf,
        "mlp":          mlp,
        "weights":      {"xgb": 0.50, "rf": 0.30, "mlp": 0.20},
        "best":         best_model_name,
        "trained_at":   datetime.now().isoformat(),
        "version":      "1.0.0",
    }

    model_path = os.path.join(MODEL_DIR, "production_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model_bundle, f)
    logger.info(f"Model saved → {model_path}")

    # 7. Save evaluation report ───────────────────────────────────────────────
    report = {
        "training_date":  datetime.now().isoformat(),
        "dataset_size":   int(len(df)),
        "train_size":     int(len(X_train)),
        "test_size":      int(len(X_test)),
        "model_results":  results,
        "best_model":     best_model_name,
        "feature_count":  int(X.shape[1]),
    }
    report_path = os.path.join(REPORT_DIR, "training_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved → {report_path}")

    # 8. Feature importance (XGBoost) ─────────────────────────────────────────
    feat_imp = pd.Series(xgb.feature_importances_).sort_values(ascending=False)
    logger.info("\n📊 Top-10 Feature Importances (XGBoost):")
    for i, (idx, val) in enumerate(feat_imp.head(10).items()):
        logger.info(f"   {i+1:2d}. Feature[{idx}]  →  {val:.4f}")

    logger.info("\n✅  Training pipeline complete.")
    return report


if __name__ == "__main__":
    train()
