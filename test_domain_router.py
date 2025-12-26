"""Test script for domain router debugging."""

import os
from src.orchestration.domain_router import DomainRouter

# Test queries
test_queries = [
    "need a ride to times square",
    "find me Italian food",
    "uber to central park",
    "best pizza near me",
    "get me to JFK airport",
    "hungry for Chinese food",
]

def test_routing():
    """Test domain routing with various queries."""
    router = DomainRouter()

    print("=" * 60)
    print("DOMAIN ROUTER DEBUG TEST")
    print("=" * 60)
    print(f"\nEnabled domains: {router.get_enabled_domains()}\n")

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)

        # Test keyword matching
        keyword_matches = router._keyword_match(query)
        print(f"Keyword matches: {keyword_matches}")

        # Test full routing
        routed_domains = router.route(query)
        print(f"Final routing: {routed_domains}")

        # Show which keywords matched
        query_lower = query.lower()
        for domain_name, domain_info in router.enabled_domains.items():
            matched_keywords = [
                kw for kw in domain_info['keywords']
                if kw in query_lower
            ]
            if matched_keywords:
                print(f"  {domain_name}: matched keywords = {matched_keywords}")

        print()

if __name__ == "__main__":
    test_routing()
