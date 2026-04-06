# 🌤 Weather Data Pipeline System

An end-to-end data engineering pipeline that extracts real-time weather data
from the OpenWeatherMap API, cleans and validates it, stores it in a
SQLite database, triggers alerts, and provides analysis and monitoring.

---

## 📁 Project Structure

```
weather_project/
│
├── README.md                    ← You are here
├── requirements.txt             ← pip install -r requirements.txt
│
├── config/
│   └── settings.env             ← ⚡ PUT YOUR API KEY HERE
│
├── src/                         ← All source code
│   ├── config.py                ← Settings loader + logging
│   ├── database.py              ← All SQLite operations
│   ├── api_client.py            ← OpenWeatherMap API calls
│   ├── etl_pipeline.py          ← Extract → Transform → Load
│   ├── validators.py            ← Data quality checks + alerts
│   ├── scheduler.py             ← Automated scheduling
│   ├── reporter.py              ← Status display + analysis
│   └── monitor.py               ← System health checks
│
├── database/
│   ├── schema.sql               ← SQL schema documentation
│   └── weather_data.db          ← Auto-created when you run pipeline
│
├── tests/
│   └── test_all.py              ← Full test suite
│
├── docs/
│   └── setup_guide.md           ← Detailed setup instructions
│
├── scripts/
│   ├── run_pipeline.py          ← Run ETL once manually
│   ├── start_scheduler.py       ← Start auto collection
│   └── health_check.py          ← Check system health
│
├── logs/
│   └── pipeline.log             ← Auto-created log file
│
└── reports/                     ← Saved report files
```

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key to config/settings.env

# 3. Run tests (no API key needed)
python tests/test_all.py

# 4. Collect data once
python scripts/run_pipeline.py

# 5. Start auto collection (every 60 min)
python scripts/start_scheduler.py

# 6. Check system health
python scripts/health_check.py
```

---

## 🗄️ Database Tables

| Table | What it stores |
|---|---|
| `cities` | One row per city (name, coordinates, country) |
| `weather_data` | One row per reading (temperature, humidity, wind, etc.) |
| `weather_alerts` | One row per triggered alert |
| `pipeline_runs` | One row per ETL execution (for monitoring) |

---

## 📊 Sample Output

```
WEATHER DATA PIPELINE SYSTEM
===================================

📊 SYSTEM STATUS: RUNNING
⏰ Last Run: 2024-01-15 09:00:00
✅ Status: Successful
📈 Records Processed: 7 cities

🌤️  CURRENT WEATHER SNAPSHOT:
-----------------------------------
📍 Bangalore: 24.8°C, 70% humidity, Light Rain
📍 Chennai: 30.2°C, 75% humidity, Sunny
📍 Delhi: 22.3°C, 45% humidity, Partly Cloudy
📍 Hyderabad: 28.1°C, 60% humidity, Haze
📍 Kolkata: 26.5°C, 80% humidity, Cloudy
📍 Mumbai: 28.5°C, 65% humidity, Clear Sky
📍 Pune: 25.3°C, 55% humidity, Clear Sky

📅 TODAY'S ALERTS:
• High temperature alert: Chennai (30.2°C > 30°C threshold)
• High humidity alert: Kolkata (80% > 75% threshold)

📊 DATABASE STATISTICS:
• Total records: 10,250
• Cities tracked: 7
• Active alerts: 2
• Last pipeline run: 2024-01-15 09:00:00

🔄 NEXT SCHEDULED RUN: See scheduler
```

---

## 🤔 Analysis Questions Answered

Run `python src/reporter.py` to see answers to all 5:

1. Which city has the highest average temperature?
2. What are the temperature trends over the last 30 days?
3. How does humidity correlate with rainfall?
4. Which months have the most extreme weather conditions?
5. What are the peak temperature hours for each city?

---

## ⚙️ Configuration (`config/settings.env`)

```env
API_KEY=your_openweathermap_key
CITIES=Mumbai,Delhi,Bangalore,Chennai,Kolkata,Hyderabad,Pune
TEMP_HIGH_THRESHOLD=35
TEMP_LOW_THRESHOLD=5
HUMIDITY_HIGH_THRESHOLD=80
WIND_SPEED_THRESHOLD=50
COLLECT_INTERVAL_MINUTES=60
```

---

*Project built for learning data engineering — Week 1 to Week 6 curriculum.*
