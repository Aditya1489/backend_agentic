from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, agents, outbound, media_stream, chat, new_chat
from app.db.init_db import init_db

app = FastAPI(title="Agent-Doc-X API")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(outbound.router, prefix="/outbound", tags=["outbound"])
app.include_router(media_stream.router, tags=["media-stream"])
app.include_router(chat.router, prefix="/agents", tags=["chat"])
app.include_router(new_chat.router, prefix="/agents", tags=["chat-new"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agent-Doc-X API"}
