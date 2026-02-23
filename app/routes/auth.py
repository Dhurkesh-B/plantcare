from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserSignup, UserLogin, Token, OTPVerifySignup, ForgotPasswordOTPRequest, ResetPasswordRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
def signup(request: UserSignup, db: Session = Depends(get_db)):
    """Initiates registration by sending an OTP to the given email."""
    return auth_service.request_signup_otp(db, request)

@router.post("/verify-signup", response_model=Token)
def verify_signup(request: OTPVerifySignup, db: Session = Depends(get_db)):
    """Verifies the OTP and officially creates the user account."""
    return auth_service.verify_signup_otp(db, request)

@router.post("/login", response_model=Token)
def login(request: UserLogin, db: Session = Depends(get_db)):
    """Authenticate via email/password and return JWT token."""
    return auth_service.authenticate_user_login(db, request)

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordOTPRequest, db: Session = Depends(get_db)):
    """Initiates password reset by sending an OTP."""
    return auth_service.request_password_reset_otp(db, request)

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Verifies the OTP and resets the password."""
    return auth_service.reset_password(db, request)
