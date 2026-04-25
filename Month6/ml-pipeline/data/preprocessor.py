"""
Data Preprocessing Pipeline — Real Estate Price Prediction
Author: Senior ML Engineer
"""

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder, StandardScaler
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealEstatePreprocessor(BaseEstimator, TransformerMixin):
    """Complete feature engineering + preprocessing for real estate data."""

    CATEGORICAL_COLS = ["city", "locality", "property_type", "facing",
                        "furnishing_status", "transaction_type", "possession_status"]
    NUMERIC_COLS = ["area_sqft", "bedrooms", "bathrooms", "balconies", "floor",
                    "total_floors", "age_years", "parking_spaces", "amenities_score",
                    "near_metro", "near_school", "near_hospital"]

    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names_ = []

    # ── fit ──────────────────────────────────────────────────────────────────
    def fit(self, df: pd.DataFrame, y=None):
        df = self._engineer_features(df.copy())
        for col in self.CATEGORICAL_COLS:
            if col in df.columns:
                le = LabelEncoder()
                le.fit(df[col].astype(str))
                self.label_encoders[col] = le

        all_features = self.NUMERIC_COLS + self.CATEGORICAL_COLS
        self.feature_names_ = [f for f in all_features if f in df.columns]
        X = self._encode(df)
        self.scaler.fit(X)
        return self

    # ── transform ────────────────────────────────────────────────────────────
    def transform(self, df: pd.DataFrame):
        df = self._engineer_features(df.copy())
        X = self._encode(df)
        return self.scaler.transform(X)

    # ── private helpers ───────────────────────────────────────────────────────
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features from raw data."""
        df["price_per_bedroom"]   = df["area_sqft"] / df["bedrooms"].clip(lower=1)
        df["bath_bed_ratio"]      = df["bathrooms"] / df["bedrooms"].clip(lower=1)
        df["floor_ratio"]         = df["floor"] / df["total_floors"].clip(lower=1)
        df["is_new_property"]     = (df["age_years"] <= 2).astype(int)
        df["is_premium_floor"]    = (df["floor"] >= 10).astype(int)
        df["connectivity_score"]  = (df["near_metro"] + df["near_school"] + df["near_hospital"])
        df["is_east_facing"]      = (df["facing"] == "East").astype(int)
        df["is_fully_furnished"]  = (df["furnishing_status"] == "Fully Furnished").astype(int)
        return df

    def _encode(self, df: pd.DataFrame) -> np.ndarray:
        extra = ["price_per_bedroom", "bath_bed_ratio", "floor_ratio",
                 "is_new_property", "is_premium_floor", "connectivity_score",
                 "is_east_facing", "is_fully_furnished"]
        features = self.feature_names_ + extra
        for col in self.CATEGORICAL_COLS:
            if col in df.columns and col in self.label_encoders:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))
        available = [f for f in features if f in df.columns]
        return df[available].fillna(0).values


def load_and_validate(data_path: str) -> pd.DataFrame:
    """Load dataset with validation and logging."""
    logger.info(f"Loading dataset from: {data_path}")
    df = pd.read_csv(data_path)

    required = ["area_sqft", "bedrooms", "bathrooms", "age_years",
                "city", "locality", "property_type", "total_price_inr"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Basic cleaning
    df = df.dropna(subset=required)
    df = df[df["total_price_inr"] > 0]
    df = df[df["area_sqft"] > 0]

    logger.info(f"Dataset loaded: {len(df):,} rows, {len(df.columns)} columns")
    logger.info(f"Price range: ₹{df['total_price_inr'].min():,.0f} — ₹{df['total_price_inr'].max():,.0f}")
    return df


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    df = load_and_validate(os.path.join(base, "real_estate_india.csv"))
    prep = RealEstatePreprocessor()
    X = prep.fit_transform(df)
    print(f"Feature matrix shape: {X.shape}")
