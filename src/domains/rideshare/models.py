"""Data models for rideshare estimates."""

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class RideQuery:
    """
    User query for ride-share comparison.

    Captures the user's intent for comparing ride options across providers.
    """
    origin: str  # Starting location (address or place name)
    destination: str  # Ending location (address or place name)
    providers: List[str]  # List of providers to compare (e.g., ["uber", "lyft", "via"])
    vehicle_type: str = "standard"  # Preferred vehicle type
    when: str = "now"  # When to request the ride (e.g., "now", "in 30 minutes")
    passengers: int = 1  # Number of passengers


@dataclass
class RideEstimate:
    """
    Standardized ride estimate from any provider.

    This model normalizes data from different rideshare APIs into a consistent format.
    """
    provider: str  # Provider name (e.g., "Uber", "Lyft")
    vehicle_type: str  # Vehicle type (e.g., "UberX", "Lyft", "Via Shared")
    price_low: float  # Minimum price estimate in currency
    price_high: float  # Maximum price estimate in currency
    price_estimate: float  # Average/display price in currency
    currency: str = "USD"  # Currency code
    surge_multiplier: float = 1.0  # Surge pricing multiplier (1.0 = no surge)
    duration_minutes: int = 0  # Estimated trip duration in minutes
    pickup_eta_minutes: int = 0  # Time until driver pickup in minutes
    distance_miles: float = 0.0  # Trip distance in miles
    origin_coords: tuple[float, float] = (0.0, 0.0)  # Origin (latitude, longitude)
    destination_coords: tuple[float, float] = (0.0, 0.0)  # Destination (latitude, longitude)
    last_updated: datetime = None  # When this estimate was retrieved
    is_available: bool = True  # Whether this ride option is currently available

    def __post_init__(self):
        """Set last_updated to now if not provided."""
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def __str__(self) -> str:
        """String representation for display."""
        surge_text = f" (surge {self.surge_multiplier}x)" if self.surge_multiplier > 1.0 else ""
        return (
            f"{self.provider} - {self.vehicle_type}\n"
            f"Price: ${self.price_estimate:.2f}{surge_text} ({self.currency})\n"
            f"Duration: {self.duration_minutes} min, Distance: {self.distance_miles} mi\n"
            f"Pickup ETA: {self.pickup_eta_minutes} min"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider": self.provider,
            "vehicle_type": self.vehicle_type,
            "price_low": self.price_low,
            "price_high": self.price_high,
            "price_estimate": self.price_estimate,
            "currency": self.currency,
            "surge_multiplier": self.surge_multiplier,
            "duration_minutes": self.duration_minutes,
            "pickup_eta_minutes": self.pickup_eta_minutes,
            "distance_miles": self.distance_miles,
            "origin_coords": self.origin_coords,
            "destination_coords": self.destination_coords,
            "last_updated": self.last_updated.isoformat(),
            "is_available": self.is_available,
        }
