"""Real Uber API client with OAuth 2.0 and Server Token support."""

import os
import logging
import requests
from typing import List, Optional
from datetime import datetime, timedelta
from ..models import RideEstimate


# Configure logging
logger = logging.getLogger(__name__)


class UberClient:
    """
    Real Uber API client for fetching ride estimates.

    Supports two authentication methods:
    1. OAuth 2.0 Client Credentials flow (recommended)
    2. Server Token (legacy)

    Uses Uber's Price Estimates API v1.2.
    Documentation: https://developer.uber.com/docs/riders/references/api/v1.2/estimates-price-get

    Examples:
        # OAuth 2.0 (recommended)
        client = UberClient(
            client_id="your_client_id",
            client_secret="your_client_secret"
        )

        # Server Token (legacy)
        client = UberClient(server_token="your_token")

        # From environment variables
        client = UberClient()  # Reads from .env
    """

    TOKEN_URL = "https://login.uber.com/oauth/v2/token"

    def __init__(
        self,
        server_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize Uber API client with authentication.

        Args:
            server_token: Uber server token (legacy auth)
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret

        Note:
            If no credentials provided, reads from environment:
            - UBER_SERVER_TOKEN (for server token auth)
            - UBER_CLIENT_ID and UBER_CLIENT_SECRET (for OAuth)

        Raises:
            ValueError: If no valid credentials provided
        """
        self.base_url = "https://api.uber.com/v1.2"

        # Try OAuth credentials first
        self.client_id = client_id or os.getenv("UBER_CLIENT_ID") or os.getenv("UBER_CLEINT_ID")  # Handle typo
        self.client_secret = client_secret or os.getenv("UBER_CLIENT_SECRET")

        # Try server token
        self.server_token = server_token or os.getenv("UBER_SERVER_TOKEN")

        # Determine authentication type
        if self.client_id and self.client_secret:
            self.auth_type = "client_credentials"
            self.access_token = None
            self.token_expiry = None
            self.headers = {
                "Accept-Language": "en_US",
                "Content-Type": "application/json"
            }
            logger.info("Initialized Uber client with OAuth 2.0 authentication")

        elif self.server_token:
            self.auth_type = "server_token"
            self.headers = {
                "Authorization": f"Token {self.server_token}",
                "Accept-Language": "en_US",
                "Content-Type": "application/json"
            }
            logger.info("Initialized Uber client with server token authentication")

        else:
            raise ValueError(
                "Uber authentication credentials required. Provide either:\n"
                "1. OAuth: client_id and client_secret (recommended)\n"
                "2. Server Token: server_token (legacy)\n"
                "Or set environment variables: UBER_CLIENT_ID + UBER_CLIENT_SECRET "
                "or UBER_SERVER_TOKEN"
            )

    def _get_access_token(self) -> None:
        """
        Get OAuth 2.0 access token using client credentials flow.

        Updates self.access_token and self.token_expiry.

        Raises:
            requests.exceptions.RequestException: If OAuth request fails
        """
        logger.info("Requesting new OAuth access token from Uber")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "request.read"
        }

        try:
            response = requests.post(
                self.TOKEN_URL,
                data=payload,
                timeout=10
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error_description", error_data.get("error", response.text))
                logger.error(f"OAuth token request failed: {response.status_code} - {error_msg}")
                raise requests.exceptions.RequestException(
                    f"OAuth authentication failed: {error_msg}"
                )

            data = response.json()

            self.access_token = data["access_token"]
            expires_in = data.get("expires_in", 2592000)  # Default 30 days
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            # Update headers with new access token
            self.headers["Authorization"] = f"Bearer {self.access_token}"

            logger.info(f"OAuth token obtained successfully, expires in {expires_in} seconds")

        except requests.exceptions.Timeout:
            logger.error("OAuth token request timed out")
            raise requests.exceptions.RequestException(
                "OAuth token request timed out. Please try again."
            )
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Uber OAuth endpoint")
            raise requests.exceptions.RequestException(
                "Could not connect to Uber OAuth service. Check internet connection."
            )
        except KeyError as e:
            logger.error(f"Unexpected OAuth response format: {e}")
            raise requests.exceptions.RequestException(
                f"Unexpected OAuth response format: missing {e}"
            )

    def _ensure_valid_token(self) -> None:
        """
        Ensure OAuth token is valid, refresh if expired.

        Only applies to OAuth authentication (client_credentials).
        For server_token auth, this is a no-op.
        """
        if self.auth_type != "client_credentials":
            return

        # Check if token exists and is not expired (60 second buffer)
        now = datetime.now()
        if self.access_token and self.token_expiry:
            time_until_expiry = (self.token_expiry - now).total_seconds()
            if time_until_expiry > 60:
                logger.debug(f"Token valid for {time_until_expiry:.0f} more seconds")
                return

        # Token expired or doesn't exist, get new one
        logger.info("Token expired or missing, refreshing...")
        self._get_access_token()

    def get_price_estimates(
        self,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float
    ) -> List[RideEstimate]:
        """
        Get ride price estimates from Uber API.

        Args:
            pickup_lat: Pickup latitude
            pickup_lng: Pickup longitude
            dropoff_lat: Dropoff latitude
            dropoff_lng: Dropoff longitude

        Returns:
            List of RideEstimate objects for available Uber products

        Raises:
            requests.exceptions.RequestException: If API call fails
            ValueError: If authentication fails or coordinates invalid
        """
        # Ensure valid OAuth token (no-op for server_token)
        self._ensure_valid_token()

        endpoint = f"{self.base_url}/estimates/price"

        params = {
            "start_latitude": pickup_lat,
            "start_longitude": pickup_lng,
            "end_latitude": dropoff_lat,
            "end_longitude": dropoff_lng
        }

        try:
            logger.debug(f"Fetching price estimates from {pickup_lat},{pickup_lng} to {dropoff_lat},{dropoff_lng}")

            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=10
            )

            # Check for errors
            if response.status_code == 401:
                error_msg = "Uber API authentication failed."
                if self.auth_type == "client_credentials":
                    error_msg += " OAuth token may be invalid or app lacks required scopes."
                else:
                    error_msg += " Server token may be invalid or expired."
                logger.error(f"{error_msg} Response: {response.text}")
                raise ValueError(error_msg)

            elif response.status_code == 422:
                logger.error(f"Invalid coordinates: {response.text}")
                raise ValueError(
                    "Invalid coordinates provided. "
                    "Please check latitude/longitude values."
                )

            elif response.status_code != 200:
                logger.error(f"Uber API error: {response.status_code} - {response.text}")
                raise requests.exceptions.RequestException(
                    f"Uber API error: {response.status_code} - {response.text}"
                )

            data = response.json()
            prices = data.get("prices", [])
            logger.info(f"Successfully retrieved {len(prices)} price estimates")

            # Parse response into RideEstimate objects
            estimates = []
            for product in prices:
                estimate = self._parse_uber_product(
                    product,
                    pickup_lat,
                    pickup_lng,
                    dropoff_lat,
                    dropoff_lng
                )
                estimates.append(estimate)

            return estimates

        except requests.exceptions.Timeout:
            logger.error("Uber API request timed out")
            raise requests.exceptions.RequestException(
                "Uber API request timed out. Please try again."
            )
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Uber API")
            raise requests.exceptions.RequestException(
                "Could not connect to Uber API. Please check your internet connection."
            )

    def get_time_estimates(
        self,
        pickup_lat: float,
        pickup_lng: float
    ) -> dict:
        """
        Get pickup time estimates for all Uber products at a location.

        Args:
            pickup_lat: Pickup latitude
            pickup_lng: Pickup longitude

        Returns:
            Dictionary mapping product names to pickup ETA in minutes

        Note:
            This uses the /estimates/time endpoint which is separate
            from price estimates.
        """
        # Ensure valid OAuth token (no-op for server_token)
        self._ensure_valid_token()

        endpoint = f"{self.base_url}/estimates/time"

        params = {
            "start_latitude": pickup_lat,
            "start_longitude": pickup_lng
        }

        try:
            logger.debug(f"Fetching time estimates for {pickup_lat},{pickup_lng}")

            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                logger.warning(f"Time estimates failed: {response.status_code}")
                return {}

            data = response.json()
            time_estimates = {}

            for product in data.get("times", []):
                display_name = product.get("display_name", product.get("localized_display_name"))
                estimate_seconds = product.get("estimate", 0)
                time_estimates[display_name] = estimate_seconds // 60  # Convert to minutes

            logger.info(f"Retrieved time estimates for {len(time_estimates)} products")
            return time_estimates

        except Exception as e:
            logger.warning(f"Time estimates request failed: {e}")
            return {}

    def _parse_uber_product(
        self,
        product: dict,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float
    ) -> RideEstimate:
        """
        Parse Uber API product response into RideEstimate.

        Args:
            product: Product data from Uber API
            pickup_lat: Pickup latitude
            pickup_lng: Pickup longitude
            dropoff_lat: Dropoff latitude
            dropoff_lng: Dropoff longitude

        Returns:
            RideEstimate object
        """
        # Extract price information
        price_estimate = self._parse_price(product.get("estimate"))
        price_low = self._parse_price(product.get("low_estimate"))
        price_high = self._parse_price(product.get("high_estimate"))

        # If we couldn't parse estimate, use midpoint of low/high
        if price_estimate == 0.0 and price_low > 0 and price_high > 0:
            price_estimate = (price_low + price_high) / 2

        # Extract surge multiplier
        surge_multiplier = product.get("surge_multiplier", 1.0)

        # Extract duration and distance
        duration_minutes = product.get("duration", 0) // 60  # Convert seconds to minutes
        distance_miles = product.get("distance", 0.0)

        # Get product display name
        display_name = product.get("display_name", product.get("localized_display_name", "Unknown"))

        return RideEstimate(
            provider="Uber",
            vehicle_type=display_name,
            price_low=price_low,
            price_high=price_high,
            price_estimate=price_estimate,
            currency=product.get("currency_code", "USD"),
            surge_multiplier=surge_multiplier,
            duration_minutes=duration_minutes,
            pickup_eta_minutes=0,  # Not provided in price estimates endpoint
            distance_miles=distance_miles,
            origin_coords=(pickup_lat, pickup_lng),
            destination_coords=(dropoff_lat, dropoff_lng),
            last_updated=datetime.now(),
            is_available=True
        )

    def _parse_price(self, price_str: str) -> float:
        """
        Parse price string to float.

        Uber API returns prices as formatted strings like "$40-50" or "$45".

        Args:
            price_str: Price string from API

        Returns:
            Price as float, or 0.0 if parsing fails
        """
        if not price_str:
            return 0.0

        try:
            # Remove currency symbols and whitespace
            price_str = str(price_str).replace("$", "").replace(",", "").strip()

            # Handle range format like "40-50"
            if "-" in price_str:
                low, high = price_str.split("-")
                return (float(low) + float(high)) / 2

            # Handle single value
            return float(price_str)

        except (ValueError, AttributeError):
            return 0.0


if __name__ == "__main__":
    """Example usage of UberClient."""
    from dotenv import load_dotenv
    load_dotenv()

    # Check available credentials
    server_token = os.getenv("UBER_SERVER_TOKEN")
    client_id = os.getenv("UBER_CLIENT_ID") or os.getenv("UBER_CLEINT_ID")
    client_secret = os.getenv("UBER_CLIENT_SECRET")

    if not (server_token or (client_id and client_secret)):
        print("❌ ERROR: No Uber credentials found")
        print("\nPlease set one of:")
        print("  Option 1 (OAuth 2.0 - Recommended):")
        print("    UBER_CLIENT_ID=your_client_id")
        print("    UBER_CLIENT_SECRET=your_client_secret")
        print("\n  Option 2 (Server Token - Legacy):")
        print("    UBER_SERVER_TOKEN=your_server_token")
        exit(1)

    # Initialize client with available credentials
    if client_id and client_secret:
        print("✓ Using OAuth 2.0 authentication")
        client = UberClient(client_id=client_id, client_secret=client_secret)
    else:
        print("✓ Using server token authentication")
        client = UberClient(server_token=server_token)

    # Test with Times Square to JFK
    print("\n📍 Testing: Times Square → JFK Airport")
    try:
        estimates = client.get_price_estimates(
            pickup_lat=40.7580,
            pickup_lng=-73.9855,
            dropoff_lat=40.6413,
            dropoff_lng=-73.7781
        )

        print(f"\n✅ Success! Retrieved {len(estimates)} estimates:\n")
        for est in estimates:
            surge = f" 🔥 {est.surge_multiplier}x" if est.surge_multiplier > 1.0 else ""
            print(f"{est.vehicle_type}: ${est.price_estimate:.2f}{surge} "
                  f"({est.distance_miles:.1f} mi, {est.duration_minutes} min)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
