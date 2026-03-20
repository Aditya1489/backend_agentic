from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.models.agent import Agent
from app.models.memory import ConversationHistory, LongTermMemory, UserPreference
from app.core.security import get_password_hash
from app.core import config

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if initial user exists
        user = db.query(User).filter(User.email == config.INITIAL_USER_EMAIL).first()
        if not user:
            new_user = User(
                email=config.INITIAL_USER_EMAIL,
                hashed_password=get_password_hash(config.INITIAL_USER_PASSWORD),
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print(f"Initial user {config.INITIAL_USER_EMAIL} created.")
        else:
            # Update password if it changed in .env
            user.hashed_password = get_password_hash(config.INITIAL_USER_PASSWORD)
            db.commit()
            print(f"Initial user {config.INITIAL_USER_EMAIL} password updated.")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
