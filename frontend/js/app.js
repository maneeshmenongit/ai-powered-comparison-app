/* ================================================================
   HOPWISE APP - APPLICATION LOGIC
   Version: 1.0.0
   ================================================================ */

// ================================
// 1. APP STATE MANAGEMENT
// ================================

const AppState = {
    currentPage: 'home',
    user: { name: 'Alex' },
    deviceId: null, // UUID for device-based favorites
    savedItems: [],
    savedRestaurantIds: new Set(), // Quick lookup for saved status
    trips: [], // User's trips (registered users only)
    currentTrip: null, // Currently viewed trip
    searchResults: [],
    placesCache: {}, // Cache all fetched places by ID for detail page
    filters: {
        category: 'Food',
        priceRange: null,
        rating: null,
        distance: null
    },
    loading: false,
    error: null,
    // Google Places Autocomplete
    autocomplete: {
        service: null,
        sessionToken: null,
        activeInput: null,
        debounceTimer: null
    }
};

// ================================
// 1B. DEVICE ID MANAGEMENT
// ================================

/**
 * Get or generate device ID for favorites feature
 * Stores in localStorage for persistence
 */
function getDeviceId() {
    if (AppState.deviceId) {
        return AppState.deviceId;
    }

    // Check localStorage
    let deviceId = localStorage.getItem('hopwise_device_id');

    if (!deviceId) {
        // Generate new UUID
        deviceId = generateUUID();
        localStorage.setItem('hopwise_device_id', deviceId);
        console.log('Generated new device ID:', deviceId);
    }

    AppState.deviceId = deviceId;
    return deviceId;
}

/**
 * Generate a UUID v4
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// ================================
// 1C. FAVORITES MANAGEMENT
// ================================

/**
 * Load saved restaurants from API
 */
async function loadSavedRestaurants() {
    try {
        // Check if user is authenticated
        if (!window.authManager || !window.authManager.isAuthenticated()) {
            console.log('User not authenticated, skipping saved restaurants load');
            return [];
        }

        const api = new HopwiseAPI();
        const response = await api.getSavedRestaurants();

        if (response.success && response.data) {
            AppState.savedItems = response.data;
            // Update the Set for quick lookup
            AppState.savedRestaurantIds.clear();
            response.data.forEach(item => {
                AppState.savedRestaurantIds.add(item.restaurant_id);
            });

            console.log(`Loaded ${response.data.length} saved restaurants`);
            return response.data;
        }
        return [];
    } catch (error) {
        console.error('Error loading saved restaurants:', error);
        return [];
    }
}

/**
 * Save a restaurant to favorites
 * @param {object} restaurant - Restaurant data object
 */
async function saveRestaurant(restaurant) {
    try {
        // Check if user is authenticated
        if (!window.authManager || !window.authManager.isAuthenticated()) {
            showToast('Please login to save restaurants', 'info');
            navigateTo('login');
            return false;
        }

        const api = new HopwiseAPI();

        // Prepare restaurant data
        const restaurantId = restaurant.place_id || restaurant.id;
        const restaurantData = {
            place_id: restaurantId,
            name: restaurant.name,
            rating: restaurant.rating,
            price_level: restaurant.price_level,
            vicinity: restaurant.vicinity || restaurant.location,
            image: restaurant.image || restaurant.image_url,
            category: restaurant.category,
            tags: restaurant.tags,
            phone: restaurant.phone,
            website: restaurant.website,
            hours: restaurant.hours,
            distance: restaurant.distance
        };

        const response = await api.saveRestaurant(restaurantId, restaurantData);

        if (response.success) {
            // Add to state
            AppState.savedItems.push(response.data);
            AppState.savedRestaurantIds.add(restaurantId);

            showToast('Saved to favorites!', 'success');
            // Don't call updateSaveButtons here - already done optimistically in toggleSave
            return true;
        }
    } catch (error) {
        if (error.message.includes('already saved')) {
            showToast('Already in favorites', 'info');
        } else {
            console.error('Error saving restaurant:', error);
            showToast('Failed to save', 'error');
        }
        return false;
    }
}

/**
 * Remove a restaurant from favorites
 * @param {number} savedId - The saved restaurant ID from the database
 * @param {string} restaurantId - The restaurant place_id for UI updates
 */
async function removeSavedRestaurant(savedId, restaurantId) {
    try {
        // Check if user is authenticated
        if (!window.authManager || !window.authManager.isAuthenticated()) {
            showToast('Please login to manage saved restaurants', 'info');
            navigateTo('login');
            return false;
        }

        const api = new HopwiseAPI();

        const response = await api.removeSavedRestaurant(savedId);

        if (response.success) {
            // Remove from state
            AppState.savedItems = AppState.savedItems.filter(item => item.id !== savedId);
            AppState.savedRestaurantIds.delete(restaurantId);

            showToast('Removed from favorites', 'success');
            // Don't call updateSaveButtons here - already done optimistically in toggleSave

            // Refresh saved page if we're on it
            if (AppState.currentPage === 'saved') {
                await initSavedPage();
            }

            return true;
        }
    } catch (error) {
        console.error('Error removing saved restaurant:', error);
        showToast('Failed to remove', 'error');
        return false;
    }
}

/**
 * Update all save buttons for a restaurant
 * @param {string} restaurantId - Place ID of the restaurant
 * @param {boolean} isSaved - Whether the restaurant is saved
 */
function updateSaveButtons(restaurantId, isSaved) {
    document.querySelectorAll(`[data-save-id="${restaurantId}"]`).forEach(btn => {
        btn.classList.toggle('saved', isSaved);
        btn.innerHTML = isSaved ? '❤️' : '🤍';
    });
}

/**
 * Check if a restaurant is saved
 * @param {string} restaurantId - Place ID of the restaurant
 * @returns {boolean}
 */
function isRestaurantSaved(restaurantId) {
    return AppState.savedRestaurantIds.has(restaurantId);
}

// ================================
// 2. DOM ELEMENTS CACHE
// ================================

const DOM = {
    // App Shell
    app: null,
    pages: null,
    bottomNav: null,
    
    // Home Page
    homeGreeting: null,
    homeSearchInput: null,
    trendingContainer: null,
    activitiesContainer: null,
    
    // Search Page
    searchInput: null,
    searchResults: null,
    filterChips: null,
    resultsCount: null,
    
    // Detail Page
    detailContainer: null,
    
    // Rides Page
    ridesContainer: null,
    rideCards: null,
    
    // Saved Page
    savedContainer: null,
    savedTabs: null,

    // Trips Page
    tripsContainer: null,
    tripsGuestMessage: null,
    tripDetailTitle: null,
    tripDetailInfo: null,
    tripTimelineContainer: null,

    // Loading & States
    loadingOverlay: null,
    toastContainer: null
};

// Initialize DOM cache
function initDOM() {
    DOM.app = document.getElementById('app');
    DOM.pages = document.querySelectorAll('.page');
    DOM.bottomNav = document.getElementById('bottom-nav');
    
    // Home
    DOM.homeGreeting = document.getElementById('home-greeting');
    DOM.homeSearchInput = document.getElementById('home-search');
    DOM.trendingContainer = document.getElementById('trending-container');
    DOM.activitiesContainer = document.getElementById('activities-container');
    
    // Search
    DOM.searchInput = document.getElementById('search-input');
    DOM.searchResults = document.getElementById('search-results');
    DOM.filterChips = document.getElementById('filter-chips');
    DOM.resultsCount = document.getElementById('results-count');
    
    // Detail
    DOM.detailContainer = document.getElementById('detail-container');
    
    // Rides
    DOM.ridesContainer = document.getElementById('rides-container');
    
    // Saved
    DOM.savedContainer = document.getElementById('saved-container');
    DOM.savedTabs = document.getElementById('saved-tabs');

    // Trips
    DOM.tripsContainer = document.getElementById('trips-container');
    DOM.tripsGuestMessage = document.getElementById('trips-guest-message');
    DOM.tripDetailTitle = document.getElementById('trip-detail-title');
    DOM.tripDetailInfo = document.getElementById('trip-detail-info');
    DOM.tripTimelineContainer = document.getElementById('trip-timeline-container');

    // States
    DOM.loadingOverlay = document.getElementById('loading-overlay');
    DOM.toastContainer = document.getElementById('toast-container');
}

// ================================
// 3. NAVIGATION
// ================================

function navigateTo(pageName, data = null) {
    // Track page view
    if (typeof gtag !== 'undefined') {
        gtag('event', 'page_view', {
            page_title: pageName,
            page_location: window.location.href,
            page_path: `/${pageName}`
        });
    }

    // Hide all pages
    DOM.pages.forEach(page => page.classList.remove('active'));

    // Show target page
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
        AppState.currentPage = pageName;

        // Update bottom nav
        updateBottomNav(pageName);

        // Page-specific init
        onPageEnter(pageName, data);

        // Scroll to top
        window.scrollTo(0, 0);
    }
}

function updateBottomNav(activePage) {
    if (!DOM.bottomNav) return;

    const navItems = DOM.bottomNav.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const page = item.dataset.page;
        item.classList.toggle('active', page === activePage);
    });
}

/**
 * Update bottom navigation visibility based on auth status
 * Guests see: Home, Search, Rides (3 tabs)
 * Authenticated users see: Home, Search, Rides, Trips, Saved, Profile (6 tabs)
 */
function updateBottomNavForAuthStatus() {
    if (!DOM.bottomNav) return;

    const isAuth = window.authManager && window.authManager.isAuthenticated();
    const isGuest = window.authManager && window.authManager.isGuest();
    const navItems = DOM.bottomNav.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        const page = item.dataset.page;

        // Show only Home, Search, and Rides for guests and non-authenticated users
        if (!isAuth || isGuest) {
            if (page === 'trips' || page === 'saved' || page === 'profile') {
                item.style.display = 'none';
            } else {
                item.style.display = 'flex';
            }
        } else {
            // Show all tabs for authenticated non-guest users
            item.style.display = 'flex';
        }
    });
}

