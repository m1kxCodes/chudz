#!/bin/bash

# NoFilters Image Generator - Unix Startup Script

echo ""
echo "========================================"
echo "  NoFilters Image Generator"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo ""
echo "Installing dependencies (this may take a few minutes on first run)..."
cd backend
pip install -r requirements.txt --upgrade
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Start the server
echo ""
echo "========================================"
echo "  Starting NoFilters API Server"
echo "========================================"
echo ""
echo "Server will be available at: http://localhost:8000"
echo "API Documentation at: http://localhost:8000/docs"
echo ""
echo "To use the frontend:"
echo "1. Keep this terminal open"
echo "2. Open 'frontend/index.html' in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
