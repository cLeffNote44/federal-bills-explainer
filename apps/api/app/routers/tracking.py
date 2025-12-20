"""Bill tracking router for notifications and updates."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import UserBillTracking, Bill

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


class TrackBillRequest(BaseModel):
    congress: int
    bill_type: str
    number: int
    notify_on_status_change: bool = True
    notify_on_vote: bool = True
    notify_on_amendments: bool = False
    email_notifications: bool = False


class TrackingResponse(BaseModel):
    id: str
    bill_id: str
    congress: int
    bill_type: str
    number: int
    title: str
    status: Optional[str]
    notify_on_status_change: bool
    notify_on_vote: bool
    notify_on_amendments: bool
    email_notifications: bool
    created_at: str
    last_checked: Optional[str]


class TrackedBillUpdate(BaseModel):
    bill_id: str
    congress: int
    bill_type: str
    number: int
    title: str
    update_type: str  # status_change, vote, amendment
    old_value: Optional[str]
    new_value: str
    update_date: str


class CheckTrackingResponse(BaseModel):
    is_tracking: bool
    tracking_id: Optional[str] = None


@router.post("", response_model=TrackingResponse)
def track_bill(
    request: TrackBillRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Start tracking a bill for updates."""
    user = get_authenticated_user(authorization, db)

    # Find the bill
    bill = db.query(Bill).filter(
        Bill.congress == request.congress,
        Bill.bill_type == request.bill_type,
        Bill.number == request.number
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Check for existing tracking
    existing = db.query(UserBillTracking).filter(
        UserBillTracking.user_id == user.id,
        UserBillTracking.bill_id == bill.id
    ).first()

    if existing:
        # Update existing tracking preferences
        existing.notify_on_status_change = request.notify_on_status_change
        existing.notify_on_vote = request.notify_on_vote
        existing.notify_on_amendments = request.notify_on_amendments
        existing.email_notifications = request.email_notifications
        db.commit()
        db.refresh(existing)

        return TrackingResponse(
            id=existing.id,
            bill_id=existing.bill_id,
            congress=bill.congress,
            bill_type=bill.bill_type,
            number=bill.number,
            title=bill.title,
            status=bill.status,
            notify_on_status_change=existing.notify_on_status_change,
            notify_on_vote=existing.notify_on_vote,
            notify_on_amendments=existing.notify_on_amendments,
            email_notifications=existing.email_notifications,
            created_at=existing.created_at.isoformat(),
            last_checked=existing.last_checked.isoformat() if existing.last_checked else None
        )

    # Create new tracking
    tracking = UserBillTracking(
        user_id=user.id,
        bill_id=bill.id,
        notify_on_status_change=request.notify_on_status_change,
        notify_on_vote=request.notify_on_vote,
        notify_on_amendments=request.notify_on_amendments,
        email_notifications=request.email_notifications,
    )
    db.add(tracking)
    db.commit()
    db.refresh(tracking)

    return TrackingResponse(
        id=tracking.id,
        bill_id=tracking.bill_id,
        congress=bill.congress,
        bill_type=bill.bill_type,
        number=bill.number,
        title=bill.title,
        status=bill.status,
        notify_on_status_change=tracking.notify_on_status_change,
        notify_on_vote=tracking.notify_on_vote,
        notify_on_amendments=tracking.notify_on_amendments,
        email_notifications=tracking.email_notifications,
        created_at=tracking.created_at.isoformat(),
        last_checked=None
    )


@router.get("", response_model=List[TrackingResponse])
def list_tracked_bills(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """List all tracked bills for current user."""
    user = get_authenticated_user(authorization, db)

    trackings = db.query(UserBillTracking, Bill).join(
        Bill, UserBillTracking.bill_id == Bill.id
    ).filter(
        UserBillTracking.user_id == user.id
    ).order_by(UserBillTracking.created_at.desc()).all()

    return [
        TrackingResponse(
            id=tracking.id,
            bill_id=tracking.bill_id,
            congress=bill.congress,
            bill_type=bill.bill_type,
            number=bill.number,
            title=bill.title,
            status=bill.status,
            notify_on_status_change=tracking.notify_on_status_change,
            notify_on_vote=tracking.notify_on_vote,
            notify_on_amendments=tracking.notify_on_amendments,
            email_notifications=tracking.email_notifications,
            created_at=tracking.created_at.isoformat(),
            last_checked=tracking.last_checked.isoformat() if tracking.last_checked else None
        )
        for tracking, bill in trackings
    ]


@router.get("/check/{congress}/{bill_type}/{number}", response_model=CheckTrackingResponse)
def check_tracking(
    congress: int,
    bill_type: str,
    number: int,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Check if a bill is being tracked."""
    user = get_authenticated_user(authorization, db)

    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        return CheckTrackingResponse(is_tracking=False)

    tracking = db.query(UserBillTracking).filter(
        UserBillTracking.user_id == user.id,
        UserBillTracking.bill_id == bill.id
    ).first()

    return CheckTrackingResponse(
        is_tracking=tracking is not None,
        tracking_id=tracking.id if tracking else None
    )


@router.get("/updates", response_model=List[TrackedBillUpdate])
def get_bill_updates(
    since_hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get recent updates for tracked bills."""
    user = get_authenticated_user(authorization, db)

    since_date = datetime.utcnow() - timedelta(hours=since_hours)

    # Get all tracked bills
    trackings = db.query(UserBillTracking, Bill).join(
        Bill, UserBillTracking.bill_id == Bill.id
    ).filter(
        UserBillTracking.user_id == user.id
    ).all()

    updates = []

    for tracking, bill in trackings:
        # Check if bill was updated recently
        if hasattr(bill, 'updated_at') and bill.updated_at:
            if bill.updated_at >= since_date:
                # Determine update type
                update_type = "status_change"
                if tracking.last_checked:
                    # Compare current status with last known
                    updates.append(TrackedBillUpdate(
                        bill_id=bill.id,
                        congress=bill.congress,
                        bill_type=bill.bill_type,
                        number=bill.number,
                        title=bill.title,
                        update_type=update_type,
                        old_value=None,
                        new_value=bill.status or "Updated",
                        update_date=bill.updated_at.isoformat()
                    ))

        # Update last_checked timestamp
        tracking.last_checked = datetime.utcnow()

    db.commit()
    return updates


@router.delete("/{congress}/{bill_type}/{number}")
def stop_tracking(
    congress: int,
    bill_type: str,
    number: int,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Stop tracking a bill."""
    user = get_authenticated_user(authorization, db)

    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    tracking = db.query(UserBillTracking).filter(
        UserBillTracking.user_id == user.id,
        UserBillTracking.bill_id == bill.id
    ).first()

    if not tracking:
        raise HTTPException(status_code=404, detail="Not tracking this bill")

    db.delete(tracking)
    db.commit()

    return {"message": "Stopped tracking bill"}


@router.patch("/{congress}/{bill_type}/{number}")
def update_tracking_preferences(
    congress: int,
    bill_type: str,
    number: int,
    notify_on_status_change: Optional[bool] = None,
    notify_on_vote: Optional[bool] = None,
    notify_on_amendments: Optional[bool] = None,
    email_notifications: Optional[bool] = None,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Update tracking notification preferences."""
    user = get_authenticated_user(authorization, db)

    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    tracking = db.query(UserBillTracking).filter(
        UserBillTracking.user_id == user.id,
        UserBillTracking.bill_id == bill.id
    ).first()

    if not tracking:
        raise HTTPException(status_code=404, detail="Not tracking this bill")

    # Update preferences
    if notify_on_status_change is not None:
        tracking.notify_on_status_change = notify_on_status_change
    if notify_on_vote is not None:
        tracking.notify_on_vote = notify_on_vote
    if notify_on_amendments is not None:
        tracking.notify_on_amendments = notify_on_amendments
    if email_notifications is not None:
        tracking.email_notifications = email_notifications

    db.commit()
    db.refresh(tracking)

    return {
        "message": "Preferences updated",
        "notify_on_status_change": tracking.notify_on_status_change,
        "notify_on_vote": tracking.notify_on_vote,
        "notify_on_amendments": tracking.notify_on_amendments,
        "email_notifications": tracking.email_notifications
    }
