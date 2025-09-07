#!/usr/bin/env python3
"""
Solana Safety Checker - Web GUI
A simple web-based interface for checking Solana token safety.
"""

import asyncio
import json
import os
import sys
import base64
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import webbrowser

# Add the sol_safety_check module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sol_safety_check.cli import fetch_all_data, assess_token_risk
from sol_safety_check.utils import validate_solana_address
from sol_safety_check.datasources.dexscreener import DexScreenerClient

# Password protection
SITE_PASSWORD = "LetsHope"


class SolSafetyCheckerHandler(BaseHTTPRequestHandler):
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

    def do_GET(self):
        """Handle GET requests"""
        # Check authentication for all routes except static files
        if self.path not in ['/style.css', '/script.js']:
            if not self.require_auth():
                return
        
        if self.path == '/':
            self.serve_index()
        elif self.path == '/style.css':
            self.serve_css()
        elif self.path == '/script.js':
            self.serve_js()
        elif self.path == '/trending':
            self.get_trending_coins()
        elif self.path == '/latest':
            self.get_latest_coins()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        # Check authentication for all POST routes
        if not self.require_auth():
            return
            
        if self.path == '/analyze':
            self.analyze_token()
        else:
            self.send_error(404)
    
    def serve_index(self):
        """Serve the main HTML page"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solana Safety Checker Pro</title>
    <link rel="stylesheet" href="/style.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app">
        <!-- Navigation -->
        <nav class="navbar">
            <div class="nav-brand">
                <i class="fas fa-shield-alt"></i>
                <span>Solana Safety Checker Pro</span>
            </div>
            <div class="nav-links">
                <a href="#analyze" class="nav-link active" data-tab="analyze">
                    <i class="fas fa-search"></i> Analyze
                </a>
                <a href="#trending" class="nav-link" data-tab="trending">
                    <i class="fas fa-fire"></i> Trending
                </a>
                <a href="#latest" class="nav-link" data-tab="latest">
                    <i class="fas fa-clock"></i> Latest
                </a>
            </div>
        </nav>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Analyze Tab -->
            <div id="analyze-tab" class="tab-content active">
                <div class="hero-section">
                    <h1>🔍 Comprehensive Token Safety Analysis</h1>
                    <p>Professional-grade risk assessment for Solana memecoins and tokens</p>
                </div>

                <div class="analysis-card">
                    <form id="analysisForm">
                        <div class="form-section">
                            <h3><i class="fas fa-coins"></i> Token Information</h3>
                            <div class="form-group">
                                <label for="tokenAddress">Token Address</label>
                                <div class="input-group">
                                    <input type="text" id="tokenAddress" placeholder="Enter Solana token mint address" required>
                                    <button type="button" class="paste-btn" onclick="pasteFromClipboard()">
                                        <i class="fas fa-paste"></i>
                                    </button>
                                </div>
                                <div class="quick-buttons">
                                    <button type="button" class="quick-btn" onclick="setToken('So11111111111111111111111111111111111111112')">
                                        <i class="fas fa-sun"></i> SOL
                                    </button>
                                    <button type="button" class="quick-btn" onclick="setToken('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')">
                                        <i class="fas fa-dollar-sign"></i> USDC
                                    </button>
                                    <button type="button" class="quick-btn" onclick="setToken('Fv73EXJBRfctJzLVC3P7uQP6er6JU8b4KtDr4LQFpump')">
                                        <i class="fas fa-flask"></i> Test
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="form-section">
                            <h3><i class="fas fa-database"></i> Data Sources</h3>
                            <div class="sources-grid">
                                <label class="source-item">
                                    <input type="checkbox" id="dexscreener" checked>
                                    <div class="source-card">
                                        <i class="fas fa-chart-line"></i>
                                        <span>DEX Screener</span>
                                        <small>Free</small>
                                    </div>
                                </label>
                                <label class="source-item">
                                    <input type="checkbox" id="birdeye" checked>
                                    <div class="source-card">
                                        <i class="fas fa-eye"></i>
                                        <span>Birdeye</span>
                                        <small>API Key</small>
                                    </div>
                                </label>
                                <label class="source-item">
                                    <input type="checkbox" id="rugcheck">
                                    <div class="source-card">
                                        <i class="fas fa-shield-virus"></i>
                                        <span>RugCheck</span>
                                        <small>JWT</small>
                                    </div>
                                </label>
                                <label class="source-item">
                                    <input type="checkbox" id="pumpfun" checked>
                                    <div class="source-card">
                                        <i class="fas fa-rocket"></i>
                                        <span>Pump.fun</span>
                                        <small>API Key</small>
                                    </div>
                                </label>
                                <label class="source-item">
                                    <input type="checkbox" id="solana_chain" checked>
                                    <div class="source-card">
                                        <i class="fas fa-link"></i>
                                        <span>Solana Chain</span>
                                        <small>RPC</small>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <div class="form-section">
                            <h3><i class="fas fa-cog"></i> Options</h3>
                            <div class="options-grid">
                                <label class="option-item">
                                    <input type="checkbox" id="fastMode" checked>
                                    <span>Fast Mode</span>
                                    <small>Skip heavy calls for quick analysis</small>
                                </label>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" id="analyzeBtn" class="btn-primary">
                                <i class="fas fa-search"></i> Analyze Token
                            </button>
                            <button type="button" onclick="clearResults()" class="btn-secondary">
                                <i class="fas fa-trash"></i> Clear
                            </button>
                        </div>
                    </form>
                </div>

                <div id="loading" class="loading hidden">
                    <div class="loading-content">
                        <div class="spinner"></div>
                        <h3>Analyzing Token...</h3>
                        <p>Fetching data from multiple sources</p>
                    </div>
                </div>

                <div id="results" class="results hidden">
                    <div id="resultsContent"></div>
                </div>

                <div id="error" class="error hidden">
                    <div class="error-content">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Analysis Error</h3>
                        <div id="errorContent"></div>
                    </div>
                </div>
            </div>

            <!-- Trending Tab -->
            <div id="trending-tab" class="tab-content">
                <div class="hero-section">
                    <h1>🔥 Trending Tokens</h1>
                    <p>Most popular and actively traded tokens right now</p>
                </div>
                <div id="trending-content" class="coins-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Loading trending tokens...</p>
                    </div>
                </div>
            </div>

            <!-- Latest Tab -->
            <div id="latest-tab" class="tab-content">
                <div class="hero-section">
                    <h1>🆕 Latest Tokens</h1>
                    <p>Newly created tokens and recent launches</p>
                </div>
                <div id="latest-content" class="coins-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Loading latest tokens...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-content">
                <p>Built with ❤️ for the Solana community</p>
                <div class="footer-links">
                    <a href="https://github.com" target="_blank"><i class="fab fa-github"></i> GitHub</a>
                    <a href="#" onclick="showAbout()"><i class="fas fa-info-circle"></i> About</a>
                </div>
            </div>
        </footer>
    </div>

    <!-- About Modal -->
    <div id="aboutModal" class="modal hidden">
        <div class="modal-content">
            <div class="modal-header">
                <h2>About Solana Safety Checker Pro</h2>
                <button class="close-btn" onclick="closeAbout()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Professional-grade token safety analysis for Solana memecoins and tokens.</p>
                <h3>Features:</h3>
                <ul>
                    <li>Comprehensive risk assessment</li>
                    <li>Multiple data source integration</li>
                    <li>Real-time trending and latest tokens</li>
                    <li>Professional analysis reports</li>
                </ul>
            </div>
        </div>
    </div>

    <script src="/script.js"></script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_css(self):
        """Serve the CSS styles"""
        css = """
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
    line-height: 1.6;
}

