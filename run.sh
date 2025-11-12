#!/bin/bash

# Quick start script for CampusFlow
# This script helps you run the Streamlit app

echo "🏛️  Starting CampusFlow..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. 
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run Streamlit
echo "🚀 Starting Streamlit app..."
echo "   The app will open in your browser at http://localhost:8501"
echo ""

cd frontend
streamlit run app.py


