#!/usr/bin/env bash

echo "============================================"
echo "       Starting Ai_Tutor Platform"
echo "============================================"
echo ""

# Load environment variables from backend .env file
if [ -f "backend/.env" ]; then
    echo " Loading environment from backend/.env..."
    export $(grep -v '^#' backend/.env | xargs)
fi

# Read URLs from environment or use defaults
JUDGE0_URL="${JUDGE0_URL:-http://192.168.16.119:2358}"
OLLAMA_URL="${OLLAMA_URL:-http://192.168.64.251:11434}"

echo "  Configuration:"
echo "   Judge0: $JUDGE0_URL"
echo "   Ollama: $OLLAMA_URL"
echo "============================================"

# Check Judge0
if ! curl -s "$JUDGE0_URL/languages" > /dev/null 2>&1; then
    echo "❌ Judge0 is not running!"
    echo "Start with: docker run -d -p 2358:2358 judge0/judge0:latest"
    read -p "Press Enter after starting Judge0..."
fi

# Check Ollama
if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
    echo "❌ Ollama is not running!"
    echo "Start with: ollama serve"
    echo "Pull model: ollama pull qwen2.5-coder:3b"
    read -p "Press Enter after starting Ollama..."
fi

echo " All services detected!"
echo ""

# Backend
echo " Starting Backend API..."
cd backend
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
deactivate
cd ..

sleep 3

# Frontend
echo " Starting Frontend..."
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "  Ai Tutor is Running!"
echo "============================================"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔌 Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

trap "echo ''; echo ' Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
