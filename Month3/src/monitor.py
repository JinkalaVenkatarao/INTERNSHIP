# ============================================================
#  src/monitor.py
#  Health checks for every component of the pipeline.
#  Tells you immediately if something is broken.
# ============================================================

import os
import shutil
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.config   import DB_PATH, LOGS_DIR, API_KEY, COLLECT_INTERVAL, get_logger
from src.database import (get_db_statistics, get_run_history,
                          get_active_alerts, get_all_cities,
                          get_latest_reading)

logger = get_logger("monitor")

ICON = {"OK": "✅", "WARN": "⚠️ ", "FAIL": "❌"}


# ===========================================================
# INDIVIDUAL CHECKS
# ===========================================================

def _check(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


def check_api_key() -> dict:
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        return _check("API Key", "FAIL",
                      "Not configured — edit config/settings.env")
    masked = API_KEY[:6] + "..." + API_KEY[-4:]
    return _check("API Key", "OK", f"Configured ({masked})")


def check_database() -> dict:
    try:
        if not DB_PATH.exists():
            return _check("Database", "FAIL", "Database file not found")
        size_kb = DB_PATH.stat().st_size / 1024
        stats   = get_db_statistics()
        detail  = (f"{size_kb:.0f} KB | "
                   f"{stats['total_records']:,} records | "
                   f"{stats['total_cities']} cities")
        return _check("Database", "OK", detail)
    except Exception as exc:
        return _check("Database", "FAIL", str(exc))


def check_data_freshness() -> dict:
    try:
        cities = get_all_cities()
        if not cities:
            return _check("Data Freshness", "WARN", "No cities tracked yet")

        threshold = timedelta(minutes=COLLECT_INTERVAL * 2)
        stale     = []
        now       = datetime.utcnow()

        for city in cities:
            rec = get_latest_reading(city["city_id"])
            if not rec:
                stale.append(f"{city['city_name']} (never)")
                continue
            try:
                ts  = rec["timestamp"].replace("Z", "").split("+")[0]
                age = now - datetime.fromisoformat(ts)
                if age > threshold:
                    mins = int(age.total_seconds() // 60)
                    stale.append(f"{city['city_name']} ({mins}m ago)")
            except Exception:
                pass

        if stale:
            return _check("Data Freshness", "WARN",
                          f"Stale: {', '.join(stale)}")
        return _check("Data Freshness", "OK",
                      f"All {len(cities)} cities fresh")
    except Exception as exc:
        return _check("Data Freshness", "FAIL", str(exc))


def check_pipeline_runs() -> dict:
    try:
        history = get_run_history(limit=10)
        if not history:
            return _check("Pipeline Runs", "WARN", "No runs recorded yet")
        total   = len(history)
        success = sum(1 for r in history if r["success"])
        rate    = success / total * 100
        last    = history[0]["run_at"][:16].replace("T", " ")
        detail  = f"{rate:.0f}% success ({success}/{total}) | last: {last}"
        status  = "OK" if rate >= 80 else "WARN" if rate >= 50 else "FAIL"
        return _check("Pipeline Runs", status, detail)
    except Exception as exc:
        return _check("Pipeline Runs", "FAIL", str(exc))


def check_disk_space() -> dict:
    try:
        total, used, free = shutil.disk_usage(str(LOGS_DIR))
        free_gb = free / (1024 ** 3)
        detail  = f"{free_gb:.1f} GB free"
        status  = "OK" if free_gb >= 2 else "WARN" if free_gb >= 0.5 else "FAIL"
        return _check("Disk Space", status, detail)
    except Exception as exc:
        return _check("Disk Space", "WARN", str(exc))


def check_log_file() -> dict:
    log = LOGS_DIR / "pipeline.log"
    if not log.exists():
        return _check("Log File", "WARN", "Not created yet")
    size_mb = log.stat().st_size / (1024 * 1024)
    status  = "OK" if size_mb < 50 else "WARN"
    return _check("Log File", status, f"{size_mb:.1f} MB")


# ===========================================================
# FULL HEALTH REPORT
# ===========================================================

def run_health_checks() -> dict:
    """Run every check. Returns dict with overall status + list of checks."""
    checks = [
        check_api_key(),
        check_database(),
        check_data_freshness(),
        check_pipeline_runs(),
        check_disk_space(),
        check_log_file(),
    ]
    statuses = [c["status"] for c in checks]
    overall  = ("FAIL" if "FAIL" in statuses
                else "WARN" if "WARN" in statuses
                else "OK")
    return {
        "overall":        overall,
        "checked_at":     datetime.now().isoformat(),
        "checks":         checks,
        "active_alerts":  len(get_active_alerts()),
    }


def print_health_report() -> dict:
    """Print formatted health report to terminal."""
    health = run_health_checks()

    print()
    print("=" * 55)
    print("  PIPELINE HEALTH MONITOR")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    for c in health["checks"]:
        icon = ICON.get(c["status"], "❓")
        print(f"  {icon}  {c['name']:<20}  {c['detail']}")

    print("─" * 55)
    overall_icon = ICON.get(health["overall"], "❓")
    print(f"  {overall_icon}  Overall Status        {health['overall']}")
    print(f"  ⚠️   Active Alerts        {health['active_alerts']}")
    print("=" * 55)
    print()

    return health


# Run directly:  python src/monitor.py
if __name__ == "__main__":
    print_health_report()
