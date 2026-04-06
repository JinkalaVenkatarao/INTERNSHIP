# Weather Pipeline — Setup Guide

## 5-Minute Quick Start

### 1. Get a Free API Key
1. Go to [openweathermap.org](https://openweathermap.org)
2. Click **Sign Up** → create free account
3. Go to **API Keys** tab → copy your key
4. **Wait 10–15 minutes** for the key to activate

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your API Key
Open `config/settings.env` and replace `YOUR_API_KEY_HERE`:
```
API_KEY=abc123yourrealkey
```

### 4. Add Your Cities
Still in `config/settings.env`, edit the cities line:
```
CITIES=Mumbai,Delhi,Bangalore,Chennai,Kolkata,Hyderabad,Pune
```

### 5. Run Tests
```bash
python tests/test_all.py
```
All tests should pass even without a real API key.

### 6. Collect Data
```bash
python scripts/run_pipeline.py
```

### 7. Start Auto Collection
```bash
python scripts/start_scheduler.py
```
This runs every 60 minutes (configurable in settings.env).

---

## File Reference

| File | Purpose | Run directly? |
|---|---|---|
| `src/config.py` | Loads all settings | No |
| `src/database.py` | All DB operations | No |
| `src/api_client.py` | Calls weather API | No |
| `src/etl_pipeline.py` | Runs Extract→Transform→Load | Yes |
| `src/validators.py` | Checks data quality | No |
| `src/scheduler.py` | Auto scheduling | Yes |
| `src/reporter.py` | Status display | Yes |
| `src/monitor.py` | Health checks | Yes |

---

## Configuration Reference

| Setting | Default | Description |
|---|---|---|
| `API_KEY` | — | OpenWeatherMap API key (required) |
| `CITIES` | Mumbai,Delhi,… | Comma-separated list |
| `TEMP_HIGH_THRESHOLD` | 35 | °C — CRITICAL alert |
| `TEMP_LOW_THRESHOLD` | 5 | °C — HIGH alert |
| `HUMIDITY_HIGH_THRESHOLD` | 80 | % — MEDIUM alert |
| `WIND_SPEED_THRESHOLD` | 50 | km/h — HIGH alert |
| `COLLECT_INTERVAL_MINUTES` | 60 | Minutes between collections |

---

## Database Location
```
database/weather_data.db
```
Use [DB Browser for SQLite](https://sqlitebrowser.org/) to view the data visually.

---

## Analysis Queries
See `database/schema.sql` for all 5 analysis queries ready to copy-paste.

---

## Troubleshooting

**"No API key configured"**
→ Edit `config/settings.env`, add your real key.

**"City not found"**
→ Use English city names: "Bangalore" not "Bengaluru".

**Tests fail**
→ Run `pip install -r requirements.txt` first.

**No data after running pipeline**
→ Wait 15 min after creating your API key, then try again.
