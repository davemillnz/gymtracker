#!/bin/bash

echo "Installing GymTracker dependencies..."
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Try to install with pip first
echo "Attempting to install with pip..."
pip install --upgrade pip

# Try different installation strategies
echo "Strategy 1: Installing with pip (may take a while)..."
if pip install -r requirements.txt; then
    echo "✓ Dependencies installed successfully with pip!"
else
    echo "⚠ Pip installation failed, trying alternative approach..."
    
    echo "Strategy 2: Installing with conda (if available)..."
    if command -v conda &> /dev/null; then
        echo "Conda found, trying conda install..."
        conda install -c conda-forge flask flask-cors pandas matplotlib -y
        if [ $? -eq 0 ]; then
            echo "✓ Dependencies installed successfully with conda!"
        else
            echo "✗ Conda installation also failed"
        fi
    else
        echo "Conda not found, trying pip with pre-built wheels..."
        echo "Strategy 3: Installing with pip using pre-built wheels..."
        pip install --only-binary=all flask flask-cors pandas matplotlib
        if [ $? -eq 0 ]; then
            echo "✓ Dependencies installed successfully with pre-built wheels!"
        else
            echo "✗ All installation methods failed"
            echo ""
            echo "Manual installation required:"
            echo "1. Install Homebrew if not already installed: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "2. Install Python packages via Homebrew: brew install python-pandas python-matplotlib"
            echo "3. Then run: pip install flask flask-cors"
            exit 1
        fi
    fi
fi

echo ""
echo "✓ Installation completed!"
echo ""
echo "To run the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run Flask app: python3 app.py"
echo "3. Open http://localhost:8080 in your browser"
echo ""
echo "Or use the run script: ./run.sh"
