"""src/domains/restaurants/models.py

Data models for restaurant domain.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


# Filter categories
FILTER_CATEGORIES = {
    'Food': {
        'name': 'Food',
        'description': 'Restaurants serving main meals',
        'keywords': ['restaurant', 'dining', 'meal', 'food', 'lunch', 'dinner'],
        'icon': '🍽️'
    },
    'Drinks': {
        'name': 'Drinks',
        'description': 'Bars, lounges, wine bars, cocktail bars',
        'keywords': ['bar', 'drinks', 'cocktails', 'wine', 'beer', 'lounge', 'pub'],
        'icon': '🍸'
    },
    'Ice Cream': {
        'name': 'Ice Cream',
        'description': 'Ice cream shops, gelato, frozen desserts',
        'keywords': ['ice cream', 'gelato', 'frozen yogurt', 'sorbet', 'froyo', 'soft serve'],
        'icon': '🍨'
    },
    'Cafe': {
        'name': 'Cafe',
        'description': 'Coffee shops, cafes, bakeries, casual spots',
        'keywords': ['cafe', 'coffee', 'espresso', 'latte', 'tea', 'bakery', 'pastry', 'casual'],
        'icon': '☕'
    }
}


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
        filter_category: Filter type (Food, Drinks, Dessert, Cafe)
    """
    cuisine: Optional[str] = None
    location: str = ""
    price_range: Optional[str] = None  # $, $$, $$$, $$$$
    rating_min: float = 0.0
    distance_miles: float = 5.0
    party_size: Optional[int] = None
    dietary_restrictions: List[str] = field(default_factory=list)
    open_now: bool = False
    filter_category: str = "Food"  # Default to Food

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
            'open_now': self.open_now,
            'filter_category': self.filter_category
        }

    def __repr__(self) -> str:
        parts = []
        if self.filter_category and self.filter_category != "Food":
            parts.append(f"[{self.filter_category}]")
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
    id: str = ""  # Unique identifier
    subcategory: Optional[str] = None  # e.g., "Pizza", "Sushi"
    tags: List[str] = field(default_factory=list)  # ["🔥 Trending", "💥 Popular"]
    badge: Optional[str] = None  # "#1", "New", etc.
    gradient: str = "linear-gradient(135deg, #FFE5B4, #FFB347)"  # Fallback gradient
    photos: List[str] = field(default_factory=list) 

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
            'last_updated': self.last_updated,
            'id': self.id,
            'subcategory': self.subcategory,
            'tags': self.tags,
            'badge': self.badge,
            'gradient': self.gradient,
            'photos': self.photos
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


def get_filter_category(filter_name: str) -> Dict:
    """
    Get filter category details.

    Args:
        filter_name: Filter category name (Food, Drinks, Dessert, Cafe)

    Returns:
        Filter category dictionary or Food if not found
    """
    return FILTER_CATEGORIES.get(filter_name, FILTER_CATEGORIES['Food'])


def validate_filter_category(filter_name: str) -> str:
    """
    Validate and normalize filter category name.

    Args:
        filter_name: Filter name to validate

    Returns:
        Valid filter name (defaults to Food if invalid)
    """
    if filter_name in FILTER_CATEGORIES:
        return filter_name

    # Try case-insensitive match
    filter_lower = filter_name.lower()
    for key in FILTER_CATEGORIES.keys():
        if key.lower() == filter_lower:
            return key

    # Default to Food
    return "Food"
