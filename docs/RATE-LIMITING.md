# Rate Limiting Configuration Guide

This document explains the rate limiting implementation in Blog AI and provides guidance for production tuning.

## Overview

Blog AI implements **three complementary rate limiting systems**:

| System | Purpose | Storage |
|--------|---------|---------|
| Request Rate Limiter | IP-based request throttling | In-memory |
| User Tier Rate Limiter | Subscription-based limits | Redis or in-memory |
| LLM API Rate Limiter | External API cost control | In-memory |

## Architecture

```
                    ┌─────────────────┐
                    │   Incoming      │
                    │   Request       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  IP Rate Limit  │  60 req/min general
                    │  Middleware     │  10 req/min generation
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ User Tier Limit │  Based on subscription
                    │  Dependency     │  per-minute + per-hour
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Usage Quota     │  Monthly/daily limits
                    │  Check          │  by tier
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ LLM Rate Limit  │  Token bucket
                    │  (if LLM call)  │  per operation type
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Process       │
                    │   Request       │
                    └─────────────────┘
```

---

## 1. Request Rate Limiter (IP-based)

**File:** `app/middleware/rate_limiter.py`

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable middleware |
| `RATE_LIMIT_GENERAL` | `60` | General endpoints (requests/min/IP) |
| `RATE_LIMIT_GENERATION` | `10` | Generation endpoints (requests/min/IP) |

### Endpoint Classification

**Generation Endpoints (stricter limits):**
- `/generate-blog`
- `/generate-book`
- `/api/v1/generate-blog`
- `/api/v1/generate-book`

**Excluded Paths (no rate limiting):**
- `/` (root)
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`

### Response Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706140800
```

### Error Response

```json
HTTP 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

---

## 2. User Tier Rate Limiter (Subscription-based)

**File:** `app/middleware/rate_limit.py`

### Tier Limits

| Tier | Per-Minute | Per-Hour |
|------|-----------|----------|
| FREE | 10 | 100 |
| STARTER | 30 | 500 |
| PRO | 60 | 2,000 |
| BUSINESS | 120 | 10,000 |

### Storage Backends

**Redis (Distributed):**
- Used when `REDIS_URL` is configured
- Supports multi-instance deployments
- Uses sorted sets with timestamp scores
- Automatic key expiration

**In-Memory (Single Instance):**
- Default when Redis unavailable
- Sliding window log algorithm
- Thread-safe implementation
- Automatic cleanup every 60 seconds

### Configuration

```bash
# Redis for distributed deployments
REDIS_URL=redis://localhost:6379/0

# Redis authentication (if required)
REDIS_URL=redis://:password@redis-host:6379/0
```

### Error Response

```json
HTTP 429 Too Many Requests
{
  "success": false,
  "error": "Rate limit exceeded. Maximum 10 requests per minute.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "limit": 10,
  "remaining": 0,
  "reset_at": 1706140800,
  "retry_after": 45,
  "window": "minute",
  "tier": "free",
  "upgrade_url": "/pricing"
}
```

---

## 3. LLM API Rate Limiter

**File:** `src/text_generation/rate_limiter.py`

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_RATE_LIMIT_ENABLED` | `true` | Enable/disable LLM rate limiting |
| `LLM_RATE_LIMIT_PER_MINUTE` | `60` | API calls per minute |
| `LLM_RATE_LIMIT_MAX_QUEUE` | `100` | Max queued requests |
| `LLM_RATE_LIMIT_MAX_WAIT` | `60.0` | Max wait time (seconds) |

### Operation Types

Different limits can apply by operation type:

| Operation | Description | Default Rate |
|-----------|-------------|--------------|
| `analysis` | Voice analysis, scoring | Shared |
| `generation` | Content generation | Shared |
| `training` | Voice fingerprint training | Shared |
| `default` | All other operations | Shared |

### Algorithm

Uses **token bucket algorithm**:
- Tokens refill at configured rate
- Requests consume tokens
- If no tokens available, request is queued
- Queue has max size and max wait time

---

## 4. Usage Quotas (Daily/Monthly Limits)

**File:** `src/usage/quota_service.py`

### Tier Limits

| Tier | Monthly | Daily | Price |
|------|---------|-------|-------|
| FREE | 5 | 2 | $0 |
| STARTER | 50 | 10 | $19/mo |
| PRO | 200 | 50 | $49/mo |
| BUSINESS | 1,000 | unlimited | $149/mo |

### Storage

