"""Congress.gov API client for fetching bills."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from rich.console import Console
from fbx_core.utils.rate_limiter import RateLimiter, RateLimitConfig

from .types import BillDTO
from .settings import get_settings

logger = logging.getLogger(__name__)
console = Console()


class CongressClient:
    """Client for Congress.gov API."""
    
    BASE_URL = "https://api.congress.gov/v3"
    
    def __init__(self, api_key: str, delay_seconds: float = 0.5, rate_limit_config: Optional[RateLimitConfig] = None):
        """Initialize Congress client with enhanced rate limiting."""
        self.api_key = api_key
        self.delay_seconds = delay_seconds
        self.session: Optional[httpx.Client] = None
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            rate_limit_config or RateLimitConfig(
                requests_per_second=0.5,  # Conservative rate for Congress.gov
                burst_size=5,
                max_retries=3,
                initial_backoff=2.0,
                max_backoff=30.0,
                backoff_multiplier=2.0,
                failure_threshold=3,
                recovery_timeout=60.0,
                log_rate_limits=True,
                log_circuit_state=True
            )
        )
        
    def __enter__(self):
        """Context manager entry."""
        self.session = httpx.Client(
            base_url=self.BASE_URL,
            params={"api_key": self.api_key, "format": "json"},
            timeout=30.0,
            headers={"User-Agent": "FederalBillsExplainer/1.0"}
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            self.session.close()
            
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with enhanced rate limiting and retries."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use with context manager.")
        
        def make_request():
            response = self.session.get(endpoint, params=params)
            
            # Check for rate limit headers
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining < 10:
                    logger.warning(f"API rate limit low: {remaining} requests remaining")
            
            response.raise_for_status()
            return response.json()
        
        # Use rate limiter to execute request
        return self.rate_limiter.execute(make_request)
        
    def list_bills(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List bills with optional date filtering."""
        params = {
            "limit": limit,
            "offset": offset,
            "sort": "latestAction.actionDate+desc"
        }
        
        # Add date filters if provided
        if from_date:
            params["fromDateTime"] = f"{from_date}T00:00:00Z"
        if to_date:
            params["toDateTime"] = f"{to_date}T23:59:59Z"
            
        logger.info(f"Fetching bills with params: {params}")
        return self._make_request("/bill", params)
        
    def get_bill(self, congress: int, bill_type: str, bill_number: int) -> Dict[str, Any]:
        """Get detailed bill information."""
        endpoint = f"/bill/{congress}/{bill_type}/{bill_number}"
        logger.info(f"Fetching bill details: {endpoint}")
        return self._make_request(endpoint)
        
    def fetch_enacted_bills(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_records: Optional[int] = None
    ) -> List[BillDTO]:
        """Fetch bills that became law."""
        enacted_bills = []
        offset = 0
        limit = 50  # API max per page
        total_fetched = 0
        
        console.print("[bold blue]Fetching bills from Congress.gov API...[/bold blue]")
        
        while True:
            # Check if we've hit max records
            if max_records and total_fetched >= max_records:
                break
                
            # Fetch batch
            try:
                response = self.list_bills(from_date, to_date, limit, offset)
            except Exception as e:
                logger.error(f"Error fetching bills at offset {offset}: {e}")
                break
                
            bills = response.get("bills", [])
            if not bills:
                logger.info("No more bills to fetch")
                break
                
            # Process bills
            for bill_data in bills:
                if max_records and total_fetched >= max_records:
                    break
                    
                total_fetched += 1
                
                # Check if bill became law
                if self._is_enacted(bill_data):
                    try:
                        # Get full details if needed
                        if "summary" not in bill_data or not bill_data.get("summary"):
                            congress = bill_data.get("congress")
                            bill_type = bill_data.get("type", "").lower()
                            bill_number = bill_data.get("number")
                            
                            if congress and bill_type and bill_number:
                                try:
                                    detailed = self.get_bill(congress, bill_type, bill_number)
                                    bill_data.update(detailed.get("bill", {}))
                                    # Add small delay to be nice to API
                                    asyncio.run(asyncio.sleep(self.delay_seconds))
                                except Exception as e:
                                    logger.warning(f"Could not fetch details for {congress}-{bill_type}-{bill_number}: {e}")
                        
                        bill_dto = BillDTO.from_congress_api(bill_data)
                        enacted_bills.append(bill_dto)
                        console.print(f"  ✓ Found enacted bill: [green]{bill_dto.external_id}[/green] - {bill_dto.short_title or bill_dto.title[:60]}...")
                    except Exception as e:
                        logger.error(f"Error processing bill: {e}")
                        
            # Move to next page
            offset += limit
            
            # Add delay between pages
            if bills:
                asyncio.run(asyncio.sleep(self.delay_seconds))
                
        console.print(f"[bold green]Found {len(enacted_bills)} enacted bills out of {total_fetched} fetched[/bold green]")
        return enacted_bills
        
    def _is_enacted(self, bill_data: Dict[str, Any]) -> bool:
        """Check if a bill became law."""
        # Check latest action
        latest_action = bill_data.get("latestAction", {})
        action_text = latest_action.get("text", "").lower()
        
        if "became public law" in action_text or "signed by president" in action_text:
            return True
            
        # Check for laws array
        if bill_data.get("laws"):
            return True
            
        # Check actions list if available
        actions = bill_data.get("actions", [])
        for action in actions:
            action_text = action.get("text", "").lower()
            if "became public law" in action_text or "signed by president" in action_text:
                return True
                
        return False
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return self.rate_limiter.get_stats()
    
    def reset_rate_limit_stats(self):
        """Reset rate limiting statistics."""
        self.rate_limiter.reset_stats()
