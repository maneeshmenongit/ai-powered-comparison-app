"""
Proof of Concept: AI-Powered Ride Comparison Tool
This demonstrates the core concept using OpenAI to parse user intent
and compare mock ride-sharing data.

Before running:
1. pip install openai rich python-dotenv
2. Create a .env file with: OPENAI_API_KEY=your_key_here
3. Run: python comparison_poc.py
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Load environment variables
load_dotenv()

# Initialize
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
console = Console()


@dataclass
class RideEstimate:
    """Represents a ride estimate from a service"""
    service: str
    price: float
    duration_minutes: int
    distance_miles: float
    vehicle_type: str


def parse_user_query(query: str) -> Dict:
    """
    Use OpenAI to extract structured information from natural language query.
    
    This is the KEY AI component - it takes messy human language and converts it
    into structured data we can use for API calls.
    
    Example input: "Compare Uber and Lyft from Times Square to JFK"
    Example output: {
        "origin": "Times Square, New York",
        "destination": "JFK Airport, New York",
        "services": ["uber", "lyft"]
    }
    """
    
    system_prompt = """You are a helpful assistant that extracts ride comparison intent from user queries.
Extract the following information:
- origin: starting location
- destination: ending location  
- services: list of services to compare (uber, lyft, etc.)

Return ONLY valid JSON with these fields. If a field is unclear, make a reasonable assumption.
For services, if not specified, default to ["uber", "lyft"]."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model, good for structured tasks
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0,  # Deterministic output for structured data
            response_format={"type": "json_object"}  # Ensures JSON response
        )
        
        result = json.loads(response.choices[0].message.content)
        console.print(f"[green]✓ Parsed query successfully[/green]")
        console.print(f"  Origin: {result.get('origin')}")
        console.print(f"  Destination: {result.get('destination')}")
        console.print(f"  Services: {', '.join(result.get('services', []))}\n")
        
        return result
    
    except Exception as e:
        console.print(f"[red]Error parsing query: {e}[/red]")
        return {}


def get_uber_estimate(origin: str, destination: str) -> RideEstimate:
    """
    Mock function simulating Uber API call.
    In a real implementation, this would call Uber's actual API.
    
    The AI helps here by normalizing the location strings that came
    from natural language into what the API expects.
    """
    # Simulated data - in reality, this would come from API
    return RideEstimate(
        service="Uber",
        price=45.50,
        duration_minutes=35,
        distance_miles=15.2,
        vehicle_type="UberX"
    )


def get_lyft_estimate(origin: str, destination: str) -> RideEstimate:
    """
    Mock function simulating Lyft API call.
    In reality, this would call Lyft's actual API.
    """
    # Simulated data
    return RideEstimate(
        service="Lyft",
        price=42.00,
        duration_minutes=38,
        distance_miles=15.2,
        vehicle_type="Lyft"
    )


def compare_rides(estimates: List[RideEstimate]) -> str:
    """
    Use OpenAI to generate a natural language comparison and recommendation.
    
    This demonstrates how AI can take structured data and create human-friendly
    insights - going beyond just displaying numbers.
    """
    
    # Convert estimates to a format the LLM can easily understand
    estimates_text = "\n".join([
        f"{e.service}: ${e.price}, {e.duration_minutes} min, {e.distance_miles} miles"
        for e in estimates
    ])
    
    prompt = f"""Compare these ride estimates and provide a brief recommendation:

{estimates_text}

Provide:
1. Which is cheapest and by how much
2. Which is fastest and by how much  
3. Your recommendation based on best value

Keep it concise (2-3 sentences)."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes ride options."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7  # Slightly more creative for recommendations
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating comparison: {e}"


def display_results(estimates: List[RideEstimate], recommendation: str):
    """Display results in a nice table format"""
    
    # Create comparison table
    table = Table(title="🚗 Ride Comparison Results", show_header=True, header_style="bold cyan")
    table.add_column("Service", style="yellow", width=12)
    table.add_column("Price", justify="right", style="green")
    table.add_column("Duration", justify="right")
    table.add_column("Distance", justify="right")
    table.add_column("Vehicle Type")
    
    for estimate in estimates:
        table.add_row(
            estimate.service,
            f"${estimate.price:.2f}",
            f"{estimate.duration_minutes} min",
            f"{estimate.distance_miles} mi",
            estimate.vehicle_type
        )
    
    console.print(table)
    console.print()
    
    # Display AI recommendation
    console.print(Panel(
        recommendation,
        title="💡 AI Recommendation",
        border_style="blue"
    ))


def main():
    """Main execution flow"""
    
    console.print("\n[bold cyan]🤖 AI-Powered Ride Comparison Tool (POC)[/bold cyan]\n")
    
    # Get user query
    query = input("Enter your comparison query (or press Enter for example): ").strip()
    
    if not query:
        query = "Compare Uber and Lyft from Times Square to JFK Airport"
        console.print(f"[dim]Using example: {query}[/dim]\n")
    
    # Step 1: Parse user intent with AI
    console.print("[bold]Step 1:[/bold] Parsing your query with AI...")
    parsed = parse_user_query(query)
    
    if not parsed:
        return
    
    # Step 2: Get estimates from services
    console.print("[bold]Step 2:[/bold] Fetching ride estimates (using mock data)...")
    estimates = []
    
    if "uber" in [s.lower() for s in parsed.get("services", [])]:
        estimates.append(get_uber_estimate(parsed["origin"], parsed["destination"]))
    
    if "lyft" in [s.lower() for s in parsed.get("services", [])]:
        estimates.append(get_lyft_estimate(parsed["origin"], parsed["destination"]))
    
    console.print(f"[green]✓ Got {len(estimates)} estimates[/green]\n")
    
    # Step 3: Use AI to compare and recommend
    console.print("[bold]Step 3:[/bold] Generating AI comparison...")
    recommendation = compare_rides(estimates)
    console.print("[green]✓ Analysis complete[/green]\n")
    
    # Step 4: Display results
    display_results(estimates, recommendation)
    
    console.print("\n[dim]This is a proof of concept using mock data.[/dim]")
    console.print("[dim]Next steps: Integrate real APIs and add more services![/dim]\n")


if __name__ == "__main__":
    main()
