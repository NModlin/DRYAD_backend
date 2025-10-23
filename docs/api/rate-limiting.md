# DRYAD.AI API Rate Limiting Guide

**Version:** 1.0  
**Last Updated:** 2025-10-13

---

## Overview

DRYAD.AI implements rate limiting to ensure fair usage and system stability. Rate limits are applied per API key or access token.

---

## Rate Limit Tiers

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|--------------|
| **Free** | 100 | 5,000 | 100,000 |
| **Pro** | 1,000 | 50,000 | 1,000,000 |
| **Enterprise** | Custom | Custom | Custom |

---

## Rate Limit Headers

Every API response includes rate limit information in the headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699999999
X-RateLimit-Retry-After: 60
```

**Header Descriptions:**
- `X-RateLimit-Limit`: Maximum requests allowed in the current window
- `X-RateLimit-Remaining`: Requests remaining in the current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `X-RateLimit-Retry-After`: Seconds to wait before retrying (only on 429 responses)

---

## Handling Rate Limits

### Python Example

```python
import time
from datetime import datetime

def make_request_with_rate_limit(client, endpoint):
    """Make request with automatic rate limit handling."""
    while True:
        try:
            response = client.get(endpoint)
            
            # Check remaining requests
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(0, reset_time - time.time())
                print(f"Approaching rate limit. Waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited. Retrying after {retry_after}s...")
                time.sleep(retry_after)
                continue
            raise
```

### JavaScript Example

```javascript
async function makeRequestWithRateLimit(client, endpoint) {
  while (true) {
    try {
      const response = await client.get(endpoint);
      
      // Check remaining requests
      const remaining = parseInt(response.headers['x-ratelimit-remaining'] || 0);
      if (remaining < 10) {
        const resetTime = parseInt(response.headers['x-ratelimit-reset'] || 0);
        const waitTime = Math.max(0, resetTime - Date.now() / 1000);
        console.log(`Approaching rate limit. Waiting ${waitTime.toFixed(0)}s...`);
        await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
      }
      
      return response.data;
      
    } catch (error) {
      if (error.response?.status === 429) {
        const retryAfter = parseInt(error.response.headers['retry-after'] || 60);
        console.log(`Rate limited. Retrying after ${retryAfter}s...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }
      throw error;
    }
  }
}
```

---

## Best Practices

### 1. Monitor Rate Limit Headers

Always check rate limit headers and adjust request rate accordingly:

```python
def adaptive_rate_limiter(client, endpoints):
    """Adaptively adjust request rate based on remaining quota."""
    for endpoint in endpoints:
        response = client.get(endpoint)
        
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        limit = int(response.headers.get('X-RateLimit-Limit', 1000))
        
        # Slow down when approaching limit
        if remaining < limit * 0.1:  # Less than 10% remaining
            time.sleep(2)
        elif remaining < limit * 0.3:  # Less than 30% remaining
            time.sleep(1)
```

### 2. Implement Request Queuing

Queue requests to stay within rate limits:

```python
from queue import Queue
from threading import Thread
import time

class RateLimitedClient:
    def __init__(self, client, requests_per_minute=100):
        self.client = client
        self.requests_per_minute = requests_per_minute
        self.request_queue = Queue()
        self.worker_thread = Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
    
    def _process_queue(self):
        """Process queued requests at controlled rate."""
        while True:
            if not self.request_queue.empty():
                request = self.request_queue.get()
                try:
                    result = self.client.get(request['endpoint'])
                    request['callback'](result)
                except Exception as e:
                    request['error_callback'](e)
                
                # Wait to maintain rate limit
                time.sleep(60 / self.requests_per_minute)
    
    def get(self, endpoint, callback, error_callback):
        """Queue a GET request."""
        self.request_queue.put({
            'endpoint': endpoint,
            'callback': callback,
            'error_callback': error_callback
        })
```

### 3. Use Batch Endpoints

When available, use batch endpoints to reduce request count:

```python
# Instead of multiple requests
for agent_id in agent_ids:
    agent = client.get(f"/agents/{agent_id}")

# Use batch endpoint
agents = client.post("/agents/batch", json={"ids": agent_ids})
```

### 4. Cache Responses

Cache responses to reduce API calls:

```python
from functools import lru_cache
import time

class CachedClient:
    def __init__(self, client, cache_ttl=300):
        self.client = client
        self.cache_ttl = cache_ttl
        self.cache = {}
    
    def get(self, endpoint):
        """Get with caching."""
        cache_key = endpoint
        
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data
        
        # Fetch from API
        data = self.client.get(endpoint)
        self.cache[cache_key] = (data, time.time())
        return data
```

---

## Rate Limit Strategies

### Strategy 1: Token Bucket

```python
import time
from threading import Lock

class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()
    
    def consume(self, tokens=1):
        """Consume tokens, waiting if necessary."""
        with self.lock:
            # Refill tokens
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                time.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= tokens

# Usage
bucket = TokenBucket(rate=100/60, capacity=100)  # 100 requests per minute

for endpoint in endpoints:
    bucket.consume()
    response = client.get(endpoint)
```

### Strategy 2: Sliding Window

```python
from collections import deque
import time

class SlidingWindowRateLimiter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def allow_request(self):
        """Check if request is allowed."""
        now = time.time()
        
        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        while not self.allow_request():
            time.sleep(0.1)

# Usage
limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)

for endpoint in endpoints:
    limiter.wait_if_needed()
    response = client.get(endpoint)
```

---

## Upgrading Limits

To increase your rate limits:

1. **Upgrade to Pro:** Visit https://dryad.ai/pricing
2. **Enterprise Plan:** Contact sales@dryad.ai for custom limits
3. **Temporary Increase:** Contact support@dryad.ai for special events

---

## Monitoring Usage

Track your API usage:

```python
def track_usage(client):
    """Track API usage over time."""
    usage_log = []
    
    response = client.get("/agents")
    
    usage_log.append({
        'timestamp': time.time(),
        'limit': int(response.headers.get('X-RateLimit-Limit', 0)),
        'remaining': int(response.headers.get('X-RateLimit-Remaining', 0)),
        'reset': int(response.headers.get('X-RateLimit-Reset', 0))
    })
    
    # Calculate usage percentage
    if usage_log:
        latest = usage_log[-1]
        used = latest['limit'] - latest['remaining']
        percentage = (used / latest['limit']) * 100
        print(f"API usage: {percentage:.1f}% ({used}/{latest['limit']})")
```

---

**Last Updated:** 2025-10-13

