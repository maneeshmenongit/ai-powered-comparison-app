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
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.prompt import Prompt

sys.path.insert(0, 'src')
from domains.rideshare.handler import RideShareHandler
from core import GeocodingService, CacheService, RateLimiter
from domains.rideshare.models import RideEstimate


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
    """Main ride-share comparison application using DomainHandler pattern."""

    def __init__(self):
        """Initialize handler and services."""
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

        # Initialize core services
        self.console.print("\n[cyan]🔧 Initializing services...[/cyan]")

        geocoder = GeocodingService()
        cache = CacheService(base_dir="data/cache", enabled=True)
        rate_limiter = RateLimiter(enabled=True)

        self.console.print("  ✅ Geocoding service")
        self.console.print("  ✅ Cache service")
        self.console.print("  ✅ Rate limiter")

        # Store services for statistics display
        self.cache = cache
        self.rate_limiter = rate_limiter

        # Initialize RideShare handler (encapsulates all domain logic)
        self.handler = RideShareHandler(
            cache_service=cache,
            geocoding_service=geocoder,
            rate_limiter=rate_limiter
        )

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

    def display_processing(self, cache_hit: bool = False):
        """
        Display processing status with progress indicators.

        Args:
            cache_hit: Whether cache was hit
        """
        if cache_hit:
            self.console.print("[green]✓ Using cached results[/green]\n")
            return

        # Show processing steps
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task1 = progress.add_task("⏳ Fetching Uber estimates...", total=None)
            time.sleep(0.3)
            progress.update(task1, description="[green]✓ Uber estimates retrieved[/green]")

            task2 = progress.add_task("⏳ Fetching Lyft estimates...", total=None)
            time.sleep(0.3)
            progress.update(task2, description="[green]✓ Lyft estimates retrieved[/green]")

            task3 = progress.add_task("⏳ Analyzing options...", total=None)
            time.sleep(0.3)
            progress.update(task3, description="[green]✓ Analysis complete[/green]")

        self.console.print()

    def display_estimates_table(self, estimates: List[Dict]):
        """
        Display estimates in a beautiful table.

        Args:
            estimates: List of formatted estimate dictionaries
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
            if est.get('surge_multiplier') and est['surge_multiplier'] > 1.0:
                surge_indicator = f" 🔥 {est['surge_multiplier']:.1f}x"
                price_style = "red"

            table.add_row(
                est['provider'],
                est['vehicle_type'],
                f"[{price_style}]${est['price']:.2f}{surge_indicator}[/{price_style}]",
                f"{est['pickup_eta_minutes']} min",
                f"{est['duration_minutes']} min",
                f"{est['distance_miles']:.1f} mi"
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

            # Process through handler (does everything!)
            with self.console.status("[bold yellow]🔍 Processing your request...[/bold yellow]"):
                try:
                    # Single method call handles entire pipeline:
                    # 1. Parse query
                    # 2. Geocode locations
                    # 3. Check cache / fetch from APIs
                    # 4. Compare with AI
                    # 5. Format results
                    results = self.handler.process(
                        raw_query=query,
                        context={'user_location': location},
                        priority=priority
                    )
                except ValueError as e:
                    self.console.print(f"\n[red]❌ Error: {e}[/red]")
                    self.console.print(
                        "[yellow]Please include both origin and destination in your query.[/yellow]"
                    )
                    return

            # Extract results
            ride_query = results['query']
            estimates = results['estimates']
            comparison = results['comparison']
            route = results['route']
            summary = results['summary']

            # Display route info
            self.console.print(f"\n[bold]📍 Route:[/bold] {ride_query.origin} → {ride_query.destination}")
            self.console.print(f"[bold]🎯 Priority:[/bold] {priority}")
            self.console.print(f"[bold]📊 Options:[/bold] {summary['total_options']} available")
            self.console.print(f"[bold]💰 Price Range:[/bold] {summary['price_range']}")
            if route:
                self.console.print(f"[bold]📏 Distance:[/bold] {route['distance_miles']:.1f} miles\n")
            else:
                self.console.print()

            # Display processing animation
            # Note: Actual work already done in handler.process()
            # This is just for visual feedback
            cache_hit = summary.get('cache_hit', False)
            self.display_processing(cache_hit)

            # Display estimates table
            if not estimates:
                self.console.print(
                    "[red]❌ No estimates available for this route.[/red]"
                )
                return

            self.display_estimates_table(estimates)

            # Display AI recommendation
            self.display_recommendation(comparison)

            # Show cache statistics
            cache_stats = self.cache.stats()
            if cache_stats['total_requests'] > 0:
                self.console.print(
                    f"[dim]📊 Cache: {cache_stats['hits']} hits, "
                    f"{cache_stats['misses']} misses "
                    f"({cache_stats['hit_rate_percent']:.1f}% hit rate)[/dim]"
                )

            # Show rate limiter statistics (for providers used)
            for provider in ride_query.providers:
                provider_lower = provider.lower()
                rate_stats = self.rate_limiter.stats(provider_lower)
                if rate_stats and rate_stats['total_requests'] > 0:
                    self.console.print(
                        f"[dim]⚡ {provider} Rate Limiter: "
                        f"{rate_stats['total_requests']} requests, "
                        f"{rate_stats['available_tokens']:.0f} tokens available[/dim]"
                    )

            self.console.print()  # Extra newline at end

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
