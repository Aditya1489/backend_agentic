import sys
import os

# Ensure absolute imports work by adding the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core import config
from app.models.user import User
from app.db.session import SessionLocal, engine
from passlib.hash import sha256_crypt

def seed():
    print(f"Connecting to database...")
    # Assuming User model and engine are already set up to use config.DATABASE_URL via app.db
    # We will ensure the tables are created if they don't exist
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        email = config.INITIAL_USER_EMAIL
        password = config.INITIAL_USER_PASSWORD
        
        if not email or not password:
            print("Error: INITIAL_USER_EMAIL or INITIAL_USER_PASSWORD not set in environment.")
            return

        print(f"Checking for user: {email}")
        user = db.query(User).filter(User.email == email).first()
        hashed_password = sha256_crypt.hash(password)
        
        if not user:
            print("Creating new user...")
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print("User created successfully.")
        else:
            print("User already exists. Updating password...")
            user.hashed_password = hashed_password
            db.commit()
            print("Password updated successfully.")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
