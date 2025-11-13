/**
 * AtroZ Data Service - Frontend Data Management Layer
 * ====================================================
 * 
 * Handles all data fetching, caching, and state management for the AtroZ Dashboard.
 * Implements connection to the Python backend API server.
 * 
 * Features:
 * - RESTful API integration
 * - Client-side caching with TTL
 * - WebSocket support for real-time updates
 * - Error handling and retry logic
 * - Authentication token management
 * 
 * @version 1.0.0
 * @author Integration Team
 */

class AtrozDataService {
    /**
     * Initialize AtroZ Data Service
     * @param {string} baseURL - Base URL for API server (default: http://localhost:5000)
     * @param {Object} config - Configuration options
     */
    constructor(baseURL = 'http://localhost:5000', config = {}) {
        this.baseURL = baseURL;
        this.config = {
            cacheTimeout: config.cacheTimeout || 300000, // 5 minutes
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 1000,
            enableWebSocket: config.enableWebSocket || true,
            ...config
        };
        
        // Cache storage
        this.cache = new Map();
        this.cacheTimestamps = new Map();
        
        // Authentication
        this.authToken = null;
        
        // WebSocket connection
        this.socket = null;
        this.socketConnected = false;
        
        // Subscribers for real-time updates
        this.subscribers = new Map();
        
        console.log('[AtroZ DataService] Initialized with baseURL:', this.baseURL);
    }
    
