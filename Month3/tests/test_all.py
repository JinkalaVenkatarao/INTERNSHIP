# ============================================================
#  tests/test_all.py
#  Full test suite — no real API key needed.
#  Run:  python tests/test_all.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; E = "\033[0m"
_pass = _fail = 0


def ok(msg):
    global _pass
    print(f"  {G}✅ PASS{E}  {msg}")
    _pass += 1


def fail(msg, err=""):
    global _fail
    print(f"  {R}❌ FAIL{E}  {msg}")
    if err:
        print(f"         {Y}{err}{E}")
    _fail += 1


def section(title):
    print(f"\n{'─'*52}\n  {title}\n{'─'*52}")


# ===========================================================
# 1. CONFIG
# ===========================================================
section("1. CONFIG")

try:
    from src.config import (BASE_URL, CITIES, TEMP_HIGH, TEMP_LOW,
                             HUM_HIGH, WIND_HIGH, DB_PATH, get_logger)
    ok(f"Config loaded | {len(CITIES)} cities: {CITIES[:3]}")
    ok(f"Thresholds — temp hi:{TEMP_HIGH} lo:{TEMP_LOW} hum:{HUM_HIGH} wind:{WIND_HIGH}")
    ok(f"DB path: {DB_PATH}")
    logger = get_logger("test")
    ok("Logger OK")
except Exception as e:
    fail("Config", str(e))


# ===========================================================
# 2. DATABASE
# ===========================================================
section("2. DATABASE")

try:
    from src.database import (setup_database, upsert_city,
                               insert_weather_record, insert_alert,
                               get_all_cities, get_latest_reading,
                               get_current_snapshot, get_db_statistics,
                               get_active_alerts, log_run)

    setup_database()
    ok("Tables created")

    cid = upsert_city("Mumbai", "IN", 19.07, 72.87, "Asia/Kolkata")
    assert cid > 0
    ok(f"City inserted  city_id={cid}")

    cid2 = upsert_city("Mumbai", "IN", 19.07, 72.87, "Asia/Kolkata")
    assert cid == cid2
    ok("Duplicate upsert returns same id")

    rid = insert_weather_record(cid, {
        "city":        "Mumbai",
        "timestamp":   datetime.utcnow().isoformat(),
        "temperature": 28.5,
        "feels_like":  30.0,
        "temp_min":    25.0,
        "temp_max":    32.0,
        "humidity":    65,
        "pressure":    1012.0,
        "wind_speed":  3.2,
        "wind_deg":    220,
        "condition":   "clear sky",
        "weather_main":"Clear",
        "visibility":  10000,
        "clouds":      5,
        "rain_1h":     0.0,
    })
    assert rid > 0
    ok(f"Weather record inserted  record_id={rid}")

    rec = get_latest_reading(cid)
    assert rec is not None
    assert rec["temperature_c"] == 28.5
    ok(f"Latest reading OK  temp={rec['temperature_c']}°C")

    snap = get_current_snapshot()
    assert len(snap) >= 1
    ok(f"Snapshot OK  cities={len(snap)}")

    stats = get_db_statistics()
    assert stats["total_records"] >= 1
    ok(f"Stats OK  records={stats['total_records']}")

    aid = insert_alert(cid, "HIGH_TEMPERATURE", "CRITICAL",
                       "Test alert", 35.0, 40.0)
    assert aid > 0
    ok(f"Alert inserted  alert_id={aid}")

    active = get_active_alerts()
    assert len(active) >= 1
    ok(f"Active alerts retrieved  count={len(active)}")

    log_run(cities_attempted=7, records_inserted=7,
            alerts_triggered=1, duration_sec=4.2, success=True)
    ok("Pipeline run logged")

except Exception as e:
    fail("Database", str(e))


# ===========================================================
# 3. VALIDATORS
# ===========================================================
section("3. VALIDATORS")

