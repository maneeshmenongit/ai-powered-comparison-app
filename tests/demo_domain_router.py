"""Demo script showing domain router capabilities."""

import sys
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from orchestration import DomainRouter
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# Print banner
console.print("\n[bold cyan]╔════════════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║     Multi-Domain Query Router - Demo                ║[/bold cyan]")
console.print("[bold cyan]╚════════════════════════════════════════════════════════╝[/bold cyan]\n")

# Initialize router
console.print("[cyan]🔧 Initializing Domain Router...[/cyan]")
router = DomainRouter()
console.print(f"[green]✅ Router ready: {router}[/green]\n")

# Create test scenarios
scenarios = [
    {
        'category': '🚗 Single Domain - Rideshare',
        'queries': [
            "Get me an Uber to JFK",
            "Compare Lyft and Uber prices",
            "I need a ride home",
        ]
    },
    {
        'category': '🍝 Single Domain - Restaurants',
        'queries': [
            "Find a good Italian restaurant",
            "Where should I eat dinner?",
            "Best pizza places nearby",
        ]
    },
    {
        'category': '🔀 Multi-Domain Queries',
        'queries': [
            "I need a ride and want to eat Italian food",
            "Take me to a nice restaurant",
            "Plan my evening - dinner and transportation",
        ]
    },
    {
        'category': '🤔 Ambiguous Queries (AI helps)',
        'queries': [
            "I want to go somewhere nice",
            "Plan my anniversary",
            "What should I do tonight?",
        ]
    }
]

# Test each scenario
for scenario in scenarios:
    console.print(f"\n[bold yellow]{scenario['category']}[/bold yellow]")
    console.print("─" * 60)

    for query in scenario['queries']:
        # Route the query
        domains = router.route(query)

        # Check if multi-domain
        is_multi = router.is_multi_domain(domains)
        multi_badge = "[red](multi-domain)[/red]" if is_multi else "[dim](single)[/dim]"

        # Format domains
        if domains:
            domains_str = "[green]" + " + ".join(domains) + "[/green]"
        else:
            domains_str = "[dim]no domains[/dim]"

        console.print(f"  Query: [white]\"{query}\"[/white]")
        console.print(f"  → Routed to: {domains_str} {multi_badge}\n")

# Show routing statistics table
console.print("\n[bold cyan]📊 Domain Router Features[/bold cyan]")
console.print("─" * 60)

features_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
features_table.add_column("Feature", style="cyan", no_wrap=True)
features_table.add_column("Description", style="white")
features_table.add_column("Status", justify="center")

features_table.add_row(
    "Fast Keyword Matching",
    "No API call for simple queries",
    "[green]✓[/green]"
)
features_table.add_row(
    "AI Fallback",
    "Handles ambiguous queries with GPT-4o-mini",
    "[green]✓[/green]"
)
features_table.add_row(
    "Multi-Domain Support",
    "Single query → Multiple domains",
    "[green]✓[/green]"
)
features_table.add_row(
    "Priority Ordering",
    "Most important domains first",
    "[green]✓[/green]"
)
features_table.add_row(
    "Extensible",
    "Easy to add new domains",
    "[green]✓[/green]"
)
features_table.add_row(
    "Graceful Degradation",
    "Falls back to keywords if AI fails",
    "[green]✓[/green]"
)

console.print(features_table)

# Show enabled domains
console.print("\n[bold cyan]🌍 Enabled Domains[/bold cyan]")
console.print("─" * 60)

domains_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
domains_table.add_column("Domain", style="cyan")
domains_table.add_column("Description", style="white")
domains_table.add_column("Keywords", style="dim")

for domain_name in router.get_enabled_domains():
    domain_info = router.AVAILABLE_DOMAINS[domain_name]
    keywords = ", ".join(domain_info['keywords'][:5]) + "..."
    domains_table.add_row(
        domain_name,
        domain_info['description'],
        keywords
    )

console.print(domains_table)

console.print("\n[green]✅ Domain Router Demo Complete![/green]\n")
