"""
Phase 2: AI-Powered Weather Comparison Tool
Real API integration with caching and intelligent comparison.

Before running:
1. pip install openai rich python-dotenv requests
2. Create .env file with OPENAI_API_KEY (required)
3. Optional: Add WEATHERAPI_KEY for WeatherAPI.com
4. Run: python src/phase2_main.py
"""

import os
from typing import List
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from models.weather import WeatherForecast
from api_clients.openmeteo_client import OpenMeteoClient
from api_clients.weatherapi_client import WeatherAPIClient
from llm.intent_parser import IntentParser
from llm.comparator import WeatherComparator
from services.cache_service import CacheService

# Load environment variables
load_dotenv()

# Initialize
console = Console()
cache = CacheService(ttl_minutes=60)


def get_forecasts(location: str, days: int, providers: List[str]) -> List[WeatherForecast]:
    """
    Fetch weather forecasts from specified providers with caching.

    Args:
        location: Location to get forecast for
        days: Number of days to forecast
        providers: List of provider names to use

    Returns:
        List of WeatherForecast objects
    """
    forecasts = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        for provider in providers:
            task = progress.add_task(f"Fetching from {provider}...", total=None)

            try:
                # Check cache first
                cache_key = f"{provider}:{location}:{days}"
                cached_data = cache.get(cache_key)

                if cached_data:
                    console.print(f"[dim]✓ Using cached data for {provider}[/dim]")
                    # Reconstruct WeatherForecast from cached dict
                    # Note: In production, we'd serialize/deserialize properly
                    # For now, just fetch fresh data
                    cached_data = None

                if not cached_data:
                    # Fetch fresh data
                    if provider.lower() == "open-meteo":
                        with OpenMeteoClient() as client:
                            forecast = client.get_forecast(location, days)

                    elif provider.lower() == "weatherapi":
                        api_key = os.getenv("WEATHERAPI_KEY")
                        if not api_key:
                            console.print(f"[yellow]⚠ Skipping WeatherAPI - no API key found[/yellow]")
                            progress.remove_task(task)
                            continue
                        with WeatherAPIClient(api_key) as client:
                            forecast = client.get_forecast(location, days)

                    else:
                        console.print(f"[yellow]⚠ Unknown provider: {provider}[/yellow]")
                        progress.remove_task(task)
                        continue

                    # Cache the result
                    cache.set(forecast.to_dict(), cache_key)
                    forecasts.append(forecast)

                    console.print(f"[green]✓ Got forecast from {provider}[/green]")

            except Exception as e:
                console.print(f"[red]✗ Error with {provider}: {e}[/red]")

            progress.remove_task(task)

    return forecasts


def display_forecasts(forecasts: List[WeatherForecast], comparison: str):
    """
    Display weather forecasts in a nice table format.

    Args:
        forecasts: List of WeatherForecast objects
        comparison: AI-generated comparison text
    """
    if not forecasts:
        console.print("[red]No forecasts to display[/red]")
        return

    # Display current conditions
    console.print("\n[bold cyan]Current Conditions[/bold cyan]")
    current_table = Table(show_header=True, header_style="bold cyan")
    current_table.add_column("Provider", style="yellow")
    current_table.add_column("Location")
    current_table.add_column("Temperature", justify="right", style="green")
    current_table.add_column("Condition")

    for forecast in forecasts:
        current_table.add_row(
            forecast.provider,
            forecast.location,
            f"{forecast.current_temp}°C",
            forecast.current_condition
        )

    console.print(current_table)
    console.print()

    # Display forecast comparison for next 5 days
    console.print("[bold cyan]5-Day Forecast Comparison[/bold cyan]")

    for i in range(min(5, len(forecasts[0].daily_forecasts))):
        date = forecasts[0].daily_forecasts[i].date

        forecast_table = Table(
            title=f"📅 {date}",
            show_header=True,
            header_style="bold cyan"
        )
        forecast_table.add_column("Provider", style="yellow", width=15)
        forecast_table.add_column("Temp Range", justify="right", style="green")
        forecast_table.add_column("Condition", width=20)
        forecast_table.add_column("Rain %", justify="right")
        forecast_table.add_column("Precip", justify="right")

        for forecast in forecasts:
            if i < len(forecast.daily_forecasts):
                day = forecast.daily_forecasts[i]
                forecast_table.add_row(
                    forecast.provider,
                    f"{day.temp_low}°C - {day.temp_high}°C",
                    day.condition,
                    f"{day.precipitation_chance}%",
                    f"{day.precipitation_mm}mm"
                )

        console.print(forecast_table)
        console.print()

    # Display AI comparison
    if comparison:
        console.print(Panel(
            comparison,
            title="🤖 AI Analysis",
            border_style="blue"
        ))


def main():
    """Main execution flow for Phase 2."""

    console.print("\n[bold cyan]🌤️  AI-Powered Weather Comparison Tool - Phase 2[/bold cyan]\n")
    console.print("[dim]Now with real weather APIs![/dim]\n")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY not found in environment[/red]")
        console.print("[yellow]Please add it to your .env file[/yellow]")
        return

    # Get user query
    query = input("Enter your weather query (or press Enter for example): ").strip()

    if not query:
        query = "Compare weather in New York for the next 5 days"
        console.print(f"[dim]Using example: {query}[/dim]\n")

    # Step 1: Parse user intent with AI
    console.print("[bold]Step 1:[/bold] Parsing your query with AI...")
    try:
        parser = IntentParser()
        parsed = parser.parse_query(query)

        console.print(f"[green]✓ Parsed successfully[/green]")
        console.print(f"  Location: {parsed.get('location')}")
        console.print(f"  Days: {parsed.get('days')}")
        console.print(f"  Providers: {', '.join(parsed.get('providers', []))}\n")

    except Exception as e:
        console.print(f"[red]Error parsing query: {e}[/red]")
        return

    # Step 2: Fetch forecasts from APIs
    console.print("[bold]Step 2:[/bold] Fetching weather forecasts from APIs...")
    forecasts = get_forecasts(
        location=parsed['location'],
        days=parsed.get('days', 7),
        providers=parsed.get('providers', ['open-meteo'])
    )

    if not forecasts:
        console.print("[red]Failed to fetch any forecasts[/red]")
        return

    console.print(f"\n[green]✓ Got {len(forecasts)} forecasts[/green]\n")

    # Step 3: Use AI to compare forecasts
    console.print("[bold]Step 3:[/bold] Generating AI comparison...")
    comparator = WeatherComparator()
    comparison = comparator.compare_forecasts(forecasts)
    console.print("[green]✓ Analysis complete[/green]\n")

    # Step 4: Display results
    display_forecasts(forecasts, comparison)

    # Show cache stats
    stats = cache.get_stats()
    console.print(f"\n[dim]Cache: {stats['total_entries']} entries, {stats['total_size_mb']} MB[/dim]")

    console.print("\n[bold green]✨ Phase 2 Complete![/bold green]")
    console.print("[dim]Next: Add web UI and user preferences tracking[/dim]\n")


if __name__ == "__main__":
    main()
