from typing import Iterable, Optional, Dict, Any, List
from datetime import datetime, timezone
import json, os
import logging

import httpx
from dateutil import parser as dateparser
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import AbstractProvider, BillRecord
from fbx_core.utils.settings import Settings
from fbx_core.utils.rate_limiter import RateLimiter, RateLimitConfig

API_BASE = "https://api.congress.gov/v3"


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _get(d: Dict[str, Any], *path, default=None):
    cur: Any = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def _as_list(v) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


class CongressGovProvider(AbstractProvider):
    name = "congress_gov"

    def __init__(self, fixtures_dir: str = "fixtures", rate_limit_config: Optional[RateLimitConfig] = None):
        self.settings = Settings()
        self.fixtures_dir = fixtures_dir
        self.api_key = self.settings.congress_api_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize rate limiter with Congress.gov API limits
        self.rate_limiter = RateLimiter(
            rate_limit_config or RateLimitConfig(
                requests_per_second=1.0,  # Congress.gov recommends max 1000 requests per hour (~0.28/sec)
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

    def fetch_bills_updated_since(
        self, since: Optional[datetime], page: int = 1, page_size: int = 100
    ) -> Iterable[BillRecord]:
        # Dry-run or missing API key uses fixture
        if self.settings.dry_run or not self.api_key:
            path = os.path.join(self.fixtures_dir, "congress_gov_became_law_sample.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for rec in data.get("results", []):
                    yield BillRecord(rec)
            return

        params = {
            "api_key": self.api_key,
            "format": "json",
        }
        if since:
            params["fromDateTime"] = _iso(since)

        limit = min(max(page_size, 1), 250)
        offset = (max(page, 1) - 1) * limit

        with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
            next_url = "/bill"
            next_params = dict(params)
            next_params.update({"limit": limit, "offset": offset})
            while next_url:
                data = self._get_json(client, next_url, next_params)
                bills = data.get("bills") or data.get("results") or []
                for b in bills:
                    ident = self._extract_identity(b)
                    if not ident:
                        continue
                    detail = self._get_json(client, f"/bill/{ident['congress']}/{ident['bill_type']}/{ident['number']}", params)
                    bill_detail = detail.get("bill") or detail
                    rec = self._normalize_bill(bill_detail)
                    if rec.get("public_law_number"):
                        yield BillRecord(rec)

                pagination = data.get("pagination") or {}
                next_link = pagination.get("next")
                if next_link:
                    next_url = next_link.replace(API_BASE, "") if next_link.startswith(API_BASE) else next_link
                    next_params = {"api_key": self.api_key, "format": "json"}
                else:
                    break

    def _get_json(self, client: httpx.Client, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retry logic."""
        def make_request():
            r = client.get(url, params=params)
            
            # Check for rate limit headers
            if 'X-RateLimit-Remaining' in r.headers:
                remaining = int(r.headers['X-RateLimit-Remaining'])
                if remaining < 10:
                    self.logger.warning(f"API rate limit low: {remaining} requests remaining")
            
            r.raise_for_status()
            return r.json()
        
        # Use rate limiter to execute the request
        return self.rate_limiter.execute(make_request)

    def _extract_identity(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            congress = int(item.get("congress") or _get(item, "bill", "congress"))
            bill_type = (item.get("billType") or _get(item, "bill", "billType") or "").lower()
            number = int(item.get("billNumber") or _get(item, "bill", "billNumber"))
            return {"congress": congress, "bill_type": bill_type, "number": number}
        except Exception:
            return None

    def _normalize_bill(self, bill: Dict[str, Any]) -> Dict[str, Any]:
        title = bill.get("title")
        if not isinstance(title, str):
            titles = bill.get("titles") or bill.get("title") or []
            if isinstance(titles, list) and titles:
                enacted = next((t for t in titles if isinstance(t, dict) and "enacted" in (t.get("type") or "").lower()), None)
                if enacted and isinstance(enacted.get("title"), str):
                    title = enacted.get("title")
                else:
                    cand = titles[0]
                    if isinstance(cand, dict) and isinstance(cand.get("title"), str):
                        title = cand.get("title")
        if not isinstance(title, str):
            title = bill.get("titleLatest") or bill.get("shortTitle") or ""

        summary = ""
        summ = bill.get("summary")
        if isinstance(summ, dict):
            summary = summ.get("text") or summ.get("summary") or ""
        elif isinstance(summ, str):
            summary = summ
        if not summary:
            summaries = bill.get("summaries")
            if isinstance(summaries, list) and summaries:
                s0 = summaries[0]
                if isinstance(s0, dict):
                    summary = s0.get("text") or s0.get("summary") or ""

        introduced_date = bill.get("introducedDate") or bill.get("introducedOn")
        latest_action = bill.get("latestAction") or {}
        latest_action_date = latest_action.get("actionDate") or latest_action.get("date")

        def parse_date(val):
            try:
                if val:
                    return dateparser.isoparse(val).date()
            except Exception:
                return None
            return None

        def parse_dt(val):
            try:
                if val:
                    dt = dateparser.isoparse(val)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
            except Exception:
                return None
            return None

        pl_number = None
        laws = bill.get("laws") or bill.get("enactedAs") or []
        for law in _as_list(laws):
            if isinstance(law, dict):
                n = law.get("number") or law.get("lawNumber") or law.get("publicLawNumber")
                if n:
                    pl_number = n
                    break
            elif isinstance(law, str):
                pl_number = law
                break

        sponsor_obj = None
        sponsors = bill.get("sponsors") or bill.get("sponsor") or []
        if isinstance(sponsors, dict):
            sponsor_obj = sponsors
        elif isinstance(sponsors, list) and sponsors:
            sponsor_obj = sponsors[0]

        committees = []
        for c in _as_list(bill.get("committees")):
            if isinstance(c, dict):
                name = c.get("name") or c.get("committeeName")
                if name:
                    committees.append(name)

        subjects: List[str] = []
        policy_area = _get(bill, "subjects", "policyArea", "name")
        if isinstance(policy_area, str):
            subjects.append(policy_area)
        leg_subj = _get(bill, "subjects", "legislativeSubjects")
        if isinstance(leg_subj, list):
            for s in leg_subj:
                n = s.get("name") if isinstance(s, dict) else None
                if n:
                    subjects.append(n)

        url = bill.get("congressdotgov_url") or bill.get("url") or _get(bill, "urls", "congress") or ""

        cosponsors_count = 0
        cosponsors = bill.get("cosponsors")
        if isinstance(cosponsors, list):
            cosponsors_count = len(cosponsors)
        elif isinstance(cosponsors, dict) and isinstance(cosponsors.get("items"), list):
            cosponsors_count = len(cosponsors.get("items"))

        status = "became-law" if pl_number else (latest_action.get("text") or latest_action.get("actionDescription") or "")

        return {
            "congress": int(bill.get("congress") or 0),
            "bill_type": str((bill.get("billType") or "")).lower(),
            "number": int(bill.get("billNumber") or 0),
            "title": title,
            "summary": summary,
            "status": status,
            "introduced_date": parse_date(introduced_date),
            "latest_action_date": parse_dt(latest_action_date),
            "congress_url": url,
            "public_law_number": pl_number,
            "sponsor": sponsor_obj,
            "committees": committees or None,
            "subjects": subjects or None,
            "cosponsors_count": cosponsors_count,
        }
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return self.rate_limiter.get_stats()
    
    def reset_rate_limit_stats(self):
        """Reset rate limiting statistics."""
        self.rate_limiter.reset_stats()

