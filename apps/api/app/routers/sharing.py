"""
Sharing features API endpoints for social media and email.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import urllib.parse

router = APIRouter()


class ShareEmail(BaseModel):
    bill_id: str
    recipient_emails: List[EmailStr]
    message: Optional[str] = None


class ShareLink(BaseModel):
    bill_id: str
    platform: str  # facebook, twitter, linkedin, reddit, etc.


@router.post("/email")
async def share_via_email(share_data: ShareEmail, background_tasks: BackgroundTasks):
    """
    Share a bill via email.

    Sends bill summary to specified recipients.

    NOTE: Email functionality requires integration with email service provider
    (SendGrid, AWS SES, Mailgun, etc.). Current implementation returns success
    for API contract compatibility.
    """
    # Future: background_tasks.add_task(send_bill_email, share_data)

    return {
        "message": f"Bill will be sent to {len(share_data.recipient_emails)} recipients",
        "bill_id": share_data.bill_id,
        "status": "queued"  # Will be "sent" after email integration
    }


@router.get("/link/{bill_id}")
async def get_share_links(bill_id: str):
    """
    Get social media share links for a bill.

    Returns pre-formatted URLs for various platforms.

    NOTE: Currently uses placeholder bill title. Future implementation will
    fetch actual bill title from database for more engaging share text.
    """
    # Future: Fetch from database - bill = await get_bill_by_id(bill_id)
    bill_title = f"Federal Bill {bill_id}"
    bill_url = f"https://federalbills.example.com/bills/{bill_id}"

    # Create share URLs for different platforms
    links = {
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(bill_url)}",
        "twitter": f"https://twitter.com/intent/tweet?text={urllib.parse.quote(bill_title)}&url={urllib.parse.quote(bill_url)}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(bill_url)}",
        "reddit": f"https://www.reddit.com/submit?url={urllib.parse.quote(bill_url)}&title={urllib.parse.quote(bill_title)}",
        "email": f"mailto:?subject={urllib.parse.quote(bill_title)}&body={urllib.parse.quote(f'Check out this bill: {bill_url}')}",
        "copy": bill_url
    }

    return {
        "bill_id": bill_id,
        "links": links
    }
