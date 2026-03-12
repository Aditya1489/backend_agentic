from app.services.auth_service import AuthService
from app.db.session import SessionLocal

db = SessionLocal()
try:
    auth_service = AuthService(db)
    result = auth_service.login_user("ashishkumar93040086@gmail.com", "agent@123")
    print(f"Result: {result}")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
