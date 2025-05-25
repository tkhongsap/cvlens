#!/bin/bash

echo "========================================"
echo "CVLens-Agent - Local Resume Screening"
echo "========================================"
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy env.example to .env and configure your settings."
    echo
    exit 1
fi

# Check if virtual environment exists
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt >/dev/null 2>&1

# Download spaCy model if not present
echo "Checking NLP models..."
python -m spacy download en_core_web_sm >/dev/null 2>&1

# Create necessary directories
mkdir -p logs
mkdir -p data/cache
mkdir -p data/db
mkdir -p data/.token

# Run the application
echo
echo "Starting CVLens-Agent..."
echo
echo "Once the app starts:"
echo "1. Open your browser at http://localhost:8501"
echo "2. Click 'Authenticate with Microsoft' in the sidebar"
echo "3. Follow the device code authentication flow"
echo
echo "Press Ctrl+C to stop the application"
echo "========================================"
echo

streamlit run app.py 