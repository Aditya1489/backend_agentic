import os
from dotenv import load_dotenv
from typing import Optional

# Load .env file
load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agent.db")
DATABASE_PASSWORD: Optional[str] = os.getenv("DATABASE_PASSWORD")
SECRET_KEY: str = os.getenv("SECRET_KEY", "yoursecretkeyhere")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

INITIAL_USER_EMAIL: str = os.getenv("INITIAL_USER_EMAIL", "")
INITIAL_USER_PASSWORD: str = os.getenv("INITIAL_USER_PASSWORD", "")

MAKE_PLAN_API_KEY: str = os.getenv("MAKE_PLAN_API_KEY", "")

TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
NGROK_URL: str = os.getenv("NGROK_URL", "")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
