# DRYAD.AI API Error Handling Guide

**Version:** 1.0  
**Last Updated:** 2025-10-13

---

## Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request was invalid or cannot be served",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "request_id": "req_abc123",
    "timestamp": "2025-10-13T10:00:00Z"
  }
}
```

---

## HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions for this resource |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Request conflicts with current state |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server encountered an error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Upstream service timeout |

---

## Error Codes

### Authentication Errors (401)

| Code | Message | Solution |
|------|---------|----------|
| `invalid_token` | The access token is invalid | Obtain a new access token |
| `expired_token` | The access token has expired | Refresh the access token |
| `missing_token` | No authentication token provided | Include Authorization header |
| `invalid_api_key` | The API key is invalid | Check your API key |

### Authorization Errors (403)

| Code | Message | Solution |
|------|---------|----------|
| `insufficient_permissions` | You don't have permission for this action | Request appropriate permissions |
| `tenant_mismatch` | Resource belongs to different tenant | Check tenant ID |
| `resource_locked` | Resource is locked | Wait or contact support |

### Validation Errors (400, 422)

| Code | Message | Solution |
|------|---------|----------|
| `invalid_parameter` | Parameter value is invalid | Check parameter format |
| `missing_parameter` | Required parameter is missing | Include required parameter |
| `invalid_format` | Data format is invalid | Check request body format |
| `validation_failed` | Request validation failed | Review validation errors |

### Resource Errors (404, 409)

| Code | Message | Solution |
|------|---------|----------|
| `not_found` | Resource not found | Check resource ID |
| `already_exists` | Resource already exists | Use different identifier |
| `conflict` | Request conflicts with current state | Resolve conflict |

### Rate Limiting Errors (429)

| Code | Message | Solution |
|------|---------|----------|
| `rate_limit_exceeded` | Too many requests | Wait and retry |
| `quota_exceeded` | Monthly quota exceeded | Upgrade plan |

### Server Errors (500, 502, 503, 504)

| Code | Message | Solution |
|------|---------|----------|
| `internal_error` | Internal server error | Retry or contact support |
| `service_unavailable` | Service temporarily unavailable | Retry with backoff |
| `timeout` | Request timeout | Retry with longer timeout |

---

## Error Handling Examples

### Python

```python
import requests
from requests.exceptions import HTTPError
import time

def make_api_request(client, endpoint, **kwargs):
    """Make API request with error handling."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = client.get(endpoint, **kwargs)
            return response
            
        except HTTPError as e:
            error_data = e.response.json()
            error_code = error_data.get("error", {}).get("code")
            
            # Handle specific errors
            if e.response.status_code == 401:
                # Authentication error - refresh token
                client.refresh_token()
                continue
                
            elif e.response.status_code == 429:
                # Rate limit - wait and retry
                retry_after = int(e.response.headers.get("Retry-After", retry_delay))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
                
            elif e.response.status_code >= 500:
                # Server error - retry with backoff
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Server error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
            # Re-raise if not retryable
            raise
            
        except requests.exceptions.RequestException as e:
            # Network error - retry
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Network error. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise
    
    raise Exception(f"Failed after {max_retries} attempts")
```

### JavaScript

```javascript
async function makeApiRequest(client, endpoint, options = {}) {
  const maxRetries = 3;
  let retryDelay = 1000;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await client.get(endpoint, options);
      return response;
      
    } catch (error) {
      const status = error.response?.status;
      const errorCode = error.response?.data?.error?.code;
      
      // Handle specific errors
      if (status === 401) {
        // Authentication error - refresh token
        await client.refreshToken();
        continue;
        
      } else if (status === 429) {
        // Rate limit - wait and retry
        const retryAfter = parseInt(error.response.headers['retry-after'] || retryDelay / 1000);
        console.log(`Rate limited. Waiting ${retryAfter}s...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
        
      } else if (status >= 500) {
        // Server error - retry with backoff
        if (attempt < maxRetries - 1) {
          const waitTime = retryDelay * Math.pow(2, attempt);
          console.log(`Server error. Retrying in ${waitTime}ms...`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
      }
      
      // Re-throw if not retryable
      throw error;
    }
  }
  
  throw new Error(`Failed after ${maxRetries} attempts`);
}
```

---

## Best Practices

### 1. Always Check Status Codes

```python
response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
elif response.status_code == 404:
    print("Resource not found")
else:
    response.raise_for_status()
```

### 2. Implement Exponential Backoff

```python
def exponential_backoff(attempt, base_delay=1, max_delay=60):
    """Calculate exponential backoff delay."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter to prevent thundering herd
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter
```

### 3. Log Error Details

```python
import logging

try:
    response = client.get("/agents")
except HTTPError as e:
    error_data = e.response.json()
    logging.error(
        "API request failed",
        extra={
            "status_code": e.response.status_code,
            "error_code": error_data.get("error", {}).get("code"),
            "request_id": error_data.get("error", {}).get("request_id"),
            "endpoint": "/agents"
        }
    )
    raise
```

### 4. Handle Rate Limits Gracefully

```python
def handle_rate_limit(response):
    """Handle rate limit response."""
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        
        print(f"Rate limit exceeded. Retry after {retry_after}s")
        print(f"Rate limit resets at {datetime.fromtimestamp(reset_time)}")
        
        time.sleep(retry_after)
        return True
    return False
```

### 5. Validate Before Sending

```python
def validate_workflow_request(data):
    """Validate workflow request before sending."""
    required_fields = ["task", "context"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(data["task"], str):
        raise ValueError("Task must be a string")
    
    if not isinstance(data["context"], dict):
        raise ValueError("Context must be a dictionary")
```

---

## Troubleshooting

### Common Issues

**Issue:** `invalid_token` error  
**Solution:** Refresh your access token or obtain a new one

**Issue:** `rate_limit_exceeded` error  
**Solution:** Implement exponential backoff and respect rate limit headers

**Issue:** `service_unavailable` error  
**Solution:** Check status page at https://status.dryad.ai

**Issue:** `timeout` error  
**Solution:** Increase timeout or break request into smaller chunks

**Issue:** `validation_failed` error  
**Solution:** Check request body against API documentation

---

## Support

For error-related issues:
- **Documentation:** https://docs.dryad.ai
- **Status Page:** https://status.dryad.ai
- **Support:** support@dryad.ai

---

**Last Updated:** 2025-10-13

