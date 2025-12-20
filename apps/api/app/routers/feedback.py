"""Feedback router for explanation ratings."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import ExplanationFeedback, Explanation

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FeedbackRequest(BaseModel):
    explanation_id: str
    bill_id: str
    is_helpful: bool
    feedback_text: Optional[str] = None
    session_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    is_helpful: bool
    created_at: str


class FeedbackStats(BaseModel):
    total: int
    helpful: int
    not_helpful: int
    helpful_percentage: float


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    request: FeedbackRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Submit feedback for an explanation."""
    # Extract user_id from token if authenticated
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        from .auth import get_current_user
        try:
            token = authorization.split(" ")[1]
            user = get_current_user(token, db)
            user_id = user.id
        except Exception:
            pass

    # Check if explanation exists
    explanation = db.query(Explanation).filter(
        Explanation.id == request.explanation_id
    ).first()
    if not explanation:
        raise HTTPException(status_code=404, detail="Explanation not found")

    # Check for existing feedback from this user/session
    existing = None
    if user_id:
        existing = db.query(ExplanationFeedback).filter(
            ExplanationFeedback.explanation_id == request.explanation_id,
            ExplanationFeedback.user_id == user_id
        ).first()
    elif request.session_id:
        existing = db.query(ExplanationFeedback).filter(
            ExplanationFeedback.explanation_id == request.explanation_id,
            ExplanationFeedback.session_id == request.session_id
        ).first()

    if existing:
        # Update existing feedback
        existing.is_helpful = request.is_helpful
        existing.feedback_text = request.feedback_text
        db.commit()
        db.refresh(existing)
        return FeedbackResponse(
            id=existing.id,
            is_helpful=existing.is_helpful,
            created_at=existing.created_at.isoformat()
        )

    # Create new feedback
    feedback = ExplanationFeedback(
        explanation_id=request.explanation_id,
        user_id=user_id,
        session_id=request.session_id if not user_id else None,
        is_helpful=request.is_helpful,
        feedback_text=request.feedback_text,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        is_helpful=feedback.is_helpful,
        created_at=feedback.created_at.isoformat()
    )


@router.get("/stats/{explanation_id}", response_model=FeedbackStats)
def get_feedback_stats(explanation_id: str, db: Session = Depends(get_db)):
    """Get feedback statistics for an explanation."""
    total = db.query(func.count(ExplanationFeedback.id)).filter(
        ExplanationFeedback.explanation_id == explanation_id
    ).scalar()

    helpful = db.query(func.count(ExplanationFeedback.id)).filter(
        ExplanationFeedback.explanation_id == explanation_id,
        ExplanationFeedback.is_helpful == True
    ).scalar()

    return FeedbackStats(
        total=total,
        helpful=helpful,
        not_helpful=total - helpful,
        helpful_percentage=round((helpful / total * 100) if total > 0 else 0, 1)
    )
