"""main_restaurants.py

Hopwise - Restaurant Search Terminal Application
Every stop matters! Hop smarter!
"""

import sys
sys.path.insert(0, 'src')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from domains.restaurants.handler import RestaurantHandler
from domains.restaurants.models import FILTER_CATEGORIES
from core import GeocodingService, CacheService, RateLimiter

console = Console()


def print_banner():
    """Display app banner."""
    console.print("\n")
    console.print("[bold]" + "=" * 60 + "[/bold]")
    console.print(Panel.fit(
        "[bold cyan]🌍 Hopwise - Restaurant Search[/bold cyan]\n"
        "[dim]Every stop matters! Hop smarter![/dim]",
        border_style="cyan"
    ))
    console.print("[bold]" + "=" * 60 + "[/bold]\n")


def print_filters():
    """Display available filter categories."""
    console.print("\n[bold]🎯 Filter Categories:[/bold]")
    for name, info in FILTER_CATEGORIES.items():
        console.print(f"  {info['icon']} [cyan]{name}[/cyan]: {info['description']}")


def get_user_inputs():
    """Get user inputs for restaurant search."""
    console.print("\n[bold]🔍 Restaurant Search[/bold]\n")
    
    # Get location
    location = Prompt.ask(
        "[cyan]Your location[/cyan]",
        default="New York, NY"
    )
    
    # Get search query
    query = Prompt.ask(
        "[cyan]What are you looking for?[/cyan]",
        default="Italian food"
    )
    
    # Show filter options
    print_filters()
    
    # Get filter preference
    filter_choice = Prompt.ask(
        "\n[cyan]Filter category[/cyan]",
        choices=list(FILTER_CATEGORIES.keys()),
        default="Food"
    )
    
    # Get priority
    console.print("\n[bold]🎯 Comparison Priority:[/bold]")
    console.print("  • [cyan]rating[/cyan]  - Highest rated restaurants")
    console.print("  • [cyan]price[/cyan]   - Best value options")
    console.print("  • [cyan]distance[/cyan] - Closest restaurants")
    console.print("  • [cyan]balanced[/cyan] - Overall best choice\n")
    
    priority = Prompt.ask(
        "[cyan]Priority[/cyan]",
        choices=["rating", "price", "distance", "balanced"],
        default="balanced"
    )
    
    return location, query, filter_choice, priority


def display_results(results):
    """Display restaurant results in a table."""
    if not results['restaurants']:
        console.print("\n[yellow]No restaurants found. Try different criteria.[/yellow]")
        return
    
    # Create table
    table = Table(
        title=f"\n🍽️ Restaurant Results ({results['total_results']} found)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("Provider", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Rating", justify="center")
    table.add_column("Reviews", justify="right")
    table.add_column("Price", justify="center")
    table.add_column("Distance", justify="right")
    table.add_column("Open", justify="center")
    
    # Add rows
    for r in results['restaurants'][:10]:  # Show top 10
        # Star display
        stars = "⭐" * int(r['rating'])
        rating_str = f"{stars} {r['rating']}"
        
        # Reviews
        reviews_str = f"{r['review_count']:,}"
        
        # Distance
        distance_str = f"{r['distance']:.1f}mi"
        
        # Open status
        open_str = "✅" if r['is_open'] else "🔴"
        
        table.add_row(
            r['provider'],
            r['name'],
            rating_str,
            reviews_str,
            r['price_range'] or "N/A",
            distance_str,
            open_str
        )
    
    console.print(table)
    
    # Display recommendation
    console.print(f"\n[bold cyan]💡 Recommendation:[/bold cyan]")
    console.print(Panel(
        results['comparison'],
        border_style="green",
        padding=(1, 2)
    ))


def display_stats(cache_service, rate_limiter):
    """Display cache and rate limiter statistics."""
    console.print("\n[bold]📊 Statistics:[/bold]")
    
    # Cache stats
    cache_stats = cache_service.stats()
    hit_rate = cache_stats.get('hit_rate_percent', 0)
    hits = cache_stats.get('hits', 0)
    misses = cache_stats.get('misses', 0)
    
    if hits + misses > 0:
        console.print(f"  Cache: {hits} hits, {misses} misses ([cyan]{hit_rate:.1f}%[/cyan] hit rate)")
    
    # Rate limiter stats
    rl_stats = rate_limiter.stats()
    console.print(f"  Rate Limiter: {rl_stats.get('total_requests', 0)} requests")


def main():
    """Main application loop."""
    print_banner()
    
    # Initialize services
    console.print("🔧 [dim]Initializing services...[/dim]")
    geocoder = GeocodingService()
    cache = CacheService()
    rate_limiter = RateLimiter()
    
    console.print("  ✅ Geocoding service")
    console.print("  ✅ Cache service")
    console.print("  ✅ Rate limiter")
    
    # Initialize handler
    handler = RestaurantHandler(
        geocoding_service=geocoder,
        cache_service=cache,
        rate_limiter=rate_limiter
    )
    
    while True:
        try:
            # Get user inputs
            location, query, filter_choice, priority = get_user_inputs()
            
            # Build full query with filter
            full_query = f"{query} near {location}"
            
            console.print(f"\n⚙️  [dim]Searching for {filter_choice.lower()}...[/dim]")
            
            # Process query
            results = handler.process(
                full_query,
                context={'user_location': location},
                priority=priority
            )
            
            # Display results
            display_results(results)
            
            # Display stats
            display_stats(cache, rate_limiter)
            
            # Ask if user wants to search again
            console.print()
            if not Confirm.ask("[cyan]Search again?[/cyan]", default=True):
                break
                
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Goodbye![/yellow]\n")
            break
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            console.print("[dim]Try again with different inputs.[/dim]\n")
            if not Confirm.ask("[cyan]Try again?[/cyan]", default=True):
                break
    
    console.print("\n[bold cyan]Thanks for using Hopwise![/bold cyan] 🌍\n")


if __name__ == "__main__":
    main()