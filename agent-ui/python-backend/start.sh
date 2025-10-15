#!/bin/bash

# Start script for Python backend

echo "================================================"
echo "   SecureMCP Python Backend Startup Script     "
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Download spaCy model if not present
echo ""
echo "Checking spaCy model..."
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Downloading spaCy model..."
    python -m spacy download en_core_web_sm
    echo "✓ spaCy model downloaded"
else
    echo "✓ spaCy model already installed"
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from example..."
    cat > .env << EOF
PORT=8003
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
DEFAULT_SECURITY_LEVEL=medium
MODEL_CACHE_DIR=./models
USE_GPU=auto
EOF
    echo "✓ .env file created"
fi

echo ""
echo "================================================"
echo "   Starting FastAPI Server...                  "
echo "================================================"
echo ""

# Start the server
# python app/main.py
python -m app.main
read -p "Press Enter to exit..."