#!/usr/bin/env python3
"""
Simple launcher for the Solana Safety Checker Web GUI
"""

import sys
import os
import webbrowser
import time
import threading

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """Open browser after server starts"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:8080')

def main():
    try:
        print("🚀 Starting Solana Safety Checker Web GUI...")
        print("📱 The web interface will open in your browser automatically")
        print("🛑 Press Ctrl+C to stop the server")
        print()
        
        # Start browser in background
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Import and run the web server
        from sol_safety_check_web import start_server
        start_server(8080)
        
    except ImportError as e:
        print(f"❌ Error importing web GUI: {e}")
        print("Make sure you're running this from the correct directory")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running web GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
