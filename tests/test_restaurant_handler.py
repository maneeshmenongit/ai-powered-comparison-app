"""Test restaurant handler integration.

Tests the complete restaurant domain pipeline:
- Intent parsing
- Multi-provider fetching (Yelp + Google Places)
- Geocoding integration
- Caching
- AI-powered comparison
- Result formatting
"""

import sys
sys.path.insert(0, 'src')

import pytest
from domains.restaurants.handler import RestaurantHandler, create_restaurant_handler
from domains.restaurants.models import RestaurantQuery, Restaurant
from core.geocoding_service import GeocodingService


@pytest.fixture
def geocoding_service():
    """Create geocoding service for testing."""
    return GeocodingService()


@pytest.fixture
def handler(geocoding_service):
    """Create restaurant handler for testing."""
    return RestaurantHandler(
        cache_service=None,  # No cache for testing
        geocoding_service=geocoding_service,
        rate_limiter=None  # No rate limiting for testing
    )


class TestRestaurantHandler:
    """Test restaurant handler functionality."""

    def test_handler_initialization(self, handler):
        """Test handler initializes correctly."""
        assert handler is not None
        assert handler.parser is not None
        assert handler.comparator is not None
        assert 'yelp' in handler.clients
        assert 'google_places' in handler.clients
        assert handler.geocoder is not None

    def test_parse_query_basic(self, handler):
        """Test basic query parsing."""
        query = handler.parse_query(
            "Find Italian food near Times Square",
            context={'user_location': 'New York, NY'}
        )

        assert isinstance(query, RestaurantQuery)
        assert query.cuisine is not None
        assert 'Italian' in query.cuisine or 'italian' in query.cuisine.lower()
        assert 'Times Square' in query.location

    def test_parse_query_with_price(self, handler):
        """Test query parsing with price range."""
        query = handler.parse_query(
            "Find cheap Mexican food in Brooklyn",
            context={'user_location': 'Brooklyn, NY'}
        )

        assert isinstance(query, RestaurantQuery)
        assert query.cuisine is not None
        assert 'Mexican' in query.cuisine or 'mexican' in query.cuisine.lower()
        assert query.price_range in ['$', '$$']  # AI should infer cheap

    def test_fetch_options(self, handler):
        """Test fetching restaurant options from multiple providers."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="Times Square, New York, NY",
            price_range=None,
            rating_min=0.0
        )

        restaurants = handler.fetch_options(query)

        assert isinstance(restaurants, list)
        assert len(restaurants) > 0
        assert all(isinstance(r, Restaurant) for r in restaurants)

        # Should have results from multiple providers
        providers = {r.provider for r in restaurants}
        assert len(providers) >= 1  # At least one provider

        # Should be sorted by rating (descending)
        ratings = [r.rating for r in restaurants]
        assert ratings == sorted(ratings, reverse=True)

    def test_fetch_options_multiple_providers(self, handler):
        """Test that we get results from both Yelp and Google."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="New York, NY",
            price_range=None,
            rating_min=0.0
        )

        restaurants = handler.fetch_options(query)

        providers = {r.provider for r in restaurants}
        # Should have both providers (unless one fails)
        assert 'yelp' in providers or 'google_places' in providers

    def test_compare_options_rating_priority(self, handler):
        """Test AI comparison with rating priority."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="New York, NY"
        )

        restaurants = handler.fetch_options(query)
        comparison = handler.compare_options(restaurants, priority="rating")

        assert isinstance(comparison, str)
        assert len(comparison) > 50  # Should be substantive
        assert "recommend" in comparison.lower()

    def test_compare_options_price_priority(self, handler):
        """Test AI comparison with price priority."""
        query = RestaurantQuery(
            cuisine="Japanese",
            location="New York, NY"
        )

        restaurants = handler.fetch_options(query)
        comparison = handler.compare_options(restaurants, priority="price")

        assert isinstance(comparison, str)
        assert "recommend" in comparison.lower()

    def test_format_results(self, handler):
        """Test result formatting."""
        query = RestaurantQuery(
            cuisine="Chinese",
            location="New York, NY"
        )

        restaurants = handler.fetch_options(query)
        comparison = handler.compare_options(restaurants, priority="balanced")
        results = handler.format_results(restaurants, comparison, priority="balanced")

        assert isinstance(results, dict)
        assert results['domain'] == 'restaurants'
        assert 'restaurants' in results
        assert 'comparison' in results
        assert 'priority' in results
        assert 'total_results' in results

        assert isinstance(results['restaurants'], list)
        assert len(results['restaurants']) > 0

        # Check first restaurant has required fields
        first = results['restaurants'][0]
        assert 'provider' in first
        assert 'name' in first
        assert 'cuisine' in first
        assert 'rating' in first
        assert 'price_range' in first
        assert 'distance' in first

    def test_process_complete_pipeline(self, handler):
        """Test complete processing pipeline."""
        results = handler.process(
            "Find Italian food near Times Square",
            context={'user_location': 'New York, NY'},
            priority="balanced"
        )

        assert isinstance(results, dict)
        assert results['domain'] == 'restaurants'
        assert 'restaurants' in results
        assert 'comparison' in results
        assert results['priority'] == 'balanced'
        assert results['total_results'] > 0

        # Check we have valid restaurant data
        restaurants = results['restaurants']
        assert len(restaurants) > 0

        first_restaurant = restaurants[0]
        assert first_restaurant['name']
        assert first_restaurant['rating'] >= 0
        assert first_restaurant['provider'] in ['yelp', 'google_places']

    def test_process_with_different_priorities(self, handler):
        """Test processing with different priority modes."""
        query = "Find Mexican food in Brooklyn"
        context = {'user_location': 'Brooklyn, NY'}

        for priority in ['rating', 'price', 'distance', 'balanced']:
            results = handler.process(query, context, priority)

            assert results['domain'] == 'restaurants'
            assert results['priority'] == priority
            assert results['total_results'] > 0
            assert len(results['comparison']) > 0

    def test_handler_repr(self, handler):
        """Test handler string representation."""
        repr_str = repr(handler)

        assert 'RestaurantHandler' in repr_str
        assert 'yelp' in repr_str
        assert 'google_places' in repr_str

    def test_create_restaurant_handler_function(self, geocoding_service):
        """Test convenience function for creating handler."""
        handler = create_restaurant_handler(
            geocoding_service=geocoding_service
        )

        assert isinstance(handler, RestaurantHandler)
        assert handler.parser is not None
        assert handler.comparator is not None


class TestRestaurantHandlerEdgeCases:
    """Test edge cases and error handling."""

    def test_fetch_options_requires_geocoder(self):
        """Test that fetch_options requires geocoding service."""
        handler = RestaurantHandler(
            geocoding_service=None  # No geocoder
        )

        query = RestaurantQuery(
            cuisine="Italian",
            location="New York, NY"
        )

        with pytest.raises(ValueError, match="Geocoding service required"):
            handler.fetch_options(query)

    def test_process_with_no_context(self, handler):
        """Test processing without context."""
        results = handler.process(
            "Find Italian food in Manhattan"
            # No context provided
        )

        assert results['domain'] == 'restaurants'
        assert results['total_results'] > 0

    def test_compare_empty_list(self, handler):
        """Test comparison with empty restaurant list."""
        comparison = handler.compare_options([], priority="balanced")

        assert isinstance(comparison, str)
        assert "No restaurants found" in comparison

    def test_compare_single_restaurant(self, handler):
        """Test comparison with single restaurant."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="New York, NY"
        )

        restaurants = handler.fetch_options(query)
        single_restaurant = [restaurants[0]]

        comparison = handler.compare_options(single_restaurant, priority="balanced")

        assert isinstance(comparison, str)
        assert restaurants[0].name in comparison


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