/**
 * Update home page header actions based on auth status
 * Guests see: Sign Up button
 * Authenticated users see: Notifications and Profile icons
 */
function updateHomeHeaderActions() {
    const headerActions = document.getElementById('home-header-actions');
    if (!headerActions) return;

    const isAuth = window.authManager && window.authManager.isAuthenticated();

    if (!isAuth) {
        // Guest user - show Sign Up button
        headerActions.innerHTML = `
            <button class="btn btn-primary" onclick="navigateTo('register')" style="padding: 10px 20px; font-weight: 700;">
                Sign Up
            </button>
        `;
    } else {
        // Authenticated user - show notifications and profile
        headerActions.innerHTML = `
            <button class="header-action">🔔</button>
            <button class="header-action" onclick="navigateTo('profile')">👤</button>
        `;
    }
}

function onPageEnter(pageName, data) {
    switch (pageName) {
        case 'home':
            initHomePage();
            break;
        case 'search':
            initSearchPage(data);
            break;
        case 'detail':
            initDetailPage(data);
            break;
        case 'rides':
            initRidesPage(data);
            break;
        case 'saved':
            initSavedPage();
            break;
        case 'trips':
            initTripsPage();
            break;
        case 'trip-detail':
            initTripDetailPage(data);
            break;
        case 'profile':
            initProfilePage();
            break;
        case 'login':
            // No initialization needed for login page
            break;
        case 'register':
            // No initialization needed for register page
            break;
    }
}

function goBack() {
    // Simple back navigation
    navigateTo('home');
}

// ================================
// 4. DATA FETCHING (API Integration Points)
// ================================

/**
 * Fetch restaurants/places from API
 * @param {Object} params - Search parameters
 * @returns {Promise<Array>} - Array of place objects
 */
async function fetchPlaces(params = {}) {
    setLoading(true);

    try {
        // Use real API
        const api = new HopwiseAPI();
        const location = params.location || 'Times Square, NYC';
        const query = params.query || '';
        const filterCategory = params.category || 'Food';
        const priority = params.priority || 'balanced';

        const response = await api.searchRestaurants(location, query, filterCategory, priority, false);

        // Transform API response to match expected format
        // Note: Response has nested structure: response.data.data.results
        const results = response.data?.data?.results || response.data?.results || [];
        const guestLimited = response.data?.data?.guest_limited || false;
        const message = response.data?.data?.message || '';

        const places = results.map(restaurant => ({
            id: restaurant.id,
            name: restaurant.name,
            category: restaurant.cuisine,
            categoryIcon: '🍽️',
            rating: restaurant.rating,
            reviews: restaurant.review_count,
            price: restaurant.price_range,
            distance: `${restaurant.distance_miles.toFixed(1)} mi`,
            meta: `${restaurant.cuisine} • ${restaurant.price_range}`,
            image: restaurant.image_url,
            gradient: restaurant.gradient,
            badge: restaurant.badge,
            tags: restaurant.tags,
            address: restaurant.address,
            phone: restaurant.phone,
            website: restaurant.website,
            hours: restaurant.hours,
            isOpen: restaurant.is_open_now
        }));

        AppState.searchResults = places;
        setLoading(false);

        // Return object with guest limitation info
        return {
            results: places,
            guestLimited: guestLimited,
            message: message
        };

    } catch (error) {
        setLoading(false);
        setError('Failed to load places. Please try again.');
        console.error('fetchPlaces error:', error);
        return [];
    }
}

/**
 * Fetch ride comparisons from API
 * @param {Object} params - Origin, destination, etc.
 * @returns {Promise<Array>} - Array of ride options
 */
async function fetchRides(params = {}) {
    setLoading(true);

    try {
        // Use real API
        const api = new HopwiseAPI();
        const origin = params.origin || 'Times Square, NYC';
        const destination = params.destination || 'Central Park, NYC';

        const response = await api.compareRides(origin, destination);

        // Transform API response to match expected format
        // Note: Response has nested structure: response.data.data.rides
        const ridesData = response.data?.data?.rides || response.data?.rides || [];
        const rides = ridesData.map(ride => ({
            id: `${ride.provider}-${ride.vehicle_type}`,
            provider: ride.provider,
            name: ride.vehicle_type, // Use vehicle_type directly (e.g., "Uber X", "Lyft Lux")
            type: ride.type,
            vehicle: ride.vehicle_type,
            price: ride.price_estimate,
            priceRange: ride.priceRange,
            duration: ride.duration_minutes,
            pickup: ride.pickup,
            distance: ride.distance_miles,
            seats: ride.seats,
            rating: ride.rating,
            surge: ride.surge,
            deepLink: ride.deepLink
        }));

        setLoading(false);
        return rides;

    } catch (error) {
        setLoading(false);
        setError('Failed to load ride options. Please try again.');
        console.error('fetchRides error:', error);
        return [];
    }
}

/**
 * Fetch place details
 * @param {string} placeId - Place ID
 * @returns {Promise<Object>} - Place details object
 */
async function fetchPlaceDetail(placeId) {
    setLoading(true);

    try {
        // First check the places cache
        if (AppState.placesCache[placeId]) {
            setLoading(false);
            return AppState.placesCache[placeId];
        }

        // Then check search results
        const place = AppState.searchResults.find(p => p.id === placeId);

        if (place) {
            // Cache it for next time
            AppState.placesCache[placeId] = place;
            setLoading(false);
            return place;
        }

        // If not found anywhere, return null
        setLoading(false);
        return null;

    } catch (error) {
        setLoading(false);
        setError('Failed to load details. Please try again.');
        console.error('fetchPlaceDetail error:', error);
        return null;
    }
}

// ================================
// 5. RENDERING FUNCTIONS
// ================================

/**
 * Render place card (search results)
 */
function renderPlaceCard(place) {
    const placeId = place.place_id || place.id;
    const isSaved = isRestaurantSaved(placeId);
    const imageUrl = place.image || place.image_url;
    const tags = Array.isArray(place.tags) ? place.tags : [];

    return `
        <div class="place-card" data-id="${placeId}" onclick="openPlaceDetail('${placeId}')">
            <div class="place-card-image">
                ${imageUrl ? `<img src="${imageUrl}" alt="${place.name}">` : ''}
                ${place.badge ? `<span class="place-card-badge">${place.badge}</span>` : ''}
            </div>
            <div class="place-card-content">
                <h3 class="place-card-name">${place.name}</h3>
                <p class="place-card-meta">${place.category} • ${place.price} • ${place.distance}</p>
                <div class="place-card-tags">
                    ${tags.map(tag => `<span class="place-card-tag">${tag}</span>`).join('')}
                </div>
                <div class="place-card-footer">
                    <span class="place-card-rating">⭐ ${place.rating}</span>
                    <span class="place-card-distance">${place.distance}</span>
                    <button class="place-card-action" onclick="event.stopPropagation(); showAddToTripDialog('restaurant', ${JSON.stringify(place).replace(/"/g, '&quot;')})" title="Add to trip" style="background: none; border: none; cursor: pointer; font-size: 18px; padding: 4px 8px;">
                        🗺️
                    </button>
                    <button class="place-card-save ${isSaved ? 'saved' : ''}" data-save-id="${placeId}" onclick="event.stopPropagation(); toggleSave('${placeId}')">
                        ${isSaved ? '❤️' : '🤍'}
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render grid card (saved items, trending)
 */
function renderGridCard(item) {
    const itemId = item.place_id || item.id;
    const isSaved = isRestaurantSaved(itemId);
    const imageUrl = item.image || item.image_url;
    const backgroundStyle = imageUrl
        ? `background-image: url('${imageUrl}'); background-size: cover; background-position: center;`
        : `background: ${item.gradient || 'var(--color-gray-100)'}`;

    return `
        <div class="grid-card" data-id="${itemId}" onclick="openPlaceDetail('${itemId}')">
            <div class="grid-card-image" style="${backgroundStyle}">
                <button class="grid-card-save ${isSaved ? 'saved' : ''}" data-save-id="${itemId}" onclick="event.stopPropagation(); toggleSave('${itemId}')">
                    ${isSaved ? '❤️' : '🤍'}
                </button>
                ${item.category ? `<span class="grid-card-category">${item.categoryIcon} ${item.category}</span>` : ''}
            </div>
            <div class="grid-card-content">
                <h3 class="grid-card-name">${item.name}</h3>
                <p class="grid-card-meta">${item.meta}</p>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span class="grid-card-rating">⭐ ${item.rating}</span>
                    <button onclick="event.stopPropagation(); showAddToTripDialog('restaurant', ${JSON.stringify(item).replace(/"/g, '&quot;')})" title="Add to trip" style="background: none; border: none; cursor: pointer; font-size: 16px; padding: 4px; color: #667eea;">
                        🗺️
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render ride card
 */
function renderRideCard(ride, isSelected = false, badgeType = null) {
    return `
        <div class="ride-card ${isSelected ? 'selected' : ''}" 
             data-provider="${ride.provider}" 
             onclick="selectRide('${ride.provider}')">
            ${badgeType ? `<span class="ride-card-badge ${badgeType}">${badgeType === 'best' ? '✓ Best Price' : '⚡ Fastest'}</span>` : ''}
            <div class="ride-card-header">
                <div class="ride-card-logo ${ride.provider.toLowerCase()}">${ride.provider[0]}</div>
                <div class="ride-card-info">
                    <h3 class="ride-card-name">${ride.name}</h3>
                    <p class="ride-card-type">${ride.seats} seats • ${ride.type}</p>
                </div>
                <div class="ride-card-price">
                    <span class="ride-card-amount">$${ride.price}</span>
                    ${ride.surge ? `<span class="ride-card-surge">${ride.surge}x surge</span>` : ''}
                </div>
            </div>
            <div class="ride-card-details">
                <span class="ride-card-detail"><span class="icon">⏱️</span> ${ride.pickup} min pickup</span>
                <span class="ride-card-detail"><span class="icon">🚙</span> ${ride.duration} min trip</span>
                <span class="ride-card-detail"><span class="icon">⭐</span> ${ride.rating}</span>
                <button class="ride-card-action" onclick="event.stopPropagation(); showAddToTripDialog('ride', ${JSON.stringify(ride).replace(/"/g, '&quot;')})" title="Add to trip" style="background: none; border: none; cursor: pointer; font-size: 14px; padding: 4px 8px; margin-left: auto; color: #667eea;">
                    + Add to Trip
                </button>
            </div>
        </div>
    `;
}

