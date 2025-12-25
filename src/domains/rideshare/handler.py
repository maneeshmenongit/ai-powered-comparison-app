"""
RideShare Domain Handler

Implements the DomainHandler interface for the ride-share domain.
Coordinates all ride-share components (parsing, API clients, comparison).
"""

from typing import List, Dict, Optional, Any
from ..base.domain_handler import DomainHandler
from .models import RideQuery, RideEstimate
from .intent_parser import RideShareIntentParser
from .comparator import RideShareComparator
from .api_clients.mock_uber_client import MockUberClient
from .api_clients.mock_lyft_client import MockLyftClient


class RideShareHandler(DomainHandler):
    """
    Ride-share domain handler implementing the DomainHandler interface.

    This handler coordinates all ride-share functionality:
    - Parsing natural language queries into structured RideQuery objects
    - Fetching estimates from multiple providers (Uber, Lyft)
    - AI-powered comparison and recommendations
    - Formatting results for display

    The handler integrates existing ride-share components:
    - RideShareIntentParser: LLM-based query parsing
    - MockUberClient/MockLyftClient: Provider API clients
    - RideShareComparator: AI-powered comparison

    Example:
        handler = RideShareHandler(
            cache_service=cache,
            geocoding_service=geocoder
        )

        # Full pipeline with one method call
        results = handler.process(
            "Get me from Times Square to JFK",
            context={"user_location": "New York"},
            priority="price"
        )

        # Results contain:
        # - query: Parsed RideQuery object
        # - estimates: List of ride options
        # - comparison: AI recommendation
        # - route: Origin/destination coordinates
    """

    def __init__(
        self,
        cache_service: Optional[Any] = None,
        geocoding_service: Optional[Any] = None,
        rate_limiter: Optional[Any] = None
    ):
        """
        Initialize ride-share handler with services and components.

        Args:
            cache_service: Optional cache for storing API results (5min TTL)
            geocoding_service: Geocoding service for location resolution
            rate_limiter: Optional rate limiter service

        Note:
            - Parser and comparator use OpenAI GPT-4o-mini
            - API clients default to mock implementations
            - Can be swapped with real clients when API access available
        """
        super().__init__(cache_service, geocoding_service)
        self.rate_limiter = rate_limiter

        # Initialize domain-specific components
        self.parser = RideShareIntentParser()
        self.comparator = RideShareComparator()

        # Initialize API clients (mock by default)
        # TODO: Support real Uber/Lyft clients when API access granted
        self.clients = {
            'uber': MockUberClient(deterministic=False),
            'lyft': MockLyftClient(deterministic=False)
        }

    def parse_query(
        self,
        raw_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RideQuery:
        """
        Parse natural language query into structured RideQuery.

        Uses LLM (GPT-4o-mini) to extract ride-share intent from natural language.
        Understands origin, destination, providers, vehicle type, and passenger count.

        Args:
            raw_query: User's natural language input
                Examples:
                - "Get me from Times Square to JFK"
                - "Compare Uber and Lyft from my location to Central Park"
                - "I need an XL ride for 5 people from Penn Station to LaGuardia"
            context: Optional context dictionary
                - user_location: User's current location (for inferring origin)
                - preferences: User preferences (provider, vehicle type)

        Returns:
            RideQuery object with:
            - origin: Pickup location
            - destination: Dropoff location
            - providers: List of providers to compare (e.g., ["uber", "lyft"])
            - vehicle_type: Requested vehicle type (e.g., "standard", "xl")
            - when: When ride is needed (default: "now")
            - passengers: Number of passengers (default: 1)

        Raises:
            ValueError: If query is missing required fields (origin or destination)

        Example:
            query = handler.parse_query(
                "Compare Uber and Lyft from Times Square to JFK",
                context={"user_location": "New York"}
            )
            # Returns: RideQuery(
            #   origin="Times Square",
            #   destination="JFK Airport",
            #   providers=["uber", "lyft"],
            #   vehicle_type="standard"
            # )
        """
        user_location = context.get('user_location') if context else None

        # Use existing intent parser
        ride_query = self.parser.parse_query(raw_query, user_location)

        return ride_query

    def fetch_options(self, query: RideQuery) -> List[RideEstimate]:
        """
        Fetch ride estimates from multiple providers.

        Geocodes origin/destination, checks cache, then fetches fresh estimates
        from requested providers (Uber, Lyft, etc.).

        Args:
            query: RideQuery with origin, destination, providers, vehicle_type

        Returns:
            List of RideEstimate objects from different providers

        Raises:
            ValueError: If geocoding fails for origin or destination
            Exception: If all API clients fail

        Example:
            query = RideQuery(
                origin="Times Square",
                destination="JFK Airport",
                providers=["uber", "lyft"]
            )
            estimates = handler.fetch_options(query)
            # Returns: [
            #   RideEstimate(provider="Uber", vehicle_type="UberX", price=40.16),
            #   RideEstimate(provider="Uber", vehicle_type="UberXL", price=60.24),
            #   RideEstimate(provider="Lyft", vehicle_type="Lyft", price=41.83),
            #   ...
            # ]

        Note:
            - Uses geocoding service to convert locations to coordinates
            - Caches results based on origin/destination coordinates
            - Cache TTL: 5 minutes (configured in cache service)
            - Returns all vehicle types from each provider
        """
        estimates = []

        # Geocode origin and destination
        if not self.geocoder:
            raise ValueError("Geocoding service required for ride-share handler")

        origin_lat, origin_lng, origin_formatted = self.geocoder.geocode(query.origin)
        dest_lat, dest_lng, dest_formatted = self.geocoder.geocode(query.destination)

        # Generate cache key from coordinates
        cache_key = None
        if self.cache:
            cache_key = self._generate_cache_key(
                origin_lat, origin_lng,
                dest_lat, dest_lng
            )
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        # Fetch from each requested provider
        for provider_name in query.providers:
            provider_name_lower = provider_name.lower()

            if provider_name_lower not in self.clients:
                continue

            try:
                # Rate limit check before API call
                if self.rate_limiter:
                    self.rate_limiter.acquire(provider_name_lower)

                client = self.clients[provider_name_lower]

                # Get price estimates (returns list of estimates for all vehicle types)
                provider_estimates = client.get_price_estimates(
                    pickup_lat=origin_lat,
                    pickup_lng=origin_lng,
                    dropoff_lat=dest_lat,
                    dropoff_lng=dest_lng
                )

                estimates.extend(provider_estimates)

            except Exception as e:
                # Log error but continue with other providers
                print(f"Warning: Failed to fetch from {provider_name}: {e}")
                continue

        # Enrich estimates with UI fields and deep links
        for estimate in estimates:
            # Generate deep link
            estimate.deep_link = self._generate_deep_link(
                estimate.provider,
                estimate.vehicle_type,
                origin_lat, origin_lng,
                dest_lat, dest_lng
            )

            # Set ride type based on vehicle type
            vehicle_lower = estimate.vehicle_type.lower()
            if 'xl' in vehicle_lower or 'suv' in vehicle_lower or 'black' in vehicle_lower:
                estimate.type = "Premium"
                estimate.seats = 6
            elif 'pool' in vehicle_lower or 'shared' in vehicle_lower or 'line' in vehicle_lower:
                estimate.type = "Shared"
                estimate.seats = 2
            else:
                estimate.type = "Standard"
                estimate.seats = 4

            # Set surge if applicable
            if estimate.surge_multiplier > 1.0:
                estimate.surge = estimate.surge_multiplier

        # Cache results
        if self.cache and cache_key and estimates:
            self.cache.set(cache_key, estimates)

        if not estimates:
            raise Exception("No estimates available from any provider")

        return estimates

    def compare_options(
        self,
        options: List[RideEstimate],
        priority: Optional[str] = "balanced"
    ) -> str:
        """
        Use AI to compare ride options and provide recommendation.

        Analyzes all ride options and generates natural language recommendation
        based on user priority (price, time, or balanced).

        Args:
            options: List of RideEstimate objects from different providers
            priority: User's priority for comparison
                - "price": Cheapest option
                - "time": Fastest option (pickup + trip duration)
                - "balanced": Best value (60% price, 40% time)

        Returns:
            Natural language comparison and recommendation

        Example:
            comparison = handler.compare_options(
                [uber_est, lyft_est],
                priority="price"
            )
            # Returns: "Take Uber UberX at $40.16. It's the cheapest option
            #           with a 5-minute pickup time and 27-minute trip."

        Note:
            - Uses GPT-4o-mini with temperature=0.7 for natural language
            - Falls back to rule-based comparison if LLM fails
            - Considers surge/primetime pricing in recommendations
            - Provides reasoning and trade-offs
        """
        # Use existing comparator
        comparison = self.comparator.compare_rides(
            options,
            user_priority=priority
        )

        return comparison

    def format_results(
        self,
        options: List[RideEstimate],
        comparison: str
    ) -> Dict[str, Any]:
        """
        Format results for display in the UI (matches UI DATA_STRUCTURE.md format).

        Args:
            options: List of RideEstimate objects
            comparison: AI-generated comparison and recommendation text

        Returns:
            Dictionary with UI-expected structure
        """
        # Find best ride (cheapest)
        best_ride = None
        if options:
            best_ride = min(options, key=lambda r: r.price_estimate)

        # Calculate trip info
        distance_mi = options[0].distance_miles if options else 0
        duration_min = options[0].duration_minutes if options else 0

        # Calculate savings (difference between most expensive and cheapest)
        prices = [opt.price_estimate for opt in options if opt.is_available]
        savings = max(prices) - min(prices) if len(prices) > 1 else 0

        return {
            'success': True,
            'data': {
                'rides': [opt.to_dict() for opt in options],
                'tripInfo': {
                    'distance': f"{distance_mi:.1f} mi",
                    'duration': f"{duration_min} min",
                    'savings': round(savings, 2)
                },
                'recommendation': {
                    'provider': best_ride.provider if best_ride else None,
                    'reason': comparison
                } if comparison else None
            }
        }

    def _generate_deep_link(
        self,
        provider: str,
        vehicle_type: str,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> str:
        """
        Generate deep link to open provider app.

        Args:
            provider: Provider name (Uber, Lyft, etc.)
            vehicle_type: Vehicle type
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            Deep link URL
        """
        import urllib.parse

        provider_lower = provider.lower()

        if 'uber' in provider_lower:
            # Uber deep link format
            params = {
                'action': 'setPickup',
                'pickup[latitude]': origin_lat,
                'pickup[longitude]': origin_lng,
                'dropoff[latitude]': dest_lat,
                'dropoff[longitude]': dest_lng,
                'product_id': vehicle_type
            }
            query_string = urllib.parse.urlencode(params)
            return f"uber://?{query_string}"

        elif 'lyft' in provider_lower:
            # Lyft deep link format
            params = {
                'pickup[latitude]': origin_lat,
                'pickup[longitude]': origin_lng,
                'destination[latitude]': dest_lat,
                'destination[longitude]': dest_lng,
            }
            query_string = urllib.parse.urlencode(params)
            return f"lyft://ridetype?{query_string}"

        else:
            # Generic fallback
            return f"https://maps.google.com/?saddr={origin_lat},{origin_lng}&daddr={dest_lat},{dest_lng}"

    def _generate_cache_key(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> str:
        """
        Generate cache key from coordinates.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            Cache key string (MD5 hash of coordinates)
        """
        import hashlib
        key_str = f"{origin_lat:.4f},{origin_lng:.4f},{dest_lat:.4f},{dest_lng:.4f}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def __repr__(self) -> str:
        """String representation for debugging."""
        providers = ', '.join(self.clients.keys())
        return (
            f"RideShareHandler(providers=[{providers}], "
            f"{'with cache' if self.cache else 'no cache'}, "
            f"{'with geocoder' if self.geocoder else 'no geocoder'}, "
            f"{'with rate limiter' if self.rate_limiter else 'no rate limiter'})"
        )
