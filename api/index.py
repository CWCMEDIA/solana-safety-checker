#!/usr/bin/env python3
"""
Vercel serverless function entry point for Solana Safety Checker
"""

import os
import sys
import json
import base64
from http.server import BaseHTTPRequestHandler
from io import BytesIO

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sol_safety_check.cli import fetch_all_data, assess_token_risk
from sol_safety_check.utils import validate_solana_address
from sol_safety_check.datasources.dexscreener import DexScreenerClient

# Password protection
SITE_PASSWORD = "LetsHope"

class VercelHandler:
    def __init__(self, request, client_address, server=None):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.rfile = BytesIO(request.get('body', b''))
        self.wfile = BytesIO()
        self.headers = request.get('headers', {})
        self.path = request.get('path', '/')
        self.command = request.get('method', 'GET')
    
    def check_auth(self):
        """Check if user is authenticated"""
        # For the main page, we'll use a simple cookie-based approach
        # Check if the request has the auth cookie
        cookie_header = self.headers.get('Cookie', '')
        if 'authenticated=true' in cookie_header:
            return True
        
        # Check for custom auth header from JavaScript API calls
        auth_header = self.headers.get('X-Auth-Token')
        if auth_header == 'authenticated':
            return True
        
        # Fallback to basic auth for API calls
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            try:
                encoded = auth_header.split(' ')[1]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)
                return password == SITE_PASSWORD
            except:
                return False
        return False
    
    def require_auth(self):
        """Require authentication for protected pages"""
        if not self.check_auth():
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_login_page().encode('utf-8'))
            return False
        return True
    
    def get_login_page(self):
        """Generate the login page HTML"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Solana Safety Checker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        
        .logo {
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .title {
            color: #333;
            margin-bottom: 30px;
            font-size: 1.5rem;
            font-weight: 300;
        }
        
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .login-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
        }
        
        .error-message {
            color: #e74c3c;
            margin-top: 15px;
            font-size: 14px;
            display: none;
        }
        
        .password-hint {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            color: #666;
            font-size: 14px;
        }
        
        .password-hint strong {
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🛡️</div>
        <h1 class="title">Solana Safety Checker</h1>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter password" required>
            </div>
            
            <button type="submit" class="login-btn">Login</button>
            
            <div class="error-message" id="errorMessage">
                Invalid password. Please try again.
            </div>
        </form>
        
        <div class="password-hint">
            <strong>Password:</strong> LetsHope
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('errorMessage');
            
            if (password === 'LetsHope') {
                // Set authentication cookie
                document.cookie = 'authenticated=true; path=/; max-age=3600'; // 1 hour
                
                // Redirect to main page
                window.location.href = '/';
            } else {
                errorDiv.style.display = 'block';
                document.getElementById('password').value = '';
                document.getElementById('password').focus();
            }
        });
        
        // Check if already authenticated
        if (document.cookie.includes('authenticated=true')) {
            window.location.href = '/';
        }
        
        // Focus on password input
        document.getElementById('password').focus();
    </script>
</body>
</html>'''
    
    def serve_index(self):
        """Serve the main HTML page"""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solana Safety Checker</title>
    <link rel="stylesheet" href="/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-content">
                <h1><i class="fas fa-shield-alt"></i> Solana Safety Checker</h1>
                <p>Professional token analysis and risk assessment</p>
            </div>
        </header>

        <nav class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('trending')">
                <i class="fas fa-fire"></i> Trending
            </button>
            <button class="tab-btn" onclick="switchTab('latest')">
                <i class="fas fa-clock"></i> Latest
            </button>
            <button class="tab-btn" onclick="switchTab('analyze')">
                <i class="fas fa-search"></i> Analyze
            </button>
        </nav>

        <main class="main-content">
            <!-- Trending Tokens Tab -->
            <div id="trending" class="tab-content active">
                <div class="section-header">
                    <h2><i class="fas fa-fire"></i> Trending Tokens</h2>
                    <p>Most popular and actively traded tokens right now</p>
                </div>
                <div id="trending-content" class="coins-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Loading trending tokens...</p>
                    </div>
                </div>
            </div>

            <!-- Latest Tokens Tab -->
            <div id="latest" class="tab-content">
                <div class="section-header">
                    <h2><i class="fas fa-clock"></i> Latest Tokens</h2>
                    <p>Newly created tokens on Solana</p>
                </div>
                <div id="latest-content" class="coins-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Loading latest tokens...</p>
                    </div>
                </div>
            </div>

            <!-- Analysis Tab -->
            <div id="analyze" class="tab-content">
                <div class="section-header">
                    <h2><i class="fas fa-search"></i> Token Analysis</h2>
                    <p>Analyze any Solana token for safety and risk factors</p>
                </div>
                
                <div class="analysis-form">
                    <div class="input-group">
                        <label for="token-address">Token Address</label>
                        <div class="input-with-button">
                            <input type="text" id="token-address" placeholder="Enter Solana token address...">
                            <button type="button" id="paste-btn" onclick="pasteFromClipboard()">
                                <i class="fas fa-paste"></i> Paste
                            </button>
                        </div>
                    </div>
                    
                    <div class="data-sources">
                        <h3>Data Sources</h3>
                        <div class="source-cards">
                            <div class="source-card active" data-source="dexscreener">
                                <i class="fas fa-chart-line"></i>
                                <span>DEX Screener</span>
                            </div>
                            <div class="source-card active" data-source="birdeye">
                                <i class="fas fa-eye"></i>
                                <span>Birdeye</span>
                            </div>
                            <div class="source-card" data-source="rugcheck">
                                <i class="fas fa-shield-alt"></i>
                                <span>RugCheck</span>
                            </div>
                            <div class="source-card" data-source="pumpfun">
                                <i class="fas fa-rocket"></i>
                                <span>Pump.fun</span>
                            </div>
                            <div class="source-card active" data-source="solana_chain">
                                <i class="fas fa-link"></i>
                                <span>Solana Chain</span>
                            </div>
                        </div>
                    </div>
                    
                    <button type="button" id="analyzeBtn" onclick="analyzeToken()">
                        <i class="fas fa-search"></i> Analyze Token
                    </button>
                </div>
                
                <div id="results" class="analysis-results hidden">
                    <!-- Results will be populated here -->
                </div>
                
                <div id="error" class="error hidden">
                    <div class="error-content" id="errorContent"></div>
                </div>
            </div>
        </main>
    </div>

    <script src="/script.js"></script>
</body>
</html>'''
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html
        }
    
    def serve_css(self):
        """Serve CSS styles"""
        css = '''/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
.header {
    text-align: center;
    margin-bottom: 40px;
    color: white;
}

.header-content h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.header-content p {
    font-size: 1.1rem;
    opacity: 0.9;
}

/* Navigation */
.nav-tabs {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 40px;
    flex-wrap: wrap;
}

.tab-btn {
    padding: 12px 24px;
    border: none;
    background: rgba(255,255,255,0.2);
    color: white;
    border-radius: 25px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.tab-btn:hover {
    background: rgba(255,255,255,0.3);
    transform: translateY(-2px);
}

.tab-btn.active {
    background: rgba(255,255,255,0.9);
    color: #667eea;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.tab-btn i {
    margin-right: 8px;
}

/* Tab content */
.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.section-header {
    text-align: center;
    margin-bottom: 30px;
    color: white;
}

.section-header h2 {
    font-size: 2rem;
    margin-bottom: 10px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.section-header p {
    font-size: 1.1rem;
    opacity: 0.9;
}

/* Coins grid */
.coins-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.coin-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: all 0.3s ease;
    border: 1px solid rgba(255,255,255,0.2);
}

.coin-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
}

.coin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.coin-symbol {
    font-size: 1.3rem;
    font-weight: bold;
    color: #333;
}

.coin-name {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 10px;
}

.coin-price {
    font-size: 1.2rem;
    font-weight: bold;
    color: #667eea;
}

.coin-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
}

.stat {
    text-align: center;
}

.stat-label {
    font-size: 0.8rem;
    color: #666;
    margin-bottom: 5px;
}

.stat-value {
    font-size: 1rem;
    font-weight: bold;
    color: #333;
}

.change-positive {
    color: #28a745;
}

.change-negative {
    color: #dc3545;
}

/* Analysis form */
.analysis-form {
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.input-group {
    margin-bottom: 25px;
}

.input-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #333;
}

.input-with-button {
    display: flex;
    gap: 10px;
}

.input-with-button input {
    flex: 1;
    padding: 12px 15px;
    border: 2px solid #e1e5e9;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s ease;
}

.input-with-button input:focus {
    outline: none;
    border-color: #667eea;
}

.input-with-button button {
    padding: 12px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.3s ease;
}

.input-with-button button:hover {
    background: #5a6fd8;
}

.data-sources {
    margin-bottom: 25px;
}

.data-sources h3 {
    margin-bottom: 15px;
    color: #333;
}

.source-cards {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.source-card {
    padding: 10px 15px;
    border: 2px solid #e1e5e9;
    border-radius: 8px;
    cursor: pointer;
    text-align: center;
    transition: all 0.3s ease;
    background: white;
}

.source-card:hover {
    border-color: #667eea;
    background: #f8f9ff;
}

.source-card.active {
    border-color: #667eea;
    background: #f0f4ff;
}

.source-card i {
    margin-right: 5px;
    color: #667eea;
}

#analyzeBtn {
    width: 100%;
    padding: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s ease;
}

#analyzeBtn:hover {
    transform: translateY(-2px);
}

#analyzeBtn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

/* Analysis results */
.analysis-results {
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.risk-score {
    font-size: 2rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
    padding: 20px;
    border-radius: 10px;
}

.risk-score.low {
    color: #28a745;
    background: #d4edda;
}

.risk-score.medium {
    color: #ffc107;
    background: #fff3cd;
}

.risk-score.high {
    color: #dc3545;
    background: #f8d7da;
}

.verdict {
    font-size: 1.5rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 8px;
}

.verdict.safe {
    color: #28a745;
    background: #d4edda;
}

.verdict.caution {
    color: #ffc107;
    background: #fff3cd;
}

.verdict.danger {
    color: #dc3545;
    background: #f8d7da;
}

.summary {
    margin-bottom: 20px;
}

.summary h4 {
    margin-bottom: 10px;
    color: #333;
}

.summary p {
    color: #666;
    line-height: 1.6;
}

/* Error state */
.error {
    background: #f8d7da;
    color: #721c24;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #f5c6cb;
    margin-bottom: 20px;
}

.error-content {
    text-align: center;
}

/* Loading state */
.loading-state {
    text-align: center;
    padding: 40px;
    color: white;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255,255,255,0.3);
    border-top: 4px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Utility classes */
.hidden {
    display: none !important;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    .header-content h1 {
        font-size: 2rem;
    }
    
    .nav-tabs {
        flex-direction: column;
        align-items: center;
    }
    
    .tab-btn {
        width: 100%;
        max-width: 300px;
    }
    
    .coins-grid {
        grid-template-columns: 1fr;
    }
    
    .coin-stats {
        grid-template-columns: 1fr;
    }
    
    .source-cards {
        justify-content: center;
    }
    
    .input-with-button {
        flex-direction: column;
    }
}'''
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/css'},
            'body': css
        }
    
    def serve_js(self):
        """Serve JavaScript"""
        js = '''// Tab switching
let currentTab = 'trending';

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    currentTab = tabName;
    
    // Load data for the tab
    if (tabName === 'trending') {
        loadTrendingCoins();
    } else if (tabName === 'latest') {
        loadLatestCoins();
    }
}

// Source card toggling
document.addEventListener('DOMContentLoaded', function() {
    const sourceCards = document.querySelectorAll('.source-card');
    sourceCards.forEach(card => {
        card.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });
    
    // Load trending coins on page load
    loadTrendingCoins();
});

// Trending and Latest coins
async function loadTrendingCoins() {
    const contentDiv = document.getElementById('trending-content');
    contentDiv.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading trending tokens...</p></div>';
    
    try {
        const response = await fetch('/trending', {
            headers: {
                'X-Auth-Token': 'authenticated'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            displayCoins(data.coins, 'trending-content');
        } else {
            contentDiv.innerHTML = `<div class="error">Failed to load trending coins: ${data.error}</div>`;
        }
    } catch (error) {
        contentDiv.innerHTML = `<div class="error">Network error: ${error.message}</div>`;
    }
}

async function loadLatestCoins() {
    const contentDiv = document.getElementById('latest-content');
    contentDiv.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading latest tokens...</p></div>';
    
    try {
        const response = await fetch('/latest', {
            headers: {
                'X-Auth-Token': 'authenticated'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            displayCoins(data.coins, 'latest-content');
        } else {
            contentDiv.innerHTML = `<div class="error">Failed to load latest coins: ${data.error}</div>`;
        }
    } catch (error) {
        contentDiv.innerHTML = `<div class="error">Network error: ${error.message}</div>`;
    }
}

function displayCoins(coins, containerId) {
    const container = document.getElementById(containerId);
    
    if (coins.length === 0) {
        container.innerHTML = '<div class="loading-state"><p>No coins available at the moment.</p></div>';
        return;
    }
    
    const html = coins.map(coin => {
        // Always use the name as the main title if it exists and is different from symbol
        // For tokens where name and symbol are the same, just show the symbol
        let mainTitle, subtitle;
        
        if (coin.name && coin.name.length > 0 && coin.name !== coin.symbol) {
            mainTitle = coin.name;
            subtitle = coin.symbol;
        } else {
            mainTitle = coin.symbol;
            subtitle = '';
        }
        
        return `
        <div class="coin-card" onclick="analyzeCoin('${coin.address}')">
            <div class="coin-header">
                <div class="coin-symbol">${mainTitle}</div>
                <div class="coin-price">$${formatPrice(coin.price)}</div>
            </div>
            ${subtitle ? `<div class="coin-name">${subtitle}</div>` : ''}
            <div class="coin-stats">
                <div class="stat">
                    <div class="stat-label">24h Change</div>
                    <div class="stat-value ${coin.change24h >= 0 ? 'change-positive' : 'change-negative'}">
                        ${coin.change24h >= 0 ? '+' : ''}${coin.change24h.toFixed(2)}%
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Volume 24h</div>
                    <div class="stat-value">$${formatNumber(coin.volume24h)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Liquidity</div>
                    <div class="stat-value">$${formatNumber(coin.liquidity)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">${coin.age ? 'Age' : 'Address'}</div>
                    <div class="stat-value">${coin.age || coin.address.substring(0, 8) + '...'}</div>
                </div>
            </div>
        </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

function formatPrice(price) {
    if (price < 0.000001) {
        return price.toExponential(2);
    } else if (price < 1) {
        return price.toFixed(6);
    } else {
        return price.toFixed(2);
    }
}

function formatNumber(num) {
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(1) + 'B';
    } else if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    } else {
        return num.toFixed(0);
    }
}

function analyzeCoin(address) {
    switchTab('analyze');
    document.getElementById('token-address').value = address;
}

function pasteFromClipboard() {
    navigator.clipboard.readText().then(text => {
        document.getElementById('token-address').value = text;
    }).catch(err => {
        console.error('Failed to read clipboard: ', err);
    });
}

async function analyzeToken() {
    const tokenAddress = document.getElementById('token-address').value.trim();
    if (!tokenAddress) {
        showError('Please enter a token address');
        return;
    }
    
    const selectedSources = Array.from(document.querySelectorAll('.source-card.active'))
        .map(card => card.dataset.source);
    
    const fastMode = false; // Always use full analysis
    
    // Show loading state
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('analyzeBtn').disabled = true;
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Token': 'authenticated'
            },
            body: JSON.stringify({
                tokenAddress: tokenAddress,
                providers: selectedSources,
                fastMode: fastMode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAnalysisResults(data.report);
        } else {
            showError(data.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Network error: ' + error.message);
    } finally {
        document.getElementById('analyzeBtn').disabled = false;
    }
}

function displayAnalysisResults(report) {
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    
    // Hide error, show results
    errorDiv.classList.add('hidden');
    resultsDiv.classList.remove('hidden');
    
    const riskScore = report.risk_score;
    const verdict = report.verdict;
    
    let riskClass = 'high';
    if (riskScore <= 30) riskClass = 'low';
    else if (riskScore <= 70) riskClass = 'medium';
    
    let verdictClass = 'danger';
    if (verdict.toLowerCase().includes('safe')) verdictClass = 'safe';
    else if (verdict.toLowerCase().includes('caution')) verdictClass = 'caution';
    
    resultsDiv.innerHTML = `
        <div class="risk-score ${riskClass}">
            Risk Score: ${riskScore}/100
        </div>
        <div class="verdict ${verdictClass}">
            ${verdict}
        </div>
        <div class="summary">
            <h4>Summary</h4>
            <p>${report.summary}</p>
        </div>
    `;
}

function showError(error) {
    const errorDiv = document.getElementById('error');
    const resultsDiv = document.getElementById('results');
    
    // Hide results, show error
    resultsDiv.classList.add('hidden');
    errorDiv.classList.remove('hidden');
    
    document.getElementById('errorContent').textContent = error;
}'''
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/javascript'},
            'body': js
        }
    
    def get_trending_coins(self):
        """Get trending coins from DEX Screener"""
        try:
            import asyncio
            
            def fetch_trending():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    client = DexScreenerClient()
                    trending_tokens = loop.run_until_complete(client.get_trending_tokens(20))
                    
                    return {
                        'success': True,
                        'coins': trending_tokens
                    }
                finally:
                    loop.close()
            
            result = fetch_trending()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
            
        except Exception as e:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'error': str(e)})
            }
    
    def get_latest_coins(self):
        """Get latest coins from DEX Screener"""
        try:
            import asyncio
            
            def fetch_latest():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    client = DexScreenerClient()
                    latest_tokens = loop.run_until_complete(client.get_latest_tokens(20))
                    
                    return {
                        'success': True,
                        'coins': latest_tokens
                    }
                finally:
                    loop.close()
            
            result = fetch_latest()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
            
        except Exception as e:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'error': str(e)})
            }
    
    def analyze_token(self):
        """Handle token analysis request"""
        try:
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            address = data.get('tokenAddress', '').strip()
            providers = data.get('providers', ['dexscreener', 'birdeye', 'solana_chain'])
            
            if not address:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'success': False, 'error': 'Token address is required'})
                }
            
            # Validate address
            if not validate_solana_address(address):
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'success': False, 'error': 'Invalid Solana address format'})
                }
            
            # Fetch data and analyze
            import asyncio
            
            def analyze():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Fetch data
                    data = loop.run_until_complete(fetch_all_data(address, providers, fast=False))
                    
                    # Assess risk
                    report = assess_token_risk(data)
                    
                    return {
                        'success': True,
                        'report': report.model_dump()
                    }
                finally:
                    loop.close()
            
            result = analyze()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'error': str(e)})
            }

def handler(request):
    """Vercel serverless function handler"""
    try:
        handler_instance = VercelHandler(request, None)
        
        # Check authentication first
        auth_result = handler_instance.require_auth()
        if auth_result:
            return auth_result
        
        # Route the request
        if request.get('method') == 'GET':
            path = request.get('path', '/')
            if path == '/':
                return handler_instance.serve_index()
            elif path == '/style.css':
                return handler_instance.serve_css()
            elif path == '/script.js':
                return handler_instance.serve_js()
            elif path == '/trending':
                return handler_instance.get_trending_coins()
            elif path == '/latest':
                return handler_instance.get_latest_coins()
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'text/plain'},
                    'body': 'Not Found'
                }
        elif request.get('method') == 'POST':
            path = request.get('path', '/')
            if path == '/analyze':
                return handler_instance.analyze_token()
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'text/plain'},
                    'body': 'Not Found'
                }
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'text/plain'},
                'body': 'Method Not Allowed'
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'Internal Server Error: {str(e)}'
        }
