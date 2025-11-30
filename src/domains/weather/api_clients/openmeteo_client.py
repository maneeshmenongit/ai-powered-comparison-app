"""Open-Meteo API client implementation."""

from typing import Dict, Any
from datetime import datetime
from api_clients.base_client import BaseAPIClient, APIError
from models.weather import WeatherForecast, DailyForecast


class OpenMeteoClient(BaseAPIClient):
    """
    Client for Open-Meteo weather API.

    Open-Meteo is a free weather API that doesn't require an API key.
    Perfect for learning and development!

    API Docs: https://open-meteo.com/en/docs
    """

    def __init__(self):
        """Initialize Open-Meteo client."""
        super().__init__(
            base_url="https://api.open-meteo.com/v1",
            api_key=None,  # No API key required!
            max_retries=3,
            timeout=10
        )
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"

    def _geocode_location(self, location: str) -> tuple[float, float, str]:
        """
        Convert location name to coordinates.

        Args:
            location: Location name (e.g., "New York", "London")

        Returns:
            Tuple of (latitude, longitude, full_location_name)

        Raises:
            APIError: If location cannot be found
        """
        try:
            response = self.session.get(
                f"{self.geocoding_url}/search",
                params={"name": location, "count": 1, "language": "en", "format": "json"},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                raise APIError(f"Location not found: {location}")

            result = data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            name = result["name"]
            country = result.get("country", "")
            full_name = f"{name}, {country}" if country else name

            return lat, lon, full_name

        except Exception as e:
            raise APIError(f"Geocoding failed: {e}")

    def get_forecast(self, location: str, days: int = 7) -> WeatherForecast:
        """
        Get weather forecast from Open-Meteo.

        Args:
            location: Location name or "lat,lon" coordinates
            days: Number of days to forecast (1-16)

        Returns:
            WeatherForecast object with normalized data

        Raises:
            APIError: If API request fails
        """
        # Handle coordinates vs location name
        if "," in location and all(part.replace(".", "").replace("-", "").isdigit()
                                   for part in location.split(",")):
            # Already coordinates
            lat, lon = map(float, location.split(","))
            full_location = f"{lat}, {lon}"
        else:
            # Need to geocode
            lat, lon, full_location = self._geocode_location(location)

        # Request weather data
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "weathercode",
                "precipitation_sum",
                "precipitation_probability_max",
                "windspeed_10m_max",
                "uv_index_max",
            ],
            "current_weather": True,
            "timezone": "auto",
            "forecast_days": min(days, 16),  # API supports max 16 days
        }

        data = self._make_request("/forecast", params)

        # Parse response
        return self._parse_response(data, full_location)

    def _parse_response(self, data: Dict[str, Any], location: str) -> WeatherForecast:
        """
        Parse Open-Meteo API response into WeatherForecast model.

        Args:
            data: Raw API response
            location: Location name

        Returns:
            WeatherForecast object
        """
        current = data["current_weather"]
        daily = data["daily"]

        # Parse daily forecasts
        daily_forecasts = []
        for i in range(len(daily["time"])):
            daily_forecasts.append(DailyForecast(
                date=daily["time"][i],
                temp_high=daily["temperature_2m_max"][i],
                temp_low=daily["temperature_2m_min"][i],
                temp_avg=daily["temperature_2m_mean"][i],
                condition=self._weathercode_to_condition(daily["weathercode"][i]),
                precipitation_chance=daily.get("precipitation_probability_max", [0])[i],
                precipitation_mm=daily["precipitation_sum"][i],
                humidity=0,  # Open-Meteo doesn't provide humidity in free tier
                wind_speed=daily["windspeed_10m_max"][i],
                uv_index=int(daily.get("uv_index_max", [0])[i]) if daily.get("uv_index_max") else None,
            ))

        return WeatherForecast(
            provider="Open-Meteo",
            location=location,
            latitude=data["latitude"],
            longitude=data["longitude"],
            timezone=data["timezone"],
            current_temp=current["temperature"],
            current_condition=self._weathercode_to_condition(current["weathercode"]),
            daily_forecasts=daily_forecasts,
            last_updated=datetime.now(),
        )

    @staticmethod
    def _weathercode_to_condition(code: int) -> str:
        """
        Convert WMO weather code to human-readable condition.

        WMO Weather interpretation codes (WW):
        https://open-meteo.com/en/docs
        """
        conditions = {
            0: "Clear",
            1: "Mainly Clear",
            2: "Partly Cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light Drizzle",
            53: "Moderate Drizzle",
            55: "Heavy Drizzle",
            61: "Light Rain",
            63: "Moderate Rain",
            65: "Heavy Rain",
            71: "Light Snow",
            73: "Moderate Snow",
            75: "Heavy Snow",
            77: "Snow Grains",
            80: "Light Showers",
            81: "Moderate Showers",
            82: "Heavy Showers",
            85: "Light Snow Showers",
            86: "Heavy Snow Showers",
            95: "Thunderstorm",
            96: "Thunderstorm with Hail",
            99: "Thunderstorm with Hail",
        }
        return conditions.get(code, "Unknown")
