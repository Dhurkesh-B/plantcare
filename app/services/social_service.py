from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User, Follower, Notification

def toggle_follow(db: Session, current_user: User, target_user_id: str):
    if current_user.id == target_user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
        
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    follow_record = db.query(Follower)\
        .filter(Follower.follower_id == current_user.id, Follower.following_id == target_user_id).first()
        
    if follow_record:
        db.delete(follow_record)
        action = "unfollowed"
    else:
        new_follow = Follower(follower_id=current_user.id, following_id=target_user_id)
        db.add(new_follow)
        
        # Insert Notification
        notif = Notification(user_id=target_user_id, type="follow", reference_id=str(current_user.id))
        db.add(notif)
        
        action = "followed"
        
    db.commit()
    return {"message": f"Successfully {action} user"}

def get_followers(db: Session, target_user_id: str):
    # Get users who follow this target string
    followers = db.query(User).join(Follower, Follower.follower_id == User.id)\
        .filter(Follower.following_id == target_user_id).all()
    return followers

def get_following(db: Session, target_user_id: str):
    following = db.query(User).join(Follower, Follower.following_id == User.id)\
        .filter(Follower.follower_id == target_user_id).all()
    return following

def get_notifications(db: Session, current_user: User, limit: int = 20):
    return db.query(Notification)\
        .filter(Notification.user_id == current_user.id)\
        .order_by(Notification.created_at.desc())\
        .limit(limit).all()

def mark_notifications_read(db: Session, current_user: User):
    db.query(Notification)\
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)\
        .update({"is_read": True})
    db.commit()
    return {"message": "Notifications marked as read"}
