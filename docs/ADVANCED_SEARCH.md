# Advanced Search & Filtering Documentation

## Overview

The Federal Bills Explainer features a powerful search system built on Elasticsearch, providing full-text search, advanced filtering, autocomplete, search history tracking, and saved filter presets. This document covers the complete search architecture, API endpoints, frontend components, and usage guidelines.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Backend Components](#backend-components)
3. [API Endpoints](#api-endpoints)
4. [Frontend Components](#frontend-components)
5. [Search Features](#search-features)
6. [Usage Guide](#usage-guide)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Future Enhancements](#future-enhancements)

---

## Architecture

### System Components

```
┌─────────────────┐
│   Frontend      │
│  - SearchBar    │
│  - Filters      │
│  - History      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│  /search/*      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│  Elastic│ │  Redis  │
│  Search │ │ History │
└─────────┘ └─────────┘
```

### Key Technologies

- **Elasticsearch**: Full-text search engine with relevance ranking
- **Redis**: Search history and popular queries tracking
- **FastAPI**: Search API with async support
- **React/Next.js**: Frontend search components

---

## Backend Components

### 1. Elasticsearch Client

**Location**: `packages/py-core/fbx_core/search/elasticsearch_client.py`

Provides connection management and core operations:

```python
from fbx_core.search import get_elasticsearch_client

# Get client instance
es_client = get_elasticsearch_client()

# Connect to Elasticsearch
await es_client.connect()

# Create an index
await es_client.create_index("bills", mappings, settings)

# Search
results = await es_client.search(
    index_name="bills",
    query={"match_all": {}},
    size=20
)
```

**Key Methods**:
- `connect()` - Establish connection
- `create_index()` - Create index with mappings
- `index_document()` - Index single document
- `bulk_index()` - Bulk index documents
- `search()` - Execute search query
- `suggest()` - Get autocomplete suggestions
- `get_document()` - Retrieve by ID
- `update_document()` - Partial update
- `delete_document()` - Delete document

### 2. Bill Indexer

**Location**: `packages/py-core/fbx_core/search/bill_indexer.py`

Manages bill indexing into Elasticsearch:

```python
from fbx_core.search import BillIndexer, get_elasticsearch_client

es_client = get_elasticsearch_client()
indexer = BillIndexer(es_client)

# Create index
await indexer.create_index()

# Index a single bill
await indexer.index_bill(bill_data)

# Bulk index bills
await indexer.bulk_index_bills(bills_list)
```

**Index Mapping**:
- **bill_id**: Keyword (unique identifier)
- **congress**: Integer
- **bill_type**: Keyword (hr, s, hjres, sjres)
- **title**: Text with completion suggester
- **summary**: Text with English analyzer
- **full_text**: Text for content search
- **sponsor**: Text with keyword subfield
- **committees**: Text array with keyword subfield
- **subjects**: Text array with keyword subfield
- **policy_area**: Text with keyword subfield
- **status**: Keyword
- **dates**: Date fields (introduced, updated, latest_action)
- **search_boost**: Float for relevance boosting

**Search Boosting**:
Bills automatically receive boost scores based on:
- Has public law: +2.0
- 50+ cosponsors: +1.0
- 20-49 cosponsors: +0.5

### 3. Search Service

**Location**: `packages/py-core/fbx_core/search/search_service.py`

Provides high-level search operations:

```python
from fbx_core.search import SearchService, get_elasticsearch_client

es_client = get_elasticsearch_client()
service = SearchService(es_client)

# Advanced search
results = await service.search(
    query="climate change",
    congress=[118, 117],
    bill_type=["hr", "s"],
    status=["introduced", "passed"],
    sponsor_party=["D"],
    has_public_law=False,
    date_from="2023-01-01",
    date_to="2024-12-31",
    sort_by="relevance",
    page=1,
    page_size=20
)

# Autocomplete
suggestions = await service.autocomplete("climate")

# Facets for filter counts
facets = await service.get_facets(query="healthcare")

# Similar bills
similar = await service.get_similar_bills("118/hr/1234", size=10)
```

**Search Algorithm**:
1. Full-text search across multiple fields with boosting:
   - Title: 3x boost
   - Summary: 2x boost
   - Sponsor: 1.5x boost
   - Committees, subjects: 1x boost
   - Full text: 1x boost

2. Fuzzy matching for typo tolerance
3. Boolean filters for exact criteria
4. Relevance scoring with custom boost field
5. Sorting by multiple fields

### 4. Search History

**Location**: `packages/py-core/fbx_core/search/search_history.py`

Tracks and retrieves search history:

```python
from fbx_core.search import SearchHistory
from fbx_core.cache import get_redis_client

redis = get_redis_client()
history = SearchHistory(redis)

# Track a search
await history.track_search(
    query="climate change",
    user_id="user_123",  # Optional
    ip_address="192.168.1.1",
    results_count=50,
    filters={"congress": [118]}
)

# Get popular searches
popular = await history.get_popular_searches(limit=10)

# Get user history
user_history = await history.get_user_history("user_123", limit=20)

# Get trending searches
trending = await history.get_trending_searches(hours=24, limit=10)

# Clear user history
await history.clear_user_history("user_123")
```

**Redis Keys**:
- `search:popular` - Sorted set of popular queries (by count)
- `search:trending` - Sorted set of trending queries (by timestamp)
- `search:user:{user_id}` - List of user's recent searches
- `search:ip:{ip}` - List of IP-based searches (anonymous)

**Data Retention**:
- User history: 90 days, 50 searches max
- IP history: 7 days, 20 searches max
- Popular searches: 30 days
- Trending: Continuous, top 1000

---

## API Endpoints

All endpoints are under `/search` prefix.

### POST/GET `/search/search`

Advanced search with multiple filters.

**Query Parameters**:
- `query` (string): Search query text
- `congress` (string): Comma-separated congress numbers
- `bill_type` (string): Comma-separated types (hr, s, hjres, sjres)
- `status` (string): Comma-separated statuses
- `sponsor_party` (string): Comma-separated parties (D, R, I)
- `sponsor_state` (string): Comma-separated states
- `committees` (string): Comma-separated committee names
- `subjects` (string): Comma-separated subjects
- `policy_area` (string): Policy area
- `has_public_law` (boolean): Filter bills that became law
- `date_from` (string): Start date (YYYY-MM-DD)
- `date_to` (string): End date (YYYY-MM-DD)
- `sort_by` (string): Sort field (relevance, date, cosponsors, congress)
- `sort_order` (string): Sort order (asc, desc)
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Results per page (default: 20, max: 100)

**Response**:
```json
{
  "bills": [...],
  "total": 1234,
  "page": 1,
  "page_size": 20,
  "total_pages": 62,
  "has_more": true
}
```

**Example**:
```bash
curl "http://localhost:8000/search/search?query=healthcare&congress=118&page=1&page_size=20"
```

### GET `/search/autocomplete`

Get autocomplete suggestions.

**Query Parameters**:
- `query` (string, required): Query text (min 2 chars)
- `field` (string): Field to suggest from (default: "title.suggest")
- `size` (integer): Number of suggestions (default: 10, max: 20)

**Response**:
```json
{
  "query": "climate",
  "suggestions": [
    "Climate Action Now Act",
    "Climate Change Education Act",
    "Climate Innovation Act"
  ]
}
```

**Caching**: 5 minutes

### GET `/search/facets`

Get facet counts for filter options.

**Query Parameters**:
- `query` (string): Search query to scope facets
- `congress` (string): Current congress filter
- `bill_type` (string): Current bill type filter
- `status` (string): Current status filter

**Response**:
```json
{
  "congress": [
    {"value": 118, "count": 1234},
    {"value": 117, "count": 987}
  ],
  "bill_type": [
    {"value": "hr", "count": 5678},
    {"value": "s", "count": 2345}
  ],
  "status": [
    {"value": "introduced", "count": 8901},
    {"value": "passed", "count": 234}
  ],
  "sponsor_party": [
    {"value": "D", "count": 4567},
    {"value": "R", "count": 3890}
  ],
  "policy_area": [
    {"value": "Healthcare", "count": 789},
    {"value": "Education", "count": 456}
  ]
}
```

**Caching**: 1 minute

### GET `/search/similar/{bill_id}`

Find similar bills using machine learning.

**Path Parameters**:
- `bill_id` (string): Bill ID (e.g., "118/hr/1234")

**Query Parameters**:
- `size` (integer): Number of similar bills (default: 10, max: 20)

**Response**:
```json
{
  "bill_id": "118/hr/1234",
  "similar_bills": [...],
  "count": 10
}
```

**Algorithm**: Uses Elasticsearch's "More Like This" query to find bills with similar content based on title, summary, and subjects.

**Caching**: 1 hour

### GET `/search/history/popular`

Get most popular search queries.

**Query Parameters**:
- `limit` (integer): Number of results (default: 10, max: 50)

**Response**:
```json
{
  "popular_searches": [
    {"query": "healthcare", "count": 1234},
    {"query": "climate change", "count": 987}
  ],
  "count": 2
}
```

**Caching**: 5 minutes

### GET `/search/history/trending`

Get trending searches in the last N hours.

**Query Parameters**:
- `hours` (integer): Hours to look back (default: 24, max: 168)
- `limit` (integer): Number of results (default: 10, max: 50)

**Response**:
```json
{
  "trending_searches": [
    {"query": "infrastructure", "timestamp": "2025-11-13T10:30:00Z"},
    {"query": "education funding", "timestamp": "2025-11-13T10:25:00Z"}
  ],
  "count": 2,
  "hours": 24
}
```

**Caching**: 1 minute

### GET `/search/history/my`

Get search history for current user/session.

**Query Parameters**:
- `limit` (integer): Number of results (default: 20, max: 100)

**Response**:
```json
{
  "history": [
    {
      "query": "healthcare",
      "timestamp": "2025-11-13T10:30:00Z",
      "results_count": 50,
      "filters": {"congress": [118]}
    }
  ],
  "count": 1
}
```

**Note**: Uses IP-based history for anonymous users. TODO: Add user authentication for personalized history.

### DELETE `/search/history/my`

Clear search history for current user/session.

**Response**:
```json
{
  "message": "Search history cleared successfully"
}
```

---

## Frontend Components

### SearchBarEnhanced

**Location**: `apps/frontend/src/components/SearchBarEnhanced.tsx`

Enhanced search bar with autocomplete and history.

**Features**:
- Real-time autocomplete with 300ms debounce
- Recent searches dropdown
- Popular searches display
- Keyboard navigation (arrow keys, enter, escape)
- Loading indicator
- Mobile-responsive

**Props**:
```typescript
interface SearchBarEnhancedProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  showHistory?: boolean; // Show recent/popular searches
}
```

**Usage**:
```tsx
import { SearchBarEnhanced } from '@/components';

<SearchBarEnhanced
  value={query}
  onChange={setQuery}
  onSubmit={handleSearch}
  showHistory={true}
/>
```

### AdvancedFilterPanel

**Location**: `apps/frontend/src/components/AdvancedFilterPanel.tsx`

Multi-select filter panel with facets.

**Features**:
- Multi-select checkboxes for all filters
- Facet counts (result counts per filter option)
- Date range selector
- Sort options
- Active filter count badge
- Quick reset button

**Props**:
```typescript
interface AdvancedFilterPanelProps {
  values: AdvancedFilterValues;
  onChange: (values: AdvancedFilterValues) => void;
  onApply: () => void;
  onReset: () => void;
  showFacets?: boolean; // Show result counts
}
```

**Filter Values**:
```typescript
interface AdvancedFilterValues {
  congress?: number[];
  bill_type?: string[];
  status?: string[];
  sponsor_party?: string[];
  sponsor_state?: string[];
  policy_area?: string;
  has_public_law?: boolean;
  date_from?: string;
  date_to?: string;
  sortBy?: string;
  sortOrder?: string;
}
```

**Usage**:
```tsx
import { AdvancedFilterPanel } from '@/components';

<AdvancedFilterPanel
  values={filters}
  onChange={setFilters}
  onApply={handleApplyFilters}
  onReset={handleResetFilters}
  showFacets={true}
/>
```

### SearchHistory

**Location**: `apps/frontend/src/components/SearchHistory.tsx`

Displays recent and popular searches.

**Features**:
- Recent searches with timestamps
- Popular searches with counts
- Click to re-run search
- Clear history button
- Relative time display (e.g., "5m ago", "2h ago")

**Props**:
```typescript
interface SearchHistoryProps {
  onSelectQuery: (query: string) => void;
}
```

**Usage**:
```tsx
import { SearchHistory } from '@/components';

<SearchHistory
  onSelectQuery={(query) => {
    setQuery(query);
    handleSearch();
  }}
/>
```

### SavedFilterPresets

**Location**: `apps/frontend/src/components/SavedFilterPresets.tsx`

Save and manage filter presets.

**Features**:
- Save current filters as preset
- Apply saved presets
- Delete presets
- LocalStorage persistence
- Filter summary display

**Props**:
```typescript
interface SavedFilterPresetsProps {
  currentFilters: AdvancedFilterValues;
  onApplyPreset: (filters: AdvancedFilterValues) => void;
}
```

**Usage**:
```tsx
import { SavedFilterPresets } from '@/components';

<SavedFilterPresets
  currentFilters={filters}
  onApplyPreset={(preset) => {
    setFilters(preset);
    handleApplyFilters();
  }}
/>
```

**Storage**: Presets are stored in browser LocalStorage under key `filter_presets`.

---

## Search Features

### 1. Full-Text Search

Searches across multiple fields:
- Bill title (highest priority)
- Summary
- Sponsor name
- Committees
- Subjects
- Full bill text

**Example Queries**:
- `"climate change"` - Exact phrase
- `healthcare reform` - Both terms
- `tax OR revenue` - Either term
- `infrastructure NOT highway` - Exclude term

### 2. Fuzzy Matching

Automatic typo tolerance:
- `helthcare` → healthcare
- `infrastructur` → infrastructure
- `edcuation` → education

**Algorithm**: Levenshtein distance with AUTO setting (1-2 edits based on term length).

### 3. Multi-Select Filters

Combine multiple criteria:
- Multiple congresses (e.g., 118, 117)
- Multiple bill types (e.g., HR, S)
- Multiple statuses (e.g., introduced, passed)
- Multiple parties (e.g., D, R)

**Logic**: OR within filter, AND between filters.

Example: `congress=[118,117] AND bill_type=[hr,s]` means:
- (Congress 118 OR 117) AND (Type HR OR S)

### 4. Date Range Filtering

Filter by introduction date:
- From date only: All bills since date
- To date only: All bills before date
- Both: Bills in date range

### 5. Autocomplete

Smart suggestions as you type:
- Based on bill titles
- Completion suggester optimized for prefix matching
- Returns up to 10 suggestions
- 300ms debounce for performance

### 6. Search History

Tracks all searches:
- User-specific (with authentication)
- IP-based (anonymous users)
- Timestamp and result count
- Applied filters

### 7. Popular & Trending

Discover what others are searching:
- **Popular**: Most searched overall
- **Trending**: Recent popular searches

### 8. Similar Bills

Machine learning-powered similarity:
- Based on title, summary, subjects
- Uses TF-IDF and BM25 algorithms
- Returns bills with similar content

### 9. Faceted Navigation

Filter counts show available options:
- See how many bills match each filter
- Helps narrow down results
- Updates dynamically

### 10. Saved Presets

Quick access to common filters:
- Save filter combinations
- Name and describe presets
- One-click application
- Stored locally

---

## Usage Guide

### Setting Up Elasticsearch

1. **Install Elasticsearch**:
```bash
# Using Docker
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0

# Or install natively
# https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html
```

2. **Configure Environment Variables**:
```bash
# .env
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379/0
```

3. **Create Index**:
```bash
curl -X POST http://localhost:8000/search/index/create
```

4. **Index Bills**:
```python
from fbx_core.search import BillIndexer, get_elasticsearch_client

es_client = get_elasticsearch_client()
indexer = BillIndexer(es_client)

# Fetch bills from database/API
bills = fetch_bills_from_source()

# Bulk index
await indexer.bulk_index_bills(bills)
```

### Basic Search

```bash
# Simple query
curl "http://localhost:8000/search/search?query=healthcare"

# With filters
curl "http://localhost:8000/search/search?query=healthcare&congress=118&bill_type=hr&page=1"
```

### Advanced Search

```bash
# Multiple filters
curl "http://localhost:8000/search/search?\
query=climate%20change&\
congress=118,117&\
bill_type=hr,s&\
status=introduced,passed&\
sponsor_party=D&\
date_from=2023-01-01&\
sort_by=date&\
sort_order=desc&\
page=1&\
page_size=20"
```

### Autocomplete

```bash
curl "http://localhost:8000/search/autocomplete?query=clim"
```

### Search History

```bash
# Popular searches
curl "http://localhost:8000/search/history/popular"

# Trending searches
curl "http://localhost:8000/search/history/trending?hours=24"

# My history
curl "http://localhost:8000/search/history/my"
```

---

## Configuration

### Elasticsearch Settings

**Index Settings** (`BillIndexer.SETTINGS`):
```python
{
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
```

**Recommendations**:
- **Shards**: 1 for < 50GB, 2-5 for 50-500GB
- **Replicas**: 1 for production (high availability)
- **Analyzer**: English for better stemming

### Search Parameters

**Relevance Tuning**:
Adjust field boosts in `SearchService._build_query()`:
```python
"fields": [
    "title^3",      # Increase for title importance
    "summary^2",    # Summary weight
    "sponsor^1.5",  # Sponsor weight
    # ...
]
```

**Fuzzy Matching**:
Adjust in `SearchService._build_query()`:
```python
"fuzziness": "AUTO"  # AUTO, 0, 1, or 2
```

**Facet Sizes**:
Increase for more options in `SearchService.get_facets()`:
```python
"terms": {"field": "congress", "size": 20}  # Default: 20
```

### Redis Configuration

**Memory Management**:
```bash
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

**Persistence** (optional):
```bash
# redis.conf
save 900 1      # Save after 900 sec if 1 key changed
save 300 10     # Save after 300 sec if 10 keys changed
save 60 10000   # Save after 60 sec if 10000 keys changed
```

---

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Elasticsearch

**Solutions**:
1. Check Elasticsearch is running: `curl http://localhost:9200`
2. Verify `ELASTICSEARCH_URL` in .env
3. Check network/firewall settings
4. Review logs: `docker logs elasticsearch`

### No Search Results

**Problem**: Search returns 0 results

**Solutions**:
1. Verify index exists: `curl http://localhost:9200/bills/_count`
2. Check documents are indexed: `curl http://localhost:9200/bills/_search`
3. Try simpler query (e.g., `query=*` for match all)
4. Review query syntax in logs

### Slow Searches

**Problem**: Searches take > 1 second

**Solutions**:
1. Add more shards for large datasets
2. Increase Elasticsearch heap size
3. Use pagination (smaller page_size)
4. Enable query caching
5. Add replicas for read scaling

### Autocomplete Not Working

**Problem**: No autocomplete suggestions

**Solutions**:
1. Verify completion field in mapping: `title.suggest`
2. Check suggestions endpoint: `/search/autocomplete?query=test`
3. Ensure bills are indexed with title field
4. Review frontend debounce (should wait 300ms)

### History Not Tracking

**Problem**: Search history not saving

**Solutions**:
1. Check Redis connection: `redis-cli ping`
2. Verify `REDIS_URL` in .env
3. Check Redis memory: `redis-cli INFO memory`
4. Review Redis logs for errors

---

## Future Enhancements

### Planned Features

1. **Natural Language Processing**
   - Entity extraction (people, organizations, locations)
   - Sentiment analysis on bill summaries
   - Topic modeling for automatic categorization

2. **Machine Learning**
   - Learning to rank for personalized results
   - Query understanding and expansion
   - Automated query suggestions

3. **Advanced Filtering**
   - Co-sponsor filtering
   - Committee activity filtering
   - Voting record filtering
   - Amendment tracking

4. **Search Analytics**
   - Search performance metrics
   - Query analysis and optimization
   - A/B testing for search algorithms

5. **User Features**
   - Saved searches with alerts
   - Search result export
   - Share search URLs
   - Collaborative filter sets

6. **Performance**
   - Query result caching
   - Aggregation caching
   - Search result pre-fetching
   - Distributed search

7. **Integration**
   - GraphQL search API
   - Webhook notifications for new matches
   - REST API versioning
   - OpenAPI schema generation

---

## API Limits

- **Search Page Size**: Max 100 results per page
- **Autocomplete**: Max 20 suggestions
- **Similar Bills**: Max 20 results
- **Search History**: Max 100 items per user/IP
- **Popular Searches**: Max 50 results
- **Trending Searches**: Max 168 hours lookback

---

## Performance Metrics

Expected performance (with properly configured Elasticsearch):

- **Simple Search**: < 100ms
- **Advanced Search (5+ filters)**: < 200ms
- **Autocomplete**: < 50ms
- **Facets**: < 150ms
- **Similar Bills**: < 300ms
- **Search History**: < 10ms (Redis)

---

## Support

For issues or questions:
- Review Elasticsearch logs: `docker logs elasticsearch`
- Check API logs: `docker-compose logs api`
- Test endpoints directly: `curl http://localhost:8000/search/*`
- Monitor Redis: `redis-cli MONITOR`
- Open GitHub issue with details

---

## References

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Full-Text Search Best Practices](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html)