**Primary:** Supabase (when configured)
- `user_quotas` table - tier and billing period
- `usage_records` table - individual events

**Fallback:** File-based
- `./data/usage/` directory
- JSON files per user

### Quota Check Flow

```python
# Automatic via dependency injection
@router.post("/generate-blog")
async def generate(
    request: Request,
    user_id: str = Depends(require_quota)  # Checks quota
):
    # If we get here, quota is available
    pass
```

---

## Production Tuning Guide

### Development Environment

```bash
# Disable all rate limiting for testing
RATE_LIMIT_ENABLED=false
LLM_RATE_LIMIT_ENABLED=false
```

### Low-Traffic Production

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=30
RATE_LIMIT_GENERATION=5
LLM_RATE_LIMIT_PER_MINUTE=20
```

### Medium-Traffic Production

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=60
RATE_LIMIT_GENERATION=10
LLM_RATE_LIMIT_PER_MINUTE=60
REDIS_URL=redis://localhost:6379/0
```

### High-Traffic Production

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=100
RATE_LIMIT_GENERATION=20
LLM_RATE_LIMIT_PER_MINUTE=100
LLM_RATE_LIMIT_MAX_QUEUE=500
REDIS_URL=redis://redis-cluster:6379/0
```

---

## Monitoring Rate Limits

### Health Check

```bash
curl http://localhost:8000/health | jq
```

### Statistics Endpoint

```bash
# If implemented
curl http://localhost:8000/stats | jq
```

### Key Metrics to Monitor

| Metric | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|
| 429 responses/min | > 10 | > 100 |
| Queue depth (LLM) | > 50 | > 90 |
| Redis latency | > 10ms | > 100ms |
| Memory usage (in-memory) | > 500MB | > 1GB |

### Redis Monitoring

```bash
# Check memory usage
redis-cli INFO memory

# Check key count
redis-cli DBSIZE

# Monitor rate limit keys
redis-cli KEYS "rate_limit:*" | wc -l
```

---

## Troubleshooting

### "Rate limit exceeded" in Development

**Cause:** Rate limiting enabled in dev environment

**Solution:**
```bash
RATE_LIMIT_ENABLED=false
```

### Users Hitting Limits Too Quickly

**Cause:** Limits too restrictive for use case

**Solutions:**
1. Increase tier limits in `tier_limits` table
2. Adjust per-tier rate limits in code
3. Upgrade user to higher tier

### Redis Connection Failures

**Cause:** Redis unavailable or misconfigured

**Behavior:** Automatic fallback to in-memory storage

**Solution:**
1. Check Redis connectivity: `redis-cli ping`
2. Verify `REDIS_URL` format
3. Check authentication credentials

### High Memory Usage

**Cause:** Too many tracked IPs/users in memory

**Solution:**
1. Reduce `max_tracked_ips` setting (default: 100,000)
2. Deploy Redis for distributed storage
3. Reduce sliding window size

### LLM Requests Timing Out

**Cause:** Queue full or max wait exceeded

**Solutions:**
1. Increase `LLM_RATE_LIMIT_MAX_QUEUE`
2. Increase `LLM_RATE_LIMIT_PER_MINUTE`
3. Reduce `LLM_RATE_LIMIT_MAX_WAIT` to fail faster

---

## API Reference

### Rate Limit Headers

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining in window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |
| `Retry-After` | Seconds until retry allowed (on 429) |

### Error Codes

| Code | Description |
|------|-------------|
| `RATE_LIMIT_EXCEEDED` | Per-minute or per-hour limit hit |
| `QUOTA_EXCEEDED` | Daily or monthly quota exhausted |
| `LLM_RATE_LIMIT` | LLM API rate limit hit |

---

## Security Considerations

### IP Spoofing Protection

The rate limiter extracts client IP from:
1. `X-Forwarded-For` header (first IP)
2. `X-Real-IP` header
3. Direct connection IP

**Warning:** Configure your reverse proxy to set these headers correctly.

### DoS Prevention

- `max_tracked_ips` limits memory usage (default: 100,000)
- Automatic cleanup of expired entries
- Connection limits at load balancer recommended

### API Key Rate Limiting

User tier limits are tied to API keys:
- API key identifies user
- User's subscription tier determines limits
- Stolen keys are automatically rate-limited to tier

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment
- [MONITORING.md](./MONITORING.md) - Error tracking and alerting
- [DATABASE.md](./DATABASE.md) - Schema including `tier_limits` table
