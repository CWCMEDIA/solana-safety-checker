# Solana Safety Checker - Web GUI

A beautiful, modern web-based interface for checking Solana token safety. No installation required - just run and open in your browser!

## 🚀 Quick Start

### Option 1: Double-click launcher (Easiest)
1. Double-click `launch_web.sh` in Finder
2. Your browser will open automatically to `http://localhost:8080`

### Option 2: Terminal command
```bash
python3 launch_web.py
```

### Option 3: Direct launch
```bash
python3 sol_safety_check_web.py
```

## 🌐 Web Interface Features

### **Beautiful Modern Design**
- **Responsive layout** - Works on desktop, tablet, and mobile
- **Gradient background** - Professional purple gradient design
- **Smooth animations** - Hover effects and transitions
- **Clean typography** - Easy to read fonts and spacing

### **Easy Token Analysis**
- **Simple input** - Just paste any Solana token address
- **Quick buttons** - Pre-loaded with SOL, USDC, and test tokens
- **One-click analysis** - Get comprehensive safety report instantly
- **Real-time feedback** - Loading spinner and progress updates

### **Configurable Data Sources**
- ✅ **DEX Screener** (Free) - Trading pairs and liquidity
- ✅ **Birdeye** (API Key) - Enhanced market data
- ✅ **RugCheck** (JWT) - Professional risk analysis
- ✅ **Pump.fun** (API Key) - Memecoin analysis
- ✅ **Solana Chain** (RPC) - On-chain data

### **Comprehensive Results Display**
- **Safety verdict** - Clear ✅/⚠️/❌ recommendations with color coding
- **Risk score** - 0-100 numerical rating
- **Detailed breakdown** - Authority, liquidity, concentration analysis
- **Professional table** - Clean, organized risk assessment details
- **Data sources** - Shows which providers were used
- **Warnings** - Any issues encountered during analysis

## 📱 How to Use

### 1. **Launch the Application**
- Double-click `launch_web.sh` or run `python3 launch_web.py`
- Your browser will open automatically to `http://localhost:8080`

### 2. **Enter Token Address**
- Paste any Solana token mint address in the input field
- Or click quick buttons for common tokens (SOL, USDC, Test Token)

### 3. **Select Data Sources**
- Choose which providers to use for analysis
- Free sources (DEX Screener, Solana Chain) work without API keys
- Paid sources require API keys for enhanced analysis

### 4. **Configure Options**
- **Fast Mode**: Skip heavier calls for quicker analysis
- **API Keys**: Configure in the `.env` file (optional)

### 5. **Run Analysis**
- Click "🔍 Analyze Token" button
- Watch the loading spinner while analysis runs
- View comprehensive safety report with color-coded results

## 🎨 Interface Highlights

### **Color-Coded Results**
- 🟢 **Green**: Safe/Low Risk (0-29 points)
- 🟡 **Yellow**: Caution/Medium Risk (30-59 points)  
- 🔴 **Red**: High Risk/Avoid (60-100 points)

### **Professional Layout**
- **Header**: App title and description
- **Form**: Token input and configuration options
- **Results**: Detailed analysis with tables and formatting
- **Footer**: Links and attribution

### **Responsive Design**
- **Desktop**: Full-width layout with side-by-side options
- **Tablet**: Optimized for touch interaction
- **Mobile**: Stacked layout for small screens

## 🔧 Technical Details

### **Built With**
- **Backend**: Python 3.9+ with asyncio
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Server**: Python HTTP server
- **Styling**: Modern CSS with gradients and animations

### **System Requirements**
- **Python**: 3.9 or higher
- **Browser**: Chrome, Firefox, Safari, or Edge
- **Memory**: 100MB RAM
- **Storage**: 50MB free space
- **Network**: Internet connection for data fetching

### **Port Configuration**
- **Default**: Port 8080
- **Custom**: `python3 sol_safety_check_web.py --port 9090`
- **Auto-open**: `python3 sol_safety_check_web.py --open-browser`

## 🛠️ Troubleshooting

### **Common Issues**

**"Server won't start"**
- Check if port 8080 is already in use
- Try a different port: `python3 sol_safety_check_web.py --port 9090`

**"Browser won't open"**
- Manually open `http://localhost:8080` in your browser
- Check if firewall is blocking the connection

**"Analysis fails"**
- Check internet connection
- Verify token address format
- Try using only free sources (DEX Screener + Solana Chain)

**"Page looks broken"**
- Refresh the browser page
- Check browser console for JavaScript errors
- Try a different browser

### **Getting Help**
- Check the terminal output for detailed error messages
- Verify all dependencies are installed
- Try the CLI version as a fallback

## 🎯 Tips for Best Results

1. **Use multiple sources** for comprehensive analysis
2. **Check both free and paid sources** for complete picture
3. **Look at all risk categories** not just overall score
4. **Consider token age** - very new tokens are riskier
5. **Verify liquidity levels** - higher is generally better
6. **Use Fast Mode** for quick checks, disable for detailed analysis

## 🔒 Security & Privacy

- **Local processing** - All analysis happens on your machine
- **No data storage** - Results are not saved or transmitted
- **API keys** - Stored locally in `.env` file only
- **HTTPS ready** - Can be configured for secure connections

## 📊 Sample Results

The web interface displays results in a professional format:

```
✅ Likely OK (still DYOR)
Risk Score: 25/100

Risk Assessment Details:
Rule          Score  Severity  Message
Authorities   0      🟢 LOW    Authorities properly renounced
Liquidity     15     🟡 MEDIUM Moderate liquidity: $8,500
Tradeability  0      🟢 LOW    Trading appears normal
```

## 🚀 Ready to Use!

Your Solana Safety Checker now has a beautiful web interface! 

**Launch it now:**
```bash
python3 launch_web.py
```

Then open your browser to `http://localhost:8080` and start analyzing tokens! 🎉
