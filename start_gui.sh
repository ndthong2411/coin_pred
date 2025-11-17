#!/bin/bash
# Startup script for Crypto Trading Bot Desktop App

echo "========================================"
echo " Crypto Trading Bot - Desktop Edition"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if PyQt5 is installed
python -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: PyQt5 not found!"
    echo "Installing required dependencies..."
    pip install PyQt5==5.15.10 pyqtgraph==0.13.3 qtawesome==1.3.0
fi

# Start the desktop app
echo ""
echo "Starting desktop application..."
echo ""
python main_gui.py

# If error occurred
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application failed to start!"
    echo "Check logs in logs/ directory"
    read -p "Press Enter to continue..."
fi
