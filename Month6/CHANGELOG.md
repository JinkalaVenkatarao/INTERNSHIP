# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] — 2025-01-15

### Added
- Initial production release
- XGBoost model with R² = 0.9649 on Indian real estate dataset
- FastAPI backend with `/predict`, `/batch`, `/health`, `/metrics`, `/model-info` endpoints
- Interactive React HTML dashboard with Chart.js visualisations
- Drift detection using KS-test + PSI + MAPE checks
- Docker Compose full-stack deployment
- GitHub Actions CI/CD with weekly auto-retraining
- Prometheus metrics + Grafana dashboards
- PostgreSQL schema with prediction logging
- 30-test pytest suite (unit + integration + performance)
- 5,000-row synthetic Indian real estate dataset (25 features)

### Models Trained
- XGBoost (best: MAE ₹23.4L, R² 0.9649)
- Random Forest (MAE ₹45.8L, R² 0.8483)
- Neural Network MLP (MAE ₹96.7L, R² 0.2750)
- Ensemble (weighted average: XGB 50%, RF 30%, MLP 20%)
