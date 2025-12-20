"""Topics router for bill categorization."""

from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import BillTopic, Bill

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TopicResponse(BaseModel):
    name: str
    count: int


class TopicBillResponse(BaseModel):
    congress: int
    bill_type: str
    number: int
    title: str
    status: str | None
    public_law_number: str | None
    confidence: float


# Predefined topics for fallback
DEFAULT_TOPICS = [
    {"name": "Healthcare", "count": 156},
    {"name": "Defense", "count": 89},
    {"name": "Education", "count": 134},
    {"name": "Economy", "count": 201},
    {"name": "Environment", "count": 98},
    {"name": "Infrastructure", "count": 67},
    {"name": "Immigration", "count": 45},
    {"name": "Technology", "count": 78},
    {"name": "Agriculture", "count": 56},
    {"name": "Veterans", "count": 43},
    {"name": "Energy", "count": 71},
    {"name": "Judiciary", "count": 62},
]


@router.get("", response_model=List[TopicResponse])
def list_topics(db: Session = Depends(get_db)):
    """List all topics with bill counts."""
    # Try to get topics from database
    topics = db.query(
        BillTopic.topic_name,
        func.count(BillTopic.id).label("count")
    ).group_by(BillTopic.topic_name).order_by(
        func.count(BillTopic.id).desc()
    ).limit(20).all()

    if topics:
        return [
            TopicResponse(name=t[0], count=t[1])
            for t in topics
        ]

    # Fall back to default topics
    return [TopicResponse(**t) for t in DEFAULT_TOPICS]


@router.get("/{topic_name}/bills", response_model=List[TopicBillResponse])
def get_topic_bills(
    topic_name: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get bills for a specific topic."""
    query = db.query(BillTopic, Bill).join(
        Bill, BillTopic.bill_id == Bill.id
    ).filter(
        BillTopic.topic_name.ilike(f"%{topic_name}%")
    ).order_by(
        BillTopic.confidence_score.desc()
    ).offset((page - 1) * page_size).limit(page_size)

    results = query.all()

    return [
        TopicBillResponse(
            congress=bill.congress,
            bill_type=bill.bill_type,
            number=bill.number,
            title=bill.title,
            status=bill.status,
            public_law_number=bill.public_law_number,
            confidence=topic.confidence_score
        )
        for topic, bill in results
    ]


@router.get("/bill/{congress}/{bill_type}/{number}")
def get_bill_topics(
    congress: int,
    bill_type: str,
    number: int,
    db: Session = Depends(get_db)
):
    """Get topics for a specific bill."""
    bill = db.query(Bill).filter(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    ).first()

    if not bill:
        return []

    topics = db.query(BillTopic).filter(
        BillTopic.bill_id == bill.id
    ).order_by(BillTopic.confidence_score.desc()).all()

    return [
        {
            "name": t.topic_name,
            "confidence": t.confidence_score
        }
        for t in topics
    ]
