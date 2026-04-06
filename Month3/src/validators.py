# ============================================================
#  src/validators.py
#  Checks every reading for quality before it goes into the DB.
#  Also evaluates alert conditions.
# ============================================================

from dataclasses import dataclass, field
from typing import Optional

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from src.config import TEMP_HIGH, TEMP_LOW, HUM_HIGH, WIND_HIGH, get_logger

logger = get_logger("validators")


# ===========================================================
# RESULT OBJECT
# ===========================================================

@dataclass
class ValidationResult:
    is_valid : bool           = True
    errors   : list           = field(default_factory=list)
    warnings : list           = field(default_factory=list)
    cleaned  : Optional[dict] = None

    def fail(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False

    def warn(self, msg: str):
        self.warnings.append(msg)


# ===========================================================
# PHYSICAL BOUNDS  (no weather reading on Earth can break these)
# ===========================================================

BOUNDS = {
    "temperature":  (-90.0, 60.0),
    "feels_like":   (-100.0, 70.0),
    "humidity":     (0.0, 100.0),
    "pressure":     (870.0, 1085.0),
    "wind_speed":   (0.0, 115.0),
    "visibility":   (0.0, 100_000.0),
    "clouds":       (0.0, 100.0),
    "rain_1h":      (0.0, 500.0),
}

REQUIRED = ["city", "timestamp", "temperature", "humidity"]


# ===========================================================
# SINGLE RECORD VALIDATOR
# ===========================================================

def validate_record(data: dict) -> ValidationResult:
    """
    Validate and clean one weather reading.
    Returns ValidationResult with is_valid, errors/warnings,
    and a cleaned copy of data.
    """
    res     = ValidationResult()
    cleaned = dict(data)

    # -- Step 1: required fields -----------------------------
    for field_name in REQUIRED:
        if data.get(field_name) is None:
            res.fail(f"Missing required field: '{field_name}'")

    if not res.is_valid:
        res.cleaned = cleaned
        return res

    # -- Step 2: city name -----------------------------------
    city = str(data.get("city", "")).strip()
    if len(city) < 2:
        res.fail("City name too short")
    cleaned["city"] = city

    # -- Step 3: numeric bounds ------------------------------
    field_map = {
        "temperature": "temperature",
        "feels_like":  "feels_like",
        "humidity":    "humidity",
        "pressure":    "pressure",
        "wind_speed":  "wind_speed",
        "visibility":  "visibility",
        "clouds":      "clouds",
        "rain_1h":     "rain_1h",
    }

    for data_key, bounds_key in field_map.items():
        val = data.get(data_key)
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            res.fail(f"'{data_key}' must be a number, got {val!r}")
            continue

        lo, hi = BOUNDS[bounds_key]
        if not (lo <= val <= hi):
            res.warn(
                f"'{data_key}' = {val} outside realistic range [{lo}, {hi}]"
            )
            # Clamp rather than reject
            cleaned[data_key] = max(lo, min(hi, val))
        else:
            cleaned[data_key] = val

    res.cleaned = cleaned
    return res


# ===========================================================
# BATCH VALIDATOR
# ===========================================================

def validate_batch(records: list) -> tuple:
    """
    Validate a list of readings.
    Returns (valid_list, invalid_list).
    """
    valid, invalid = [], []
    for rec in records:
        res = validate_record(rec)
        if res.is_valid:
            valid.append(res.cleaned)
        else:
            invalid.append({"data": rec, "errors": res.errors})

    logger.info(
        f"Batch validation — passed: {len(valid)}, "
        f"failed: {len(invalid)}"
    )
    return valid, invalid


# ===========================================================
# ALERT CONDITION CHECKER
# ===========================================================

def check_alerts(data: dict) -> list:
    """
    Compare a reading against thresholds.
    Returns a list of alert dicts (empty = no alerts).
    """
    alerts = []
    city   = data.get("city", "Unknown")
    temp   = data.get("temperature")
    hum    = data.get("humidity")
    wind   = data.get("wind_speed")

    if temp is not None:
        if temp >= TEMP_HIGH:
            alerts.append({
                "alert_type": "HIGH_TEMPERATURE",
                "severity":   "CRITICAL",
                "message":    f"High temperature alert: {city} ({temp}°C > {TEMP_HIGH}°C threshold)",
                "threshold":  TEMP_HIGH,
                "actual":     temp,
            })
        elif temp <= TEMP_LOW:
            alerts.append({
                "alert_type": "LOW_TEMPERATURE",
                "severity":   "HIGH",
                "message":    f"Low temperature alert: {city} ({temp}°C < {TEMP_LOW}°C threshold)",
                "threshold":  TEMP_LOW,
                "actual":     temp,
            })

    if hum is not None and hum >= HUM_HIGH:
        alerts.append({
            "alert_type": "HIGH_HUMIDITY",
            "severity":   "MEDIUM",
            "message":    f"High humidity alert: {city} ({hum}% > {HUM_HIGH}% threshold)",
            "threshold":  HUM_HIGH,
            "actual":     hum,
        })

    if wind is not None:
        wind_kmh = wind * 3.6
        if wind_kmh >= WIND_HIGH:
            alerts.append({
                "alert_type": "HIGH_WIND",
                "severity":   "HIGH",
                "message":    f"High wind alert: {city} ({wind_kmh:.1f} km/h > {WIND_HIGH} km/h threshold)",
                "threshold":  WIND_HIGH,
                "actual":     wind_kmh,
            })

    return alerts
