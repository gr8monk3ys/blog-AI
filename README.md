# Blog AI

An AI-powered content generation platform for creating high-quality blog posts and books. Built with a **Next.js** frontend and a **FastAPI** (Python) backend, Blog AI supports multiple LLM providers (OpenAI, Anthropic, Google Gemini), web research, SEO optimization, and publishing integrations.

[![CI](https://github.com/gr8monk3ys/blog-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/gr8monk3ys/blog-AI/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

---

## Features

- **Blog Post Generation** -- Create high-quality blog posts on any topic with customizable tone, research depth, proofreading, and humanization
- **Book Generation** -- Generate complete books with chapters, sections, and topics
- **Multi-Provider LLM Support** -- Switch between OpenAI (GPT-4), Anthropic (Claude), and Google Gemini
- **Web Research** -- Optionally enrich content with live web research via SERP, Tavily, or Metaphor APIs
- **SEO Optimization** -- Automatic meta descriptions, keyword targeting, and content scoring
- **Content Editing** -- Edit generated content with an intuitive in-browser editor
- **Conversation History** -- Track and revisit your interactions with the AI
- **Export / Download** -- Export content in multiple formats
- **Brand Profiles** -- Maintain consistent voice across generated content
- **Content Templates** -- Save and reuse generation configurations
- **Social Media Scheduling** -- Schedule and auto-post to Twitter/X and LinkedIn
- **Subscription Billing** -- Stripe-powered tiered pricing (Starter, Pro, Business)
- **Chrome Extension** -- Generate content directly from your browser
- **Authentication** -- Clerk-based auth with SSO support (SAML, OIDC)
- **Fact Checking & Plagiarism Detection** -- Verify content accuracy and originality
- **Image Generation** -- AI-generated images via DALL-E 3 or Stability AI
- **Webhooks** -- Zapier-compatible webhooks for workflow automation

---

## Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| [Next.js](https://nextjs.org/) 16 | React framework (App Router) |
| [React](https://react.dev/) 18 | UI library |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first styling |
| [Framer Motion](https://www.framer.com/motion/) | Animations |
| [Headless UI](https://headlessui.com/) | Accessible UI primitives |
| [Clerk](https://clerk.com/) | Authentication |
| [Neon](https://neon.tech/) (via `@neondatabase/serverless`) | Serverless Postgres |
| [Sentry](https://sentry.io/) | Error tracking |
| [Vitest](https://vitest.dev/) + [Playwright](https://playwright.dev/) | Unit and E2E testing |

### Backend

| Technology | Purpose |
|---|---|
| [Python](https://www.python.org/) 3.12 | Runtime |
| [FastAPI](https://fastapi.tiangolo.com/) | API framework |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |
| [OpenAI SDK](https://platform.openai.com/docs) | GPT model integration |
| [Anthropic SDK](https://docs.anthropic.com/) | Claude model integration |
| [Google Generative AI](https://ai.google.dev/) | Gemini model integration |
| [Pydantic](https://docs.pydantic.dev/) | Data validation and settings |
| [asyncpg](https://magicstack.github.io/asyncpg/) | Async Postgres driver |
| [Stripe](https://stripe.com/) | Payment processing |
| [Redis](https://redis.io/) | Caching and job queues |
| [Sentry](https://sentry.io/) | Error tracking |
| [Poetry](https://python-poetry.org/) | Dependency management |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 -- App Router)                         │
│  Port 3000                                                   │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ ContentGenerator │  │ BookGenerator │  │ ContentViewer  │  │
│  └────────┬────────┘  └──────┬───────┘  └───────┬────────┘  │
│           │                  │                   │            │
│           └──────────────────┼───────────────────┘            │
│                     REST / WebSocket                          │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────┐
│  Backend (FastAPI)                                            │
│  Port 8000                                                   │
│                                                              │
│  server.py                                                   │
│      ↓                                                       │
│  src/blog/make_blog.py  |  src/book/make_book.py             │
│      ↓                                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Pipeline stages:                                       │ │
│  │  1. research/web_researcher.py (optional)               │ │
│  │  2. planning/content_outline.py                         │ │
│  │  3. blog_sections/* generators                          │ │
│  │  4. seo/meta_description.py                             │ │
│  │  5. post_processing/{proofreader, humanizer}.py         │ │
│  └─────────────────────────────────────────────────────────┘ │
│      ↓                                                       │
│  src/text_generation/core.py  (LLM abstraction)              │
│      ↓                                                       │
│  OpenAI  /  Anthropic  /  Gemini                             │
└──────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate-blog` | Generate a blog post |
| `POST` | `/generate-book` | Generate a book |
| `POST` | `/edit-section` | Edit a section of content |
| `POST` | `/save-book` | Save changes to a book |
| `POST` | `/download-book` | Download a book in various formats |
| `GET` | `/conversations/{id}` | Get conversation history |
| `WS` | `/ws/conversation/{id}` | Real-time updates via WebSocket |
| `GET` | `/health` | Health check |

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** (or [Bun](https://bun.sh/))
- **Git**
- At least one LLM API key (OpenAI, Anthropic, or Gemini)

### 1. Clone the Repository

```bash
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies (choose one)
pip install -r requirements.txt
# or
poetry install

# Copy the environment file and add your API keys
cd ..
cp .env.example .env
# Edit .env -- at minimum set OPENAI_API_KEY

# Start the backend server
cd backend
python server.py
# Backend runs at http://localhost:8000
```

### 3. Frontend Setup

```bash
# From the project root
npm install        # or: bun install

# Copy the frontend environment file
cp .env.local.example .env.local
# Edit .env.local -- set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the development server
npm run dev        # or: bun dev
# Frontend runs at http://localhost:3000
```

### 4. Open the App

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

---

## Docker

### Development (Single Container)

The default `docker-compose.yml` runs both the backend and frontend in a single container:

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

The backend API is available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

> **Note:** Mount your `.env` file before starting -- the container reads it as a volume.

### Production (with Redis)

The production compose file (`docker-compose.prod.yml`) adds Redis for caching/job queues and includes resource limits, health checks, and logging configuration:

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop
docker-compose -f docker-compose.prod.yml down
```

### Backend-Only Docker Image

A standalone backend Dockerfile is available at `Dockerfile.backend`:

```bash
docker build -f Dockerfile.backend -t blog-ai-backend .
docker run -p 8000:8000 --env-file .env blog-ai-backend
```

---

## Environment Variables

The project uses three environment files:

| File | Purpose | Template |
|---|---|---|
| `.env` | Backend configuration (API keys, server settings, database, payments) | `.env.example` |
| `.env.local` | Frontend local development (API URL, Clerk keys, database) | `.env.local.example` |
| `.env.production.local` | Frontend production build | `.env.production.example` |

### Required Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (primary LLM provider) |
| `NEXT_PUBLIC_API_URL` | Backend API URL for the frontend (e.g., `http://localhost:8000`) |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL (e.g., `ws://localhost:8000`) |

### Optional / Feature-Specific Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative LLM provider) |
| `GEMINI_API_KEY` | Google Gemini API key (alternative LLM provider) |
| `SERP_API_KEY` | SERP API key for web research |
| `TAVILY_API_KEY` | Tavily API key for web research |
| `DATABASE_URL` | Neon / Postgres connection string |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk authentication (frontend) |
| `CLERK_SECRET_KEY` | Clerk authentication (server-side) |
| `STRIPE_SECRET_KEY` | Stripe payments |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification |
| `REDIS_URL` | Redis connection for caching/queues |
| `SENTRY_DSN` | Sentry error tracking |
| `STABILITY_API_KEY` | Stability AI for image generation |

See `.env.example` for the complete list with detailed descriptions.

---

## CLI Usage

The backend includes a CLI for generating content without the web UI:

```bash
# Generate a blog post
python -m src.blog.make_blog "Topic" --keywords "a,b" --research --proofread --humanize

# Generate a book
python -m src.book.make_book "Title" --chapters 5 --sections 3 --research

# Planning tools
python -m src.planning.content_calendar "Niche" --timeframe month
python -m src.planning.competitor_analysis "Niche" --competitors "A,B"
python -m src.planning.topic_clusters "Niche" --clusters 3
python -m src.planning.content_outline "Topic" --sections 5
```

---

## Testing

### Frontend

```bash
# Unit tests (Vitest)
npm test
npm run test:run              # Single run (no watch)
npm run test:coverage         # With coverage report

# E2E tests (Playwright)
npm run test:e2e
npm run test:e2e:headed       # Run with visible browser
npm run test:e2e:ui           # Interactive Playwright UI
```

### Backend

```bash
cd backend

# Run all tests
python run_tests.py
# or
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_blog.py -v
```

### Linting and Type Checking

```bash
# Frontend
npm run lint
npm run type-check

# Backend
black src/ tests/ server.py
isort src/ tests/ server.py
mypy src/ server.py --ignore-missing-imports
```

---

## Project Structure

```
blog-AI/
├── app/                        # Next.js App Router pages
│   ├── api/                    #   Route handlers
│   ├── blog/                   #   Blog CMS pages
│   ├── pricing/                #   Pricing page
│   ├── templates/              #   Template management
│   ├── analytics/              #   Analytics dashboard
│   ├── brand/                  #   Brand profiles
│   ├── team/                   #   Team management
│   ├── sign-in/ & sign-up/    #   Auth pages (Clerk)
│   └── page.tsx                #   Home page
├── components/                 # React components
│   ├── ContentGenerator.tsx    #   Blog generation UI
│   ├── BookGenerator.tsx       #   Book generation UI
│   ├── ContentViewer.tsx       #   Content display
│   ├── BookEditor.tsx          #   Book editing
│   ├── brand/                  #   Brand profile components
│   ├── analytics/              #   Analytics widgets
│   ├── tools/                  #   AI tools UI
│   └── ui/                     #   Shared UI primitives
├── lib/                        # Frontend utilities
├── hooks/                      # Custom React hooks
├── __tests__/                  # Frontend unit tests
├── e2e/                        # Playwright E2E tests
├── backend/                    # Python backend
│   ├── server.py               #   FastAPI entry point
│   ├── src/                    #   Source modules
│   │   ├── blog/               #     Blog generation pipeline
│   │   ├── book/               #     Book generation pipeline
│   │   ├── text_generation/    #     LLM abstraction layer
│   │   ├── research/           #     Web research
│   │   ├── planning/           #     Content planning
│   │   ├── seo/                #     SEO optimization
│   │   ├── post_processing/    #     Proofreading & humanization
│   │   ├── integrations/       #     WordPress, GitHub, Medium
│   │   ├── payments/           #     Stripe billing
│   │   ├── social/             #     Social media scheduling
│   │   ├── knowledge/          #     RAG / Knowledge base
│   │   ├── images/             #     AI image generation
│   │   ├── fact_checking/      #     Fact verification
│   │   ├── organizations/      #     Multi-tenant orgs
│   │   ├── types/              #     Pydantic models
│   │   └── ...
│   ├── app/                    #   FastAPI route modules
│   ├── tests/                  #   Backend tests
│   ├── pyproject.toml          #   Poetry config
│   └── requirements.txt        #   Pip requirements
├── chrome-extension/           # Chrome extension for in-browser generation
├── docs/                       # Architecture and deployment docs
├── docker-compose.yml          # Dev Docker config
├── docker-compose.prod.yml     # Production Docker config (with Redis)
├── Dockerfile                  # Full-stack Docker image
├── Dockerfile.backend          # Backend-only Docker image
└── Dockerfile.prod             # Production Docker image
```

---

## Deployment

Blog AI is designed for a split deployment:

- **Frontend** -- Deployed to [Vercel](https://vercel.com) automatically on push to `main`
- **Backend** -- Dockerized and deployed to any container host (Railway, Fly.io, self-hosted VM, etc.) via GitHub Container Registry (`ghcr.io`)
- **Database** -- [Neon](https://neon.tech/) serverless Postgres

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for the full deployment guide, including GitHub Secrets configuration and CI/CD pipeline details.

---

## Screenshots

<!-- Add screenshots of the application here -->
<!-- Example:
![Home Page](docs/screenshots/home.png)
![Content Generator](docs/screenshots/generator.png)
![Book Editor](docs/screenshots/book-editor.png)
-->

_Screenshots coming soon._

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines on:

- Development environment setup
- Code style (Black, isort, ESLint)
- Testing requirements
- Pull request process and conventional commit format

Please also review the [Code of Conduct](./CODE_OF_CONDUCT.md).

---

## License

This project is licensed under the [GNU General Public License v3.0](./LICENSE).

---

## Acknowledgements

Built by [Lorenzo Scaturchio](https://github.com/gr8monk3ys).
