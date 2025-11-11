# blog-AI

AI-powered content generation tool for blog posts, books, and FAQs using OpenAI GPT-4 or Anthropic Claude.

**Version:** 0.1.0
**Status:** Feature complete, needs real-world testing
**Python:** 3.12+

## What It Does

Generate content with AI:
- **Blog posts** (Markdown/MDX with SEO)
- **Books** (Multi-chapter DOCX)
- **FAQs** (Markdown/HTML with Schema.org)
- **Batch processing** (Multiple topics from file)
- **REST API** (FastAPI with OpenAPI docs)

## Quick Start

### 1. Install

```bash
git clone https://github.com/yourusername/blog-AI.git
cd blog-AI
uv sync --all-extras
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-...
```

Get your API key: https://platform.openai.com/api-keys

### 3. Generate

```bash
# Blog post
blog-ai-blog "Your Topic" --sections 3

# Book
blog-ai-book "Book Title" --chapters 5 --author "Your Name"

# FAQ
blog-ai-faq "FAQ Topic" --questions 10

# Interactive mode (guided)
blog-ai-interactive

# Batch process topics
blog-ai-batch topics.txt --concurrent 5

# REST API server
blog-ai-server
# Then visit: http://localhost:8000/docs
```

## Features

### Content Types

- ✅ **Blog posts** - SEO-optimized, 3+ sections, MDX format
- ✅ **Books** - Multi-chapter DOCX with styling
- ✅ **FAQs** - Markdown or HTML with Schema.org markup
- ✅ **Batch processing** - Process multiple topics in parallel

### LLM Providers

- ✅ **OpenAI** (GPT-4, GPT-3.5) - Default, always available
- ✅ **Anthropic** (Claude) - Optional: `pip install blog-ai[anthropic]`

### Performance

- ✅ **Async/await** - Concurrent API calls for speed
- ✅ **Caching** - Save API costs by caching responses (TTL-based)
- ✅ **Batch processing** - Parallel generation with concurrency control

### Developer Experience

- ✅ **Interactive mode** - Questionary-based prompts
- ✅ **Config wizard** - First-time setup helper
- ✅ **Template system** - Customize prompts and structure
- ✅ **REST API** - FastAPI with Swagger docs

## CLI Commands

```bash
blog-ai-blog <topic>          # Generate blog post
blog-ai-book <topic>          # Generate book
blog-ai-faq <topic>           # Generate FAQ
blog-ai-batch <file>          # Batch process topics
blog-ai-interactive           # Interactive mode
blog-ai-config               # Setup wizard
blog-ai-template             # Manage templates
blog-ai-server               # Launch REST API
blog-ai                      # Main CLI with subcommands
```

### Blog Options

```bash
blog-ai-blog "Topic" \
  --sections 3 \
  --provider openai \
  --temperature 0.7 \
  --output-dir content/blog \
  --verbose
```

### Book Options

```bash
blog-ai-book "Book Title" \
  --chapters 11 \
  --topics 4 \
  --author "Your Name" \
  --subtitle "Optional Subtitle" \
  --provider anthropic \
  --output mybook.docx
```

### FAQ Options

```bash
blog-ai-faq "Topic" \
  --questions 8 \
  --format markdown \
  --provider openai \
  --no-intro \
  --no-conclusion
```

### Batch Processing

```bash
# Create topics.txt (one topic per line)
echo "AI in Healthcare" > topics.txt
echo "Climate Tech" >> topics.txt
echo "Web3 Trends" >> topics.txt

# Process in parallel
blog-ai-batch topics.txt --concurrent 5 --provider openai
```

## REST API

Start the server:

```bash
blog-ai-server --host 0.0.0.0 --port 8000
```

API documentation: http://localhost:8000/docs

### Example Request

```bash
# Generate blog post
curl -X POST http://localhost:8000/api/v1/blog/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI in 2024",
    "sections": 3,
    "provider": "openai",
    "output_format": "json"
  }'

# Health check
curl http://localhost:8000/health
```

### Endpoints

