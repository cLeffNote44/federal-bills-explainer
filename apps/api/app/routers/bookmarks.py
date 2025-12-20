"""Bookmarks router for saving bills."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import UserBookmark, Bill

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


class BookmarkRequest(BaseModel):
    bill_id: str
    congress: int
    bill_type: str
    number: int
    notes: Optional[str] = None
    folder: Optional[str] = None


class BookmarkResponse(BaseModel):
    id: str
    bill_id: str
    created_at: str
    notes: Optional[str]
    folder: Optional[str]


class BookmarkedBillResponse(BaseModel):
    id: str
    congress: int
    bill_type: str
    number: int
    title: str
    status: Optional[str]
    public_law_number: Optional[str]
    bookmark_id: str
    bookmarked_at: str
    notes: Optional[str]
    folder: Optional[str]


class CheckBookmarkResponse(BaseModel):
    is_bookmarked: bool
    bookmark_id: Optional[str] = None


@router.post("", response_model=BookmarkResponse)
def create_bookmark(
    request: BookmarkRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Bookmark a bill."""
    user = get_authenticated_user(authorization, db)

    # Check if bill exists
    bill = db.query(Bill).filter(Bill.id == request.bill_id).first()
    if not bill:
        # Try to find by identifiers
        bill = db.query(Bill).filter(
            Bill.congress == request.congress,
            Bill.bill_type == request.bill_type,
            Bill.number == request.number
        ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Check for existing bookmark
    existing = db.query(UserBookmark).filter(
        UserBookmark.user_id == user.id,
        UserBookmark.bill_id == bill.id
    ).first()

    if existing:
        # Update existing bookmark
        if request.notes is not None:
            existing.notes = request.notes
        if request.folder is not None:
            existing.folder = request.folder
        db.commit()
        db.refresh(existing)
        return BookmarkResponse(
            id=existing.id,
            bill_id=existing.bill_id,
            created_at=existing.created_at.isoformat(),
            notes=existing.notes,
            folder=existing.folder
        )

    # Create new bookmark
    bookmark = UserBookmark(
        user_id=user.id,
        bill_id=bill.id,
        notes=request.notes,
        folder=request.folder,
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return BookmarkResponse(
        id=bookmark.id,
        bill_id=bookmark.bill_id,
        created_at=bookmark.created_at.isoformat(),
        notes=bookmark.notes,
        folder=bookmark.folder
    )


@router.get("", response_model=List[BookmarkedBillResponse])
def list_bookmarks(
    folder: Optional[str] = None,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """List all bookmarked bills for current user."""
    user = get_authenticated_user(authorization, db)

    query = db.query(UserBookmark, Bill).join(
        Bill, UserBookmark.bill_id == Bill.id
    ).filter(
        UserBookmark.user_id == user.id
    )

    if folder:
        query = query.filter(UserBookmark.folder == folder)

    query = query.order_by(UserBookmark.created_at.desc())
    results = query.all()

    return [
        BookmarkedBillResponse(
            id=bill.id,
            congress=bill.congress,
            bill_type=bill.bill_type,
            number=bill.number,
            title=bill.title,
            status=bill.status,
            public_law_number=bill.public_law_number,
            bookmark_id=bookmark.id,
            bookmarked_at=bookmark.created_at.isoformat(),
            notes=bookmark.notes,
            folder=bookmark.folder
        )
        for bookmark, bill in results
    ]


@router.get("/check/{congress}/{bill_type}/{number}", response_model=CheckBookmarkResponse)
def check_bookmark(
    congress: int,
    bill_type: str,
    number: int,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Check if a bill is bookmarked."""
    user = get_authenticated_user(authorization, db)

    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        return CheckBookmarkResponse(is_bookmarked=False)

    bookmark = db.query(UserBookmark).filter(
        UserBookmark.user_id == user.id,
        UserBookmark.bill_id == bill.id
    ).first()

    return CheckBookmarkResponse(
        is_bookmarked=bookmark is not None,
        bookmark_id=bookmark.id if bookmark else None
    )


@router.delete("/{congress}/{bill_type}/{number}")
def delete_bookmark(
    congress: int,
    bill_type: str,
    number: int,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Remove a bookmark."""
    user = get_authenticated_user(authorization, db)

    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    bookmark = db.query(UserBookmark).filter(
        UserBookmark.user_id == user.id,
        UserBookmark.bill_id == bill.id
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()

    return {"message": "Bookmark removed"}


@router.get("/folders")
def list_folders(authorization: str = None, db: Session = Depends(get_db)):
    """List all bookmark folders for current user."""
    user = get_authenticated_user(authorization, db)

    folders = db.query(UserBookmark.folder).filter(
        UserBookmark.user_id == user.id,
        UserBookmark.folder.isnot(None)
    ).distinct().all()

    return [f[0] for f in folders if f[0]]
