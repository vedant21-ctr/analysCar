#!/bin/bash
# Urban Mobility Intelligence OS — Frontend Startup Script

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║     Urban Mobility Intelligence OS — Frontend        ║"
echo "╚══════════════════════════════════════════════════════╝"

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "📥 Installing npm packages..."
    npm install
fi

echo ""
echo "✅ Starting React app on http://localhost:3000"
echo ""

npm start
