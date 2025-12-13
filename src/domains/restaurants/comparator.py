"""src/domains/restaurants/comparator.py

AI-powered restaurant comparison and recommendation.
"""

import json
from typing import List, Optional
from openai import OpenAI
import os

from domains.restaurants.models import Restaurant


class RestaurantComparator:
    """
    AI-powered restaurant comparison using GPT-4o-mini.

    Analyzes multiple restaurant options and provides intelligent
    recommendations based on ratings, price, distance, and reviews.

    Features:
    - Rating-focused recommendations
    - Price-conscious suggestions
    - Distance-aware advice
    - Review count consideration
    - Natural language explanations

    Example:
        comparator = RestaurantComparator()
        recommendation = comparator.compare_restaurants(
            restaurants=[rest1, rest2, rest3],
            priority="rating"
        )
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize restaurant comparator.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key required for comparison")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def compare_restaurants(
        self,
        restaurants: List[Restaurant],
        priority: str = "balanced"
    ) -> str:
        """
        Compare restaurants and provide AI recommendation.

        Args:
            restaurants: List of Restaurant objects to compare
            priority: Comparison priority
                - "rating": Focus on highest ratings
                - "price": Focus on best value/cheapest
                - "distance": Focus on closest options
                - "balanced": Overall best choice (default)

        Returns:
            Natural language recommendation (3-4 sentences)

        Example:
            compare_restaurants([rest1, rest2], priority="rating")
            → "I recommend Carbone with 4.5 stars and 1200 reviews..."
        """
        if not restaurants:
            return "No restaurants found matching your criteria."

        if len(restaurants) == 1:
            r = restaurants[0]
            return f"I found {r.name} ({r.provider}) with {r.rating}⭐ rating, {r.review_count} reviews, and {r.price_range} price range. It's {r.distance_miles} miles away."

        # Build system prompt
        system_prompt = f"""You are a restaurant recommendation assistant for Hopwise.
Every stop matters! Hop smarter!

Your job: Compare restaurants and recommend the best option based on the user's priority.

PRIORITY: {priority}
- rating: Recommend highest rated with good review count
- price: Recommend best value (consider rating vs price)
- distance: Recommend closest good option
- balanced: Best overall choice (rating + price + distance)

RESPONSE FORMAT:
- Start with clear recommendation: "I recommend [Name] from [Provider]"
- Explain why (2-3 key reasons)
- Mention price, rating, distance, review count
- If relevant, mention notable alternatives
- Keep it conversational and helpful (3-4 sentences max)

IMPORTANT:
- Be specific with numbers (rating, reviews, price, distance)
- Consider review count (more reviews = more reliable)
- Price range: $ cheap, $$ moderate, $$$ upscale, $$$$ fine dining
- Distance matters for convenience
- Don't just pick highest rating - context matters
"""

        # Format restaurant data
        restaurant_data = []
        for r in restaurants:
            restaurant_data.append({
                'provider': r.provider,
                'name': r.name,
                'cuisine': r.cuisine,
                'rating': r.rating,
                'review_count': r.review_count,
                'price_range': r.price_range,
                'distance_miles': r.distance_miles,
                'is_open_now': r.is_open_now
            })

        user_prompt = f"Restaurants to compare:\n{json.dumps(restaurant_data, indent=2)}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Slightly creative
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # Fallback to programmatic selection
            print(f"AI comparison failed: {e}, using fallback")
            return self._fallback_comparison(restaurants, priority)

    def _fallback_comparison(self, restaurants: List[Restaurant], priority: str) -> str:
        """
        Fallback comparison if AI fails.

        Args:
            restaurants: List of restaurants
            priority: Comparison priority

        Returns:
            Simple programmatic recommendation
        """
        if priority == "rating":
            # Highest rating with decent review count
            best = max(restaurants, key=lambda r: (r.rating, r.review_count))
            return f"I recommend {best.name} from {best.provider} with {best.rating}⭐ rating and {best.review_count} reviews. It's {best.price_range} and {best.distance_miles} miles away."

        elif priority == "price":
            # Cheapest with good rating
            cheap_good = [r for r in restaurants if r.rating >= 4.0]
            if cheap_good:
                best = min(cheap_good, key=lambda r: len(r.price_range or "$"))
            else:
                best = min(restaurants, key=lambda r: len(r.price_range or "$"))
            return f"For the best value, I recommend {best.name} from {best.provider}. It's {best.price_range}, has {best.rating}⭐ rating, and is {best.distance_miles} miles away."

        elif priority == "distance":
            # Closest with good rating
            good_nearby = [r for r in restaurants if r.rating >= 4.0]
            if good_nearby:
                best = min(good_nearby, key=lambda r: r.distance_miles)
            else:
                best = min(restaurants, key=lambda r: r.distance_miles)
            return f"The closest good option is {best.name} from {best.provider}, only {best.distance_miles} miles away with {best.rating}⭐ rating and {best.price_range} price range."

        else:  # balanced
            # Best overall score
            def score(r):
                price_score = 5 - len(r.price_range or "$")  # Cheaper is better
                rating_score = r.rating * 2  # Rating out of 10
                distance_score = max(0, 5 - r.distance_miles)  # Closer is better
                review_score = min(r.review_count / 1000, 3)  # More reviews up to 3 points
                return rating_score + price_score + distance_score + review_score

            best = max(restaurants, key=score)
            return f"For the best overall choice, I recommend {best.name} from {best.provider}. It has {best.rating}⭐ rating, {best.price_range} price range, and is {best.distance_miles} miles away with {best.review_count} reviews."

    def __repr__(self) -> str:
        return f"RestaurantComparator(model={self.model})"


# Convenience function
def compare_restaurants(restaurants: List[Restaurant], priority: str = "balanced") -> str:
    """
    Compare restaurants using AI.

    Args:
        restaurants: List of Restaurant objects
        priority: Comparison priority (rating, price, distance, balanced)

    Returns:
        Recommendation string
    """
    comparator = RestaurantComparator()
    return comparator.compare_restaurants(restaurants, priority)
