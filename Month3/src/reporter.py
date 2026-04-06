# ============================================================
#  src/reporter.py
#  Produces the exact output format shown in the requirements,
#  plus saves full reports to the reports/ folder.
# ============================================================

from datetime import datetime
from pathlib  import Path

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.config   import REPORTS_DIR, get_logger
from src.database import (get_current_snapshot, get_todays_alerts,
                           get_db_statistics, get_run_history,
                           get_all_cities, query_highest_avg_temp,
                           query_temp_trend, query_humidity_vs_rain,
                           query_peak_temp_hours)

logger = get_logger("reporter")


# ===========================================================
# LIVE STATUS DISPLAY  (matches the sample output exactly)
# ===========================================================

def print_status() -> None:
    """
    Print the live weather status to the terminal.
    Output format matches the sample output in the requirements.
    """
    stats    = get_db_statistics()
    history  = get_run_history(limit=1)
    snapshot = get_current_snapshot()
    alerts   = get_todays_alerts()

    last_run    = history[0]["run_at"][:19].replace("T", " ") if history else "Never"
    last_status = "Successful" if (history and history[0]["success"]) else "Failed"
    next_run    = "See scheduler"

    print()
    print("WEATHER DATA PIPELINE SYSTEM")
    print("=" * 35)
    print()
    print(f"📊 SYSTEM STATUS: RUNNING")
    print(f"⏰ Last Run: {last_run}")
    print(f"✅ Status: {last_status}")
    print(f"📈 Records Processed: {len(snapshot)} cities")
    print()

    # ── Current conditions ───────────────────────────────────
    print("🌤️  CURRENT WEATHER SNAPSHOT:")
    print("-" * 35)
    for row in snapshot:
        if row.get("temperature_c") is None:
            print(f"📍 {row['city_name']}: no data yet")
            continue
        temp  = row["temperature_c"]
        hum   = row["humidity"]
        cond  = row.get("weather_condition") or ""
        print(f"📍 {row['city_name']}: {temp}°C, {hum}% humidity, {cond.title()}")

    print()

    # ── Today's alerts ───────────────────────────────────────
    print("📅 TODAY'S ALERTS:")
    if alerts:
        for a in alerts:
            print(f"• {a['message']}")
    else:
        print("• No alerts today")

    print()

    # ── Database statistics ──────────────────────────────────
    print("📊 DATABASE STATISTICS:")
    print(f"• Total records: {stats.get('total_records', 0):,}")
    print(f"• Cities tracked: {stats.get('total_cities', 0)}")
    print(f"• Active alerts: {stats.get('active_alerts', 0)}")
    print(f"• Last pipeline run: {last_run}")

    print()
    print(f"🔄 NEXT SCHEDULED RUN: {next_run}")
    print()


# ===========================================================
# ANALYSIS REPORT  (answers the 5 questions from requirements)
# ===========================================================

def print_analysis() -> None:
    """Print answers to all 5 analysis questions."""
    cities = get_all_cities()
    print()
    print("=" * 50)
    print("  WEATHER ANALYSIS REPORT")
    print("=" * 50)

    # Q1
    print("\n🏆 Q1: Highest average temperature (last 30 days)")
    print("─" * 40)
    rows = query_highest_avg_temp(days=30)
    if rows:
        for i, r in enumerate(rows[:5], 1):
            bar = "█" * int(r["avg_temp_c"] / 2) if r["avg_temp_c"] > 0 else ""
            print(f"  {i}. {r['city_name']:<15} {r['avg_temp_c']:>5.1f}°C  {bar}")
    else:
        print("  No data yet")

    # Q2
    print("\n📈 Q2: Temperature trend — last 30 days")
    print("─" * 40)
    if cities:
        city = cities[0]
        rows = query_temp_trend(city["city_id"], days=30)
        if rows:
            for r in rows[-7:]:     # show last 7 days
                bar = "█" * int(r["avg_temp"] / 2) if r["avg_temp"] > 0 else ""
                print(f"  {r['day']}  avg {r['avg_temp']:>5.1f}°C  "
                      f"(min {r['min_temp']}, max {r['max_temp']})  {bar}")
        else:
            print(f"  No trend data for {city['city_name']} yet")

    # Q3
    print("\n💧 Q3: Humidity vs Rainfall correlation")
    print("─" * 40)
    rows = query_humidity_vs_rain()
    if rows:
        for r in rows:
            print(f"  Humidity ~{r['humidity_bucket']:>3}%  →  "
                  f"avg rain {r['avg_rain_mm']:.3f} mm  "
                  f"({r['readings']} readings)")
    else:
        print("  No data yet")

    # Q4
    print("\n🌡️  Q4: Extreme weather by month")
    print("─" * 40)
    from src.database import query_extreme_by_month
    rows = query_extreme_by_month()
    months = ["", "Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    if rows:
        for r in rows:
            m = months[int(r["month"])]
            print(f"  {m}  max {r['max_temp']}°C  "
                  f"min {r['min_temp']}°C  "
                  f"max wind {r['max_wind']} m/s  "
                  f"max hum {r['max_humidity']}%")
    else:
        print("  No data yet")

    # Q5
    print("\n⏰ Q5: Peak temperature hours")
    print("─" * 40)
    if cities:
        city = cities[0]
        rows = query_peak_temp_hours(city["city_id"])
        if rows:
            print(f"  City: {city['city_name']}")
            for r in rows[:5]:
                bar = "█" * int(r["avg_temp"] / 2) if r["avg_temp"] > 0 else ""
                print(f"  {r['hour']:02d}:00  {r['avg_temp']:>5.1f}°C  {bar}")
        else:
            print(f"  No data for {city['city_name']} yet")

    print()


# ===========================================================
# SAVE REPORT TO FILE
# ===========================================================

def save_report() -> Path:
    """Save the full analysis to a text file in reports/."""
    import io, contextlib
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"report_{timestamp}.txt"

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_status()
        print_analysis()

    path.write_text(buf.getvalue(), encoding="utf-8")
    logger.info(f"Report saved: {path}")
    return path


# Run directly:  python src/reporter.py
if __name__ == "__main__":
    print_status()
    print_analysis()
