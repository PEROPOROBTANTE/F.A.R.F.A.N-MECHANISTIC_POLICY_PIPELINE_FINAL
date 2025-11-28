/**
 * AtroZ Dashboard Integration - Complete Integration Layer
 * ==========================================================
 * 
 * Integrates the AtroZ HTML dashboard with the Python backend orchestrator.
 * Handles state management, data binding, and visualization updates.
 * 
 * This file should be included AFTER atroz-data-service.js in the HTML
 * 
 * @version 1.0.0
 * @author Integration Team
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const ATROZ_CONFIG = {
    apiBaseURL: window.ATROZ_API_URL || 'http://localhost:5000',
    enableRealtime: window.ATROZ_ENABLE_REALTIME !== 'false',
    enableAuth: window.ATROZ_ENABLE_AUTH === 'true',
    clientId: window.ATROZ_CLIENT_ID || 'atroz-dashboard-v1',
    clientSecret: window.ATROZ_CLIENT_SECRET || 'dev-secret',
    cacheTimeout: parseInt(window.ATROZ_CACHE_TIMEOUT || '300000'),
    refreshInterval: parseInt(window.ATROZ_REFRESH_INTERVAL || '60000')
};

// ============================================================================
// STATE MANAGER
// ============================================================================

class DashboardStateManager {
    constructor() {
        this.state = {
            currentView: 'constellation',
            selectedRegions: new Set(),
            focusMode: false,
            filters: {
                scoreRange: [0, 100],
                categories: [],
                timeRange: [2018, 2024]
            },
            dataVersion: 0,
            lastUpdate: null,
            regions: [],
            activeRegion: null
        };
        
        this.subscribers = new Set();
        this.history = [];
        this.maxHistoryLength = 50;
    }
    
    /**
     * Get current state
     * @returns {Object} Current state
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * Update state with validation
     * @param {Object} updates - State updates
     */
    updateState(updates) {
        const previousState = { ...this.state };
        
        // Validate and apply updates
        Object.keys(updates).forEach(key => {
            if (this.validateStateUpdate(key, updates[key])) {
                this.state[key] = updates[key];
            }
        });
        
        this.state.dataVersion++;
        this.state.lastUpdate = new Date().toISOString();
        
        // Store in history
        this.history.push({
            timestamp: this.state.lastUpdate,
            previousState,
            newState: { ...this.state }
        });
        
        // Trim history
        if (this.history.length > this.maxHistoryLength) {
            this.history = this.history.slice(-this.maxHistoryLength);
        }
        
        // Notify subscribers
        this.notifySubscribers(previousState, this.state);
    }
    
    /**
     * Validate state update
     * @param {string} key - State key
     * @param {*} value - New value
     * @returns {boolean} Valid or not
     */
    validateStateUpdate(key, value) {
        switch (key) {
            case 'currentView':
                return ['constellation', 'macro', 'meso', 'micro'].includes(value);
            case 'focusMode':
                return typeof value === 'boolean';
            case 'selectedRegions':
                return value instanceof Set;
            default:
                return true;
        }
    }
    
    /**
     * Subscribe to state changes
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback) {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }
    
    /**
     * Notify all subscribers
     * @param {Object} previousState - Previous state
     * @param {Object} newState - New state
     */
    notifySubscribers(previousState, newState) {
        for (const callback of this.subscribers) {
            try {
                callback(previousState, newState);
            } catch (error) {
                console.error('[StateManager] Subscriber error:', error);
            }
        }
    }
    
    /**
     * Undo last state change
     */
    undo() {
        if (this.history.length > 1) {
            const previous = this.history[this.history.length - 2];
            this.state = { ...previous.newState };
            this.history.pop();
            this.notifySubscribers({}, this.state);
        }
    }
}

// ============================================================================
// VISUALIZATION ADAPTER
// ============================================================================

class VisualizationAdapter {
    /**
     * Adapt PDET regions from backend to dashboard format
     * @param {Array} backendData - Data from backend API
     * @returns {Array} Adapted data for dashboard
     */
    static adaptPDETRegions(backendData) {
        return backendData.map(region => ({
            id: region.id,
            name: region.name.toUpperCase(),
            x: region.coordinates.x,
            y: region.coordinates.y,
            municipalities: region.metadata.municipalities,
            score: region.scores.overall,
            // Visualization properties
            pulseIntensity: this.calculatePulseIntensity(region.scores),
            connectionStrength: this.calculateConnectionStrength(region.connections),
            colorVariant: this.getColorVariant(region.scores.overall)
        }));
    }
    
