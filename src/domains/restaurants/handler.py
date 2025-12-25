"""src/domains/restaurants/handler.py

Restaurant domain handler implementing DomainHandler interface.
"""

from typing import List, Dict, Optional
from domains.base.domain_handler import DomainHandler
from domains.restaurants.models import RestaurantQuery, Restaurant
from domains.restaurants.intent_parser import RestaurantIntentParser
from domains.restaurants.comparator import RestaurantComparator
from domains.restaurants.api_clients.mock_yelp_client import MockYelpClient
from domains.restaurants.api_clients.mock_google_places_client import MockGooglePlacesClient
from domains.restaurants.api_clients.google_places_client import GooglePlacesClient


class RestaurantHandler(DomainHandler):
    """
    Restaurant domain handler implementing the DomainHandler interface.

    Coordinates:
    - Intent parsing (natural language → RestaurantQuery)
    - API client calls (Yelp, Google Places)
    - AI-powered comparison
    - Result formatting

    Features:
    - Multiple providers (Yelp, Google Places)
    - AI-powered recommendations
    - Cuisine-based search
    - Rating and price filtering
    - Distance-aware results

    Example:
        handler = RestaurantHandler(
            geocoding_service=geocoder,
            cache_service=cache,
            rate_limiter=limiter
        )

        results = handler.process(
            "Find me Italian food near Times Square",
            context={'user_location': 'New York, NY'}
        )
    """

    def __init__(
        self,
        cache_service=None,
        geocoding_service=None,
        rate_limiter=None
    ):
        """
        Initialize restaurant handler.

        Args:
            cache_service: Optional caching service
            geocoding_service: Geocoding service for location resolution
            rate_limiter: Optional rate limiter service
        """
        super().__init__(cache_service, geocoding_service)
        self.rate_limiter = rate_limiter

        # Initialize domain-specific components
        self.parser = RestaurantIntentParser()
        self.comparator = RestaurantComparator()

        # Initialize API clients (mock for now)
        self.clients = {
            'yelp': MockYelpClient(rate_limiter=rate_limiter),
            'google_places': GooglePlacesClient(rate_limiter=rate_limiter)
        }

    def parse_query(self, raw_query: str, context: Dict = None) -> RestaurantQuery:
        """
        Parse natural language query into RestaurantQuery.

        Args:
            raw_query: User's natural language input
            context: Optional context with user_location, etc.

        Returns:
            RestaurantQuery object

        Example:
            parse_query("Find Italian food near Times Square")
            → RestaurantQuery(cuisine="Italian", location="Times Square, NY")
        """
        user_location = context.get('user_location') if context else None

        # Use existing intent parser
        restaurant_query = self.parser.parse(raw_query, user_location)

        return restaurant_query

    def fetch_options(self, query: RestaurantQuery) -> List[Restaurant]:
        """
        Fetch restaurant options from multiple providers.

        Args:
            query: RestaurantQuery with search criteria

        Returns:
            List of Restaurant objects from different providers

        Example:
            fetch_options(RestaurantQuery(cuisine="Italian", location="NYC"))
            → [Restaurant(yelp), Restaurant(google), ...]
        """
        # Geocode the search location
        if not self.geocoder:
            raise ValueError("Geocoding service required for restaurant search")

        lat, lon, formatted_location = self.geocoder.geocode(query.location)

        # Check cache first (if available)
        cache_key = None
        if self.cache:
            cache_key = f"restaurants_{query.cuisine or 'any'}_{lat:.4f}_{lon:.4f}_{query.price_range or 'any'}"
            cached = self.cache.get(cache_key)
            if cached:
                # Convert dicts back to Restaurant objects
                if cached and isinstance(cached[0], dict):
                    return [Restaurant(**r) for r in cached]
                return cached

        # Fetch from each provider
        restaurants = []

        for provider_name, client in self.clients.items():
            try:
                results = client.search(
                    cuisine=query.cuisine,
                    latitude=lat,
                    longitude=lon,
                    limit=5,
                    price_range=query.price_range,
                    rating_min=query.rating_min
                )
                restaurants.extend(results)
            except Exception as e:
                print(f"Error fetching from {provider_name}: {e}")
                continue

        # Sort by rating (best first)
        restaurants.sort(key=lambda r: r.rating, reverse=True)

        # Cache results (if available)
        if self.cache and cache_key:
            # Use restaurant-specific TTL (1 hour)
            ttl = self.cache.get_ttl_for_domain('restaurants')
            self.cache.set(cache_key, restaurants, ttl=ttl)

        return restaurants

    def compare_options(self, options: List[Restaurant], priority: str = "balanced", use_ai: bool = False) -> str:    
        """
        Compare restaurant options and provide recommendation.
        
        Args:
            options: List of Restaurant objects
            priority: Comparison priority (rating, price, distance, balanced)
            use_ai: If True, use AI (slower, detailed). If False, use fast fallback.
        
        Returns:
            Natural language comparison and recommendation
        """
        if use_ai:
            # AI-powered (2-4 seconds, detailed analysis)
            comparison = self.comparator.compare_restaurants(options, priority)
        else:
            # Fast fallback (instant, simple recommendation)
            comparison = self.comparator._fallback_comparison(options, priority)
        
        return comparison

    def format_results(
        self,
        options: List[Restaurant],
        comparison: str,
        priority: str = "balanced",
        search_time: float = 0.0,
        query_text: str = ""
    ) -> Dict:
        """
        Format results for display in UI-expected format.

        Args:
            options: List of Restaurant objects
            comparison: AI-generated comparison text
            priority: Priority used for comparison
            search_time: Time taken for search in seconds
            query_text: Original query text

        Returns:
            Dictionary with formatted results matching UI expectations
        """
        # Find best restaurant (highest rating, then most reviews)
        best_restaurant = None
        if options:
            best_restaurant = max(options, key=lambda r: (r.rating, r.review_count))

        return {
            'success': True,
            'data': {
                'results': [opt.to_dict() for opt in options],
                'total': len(options),
                'aiRecommendation': {
                    'placeId': best_restaurant.id if best_restaurant else None,
                    'reason': comparison
                } if comparison else None
            },
            'meta': {
                'searchTime': round(search_time, 2),
                'query': query_text,
                'priority': priority
            }
        }

    def process(
        self,
        raw_query: str,
        context: Dict = None,
        priority: str = "balanced",
        use_ai: bool = False
    ) -> Dict:
        """
        Main processing pipeline - calls all steps in order.

        This is the public interface that other components use.

        Args:
            raw_query: User's query
            context: Optional context (user_location, etc.)
            priority: Comparison priority (rating, price, distance, balanced)
            use_ai: If True, use AI (slower, detailed). If False, use fast fallback.

        Returns:
            Complete results ready for display

        Example:
            process("Find Italian food near Times Square")
            → {'success': True, 'data': {'results': [...], ...}, 'meta': {...}}
        """
        import time
        import hashlib

        start_time = time.time()

        # Step 1: Parse query
        query = self.parse_query(raw_query, context)

        # Step 2: Fetch options
        options = self.fetch_options(query)

        # Step 3: Enrich restaurant data with UI fields
        for i, restaurant in enumerate(options):
            # Generate unique ID from provider + name
            id_string = f"{restaurant.provider}_{restaurant.name}".lower()
            restaurant.id = hashlib.md5(id_string.encode()).hexdigest()[:12]

            # Add tags based on rating
            tags = []
            if restaurant.rating >= 4.5:
                tags.append("🔥 Trending")
            elif restaurant.rating >= 4.0:
                tags.append("💥 Popular")

            # Add "Open Now" tag if applicable
            if restaurant.is_open_now:
                tags.append("Open Now")

            restaurant.tags = tags

            # Add badge for top result
            if i == 0:
                restaurant.badge = "#1"

            # Add gradient fallback if no image
            if not restaurant.image_url:
                gradients = [
                    "linear-gradient(135deg, #FFE5B4, #FFB347)",  # Peach
                    "linear-gradient(135deg, #E0BBE4, #957DAD)",  # Purple
                    "linear-gradient(135deg, #FFDAB9, #FFA07A)",  # Orange
                    "linear-gradient(135deg, #B0E0E6, #87CEEB)",  # Blue
                ]
                restaurant.gradient = gradients[i % len(gradients)]

        # Step 4: Compare options
        comparison = self.compare_options(options, priority, use_ai=use_ai)

        # Step 5: Calculate search time
        search_time = time.time() - start_time

        # Step 6: Format results
        results = self.format_results(
            options,
            comparison,
            priority,
            search_time=search_time,
            query_text=raw_query
        )

        return results

    def __repr__(self) -> str:
        providers = ", ".join(self.clients.keys())
        return f"RestaurantHandler(providers=[{providers}])"


# Convenience function
def create_restaurant_handler(
    cache_service=None,
    geocoding_service=None,
    rate_limiter=None
) -> RestaurantHandler:
    """
    Create a restaurant handler instance.

    Args:
        cache_service: Optional cache service
        geocoding_service: Optional geocoding service
        rate_limiter: Optional rate limiter

    Returns:
        RestaurantHandler instance
    """
    return RestaurantHandler(
        cache_service=cache_service,
        geocoding_service=geocoding_service,
        rate_limiter=rate_limiter
    )
