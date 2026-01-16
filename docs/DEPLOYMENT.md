# Deployment Guide

This guide covers deploying Blog AI to production environments.

## Prerequisites

- Docker and Docker Compose (recommended)
- Or: Python 3.12+ and Node.js 18+
- OpenAI API key (required)
- Domain name and SSL certificate (for production)

## Quick Start with Docker

The fastest way to deploy is using Docker Compose:

```bash
# Clone and configure
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI
cp .env.example .env

# Edit .env with production values
# IMPORTANT: Set DEV_MODE=false for production
nano .env

# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f
```

## Production Configuration

### Required Environment Variables

```bash
# API Keys (required)
OPENAI_API_KEY=sk-your-key-here

# Security (CRITICAL for production)
DEV_MODE=false

# CORS - set to your actual domain
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=60
RATE_LIMIT_GENERATION=10

# Data Storage
CONVERSATION_STORAGE_DIR=/app/data/conversations
```

### Security Checklist

- [ ] `DEV_MODE=false` (enforces API key authentication)
- [ ] Rate limiting enabled
- [ ] CORS origins restricted to your domain
- [ ] HTTPS enabled (via reverse proxy)
- [ ] API keys stored securely (not in code)
- [ ] Logs don't contain sensitive data

## Deployment Options

### Option 1: Docker Compose (Recommended)

Best for small to medium deployments.

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  blog-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEV_MODE=false
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    volumes:
      - blog-ai-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  blog-ai-data:
```

### Option 2: Manual Deployment

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

### Option 3: Cloud Platforms

#### Vercel (Frontend)

```bash
cd frontend
vercel
```

#### Railway/Render (Backend)

Use the provided Dockerfile or connect your GitHub repo.

## Reverse Proxy Setup (Nginx)

For HTTPS and load balancing:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Check

The API provides a health check endpoint:

```bash
curl https://api.yourdomain.com/health
# {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

### Logging

Logs are output to stdout. Use your container orchestrator's log aggregation or redirect to a file:

```bash
docker-compose logs -f blog-ai > /var/log/blog-ai.log 2>&1
```

### Metrics

Consider adding:
- Prometheus metrics endpoint
- Request latency tracking
- Error rate monitoring
- LLM API cost tracking

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```yaml
# docker-compose.scale.yml
services:
  blog-ai:
    deploy:
      replicas: 3
```

### Caching

Add Redis for:
- Session storage
- Rate limiting (distributed)
- Response caching

### Database

For larger deployments, migrate conversation storage to:
- PostgreSQL (structured data)
- MongoDB (document storage)
- Redis (fast access)

## Backup

Backup the data directory regularly:

```bash
# Backup conversations
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf backup-20240115.tar.gz
```

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

## Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```
