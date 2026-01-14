---
description: Generate deployment configurations and workflows
model: claude-opus-4-5
---

Generate deployment configuration for the specified platform and environment.

## Deployment Specification

$ARGUMENTS

## Supported Platforms

### Vercel (Next.js Optimized)
- Zero-config deployments for Next.js
- Automatic previews for pull requests
- Edge Network deployment
- Environment variables management

### Netlify
- Static sites and serverless functions
- Deploy previews
- Forms and identity services
- Build plugins

### AWS (EC2, ECS, Lambda)
- Full infrastructure control
- Scalable containerized deployments
- Serverless functions

### Docker + Docker Compose
- Containerized applications
- Multi-service orchestration
- Local and production parity

### GitHub Actions CI/CD
- Automated testing and deployment
- Multi-platform support
- Secrets management

## Deployment Patterns

### Vercel Deployment

**vercel.json**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "DATABASE_URL": "@database-url",
    "API_KEY": "@api-key"
  },
  "regions": ["iad1"],
  "framework": "nextjs"
}
```

**GitHub Actions (.github/workflows/deploy.yml)**
```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### Docker Deployment

**Dockerfile**
```dockerfile
# Multi-stage build for Next.js
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package*.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Environment variables must be present at build time
ARG DATABASE_URL
ARG NEXT_PUBLIC_API_URL

ENV DATABASE_URL=$DATABASE_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# Production image, copy all files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        DATABASE_URL: ${DATABASE_URL}
        NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
```

**.dockerignore**
```
node_modules
.next
.git
.env
.env.local
.DS_Store
*.log
coverage
.vscode
```

### AWS ECS Deployment

**buildspec.yml** (AWS CodeBuild)
```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  build:
    commands:
      - echo Build started on `date`
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"%s","imageUri":"%s"}]' $CONTAINER_NAME $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG > imagedefinitions.json

artifacts:
  files: imagedefinitions.json
```

### GitHub Actions for Multiple Environments

```yaml
name: Deploy

on:
  push:
    branches: [main, staging, develop]
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
      - run: npm ci
      - run: npm run lint
      - run: npm test

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Staging
        run: |
          # Deploy commands for staging
          echo "Deploying to staging..."

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Production
        run: |
          # Deploy commands for production
          echo "Deploying to production..."
```

## Best Practices

### Environment Variables
```bash
# .env.example (commit this)
DATABASE_URL=postgresql://user:pass@localhost:5432/db
API_KEY=your_api_key_here
NEXT_PUBLIC_API_URL=https://api.example.com

# .env (DO NOT commit this)
# Contains actual secrets
```

### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Build succeeds locally
- [ ] No console errors
- [ ] Dependencies up to date
- [ ] Security vulnerabilities checked (`npm audit`)
- [ ] Performance tested
- [ ] Monitoring/logging configured
- [ ] Rollback plan ready

### Zero-Downtime Deployment
```yaml
# Blue-Green Deployment
steps:
  - Deploy to staging slot
  - Run smoke tests
  - Swap staging with production
  - Monitor for errors
  - Rollback if needed
```

### Database Migrations
```bash
# Run migrations before deploying code
npm run migrate:production

# Rollback strategy
npm run migrate:rollback
```

### Health Checks
```typescript
// pages/api/health.ts
export default function handler(req, res) {
  // Check database connection
  // Check external services
  // Return 200 if healthy, 503 if not
  res.status(200).json({ status: 'healthy' })
}
```

### Monitoring & Logging
```typescript
// Add to production config
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
})
```

## Platform-Specific Commands

### Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Environment variables
vercel env add DATABASE_URL production
vercel env ls
```

### Docker Commands
```bash
# Build image
docker build -t myapp:latest .

# Run locally
docker run -p 3000:3000 myapp:latest

# Compose up
docker-compose up -d

# View logs
docker-compose logs -f app
```

### AWS CLI
```bash
# Update ECS service
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --force-new-deployment

# View logs
aws logs tail /aws/ecs/my-service --follow
```

## Rollback Procedures

### Vercel
```bash
# List deployments
vercel ls

# Promote previous deployment
vercel promote [deployment-url]
```

### Docker
```bash
# Rollback to previous image
docker tag myapp:previous myapp:latest
docker-compose up -d
```

### GitHub Actions
```yaml
# Manual rollback workflow
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true
```

## Output Format

Generate:
1. **Deployment Configuration** - Platform-specific config files
2. **CI/CD Pipeline** - Automated deployment workflow
3. **Environment Setup** - Environment variables template
4. **Health Checks** - Monitoring endpoints
5. **Rollback Script** - Emergency rollback procedure
6. **Documentation** - Deployment runbook

## Security Considerations

- ✅ Never commit secrets (.env files)
- ✅ Use secrets management (GitHub Secrets, AWS Secrets Manager)
- ✅ Enable HTTPS/TLS
- ✅ Configure CORS properly
- ✅ Set up rate limiting
- ✅ Enable security headers
- ✅ Regular security audits
- ✅ Automated dependency updates

Generate production-ready deployment configurations with proper CI/CD pipelines, monitoring, and rollback procedures.
