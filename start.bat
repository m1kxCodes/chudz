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

REM Ask which compute backend to use for this run
echo.
echo Select compute backend:
echo   1. NVIDIA GPU (CUDA) - use this for RTX/GTX cards
echo   2. AMD/Intel GPU (DirectML)
echo   3. CPU only
echo.
choice /C 123 /N /M "Choose 1, 2, or 3: "
if errorlevel 3 goto backend_cpu
if errorlevel 2 goto backend_directml
if errorlevel 1 goto backend_cuda

:backend_cuda
set "NOFILTERS_DEVICE=cuda"
set "REQ_FILE=requirements-cuda.txt"
set "BACKEND_NAME=NVIDIA CUDA"
goto backend_selected

:backend_directml
set "NOFILTERS_DEVICE=amd"
set "REQ_FILE=requirements-directml.txt"
set "BACKEND_NAME=AMD/Intel DirectML"
goto backend_selected

:backend_cpu
set "NOFILTERS_DEVICE=cpu"
set "REQ_FILE=requirements-cpu.txt"
set "BACKEND_NAME=CPU"
goto backend_selected

:backend_selected
echo.
echo Selected backend: %BACKEND_NAME%

REM Install/update requirements
echo.
echo Installing dependencies (this may take a few minutes on first run)...
cd backend
if "%NOFILTERS_DEVICE%"=="cuda" pip uninstall -y torch-directml >nul 2>nul
if "%NOFILTERS_DEVICE%"=="cpu" pip uninstall -y torch-directml >nul 2>nul
pip install -r %REQ_FILE% --upgrade
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
