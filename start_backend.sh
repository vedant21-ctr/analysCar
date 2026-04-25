#!/bin/bash
# Urban Mobility Intelligence OS — Backend Startup Script

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║     Urban Mobility Intelligence OS — Backend         ║"
echo "╚══════════════════════════════════════════════════════╝"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Generate dataset if not present
if [ ! -f "data/uber_rides.csv" ]; then
    echo "🚀 Generating dataset..."
    python3 data/generate_dataset.py
fi

# Create models directory
mkdir -p models/saved

# Start API server
echo ""
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo ""

cd backend/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
