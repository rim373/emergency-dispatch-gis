#!/bin/bash

# Emergency Response System - Backend Start Script

echo "================================================"
echo "Emergency Response System - Starting Backend"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
    echo ""
fi

# Start the server
echo ""
echo "🚀 Starting FastAPI server..."
echo "📊 API will be available at: http://localhost:8000"
echo "📖 API docs will be available at: http://localhost:8000/docs"
echo "🔌 WebSocket will be available at: ws://localhost:8000/socket.io"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Run with uvicorn
uvicorn app.main:sio_app --host 0.0.0.0 --port 8000 --reload
