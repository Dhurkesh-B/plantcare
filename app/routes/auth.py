from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import GoogleAuthRequest, Token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/google", response_model=Token)
def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate via Google OAuth2 ID Token and return application JWT."""
    return auth_service.authenticate_google_user(db, request)
