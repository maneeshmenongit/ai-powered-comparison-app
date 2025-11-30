"""LLM-powered intent parsing for weather queries."""

import os
import json
from typing import Dict
from openai import OpenAI


class IntentParser:
    """
    Parses natural language weather queries into structured data.

    Uses OpenAI to extract:
    - Location(s) to check weather for
    - Number of days to forecast
    - Weather services to compare
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the intent parser.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def parse_query(self, query: str) -> Dict:
        """
        Parse a natural language weather query.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with parsed intent:
            {
                "location": str,
                "days": int,
                "providers": List[str]
            }

        Example:
            Input: "Compare weather in New York for next 5 days"
            Output: {
                "location": "New York",
                "days": 5,
                "providers": ["open-meteo", "weatherapi"]
            }
        """
        system_prompt = """You are a helpful assistant that extracts weather query intent from user queries.

Extract the following information:
- location: the city/place for weather forecast (required)
- days: number of days to forecast (default: 7, max: 10)
- providers: list of weather services to compare (default: ["open-meteo", "weatherapi"])

Available providers: open-meteo, weatherapi

Return ONLY valid JSON with these fields. If location is unclear, ask for clarification.
If days or providers are not specified, use the defaults."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            raise ValueError(f"Failed to parse query: {e}")
