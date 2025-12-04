"""
Base domain handler pattern for multi-domain tourist companion app.

This module defines the abstract base classes that all domain handlers
(rideshare, restaurants, hotels, activities, etc.) must implement.

The domain handler pattern ensures:
- Consistent behavior across all domains
- Separation of concerns (parsing, fetching, comparing, formatting)
- Easy testing and mocking
- Plug-and-play architecture for new domains
- Shared services (caching, geocoding)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class DomainQuery:
    """
    Base class for all domain-specific queries.

    This is the structured representation of a user's natural language request.
    Each domain extends this with domain-specific fields.

    Attributes:
        raw_query: Original user query string
        user_location: User's current location (for context)
        user_preferences: Optional user preferences (price range, dietary restrictions, etc.)

    Example:
        # Rideshare domain
        query = RideQuery(
            raw_query="Get me from Times Square to JFK",
            user_location="New York",
            origin="Times Square",
            destination="JFK Airport"
        )

        # Restaurant domain
        query = RestaurantQuery(
            raw_query="Find Italian restaurants nearby",
            user_location="Manhattan",
            cuisine="Italian"
        )
    """

    raw_query: str
    user_location: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DomainResult:
    """
    Base class for all domain-specific results.

    Represents a single option from a provider (e.g., one Uber estimate,
    one restaurant recommendation, one hotel option).

    Attributes:
        provider: Name of the provider (e.g., "Uber", "Lyft", "OpenTable")
        score: Overall quality score from 0-100 (for ranking/comparison)
        metadata: Optional domain-specific metadata

    Example:
        # Rideshare result
        result = RideEstimate(
            provider="Uber",
            score=85.0,
            price_estimate=40.16,
            duration_minutes=27
        )

        # Restaurant result
        result = RestaurantOption(
            provider="Yelp",
            score=92.0,
            name="Joe's Pizza",
            rating=4.5
        )
    """

    provider: str
    score: float = 0.0  # 0-100 scale
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate score is in valid range."""
        if not 0 <= self.score <= 100:
            raise ValueError(f"Score must be 0-100, got {self.score}")


