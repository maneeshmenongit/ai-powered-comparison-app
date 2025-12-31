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
# Add parent directory to path for api module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import traceback
from datetime import timedelta

from domains.rideshare.handler import RideShareHandler
from domains.restaurants.handler import RestaurantHandler
from core import GeocodingService, CacheService, RateLimiter
from orchestration.domain_router import DomainRouter
from cost_tracker import CostTracker, create_cost_tracker_blueprint

# Database imports
from api.database import SessionLocal, close_db
from api.models import User, SavedRestaurant
from api.db_init import initialize_database
import uuid

# Initialize Flask app
app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
jwt = JWTManager(app)

# Configure CORS for frontend
CORS(app, resources={r"/api/*": {
    "origins": [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # For admin dashboard served locally
        "https://hopwise.app",
        "https://www.hopwise.app",
        "https://app.hopwise.app",
        "https://*.netlify.app",  # For admin dashboard on Netlify (including preview deploys)
        "null"  # For file:// protocol (admin dashboard opened directly)
    ]
}})

# Initialize services (singleton pattern)
geocoder = GeocodingService()
cache = CacheService()
rate_limiter = RateLimiter()

# Initialize cost tracker
cost_tracker = CostTracker(data_dir="./cost_data")
app.config['COST_TRACKER'] = cost_tracker

# Register cost tracker endpoints
app.register_blueprint(
    create_cost_tracker_blueprint(cost_tracker),
    url_prefix='/api/costs'
)

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

# Initialize database
print("Initializing database...")
initialize_database()

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


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user account.

    Request body:
    {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "securepassword123"
    }
    """
    db = SessionLocal()
    try:
        data = request.get_json()

        # Validate input
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Username, email, and password are required'
            }), 400

        # Validate password length
        if len(password) < 8:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 8 characters'
            }), 400

        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 409

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 409

        # Create new user
        user = User(
            username=username,
            email=email,
            is_guest=False,
            is_premium=False
        )
        user.set_password(password)

        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate JWT token (identity must be string for Flask-JWT-Extended v4+)
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        }), 201

    except Exception as e:
        db.rollback()
        print(f"Registration error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Registration failed'
        }), 500
    finally:
        db.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login with email and password.

    Request body:
    {
        "email": "john@example.com",
        "password": "securepassword123"
    }
    """
    db = SessionLocal()
    try:
        data = request.get_json()

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        # Find user by email
        user = db.query(User).filter(User.email == email).first()

        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        # Generate JWT token (identity must be string for Flask-JWT-Extended v4+)
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        }), 200

    except Exception as e:
        print(f"Login error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500
    finally:
        db.close()


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout current user.
    Note: JWT tokens are stateless, so logout is handled client-side by removing the token.
    This endpoint exists for consistency and can be extended with token blacklisting if needed.
    """
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user information.
    Requires JWT token in Authorization header: "Bearer <token>"
    """
    db = SessionLocal()
    try:
        # Get user from JWT token
        user = get_current_user_from_jwt(db)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200

    except Exception as e:
        print(f"Get current user error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Failed to get user information'
        }), 500
    finally:
        db.close()


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

        # Check if user is authenticated (has JWT token)
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        is_authenticated = False
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            is_authenticated = user_id is not None
        except:
            is_authenticated = False

        location = data['location']
        query = data.get('query', 'restaurants')
        filter_category = data.get('filter_category', 'Food')
        priority = data.get('priority', 'balanced')
        use_ai = data.get('use_ai', False)

        # Limit AI usage and results for guest users
        if not is_authenticated:
            use_ai = False  # Force disable AI for guests
            print("Guest user request - AI disabled, results limited")

        # Build full query
        full_query = f"{query} near {location}"

        # Process
        results = restaurant_handler.process(
            full_query,
            context={'user_location': location},
            priority=priority,
            use_ai=use_ai
        )

        # Limit results for guest users (max 5 results)
        if not is_authenticated and results.get('data', {}).get('results'):
            results['data']['results'] = results['data']['results'][:5]
            results['data']['guest_limited'] = True
            results['data']['message'] = 'Sign up to see more results and get AI recommendations!'

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
# USER FAVORITES ENDPOINTS
# ============================================================================

def get_current_user_from_jwt(db):
    """
    Helper function to get current user from JWT token.
    Converts UUID string from JWT to UUID object and queries database.
    """
    user_id_str = get_jwt_identity()
    user_id = uuid.UUID(user_id_str)  # Convert string to UUID
    return db.query(User).filter(User.id == user_id).first()

@app.route('/api/user/saved', methods=['POST'])
@jwt_required()
def save_restaurant():
    """
    Save a restaurant to user's favorites.
    Requires JWT authentication.

    Request body:
    {
        "restaurant_id": "ChIJ...",
        "restaurant_data": {...}     // full restaurant object
    }
    """
    db = SessionLocal()
    try:
        # Get user from JWT token
        user = get_current_user_from_jwt(db)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json()

        # Validate required fields
        if not data.get('restaurant_id') or not data.get('restaurant_data'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: restaurant_id, restaurant_data'
            }), 400

        # Check if already saved
        existing = db.query(SavedRestaurant).filter(
            SavedRestaurant.user_id == user.id,
            SavedRestaurant.restaurant_id == data['restaurant_id']
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'error': 'Restaurant already saved',
                'data': existing.to_dict()
            }), 409

        # Create saved restaurant
        saved = SavedRestaurant(
            user_id=user.id,
            restaurant_id=data['restaurant_id'],
            restaurant_data=data['restaurant_data']
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)

        return jsonify({
            'success': True,
            'data': saved.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        print(f"Error in /api/user/saved POST: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/api/user/saved', methods=['GET'])
@jwt_required()
def get_saved_restaurants():
    """
    Get user's saved restaurants.
    Requires JWT authentication.
    """
    db = SessionLocal()
    try:
        # Get user from JWT token
        user = get_current_user_from_jwt(db)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Get saved restaurants
        saved_restaurants = db.query(SavedRestaurant).filter(
            SavedRestaurant.user_id == user.id
        ).order_by(SavedRestaurant.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': [saved.to_dict() for saved in saved_restaurants]
        })

    except Exception as e:
        print(f"Error in /api/user/saved GET: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/api/user/saved/<int:saved_id>', methods=['DELETE'])
@jwt_required()
def delete_saved_restaurant(saved_id):
    """
    Delete a saved restaurant.
    Requires JWT authentication.
    """
    db = SessionLocal()
    try:
        # Get user from JWT token
        user = get_current_user_from_jwt(db)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Get saved restaurant (ensure it belongs to this user)
        saved = db.query(SavedRestaurant).filter(
            SavedRestaurant.id == saved_id,
            SavedRestaurant.user_id == user.id
        ).first()

        if not saved:
            return jsonify({
                'success': False,
                'error': 'Saved restaurant not found'
            }), 404

        # Delete
        db.delete(saved)
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Restaurant removed from saved items'
        })

    except Exception as e:
        db.rollback()
        print(f"Error in /api/user/saved DELETE: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


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