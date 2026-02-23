from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.user import UserMinimalResponse
from app.schemas.social import NotificationResponse
from app.routes.deps import get_current_user
from app.services import social_service

router = APIRouter(prefix="/social", tags=["Social"])

@router.post("/follow/{target_user_id}", response_model=dict)
def follow_or_unfollow_user(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle following a specific user."""
    return social_service.toggle_follow(db, current_user, target_user_id)

@router.get("/{target_user_id}/followers", response_model=List[UserMinimalResponse])
def get_user_followers(
    target_user_id: str,
    db: Session = Depends(get_db)
):
    """List of users following a given user."""
    return social_service.get_followers(db, target_user_id)

@router.get("/{target_user_id}/following", response_model=List[UserMinimalResponse])
def get_user_following(
    target_user_id: str,
    db: Session = Depends(get_db)
):
    """List of users the given user is following."""
    return social_service.get_following(db, target_user_id)

@router.get("/notifications", response_model=List[NotificationResponse])
def get_my_notifications(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch notifications for the current user."""
    return social_service.get_notifications(db, current_user, limit)

@router.put("/notifications/read", response_model=dict)
def mark_my_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks all unread notifications as read."""
    return social_service.mark_notifications_read(db, current_user)