/**
 * Render skeleton loader for place card
 */
function renderPlaceCardSkeleton() {
    return `
        <div class="skeleton-card">
            <div class="flex gap-3">
                <div class="skeleton skeleton-image" style="width: 100px; height: 100px;"></div>
                <div style="flex: 1;">
                    <div class="skeleton skeleton-text lg"></div>
                    <div class="skeleton skeleton-text sm"></div>
                    <div class="skeleton skeleton-text" style="width: 80%;"></div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render empty state
 */
function renderEmptyState(type = 'search') {
    const states = {
        search: {
            icon: '🔍',
            title: 'No results found',
            text: 'Try adjusting your filters or search terms',
            action: { text: 'Clear filters', handler: 'clearFilters()' }
        },
        saved: {
            icon: '❤️',
            title: 'No saved items yet',
            text: 'Start exploring and save your favorites!',
            action: { text: 'Explore now', handler: "navigateTo('home')" }
        },
        trips: {
            icon: '<img src="./assets/images/trips_empty_icon.png" alt="Trips" style="width: 150px; height: 150px; display: block; margin: 0 auto;">',
            title: 'No trips yet',
            text: 'Plan your next adventure! Create a trip to organize restaurants, rides, and activities.',
            action: { text: 'Create Trip', handler: 'showCreateTripDialog()' }
        },
        error: {
            icon: '⚠️',
            title: 'Something went wrong',
            text: 'Please check your connection and try again',
            action: { text: 'Try again', handler: 'retry()' }
        }
    };
    
    const state = states[type] || states.search;
    
    return `
        <div class="empty-state">
            <div class="empty-state-icon">${state.icon}</div>
            <h3 class="empty-state-title">${state.title}</h3>
            <p class="empty-state-text">${state.text}</p>
            ${state.action ? `<button class="btn btn-primary" onclick="${state.action.handler}">${state.action.text}</button>` : ''}
        </div>
    `;
}

/**
 * Render error state
 */
function renderErrorState(message = 'Something went wrong') {
    return `
        <div class="error-state">
            <div class="error-state-icon">😕</div>
            <h3 class="error-state-title">Oops!</h3>
            <p class="error-state-text">${message}</p>
            <button class="btn btn-primary" onclick="retry()">Try again</button>
        </div>
    `;
}

// ================================
// 6. PAGE INITIALIZERS
// ================================

function initHomePage() {
    // Set greeting based on time
    if (DOM.homeGreeting) {
        const hour = new Date().getHours();
        let greeting = 'Good evening';
        if (hour < 12) greeting = 'Good morning';
        else if (hour < 18) greeting = 'Good afternoon';

        // Get username from authenticated user or show generic greeting for guests
        const isAuth = window.authManager && window.authManager.isAuthenticated();
        const userName = isAuth ? (window.authManager.getUser()?.username || '') : '';

        if (isAuth && userName) {
            DOM.homeGreeting.textContent = `${greeting}, ${userName}! 👋`;
        } else {
            DOM.homeGreeting.textContent = `${greeting}! 👋`;
        }
    }

    // Update header actions based on auth status
    updateHomeHeaderActions();

    // Update bottom navigation based on auth status
    updateBottomNavForAuthStatus();

    // Load trending items
    loadTrendingItems();

    // Load activities
    loadActivities();
}

async function initSearchPage(query = '') {
    if (DOM.searchInput && query) {
        DOM.searchInput.value = query;
    }

    // Show loading
    if (DOM.searchResults) {
        DOM.searchResults.innerHTML = Array(4).fill(renderPlaceCardSkeleton()).join('');
    }

    // Fetch results
    const response = await fetchPlaces({ query, ...AppState.filters });

    // Check if results are limited for guests
    const guestLimited = response.guestLimited || false;
    const guestMessage = response.message || '';
    const results = response.results || response;

    // Render results
    renderSearchResults(results, guestLimited, guestMessage);
}

async function initDetailPage(placeId) {
    if (!placeId || !DOM.detailContainer) return;
    
    // Show loading
    DOM.detailContainer.innerHTML = '<div class="loading-overlay"><div class="spinner spinner-lg"></div></div>';
    
    // Fetch details
    const detail = await fetchPlaceDetail(placeId);
    
    if (detail) {
        renderPlaceDetail(detail);
    } else {
        DOM.detailContainer.innerHTML = renderErrorState('Could not load details');
    }
}

async function initRidesPage(params = {}) {
    if (!DOM.ridesContainer) return;

    // Get UI elements first
    const pickupElement = document.getElementById('ride-pickup');
    const destinationElement = document.getElementById('ride-destination');

    // Get destination (from params or default)
    const destination = params.destination || destinationElement?.textContent || 'JFK Airport Terminal 4';

    // Get origin - try user's current location first
    let origin = params.origin;
    let displayOrigin = origin;

    if (!origin) {
        // Try to get user's current location
        try {
            const position = await new Promise((resolve, reject) => {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                } else {
                    reject(new Error('Geolocation not supported'));
                }
            });

            // Use coordinates as origin (format: "lat,lng")
            // This will be more accurate for the ride API
            origin = `${position.coords.latitude},${position.coords.longitude}`;
            displayOrigin = 'Current Location';

        } catch (error) {
            // Geolocation failed or denied
            // Use a default NYC location (Empire State Building)
            origin = '40.748817,-73.985428'; // Empire State Building coordinates
            displayOrigin = 'Empire State Building, NYC';
        }
    }

    // Update UI to show origin and destination
    if (pickupElement) pickupElement.textContent = displayOrigin;
    if (destinationElement) destinationElement.textContent = destination;

    // Show loading skeletons
    DOM.ridesContainer.innerHTML = Array(3).fill(renderPlaceCardSkeleton()).join('');

    // Fetch rides with origin and destination
    const rides = await fetchRides({ origin, destination, ...params });

    // Render rides
    renderRideResults(rides);
}

async function initSavedPage() {
    if (!DOM.savedContainer) return;

    // Show loading state
    DOM.savedContainer.innerHTML = '<div class="loading-overlay"><div class="spinner spinner-lg"></div></div>';

    // Load saved restaurants from API
    await loadSavedRestaurants();

    // Update category counts
    updateSavedCategoryCounts();

    if (AppState.savedItems.length === 0) {
        DOM.savedContainer.innerHTML = renderEmptyState('saved');
        return;
    }

    // Load and render saved items
    renderSavedItems();
}

/**
 * Update the category counts in the saved page tabs
 */
function updateSavedCategoryCounts() {
    const savedTabs = document.getElementById('saved-tabs');
    if (!savedTabs) return;

    // Count items by category
    const counts = {
        all: AppState.savedItems.length,
        food: 0,
        drinks: 0,
        activities: 0,
        routes: 0
    };

    // Count each category
    AppState.savedItems.forEach(savedItem => {
        const category = savedItem.restaurant_data?.category?.toLowerCase() || '';

        if (category.includes('food') || category.includes('restaurant') || category.includes('cuisine')) {
            counts.food++;
        } else if (category.includes('drink') || category.includes('bar') || category.includes('cafe')) {
            counts.drinks++;
        } else if (category.includes('activity') || category.includes('entertainment')) {
            counts.activities++;
        } else if (category.includes('ride') || category.includes('transport')) {
            counts.routes++;
        } else {
            // Default to food category if unclear
            counts.food++;
        }
    });

    // Update the HTML
    savedTabs.innerHTML = `
        <button class="filter-chip active">All <span class="count">${counts.all}</span></button>
        <button class="filter-chip">🍽️ Food <span class="count">${counts.food}</span></button>
        <button class="filter-chip">🍸 Drinks <span class="count">${counts.drinks}</span></button>
        <button class="filter-chip">🎡 Activities <span class="count">${counts.activities}</span></button>
        <button class="filter-chip">🚗 Routes <span class="count">${counts.routes}</span></button>
    `;
}

// ============================================================================
// TRIP PLANNING FUNCTIONS (Registered Users Only)
// ============================================================================

/**
 * Initialize trips page - show guest message or load user's trips
 */
async function initTripsPage() {
    const isAuth = window.authManager && window.authManager.isAuthenticated();
    const isGuest = window.authManager && window.authManager.isGuest();

    // Show guest message for non-authenticated users or guests
    if (!isAuth || isGuest) {
        if (DOM.tripsGuestMessage) {
            DOM.tripsGuestMessage.style.display = 'block';
        }
        if (DOM.tripsContainer) {
            DOM.tripsContainer.style.display = 'none';
        }
        return;
    }

    // Hide guest message for authenticated users
    if (DOM.tripsGuestMessage) {
        DOM.tripsGuestMessage.style.display = 'none';
    }
    if (DOM.tripsContainer) {
        DOM.tripsContainer.style.display = 'block';
    }

    // Load user's trips
    await loadTrips();
}

/**
 * Load trips from API and render
 */
async function loadTrips() {
    if (!DOM.tripsContainer) return;

    showLoading();

    try {
        // Debug authentication state
        console.log('[loadTrips] Auth check:', {
            hasAuthManager: !!window.authManager,
            isAuthenticated: window.authManager?.isAuthenticated(),
            isGuest: window.authManager?.isGuest(),
            hasToken: !!window.authManager?.token
        });

        const api = new HopwiseAPI();
        const response = await api.getTrips();

        if (response.success && response.data) {
            AppState.trips = response.data;
            renderTripsList();
        } else {
            throw new Error(response.error || 'Failed to load trips');
        }
    } catch (error) {
        console.error('Error loading trips:', error);
        showToast('Failed to load trips: ' + error.message, 'error');
        DOM.tripsContainer.innerHTML = renderEmptyState('trips');
    } finally {
        hideLoading();
    }
}

/**
 * Render trips list
 */
function renderTripsList() {
    if (!DOM.tripsContainer) return;

    const createTripBtn = document.getElementById('create-trip-btn');

    if (AppState.trips.length === 0) {
        DOM.tripsContainer.innerHTML = renderEmptyState('trips');
        // Hide + button when no trips - user should use "Create Trip" button in empty state
        if (createTripBtn) createTripBtn.style.display = 'none';
        return;
    }

    // Show + button when trips exist
    if (createTripBtn) createTripBtn.style.display = 'flex';

    DOM.tripsContainer.innerHTML = AppState.trips
        .map(trip => renderTripCard(trip))
        .join('');
}

/**
 * Render a single trip card
 */
function renderTripCard(trip) {
    const itemCount = trip.items?.length || 0;
    const startDate = trip.start_date ? new Date(trip.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    const endDate = trip.end_date ? new Date(trip.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    const dateRange = startDate && endDate ? `${startDate} - ${endDate}` : 'No dates set';

    return `
        <div class="trip-card" onclick="navigateTo('trip-detail', { tripId: '${trip.id}' })">
            <button class="trip-card-delete" onclick="event.stopPropagation(); deleteTrip('${trip.id}')">×</button>
            <h3 class="trip-card-name">${trip.name}</h3>
            <div class="trip-card-dates">📅 ${dateRange}</div>
            <div class="trip-card-count">📍 ${itemCount} ${itemCount === 1 ? 'item' : 'items'}</div>
        </div>
    `;
}

/**
 * Show create trip dialog
 */
function showCreateTripDialog() {
    console.log('[showCreateTripDialog] Called');

    const isAuth = window.authManager && window.authManager.isAuthenticated();
    const isGuest = window.authManager && window.authManager.isGuest();

    console.log('[showCreateTripDialog] Auth check:', { isAuth, isGuest });

    if (!isAuth || isGuest) {
        console.log('[showCreateTripDialog] User not authenticated, redirecting to register');
        showToast('Please sign up to create trips', 'info');
        navigateTo('register');
        return;
    }

    console.log('[showCreateTripDialog] Creating dialog');

    const dialog = document.createElement('div');
    dialog.className = 'modal-overlay';
    dialog.style.cssText = 'position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; padding: 20px; z-index: 1000; backdrop-filter: blur(4px);';
    dialog.innerHTML = `
        <div class="modal" style="background: white; border-radius: 24px; padding: 24px; max-width: 400px; width: 90%;">
            <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 20px;">Create New Trip</h2>
            <form id="create-trip-form">
                <div style="margin-bottom: 16px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px;">Trip Name</label>
                    <input type="text" name="name" placeholder="Weekend in SF" required style="width: 100%; padding: 12px; border: 1px solid #E0E0E0; border-radius: 12px; font-size: 16px;">
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px;">Start Date</label>
                    <input type="date" name="start_date" style="width: 100%; padding: 12px; border: 1px solid #E0E0E0; border-radius: 12px; font-size: 16px;">
                </div>
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px;">End Date</label>
                    <input type="date" name="end_date" style="width: 100%; padding: 12px; border: 1px solid #E0E0E0; border-radius: 12px; font-size: 16px;">
                </div>
                <div style="display: flex; gap: 12px;">
                    <button type="button" onclick="this.closest('.modal-overlay').remove()" style="flex: 1; padding: 14px; border: 1px solid #E0E0E0; border-radius: 12px; background: white; font-weight: 700; cursor: pointer;">Cancel</button>
                    <button type="submit" style="flex: 1; padding: 14px; border: none; border-radius: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 700; cursor: pointer;">Create</button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(dialog);

    // Handle form submission
    document.getElementById('create-trip-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const tripData = {
            name: formData.get('name'),
            start_date: formData.get('start_date') || null,
            end_date: formData.get('end_date') || null
        };

        await createTrip(tripData);
        dialog.remove();
    });
}

