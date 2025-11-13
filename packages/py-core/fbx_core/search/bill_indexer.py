"""
Bill indexing service for Elasticsearch.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BillIndexer:
    """Service for indexing bills into Elasticsearch."""

    INDEX_NAME = "bills"

    # Elasticsearch mappings for bills index
    MAPPINGS = {
        "properties": {
            "bill_id": {"type": "keyword"},
            "congress": {"type": "integer"},
            "bill_type": {"type": "keyword"},
            "bill_number": {"type": "integer"},
            "title": {
                "type": "text",
                "analyzer": "english",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"}
                }
            },
            "summary": {
                "type": "text",
                "analyzer": "english"
            },
            "full_text": {
                "type": "text",
                "analyzer": "english"
            },
            "sponsor": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "sponsor_party": {"type": "keyword"},
            "sponsor_state": {"type": "keyword"},
            "cosponsors": {"type": "integer"},
            "committees": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "subjects": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "status": {"type": "keyword"},
            "latest_action": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "latest_action_date": {"type": "date"},
            "introduced_date": {"type": "date"},
            "updated_date": {"type": "date"},
            "public_law_number": {"type": "keyword"},
            "has_public_law": {"type": "boolean"},
            "policy_area": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "legislative_subjects": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "search_boost": {"type": "float"}
        }
    }

    # Index settings
    SETTINGS = {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "english": {
                    "type": "standard",
                    "stopwords": "_english_"
                }
            }
        }
    }

    def __init__(self, es_client):
        """
        Initialize bill indexer.

        Args:
            es_client: ElasticsearchClient instance
        """
        self.es_client = es_client

    async def create_index(self):
        """Create the bills index with mappings and settings."""
        await self.es_client.create_index(
            self.INDEX_NAME,
            self.MAPPINGS,
            self.SETTINGS
        )

    async def delete_index(self):
        """Delete the bills index."""
        await self.es_client.delete_index(self.INDEX_NAME)

    async def index_bill(self, bill_data: Dict[str, Any]):
        """
        Index a single bill.

        Args:
            bill_data: Bill data dictionary
        """
        # Transform bill data for indexing
        doc = self._transform_bill(bill_data)

        # Index the document
        bill_id = doc["bill_id"]
        await self.es_client.index_document(self.INDEX_NAME, bill_id, doc)

        logger.info(f"Indexed bill: {bill_id}")

    async def bulk_index_bills(self, bills: List[Dict[str, Any]]):
        """
        Bulk index multiple bills.

        Args:
            bills: List of bill data dictionaries
        """
        # Transform bills for indexing
        documents = [self._transform_bill(bill) for bill in bills]

        # Bulk index
        success, failed = await self.es_client.bulk_index(
            self.INDEX_NAME,
            documents,
            id_field="bill_id"
        )

        logger.info(f"Bulk indexed {success} bills, {len(failed)} failed")

        return success, failed

    async def update_bill(self, bill_id: str, partial_data: Dict[str, Any]):
        """
        Update a bill partially.

        Args:
            bill_id: Bill ID
            partial_data: Partial bill data to update
        """
        await self.es_client.update_document(self.INDEX_NAME, bill_id, partial_data)
        logger.info(f"Updated bill: {bill_id}")

    async def delete_bill(self, bill_id: str):
        """
        Delete a bill from the index.

        Args:
            bill_id: Bill ID
        """
        await self.es_client.delete_document(self.INDEX_NAME, bill_id)
        logger.info(f"Deleted bill: {bill_id}")

    def _transform_bill(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform bill data for Elasticsearch indexing.

        Args:
            bill_data: Raw bill data

        Returns:
            Transformed document
        """
        # Create bill ID
        bill_id = f"{bill_data.get('congress')}/{bill_data.get('type')}/{bill_data.get('number')}"

        # Extract sponsor info
        sponsor_info = bill_data.get("sponsor", {})
        sponsor_name = None
        sponsor_party = None
        sponsor_state = None

        if isinstance(sponsor_info, dict):
            sponsor_name = sponsor_info.get("name")
            sponsor_party = sponsor_info.get("party")
            sponsor_state = sponsor_info.get("state")
        elif isinstance(sponsor_info, str):
            sponsor_name = sponsor_info

        # Extract committees
        committees = []
        committee_data = bill_data.get("committees", [])
        if isinstance(committee_data, list):
            committees = [c.get("name") if isinstance(c, dict) else c for c in committee_data]

        # Extract subjects
        subjects = bill_data.get("subjects", [])
        legislative_subjects = bill_data.get("legislative_subjects", [])

        # Policy area
        policy_area = bill_data.get("policy_area")

        # Calculate search boost based on activity
        cosponsors_count = len(bill_data.get("cosponsors", []))
        has_public_law = bool(bill_data.get("public_law_number"))

        search_boost = 1.0
        if has_public_law:
            search_boost += 2.0
        if cosponsors_count > 50:
            search_boost += 1.0
        elif cosponsors_count > 20:
            search_boost += 0.5

        # Build document
        doc = {
            "bill_id": bill_id,
            "congress": bill_data.get("congress"),
            "bill_type": bill_data.get("type"),
            "bill_number": bill_data.get("number"),
            "title": bill_data.get("title", ""),
            "summary": bill_data.get("summary", ""),
            "full_text": bill_data.get("text", ""),
            "sponsor": sponsor_name,
            "sponsor_party": sponsor_party,
            "sponsor_state": sponsor_state,
            "cosponsors": cosponsors_count,
            "committees": committees,
            "subjects": subjects,
            "legislative_subjects": legislative_subjects,
            "policy_area": policy_area,
            "status": bill_data.get("status"),
            "latest_action": bill_data.get("latest_action", {}).get("text") if isinstance(bill_data.get("latest_action"), dict) else bill_data.get("latest_action"),
            "latest_action_date": self._parse_date(bill_data.get("latest_action", {}).get("date") if isinstance(bill_data.get("latest_action"), dict) else None),
            "introduced_date": self._parse_date(bill_data.get("introduced_date")),
            "updated_date": self._parse_date(bill_data.get("updated_date")),
            "public_law_number": bill_data.get("public_law_number"),
            "has_public_law": has_public_law,
            "search_boost": search_boost
        }

        return doc

    def _parse_date(self, date_value: Any) -> Optional[str]:
        """
        Parse date value to ISO format.

        Args:
            date_value: Date value (string or datetime)

        Returns:
            ISO formatted date string or None
        """
        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value.isoformat()

        if isinstance(date_value, str):
            # Try to parse common date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue

        return None
