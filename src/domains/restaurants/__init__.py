"""
Hopwise - Restaurant Domain
Every stop matters! Hop smarter!

Restaurant comparison across multiple providers.
"""

from .handler import RestaurantHandler
from .models import RestaurantQuery, Restaurant
from .intent_parser import RestaurantIntentParser
from .comparator import RestaurantComparator

__all__ = [
    'RestaurantHandler',
    'RestaurantQuery',
    'Restaurant',
    'RestaurantIntentParser',
    'RestaurantComparator',
]
