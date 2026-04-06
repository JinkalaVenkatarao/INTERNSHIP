# ============================================================
#  src/api_client.py
#  All communication with the OpenWeatherMap API.
#  Handles retries, error codes, and response parsing.
# ============================================================

import time
import requests
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from src.config import API_KEY, BASE_URL, get_logger

logger = get_logger("api_client")

MAX_RETRIES    = 3
RETRY_DELAY_S  = 2
REQUEST_TIMEOUT = 10


# ===========================================================
# CORE HTTP CALL
# ===========================================================

def _get(endpoint: str, params: dict) -> Optional[dict]:
    """
    Make a GET request with automatic retries.
    Returns parsed JSON on success, None on failure.
    """
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        logger.error("No API key configured. Edit config/settings.env")
        return None

    params["appid"] = API_KEY
    params["units"] = "metric"      # Celsius
    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params,
                                    timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 401:
                logger.error("Bad API key — check config/settings.env")
                return None          # No retry — key is wrong

            elif response.status_code == 404:
                logger.warning(f"City not found: {params.get('q', '?')}")
                return None          # No retry — city doesn't exist

            elif response.status_code == 429:
                logger.warning("Rate limit hit — waiting 60s")
                time.sleep(60)

            else:
                logger.warning(f"HTTP {response.status_code} on attempt {attempt}")

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout — attempt {attempt}/{MAX_RETRIES}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"No connection — attempt {attempt}/{MAX_RETRIES}")
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_S * attempt)   # 2s, 4s

    logger.error(f"All {MAX_RETRIES} attempts failed")
    return None


# ===========================================================
# PUBLIC API
# ===========================================================

def fetch_weather_data(city: str) -> Optional[dict]:
    """
    Fetch current weather for one city name.
    Returns a clean flat dict ready for the database, or None.
    """
    raw = _get("weather", {"q": city})
    if raw is None:
        return None
    return _parse(raw)


def fetch_multiple_cities(cities: list) -> list:
    """
    Fetch weather for a list of city names.
    Returns a list of successful results (failures are skipped).
    """
    results = []
    for city in cities:
        data = fetch_weather_data(city)
        if data:
            results.append(data)
            logger.info(
                f"  {city}: {data['temperature']}°C, "
                f"{data['humidity']}% humidity, {data['condition']}"
            )
        else:
            logger.warning(f"  Skipping {city} — no data")
        time.sleep(0.4)     # avoid hammering the API

    logger.info(f"Fetched {len(results)}/{len(cities)} cities successfully")
    return results


def test_api_connection() -> bool:
    """Quick connectivity test. Returns True if API responds."""
    logger.info("Testing API connection...")
    result = fetch_weather_data("London")
    if result:
        logger.info(f"API OK — London: {result['temperature']}°C")
        return True
    logger.error("API connection test FAILED")
    return False


# ===========================================================
# RESPONSE PARSER
# ===========================================================

def _parse(raw: dict) -> dict:
    """
    Convert nested OpenWeatherMap JSON into a flat dict.

    Raw API structure (abbreviated):
    {
      "name": "Mumbai",
      "main": {"temp": 28.5, "humidity": 65, "pressure": 1012, ...},
      "wind": {"speed": 3.2, "deg": 220},
      "weather": [{"main": "Clear", "description": "clear sky"}],
      "clouds": {"all": 10},
      "rain": {"1h": 0},
      "coord": {"lat": 19.07, "lon": 72.87},
      "sys":  {"country": "IN"},
      "dt": 1705312800         ← Unix timestamp
    }
    """
    main    = raw.get("main",    {})
    wind    = raw.get("wind",    {})
    weather = raw.get("weather", [{}])
    clouds  = raw.get("clouds",  {})
    rain    = raw.get("rain",    {})
    coord   = raw.get("coord",   {})
    sys_    = raw.get("sys",     {})

    # Convert Unix timestamp → ISO string
    unix_ts   = raw.get("dt", time.time())
    timestamp = datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()

    return {
        # City info
        "city":         raw.get("name", "Unknown"),
        "country":      sys_.get("country", ""),
        "latitude":     coord.get("lat"),
        "longitude":    coord.get("lon"),
        "timezone":     str(raw.get("timezone", "")),

        # Time
        "timestamp":    timestamp,

        # Temperature
        "temperature":  main.get("temp"),
        "feels_like":   main.get("feels_like"),
        "temp_min":     main.get("temp_min"),
        "temp_max":     main.get("temp_max"),

        # Atmosphere
        "humidity":     main.get("humidity"),
        "pressure":     main.get("pressure"),
        "visibility":   raw.get("visibility"),

        # Wind
        "wind_speed":   wind.get("speed"),
        "wind_deg":     wind.get("deg"),

        # Sky
        "weather_main": weather[0].get("main"),
        "condition":    weather[0].get("description"),
        "clouds":       clouds.get("all"),

        # Precipitation
        "rain_1h":      rain.get("1h", 0.0),

        # Keep the original so nothing is ever lost
        "raw": raw,
    }
