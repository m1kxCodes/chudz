@echo off
REM NoFilters Image Generator - Windows Startup Script

echo.
echo ========================================
echo   NoFilters Image Generator
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Make sure Python 3.9+ is installed and in PATH
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements
echo.
echo Installing dependencies (this may take a few minutes on first run)...
cd backend
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Start the server
echo.
echo ========================================
echo   Starting NoFilters API Server
echo ========================================
echo.
echo Server will be available at: http://localhost:8000
echo API Documentation at: http://localhost:8000/docs
echo.
echo To use the frontend:
echo 1. Keep this window open
echo 2. Open 'frontend/index.html' in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py

pause
