# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blog AI is an AI-driven content generation tool for creating blog posts and books. It uses a Python backend (FastAPI) with multi-provider LLM support and a Next.js frontend.

## Common Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt    # or: poetry install

# Run backend server (http://localhost:8000)
python server.py

# Run all tests
python run_tests.py
# or: python -m unittest discover tests

# Run a single test file
python -m unittest tests.test_blog
python -m unittest tests.test_book

# Linting and formatting (dev dependencies)
black src/ tests/
isort src/ tests/
mypy src/
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install    # or: bun install

# Run dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### Docker
```bash
docker-compose up -d              # Start both services
docker-compose up -d --build      # Rebuild and start
docker-compose logs -f            # View logs
docker-compose down               # Stop services
```

## Architecture

### Backend (Python)

The backend follows a modular pipeline architecture for content generation:

```
server.py (FastAPI)
    ↓
src/blog/make_blog.py  or  src/book/make_book.py
    ↓
┌─────────────────────────────────────────────────┐
│  Pipeline stages (called in sequence):          │
│  1. research/web_researcher.py (optional)       │
│  2. planning/content_outline.py                 │
│  3. blog_sections/* generators                  │
│  4. seo/meta_description.py                     │
│  5. post_processing/{proofreader,humanizer}.py  │
└─────────────────────────────────────────────────┘
    ↓
src/text_generation/core.py (LLM abstraction layer)
    ↓
OpenAI / Anthropic / Gemini
```

**Key modules:**
- `src/text_generation/core.py` - LLM provider abstraction with `generate_text()` and `create_provider_from_env()`
- `src/types/providers.py` - Provider configs (`OpenAIConfig`, `AnthropicConfig`, `GeminiConfig`) and `GenerationOptions`
- `src/types/content.py` - Content models (`BlogPost`, `Book`, `Section`, `Chapter`, `SubTopic`, `Topic`)
- `src/integrations/` - Publishing to WordPress, GitHub, Medium

**Provider selection:** Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY` in `.env`. The provider is selected via the `provider_type` parameter (defaults to "openai").

### Frontend (Next.js 14)

App Router structure in `frontend/app/` with:
- `page.tsx` - Main content generation UI
- `providers.tsx` - React context providers
- `frontend/components/` - ContentGenerator, ContentViewer, BookGenerator, BookEditor, ConversationHistory

Uses Tailwind CSS, Framer Motion for animations, and HeadlessUI for accessible components.

### API Endpoints

- `POST /generate-blog` - Generate blog post (BlogGenerationRequest)
- `POST /generate-book` - Generate book (BookGenerationRequest)
- `GET /conversations/{id}` - Get conversation history
- `WS /ws/conversation/{id}` - Real-time updates via WebSocket

## Environment Variables

Required:
- `OPENAI_API_KEY` - For GPT-4 text generation (primary)

Optional:
- `ANTHROPIC_API_KEY` - For Claude models
- `GEMINI_API_KEY` - For Google Gemini
- `SERP_API_KEY` - For web research feature
- `SEC_API_API_KEY` - For SEC filings research
- `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL` - Override default models

## Content Generation CLI

```bash
# Blog post
python -m src.blog.make_blog "Topic" --keywords "a,b" --research --proofread --humanize

# Book
python -m src.book.make_book "Title" --chapters 5 --sections 3 --research

# Planning tools
python -m src.planning.content_calendar "Niche" --timeframe month
python -m src.planning.competitor_analysis "Niche" --competitors "A,B"
python -m src.planning.topic_clusters "Niche" --clusters 3
python -m src.planning.content_outline "Topic" --sections 5
```
