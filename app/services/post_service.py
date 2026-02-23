from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Post, Comment, Like, Follower, Notification, User
from app.schemas.social import PostCreate, PostUpdate, CommentCreate

def create_post(db: Session, current_user: User, post_in: PostCreate):
    new_post = Post(user_id=current_user.id, content=post_in.content, image_path=post_in.image_path)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

def get_global_feed(db: Session, limit: int = 50, offset: int = 0):
    return db.query(Post).order_by(Post.created_at.desc()).offset(offset).limit(limit).all()

def get_following_feed(db: Session, current_user: User, limit: int = 50, offset: int = 0):
    following_ids = db.query(Follower.following_id).filter(Follower.follower_id == current_user.id).subquery()
    return db.query(Post)\
        .filter(Post.user_id.in_(following_ids))\
        .order_by(Post.created_at.desc())\
        .offset(offset).limit(limit).all()

def get_post_by_id(db: Session, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

def toggle_like(db: Session, current_user: User, post_id: int):
    post = get_post_by_id(db, post_id)
    like = db.query(Like).filter(Like.post_id == post_id, Like.user_id == current_user.id).first()
    
    if like:
        db.delete(like)
        action = "unliked"
    else:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        
        # Notify post owner if it's someone else liking
        if post.user_id != current_user.id:
            notif = Notification(user_id=post.user_id, type="like", reference_id=str(post_id))
            db.add(notif)
            
        action = "liked"
        
    db.commit()
    return {"message": f"Successfully {action} post"}

def create_comment(db: Session, current_user: User, post_id: int, comment_in: CommentCreate):
    post = get_post_by_id(db, post_id)
    
    new_comment = Comment(post_id=post_id, user_id=current_user.id, content=comment_in.content)
    db.add(new_comment)
    
    # Notify host owner
    if post.user_id != current_user.id:
        notif = Notification(user_id=post.user_id, type="comment", reference_id=str(post_id))
        db.add(notif)
        
    db.commit()
    db.refresh(new_comment)
    return new_comment
