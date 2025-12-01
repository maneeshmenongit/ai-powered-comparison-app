"""LLM-powered intent parsing for ride-share queries."""

import os
import json
from openai import OpenAI
from .models import RideQuery


class RideShareIntentParser:
    """
    Parses natural language ride-share queries into structured data.

    Uses OpenAI to extract:
    - Origin and destination locations
    - Preferred ride-share providers
    - Vehicle type preferences
    - Timing and passenger count
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the intent parser.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def parse_query(self, query: str, user_location: str = None) -> RideQuery:
        """
        Parse a natural language ride-share query.

        Args:
            query: User's natural language query
            user_location: Optional user's current location for context

        Returns:
            RideQuery object with parsed intent

        Raises:
            ValueError: If origin or destination cannot be determined

        Example:
            Input: "Get me an Uber from Times Square to JFK"
            Output: RideQuery(
                origin="Times Square, New York",
                destination="JFK Airport, New York",
                providers=["uber"],
                vehicle_type="standard",
                when="now",
                passengers=1
            )
        """
        # Build system prompt with context
        context_note = ""
        if user_location:
            context_note = f"\n\nUser's current location context: {user_location}"
            context_note += "\nUse this to infer unclear origins or destinations."

        system_prompt = f"""You are a helpful assistant that extracts ride-share query intent from user queries.

Extract the following information:
- origin: starting location (REQUIRED - must be specific address or landmark)
- destination: ending location (REQUIRED - must be specific address or landmark)
- providers: list of ride services to compare (default: ["uber", "lyft"])
- vehicle_type: preferred vehicle type (default: "standard")
- when: when to request ride (default: "now")
- passengers: number of passengers (default: 1)

Available providers: uber, lyft, via
Available vehicle_types: standard, xl, luxury, shared

IMPORTANT:
- Both origin and destination are REQUIRED
- If unclear, use context to make reasonable inference
- If still unclear, set origin/destination to "UNCLEAR" and explain in error message
- Always include city/area in location names for clarity{context_note}

Return ONLY valid JSON with these fields."""

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

            parsed = json.loads(response.choices[0].message.content)

            # Validate required fields
            if not parsed.get("origin") or parsed.get("origin") == "UNCLEAR":
                raise ValueError(
                    "Could not determine origin location. "
                    "Please specify where you want to be picked up."
                )

            if not parsed.get("destination") or parsed.get("destination") == "UNCLEAR":
                raise ValueError(
                    "Could not determine destination. "
                    "Please specify where you want to go."
                )

            # Create RideQuery object with defaults
            return RideQuery(
                origin=parsed["origin"],
                destination=parsed["destination"],
                providers=parsed.get("providers", ["uber", "lyft"]),
                vehicle_type=parsed.get("vehicle_type", "standard"),
                when=parsed.get("when", "now"),
                passengers=parsed.get("passengers", 1)
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response as JSON: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in response: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse query: {e}")
