# Demo Protection Implementation

This document describes the access code and rate limiting protection added to MedContext for public demo deployments.

## Overview

To prevent malicious actors from running up API costs, MedContext includes:

1. **Access Code Validation** - Simple authentication via header or query parameter
2. **Rate Limiting** - 10 requests per IP address per hour
3. **Protected Endpoints** - Only main API routes require protection

## Configuration

### Environment Variable

Set the `DEMO_ACCESS_CODE` in your `.env` file:

```bash
# For public demo
DEMO_ACCESS_CODE=MEDCONTEXT-DEMO-2026

# For local development (no protection)
DEMO_ACCESS_CODE=
```

### Docker Deployment

The access code is automatically passed to the Docker container via `docker-compose.yml`:

```yaml
environment:
  - DEMO_ACCESS_CODE=${DEMO_ACCESS_CODE}
```

## Usage

### Via Web UI

1. Navigate to the demo site
2. Click **"Settings"** in the top-right corner
3. Enter the access code in the **"Demo Access Code"** field
4. The code is stored in your browser's localStorage
5. All subsequent requests will include the access code automatically

### Via API/cURL

Include the access code in the `X-Demo-Access-Code` header:

```bash
curl -X POST http://your-demo-url/api/v1/orchestrator/run \
  -H "X-Demo-Access-Code: MEDCONTEXT-DEMO-2026" \
  -F "file=@image.jpg" \
  -F "context=Your context here"
```

Or as a query parameter:

```bash
curl -X POST "http://your-demo-url/api/v1/orchestrator/run?access_code=MEDCONTEXT-DEMO-2026" \
  -F "file=@image.jpg" \
  -F "context=Your context here"
```

## Protected Endpoints

The following endpoints require an access code:

- `POST /api/v1/orchestrator/run`
- `POST /api/v1/ingestion/upload`
- `POST /api/v1/forensics/analyze`
- `POST /api/v1/reverse-search/search`
- `GET /api/v1/reverse-search/results/{image_id}`

Public endpoints (no access code required):

- `GET /health`
- `GET /docs`
- `GET /openapi.json`

## Rate Limiting

**Limits:**

- 10 requests per IP address per hour
- In-memory tracking (resets on server restart)
- Separate limit per IP address

**Exceeded Limit Response:**

```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per hour."
}
```

HTTP Status: `429 Too Many Requests`

## Error Responses

### Missing Access Code

```json
{
  "detail": "Access denied. Valid access code required. See README for instructions."
}
```

HTTP Status: `403 Forbidden`

### Invalid Access Code

```json
{
  "detail": "Access denied. Valid access code required. See README for instructions."
}
```

HTTP Status: `403 Forbidden`

## Implementation Details

### Middleware

The protection is implemented as a FastAPI middleware in `src/app/middleware/demo_protection.py`:

```python
class DemoProtectionMiddleware(BaseHTTPMiddleware):
    """Simple access code validation and rate limiting."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._request_log: dict[str, list[float]] = defaultdict(list)
        self._rate_limit_requests = 10
        self._rate_limit_window = 3600  # 1 hour
```

### Security Through Obscurity

This implementation uses **security through obscurity** - the access code is documented but not advertised. This is sufficient for:

- **Demo deployments** - Judges and evaluators can easily access
- **Cost control** - Prevents casual abuse and bot traffic
- **Rate limiting** - Backup protection even if code is shared

### Not for Production Security

This is **NOT** designed for:

- ❌ Protecting sensitive data
- ❌ Authentication/authorization
- ❌ Preventing determined attackers
- ❌ Long-term production use

For production, implement:

- OAuth2 / JWT authentication
- API key management
- Database-backed rate limiting (Redis)
- DDoS protection (Cloudflare, etc.)

## Verification

### Manual Testing

```bash
# Test without code (should fail)
curl -X POST http://localhost:8000/api/v1/orchestrator/run
# Expected: {"detail":"Access denied..."}

# Test with code (should succeed past auth)
curl -X POST http://localhost:8000/api/v1/orchestrator/run \
  -H "X-Demo-Access-Code: MEDCONTEXT-DEMO-2026"
# Expected: 422 (validation error - needs image file)

# Test health check (no code required)
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

> **Note:** The JSON response uses compact formatting (no spaces) as returned by FastAPI's default JSON encoder.

### Expected Cost Impact

With these protections in place:

| Scenario                                     | Cost Estimate |
| -------------------------------------------- | ------------- |
| Normal judge usage (5-10 tests each)         | **$5-15**     |
| Moderate sharing (50 unique users)           | **$25-40**    |
| Malicious actor (before rate limit kicks in) | **$2-5**      |
| **Maximum possible cost**                    | **~$50**      |

The rate limit of 10 requests/hour per IP means even if someone shares the code, total cost is bounded.

## Monitoring

To monitor demo usage:

1. Check application logs for 403 (blocked) and 429 (rate limited) responses
2. Track IP addresses hitting rate limits
3. Monitor API costs in GCP console
4. Set billing alerts at $10, $25, $50

## Disabling Protection

For local development, simply leave `DEMO_ACCESS_CODE` empty in your `.env` file. The middleware will automatically skip validation when no code is configured.

## Future Enhancements

For production deployments, consider:

1. **Database-backed rate limiting** (Redis) for distributed systems
2. **API key management** with per-key quotas
3. **OAuth2 integration** for user authentication
4. **Analytics dashboard** for usage tracking
5. **Automated billing alerts** with emergency shutdown
6. **CAPTCHA** for upload endpoints
7. **Request caching** to reduce duplicate API calls

## Summary

This simple protection layer provides:

✅ **Easy access** for legitimate users (judges, evaluators)  
✅ **Cost control** through rate limiting  
✅ **Abuse prevention** via access code  
✅ **Zero configuration** for local development  
✅ **Minimal complexity** - ~100 lines of code

Perfect for demo/competition deployments where you need basic protection without heavy authentication infrastructure.
