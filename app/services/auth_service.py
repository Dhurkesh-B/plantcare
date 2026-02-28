from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User
from app.schemas.auth import GoogleAuthRequest, Token
from app.utils.security import create_access_token
from app.config import settings
from google.oauth2 import id_token
from google.auth.transport import requests

def authenticate_google_user(db: Session, request: GoogleAuthRequest) -> Token:
    try:
        # Verify the token against Google's servers
        idinfo = id_token.verify_oauth2_token(
            request.credential, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )

        # ID token is valid. Extract user info.
        email = idinfo['email'].lower()
        name = idinfo.get('name', 'Google User')
        
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google authentication token")

    # Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Auto-generate a unique username from email prefix
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        # Ensure uniqueness
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
            
        # Create the new user. hashed_password is now nullable.
        user = User(
            email=email,
            username=username,
            name=name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    # Generate our own platform JWT for them
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")
