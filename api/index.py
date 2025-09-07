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

# Password protection disabled for public deployment
# SITE_PASSWORD = "LetsHope"

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
        """Check if user is authenticated - disabled for public deployment"""
        return True  # Always return True to bypass authentication
    
    def require_auth(self):
        """Require authentication for protected pages - disabled for public deployment"""
        return None  # Always return None to bypass authentication
    
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
                <div id="trending-coins" class="coins-grid">
                    <div class="loading">Loading trending tokens...</div>
                </div>
            </div>

            <!-- Latest Tokens Tab -->
            <div id="latest" class="tab-content">
                <div class="section-header">
                    <h2><i class="fas fa-clock"></i> Latest Tokens</h2>
                    <p>Newly created tokens on Solana</p>
                </div>
                <div id="latest-coins" class="coins-grid">
                    <div class="loading">Loading latest tokens...</div>
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
                    
                    <button type="button" id="analyze-btn" onclick="analyzeToken()">
                        <i class="fas fa-search"></i> Analyze Token
                    </button>
                </div>
                
                <div id="analysis-results" class="analysis-results" style="display: none;">
                    <!-- Results will be populated here -->
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
        # Return a simplified CSS for Vercel
        css = '''
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .nav-tabs { display: flex; gap: 10px; margin-bottom: 30px; }
        .tab-btn { padding: 10px 20px; border: none; background: rgba(255,255,255,0.2); color: white; border-radius: 5px; cursor: pointer; }
        .tab-btn.active { background: rgba(255,255,255,0.3); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .coins-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .coin-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; }
        .coin-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
        .analysis-form { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .input-group { margin-bottom: 20px; }
        .input-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .input-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-with-button { display: flex; gap: 10px; }
        .input-with-button input { flex: 1; }
        .source-cards { display: flex; gap: 10px; flex-wrap: wrap; }
        .source-card { padding: 10px 15px; border: 2px solid #ddd; border-radius: 5px; cursor: pointer; text-align: center; }
        .source-card.active { border-color: #667eea; background: #f0f4ff; }
        #analyze-btn { background: #667eea; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .loading { text-align: center; padding: 40px; color: white; }
        '''
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/css'},
            'body': css
        }
    
    def serve_js(self):
        """Serve JavaScript"""
        js = '''
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
        
        function loadTrendingCoins() {
            fetch('/trending')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayCoins(data.coins, 'trending-coins');
                    }
                })
                .catch(error => {
                    console.error('Error loading trending coins:', error);
                });
        }
        
        function loadLatestCoins() {
            fetch('/latest')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayCoins(data.coins, 'latest-coins');
                    }
                })
                .catch(error => {
                    console.error('Error loading latest coins:', error);
                });
        }
        
        function displayCoins(coins, containerId) {
            const container = document.getElementById(containerId);
            
            if (coins.length === 0) {
                container.innerHTML = '<div class="loading">No coins available at the moment.</div>';
                return;
            }
            
            const html = coins.map(coin => {
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
            });
        }
        
        function analyzeToken() {
            const address = document.getElementById('token-address').value.trim();
            if (!address) {
                alert('Please enter a token address');
                return;
            }
            
            const selectedSources = Array.from(document.querySelectorAll('.source-card.active'))
                .map(card => card.dataset.source);
            
            const data = {
                address: address,
                providers: selectedSources
            };
            
            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayAnalysisResults(data.report);
                } else {
                    alert('Analysis failed: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Analysis failed: ' + error.message);
            });
        }
        
        function displayAnalysisResults(report) {
            const resultsDiv = document.getElementById('analysis-results');
            resultsDiv.style.display = 'block';
            
            const riskColor = report.risk_score <= 30 ? '#28a745' : 
                             report.risk_score <= 70 ? '#ffc107' : '#dc3545';
            
            resultsDiv.innerHTML = `
                <div class="analysis-results">
                    <h3>Analysis Results</h3>
                    <div class="risk-score" style="color: ${riskColor}">
                        Risk Score: ${report.risk_score}/100
                    </div>
                    <div class="verdict" style="color: ${riskColor}">
                        ${report.verdict}
                    </div>
                    <div class="summary">
                        <h4>Summary</h4>
                        <p>${report.summary}</p>
                    </div>
                </div>
            `;
        }
        
        // Load trending coins on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadTrendingCoins();
        });
        '''
        
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
            
            address = data.get('address', '').strip()
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
