"""
Real Estate Price Prediction API  — v1.0.0
FastAPI Production Backend
"""

from __future__ import annotations
import os, sys, uuid, pickle, logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  [%(name)s]  %(message)s")
logger = logging.getLogger("real_estate_api")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
MODEL_PATH = BASE_DIR / "backend" / "models" / "production_model.pkl"
SYS_PATH   = BASE_DIR / "ml-pipeline"
sys.path.insert(0, str(SYS_PATH))

# ─── App bootstrap ────────────────────────────────────────────────────────────
app = FastAPI(
    title="🏠 Real Estate Price Prediction API",
    description="Production-grade ML API for Indian real estate price prediction.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ─── In-memory stats (replaces Prometheus for simplicity) ─────────────────────
class _Stats:
    total_predictions: int = 0
    errors: int = 0
    latencies: List[float] = []
    start_time: datetime = datetime.now()

STATS = _Stats()

# ─── Load model bundle on startup ─────────────────────────────────────────────
MODEL_BUNDLE: dict = {}

@app.on_event("startup")
async def load_model():
    global MODEL_BUNDLE
    logger.info(f"Loading model from {MODEL_PATH} …")
    if not MODEL_PATH.exists():
        logger.error("Model file not found! Run the training pipeline first.")
        return
    with open(MODEL_PATH, "rb") as f:
        MODEL_BUNDLE = pickle.load(f)
    logger.info(f"Model loaded  (version={MODEL_BUNDLE.get('version','?')}, "
                f"trained={MODEL_BUNDLE.get('trained_at','?')})")


# ─── Pydantic schemas ─────────────────────────────────────────────────────────
CITIES     = ["Hyderabad", "Bangalore", "Mumbai", "Delhi NCR", "Pune"]
PROP_TYPES = ["Apartment", "Villa", "Independent House", "Penthouse", "Studio"]
FURNISHING = ["Unfurnished", "Semi-Furnished", "Fully Furnished"]
FACINGS    = ["East", "West", "North", "South", "North-East", "North-West"]
POSSESSION = ["Ready to Move", "Under Construction", "New Launch"]

class PropertyRequest(BaseModel):
    area_sqft:         float   = Field(..., gt=0, le=50000, example=1200.0)
    bedrooms:          int     = Field(..., ge=1, le=10,    example=3)
    bathrooms:         int     = Field(..., ge=1, le=10,    example=2)
    balconies:         int     = Field(0,  ge=0, le=5,     example=1)
    floor:             int     = Field(0,  ge=0, le=60,    example=5)
    total_floors:      int     = Field(10, ge=1, le=60,    example=12)
    age_years:         int     = Field(..., ge=0, le=50,   example=3)
    city:              str     = Field(..., example="Hyderabad")
    locality:          str     = Field(..., example="Gachibowli")
    property_type:     str     = Field(..., example="Apartment")
    facing:            str     = Field("East", example="East")
    furnishing_status: str     = Field("Unfurnished", example="Semi-Furnished")
    parking_spaces:    int     = Field(1,  ge=0, le=5)
    amenities_score:   float   = Field(0.5, ge=0.0, le=1.0)
    near_metro:        int     = Field(0, ge=0, le=1)
    near_school:       int     = Field(0, ge=0, le=1)
    near_hospital:     int     = Field(0, ge=0, le=1)
    transaction_type:  str     = Field("Sale", example="Sale")
    possession_status: str     = Field("Ready to Move", example="Ready to Move")

    @validator("city")
    def validate_city(cls, v):
        if v not in CITIES:
            raise ValueError(f"city must be one of {CITIES}")
        return v

    @validator("property_type")
    def validate_ptype(cls, v):
        if v not in PROP_TYPES:
            raise ValueError(f"property_type must be one of {PROP_TYPES}")
        return v


class PredictionResponse(BaseModel):
    prediction_id:      str
    timestamp:          str
    predicted_price:    float
    currency:           str = "INR"
    price_in_lakhs:     float
    confidence_interval: dict
    model_version:      str
    metadata:           dict


class BatchRequest(BaseModel):
    properties: List[PropertyRequest]


# ─── Helper: run prediction ───────────────────────────────────────────────────
def _predict_single(req: PropertyRequest) -> PredictionResponse:
    import time
    t0 = time.time()

    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Model not loaded")

    prep = MODEL_BUNDLE["preprocessor"]
    xgb  = MODEL_BUNDLE["xgb"]

    input_df = pd.DataFrame([req.dict()])
    X        = prep.transform(input_df)
    log_pred = xgb.predict(X)[0]
    price    = float(np.expm1(log_pred))
    margin   = price * 0.10        # ±10% confidence

    latency = time.time() - t0
    STATS.total_predictions += 1
    STATS.latencies.append(latency)

    return PredictionResponse(
        prediction_id      = str(uuid.uuid4()),
        timestamp          = datetime.now().isoformat(),
        predicted_price    = round(price, 2),
        price_in_lakhs     = round(price / 100_000, 2),
        confidence_interval= {
            "lower_bound": round(price - margin, 2),
            "upper_bound": round(price + margin, 2),
        },
        model_version      = MODEL_BUNDLE.get("version", "1.0.0"),
        metadata           = {
            "area_sqft":       req.area_sqft,
            "city":            req.city,
            "locality":        req.locality,
            "property_type":   req.property_type,
            "latency_ms":      round(latency * 1000, 2),
        },
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {"message": "🏠 Real Estate Price Prediction API", "status": "running",
            "docs": "/api/docs"}


@app.get("/api/v1/health", tags=["System"])
async def health():
    uptime = (datetime.now() - STATS.start_time).total_seconds()
    avg_latency = (sum(STATS.latencies[-100:]) / max(len(STATS.latencies[-100:]), 1)) * 1000
    return {
        "status":              "healthy",
        "version":             "1.0.0",
        "model_loaded":        bool(MODEL_BUNDLE),
        "uptime_seconds":      round(uptime, 1),
        "total_predictions":   STATS.total_predictions,
        "avg_latency_ms":      round(avg_latency, 2),
        "error_rate":          round(STATS.errors / max(STATS.total_predictions, 1) * 100, 3),
        "timestamp":           datetime.now().isoformat(),
    }


@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict(request: PropertyRequest):
    """Predict price for a single property."""
    try:
        result = _predict_single(request)
        logger.info(f"Prediction  id={result.prediction_id}  "
                    f"price=₹{result.predicted_price:,.0f}  "
                    f"latency={result.metadata['latency_ms']}ms")
        return result
    except HTTPException:
        raise
    except Exception as e:
        STATS.errors += 1
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch", tags=["Predictions"])
async def batch_predict(batch: BatchRequest):
    """Predict prices for multiple properties (max 50)."""
    if len(batch.properties) > 50:
        raise HTTPException(status_code=400, detail="Max 50 properties per batch")
    results = [_predict_single(p).dict() for p in batch.properties]
    return {"count": len(results), "predictions": results,
            "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/metrics", tags=["System"])
async def metrics():
    lats = STATS.latencies[-500:] or [0]
    return {
        "total_predictions": STATS.total_predictions,
        "total_errors":      STATS.errors,
        "error_rate_pct":    round(STATS.errors / max(STATS.total_predictions, 1) * 100, 3),
        "latency_ms": {
            "avg": round(np.mean(lats) * 1000, 2),
            "p50": round(np.percentile(lats, 50) * 1000, 2),
            "p95": round(np.percentile(lats, 95) * 1000, 2),
            "p99": round(np.percentile(lats, 99) * 1000, 2),
        },
    }


@app.get("/api/v1/model-info", tags=["Model"])
async def model_info():
    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "version":     MODEL_BUNDLE.get("version"),
        "trained_at":  MODEL_BUNDLE.get("trained_at"),
        "best_model":  MODEL_BUNDLE.get("best"),
        "models":      list(MODEL_BUNDLE.get("weights", {}).keys()),
        "weights":     MODEL_BUNDLE.get("weights"),
    }


@app.get("/api/v1/options", tags=["Metadata"])
async def get_options():
    """Return valid dropdown options for the UI."""
    from data.preprocessor import load_and_validate
    df  = load_and_validate(str(BASE_DIR / "ml-pipeline/data/real_estate_india.csv"))
    return {
        "cities":            sorted(df["city"].unique().tolist()),
        "localities":        {c: sorted(df[df["city"] == c]["locality"].unique().tolist())
                              for c in df["city"].unique()},
        "property_types":    PROP_TYPES,
        "furnishing_status": FURNISHING,
        "facing":            FACINGS,
        "possession_status": POSSESSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