/**
 * Create a new trip
 */
async function createTrip(tripData) {
    showLoading();

    try {
        const api = new HopwiseAPI();
        const response = await api.createTrip(tripData);

        if (response.success && response.data) {
            showToast('Trip created!', 'success');
            AppState.trips.push(response.data);
            renderTripsList();
        } else {
            throw new Error(response.error || 'Failed to create trip');
        }
    } catch (error) {
        console.error('Error creating trip:', error);
        showToast('Failed to create trip: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Delete a trip
 */
async function deleteTrip(tripId) {
    if (!confirm('Are you sure you want to delete this trip?')) {
        return;
    }

    showLoading();

    try {
        const api = new HopwiseAPI();
        const response = await api.deleteTrip(tripId);

        if (response.success) {
            showToast('Trip deleted', 'success');
            AppState.trips = AppState.trips.filter(t => t.id !== tripId);
            renderTripsList();
        } else {
            throw new Error(response.error || 'Failed to delete trip');
        }
    } catch (error) {
        console.error('Error deleting trip:', error);
        showToast('Failed to delete trip: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Initialize trip detail page
 */
async function initTripDetailPage(data) {
    if (!data || !data.tripId) {
        showToast('Trip not found', 'error');
        navigateTo('trips');
        return;
    }

    showLoading();

    try {
        const api = new HopwiseAPI();
        const response = await api.getTrip(data.tripId);

        if (response.success && response.data) {
            AppState.currentTrip = response.data;
            renderTripDetail(response.data);
        } else {
            throw new Error(response.error || 'Failed to load trip');
        }
    } catch (error) {
        console.error('Error loading trip:', error);
        showToast('Failed to load trip: ' + error.message, 'error');
        navigateTo('trips');
    } finally {
        hideLoading();
    }
}

/**
 * Render trip detail page
 */
function renderTripDetail(trip) {
    // Update title
    if (DOM.tripDetailTitle) {
        DOM.tripDetailTitle.textContent = trip.name;
    }

    // Render trip info
    if (DOM.tripDetailInfo) {
        const startDate = trip.start_date ? new Date(trip.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not set';
        const endDate = trip.end_date ? new Date(trip.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not set';

        DOM.tripDetailInfo.innerHTML = `
            <div class="trip-info-card">
                <h2 class="trip-info-name">${trip.name}</h2>
                <div class="trip-info-row">📅 ${startDate} - ${endDate}</div>
                <div class="trip-info-row">📍 ${trip.items?.length || 0} ${trip.items?.length === 1 ? 'item' : 'items'}</div>
            </div>
        `;
    }

    // Render timeline
    if (DOM.tripTimelineContainer) {
        if (!trip.items || trip.items.length === 0) {
            DOM.tripTimelineContainer.innerHTML = `
                <div class="empty-state" style="padding: 40px 20px;">
                    <div class="empty-state-icon">📍</div>
                    <h3 class="empty-state-title">No items in this trip yet</h3>
                    <p class="empty-state-text">Tap the + button to add restaurants or rides</p>
                </div>
            `;
        } else {
            DOM.tripTimelineContainer.innerHTML = trip.items
                .sort((a, b) => a.item_order - b.item_order)
                .map((item, index) => renderTripItem(item, index))
                .join('');
        }
    }
}

/**
 * Render a single trip item in timeline
 */
function renderTripItem(item, index) {
    const data = item.item_data;
    let icon = '📍';
    let title = 'Item';
    let subtitle = '';

    if (item.item_type === 'restaurant') {
        icon = '🍽️';
        title = data.name || 'Restaurant';
        subtitle = data.cuisine || data.category || '';
    } else if (item.item_type === 'ride') {
        icon = '🚗';
        title = `Ride to ${data.destination || 'destination'}`;
        subtitle = data.service || '';
    }

    return `
        <div class="itinerary-item">
            <div class="itinerary-icon">${icon}</div>
            <div class="itinerary-content">
                <div class="itinerary-name">${title}</div>
                ${subtitle ? `<div class="itinerary-meta">${subtitle}</div>` : ''}
            </div>
            <button class="itinerary-remove" onclick="removeTripItem('${item.trip_id}', '${item.id}')">×</button>
        </div>
    `;
}

/**
 * Show add to trip dialog
 */
function showAddToTripDialog(itemType, itemData) {
    const isAuth = window.authManager && window.authManager.isAuthenticated();
    const isGuest = window.authManager && window.authManager.isGuest();

    if (!isAuth || isGuest) {
        showToast('Please sign up to use trip planning', 'info');
        navigateTo('register');
        return;
    }

    if (!AppState.trips || AppState.trips.length === 0) {
        showToast('Create a trip first!', 'info');
        showCreateTripDialog();
        return;
    }

    const dialog = document.createElement('div');
    dialog.className = 'modal-overlay';
    dialog.innerHTML = `
        <div class="modal">
            <h2 class="modal-title">Add to Trip</h2>
            <div>
                ${AppState.trips.map(trip => `
                    <div class="trip-select-item" onclick="addItemToTrip('${trip.id}', '${itemType}', ${JSON.stringify(itemData).replace(/"/g, '&quot;')})">
                        <div class="trip-select-name">${trip.name}</div>
                        <div class="trip-select-count">${trip.items?.length || 0} items</div>
                    </div>
                `).join('')}
            </div>
            <button class="btn btn-secondary btn-block" onclick="this.closest('.modal-overlay').remove()" style="margin-top: 16px;">Cancel</button>
        </div>
    `;

    document.body.appendChild(dialog);
}

/**
 * Add item to trip
 */
async function addItemToTrip(tripId, itemType, itemData) {
    // Close dialog
    const dialog = document.querySelector('.modal-overlay');
    if (dialog) dialog.remove();

    showLoading();

    try {
        const api = new HopwiseAPI();
        const response = await api.addTripItem(tripId, {
            item_type: itemType,
            item_data: itemData,
            item_order: 999 // Will be sorted later
        });

        if (response.success) {
            showToast('Added to trip!', 'success');
        } else {
            throw new Error(response.error || 'Failed to add item to trip');
        }
    } catch (error) {
        console.error('Error adding item to trip:', error);
        showToast('Failed to add to trip: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Remove item from trip
 */
async function removeTripItem(tripId, itemId) {
    showLoading();

    try {
        const api = new HopwiseAPI();
        const response = await api.removeTripItem(tripId, itemId);

        if (response.success) {
            showToast('Item removed', 'success');
            // Reload trip detail
            if (AppState.currentTrip && AppState.currentTrip.id === tripId) {
                await initTripDetailPage({ tripId });
            }
        } else {
            throw new Error(response.error || 'Failed to remove item');
        }
    } catch (error) {
        console.error('Error removing item:', error);
        showToast('Failed to remove item: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function initProfilePage() {
    // Update saved count stat
    const statSavedEl = document.getElementById('stat-saved');
    if (statSavedEl) {
        statSavedEl.textContent = AppState.savedItems.length;
    }

    // Update profile info if user is authenticated
    if (window.authManager && window.authManager.isAuthenticated()) {
        const user = window.authManager.getUser();

        // Update name
        const profileNameEl = document.getElementById('profile-name');
        if (profileNameEl && user.username) {
            profileNameEl.textContent = user.username;
        }

        // Update email
        const profileEmailEl = document.getElementById('profile-email');
        if (profileEmailEl && user.email) {
            profileEmailEl.textContent = user.email;
        }

        // Update avatar initial
        const profileAvatarEl = document.getElementById('profile-avatar');
        if (profileAvatarEl && user.username) {
            profileAvatarEl.textContent = user.username.charAt(0).toUpperCase();
        }
    } else {
        // Show guest info
        const profileNameEl = document.getElementById('profile-name');
        if (profileNameEl) {
            profileNameEl.textContent = 'Guest User';
        }

        const profileEmailEl = document.getElementById('profile-email');
        if (profileEmailEl) {
            profileEmailEl.textContent = 'Not logged in';
        }

        const profileAvatarEl = document.getElementById('profile-avatar');
        if (profileAvatarEl) {
            profileAvatarEl.textContent = '?';
        }
    }
}

// ================================
// 7. RENDER PAGE CONTENT
// ================================

function renderSearchResults(results, guestLimited = false, guestMessage = '') {
    if (!DOM.searchResults) return;

    // Update count
    if (DOM.resultsCount) {
        DOM.resultsCount.textContent = `${results.length} places found`;
    }

    // Render results or empty state
    if (results.length === 0) {
        DOM.searchResults.innerHTML = renderEmptyState('search');
    } else {
        let html = results.map(place => renderPlaceCard(place)).join('');

        // Add signup banner for guest users with limited results
        if (guestLimited && guestMessage) {
            html += `
                <div style="background: linear-gradient(135deg, #FF8E53, #FE6B8B); border-radius: 20px; padding: 24px; margin: 16px 0; color: white; text-align: center;">
                    <div style="font-size: 32px; margin-bottom: 12px;">✨</div>
                    <div style="font-weight: 800; font-size: 18px; margin-bottom: 8px;">Want to see more?</div>
                    <div style="font-size: 14px; margin-bottom: 16px; opacity: 0.95;">${guestMessage}</div>
                    <button onclick="navigateTo('register')" class="btn" style="background: white; color: #FF8E53; font-weight: 800; padding: 12px 24px; border-radius: 12px; border: none; cursor: pointer; width: 100%; max-width: 200px;">
                        Sign Up Free
                    </button>
                </div>
            `;
        }

        DOM.searchResults.innerHTML = html;
    }
}

function renderPlaceDetail(detail) {
    if (!DOM.detailContainer) return;

    // Safely handle badges
    const badges = detail.badges || (detail.badge ? [detail.badge] : []);
    const badgesHtml = badges.length > 0
        ? `<div style="position: absolute; bottom: 16px; left: 16px; display: flex; gap: 8px;">
            ${badges.map(b => `<span class="badge">${b}</span>`).join('')}
           </div>`
        : '';

    // Handle hero image
    const imageUrl = detail.image || detail.image_url;
    const heroStyle = imageUrl
        ? `height: 280px; background-image: url('${imageUrl}'); background-size: cover; background-position: center; position: relative;`
        : `height: 280px; background: ${detail.gradient || 'linear-gradient(135deg, #FFE5B4, #FFB347)'}; position: relative;`;

    DOM.detailContainer.innerHTML = `
        <!-- Hero Image -->
        <div class="detail-hero" style="${heroStyle}">
            <div class="header" style="position: absolute; top: 0; left: 0; right: 0; background: linear-gradient(180deg, rgba(0,0,0,0.5) 0%, transparent 100%);">
                <button class="header-back" onclick="goBack()">←</button>
                <div class="header-actions">
                    <button class="header-action" onclick="toggleSave('${detail.id}')">🤍</button>
                    <button class="header-action" onclick="sharePage()">↗️</button>
                </div>
            </div>
            ${badgesHtml}
        </div>
        
        <!-- Content -->
        <div class="section">
            <h1 class="text-2xl font-black mb-2">${detail.name}</h1>
            <p class="text-gray mb-3">${detail.category || 'Restaurant'} • ${detail.price || detail.priceLevel || 'N/A'} • ${detail.distance || '0 mi'}</p>
            <div class="flex items-center gap-3 mb-4">
                <span class="badge badge-warning">⭐ ${detail.rating || 0}</span>
                <span class="text-sm text-gray">${detail.reviews || detail.reviewCount || 0} reviews</span>
            </div>
            
            <!-- Quick Actions -->
            <div class="grid-2 mb-4">
                <button class="btn btn-primary btn-block">📍 Directions</button>
                <button class="btn btn-secondary btn-block">📞 Call</button>
            </div>
            <button class="btn btn-block" onclick="showAddToTripDialog('restaurant', ${JSON.stringify(detail).replace(/"/g, '&quot;')})" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; margin-bottom: 16px;">
                🗺️ Add to Trip
            </button>
            
            <!-- Info Card -->
            <div class="info-card mb-4">
                <div class="info-row">
                    <div class="info-row-icon">🕐</div>
                    <div class="info-row-content">
                        <div class="info-row-label">Hours</div>
                        <div class="info-row-value ${detail.isOpen ? 'success' : ''}">
                            ${Array.isArray(detail.hours) ? detail.hours[0] || 'Hours not available' : detail.hours || 'Hours not available'}
                        </div>
                    </div>
                    <span class="info-row-action">›</span>
                </div>
                <div class="info-row">
                    <div class="info-row-icon">📍</div>
                    <div class="info-row-content">
                        <div class="info-row-label">Address</div>
                        <div class="info-row-value">${detail.address || 'Address not available'}</div>
                    </div>
                    <span class="info-row-action">›</span>
                </div>
                <div class="info-row">
                    <div class="info-row-icon">📞</div>
                    <div class="info-row-content">
                        <div class="info-row-label">Phone</div>
                        <div class="info-row-value">${detail.phone || 'Phone not available'}</div>
                    </div>
                    <span class="info-row-action">›</span>
                </div>
            </div>
            
            <!-- Get a Ride Banner -->
            <div class="banner banner-ai mb-4" onclick="navigateTo('rides', {destination: '${detail.address}'})">
                <span class="banner-icon">🚗</span>
                <div class="banner-content">
                    <div class="banner-title">Need a ride?</div>
                    <div class="banner-text">Compare Uber & Lyft prices instantly</div>
                </div>
            </div>
        </div>
    `;
}

function renderRideResults(rides) {
    if (!DOM.ridesContainer) return;

    if (rides.length === 0) {
        DOM.ridesContainer.innerHTML = renderErrorState('No rides available');
        return;
    }

    // Find best price and fastest
    const sortedByPrice = [...rides].sort((a, b) => a.price - b.price);
    const sortedByTime = [...rides].sort((a, b) => a.pickup - b.pickup);
    const bestPriceRide = sortedByPrice[0];
    const fastestRide = sortedByTime[0];
    const bestPriceId = bestPriceRide.provider;
    const fastestId = fastestRide.provider;

    DOM.ridesContainer.innerHTML = rides.map(ride => {
        let badge = null;
        if (ride.provider === bestPriceId && ride.provider !== fastestId) badge = 'best';
        else if (ride.provider === fastestId && ride.provider !== bestPriceId) badge = 'fastest';
        else if (ride.provider === bestPriceId) badge = 'best';

        return renderRideCard(ride, ride.provider === bestPriceId, badge);
    }).join('');

    // Update trip stats
    const avgDistance = rides.reduce((sum, r) => sum + (r.distance || 0), 0) / rides.length;
    const avgDuration = rides.reduce((sum, r) => sum + (r.duration || 0), 0) / rides.length;
    const maxPrice = Math.max(...rides.map(r => r.price));
    const minPrice = Math.min(...rides.map(r => r.price));
    const savings = maxPrice - minPrice;

    const distanceEl = document.getElementById('ride-distance');
    const timeEl = document.getElementById('ride-time');
    const savingsEl = document.getElementById('ride-savings');

    if (distanceEl) distanceEl.textContent = `${avgDistance.toFixed(1)} mi`;
    if (timeEl) timeEl.textContent = `${Math.round(avgDuration)} min`;
    if (savingsEl) savingsEl.textContent = `$${Math.round(savings)}`;

    // Update CTA button with best price option
    const ctaBtn = document.getElementById('book-ride-btn');
    if (ctaBtn) {
        const providerName = bestPriceRide.name || bestPriceRide.provider;
        ctaBtn.textContent = `Book ${providerName} • $${bestPriceRide.price.toFixed(2)}`;
    }

    // Update AI recommendation banner
    const recommendationEl = document.getElementById('ride-recommendation');
    if (recommendationEl) {
        const savingsFromBest = maxPrice - bestPriceRide.price;
        const savingsText = savingsFromBest > 0 ? `$${Math.round(savingsFromBest)} cheaper than other options` : 'Best price available';
        const providerDisplayName = bestPriceRide.name || bestPriceRide.provider;
        recommendationEl.innerHTML = `
            <span class="banner-icon">💡</span>
            <div class="banner-content">
                <div class="banner-title">${providerDisplayName} is your best bet! (Demo)</div>
                <div class="banner-text">${savingsText} with ${bestPriceRide.pickup} min pickup time. <em>Sample data</em></div>
            </div>
        `;
    }
}

function renderSavedItems() {
    if (!DOM.savedContainer) return;

    DOM.savedContainer.innerHTML = `
        <div class="list">
            ${AppState.savedItems.map(savedItem => {
                const restaurant = savedItem.restaurant_data;
                const placeId = restaurant.place_id;

                return `
                    <div class="place-card" data-id="${placeId}" onclick="openPlaceDetail('${placeId}')" style="cursor: pointer;">
                        <div class="place-card-image">
                            ${restaurant.image ? `<img src="${restaurant.image}" alt="${restaurant.name}">` : ''}
                        </div>
                        <div class="place-card-content">
                            <h3 class="place-card-name">${restaurant.name}</h3>
                            <p class="place-card-meta">${restaurant.category || 'Restaurant'} • ${restaurant.vicinity || ''}</p>
                            <div class="place-card-tags">
                                ${Array.isArray(restaurant.tags) ? restaurant.tags.map(tag => `<span class="place-card-tag">${tag}</span>`).join('') : ''}
                            </div>
                            <div class="place-card-footer">
                                <span class="place-card-rating">⭐ ${restaurant.rating || 'N/A'}</span>
                                ${restaurant.distance ? `<span class="place-card-distance">${restaurant.distance}</span>` : ''}
                                <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); removeSavedRestaurant(${savedItem.id}, '${placeId}')">
                                    🗑️ Remove
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

async function loadTrendingItems() {
    if (!DOM.trendingContainer) return;

    // Get user's current location
    let location = 'Times Square, NYC'; // Default fallback

    try {
        if (navigator.geolocation) {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
            });
            const { latitude, longitude } = position.coords;
            location = `${latitude},${longitude}`;
        }
    } catch (error) {
        console.log('Using default location for trending items:', error.message);
    }

    const response = await fetchPlaces({ trending: true, limit: 5, location });
    const items = response.results || response; // Handle both object and array response

    // Cache items for detail page
    items.forEach(item => {
        AppState.placesCache[item.id] = item;
    });

    DOM.trendingContainer.innerHTML = items.map(item => {
        const imageUrl = item.image || item.image_url;
        const backgroundStyle = imageUrl
            ? `background-image: url('${imageUrl}'); background-size: cover; background-position: center;`
            : `background: ${item.gradient}`;
        return `
            <div class="grid-card" style="min-width: 160px;" onclick="openPlaceDetail('${item.id}')">
                <div class="grid-card-image" style="${backgroundStyle}"></div>
                <div class="grid-card-content">
                    <h3 class="grid-card-name">${item.name}</h3>
                    <p class="grid-card-meta">${item.category}</p>
                    <span class="grid-card-rating">⭐ ${item.rating}</span>
                </div>
            </div>
        `;
    }).join('');
}

async function loadActivities() {
    if (!DOM.activitiesContainer) return;

    const response = await fetchPlaces({ type: 'activity', limit: 4 });
    const items = response.results || response; // Handle both object and array response

    // Cache items for detail page
    items.forEach(item => {
        AppState.placesCache[item.id] = item;
    });

    DOM.activitiesContainer.innerHTML = items.map(item => renderGridCard(item)).join('');
}

// ================================
// 8. EVENT HANDLERS
// ================================

function handleSearch(event) {
    event.preventDefault();
    const query = DOM.homeSearchInput?.value || DOM.searchInput?.value || '';

    // Check if query is about rides
    const rideKeywords = ['ride', 'uber', 'lyft', 'taxi', 'cab', 'drive', 'pick up', 'pickup', 'drop off', 'drop-off'];
    const isRideQuery = rideKeywords.some(keyword => query.toLowerCase().includes(keyword));

    if (isRideQuery) {
        // Track ride search event
        if (typeof gtag !== 'undefined') {
            gtag('event', 'search', {
                search_term: query,
                search_type: 'ride'
            });
        }
        // Use backend's intelligent parsing via /api/search
        parseAndNavigateToRides(query);
    } else {
        // Track restaurant search event
        if (typeof gtag !== 'undefined') {
            gtag('event', 'search', {
                search_term: query,
                search_type: 'restaurant'
            });
        }
        navigateTo('search', query);
    }
}

async function parseAndNavigateToRides(query) {
    // Use frontend parsing directly (backend /api/search has geocoding timeout issues)
    const { origin, destination } = parseRideQuerySimple(query);
    navigateTo('rides', { origin, destination });
}

function parseRideQuerySimple(query) {
    const queryLower = query.toLowerCase();
    let origin = null;
    let destination = 'Times Square, NYC';

    // Remove common filler words that appear before the destination "to"
    // This handles patterns like "need to take ride to X" or "need to go to X"
    let cleaned = queryLower;
    cleaned = cleaned.replace(/\b(need|want|like)\s+(to|a)\s+(take|get|book|find|have)\s+(a|an|the)?\s*(ride|uber|lyft|taxi|cab)\s+to\s+/gi, 'to ');
    cleaned = cleaned.replace(/\b(need|want|like)\s+to\s+(go|head|travel)\s+to\s+/gi, 'to ');

    // Now extract destination after "to"
    const toMatch = cleaned.match(/\bto\s+([a-z][a-z\s,]+?)(?:\s*$|\.)/i);
    if (toMatch) {
        let dest = toMatch[1].trim();

        // Capitalize each word
        dest = dest.split(' ').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');

        // Add ", NYC" if not present and no state/city mentioned
        if (!dest.includes(',') && !dest.toLowerCase().includes('nyc') && !dest.toLowerCase().includes('new york')) {
            dest = `${dest}, NYC`;
        }

        destination = dest;
    }

    // Try to extract origin - look for "from" pattern
    const fromMatch = queryLower.match(/\bfrom\s+([a-z\s,]+?)\s+to\s+/i);
    if (fromMatch) {
        let orig = fromMatch[1].trim();
        // Capitalize
        orig = orig.split(' ').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        if (!orig.includes(',')) {
            orig = `${orig}, NYC`;
        }
        origin = orig;
    }

    return { origin, destination };
}

function handleCategoryClick(category) {
    // Toggle category filter
    const chip = event.target.closest('.filter-chip');
    const isActive = chip.classList.contains('active');

    // Remove active from all chips in same group
    chip.parentElement.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));

    if (!isActive) {
        chip.classList.add('active');
        AppState.filters.category = category;
    } else {
        // If clicking active chip, default to Food
        chip.classList.add('active');
        AppState.filters.category = category;
    }

    // Re-fetch results
    initSearchPage(DOM.searchInput?.value || '');
}

function handleFilterClick(filter) {
    // Toggle sort filter
    const chip = event.target.closest('.filter-chip');
    const isActive = chip.classList.contains('active');

    // Remove active from all chips in same group
    chip.parentElement.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));

    if (!isActive) {
        chip.classList.add('active');
        // Store filter in AppState for future use with sorting
        // For now, just re-fetch with same category
    } else {
        // Deactivate filter
    }

    // Re-fetch results (currently filters are applied on backend)
    initSearchPage(DOM.searchInput?.value || '');
}

function selectRide(provider) {
    // Track ride selection event
    const selectedRide = document.querySelector(`.ride-card[data-provider="${provider}"]`);
    const price = selectedRide?.querySelector('.ride-card-amount')?.textContent;
    const vehicleType = selectedRide?.dataset.vehicleType;

    if (typeof gtag !== 'undefined') {
        gtag('event', 'select_content', {
            content_type: 'ride',
            item_id: provider,
            vehicle_type: vehicleType,
            price: price
        });
    }

    // Update selection
    document.querySelectorAll('.ride-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.provider === provider);
    });

    // Update CTA button
    const ctaBtn = document.getElementById('book-ride-btn');
    if (ctaBtn && price) {
        ctaBtn.textContent = `Book ${provider} • ${price}`;
    }
}

async function toggleSave(restaurantId) {
    // Check if user is authenticated - force signup for guests
    const isAuth = window.authManager && window.authManager.isAuthenticated();

    if (!isAuth) {
        // Guest user trying to save - redirect to signup
        showToast('Sign up to save your favorite places!', 'info');
        setTimeout(() => {
            navigateTo('register');
        }, 1000);
        return;
    }

    // Find the restaurant in search results or places cache
    let restaurant = AppState.searchResults.find(r => (r.place_id || r.id) === restaurantId);

    if (!restaurant) {
        restaurant = AppState.placesCache[restaurantId];
    }

    if (!restaurant) {
        console.error('Restaurant not found:', restaurantId);
        showToast('Could not save restaurant', 'error');
        return;
    }

    // Check if already saved
    const isSaved = isRestaurantSaved(restaurantId);

    // IMMEDIATE UI UPDATE - optimistic update
    updateSaveButtons(restaurantId, !isSaved);

    if (isSaved) {
        // Find the saved item to get its database ID
        const savedItem = AppState.savedItems.find(item => item.restaurant_id === restaurantId);
        if (savedItem) {
            const success = await removeSavedRestaurant(savedItem.id, restaurantId);
            // If failed, revert the UI
            if (!success) {
                updateSaveButtons(restaurantId, true);
            }
        }
    } else {
        const success = await saveRestaurant(restaurant);
        // If failed, revert the UI
        if (!success) {
            updateSaveButtons(restaurantId, false);
        }
    }
}

function openPlaceDetail(placeId) {
    // Track restaurant click event
    if (typeof gtag !== 'undefined') {
        gtag('event', 'select_content', {
            content_type: 'restaurant',
            item_id: placeId
        });
    }
    navigateTo('detail', placeId);
}

function editRideLocation(type) {
    const elementId = type === 'pickup' ? 'ride-pickup' : 'ride-destination';
    const element = document.getElementById(elementId);
    const currentValue = element.textContent;

    // Create an input field to replace the text
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentValue;
    input.className = 'info-row-value';
    input.style.cssText = 'border: none; border-bottom: 2px solid var(--color-sunset-orange); background: transparent; padding: 4px 0; font-size: inherit; width: 100%; outline: none;';

    // Replace element with input
    element.replaceWith(input);
    input.focus();
    input.select();

    // Add autocomplete on input
    input.addEventListener('input', (e) => {
        const value = e.target.value;

        // Get autocomplete predictions
        getAutocompletePredictions(value, (predictions) => {
            if (predictions.length > 0) {
                showAutocompleteDropdown(input, predictions);
            } else {
                hideAutocompleteDropdown();
            }
        });
    });

    // Hide dropdown on Escape
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideAutocompleteDropdown();
        }
    });

    // Handle when user finishes editing
    const finishEditing = async () => {
        // Hide autocomplete dropdown
        hideAutocompleteDropdown();
        const newValue = input.value.trim();

        // Create text element to replace input
        const textElement = document.createElement('div');
        textElement.id = elementId;
        textElement.className = 'info-row-value';
        textElement.textContent = newValue || currentValue;

        input.replaceWith(textElement);

        // If value changed, re-fetch rides
        if (newValue && newValue !== currentValue) {
            const pickup = document.getElementById('ride-pickup').textContent;
            const destination = document.getElementById('ride-destination').textContent;

            // Convert "Current Location" or "Empire State Building, NYC" to coordinates
            let origin = pickup;
            if (pickup.includes('Current Location') || pickup === 'Empire State Building, NYC') {
                origin = '40.748817,-73.985428';
            }

            // Re-fetch rides with new locations
            await initRidesPage({ origin, destination });
        }
    };

    // Finish on blur or Enter key
    input.addEventListener('blur', finishEditing);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            finishEditing();
        } else if (e.key === 'Escape') {
            const textElement = document.createElement('div');
            textElement.id = elementId;
            textElement.className = 'info-row-value';
            textElement.textContent = currentValue;
            input.replaceWith(textElement);
        }
    });
}

