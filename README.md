# Sol Safety Check

A comprehensive Solana token safety checker CLI tool that analyzes multiple risk factors to determine if a token is safe to invest in.

## Features

- **Multi-source data aggregation** from DEX Screener, Birdeye, RugCheck, Pump.fun, and Solana chain
- **Comprehensive risk assessment** covering authorities, liquidity, tradeability, concentration, and more
- **Real-time analysis** with concurrent API calls for fast results
- **Beautiful console output** with Rich formatting and tables
- **JSON output** for programmatic use
- **Configurable data sources** to focus on specific providers
- **Production-ready** with proper error handling and logging

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or poetry for package management

### Install from source

```bash
git clone <repository-url>
cd crypto-checker
pip install -e .
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the environment example file:
```bash
cp .env.example .env
```

2. Edit `.env` with your API keys (optional but recommended for better data):

```env
# Required
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Optional (for enhanced analysis)
BIRDEYE_API_KEY=your_birdeye_api_key_here
MORALIS_API_KEY=your_moralis_api_key_here
BITQUERY_API_KEY=your_bitquery_api_key_here
RUGCHECK_JWT=your_rugcheck_jwt_token_here
```

### API Keys

- **SOLANA_RPC_URL**: Required. Use a free public RPC or get a dedicated one from providers like Helius, QuickNode, etc.
- **BIRDEYE_API_KEY**: Optional. Get from [Birdeye Docs](https://docs.birdeye.so/) - Enables comprehensive V3 API access for enhanced analysis
- **MORALIS_API_KEY**: Optional. Get from [Moralis](https://moralis.io/)
- **BITQUERY_API_KEY**: Optional. Get from [Bitquery](https://bitquery.io/)
- **RUGCHECK_JWT**: Optional. Get from [RugCheck](https://rugcheck.xyz/)

## Usage

### Basic Usage

```bash
# Check a token
sol-safety-check Fv73EXJBRfctJzLVC3P7uQP6er6JU8b4KtDr4LQFpump

# Quick analysis (skip heavier calls)
sol-safety-check <MINT> --fast

# JSON output for programmatic use
sol-safety-check <MINT> --json

# Use specific data sources only
sol-safety-check <MINT> --providers dexscreener,birdeye

# Custom RPC URL
sol-safety-check <MINT> --rpc https://your-rpc-url.com
```

### Command Line Options

- `mint`: Solana token mint address (required)
- `--rpc`: Custom Solana RPC URL (optional)
- `--fast`: Skip heavier calls for quick analysis (optional)
- `--json`: Output results in JSON format (optional)
- `--providers`: Comma-separated list of providers to use (optional)

## Risk Assessment

The tool evaluates tokens based on multiple risk factors:

### Risk Categories

1. **Authorities** (20% weight)
   - Mint authority status
   - Freeze authority status
   - Renunciation verification

2. **Liquidity** (25% weight)
   - Liquidity levels (USD/SOL)
   - Lock percentage and duration
   - Lock provider verification

3. **Tradeability** (20% weight)
   - Buy/sell restrictions
   - Tax percentages
   - Honeypot detection

4. **Concentration** (15% weight)
   - Top holder distribution
   - Insider accumulation
   - Whale concentration

5. **Age/Hype** (10% weight)
   - Token age
   - Volume spikes
   - Pump and dump patterns

6. **Pump.fun** (5% weight)
   - Dev wallet holdings
   - Migration status
   - Creation context

7. **Listings** (5% weight)
   - DEX presence
   - Exchange listings
   - Ecosystem integration

### Risk Scoring

- **0-29**: ✅ Likely OK (still DYOR)
- **30-59**: ⚠️ Caution
- **60-100**: ❌ High Risk / Avoid

## Data Sources

### DEX Screener (Free)
- Trading pairs and liquidity
- Volume and price data
- DEX information

### Birdeye (API Key Required)
- Enhanced market data and price statistics
- Comprehensive token metadata and overview
- Holder statistics and distribution
- OHLCV data with multiple timeframes
- Security analysis and risk assessment
- Token creation information
- Trade data and market analysis
- Pair overview and liquidity data

### RugCheck (JWT Required)
- Risk analysis
- Holder analysis
- Liquidity analysis

### Pump.fun Intelligence (API Key Required)
- Creation information
- Dev wallet analysis
- Migration status

### Solana Chain (RPC Required)
- On-chain token data
- Holder distribution
- Authority information

## Output Examples

### Console Output

```
┌─ Safety Verdict ─────────────────────────────────────────┐
│ ✅ Likely OK (still DYOR)                               │
│ Risk Score: 25/100                                       │
└──────────────────────────────────────────────────────────┘

┌─ Risk Assessment Details ────────────────────────────────┐
│ Rule          │ Score │ Severity │ Message              │
├───────────────┼───────┼──────────┼──────────────────────┤
│ Authorities   │ 0     │ 🟢 LOW   │ Authorities properly  │
│               │       │          │ renounced            │
│ Liquidity     │ 15    │ 🟡 MED   │ Moderate liquidity:  │
│               │       │          │ $8,500               │
│ Tradeability  │ 0     │ 🟢 LOW   │ Trading appears      │
│               │       │          │ normal               │
└───────────────┴───────┴──────────┴──────────────────────┘
```

### JSON Output

```json
{
  "mint_address": "Fv73EXJBRfctJzLVC3P7uQP6er6JU8b4KtDr4LQFpump",
  "overall_score": 25,
  "verdict": "Likely OK (still DYOR)",
  "risk_level": "safe",
  "notes": [
    {
      "rule_name": "Authorities",
      "score": 0,
      "message": "Authorities properly renounced",
      "severity": "low"
    }
  ],
  "data_sources_used": ["dexscreener", "birdeye", "solana_chain"],
  "warnings": []
}
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black sol_safety_check/
ruff check sol_safety_check/

# Type checking
mypy sol_safety_check/
```

### Project Structure

```
sol_safety_check/
├── __init__.py
├── cli.py                 # CLI interface
├── models.py              # Pydantic models
├── utils.py               # Utility functions
├── datasources/           # Data source clients
│   ├── __init__.py
│   ├── dexscreener.py
│   ├── birdeye.py
│   ├── rugcheck.py
│   ├── pumpfun.py
│   └── solana_chain.py
└── risk/                  # Risk assessment
    ├── __init__.py
    ├── rules.py           # Risk rules
    └── scoring.py         # Scoring system
```

## Limitations

- **API Rate Limits**: Some providers have rate limits that may affect analysis speed
- **Data Availability**: Not all tokens may have complete data from all sources
- **False Positives**: Risk assessment is based on heuristics and may not catch all risks
- **DYOR**: This tool is for informational purposes only and should not replace your own research

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for educational and informational purposes only. It does not constitute financial advice. Always do your own research (DYOR) before investing in any cryptocurrency. The authors are not responsible for any financial losses.
