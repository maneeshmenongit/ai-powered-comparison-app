#!/usr/bin/env python3
"""
Ride-Share Comparison Tool - Main Entry Point

A beautiful terminal application that compares ride-share options
from multiple providers using natural language queries.

Usage:
    # Interactive mode
    python main_rideshare.py

    # Command-line mode
    python main_rideshare.py \
        --query "Get me from Times Square to JFK" \
        --location "New York" \
        --priority "balanced"
"""

import os
import sys
import time
import hashlib
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.prompt import Prompt

sys.path.insert(0, 'src')
from domains.rideshare.intent_parser import RideShareIntentParser
from domains.rideshare.comparator import RideShareComparator
from domains.rideshare.api_clients.mock_uber_client import MockUberClient
from domains.rideshare.api_clients.mock_lyft_client import MockLyftClient
from core.geocoding_service import GeocodingService
from domains.rideshare.models import RideEstimate, RideQuery


class SimpleCache:
    """Simple in-memory cache with time-to-live."""

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache with TTL.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.cache: Dict[str, Tuple[List[RideEstimate], float]] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[List[RideEstimate]]:
        """
        Retrieve cached data if still valid.

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        if key in self.cache:
            data, timestamp = self.cache[key]
            age = time.time() - timestamp
            if age < self.ttl:
                return data
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None

    def set(self, key: str, data: List[RideEstimate]):
        """
        Store data in cache with current timestamp.

        Args:
            key: Cache key
            data: Data to cache
        """
        self.cache[key] = (data, time.time())

    @staticmethod
    def generate_key(
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> str:
        """
        Generate cache key from coordinates.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            MD5 hash of coordinates (16 chars)
        """
        key_str = f"{origin_lat:.4f},{origin_lng:.4f},{dest_lat:.4f},{dest_lng:.4f}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]


class RideShareApp:
    """Main ride-share comparison application."""

    def __init__(self):
        """Initialize all services and clients."""
        self.console = Console()
        load_dotenv()

        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            self.console.print(
                "[red]❌ ERROR: OPENAI_API_KEY not found in environment[/red]"
            )
            self.console.print(
                "[yellow]Please set OPENAI_API_KEY in your .env file[/yellow]"
            )
            sys.exit(1)

        # Initialize services
        self.parser = RideShareIntentParser()
        self.geocoder = GeocodingService()
        self.comparator = RideShareComparator()
        self.uber_client = MockUberClient()
        self.lyft_client = MockLyftClient()
        self.cache = SimpleCache(ttl_seconds=300)

    def show_welcome_banner(self):
        """Display welcome banner."""
        banner = Panel.fit(
            "[bold cyan]🚗 Ride-Share Comparison Tool 🚗[/bold cyan]",
            box=box.DOUBLE,
            border_style="cyan"
        )
        self.console.print("\n")
        self.console.print(banner)
        self.console.print("\n")

    def get_user_input(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Tuple[str, Optional[str], str]:
        """
        Get user input interactively or from arguments.

        Args:
            query: Pre-provided query (optional)
            location: Pre-provided location (optional)
            priority: Pre-provided priority (optional)

        Returns:
            Tuple of (query, location, priority)
        """
        if query is None:
            self.console.print("[bold]Enter your ride request:[/bold]")
            self.console.print(
                "[dim]Example: Compare Uber and Lyft from Times Square to JFK[/dim]"
            )
            query = Prompt.ask("Query")

        if location is None:
            location = Prompt.ask(
                "\n[bold]Your current location (for context)[/bold]",
                default="New York"
            )

        if priority is None:
            priority = Prompt.ask(
                "\n[bold]Priority[/bold]",
                choices=["price", "time", "balanced"],
                default="balanced"
            )

        return query, location, priority

    def display_route_info(
        self,
        origin: str,
        destination: str,
        priority: str,
        cache_status: str
    ):
        """
        Display route and priority information.

        Args:
            origin: Origin location name
            destination: Destination location name
            priority: User priority (price/time/balanced)
            cache_status: Cache hit/miss status
        """
        self.console.print(f"\n[bold]📍 Route:[/bold] {origin} → {destination}")
        self.console.print(f"[bold]🎯 Priority:[/bold] {priority}")
        self.console.print(f"[bold]💾 Cache:[/bold] {cache_status}\n")

    def fetch_estimates(
        self,
        origin_coords: Tuple[float, float],
        dest_coords: Tuple[float, float],
        cache_key: str
    ) -> List[RideEstimate]:
        """
        Fetch ride estimates with caching and progress indicators.

        Args:
            origin_coords: Origin (lat, lng)
            dest_coords: Destination (lat, lng)
            cache_key: Cache key for storing results

        Returns:
            List of RideEstimate objects
        """
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            self.console.print("[green]✓ Using cached results[/green]\n")
            return cached_data

        # Fetch fresh data with progress indicator
        all_estimates = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            # Uber
            task = progress.add_task("⏳ Fetching Uber estimates...", total=None)
            uber_estimates = self.uber_client.get_price_estimates(
                origin_coords[0], origin_coords[1],
                dest_coords[0], dest_coords[1]
            )
            all_estimates.extend(uber_estimates)
            progress.update(task, description="[green]✓ Uber estimates retrieved[/green]")

            # Lyft
            task = progress.add_task("⏳ Fetching Lyft estimates...", total=None)
            lyft_estimates = self.lyft_client.get_price_estimates(
                origin_coords[0], origin_coords[1],
                dest_coords[0], dest_coords[1]
            )
            all_estimates.extend(lyft_estimates)
            progress.update(task, description="[green]✓ Lyft estimates retrieved[/green]")

            # Compare
            task = progress.add_task("⏳ Analyzing options...", total=None)
            time.sleep(0.5)  # Brief pause for effect
            progress.update(task, description="[green]✓ Analysis complete[/green]")

        self.console.print()

        # Cache the results
        self.cache.set(cache_key, all_estimates)

        return all_estimates

    def display_estimates_table(self, estimates: List[RideEstimate]):
        """
        Display estimates in a beautiful table.

        Args:
            estimates: List of RideEstimate objects
        """
        table = Table(
            title="Available Options",
            box=box.ROUNDED,
            title_style="bold cyan"
        )

        table.add_column("Provider", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Price", style="green", justify="right")
        table.add_column("ETA", justify="center")
        table.add_column("Trip", justify="center")
        table.add_column("Distance", justify="right")

        for est in estimates:
            surge_indicator = ""
            price_style = "green"
            if est.surge_multiplier and est.surge_multiplier > 1.0:
                surge_indicator = f" 🔥 {est.surge_multiplier:.1f}x"
                price_style = "red"

            table.add_row(
                est.provider,
                est.vehicle_type,
                f"[{price_style}]${est.price_estimate:.2f}{surge_indicator}[/{price_style}]",
                f"{est.pickup_eta_minutes} min",
                f"{est.duration_minutes} min",
                f"{est.distance_miles:.1f} mi"
            )

        self.console.print(table)
        self.console.print()

    def display_recommendation(self, recommendation: str):
        """
        Display recommendation in a highlighted panel.

        Args:
            recommendation: Recommendation text from comparator
        """
        panel = Panel(
            recommendation,
            title="💡 RECOMMENDATION",
            box=box.DOUBLE,
            border_style="bold green",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def run(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        priority: Optional[str] = None
    ):
        """
        Run the ride-share comparison application.

        Args:
            query: Optional pre-provided query
            location: Optional pre-provided location
            priority: Optional pre-provided priority
        """
        try:
            # Welcome banner
            self.show_welcome_banner()

            # Get user input
            query, location, priority = self.get_user_input(query, location, priority)

            # Parse query
            try:
                with self.console.status("[bold yellow]🔍 Parsing your query...[/bold yellow]"):
                    ride_query = self.parser.parse_query(query, user_location=location)
            except ValueError as e:
                self.console.print(f"[red]❌ Query Error: {e}[/red]")
                self.console.print(
                    "[yellow]Please include both origin and destination in your query.[/yellow]"
                )
                return

            # Geocode origin and destination
            try:
                with self.console.status("[bold yellow]🌍 Finding locations...[/bold yellow]"):
                    origin_lat, origin_lng, origin_name = self.geocoder.geocode(
                        ride_query.origin
                    )
                    dest_lat, dest_lng, dest_name = self.geocoder.geocode(
                        ride_query.destination
                    )
            except Exception as e:
                self.console.print(f"[red]❌ Geocoding Error: {e}[/red]")
                self.console.print(
                    "[yellow]Could not find one or more locations. Please check your query.[/yellow]"
                )
                return

            # Generate cache key
            cache_key = SimpleCache.generate_key(
                origin_lat, origin_lng, dest_lat, dest_lng
            )

            # Check cache status
            cache_status = (
                "[green]HIT (using cached data)[/green]"
                if self.cache.get(cache_key)
                else "[yellow]MISS (fetching fresh data...)[/yellow]"
            )

            # Display route info
            self.display_route_info(origin_name, dest_name, priority, cache_status)

            # Fetch estimates
            estimates = self.fetch_estimates(
                (origin_lat, origin_lng),
                (dest_lat, dest_lng),
                cache_key
            )

            if not estimates:
                self.console.print(
                    "[red]❌ No estimates available for this route.[/red]"
                )
                return

            # Display estimates table
            self.display_estimates_table(estimates)

            # Get and display recommendation
            try:
                recommendation = self.comparator.compare_rides(
                    estimates,
                    user_priority=priority
                )
                self.display_recommendation(recommendation)
            except Exception as e:
                self.console.print(
                    f"[red]❌ Comparison Error: {e}[/red]"
                )
                # Fallback to programmatic selection
                best = self.comparator.identify_best_option(estimates, priority)
                fallback_text = (
                    f"Best option based on {priority} priority: "
                    f"{best.provider} {best.vehicle_type} at ${best.price_estimate:.2f}"
                )
                self.display_recommendation(fallback_text)

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]👋 Goodbye![/yellow]\n")
            sys.exit(0)
        except Exception as e:
            self.console.print(f"\n[red]❌ Unexpected Error: {e}[/red]\n")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Compare ride-share options using natural language queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main_rideshare.py

  # Command-line mode
  python main_rideshare.py \\
      --query "Compare Uber and Lyft from Times Square to JFK" \\
      --location "New York" \\
      --priority balanced
        """
    )

    parser.add_argument(
        "--query",
        "-q",
        help="Natural language ride request",
        default=None
    )

    parser.add_argument(
        "--location",
        "-l",
        help="Your current location (for context)",
        default=None
    )

    parser.add_argument(
        "--priority",
        "-p",
        choices=["price", "time", "balanced"],
        help="Priority for comparison (default: balanced)",
        default=None
    )

    args = parser.parse_args()

    # Run the application
    app = RideShareApp()
    app.run(
        query=args.query,
        location=args.location,
        priority=args.priority
    )


if __name__ == "__main__":
    main()
