# 🔌 API Reference

Complete API documentation for the Browser Isolation System REST API.

---

## Base URL

```
Production: https://api.yourdomain.com
Development: http://localhost:8000
```

## Authentication

Currently, the API is open for demonstration. For production:

```http
Authorization: Bearer <your_api_token>
```

---

## Endpoints

### Health Check

**GET** `/api/v1/health`

Check API health and status.

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "chromium_available": true,
  "active_renders": 2,
  "total_renders": 150
}
```

#### Example

```bash
curl http://localhost:8000/api/v1/health
```

---

### Render URL

**POST** `/api/v1/render`

Isolate and render a URL in the headless browser.

#### Request Body

```json
{
  "url": "https://example.com",
  "timeout": 30,
  "wait_for_load": true,
  "block_trackers": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to isolate (must start with http/https) |
| `timeout` | integer | No | 30 | Timeout in seconds (5-120) |
| `wait_for_load` | boolean | No | true | Wait for full page load |
| `block_trackers` | boolean | No | true | Remove tracking elements |

#### Response

```json
{
  "render_id": "render-a1b2c3d4e5f6g7h8",
  "url": "https://example.com",
  "status": "completed",
  "html": "<html>...</html>",
  "metadata": {
    "url": "https://example.com",
    "timestamp": "2025-11-22T14:30:00",
    "render_id": "render-a1b2c3d4e5f6g7h8",
    "original_size": 25600,
    "sanitized_size": 8900,
    "fetch_time": 2.5,
    "sanitization_time": 0.3,
    "risk_score": 3.2,
    "removed_elements": {
      "scripts": 12,
      "event_handlers": 45,
      "iframes": 2,
      "trackers": 8
    },
    "status": "success"
  },
  "warnings": [
    "JavaScript execution blocked: 12 scripts removed",
    "Privacy protection: Removed 8 tracking elements"
  ],
  "blocked_content": [
    {
      "type": "scripts",
      "count": "12",
      "description": "JavaScript code removed for security",
      "risk": "high"
    },
    {
      "type": "trackers",
      "count": "8",
      "description": "Tracking and analytics removed",
      "risk": "low"
    }
  ],
  "risk_score": 3.2,
  "timestamp": "2025-11-22T14:30:00"
}
```

#### Example

```bash
curl -X POST http://localhost:8000/api/v1/render \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "timeout": 30,
    "wait_for_load": true,
    "block_trackers": true
  }'
```

#### Error Responses

**400 Bad Request** - Invalid input

```json
{
  "error": "Validation Error",
  "detail": "URL must start with http:// or https://"
}
```

**403 Forbidden** - URL blocked by policy

```json
{
  "error": "Policy Violation",
  "detail": "URL blocked by policy: Domain is in blocklist"
}
```

**500 Internal Server Error** - Server error

```json
{
  "error": "Internal Server Error",
  "detail": "Rendering failed: Timeout"
}
```

---

### Check URL Policy

**POST** `/api/v1/check-url`

Check if a URL is allowed by policy without rendering.

#### Request Body

```json
{
  "url": "https://example.com"
}
```

#### Response

```json
{
  "url": "https://example.com",
  "allowed": true,
  "reason": "No blocking rules matched, isolation will sanitize content",
  "risk_level": "low",
  "matched_rules": ["default_allow"]
}
```

#### Example

```bash
curl -X POST http://localhost:8000/api/v1/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

### Get Audit Logs

**GET** `/api/v1/audit`

Retrieve audit logs of isolation operations.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 50 | Number of entries (1-500) |
| `offset` | integer | No | 0 | Pagination offset |
| `event_type` | string | No | - | Filter by event type |

#### Response

```json
{
  "total": 150,
  "entries": [
    {
      "timestamp": "2025-11-22T14:30:00",
      "event_type": "render_success",
      "url": "https://example.com",
      "render_id": "render-abc123",
      "user": null,
      "action": "render",
      "details": {
        "risk_score": 3.2,
        "removed_scripts": 12,
        "removed_event_handlers": 45
      },
      "risk_score": 3.2
    }
  ],
  "from_date": null,
  "to_date": null
}
```

#### Example

```bash
# Get last 10 entries
curl "http://localhost:8000/api/v1/audit?limit=10"

# Filter by event type
curl "http://localhost:8000/api/v1/audit?event_type=render_success&limit=20"
```

---

### Get Policies

**GET** `/api/v1/policies`

Get active policy configuration summary.

#### Response

```json
{
  "blocked_domains_count": 15,
  "allowed_domains_count": 7,
  "blocked_categories": ["ads", "trackers", "cryptominers", "malware", "phishing"],
  "blocked_patterns_count": 5,
  "allowed_patterns_count": 2,
  "malware_domains_count": 5,
  "phishing_domains_count": 3
}
```

#### Example

```bash
curl http://localhost:8000/api/v1/policies
```

---

### Get Render Status

**GET** `/api/v1/status/{render_id}`

Get status of a specific render operation (for async implementations).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `render_id` | string | Yes | Render operation ID |

#### Response

```json
{
  "render_id": "render-abc123",
  "status": "completed",
  "url": "https://example.com",
  "progress": 100,
  "created_at": "2025-11-22T14:30:00",
  "completed_at": "2025-11-22T14:30:05",
  "error": null
}
```

#### Example

```bash
curl http://localhost:8000/api/v1/status/render-abc123
```

---

## Rate Limiting

Default rate limits:
- **Public API:** 100 requests per minute
- **Authenticated:** 1000 requests per minute

Rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638360000
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Missing or invalid token |
| `403` | Forbidden - Policy violation |
| `404` | Not Found - Resource not found |
| `422` | Unprocessable Entity - Validation error |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

---

## Interactive Documentation

Visit these URLs for interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## SDK Examples

### Python

```python
import httpx

# Initialize client
client = httpx.Client(base_url="http://localhost:8000")

# Render URL
response = client.post("/api/v1/render", json={
    "url": "https://example.com",
    "timeout": 30
})
result = response.json()
print(f"Risk Score: {result['risk_score']}/10")

# Check policy
response = client.post("/api/v1/check-url", json={
    "url": "https://suspicious-site.com"
})
policy = response.json()
print(f"Allowed: {policy['allowed']}")
```

### JavaScript

```javascript
// Render URL
const response = await fetch('http://localhost:8000/api/v1/render', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://example.com',
    timeout: 30
  })
});