- `POST /api/v1/blog/generate` - Generate blog post
- `POST /api/v1/book/generate` - Generate book
- `POST /api/v1/faq/generate` - Generate FAQ
- `GET /health` - Check API health and provider status

## Configuration

All settings via `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
ANTHROPIC_API_KEY=sk-ant-...
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4000
CACHE_ENABLED=true
CACHE_TTL=3600
LOG_LEVEL=INFO
```

See [.env.example](.env.example) for all options.

## Project Structure

```
blog-AI/
├── src/
│   ├── api/          # FastAPI REST API
│   ├── cli/          # CLI commands (9 total)
│   ├── models/       # Pydantic models
│   ├── services/     # Generators, formatters, LLM providers
│   ├── utils/        # Caching, batch processing, templates
│   └── config/       # Settings
├── tests/            # Unit & integration tests
├── examples/         # Example scripts
└── templates/        # User templates
```

**Code Stats:**
- 53 Python files
- ~9,000 lines of code
- Type hints throughout
- Comprehensive error handling

## Development

### Setup

```bash
# Install all dependencies
uv sync --all-extras

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Quality checks
ruff format src/ tests/
ruff check src/ tests/
mypy src/
```

### Run Examples

```bash
# See all examples
ls examples/

# Async performance demo
python examples/async_demo.py --topics 5

# Cache demo
python examples/cache_demo.py --runs 3

# Batch processing demo
python examples/batch_demo.py

# FAQ demo
python examples/faq_demo.py

# Provider comparison (OpenAI vs Anthropic)
python examples/provider_comparison.py
```

### Adding Features

See [CLAUDE.md](CLAUDE.md) for architecture details and development guidelines.

**Example: Add new content type**
1. Create model in `src/models/`
2. Create generator in `src/services/generators/`
3. Create formatter in `src/services/formatters/`
4. Create CLI in `src/cli/`
5. Add entry point to `pyproject.toml`

## Architecture

**Clean Architecture with Dependency Injection:**

```
CLI/API → Generator → LLM Provider → [Cache] → API Call
                ↓
         Pydantic Model
                ↓
           Formatter
                ↓
          Repository
                ↓
          File Output
```

**Key Patterns:**
- Strategy (interchangeable providers/formatters)
- Template Method (base generator flow)
- Repository (abstract I/O)
- Retry with exponential backoff

## Testing

**Run tests:**
```bash
# Quick validation (needs API key)
python test_quick.py

# Full test suite
pytest tests/ -v

# With coverage
pytest --cov=src tests/

# Specific test
pytest tests/unit/test_models.py -v
```

**Test Strategy:**
- Unit tests with mocked LLM calls (no API charges)
- Integration tests verify end-to-end flow
- Fixtures for reusable test data

## Known Issues

- **Requires API key** - Can't run without OpenAI or Anthropic API key
- **Untested end-to-end** - Code is complete but needs real-world validation
- **Interactive mode** - Requires `questionary`: `pip install blog-ai[interactive]`
- **Windows** - Use `uv sync --link-mode=copy` to avoid hardlink issues

## Troubleshooting

### "Configuration Error: OPENAI_API_KEY"
```bash
cp .env.example .env
# Edit .env and add your API key
```

### "questionary not available"
```bash
uv sync --extra interactive
# or
pip install blog-ai[interactive]
```

### "anthropic not available"
```bash
uv sync --extra anthropic
# or
pip install blog-ai[anthropic]
```

### Import errors
```bash
uv sync --all-extras
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guide
- Testing guidelines
- Pull request process

## Roadmap

See [TODO.md](TODO.md) for current priorities and future plans.

**Current focus:**
- Real-world testing with API keys
- Documentation accuracy verification
- Example validation
- Version 1.0.0 release preparation

## License

GPL-3.0 - See LICENSE file

## Credits

Built with:
- OpenAI GPT-4
- Anthropic Claude
- FastAPI
- Pydantic
- LangChain
- python-docx

---

**Status:** Feature complete but needs real-world testing. See [TODO.md](TODO.md) for details.

**Want to help?** Test with real API keys and report issues!
