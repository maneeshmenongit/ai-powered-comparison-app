"""src/domains/restaurants/api_clients/mock_google_places_client.py

Mock Google Places API client for testing restaurant domain.
"""

import random
from typing import List, Optional
from domains.restaurants.models import Restaurant


class MockGooglePlacesClient:
    """
    Mock Google Places API client.

    Simulates Google Places API responses with realistic restaurant data.
    Slightly different results than Yelp for comparison testing.

    Features:
    - Different restaurant selection than Yelp
    - Slightly different ratings
    - Google-style data format
    - Realistic variety for comparison

    Example:
        client = MockGooglePlacesClient()
        restaurants = client.search(
            cuisine="Italian",
            latitude=40.7580,
            longitude=-73.9855,
            limit=5
        )
    """

    # Different restaurant data than Yelp
    RESTAURANT_DATA = {
        'Italian': [
            ('Il Buco', 4.4, '$$$', 890),
            ('Peasant', 4.3, '$$$', 670),
            ('Babbo', 4.5, '$$$$', 1100),
            ('Locanda Verde', 4.4, '$$$', 1450),
            ('Torrisi', 4.6, '$$$$', 450),
            ('Don Angie', 4.7, '$$$', 890),
        ],
        'Japanese': [
            ('Taka Taka', 4.6, '$$', 780),
            ('Raku', 4.5, '$$', 560),
            ('Okonomi', 4.4, '$$', 890),
            ('Hatsuhana', 4.3, '$$$', 670),
            ('Tanoshi', 4.7, '$$$', 340),
        ],
        'Chinese': [
            ('Han Dynasty', 4.4, '$$', 2100),
            ('Xi\'an Famous Foods', 4.5, '$', 3890),
            ('Kings County Imperial', 4.6, '$$$', 560),
            ('Congee Village', 4.2, '$', 1890),
        ],
        'Mexican': [
            ('Oxomoco', 4.5, '$$$', 670),
            ('Casa Enrique', 4.6, '$$$', 890),
            ('Atla', 4.4, '$$', 1200),
            ('Café Habana', 4.3, '$', 2300),
        ],
        'American': [
            ('Union Square Café', 4.5, '$$$', 2100),
            ('The Spotted Pig', 4.3, '$$', 3400),
            ('Minetta Tavern', 4.4, '$$$', 1890),
            ('Peter Luger', 4.6, '$$$$', 4200),
        ],
        'Thai': [
            ('Pok Pok NY', 4.5, '$$', 1670),
            ('Kiin Thai', 4.4, '$$', 890),
            ('Ugly Baby', 4.6, '$$', 1100),
        ],
        'Indian': [
            ('Bombay Bread Bar', 4.5, '$$', 670),
            ('Benares', 4.3, '$$$', 560),
            ('Utsav', 4.4, '$$', 890),
        ],
        'French': [
            ('Bouley', 4.7, '$$$$', 780),
            ('Frenchette', 4.5, '$$$', 1450),
            ('Raoul\'s', 4.4, '$$$', 1100),
        ],
    }

    def __init__(self, rate_limiter=None):
        """
        Initialize mock Google Places client.

        Args:
            rate_limiter: Optional rate limiter service
        """
        self.rate_limiter = rate_limiter
        self.provider = "google_places"

    def search(
        self,
        cuisine: Optional[str] = None,
        latitude: float = 40.7580,
        longitude: float = -73.9855,
        limit: int = 5,
        price_range: Optional[str] = None,
        rating_min: float = 0.0
    ) -> List[Restaurant]:
        """
        Search for restaurants.

        Args:
            cuisine: Cuisine type
            latitude: Search center latitude
            longitude: Search center longitude
            limit: Maximum results
            price_range: Filter by price
            rating_min: Minimum rating

        Returns:
            List of Restaurant objects
        """
        # Rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire('google_places')

        # Get restaurant data
        cuisine_key = self._normalize_cuisine(cuisine)
        restaurant_pool = self.RESTAURANT_DATA.get(
            cuisine_key,
            self.RESTAURANT_DATA['American']
        )

        results = []

        for name, rating, price, reviews in restaurant_pool[:limit * 2]:
            # Filter by price range
            if price_range and price != price_range:
                continue

            # Filter by rating
            if rating < rating_min:
                continue

            # Generate random distance
            distance = round(random.uniform(0.2, 2.5), 1)

            # Generate address
            address = self._generate_address()

            # Generate coordinates
            rest_lat = latitude + random.uniform(-0.01, 0.01)
            rest_lon = longitude + random.uniform(-0.01, 0.01)

            # Create Restaurant
            restaurant = Restaurant(
                provider=self.provider,
                name=name,
                cuisine=cuisine or cuisine_key,
                rating=rating,
                review_count=reviews,
                price_range=price,
                address=address,
                distance_miles=distance,
                phone=self._generate_phone(),
                website=f"https://www.google.com/maps/search/{name.replace(' ', '+')}",
                hours="Hours vary",
                is_open_now=random.choice([True, True, False]),  # 67% open
                coordinates=(rest_lat, rest_lon),
                image_url=None,  # Use gradient backgrounds instead of placeholder URLs
                categories=[cuisine_key, "Restaurant"]
            )

            results.append(restaurant)

            if len(results) >= limit:
                break

        return results

    def _normalize_cuisine(self, cuisine: Optional[str]) -> str:
        """Normalize cuisine type."""
        if not cuisine:
            return 'American'

        cuisine_lower = cuisine.lower()

        mappings = {
            'italian': 'Italian',
            'japanese': 'Japanese',
            'sushi': 'Japanese',
            'chinese': 'Chinese',
            'mexican': 'Mexican',
            'american': 'American',
            'thai': 'Thai',
            'indian': 'Indian',
            'french': 'French',
        }

        for key, value in mappings.items():
            if key in cuisine_lower:
                return value

        return 'American'

    def _generate_address(self) -> str:
        """Generate NYC address."""
        streets = ['Broadway', '6th Ave', '7th Ave', 'Houston St',
                   'Bleecker St', 'Prince St', 'Spring St']
        neighborhoods = ['Greenwich Village', 'SoHo', 'East Village',
                        'West Village', 'Chelsea', 'Tribeca']

        number = random.randint(10, 500)
        street = random.choice(streets)
        neighborhood = random.choice(neighborhoods)

        return f"{number} {street}, {neighborhood}, NY 10012"

    def _generate_phone(self) -> str:
        """Generate phone number."""
        area = random.choice(['212', '646', '917'])
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"({area}) {exchange}-{number}"

    def __repr__(self) -> str:
        return f"MockGooglePlacesClient(provider={self.provider})"