// ================================
// GOOGLE PLACES AUTOCOMPLETE
// ================================

// Initialize Google Places Autocomplete (called when Maps API loads)
function initAutocomplete() {
    if (typeof google === 'undefined' || !google.maps) {
        console.warn('Google Maps API not loaded yet');
        return;
    }

    // Initialize autocomplete service
    AppState.autocomplete.service = new google.maps.places.AutocompleteService();
    console.log('✓ Google Places Autocomplete initialized');
}

// Create a new session token for autocomplete
function createSessionToken() {
    if (typeof google !== 'undefined' && google.maps && google.maps.places) {
        AppState.autocomplete.sessionToken = new google.maps.places.AutocompleteSessionToken();
    }
}

// Get autocomplete predictions with debouncing and session token
function getAutocompletePredictions(input, callback) {
    // Don't trigger if less than 3 characters
    if (!input || input.trim().length < 3) {
        callback([]);
        return;
    }

    // Clear previous debounce timer
    if (AppState.autocomplete.debounceTimer) {
        clearTimeout(AppState.autocomplete.debounceTimer);
    }

    // Debounce: wait 300ms before making API call
    AppState.autocomplete.debounceTimer = setTimeout(() => {
        if (!AppState.autocomplete.service) {
            console.warn('Autocomplete service not initialized');
            callback([]);
            return;
        }

        // Create session token if not exists
        if (!AppState.autocomplete.sessionToken) {
            createSessionToken();
        }

        const request = {
            input: input.trim(),
            sessionToken: AppState.autocomplete.sessionToken,
            // Restrict to NYC area
            location: new google.maps.LatLng(40.7128, -74.0060), // NYC coordinates
            radius: 50000, // 50km radius around NYC
            componentRestrictions: { country: 'us' }
        };

        AppState.autocomplete.service.getPlacePredictions(request, (predictions, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK && predictions) {
                callback(predictions);
            } else {
                console.warn('Autocomplete failed:', status);
                callback([]);
            }
        });
    }, 300); // 300ms debounce
}

// Show autocomplete dropdown
function showAutocompleteDropdown(inputElement, predictions) {
    // Remove existing dropdown
    hideAutocompleteDropdown();

    if (!predictions || predictions.length === 0) {
        return;
    }

    const dropdown = document.createElement('div');
    dropdown.id = 'autocomplete-dropdown';
    dropdown.className = 'autocomplete-dropdown';

    predictions.forEach(prediction => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.textContent = prediction.description;
        item.onclick = () => selectAutocompletePlace(inputElement, prediction);
        dropdown.appendChild(item);
    });

    // Position dropdown below input
    const rect = inputElement.getBoundingClientRect();
    dropdown.style.top = `${rect.bottom + window.scrollY}px`;
    dropdown.style.left = `${rect.left}px`;
    dropdown.style.width = `${rect.width}px`;

    document.body.appendChild(dropdown);
    AppState.autocomplete.activeInput = inputElement;
}

// Hide autocomplete dropdown
function hideAutocompleteDropdown() {
    const dropdown = document.getElementById('autocomplete-dropdown');
    if (dropdown) {
        dropdown.remove();
    }
    AppState.autocomplete.activeInput = null;
}

// Select a place from autocomplete
function selectAutocompletePlace(inputElement, prediction) {
    // Update input value
    inputElement.value = prediction.description;

    // Hide dropdown
    hideAutocompleteDropdown();

    // Clear session token (session complete)
    createSessionToken();

    // Trigger blur to save the location
    inputElement.blur();
}

