# Analytics System Documentation

## Overview

The Federal Bills Explainer includes a comprehensive analytics system for monitoring API usage, performance, errors, and user behavior. The system consists of backend tracking middleware, aggregation services, API endpoints, and frontend visualization components.

## Architecture

### Backend Components

#### 1. Analytics Middleware (`fbx_core.middleware.analytics.AnalyticsMiddleware`)

Tracks all API requests automatically:
- Request counts by endpoint
- Response times (avg, P95, P99)
- Status codes and error rates
- User agent information
- IP addresses
- Request timestamps

**How it works:**
- Intercepts every HTTP request
- Measures request duration
- Stores metrics in Redis
- Falls back to in-memory storage if Redis unavailable

**Configuration:**
```python
# In main.py
app.add_middleware(AnalyticsMiddleware, redis_url=redis_url)
```

#### 2. Analytics Collector (`fbx_core.middleware.analytics.AnalyticsCollector`)

Aggregates and retrieves analytics data:
- Endpoint statistics
- Hourly trends
- Error tracking
- User agent analysis
- Popular endpoints

**Data Storage:**
- **Redis Keys:**
  - `analytics:requests:count` - Request counters by endpoint
  - `analytics:requests:times:{endpoint}` - Response times (sorted set)
  - `analytics:status:{endpoint}` - Status code counts
  - `analytics:errors:count` - Error counters
  - `analytics:errors:recent` - Recent error list (last 100)
  - `analytics:user_agents` - User agent distribution
  - `analytics:hourly:{hour}` - Hourly aggregated data (7-day TTL)
  - `analytics:daily:{day}` - Daily aggregated data (30-day TTL)

**TTL (Time To Live):**
- Hourly data: 7 days
- Daily data: 30 days
- Recent errors: 100 items (FIFO)

### API Endpoints

All analytics endpoints are under `/analytics`:

#### `GET /analytics/overview`
Returns key metrics summary:
```json
{
  "total_requests": 12543,
  "avg_response_time": 145.23,
  "error_rate": 2.5,
  "total_errors": 314,
  "popular_endpoints": [
    {"endpoint": "GET:/bills", "count": 5432}
  ],
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/endpoints?hours=24`
Detailed statistics for all endpoints:
```json
{
  "endpoints": {
    "GET:/bills": {
      "count": 5432,
      "error_count": 12,
      "avg_response_time": 123.45,
      "p95_response_time": 234.56,
      "p99_response_time": 345.67
    }
  },
  "hours": 24,
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/trends?hours=24`
Hourly request trends:
```json
{
  "hourly_totals": {
    "2025-11-13T09:00:00Z": 523,
    "2025-11-13T10:00:00Z": 612
  },
  "detailed_trends": {
    "2025-11-13T09:00:00Z": {
      "GET:/bills": 423,
      "GET:/bills/{id}": 100
    }
  },
  "hours": 24,
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/errors?limit=20`
Recent errors and statistics:
```json
{
  "recent_errors": [
    {
      "endpoint": "GET:/bills/123",
      "status_code": 404,
      "timestamp": "2025-11-13T10:25:00Z",
      "error_message": "Bill not found",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "error_by_endpoint": {
    "GET:/bills/{id}": 5
  },
  "error_by_status": {
    "404": 3,
    "500": 2
  },
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/user-agents`
Browser and device statistics:
```json
{
  "categories": {
    "mobile": 3245,
    "desktop": 8234,
    "bot": 1064,
    "unknown": 0
  },
  "browsers": {
    "Chrome": 7234,
    "Firefox": 2345,
    "Safari": 1900,
    "Edge": 800
  },
  "raw_user_agents": {
    "Mozilla/5.0...": 523
  },
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/performance`
Response time percentiles:
```json
{
  "overall_percentiles": {
    "p50": 123.45,
    "p95": 234.56,
    "p99": 345.67
  },
  "slowest_endpoints": [
    {
      "endpoint": "GET:/bills/search",
      "avg_response_time": 456.78,
      "p95_response_time": 789.01,
      "p99_response_time": 1234.56,
      "count": 1234
    }
  ],
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/bills/popular?limit=10`
Most viewed bills:
```json
{
  "popular_bills": [
    {
      "bill_id": "118/hr/1234",
      "views": 523
    }
  ],
  "total_tracked": 145,
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### `GET /analytics/export-usage`
Export feature usage:
```json
{
  "total_exports": 234,
  "csv_exports": 145,
  "json_exports": 89,
  "export_breakdown": {
    "CSV": 145,
    "JSON": 89
  },
  "timestamp": "2025-11-13T10:30:00Z"
}
```

### Frontend Components

#### 1. Admin Dashboard (`/admin`)
Main analytics dashboard with overview cards:
- Total requests
- Average response time
- Error rate
- Total errors
- Performance percentiles (P50, P95, P99)
- Slowest endpoints table
- Popular endpoints bar chart
- Most viewed bills

**Features:**
- Auto-refresh every 30 seconds
- Manual refresh button
- Real-time metric updates
- Mobile-responsive layout

#### 2. Advanced Analytics Page (`/admin/analytics`)
Detailed analytics visualizations:
- Request trends chart (24-hour bars)
- User agent analytics (device types, browsers)
- Error analytics (recent errors, by endpoint, by status)

**Features:**
- Interactive charts
- Tabbed interface for error views
- Hourly trend visualization
- Device and browser breakdowns

#### 3. Analytics Components

**AnalyticsTrendsChart**
- Displays hourly request trends as bar chart
- Configurable time range (default: 24 hours)
- Hover tooltips with exact counts
- Summary statistics (total, average, peak)
- Auto-refresh every minute

**ErrorAnalytics**
- Three views: Recent errors, By endpoint, By status
- Color-coded status codes (4xx orange, 5xx red)
- Error message display
- User agent tracking
- Configurable limit (default: 20)
- Auto-refresh every 30 seconds

**UserAgentAnalytics**
- Device type breakdown (mobile, desktop, bot, unknown)
- Browser distribution with visual bars
- Percentage calculations
- Color-coded categories
- Interactive hover states
- Auto-refresh every minute

### Frontend Event Tracking

Client-side analytics tracking for user interactions:

```typescript
import { trackEvent, trackPageView, trackSearch, trackBillView } from '@/lib/analytics';

