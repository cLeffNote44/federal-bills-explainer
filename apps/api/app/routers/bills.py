from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
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
def list_bills(q: str | None = Query(default=None), status: str | None = Query(default=None),
               page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
               db: Session = Depends(get_db)):
    stmt = select(Bill)
    if q:
        stmt = stmt.where(or_(Bill.title.ilike(f"%{q}%"), Bill.summary.ilike(f"%{q}%")))
    if status:
        stmt = stmt.where(Bill.status == status)
    stmt = stmt.order_by(Bill.latest_action_date.desc().nullslast()).limit(page_size).offset((page-1)*page_size)
    items = db.execute(stmt).scalars().all()
    return [{"congress": b.congress, "bill_type": b.bill_type, "number": b.number, "title": b.title, "public_law_number": b.public_law_number} for b in items]

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

