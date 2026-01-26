#!/bin/bash

# PostgreSQL Query Agent - Quick Start Script
# This script helps you get started quickly

set -e

echo "🤖 PostgreSQL Query Agent - Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your:"
    echo "   - PostgreSQL database credentials"
    echo "   - Anthropic API key"
    echo ""
    read -p "Press Enter once you've configured .env..."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Check for Node.js and npm
if ! command -v npm &> /dev/null; then
    echo "⚠️  npm not found. MCP server requires Node.js."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Install MCP server
echo "🔌 Checking MCP PostgreSQL server..."
if ! npm list -g @modelcontextprotocol/server-postgres &> /dev/null; then
    echo "Installing MCP PostgreSQL server..."
    npm install -g @modelcontextprotocol/server-postgres
    echo "✅ MCP server installed"
else
    echo "✅ MCP server already installed"
fi

echo ""
echo "🚀 Setup complete! Starting the application..."
echo ""
echo "📍 The application will be available at:"
echo "   http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
