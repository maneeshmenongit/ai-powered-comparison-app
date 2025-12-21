"""Mock Lyft API client for testing without real API calls."""

import random
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import List
from ..models import RideEstimate


class MockLyftClient:
    """
    Simulates Lyft API responses with realistic pricing.

    Generates price estimates for multiple vehicle types based on
    distance, time, and primetime pricing. No API key required.

    Example:
        client = MockLyftClient()
        estimates = client.get_price_estimates(
            pickup_lat=40.7580,
            pickup_lng=-73.9855,
            dropoff_lat=40.6413,
            dropoff_lng=-73.7781
        )
    """

    def __init__(self, deterministic: bool = False, rate_limiter=None):
        """
        Initialize mock Lyft client.

        Args:
            deterministic: If True, uses fixed seed for reproducible results
            rate_limiter: Optional rate limiter service
        """
        self.rate_limiter = rate_limiter

        # Pricing parameters (slightly different from Uber)
        self.base_fare = 4.50
        self.per_mile = 2.20
        self.per_minute = 0.28
        self.min_fare = 7.50

        # Vehicle type multipliers (Lyft's vehicle types)
        self.vehicle_multipliers = {
            "Lyft": 1.0,
            "Lyft XL": 1.4,
            "Lyft Lux": 1.8
        }

        # Primetime pricing (Lyft's version of surge)
        self.primetime_chance = 0.15  # 15% chance of primetime
        self.primetime_min = 1.0
        self.primetime_max = 1.8

        if deterministic:
            random.seed(42)

    def get_price_estimates(
        self,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float
    ) -> List[RideEstimate]:
        """
        Get mock price estimates for all Lyft vehicle types.

        Args:
            pickup_lat: Pickup latitude
            pickup_lng: Pickup longitude
            dropoff_lat: Dropoff latitude
            dropoff_lng: Dropoff longitude

        Returns:
            List of RideEstimate objects for each vehicle type

        Example:
            estimates = client.get_price_estimates(40.758, -73.986, 40.641, -73.778)
        """
        # Rate limit check (if limiter provided)
        if self.rate_limiter:
            self.rate_limiter.acquire('lyft')

        # Calculate trip distance and duration
        distance_miles = self._haversine_distance(
            pickup_lat, pickup_lng,
            dropoff_lat, dropoff_lng
        )
        duration_minutes = self._calculate_duration(distance_miles)

        # Determine primetime multiplier
        primetime = self._get_primetime_multiplier()

        # Generate estimates for each vehicle type
        estimates = []
        for vehicle_type, multiplier in self.vehicle_multipliers.items():
            estimate = self._create_estimate(
                vehicle_type=vehicle_type,
                multiplier=multiplier,
                distance_miles=distance_miles,
                duration_minutes=duration_minutes,
                primetime=primetime,
                pickup_coords=(pickup_lat, pickup_lng),
                dropoff_coords=(dropoff_lat, dropoff_lng)
            )
            estimates.append(estimate)

        return estimates

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance in miles between two coordinates using Haversine formula.

        Args:
            lat1: Origin latitude
            lon1: Origin longitude
            lat2: Destination latitude
            lon2: Destination longitude

        Returns:
            Distance in miles
        """
        R = 3959  # Earth's radius in miles

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _calculate_duration(self, distance_miles: float) -> int:
        """
        Calculate estimated trip duration.

        Args:
            distance_miles: Trip distance in miles

        Returns:
            Duration in minutes
        """
        avg_speed_mph = 30  # Average city speed
        duration = (distance_miles / avg_speed_mph) * 60
        return max(int(duration), 5)  # Minimum 5 minutes

    def _get_primetime_multiplier(self) -> float:
        """
        Determine primetime pricing multiplier (Lyft's surge pricing).

        Returns:
            Primetime multiplier (1.0 = no primetime, 1.8 = 1.8x primetime)
        """
        if random.random() < self.primetime_chance:
            # Apply primetime pricing
            return round(random.uniform(self.primetime_min, self.primetime_max), 1)
        return 1.0

    def _calculate_price(
        self,
        distance_miles: float,
        duration_minutes: int,
        multiplier: float,
        primetime: float
    ) -> tuple[float, float, float]:
        """
        Calculate price estimate with range.

        Args:
            distance_miles: Trip distance
            duration_minutes: Trip duration
            multiplier: Vehicle type multiplier
            primetime: Primetime pricing multiplier

        Returns:
            Tuple of (price_low, price_high, price_estimate)
        """
        # Base calculation
        base_price = (
            self.base_fare +
            (distance_miles * self.per_mile) +
            (duration_minutes * self.per_minute)
        )

        # Apply vehicle type multiplier
        base_price *= multiplier

        # Apply primetime pricing
        base_price *= primetime

        # Ensure minimum fare
        base_price = max(base_price, self.min_fare)

        # Add variance for price range (±10%)
        price_estimate = round(base_price, 2)
        price_low = round(base_price * 0.9, 2)
        price_high = round(base_price * 1.1, 2)

        return price_low, price_high, price_estimate

    def _calculate_eta(self) -> int:
        """
        Calculate pickup ETA.

        Returns:
            ETA in minutes (random 3-8 minutes)
        """
        return random.randint(3, 8)

    def _create_estimate(
        self,
        vehicle_type: str,
        multiplier: float,
        distance_miles: float,
        duration_minutes: int,
        primetime: float,
        pickup_coords: tuple[float, float],
        dropoff_coords: tuple[float, float]
    ) -> RideEstimate:
        """
        Create a RideEstimate object.

        Args:
            vehicle_type: Type of vehicle (e.g., "Lyft", "Lyft XL")
            multiplier: Price multiplier for vehicle type
            distance_miles: Trip distance
            duration_minutes: Trip duration
            primetime: Primetime pricing multiplier
            pickup_coords: Pickup (lat, lon)
            dropoff_coords: Dropoff (lat, lon)

        Returns:
            RideEstimate object
        """
        price_low, price_high, price_estimate = self._calculate_price(
            distance_miles, duration_minutes, multiplier, primetime
        )

        return RideEstimate(
            provider="Lyft",
            vehicle_type=vehicle_type,
            price_low=price_low,
            price_high=price_high,
            price_estimate=price_estimate,
            currency="USD",
            surge_multiplier=primetime,  # Lyft calls it primetime, but use same field
            duration_minutes=duration_minutes,
            pickup_eta_minutes=self._calculate_eta(),
            distance_miles=round(distance_miles, 2),
            origin_coords=pickup_coords,
            destination_coords=dropoff_coords,
            last_updated=datetime.now(),
            is_available=True
        )
