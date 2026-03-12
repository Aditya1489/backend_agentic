# Agent-Doc-X Backend

A Python FastAPI backend for Agent-Doc-X.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Update `.env` with your secrets.

3. **Initialize Database and Seed User**:
   The database tables will be created and the initial user will be seeded automatically when you start the server for the first time.

4. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, visit:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Features
- **SQLAlchemy 2.0 ORM**
- **FastAPI** for high-performance API
- **JWT Authentication**
- **Pydantic v2** for data validation
- **Environment-based seeding** (Zero hardcoding)
