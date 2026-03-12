Write-Host "🚀 Starting Agent-Doc-X Backend..." -ForegroundColor Green

Write-Host "📦 Installing/Updating dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "🌱 Initializing Database..." -ForegroundColor Cyan
python -m app.db.init_db

Write-Host "🔥 Starting FastAPI server..." -ForegroundColor Cyan
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
