"""src/domains/restaurants/api_clients/mock_yelp_client.py

Mock Yelp API client for testing restaurant domain.
"""

import random
from typing import List, Optional
from domains.restaurants.models import Restaurant


class MockYelpClient:
    """
    Mock Yelp Fusion API client.

    Simulates Yelp API responses with realistic restaurant data.
    Used for development and testing before real API integration.

    Features:
    - Realistic restaurant names and cuisines
    - Varied ratings (3.0-5.0 stars)
    - Price ranges ($-$$$$)
    - Distance-based results
    - Review counts

    Example:
        client = MockYelpClient()
        restaurants = client.search(
            cuisine="Italian",
            latitude=40.7580,
            longitude=-73.9855,
            limit=5
        )
    """

    # Realistic restaurant data by cuisine
    RESTAURANT_DATA = {
        'Italian': [
            ('Carbone', 4.5, '$$$$', 1200),
            ('Lilia', 4.6, '$$$', 890),
            ('Via Carota', 4.4, '$$$', 1450),
            ("L'Artusi", 4.3, '$$$', 980),
            ('Rubirosa', 4.5, '$$', 2100),
            ('Marea', 4.6, '$$$$', 756),
            ('Il Mulino', 4.2, '$$$$', 890),
            ('Osteria Morini', 4.3, '$$$', 670),
        ],
        'Japanese': [
            ('Sushi Nakazawa', 4.7, '$$$$', 890),
            ('Ippudo', 4.4, '$$', 3200),
            ('Totto Ramen', 4.3, '$', 2890),
            ('Yakitori Totto', 4.5, '$$', 1100),
            ('Ichiran', 4.2, '$$', 4500),
            ('Blue Ribbon Sushi', 4.4, '$$$', 1230),
        ],
        'Chinese': [
            ('Joe\'s Shanghai', 4.3, '$$', 3400),
            ('Nom Wah Tea Parlor', 4.2, '$', 2890),
            ('Hwa Yuan', 4.4, '$$', 890),
            ('RedFarm', 4.5, '$$$', 1670),
            ('Birds of a Feather', 4.6, '$$', 450),
        ],
        'Mexican': [
            ('Los Tacos No. 1', 4.6, '$', 5600),
            ('Cosme', 4.4, '$$$', 1230),
            ('Empellón', 4.3, '$$$', 890),
            ('Los Mariscos', 4.5, '$', 2100),
            ('Taco Mix', 4.2, '$', 1890),
        ],
        'American': [
            ('The Smith', 4.2, '$$', 4200),
            ('Gramercy Tavern', 4.6, '$$$$', 2100),
            ('Blue Hill', 4.7, '$$$$', 890),
            ('Shake Shack', 4.3, '$', 8900),
            ('Five Guys', 4.1, '$', 3400),
        ],
        'Thai': [
            ('Uncle Boons', 4.5, '$$', 1200),
            ('Somtum Der', 4.4, '$$', 980),
            ('Fish Cheeks', 4.6, '$$$', 670),
            ('Ayada Thai', 4.5, '$', 2300),
        ],
        'Indian': [
            ('Junoon', 4.4, '$$$', 890),
            ('Tamarind', 4.3, '$$$', 1100),
            ('Dhamaka', 4.6, '$$', 560),
            ('Adda', 4.5, '$$', 780),
        ],
        'French': [
            ('Le Bernardin', 4.8, '$$$$', 1890),
            ('Daniel', 4.6, '$$$$', 1200),
            ('Balthazar', 4.3, '$$$', 3400),
            ('Café Boulud', 4.4, '$$$', 890),
        ],
    }

    def __init__(self, rate_limiter=None):
        """
        Initialize mock Yelp client.

        Args:
            rate_limiter: Optional rate limiter service
        """
        self.rate_limiter = rate_limiter
        self.provider = "yelp"

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
            cuisine: Cuisine type (Italian, Chinese, etc.)
            latitude: Search center latitude
            longitude: Search center longitude
            limit: Maximum results to return
            price_range: Filter by price ($, $$, $$$, $$$$)
            rating_min: Minimum rating (0-5)

        Returns:
            List of Restaurant objects
        """
        # Rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire('yelp')

        # Get restaurant data for cuisine
        cuisine_key = self._normalize_cuisine(cuisine)
        restaurant_pool = self.RESTAURANT_DATA.get(
            cuisine_key,
            self.RESTAURANT_DATA['American']  # Default
        )

        results = []

        for name, rating, price, reviews in restaurant_pool[:limit * 2]:  # Get more than needed
            # Filter by price range
            if price_range and price != price_range:
                continue

            # Filter by rating
            if rating < rating_min:
                continue

            # Generate random distance (0.1 to 3.0 miles)
            distance = round(random.uniform(0.1, 3.0), 1)

            # Generate address
            address = self._generate_address(latitude, longitude)

            # Generate coordinates near search location
            rest_lat = latitude + random.uniform(-0.01, 0.01)
            rest_lon = longitude + random.uniform(-0.01, 0.01)

            # Create Restaurant object
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
                website=f"https://www.yelp.com/biz/{name.lower().replace(' ', '-').replace("'", '')}",
                hours="Mon-Sun: 11:00 AM - 10:00 PM",
                is_open_now=random.choice([True, True, True, False]),  # 75% open
                coordinates=(rest_lat, rest_lon),
                image_url=f"https://via.placeholder.com/400x300?text={name.replace(' ', '+')}",
                categories=[cuisine_key, "Restaurant", "Dining"]
            )

            results.append(restaurant)

            if len(results) >= limit:
                break

        return results

    def _normalize_cuisine(self, cuisine: Optional[str]) -> str:
        """Normalize cuisine type to match data keys."""
        if not cuisine:
            return 'American'

        cuisine_lower = cuisine.lower()

        # Map common variations
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

    def _generate_address(self, lat: float, lon: float) -> str:
        """Generate realistic NYC address."""
        streets = ['Broadway', 'Madison Ave', 'Park Ave', '5th Ave',
                   'Lexington Ave', '3rd Ave', 'Amsterdam Ave']
        cross_streets = ['14th St', '23rd St', '34th St', '42nd St',
                        '50th St', '59th St', '72nd St']

        street = random.choice(streets)
        cross = random.choice(cross_streets)
        number = random.randint(100, 999)

        return f"{number} {street} (near {cross}), New York, NY 10001"

    def _generate_phone(self) -> str:
        """Generate realistic phone number."""
        area = random.choice(['212', '646', '917', '347'])
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"({area}) {exchange}-{number}"

    def __repr__(self) -> str:
        return f"MockYelpClient(provider={self.provider})"
