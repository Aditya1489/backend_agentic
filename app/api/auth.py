from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.user import Token

router = APIRouter()

@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    auth_service = AuthService(db)
    return auth_service.login_user(email=form_data.username, password=form_data.password)

@router.post("/logout")
def logout():
    # Logout logic is simple for JWT (client-side removal), but we keep the endpoint for consistency
    auth_service = AuthService(None) # DB not needed for stateless logout message
    return auth_service.logout_user()
