"""Multi-domain query router using AI to determine which domains to query."""

import json
from typing import List, Dict, Optional
from openai import OpenAI
import os


class DomainRouter:
    """
    Routes user queries to appropriate domain(s) using AI.

    Analyzes natural language queries to determine which domains
    (rideshare, restaurants, activities, hotels) should handle the query.

    Features:
    - Single-domain queries: "Get me a ride to JFK"
    - Multi-domain queries: "Find a ride and Italian restaurant"
    - Priority ordering: Most important domains first
    - Extensible: Easy to add new domains

    Example:
        router = DomainRouter()

        domains = router.route("Find me a ride to a good restaurant")
        # Returns: ["rideshare", "restaurants"]

        domains = router.route("Book a hotel near Times Square")
        # Returns: ["hotels"]
    """

    # Available domains with descriptions
    AVAILABLE_DOMAINS = {
        'rideshare': {
            'name': 'rideshare',
            'description': 'Transportation, rides, Uber, Lyft, taxis, getting from A to B',
            'keywords': ['ride', 'uber', 'lyft', 'taxi', 'transport', 'drive', 'car', 'get to', 'go to'],
            'enabled': True
        },
        'restaurants': {
            'name': 'restaurants',
            'description': 'Restaurants, dining, food, eating, cuisine types',
            'keywords': ['restaurant', 'food', 'eat', 'dining', 'lunch', 'dinner', 'cuisine', 'meal'],
            'enabled': True  # Set to True when restaurants domain is ready
        },
        'activities': {
            'name': 'activities',
            'description': 'Things to do, attractions, tours, entertainment, sightseeing',
            'keywords': ['activity', 'tour', 'attraction', 'museum', 'show', 'entertainment', 'visit', 'see'],
            'enabled': False  # Not yet implemented
        },
        'hotels': {
            'name': 'hotels',
            'description': 'Hotels, accommodation, lodging, places to stay',
            'keywords': ['hotel', 'stay', 'accommodation', 'lodging', 'sleep', 'room', 'booking'],
            'enabled': False  # Not yet implemented
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize domain router.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key required for domain routing")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

        # Build enabled domains list
        self.enabled_domains = {
            name: info for name, info in self.AVAILABLE_DOMAINS.items()
            if info['enabled']
        }

    def route(self, query: str, context: Optional[Dict] = None) -> List[str]:
        """
        Route a query to appropriate domain(s).

        Args:
            query: User's natural language query
            context: Optional context (location, preferences, etc.)

        Returns:
            List of domain names in priority order
            Empty list if no domains match

        Example:
            route("Find me a ride and a restaurant")
            → ["rideshare", "restaurants"]
        """
        # First try simple keyword matching (fast, no API call)
        keyword_match = self._keyword_match(query)

        print(f"[DomainRouter] Query: '{query}'")
        print(f"[DomainRouter] Keyword matches: {keyword_match}")

        # If only one domain matched, return it
        if len(keyword_match) == 1:
            print(f"[DomainRouter] Single match, using: {keyword_match}")
            return keyword_match

        # For ambiguous or multi-domain, use AI
        print(f"[DomainRouter] Multiple/no matches, using AI routing...")
        ai_result = self._ai_route(query, context)
        print(f"[DomainRouter] AI routing result: {ai_result}")
        return ai_result

    def _keyword_match(self, query: str) -> List[str]:
        """
        Simple keyword matching for fast routing.

        Args:
            query: User query

        Returns:
            List of domains that match keywords
        """
        query_lower = query.lower()
        matched_domains = []

        for domain_name, domain_info in self.enabled_domains.items():
            # Check if any keyword appears in query
            if any(keyword in query_lower for keyword in domain_info['keywords']):
                matched_domains.append(domain_name)

        return matched_domains

    def _ai_route(self, query: str, context: Optional[Dict] = None) -> List[str]:
        """
        Use AI to route query to domains.

        Args:
            query: User query
            context: Optional context

        Returns:
            List of domain names in priority order
        """
        # Build system prompt with available domains
        domains_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.enabled_domains.items()
        ])

        system_prompt = f"""You are a domain routing assistant for Hopwise, a travel app.

Available domains:
{domains_desc}

Your task: Analyze the user's query and determine which domain(s) should handle it.

Rules:
1. Return domains in order of importance (most important first)
2. Only return domains that are clearly relevant
3. For multi-domain queries, include all relevant domains
4. If unsure, prefer returning multiple domains over missing one

Respond with ONLY a JSON object:
{{
    "domains": ["domain1", "domain2"],
    "reasoning": "Brief explanation of why these domains"
}}"""

        user_prompt = f"Query: {query}"

        if context:
            user_prompt += f"\nContext: {json.dumps(context)}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate domains are enabled
            domains = [
                d for d in result.get('domains', [])
                if d in self.enabled_domains
            ]

            return domains

        except Exception as e:
            # Fallback to keyword matching if AI fails
            print(f"AI routing failed: {e}, falling back to keyword matching")
            return self._keyword_match(query)

    def get_enabled_domains(self) -> List[str]:
        """
        Get list of currently enabled domains.

        Returns:
            List of enabled domain names
        """
        return list(self.enabled_domains.keys())

    def is_multi_domain(self, domains: List[str]) -> bool:
        """
        Check if routing result indicates multi-domain query.

        Args:
            domains: List of domain names from route()

        Returns:
            True if multiple domains, False otherwise
        """
        return len(domains) > 1

    def __repr__(self) -> str:
        enabled = ", ".join(self.enabled_domains.keys())
        return f"DomainRouter(enabled_domains=[{enabled}])"


# Convenience function
def create_router(api_key: Optional[str] = None) -> DomainRouter:
    """
    Create a domain router instance.

    Args:
        api_key: Optional OpenAI API key

    Returns:
        DomainRouter instance
    """
    return DomainRouter(api_key=api_key)
