"""
Export router for downloading bills data in various formats.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from datetime import date
from typing import Optional
import csv
import json
import io

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import Bill

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_filters(stmt, q, status, congress, bill_type, date_from, date_to, has_public_law):
    """Apply common filters to query."""
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

    return stmt


@router.get("/csv")
def export_bills_csv(
    q: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    congress: Optional[int] = Query(default=None),
    bill_type: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    has_public_law: Optional[bool] = Query(default=None),
    limit: int = Query(default=1000, le=10000, description="Maximum number of bills to export"),
    db: Session = Depends(get_db)
):
    """
    Export bills to CSV format.

    Maximum 10,000 bills per export to prevent server overload.
    """
    stmt = select(Bill)
    stmt = apply_filters(stmt, q, status, congress, bill_type, date_from, date_to, has_public_law)
    stmt = stmt.order_by(Bill.latest_action_date.desc().nullslast()).limit(limit)

    bills = db.execute(stmt).scalars().all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Congress',
        'Bill Type',
        'Number',
        'Title',
        'Summary',
        'Status',
        'Introduced Date',
        'Latest Action Date',
        'Public Law Number',
        'Congress URL'
    ])

    # Write data
    for bill in bills:
        writer.writerow([
            bill.congress,
            bill.bill_type.upper(),
            bill.number,
            bill.title,
            bill.summary or '',
            bill.status or '',
            bill.introduced_date.isoformat() if bill.introduced_date else '',
            bill.latest_action_date.isoformat() if bill.latest_action_date else '',
            bill.public_law_number or '',
            bill.congress_url or ''
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=federal_bills_{date.today().isoformat()}.csv"
        }
    )


@router.get("/json")
def export_bills_json(
    q: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    congress: Optional[int] = Query(default=None),
    bill_type: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    has_public_law: Optional[bool] = Query(default=None),
    limit: int = Query(default=1000, le=10000, description="Maximum number of bills to export"),
    include_explanations: bool = Query(default=False, description="Include bill explanations"),
    db: Session = Depends(get_db)
):
    """
    Export bills to JSON format.

    Maximum 10,000 bills per export to prevent server overload.
    Optionally includes explanations (increases file size).
    """
    stmt = select(Bill)
    stmt = apply_filters(stmt, q, status, congress, bill_type, date_from, date_to, has_public_law)
    stmt = stmt.order_by(Bill.latest_action_date.desc().nullslast()).limit(limit)

    bills = db.execute(stmt).scalars().all()

    # Convert to dict
    bills_data = []
    for bill in bills:
        bill_dict = {
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "number": bill.number,
            "title": bill.title,
            "summary": bill.summary,
            "status": bill.status,
            "introduced_date": bill.introduced_date.isoformat() if bill.introduced_date else None,
            "latest_action_date": bill.latest_action_date.isoformat() if bill.latest_action_date else None,
            "public_law_number": bill.public_law_number,
            "congress_url": bill.congress_url,
            "sponsor": bill.sponsor,
            "committees": bill.committees,
            "subjects": bill.subjects,
            "cosponsors_count": bill.cosponsors_count
        }

        if include_explanations and bill.explanations:
            latest_explanation = sorted(bill.explanations, key=lambda e: e.generated_at, reverse=True)[0]
            bill_dict["explanation"] = {
                "text": latest_explanation.text,
                "model": latest_explanation.model_name,
                "generated_at": latest_explanation.generated_at.isoformat() if latest_explanation.generated_at else None
            }

        bills_data.append(bill_dict)

    # Create JSON response
    json_output = json.dumps({
        "export_date": date.today().isoformat(),
        "total_bills": len(bills_data),
        "filters_applied": {
            "query": q,
            "status": status,
            "congress": congress,
            "bill_type": bill_type,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "has_public_law": has_public_law
        },
        "bills": bills_data
    }, indent=2)

    return Response(
        content=json_output,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=federal_bills_{date.today().isoformat()}.json"
        }
    )


@router.get("/{congress}/{bill_type}/{number}/json")
def export_single_bill_json(
    congress: int,
    bill_type: str,
    number: int,
    include_explanation: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    """
    Export a single bill to JSON format with full details.
    """
    stmt = select(Bill).where(
        Bill.congress == congress,
        Bill.bill_type == bill_type,
        Bill.number == number
    )
    bill = db.execute(stmt).scalar_one_or_none()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    bill_dict = {
        "congress": bill.congress,
        "bill_type": bill.bill_type,
        "number": bill.number,
        "title": bill.title,
        "summary": bill.summary,
        "status": bill.status,
        "introduced_date": bill.introduced_date.isoformat() if bill.introduced_date else None,
        "latest_action_date": bill.latest_action_date.isoformat() if bill.latest_action_date else None,
        "public_law_number": bill.public_law_number,
        "congress_url": bill.congress_url,
        "sponsor": bill.sponsor,
        "committees": bill.committees,
        "subjects": bill.subjects,
        "cosponsors_count": bill.cosponsors_count
    }

    if include_explanation and bill.explanations:
        latest_explanation = sorted(bill.explanations, key=lambda e: e.generated_at, reverse=True)[0]
        bill_dict["explanation"] = {
            "text": latest_explanation.text,
            "model": latest_explanation.model_name,
            "generated_at": latest_explanation.generated_at.isoformat() if latest_explanation.generated_at else None
        }

    json_output = json.dumps(bill_dict, indent=2)

    return Response(
        content=json_output,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=bill_{congress}_{bill_type}_{number}.json"
        }
    )