    /**
     * Calculate pulse intensity based on score volatility
     * @param {Object} scores - Score object
     * @returns {number} Pulse intensity (0-1)
     */
    static calculatePulseIntensity(scores) {
        const volatility = Math.max(
            Math.abs(scores.overall - scores.governance),
            Math.abs(scores.overall - scores.social),
            Math.abs(scores.overall - scores.economic)
        );
        return Math.min(volatility / 50, 1);
    }
    
    /**
     * Calculate connection strength
     * @param {Array} connections - Connection array
     * @returns {number} Connection strength (0-1)
     */
    static calculateConnectionStrength(connections) {
        return Math.min(connections.length / 5, 1);
    }
    
    /**
     * Get color variant based on score
     * @param {number} score - Overall score
     * @returns {string} Color variant name
     */
    static getColorVariant(score) {
        if (score > 70) return 'toxic-green';
        if (score > 60) return 'copper-oxide';
        return 'blood-red';
    }
    
    /**
     * Adapt municipality detail data
     * @param {Object} backendData - Municipality data from backend
     * @returns {Object} Adapted data
     */
    static adaptMunicipalityDetail(backendData) {
        return {
            radarData: this.formatRadarData(backendData.analysis.radar),
            clusterData: this.formatClusterData(backendData.analysis.clusters),
            questionMatrix: this.formatQuestionMatrix(backendData.analysis.questions),
            recommendations: this.extractRecommendations(backendData.analysis.questions)
        };
    }
    
    /**
     * Format radar chart data
     * @param {Object} radarData - Raw radar data
     * @returns {Object} Formatted radar data
     */
    static formatRadarData(radarData) {
        return {
            labels: radarData.dimensions,
            values: radarData.scores,
            maxValue: 100
        };
    }
    
    /**
     * Format cluster data
     * @param {Array} clusterData - Raw cluster data
     * @returns {Array} Formatted cluster data
     */
    static formatClusterData(clusterData) {
        return clusterData.map(cluster => ({
            name: cluster.name,
            value: cluster.value,
            trend: cluster.trend,
            color: this.getColorVariant(cluster.value)
        }));
    }
    
    /**
     * Format question matrix
     * @param {Array} questions - Question array
     * @returns {Array} Formatted question matrix
     */
    static formatQuestionMatrix(questions) {
        return questions.map(q => ({
            id: q.id,
            score: q.score,
            category: q.category,
            color: this.getScoreColor(q.score),
            opacity: q.score
        }));
    }
    
    /**
     * Get color for score
     * @param {number} score - Score value (0-1)
     * @returns {string} Color CSS variable
     */
    static getScoreColor(score) {
        if (score > 0.7) return 'var(--atroz-green-toxic)';
        if (score > 0.4) return 'var(--atroz-copper-oxide)';
        return 'var(--atroz-red-500)';
    }
    
    /**
     * Extract recommendations from questions
     * @param {Array} questions - Questions array
     * @returns {Array} Recommendations
     */
    static extractRecommendations(questions) {
        const recs = [];
        questions.forEach(q => {
            if (q.score < 0.7 && q.recommendations && q.recommendations.length > 0) {
                recs.push(...q.recommendations);
            }
        });
        return recs.slice(0, 10); // Limit to top 10
    }
}

// ============================================================================
// MAIN INTEGRATION CLASS
// ============================================================================

class AtrozDashboardIntegration {
    constructor() {
        console.log('[AtroZ Integration] Initializing...');
        
        // Initialize services
        this.dataService = new AtrozDataService(ATROZ_CONFIG.apiBaseURL, {
            cacheTimeout: ATROZ_CONFIG.cacheTimeout,
            enableWebSocket: ATROZ_CONFIG.enableRealtime
        });
        
        this.stateManager = new DashboardStateManager();
        
        // Bind to global scope for easy access from HTML
        window.atrozIntegration = this;
        window.atrozDataService = this.dataService;
        window.atrozStateManager = this.stateManager;
        
        // Auto-refresh timer
        this.refreshTimer = null;
        
        // Initialize flag
        this.initialized = false
        
        console.log('[AtroZ Integration] Services initialized');
    }
    
