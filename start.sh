#!/bin/bash

# Drilling Insight Startup Script
# Starts frontend on port 8080 and backend on port 8001

echo "=========================================="
echo "Drilling Insight - Full Stack Startup"
echo "=========================================="
echo ""
echo "Frontend: http://localhost:8080"
echo "Backend:  http://localhost:8001"
echo ""

# Kill any existing processes on these ports
echo "Cleaning up old processes..."
lsof -i :8080 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
lsof -i :8001 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
sleep 2

echo ""
echo "Starting Backend on port 8001..."
cd ai_service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 3

echo ""
echo "Starting Frontend on port 8080..."
cd ..
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "✅ Application started successfully!"
echo "=========================================="
echo ""
echo "Access the application at:"
echo "  http://localhost:8080"
echo ""
echo "API available at:"
echo "  http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
