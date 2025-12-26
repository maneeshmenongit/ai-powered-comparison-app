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
    savedItems: [],
    searchResults: [],
    placesCache: {}, // Cache all fetched places by ID for detail page
    filters: {
        category: 'all',
        priceRange: null,
        rating: null,
        distance: null
    },
    loading: false,
    error: null
};

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
    
    // States
    DOM.loadingOverlay = document.getElementById('loading-overlay');
    DOM.toastContainer = document.getElementById('toast-container');
}

// ================================
// 3. NAVIGATION
// ================================

function navigateTo(pageName, data = null) {
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
        case 'profile':
            initProfilePage();
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
        return places;

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
    const isSaved = AppState.savedItems.includes(place.id);
    const imageUrl = place.image || place.image_url;
    const tags = Array.isArray(place.tags) ? place.tags : [];

    return `
        <div class="place-card" data-id="${place.id}" onclick="openPlaceDetail('${place.id}')">
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
                    <button class="place-card-save ${isSaved ? 'saved' : ''}" data-save-id="${place.id}" onclick="event.stopPropagation(); toggleSave('${place.id}')">
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
    const isSaved = AppState.savedItems.includes(item.id);
    const imageUrl = item.image || item.image_url;
    const backgroundStyle = imageUrl
        ? `background-image: url('${imageUrl}'); background-size: cover; background-position: center;`
        : `background: ${item.gradient || 'var(--color-gray-100)'}`;

    return `
        <div class="grid-card" data-id="${item.id}" onclick="openPlaceDetail('${item.id}')">
            <div class="grid-card-image" style="${backgroundStyle}">
                <button class="grid-card-save" data-save-id="${item.id}" onclick="event.stopPropagation(); toggleSave('${item.id}')">
                    ${isSaved ? '❤️' : '🤍'}
                </button>
                ${item.category ? `<span class="grid-card-category">${item.categoryIcon} ${item.category}</span>` : ''}
            </div>
            <div class="grid-card-content">
                <h3 class="grid-card-name">${item.name}</h3>
                <p class="grid-card-meta">${item.meta}</p>
                <span class="grid-card-rating">⭐ ${item.rating}</span>
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

        const userName = AppState.user?.name || '';
        DOM.homeGreeting.textContent = `${greeting} ${userName}! 👋`;
    }
    
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
    const results = await fetchPlaces({ query, ...AppState.filters });
    
    // Render results
    renderSearchResults(results);
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
            // Geolocation failed or denied, use default
            origin = pickupElement?.textContent || 'Times Square, NYC';
            displayOrigin = origin;
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

function initSavedPage() {
    if (!DOM.savedContainer) return;
    
    if (AppState.savedItems.length === 0) {
        DOM.savedContainer.innerHTML = renderEmptyState('saved');
        return;
    }
    
    // Load and render saved items
    renderSavedItems();
}

function initProfilePage() {
    // Profile page initialization
}

// ================================
// 7. RENDER PAGE CONTENT
// ================================

function renderSearchResults(results) {
    if (!DOM.searchResults) return;
    
    // Update count
    if (DOM.resultsCount) {
        DOM.resultsCount.textContent = `${results.length} places found`;
    }
    
    // Render results or empty state
    if (results.length === 0) {
        DOM.searchResults.innerHTML = renderEmptyState('search');
    } else {
        DOM.searchResults.innerHTML = results.map(place => renderPlaceCard(place)).join('');
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
                <div class="banner-title">${providerDisplayName} is your best bet!</div>
                <div class="banner-text">${savingsText} with ${bestPriceRide.pickup} min pickup time.</div>
            </div>
        `;
    }
}

function renderSavedItems() {
    if (!DOM.savedContainer) return;
    
    // TODO: Fetch saved items by IDs
    DOM.savedContainer.innerHTML = `
        <div class="grid-2">
            ${AppState.savedItems.map(id => {
                const item = getMockPlaceDetail(id);
                return item ? renderGridCard(item) : '';
            }).join('')}
        </div>
    `;
}

async function loadTrendingItems() {
    if (!DOM.trendingContainer) return;

    const items = await fetchPlaces({ trending: true, limit: 5 });

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

    const items = await fetchPlaces({ type: 'activity', limit: 4 });

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
    navigateTo('search', query);
}

function handleFilterClick(filter) {
    // Toggle filter
    const chip = event.target.closest('.filter-chip');
    const isActive = chip.classList.contains('active');
    
    // Remove active from all chips in same group
    chip.parentElement.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    
    if (!isActive) {
        chip.classList.add('active');
        AppState.filters.category = filter;
    } else {
        AppState.filters.category = 'all';
    }
    
    // Re-fetch results
    initSearchPage(DOM.searchInput?.value || '');
}

function selectRide(provider) {
    // Update selection
    document.querySelectorAll('.ride-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.provider === provider);
    });
    
    // Update CTA button
    const selectedRide = document.querySelector(`.ride-card[data-provider="${provider}"]`);
    const price = selectedRide?.querySelector('.ride-card-amount')?.textContent;
    const ctaBtn = document.getElementById('book-ride-btn');
    if (ctaBtn && price) {
        ctaBtn.textContent = `Book ${provider} • ${price}`;
    }
}

function toggleSave(itemId) {
    const index = AppState.savedItems.indexOf(itemId);
    
    if (index > -1) {
        AppState.savedItems.splice(index, 1);
        showToast('Removed from saved');
    } else {
        AppState.savedItems.push(itemId);
        showToast('Saved!', 'success');
    }
    
    // Update UI
    document.querySelectorAll(`[data-id="${itemId}"] .place-card-save, [data-id="${itemId}"] .grid-card-save`).forEach(btn => {
        btn.classList.toggle('saved');
        btn.innerHTML = AppState.savedItems.includes(itemId) ? '❤️' : '🤍';
    });
    
    // Persist to localStorage
    localStorage.setItem('hopwise_saved', JSON.stringify(AppState.savedItems));
}

function openPlaceDetail(placeId) {
    navigateTo('detail', placeId);
}

function clearFilters() {
    AppState.filters = {
        category: 'all',
        priceRange: null,
        rating: null,
        distance: null
    };
    
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    
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
// 11. INITIALIZATION
// ================================

function initApp() {
    // Initialize DOM cache
    initDOM();
    
    // Load saved items from localStorage
    const savedItems = localStorage.getItem('hopwise_saved');
    if (savedItems) {
        AppState.savedItems = JSON.parse(savedItems);
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Navigate to initial page
    navigateTo('home');
    
    console.log('🎒 Hopwise App initialized!');
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

    // Filter chips
    document.querySelectorAll('.filter-chip').forEach(chip => {
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

window.Hopwise = {
    navigateTo,
    goBack,
    toggleSave,
    openPlaceDetail,
    selectRide,
    handleSearch,
    showToast,
    AppState
};
