"""Comments router for community discussions on bills."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import Comment, Bill, User

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_authenticated_user(authorization: str, db: Session):
    """Get authenticated user from token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    from .auth import get_current_user
    token = authorization.split(" ")[1]
    return get_current_user(token, db)


def get_optional_user(authorization: Optional[str], db: Session):
    """Get user if authenticated, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        from .auth import get_current_user
        token = authorization.split(" ")[1]
        return get_current_user(token, db)
    except:
        return None


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[str] = None


class UpdateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class AuthorResponse(BaseModel):
    id: str
    display_name: str


class CommentResponse(BaseModel):
    id: str
    bill_id: str
    content: str
    author: AuthorResponse
    parent_id: Optional[str]
    created_at: str
    updated_at: Optional[str]
    upvotes: int
    is_edited: bool
    replies_count: int
    user_has_upvoted: bool = False


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int


@router.post("/{congress}/{bill_type}/{number}", response_model=CommentResponse)
def create_comment(
    congress: int,
    bill_type: str,
    number: int,
    request: CreateCommentRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Create a new comment on a bill."""
    user = get_authenticated_user(authorization, db)

    # Find the bill
    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Validate parent comment if provided
    if request.parent_id:
        parent = db.query(Comment).filter(
            Comment.id == request.parent_id,
            Comment.bill_id == bill.id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    # Create comment
    comment = Comment(
        bill_id=bill.id,
        user_id=user.id,
        content=request.content,
        parent_id=request.parent_id,
        upvotes=0,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        bill_id=comment.bill_id,
        content=comment.content,
        author=AuthorResponse(
            id=user.id,
            display_name=user.display_name or user.email.split('@')[0]
        ),
        parent_id=comment.parent_id,
        created_at=comment.created_at.isoformat(),
        updated_at=None,
        upvotes=0,
        is_edited=False,
        replies_count=0,
        user_has_upvoted=False
    )


@router.get("/{congress}/{bill_type}/{number}", response_model=CommentListResponse)
def get_comments(
    congress: int,
    bill_type: str,
    number: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    sort_by: str = Query(default="newest", regex="^(newest|oldest|popular)$"),
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get comments for a bill."""
    current_user = get_optional_user(authorization, db)

    # Find the bill
    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Base query for top-level comments only
    query = db.query(Comment, User).join(
        User, Comment.user_id == User.id
    ).filter(
        Comment.bill_id == bill.id,
        Comment.parent_id.is_(None)  # Only top-level comments
    )

    # Count total
    total = db.query(func.count(Comment.id)).filter(
        Comment.bill_id == bill.id,
        Comment.parent_id.is_(None)
    ).scalar()

    # Apply sorting
    if sort_by == "newest":
        query = query.order_by(Comment.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Comment.created_at.asc())
    elif sort_by == "popular":
        query = query.order_by(Comment.upvotes.desc(), Comment.created_at.desc())

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    results = query.all()

    # Get replies count for each comment
    comments = []
    for comment, author in results:
        replies_count = db.query(func.count(Comment.id)).filter(
            Comment.parent_id == comment.id
        ).scalar()

        # Check if user has upvoted (simplified - would need upvote tracking table)
        user_has_upvoted = False

        comments.append(CommentResponse(
            id=comment.id,
            bill_id=comment.bill_id,
            content=comment.content,
            author=AuthorResponse(
                id=author.id,
                display_name=author.display_name or author.email.split('@')[0]
            ),
            parent_id=comment.parent_id,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat() if comment.updated_at else None,
            upvotes=comment.upvotes,
            is_edited=comment.updated_at is not None,
            replies_count=replies_count,
            user_has_upvoted=user_has_upvoted
        ))

    return CommentListResponse(
        comments=comments,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{congress}/{bill_type}/{number}/replies/{comment_id}", response_model=List[CommentResponse])
def get_replies(
    congress: int,
    bill_type: str,
    number: int,
    comment_id: str,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get replies to a specific comment."""
    current_user = get_optional_user(authorization, db)

    replies = db.query(Comment, User).join(
        User, Comment.user_id == User.id
    ).filter(
        Comment.parent_id == comment_id
    ).order_by(Comment.created_at.asc()).all()

    return [
        CommentResponse(
            id=comment.id,
            bill_id=comment.bill_id,
            content=comment.content,
            author=AuthorResponse(
                id=author.id,
                display_name=author.display_name or author.email.split('@')[0]
            ),
            parent_id=comment.parent_id,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat() if comment.updated_at else None,
            upvotes=comment.upvotes,
            is_edited=comment.updated_at is not None,
            replies_count=0,  # No nested replies for now
            user_has_upvoted=False
        )
        for comment, author in replies
    ]


@router.put("/{congress}/{bill_type}/{number}/{comment_id}", response_model=CommentResponse)
def update_comment(
    congress: int,
    bill_type: str,
    number: int,
    comment_id: str,
    request: UpdateCommentRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Update a comment (only by author)."""
    user = get_authenticated_user(authorization, db)

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    comment.content = request.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)

    replies_count = db.query(func.count(Comment.id)).filter(
        Comment.parent_id == comment.id
    ).scalar()

    return CommentResponse(
        id=comment.id,
        bill_id=comment.bill_id,
        content=comment.content,
        author=AuthorResponse(
            id=user.id,
            display_name=user.display_name or user.email.split('@')[0]
        ),
        parent_id=comment.parent_id,
        created_at=comment.created_at.isoformat(),
        updated_at=comment.updated_at.isoformat(),
        upvotes=comment.upvotes,
        is_edited=True,
        replies_count=replies_count,
        user_has_upvoted=False
    )


@router.delete("/{congress}/{bill_type}/{number}/{comment_id}")
def delete_comment(
    congress: int,
    bill_type: str,
    number: int,
    comment_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Delete a comment (only by author or admin)."""
    user = get_authenticated_user(authorization, db)

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check authorization (author or admin)
    is_admin = hasattr(user, 'role') and user.role == 'admin'
    if comment.user_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    # Delete replies first
    db.query(Comment).filter(Comment.parent_id == comment.id).delete()

    # Delete the comment
    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted"}


@router.post("/{congress}/{bill_type}/{number}/{comment_id}/upvote")
def upvote_comment(
    congress: int,
    bill_type: str,
    number: int,
    comment_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Upvote a comment."""
    user = get_authenticated_user(authorization, db)

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Simple increment (in production, would track per-user upvotes)
    comment.upvotes = (comment.upvotes or 0) + 1
    db.commit()

    return {"upvotes": comment.upvotes}


@router.delete("/{congress}/{bill_type}/{number}/{comment_id}/upvote")
def remove_upvote(
    congress: int,
    bill_type: str,
    number: int,
    comment_id: str,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Remove upvote from a comment."""
    user = get_authenticated_user(authorization, db)

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Simple decrement (in production, would track per-user upvotes)
    if comment.upvotes and comment.upvotes > 0:
        comment.upvotes -= 1
        db.commit()

    return {"upvotes": comment.upvotes}
