from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Post
from app.schemas.social import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.routes.deps import get_current_user
from app.services import post_service

router = APIRouter(prefix="/posts", tags=["Posts & Feed"])

@router.get("/search", response_model=List[PostResponse])
def search_posts(q: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Search posts globally based on content."""
    if not q.strip():
        return []
    return db.query(Post).filter(Post.content.ilike(f"%{q}%")).order_by(Post.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/feed/global", response_model=List[PostResponse])
def get_global_posts(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Fetch global user posts."""
    return post_service.get_global_feed(db, limit, offset)

@router.get("/feed/following", response_model=List[PostResponse])
def get_following_posts(
    limit: int = 50, 
    offset: int = 0, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Fetch posts from users that I am following."""
    return post_service.get_following_feed(db, current_user, limit, offset)

@router.post("/", response_model=PostResponse)
def create_new_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new text/image post."""
    return post_service.create_post(db, current_user, post_in)

@router.post("/{post_id}/like", response_model=dict)
def like_or_unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle a like for a post."""
    return post_service.toggle_like(db, current_user, post_id)

@router.post("/{post_id}/comments", response_model=CommentResponse)
def add_comment_to_post(
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new comment to a post."""
    return post_service.create_comment(db, current_user, post_id, comment_in)
