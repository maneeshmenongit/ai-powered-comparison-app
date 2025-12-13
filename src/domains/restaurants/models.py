"""src/domains/restaurants/models.py

Data models for restaurant domain.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class RestaurantQuery:
    """
    Represents a restaurant search query.

    Attributes:
        cuisine: Type of cuisine (Italian, Chinese, etc.)
        location: Where to search (address, landmark, coordinates)
        price_range: $ to $$$$ (1-4 dollar signs)
        rating_min: Minimum rating (0-5 stars)
        distance_miles: Maximum distance to search (miles)
        party_size: Number of people (optional)
        dietary_restrictions: List of restrictions (vegetarian, vegan, etc.)
        open_now: Whether restaurant must be open now
    """
    cuisine: Optional[str] = None
    location: str = ""
    price_range: Optional[str] = None  # $, $$, $$$, $$$$
    rating_min: float = 0.0
    distance_miles: float = 5.0
    party_size: Optional[int] = None
    dietary_restrictions: List[str] = field(default_factory=list)
    open_now: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for caching/serialization."""
        return {
            'cuisine': self.cuisine,
            'location': self.location,
            'price_range': self.price_range,
            'rating_min': self.rating_min,
            'distance_miles': self.distance_miles,
            'party_size': self.party_size,
            'dietary_restrictions': self.dietary_restrictions,
            'open_now': self.open_now
        }

    def __repr__(self) -> str:
        parts = []
        if self.cuisine:
            parts.append(f"{self.cuisine}")
        parts.append(f"near {self.location}")
        if self.price_range:
            parts.append(f"({self.price_range})")
        return f"RestaurantQuery({', '.join(parts)})"


@dataclass
class Restaurant:
    """
    Represents a restaurant with details from providers.

    Attributes:
        provider: Source (yelp, google_places)
        name: Restaurant name
        cuisine: Type of cuisine
        rating: Star rating (0-5)
        review_count: Number of reviews
        price_range: $ to $$$$
        address: Full address
        distance_miles: Distance from search location
        phone: Phone number
        website: Website URL
        hours: Operating hours
        is_open_now: Currently open
        coordinates: (lat, lon) tuple
        image_url: Photo URL
        categories: List of category tags
        last_updated: When data was fetched
    """
    provider: str
    name: str
    cuisine: Optional[str] = None
    rating: float = 0.0
    review_count: int = 0
    price_range: Optional[str] = None
    address: str = ""
    distance_miles: float = 0.0
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    is_open_now: bool = False
    coordinates: Optional[tuple] = None  # (lat, lon)
    image_url: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for caching/serialization."""
        return {
            'provider': self.provider,
            'name': self.name,
            'cuisine': self.cuisine,
            'rating': self.rating,
            'review_count': self.review_count,
            'price_range': self.price_range,
            'address': self.address,
            'distance_miles': self.distance_miles,
            'phone': self.phone,
            'website': self.website,
            'hours': self.hours,
            'is_open_now': self.is_open_now,
            'coordinates': self.coordinates,
            'image_url': self.image_url,
            'categories': self.categories,
            'last_updated': self.last_updated
        }

    def __repr__(self) -> str:
        stars = "⭐" * int(self.rating)
        return f"{self.name} ({self.provider}) - {stars} {self.rating}/5 - {self.price_range or 'N/A'}"


# Helper functions
def price_range_to_number(price_range: str) -> int:
    """Convert $ symbols to number (1-4)."""
    if not price_range:
        return 0
    return len(price_range)


def number_to_price_range(number: int) -> str:
    """Convert number to $ symbols."""
    if number <= 0:
        return ""
    return "$" * min(number, 4)
