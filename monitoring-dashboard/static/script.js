// Tab switching functionality
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Mark button as active
    const clickedButton = event.target;
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
}

// Auto-refresh functionality
let refreshTimer = 30;
const timerDisplay = document.getElementById('refresh-timer');

if (timerDisplay) {
    setInterval(() => {
        refreshTimer--;
        timerDisplay.textContent = refreshTimer;
        
        if (refreshTimer <= 0) {
            location.reload();
        }
    }, 1000);

    // Auto-refresh every 30 seconds
    setTimeout(() => {
        location.reload();
    }, 30000);
}

// Secure Authentication and Monitoring Dashboard JavaScript

class SecureMonitoring {
    constructor() {
        this.authStatus = {
            grafana: false,
            rabbitmq: false
        };
        this.authCheckInterval = null;
        this.autoRefreshInterval = null;
        this.refreshTimer = 30;
        
        this.init();
    }
    
    async init() {
        await this.checkAuthStatus();
        this.startAuthCheck();
        this.startAutoRefresh();
        this.setupEventListeners();
    }
    
    // Authentication Status Management
    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status');
            if (response.ok) {
                this.authStatus = await response.json();
                this.updateAuthUI();
            }
        } catch (error) {
            console.warn('Auth status check failed:', error);
        }
    }
    
    startAuthCheck() {
        if (this.authCheckInterval) {
            clearInterval(this.authCheckInterval);
        }
        // Check auth status every 30 seconds
        this.authCheckInterval = setInterval(() => {
            this.checkAuthStatus();
        }, 30000);
    }
    
    updateAuthUI() {
        // Update Grafana UI
        const grafanaContainer = document.getElementById('grafana-iframe-container');
        if (grafanaContainer) {
            if (this.authStatus.grafana) {
                this.showAuthenticatedGrafana();
            } else {
                this.showGrafanaLoginPrompt();
            }
        }
        
        // Update RabbitMQ UI
        const rabbitmqContainer = document.getElementById('rabbitmq-iframe-container');
        if (rabbitmqContainer) {
            if (this.authStatus.rabbitmq) {
                this.showAuthenticatedRabbitMQ();
            } else {
                this.showRabbitMQLoginPrompt();
            }
        }
        
        // Update auth indicators
        this.updateAuthIndicators();
    }
    
    // Secure Authentication Methods
    async authenticateGrafana() {
        const button = document.getElementById('grafana-auth-btn');
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Authenticating...';
        }
        
        try {
            const response = await fetch('/api/auth/grafana', {
                method: 'POST',
                credentials: 'same-origin'  // Include cookies
            });
            
            if (response.ok) {
                const result = await response.json();
                this.authStatus.grafana = true;
                this.showAuthenticatedGrafana();
                this.showSuccess('Grafana authenticated successfully');
            } else {
                throw new Error('Authentication failed');
            }
        } catch (error) {
            this.showError('Grafana authentication failed: ' + error.message);
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Authenticate';
            }
        }
    }
    
    async authenticateRabbitMQ() {
        const button = document.getElementById('rabbitmq-auth-btn');
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Authenticating...';
        }
        
        try {
            const response = await fetch('/api/auth/rabbitmq', {
                method: 'POST',
                credentials: 'same-origin'  // Include cookies
            });
            
            if (response.ok) {
                const result = await response.json();
                this.authStatus.rabbitmq = true;
                this.showAuthenticatedRabbitMQ();
                this.showSuccess('RabbitMQ authenticated successfully');
            } else {
                throw new Error('Authentication failed');
            }
        } catch (error) {
            this.showError('RabbitMQ authentication failed: ' + error.message);
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Authenticate';
            }
        }
    }
    
    // Grafana Secure Embedding
    showGrafanaLoginPrompt() {
        const container = document.getElementById('grafana-iframe-container');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-12 bg-blue-50 border border-blue-300 rounded">
                    <i class="fas fa-shield-alt text-4xl text-blue-500 mb-4"></i>
                    <h3 class="text-lg font-semibold text-blue-800 mb-2">Secure Grafana Access</h3>
                    <p class="text-blue-700 text-sm mb-4">
                        Click below to securely authenticate with Grafana.<br>
                        Your credentials are managed server-side and never exposed to the browser.
                    </p>
                    <button id="grafana-auth-btn" onclick="secureMonitoring.authenticateGrafana()" 
                            class="bg-blue-500 text-white px-6 py-3 rounded hover:bg-blue-600 font-medium">
                        <i class="fas fa-sign-in-alt mr-2"></i>Authenticate with Grafana
                    </button>
                    <p class="text-xs text-blue-600 mt-3">
                        <i class="fas fa-lock mr-1"></i>Session expires in 1 hour
                    </p>
                </div>
            `;
        }
    }
    
    showAuthenticatedGrafana() {
        const container = document.getElementById('grafana-iframe-container');
        if (container) {
            const dashboardUrl = '/api/proxy/grafana/d/did-services-overview/did-services-overview?orgId=1&refresh=5s&kiosk=tv&theme=dark';
            container.innerHTML = `
                <div class="mb-2 flex justify-between items-center bg-green-50 border border-green-300 rounded p-2">
                    <span class="text-green-700 text-sm">
                        <i class="fas fa-check-circle mr-1"></i>Grafana Authenticated
                    </span>
                    <div class="space-x-2">
                        <button onclick="secureMonitoring.refreshGrafana()" 
                                class="text-green-600 hover:text-green-800 text-sm">
                            <i class="fas fa-sync-alt mr-1"></i>Refresh
                        </button>
                        <button onclick="secureMonitoring.logoutGrafana()" 
                                class="text-red-600 hover:text-red-800 text-sm">
                            <i class="fas fa-sign-out-alt mr-1"></i>Logout
                        </button>
                    </div>
                </div>
                <iframe 
                    src="${dashboardUrl}" 
                    allowfullscreen
                    style="width: 100%; height: 500px; border: none; border-radius: 4px;">
                </iframe>
            `;
        }
    }
    
    // RabbitMQ Secure Embedding  
    showRabbitMQLoginPrompt() {
        const container = document.getElementById('rabbitmq-iframe-container');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-12 bg-orange-50 border border-orange-300 rounded">
                    <i class="fas fa-shield-alt text-4xl text-orange-500 mb-4"></i>
                    <h3 class="text-lg font-semibold text-orange-800 mb-2">Secure RabbitMQ Access</h3>
                    <p class="text-orange-700 text-sm mb-4">
                        Click below to securely authenticate with RabbitMQ Management.<br>
                        Your credentials are managed server-side and never exposed to the browser.
                    </p>
                    <button id="rabbitmq-auth-btn" onclick="secureMonitoring.authenticateRabbitMQ()" 
                            class="bg-orange-500 text-white px-6 py-3 rounded hover:bg-orange-600 font-medium">
                        <i class="fas fa-sign-in-alt mr-2"></i>Authenticate with RabbitMQ
                    </button>
                    <p class="text-xs text-orange-600 mt-3">
                        <i class="fas fa-lock mr-1"></i>Session expires in 1 hour
                    </p>
                </div>
            `;
        }
    }
    
    showAuthenticatedRabbitMQ() {
        const container = document.getElementById('rabbitmq-iframe-container');
        if (container) {
            const managementUrl = '/api/proxy/rabbitmq/';
            container.innerHTML = `
                <div class="mb-2 flex justify-between items-center bg-green-50 border border-green-300 rounded p-2">
                    <span class="text-green-700 text-sm">
                        <i class="fas fa-check-circle mr-1"></i>RabbitMQ Authenticated
                    </span>
                    <div class="space-x-2">
                        <button onclick="secureMonitoring.refreshRabbitMQ()" 
                                class="text-green-600 hover:text-green-800 text-sm">
                            <i class="fas fa-sync-alt mr-1"></i>Refresh
                        </button>
                        <button onclick="secureMonitoring.logoutRabbitMQ()" 
                                class="text-red-600 hover:text-red-800 text-sm">
                            <i class="fas fa-sign-out-alt mr-1"></i>Logout
                        </button>
                    </div>
                </div>
                <iframe 
                    src="${managementUrl}" 
                    allowfullscreen
                    style="width: 100%; height: 500px; border: none; border-radius: 4px;">
                </iframe>
            `;
        }
    }
    
    // Refresh Methods
    refreshGrafana() {
        if (this.authStatus.grafana) {
            this.showAuthenticatedGrafana();
        }
    }
    
    refreshRabbitMQ() {
        if (this.authStatus.rabbitmq) {
            this.showAuthenticatedRabbitMQ();
        }
    }
    
    // Logout Methods
    async logoutGrafana() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin'
            });
            this.authStatus.grafana = false;
            this.showGrafanaLoginPrompt();
            this.showSuccess('Logged out from Grafana');
        } catch (error) {
            this.showError('Logout failed: ' + error.message);
        }
    }
    
    async logoutRabbitMQ() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin'
            });
            this.authStatus.rabbitmq = false;
            this.showRabbitMQLoginPrompt();
            this.showSuccess('Logged out from RabbitMQ');
        } catch (error) {
            this.showError('Logout failed: ' + error.message);
        }
    }
    
    // Auth Indicators
    updateAuthIndicators() {
        // Update header indicators
        const authIndicators = document.getElementById('auth-indicators');
        if (authIndicators) {
            const grafanaStatus = this.authStatus.grafana ? 'authenticated' : 'not authenticated';
            const rabbitmqStatus = this.authStatus.rabbitmq ? 'authenticated' : 'not authenticated';
            
            authIndicators.innerHTML = `
                <div class="flex space-x-4 text-xs">
                    <span class="flex items-center ${this.authStatus.grafana ? 'text-green-600' : 'text-gray-500'}">
                        <i class="fas fa-chart-bar mr-1"></i>Grafana: ${grafanaStatus}
                    </span>
                    <span class="flex items-center ${this.authStatus.rabbitmq ? 'text-green-600' : 'text-gray-500'}">
                        <i class="fas fa-envelope mr-1"></i>RabbitMQ: ${rabbitmqStatus}
                    </span>
                </div>
            `;
        }
    }
    
    // Auto-refresh functionality
    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        this.autoRefreshInterval = setInterval(() => {
            this.refreshTimer--;
            const timerElement = document.getElementById('refresh-timer');
            if (timerElement) {
                timerElement.textContent = this.refreshTimer;
            }
            
            if (this.refreshTimer <= 0) {
                this.refreshTimer = 30;
                // Only refresh the authenticated iframes, not the whole page
                if (this.authStatus.grafana) {
                    this.refreshGrafana();
                }
                if (this.authStatus.rabbitmq) {
                    this.refreshRabbitMQ();
                }
            }
        }, 1000);
    }
    
    // Utility Methods
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
                ${message}
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    setupEventListeners() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkAuthStatus();
            }
        });
        
        // Handle window focus
        window.addEventListener('focus', () => {
            this.checkAuthStatus();
        });
    }
    
    // Cleanup on page unload
    cleanup() {
        if (this.authCheckInterval) {
            clearInterval(this.authCheckInterval);
        }
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }
}

// Initialize secure monitoring when DOM is loaded
let secureMonitoring;

document.addEventListener('DOMContentLoaded', () => {
    secureMonitoring = new SecureMonitoring();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (secureMonitoring) {
        secureMonitoring.cleanup();
    }
});

// Expose for inline onclick handlers (for tab switching)
function showTab(tabName) {
    if (secureMonitoring) {
        secureMonitoring.showTab(tabName);
    }
}