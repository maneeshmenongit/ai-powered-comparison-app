"""Real Google Places API client."""

import os
import requests
from typing import List, Optional
from ..models import Restaurant

class GooglePlacesClient:
    """Real Google Places API client."""
    
    def __init__(self, api_key: str = None, rate_limiter=None):
        self.api_key = api_key or os.environ.get('GOOGLE_PLACES_API_KEY')
        self.rate_limiter = rate_limiter
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY not set")
    
    def search(
        self,
        cuisine: str = None,
        latitude: float = None,
        longitude: float = None,
        limit: int = 5,
        price_range: str = None,
        rating_min: float = 0.0
    ) -> List[Restaurant]:
        """Search restaurants via Google Places API."""
        
        # Build query
        query = f"{cuisine} restaurant" if cuisine else "restaurant"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.priceLevel,places.formattedAddress,places.location"
        }
        
        body = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": 8000  # 5 miles in meters
                }
            },
            "maxResultCount": limit
        }
        
        try:
            response = requests.post(self.base_url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            restaurants = []
            for place in data.get('places', []):
                # Convert Google data to our format
                rating = place.get('rating', 0.0)
                if rating < rating_min:
                    continue
                
                restaurant = Restaurant(
                    provider='google_places',
                    name=place.get('displayName', {}).get('text', 'Unknown'),
                    cuisine=cuisine or 'Restaurant',
                    rating=rating,
                    review_count=place.get('userRatingCount', 0),
                    price_range=self._convert_price_level(place.get('priceLevel')),
                    address=place.get('formattedAddress', ''),
                    distance_miles=0.0,  # Calculate if needed
                    coordinates=(
                        place.get('location', {}).get('latitude'),
                        place.get('location', {}).get('longitude')
                    )
                )
                restaurants.append(restaurant)
            
            return restaurants
            
        except Exception as e:
            print(f"Google Places API error: {e}")
            return []
    
    def _convert_price_level(self, level: str) -> str:
        """Convert Google price level to $ format."""
        mapping = {
            'PRICE_LEVEL_INEXPENSIVE': '$',
            'PRICE_LEVEL_MODERATE': '$$',
            'PRICE_LEVEL_EXPENSIVE': '$$$',
            'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$'
        }
        return mapping.get(level, '$$')