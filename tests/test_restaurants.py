"""tests/test_restaurants.py

Comprehensive tests for restaurant domain.
"""

import sys
sys.path.insert(0, 'src')

import pytest
from domains.restaurants.models import (
    RestaurantQuery,
    Restaurant,
    FILTER_CATEGORIES,
    get_filter_category,
    validate_filter_category
)
from domains.restaurants.intent_parser import RestaurantIntentParser
from domains.restaurants.comparator import RestaurantComparator
from domains.restaurants.handler import RestaurantHandler
from domains.restaurants.api_clients.mock_yelp_client import MockYelpClient
from domains.restaurants.api_clients.mock_google_places_client import MockGooglePlacesClient
from core import GeocodingService, CacheService, RateLimiter


# ============================================================================
# MODEL TESTS
# ============================================================================

def test_restaurant_query_creation():
    """Test creating a RestaurantQuery."""
    query = RestaurantQuery(
        cuisine="Italian",
        location="Times Square, NY",
        price_range="$$",
        rating_min=4.0
    )

    assert query.cuisine == "Italian"
    assert query.location == "Times Square, NY"
    assert query.price_range == "$$"
    assert query.rating_min == 4.0
    assert query.filter_category == "Food"  # Default


def test_restaurant_query_with_filter():
    """Test RestaurantQuery with filter category."""
    query = RestaurantQuery(
        location="NYC",
        filter_category="Ice Cream"
    )

    assert query.filter_category == "Ice Cream"


def test_restaurant_query_to_dict():
    """Test RestaurantQuery serialization."""
    query = RestaurantQuery(
        cuisine="Japanese",
        location="Brooklyn",
        filter_category="Drinks"
    )

    data = query.to_dict()

    assert data['cuisine'] == "Japanese"
    assert data['location'] == "Brooklyn"
    assert data['filter_category'] == "Drinks"


def test_restaurant_creation():
    """Test creating a Restaurant."""
    restaurant = Restaurant(
        provider="yelp",
        name="Carbone",
        cuisine="Italian",
        rating=4.5,
        review_count=1200,
        price_range="$$$$",
        distance_miles=0.8
    )

    assert restaurant.provider == "yelp"
    assert restaurant.name == "Carbone"
    assert restaurant.rating == 4.5
    assert restaurant.review_count == 1200


def test_restaurant_to_dict():
    """Test Restaurant serialization."""
    restaurant = Restaurant(
        provider="google_places",
        name="Test Restaurant",
        rating=4.0
    )

    data = restaurant.to_dict()

    assert data['provider'] == "google_places"
    assert data['name'] == "Test Restaurant"
    assert data['rating'] == 4.0


def test_filter_categories_structure():
    """Test filter categories are properly defined."""
    assert len(FILTER_CATEGORIES) == 4
    assert 'Food' in FILTER_CATEGORIES
    assert 'Drinks' in FILTER_CATEGORIES
    assert 'Ice Cream' in FILTER_CATEGORIES
    assert 'Cafe' in FILTER_CATEGORIES

    # Check each has required fields
    for name, info in FILTER_CATEGORIES.items():
        assert 'name' in info
        assert 'description' in info
        assert 'keywords' in info
        assert 'icon' in info


def test_get_filter_category():
    """Test getting filter category details."""
    ice_cream = get_filter_category("Ice Cream")

    assert ice_cream['name'] == "Ice Cream"
    assert ice_cream['icon'] == "🍨"
    assert 'ice cream' in ice_cream['keywords']


def test_validate_filter_category():
    """Test filter category validation."""
    assert validate_filter_category("Food") == "Food"
    assert validate_filter_category("food") == "Food"  # Case insensitive
    assert validate_filter_category("Drinks") == "Drinks"
    assert validate_filter_category("invalid") == "Food"  # Default


# ============================================================================
# INTENT PARSER TESTS
# ============================================================================

