# Solana Safety Checker - Vercel Deployment Guide

## 🚀 Deploy to Vercel

### Prerequisites
1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Account**: Your code needs to be in a GitHub repository
3. **Vercel CLI** (optional): `npm i -g vercel`

### Deployment Steps

#### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add password protection and Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will automatically detect the Python project

3. **Configure Environment Variables** (Optional):
   - In Vercel dashboard, go to your project settings
   - Add environment variables if you have API keys:
     ```
     BIRDEYE_API_KEY=your_birdeye_api_key_here
     RUGCHECK_JWT_TOKEN=your_rugcheck_token_here
     MORALIS_API_KEY=your_moralis_api_key_here
     BITQUERY_API_KEY=your_bitquery_api_key_here
     SOLANA_RPC_URL=your_solana_rpc_url_here
     ```

4. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete
   - Your site will be available at `https://your-project-name.vercel.app`

#### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Follow the prompts**:
   - Link to existing project or create new one
   - Set up environment variables if needed
   - Deploy

### 🔐 Password Protection

The site is protected with the password: **LetsHope**

- Users will be prompted for authentication when accessing any page
- The password is hardcoded in the application for simplicity
- All routes (except static files) require authentication

### 📁 Project Structure

```
crypto-checker/
├── api/
│   └── index.py          # Vercel serverless function
├── sol_safety_check/     # Main application code
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
├── .env                 # Environment variables (local only)
└── DEPLOYMENT.md        # This file
```

### 🔧 Configuration Files

- **`vercel.json`**: Vercel deployment configuration
- **`requirements.txt`**: Python dependencies for Vercel
- **`api/index.py`**: Serverless function entry point

### 🌐 Accessing Your Deployed Site

1. **Main URL**: `https://your-project-name.vercel.app`
2. **Password**: `LetsHope`
3. **Features Available**:
   - ✅ Trending tokens from DEX Screener
   - ✅ Latest tokens discovery
   - ✅ Token analysis with risk scoring
   - ✅ Password protection on all pages

### 🐛 Troubleshooting

**Common Issues**:

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Authentication Issues**: Check that the password is correctly set
3. **API Errors**: Verify environment variables are set in Vercel dashboard
4. **Timeout Issues**: Vercel has a 10-second timeout for serverless functions

**Debug Steps**:
1. Check Vercel function logs in the dashboard
2. Test locally with `vercel dev`
3. Verify all imports are working correctly

### 🔄 Updating the Deployment

To update your deployed site:

1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. Vercel will automatically redeploy

### 📊 Monitoring

- **Vercel Dashboard**: Monitor deployments, logs, and performance
- **Function Logs**: Check for errors in the Vercel dashboard
- **Analytics**: Available in Vercel Pro plan

### 🎯 Next Steps

After deployment:
1. Test all functionality on the live site
2. Share the URL with users
3. Monitor usage and performance
4. Consider upgrading to Vercel Pro for advanced features

---

**Your Solana Safety Checker is now live and password-protected!** 🚀
