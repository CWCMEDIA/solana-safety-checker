#!/bin/bash

# Solana Safety Checker GUI Launcher
# Double-click this file or run from terminal

echo "🚀 Starting Solana Safety Checker GUI..."

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 run_gui.py
elif command -v python &> /dev/null; then
    python run_gui.py
else
    echo "❌ Python not found. Please install Python 3.9 or higher."
    echo "You can download it from: https://www.python.org/downloads/"
    read -p "Press Enter to exit..."
fi
