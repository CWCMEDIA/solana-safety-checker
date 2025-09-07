# Solana Safety Checker - GUI Application

A user-friendly desktop application for checking Solana token safety with an intuitive interface.

## 🚀 Quick Start

### Option 1: Double-click launcher
1. Double-click `launch_gui.sh` in Finder
2. The GUI will open automatically

### Option 2: Terminal command
```bash
python3 run_gui.py
```

### Option 3: Direct launch
```bash
python3 sol_safety_check_gui.py
```

## 🖥️ Features

### **Easy Token Analysis**
- **Simple input**: Just paste any Solana token address
- **Quick buttons**: Pre-loaded with SOL, USDC, and test tokens
- **One-click analysis**: Get comprehensive safety report instantly

### **Configurable Data Sources**
- ✅ **DEX Screener** (Free) - Trading pairs and liquidity
- ✅ **Birdeye** (API Key) - Enhanced market data
- ✅ **RugCheck** (JWT) - Professional risk analysis
- ✅ **Pump.fun** (API Key) - Memecoin analysis
- ✅ **Solana Chain** (RPC) - On-chain data

### **API Key Management**
- **Built-in config**: Manage all API keys in one place
- **Auto-save**: Configuration saved to `.env` file
- **Secure input**: API keys are masked in the interface

### **Comprehensive Results**
- **Safety verdict**: Clear ✅/⚠️/❌ recommendations
- **Risk score**: 0-100 numerical rating
- **Detailed breakdown**: Authority, liquidity, concentration analysis
- **Trading data**: Pairs, volume, liquidity information
- **Token metadata**: Supply, authorities, creation info

## 📋 How to Use

### 1. **Enter Token Address**
- Paste any Solana token mint address
- Or use quick buttons for common tokens

### 2. **Select Data Sources**
- Choose which providers to use
- Free sources work without API keys
- Paid sources require API keys

### 3. **Configure API Keys** (Optional)
- Enter your API keys for enhanced analysis
- Keys are saved automatically
- Leave blank to use free sources only

### 4. **Run Analysis**
- Click "🔍 Analyze Token"
- Wait for results (usually 5-15 seconds)
- View comprehensive safety report

## 🔧 Configuration

### **API Keys Setup**
1. Click "Save Config" to save your API keys
2. Keys are stored in `.env` file
3. Restart the app to load new keys

### **Data Source Options**
- **DEX Screener**: Always works (free)
- **Birdeye**: Requires free API key from [bds.birdeye.so](https://bds.birdeye.so/)
- **RugCheck**: Requires JWT token from [rugcheck.xyz](https://rugcheck.xyz/)
- **Pump.fun**: Requires API key from [moralis.io](https://moralis.io/) or [bitquery.io](https://bitquery.io/)
- **Solana Chain**: Uses free public RPC

## 📊 Understanding Results

### **Safety Verdict**
- ✅ **Likely OK** (0-29): Low risk, still do your own research
- ⚠️ **Caution** (30-59): Medium risk, be careful
- ❌ **High Risk** (60-100): Avoid this token

### **Risk Categories**
- **Authorities**: Mint/freeze authority status
- **Liquidity**: Lock status and levels
- **Tradeability**: Buy/sell restrictions
- **Concentration**: Holder distribution
- **Age/Hype**: Token age and volume patterns
- **Pump.fun**: Memecoin-specific analysis
- **Listings**: DEX presence and listings

## 🛠️ Troubleshooting

### **Common Issues**
- **"Invalid address"**: Check token address format
- **"No data sources"**: Select at least one provider
- **"API errors"**: Check your API keys or use free sources
- **"Network error"**: Check internet connection

### **Getting Help**
- Check the console output for detailed error messages
- Try using only free sources (DEX Screener + Solana Chain)
- Verify API keys are correct and active

## 🎯 Tips for Best Results

1. **Use multiple sources** for comprehensive analysis
2. **Check both free and paid sources** for complete picture
3. **Look at all risk categories** not just overall score
4. **Consider token age** - very new tokens are riskier
5. **Verify liquidity levels** - higher is generally better

## 🔒 Security

- API keys are stored locally in `.env` file
- No data is sent to external servers except for analysis
- All analysis happens on your local machine
- API keys are masked in the interface

## 📱 System Requirements

- **macOS**: 10.14 or later
- **Python**: 3.9 or higher
- **Memory**: 100MB RAM
- **Storage**: 50MB free space
- **Network**: Internet connection for data fetching

---

**Ready to analyze some tokens? Launch the GUI and start checking!** 🚀
