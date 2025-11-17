@echo off
REM Startup script for Crypto Trading Bot Desktop App

echo ========================================
echo  Crypto Trading Bot - Desktop Edition
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if PyQt5 is installed
python -c "from PyQt5.QtWidgets import QApplication" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: PyQt5 not found!
    echo Installing required dependencies...
    pip install PyQt5==5.15.10 pyqtgraph==0.13.3 qtawesome==1.3.0
)

REM Start the desktop app
echo.
echo Starting desktop application...
echo.
python main_gui.py

REM If error occurred
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start!
    echo Check logs in logs/ directory
    pause
)
