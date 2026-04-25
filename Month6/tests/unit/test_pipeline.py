"""
Comprehensive Test Suite — Real Estate Price Prediction
Covers: unit tests, integration tests, performance tests
Run: python -m pytest tests/ -v --tb=short
"""

import os, sys, json, time, pickle, pytest
import numpy as np
import pandas as pd

BASE = os.environ.get("PROJECT_ROOT", os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(BASE, "ml-pipeline"))

# ─── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def sample_df():
    path = os.path.join(BASE, "ml-pipeline", "data", "real_estate_india.csv")
    return pd.read_csv(path)

@pytest.fixture(scope="module")
def model_bundle():
    path = os.path.join(BASE, "backend", "models", "production_model.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)

@pytest.fixture(scope="module")
def preprocessor(model_bundle):
    return model_bundle["preprocessor"]

@pytest.fixture
def sample_property():
    return {
        "area_sqft": 1200.0, "bedrooms": 3, "bathrooms": 2, "balconies": 1,
        "floor": 5, "total_floors": 12, "age_years": 3,
        "city": "Hyderabad", "locality": "Gachibowli",
        "property_type": "Apartment", "facing": "East",
        "furnishing_status": "Semi-Furnished", "parking_spaces": 1,
        "amenities_score": 0.6, "near_metro": 1, "near_school": 1,
        "near_hospital": 0, "transaction_type": "Sale",
        "possession_status": "Ready to Move",
    }


# ══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — Data
# ══════════════════════════════════════════════════════════════════════════════
class TestDataset:
    def test_dataset_exists(self):
        path = os.path.join(BASE, "ml-pipeline", "data", "real_estate_india.csv")
        assert os.path.exists(path), "Dataset file missing"

    def test_dataset_shape(self, sample_df):
        assert len(sample_df) >= 1000, f"Expected ≥1000 rows, got {len(sample_df)}"
        assert len(sample_df.columns) >= 20

    def test_required_columns(self, sample_df):
        required = ["area_sqft", "bedrooms", "bathrooms", "age_years",
                    "city", "locality", "property_type", "total_price_inr"]
        for col in required:
            assert col in sample_df.columns, f"Missing column: {col}"

    def test_no_negative_prices(self, sample_df):
        assert (sample_df["total_price_inr"] > 0).all()

    def test_no_negative_areas(self, sample_df):
        assert (sample_df["area_sqft"] > 0).all()

    def test_city_distribution(self, sample_df):
        cities = sample_df["city"].unique()
        assert len(cities) >= 3, "Expected at least 3 cities"

    def test_price_range_sensible(self, sample_df):
        assert sample_df["total_price_inr"].min() >= 500_000,   "Min price too low"
        assert sample_df["total_price_inr"].max() <= 5_00_00_00_000, "Max price unrealistic"

    def test_bedroom_range(self, sample_df):
        assert sample_df["bedrooms"].between(1, 10).all()

    def test_no_all_nulls(self, sample_df):
        null_cols = sample_df.columns[sample_df.isnull().all()].tolist()
        assert not null_cols, f"Fully-null columns: {null_cols}"


# ══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — Preprocessor
# ══════════════════════════════════════════════════════════════════════════════
class TestPreprocessor:
    def test_fit_transform_shape(self, sample_df, preprocessor):
        X = preprocessor.transform(sample_df)
        assert X.shape[0] == len(sample_df)
        assert X.shape[1] > 5

    def test_no_nan_in_output(self, sample_df, preprocessor):
        X = preprocessor.transform(sample_df)
        assert not np.isnan(X).any(), "NaN values found in transformed output"

    def test_no_inf_in_output(self, sample_df, preprocessor):
        X = preprocessor.transform(sample_df)
        assert not np.isinf(X).any(), "Inf values found in transformed output"

    def test_single_row_transform(self, preprocessor, sample_property):
        df = pd.DataFrame([sample_property])
        X  = preprocessor.transform(df)
        assert X.shape[0] == 1

    def test_feature_engineering_columns(self, sample_df, preprocessor):
        df = sample_df.copy()
        df2 = preprocessor._engineer_features(df)
        for col in ["price_per_bedroom", "bath_bed_ratio", "floor_ratio",
                    "connectivity_score", "is_new_property"]:
            assert col in df2.columns, f"Feature '{col}' not engineered"


# ══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — Model
# ══════════════════════════════════════════════════════════════════════════════
class TestModel:
    def test_model_file_exists(self):
        path = os.path.join(BASE, "backend", "models", "production_model.pkl")
        assert os.path.exists(path)

    def test_model_bundle_keys(self, model_bundle):
        for key in ["preprocessor", "xgb", "rf", "mlp", "weights", "version", "trained_at"]:
            assert key in model_bundle, f"Missing key: {key}"

    def test_xgb_prediction_positive(self, model_bundle, sample_property, preprocessor):
        df  = pd.DataFrame([sample_property])
        X   = preprocessor.transform(df)
        raw = model_bundle["xgb"].predict(X)[0]
        price = np.expm1(raw)
        assert price > 0, "Predicted price must be positive"

    def test_prediction_in_reasonable_range(self, model_bundle, sample_property, preprocessor):
        df    = pd.DataFrame([sample_property])
        X     = preprocessor.transform(df)
        price = float(np.expm1(model_bundle["xgb"].predict(X)[0]))
        # 1200 sqft Apartment in Gachibowli → expect 50L–5Cr
        assert 5_000_000 <= price <= 500_000_000, f"Price out of range: ₹{price:,.0f}"

    def test_larger_area_costs_more(self, model_bundle, sample_property, preprocessor):
        small = dict(sample_property, area_sqft=800)
        large = dict(sample_property, area_sqft=3000)
        def pred(p):
            return float(np.expm1(model_bundle["xgb"].predict(preprocessor.transform(pd.DataFrame([p])))[0]))
        assert pred(large) > pred(small), "Larger area should predict higher price"

    def test_premium_location_higher_price(self, model_bundle, sample_property, preprocessor):
        base_prop = dict(sample_property, locality="Uppal")
        prem_prop = dict(sample_property, locality="Gachibowli")
        def pred(p):
            return float(np.expm1(model_bundle["xgb"].predict(preprocessor.transform(pd.DataFrame([p])))[0]))
        assert pred(prem_prop) >= pred(base_prop) * 0.95, "Premium locality should not be cheaper"

    def test_older_property_cheaper(self, model_bundle, sample_property, preprocessor):
        new_p = dict(sample_property, age_years=0)
        old_p = dict(sample_property, age_years=20)
        def pred(p):
            return float(np.expm1(model_bundle["xgb"].predict(preprocessor.transform(pd.DataFrame([p])))[0]))
        assert pred(new_p) > pred(old_p), "Newer property should predict higher price"

    def test_model_version_present(self, model_bundle):
        assert model_bundle.get("version"), "Model version must be set"


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestPerformance:
    def test_single_prediction_latency(self, model_bundle, sample_property, preprocessor):
        df  = pd.DataFrame([sample_property])
        X   = preprocessor.transform(df)
        t0  = time.perf_counter()
        model_bundle["xgb"].predict(X)
        ms  = (time.perf_counter() - t0) * 1000
        assert ms < 200, f"Prediction too slow: {ms:.1f}ms (threshold 200ms)"

    def test_batch_prediction_throughput(self, model_bundle, sample_df, preprocessor):
        batch = sample_df.sample(100, random_state=1)
        X     = preprocessor.transform(batch)
        t0    = time.perf_counter()
        model_bundle["xgb"].predict(X)
        secs  = time.perf_counter() - t0
        assert secs < 2.0, f"100-row batch took {secs:.2f}s (threshold 2s)"

    def test_preprocessor_transform_speed(self, sample_df, preprocessor):
        t0   = time.perf_counter()
        preprocessor.transform(sample_df)
        ms   = (time.perf_counter() - t0) * 1000
        assert ms < 3000, f"Transform too slow: {ms:.0f}ms"

    def test_1000_predictions_under_5s(self, model_bundle, sample_df, preprocessor):
        batch = sample_df.sample(min(1000, len(sample_df)), random_state=42)
        X     = preprocessor.transform(batch)
        t0    = time.perf_counter()
        model_bundle["xgb"].predict(X)
        secs  = time.perf_counter() - t0
        assert secs < 5.0, f"1000 predictions took {secs:.2f}s"


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Training report
# ══════════════════════════════════════════════════════════════════════════════
class TestTrainingReport:
    def test_report_exists(self):
        path = os.path.join(BASE, "ml-pipeline", "evaluation", "training_report.json")
        assert os.path.exists(path), "Training report missing — run train.py first"

    def test_report_structure(self):
        path = os.path.join(BASE, "ml-pipeline", "evaluation", "training_report.json")
        with open(path) as f:
            r = json.load(f)
        for key in ["training_date", "dataset_size", "model_results", "best_model"]:
            assert key in r, f"Missing key in report: {key}"

    def test_xgb_r2_above_threshold(self):
        path = os.path.join(BASE, "ml-pipeline", "evaluation", "training_report.json")
        with open(path) as f:
            r = json.load(f)
        r2 = r["model_results"]["XGBoost"]["R2"]
        assert r2 >= 0.85, f"XGBoost R² too low: {r2}"

    def test_best_model_is_xgb_or_ensemble(self):
        path = os.path.join(BASE, "ml-pipeline", "evaluation", "training_report.json")
        with open(path) as f:
            r = json.load(f)
        assert r["best_model"] in ["XGBoost", "Ensemble"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
