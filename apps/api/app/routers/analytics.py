"""
Analytics API endpoints for admin dashboard.

Provides analytics data for monitoring and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fbx_core.middleware.analytics import AnalyticsCollector
from fbx_core.cache import get_redis_client

router = APIRouter()


def get_analytics_collector():
    """Dependency to get analytics collector."""
    redis_client = get_redis_client()
    return AnalyticsCollector(redis_client)


@router.get("/overview")
async def get_analytics_overview(
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get analytics overview with key metrics.

    Returns:
    - Total requests
    - Average response time
    - Error rate
    - Popular endpoints
    """
    stats = await collector.get_endpoint_stats()

    if not stats:
        return {
            'total_requests': 0,
            'avg_response_time': 0,
            'error_rate': 0,
            'total_errors': 0,
            'popular_endpoints': [],
        }

    total_requests = sum(s['count'] for s in stats.values())
    total_errors = sum(s['error_count'] for s in stats.values())
    avg_response_time = sum(
        s['avg_response_time'] * s['count'] for s in stats.values()
    ) / total_requests if total_requests > 0 else 0

    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

    popular_endpoints = await collector.get_popular_endpoints(limit=10)

    return {
        'total_requests': total_requests,
        'avg_response_time': round(avg_response_time, 2),
        'error_rate': round(error_rate, 2),
        'total_errors': total_errors,
        'popular_endpoints': popular_endpoints,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/endpoints")
async def get_endpoint_analytics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get detailed analytics for all endpoints.

    Returns statistics for each endpoint including:
    - Request count
    - Error count and rate
    - Response time percentiles
    """
    stats = await collector.get_endpoint_stats(hours=hours)

    return {
        'endpoints': stats,
        'hours': hours,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/trends")
async def get_analytics_trends(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get hourly request trends.

    Returns request counts by hour for trend visualization.
    """
    trends = await collector.get_hourly_trends(hours=hours)

    # Calculate totals per hour
    hourly_totals = {}
    for hour, endpoints in trends.items():
        hourly_totals[hour] = sum(endpoints.values())

    return {
        'hourly_totals': hourly_totals,
        'detailed_trends': trends,
        'hours': hours,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/errors")
async def get_error_analytics(
    limit: int = Query(default=20, ge=1, le=100, description="Number of recent errors"),
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get recent errors and error statistics.
    """
    recent_errors = await collector.get_recent_errors(limit=limit)

    # Calculate error statistics
    error_by_endpoint = {}
    error_by_status = {}

    for error in recent_errors:
        endpoint = error.get('endpoint', 'unknown')
        status_code = error.get('status_code', 500)

        error_by_endpoint[endpoint] = error_by_endpoint.get(endpoint, 0) + 1
        error_by_status[status_code] = error_by_status.get(status_code, 0) + 1

    return {
        'recent_errors': recent_errors,
        'error_by_endpoint': error_by_endpoint,
        'error_by_status': error_by_status,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/user-agents")
async def get_user_agent_analytics(
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get user agent statistics.

    Shows distribution of browsers, mobile vs desktop, etc.
    """
    user_agents = await collector.get_user_agent_stats()

    # Categorize user agents
    categories = {
        'mobile': 0,
        'desktop': 0,
        'bot': 0,
        'unknown': 0,
    }

    browsers = {}

    for ua, count in user_agents.items():
        ua_lower = ua.lower()

        # Categorize by device type
        if any(mobile in ua_lower for mobile in ['mobile', 'android', 'iphone', 'ipad']):
            categories['mobile'] += count
        elif any(bot in ua_lower for bot in ['bot', 'crawler', 'spider']):
            categories['bot'] += count
        elif ua_lower != 'unknown':
            categories['desktop'] += count
        else:
            categories['unknown'] += count

        # Detect browser
        if 'chrome' in ua_lower:
            browsers['Chrome'] = browsers.get('Chrome', 0) + count
        elif 'firefox' in ua_lower:
            browsers['Firefox'] = browsers.get('Firefox', 0) + count
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            browsers['Safari'] = browsers.get('Safari', 0) + count
        elif 'edge' in ua_lower:
            browsers['Edge'] = browsers.get('Edge', 0) + count
        else:
            browsers['Other'] = browsers.get('Other', 0) + count

    return {
        'categories': categories,
        'browsers': browsers,
        'raw_user_agents': user_agents,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/performance")
async def get_performance_analytics(
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get performance metrics including response time percentiles.
    """
    stats = await collector.get_endpoint_stats()

    # Find slowest endpoints
    slowest_endpoints = sorted(
        [
            {
                'endpoint': endpoint,
                'avg_response_time': data['avg_response_time'],
                'p95_response_time': data['p95_response_time'],
                'p99_response_time': data['p99_response_time'],
                'count': data['count'],
            }
            for endpoint, data in stats.items()
        ],
        key=lambda x: x['p95_response_time'],
        reverse=True
    )[:10]

    # Calculate overall percentiles
    all_times = []
    for data in stats.values():
        all_times.extend([data['avg_response_time']] * data['count'])

    if all_times:
        all_times.sort()
        p50 = all_times[len(all_times) // 2]
        p95 = all_times[int(len(all_times) * 0.95)]
        p99 = all_times[int(len(all_times) * 0.99)]
    else:
        p50 = p95 = p99 = 0

    return {
        'overall_percentiles': {
            'p50': round(p50, 2),
            'p95': round(p95, 2),
            'p99': round(p99, 2),
        },
        'slowest_endpoints': slowest_endpoints,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/search-terms")
async def get_search_analytics(
    limit: int = Query(default=20, ge=1, le=100),
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get popular search terms.

    NOTE: This endpoint currently returns empty data as search term tracking
    requires analytics aggregation pipeline. Future implementation will aggregate
    search queries from Redis analytics data to identify trending topics.

    Future enhancement: Implement Redis sorted sets to track search term frequency
    and return top N most popular search terms over various time windows.
    """
    return {
        'popular_searches': [],
        'message': 'Search term analytics aggregation in development',
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/bills/popular")
async def get_popular_bills(
    limit: int = Query(default=10, ge=1, le=50),
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get most viewed bills.

    Analyzes bill detail endpoint requests to find popular bills.
    """
    stats = await collector.get_endpoint_stats()

    # Find bill detail requests
    bill_views = {}

    for endpoint, data in stats.items():
        # Match pattern: GET:/bills/{congress}/{type}/{number}
        if 'GET:/bills/' in endpoint:
            parts = endpoint.split('/')
            if len(parts) >= 5:
                try:
                    congress = parts[2]
                    bill_type = parts[3]
                    number = parts[4]

                    bill_id = f"{congress}/{bill_type}/{number}"
                    bill_views[bill_id] = data['count']
                except (IndexError, ValueError):
                    continue

    # Sort by view count
    popular_bills = sorted(
        [
            {'bill_id': bill_id, 'views': count}
            for bill_id, count in bill_views.items()
        ],
        key=lambda x: x['views'],
        reverse=True
    )[:limit]

    return {
        'popular_bills': popular_bills,
        'total_tracked': len(bill_views),
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.get("/export-usage")
async def get_export_usage(
    collector: AnalyticsCollector = Depends(get_analytics_collector)
):
    """
    Get data export usage statistics.
    """
    stats = await collector.get_endpoint_stats()

    # Find export requests
    csv_exports = 0
    json_exports = 0

    for endpoint, data in stats.items():
        if '/export/csv' in endpoint:
            csv_exports += data['count']
        elif '/export/json' in endpoint:
            json_exports += data['count']

    total_exports = csv_exports + json_exports

    return {
        'total_exports': total_exports,
        'csv_exports': csv_exports,
        'json_exports': json_exports,
        'export_breakdown': {
            'CSV': csv_exports,
            'JSON': json_exports,
        },
        'timestamp': datetime.utcnow().isoformat(),
    }
