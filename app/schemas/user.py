from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr

class UserUpdate(UserBase):
    pass

class UserResponse(UserBase):
    id: str
    email: str
    created_at: datetime
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False

    class Config:
        from_attributes = True

class UserMinimalResponse(BaseModel):
    id: str
    username: Optional[str] = None
    name: Optional[str] = None
    profile_image: Optional[str] = None
    is_following: bool = False
    
    class Config:
        from_attributes = True
