#!/bin/bash
echo "🚀 Starting Agent-Doc-X Backend..."

echo "📦 Installing/Updating dependencies..."
python3 -m pip install -r requirements.txt

echo "🌱 Initializing Database..."
python3 -m app.db.init_db

echo "🔥 Starting FastAPI server..."
# Kill any process on port 8000 to avoid "Address already in use"
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
