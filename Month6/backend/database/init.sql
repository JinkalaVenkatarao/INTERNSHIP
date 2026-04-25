-- ══════════════════════════════════════════════════════════════════════════════
-- Real Estate Price Prediction — Database Schema
-- PostgreSQL 15+
-- ══════════════════════════════════════════════════════════════════════════════

-- ── Extensions ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ── Properties table (raw ingested listings) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS properties (
    id                 UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id        VARCHAR(20) UNIQUE NOT NULL,
    city               VARCHAR(50) NOT NULL,
    locality           VARCHAR(100) NOT NULL,
    property_type      VARCHAR(50) NOT NULL,
    area_sqft          NUMERIC(10,2) NOT NULL,
    bedrooms           SMALLINT NOT NULL,
    bathrooms          SMALLINT NOT NULL,
    balconies          SMALLINT DEFAULT 0,
    floor              SMALLINT DEFAULT 0,
    total_floors       SMALLINT DEFAULT 1,
    age_years          SMALLINT NOT NULL,
    facing             VARCHAR(20),
    furnishing_status  VARCHAR(30),
    parking_spaces     SMALLINT DEFAULT 0,
    amenities_score    NUMERIC(4,2) DEFAULT 0.5,
    near_metro         BOOLEAN DEFAULT FALSE,
    near_school        BOOLEAN DEFAULT FALSE,
    near_hospital      BOOLEAN DEFAULT FALSE,
    transaction_type   VARCHAR(20) DEFAULT 'Sale',
    possession_status  VARCHAR(30),
    actual_price_inr   BIGINT,
    listed_date        DATE,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ── Predictions table (API prediction log) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id                   UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id          UUID         REFERENCES properties(id) ON DELETE SET NULL,
    predicted_price      BIGINT       NOT NULL,
    lower_bound          BIGINT,
    upper_bound          BIGINT,
    model_version        VARCHAR(20)  NOT NULL DEFAULT '1.0.0',
    input_payload        JSONB        NOT NULL,
    latency_ms           NUMERIC(8,2),
    user_agent           TEXT,
    ip_address           INET,
    feedback_rating      SMALLINT     CHECK (feedback_rating BETWEEN 1 AND 5),
    actual_price         BIGINT,
    created_at           TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Model registry table ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_registry (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    version         VARCHAR(20) NOT NULL UNIQUE,
    model_type      VARCHAR(50) NOT NULL DEFAULT 'XGBoost',
    mae_inr         BIGINT,
    rmse_inr        BIGINT,
    r2_score        NUMERIC(6,4),
    mape_pct        NUMERIC(6,2),
    training_rows   INTEGER,
    artifact_path   TEXT,
    is_production   BOOLEAN DEFAULT FALSE,
    deployed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── API metrics table ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS api_metrics (
    id              BIGSERIAL   PRIMARY KEY,
    endpoint        VARCHAR(100) NOT NULL,
    method          VARCHAR(10)  NOT NULL,
    status_code     SMALLINT     NOT NULL,
    latency_ms      NUMERIC(10,2),
    user_agent      TEXT,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_properties_city    ON properties(city);
CREATE INDEX IF NOT EXISTS idx_properties_type    ON properties(property_type);
CREATE INDEX IF NOT EXISTS idx_properties_price   ON properties(actual_price_inr);
CREATE INDEX IF NOT EXISTS idx_predictions_model  ON predictions(model_version);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_created    ON api_metrics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_endpoint   ON api_metrics(endpoint);

-- ── Seed model registry with initial version ──────────────────────────────────
INSERT INTO model_registry (version, model_type, r2_score, mape_pct, is_production, deployed_at)
VALUES ('1.0.0', 'XGBoost+Ensemble', 0.9649, 10.97, TRUE, NOW())
ON CONFLICT (version) DO NOTHING;

-- ── Updated_at trigger ────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_properties_updated
    BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Useful views ──────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_prediction_summary AS
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*)                       AS total_predictions,
    AVG(latency_ms)                AS avg_latency_ms,
    AVG(predicted_price / 100000.0) AS avg_price_lakhs,
    AVG(feedback_rating)           AS avg_rating
FROM predictions
GROUP BY 1 ORDER BY 1 DESC;

CREATE OR REPLACE VIEW v_city_stats AS
SELECT
    city,
    COUNT(*)                              AS listing_count,
    ROUND(AVG(actual_price_inr)/100000,2) AS avg_price_lakhs,
    ROUND(MIN(actual_price_inr)/100000,2) AS min_price_lakhs,
    ROUND(MAX(actual_price_inr)/100000,2) AS max_price_lakhs,
    ROUND(AVG(area_sqft),0)               AS avg_area_sqft
FROM properties
WHERE actual_price_inr IS NOT NULL
GROUP BY city ORDER BY avg_price_lakhs DESC;