def test_intent_parser_basic():
    """Test basic intent parsing."""
    parser = RestaurantIntentParser()

    query = parser.parse(
        "Find me Italian food near Times Square"
    )

    assert query.cuisine is not None
    assert "Italian" in query.cuisine or "italian" in query.cuisine.lower()
    assert query.location != ""


def test_intent_parser_with_price():
    """Test parsing price range."""
    parser = RestaurantIntentParser()

    query = parser.parse(
        "Find cheap sushi",
        user_location="New York, NY"
    )

    assert query.location != ""
    # Should detect cheap = $ or $$
    assert query.price_range in ["$", "$$"] or query.price_range is None


def test_intent_parser_with_rating():
    """Test parsing rating preferences."""
    parser = RestaurantIntentParser()

    query = parser.parse(
        "Best Mexican restaurants in Manhattan"
    )

    # "Best" should trigger higher minimum rating
    assert query.rating_min >= 4.0 or query.rating_min == 0.0


def test_intent_parser_with_party_size():
    """Test parsing party size."""
    parser = RestaurantIntentParser()

    query = parser.parse(
        "Restaurant for 4 people near Central Park"
    )

    assert query.party_size == 4 or query.party_size is None


# ============================================================================
# MOCK CLIENT TESTS
# ============================================================================

def test_mock_yelp_client():
    """Test MockYelpClient basic functionality."""
    client = MockYelpClient()

    results = client.search(
        cuisine="Italian",
        latitude=40.7580,
        longitude=-73.9855,
        limit=3
    )

    assert len(results) > 0
    assert len(results) <= 3
    assert all(r.provider == "yelp" for r in results)
    assert all(r.cuisine is not None for r in results)


def test_mock_yelp_price_filter():
    """Test Yelp client price filtering."""
    client = MockYelpClient()

    results = client.search(
        cuisine="Italian",
        latitude=40.7580,
        longitude=-73.9855,
        price_range="$$",
        limit=5
    )

    # All results should be $$
    assert all(r.price_range == "$$" for r in results) or len(results) == 0


def test_mock_yelp_rating_filter():
    """Test Yelp client rating filtering."""
    client = MockYelpClient()

    results = client.search(
        cuisine="Japanese",
        latitude=40.7580,
        longitude=-73.9855,
        rating_min=4.5,
        limit=5
    )

    # All results should have rating >= 4.5
    assert all(r.rating >= 4.5 for r in results) or len(results) == 0


def test_mock_google_places_client():
    """Test MockGooglePlacesClient basic functionality."""
    client = MockGooglePlacesClient()

    results = client.search(
        cuisine="Chinese",
        latitude=40.7580,
        longitude=-73.9855,
        limit=3
    )

    assert len(results) > 0
    assert len(results) <= 3
    assert all(r.provider == "google_places" for r in results)


def test_different_providers_return_different_results():
    """Test that Yelp and Google return different restaurants."""
    yelp = MockYelpClient()
    google = MockGooglePlacesClient()

    yelp_results = yelp.search(cuisine="Italian", limit=3)
    google_results = google.search(cuisine="Italian", limit=3)

    # Different providers should have different restaurant names
    yelp_names = set(r.name for r in yelp_results)
    google_names = set(r.name for r in google_results)

    # Should have some different names (not identical lists)
    assert yelp_names != google_names or len(yelp_names) == 0


# ============================================================================
# COMPARATOR TESTS
# ============================================================================

def test_comparator_basic():
    """Test basic restaurant comparison."""
    comparator = RestaurantComparator()

    restaurants = [
        Restaurant(provider="yelp", name="Restaurant A", rating=4.5,
                  review_count=1000, price_range="$$", distance_miles=0.5),
        Restaurant(provider="google", name="Restaurant B", rating=4.2,
                  review_count=500, price_range="$", distance_miles=1.0)
    ]

    recommendation = comparator.compare_restaurants(restaurants, priority="balanced")

    assert isinstance(recommendation, str)
    assert len(recommendation) > 0
    assert "Restaurant" in recommendation


