#!/usr/bin/env python3
"""
Simple launcher for the Solana Safety Checker GUI
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sol_safety_check_gui import main
    main()
except ImportError as e:
    print(f"Error importing GUI: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)
except Exception as e:
    print(f"Error running GUI: {e}")
    sys.exit(1)
