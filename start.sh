#!/bin/bash
echo "🚀 Starting Agent-Doc-X Backend..."

echo "📦 Installing/Updating dependencies..."
pip install -r requirements.txt

echo "🌱 Initializing Database..."
python3 -m app.db.init_db

echo "🔥 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
