#!/bin/bash

# Illegal Mining Detection System - Demo Startup Script
# Smart India Hackathon Project

echo "🚛 Starting Illegal Mining Detection System (Demo Mode)..."
echo "========================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Function to start backend
start_backend() {
    echo "🔧 Starting Backend Server (Demo Mode)..."
    cd backend
    
    # Install minimal dependencies if not already installed
    echo "📦 Installing Python dependencies..."
    pip3 install fastapi uvicorn pydantic python-multipart python-dotenv requests tqdm numpy pandas matplotlib reportlab jinja2 --quiet
    
    # Start FastAPI server
    echo "🚀 Starting FastAPI server on http://localhost:8000"
    python3 app_simple.py &
    
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Frontend Server..."
    cd frontend
    
    # Install dependencies if not already installed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing Node.js dependencies..."
        npm install --legacy-peer-deps --quiet
    fi
    
    # Start development server
    echo "🚀 Starting React development server on http://localhost:5173"
    npm run dev &
    
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
    cd ..
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend server stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend server stopped"
    fi
    echo "👋 Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start both servers
start_backend
sleep 3
start_frontend

echo ""
echo "🎉 Illegal Mining Detection System is running in DEMO MODE!"
echo "=========================================================="
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend UI: http://localhost:5173"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "⚠️  Note: This is a demo version with mock data."
echo "   For full functionality, install geospatial dependencies."
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user to stop
wait
