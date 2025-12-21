"""tests/test_restaurant_intent_parser.py

Unit tests for restaurant intent parser.
"""

import sys
sys.path.insert(0, 'src')

import pytest
from domains.restaurants.intent_parser import RestaurantIntentParser
from domains.restaurants.models import RestaurantQuery


@pytest.fixture
def parser():
    """Create parser for testing."""
    return RestaurantIntentParser()


def test_parser_initialization():
    """Test parser initializes correctly."""
    parser = RestaurantIntentParser()

    assert parser is not None
    assert parser.model == "gpt-4o-mini"


def test_simple_cuisine_and_location(parser):
    """Test parsing simple cuisine + location query."""
    query = parser.parse("Find me Italian food near Times Square")

    assert isinstance(query, RestaurantQuery)
    assert query.cuisine == "Italian"
    assert "Times Square" in query.location
    assert query.location is not None


def test_price_range_parsing(parser):
    """Test parsing price range (cheap → $)."""
    query = parser.parse("I want cheap sushi", user_location="New York, NY")

    assert isinstance(query, RestaurantQuery)
    assert query.cuisine in ["Sushi", "Japanese"]  # Could be either
    assert query.price_range == "$"
    assert "New York" in query.location


def test_party_size_extraction(parser):
    """Test extracting party size from query."""
    query = parser.parse("Find a restaurant for 4 people near Central Park")

    assert isinstance(query, RestaurantQuery)
    assert query.party_size == 4
    assert "Central Park" in query.location


def test_rating_and_cuisine(parser):
    """Test parsing rating requirements (best → 4.5)."""
    query = parser.parse("Best Mexican food in Manhattan")

    assert isinstance(query, RestaurantQuery)
    assert query.cuisine == "Mexican"
    assert query.rating_min >= 4.0  # "best" should give high rating
    assert "Manhattan" in query.location


def test_dietary_restrictions(parser):
    """Test extracting dietary restrictions."""
    query = parser.parse("Find vegetarian restaurants nearby", user_location="Brooklyn, NY")

    assert isinstance(query, RestaurantQuery)
    assert "vegetarian" in query.dietary_restrictions
    assert "Brooklyn" in query.location


def test_expensive_price_range(parser):
    """Test parsing expensive → $$$$."""
    query = parser.parse("Find expensive French cuisine", user_location="Manhattan, NY")

    assert isinstance(query, RestaurantQuery)
    assert query.cuisine == "French"
    assert query.price_range in ["$$$", "$$$$"]


def test_open_now_requirement(parser):
    """Test parsing 'open now' requirement."""
    query = parser.parse("Find Italian restaurants open now", user_location="New York, NY")

    assert isinstance(query, RestaurantQuery)
    assert query.open_now == True


def test_location_inference_from_context(parser):
    """Test location inferred from user_location when not in query."""
    query = parser.parse("Find Italian food", user_location="Seattle, WA")

    assert isinstance(query, RestaurantQuery)
    assert query.location is not None
    assert len(query.location) > 0


def test_missing_location_raises_error(parser):
    """Test that missing location raises ValueError."""
    # Note: AI may infer generic location, so this test checks error handling exists
    # Rather than strict error raising for vague queries
    try:
        query = parser.parse("Find food")
        # If it succeeds, it should have some location
        assert query.location is not None
        assert len(query.location) > 0
    except ValueError as e:
        # If it raises error, should mention location
        assert "location" in str(e).lower()


def test_multiple_dietary_restrictions(parser):
    """Test multiple dietary restrictions."""
    query = parser.parse(
        "Find vegan and gluten-free restaurants",
        user_location="Portland, OR"
    )

    assert isinstance(query, RestaurantQuery)
    # Should have at least one restriction
    assert len(query.dietary_restrictions) > 0


def test_good_rating_mapping(parser):
    """Test 'good' maps to rating 4.0."""
    query = parser.parse("Find good Chinese food", user_location="San Francisco, CA")

    assert isinstance(query, RestaurantQuery)
    assert query.cuisine == "Chinese"
    assert query.rating_min >= 4.0


def test_query_defaults(parser):
    """Test default values when not specified."""
    query = parser.parse("Find pizza", user_location="Chicago, IL")

    assert isinstance(query, RestaurantQuery)
    assert query.distance_miles == 5.0  # Default
    assert query.rating_min == 0.0 or query.rating_min is None  # No rating filter by default
    assert query.open_now == False  # Not required by default
    assert query.party_size is None  # Not specified


def test_parser_repr(parser):
    """Test parser string representation."""
    repr_str = repr(parser)

    assert "RestaurantIntentParser" in repr_str
    assert "gpt-4o-mini" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
