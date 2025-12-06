"""
Ride-share comparison domain.

Compares ride options from multiple providers (Uber, Lyft, Via).
"""

from .handler import RideShareHandler
from .models import RideQuery, RideEstimate
from .intent_parser import RideShareIntentParser
from .comparator import RideShareComparator

__all__ = [
    'RideShareHandler',
    'RideQuery',
    'RideEstimate',
    'RideShareIntentParser',
    'RideShareComparator',
]
