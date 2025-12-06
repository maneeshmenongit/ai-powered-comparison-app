"""tests/test_rideshare_handler_unit.py

Unit tests for RideShare domain handler with mocking.
"""

import sys
sys.path.insert(0, 'src')

import pytest
from unittest.mock import Mock, MagicMock, patch
from domains.rideshare import RideShareHandler, RideQuery, RideEstimate
from datetime import datetime


@pytest.fixture
def mock_geocoder():
    """Mock geocoding service."""
    geocoder = Mock()
    geocoder.geocode = Mock(side_effect=[
        (40.7580, -73.9855, "Times Square, NYC"),  # Origin
        (40.6413, -73.7781, "JFK Airport, NYC"),   # Destination
    ])
    return geocoder


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = Mock()
    cache.get = Mock(return_value=None)  # Cache miss by default
    cache.set = Mock()
    return cache


@pytest.fixture
def handler(mock_cache, mock_geocoder):
    """Create RideShareHandler with mocked services."""
    return RideShareHandler(
        cache_service=mock_cache,
        geocoding_service=mock_geocoder
    )


@pytest.fixture
def sample_estimates():
    """Sample ride estimates for testing."""
    return [
        RideEstimate(
            provider="Uber",
            vehicle_type="UberX",
            price_estimate=25.0,
            price_low=22.0,
            price_high=28.0,
            duration_minutes=30,
            pickup_eta_minutes=5,
            distance_miles=15.0,
            origin_coords=(40.7580, -73.9855),
            destination_coords=(40.6413, -73.7781),
            surge_multiplier=1.0,
            currency="USD",
            is_available=True,
            last_updated=datetime.now()
        ),
        RideEstimate(
            provider="Lyft",
            vehicle_type="Lyft",
            price_estimate=23.0,
            price_low=20.0,
            price_high=26.0,
            duration_minutes=32,
            pickup_eta_minutes=4,
            distance_miles=15.0,
            origin_coords=(40.7580, -73.9855),
            destination_coords=(40.6413, -73.7781),
            surge_multiplier=1.0,
            currency="USD",
            is_available=True,
            last_updated=datetime.now()
        )
    ]


def test_rideshare_handler_initialization():
    """Test RideShareHandler initializes correctly."""
    handler = RideShareHandler()

    assert handler is not None
    assert handler.parser is not None
    assert handler.comparator is not None
    assert 'uber' in handler.clients
    assert 'lyft' in handler.clients


def test_rideshare_handler_initialization_with_services():
    """Test RideShareHandler initialization with services."""
    mock_cache = Mock()
    mock_geocoder = Mock()

    handler = RideShareHandler(
        cache_service=mock_cache,
        geocoding_service=mock_geocoder
    )

    assert handler.cache == mock_cache
    assert handler.geocoder == mock_geocoder


def test_parse_query(handler):
    """Test query parsing."""
    with patch.object(handler.parser, 'parse_query') as mock_parse:
        mock_parse.return_value = RideQuery(
            origin="Times Square",
            destination="JFK Airport",
            providers=["uber", "lyft"],
            vehicle_type="standard"
        )

        query = handler.parse_query(
            "Get me from Times Square to JFK",
            context={'user_location': 'New York, NY'}
        )

        assert isinstance(query, RideQuery)
        assert query.origin == "Times Square"
        assert query.destination == "JFK Airport"
        mock_parse.assert_called_once()


def test_parse_query_missing_origin():
    """Test that parse_query raises error when origin is missing."""
    handler = RideShareHandler()

    with pytest.raises(ValueError, match="origin"):
        handler.parse_query("I want to go to JFK")


def test_fetch_options_calls_geocoder(handler, mock_geocoder):
    """Test that fetch_options calls geocoder."""
    query = RideQuery(
        origin="Times Square",
        destination="JFK Airport",
        providers=["uber", "lyft"],
        vehicle_type="standard"
    )

    estimates = handler.fetch_options(query)

    # Verify geocoder was called twice (origin and destination)
    assert mock_geocoder.geocode.call_count == 2
    assert len(estimates) > 0


def test_fetch_options_without_geocoder():
    """Test that fetch_options raises error without geocoder."""
    handler = RideShareHandler()  # No geocoder

    query = RideQuery(
        origin="Times Square",
        destination="JFK Airport",
        providers=["uber"],
        vehicle_type="standard"
    )

    with pytest.raises(ValueError, match="Geocoding service required"):
        handler.fetch_options(query)


def test_fetch_options_returns_estimates(handler):
    """Test that fetch_options returns RideEstimate objects."""
    query = RideQuery(
        origin="Times Square",
        destination="JFK Airport",
        providers=["uber", "lyft"],
        vehicle_type="standard"
    )

    estimates = handler.fetch_options(query)

    assert isinstance(estimates, list)
    assert len(estimates) >= 1
    assert all(isinstance(e, RideEstimate) for e in estimates)


