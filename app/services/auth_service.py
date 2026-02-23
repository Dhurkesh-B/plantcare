from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User
from app.models.otp import OtpCode
from app.schemas.auth import UserSignup, UserLogin, Token, OTPVerifySignup, ForgotPasswordOTPRequest, ResetPasswordRequest
from app.utils.security import create_access_token, get_password_hash, verify_password
from app.config import settings
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(receiver_email: str, otp: str):
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USERNAME
    msg['To'] = receiver_email
    msg['Subject'] = "PlantCare AI - Your Registration Code"
    
    body = f"Welcome to PlantCare AI!\n\nYour 6-digit verification code to complete registration is: {otp}\n\nThis code expires in 15 minutes."
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USERNAME, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def request_signup_otp(db: Session, request: UserSignup):
    email = request.email.lower()
    username = request.username.strip().lower()
    
    if len(username) < 3 or not username.isalnum():
        raise HTTPException(status_code=400, detail="Username must be at least 3 alphanumeric characters")
        
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = get_password_hash(request.password)
    
    # Generate 6 digit OTP
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    # Remove existing pending otps
    db.query(OtpCode).filter(OtpCode.email == email).delete()
    
    otp_record = OtpCode(
        email=email,
        username=username,
        hashed_password=hashed_pw,
        otp_code=otp,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send email
    send_otp_email(email, otp)
    return {"message": "OTP sent successfully"}

def verify_signup_otp(db: Session, request: OTPVerifySignup) -> Token:
    email = request.email.lower()
    code = request.otp_code
    
    otp_record = db.query(OtpCode).filter(OtpCode.email == email).first()
    
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No pending signup found for this email")
        
    if otp_record.otp_code != code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")
        
    if datetime.utcnow() > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP code expired")
        
    # Extra safety check
    if db.query(User).filter(User.username == otp_record.username).first():
        raise HTTPException(status_code=400, detail="Username was taken while verifying. Please start over.")
        
    new_user = User(
        email=email,
        username=otp_record.username,
        hashed_password=otp_record.hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    db.delete(otp_record)
    db.commit()
    
    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

def authenticate_user_login(db: Session, request: UserLogin) -> Token:
    email = request.email.lower()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

def send_password_reset_otp_email(receiver_email: str, otp: str):
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USERNAME
    msg['To'] = receiver_email
    msg['Subject'] = "PlantCare AI - Password Reset Code"
    
    body = f"Hello!\n\nYour 6-digit verification code to reset your password is: {otp}\n\nThis code expires in 15 minutes."
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USERNAME, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def request_password_reset_otp(db: Session, request: ForgotPasswordOTPRequest):
    email = request.email.lower()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Standard silent failure pattern to prevent enumeration attacks
        return {"message": "Reset OTP sent successfully"}
        
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    db.query(OtpCode).filter(OtpCode.email == email).delete()
    
    otp_record = OtpCode(
        email=email,
        otp_code=otp,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    send_password_reset_otp_email(email, otp)
    return {"message": "Reset OTP sent successfully"}

def reset_password(db: Session, request: ResetPasswordRequest):
    email = request.email.lower()
    code = request.otp_code
    
    otp_record = db.query(OtpCode).filter(OtpCode.email == email).first()
    if not otp_record or otp_record.otp_code != code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")
        
    if datetime.utcnow() > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP code expired")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(request.new_password)
    db.delete(otp_record)
    db.commit()
    
    return {"message": "Password reset successfully"}
