# Monitoring and Alerting Guide

This document provides comprehensive guidance for monitoring the Blog AI application in production, including error tracking, alerting rules, and on-call procedures.

## Table of Contents

1. [Overview](#overview)
2. [Sentry Integration](#sentry-integration)
3. [Health Check Endpoints](#health-check-endpoints)
4. [Alerting Rules](#alerting-rules)
5. [Key Metrics](#key-metrics)
6. [On-Call Procedures](#on-call-procedures)
7. [Runbooks](#runbooks)

---

## Overview

Blog AI uses a multi-layered monitoring approach:

| Layer | Tool | Purpose |
|-------|------|---------|
| Error Tracking | Sentry | Exception capture, performance monitoring, session replay |
| Health Checks | FastAPI endpoints | Service availability, dependency status |
| Logging | Structured JSON logs | Request tracing, debugging |
| Metrics | Custom endpoints | Cache stats, usage tracking |

### Architecture Diagram

```
                    +-----------------+
                    |   Load Balancer |
                    |  (Health Checks)|
                    +--------+--------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+           +--------v--------+
     |   Backend API   |           |   Frontend      |
     |   (FastAPI)     |           |   (Next.js)     |
     +--------+--------+           +--------+--------+
              |                             |
              +-------------+---------------+
                            |
                    +-------v-------+
                    |    Sentry     |
                    | Error Tracking|
                    +---------------+
```

---

## Sentry Integration

### Configuration

Sentry is configured via environment variables:

```bash
# Required
SENTRY_DSN=https://xxxxx@o123456.ingest.sentry.io/123456

# Recommended
SENTRY_ENVIRONMENT=production  # or staging, development
SENTRY_RELEASE=blog-ai@1.0.0  # Matches git tag/version

# Performance Tuning
SENTRY_TRACES_SAMPLE_RATE=0.1   # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1 # 10% of profiled transactions

# Instance Identification
SERVER_NAME=blog-ai-api-prod-1
```

### Backend Integration

The backend (`server.py`) initializes Sentry with:

- **FastAPI and Starlette integrations** for automatic request instrumentation
- **Breadcrumb filtering** to remove sensitive data (API keys, passwords, tokens)
- **PII protection** (`send_default_pii=False`)
- **Stack traces** attached to all exceptions
- **Release tracking** for deployment correlation

### Frontend Integration

Three Sentry configuration files handle different runtime contexts:

| File | Runtime | Purpose |
|------|---------|---------|
| `sentry.client.config.ts` | Browser | Client-side errors, session replay |
| `sentry.server.config.ts` | Node.js | Server components, API routes |
| `sentry.edge.config.ts` | Edge Runtime | Middleware, edge functions |

**Privacy Features:**
- Session replay masks all text and blocks media
- IP addresses and emails are stripped from events
- Authorization headers and cookies are filtered

### Error Context

Errors include the following context for debugging:

| Context | Description | Privacy |
|---------|-------------|---------|
| `request_id` | Unique ID for request correlation | Safe |
| `user_id` | Anonymized user identifier | No PII |
| `environment` | production/staging/development | Safe |
| `release` | Application version | Safe |
| `error_reference` | Short ID for support tickets | Safe |

### Sensitive Data Filtering

The following patterns are automatically filtered:

```python
SENSITIVE_PATTERNS = [
    r"api[_-]?key", r"secret", r"password", r"token",
    r"auth", r"credential", r"bearer", r"session", r"cookie",
    r"postgres://", r"mysql://", r"mongodb://", r"redis://",
]
```

---

## Health Check Endpoints

### Primary Health Check

**Endpoint:** `GET /health`

Returns overall system health for load balancer integration.

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "blog-ai@1.0.0",
  "environment": "production",
  "services": {
    "database": { "status": "up", "latency_ms": 12.5 },
    "stripe": { "status": "up", "mode": "live" },
    "sentry": { "status": "up" },
    "redis": { "status": "up", "latency_ms": 1.2 }
  }
}
```

**Status Values:**
- `healthy` - All critical services operational
- `degraded` - Non-critical services down, core functionality available

### Service-Specific Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health/db` | Database connectivity and latency |
| `GET /health/stripe` | Payment system status and mode |
| `GET /health/sentry` | Error tracking configuration |
| `GET /health/redis` | Cache connectivity and version |
| `GET /health/cache` | In-memory cache statistics |

### Load Balancer Configuration

Recommended health check settings:

```yaml
health_check:
  path: /health
  interval: 30s
  timeout: 10s
  healthy_threshold: 2
  unhealthy_threshold: 3
  matcher: 200
```

---

## Alerting Rules

### Critical Alerts (PagerDuty/Opsgenie)

These alerts require immediate response:

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| High Error Rate | 5xx errors / total requests | > 5% for 5 min | Page on-call |
| Database Down | `/health/db` returns down | 3 consecutive checks | Page on-call |
| High Latency P99 | 99th percentile response time | > 5s for 10 min | Page on-call |
| LLM Provider Failure | External service errors | > 10 in 5 min | Page on-call |

### Warning Alerts (Slack/Email)

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| Elevated Error Rate | 5xx errors / total requests | > 1% for 15 min | Notify channel |
| Cache Miss Rate | Cache hits / total requests | < 80% for 30 min | Notify channel |
| Quota Approaching | User quota usage | > 80% | Email user |
| Rate Limit Hits | 429 responses | > 100 in 5 min | Notify channel |

### Sentry Alert Rules

Configure in Sentry Dashboard:

```yaml
# Critical Error Alert
- name: Critical Backend Errors
  conditions:
    - event.type == error
    - event.level == fatal OR event.level == error
    - tags.environment == production
  filters:
    - event.count > 10 in 5m
  actions:
    - send_notification: pagerduty

# Performance Alert
- name: Slow Transactions
  conditions:
    - event.type == transaction
    - transaction.duration > 5000ms
  filters:
    - event.count > 50 in 15m
  actions:
    - send_notification: slack
```

---

## Key Metrics

### RED Method (Rate, Errors, Duration)

| Metric | Description | Target |
|--------|-------------|--------|
| Request Rate | Requests per second | Baseline +/- 20% |
| Error Rate | % of 5xx responses | < 0.1% |
| Duration P50 | Median response time | < 200ms |
| Duration P95 | 95th percentile | < 1s |
| Duration P99 | 99th percentile | < 3s |

### Business Metrics

| Metric | Description | Monitor For |
|--------|-------------|-------------|
| Blog Generations | Successful blog posts created | Sudden drops |
| Book Generations | Successful books created | Sudden drops |
| Active Users | Unique users per hour | Unusual patterns |
| API Key Usage | Requests per API key | Abuse detection |

### Infrastructure Metrics

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Usage | > 70% | > 85% |
| DB Connections | > 80% pool | > 95% pool |

---

## On-Call Procedures

### Escalation Matrix

| Severity | Response Time | Escalation |
|----------|--------------|------------|
| P1 (Critical) | 15 minutes | Immediate page |
| P2 (High) | 1 hour | Slack + email |
| P3 (Medium) | 4 hours | Email only |
| P4 (Low) | Next business day | Ticket |

### On-Call Checklist

When paged:

1. **Acknowledge** the alert within 5 minutes
2. **Assess** severity using health endpoints
3. **Communicate** status in #incidents channel
4. **Mitigate** following runbooks below
5. **Document** in incident postmortem

### Communication Templates

**Initial Response:**
```
INCIDENT: [Brief Description]
STATUS: Investigating
IMPACT: [User-facing impact]
ETA: Assessing, update in 15 min
```

**Resolution:**
```
INCIDENT: [Brief Description]
STATUS: Resolved
ROOT CAUSE: [Brief explanation]
DURATION: [Start time] - [End time]
POSTMORTEM: [Link to doc]
```

---

## Runbooks

### Database Connection Failure

**Symptoms:**
- `/health` returns `degraded`
- `/health/db` shows `connected: false`
- Errors with `DATABASE_ERROR` code in logs

**Steps:**
1. Check Neon status dashboard for outages
2. Verify `DATABASE_URL` / `DATABASE_URL_DIRECT` are set
3. Check connection pool exhaustion in logs
4. Restart affected pods if pool is stuck
5. Escalate to Neon support if issue persists

**Rollback:** Not applicable (external service)

### High Error Rate

**Symptoms:**
- Error rate > 5% in Sentry
- Multiple error types in short time

**Steps:**
1. Check recent deployments in Sentry releases
2. Identify error patterns (specific endpoint? user?)
3. Check external service status (OpenAI, Anthropic, Stripe)
4. If deployment-related, rollback:
   ```bash
   # Vercel rollback
   vercel rollback

   # Or revert to previous commit
   git revert HEAD
   git push origin main
   ```
5. If external service issue, enable circuit breaker

### LLM Provider Outage

**Symptoms:**
- `OPENAI_ERROR`, `ANTHROPIC_ERROR`, or `GEMINI_ERROR` in Sentry
- Generation endpoints returning 502

**Steps:**
1. Check provider status pages:
   - OpenAI: https://status.openai.com
   - Anthropic: https://status.anthropic.com
   - Google: https://status.cloud.google.com
2. Switch to backup provider if available:
   ```bash
   # Temporarily prioritize different provider
   OPENAI_API_KEY=   # Unset to fallback
   ```
3. Enable rate limit backoff
4. Communicate to users about degraded service

### High Latency

**Symptoms:**
- P99 latency > 5s
- Timeout errors in logs

**Steps:**
1. Check for slow database queries in logs
2. Review cache hit rates at `/health/cache`
3. Check LLM response times in Sentry transactions
4. Scale up if CPU/memory constrained
5. Enable aggressive caching for repeated requests

### Memory Pressure

**Symptoms:**
- OOM kills in container logs
- Increasing memory usage trend

**Steps:**
1. Check for memory leaks in recent deployments
2. Review cache sizes at `/health/cache`
3. Force cache cleanup:
   ```bash
   curl -X POST /health/cache/cleanup
   ```
4. Restart affected pods
5. Scale horizontally if needed

---

## Testing Monitoring

### Verify Sentry Integration

```bash
# Trigger test error (non-production only)
curl http://localhost:8000/debug-sentry
```

### Verify Health Checks

```bash
# All services
curl http://localhost:8000/health | jq

# Specific services
curl http://localhost:8000/health/db | jq
curl http://localhost:8000/health/stripe | jq
curl http://localhost:8000/health/sentry | jq
curl http://localhost:8000/health/redis | jq
curl http://localhost:8000/health/cache | jq
```

### Simulate Failure Scenarios

```bash
# Test database failure (development only)
# Temporarily unset DATABASE_URL

# Test high latency
# Add artificial delay in LLM calls

# Test rate limiting
for i in {1..100}; do curl http://localhost:8000/generate-blog; done
```

---

## Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call Engineer | PagerDuty rotation | Auto-escalates after 30 min |
| Engineering Lead | Slack @eng-lead | P1 incidents |
| Infrastructure | Slack #infra | Platform issues |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0.0 | Initial documentation |
