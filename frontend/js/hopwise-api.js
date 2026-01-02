/**
 * frontend/hopwise-api.js
 *
 * JavaScript to connect UI designs to Flask backend
 */

// Use global API_BASE_URL defined in index.html (before scripts load)
// Fallback to production if not defined
const API_BASE_URL = window.API_BASE_URL || 'https://api.hopwise.app/api';

// ============================================================================
// API Client
// ============================================================================

class HopwiseAPI {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        // Get auth token from authManager if available
        const authHeader = window.authManager?.getAuthHeader();

        // Debug logging for authentication
        console.log(`[HopwiseAPI] ${options.method || 'GET'} ${endpoint}`, {
            hasAuthHeader: !!authHeader,
            authHeader: authHeader ? 'Bearer ***' : null
        });

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                    ...(authHeader || {})
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.msg || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }

    // Compare rides
    async compareRides(origin, destination) {
        return this.request('/rides', {
            method: 'POST',
            body: JSON.stringify({ origin, destination })
        });
    }

    // Search restaurants
    async searchRestaurants(location, query = '', filterCategory = 'Food', priority = 'balanced', useAI = false) {
        return this.request('/restaurants', {
            method: 'POST',
            body: JSON.stringify({
                location,
                query,
                filter_category: filterCategory,
                priority,
                use_ai: useAI
            })
        });
    }

    async getAIRecommendation(location, query = '', filterCategory = 'Food', priority = 'balanced') {
    return this.searchRestaurants(location, query, filterCategory, priority, true);
    }

    // Get statistics
    async getStats() {
        return this.request('/stats');
    }

    // ========================================
    // FAVORITES API (Requires JWT Authentication)
    // ========================================

    /**
     * Save a restaurant to favorites
     * Requires user to be logged in (JWT token)
     * @param {string} restaurantId - Place ID of the restaurant
     * @param {object} restaurantData - Full restaurant data object
     * @returns {Promise} API response
     */
    async saveRestaurant(restaurantId, restaurantData) {
        return this.request('/user/saved', {
            method: 'POST',
            body: JSON.stringify({
                restaurant_id: restaurantId,
                restaurant_data: restaurantData
            })
        });
    }

    /**
     * Get all saved restaurants for authenticated user
     * Requires user to be logged in (JWT token)
     * @returns {Promise} API response with saved restaurants array
     */
    async getSavedRestaurants() {
        return this.request('/user/saved', {
            method: 'GET'
        });
    }

    /**
     * Remove a saved restaurant
     * Requires user to be logged in (JWT token)
     * @param {number} savedId - ID of the saved restaurant record
     * @returns {Promise} API response
     */
    async removeSavedRestaurant(savedId) {
        return this.request(`/user/saved/${savedId}`, {
            method: 'DELETE'
        });
    }

    // ============================================================================
    // Trip Planning API Methods (Registered Users Only)
    // ============================================================================

    /**
     * Create a new trip
     * @param {object} tripData - Trip data {name, start_date, end_date}
     * @returns {Promise} API response with trip data
     */
    async createTrip(tripData) {
        return this.request('/trips', {
            method: 'POST',
            body: JSON.stringify(tripData)
        });
    }

    /**
     * Get all trips for the current user
     * @returns {Promise} API response with trips array
     */
    async getTrips() {
        return this.request('/trips', {
            method: 'GET'
        });
    }

    /**
     * Get a specific trip by ID
     * @param {string} tripId - Trip ID
     * @returns {Promise} API response with trip data
     */
    async getTrip(tripId) {
        return this.request(`/trips/${tripId}`, {
            method: 'GET'
        });
    }

    /**
     * Update a trip
     * @param {string} tripId - Trip ID
     * @param {object} tripData - Updated trip data {name, start_date, end_date}
     * @returns {Promise} API response with updated trip data
     */
    async updateTrip(tripId, tripData) {
        return this.request(`/trips/${tripId}`, {
            method: 'PUT',
            body: JSON.stringify(tripData)
        });
    }

    /**
     * Delete a trip
     * @param {string} tripId - Trip ID
     * @returns {Promise} API response
     */
    async deleteTrip(tripId) {
        return this.request(`/trips/${tripId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Add an item to a trip
     * @param {string} tripId - Trip ID
     * @param {object} itemData - Item data {item_type, item_data, item_order, scheduled_time}
     * @returns {Promise} API response with trip item data
     */
    async addTripItem(tripId, itemData) {
        return this.request(`/trips/${tripId}/items`, {
            method: 'POST',
            body: JSON.stringify(itemData)
        });
    }

    /**
     * Remove an item from a trip
     * @param {string} tripId - Trip ID
     * @param {string} itemId - Item ID
     * @returns {Promise} API response
     */
    async removeTripItem(tripId, itemId) {
        return this.request(`/trips/${tripId}/items/${itemId}`, {
            method: 'DELETE'
        });
    }
}

// ============================================================================
// UI Helpers
// ============================================================================

// Show loading state
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading">🔄 Searching...</div>';
    }
}

// Show error
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="error">❌ ${message}</div>`;
    }
}

