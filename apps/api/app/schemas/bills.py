"""
Pydantic schemas for bills API with OpenAPI examples.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class BillStatus(str, Enum):
    """Bill status enumeration."""
    INTRODUCED = "introduced"
    IN_COMMITTEE = "in_committee"
    PASSED_HOUSE = "passed_house"
    PASSED_SENATE = "passed_senate"
    ENROLLED = "enrolled"
    VETOED = "vetoed"
    BECAME_LAW = "became_law"


class BillType(str, Enum):
    """Bill type enumeration."""
    HR = "hr"  # House Bill
    S = "s"    # Senate Bill
    HJRES = "hjres"  # House Joint Resolution
    SJRES = "sjres"  # Senate Joint Resolution
    HCONRES = "hconres"  # House Concurrent Resolution
    SCONRES = "sconres"  # Senate Concurrent Resolution
    HRES = "hres"  # House Resolution
    SRES = "sres"  # Senate Resolution


class BillBase(BaseModel):
    """Base bill schema."""
    bill_id: str = Field(..., example="hr1234-118", description="Unique bill identifier")
    title: str = Field(..., example="Infrastructure Investment and Jobs Act", description="Official bill title")
    short_title: Optional[str] = Field(None, example="Infrastructure Act", description="Short title if available")
    summary: str = Field(..., example="A bill to authorize funds for Federal-aid highways...", description="Bill summary")
    bill_type: BillType = Field(..., example=BillType.HR, description="Type of bill")
    introduced_date: date = Field(..., example="2024-01-15", description="Date bill was introduced")
    status: BillStatus = Field(..., example=BillStatus.IN_COMMITTEE, description="Current status of the bill")


class BillCreate(BillBase):
    """Schema for creating a new bill."""
    sponsor_id: str = Field(..., example="M000312", description="ID of the bill sponsor")
    cosponsors: Optional[List[str]] = Field(None, example=["S000148", "C001070"], description="List of cosponsor IDs")
    committees: Optional[List[str]] = Field(None, example=["House Transportation and Infrastructure"], description="Committees involved")
    full_text: Optional[str] = Field(None, description="Full text of the bill")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "bill_id": "hr5678-118",
            "title": "Climate Action Now Act",
            "short_title": "Climate Act",
            "summary": "To require the President to develop and update annually a plan for the United States to meet its nationally determined contribution under the Paris Agreement on climate change.",
            "bill_type": "hr",
            "introduced_date": "2024-02-01",
            "status": "introduced",
            "sponsor_id": "P000197",
            "cosponsors": ["S000148", "M001160"],
            "committees": ["House Committee on Energy and Commerce"]
        }
    })


class BillUpdate(BaseModel):
    """Schema for updating a bill."""
    title: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[BillStatus] = None
    committees: Optional[List[str]] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "passed_house",
            "committees": ["House Committee on Energy and Commerce", "House Committee on Ways and Means"]
        }
    })


class BillResponse(BillBase):
    """Schema for bill response."""
    id: int = Field(..., example=1, description="Database ID")
    sponsor_name: str = Field(..., example="Rep. John Doe", description="Name of the bill sponsor")
    cosponsors_count: int = Field(..., example=25, description="Number of cosponsors")
    last_action: Optional[str] = Field(None, example="Referred to the Committee on Transportation", description="Last recorded action")
    last_action_date: Optional[date] = Field(None, example="2024-01-20", description="Date of last action")
    created_at: datetime = Field(..., example="2024-01-15T10:00:00Z", description="When the record was created")
    updated_at: datetime = Field(..., example="2024-01-20T15:30:00Z", description="When the record was last updated")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "bill_id": "hr1234-118",
                "title": "Infrastructure Investment and Jobs Act",
                "short_title": "Infrastructure Act",
                "summary": "A bill to authorize funds for Federal-aid highways, highway safety programs, and transit programs.",
                "bill_type": "hr",
                "introduced_date": "2024-01-15",
                "status": "passed_house",
                "sponsor_name": "Rep. Peter DeFazio",
                "cosponsors_count": 38,
                "last_action": "Received in the Senate and Read twice and referred to the Committee on Commerce, Science, and Transportation.",
                "last_action_date": "2024-02-10",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-02-10T18:45:00Z"
            }
        }
    )


class BillExplanation(BaseModel):
    """Schema for AI-generated bill explanation."""
    bill_id: str = Field(..., example="hr1234-118", description="Bill identifier")
    explanation: str = Field(..., description="AI-generated explanation")
    key_points: List[str] = Field(..., description="Key points from the bill")
    potential_impact: str = Field(..., description="Potential impact analysis")
    simplified_summary: str = Field(..., description="Simplified summary for general public")
    generated_at: datetime = Field(..., description="When the explanation was generated")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "bill_id": "hr1234-118",
            "explanation": "This bill aims to modernize America's infrastructure by investing in roads, bridges, public transit, and broadband internet...",
            "key_points": [
                "$550 billion in new federal investment",
                "Repairs to 173,000 miles of highways",
                "Replacement of lead pipes nationwide",
                "Expansion of EV charging network"
            ],
            "potential_impact": "This legislation would create approximately 2 million jobs per year and significantly improve transportation infrastructure...",
            "simplified_summary": "This bill will fix roads and bridges, improve public transportation, and bring high-speed internet to more areas.",
            "generated_at": "2024-01-20T12:00:00Z"
        }
    })


class BillSearchParams(BaseModel):
    """Schema for bill search parameters."""
    q: Optional[str] = Field(None, example="healthcare", description="Search query")
    status: Optional[BillStatus] = Field(None, example=BillStatus.IN_COMMITTEE, description="Filter by status")
    bill_type: Optional[BillType] = Field(None, example=BillType.HR, description="Filter by bill type")
    start_date: Optional[date] = Field(None, example="2024-01-01", description="Start date for date range filter")
    end_date: Optional[date] = Field(None, example="2024-12-31", description="End date for date range filter")
    sponsor_id: Optional[str] = Field(None, example="M000312", description="Filter by sponsor ID")
    committee: Optional[str] = Field(None, example="House Transportation", description="Filter by committee")
    skip: int = Field(0, ge=0, example=0, description="Number of records to skip")
    limit: int = Field(10, ge=1, le=100, example=10, description="Maximum number of records to return")


class PaginatedBillsResponse(BaseModel):
    """Schema for paginated bills response."""
    items: List[BillResponse] = Field(..., description="List of bills")
    total: int = Field(..., example=150, description="Total number of bills matching the query")
    skip: int = Field(..., example=0, description="Number of records skipped")
    limit: int = Field(..., example=10, description="Maximum number of records returned")
    has_more: bool = Field(..., example=True, description="Whether there are more results available")