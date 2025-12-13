"""src/domains/restaurants/intent_parser.py

Natural language intent parser for restaurant queries.
"""

import json
from typing import Optional, Dict
from openai import OpenAI
import os

from domains.restaurants.models import RestaurantQuery


class RestaurantIntentParser:
    """
    Parses natural language restaurant queries into structured RestaurantQuery objects.

    Uses OpenAI GPT-4o-mini to understand queries like:
    - "Find me Italian food near Times Square"
    - "I want cheap sushi for 4 people"
    - "Best restaurants with vegetarian options"

    Features:
    - Cuisine extraction (Italian, Chinese, Japanese, etc.)
    - Location inference from context
    - Price range detection ($, $$, $$$, $$$$)
    - Party size extraction
    - Dietary restrictions detection
    - Rating preferences

    Example:
        parser = RestaurantIntentParser()
        query = parser.parse(
            "Find me good Italian food near Times Square",
            user_location="New York, NY"
        )
        # Returns: RestaurantQuery(cuisine="Italian", location="Times Square, NY", ...)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize intent parser.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key required for intent parsing")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def parse(self, query: str, user_location: Optional[str] = None) -> RestaurantQuery:
        """
        Parse natural language query into RestaurantQuery.

        Args:
            query: User's natural language query
            user_location: User's current location for context

        Returns:
            RestaurantQuery object with extracted parameters

        Raises:
            ValueError: If query is too vague or missing critical info

        Example:
            parse("Find Italian food near Times Square")
            → RestaurantQuery(cuisine="Italian", location="Times Square, NY", ...)
        """
        system_prompt = """You are a restaurant search query parser for Hopwise.
Every stop matters! Hop smarter!

Extract restaurant search parameters from user queries.

CUISINE TYPES (examples):
- Italian, Chinese, Japanese, Mexican, Indian, Thai, French
- American, Mediterranean, Korean, Vietnamese
- Sushi, Pizza, Burgers, Steakhouse, Seafood

PRICE RANGES:
- $ = Cheap/Budget (under $15 per person)
- $$ = Moderate ($15-30 per person)
- $$$ = Upscale ($30-60 per person)
- $$$$ = Fine dining (over $60 per person)

COMMON TERMS:
- "cheap" = $
- "affordable", "reasonable" = $$
- "nice", "good" = $$
- "upscale", "fancy" = $$$
- "fine dining", "expensive" = $$$$

DIETARY RESTRICTIONS:
- vegetarian, vegan, gluten-free, halal, kosher, etc.

LOCATION INFERENCE:
- If user says "near me" or "nearby" and user_location provided, use that
- If user mentions specific area (Times Square, downtown), use that
- Common shortcuts: "downtown" = city center, "airport" = nearest airport

RATING:
- "good" = 4.0+ stars
- "great", "excellent", "best" = 4.5+ stars
- No mention = 0.0 (any rating)

RESPOND WITH JSON ONLY:
{
    "cuisine": "Italian" or null,
    "location": "Times Square, NY" (required!),
    "price_range": "$" or "$$" or "$$$" or "$$$$" or null,
    "rating_min": 4.0 (number),
    "distance_miles": 5.0 (number),
    "party_size": 4 (number) or null,
    "dietary_restrictions": ["vegetarian", "gluten-free"] or [],
    "open_now": true/false
}

IMPORTANT:
- location is REQUIRED - infer from context if not explicit
- If query is too vague, make reasonable assumptions
- Default distance_miles: 5.0
- Default rating_min: 0.0 (no filter)
- Default open_now: false
"""

        user_prompt = f"Query: {query}"
        if user_location:
            user_prompt += f"\nUser Location: {user_location}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,  # Deterministic
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate location
            if not result.get('location'):
                raise ValueError("Could not determine location. Please specify where to search.")

            # Create RestaurantQuery
            return RestaurantQuery(
                cuisine=result.get('cuisine'),
                location=result.get('location', ''),
                price_range=result.get('price_range'),
                rating_min=result.get('rating_min', 0.0),
                distance_miles=result.get('distance_miles', 5.0),
                party_size=result.get('party_size'),
                dietary_restrictions=result.get('dietary_restrictions', []),
                open_now=result.get('open_now', False)
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse query: {e}")

    def __repr__(self) -> str:
        return f"RestaurantIntentParser(model={self.model})"


# Convenience function
def parse_restaurant_query(query: str, user_location: Optional[str] = None) -> RestaurantQuery:
    """
    Parse a restaurant query using the intent parser.

    Args:
        query: Natural language query
        user_location: Optional user location

    Returns:
        RestaurantQuery object
    """
    parser = RestaurantIntentParser()
    return parser.parse(query, user_location)
