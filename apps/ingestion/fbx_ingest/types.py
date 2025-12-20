"""Data transfer objects for ingestion."""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class BillDTO(BaseModel):
    """Bill data transfer object."""
    
    external_id: str = Field(..., description="Unique external ID like 118-hr-1234")
    congress: int = Field(..., description="Congress number")
    bill_type: str = Field(..., description="Bill type (hr, s, hjres, sjres)")
    bill_number: int = Field(..., description="Bill number")
    title: str = Field(..., description="Full title of the bill")
    short_title: Optional[str] = Field(None, description="Short title if available")
    summary: Optional[str] = Field(None, description="Bill summary text")
    law_number: Optional[str] = Field(None, description="Public law number if enacted")
    latest_action_date: Optional[date] = Field(None, description="Date of latest action")
    latest_action_text: Optional[str] = Field(None, description="Text of latest action")
    sponsor: Optional[str] = Field(None, description="Bill sponsor name")
    policy_area: Optional[str] = Field(None, description="Primary policy area")
    text_url: Optional[str] = Field(None, description="URL to bill text")
    govtrack_url: Optional[str] = Field(None, description="GovTrack URL")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw API response")
    
    @classmethod
    def from_congress_api(cls, data: Dict[str, Any]) -> "BillDTO":
        """Create DTO from Congress API response."""
        # Extract congress and type from the bill dict
        congress = data.get("congress", 0)
        bill_type = data.get("type", "").lower()
        bill_number = data.get("number", 0)
        
        # Create external ID
        external_id = f"{congress}-{bill_type}-{bill_number}"
        
        # Extract dates
        latest_action = data.get("latestAction", {})
        action_date = None
        if latest_action.get("actionDate"):
            try:
                action_date = datetime.strptime(
                    latest_action["actionDate"], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                pass
        
        # Extract URLs
        text_url = None
        govtrack_url = None
        if "url" in data:
            govtrack_url = data["url"]
        
        # Look for text versions
        text_versions = data.get("textVersions", [])
        if text_versions and isinstance(text_versions, list):
            for version in text_versions:
                if version.get("type") == "Enrolled Bill":
                    text_url = version.get("url")
                    break
            if not text_url and text_versions:
                text_url = text_versions[0].get("url")
        
        return cls(
            external_id=external_id,
            congress=congress,
            bill_type=bill_type,
            bill_number=bill_number,
            title=data.get("title", ""),
            short_title=data.get("shortTitle"),
            summary=data.get("summary", {}).get("text") if isinstance(data.get("summary"), dict) else None,
            law_number=data.get("laws", [{}])[0].get("number") if data.get("laws") else None,
            latest_action_date=action_date,
            latest_action_text=latest_action.get("text"),
            sponsor=data.get("sponsors", [{}])[0].get("fullName") if data.get("sponsors") else None,
            policy_area=data.get("policyArea", {}).get("name") if isinstance(data.get("policyArea"), dict) else None,
            text_url=text_url,
            govtrack_url=govtrack_url,
            raw_data=data
        )


class ExplanationDTO(BaseModel):
    """Explanation data transfer object."""
    
    bill_external_id: str = Field(..., description="Bill external ID")
    explanation_text: str = Field(..., description="Generated explanation text")
    model_name: str = Field(..., description="Model used for generation")
    sections: Optional[Dict[str, str]] = Field(None, description="Parsed sections")
    word_count: int = Field(..., description="Word count of explanation")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    

class EmbeddingDTO(BaseModel):
    """Embedding data transfer object."""
    
    entity_type: str = Field(..., description="Type of entity (bill, explanation)")
    entity_id: str = Field(..., description="ID of the entity")
    vector: List[float] = Field(..., description="Embedding vector")
    model_name: str = Field(..., description="Model used for embedding")
    dimensions: int = Field(..., description="Vector dimensions")
    text_used: str = Field(..., description="Text that was embedded")
    created_at: datetime = Field(default_factory=datetime.utcnow)
