#!/bin/bash

echo "Starting GymTracker..."
echo "Installing dependencies..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start the Flask application
echo "Starting Flask application..."
echo "Open http://localhost:8080 in your browser"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