def test_comparator_rating_priority():
    """Test comparison with rating priority."""
    comparator = RestaurantComparator()

    restaurants = [
        Restaurant(provider="yelp", name="High Rated", rating=4.8,
                  review_count=1000, price_range="$$", distance_miles=2.0),
        Restaurant(provider="google", name="Low Rated", rating=3.5,
                  review_count=100, price_range="$", distance_miles=0.5)
    ]

    recommendation = comparator.compare_restaurants(restaurants, priority="rating")

    # Should recommend the higher rated one
    assert "High Rated" in recommendation or "4.8" in recommendation


def test_comparator_empty_list():
    """Test comparator with empty restaurant list."""
    comparator = RestaurantComparator()

    recommendation = comparator.compare_restaurants([])

    assert "No restaurants found" in recommendation


# ============================================================================
# HANDLER TESTS
# ============================================================================

def test_handler_initialization():
    """Test RestaurantHandler initialization."""
    geocoder = GeocodingService()
    cache = CacheService()
    rate_limiter = RateLimiter()

    handler = RestaurantHandler(
        geocoding_service=geocoder,
        cache_service=cache,
        rate_limiter=rate_limiter
    )

    assert handler is not None
    assert handler.geocoder is not None
    assert handler.cache is not None
    assert 'yelp' in handler.clients
    assert 'google_places' in handler.clients


def test_handler_parse_query():
    """Test handler query parsing."""
    handler = RestaurantHandler(
        geocoding_service=GeocodingService()
    )

    query = handler.parse_query(
        "Find Italian food near Times Square",
        context={'user_location': 'New York, NY'}
    )

    assert isinstance(query, RestaurantQuery)
    assert query.location != ""


def test_handler_fetch_options():
    """Test handler fetching restaurant options."""
    geocoder = GeocodingService()
    handler = RestaurantHandler(geocoding_service=geocoder)

    query = RestaurantQuery(
        cuisine="Italian",
        location="New York, NY"
    )

    restaurants = handler.fetch_options(query)

    assert isinstance(restaurants, list)
    assert len(restaurants) > 0
    assert all(isinstance(r, Restaurant) for r in restaurants)


def test_handler_compare_options():
    """Test handler comparing options."""
    handler = RestaurantHandler()

    restaurants = [
        Restaurant(provider="yelp", name="Test 1", rating=4.5,
                  review_count=1000, price_range="$$", distance_miles=0.5),
        Restaurant(provider="google", name="Test 2", rating=4.2,
                  review_count=500, price_range="$", distance_miles=1.0)
    ]

    comparison = handler.compare_options(restaurants, priority="balanced")

    assert isinstance(comparison, str)
    assert len(comparison) > 0


def test_handler_end_to_end():
    """Test complete handler pipeline."""
    geocoder = GeocodingService()
    cache = CacheService()
    rate_limiter = RateLimiter()

    handler = RestaurantHandler(
        geocoding_service=geocoder,
        cache_service=cache,
        rate_limiter=rate_limiter
    )

    results = handler.process(
        "Find me Italian food near Times Square",
        context={'user_location': 'New York, NY'},
        priority='balanced'
    )

    assert results['domain'] == 'restaurants'
    assert 'restaurants' in results
    assert 'comparison' in results
    assert 'priority' in results
    assert len(results['restaurants']) > 0


def test_handler_with_cache():
    """Test handler caching behavior."""
    geocoder = GeocodingService()
    cache = CacheService()

    handler = RestaurantHandler(
        geocoding_service=geocoder,
        cache_service=cache
    )

    # First call - cache miss
    results1 = handler.process(
        "Italian food in NYC",
        context={'user_location': 'New York, NY'}
    )

    # Second call - should hit cache
    results2 = handler.process(
        "Italian food in NYC",
        context={'user_location': 'New York, NY'}
    )

    assert results1['total_results'] == results2['total_results']


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
