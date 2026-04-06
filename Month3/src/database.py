# ============================================================
#  src/database.py
#  Everything that touches the SQLite database lives here.
#  Tables:
#    1. cities          — one row per tracked city
#    2. weather_data    — one row per reading
#    3. weather_alerts  — one row per triggered alert
#    4. pipeline_runs   — one row per ETL execution (monitoring)
# ============================================================

import sqlite3
import json
from datetime import datetime
from typing import Optional

import sys, os
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from src.config import DB_PATH, get_logger

logger = get_logger("database")


# ===========================================================
# CONNECTION
# ===========================================================

def get_conn() -> sqlite3.Connection:
    """Open a database connection. Rows behave like dicts."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row          # row["col"] not row[0]
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ===========================================================
# SETUP — create all tables and indexes
# ===========================================================

def setup_database() -> None:
    """
    Create every table and index.
    Safe to call multiple times — uses IF NOT EXISTS.
    """
    statements = [

        # ── Table 1: cities ──────────────────────────────────
        """
        CREATE TABLE IF NOT EXISTS cities (
            city_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            city_name   TEXT    NOT NULL,
            country     TEXT,
            latitude    REAL,
            longitude   REAL,
            timezone    TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (city_name, country)
        )
        """,

        # ── Table 2: weather_data ────────────────────────────
        """
        CREATE TABLE IF NOT EXISTS weather_data (
            record_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
            city_id         INTEGER  NOT NULL,
            timestamp       TIMESTAMP NOT NULL,
            temperature_c   REAL,
            feels_like_c    REAL,
            temp_min_c      REAL,
            temp_max_c      REAL,
            humidity        INTEGER,
            pressure_hpa    REAL,
            wind_speed_mps  REAL,
            wind_deg        INTEGER,
            weather_condition TEXT,
            weather_main    TEXT,
            visibility_m    INTEGER,
            clouds_pct      INTEGER,
            rain_1h_mm      REAL DEFAULT 0,
            raw_json        TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES cities (city_id)
        )
        """,

        # ── Table 3: weather_alerts ──────────────────────────
        """
        CREATE TABLE IF NOT EXISTS weather_alerts (
            alert_id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            city_id         INTEGER  NOT NULL,
            alert_type      TEXT     NOT NULL,
            severity        TEXT     NOT NULL,
            message         TEXT,
            threshold_value REAL,
            actual_value    REAL,
            triggered_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_resolved     INTEGER  NOT NULL DEFAULT 0,
            FOREIGN KEY (city_id) REFERENCES cities (city_id)
        )
        """,

        # ── Table 4: pipeline_runs ───────────────────────────
        """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            run_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cities_attempted INTEGER  DEFAULT 0,
            records_inserted INTEGER  DEFAULT 0,
            alerts_triggered INTEGER  DEFAULT 0,
            success          INTEGER  NOT NULL DEFAULT 1,
            duration_sec     REAL,
            error_message    TEXT
        )
        """,

        # ── Indexes for speed ────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_wd_city     ON weather_data (city_id)",
        "CREATE INDEX IF NOT EXISTS idx_wd_time     ON weather_data (timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_wd_cityTime ON weather_data (city_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_al_city     ON weather_alerts (city_id)",
        "CREATE INDEX IF NOT EXISTS idx_al_resolved ON weather_alerts (is_resolved)",
    ]

    with get_conn() as conn:
        for stmt in statements:
            conn.execute(stmt)
        conn.commit()

    logger.info("Database setup complete — all tables and indexes ready")


# ===========================================================
# CITIES
# ===========================================================

def upsert_city(city_name: str, country: str = "",
                latitude: float = None, longitude: float = None,
                timezone: str = "") -> int:
    """
    Insert a city if it doesn't exist, or return its existing id.
    This is 'upsert' = UPDATE or INSERT.
    """
    sql_insert = """
        INSERT OR IGNORE INTO cities (city_name, country, latitude, longitude, timezone)
        VALUES (?, ?, ?, ?, ?)
    """
    sql_select = "SELECT city_id FROM cities WHERE city_name = ? AND country = ?"

    with get_conn() as conn:
        conn.execute(sql_insert, (city_name, country, latitude, longitude, timezone))
        conn.commit()
        row = conn.execute(sql_select, (city_name, country)).fetchone()
        return row["city_id"] if row else -1


def get_all_cities() -> list:
    """Return all active cities as a list of dicts."""
    sql = "SELECT * FROM cities WHERE is_active = 1 ORDER BY city_name"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def get_city_by_name(name: str) -> Optional[dict]:
    """Find one city by name."""
    sql = "SELECT * FROM cities WHERE city_name = ? AND is_active = 1"
    with get_conn() as conn:
        row = conn.execute(sql, (name,)).fetchone()
        return dict(row) if row else None


# ===========================================================
# WEATHER DATA
# ===========================================================

def insert_weather_record(city_id: int, data: dict) -> int:
    """
    Save one weather reading to weather_data.
    Returns the new record_id.
    """
    sql = """
        INSERT INTO weather_data (
            city_id, timestamp, temperature_c, feels_like_c,
            temp_min_c, temp_max_c, humidity, pressure_hpa,
            wind_speed_mps, wind_deg, weather_condition,
            weather_main, visibility_m, clouds_pct,
            rain_1h_mm, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    values = (
        city_id,
        data.get("timestamp", datetime.utcnow().isoformat()),
        data.get("temperature"),
        data.get("feels_like"),
        data.get("temp_min"),
        data.get("temp_max"),
        data.get("humidity"),
        data.get("pressure"),
        data.get("wind_speed"),
        data.get("wind_deg"),
        data.get("condition"),
        data.get("weather_main"),
        data.get("visibility"),
        data.get("clouds"),
        data.get("rain_1h", 0.0),
        json.dumps(data.get("raw", {})),
    )
    with get_conn() as conn:
        cur = conn.execute(sql, values)
        conn.commit()
        return cur.lastrowid


def get_latest_reading(city_id: int) -> Optional[dict]:
    """Get the most recent record for a city."""
    sql = """
        SELECT wd.*, c.city_name, c.country
        FROM weather_data wd
        JOIN cities c ON wd.city_id = c.city_id
        WHERE wd.city_id = ?
        ORDER BY wd.timestamp DESC
        LIMIT 1
    """
    with get_conn() as conn:
        row = conn.execute(sql, (city_id,)).fetchone()
        return dict(row) if row else None


def get_readings_last_n_days(city_id: int, days: int = 30) -> list:
    """All readings for a city over the last N days, oldest first."""
    sql = """
        SELECT * FROM weather_data
        WHERE city_id = ?
          AND timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    """
    with get_conn() as conn:
        return [dict(r) for r in
                conn.execute(sql, (city_id, f"-{days} days")).fetchall()]


def get_current_snapshot() -> list:
    """
    One latest reading per active city — used for the live dashboard.
    Uses a subquery so we don't need window functions (SQLite safe).
    """
    sql = """
        SELECT
            c.city_id,
            c.city_name,
            c.country,
            wd.temperature_c,
            wd.feels_like_c,
            wd.humidity,
            wd.wind_speed_mps,
            wd.weather_condition,
            wd.pressure_hpa,
            wd.timestamp
        FROM cities c
        LEFT JOIN weather_data wd ON wd.record_id = (
            SELECT record_id FROM weather_data
            WHERE city_id = c.city_id
            ORDER BY timestamp DESC
            LIMIT 1
        )
        WHERE c.is_active = 1
        ORDER BY c.city_name
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


# ===========================================================
# ANALYTICS QUERIES  (the 5 analysis questions from requirements)
# ===========================================================

def query_highest_avg_temp(days: int = 30) -> list:
    """Q1: Which city has the highest average temperature?"""
    sql = """
        SELECT
            c.city_name,
            ROUND(AVG(wd.temperature_c), 2) AS avg_temp_c,
            COUNT(*)                         AS readings
        FROM weather_data wd
        JOIN cities c ON wd.city_id = c.city_id
        WHERE wd.timestamp >= datetime('now', ?)
        GROUP BY c.city_id
        ORDER BY avg_temp_c DESC
    """
    with get_conn() as conn:
        return [dict(r) for r in
                conn.execute(sql, (f"-{days} days",)).fetchall()]


def query_temp_trend(city_id: int, days: int = 30) -> list:
    """Q2: Temperature trend over the last 30 days (daily averages)."""
    sql = """
        SELECT
            DATE(timestamp)            AS day,
            ROUND(AVG(temperature_c), 1) AS avg_temp,
            ROUND(MIN(temperature_c), 1) AS min_temp,
            ROUND(MAX(temperature_c), 1) AS max_temp
        FROM weather_data
        WHERE city_id = ?
          AND timestamp >= datetime('now', ?)
        GROUP BY day
        ORDER BY day
    """
    with get_conn() as conn:
        return [dict(r) for r in
                conn.execute(sql, (city_id, f"-{days} days")).fetchall()]


def query_humidity_vs_rain() -> list:
    """Q3: How does humidity correlate with rainfall?"""
    sql = """
        SELECT
            CAST(ROUND(humidity / 10.0) * 10 AS INTEGER) AS humidity_bucket,
            ROUND(AVG(rain_1h_mm), 3)  AS avg_rain_mm,
            COUNT(*)                   AS readings
        FROM weather_data
        WHERE humidity IS NOT NULL
        GROUP BY humidity_bucket
        ORDER BY humidity_bucket
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def query_extreme_by_month() -> list:
    """Q4: Which months have the most extreme weather?"""
    sql = """
        SELECT
            strftime('%m', timestamp)   AS month,
            ROUND(MAX(temperature_c), 1) AS max_temp,
            ROUND(MIN(temperature_c), 1) AS min_temp,
            ROUND(MAX(wind_speed_mps), 1) AS max_wind,
            ROUND(MAX(humidity), 0)      AS max_humidity
        FROM weather_data
        GROUP BY month
        ORDER BY month
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def query_peak_temp_hours(city_id: int) -> list:
    """Q5: What are the peak temperature hours for a city?"""
    sql = """
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            ROUND(AVG(temperature_c), 1)               AS avg_temp
        FROM weather_data
        WHERE city_id = ?
        GROUP BY hour
        ORDER BY avg_temp DESC
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, (city_id,)).fetchall()]


