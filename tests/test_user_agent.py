from unittest.mock import MagicMock, patch

import src.tools.wikipedia as wikipedia_module
import src.tools.weather as weather_module
from src.config import USER_AGENT


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.ok = status_code < 400
    mock.json.return_value = json_data
    return mock


def test_wikipedia_sends_user_agent():
    summary_response = _mock_response({
        "title": "Python",
        "extract": "Python is a programming language.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Python"}},
    })

    with patch("src.tools.wikipedia.requests.get", return_value=summary_response) as mock_get:
        wikipedia_module.search_wikipedia("Python")

    _assert_user_agent_header(mock_get)


def test_weather_geocode_sends_user_agent():
    geocode_response = _mock_response({
        "results": [{"name": "London", "country": "UK", "latitude": 51.5, "longitude": -0.1}]
    })
    forecast_response = _mock_response({
        "current": {
            "temperature_2m": 15.0,
            "apparent_temperature": 13.0,
            "relative_humidity_2m": 70,
            "wind_speed_10m": 10.0,
            "wind_direction_10m": 180,
            "precipitation": 0.0,
            "weather_code": 1,
        },
        "current_units": {
            "temperature_2m": "°C",
            "wind_speed_10m": "km/h",
            "precipitation": "mm",
        },
    })

    with patch(
        "src.tools.weather.requests.get", side_effect=[geocode_response, forecast_response]
    ) as mock_get:
        weather_module.get_weather("London")

    for call in mock_get.call_args_list:
        headers = call.kwargs.get("headers", {})
        assert "User-Agent" in headers, "User-Agent missing from weather request"
        assert headers["User-Agent"] == USER_AGENT


def _assert_user_agent_header(mock_get: MagicMock) -> None:
    call_kwargs = mock_get.call_args.kwargs
    headers = call_kwargs.get("headers", {})
    assert "User-Agent" in headers, "User-Agent header missing from request"
    assert headers["User-Agent"] == USER_AGENT
