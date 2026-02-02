# Blog AI Deployment Guide

This comprehensive guide covers deploying the Blog AI application to various environments, from single-server Docker deployments to production-grade Kubernetes clusters.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment Options](#cloud-deployment-options)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Database Setup](#database-setup)
6. [Production Checklist](#production-checklist)
7. [Scaling Considerations](#scaling-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Infrastructure

#### Minimum Server Specifications

| Component | Development | Production (Minimum) | Production (Recommended) |
|-----------|-------------|----------------------|--------------------------|
| CPU | 1 vCPU | 2 vCPU | 4+ vCPU |
| RAM | 2 GB | 4 GB | 8 GB |
| Storage | 10 GB SSD | 40 GB SSD | 100 GB SSD |
| Network | 10 Mbps | 100 Mbps | 1 Gbps |

#### Software Requirements

| Software | Minimum Version | Notes |
|----------|-----------------|-------|
| Docker | 24.0+ | Required for containerized deployment |
| Docker Compose | 2.20+ | Required for multi-container orchestration |
| Node.js | 18.x LTS | For frontend build (20.x recommended) |
| Python | 3.11+ | Backend runtime (3.12 recommended) |
| PostgreSQL | 15+ | Via Supabase or self-hosted |
| Redis | 7.x | Optional but recommended for production |
| nginx | 1.24+ | Recommended reverse proxy |

#### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y \
    curl \
    git \
    build-essential \
    python3-dev \
    libpq-dev \
    nginx \
    certbot \
    python3-certbot-nginx

# RHEL/CentOS/Amazon Linux
sudo yum install -y \
    curl \
    git \
    gcc \
    python3-devel \
    postgresql-devel \
    nginx \
    certbot \
    python3-certbot-nginx
```

### Required Accounts and API Keys

#### Essential (At Least One LLM Provider Required)

| Service | Purpose | Signup URL |
|---------|---------|------------|
| OpenAI | GPT-4 content generation (primary) | https://platform.openai.com/signup |
| Anthropic | Claude models (alternative) | https://console.anthropic.com/ |
| Google AI | Gemini models (alternative) | https://makersuite.google.com/app/apikey |

#### Recommended for Production

| Service | Purpose | Signup URL |
|---------|---------|------------|
| Supabase | Database and authentication | https://supabase.com/ |
| Stripe | Payment processing | https://dashboard.stripe.com/register |
| Sentry | Error tracking and monitoring | https://sentry.io/signup/ |

#### Optional (Enhanced Features)

| Service | Purpose | Signup URL |
|---------|---------|------------|
| SERP API | Web search research | https://serpapi.com/ |
| Tavily | AI-powered research | https://tavily.com/ |
| Stability AI | Image generation | https://platform.stability.ai/ |

### Environment Variables Reference

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

**Critical production variables:**

```bash
# Required - at least one LLM provider
OPENAI_API_KEY=sk-...

# Production settings
ENVIRONMENT=production
DEV_MODE=false
HTTPS_REDIRECT_ENABLED=true

# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=60
RATE_LIMIT_GENERATION=10

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Error tracking
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
```

---

## Docker Deployment

### Single Server Deployment

#### Quick Start

```bash
# Clone the repository
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Build and start
docker-compose up -d --build

# Verify deployment
curl http://localhost:8000/health
```

#### Production Docker Compose

Use the production configuration for better resource management:

```bash
# Set build metadata
export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
export GIT_SHA=$(git rev-parse HEAD)
export VERSION=$(git describe --tags --always 2>/dev/null || echo "1.0.0")

# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f blog-ai

# Check status
docker-compose -f docker-compose.prod.yml ps
```

#### Docker Compose Architecture

```
+------------------+     +------------------+
|   blog-ai        |     |   redis          |
|   container      |---->|   container      |
|                  |     |                  |
|  Backend: 8000   |     |  Port: 6379      |
|  Frontend: 3000  |     |  (internal only) |
+------------------+     +------------------+
         |
         v
+------------------+
|   nginx          |
|   (host)         |
|                  |
|  HTTP: 80        |
|  HTTPS: 443      |
+------------------+
         |
         v
    [Internet]
```

### Environment Configuration

#### Development vs Production

| Variable | Development | Production |
|----------|-------------|------------|
| `ENVIRONMENT` | `development` | `production` |
| `DEV_MODE` | `true` | `false` |
| `HTTPS_REDIRECT_ENABLED` | `false` | `true` |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `UVICORN_WORKERS` | `1` | `2 * CPU + 1` |
| `SENTRY_TRACES_SAMPLE_RATE` | `1.0` | `0.1` |

#### Docker Environment File

Create `.env.production`:

```bash
# Application
ENVIRONMENT=production
VERSION=1.0.0

# Workers (adjust based on CPU cores)
UVICORN_WORKERS=4

# Security
ALLOWED_ORIGINS=https://yourdomain.com
HTTPS_REDIRECT_ENABLED=true
RATE_LIMIT_ENABLED=true

# Redis
REDIS_URL=redis://redis:6379/0

# LLM Provider
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
```

### SSL/TLS Setup with Nginx Reverse Proxy

#### Install Certbot and Obtain Certificates

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/blog-ai`:

```nginx
# Rate limiting configuration
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

# Upstream definitions
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Main application (frontend)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;

    # Rate limiting
    limit_req zone=general_limit burst=50 nodelay;

    # Frontend proxy
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static assets caching
    location /_next/static {
        proxy_pass http://frontend;
        proxy_cache_valid 200 365d;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
}

# API server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration (same certificates)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API rate limiting
    limit_req zone=api_limit burst=20 nodelay;

    # Request size limit
    client_max_body_size 10M;

    # API proxy
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;

        # Timeouts for LLM requests (can take 60+ seconds)
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://backend/health;
        limit_req off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/blog-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Health Checks and Monitoring

#### Docker Health Check

The production Dockerfile includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

#### External Health Check Script

Create `scripts/health-check.sh`:

```bash
#!/bin/bash
# Health check script for Blog AI

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

check_endpoint() {
    local url=$1
    local name=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")

    if [ "$status" == "200" ]; then
        echo "[PASS] $name"
        return 0
    else
        echo "[FAIL] $name (HTTP $status)"
        return 1
    fi
}

echo "=== Blog AI Health Check ==="
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

FAILED=0

check_endpoint "$API_URL/health" "Backend Health" || FAILED=1
check_endpoint "$API_URL/health/db" "Database Connection" || FAILED=1
check_endpoint "$API_URL/docs" "API Documentation" || FAILED=1
check_endpoint "$FRONTEND_URL" "Frontend Application" || FAILED=1

echo ""
if [ $FAILED -eq 0 ]; then
    echo "=== All checks passed ==="
    exit 0
else
    echo "=== Some checks failed ==="
    exit 1
fi
```

#### Monitoring with Docker Stats

```bash
# Real-time resource monitoring
docker stats blog-ai-app blog-ai-redis

# Container logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

---

## Cloud Deployment Options

### Architecture Overview

```mermaid
flowchart TB
    subgraph Internet
        Users[Users/Clients]
    end

    subgraph CDN["CDN Layer"]
        CF[CloudFlare/CloudFront]
    end

    subgraph LoadBalancer["Load Balancer"]
        LB[ALB/Cloud Load Balancer]
    end

    subgraph AppTier["Application Tier"]
        App1[Blog AI Instance 1]
        App2[Blog AI Instance 2]
        AppN[Blog AI Instance N]
    end

    subgraph CacheTier["Cache Tier"]
        Redis[(Redis Cluster)]
    end

    subgraph DataTier["Data Tier"]
        Supabase[(Supabase/PostgreSQL)]
    end

    subgraph External["External Services"]
        OpenAI[OpenAI API]
        Stripe[Stripe API]
        Sentry[Sentry]
    end

    Users --> CF
    CF --> LB
    LB --> App1 & App2 & AppN
    App1 & App2 & AppN --> Redis
    App1 & App2 & AppN --> Supabase
    App1 & App2 & AppN --> OpenAI
    App1 & App2 & AppN --> Stripe
    App1 & App2 & AppN --> Sentry
```

### AWS Deployment

#### Option A: ECS with Fargate (Serverless Containers)

**Architecture Diagram:**

```
                            +-----------------+
                            |   Route 53      |
                            |   (DNS)         |
                            +-----------------+
                                    |
                            +-----------------+
                            |  CloudFront     |
                            |  (CDN)          |
                            +-----------------+
                                    |
                            +-----------------+
                            |  Application    |
                            |  Load Balancer  |
                            +-----------------+
                                    |
                    +---------------+---------------+
                    |               |               |
            +-------v-------+ +-----v-----+ +------v------+
            | ECS Fargate   | | Fargate   | | Fargate     |
            | Task 1        | | Task 2    | | Task N      |
            | (Blog AI)     | | (Blog AI) | | (Blog AI)   |
            +---------------+ +-----------+ +-------------+
                    |               |               |
                    +---------------+---------------+
                            |               |
                    +-------v-------+ +-----v-----+
                    | ElastiCache   | | RDS/      |
                    | (Redis)       | | Supabase  |
                    +---------------+ +-----------+
```

**ECS Task Definition (`task-definition.json`):**

```json
{
  "family": "blog-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "blog-ai",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/blog-ai:latest",
      "portMappings": [
        { "containerPort": 8000, "protocol": "tcp" },
        { "containerPort": 3000, "protocol": "tcp" }
      ],
      "environment": [
        { "name": "ENVIRONMENT", "value": "production" },
        { "name": "UVICORN_WORKERS", "value": "2" }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:blog-ai/openai-key"
        },
        {
          "name": "SUPABASE_SERVICE_ROLE_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:blog-ai/supabase-key"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/blog-ai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deployment Commands:**

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -f Dockerfile.prod -t blog-ai:latest .
docker tag blog-ai:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-ai:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-ai:latest

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create/update service
aws ecs update-service \
  --cluster blog-ai-cluster \
  --service blog-ai-service \
  --task-definition blog-ai \
  --desired-count 2 \
  --force-new-deployment
```

#### Option B: EC2 with Auto Scaling

**User Data Script for EC2:**

```bash
#!/bin/bash
# EC2 User Data for Blog AI

# Install Docker
yum update -y
amazon-linux-extras install docker -y
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone application
cd /opt
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI

# Get secrets from Parameter Store
aws ssm get-parameter --name "/blog-ai/env" --with-decryption --query "Parameter.Value" --output text > .env

# Start application
docker-compose -f docker-compose.prod.yml up -d
```

**Auto Scaling Policy:**

```json
{
  "AutoScalingGroupName": "blog-ai-asg",
  "PolicyName": "cpu-target-tracking",
  "PolicyType": "TargetTrackingScaling",
  "TargetTrackingConfiguration": {
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 70.0,
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }
}
```

### Google Cloud Run

**Architecture Diagram:**

```
                    +-------------------+
                    |  Cloud DNS        |
                    +-------------------+
                            |
                    +-------------------+
                    |  Cloud CDN        |
                    +-------------------+
                            |
                    +-------------------+
                    |  Cloud Load       |
                    |  Balancing        |
                    +-------------------+
                            |
            +---------------+---------------+
            |               |               |
    +-------v-------+ +-----v-----+ +------v------+
    | Cloud Run     | | Cloud Run | | Cloud Run   |
    | Instance 1    | | Instance 2| | Instance N  |
    +---------------+ +-----------+ +-------------+
            |               |               |
            +---------------+---------------+
                    |               |
            +-------v-------+ +-----v-----+
            | Memorystore   | | Cloud SQL |
            | (Redis)       | | /Supabase |
            +---------------+ +-----------+
```

**Cloud Run Deployment:**

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/PROJECT_ID/blog-ai:latest .

# Deploy to Cloud Run
gcloud run deploy blog-ai \
  --image gcr.io/PROJECT_ID/blog-ai:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 2 \
  --memory 2Gi \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 300 \
  --set-env-vars="ENVIRONMENT=production,UVICORN_WORKERS=2" \
  --set-secrets="OPENAI_API_KEY=openai-key:latest,SUPABASE_SERVICE_ROLE_KEY=supabase-key:latest"
```

**Cloud Run Configuration (`service.yaml`):**

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: blog-ai
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: gcr.io/PROJECT_ID/blog-ai:latest
          ports:
            - containerPort: 8000
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
          env:
            - name: ENVIRONMENT
              value: production
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openai-key
                  key: latest
          startupProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            periodSeconds: 30
```

### DigitalOcean App Platform

**Architecture Diagram:**

```
                    +-------------------+
                    |  DigitalOcean     |
                    |  DNS              |
                    +-------------------+
                            |
                    +-------------------+
                    |  App Platform     |
                    |  (Managed)        |
                    +-------------------+
                            |
            +---------------+---------------+
            |                               |
    +-------v-------+               +-------v-------+
    | Blog AI       |               | Redis         |
    | Service       |               | (Managed)     |
    | (Auto-scaled) |               |               |
    +---------------+               +---------------+
            |
    +-------v-------+
    | Managed       |
    | PostgreSQL    |
    | /Supabase     |
    +---------------+
```

**App Specification (`app.yaml`):**

```yaml
name: blog-ai
region: nyc
services:
  - name: blog-ai-api
    dockerfile_path: Dockerfile.prod
    source_dir: /
    http_port: 8000
    instance_count: 2
    instance_size_slug: professional-xs

    # Scaling configuration
    autoscaling:
      min_instance_count: 1
      max_instance_count: 5
      metrics:
        - type: CPU
          percent: 70

    # Health checks
    health_check:
      http_path: /health
      initial_delay_seconds: 30
      period_seconds: 30
      timeout_seconds: 10
      success_threshold: 1
      failure_threshold: 3

    # Environment variables
    envs:
      - key: ENVIRONMENT
        value: production
      - key: UVICORN_WORKERS
        value: "2"
      - key: OPENAI_API_KEY
        type: SECRET
        value: ${OPENAI_API_KEY}
      - key: SUPABASE_URL
        value: ${SUPABASE_URL}
      - key: SUPABASE_SERVICE_ROLE_KEY
        type: SECRET
        value: ${SUPABASE_SERVICE_ROLE_KEY}
      - key: REDIS_URL
        value: ${redis.REDIS_URL}

    # Alerts
    alerts:
      - rule: DEPLOYMENT_FAILED
      - rule: DOMAIN_FAILED
      - rule: CPU_UTILIZATION
        value: 80
        operator: GREATER_THAN
        window: FIVE_MINUTES

databases:
  - name: redis
    engine: REDIS
    size: db-s-1vcpu-1gb
    version: "7"

# Domain configuration
domains:
  - domain: api.yourdomain.com
    type: PRIMARY
```

**Deployment:**

```bash
# Install doctl CLI
brew install doctl  # macOS
# or snap install doctl  # Linux

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec app.yaml

# Update existing app
doctl apps update APP_ID --spec app.yaml
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x (optional but recommended)

### Basic Manifests

#### Namespace

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
    app.kubernetes.io/part-of: blog-ai-system
```

#### ConfigMap

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: blog-ai-config
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
data:
  # Application settings
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  LOG_FORMAT_JSON: "true"

  # Server configuration
  BACKEND_PORT: "8000"
  FRONTEND_PORT: "3000"
  UVICORN_WORKERS: "2"

  # Rate limiting
  RATE_LIMIT_ENABLED: "true"
  RATE_LIMIT_GENERAL: "60"
  RATE_LIMIT_GENERATION: "10"

  # Security
  HTTPS_REDIRECT_ENABLED: "true"
  SECURITY_ENABLED: "true"
  SECURITY_HSTS_ENABLED: "true"

  # Model configuration
  OPENAI_MODEL: "gpt-4"
  ANTHROPIC_MODEL: "claude-3-opus-20240229"
```

#### Secret

```yaml
# kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: blog-ai-secrets
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
type: Opaque
stringData:
  # LLM API Keys
  OPENAI_API_KEY: "sk-your-openai-key"
  ANTHROPIC_API_KEY: ""
  GEMINI_API_KEY: ""

  # Database
  SUPABASE_URL: "https://xxx.supabase.co"
  SUPABASE_SERVICE_ROLE_KEY: "eyJ..."

  # Payment
  STRIPE_SECRET_KEY: "sk_live_..."
  STRIPE_WEBHOOK_SECRET: "whsec_..."

  # Monitoring
  SENTRY_DSN: "https://xxx@sentry.io/xxx"

  # Redis
  REDIS_URL: "redis://blog-ai-redis:6379/0"

  # CORS
  ALLOWED_ORIGINS: "https://yourdomain.com,https://api.yourdomain.com"
```

#### Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-ai
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
    app.kubernetes.io/component: application
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: blog-ai
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: blog-ai
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: blog-ai
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001

      containers:
        - name: blog-ai
          image: ghcr.io/gr8monk3ys/blog-ai:latest
          imagePullPolicy: Always

          ports:
            - name: backend
              containerPort: 8000
              protocol: TCP
            - name: frontend
              containerPort: 3000
              protocol: TCP

          envFrom:
            - configMapRef:
                name: blog-ai-config
            - secretRef:
                name: blog-ai-secrets

          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2Gi"

          readinessProbe:
            httpGet:
              path: /health
              port: backend
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 5
            successThreshold: 1
            failureThreshold: 3

          livenessProbe:
            httpGet:
              path: /health
              port: backend
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            successThreshold: 1
            failureThreshold: 3

          startupProbe:
            httpGet:
              path: /health
              port: backend
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 5
            failureThreshold: 30

          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false
            capabilities:
              drop:
                - ALL

      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app.kubernetes.io/name: blog-ai
                topologyKey: kubernetes.io/hostname

      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: blog-ai
```

#### Service

```yaml
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: blog-ai
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: blog-ai
  ports:
    - name: backend
      port: 8000
      targetPort: backend
      protocol: TCP
    - name: frontend
      port: 3000
      targetPort: frontend
      protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: blog-ai-backend
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
    app.kubernetes.io/component: backend
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: blog-ai
  ports:
    - name: http
      port: 80
      targetPort: backend
      protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: blog-ai-frontend
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
    app.kubernetes.io/component: frontend
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: blog-ai
  ports:
    - name: http
      port: 80
      targetPort: frontend
      protocol: TCP
```

### Ingress Configuration

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blog-ai
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    # WebSocket support
    nginx.ingress.kubernetes.io/websocket-services: "blog-ai-backend"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$request_uri"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - yourdomain.com
        - api.yourdomain.com
      secretName: blog-ai-tls
  rules:
    # Frontend
    - host: yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: blog-ai-frontend
                port:
                  number: 80
    # Backend API
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: blog-ai-backend
                port:
                  number: 80
```

### Horizontal Pod Autoscaler

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: blog-ai
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: blog-ai
  minReplicas: 2
  maxReplicas: 10
  metrics:
    # Scale based on CPU
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    # Scale based on Memory
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
        - type: Pods
          value: 1
          periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

### Redis Deployment

```yaml
# kubernetes/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-ai-redis
  namespace: blog-ai
  labels:
    app.kubernetes.io/name: blog-ai-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: blog-ai-redis
  template:
    metadata:
      labels:
        app.kubernetes.io/name: blog-ai-redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          command:
            - redis-server
            - --appendonly
            - "yes"
            - --maxmemory
            - 256mb
            - --maxmemory-policy
            - allkeys-lru
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 10
            periodSeconds: 10
          volumeMounts:
            - name: redis-data
              mountPath: /data
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: blog-ai-redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: blog-ai-redis
  namespace: blog-ai
spec:
  selector:
    app.kubernetes.io/name: blog-ai-redis
  ports:
    - port: 6379
      targetPort: 6379
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: blog-ai-redis-pvc
  namespace: blog-ai
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### Deployment Commands

```bash
# Apply all manifests
kubectl apply -f kubernetes/

# Or apply individually
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/redis.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/hpa.yaml

# Check deployment status
kubectl -n blog-ai get pods
kubectl -n blog-ai get services
kubectl -n blog-ai get ingress

# View logs
kubectl -n blog-ai logs -f deployment/blog-ai

# Scale manually
kubectl -n blog-ai scale deployment/blog-ai --replicas=5

# Rolling update
kubectl -n blog-ai set image deployment/blog-ai blog-ai=ghcr.io/gr8monk3ys/blog-ai:v1.1.0

# Rollback
kubectl -n blog-ai rollout undo deployment/blog-ai
```

---

## Database Setup

### Supabase Configuration

#### Initial Setup

1. **Create Project**
   - Go to https://supabase.com/dashboard
   - Click "New Project"
   - Choose organization, name, and region
   - Save the generated password securely

2. **Get Connection Details**
   - Navigate to Settings > API
   - Copy:
     - Project URL (`SUPABASE_URL`)
     - Anon/Public key (`SUPABASE_KEY`)
     - Service Role key (`SUPABASE_SERVICE_ROLE_KEY`)

3. **Run Migrations**

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Push migrations
supabase db push

# Or apply manually
psql "$DATABASE_URL" -f supabase/migrations/001_create_generated_content.sql
psql "$DATABASE_URL" -f supabase/migrations/002_create_tool_usage.sql
psql "$DATABASE_URL" -f supabase/migrations/003_create_conversations.sql
psql "$DATABASE_URL" -f supabase/migrations/004_add_favorites.sql
psql "$DATABASE_URL" -f supabase/migrations/004_create_templates.sql
psql "$DATABASE_URL" -f supabase/migrations/005_create_brand_profiles.sql
psql "$DATABASE_URL" -f supabase/migrations/006_enhance_brand_voice_training.sql
psql "$DATABASE_URL" -f supabase/migrations/007_usage_quotas.sql
psql "$DATABASE_URL" -f supabase/migrations/008_stripe_integration.sql
```

### Connection Pooling

#### Supabase Connection Pooler (PgBouncer)

Supabase provides built-in connection pooling via PgBouncer.

**Connection Strings:**

| Type | Port | Use Case |
|------|------|----------|
| Direct | 5432 | Migrations, admin tasks |
| Pooler (Transaction) | 6543 | Application connections |
| Pooler (Session) | 5432 | Long-running connections |

**Recommended Configuration:**

```bash
# For application use (transaction mode)
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres?pgbouncer=true

# For migrations (direct connection)
DATABASE_URL_DIRECT=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

**Python Connection Settings:**

```python
# In your application configuration
DATABASE_POOL_SIZE = 10  # Connections per worker
DATABASE_POOL_OVERFLOW = 20  # Additional connections allowed
DATABASE_POOL_TIMEOUT = 30  # Seconds to wait for connection
DATABASE_POOL_RECYCLE = 1800  # Recycle connections after 30 minutes
```

### Backup Strategy

#### Automated Backups (Supabase Pro)

Supabase Pro plan includes:
- Daily automated backups
- Point-in-Time Recovery (PITR) up to 7 days
- Cross-region backup replication

#### Manual Backup Procedures

```bash
# Export database
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Export specific tables
pg_dump "$DATABASE_URL" -t generated_content -t conversations > content_backup.sql

# Compressed backup
pg_dump "$DATABASE_URL" | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from backup
psql "$DATABASE_URL" < backup.sql
# or
gunzip -c backup.sql.gz | psql "$DATABASE_URL"
```

#### Backup Schedule Recommendation

| Backup Type | Frequency | Retention |
|-------------|-----------|-----------|
| Full database | Daily | 30 days |
| Transaction logs | Continuous | 7 days |
| Configuration | On change | 90 days |

#### Backup Verification Script

```bash
#!/bin/bash
# scripts/verify-backup.sh

BACKUP_FILE=$1
TEST_DB="blog_ai_backup_test"

# Create test database
createdb "$TEST_DB"

# Restore backup
psql "$TEST_DB" < "$BACKUP_FILE"

# Verify tables exist
TABLES=$(psql "$TEST_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLES" -gt 0 ]; then
    echo "Backup verification: SUCCESS ($TABLES tables restored)"
else
    echo "Backup verification: FAILED (no tables found)"
    exit 1
fi

# Cleanup
dropdb "$TEST_DB"
```

---

## Production Checklist

### Security Hardening Steps

#### Application Security

- [ ] `ENVIRONMENT=production` is set
- [ ] `DEV_MODE=false` is set
- [ ] Debug endpoints are disabled (`/debug-sentry`, `/config-status`)
- [ ] API documentation is access-controlled or disabled (`/docs`, `/redoc`)
- [ ] Rate limiting is enabled and configured
- [ ] Request body size limits are set
- [ ] Input validation is enabled on all endpoints

#### Network Security

- [ ] `HTTPS_REDIRECT_ENABLED=true` is set
- [ ] TLS 1.2+ is enforced
- [ ] HSTS is enabled (`SECURITY_HSTS_ENABLED=true`)
- [ ] CORS origins are restricted (`ALLOWED_ORIGINS` set to specific domains)
- [ ] Firewall rules allow only necessary ports (80, 443)
- [ ] Internal services (Redis, database) are not exposed publicly

#### Authentication and Authorization

- [ ] API keys are required for all protected endpoints
- [ ] API keys are hashed before storage
- [ ] JWT tokens have appropriate expiration
- [ ] Webhook signatures are verified (Stripe)

#### Infrastructure Security

- [ ] Containers run as non-root user
- [ ] Docker images are scanned for vulnerabilities
- [ ] Secrets are stored in secure secret management (not in code)
- [ ] SSH access uses key-based authentication only
- [ ] Regular security updates are applied

### Environment Variables to Set

#### Required for Production

```bash
# Core
ENVIRONMENT=production
DEV_MODE=false

# At least one LLM provider
OPENAI_API_KEY=sk-...

# Security
ALLOWED_ORIGINS=https://yourdomain.com
HTTPS_REDIRECT_ENABLED=true
RATE_LIMIT_ENABLED=true
```

#### Recommended for Production

```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Payments (if using subscriptions)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_STARTER=price_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_BUSINESS=price_...

# Error tracking
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Caching
REDIS_URL=redis://redis:6379/0
```

### Monitoring and Alerting Setup

#### Sentry Configuration

1. **Create Project**
   - Go to https://sentry.io
   - Create two projects: Python (backend), JavaScript/Next.js (frontend)

2. **Configure Alerts**

```yaml
# Sentry alert rules
alerts:
  - name: "High Error Rate"
    trigger: event_frequency > 100 per hour
    action: slack_notification

  - name: "Critical Error"
    trigger: level = error AND first_seen
    action: pagerduty_alert

  - name: "Slow Response Time"
    trigger: transaction_duration p95 > 5s
    action: slack_notification
```

3. **Environment Variables**

```bash
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_RELEASE=blog-ai@1.0.0
```

#### Uptime Monitoring

Configure monitoring for these endpoints:

| Endpoint | Interval | Alert After |
|----------|----------|-------------|
| `GET /health` | 30s | 3 failures |
| `GET /health/db` | 60s | 2 failures |
| `GET /` (frontend) | 60s | 3 failures |
| WebSocket connection | 120s | 2 failures |

**Recommended Services:**
- UptimeRobot (free tier available)
- Better Uptime
- Pingdom
- Datadog Synthetics

### Logging Configuration

#### Structured Logging

The application outputs JSON-formatted logs in production:

```bash
LOG_LEVEL=INFO
LOG_FORMAT_JSON=true
REQUEST_LOGGING_ENABLED=true
```

#### Log Aggregation Options

| Provider | Setup |
|----------|-------|
| Datadog | Install dd-agent, configure log collection |
| CloudWatch | Use awslogs Docker driver |
| ELK Stack | Configure Filebeat/Fluentd |
| Loki | Deploy Promtail alongside containers |

#### Docker Logging Configuration

```yaml
# docker-compose.prod.yml
services:
  blog-ai:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
        labels: "service,environment"
```

### Backup Procedures

#### What to Backup

| Data | Method | Frequency |
|------|--------|-----------|
| Database | Supabase automated + pg_dump | Daily |
| Redis data | RDB snapshots | Hourly |
| Configuration | Git + secret manager | On change |
| Logs | Log aggregation service | Continuous |

#### Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/database.sql.gz"

# Redis backup
docker exec blog-ai-redis redis-cli BGSAVE
docker cp blog-ai-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# Configuration backup (exclude secrets)
cp .env.example "$BACKUP_DIR/"
cp docker-compose.prod.yml "$BACKUP_DIR/"

# Upload to S3/GCS (optional)
# aws s3 sync "$BACKUP_DIR" "s3://your-bucket/backups/$(date +%Y%m%d)/"

echo "Backup completed: $BACKUP_DIR"
```

---

## Scaling Considerations

### When to Scale

| Metric | Scale Up Threshold | Scale Down Threshold |
|--------|-------------------|---------------------|
| CPU Utilization | > 70% for 5 min | < 30% for 15 min |
| Memory Utilization | > 80% for 5 min | < 40% for 15 min |
| Request Queue | > 100 pending | < 10 pending |
| Response Time (p95) | > 2s | < 500ms |
| Error Rate | > 5% | < 0.1% |

### Scaling Architecture

```mermaid
flowchart TB
    subgraph "Auto-Scaling Group"
        direction TB
        LB[Load Balancer]

        subgraph "Min: 2, Max: 10"
            App1[Instance 1]
            App2[Instance 2]
            AppN[Instance N...]
        end

        LB --> App1 & App2 & AppN
    end

    subgraph "Shared State"
        Redis[(Redis Cluster)]
        DB[(PostgreSQL)]
    end

    App1 & App2 & AppN --> Redis
    App1 & App2 & AppN --> DB
```

### Caching Strategies with Redis

#### Cache Configuration

```bash
# Redis environment variables
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=3600  # 1 hour default
REDIS_MAX_MEMORY=256mb
REDIS_EVICTION_POLICY=allkeys-lru
```

#### What to Cache

| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| LLM responses | 24h | On content update |
| User sessions | 1h | On logout |
| Rate limit counters | 1m | Automatic |
| API key validations | 5m | On key change |
| Template content | 1h | On template update |

#### Cache Implementation Example

```python
# Example caching pattern
import redis
import json
import hashlib

redis_client = redis.from_url(os.environ['REDIS_URL'])

def get_cached_or_generate(prompt: str, generate_fn):
    cache_key = f"llm:{hashlib.md5(prompt.encode()).hexdigest()}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Generate and cache
    result = generate_fn(prompt)
    redis_client.setex(
        cache_key,
        timedelta(hours=24),
        json.dumps(result)
    )
    return result
```

### Rate Limiting Configuration

#### Application Rate Limits

```bash
# General endpoint rate limits (per IP)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=60        # 60 requests/minute
RATE_LIMIT_GENERATION=10     # 10 generation requests/minute

# LLM API rate limits
LLM_RATE_LIMIT_ENABLED=true
LLM_RATE_LIMIT_PER_MINUTE=60
LLM_RATE_LIMIT_MAX_QUEUE=100
LLM_RATE_LIMIT_MAX_WAIT=60.0
```

#### Nginx Rate Limiting

```nginx
# Rate limit zones
limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=generation:10m rate=1r/s;

# Apply to locations
location / {
    limit_req zone=general burst=50 nodelay;
}

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /generate {
    limit_req zone=generation burst=5 nodelay;
}
```

#### Tiered Rate Limits

For SaaS deployments with subscription tiers:

| Tier | General | Generation | LLM Calls |
|------|---------|------------|-----------|
| Free | 30/min | 5/min | 100/day |
| Starter | 60/min | 15/min | 500/day |
| Pro | 120/min | 30/min | 2000/day |
| Business | 300/min | 60/min | Unlimited |

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Application fails to start

**Symptoms:** Container exits immediately, health check fails

**Solutions:**

1. Check environment variables:
```bash
docker-compose config  # Verify configuration
docker logs blog-ai-app  # Check startup logs
```

2. Verify API keys are valid:
```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. Check port availability:
```bash
netstat -tlnp | grep -E '8000|3000'
```

#### Issue: High latency/slow responses

**Symptoms:** p95 response time > 5 seconds

**Solutions:**

1. Check database latency:
```bash
curl http://localhost:8000/health/db | jq '.database.latency_ms'
```

2. Check Redis connection:
```bash
redis-cli -h localhost ping
```

3. Monitor LLM API response times:
```bash
# Check Sentry for slow transactions
# Or add timing logs to LLM calls
```

4. Scale horizontally:
```bash
docker-compose -f docker-compose.prod.yml up -d --scale blog-ai=3
```

#### Issue: Rate limit exceeded

**Symptoms:** HTTP 429 responses

**Solutions:**

1. Identify the limit being hit:
```bash
# Check response headers
curl -I http://localhost:8000/api/endpoint
# Look for: X-RateLimit-Limit, X-RateLimit-Remaining
```

2. Adjust limits if appropriate:
```bash
RATE_LIMIT_GENERAL=120
RATE_LIMIT_GENERATION=20
```

3. Implement client-side backoff

#### Issue: WebSocket disconnections

**Symptoms:** Real-time updates fail, connection drops

**Solutions:**

1. Check nginx WebSocket configuration:
```nginx
location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400s;
}
```

2. Verify load balancer settings support WebSocket

3. Check for proxy timeout settings

#### Issue: Database connection errors

**Symptoms:** "Connection refused" or "Too many connections"

**Solutions:**

1. Check database status:
```bash
psql "$DATABASE_URL" -c "SELECT 1"
```

2. Review connection pool settings:
```bash
# Reduce pool size if hitting limits
DATABASE_POOL_SIZE=5
```

3. Use connection pooler (Supabase PgBouncer):
```bash
# Use port 6543 for pooled connections
DATABASE_URL=postgresql://...@pooler.supabase.com:6543/postgres
```

#### Issue: Memory exhaustion (OOMKilled)

**Symptoms:** Container restarts, "OOMKilled" in Docker logs

**Solutions:**

1. Check memory usage:
```bash
docker stats blog-ai-app
```

2. Increase memory limits:
```yaml
deploy:
  resources:
    limits:
      memory: 4G
```

3. Reduce worker count:
```bash
UVICORN_WORKERS=2
```

4. Enable memory monitoring in Sentry

### Log Locations

| Component | Location | Command |
|-----------|----------|---------|
| Application | stdout/stderr | `docker logs blog-ai-app` |
| Nginx | /var/log/nginx/ | `tail -f /var/log/nginx/access.log` |
| System | /var/log/syslog | `journalctl -u docker` |
| Redis | Container stdout | `docker logs blog-ai-redis` |

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Overall health | `{"status": "healthy"}` |
| `GET /health/db` | Database connectivity | `{"database": {"connected": true}}` |
| `GET /health/stripe` | Stripe connection | `{"stripe": {"connected": true}}` |
| `GET /health/sentry` | Sentry status | `{"sentry": {"active": true}}` |
| `GET /health/cache` | Redis connection | `{"cache": {"connected": true}}` |

### Debug Mode

For troubleshooting production issues (use temporarily):

```bash
# Enable debug logging
LOG_LEVEL=DEBUG docker-compose -f docker-compose.prod.yml up

# Check specific component
docker exec -it blog-ai-app python -c "
import os
from src.text_generation.core import create_provider_from_env
provider = create_provider_from_env()
print(f'Provider: {type(provider).__name__}')
"
```

### Emergency Procedures

#### Rolling Back

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml down
docker tag blog-ai:previous blog-ai:latest
docker-compose -f docker-compose.prod.yml up -d

# Kubernetes
kubectl -n blog-ai rollout undo deployment/blog-ai
kubectl -n blog-ai rollout status deployment/blog-ai
```

#### Disabling Features

```bash
# Disable rate limiting temporarily
RATE_LIMIT_ENABLED=false

# Disable HTTPS redirect (for debugging)
HTTPS_REDIRECT_ENABLED=false

# Enable development mode (DANGEROUS - removes auth)
# DEV_MODE=true  # Only for local debugging
```

#### Contact and Escalation

For production incidents:
1. Check Sentry for error details
2. Review application logs
3. Consult this troubleshooting guide
4. Escalate to engineering team via incident management

---

## Appendix: Quick Reference

### Docker Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart service
docker-compose -f docker-compose.prod.yml restart blog-ai

# Stop services
docker-compose -f docker-compose.prod.yml down

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Kubernetes Commands

```bash
# Apply configuration
kubectl apply -f kubernetes/

# Check status
kubectl -n blog-ai get all

# View logs
kubectl -n blog-ai logs -f deployment/blog-ai

# Scale
kubectl -n blog-ai scale deployment/blog-ai --replicas=5

# Rollback
kubectl -n blog-ai rollout undo deployment/blog-ai
```

### Health Check Commands

```bash
# Backend health
curl -s http://localhost:8000/health | jq .

# Database check
curl -s http://localhost:8000/health/db | jq .

# Full verification
./scripts/health-check.sh
```

---

*Document Version: 2.0.0*
*Last Updated: 2026-02*
