# ============================================================
#  src/etl_pipeline.py
#  Orchestrates the three ETL steps:
#    Extract  → pull data from the API
#    Transform → validate and clean the data
#    Load     → write clean data to the database
# ============================================================

import time
from datetime import datetime

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.config     import CITIES, get_logger
from src.api_client import fetch_multiple_cities
from src.validators import validate_batch, check_alerts
from src.database   import (setup_database, upsert_city,
                             insert_weather_record, insert_alert, log_run)

logger = get_logger("etl_pipeline")


# ===========================================================
# STEP 1 — EXTRACT
# ===========================================================

def extract(city_list: list = None) -> list:
    """Pull raw weather data from the API for each city."""
    targets = city_list or CITIES
    logger.info(f"[EXTRACT] Fetching {len(targets)} cities: {targets}")
    raw = fetch_multiple_cities(targets)
    logger.info(f"[EXTRACT] Got {len(raw)} responses")
    return raw


# ===========================================================
# STEP 2 — TRANSFORM
# ===========================================================

def transform(raw_data: list) -> tuple:
    """Validate and clean raw API records."""
    logger.info(f"[TRANSFORM] Validating {len(raw_data)} records...")
    valid, invalid = validate_batch(raw_data)

    for item in invalid:
        city = item["data"].get("city", "?")
        logger.warning(f"[TRANSFORM] Rejected {city}: {item['errors']}")

    logger.info(
        f"[TRANSFORM] {len(valid)} valid, {len(invalid)} rejected"
    )
    return valid, invalid


# ===========================================================
# STEP 3 — LOAD
# ===========================================================

def load(valid_records: list) -> tuple:
    """Write valid records to the database. Check alert conditions."""
    logger.info(f"[LOAD] Writing {len(valid_records)} records...")

    inserted       = 0
    alerts_fired   = 0

    for rec in valid_records:
        try:
            # 3a — ensure city row exists
            city_id = upsert_city(
                city_name = rec["city"],
                country   = rec.get("country", ""),
                latitude  = rec.get("latitude"),
                longitude = rec.get("longitude"),
                timezone  = rec.get("timezone", ""),
            )

            # 3b — insert weather reading
            insert_weather_record(city_id, rec)
            inserted += 1

            # 3c — evaluate alert rules
            for alert in check_alerts(rec):
                insert_alert(
                    city_id    = city_id,
                    alert_type = alert["alert_type"],
                    severity   = alert["severity"],
                    message    = alert["message"],
                    threshold  = alert["threshold"],
                    actual     = alert["actual"],
                )
                alerts_fired += 1

        except Exception as exc:
            logger.error(f"[LOAD] Failed for {rec.get('city', '?')}: {exc}")

    logger.info(
        f"[LOAD] Done — {inserted} records inserted, "
        f"{alerts_fired} alerts triggered"
    )
    return inserted, alerts_fired


# ===========================================================
# FULL PIPELINE
# ===========================================================

def run_pipeline(city_list: list = None) -> dict:
    """
    Run Extract → Transform → Load.
    Logs the result to pipeline_runs and returns a summary dict.
    """
    start  = time.time()
    cities = city_list or CITIES

    summary = {
        "run_at":    datetime.now().isoformat(),
        "targeted":  len(cities),
        "extracted": 0,
        "valid":     0,
        "invalid":   0,
        "loaded":    0,
        "alerts":    0,
        "success":   False,
        "error":     None,
    }

    logger.info("=" * 55)
    logger.info("  PIPELINE RUN STARTED")
    logger.info("=" * 55)

    try:
        raw              = extract(cities)
        summary["extracted"] = len(raw)

        if not raw:
            raise RuntimeError(
                "No data extracted — check API key and city list"
            )

        valid, invalid   = transform(raw)
        summary["valid"]   = len(valid)
        summary["invalid"] = len(invalid)

        loaded, alerts   = load(valid)
        summary["loaded"]  = loaded
        summary["alerts"]  = alerts
        summary["success"] = True

    except Exception as exc:
        summary["error"] = str(exc)
        logger.error(f"PIPELINE FAILED: {exc}")

    finally:
        duration = round(time.time() - start, 2)
        summary["duration_sec"] = duration

        log_run(
            cities_attempted = summary["targeted"],
            records_inserted = summary.get("loaded", 0),
            alerts_triggered = summary.get("alerts", 0),
            duration_sec     = duration,
            success          = summary["success"],
            error_message    = summary.get("error"),
        )

        status = "SUCCESS ✅" if summary["success"] else "FAILED ❌"
        logger.info(f"  Status    : {status}")
        logger.info(f"  Extracted : {summary['extracted']}")
        logger.info(f"  Loaded    : {summary['loaded']}")
        logger.info(f"  Alerts    : {summary['alerts']}")
        logger.info(f"  Duration  : {duration}s")
        logger.info("=" * 55)

    return summary


# Run directly:  python src/etl_pipeline.py
if __name__ == "__main__":
    setup_database()
    result = run_pipeline()
    print("\nSummary:")
    for k, v in result.items():
        print(f"  {k:<15}: {v}")
