"""
Advanced search service with filtering and ranking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SearchService:
    """Service for advanced bill search with filters."""

    def __init__(self, es_client, index_name: str = "bills"):
        """
        Initialize search service.

        Args:
            es_client: ElasticsearchClient instance
            index_name: Name of the bills index
        """
        self.es_client = es_client
        self.index_name = index_name

    async def search(
        self,
        query: Optional[str] = None,
        congress: Optional[List[int]] = None,
        bill_type: Optional[List[str]] = None,
        status: Optional[List[str]] = None,
        sponsor_party: Optional[List[str]] = None,
        sponsor_state: Optional[List[str]] = None,
        committees: Optional[List[str]] = None,
        subjects: Optional[List[str]] = None,
        policy_area: Optional[str] = None,
        has_public_law: Optional[bool] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Advanced search with multiple filters.

        Args:
            query: Search query text
            congress: Filter by congress numbers
            bill_type: Filter by bill types (hr, s, hjres, sjres, etc.)
            status: Filter by bill status
            sponsor_party: Filter by sponsor party
            sponsor_state: Filter by sponsor state
            committees: Filter by committees
            subjects: Filter by subjects
            policy_area: Filter by policy area
            has_public_law: Filter bills that became law
            date_from: Start date for date range filter
            date_to: End date for date range filter
            sort_by: Sort field (relevance, date, cosponsors, congress)
            sort_order: Sort order (asc, desc)
            page: Page number (1-indexed)
            page_size: Results per page
            **kwargs: Additional search parameters

        Returns:
            Search results with metadata
        """
        # Build Elasticsearch query
        es_query = self._build_query(
            query=query,
            congress=congress,
            bill_type=bill_type,
            status=status,
            sponsor_party=sponsor_party,
            sponsor_state=sponsor_state,
            committees=committees,
            subjects=subjects,
            policy_area=policy_area,
            has_public_law=has_public_law,
            date_from=date_from,
            date_to=date_to
        )

        # Build sort criteria
        sort_criteria = self._build_sort(sort_by, sort_order)

        # Calculate pagination
        from_offset = (page - 1) * page_size

        # Execute search
        result = await self.es_client.search(
            index_name=self.index_name,
            query=es_query,
            size=page_size,
            from_=from_offset,
            sort=sort_criteria,
            track_total_hits=True
        )

        # Format results
        hits = result.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        bills = [hit["_source"] for hit in hits.get("hits", [])]

        return {
            "bills": bills,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_more": from_offset + len(bills) < total
        }

    async def autocomplete(
        self,
        query: str,
        field: str = "title.suggest",
        size: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions.

        Args:
            query: Query text
            field: Field to get suggestions from
            size: Number of suggestions

        Returns:
            List of suggestions
        """
        suggestions = await self.es_client.suggest(
            index_name=self.index_name,
            text=query,
            field=field
        )

        # Extract suggestion texts
        results = []
        for suggestion in suggestions:
            for option in suggestion.get("options", []):
                text = option.get("text")
                if text and text not in results:
                    results.append(text)

        return results[:size]

    async def get_facets(
        self,
        query: Optional[str] = None,
        **filters
    ) -> Dict[str, Any]:
        """
        Get facet counts for filters.

        Args:
            query: Search query text
            **filters: Current filter values

        Returns:
            Facet counts for each filter dimension
        """
        # Build base query with current filters
        es_query = self._build_query(query=query, **filters)

        # Build aggregations for each facet
        aggs = {
            "congress": {
                "terms": {"field": "congress", "size": 20}
            },
            "bill_type": {
                "terms": {"field": "bill_type", "size": 10}
            },
            "status": {
                "terms": {"field": "status", "size": 20}
            },
            "sponsor_party": {
                "terms": {"field": "sponsor_party", "size": 10}
            },
            "sponsor_state": {
                "terms": {"field": "sponsor_state", "size": 60}
            },
            "policy_area": {
                "terms": {"field": "policy_area.keyword", "size": 50}
            },
            "has_public_law": {
                "terms": {"field": "has_public_law"}
            }
        }

        # Execute search with aggregations
        result = await self.es_client.search(
            index_name=self.index_name,
            query=es_query,
            size=0,
            aggs=aggs
        )

        # Format facets
        aggregations = result.get("aggregations", {})
        facets = {}

        for facet_name, agg_result in aggregations.items():
            buckets = agg_result.get("buckets", [])
            facets[facet_name] = [
                {"value": bucket["key"], "count": bucket["doc_count"]}
                for bucket in buckets
            ]

        return facets

    def _build_query(
        self,
        query: Optional[str] = None,
        congress: Optional[List[int]] = None,
        bill_type: Optional[List[str]] = None,
        status: Optional[List[str]] = None,
        sponsor_party: Optional[List[str]] = None,
        sponsor_state: Optional[List[str]] = None,
        committees: Optional[List[str]] = None,
        subjects: Optional[List[str]] = None,
        policy_area: Optional[str] = None,
        has_public_law: Optional[bool] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build Elasticsearch query DSL.

        Returns:
            Elasticsearch query object
        """
        must = []
        should = []
        filters = []

        # Full-text search
        if query:
            must.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "summary^2",
                        "sponsor^1.5",
                        "committees",
                        "subjects",
                        "full_text"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            })

            # Boost by search_boost field
            should.append({
                "function_score": {
                    "field_value_factor": {
                        "field": "search_boost",
                        "factor": 1.0,
                        "modifier": "log1p"
                    }
                }
            })

        # Congress filter
        if congress:
            filters.append({"terms": {"congress": congress}})

        # Bill type filter
        if bill_type:
            filters.append({"terms": {"bill_type": bill_type}})

        # Status filter
        if status:
            filters.append({"terms": {"status": status}})

        # Sponsor party filter
        if sponsor_party:
            filters.append({"terms": {"sponsor_party": sponsor_party}})

        # Sponsor state filter
        if sponsor_state:
            filters.append({"terms": {"sponsor_state": sponsor_state}})

        # Committees filter
        if committees:
            filters.append({"terms": {"committees.keyword": committees}})

        # Subjects filter
        if subjects:
            filters.append({"terms": {"subjects.keyword": subjects}})

        # Policy area filter
        if policy_area:
            filters.append({"term": {"policy_area.keyword": policy_area}})

        # Public law filter
        if has_public_law is not None:
            filters.append({"term": {"has_public_law": has_public_law}})

        # Date range filter
        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from
            if date_to:
                date_range["lte"] = date_to

            filters.append({
                "range": {
                    "introduced_date": date_range
                }
            })

        # Build final query
        if not must and not filters:
            # Match all if no criteria
            return {"match_all": {}}

        bool_query = {}

        if must:
            bool_query["must"] = must
        if should:
            bool_query["should"] = should
            bool_query["minimum_should_match"] = 0
        if filters:
            bool_query["filter"] = filters

        return {"bool": bool_query}

    def _build_sort(self, sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
        """
        Build sort criteria.

        Args:
            sort_by: Sort field
            sort_order: Sort order (asc, desc)

        Returns:
            Elasticsearch sort criteria
        """
        sort_mapping = {
            "relevance": "_score",
            "date": "introduced_date",
            "updated": "updated_date",
            "cosponsors": "cosponsors",
            "congress": "congress",
            "title": "title.keyword"
        }

        field = sort_mapping.get(sort_by, "_score")

        if field == "_score":
            # For relevance, always descending
            return [{"_score": {"order": "desc"}}]

        return [{field: {"order": sort_order}}]

    async def get_similar_bills(
        self,
        bill_id: str,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar bills using More Like This.

        Args:
            bill_id: Bill ID to find similar bills for
            size: Number of similar bills to return

        Returns:
            List of similar bills
        """
        query = {
            "more_like_this": {
                "fields": ["title", "summary", "subjects"],
                "like": [
                    {
                        "_index": self.index_name,
                        "_id": bill_id
                    }
                ],
                "min_term_freq": 1,
                "min_doc_freq": 1,
                "max_query_terms": 25
            }
        }

        result = await self.es_client.search(
            index_name=self.index_name,
            query=query,
            size=size
        )

        hits = result.get("hits", {}).get("hits", [])
        return [hit["_source"] for hit in hits]
