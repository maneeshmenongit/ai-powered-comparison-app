"""api/app.py

Hopwise Backend API
Provides ride and restaurant comparison endpoints.
"""

import sys
import os
sys.path.insert(0, 'src')

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

# Check for required environment variables
print("🔍 Checking environment variables...")
print(f"PORT: {os.getenv('PORT', 'not set')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'not set')}")
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"✅ OPENAI_API_KEY found (length: {len(openai_key)})")
else:
    print("❌ OPENAI_API_KEY not found!")
    print(f"Available env vars: {[k for k in os.environ.keys() if 'API' in k or 'KEY' in k]}")

print("\n🚀 Starting Flask app initialization...")

from domains.rideshare.handler import RideShareHandler
from domains.restaurants.handler import RestaurantHandler
from core import GeocodingService, CacheService, RateLimiter

print("✅ Imports successful")

# Initialize Flask app
print("📦 Creating Flask app...")
app = Flask(__name__)
print("✅ Flask app created")

# Configure CORS for frontend - allow all origins for now to debug
print("🌐 Configuring CORS...")
CORS(app, resources={r"/api/*": {"origins": "*"}})
print("✅ CORS configured")

# Initialize services (singleton pattern)
print("⚙️  Initializing services...")
geocoder = GeocodingService()
cache = CacheService()
rate_limiter = RateLimiter()
print("✅ Services initialized")

print("🚗 Initializing rideshare handler...")
rideshare_handler = RideShareHandler(
    geocoding_service=geocoder,
    cache_service=cache,
    rate_limiter=rate_limiter
)
print("✅ Rideshare handler initialized")

print("🍽️  Initializing restaurant handler...")
restaurant_handler = RestaurantHandler(
    geocoding_service=geocoder,
    cache_service=cache,
    rate_limiter=rate_limiter
)
print("✅ Restaurant handler initialized")

print("\n✨ All initialization complete! App is ready.")
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
    import sys
    print(f"🚨 /api/restaurants ENDPOINT HIT!", file=sys.stderr, flush=True)
    try:
        print(f"📥 /api/restaurants request received", flush=True)
        data = request.get_json()
        print(f"📦 Request data: {data}")

        # Validate input
        if not data or 'location' not in data:
            print(f"❌ Missing location field")
            return jsonify({
                'error': 'Missing required field: location'
            }), 400

        location = data['location']
        query = data.get('query', 'restaurants')
        filter_category = data.get('filter_category', 'Food')
        priority = data.get('priority', 'balanced')
        use_ai = data.get('use_ai', False)

        print(f"🔍 Processing: query='{query}', location='{location}', priority='{priority}', use_ai={use_ai}")

        # Build full query
        full_query = f"{query} near {location}"

        # Process
        print(f"⚙️  Calling restaurant_handler.process...")
        results = restaurant_handler.process(
            full_query,
            context={'user_location': location},
            priority=priority,
            use_ai=use_ai
        )
        print(f"✅ Processing complete, {results.get('total_results', 0)} results")
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        print(f"❌ ERROR in /api/restaurants: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
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

# Add to the end of api/app.py, replace the if __name__ section:

if __name__ == '__main__':
    import os
    
    # Get port from environment (for Railway/Render)
    port = int(os.environ.get('PORT', 5001))
    
    # Get environment
    env = os.environ.get('ENVIRONMENT', 'development')
    debug = env == 'development'
    
    print("🌍 Hopwise API starting...")
    print(f"📡 Environment: {env}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🚀 Port: {port}")
    print("📡 Endpoints available:")
    print("   GET  /api/health")
    print("   POST /api/rides")
    print("   POST /api/restaurants")
    print("   GET  /api/stats")
    print(f"\n✅ Server running on port {port}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)