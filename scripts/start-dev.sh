#!/bin/bash

# Aetherius Component: Web Development Startup Script
# This script starts both backend and frontend in development mode

set -e

echo "🚀 Starting Aetherius Component: Web Development Environment"
echo "============================================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ All dependencies found"

# Check for virtual environment
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment and install dependencies
echo "📦 Setting up backend dependencies..."
cd backend
source venv/bin/activate

if [ ! -f "venv/installed" ]; then
    pip install -r requirements.txt
    touch venv/installed
    echo "✅ Backend dependencies installed"
else
    echo "✅ Backend dependencies already installed"
fi

cd ..

# Install frontend dependencies
echo "📦 Setting up frontend dependencies..."
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi

cd ..

# Check if ports are available
echo "🔍 Checking port availability..."

if port_in_use 8000; then
    echo "⚠️  Port 8000 is already in use (backend)"
    echo "   You may need to stop other services or change the port"
fi

if port_in_use 3000; then
    echo "⚠️  Port 3000 is already in use (frontend)"
    echo "   You may need to stop other services or change the port"
fi

echo ""
echo "🎯 Starting services..."
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo "✅ Services stopped"
}

trap cleanup EXIT

# Start backend
echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🎨 Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID