"""Shared geocoding service for converting location names to coordinates."""

import requests
from functools import lru_cache
from typing import Tuple


class GeocodingService:
    """
    Geocoding service using Nominatim (OpenStreetMap) API.

    Converts human-readable location names into geographic coordinates.
    Results are cached to minimize API calls and improve performance.

    Example:
        geocoder = GeocodingService()
        lat, lon, name = geocoder.geocode("Times Square")
        # Returns: (40.758, -73.985, "Times Square, New York, USA")
    """

    def __init__(self):
        """
        Initialize the geocoding service.

        Nominatim is free and doesn't require an API key.
        """
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "TouristCompanionApp/1.0"  # Required by Nominatim
        }

    @lru_cache(maxsize=1000)
    def geocode(self, location: str) -> Tuple[float, float, str]:
        """
        Convert a location name to coordinates.

        Args:
            location: Location name (e.g., "Times Square", "JFK Airport")

        Returns:
            Tuple of (latitude, longitude, formatted_address)

        Raises:
            ValueError: If location cannot be found

        Example:
            lat, lon, name = geocoder.geocode("Central Park")
        """
        return self._geocode_nominatim(location)

    def _geocode_nominatim(self, location: str) -> Tuple[float, float, str]:
        """
        Make the actual API call to Nominatim.

        Args:
            location: Location name to geocode

        Returns:
            Tuple of (latitude, longitude, formatted_address)

        Raises:
            ValueError: If location not found or API error occurs
        """
        params = {
            "q": location,
            "format": "json",
            "limit": 1
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()

            if not results or len(results) == 0:
                raise ValueError(f"Location not found: {location}")

            result = results[0]
            latitude = float(result["lat"])
            longitude = float(result["lon"])
            formatted_address = result.get("display_name", location)

            return latitude, longitude, formatted_address

        except requests.exceptions.Timeout:
            raise ValueError(f"Geocoding request timed out for: {location}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Geocoding API error for {location}: {e}")
        except (KeyError, ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse geocoding response for {location}: {e}")
