# Blog AI Production Deployment Checklist

This document provides a comprehensive checklist for deploying the Blog AI SaaS application to production.

---

## Table of Contents

1. [Pre-deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Deployment Steps](#deployment-steps)
4. [Post-deployment Verification](#post-deployment-verification)
5. [Monitoring Setup](#monitoring-setup)
6. [Scaling Considerations](#scaling-considerations)
7. [Runbooks](#runbooks)

---

## Pre-deployment Checklist

### Environment Variables

Before deploying, ensure all required environment variables are configured.

#### Backend Environment Variables (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models (primary provider) | `sk-...` |
| `ENVIRONMENT` | Environment name (affects security defaults) | `production` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `https://yourdomain.com` |

#### Backend Environment Variables (Recommended for Production)

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side) | `eyJ...` |
| `STRIPE_SECRET_KEY` | Stripe secret API key | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |
| `STRIPE_PRICE_ID_STARTER` | Stripe price ID for Starter tier | `price_...` |
| `STRIPE_PRICE_ID_PRO` | Stripe price ID for Pro tier | `price_...` |
| `STRIPE_PRICE_ID_BUSINESS` | Stripe price ID for Business tier | `price_...` |
| `SENTRY_DSN` | Sentry DSN for error tracking | `https://xxx@xxx.ingest.sentry.io/xxx` |
| `SENTRY_ENVIRONMENT` | Sentry environment name | `production` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |

#### Backend Environment Variables (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `SERP_API_KEY` | SERP API key for web research | - |
| `OPENAI_MODEL` | Override default OpenAI model | `gpt-4` |
| `HTTPS_REDIRECT_ENABLED` | Enable HTTPS redirect | `true` in production |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_GENERAL` | General endpoint rate limit/min | `60` |
| `RATE_LIMIT_GENERATION` | Generation endpoint rate limit/min | `10` |
| `LLM_RATE_LIMIT_PER_MINUTE` | LLM API calls per minute | `60` |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance sampling rate | `0.1` |
| `UVICORN_WORKERS` | Number of Uvicorn workers | `2` |

#### Frontend Environment Variables (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `wss://api.yourdomain.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJ...` |

#### Frontend Environment Variables (Recommended)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_live_...` |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN for frontend | `https://xxx@xxx.ingest.sentry.io/xxx` |

### Database Migrations

The following migrations must be applied in order:

```bash
# List of migrations (apply in order)
supabase/migrations/001_create_generated_content.sql
supabase/migrations/002_create_tool_usage.sql
supabase/migrations/003_create_conversations.sql
supabase/migrations/004_add_favorites.sql
supabase/migrations/004_create_templates.sql
supabase/migrations/005_create_brand_profiles.sql
supabase/migrations/006_enhance_brand_voice_training.sql
supabase/migrations/007_usage_quotas.sql
supabase/migrations/008_stripe_integration.sql
```

### External Service Setup

#### Supabase Setup
- [ ] Create Supabase project at https://supabase.com
- [ ] Note the project URL and API keys
- [ ] Enable Row Level Security (RLS) on all tables
- [ ] Configure authentication providers (if using Supabase Auth)
- [ ] Run all database migrations
- [ ] Verify `tier_limits` table is populated with tier data

#### Stripe Setup
- [ ] Create Stripe account at https://stripe.com
- [ ] Create Products and Prices for each tier:
  - Starter tier (monthly recurring)
  - Pro tier (monthly recurring)
  - Business tier (monthly recurring)
- [ ] Configure webhook endpoint: `https://api.yourdomain.com/webhooks/stripe`
- [ ] Enable webhook events:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
- [ ] Note webhook signing secret

#### Sentry Setup
- [ ] Create Sentry project at https://sentry.io
- [ ] Create two projects: one for backend (Python), one for frontend (Next.js)
- [ ] Note DSN for each project
- [ ] Configure release tracking
- [ ] Set up alert rules

### SSL/TLS Certificate Requirements

- [ ] Valid SSL certificate for your domain
- [ ] Certificate covers both `yourdomain.com` and `api.yourdomain.com`
- [ ] Auto-renewal configured (Let's Encrypt recommended)
- [ ] TLS 1.2 or higher enforced
- [ ] HSTS enabled (`SECURITY_HSTS_ENABLED=true`)

---

## Infrastructure Requirements

### Minimum Server Specifications

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| CPU | 2 vCPU | 4 vCPU | More CPUs improve concurrent request handling |
| RAM | 2 GB | 4 GB | LLM responses can be memory-intensive |
| Storage | 20 GB SSD | 50 GB SSD | Logs and temporary files |
| Network | 100 Mbps | 1 Gbps | WebSocket connections benefit from bandwidth |

### Redis Requirements

| Specification | Value |
|--------------|-------|
| Version | 7.x (Alpine image recommended) |
| Memory | 256 MB minimum, 512 MB recommended |
| Persistence | AOF enabled (`appendonly yes`) |
| Max Memory Policy | `allkeys-lru` |
| Connection | Internal network only (do not expose port 6379) |

Docker configuration (from `docker-compose.prod.yml`):
```yaml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --appendonly yes
    --maxmemory 200mb
    --maxmemory-policy allkeys-lru
    --save 60 1
    --loglevel warning
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 256M
```

### Database Requirements (Supabase)

| Specification | Value |
|--------------|-------|
| Plan | Pro plan recommended for production |
| Database | PostgreSQL 15+ |
| Connection Pooling | Enabled (PgBouncer) |
| Max Connections | 60+ (depends on plan) |
| Point-in-Time Recovery | Enabled |
| Daily Backups | Enabled |

### CDN Recommendations for Frontend

| Provider | Configuration |
|----------|--------------|
| Vercel | Recommended for Next.js (automatic CDN) |
| Cloudflare | Cache static assets, enable minification |
| AWS CloudFront | Configure origin to frontend server |

Recommended CDN settings:
- Cache static assets (`/_next/static/*`) for 1 year
- Cache images for 1 month
- Purge cache on deploy
- Enable Brotli/Gzip compression
- Enable HTTP/2 and HTTP/3

---

## Deployment Steps

### Option 1: Docker Deployment (Recommended)

#### Build and Deploy

```bash
# Set build metadata
export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
export GIT_SHA=$(git rev-parse HEAD)
export VERSION=$(git describe --tags --always)

# Build production image
docker-compose -f docker-compose.prod.yml build

# Deploy with rolling update
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f blog-ai

# Check container status
docker-compose -f docker-compose.prod.yml ps
```

#### Single Container Deployment

```bash
# Build image
docker build -f Dockerfile.prod -t blog-ai:latest \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg GIT_SHA=$(git rev-parse HEAD) \
  --build-arg VERSION=1.0.0 .

# Run container
docker run -d \
  --name blog-ai \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env.production \
  --restart unless-stopped \
  blog-ai:latest
```

### Option 2: Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-ai
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
      - name: blog-ai
        image: blog-ai:latest
        ports:
        - containerPort: 8000
        - containerPort: 3000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        envFrom:
        - secretRef:
            name: blog-ai-secrets
```

### Option 3: Manual Deployment

For more control over the deployment:

```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Frontend (separate server or static hosting)
cd frontend
npm install
npm run build
# Serve with nginx or deploy to Vercel/Netlify
```

### Option 4: Cloud Platforms

#### Vercel (Frontend)

```bash
cd frontend
vercel --prod
```

#### Railway/Render (Backend)

Use the provided Dockerfile or connect your GitHub repo.

### Database Migration Commands

```bash
# Using Supabase CLI
supabase db push

# Or apply migrations manually via psql
psql $DATABASE_URL -f supabase/migrations/001_create_generated_content.sql
psql $DATABASE_URL -f supabase/migrations/002_create_tool_usage.sql
# ... continue for all migrations

# Verify migrations
psql $DATABASE_URL -c "SELECT * FROM tier_limits;"
```

### Health Check Verification

```bash
# Basic health check
curl -s http://localhost:8000/health | jq .

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T00:00:00.000000",
#   "version": "1.0.0",
#   "services": {
#     "database": { "status": "up", "latency_ms": 5.2 },
#     "stripe": { "status": "up", "mode": "live" },
#     "sentry": { "status": "up" }
#   }
# }

# Detailed health checks
curl -s http://localhost:8000/health/db | jq .
curl -s http://localhost:8000/health/stripe | jq .
curl -s http://localhost:8000/health/sentry | jq .
curl -s http://localhost:8000/health/cache | jq .
```

### Reverse Proxy Setup (Nginx)

For HTTPS and load balancing:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running LLM requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
    }
}
```

### Rollback Procedures

#### Docker Rollback

```bash
# List available images
docker images blog-ai

# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Deploy previous version
export VERSION=previous-version-tag
docker-compose -f docker-compose.prod.yml up -d

# Or using specific image
docker run -d \
  --name blog-ai \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env.production \
  blog-ai:previous-version
```

#### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/blog-ai

# Rollback to previous revision
kubectl rollout undo deployment/blog-ai

# Rollback to specific revision
kubectl rollout undo deployment/blog-ai --to-revision=2

# Check rollout status
kubectl rollout status deployment/blog-ai
```

#### Database Rollback

For database migrations, maintain rollback scripts:
```bash
# Create rollback scripts for each migration
# Example: supabase/migrations/008_stripe_integration_rollback.sql

# Execute rollback
psql $DATABASE_URL -f supabase/migrations/008_stripe_integration_rollback.sql
```

---

## Post-deployment Verification

### Health Endpoint Checks

Run this verification script after deployment:

```bash
#!/bin/bash
# post-deploy-verify.sh

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "=== Post-Deployment Verification ==="

# 1. Backend health check
echo -n "Backend health: "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$HEALTH" == "200" ]; then
  echo "PASS"
else
  echo "FAIL (HTTP $HEALTH)"
  exit 1
fi

# 2. Database connectivity
echo -n "Database: "
DB_STATUS=$(curl -s "$API_URL/health/db" | jq -r '.database.connected')
if [ "$DB_STATUS" == "true" ]; then
  echo "PASS"
else
  echo "FAIL"
  exit 1
fi

# 3. Stripe connectivity
echo -n "Stripe: "
STRIPE_STATUS=$(curl -s "$API_URL/health/stripe" | jq -r '.stripe.connected')
if [ "$STRIPE_STATUS" == "true" ]; then
  echo "PASS"
else
  echo "WARNING (payments may be degraded)"
fi

# 4. Sentry connectivity
echo -n "Sentry: "
SENTRY_STATUS=$(curl -s "$API_URL/health/sentry" | jq -r '.sentry.active')
if [ "$SENTRY_STATUS" == "true" ]; then
  echo "PASS"
else
  echo "WARNING (error tracking disabled)"
fi

# 5. Frontend health
echo -n "Frontend: "
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$FRONTEND" == "200" ]; then
  echo "PASS"
else
  echo "FAIL (HTTP $FRONTEND)"
  exit 1
fi

# 6. API docs accessible
echo -n "API Docs: "
DOCS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$DOCS" == "200" ]; then
  echo "PASS"
else
  echo "FAIL"
fi

echo "=== Verification Complete ==="
```

### Stripe Webhook Test

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to local endpoint for testing
stripe listen --forward-to http://localhost:8000/webhooks/stripe

# In another terminal, trigger a test webhook
stripe trigger checkout.session.completed

# Verify webhook was received
curl -s http://localhost:8000/health/stripe | jq '.stripe.webhook_configured'
```

### API Key Generation Test

```bash
# Test API key generation endpoint (if applicable)
curl -X POST "$API_URL/api-keys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name": "test-key", "permissions": ["read"]}'
```

### Content Generation Smoke Test

```bash
# Test blog generation endpoint
curl -X POST "$API_URL/generate-blog" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "topic": "Test Blog Post",
    "keywords": ["test", "deployment"],
    "sections": 2,
    "include_research": false
  }' | jq '.title, .status'

# Expected: Should return a title and "success" status

# Test with WebSocket for real-time updates
wscat -c "wss://api.yourdomain.com/ws/conversation/test-123"
```

---

## Monitoring Setup

### Sentry Configuration

#### Backend (Python/FastAPI)

The backend automatically initializes Sentry when `SENTRY_DSN` is configured:

```python
# Configured in server.py - no additional setup needed
# Environment variables to configure:
# - SENTRY_DSN
# - SENTRY_ENVIRONMENT=production
# - SENTRY_TRACES_SAMPLE_RATE=0.1
# - SENTRY_PROFILES_SAMPLE_RATE=0.1
# - SENTRY_RELEASE=blog-ai@1.0.0
```

#### Frontend (Next.js)

Add Sentry to frontend (if not already configured):

```bash
cd frontend
npx @sentry/wizard@latest -i nextjs
```

### Log Aggregation

#### Docker Logging

The production Docker Compose already configures JSON logging:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"
```

#### Centralized Logging Options

| Provider | Configuration |
|----------|--------------|
| Datadog | Use `docker-dd-agent` sidecar |
| CloudWatch | Configure awslogs driver |
| ELK Stack | Use Filebeat to ship logs |
| Loki | Use Promtail for log collection |

Example Datadog configuration:
```yaml
blog-ai:
  labels:
    com.datadoghq.ad.logs: '[{"source": "python", "service": "blog-ai-api"}]'
```

### Uptime Monitoring

Configure uptime monitoring for these endpoints:

| Endpoint | Check Interval | Alert Threshold |
|----------|----------------|-----------------|
| `GET /health` | 30 seconds | 3 failures |
| `GET /health/db` | 60 seconds | 2 failures |
| `GET /` (frontend) | 60 seconds | 3 failures |

Recommended providers:
- UptimeRobot (free tier available)
- Pingdom
- Better Uptime
- Datadog Synthetics

### Alert Thresholds

Configure alerts for these metrics:

| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate (5xx) | > 1% | > 5% |
| Response Time (p95) | > 2s | > 5s |
| Response Time (p99) | > 5s | > 10s |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 75% | > 90% |
| Disk Usage | > 70% | > 85% |
| Redis Memory | > 80% | > 95% |
| Database Connections | > 70% | > 90% |

#### Sentry Alert Rules

```yaml
# Example Sentry alert configuration
alerts:
  - name: "High Error Rate"
    conditions:
      - type: event_frequency
        interval: 1h
        value: 100
    actions:
      - type: slack
        channel: "#alerts"

  - name: "Critical Error"
    conditions:
      - type: first_seen_event
        level: error
        tags:
          severity: critical
    actions:
      - type: pagerduty
```

---

## Scaling Considerations

### Horizontal Scaling with Redis

Redis enables horizontal scaling by providing:
- Session/state sharing across instances
- Job queue for async content generation
- Rate limiting state synchronization

```yaml
# Scale to multiple instances
docker-compose -f docker-compose.prod.yml up -d --scale blog-ai=3
```

Kubernetes HPA example:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: blog-ai-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: blog-ai
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Connection Pooling

Supabase provides PgBouncer for connection pooling. Configure your connection:

```python
# Use the pooler connection string for high-traffic scenarios
# Connection string format with pooling:
# postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Recommended pool settings:
- Pool mode: Transaction
- Pool size: 15-25 per instance
- Max client connections: 100

### Rate Limit Adjustments

Adjust rate limits based on tier and traffic:

```bash
# Environment variable overrides
RATE_LIMIT_GENERAL=100     # General endpoints: 100/min
RATE_LIMIT_GENERATION=20   # Generation endpoints: 20/min
LLM_RATE_LIMIT_PER_MINUTE=120  # LLM API calls: 120/min
```

For enterprise deployments, consider:
- Per-API-key rate limits
- Tiered rate limits based on subscription
- Burst allowance for authenticated users

### Worker Scaling

Adjust Uvicorn workers based on CPU cores:

```bash
# General formula: (2 * CPU cores) + 1
# For a 4-core server:
UVICORN_WORKERS=9

# For memory-constrained environments:
UVICORN_WORKERS=2
```

---

## Runbooks

### Runbook: High Error Rate

**Symptoms**: Error rate > 5%, Sentry alerts firing

**Steps**:
1. Check Sentry for error details
2. Review recent deployments
3. Check database connectivity: `curl /health/db`
4. Check external service status (OpenAI, Stripe)
5. Review logs: `docker-compose logs --tail=100 blog-ai`
6. If caused by recent deployment, rollback immediately

### Runbook: High Latency

**Symptoms**: p95 response time > 5s

**Steps**:
1. Check database latency: `curl /health/db | jq '.database.latency_ms'`
2. Check Redis connectivity
3. Review LLM API response times
4. Check for resource exhaustion (CPU, memory)
5. Scale horizontally if under high load
6. Review and optimize slow queries

### Runbook: Database Connection Issues

**Symptoms**: Database health check failing

**Steps**:
1. Verify Supabase project status
2. Check connection pool exhaustion
3. Verify environment variables are correct
4. Test connection manually: `psql $DATABASE_URL -c "SELECT 1"`
5. Check Supabase dashboard for connection limits
6. Restart application if connections are stale

### Runbook: Stripe Webhook Failures

**Symptoms**: Payments not processing, subscription status not updating

**Steps**:
1. Check Stripe dashboard for webhook delivery status
2. Verify webhook secret is correct
3. Check endpoint is accessible: `curl -I /webhooks/stripe`
4. Review webhook logs in Stripe dashboard
5. Resend failed webhooks from Stripe dashboard
6. Check application logs for webhook processing errors

### Runbook: Out of Memory

**Symptoms**: Container killed, OOMKilled events

**Steps**:
1. Check memory usage: `docker stats blog-ai`
2. Review for memory leaks in application
3. Increase container memory limits
4. Reduce worker count if needed
5. Enable swap as last resort
6. Consider adding memory-based HPA

---

## Security Checklist

Before going live, verify:

- [ ] `ENVIRONMENT=production` is set
- [ ] `DEV_MODE=false` is set
- [ ] `HTTPS_REDIRECT_ENABLED=true` is set
- [ ] CORS origins are restricted to specific domains
- [ ] All secrets are in environment variables (not in code)
- [ ] Debug endpoints (`/debug-sentry`, `/config-status`) are disabled
- [ ] Rate limiting is enabled
- [ ] HSTS is enabled
- [ ] CSP headers are configured
- [ ] Database uses SSL connections
- [ ] API keys are hashed before storage
- [ ] Stripe uses live mode keys (not test keys)
- [ ] Sentry does not capture PII

---

## Troubleshooting

### Common Issues

1. **"Missing API key" error**
   - Ensure `DEV_MODE=false` and provide valid API key via header

2. **Rate limit exceeded**
   - Wait for the rate limit window to reset
   - Increase limits if needed for your use case

3. **CORS errors**
   - Add your domain to `ALLOWED_ORIGINS`

4. **WebSocket disconnections**
   - Check nginx/proxy WebSocket configuration
   - Ensure proper upgrade headers

### Debug Mode

For debugging production issues:

```bash
LOG_LEVEL=DEBUG docker-compose up
```

---

## Backup and Recovery

### Backup Procedures

```bash
# Backup conversations (if using local storage)
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup Redis data
docker exec blog-ai-redis redis-cli BGSAVE

# For Supabase, use built-in backup features
# or export via pg_dump if self-hosted
```

### Recovery Procedures

```bash
# Restore from backup
tar -xzf backup-20240115.tar.gz

# Restore Redis
docker cp dump.rdb blog-ai-redis:/data/dump.rdb
docker restart blog-ai-redis
```

---

## Updates and Maintenance

### Rolling Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart with zero downtime
docker-compose -f docker-compose.prod.yml up -d --build --no-deps blog-ai
```

### Scheduled Maintenance

For planned maintenance:
1. Enable maintenance mode (if implemented)
2. Complete in-flight requests
3. Perform updates
4. Verify health checks pass
5. Disable maintenance mode

---

## Contact Information

For deployment issues:
- **On-call**: Check PagerDuty/Opsgenie rotation
- **Slack**: #blog-ai-incidents
- **Escalation**: Contact engineering lead

---

*Last updated: 2024*
*Version: 1.0.0*
