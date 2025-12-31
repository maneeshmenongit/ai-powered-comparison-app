/**
 * frontend/js/auth.js
 *
 * Authentication module for Hopwise
 * Handles user registration, login, logout, and token management
 */

// ============================================================================
// Auth API Client
// ============================================================================

class AuthAPI {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error(`Auth API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * Register a new user
     * @param {string} username - Username
     * @param {string} email - Email address
     * @param {string} password - Password (min 8 characters)
     * @returns {Promise} Response with user data and access token
     */
    async register(username, email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
    }

    /**
     * Login with email and password
     * @param {string} email - Email address
     * @param {string} password - Password
     * @returns {Promise} Response with user data and access token
     */
    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    /**
     * Logout current user
     * @param {string} token - JWT access token
     * @returns {Promise} Response
     */
    async logout(token) {
        return this.request('/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    /**
     * Get current user information
     * @param {string} token - JWT access token
     * @returns {Promise} Response with user data
     */
    async getCurrentUser(token) {
        return this.request('/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }
}

// ============================================================================
// Auth Manager
// ============================================================================

class AuthManager {
    constructor() {
        this.api = new AuthAPI(window.API_BASE_URL || 'http://localhost:5001/api');
        this.currentUser = null;
        this.token = null;

        // Load token and user from localStorage on init
        this.loadFromStorage();
    }

    /**
     * Load authentication data from localStorage
     */
    loadFromStorage() {
        this.token = localStorage.getItem('hopwise_auth_token');
        const userJson = localStorage.getItem('hopwise_user');

        if (userJson) {
            try {
                this.currentUser = JSON.parse(userJson);
            } catch (e) {
                console.error('Failed to parse user data:', e);
                this.clearStorage();
            }
        }
    }

    /**
     * Save authentication data to localStorage
     */
    saveToStorage(user, token) {
        this.currentUser = user;
        this.token = token;

        localStorage.setItem('hopwise_auth_token', token);
        localStorage.setItem('hopwise_user', JSON.stringify(user));
    }

    /**
     * Clear authentication data from localStorage
     */
    clearStorage() {
        this.currentUser = null;
        this.token = null;

        localStorage.removeItem('hopwise_auth_token');
        localStorage.removeItem('hopwise_user');
    }

    /**
     * Check if user is authenticated
     * @returns {boolean}
     */
    isAuthenticated() {
        return !!(this.token && this.currentUser);
    }

    /**
     * Check if user is a guest
     * @returns {boolean}
     */
    isGuest() {
        return this.currentUser?.is_guest === true;
    }

    /**
     * Check if user is premium
     * @returns {boolean}
     */
    isPremium() {
        return this.currentUser?.is_premium === true;
    }

    /**
     * Get authorization header for API requests
     * @returns {object|null}
     */
    getAuthHeader() {
        if (!this.token) return null;
        return { 'Authorization': `Bearer ${this.token}` };
    }

    /**
     * Register a new user
     * @param {string} username - Username
     * @param {string} email - Email
     * @param {string} password - Password
     * @returns {Promise<object>} User data
     */
    async register(username, email, password) {
        try {
            const response = await this.api.register(username, email, password);

            if (response.success && response.data) {
                this.saveToStorage(response.data.user, response.data.access_token);
                return response.data.user;
            }

            throw new Error(response.error || 'Registration failed');
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    /**
     * Login with email and password
     * @param {string} email - Email
     * @param {string} password - Password
     * @returns {Promise<object>} User data
     */
    async login(email, password) {
        try {
            const response = await this.api.login(email, password);

            if (response.success && response.data) {
                this.saveToStorage(response.data.user, response.data.access_token);
                return response.data.user;
            }

            throw new Error(response.error || 'Login failed');
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    /**
     * Logout current user
     * @returns {Promise<void>}
     */
    async logout() {
        try {
            if (this.token) {
                await this.api.logout(this.token);
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearStorage();
        }
    }

    /**
     * Refresh current user data from API
     * @returns {Promise<object|null>}
     */
    async refreshUser() {
        if (!this.token) {
            return null;
        }

        try {
            const response = await this.api.getCurrentUser(this.token);

            if (response.success && response.data) {
                this.currentUser = response.data;
                localStorage.setItem('hopwise_user', JSON.stringify(response.data));
                return response.data;
            }

            throw new Error(response.error || 'Failed to get user data');
        } catch (error) {
            console.error('Refresh user error:', error);
            // If token is invalid, clear auth data
            this.clearStorage();
            return null;
        }
    }

    /**
     * Get current user
     * @returns {object|null}
     */
    getUser() {
        return this.currentUser;
    }

    /**
     * Get access token
     * @returns {string|null}
     */
    getToken() {
        return this.token;
    }
}

// ============================================================================
// Export for use in other modules
// ============================================================================

if (typeof window !== 'undefined') {
    window.AuthManager = AuthManager;
    window.authManager = new AuthManager();
}