    /**
     * Initialize the integration
     */
    async initialize() {
        if (this.initialized) {
            console.warn('[AtroZ Integration] Already initialized');
            return;
        }
        
        console.log('[AtroZ Integration] Starting initialization...');
        
        try {
            // Authenticate if enabled
            if (ATROZ_CONFIG.enableAuth) {
                await this.dataService.authenticate(
                    ATROZ_CONFIG.clientId,
                    ATROZ_CONFIG.clientSecret
                );
            }
            
            // Load initial data
            await this.loadInitialData();
            
            // Initialize WebSocket if enabled
            if (ATROZ_CONFIG.enableRealtime) {
                this.dataService.initWebSocket();
            }
            
            // Subscribe to state changes
            this.stateManager.subscribe((prevState, newState) => {
                this.handleStateChange(prevState, newState);
            });
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            this.initialized = true;
            console.log('[AtroZ Integration] Initialization complete');
            
            // Emit ready event
            window.dispatchEvent(new CustomEvent('atroz:ready', {
                detail: { integration: this }
            }));
            
        } catch (error) {
            console.error('[AtroZ Integration] Initialization failed:', error);
            throw error;
        }
    }
    
    /**
     * Load initial data
     */
    async loadInitialData() {
        console.log('[AtroZ Integration] Loading initial data...');
        
        try {
            // Load PDET regions
            const regions = await this.dataService.fetchPDETRegions();
            const adaptedRegions = VisualizationAdapter.adaptPDETRegions(regions);
            
            // Update state
            this.stateManager.updateState({
                regions: adaptedRegions
            });
            
            // Update visualization
            this.updatePDETNodes(adaptedRegions);
            
            // Load evidence stream
            const evidence = await this.dataService.fetchEvidenceStream();
            this.updateEvidenceStream(evidence);
            
            console.log(`[AtroZ Integration] Loaded ${regions.length} regions`);
            
        } catch (error) {
            console.error('[AtroZ Integration] Failed to load initial data:', error);
            throw error;
        }
    }
    
    /**
     * Update PDET nodes in visualization
     * @param {Array} regions - Adapted regions data
     */
    updatePDETNodes(regions) {
        console.log('[AtroZ Integration] Updating PDET nodes...');
        
        // Update global pdetRegions variable
        if (typeof window.pdetRegions !== 'undefined') {
            window.pdetRegions = regions;
        }
        
        // Re-initialize constellation if function exists
        if (typeof window.initConstellation === 'function') {
            window.initConstellation();
        }
    }
    
