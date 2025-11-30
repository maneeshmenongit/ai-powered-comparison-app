"""Data models for weather forecasts."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class DailyForecast:
    """Daily weather forecast data."""
    date: str  # YYYY-MM-DD format
    temp_high: float  # Celsius
    temp_low: float  # Celsius
    temp_avg: float  # Celsius
    condition: str  # e.g., "Sunny", "Rainy", "Cloudy"
    precipitation_chance: int  # Percentage (0-100)
    precipitation_mm: float  # Millimeters
    humidity: int  # Percentage (0-100)
    wind_speed: float  # km/h
    uv_index: Optional[int] = None  # 0-11+ scale


@dataclass
class WeatherForecast:
    """
    Standardized weather forecast from any provider.

    This model normalizes data from different weather APIs into a consistent format.
    """
    provider: str  # Name of the weather service (e.g., "Open-Meteo", "WeatherAPI")
    location: str  # Location name
    latitude: float
    longitude: float
    timezone: str
    current_temp: float  # Current temperature in Celsius
    current_condition: str  # Current weather condition
    daily_forecasts: List[DailyForecast]  # List of daily forecasts
    last_updated: datetime  # When this forecast was retrieved

    def __str__(self) -> str:
        """String representation for display."""
        return (
            f"{self.provider} - {self.location}\n"
            f"Current: {self.current_temp}°C, {self.current_condition}\n"
            f"Forecast: {len(self.daily_forecasts)} days"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider": self.provider,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "current_temp": self.current_temp,
            "current_condition": self.current_condition,
            "daily_forecasts": [
                {
                    "date": day.date,
                    "temp_high": day.temp_high,
                    "temp_low": day.temp_low,
                    "temp_avg": day.temp_avg,
                    "condition": day.condition,
                    "precipitation_chance": day.precipitation_chance,
                    "precipitation_mm": day.precipitation_mm,
                    "humidity": day.humidity,
                    "wind_speed": day.wind_speed,
                    "uv_index": day.uv_index,
                }
                for day in self.daily_forecasts
            ],
            "last_updated": self.last_updated.isoformat(),
        }