// Track custom events
trackEvent('button_click', {
  event_category: 'interaction',
  event_label: 'export_csv',
  event_value: 10
});

// Track page views
trackPageView('/bills');

// Track searches
trackSearch('climate change', 15);

// Track bill views
trackBillView('118/hr/1234', 'Climate Action Bill');

// Track exports
trackExport('csv', 50);

// Track filters
trackFilter('status', 'enacted');

// Track errors
trackError('Failed to load bill', stackTrace, context);

// Track performance
trackPerformance('page_load', 1234, 'ms');

// Track engagement
trackEngagement('scroll', 'bill_list', 75);
```

**React Hooks:**
```typescript
import { useAnalytics, usePageTracking } from '@/lib/analytics';

function MyComponent() {
  const analytics = useAnalytics();
  usePageTracking(); // Automatic page view tracking

  const handleClick = () => {
    analytics.track('button_click', { ... });
  };

  return <button onClick={handleClick}>Click me</button>;
}
```

**Features:**
- Automatic batching (flushes every 10 seconds or 10 events)
- Queuing with retry on failure
- Debug mode for development
- Singleton pattern for consistency
- Cleanup on unmount

## Usage Guide

### Viewing Analytics

1. **Admin Dashboard**: Navigate to `/admin`
   - View high-level metrics
   - Monitor performance percentiles
   - See popular endpoints and bills

2. **Advanced Analytics**: Navigate to `/admin/analytics`
   - View detailed trends
   - Analyze user agents
   - Investigate errors

### Monitoring Performance

1. Check response time percentiles:
   - P50 (median) - typical performance
   - P95 - 95% of requests faster than this
   - P99 - 99% of requests faster than this

2. Review slowest endpoints:
   - Identify bottlenecks
   - Prioritize optimization efforts

3. Monitor error rates:
   - Overall error percentage
   - Errors by endpoint
   - Errors by status code

### Troubleshooting

#### High Error Rate
1. Check `/admin/analytics` error tab
2. Identify problematic endpoints
3. Review recent errors for patterns
4. Check status code distribution

#### Slow Performance
1. Review performance percentiles
2. Check slowest endpoints table
3. Look for P95/P99 outliers
4. Monitor trends over time

#### No Data Showing
1. Verify Redis is running: `redis-cli ping`
2. Check environment variables: `REDIS_URL`
3. Check middleware is enabled in `main.py`
4. Review logs for errors

## Configuration

### Environment Variables

```bash
# Redis connection for analytics storage
REDIS_URL=redis://localhost:6379/0

