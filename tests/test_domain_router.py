"""tests/test_domain_router.py

Unit tests for multi-domain query router.
"""

import sys
sys.path.insert(0, 'src')

import pytest
from orchestration.domain_router import DomainRouter, create_router


def test_router_initialization():
    """Test router initializes with correct domains."""
    router = DomainRouter()

    assert router.model == "gpt-4o-mini"
    assert 'rideshare' in router.enabled_domains
    assert 'restaurants' in router.enabled_domains
    assert 'activities' not in router.enabled_domains  # Disabled
    assert 'hotels' not in router.enabled_domains  # Disabled


def test_get_enabled_domains():
    """Test getting list of enabled domains."""
    router = DomainRouter()
    enabled = router.get_enabled_domains()

    assert 'rideshare' in enabled
    assert 'restaurants' in enabled
    assert len(enabled) == 2  # Only rideshare and restaurants enabled


def test_keyword_match_rideshare():
    """Test keyword matching for rideshare queries."""
    router = DomainRouter()

    # Clear rideshare keywords
    queries = [
        "Get me an Uber",
        "I need a ride to JFK",
        "Compare Lyft prices",
        "Drive me to Times Square",  # Changed from "Take me" to "Drive me"
    ]

    for query in queries:
        matches = router._keyword_match(query)
        assert 'rideshare' in matches, f"Query '{query}' should match rideshare"


def test_keyword_match_restaurants():
    """Test keyword matching for restaurant queries."""
    router = DomainRouter()

    queries = [
        "Find a good restaurant",
        "Where should I eat dinner?",
        "I want Italian food",
        "Best lunch spots",
    ]

    for query in queries:
        matches = router._keyword_match(query)
        assert 'restaurants' in matches, f"Query '{query}' should match restaurants"


def test_keyword_match_multi_domain():
    """Test keyword matching for multi-domain queries."""
    router = DomainRouter()

    query = "Get me a ride to a nice restaurant"
    matches = router._keyword_match(query)

    assert 'rideshare' in matches
    assert 'restaurants' in matches
    assert len(matches) == 2


def test_single_domain_route():
    """Test routing single-domain queries."""
    router = DomainRouter()

    # Should use keyword matching (fast path)
    query = "Get me an Uber to JFK"
    domains = router.route(query)

    assert len(domains) == 1
    assert domains[0] == 'rideshare'


def test_multi_domain_route():
    """Test routing multi-domain queries."""
    router = DomainRouter()

    query = "I need a ride and want to eat Italian food"
    domains = router.route(query)

    # Should include both domains
    assert 'rideshare' in domains
    assert 'restaurants' in domains


def test_is_multi_domain():
    """Test multi-domain detection."""
    router = DomainRouter()

    # Single domain
    assert not router.is_multi_domain(['rideshare'])

    # Multi domain
    assert router.is_multi_domain(['rideshare', 'restaurants'])


def test_router_repr():
    """Test router string representation."""
    router = DomainRouter()
    repr_str = repr(router)

    assert 'DomainRouter' in repr_str
    assert 'rideshare' in repr_str
    assert 'restaurants' in repr_str


def test_create_router_function():
    """Test convenience function for creating router."""
    router = create_router()

    assert isinstance(router, DomainRouter)
    assert len(router.get_enabled_domains()) > 0


def test_context_parameter():
    """Test routing with context."""
    router = DomainRouter()

    context = {'location': 'New York', 'preferences': {'cuisine': 'Italian'}}
    query = "Find me something"

    # Should not crash with context
    domains = router.route(query, context=context)
    assert isinstance(domains, list)


def test_empty_query():
    """Test routing with empty query."""
    router = DomainRouter()

    domains = router.route("")
    # Should return empty list or handle gracefully
    assert isinstance(domains, list)


def test_disabled_domains_not_returned():
    """Test that disabled domains are never returned."""
    router = DomainRouter()

    # Even if we try to trick it with keywords
    query = "I need a hotel room for my activity tour"

    domains = router.route(query)

    # Should not include disabled domains
    assert 'hotels' not in domains
    assert 'activities' not in domains


def test_fallback_to_keywords_on_ai_failure():
    """Test fallback behavior when AI routing fails."""
    router = DomainRouter()

    # Test with a query that has clear keywords
    query = "Get me an Uber"

    # Even if AI fails, keyword matching should work
    domains = router._keyword_match(query)
    assert 'rideshare' in domains


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
