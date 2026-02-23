from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models import User
from app.models.social import Message
from app.schemas.social import MessageCreate, MessageResponse
from app.schemas.user import UserMinimalResponse
from app.routes.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=MessageResponse)
def send_message(
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a direct message to a user."""
    # Verify receiver exists
    receiver = db.query(User).filter(User.id == message_in.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
        
    new_message = Message(
        sender_id=current_user.id,
        receiver_id=message_in.receiver_id,
        content=message_in.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.get("/{other_user_id}", response_model=List[MessageResponse])
def get_conversation(
    other_user_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history with a specific user."""
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    
    # Mark as read if we are the receiver
    unread_messages = [m for m in messages if m.receiver_id == current_user.id and not m.is_read]
    if unread_messages:
        for m in unread_messages:
            m.is_read = True
        db.commit()
        
    return messages

@router.get("/users/recent", response_model=List[UserMinimalResponse])
def get_recent_chat_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a list of users the current user has chatted with recently."""
    # This is a bit complex in pure ORM without subqueries, so we do Python side for simplicity in SQLite
    messages = db.query(Message).filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()
    
    unique_user_ids = []
    for m in messages:
        other_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in unique_user_ids:
            unique_user_ids.append(other_id)
            
    users = db.query(User).filter(User.id.in_(unique_user_ids)).all()
    # Sort them back into the recent order
    user_dict = {u.id: u for u in users}
    sorted_users = [user_dict[uid] for uid in unique_user_ids if uid in user_dict]
    
    return sorted_users