# Enable/disable analytics (default: true)
ENABLE_ANALYTICS=true

# Analytics retention (days)
ANALYTICS_HOURLY_TTL=7
ANALYTICS_DAILY_TTL=30

# Frontend analytics
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Redis Configuration

Ensure Redis is properly configured:
```bash
# Start Redis
redis-server

# Check connection
redis-cli ping
# Should return: PONG

# View analytics keys
redis-cli KEYS "analytics:*"

# Check specific metric
redis-cli HGETALL "analytics:requests:count"
```

## Performance Considerations

### Backend
- Uses Redis sorted sets for efficient time-series data
- TTL automatically expires old data
- Minimal overhead per request (~1-2ms)
- Falls back to in-memory if Redis unavailable

### Frontend
- Auto-refresh intervals configurable
- Data cached in component state
- Lazy loading for chart components
- Optimized re-renders with React memo

### Scalability
- Horizontal scaling: Multiple API instances can write to same Redis
- Vertical scaling: Redis can handle millions of keys
- Data retention: Configurable TTL prevents unbounded growth
- Query optimization: Pre-aggregated hourly/daily stats

## Security

### Access Control
- Analytics endpoints should be protected with admin authentication
- Add JWT middleware to `/analytics/*` routes
- Implement role-based access control (RBAC)

### Data Privacy
- User agent strings are stored
- IP addresses are tracked (consider anonymization)
- No PII (Personally Identifiable Information) in events
- Comply with GDPR/privacy regulations

### Example Protection
```python
from fastapi import Depends
from app.auth import require_admin

@router.get("/overview", dependencies=[Depends(require_admin)])
async def get_analytics_overview(...):
    ...
```

## Maintenance

### Regular Tasks

1. **Monitor Redis Memory Usage**
   ```bash
   redis-cli INFO memory
   ```

2. **Check Key Counts**
   ```bash
   redis-cli DBSIZE
   ```

3. **Review Error Logs**
   - Check for analytics middleware errors
   - Monitor Redis connection issues

4. **Optimize Slow Queries**
   - Review performance metrics
   - Add indexes if needed
   - Adjust caching strategies

### Backup and Recovery

```bash
# Backup Redis data
redis-cli BGSAVE

# Restore from backup
redis-cli SHUTDOWN SAVE
cp /var/lib/redis/dump.rdb /backup/location/
```

## Future Enhancements

- [ ] Real-time dashboard updates with WebSockets
- [ ] Custom date range selection
- [ ] Export analytics data (CSV/JSON)
- [ ] Email alerts for high error rates
- [ ] Anomaly detection
- [ ] A/B testing support
- [ ] Session tracking
- [ ] User journey analysis
- [ ] Conversion funnel tracking
- [ ] Geographic data (GeoIP)
- [ ] Custom dashboards
- [ ] Scheduled reports

## API Reference

See full API documentation at `/docs` when running the application.

All analytics endpoints return JSON with:
- Consistent timestamp format (ISO 8601)
- Proper HTTP status codes
- Error messages on failure
- Pagination where applicable

## Contributing

When adding new analytics features:

1. Update middleware to track new metrics
2. Add API endpoints for data retrieval
3. Create frontend components for visualization
4. Update this documentation
5. Add tests for new functionality
6. Update OpenAPI schema

## Support

For issues or questions:
- Check logs: `docker-compose logs api`
- Review Redis: `redis-cli MONITOR`
- Test endpoints: `curl http://localhost:8000/analytics/overview`
- Open GitHub issue with details