// Use current location for pickup
function useCurrentLocation() {
    if (!navigator.geolocation) {
        showToast('Geolocation not supported by your browser', 'error');
        return;
    }

    setLoading(true);

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude } = position.coords;
            const origin = `${latitude},${longitude}`;

            // Update pickup display
            const pickupElement = document.getElementById('ride-pickup');
            if (pickupElement) {
                pickupElement.textContent = 'Current Location';
            }

            // Get current destination
            const destinationElement = document.getElementById('ride-destination');
            const destination = destinationElement ? destinationElement.textContent : 'Times Square, NYC';

            // Re-fetch rides with current location
            await initRidesPage({ origin, destination });

            showToast('Using your current location', 'success');
            setLoading(false);
        },
        (error) => {
            console.error('Geolocation error:', error);
            showToast('Unable to get your location', 'error');
            setLoading(false);
        }
    );
}

function clearFilters() {
    AppState.filters = {
        category: 'Food',
        priceRange: null,
        rating: null,
        distance: null
    };

    // Remove active from all filter chips
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));

    // Set Food category as active
    const foodChip = document.querySelector('#category-chips .filter-chip[data-category="Food"]');
    if (foodChip) {
        foodChip.classList.add('active');
    }

    initSearchPage(DOM.searchInput?.value || '');
}

function retry() {
    // Re-initialize current page
    onPageEnter(AppState.currentPage);
}

