# Blog AI Generation Tool

An AI-driven content generation tool for creating blog posts and books. Features a Python backend (FastAPI) with multi-provider LLM support (OpenAI, Anthropic, Gemini) and a Next.js frontend.

## Key Features

- **Blog Post Generation**: Create structured, SEO-optimized blog posts with a single command
- **Book Creation**: Generate full-length books with chapters, sections, and consistent style
- **Content Planning**: Plan your content with calendars, topic clusters, and outlines
- **Competitor Analysis**: Analyze competitors to identify content gaps and opportunities
- **Web Research**: Conduct research to enhance content with accurate information
- **Post-Processing**: Proofread, humanize, and format your content for various platforms
- **Integrations**: Publish directly to WordPress, GitHub, and Medium
- **Multi-Provider LLM Support**: Choose between OpenAI (GPT-4), Anthropic (Claude), or Google Gemini

## Project Structure

```
blog-AI/
├── src/                      # Source code
│   ├── blog/                 # Blog generation modules
│   ├── book/                 # Book generation modules
│   ├── blog_sections/        # Blog section generators
│   ├── planning/             # Content planning tools
│   ├── research/             # Research tools
│   ├── seo/                  # SEO optimization tools
│   ├── integrations/         # Publishing integrations
│   ├── post_processing/      # Content post-processing
│   ├── text_generation/      # LLM abstraction layer
│   └── types/                # Type definitions
├── tests/                    # Test files
├── frontend/                 # Web interface (Next.js 14)
├── .env.example              # Example environment configuration
├── pyproject.toml            # Project dependencies
└── README.md                 # Project documentation
```

## Architecture

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

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI
```

### 2. Configure environment
Create a `.env` file based on `.env.example`:

```bash
# Required - at least one LLM provider
OPENAI_API_KEY=your_openai_api_key_here

# Optional - additional LLM providers
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - model overrides
OPENAI_MODEL=gpt-4
ANTHROPIC_MODEL=claude-3-opus-20240229
GEMINI_MODEL=gemini-1.5-flash-latest

# Optional - research features
SERP_API_KEY=your_serp_api_key_here
SEC_API_API_KEY=your_sec_api_key_here

# Server configuration
DEV_MODE=false                    # Set true for local development without auth
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=60             # Requests per minute for general endpoints
RATE_LIMIT_GENERATION=10          # Requests per minute for generation endpoints
LOG_LEVEL=INFO
```

### 3. Install dependencies

Using Poetry (recommended):
```bash
poetry install
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 4. Start the backend server
```bash
python server.py
```
The API will be available at http://localhost:8000

### 5. Start the frontend (optional)
```bash
cd frontend
npm install
npm run dev
```
The web interface will be available at http://localhost:3000

## Docker Setup

Run the entire application with Docker:

```bash
# Build and start containers
docker-compose up -d

# Rebuild after changes
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

Access points:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate-blog` | Generate a blog post |
| POST | `/generate-book` | Generate a book |
| GET | `/conversations/{id}` | Get conversation history |
| WS | `/ws/conversation/{id}` | Real-time updates via WebSocket |

## CLI Usage

### Generate a Blog Post
```bash
python -m src.blog.make_blog "Your Blog Topic" --keywords "keyword1,keyword2" --research --proofread --humanize
```

Options:
- `--keywords`: Comma-separated list of keywords
- `--research`: Enable web research
- `--tone`: Set content tone (default: "informative")
- `--output`: Specify output filename
- `--proofread`: Enable proofreading
- `--humanize`: Make content more human-like

### Generate a Book
```bash
python -m src.book.make_book "Your Book Topic" --chapters 5 --sections 3 --research
```

Options:
- `--chapters`: Number of chapters (default: 5)
- `--sections`: Sections per chapter (default: 3)
- `--keywords`: Comma-separated keywords
- `--research`: Enable web research
- `--output`: Specify output filename

### Content Planning
```bash
# Generate a content calendar
python -m src.planning.content_calendar "Your Niche" --timeframe month

# Analyze competitors
python -m src.planning.competitor_analysis "Your Niche" --competitors "Competitor1,Competitor2"

# Generate topic clusters
python -m src.planning.topic_clusters "Your Niche" --clusters 3 --subtopics 5

# Create content outlines
python -m src.planning.content_outline "Your Topic" --sections 5
```

### Publishing
```bash
# Publish to WordPress
python -m src.integrations.wordpress "content.md" --url "https://yourblog.com" --username "user" --password "pass"

# Publish to GitHub
python -m src.integrations.github "content.md" --repo "username/repo" --token "github_token"

# Publish to Medium
python -m src.integrations.medium "content.md" --token "medium_token" --tags "tag1,tag2"
```

## Testing

### Backend
```bash
# Run all tests
python run_tests.py
# or
python -m unittest discover tests

# Run a single test file
python -m unittest tests.test_blog
python -m unittest tests.test_book
```

### Frontend
```bash
cd frontend

# Run tests
npm run test

# Run tests once
npm run test:run

# Run with coverage
npm run test:coverage
```

### Linting and Formatting
```bash
# Backend
black src/ tests/
isort src/ tests/
mypy src/

# Frontend
cd frontend && npm run lint
```

## Dependencies

**Backend:**
- `openai` - OpenAI API client
- `anthropic` - Anthropic API client
- `google-generativeai` - Google Gemini API client
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-dotenv` - Environment management

**Frontend:**
- `next` - React framework (v14)
- `tailwindcss` - CSS framework
- `framer-motion` - Animations
- `@headlessui/react` - Accessible components

## Troubleshooting

See the [Troubleshooting Guide](troubleshooting.md) for solutions to common issues.

## License

This project is available under the [MIT License](LICENSE).