    /**
     * Authenticate with the API server
     * @param {string} clientId - Client identifier
     * @param {string} clientSecret - Client secret
     * @returns {Promise<Object>} Authentication response
     */
    async authenticate(clientId, clientSecret) {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: clientId,
                    client_secret: clientSecret
                })
            });
            
            if (!response.ok) {
                throw new Error(`Authentication failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.authToken = data.access_token;
            
            console.log('[AtroZ DataService] Authentication successful');
            return data;
            
        } catch (error) {
            console.error('[AtroZ DataService] Authentication error:', error);
            throw error;
        }
    }
    
    /**
     * Get authentication headers
     * @returns {Object} Headers object
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'X-Atroz-Client': 'dashboard-v1'
        };
        
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        
        return headers;
    }
    
    /**
     * Make HTTP request with retry logic
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: this.getAuthHeaders(),
            ...options
        };
        
        for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, defaultOptions);
                
                if (!response.ok) {
                    if (response.status === 429) {
                        // Rate limited, wait and retry
                        const retryAfter = parseInt(response.headers.get('Retry-After') || '5');
                        console.warn(`[AtroZ DataService] Rate limited, retrying after ${retryAfter}s`);
                        await this.sleep(retryAfter * 1000);
                        continue;
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                return data;
                
            } catch (error) {
                console.error(`[AtroZ DataService] Request failed (attempt ${attempt}/${this.config.retryAttempts}):`, error);
                
                if (attempt === this.config.retryAttempts) {
                    throw error;
                }
                
                // Wait before retry
                await this.sleep(this.config.retryDelay * attempt);
            }
        }
    }
    
    /**
     * Get cached data or fetch from API
     * @param {string} cacheKey - Cache key
     * @param {Function} fetchFn - Function to fetch data if not cached
     * @returns {Promise<Object>} Data
     */
    async getCached(cacheKey, fetchFn) {
        const now = Date.now();
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            const timestamp = this.cacheTimestamps.get(cacheKey);
            if (now - timestamp < this.config.cacheTimeout) {
                console.log(`[AtroZ DataService] Cache hit: ${cacheKey}`);
                return this.cache.get(cacheKey);
            } else {
                // Cache expired
                this.cache.delete(cacheKey);
                this.cacheTimestamps.delete(cacheKey);
            }
        }
        
        // Fetch fresh data
        console.log(`[AtroZ DataService] Cache miss: ${cacheKey}`);
        const data = await fetchFn();
        
        // Store in cache
        this.cache.set(cacheKey, data);
        this.cacheTimestamps.set(cacheKey, now);
        
        return data;
    }
    
    /**
     * Clear cache
     * @param {string} pattern - Pattern to match cache keys (optional)
     */
    clearCache(pattern = null) {
        if (pattern) {
            // Clear matching keys
            const regex = new RegExp(pattern);
            for (const key of this.cache.keys()) {
                if (regex.test(key)) {
                    this.cache.delete(key);
                    this.cacheTimestamps.delete(key);
                }
            }
        } else {
            // Clear all
            this.cache.clear();
            this.cacheTimestamps.clear();
        }
        console.log('[AtroZ DataService] Cache cleared');
    }
    
    /**
     * Sleep for specified milliseconds
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // ========================================================================
    // API METHODS - PDET REGIONS
    // ========================================================================
    
    /**
     * Fetch all PDET regions
     * @returns {Promise<Array>} List of PDET regions
     */
    async fetchPDETRegions() {
        return await this.getCached('pdet-regions', async () => {
            const response = await this.request('/api/v1/pdet/regions');
            return response.data;
        });
    }
    
    /**
     * Fetch specific PDET region detail
     * @param {string} regionId - Region identifier
     * @returns {Promise<Object>} Region detail
     */
    async fetchRegionDetail(regionId) {
        return await this.getCached(`region-${regionId}`, async () => {
            const response = await this.request(`/api/v1/pdet/regions/${regionId}`);
            return response.data;
        });
    }
    
    // ========================================================================
    // API METHODS - MUNICIPALITIES
    // ========================================================================
    
    /**
     * Fetch municipality analysis data
     * @param {string} municipalityId - Municipality identifier
     * @returns {Promise<Object>} Municipality data
     */
    async fetchMunicipalityData(municipalityId) {
        return await this.getCached(`municipality-${municipalityId}`, async () => {
            const response = await this.request(`/api/v1/municipalities/${municipalityId}`);
            return response.data;
        });
    }
    
    // ========================================================================
    // API METHODS - EVIDENCE & DOCUMENTATION
    // ========================================================================
    
    /**
     * Fetch evidence stream for ticker
     * @returns {Promise<Array>} Evidence items
     */
    async fetchEvidenceStream() {
        // Shorter cache for evidence stream
        return await this.getCached('evidence-stream', async () => {
            const response = await this.request('/api/v1/evidence/stream');
            return response.data;
        });
    }
    
    // ========================================================================
    // API METHODS - EXPORT
    // ========================================================================
    
    /**
     * Export dashboard data
     * @param {Object} options - Export options
     * @returns {Promise<Object>} Export result
     */
    async exportDashboardData(options = {}) {
        const response = await this.request('/api/v1/export/dashboard', {
            method: 'POST',
            body: JSON.stringify({
                format: options.format || 'json',
                regions: options.regions || [],
                include_evidence: options.includeEvidence || false
            })
        });
        return response.data;
    }
    
    // ========================================================================
    // WEBSOCKET INTEGRATION
    // ========================================================================
    
    /**
     * Initialize WebSocket connection
     */
    initWebSocket() {
        if (!this.config.enableWebSocket) {
            console.log('[AtroZ DataService] WebSocket disabled');
            return;
        }
        
        try {
            // Note: Requires socket.io-client library
            if (typeof io === 'undefined') {
                console.warn('[AtroZ DataService] socket.io-client not loaded, WebSocket disabled');
                return;
            }
            
            this.socket = io(this.baseURL);
            
            this.socket.on('connect', () => {
                console.log('[AtroZ DataService] WebSocket connected');
                this.socketConnected = true;
            });
            
            this.socket.on('disconnect', () => {
                console.log('[AtroZ DataService] WebSocket disconnected');
                this.socketConnected = false;
            });
            
            this.socket.on('connection_response', (data) => {
                console.log('[AtroZ DataService] WebSocket connection response:', data);
            });
            
            this.socket.on('region_update', (data) => {
                console.log('[AtroZ DataService] Region update received:', data);
                this.handleRegionUpdate(data);
            });
            
        } catch (error) {
            console.error('[AtroZ DataService] WebSocket initialization failed:', error);
        }
    }
    
    /**
     * Subscribe to region updates
     * @param {string} regionId - Region identifier
     * @param {Function} callback - Callback function for updates
     */
    subscribeToRegion(regionId, callback) {
        if (!this.socketConnected) {
            console.warn('[AtroZ DataService] WebSocket not connected, cannot subscribe');
            return;
        }
        
        // Store callback
        if (!this.subscribers.has(regionId)) {
            this.subscribers.set(regionId, []);
        }
        this.subscribers.get(regionId).push(callback);
        
        // Send subscription request
        this.socket.emit('subscribe_region', { region_id: regionId });
        
        console.log(`[AtroZ DataService] Subscribed to region: ${regionId}`);
    }
    
    /**
     * Handle region update from WebSocket
     * @param {Object} data - Update data
     */
    handleRegionUpdate(data) {
        const regionId = data.id;
        
        // Invalidate cache
        this.cache.delete(`region-${regionId}`);
        this.cacheTimestamps.delete(`region-${regionId}`);
        
        // Notify subscribers
        if (this.subscribers.has(regionId)) {
            for (const callback of this.subscribers.get(regionId)) {
                try {
                    callback(data);
                } catch (error) {
                    console.error('[AtroZ DataService] Subscriber callback error:', error);
                }
            }
        }
    }
    
    /**
     * Disconnect WebSocket
     */
    disconnectWebSocket() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.socketConnected = false;
            console.log('[AtroZ DataService] WebSocket disconnected');
        }
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AtrozDataService;
}
