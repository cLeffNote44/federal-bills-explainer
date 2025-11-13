# Rate Limiting Documentation

## Overview

The Federal Bills Explainer API implements intelligent rate limiting to protect against abuse while ensuring fair access for all users. Rate limits are enforced per IP address and vary by endpoint category.

## Rate Limit Tiers

### Public Endpoints
- **Limit**: 100 requests per minute
- **Endpoints**: `/bills`, `/bills/{id}`, `/healthz`
- **Use Case**: General browsing and bill lookups

### Search Endpoints
- **Limit**: 30 requests per minute
- **Endpoints**: `/bills/search`, `/bills/autocomplete`
- **Use Case**: Search and autocomplete functionality

### Export Endpoints
- **Limit**: 10 requests per minute
- **Endpoints**: `/export/*`
- **Use Case**: Data export (CSV, JSON)

### Admin Endpoints
- **Limit**: 10 requests per minute
- **Endpoints**: `/admin/*`
- **Use Case**: Administrative operations

## Response Headers

When a request is rate-limited, the API returns HTTP status code `429 Too Many Requests` along with the following headers:

```
X-RateLimit-Limit: 100          # Maximum requests allowed in the time window
X-RateLimit-Remaining: 95       # Remaining requests in current window
X-RateLimit-Reset: 1234567890   # Unix timestamp when the limit resets
Retry-After: 60                 # Seconds to wait before retrying
```

## Example Rate Limit Response

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45,
  "limit": 100,
  "window": "1 minute"
}
```

## Best Practices

### 1. Check Rate Limit Headers

Always check the `X-RateLimit-Remaining` header to know how many requests you have left:

```python
import requests

response = requests.get('https://api.example.com/bills')
remaining = int(response.headers.get('X-RateLimit-Remaining', 0))

if remaining < 10:
    print(f"Warning: Only {remaining} requests remaining!")
```

### 2. Implement Exponential Backoff

When you receive a 429 response, implement exponential backoff:

```python
import time
import requests

def fetch_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            wait_time = retry_after * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### 3. Batch Requests

Instead of making many individual requests, use pagination and filtering:

```python
# Bad: Multiple requests
for i in range(1, 101):
    response = requests.get(f'/bills?page={i}')

# Good: Single request with larger page size
response = requests.get('/bills?page=1&page_size=100')
```

### 4. Cache Responses

Cache frequently accessed data to reduce API calls:

```python
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def get_bill(bill_id):
    response = requests.get(f'/bills/{bill_id}')
    return response.json()

# Subsequent calls use cached data
bill1 = get_bill('118-hr-1234')  # API call
bill2 = get_bill('118-hr-1234')  # Cached
```

### 5. Use Export Endpoints for Bulk Data

For bulk data access, use the export endpoints instead of pagination:

```python
# Bad: Multiple paginated requests
all_bills = []
for page in range(1, 50):
    response = requests.get(f'/bills?page={page}')
    all_bills.extend(response.json())

# Good: Single export request
response = requests.get('/export/json?limit=1000')
all_bills = response.json()['bills']
```

## Rate Limit Bypass for Partners

If you need higher rate limits for integration purposes, please contact the API team at [api@example.com](mailto:api@example.com) with:

1. Your use case and expected request volume
2. Organization details
3. Integration timeline

We offer the following partner tiers:

- **Basic Partner**: 500 requests/minute
- **Premium Partner**: 1,000 requests/minute
- **Enterprise**: Custom limits

## Monitoring Rate Limits

### Using curl

```bash
curl -i https://api.example.com/bills

# Check headers
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

### Using Python

```python
import requests

response = requests.get('https://api.example.com/bills')

print(f"Limit: {response.headers['X-RateLimit-Limit']}")
print(f"Remaining: {response.headers['X-RateLimit-Remaining']}")
print(f"Resets at: {response.headers['X-RateLimit-Reset']}")
```

### Using JavaScript

```javascript
fetch('https://api.example.com/bills')
  .then(response => {
    console.log('Limit:', response.headers.get('X-RateLimit-Limit'));
    console.log('Remaining:', response.headers.get('X-RateLimit-Remaining'));
    console.log('Reset:', response.headers.get('X-RateLimit-Reset'));
    return response.json();
  });
```

## Troubleshooting

### Q: I'm getting rate limited but my app isn't making many requests

**A**: Check if multiple users share the same IP address (corporate network, VPN, etc.). Rate limits are per IP, so shared IPs may hit limits faster.

### Q: Can I request a temporary rate limit increase?

**A**: Yes, contact support for temporary increases during testing or special events.

### Q: Do authenticated requests have higher limits?

**A**: Currently, rate limits are the same for authenticated and unauthenticated requests. Partner programs offer higher limits.

### Q: What happens if I exceed the rate limit?

**A**: You'll receive a 429 status code. Your requests will be rejected until the rate limit window resets (typically 1 minute).

## Implementation Details

The rate limiting is implemented using:

- **Redis**: For distributed rate limiting across multiple API instances
- **Token Bucket Algorithm**: Allows burst traffic while maintaining average rate
- **Sliding Window**: More accurate than fixed windows
- **Per-IP Tracking**: Based on `X-Forwarded-For` header (behind proxy) or direct IP

## Security Note

Excessive rate limit violations may trigger additional security measures:

- **Soft Ban**: Temporary extended rate limit reduction
- **Hard Ban**: IP address blocking (requires manual review)
- **CAPTCHA**: Required verification for suspicious patterns

All rate limit violations are logged and monitored for abuse patterns.

## Contact

For questions about rate limits or to request increases:

- **Email**: api@federalbills.example.com
- **Documentation**: https://docs.federalbills.example.com
- **Status Page**: https://status.federalbills.example.com
