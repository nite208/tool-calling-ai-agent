import logging
from typing import Any

import requests

from src.config import REQUEST_TIMEOUT, USER_AGENT
from src.exceptions import WeatherError

logger = logging.getLogger(__name__)

_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_CURRENT_VARIABLES = (
    "temperature_2m,apparent_temperature,relative_humidity_2m,"
    "weather_code,wind_speed_10m,wind_direction_10m,precipitation"
)
_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def _geocode(city: str) -> tuple[float, float, str]:
    try:
        response = requests.get(
            _GEOCODING_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise WeatherError(f"Geocoding request timed out for city: {city!r}") from exc
    except requests.RequestException as exc:
        raise WeatherError(f"Geocoding network error: {exc}") from exc

    data = response.json()
    results = data.get("results")
    if not results:
        raise WeatherError(f"City not found: {city!r}")

    location = results[0]
    label = f"{location['name']}, {location.get('country', '')}"
    return float(location["latitude"]), float(location["longitude"]), label


def _fetch_forecast(latitude: float, longitude: float) -> dict[str, Any]:
    try:
        response = requests.get(
            _FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": _CURRENT_VARIABLES,
                "timezone": "auto",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise WeatherError("Forecast request timed out.") from exc
    except requests.RequestException as exc:
        raise WeatherError(f"Forecast network error: {exc}") from exc

    return response.json()


def get_weather(city: str) -> str:
    logger.info("Weather lookup city=%r", city)
    latitude, longitude, location_label = _geocode(city)
    data = _fetch_forecast(latitude, longitude)

    current = data.get("current", {})
    units = data.get("current_units", {})

    temperature = current.get("temperature_2m")
    apparent = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind_speed = current.get("wind_speed_10m")
    wind_direction = current.get("wind_direction_10m")
    precipitation = current.get("precipitation")
    weather_code = current.get("weather_code", -1)
    condition = _WMO_DESCRIPTIONS.get(int(weather_code), f"WMO code {weather_code}")

    temp_unit = units.get("temperature_2m", "°C")
    wind_unit = units.get("wind_speed_10m", "km/h")
    precip_unit = units.get("precipitation", "mm")

    result = (
        f"Location: {location_label}\n"
        f"Condition: {condition}\n"
        f"Temperature: {temperature}{temp_unit} (feels like {apparent}{temp_unit})\n"
        f"Humidity: {humidity}%\n"
        f"Wind: {wind_speed}{wind_unit} at {wind_direction}°\n"
        f"Precipitation: {precipitation}{precip_unit}"
    )
    logger.info("Weather result for %r: %s", city, result)
    return result


SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Get the current weather conditions for a city. "
            "Use this whenever the user asks about weather, temperature, or climate in a location."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'London' or 'New York'.",
                }
            },
            "required": ["city"],
        },
    },
}


def handle(arguments: dict[str, Any]) -> str:
    city = arguments.get("city", "")
    if not city.strip():
        return "error: city name is required."
    try:
        return get_weather(city)
    except WeatherError as exc:
        return f"error: {exc}"
