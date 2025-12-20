"""api/app.py

Hopwise Backend API
Provides ride and restaurant comparison endpoints.
"""

import sys
sys.path.insert(0, 'src')

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from domains.rideshare.handler import RideShareHandler
from domains.restaurants.handler import RestaurantHandler
from core import GeocodingService, CacheService, RateLimiter

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

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


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'hopwise-api',
        'version': '1.0.0'
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
        results = restaurant_handler.process(
            full_query,
            context={'user_location': location},
            priority=priority
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
    print("🌍 Hopwise API starting...")
    print("📡 Endpoints available:")
    print("   GET  /api/health")
    print("   POST /api/rides")
    print("   POST /api/restaurants")
    print("   GET  /api/stats")
    print("\n✅ Server running on http://localhost:5001\n")

    app.run(host='0.0.0.0', port=5001, debug=True)