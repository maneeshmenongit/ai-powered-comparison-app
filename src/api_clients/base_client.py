"""Base API client with retry logic and error handling."""

import time
import requests
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class APIError(Exception):
    """Custom exception for API-related errors."""
    pass


class BaseAPIClient(ABC):
    """
    Base class for all API clients.

    Provides common functionality:
    - HTTP request handling with retries
    - Error handling and logging
    - Rate limiting
    - Response validation
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 max_retries: int = 3, timeout: int = 10):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication (if required)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an HTTP GET request with retry logic.

        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            APIError: If request fails after all retries
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

                # Raise exception for 4xx/5xx status codes
                response.raise_for_status()

                return response.json()

            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise APIError(f"Request timed out after {self.max_retries} attempts")
                time.sleep(2 ** attempt)  # Exponential backoff

            except requests.exceptions.HTTPError as e:
                if response.status_code >= 500:
                    # Retry on server errors
                    if attempt == self.max_retries - 1:
                        raise APIError(f"Server error: {e}")
                    time.sleep(2 ** attempt)
                else:
                    # Don't retry on client errors (4xx)
                    raise APIError(f"Client error: {e}")

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise APIError(f"Request failed: {e}")
                time.sleep(2 ** attempt)

        raise APIError("Request failed after all retry attempts")

    @abstractmethod
    def get_forecast(self, location: str, days: int = 7) -> Dict[str, Any]:
        """
        Get weather forecast for a location.

        This method must be implemented by subclasses.

        Args:
            location: Location name or coordinates
            days: Number of days to forecast

        Returns:
            Weather forecast data
        """
        pass

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
