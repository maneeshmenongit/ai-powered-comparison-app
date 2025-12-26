"""Real Google Places API client."""

import os
import requests
from math import radians, sin, cos, sqrt, atan2
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
            "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.priceLevel,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.regularOpeningHours,places.photos"
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

            # Log the full error response for debugging
            if response.status_code != 200:
                print(f"Google Places API Error {response.status_code}:")
                print(f"Response: {response.text}")

            response.raise_for_status()
            data = response.json()
            
            restaurants = []
            for place in data.get('places', []):
                # Convert Google data to our format
                rating = place.get('rating', 0.0)
                if rating < rating_min:
                    continue
                
                place_lat = place.get('location', {}).get('latitude', latitude)
                place_lon = place.get('location', {}).get('longitude', longitude)

                # Extract photo resource names and construct media URLs
                photos = place.get('photos', [])
                photo_urls = []
                image_url = None

                if photos and len(photos) > 0:
                    # Get the first photo's resource name
                    first_photo = photos[0]
                    photo_name = first_photo.get('name', '')

                    if photo_name:
                        # Construct the media URL with API key
                        # Use maxHeightPx to control image size (400px height)
                        image_url = f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=400&key={self.api_key}"
                        photo_urls.append(image_url)

                        # Add additional photos (up to 5 total)
                        for photo in photos[1:5]:
                            photo_name = photo.get('name', '')
                            if photo_name:
                                photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=400&key={self.api_key}"
                                photo_urls.append(photo_url)

                restaurant = Restaurant(
                    provider='google_places',
                    name=place.get('displayName', {}).get('text', 'Unknown'),
                    cuisine=cuisine or 'Restaurant',
                    rating=rating,
                    review_count=place.get('userRatingCount', 0),
                    price_range=self._convert_price_level(place.get('priceLevel')),
                    address=place.get('formattedAddress', ''),
                    distance_miles=self._calculate_distance(latitude, longitude, place_lat, place_lon),
                    phone=place.get('nationalPhoneNumber'),
                    website=place.get('websiteUri'),
                    hours=self._format_hours(place.get('regularOpeningHours')),
                    is_open_now=place.get('regularOpeningHours', {}).get('openNow', False),
                    coordinates=(place_lat, place_lon),
                    image_url=image_url,
                    photos=photo_urls
                )
                restaurants.append(restaurant)
            
            return restaurants
            
        except Exception as e:
            print(f"Google Places API error: {e}")
            return []
    
    def _format_hours(self, hours_data):
        """Format opening hours."""
        if not hours_data:
            return None
        return hours_data.get('weekdayDescriptions', [])

    def _convert_price_level(self, level: str) -> str:
        """Convert Google price level to $ format."""
        mapping = {
            'PRICE_LEVEL_INEXPENSIVE': '$',
            'PRICE_LEVEL_MODERATE': '$$',
            'PRICE_LEVEL_EXPENSIVE': '$$$',
            'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$'
        }
        return mapping.get(level, '$$')
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in miles using Haversine formula."""
        R = 3959  # Earth radius in miles
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c