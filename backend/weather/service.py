"""
Weather Service — Real Weather Data + Spray Safety (service.py)
================================================================
Uses Open-Meteo API (FREE, no API key, no signup required).

Spray Safety Rules (from FAO/WHO guidelines):
    - Wind > 15 km/h → UNSAFE (pesticide drift)
    - Rain probability > 60% → UNSAFE (wash-off)
    - Temperature > 35°C → UNSAFE (evaporation)
    - Temperature < 5°C → UNSAFE (ineffective)

Every response includes a micro-climate disclaimer.

Usage:
    from weather.service import WeatherService

    weather = WeatherService()
    data = weather.get_weather(41.0, 29.0)  # Istanbul
    print(data["condition"], data["safe_to_spray"])
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from core.retry import retry_with_backoff

log = get_logger("pestguard.weather")


# ============================================================================
# Micro-climate disclaimer — required on ALL weather outputs
# ============================================================================
WEATHER_DISCLAIMER = (
    "⚠️ Weather data reflects broad regional forecasts. "
    "Actual field conditions (fog, local frost, microclimates) may differ. "
    "Always verify conditions on-site before applying pesticides."
)


# ============================================================================
# Spray Safety Thresholds (based on FAO/WHO pesticide application guidelines)
# ============================================================================
SAFETY_THRESHOLDS = {
    "max_wind_kmh": 15.0,        # Above this → pesticide drift risk
    "max_rain_pct": 60.0,        # Above this → wash-off risk
    "max_temp_c": 35.0,          # Above this → evaporation/phytotoxicity
    "min_temp_c": 5.0,           # Below this → reduced efficacy
    "max_humidity_pct": 95.0,    # Above this → poor drying
    "min_humidity_pct": 30.0,    # Below this → excessive evaporation
}

# WMO Weather Codes → human-readable conditions
WMO_CODES = {
    0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing Rime Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    56: "Light Freezing Drizzle", 57: "Dense Freezing Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    66: "Light Freezing Rain", 67: "Heavy Freezing Rain",
    71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow",
    77: "Snow Grains",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
    85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Slight Hail", 99: "Thunderstorm with Heavy Hail",
}

# Weather codes that are automatically UNSAFE for spraying
UNSAFE_CODES = {
    45, 48,           # Fog
    51, 53, 55,       # Drizzle
    56, 57,           # Freezing drizzle
    61, 63, 65,       # Rain
    66, 67,           # Freezing rain
    71, 73, 75, 77,   # Snow
    80, 81, 82,       # Rain showers
    85, 86,           # Snow showers
    95, 96, 99,       # Thunderstorm
}


class WeatherService:
    """
    Weather data provider using Open-Meteo API (FREE, no key needed).
    Includes spray safety assessment based on FAO/WHO thresholds.
    """

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.is_real = True  # Open-Meteo always works (no key needed)
        log.info("Open-Meteo API ready (free, no key required) ✅")

    def get_weather(self, lat: float, lon: float) -> dict:
        """
        Get current weather data for a location.

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)

        Returns:
            dict with weather data + spray safety assessment
        """
        try:
            return self._get_real_weather_with_retry(lat, lon)
        except Exception as exc:
            log.warning(f"Weather API failed after retries: {exc}  →  using mock data")
            return self._get_mock_weather(lat, lon)

    @retry_with_backoff(max_attempts=3, base_delay=1.0, label="WeatherAPI")
    def _get_real_weather_with_retry(self, lat: float, lon: float) -> dict:
        """Fetch real weather from Open-Meteo API (retried up to 3×)."""
        return self._get_real_weather(lat, lon)

    def _get_real_weather(self, lat: float, lon: float) -> dict:
        """Core fetch — called by the retry wrapper."""

        response = requests.get(
            self.base_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "hourly": "relativehumidity_2m,precipitation_probability",
                "forecast_days": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        current = data["current_weather"]
        temperature = current["temperature"]
        wind_speed_kmh = current["windspeed"]
        weather_code = current["weathercode"]
        condition = WMO_CODES.get(weather_code, f"Code {weather_code}")

        # Get humidity and rain probability from hourly data (current hour)
        hourly = data.get("hourly", {})
        humidity_list = hourly.get("relativehumidity_2m", [])
        rain_prob_list = hourly.get("precipitation_probability", [])

        # Get current hour's index
        current_time = current.get("time", "")
        current_hour = int(current_time.split("T")[1].split(":")[0]) if "T" in current_time else 0

        humidity = humidity_list[current_hour] if current_hour < len(humidity_list) else 50
        rain_probability = rain_prob_list[current_hour] if current_hour < len(rain_prob_list) else 0

        # Get active alerts based on weather code
        alerts = []
        if weather_code in UNSAFE_CODES:
            alerts.append(f"Active weather: {condition}")

        # Fetch MGM (Turkish Meteorology) alerts for Turkey-region coordinates
        mgm_alerts = self._fetch_mgm_alerts(lat, lon)
        if mgm_alerts:
            alerts.extend(mgm_alerts)

        # Assess spray safety
        safety = self._assess_spray_safety(
            temperature=temperature,
            humidity=humidity,
            wind_speed_kmh=wind_speed_kmh,
            rain_probability=rain_probability,
            weather_code=weather_code,
            condition=condition,
            alerts=alerts,
        )

        return {
            "temperature": round(temperature, 1),
            "humidity": round(humidity),
            "wind_speed": round(wind_speed_kmh, 1),
            "rain_probability": rain_probability,
            "condition": condition,
            "safe_to_spray": safety["safe"],
            "alerts": safety["warnings"],
            "safety_details": safety["details"],
            "mgm_alerts": mgm_alerts if mgm_alerts else [],
            "lat": lat,
            "lon": lon,
            "timestamp": datetime.now().isoformat(),
            "is_mock": False,
            "disclaimer": WEATHER_DISCLAIMER,
        }

    def _fetch_mgm_alerts(self, lat: float, lon: float) -> list:
        """
        Fetch weather alerts from MGM (Meteoroloji Genel Müdürlüğü — Turkish Met Office).
        Only queries MGM for locations within Turkey's bounding box.

        Returns:
            List of alert strings, or empty list if not in Turkey or MGM unreachable.
        """
        # Turkey bounding box: lat 35.8–42.1, lon 25.6–44.8
        if not (35.8 <= lat <= 42.1 and 25.6 <= lon <= 44.8):
            return []

        try:
            # MGM public API for recent warnings
            mgm_url = "https://servis.mgm.gov.tr/web/merkezler/uyarilar"
            headers = {"Origin": "https://mgm.gov.tr"}
            resp = requests.get(mgm_url, headers=headers, timeout=5)

            if resp.status_code == 200:
                data = resp.json()
                alerts = []
                if isinstance(data, list):
                    for item in data[:5]:  # Max 5 alerts
                        desc = item.get("piAciklama", item.get("uyariTipiAdi", ""))
                        if desc:
                            alerts.append(f"🇹🇷 MGM: {desc}")
                if alerts:
                    log.info(f"MGM returned {len(alerts)} alert(s) for ({lat}, {lon})")
                return alerts
            else:
                log.debug(f"MGM API returned {resp.status_code}")
                return []

        except Exception as exc:
            log.debug(f"MGM alerts unavailable: {exc}")
            return []

    def _assess_spray_safety(
        self,
        temperature: float,
        humidity: float,
        wind_speed_kmh: float,
        rain_probability: float,
        weather_code: int,
        condition: str,
        alerts: list,
    ) -> dict:
        """
        Determine if conditions are safe for pesticide spraying.
        Checks multiple safety thresholds from FAO/WHO guidelines.
        """
        warnings = list(alerts)
        details = []
        safe = True

        # Check wind speed
        if wind_speed_kmh > SAFETY_THRESHOLDS["max_wind_kmh"]:
            safe = False
            warnings.append(f"High wind: {wind_speed_kmh:.0f} km/h (max {SAFETY_THRESHOLDS['max_wind_kmh']} km/h)")
            details.append("Wind causes pesticide drift — spray will not reach target.")
        else:
            details.append(f"Wind OK: {wind_speed_kmh:.0f} km/h")

        # Check rain probability
        if rain_probability > SAFETY_THRESHOLDS["max_rain_pct"]:
            safe = False
            warnings.append(f"Rain risk: {rain_probability}% (max {SAFETY_THRESHOLDS['max_rain_pct']}%)")
            details.append("Rain will wash pesticide off plants before it takes effect.")
        else:
            details.append(f"Rain risk OK: {rain_probability}%")

        # Check temperature
        if temperature > SAFETY_THRESHOLDS["max_temp_c"]:
            safe = False
            warnings.append(f"Too hot: {temperature}°C (max {SAFETY_THRESHOLDS['max_temp_c']}°C)")
            details.append("High temp causes rapid evaporation and potential crop burn.")
        elif temperature < SAFETY_THRESHOLDS["min_temp_c"]:
            safe = False
            warnings.append(f"Too cold: {temperature}°C (min {SAFETY_THRESHOLDS['min_temp_c']}°C)")
            details.append("Low temp reduces pesticide efficacy significantly.")
        else:
            details.append(f"Temperature OK: {temperature}°C")

        # Check humidity
        if humidity > SAFETY_THRESHOLDS["max_humidity_pct"]:
            warnings.append(f"Very high humidity: {humidity}% — slow drying")
            details.append("Pesticide may not dry properly on leaf surfaces.")
        elif humidity < SAFETY_THRESHOLDS["min_humidity_pct"]:
            warnings.append(f"Very low humidity: {humidity}% — rapid evaporation")
            details.append("Spray droplets may evaporate before reaching plants.")
        else:
            details.append(f"Humidity OK: {humidity}%")

        # Check weather code for unsafe conditions
        if weather_code in UNSAFE_CODES:
            safe = False
            if not any("Active weather" in w for w in warnings):
                warnings.append(f"Unsafe conditions: {condition}")

        return {"safe": safe, "warnings": warnings, "details": details}

    def _get_mock_weather(self, lat: float, lon: float) -> dict:
        """Fallback mock weather data."""
        import random

        scenarios = [
            {"temperature": 22, "humidity": 55, "wind_speed": 8,
             "rain_probability": 10, "condition": "Clear Sky"},
            {"temperature": 18, "humidity": 85, "wind_speed": 25,
             "rain_probability": 80, "condition": "Heavy Rain"},
            {"temperature": 28, "humidity": 45, "wind_speed": 5,
             "rain_probability": 5, "condition": "Partly Cloudy"},
        ]
        weather = random.choice(scenarios)

        safety = self._assess_spray_safety(
            temperature=weather["temperature"],
            humidity=weather["humidity"],
            wind_speed_kmh=weather["wind_speed"],
            rain_probability=weather["rain_probability"],
            weather_code=0,
            condition=weather["condition"],
            alerts=[],
        )

        weather.update({
            "safe_to_spray": safety["safe"],
            "alerts": safety["warnings"],
            "safety_details": safety["details"],
            "lat": lat, "lon": lon,
            "timestamp": datetime.now().isoformat(),
            "is_mock": True,
            "disclaimer": WEATHER_DISCLAIMER,
        })
        return weather


# ============================================================================
# Quick test
# ============================================================================
if __name__ == "__main__":
    print("Testing WeatherService (Open-Meteo)...\n")
    svc = WeatherService()

    # Test Istanbul
    result = svc.get_weather(41.0, 29.0)
    print(f"Temp: {result['temperature']}°C")
    print(f"Humidity: {result['humidity']}%")
    print(f"Wind: {result['wind_speed']} km/h")
    print(f"Rain: {result['rain_probability']}%")
    print(f"Condition: {result['condition']}")
    print(f"Safe to spray: {result['safe_to_spray']}")
    print(f"Warnings: {result['alerts']}")
    print(f"Details: {result['safety_details']}")
    print(f"Mock: {result['is_mock']}")