try:
    from src.validators import validate_record, validate_batch, check_alerts

    good = {
        "city":        "Delhi",
        "timestamp":   "2024-01-15T10:00:00",
        "temperature": 22.3,
        "humidity":    45.0,
        "pressure":    1015.0,
        "wind_speed":  2.8,
    }
    res = validate_record(good)
    assert res.is_valid, res.errors
    ok("Valid record passes")

    bad = {"temperature": 25.0}
    res = validate_record(bad)
    assert not res.is_valid
    ok(f"Missing fields rejected: {res.errors}")

    extreme = dict(good)
    extreme["temperature"] = 999.0
    res = validate_record(extreme)
    assert res.warnings
    assert res.cleaned["temperature"] <= 60.0
    ok(f"Out-of-range value clamped to {res.cleaned['temperature']}")

    valid, invalid = validate_batch([good, bad, extreme])
    assert len(valid)   == 2
    assert len(invalid) == 1
    ok(f"Batch: {len(valid)} valid, {len(invalid)} invalid")

    hot = dict(good)
    hot["temperature"] = 42.0
    alerts = check_alerts(hot)
    assert any(a["alert_type"] == "HIGH_TEMPERATURE" for a in alerts)
    ok(f"High-temp alert triggered: {alerts[0]['message']}")

    normal_alerts = check_alerts(good)
    assert len(normal_alerts) == 0
    ok("Normal reading produces zero alerts")

except Exception as e:
    fail("Validators", str(e))


# ===========================================================
# 4. API CLIENT (parser only — no real HTTP call)
# ===========================================================
section("4. API CLIENT — PARSER")

try:
    from src.api_client import _parse

    fake_raw = {
        "name": "Bangalore",
        "dt":   1705312800,
        "main": {"temp": 24.8, "feels_like": 25.5, "temp_min": 20.0,
                 "temp_max": 28.0, "humidity": 70, "pressure": 1013},
        "wind":    {"speed": 2.1, "deg": 180},
        "weather": [{"main": "Rain", "description": "light rain"}],
        "clouds":  {"all": 80},
        "rain":    {"1h": 0.5},
        "snow":    {},
        "coord":   {"lat": 12.97, "lon": 77.59},
        "sys":     {"country": "IN"},
        "timezone": 19800,
        "visibility": 8000,
    }

    parsed = _parse(fake_raw)

    assert parsed["city"]        == "Bangalore"
    assert parsed["temperature"] == 24.8
    assert parsed["humidity"]    == 70
    assert parsed["rain_1h"]     == 0.5
    assert "timestamp" in parsed
    ok(f"Parser correct: {parsed['city']} {parsed['temperature']}°C "
       f"{parsed['condition']}")

except Exception as e:
    fail("API parser", str(e))


# ===========================================================
# 5. REPORTER
# ===========================================================
section("5. REPORTER")

try:
    import io, contextlib
    from src.reporter import print_status, print_analysis

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_status()
    out = buf.getvalue()
    assert "WEATHER DATA PIPELINE SYSTEM" in out
    assert "CURRENT WEATHER SNAPSHOT" in out
    ok("print_status() runs without error")

    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        print_analysis()
    out2 = buf2.getvalue()
    assert "WEATHER ANALYSIS REPORT" in out2
    ok("print_analysis() runs without error")

except Exception as e:
    fail("Reporter", str(e))


# ===========================================================
# 6. MONITOR
# ===========================================================
section("6. MONITOR")

try:
    from src.monitor import run_health_checks

    health = run_health_checks()
    assert "overall"  in health
    assert "checks"   in health
    assert len(health["checks"]) >= 5
    ok(f"Health checks ran  overall={health['overall']}")
    for c in health["checks"]:
        icon = {"OK":"✅","WARN":"⚠️","FAIL":"❌"}.get(c["status"],"❓")
        print(f"         {icon}  {c['name']}: {c['detail']}")

except Exception as e:
    fail("Monitor", str(e))


# ===========================================================
# SUMMARY
# ===========================================================
total = _pass + _fail
print(f"\n{'═'*52}")
print(f"  RESULTS: {_pass}/{total} passed", end="")
if _fail:
    print(f"   {R}{_fail} FAILED{E}")
else:
    print(f"   {G}All tests passed 🎉{E}")
print(f"{'═'*52}\n")
sys.exit(1 if _fail else 0)