// Format ride results
function formatRideResults(results) {
    // API returns 'estimates' not 'rides'
    const rides = results.estimates || results.rides || [];

    if (rides.length === 0) {
        return '<p>No rides found</p>';
    }

    let html = '<div class="ride-results">';

    // Results table
    html += '<div class="results-grid">';
    rides.forEach(ride => {
        html += `
            <div class="ride-card">
                <div class="provider">${ride.provider}</div>
                <div class="service">${ride.vehicle_type}</div>
                <div class="price">$${ride.price.toFixed(2)}</div>
                <div class="duration">${ride.duration_minutes} min</div>
                <div class="distance">${ride.distance_miles.toFixed(1)} mi</div>
            </div>
        `;
    });
    html += '</div>';
    
    // AI Recommendation
    html += `
        <div class="recommendation">
            <h4>💡 Recommendation</h4>
            <p>${results.comparison}</p>
        </div>
    `;
    
    html += '</div>';
    return html;
}

// Format restaurant results
function formatRestaurantResults(results) {
    if (!results.restaurants || results.restaurants.length === 0) {
        return '<p>No restaurants found</p>';
    }

    let html = '<div class="restaurant-results">';
    
    // Results grid
    html += '<div class="results-grid">';
    results.restaurants.slice(0, 10).forEach(restaurant => {
        const stars = '⭐'.repeat(Math.floor(restaurant.rating));
        const isOpen = restaurant.is_open_now ? '✅' : '🔴';
        const distance = restaurant.distance_miles || restaurant.distance || 0;

        html += `
            <div class="restaurant-card">
                <div class="name">${restaurant.name}</div>
                <div class="provider">${restaurant.provider}</div>
                <div class="rating">${stars} ${restaurant.rating.toFixed(1)}</div>
                <div class="reviews">${restaurant.review_count.toLocaleString()} reviews</div>
                <div class="price">${restaurant.price_range || 'N/A'}</div>
                <div class="distance">${distance.toFixed(1)} mi</div>
                <div class="status">${isOpen}</div>
            </div>
        `;
    });
    html += '</div>';
    
    // AI Recommendation
    html += `
        <div class="recommendation">
            <h4>💡 Recommendation</h4>
            <p>${results.comparison}</p>
        </div>
    `;
    
    html += '</div>';
    return html;
}

// ============================================================================
// Example Usage (for testing)
// ============================================================================

// Initialize API client
const api = new HopwiseAPI();

// Example: Search rides
async function searchRides() {
    const origin = document.getElementById('ride-origin')?.value || 'Times Square, NYC';
    const destination = document.getElementById('ride-destination')?.value || 'Central Park, NYC';
    
    showLoading('ride-results');
    
    try {
        const response = await api.compareRides(origin, destination);
        const html = formatRideResults(response.data);
        document.getElementById('ride-results').innerHTML = html;
    } catch (error) {
        showError('ride-results', error.message);
    }
}

// Example: Search restaurants
async function searchRestaurants(useAI = false) {
    const location = document.getElementById('restaurant-location')?.value || 'Times Square, NYC';
    const query = document.getElementById('restaurant-query')?.value || 'Italian food';
    const filter = document.getElementById('restaurant-filter')?.value || 'Food';
    const priority = document.getElementById('restaurant-priority')?.value || 'balanced';

    if (useAI) {
        showLoading('restaurant-results');
        document.getElementById('restaurant-results').innerHTML += '<p style="text-align:center; color:#FF8E53; font-weight:700;">🤖 Getting AI recommendation...</p>';
    } else {
        showLoading('restaurant-results');
    }

    try {
        const response = await api.searchRestaurants(location, query, filter, priority, useAI);
        let html = formatRestaurantResults(response.data);
        // Add AI enhancement button if not using AI
        if (!useAI) {
            html += `
                <div style="text-align:center; margin-top:20px;">
                    <button class="btn" onclick="searchRestaurants(true)" style="max-width:300px; margin:0 auto;">
                        ✨ Get AI Recommendation
                    </button>
                </div>
            `;
        }
        document.getElementById('restaurant-results').innerHTML = html;
    } catch (error) {
        showError('restaurant-results', error.message);
    }
}

// Export for use in HTML
if (typeof window !== 'undefined') {
    window.HopwiseAPI = HopwiseAPI;
    window.searchRides = searchRides;
    window.searchRestaurants = searchRestaurants;
}