class DomainHandler(ABC):
    """
    Abstract base class for all domain handlers.

    Each domain (rideshare, restaurants, hotels, activities) implements this
    interface to provide a consistent experience across the application.

    The handler follows a 4-step pipeline:
    1. Parse: Natural language → Structured query
    2. Fetch: Query → Options from multiple providers
    3. Compare: Options → AI-powered recommendation
    4. Format: Raw results → Display-ready format

    Attributes:
        cache: Optional cache service for storing results
        geocoder: Optional geocoding service for location resolution

    Example:
        class RideShareHandler(DomainHandler):
            def parse_query(self, raw_query, context):
                # Use LLM to extract origin/destination
                return RideQuery(...)

            def fetch_options(self, query):
                # Call Uber and Lyft APIs
                return [uber_estimates, lyft_estimates]

            def compare_options(self, options):
                # Use LLM to compare and recommend
                return "Take Uber UberX for $40..."

            def format_results(self, options, comparison):
                # Format for Rich terminal display
                return {"table": ..., "recommendation": ...}

        # Usage
        handler = RideShareHandler()
        results = handler.process("Get me from Times Square to JFK")
    """

    def __init__(
        self,
        cache_service: Optional[Any] = None,
        geocoding_service: Optional[Any] = None
    ):
        """
        Initialize domain handler with shared services.

        Args:
            cache_service: Optional cache for storing API results
            geocoding_service: Optional service for geocoding locations

        Note:
            Services are optional to allow flexibility in testing and
            different deployment scenarios.
        """
        self.cache = cache_service
        self.geocoder = geocoding_service

    @abstractmethod
    def parse_query(
        self,
        raw_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainQuery:
        """
        Parse natural language query into structured domain query.

        This method uses LLM to understand user intent and extract
        domain-specific parameters.

        Args:
            raw_query: User's natural language request
            context: Optional context (user location, preferences, history)

        Returns:
            Domain-specific query object (subclass of DomainQuery)

        Raises:
            ValueError: If query is invalid or missing required fields

        Example:
            # Rideshare
            query = handler.parse_query(
                "Get me from Times Square to JFK",
                context={"user_location": "Manhattan"}
            )
            # Returns: RideQuery(origin="Times Square", destination="JFK")

            # Restaurant
            query = handler.parse_query(
                "Find cheap Italian restaurants near me",
                context={"user_location": "40.7580,-73.9855"}
            )
            # Returns: RestaurantQuery(cuisine="Italian", price_level="$")
        """
        pass

    @abstractmethod
    def fetch_options(self, query: DomainQuery) -> List[DomainResult]:
        """
        Fetch options from multiple providers.

        Calls external APIs (or mock clients) to get real-time options.
        Results should be cached if cache_service is available.

        Args:
            query: Structured domain query

        Returns:
            List of domain-specific result objects (subclass of DomainResult)

        Raises:
            requests.exceptions.RequestException: If API calls fail

        Example:
            # Rideshare - fetches from Uber and Lyft
            options = handler.fetch_options(ride_query)
            # Returns: [
            #   RideEstimate(provider="Uber", price=40.16),
            #   RideEstimate(provider="Lyft", price=41.83),
            #   ...
            # ]

            # Restaurant - fetches from Yelp and Google
            options = handler.fetch_options(restaurant_query)
            # Returns: [
            #   RestaurantOption(provider="Yelp", name="Joe's Pizza"),
            #   RestaurantOption(provider="Google", name="Lombardi's"),
            #   ...
            # ]
        """
        pass

    @abstractmethod
    def compare_options(
        self,
        options: List[DomainResult],
        priority: Optional[str] = "balanced"
    ) -> str:
        """
        AI-powered comparison and recommendation.

        Uses LLM to analyze options and provide natural language
        recommendation based on user priorities.

        Args:
            options: List of options from providers
            priority: User priority (e.g., "price", "time", "quality", "balanced")

        Returns:
            Natural language recommendation text

        Example:
            # Rideshare
            recommendation = handler.compare_options(
                [uber_est, lyft_est],
                priority="price"
            )
            # Returns: "Take Uber UberX at $40.16. It's the cheapest option
            #           and has a 5-minute pickup time."

            # Restaurant
            recommendation = handler.compare_options(
                [restaurant1, restaurant2],
                priority="quality"
            )
            # Returns: "Try Lombardi's Pizza. It has a 4.8 rating and is
            #           known for authentic Neapolitan pizza."
        """
        pass

    @abstractmethod
    def format_results(
        self,
        options: List[DomainResult],
        comparison: str
    ) -> Dict[str, Any]:
        """
        Format results for display in the UI.

        Transforms raw options and comparison into display-ready format
        (e.g., Rich tables, JSON for API, etc.).

        Args:
            options: List of options from providers
            comparison: Natural language recommendation

        Returns:
            Dictionary with formatted results for display

        Example:
            results = handler.format_results(options, comparison)
            # Returns: {
            #   "options": [
            #     {
            #       "provider": "Uber",
            #       "vehicle_type": "UberX",
            #       "price": "$40.16",
            #       "eta": "5 min"
            #     },
            #     ...
            #   ],
            #   "recommendation": "Take Uber UberX at $40.16...",
            #   "metadata": {
            #     "total_options": 6,
            #     "cache_hit": True
            #   }
            # }
        """
        pass

    def process(
        self,
        raw_query: str,
        context: Optional[Dict[str, Any]] = None,
        priority: Optional[str] = "balanced"
    ) -> Dict[str, Any]:
        """
        Main processing pipeline - orchestrates all steps.

        This is the primary public interface. It calls the abstract methods
        in order and handles the complete flow from raw query to formatted results.

        Args:
            raw_query: User's natural language request
            context: Optional context (user location, preferences)
            priority: User priority for comparison (default: "balanced")

        Returns:
            Formatted results ready for display

        Raises:
            ValueError: If query parsing fails
            requests.exceptions.RequestException: If API calls fail
            Exception: For other unexpected errors

        Example:
            handler = RideShareHandler()

            # Simple usage
            results = handler.process("Get me from Times Square to JFK")

            # With context and priority
            results = handler.process(
                "Find restaurants nearby",
                context={"user_location": "Manhattan"},
                priority="quality"
            )

            # Results structure:
            {
                "query": {...},           # Parsed query
                "options": [...],         # List of options
                "recommendation": "...",  # AI comparison
                "metadata": {...}         # Additional info
            }
        """
        # Step 1: Parse natural language into structured query
        query = self.parse_query(raw_query, context)

        # Step 2: Fetch options from multiple providers
        options = self.fetch_options(query)

        # Step 3: AI-powered comparison and recommendation
        comparison = self.compare_options(options, priority=priority)

        # Step 4: Format results for display
        results = self.format_results(options, comparison)

        # Add query to results for reference
        results["query"] = query

        return results

    def __repr__(self) -> str:
        """String representation for debugging."""
        class_name = self.__class__.__name__
        has_cache = "with cache" if self.cache else "no cache"
        has_geocoder = "with geocoder" if self.geocoder else "no geocoder"
        return f"{class_name}({has_cache}, {has_geocoder})"