function sharePage() {
    if (navigator.share) {
        navigator.share({
            title: 'Check this out on Hopwise!',
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href);
        showToast('Link copied!');
    }
}

// ================================
// 9. UI HELPERS
// ================================

function setLoading(isLoading) {
    AppState.loading = isLoading;
    
    if (DOM.loadingOverlay) {
        DOM.loadingOverlay.classList.toggle('hidden', !isLoading);
    }
}

function setError(message) {
    AppState.error = message;
    showToast(message, 'error');
}

function showToast(message, type = 'default') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ================================
// 10. MOCK DATA (Replace with API)
// ================================

function getMockPlaces(params = {}) {
    return [
        {
            id: 'place-1',
            name: "Joe's Pizza",
            category: 'Italian',
            priceLevel: '$',
            distance: '0.3 mi',
            rating: 4.8,
            tags: ['🔥 Trending', '👥 Popular'],
            badge: '🏆 #1',
            gradient: 'linear-gradient(135deg, #FFE5B4, #FFB347)',
            image: null
        },
        {
            id: 'place-2',
            name: 'Sweetgreen',
            category: 'Healthy',
            priceLevel: '$$',
            distance: '0.4 mi',
            rating: 4.6,
            tags: ['🌿 Healthy', '⚡ Quick'],
            badge: null,
            gradient: 'linear-gradient(135deg, #E8F5E9, #A5D6A7)',
            image: null
        },
        {
            id: 'place-3',
            name: 'Sushi Nakazawa',
            category: 'Japanese',
            priceLevel: '$$$$',
            distance: '0.8 mi',
            rating: 4.9,
            tags: ['⭐ Fine Dining'],
            badge: null,
            gradient: 'linear-gradient(135deg, #FCE4EC, #F48FB1)',
            image: null
        },
        {
            id: 'place-4',
            name: 'The Smith',
            category: 'American',
            priceLevel: '$$',
            distance: '0.5 mi',
            rating: 4.5,
            tags: ['🍳 Brunch', '🍸 Bar'],
            badge: null,
            gradient: 'linear-gradient(135deg, #E3F2FD, #90CAF9)',
            image: null
        }
    ];
}

function getMockRides(params = {}) {
    return [
        {
            provider: 'Uber',
            name: 'Uber X',
            type: 'Standard',
            seats: 4,
            price: 45,
            pickup: 5,
            duration: 42,
            rating: 4.9,
            surge: null
        },
        {
            provider: 'Lyft',
            name: 'Lyft',
            type: 'Standard',
            seats: 4,
            price: 52,
            pickup: 3,
            duration: 42,
            rating: 4.8,
            surge: 1.2
        },
        {
            provider: 'Via',
            name: 'Via',
            type: 'Shared',
            seats: 2,
            price: 38,
            pickup: 8,
            duration: 55,
            rating: 4.7,
            surge: null
        }
    ];
}

function getMockPlaceDetail(placeId) {
    const details = {
        'place-1': {
            id: 'place-1',
            name: "Joe's Pizza",
            category: 'Italian • Pizza',
            priceLevel: '$',
            distance: '0.3 mi',
            rating: 4.8,
            reviewCount: 2347,
            badges: ['🏆 #1 Pizza in NYC', '📸 2.3k photos'],
            isOpen: true,
            hours: 'Open · Closes 4:00 AM',
            address: '7 Carmine St, New York',
            phone: '(212) 366-1182',
            gradient: 'linear-gradient(135deg, #FFE5B4, #FFB347)'
        }
    };
    
    return details[placeId] || details['place-1'];
}

// ================================
// 10. AUTHENTICATION HANDLERS
// ================================

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    const submitBtn = document.getElementById('login-submit-btn');

    // Hide previous errors
    errorDiv.style.display = 'none';

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';

    try {
        await window.authManager.login(email, password);

        // Show success message
        showToast('Welcome back!', 'success');

        // Reload saved restaurants for this user
        await loadSavedRestaurants();

        // Update navigation to show all tabs
        updateBottomNavForAuthStatus();

        // Update home header to show profile/notifications
        updateHomeHeaderActions();

        // Navigate to home
        navigateTo('home');

        // Reset form
        event.target.reset();

    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = error.message || 'Login failed. Please check your credentials.';
        errorDiv.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Log In';
    }
}

/**
 * Handle registration form submission
 */
async function handleRegister(event) {
    event.preventDefault();

    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const errorDiv = document.getElementById('register-error');
    const submitBtn = document.getElementById('register-submit-btn');

    // Hide previous errors
    errorDiv.style.display = 'none';

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';

    try {
        await window.authManager.register(username, email, password);

        // Show success message
        showToast('Account created successfully!', 'success');

        // Reload saved restaurants for this user
        await loadSavedRestaurants();

        // Update navigation to show all tabs
        updateBottomNavForAuthStatus();

        // Update home header to show profile/notifications
        updateHomeHeaderActions();

        // Navigate to home
        navigateTo('home');

        // Reset form
        event.target.reset();

    } catch (error) {
        console.error('Registration error:', error);
        errorDiv.textContent = error.message || 'Registration failed. Please try again.';
        errorDiv.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Account';
    }
}

/**
 * Handle logout
 */
async function handleLogout() {
    try {
        await window.authManager.logout();

        // Clear saved items from state
        AppState.savedItems = [];
        AppState.savedRestaurantIds.clear();

        // Update navigation to show only guest tabs
        updateBottomNavForAuthStatus();

        // Update home header to show Sign Up button
        updateHomeHeaderActions();

        // Show success message
        showToast('Logged out successfully', 'success');

        // Navigate to home
        navigateTo('home');

    } catch (error) {
        console.error('Logout error:', error);
        showToast('Logout failed', 'error');
    }
}

// ================================
// 11. INITIALIZATION
// ================================

async function initApp() {
    // Initialize DOM cache
    initDOM();

    // Initialize device ID for favorites
    getDeviceId();

    // Load saved restaurants from API (only for authenticated users)
    if (window.authManager && window.authManager.isAuthenticated()) {
        await loadSavedRestaurants();
    }

    // Set up event listeners
    setupEventListeners();

    // Update bottom navigation based on auth status
    updateBottomNavForAuthStatus();

    // Navigate to initial page
    navigateTo('home');

    console.log('🎒 Hopwise App initialized!');
    console.log('Device ID:', AppState.deviceId);
    console.log('Authenticated:', window.authManager?.isAuthenticated() || false);
    console.log('Saved restaurants:', AppState.savedItems.length);
}

function setupEventListeners() {
    // Bottom navigation
    DOM.bottomNav?.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            if (page) navigateTo(page);
        });
    });

    // Search form
    document.querySelectorAll('.search-form').forEach(form => {
        form.addEventListener('submit', handleSearch);
    });

    // Category filter chips (Food, Drinks, Ice Cream, Cafe)
    document.querySelectorAll('#category-chips .filter-chip').forEach(chip => {
        chip.addEventListener('click', () => handleCategoryClick(chip.dataset.category));
    });

    // Sort filter chips (Price, Rating, Distance, Open Now)
    document.querySelectorAll('#filter-chips .filter-chip').forEach(chip => {
        chip.addEventListener('click', () => handleFilterClick(chip.dataset.filter));
    });

    // Event delegation for place cards and grid cards
    document.body.addEventListener('click', (e) => {
        // Handle place card clicks
        const placeCard = e.target.closest('.place-card, .grid-card');
        if (placeCard) {
            const placeId = placeCard.dataset.id;
            if (placeId) {
                openPlaceDetail(placeId);
            }
        }

        // Handle save button clicks
        const saveButton = e.target.closest('.place-card-save, .grid-card-save');
        if (saveButton) {
            e.stopPropagation();
            const saveId = saveButton.dataset.saveId;
            if (saveId) {
                toggleSave(saveId);
            }
        }
    });
}

// Start app when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);

// ================================
// 12. EXPORTS (for module usage)
// ================================

// ============================================================================
// PROFILE PAGE FUNCTIONS
// ============================================================================

/**
 * Initialize profile page with user data
 */
function initProfilePage() {
    const user = window.authManager?.getUser();

    if (!user) {
        // Redirect to login if not authenticated
        navigateTo('login');
        return;
    }

    // Update avatar with first letter of username
    const avatarText = document.getElementById('profile-avatar-text');
    if (avatarText && user.username) {
        avatarText.textContent = user.username.charAt(0).toUpperCase();
    }

    // Update name and email
    const nameElement = document.getElementById('profile-name');
    const emailElement = document.getElementById('profile-email');

    if (nameElement) {
        nameElement.textContent = user.username || 'User';
    }

    if (emailElement) {
        emailElement.textContent = user.email || '';
    }

    // Show premium badge if user is premium
    const premiumBadge = document.getElementById('profile-badge');
    const premiumBannerSection = document.getElementById('premium-banner-section');

    if (user.is_premium) {
        if (premiumBadge) {
            premiumBadge.style.display = 'inline-flex';
        }
        // Hide premium upgrade banner for premium users
        if (premiumBannerSection) {
            premiumBannerSection.style.display = 'none';
        }
    } else {
        if (premiumBadge) {
            premiumBadge.style.display = 'none';
        }
        if (premiumBannerSection) {
            premiumBannerSection.style.display = 'block';
        }
    }

    // Update stats
    updateProfileStats();
}

/**
 * Update profile statistics
 */
function updateProfileStats() {
    // Get saved items count
    const savedCount = AppState.savedItems ? AppState.savedItems.length : 0;

    // Update saved stat
    const statSaved = document.getElementById('stat-saved');
    if (statSaved) {
        statSaved.textContent = savedCount;
    }

    // TODO: Update trips and savings stats when we track those
    // For now, they remain at 0
}

/**
 * Toggle notifications
 */
function toggleNotifications(element) {
    const toggle = element.querySelector('.toggle-switch');
    const subtitle = element.querySelector('.menu-item-subtitle');

    if (!toggle) return;

    const isEnabled = toggle.dataset.enabled === 'true';
    const newState = !isEnabled;

    // Update toggle state
    toggle.dataset.enabled = newState.toString();

    if (newState) {
        toggle.classList.add('active');
        if (subtitle) {
            subtitle.textContent = 'Push notifications enabled';
        }
        showToast('Notifications enabled', 'success');
    } else {
        toggle.classList.remove('active');
        if (subtitle) {
            subtitle.textContent = 'Push notifications disabled';
        }
        showToast('Notifications disabled', 'info');
    }

    // TODO: Save preference to backend
}

/**
 * Toggle dark mode
 */
function toggleDarkMode(element) {
    const toggle = element.querySelector('.toggle-switch');

    if (!toggle) return;

    const isEnabled = toggle.dataset.enabled === 'true';
    const newState = !isEnabled;

    // Update toggle state
    toggle.dataset.enabled = newState.toString();

    if (newState) {
        toggle.classList.add('active');
        showToast('Dark mode coming soon!', 'info');
    } else {
        toggle.classList.remove('active');
        showToast('Dark mode coming soon!', 'info');
    }

    // TODO: Implement dark mode
}

window.Hopwise = {
    navigateTo,
    goBack,
    toggleSave,
    openPlaceDetail,
    selectRide,
    handleSearch,
    showToast,
    editRideLocation,
    useCurrentLocation,
    AppState
};

// Export profile functions globally
window.initProfilePage = initProfilePage;
window.toggleNotifications = toggleNotifications;
window.toggleDarkMode = toggleDarkMode;

// Export trip functions globally
window.showCreateTripDialog = showCreateTripDialog;

// Export autocomplete init function globally (called by Google Maps API)
window.initAutocomplete = initAutocomplete;
