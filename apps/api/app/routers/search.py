"""
Advanced search API endpoints with Elasticsearch.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel
from fbx_core.search import get_elasticsearch_client, SearchService, SearchHistory
from fbx_core.cache import cached, get_redis_client

router = APIRouter()


class SearchRequest(BaseModel):
    """Search request model."""
    query: Optional[str] = None
    congress: Optional[List[int]] = None
    bill_type: Optional[List[str]] = None
    status: Optional[List[str]] = None
    sponsor_party: Optional[List[str]] = None
    sponsor_state: Optional[List[str]] = None
    committees: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    policy_area: Optional[str] = None
    has_public_law: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20


def get_search_service() -> SearchService:
    """Get search service instance."""
    es_client = get_elasticsearch_client()
    return SearchService(es_client)


@router.post("/search")
@router.get("/search")
async def search_bills(
    request: Request,
    query: Optional[str] = Query(None, description="Search query text"),
    congress: Optional[str] = Query(None, description="Comma-separated congress numbers"),
    bill_type: Optional[str] = Query(None, description="Comma-separated bill types"),
    status: Optional[str] = Query(None, description="Comma-separated status values"),
    sponsor_party: Optional[str] = Query(None, description="Comma-separated parties"),
    sponsor_state: Optional[str] = Query(None, description="Comma-separated states"),
    committees: Optional[str] = Query(None, description="Comma-separated committee names"),
    subjects: Optional[str] = Query(None, description="Comma-separated subjects"),
    policy_area: Optional[str] = Query(None, description="Policy area"),
    has_public_law: Optional[bool] = Query(None, description="Filter bills that became law"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sort_by: str = Query("relevance", description="Sort field (relevance, date, cosponsors, congress)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page")
):
    """
    Advanced search for bills with multiple filters.

    Supports:
    - Full-text search across title, summary, and content
    - Fuzzy matching for typos
    - Multiple filter dimensions
    - Relevance ranking
    - Pagination
    """
    try:
        service = get_search_service()

        # Parse comma-separated values
        congress_list = [int(c.strip()) for c in congress.split(",")] if congress else None
        bill_type_list = [t.strip() for t in bill_type.split(",")] if bill_type else None
        status_list = [s.strip() for s in status.split(",")] if status else None
        party_list = [p.strip() for p in sponsor_party.split(",")] if sponsor_party else None
        state_list = [s.strip() for s in sponsor_state.split(",")] if sponsor_state else None
        committee_list = [c.strip() for c in committees.split(",")] if committees else None
        subject_list = [s.strip() for s in subjects.split(",")] if subjects else None

        # Execute search
        results = await service.search(
            query=query,
            congress=congress_list,
            bill_type=bill_type_list,
            status=status_list,
            sponsor_party=party_list,
            sponsor_state=state_list,
            committees=committee_list,
            subjects=subject_list,
            policy_area=policy_area,
            has_public_law=has_public_law,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )

        # Track search in history (if query provided)
        if query:
            redis_client = get_redis_client()
            if redis_client:
                history = SearchHistory(redis_client)
                filters_dict = {
                    "congress": congress_list,
                    "bill_type": bill_type_list,
                    "status": status_list,
                    "sponsor_party": party_list,
                    "sponsor_state": state_list
                }
                # Filter out None values
                filters_dict = {k: v for k, v in filters_dict.items() if v}

                ip_address = request.client.host if request.client else None
                await history.track_search(
                    query=query,
                    ip_address=ip_address,
                    results_count=results.get("total", 0),
                    filters=filters_dict if filters_dict else None
                )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/autocomplete")
@cached(ttl=300)
async def autocomplete(
    query: str = Query(..., min_length=2, description="Query text for autocomplete"),
    field: str = Query("title.suggest", description="Field to get suggestions from"),
    size: int = Query(10, ge=1, le=20, description="Number of suggestions")
):
    """
    Get autocomplete suggestions for search queries.

    Returns:
        List of suggested completions
    """
    try:
        service = get_search_service()
        suggestions = await service.autocomplete(query, field, size)

        return {
            "query": query,
            "suggestions": suggestions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")


@router.get("/facets")
@cached(ttl=60)
async def get_facets(
    query: Optional[str] = Query(None, description="Search query to scope facets"),
    congress: Optional[str] = Query(None, description="Current congress filter"),
    bill_type: Optional[str] = Query(None, description="Current bill type filter"),
    status: Optional[str] = Query(None, description="Current status filter")
):
    """
    Get facet counts for filter options.

    Returns counts for each filter dimension based on current search/filters.
    Useful for showing result counts next to filter options.
    """
    try:
        service = get_search_service()

        # Parse filters
        filters = {}
        if congress:
            filters["congress"] = [int(c.strip()) for c in congress.split(",")]
        if bill_type:
            filters["bill_type"] = [t.strip() for t in bill_type.split(",")]
        if status:
            filters["status"] = [s.strip() for s in status.split(",")]

        facets = await service.get_facets(query=query, **filters)

        return facets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Facets failed: {str(e)}")


@router.get("/similar/{bill_id}")
@cached(ttl=3600)
async def get_similar_bills(
    bill_id: str,
    size: int = Query(10, ge=1, le=20, description="Number of similar bills")
):
    """
    Find similar bills using machine learning.

    Uses Elasticsearch's More Like This query to find bills with similar
    content based on title, summary, and subjects.
    """
    try:
        service = get_search_service()
        similar_bills = await service.get_similar_bills(bill_id, size)

        return {
            "bill_id": bill_id,
            "similar_bills": similar_bills,
            "count": len(similar_bills)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar bills search failed: {str(e)}")


@router.get("/suggestions")
@cached(ttl=3600)
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions")
):
    """
    Get popular/trending search queries.

    This could be enhanced with analytics integration to show actual popular searches.
    For now, returns suggested topics.
    """
    # TODO: Integrate with analytics to get real popular searches
    suggestions = [
        "climate change",
        "healthcare",
        "education funding",
        "tax reform",
        "infrastructure",
        "immigration",
        "defense spending",
        "social security",
        "renewable energy",
        "national security"
    ]

    return {
        "suggestions": suggestions[:limit],
        "message": "Popular search topics - could be enhanced with real analytics"
    }


@router.post("/index/create")
async def create_search_index():
    """
    Create the Elasticsearch index for bills.

    This endpoint should be protected and only accessible to admins.
    """
    try:
        from fbx_core.search import BillIndexer

        es_client = get_elasticsearch_client()
        indexer = BillIndexer(es_client)

        await indexer.create_index()

        return {
            "message": "Search index created successfully",
            "index": "bills"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index creation failed: {str(e)}")


@router.delete("/index/delete")
async def delete_search_index():
    """
    Delete the Elasticsearch index for bills.

    WARNING: This will delete all indexed data!
    This endpoint should be protected and only accessible to admins.
    """
    try:
        from fbx_core.search import BillIndexer

        es_client = get_elasticsearch_client()
        indexer = BillIndexer(es_client)

        await indexer.delete_index()

        return {
            "message": "Search index deleted successfully",
            "index": "bills"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index deletion failed: {str(e)}")


@router.post("/index/bill")
async def index_bill(bill_data: dict):
    """
    Index a single bill into Elasticsearch.

    This endpoint should be protected and only accessible to admins.
    """
    try:
        from fbx_core.search import BillIndexer

        es_client = get_elasticsearch_client()
        indexer = BillIndexer(es_client)

        await indexer.index_bill(bill_data)

        bill_id = f"{bill_data.get('congress')}/{bill_data.get('type')}/{bill_data.get('number')}"

        return {
            "message": "Bill indexed successfully",
            "bill_id": bill_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bill indexing failed: {str(e)}")


@router.get("/history/popular")
@cached(ttl=300)
async def get_popular_searches_history(
    limit: int = Query(10, ge=1, le=50, description="Number of popular searches")
):
    """
    Get most popular search queries from history.

    Returns searches ranked by frequency of use.
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {"popular_searches": [], "message": "Search history not available (Redis not configured)"}

        history = SearchHistory(redis_client)
        popular = await history.get_popular_searches(limit)

        return {
            "popular_searches": popular,
            "count": len(popular)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get popular searches: {str(e)}")


@router.get("/history/trending")
@cached(ttl=60)
async def get_trending_searches(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of trending searches")
):
    """
    Get trending searches in the last N hours.

    Returns recent popular searches, useful for showing what's currently trending.
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {"trending_searches": [], "message": "Search history not available (Redis not configured)"}

        history = SearchHistory(redis_client)
        trending = await history.get_trending_searches(hours, limit)

        return {
            "trending_searches": trending,
            "count": len(trending),
            "hours": hours
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending searches: {str(e)}")


@router.get("/history/my")
async def get_my_search_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Number of recent searches")
):
    """
    Get search history for the current user/session.

    Returns recent searches based on IP address for anonymous users.
    For authenticated users, would use user ID.
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {"history": [], "message": "Search history not available (Redis not configured)"}

        history = SearchHistory(redis_client)

        # For now, use IP-based history
        # TODO: Add user authentication and use user_id
        ip_address = request.client.host if request.client else None
        if not ip_address:
            return {"history": [], "message": "Unable to identify session"}

        searches = await history.get_ip_history(ip_address, limit)

        return {
            "history": searches,
            "count": len(searches)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")


@router.delete("/history/my")
async def clear_my_search_history(request: Request):
    """
    Clear search history for the current user/session.
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {"message": "Search history not available (Redis not configured)"}

        history = SearchHistory(redis_client)

        # For now, use IP-based history
        # TODO: Add user authentication and use user_id
        ip_address = request.client.host if request.client else None
        if not ip_address:
            return {"message": "Unable to identify session"}

        # Clear IP-based history
        key = f"search:ip:{ip_address}"
        await redis_client.delete(key)

        return {"message": "Search history cleared successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear search history: {str(e)}")
