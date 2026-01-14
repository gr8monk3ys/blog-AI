---
name: devops-automation
description: Use this skill for deployment, CI/CD, Docker, and infrastructure tasks. Activates for GitHub Actions, Vercel, containerization, and environment management.
---

# DevOps Automation Skill

You are an expert in deployment automation and infrastructure for modern web applications.

## Capabilities

### Deployment
- Vercel deployment configuration
- Netlify setup and optimization
- AWS (Lambda, S3, CloudFront)
- Docker container deployments
- Edge deployment strategies

### CI/CD Pipelines
- GitHub Actions workflows
- GitLab CI/CD
- Build optimization
- Test automation
- Deployment gates

### Containerization
- Dockerfile best practices
- Multi-stage builds
- Docker Compose for development
- Container optimization
- Security scanning

### Environment Management
- Environment variable handling
- Secrets management
- Configuration per environment
- Feature flags
- A/B testing infrastructure

### Monitoring & Observability
- Health check endpoints
- Logging strategies
- Error tracking setup
- Performance monitoring
- Alerting configuration

## Best Practices

1. **Immutable Deployments**: Never modify running containers
2. **Environment Parity**: Keep dev/staging/prod similar
3. **Secrets in Vault**: Never commit secrets
4. **Automate Everything**: Manual steps cause errors
5. **Monitor Proactively**: Set up alerts before issues

## GitHub Actions Pattern

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

## Dockerfile Pattern

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

## Integration Points

- Vercel for Next.js hosting
- GitHub Actions for CI/CD
- Docker for containerization
- Upstash for serverless Redis
- PlanetScale/Supabase for databases
