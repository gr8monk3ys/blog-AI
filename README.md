# Blog AI

Blog AI is a monorepo for an AI-assisted content product with three app surfaces:

- `apps/web`: Next.js web app
- `apps/api`: FastAPI backend
- `apps/extension`: browser extension

The current product wedge is not “all-purpose AI writing.” It is brand-consistent, SEO-focused content production for founders, consultants, and lean marketing teams.

## Current Status

- Frontend lint, typecheck, and production build pass locally
- Backend smoke, blocking, and full test suites pass locally
- Public web routes render without Clerk
- Protected product routes require Clerk in production
- Monetization and durable user workflows still require real staging infrastructure:
  - `DATABASE_URL`
  - Clerk keys
  - Stripe keys
  - at least one valid LLM API key

## Repo Layout

```text
blog-AI/
├── apps/
│   ├── api/         FastAPI backend
│   ├── extension/   Browser extension
│   └── web/         Next.js app
├── db/              SQL migrations
├── docs/            Active operational and technical docs
├── scripts/         Utility scripts
├── Dockerfile*      Container build files
└── package.json     Workspace shell for web scripts
```

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.12+
- at least one LLM API key

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd /workspaces/blog-AI
cp .env.example .env
```

At minimum, set:

```bash
OPENAI_API_KEY=...
ENVIRONMENT=development
```

Then start the API:

```bash
cd apps/api
python server.py
```

### Frontend

```bash
cd /workspaces/blog-AI
npm install
cp .env.local.example apps/web/.env.local
```

For local development with the backend above, set:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

Then start the web app:

```bash
npm run dev
```

## Validation

Run these before merging:

```bash
npm run lint
npm run type-check
npm run test:run
npm run test:api:smoke
```

For release-readiness:

```bash
npm run test:api:blocking
npm run test:api:full
npm run build
npm audit
```

## Staging / Production Reality

This repo is not “just market it” ready without real infrastructure.

Before paid-user rollout, you need:

- Clerk configured for auth
- Neon/Postgres configured for durable storage
- Stripe test mode configured for checkout and portal flows
- valid LLM provider credentials for real output generation

Use these docs next:

- [Deployment Overview](./docs/DEPLOYMENT.md)
- [Vercel + Railway + Neon Guide](./docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
- [Environment Variables](./docs/ENVIRONMENT.md)
- [Staging Checklist](./docs/STAGING_CHECKLIST.md)
- [Repo Operations](./docs/REPO_OPERATIONS.md)

## Notes

- `Business` should stay off the public sales path until team/billing/admin workflows are fully proven.
- Local development can run with reduced infrastructure, but database-backed and billing-backed features will degrade or stay unavailable.

## License

GPL-3.0. See [LICENSE](./LICENSE).