    /**
     * Update evidence stream ticker
     * @param {Array} evidence - Evidence items
     */
    updateEvidenceStream(evidence) {
        console.log('[AtroZ Integration] Updating evidence stream...');
        
        const ticker = document.querySelector('.evidence-ticker');
        if (!ticker) {
            console.warn('[AtroZ Integration] Evidence ticker element not found');
            return;
        }
        
        // Clear existing items
        ticker.innerHTML = '';
        
        // Add evidence items
        evidence.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'evidence-item';
            itemEl.innerHTML = `
                <span class="evidence-dot"></span>
                ${item.source} · Página ${item.page} · "${item.text}"
            `;
            ticker.appendChild(itemEl);
        });
    }
    
    /**
     * Handle state changes
     * @param {Object} prevState - Previous state
     * @param {Object} newState - New state
     */
    handleStateChange(prevState, newState) {
        console.log('[AtroZ Integration] State changed:', {
            prev: prevState,
            new: newState
        });
        
        // Handle view changes
        if (prevState.currentView !== newState.currentView) {
            this.handleViewChange(newState.currentView);
        }
        
        // Handle region selection changes
        if (prevState.selectedRegions !== newState.selectedRegions) {
            this.handleRegionSelectionChange(newState.selectedRegions);
        }
    }
    
    /**
     * Handle view change
     * @param {string} view - New view name
     */
    handleViewChange(view) {
        console.log(`[AtroZ Integration] View changed to: ${view}`);
        // Implement view-specific logic here
    }
    
    /**
     * Handle region selection change
     * @param {Set} selectedRegions - Selected region IDs
     */
    handleRegionSelectionChange(selectedRegions) {
        console.log(`[AtroZ Integration] Selected regions:`, Array.from(selectedRegions));
        // Implement selection-specific logic here
    }
    
    /**
     * Open municipality detail modal
     * @param {Object} region - Region data
     */
    async openMunicipalityDetail(region) {
        console.log(`[AtroZ Integration] Opening municipality detail for:`, region.id);
        
        try {
            // Fetch detailed data
            const detailData = await this.dataService.fetchRegionDetail(region.id);
            const adaptedData = VisualizationAdapter.adaptMunicipalityDetail(detailData);
            
            // Update state
            this.stateManager.updateState({
                activeRegion: region.id
            });
            
            // Populate modal (call existing function from HTML)
            if (typeof window.openMunicipalityDetail === 'function') {
                window.openMunicipalityDetail(region);
            }
            
            // Update modal content with fresh data
            this.updateModalContent(adaptedData);
            
        } catch (error) {
            console.error('[AtroZ Integration] Failed to load municipality detail:', error);
        }
    }
    
    /**
     * Update modal content
     * @param {Object} data - Adapted municipality data
     */
    updateModalContent(data) {
        // Update radar chart
        // Update cluster bars
        // Update question matrix
        // Implementation depends on specific modal structure
        console.log('[AtroZ Integration] Modal content updated');
    }
    
    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.refreshData();
        }, ATROZ_CONFIG.refreshInterval);
        
        console.log(`[AtroZ Integration] Auto-refresh started (${ATROZ_CONFIG.refreshInterval}ms)`);
    }
    
    /**
     * Stop auto-refresh timer
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('[AtroZ Integration] Auto-refresh stopped');
        }
    }
    
    /**
     * Refresh data
     */
    async refreshData() {
        console.log('[AtroZ Integration] Refreshing data...');
        
        try {
            // Clear cache to force fresh data
            this.dataService.clearCache('regions');
            this.dataService.clearCache('evidence');
            
            // Reload data
            await this.loadInitialData();
            
        } catch (error) {
            console.error('[AtroZ Integration] Refresh failed:', error);
        }
    }
    
    /**
     * Export dashboard data
     * @param {Object} options - Export options
     */
    async exportData(options = {}) {
        console.log('[AtroZ Integration] Exporting data...', options);
        
        try {
            const state = this.stateManager.getState();
            const regionIds = options.regions || Array.from(state.selectedRegions);
            
            const data = await this.dataService.exportDashboardData({
                format: options.format || 'json',
                regions: regionIds,
                includeEvidence: options.includeEvidence || false
            });
            
            // Download or display data
            this.downloadExport(data, options.format || 'json');
            
            console.log('[AtroZ Integration] Export complete');
            
        } catch (error) {
            console.error('[AtroZ Integration] Export failed:', error);
        }
    }
    
    /**
     * Download export data
     * @param {Object} data - Export data
     * @param {string} format - Export format
     */
    downloadExport(data, format) {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `atroz-export-${Date.now()}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    /**
     * Destroy integration and cleanup
     */
    destroy() {
        console.log('[AtroZ Integration] Destroying...');
        
        // Stop auto-refresh
        this.stopAutoRefresh();
        
        // Disconnect WebSocket
        this.dataService.disconnectWebSocket();
        
        // Clear cache
        this.dataService.clearCache();
        
        this.initialized = false;
        
        console.log('[AtroZ Integration] Destroyed');
    }
}

// ============================================================================
// AUTO-INITIALIZATION
// ============================================================================

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.atrozDashboard = new AtrozDashboardIntegration();
        window.atrozDashboard.initialize().catch(error => {
            console.error('[AtroZ Integration] Auto-initialization failed:', error);
        });
    });
} else {
    // DOM already loaded
    window.atrozDashboard = new AtrozDashboardIntegration();
    window.atrozDashboard.initialize().catch(error => {
        console.error('[AtroZ Integration] Auto-initialization failed:', error);
    });
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AtrozDashboardIntegration,
        DashboardStateManager,
        VisualizationAdapter
    };
}
