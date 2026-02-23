from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserMinimalResponse

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    post_id: int
    user_id: str
    created_at: datetime
    author: UserMinimalResponse

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content: str
    image_path: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostUpdate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    user_id: str
    created_at: datetime
    author: UserMinimalResponse
    likes_count: int = 0
    comments_count: int = 0
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    user_id: str
    type: str
    reference_id: Optional[str] = None
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    receiver_id: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(BaseModel):
    id: int
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime
    is_read: bool
    sender: UserMinimalResponse
    receiver: UserMinimalResponse

    class Config:
        from_attributes = True
