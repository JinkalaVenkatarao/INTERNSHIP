-- ============================================================
-- database/schema.sql
-- Full SQL schema for the Weather Pipeline database.
-- This is documentation only — the database is created
-- automatically by src/database.py when you run the pipeline.
-- ============================================================

-- Table 1: cities
-- One row per tracked city. City readings link back here.
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
);

-- Table 2: weather_data
-- One row per API reading. The main data table.
CREATE TABLE IF NOT EXISTS weather_data (
    record_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
    city_id         INTEGER  NOT NULL,
    timestamp       TIMESTAMP NOT NULL,
    temperature_c   REAL,               -- °C
    feels_like_c    REAL,               -- °C
    temp_min_c      REAL,               -- °C
    temp_max_c      REAL,               -- °C
    humidity        INTEGER,            -- %
    pressure_hpa    REAL,               -- hPa
    wind_speed_mps  REAL,               -- m/s
    wind_deg        INTEGER,            -- degrees 0-360
    weather_condition TEXT,             -- e.g. "clear sky"
    weather_main    TEXT,               -- e.g. "Clear"
    visibility_m    INTEGER,            -- metres
    clouds_pct      INTEGER,            -- %
    rain_1h_mm      REAL DEFAULT 0,     -- mm in last hour
    raw_json        TEXT,               -- full API response
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES cities (city_id)
);

-- Table 3: weather_alerts
-- One row per triggered alert condition.
CREATE TABLE IF NOT EXISTS weather_alerts (
    alert_id        INTEGER  PRIMARY KEY AUTOINCREMENT,
    city_id         INTEGER  NOT NULL,
    alert_type      TEXT     NOT NULL,  -- HIGH_TEMPERATURE, etc.
    severity        TEXT     NOT NULL,  -- CRITICAL, HIGH, MEDIUM, LOW
    message         TEXT,
    threshold_value REAL,               -- configured limit
    actual_value    REAL,               -- what was measured
    triggered_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_resolved     INTEGER  NOT NULL DEFAULT 0,
    FOREIGN KEY (city_id) REFERENCES cities (city_id)
);

-- Table 4: pipeline_runs
-- Audit log for every ETL execution.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id           INTEGER  PRIMARY KEY AUTOINCREMENT,
    run_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cities_attempted INTEGER  DEFAULT 0,
    records_inserted INTEGER  DEFAULT 0,
    alerts_triggered INTEGER  DEFAULT 0,
    success          INTEGER  NOT NULL DEFAULT 1,
    duration_sec     REAL,
    error_message    TEXT
);

-- ── Indexes (speed up common queries) ─────────────────────
CREATE INDEX IF NOT EXISTS idx_wd_city     ON weather_data (city_id);
CREATE INDEX IF NOT EXISTS idx_wd_time     ON weather_data (timestamp);
CREATE INDEX IF NOT EXISTS idx_wd_cityTime ON weather_data (city_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_al_city     ON weather_alerts (city_id);
CREATE INDEX IF NOT EXISTS idx_al_resolved ON weather_alerts (is_resolved);

-- ── Sample analysis queries ────────────────────────────────

-- Q1: Highest average temperature
SELECT c.city_name, ROUND(AVG(wd.temperature_c),2) AS avg_temp
FROM weather_data wd JOIN cities c ON wd.city_id = c.city_id
GROUP BY c.city_id ORDER BY avg_temp DESC;

-- Q2: Daily temperature trend for a city (city_id = 1)
SELECT DATE(timestamp) AS day,
       ROUND(AVG(temperature_c),1) AS avg,
       ROUND(MIN(temperature_c),1) AS min,
       ROUND(MAX(temperature_c),1) AS max
FROM weather_data WHERE city_id = 1
GROUP BY day ORDER BY day;

-- Q3: Humidity vs rainfall
SELECT CAST(ROUND(humidity/10.0)*10 AS INT) AS bucket,
       ROUND(AVG(rain_1h_mm),3) AS avg_rain
FROM weather_data GROUP BY bucket ORDER BY bucket;

-- Q4: Extreme weather by month
SELECT strftime('%m', timestamp) AS month,
       MAX(temperature_c) AS max_temp, MIN(temperature_c) AS min_temp,
       MAX(wind_speed_mps) AS max_wind
FROM weather_data GROUP BY month ORDER BY month;

-- Q5: Peak temperature hours for a city
SELECT CAST(strftime('%H', timestamp) AS INT) AS hour,
       ROUND(AVG(temperature_c),1) AS avg_temp
FROM weather_data WHERE city_id = 1
GROUP BY hour ORDER BY avg_temp DESC;
