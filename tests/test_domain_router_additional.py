"""tests/test_domain_router.py

Tests for domain router.
"""

import sys
sys.path.insert(0, 'src')

import pytest
from unittest.mock import Mock, patch
from orchestration.domain_router import DomainRouter, create_router


@pytest.fixture
def router():
    """Create router for testing."""
    return create_router()


def test_router_initialization():
    """Test router initializes correctly."""
    router = DomainRouter()
    
    assert router is not None
    assert 'rideshare' in router.enabled_domains
    assert 'restaurants' in router.enabled_domains


def test_get_enabled_domains(router):
    """Test getting enabled domains list."""
    domains = router.get_enabled_domains()
    
    assert 'rideshare' in domains
    assert 'restaurants' in domains
    # activities and hotels disabled by default
    assert 'activities' not in domains
    assert 'hotels' not in domains


def test_keyword_match_rideshare(router):
    """Test keyword matching for rideshare queries."""
    # Test various ride-related queries
    assert router._keyword_match("Get me an Uber") == ['rideshare']
    assert router._keyword_match("I need a ride to JFK") == ['rideshare']
    assert router._keyword_match("Call me a taxi") == ['rideshare']


def test_keyword_match_restaurants(router):
    """Test keyword matching for restaurant queries."""
    assert router._keyword_match("Find me a restaurant") == ['restaurants']
    assert router._keyword_match("Where should I eat dinner") == ['restaurants']
    assert router._keyword_match("Good Italian food nearby") == ['restaurants']


def test_keyword_match_multi_domain(router):
    """Test keyword matching for multi-domain queries."""
    result = router._keyword_match("I need a ride to a restaurant")
    
    assert len(result) == 2
    assert 'rideshare' in result
    assert 'restaurants' in result


def test_route_single_domain_rideshare(router):
    """Test routing single domain query (rideshare)."""
    domains = router.route("Get me to Times Square")
    
    assert len(domains) >= 1
    assert 'rideshare' in domains


def test_route_single_domain_restaurants(router):
    """Test routing single domain query (restaurants)."""
    domains = router.route("Find me Italian food")
    
    assert len(domains) >= 1
    assert 'restaurants' in domains


def test_route_multi_domain(router):
    """Test routing multi-domain query."""
    domains = router.route("I need a ride to a good restaurant")
    
    # Should identify both domains
    assert len(domains) >= 2
    assert 'rideshare' in domains
    assert 'restaurants' in domains


def test_is_multi_domain(router):
    """Test multi-domain detection."""
    assert router.is_multi_domain(['rideshare', 'restaurants']) == True
    assert router.is_multi_domain(['rideshare']) == False
    assert router.is_multi_domain([]) == False


def test_router_with_context(router):
    """Test routing with context."""
    context = {'user_location': 'New York, NY'}
    
    domains = router.route("Find me a ride", context=context)
    
    assert 'rideshare' in domains


def test_route_empty_query(router):
    """Test routing with empty query."""
    domains = router.route("")
    
    # Should return empty list or handle gracefully
    assert isinstance(domains, list)


def test_route_ambiguous_query(router):
    """Test routing with ambiguous query."""
    # "Find me something good" is ambiguous
    domains = router.route("Find me something good")
    
    # Should either return multiple domains or handle gracefully
    assert isinstance(domains, list)


@patch('orchestration.domain_router.OpenAI')
def test_ai_routing_fallback(mock_openai, router):
    """Test AI routing falls back to keywords on error."""
    # Make AI fail
    mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
    
    # Should fall back to keyword matching
    domains = router.route("I need a ride and food")
    
    # Keyword matching should work
    assert 'rideshare' in domains or 'restaurants' in domains


def test_router_repr(router):
    """Test string representation."""
    repr_str = repr(router)
    
    assert 'DomainRouter' in repr_str
    assert 'rideshare' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])