const result = await response.json();
console.log(`Risk Score: ${result.risk_score}/10`);
```

### cURL

```bash
# Complete workflow example
# 1. Check policy
curl -X POST http://localhost:8000/api/v1/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 2. Render if allowed
curl -X POST http://localhost:8000/api/v1/render \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  | jq '.risk_score'

# 3. Get audit logs
curl "http://localhost:8000/api/v1/audit?limit=5" | jq '.entries'
```

---

## Webhook Integration (Future)

Subscribe to events:

```json
POST /api/v1/webhooks
{
  "url": "https://your-server.com/webhook",
  "events": ["render_complete", "high_risk_detected"],
  "secret": "your-webhook-secret"
}
```

Webhook payload:

```json
{
  "event": "render_complete",
  "timestamp": "2025-11-22T14:30:00",
  "data": {
    "render_id": "render-abc123",
    "url": "https://example.com",
    "risk_score": 3.2
  }
}
```

---

## Best Practices

1. **Always check policy first** before rendering
2. **Use appropriate timeouts** based on expected page complexity
3. **Handle errors gracefully** with retry logic
4. **Monitor rate limits** to avoid throttling
5. **Review audit logs** regularly for security insights
6. **Cache results** when appropriate to reduce API calls

---

## Support

- **Documentation:** [README.md](README.md)
- **Issues:** [GitHub Issues](https://github.com/yourusername/browser_isolation/issues)
- **Email:** support@example.com

---

**API Version:** 1.0.0  
**Last Updated:** 2025-11-22

