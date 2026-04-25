---
name: weather
description: Daily weather reports using Open-Meteo API. Fetches current conditions and forecasts for any US zipcode.
version: 1.0.0
author: hermclaw
license: MIT
dependencies: []
metadata:
  hermes:
    tags: ["weather", "forecast", "open-meteo", "zipcode"]
---

# Weather Skill

Fetches daily weather reports using the free Open-Meteo API (no API key required).

## Features

- Current conditions + daily forecast
- Emoji weather icons
- Configurable zipcode (via arg or env var)
- Free, no API key needed

## Usage

```bash
# Auto-detect zipcode from context/memory, or prompt
python3 scripts/weather

# Specify zipcode
python3 scripts/weather 90210
python3 scripts/weather 11201

# Tomorrow's forecast
python3 scripts/weather 11201 tomorrow
```

## Configuration

Zipcode resolution (highest priority first):

1. **Command line argument:** `weather 90210`
2. **Environment variable:** `WEATHER_ZIPCODE=90210`
3. **Memory/context file:** Reads `~/.hermes-openrouter/memories/USER.md`
4. **Interactive prompt:** Asks user, then saves to context for future use

To set permanently, add to your memory:
```bash
echo "Location: 90210" >> ~/.hermes-openrouter/memories/USER.md
```

## Example Output

```
🌤️ **Weather Report** 🌤️
📍 Location: 90210
📅 Friday, April 25, 2026

**Current Conditions**
🌤️ Mainly clear
🌡️ 18.5°C / 65.3°F
💧 Humidity: 62%
💨 Wind: 12 km/h (7 mph)

**Today's Forecast**
⏫ High: 22.1°C / 71.8°F
⏬ Low: 14.3°C / 57.7°F
🌧️ Precipitation: 10%

☕ Have a great day!
```

## Data Sources

- **Geocoding:** OpenStreetMap Nominatim API (free)
- **Weather:** Open-Meteo API (free, no key required)

## Cron Integration

Run daily at 7:10 AM:

```bash
# cd to skill dir, then:
hermes cron create \
  --schedule "10 7 * * *" \
  --command "python3 scripts/weather YOUR_ZIPCODE" \
  --name "daily-weather"
```
