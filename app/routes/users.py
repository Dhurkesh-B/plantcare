from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Follower, Post, Prediction
from app.schemas.user import UserResponse, UserUpdate, UserMinimalResponse
from app.routes.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/search", response_model=List[UserMinimalResponse])
def search_users(q: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not q.strip():
        return []
    # Search by username or name
    results = db.query(User).filter(User.username.ilike(f"%{q}%") | User.name.ilike(f"%{q}%")).all()
    
    following_ids = {f.following_id for f in db.query(Follower).filter(Follower.follower_id == current_user.id).all()}
    for u in results:
        u.is_following = u.id in following_ids
        
    return results

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Calculate followers/following counts
    followers_count = db.query(Follower).filter(Follower.following_id == current_user.id).count()
    following_count = db.query(Follower).filter(Follower.follower_id == current_user.id).count()
    
    # We can inject them, though it's technically a modification of the model dump before returning
    current_user.followers_count = followers_count
    current_user.following_count = following_count
    return current_user

@router.put("/me", response_model=UserResponse)
def update_my_profile(update_data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if update_data.name is not None:
        current_user.name = update_data.name
    if update_data.bio is not None:
        current_user.bio = update_data.bio
    if update_data.profile_image is not None:
        current_user.profile_image = update_data.profile_image
        
    db.commit()
    db.refresh(current_user)
    
    current_user.followers_count = db.query(Follower).filter(Follower.following_id == current_user.id).count()
    current_user.following_count = db.query(Follower).filter(Follower.follower_id == current_user.id).count()
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.followers_count = db.query(Follower).filter(Follower.following_id == user.id).count()
    user.following_count = db.query(Follower).filter(Follower.follower_id == user.id).count()
    
    user.is_following = db.query(Follower).filter(
        Follower.follower_id == current_user.id, 
        Follower.following_id == user.id
    ).first() is not None
    
    return user
