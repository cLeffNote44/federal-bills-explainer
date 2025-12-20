from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, func
from datetime import date
from typing import List, Optional
from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import Bill, Embedding
from fbx_core.services.embeddings import embed_text
from fbx_core.utils.settings import Settings

router = APIRouter()
settings = Settings()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def list_bills(
    q: Optional[str] = Query(default=None, description="Search query for title/summary"),
    status: Optional[str] = Query(default=None, description="Filter by bill status"),
    congress: Optional[int] = Query(default=None, description="Filter by congress number"),
    bill_type: Optional[str] = Query(default=None, description="Filter by bill type (hr, s, hjres, sjres)"),
    date_from: Optional[date] = Query(default=None, description="Filter bills introduced after this date"),
    date_to: Optional[date] = Query(default=None, description="Filter bills introduced before this date"),
    has_public_law: Optional[bool] = Query(default=None, description="Filter bills that became law"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="date", regex="^(date|congress|number)$", description="Sort by: date, congress, or number"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    """
    List bills with advanced filtering and sorting.

    Supports filtering by:
    - Search query (title/summary)
    - Status
    - Congress number
    - Bill type
    - Date range
    - Public law status
    """
    stmt = select(Bill)

    # Apply filters
    conditions = []

    if q:
        conditions.append(or_(
            Bill.title.ilike(f"%{q}%"),
            Bill.summary.ilike(f"%{q}%")
        ))

    if status:
        conditions.append(Bill.status == status)

    if congress:
        conditions.append(Bill.congress == congress)

    if bill_type:
        conditions.append(Bill.bill_type == bill_type.lower())

    if date_from:
        conditions.append(Bill.introduced_date >= date_from)

    if date_to:
        conditions.append(Bill.introduced_date <= date_to)

    if has_public_law is not None:
        if has_public_law:
            conditions.append(Bill.public_law_number.isnot(None))
        else:
            conditions.append(Bill.public_law_number.is_(None))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Apply sorting
    if sort_by == "date":
        order_column = Bill.latest_action_date.desc() if sort_order == "desc" else Bill.latest_action_date.asc()
        stmt = stmt.order_by(order_column.nullslast())
    elif sort_by == "congress":
        order_column = Bill.congress.desc() if sort_order == "desc" else Bill.congress.asc()
        stmt = stmt.order_by(order_column, Bill.number.desc())
    elif sort_by == "number":
        order_column = Bill.number.desc() if sort_order == "desc" else Bill.number.asc()
        stmt = stmt.order_by(Bill.congress.desc(), order_column)

    # Apply pagination
    stmt = stmt.limit(page_size).offset((page-1)*page_size)

    items = db.execute(stmt).scalars().all()

    return [{
        "congress": b.congress,
        "bill_type": b.bill_type,
        "number": b.number,
        "title": b.title,
        "summary": b.summary,
        "status": b.status,
        "introduced_date": b.introduced_date.isoformat() if b.introduced_date else None,
        "latest_action_date": b.latest_action_date.isoformat() if b.latest_action_date else None,
        "public_law_number": b.public_law_number
    } for b in items]

@router.get("/{congress}/{bill_type}/{number}")
def get_bill(congress: int, bill_type: str, number: int, db: Session = Depends(get_db)):
    stmt = select(Bill).where(Bill.congress==congress, Bill.bill_type==bill_type, Bill.number==number)
    bill = db.execute(stmt).scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    expl = None
    if bill.explanations:
        expl = sorted(bill.explanations, key=lambda e: e.generated_at, reverse=True)[0].text
    return {
        "bill": {
            "congress": bill.congress, "bill_type": bill.bill_type, "number": bill.number,
            "title": bill.title, "summary": bill.summary, "status": bill.status,
            "public_law_number": bill.public_law_number
        },
        "explanation": expl
    }

@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Autocomplete endpoint for search suggestions.

    Returns quick title-based matches for search input.
    Useful for implementing search-as-you-type functionality.
    """
    if len(q) < 2:
        return []

    # Search in title and bill identifier
    stmt = (
        select(Bill)
        .where(or_(
            Bill.title.ilike(f"%{q}%"),
            func.concat(Bill.bill_type, ' ', Bill.number).ilike(f"%{q}%")
        ))
        .order_by(Bill.latest_action_date.desc().nullslast())
        .limit(limit)
    )

    bills = db.execute(stmt).scalars().all()

    return [{
        "congress": b.congress,
        "bill_type": b.bill_type,
        "number": b.number,
        "title": b.title,
        "identifier": f"{b.bill_type.upper()} {b.number}"
    } for b in bills]


@router.get("/search")
def semantic_search(q: str = Query(...), page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    # Compute query vector
    qvec = embed_text(q, settings.embedding_model)
    # Order by vector distance using pgvector-sqlalchemy helper; pass list not numpy array
    stmt = (
        select(Bill)
        .join(Embedding, Embedding.bill_id == Bill.id)
        .order_by(Embedding.vector.l2_distance(qvec))
        .limit(page_size)
        .offset((page-1)*page_size)
    )
    items = db.execute(stmt).scalars().all()
    return [{"congress": b.congress, "bill_type": b.bill_type, "number": b.number, "title": b.title} for b in items]