.app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Navigation */
.navbar {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.nav-brand {
    display: flex;
    align-items: center;
    font-size: 1.5rem;
    font-weight: 700;
    color: #667eea;
}

.nav-brand i {
    margin-right: 0.5rem;
    font-size: 1.8rem;
}

.nav-links {
    display: flex;
    gap: 2rem;
}

.nav-link {
    display: flex;
    align-items: center;
    text-decoration: none;
    color: #666;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.nav-link:hover {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
}

.nav-link.active {
    background: #667eea;
    color: white;
}

.nav-link i {
    margin-right: 0.5rem;
}

/* Main Content */
.main-content {
    flex: 1;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* Hero Section */
.hero-section {
    text-align: center;
    margin-bottom: 3rem;
    color: white;
}

.hero-section h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    background: linear-gradient(45deg, #fff, #f0f0f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-section p {
    font-size: 1.2rem;
    opacity: 0.9;
    max-width: 600px;
    margin: 0 auto;
}

/* Analysis Card */
.analysis-card {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
}

.form-section {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #eee;
}

.form-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.form-section h3 {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
    color: #333;
    font-size: 1.3rem;
}

.form-section h3 i {
    margin-right: 0.5rem;
    color: #667eea;
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #555;
}

.input-group {
    display: flex;
    gap: 0.5rem;
}

.input-group input {
    flex: 1;
    padding: 1rem;
    border: 2px solid #e1e5e9;
    border-radius: 12px;
    font-size: 1rem;
    transition: all 0.3s ease;
}

.input-group input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.paste-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 1rem;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.paste-btn:hover {
    background: #5a6fd8;
    transform: translateY(-2px);
}

.quick-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.quick-btn {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.quick-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* Sources Grid */
.sources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.source-item {
    cursor: pointer;
}

.source-item input {
    display: none;
}

.source-card {
    background: #f8f9fa;
    border: 2px solid #e1e5e9;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.source-card i {
    font-size: 2rem;
    color: #667eea;
    margin-bottom: 0.5rem;
}

.source-card span {
    font-weight: 600;
    color: #333;
}

.source-card small {
    color: #666;
    font-size: 0.8rem;
}

.source-item input:checked + .source-card {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border-color: #667eea;
}

.source-item input:checked + .source-card i,
.source-item input:checked + .source-card span,
.source-item input:checked + .source-card small {
    color: white;
}

/* Options Grid */
.options-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
}

.option-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.option-item:hover {
    background: #e9ecef;
}

.option-item input {
    margin-top: 0.2rem;
    transform: scale(1.2);
}

.option-item span {
    font-weight: 600;
    color: #333;
}

.option-item small {
    display: block;
    color: #666;
    font-size: 0.9rem;
    margin-top: 0.2rem;
}

/* Form Actions */
.form-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 2rem;
}

.btn-primary, .btn-secondary {
    padding: 1rem 2rem;
    border: none;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.btn-primary {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background: #5a6268;
    transform: translateY(-2px);
}

.btn-primary:disabled {
    background: #ccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

/* Loading States */
.loading, .loading-state {
    text-align: center;
    padding: 3rem;
}

.loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Results */
.results {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    margin-top: 2rem;
}

.verdict {
    font-size: 2rem;
    font-weight: bold;
    margin: 2rem 0;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.verdict.safe {
    background: linear-gradient(45deg, #d4edda, #c3e6cb);
    color: #155724;
    border: 2px solid #c3e6cb;
}

.verdict.caution {
    background: linear-gradient(45deg, #fff3cd, #ffeaa7);
    color: #856404;
    border: 2px solid #ffeaa7;
}

.verdict.danger {
    background: linear-gradient(45deg, #f8d7da, #f5c6cb);
    color: #721c24;
    border: 2px solid #f5c6cb;
}

/* Error */
.error {
    background: #f8d7da;
    border: 2px solid #f5c6cb;
    border-radius: 15px;
    padding: 2rem;
    margin-top: 2rem;
}

.error-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    text-align: center;
}

.error-content i {
    font-size: 3rem;
    color: #e53e3e;
}

.error-content h3 {
    color: #e53e3e;
    font-size: 1.5rem;
}

/* Coins Grid */
.coins-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 2rem;
}

.coin-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    cursor: pointer;
}

.coin-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.coin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.coin-symbol {
    font-size: 1.5rem;
    font-weight: 700;
    color: #333;
}

.coin-price {
    font-size: 1.2rem;
    font-weight: 600;
    color: #667eea;
}

.coin-name {
    color: #666;
    margin-bottom: 1rem;
}

.coin-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

.stat {
    text-align: center;
}

.stat-label {
    font-size: 0.8rem;
    color: #666;
    margin-bottom: 0.2rem;
}

.stat-value {
    font-weight: 600;
    color: #333;
}

.change-positive {
    color: #28a745;
}

.change-negative {
    color: #dc3545;
}

/* Footer */
.footer {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 2rem;
    text-align: center;
    color: white;
    margin-top: auto;
}

.footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.footer-links {
    display: flex;
    gap: 2rem;
}

.footer-links a {
    color: white;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.3s ease;
}

.footer-links a:hover {
    color: #f0f0f0;
    transform: translateY(-2px);
}

/* Modal */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
}

.modal-content {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
}

.close-btn {
    background: none;
    border: none;
    font-size: 2rem;
    cursor: pointer;
    color: #666;
}

.close-btn:hover {
    color: #333;
}

.modal-body ul {
    margin-left: 1.5rem;
    margin-top: 1rem;
}

.modal-body li {
    margin-bottom: 0.5rem;
}

/* Utility Classes */
.hidden {
    display: none !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
    }
    
    .nav-links {
        gap: 1rem;
    }
    
    .hero-section h1 {
        font-size: 2rem;
    }
    
    .main-content {
        padding: 1rem;
    }
    
    .analysis-card {
        padding: 1.5rem;
    }
    
    .sources-grid {
        grid-template-columns: 1fr;
    }
    
    .form-actions {
        flex-direction: column;
    }
    
    .footer-content {
        flex-direction: column;
        gap: 1rem;
    }
    
    .coins-grid {
        grid-template-columns: 1fr;
    }
}
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css.encode())
    
    def serve_js(self):
        """Serve the JavaScript"""
        js = """
// Global state
let currentTab = 'analyze';

// Tab switching
function switchTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    currentTab = tabName;
    
    // Load data for trending/latest tabs
    if (tabName === 'trending') {
        loadTrendingCoins();
    } else if (tabName === 'latest') {
        loadLatestCoins();
    }
}

// Token management
function setToken(address) {
    document.getElementById('tokenAddress').value = address;
}

async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        document.getElementById('tokenAddress').value = text;
    } catch (err) {
        alert('Unable to paste from clipboard. Please paste manually.');
    }
}

function clearResults() {
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('loading').classList.add('hidden');
}

// Analysis functions
async function analyzeToken(event) {
    event.preventDefault();
    
    const tokenAddress = document.getElementById('tokenAddress').value.trim();
    if (!tokenAddress) {
        alert('Please enter a token address');
        return;
    }
    
    // Get selected providers
    const providers = [];
    if (document.getElementById('dexscreener').checked) providers.push('dexscreener');
    if (document.getElementById('birdeye').checked) providers.push('birdeye');
    if (document.getElementById('rugcheck').checked) providers.push('rugcheck');
    if (document.getElementById('pumpfun').checked) providers.push('pumpfun');
    if (document.getElementById('solana_chain').checked) providers.push('solana_chain');
    
    if (providers.length === 0) {
        alert('Please select at least one data source');
        return;
    }
    
    const fastMode = document.getElementById('fastMode').checked;
    
    // Show loading
    document.getElementById('loading').classList.remove('hidden');
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
                providers: providers,
                fastMode: fastMode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.results);
        } else {
            displayError(data.error);
        }
    } catch (error) {
        displayError('Network error: ' + error.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('analyzeBtn').disabled = false;
    }
}

function displayResults(results) {
    const resultsDiv = document.getElementById('resultsContent');
    
    let html = `
        <div class="verdict ${getVerdictClass(results.overall_score)}">
            ${results.verdict}
            <br>
            <small>Risk Score: ${results.overall_score}/100</small>
        </div>
        
        <h3><i class="fas fa-shield-alt"></i> Risk Assessment Details</h3>
        <div class="results-table">
            <table>
                <thead>
                    <tr>
                        <th>Rule</th>
                        <th>Score</th>
                        <th>Severity</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    results.notes.forEach(note => {
        const severityEmoji = getSeverityEmoji(note.severity);
        html += `
            <tr>
                <td>${note.rule_name}</td>
                <td class="score-cell">${note.score}</td>
                <td class="severity-cell">${severityEmoji} ${note.severity.toUpperCase()}</td>
                <td>${note.message}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        
        <div class="results-info">
            <h3><i class="fas fa-database"></i> Data Sources Used</h3>
            <p>${results.data_sources_used.join(', ')}</p>
        </div>
    `;
    
    if (results.warnings && results.warnings.length > 0) {
        html += `
            <div class="warnings">
                <h3><i class="fas fa-exclamation-triangle"></i> Warnings</h3>
                <ul>
                    ${results.warnings.map(warning => `<li>⚠️ ${warning}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    resultsDiv.innerHTML = html;
    document.getElementById('results').classList.remove('hidden');
}

function displayError(error) {
    document.getElementById('errorContent').textContent = error;
    document.getElementById('error').classList.remove('hidden');
}

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
        container.innerHTML = '<div class="no-data">No coins available at the moment.</div>';
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

function analyzeCoin(address) {
    // Switch to analyze tab
    switchTab('analyze');
    
    // Set the token address
    setToken(address);
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Utility functions
function getVerdictClass(score) {
    if (score <= 29) return 'safe';
    if (score <= 59) return 'caution';
    return 'danger';
}

function getSeverityEmoji(severity) {
    switch(severity) {
        case 'low': return '🟢';
        case 'medium': return '🟡';
        case 'high': return '🔴';
        default: return '⚪';
    }
}

function formatPrice(price) {
    if (price >= 1) {
        return price.toFixed(2);
    } else if (price >= 0.01) {
        return price.toFixed(4);
    } else {
        return price.toExponential(2);
    }
}

function formatNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(1) + 'B';
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(1) + 'M';
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(1) + 'K';
    } else {
        return num.toFixed(0);
    }
}

// Modal functions
function showAbout() {
    document.getElementById('aboutModal').classList.remove('hidden');
}

function closeAbout() {
    document.getElementById('aboutModal').classList.add('hidden');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Tab navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // Analysis form
    document.getElementById('analysisForm').addEventListener('submit', analyzeToken);
    
    // Modal close on outside click
    document.getElementById('aboutModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeAbout();
        }
    });
    
    // Load initial data
    loadTrendingCoins();
    loadLatestCoins();
});
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.wfile.write(js.encode())
    
    def get_trending_coins(self):
        """Get trending coins from DEX Screener"""
        try:
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
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def get_latest_coins(self):
        """Get latest coins from DEX Screener"""
        try:
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
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def analyze_token(self):
        """Handle token analysis request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            token_address = data.get('tokenAddress', '').strip()
            providers = data.get('providers', [])
            fast_mode = data.get('fastMode', False)
            
            if not token_address:
                self.send_json_response({'success': False, 'error': 'Token address is required'})
                return
            
            if not validate_solana_address(token_address):
                self.send_json_response({'success': False, 'error': 'Invalid Solana address format'})
                return
            
            if not providers:
                self.send_json_response({'success': False, 'error': 'At least one data source must be selected'})
                return
            
            # Run analysis in a separate thread
            def run_analysis():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Fetch data
                        data_result = loop.run_until_complete(fetch_all_data(token_address, providers, fast_mode))
                        
                        # Assess risk
                        report = assess_token_risk(data_result)
                        
                        # Convert to dict for JSON serialization
                        result = {
                            'mint_address': report.mint_address,
                            'overall_score': report.overall_score,
                            'verdict': report.verdict,
                            'risk_level': report.risk_level,
                            'notes': [note.model_dump() for note in report.notes],
                            'data_sources_used': report.data_sources_used,
                            'warnings': report.warnings,
                        }
                        
                        self.send_json_response({'success': True, 'results': result})
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    self.send_json_response({'success': False, 'error': str(e)})
            
            # Start analysis in background thread
            thread = threading.Thread(target=run_analysis)
            thread.daemon = True
            thread.start()
            
            # Wait for completion (with timeout)
            thread.join(timeout=60)  # 60 second timeout
            
            if thread.is_alive():
                self.send_json_response({'success': False, 'error': 'Analysis timeout - please try again'})
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'Server error: {str(e)}'})
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def start_server(port=8080):
    """Start the web server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SolSafetyCheckerHandler)
    
    print(f"🚀 Solana Safety Checker Web GUI")
    print(f"📱 Open your browser and go to: http://localhost:{port}")
    print(f"🛑 Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.shutdown()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Solana Safety Checker Web GUI')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--open-browser', action='store_true', help='Automatically open browser')
    
    args = parser.parse_args()
    
    if args.open_browser:
        # Open browser after a short delay
        def open_browser():
            import time
            time.sleep(1)
            webbrowser.open(f'http://localhost:{args.port}')
        
        threading.Thread(target=open_browser).start()
    
    start_server(args.port)


if __name__ == "__main__":
    main()