def get_db_statistics() -> dict:
    """Return summary stats for the monitor/dashboard."""
    sqls = {
        "total_records": "SELECT COUNT(*) AS n FROM weather_data",
        "total_cities":  "SELECT COUNT(*) AS n FROM cities WHERE is_active=1",
        "active_alerts": "SELECT COUNT(*) AS n FROM weather_alerts WHERE is_resolved=0",
        "last_run":      "SELECT MAX(run_at) AS n FROM pipeline_runs",
    }
    stats = {}
    with get_conn() as conn:
        for key, sql in sqls.items():
            row = conn.execute(sql).fetchone()
            stats[key] = row["n"] if row else 0
    return stats


# ===========================================================
# ALERTS
# ===========================================================

def insert_alert(city_id: int, alert_type: str, severity: str,
                 message: str, threshold: float, actual: float) -> int:
    sql = """
        INSERT INTO weather_alerts
            (city_id, alert_type, severity, message, threshold_value, actual_value)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with get_conn() as conn:
        cur = conn.execute(sql, (city_id, alert_type, severity,
                                 message, threshold, actual))
        conn.commit()
        logger.warning(f"ALERT [{severity}] {alert_type}: {message}")
        return cur.lastrowid


def get_active_alerts() -> list:
    sql = """
        SELECT a.*, c.city_name
        FROM weather_alerts a
        JOIN cities c ON a.city_id = c.city_id
        WHERE a.is_resolved = 0
        ORDER BY a.triggered_at DESC
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def get_todays_alerts() -> list:
    sql = """
        SELECT a.*, c.city_name
        FROM weather_alerts a
        JOIN cities c ON a.city_id = c.city_id
        WHERE DATE(a.triggered_at) = DATE('now')
        ORDER BY a.triggered_at DESC
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


# ===========================================================
# PIPELINE RUNS  (for monitoring)
# ===========================================================

def log_run(cities_attempted: int, records_inserted: int,
            alerts_triggered: int, duration_sec: float,
            success: bool = True, error_message: str = None) -> None:
    sql = """
        INSERT INTO pipeline_runs
            (cities_attempted, records_inserted, alerts_triggered,
             success, duration_sec, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with get_conn() as conn:
        conn.execute(sql, (cities_attempted, records_inserted,
                           alerts_triggered, int(success),
                           round(duration_sec, 3), error_message))
        conn.commit()


def get_run_history(limit: int = 20) -> list:
    sql = """
        SELECT * FROM pipeline_runs
        ORDER BY run_at DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, (limit,)).fetchall()]