def test_fetch_options_uses_cache(handler, mock_cache, sample_estimates):
    """Test that fetch_options uses cache when available."""
    # Set up cache to return cached data
    mock_cache.get = Mock(return_value=sample_estimates)

    query = RideQuery(
        origin="Times Square",
        destination="JFK Airport",
        providers=["uber"],
        vehicle_type="standard"
    )

    estimates = handler.fetch_options(query)

    # Should return cached data
    assert estimates == sample_estimates
    assert mock_cache.get.called
    # Geocoder should still be called for cache key generation
    assert handler.geocoder.geocode.call_count == 2


def test_fetch_options_caches_results(handler, mock_cache):
    """Test that fetch_options caches results on cache miss."""
    query = RideQuery(
        origin="Times Square",
        destination="JFK Airport",
        providers=["uber"],
        vehicle_type="standard"
    )

    estimates = handler.fetch_options(query)

    # Verify cache.set was called with results
    assert mock_cache.set.called
    call_args = mock_cache.set.call_args
    assert len(call_args[0]) == 2  # key and value
    assert isinstance(call_args[0][1], list)  # value is list of estimates


def test_compare_options(handler, sample_estimates):
    """Test AI comparison of options."""
    comparison = handler.compare_options(sample_estimates, priority="price")

    assert isinstance(comparison, str)
    assert len(comparison) > 0


def test_compare_options_with_different_priorities(handler, sample_estimates):
    """Test comparison with different priority values."""
    priorities = ["price", "time", "balanced"]

    for priority in priorities:
        comparison = handler.compare_options(sample_estimates, priority=priority)
        assert isinstance(comparison, str)
        assert len(comparison) > 0


def test_format_results(handler, sample_estimates):
    """Test result formatting."""
    comparison = "Uber is recommended"

    results = handler.format_results(sample_estimates, comparison)

    assert 'domain' in results
    assert results['domain'] == 'rideshare'
    assert 'estimates' in results
    assert 'comparison' in results
    assert 'route' in results
    assert 'summary' in results
    assert len(results['estimates']) == 2


def test_format_results_summary(handler, sample_estimates):
    """Test that format_results includes proper summary."""
    comparison = "Test recommendation"

    results = handler.format_results(sample_estimates, comparison)

    summary = results['summary']
    assert 'total_options' in summary
    assert 'available_options' in summary
    assert 'price_range' in summary
    assert 'providers' in summary
    assert 'has_surge' in summary

    assert summary['total_options'] == 2
    assert summary['available_options'] == 2
    assert 'Uber' in summary['providers']
    assert 'Lyft' in summary['providers']


def test_format_results_route_info(handler, sample_estimates):
    """Test that format_results includes route information."""
    comparison = "Test recommendation"

    results = handler.format_results(sample_estimates, comparison)

    route = results['route']
    assert 'origin' in route
    assert 'destination' in route
    assert 'distance_miles' in route

    assert route['origin'] == (40.7580, -73.9855)
    assert route['destination'] == (40.6413, -73.7781)
    assert route['distance_miles'] == 15.0


def test_full_process_pipeline(handler):
    """Test the complete process pipeline end-to-end."""
    with patch.object(handler.parser, 'parse_query') as mock_parse:
        mock_parse.return_value = RideQuery(
            origin="Times Square",
            destination="JFK Airport",
            providers=["uber", "lyft"],
            vehicle_type="standard"
        )

        results = handler.process(
            "Get me from Times Square to JFK Airport",
            context={'user_location': 'New York, NY'},
            priority='balanced'
        )

        assert 'domain' in results
        assert 'estimates' in results
        assert 'comparison' in results
        assert 'route' in results
        assert 'query' in results
        assert results['domain'] == 'rideshare'


def test_generate_cache_key(handler):
    """Test cache key generation."""
    key1 = handler._generate_cache_key(40.7580, -73.9855, 40.6413, -73.7781)
    key2 = handler._generate_cache_key(40.7580, -73.9855, 40.6413, -73.7781)
    key3 = handler._generate_cache_key(40.7580, -73.9855, 41.0000, -74.0000)

    # Same coordinates should generate same key
    assert key1 == key2

    # Different coordinates should generate different key
    assert key1 != key3

    # Key should be reasonable length (MD5 truncated to 16 chars)
    assert len(key1) == 16


def test_handler_repr(handler):
    """Test handler string representation."""
    repr_str = repr(handler)

    assert isinstance(repr_str, str)
    assert 'RideShareHandler' in repr_str
    assert 'providers' in repr_str
    assert 'uber' in repr_str or 'lyft' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
