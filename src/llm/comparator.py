"""LLM-powered weather forecast comparison."""

import os
from typing import List
from openai import OpenAI
from models.weather import WeatherForecast


class WeatherComparator:
    """
    Uses AI to compare weather forecasts from different providers.

    Provides natural language analysis of forecast differences,
    reliability assessment, and recommendations.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the comparator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def compare_forecasts(self, forecasts: List[WeatherForecast]) -> str:
        """
        Generate AI-powered comparison of weather forecasts.

        Args:
            forecasts: List of WeatherForecast objects to compare

        Returns:
            Natural language comparison and analysis
        """
        if not forecasts:
            return "No forecasts to compare."

        if len(forecasts) == 1:
            return f"Showing forecast from {forecasts[0].provider} only."

        # Build comparison data for the LLM
        comparison_data = self._build_comparison_text(forecasts)

        prompt = f"""Compare these weather forecasts from different providers for the same location:

{comparison_data}

Provide a brief analysis covering:
1. Key differences in temperature predictions
2. Differences in precipitation forecasts
3. Which provider seems more optimistic/pessimistic
4. Overall consensus and reliability assessment

Keep it concise (3-4 sentences) and helpful for planning."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful meteorology assistant that compares weather forecasts."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating comparison: {e}"

    def _build_comparison_text(self, forecasts: List[WeatherForecast]) -> str:
        """Build formatted text representation of forecasts for LLM."""
        lines = []

        for forecast in forecasts:
            lines.append(f"\n{forecast.provider}:")
            lines.append(f"  Current: {forecast.current_temp}°C, {forecast.current_condition}")
            lines.append(f"  {len(forecast.daily_forecasts)}-day forecast:")

            for day in forecast.daily_forecasts[:5]:  # Show first 5 days
                lines.append(
                    f"    {day.date}: {day.temp_low}°C to {day.temp_high}°C, "
                    f"{day.condition}, {day.precipitation_chance}% rain"
                )

        return "\n".join(lines)

    def generate_summary(self, forecast: WeatherForecast, days: int = 3) -> str:
        """
        Generate a natural language summary of a single forecast.

        Args:
            forecast: WeatherForecast to summarize
            days: Number of days to include in summary

        Returns:
            Natural language summary
        """
        summary_data = []
        for day in forecast.daily_forecasts[:days]:
            summary_data.append(
                f"{day.date}: {day.temp_low}-{day.temp_high}°C, {day.condition}, "
                f"{day.precipitation_chance}% chance of rain"
            )

        summary_text = "\n".join(summary_data)

        prompt = f"""Summarize this weather forecast in a friendly, conversational way:

Location: {forecast.location}
Current: {forecast.current_temp}°C, {forecast.current_condition}

Forecast:
{summary_text}

Provide a brief summary (2-3 sentences) that highlights what someone should know for planning their next few days."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a friendly weather assistant providing helpful summaries."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating summary: {e}"
