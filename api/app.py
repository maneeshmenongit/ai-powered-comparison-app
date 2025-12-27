"""api/app.py

Hopwise Backend API
Provides ride and restaurant comparison endpoints.
"""

import sys
import os

# Load .env file for local development
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

sys.path.insert(0, 'src')

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from domains.rideshare.handler import RideShareHandler
from domains.restaurants.handler import RestaurantHandler
from core import GeocodingService, CacheService, RateLimiter
from orchestration.domain_router import DomainRouter

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize services (singleton pattern)
geocoder = GeocodingService()
cache = CacheService()
rate_limiter = RateLimiter()

rideshare_handler = RideShareHandler(
    geocoding_service=geocoder,
    cache_service=cache,
    rate_limiter=rate_limiter
)

restaurant_handler = RestaurantHandler(
    geocoding_service=geocoder,
    cache_service=cache,
    rate_limiter=rate_limiter
)

# Initialize domain router
domain_router = DomainRouter()
# ============================================================================
# ROUTES
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint for Railway health check."""
    return jsonify({
        'status': 'healthy',
        'service': 'hopwise-api',
        'version': '1.0.0',
        'message': 'API is running. Use /api/* endpoints.'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    import os
    google_key = os.getenv('GOOGLE_PLACES_API_KEY', '')

    # Check for quotes in the key
    has_quotes = google_key.startswith('"') or google_key.startswith("'")
    key_length = len(google_key)
    key_preview = f"{google_key[:10]}...{google_key[-4:]}" if len(google_key) > 14 else "NOT_SET"

    return jsonify({
        'status': 'healthy',
        'service': 'hopwise-api',
        'version': '1.0.0',
        'google_api_key_configured': bool(google_key),
        'google_api_key_length': key_length,
        'google_api_key_preview': key_preview,
        'google_api_key_has_quotes': has_quotes
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get frontend configuration including API keys."""
    import os
    return jsonify({
        'google_maps_api_key': os.getenv('GOOGLE_PLACES_API_KEY', ''),
        'ga_measurement_id': os.getenv('GA_MEASUREMENT_ID', '')
    })


@app.route('/api/rides', methods=['POST'])
def compare_rides():
    """
    Compare ride options (Uber, Lyft).
    
    Request body:
    {
        "origin": "Times Square, NYC",
        "destination": "Central Park, NYC"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'origin' not in data or 'destination' not in data:
            return jsonify({
                'error': 'Missing required fields: origin, destination'
            }), 400
        
        origin = data['origin']
        destination = data['destination']
        
        # Build query
        query = f"ride from {origin} to {destination}"
        
        # Process
        results = rideshare_handler.process(
            query,
            context={'user_location': origin}
        )
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        print(f"Error in /api/rides: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/restaurants', methods=['POST'])
def search_restaurants():
    """
    Search restaurants with filters.

    Request body:
    {
        "query": "Italian food",
        "location": "Times Square, NYC",
        "filter_category": "Food",  // Food, Drinks, Ice Cream, Cafe
        "priority": "balanced"       // balanced, rating, price, distance
    }
    """
    try:
        data = request.get_json()

        # Validate input
        if not data or 'location' not in data:
            return jsonify({
                'error': 'Missing required field: location'
            }), 400

        location = data['location']
        query = data.get('query', 'restaurants')
        filter_category = data.get('filter_category', 'Food')
        priority = data.get('priority', 'balanced')

        # Build full query
        full_query = f"{query} near {location}"

        # Process
        use_ai = data.get('use_ai', False)  # Default to fast mode

        results = restaurant_handler.process(
            full_query,
            context={'user_location': location},
            priority=priority,
            use_ai=use_ai
        )

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        print(f"Error in /api/restaurants: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search', methods=['POST'])
def unified_search():
    """
    Unified search endpoint that uses domain routing.

    Analyzes the query and routes to appropriate domain(s).

    Request body:
    {
        "query": "need a ride to times square",
        "location": "Central Park, NYC"  // optional, defaults to query location
    }

    Response:
    {
        "success": true,
        "domain": "rideshare",  // or "restaurants"
        "data": {...}  // domain-specific results
    }
    """
    try:
        data = request.get_json()

        # Validate input
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing required field: query'
            }), 400

        query = data['query']
        location = data.get('location', '')

        # Route query to appropriate domain(s)
        domains = domain_router.route(query)

        print(f"Query: '{query}' routed to domains: {domains}")

        if not domains:
            return jsonify({
                'success': False,
                'error': 'Could not determine domain for query'
            }), 400

        # For now, handle single domain (first match)
        primary_domain = domains[0]

        # Route to appropriate handler
        if primary_domain == 'rideshare':
            # Parse origin/destination from query
            origin = location if location else "Times Square, NYC"
            destination = "Central Park, NYC"  # Default

            # Simple destination extraction (can be improved with NLP)
            query_lower = query.lower()
            if ' to ' in query_lower:
                parts = query_lower.split(' to ')
                if len(parts) == 2:
                    destination = parts[1].strip().title()
                    # Check if origin is specified
                    first_part = parts[0].strip()
                    if 'from ' in first_part:
                        origin = first_part.split('from ')[-1].strip().title()
                    elif location:
                        origin = location

            # Build rideshare query
            ride_query = f"ride from {origin} to {destination}"

            results = rideshare_handler.process(
                ride_query,
                context={'user_location': origin}
            )

            return jsonify({
                'success': True,
                'domain': 'rideshare',
                'query_parsed': {
                    'origin': origin,
                    'destination': destination
                },
                'data': results
            })

        elif primary_domain == 'restaurants':
            # Use restaurant handler
            full_query = f"{query} near {location}" if location else query

            results = restaurant_handler.process(
                full_query,
                context={
                    'user_location': location,
                    'filter_category': 'Food',
                    'priority': 'balanced'
                }
            )

            return jsonify({
                'success': True,
                'domain': 'restaurants',
                'data': results
            })

        else:
            return jsonify({
                'success': False,
                'error': f'Domain {primary_domain} not yet implemented'
            }), 501

    except Exception as e:
        print(f"Error in /api/search: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get cache and rate limiter statistics."""
    try:
        cache_stats = cache.stats()
        rl_stats = rate_limiter.stats()
        
        return jsonify({
            'success': True,
            'data': {
                'cache': cache_stats,
                'rate_limiter': rl_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    import os
    from waitress import serve

    port = int(os.environ.get('PORT', 5001))

    print(f"Starting Hopwise API on port {port}...")

    # Use waitress production WSGI server
    serve(app, host='0.0.0.0', port=port, threads=4, channel_timeout=300)