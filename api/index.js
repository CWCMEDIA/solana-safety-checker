module.exports = (req, res) => {
  res.status(200).send(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solana Safety Checker</title>
    <style>
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
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-content">
                <h1>🛡️ Solana Safety Checker</h1>
                <p>Professional token analysis and risk assessment</p>
            </div>
        </header>

        <nav class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('trending')">
                🔥 Trending
            </button>
            <button class="tab-btn" onclick="switchTab('latest')">
                ⏰ Latest
            </button>
            <button class="tab-btn" onclick="switchTab('analyze')">
                🔍 Analyze
            </button>
        </nav>

        <main class="main-content">
            <div id="trending" class="tab-content active">
                <div class="section-header">
                    <h2>🔥 Trending Tokens</h2>
                    <p>Most popular and actively traded tokens right now</p>
                </div>
                <div id="trending-coins" class="coins-grid">
                    <div class="loading">Loading trending tokens...</div>
                </div>
            </div>

            <div id="latest" class="tab-content">
                <div class="section-header">
                    <h2>⏰ Latest Tokens</h2>
                    <p>Newly created tokens on Solana</p>
                </div>
                <div id="latest-coins" class="coins-grid">
                    <div class="loading">Loading latest tokens...</div>
                </div>
            </div>

            <div id="analyze" class="tab-content">
                <div class="section-header">
                    <h2>🔍 Token Analysis</h2>
                    <p>Analyze any Solana token for safety and risk factors</p>
                </div>
                
                <div class="analysis-form">
                    <div class="input-group">
                        <label for="token-address">Token Address</label>
                        <div class="input-with-button">
                            <input type="text" id="token-address" placeholder="Enter Solana token address...">
                            <button type="button" id="paste-btn" onclick="pasteFromClipboard()">
                                📋 Paste
                            </button>
                        </div>
                    </div>
                    
                    <div class="data-sources">
                        <h3>Data Sources</h3>
                        <div class="source-cards">
                            <div class="source-card active" data-source="dexscreener">
                                📈 DEX Screener
                            </div>
                            <div class="source-card active" data-source="birdeye">
                                👁️ Birdeye
                            </div>
                            <div class="source-card" data-source="rugcheck">
                                🛡️ RugCheck
                            </div>
                            <div class="source-card" data-source="pumpfun">
                                🚀 Pump.fun
                            </div>
                            <div class="source-card active" data-source="solana_chain">
                                🔗 Solana Chain
                            </div>
                        </div>
                    </div>
                    
                    <button type="button" id="analyze-btn" onclick="analyzeToken()">
                        🔍 Analyze Token
                    </button>
                </div>
                
                <div id="analysis-results" class="analysis-results" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
            </div>
        </main>
    </div>

    <script>
        let currentTab = 'trending';
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            currentTab = tabName;
            
            if (tabName === 'trending') {
                loadTrendingCoins();
            } else if (tabName === 'latest') {
                loadLatestCoins();
            }
        }
        
        function loadTrendingCoins() {
            const mockCoins = [
                {
                    address: 'So11111111111111111111111111111111111111112',
                    symbol: 'SOL',
                    name: 'Solana',
                    price: 100.50,
                    change24h: 5.2,
                    volume24h: 1000000000,
                    liquidity: 5000000000,
                    age: '4 years'
                },
                {
                    address: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                    symbol: 'USDC',
                    name: 'USD Coin',
                    price: 1.00,
                    change24h: 0.1,
                    volume24h: 2000000000,
                    liquidity: 10000000000,
                    age: '3 years'
                }
            ];
            displayCoins(mockCoins, 'trending-coins');
        }
        
        function loadLatestCoins() {
            const mockCoins = [
                {
                    address: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                    symbol: 'BONK',
                    name: 'Bonk',
                    price: 0.00001234,
                    change24h: 15.6,
                    volume24h: 50000000,
                    liquidity: 25000000,
                    age: '1 year'
                }
            ];
            displayCoins(mockCoins, 'latest-coins');
        }
        
        function displayCoins(coins, containerId) {
            const container = document.getElementById(containerId);
            
            if (coins.length === 0) {
                container.innerHTML = '<div class="loading">No coins available at the moment.</div>';
                return;
            }
            
            let html = '';
            for (let i = 0; i < coins.length; i++) {
                const coin = coins[i];
                let mainTitle, subtitle;
                
                if (coin.name && coin.name.length > 0 && coin.name !== coin.symbol) {
                    mainTitle = coin.name;
                    subtitle = coin.symbol;
                } else {
                    mainTitle = coin.symbol;
                    subtitle = '';
                }
                
                html += '<div class="coin-card" onclick="analyzeCoin(\\'' + coin.address + '\\')">';
                html += '<div class="coin-header">';
                html += '<div class="coin-symbol">' + mainTitle + '</div>';
                html += '<div class="coin-price">$' + formatPrice(coin.price) + '</div>';
                html += '</div>';
                if (subtitle) {
                    html += '<div class="coin-name">' + subtitle + '</div>';
                }
                html += '<div class="coin-stats">';
                html += '<div class="stat">';
                html += '<div class="stat-label">24h Change</div>';
                html += '<div class="stat-value ' + (coin.change24h >= 0 ? 'change-positive' : 'change-negative') + '">';
                html += (coin.change24h >= 0 ? '+' : '') + coin.change24h.toFixed(2) + '%';
                html += '</div>';
                html += '</div>';
                html += '<div class="stat">';
                html += '<div class="stat-label">Volume 24h</div>';
                html += '<div class="stat-value">$' + formatNumber(coin.volume24h) + '</div>';
                html += '</div>';
                html += '<div class="stat">';
                html += '<div class="stat-label">Liquidity</div>';
                html += '<div class="stat-value">$' + formatNumber(coin.liquidity) + '</div>';
                html += '</div>';
                html += '<div class="stat">';
                html += '<div class="stat-label">' + (coin.age ? 'Age' : 'Address') + '</div>';
                html += '<div class="stat-value">' + (coin.age || coin.address.substring(0, 8) + '...') + '</div>';
                html += '</div>';
                html += '</div>';
                html += '</div>';
            }
            
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
            
            const resultsDiv = document.getElementById('analysis-results');
            resultsDiv.style.display = 'block';
            
            resultsDiv.innerHTML = '<div class="analysis-results">' +
                '<h3>Analysis Results</h3>' +
                '<div class="risk-score" style="color: #28a745">' +
                'Risk Score: 25/100' +
                '</div>' +
                '<div class="verdict" style="color: #28a745">' +
                'Low Risk' +
                '</div>' +
                '<div class="summary">' +
                '<h4>Summary</h4>' +
                '<p>This token appears to be safe based on initial analysis. (Mock data for testing)</p>' +
                '</div>' +
                '</div>';
        }
        
        // Load trending coins immediately when page loads
        window.onload = function() {
            loadTrendingCoins();
        };
    </script>
</body>
</html>
`);
};