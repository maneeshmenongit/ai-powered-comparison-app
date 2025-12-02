"""Rideshare comparison service using LLM for intelligent recommendations."""

import os
from typing import List
from openai import OpenAI
from .models import RideEstimate


class RideShareComparator:
    """
    Compares ride estimates from multiple providers using LLM analysis.

    Provides natural language recommendations based on price, time,
    or balanced priorities. Uses OpenAI GPT-4o-mini for comparison.

    Example:
        comparator = RideShareComparator()
        recommendation = comparator.compare_rides(
            estimates=[uber_estimate, lyft_estimate],
            user_priority="price"
        )
    """

    def __init__(self, api_key: str = None):
        """
        Initialize comparator with OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def compare_rides(
        self,
        estimates: List[RideEstimate],
        user_priority: str = "balanced"
    ) -> str:
        """
        Compare ride estimates and provide intelligent recommendation.

        Args:
            estimates: List of RideEstimate objects from different providers
            user_priority: Priority mode - "price", "time", or "balanced"

        Returns:
            Natural language recommendation as string

        Example:
            recommendation = comparator.compare_rides(
                estimates=[uber_est, lyft_est],
                user_priority="price"
            )
        """
        if not estimates:
            return "No ride estimates available for comparison."

        if len(estimates) == 1:
            est = estimates[0]
            return (
                f"Only {est.provider} {est.vehicle_type} is available. "
                f"Estimated price: ${est.price_estimate:.2f} "
                f"({est.duration_minutes} min trip, {est.pickup_eta_minutes} min pickup)."
            )

        # Format estimates for LLM
        formatted_text = self._format_estimates_for_llm(estimates, user_priority)

        try:
            # Call OpenAI for natural language comparison
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(user_priority)
                    },
                    {
                        "role": "user",
                        "content": formatted_text
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # Fallback to rule-based comparison if LLM fails
            print(f"LLM comparison failed: {e}. Using fallback method.")
            return self.get_best_option_text(estimates, user_priority)

    def _get_system_prompt(self, priority: str) -> str:
        """
        Generate system prompt based on user priority.

        Args:
            priority: User's priority mode

        Returns:
            System prompt string for LLM
        """
        base_prompt = (
            "You are a helpful rideshare comparison assistant. "
            "Compare ride estimates and provide a clear, concise recommendation. "
        )

        if priority == "price":
            priority_prompt = (
                "Prioritize the cheapest option. Mention price differences and "
                "note if surge/primetime pricing is active. Only consider time "
                "if prices are very similar."
            )
        elif priority == "time":
            priority_prompt = (
                "Prioritize the fastest option (shortest pickup ETA + trip duration). "
                "Mention time differences and only consider price if times are very similar."
            )
        else:  # balanced
            priority_prompt = (
                "Provide a balanced recommendation considering both price and time. "
                "Identify the best overall value. Mention if one option is significantly "
                "better in either dimension."
            )

        format_prompt = (
            "\n\nFormat your response as:\n"
            "1. Brief recommendation (which ride to take)\n"
            "2. Key reason (1-2 sentences)\n"
            "3. Notable trade-offs if any\n\n"
            "Keep it concise and actionable."
        )

        return base_prompt + priority_prompt + format_prompt

    def _format_estimates_for_llm(
        self,
        estimates: List[RideEstimate],
        priority: str
    ) -> str:
        """
        Format ride estimates into readable text for LLM.

        Args:
            estimates: List of RideEstimate objects
            priority: User's priority mode

        Returns:
            Formatted string with all relevant details
        """
        lines = [f"User Priority: {priority.upper()}\n"]
        lines.append("Available Rides:\n")

        for i, est in enumerate(estimates, 1):
            surge_note = ""
            if est.surge_multiplier > 1.0:
                surge_note = f" (⚡ {est.surge_multiplier}x surge)"

            lines.append(
                f"{i}. {est.provider} {est.vehicle_type}:\n"
                f"   - Price: ${est.price_low:.2f} - ${est.price_high:.2f} "
                f"(est. ${est.price_estimate:.2f}){surge_note}\n"
                f"   - Trip Duration: {est.duration_minutes} minutes\n"
                f"   - Pickup ETA: {est.pickup_eta_minutes} minutes\n"
                f"   - Distance: {est.distance_miles} miles\n"
            )

        # Add value scores for balanced priority
        if priority == "balanced":
            lines.append("\nValue Scores (lower is better):")
            for i, est in enumerate(estimates, 1):
                score = self._calculate_value_score(est)
                lines.append(
                    f"{i}. {est.provider} {est.vehicle_type}: {score:.2f}"
                )

        return "\n".join(lines)

    def _calculate_value_score(self, estimate: RideEstimate) -> float:
        """
        Calculate value score for balanced comparison.

        Lower score is better. Balances price per mile and total time.

        Args:
            estimate: RideEstimate object

        Returns:
            Value score (float)
        """
        # Price component: normalized price per mile
        price_per_mile = estimate.price_estimate / max(estimate.distance_miles, 1)

        # Time component: total time (pickup + trip)
        total_time = estimate.pickup_eta_minutes + estimate.duration_minutes

        # Weighted combination (60% price, 40% time)
        # Normalize time by dividing by 10 to balance scales
        value_score = (0.6 * price_per_mile) + (0.4 * (total_time / 10))

        return value_score

    def identify_best_option(
        self,
        estimates: List[RideEstimate],
        priority: str = "balanced"
    ) -> RideEstimate:
        """
        Fallback rule-based comparison if LLM fails.

        Returns the best RideEstimate object based on priority.

        Args:
            estimates: List of RideEstimate objects
            priority: User's priority mode

        Returns:
            Best RideEstimate object based on priority
        """
        if not estimates:
            raise ValueError("No rides available.")

        if priority == "price":
            # Find cheapest estimate
            return min(estimates, key=lambda x: x.price_estimate)

        elif priority == "time":
            # Find fastest (pickup + trip)
            return min(
                estimates,
                key=lambda x: x.pickup_eta_minutes + x.duration_minutes
            )

        else:  # balanced
            # Find best value score
            return min(estimates, key=self._calculate_value_score)

    def get_best_option_text(
        self,
        estimates: List[RideEstimate],
        priority: str = "balanced"
    ) -> str:
        """
        Get text description of best option without LLM.

        Args:
            estimates: List of RideEstimate objects
            priority: User's priority mode

        Returns:
            Simple text recommendation
        """
        if not estimates:
            return "No rides available."

        best = self.identify_best_option(estimates, priority)

        if priority == "price":
            return (
                f"💰 Best Price: {best.provider} {best.vehicle_type} "
                f"at ${best.price_estimate:.2f} "
                f"({best.duration_minutes} min trip, {best.pickup_eta_minutes} min pickup)"
            )

        elif priority == "time":
            total_time = best.pickup_eta_minutes + best.duration_minutes
            return (
                f"⚡ Fastest Option: {best.provider} {best.vehicle_type} "
                f"in {total_time} minutes total "
                f"(${best.price_estimate:.2f})"
            )

        else:  # balanced
            score = self._calculate_value_score(best)
            return (
                f"⭐ Best Value: {best.provider} {best.vehicle_type} "
                f"at ${best.price_estimate:.2f} "
                f"({best.duration_minutes} min trip, {best.pickup_eta_minutes} min pickup). "
                f"Value score: {score:.2f}"
            )
