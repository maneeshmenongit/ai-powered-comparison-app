"""WeatherAPI.com client implementation."""

from typing import Dict, Any
from datetime import datetime
from api_clients.base_client import BaseAPIClient, APIError
from models.weather import WeatherForecast, DailyForecast


class WeatherAPIClient(BaseAPIClient):
    """
    Client for WeatherAPI.com.

    WeatherAPI.com offers a free tier with 1M calls/month.
    Sign up at: https://www.weatherapi.com/signup.aspx

    API Docs: https://www.weatherapi.com/docs/
    """

    def __init__(self, api_key: str):
        """
        Initialize WeatherAPI client.

        Args:
            api_key: Your WeatherAPI.com API key
        """
        super().__init__(
            base_url="https://api.weatherapi.com/v1",
            api_key=api_key,
            max_retries=3,
            timeout=10
        )

    def get_forecast(self, location: str, days: int = 7) -> WeatherForecast:
        """
        Get weather forecast from WeatherAPI.com.

        Args:
            location: Location name, coordinates, or postal code
            days: Number of days to forecast (1-10 for free tier)

        Returns:
            WeatherForecast object with normalized data

        Raises:
            APIError: If API request fails or API key is invalid
        """
        params = {
            "key": self.api_key,
            "q": location,
            "days": min(days, 10),  # Free tier supports max 10 days
            "aqi": "no",  # Air quality not needed
            "alerts": "no",  # Alerts not needed
        }

        data = self._make_request("/forecast.json", params)
        return self._parse_response(data)

    def _parse_response(self, data: Dict[str, Any]) -> WeatherForecast:
        """
        Parse WeatherAPI.com response into WeatherForecast model.

        Args:
            data: Raw API response

        Returns:
            WeatherForecast object
        """
        location_data = data["location"]
        current = data["current"]
        forecast_data = data["forecast"]["forecastday"]

        # Parse daily forecasts
        daily_forecasts = []
        for day_data in forecast_data:
            day = day_data["day"]
            daily_forecasts.append(DailyForecast(
                date=day_data["date"],
                temp_high=day["maxtemp_c"],
                temp_low=day["mintemp_c"],
                temp_avg=day["avgtemp_c"],
                condition=day["condition"]["text"],
                precipitation_chance=day.get("daily_chance_of_rain", 0),
                precipitation_mm=day["totalprecip_mm"],
                humidity=day["avghumidity"],
                wind_speed=day["maxwind_kph"],
                uv_index=int(day.get("uv", 0)),
            ))

        return WeatherForecast(
            provider="WeatherAPI.com",
            location=f"{location_data['name']}, {location_data['country']}",
            latitude=location_data["lat"],
            longitude=location_data["lon"],
            timezone=location_data["tz_id"],
            current_temp=current["temp_c"],
            current_condition=current["condition"]["text"],
            daily_forecasts=daily_forecasts,
            last_updated=datetime.now(),
        )
