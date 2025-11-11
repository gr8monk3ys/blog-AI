# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

blog-AI is a Python package for AI-powered content generation. It generates blog posts (MDX), books (DOCX), and FAQs (Markdown/HTML) using OpenAI GPT-4 or Anthropic Claude.

**Architecture:** Clean architecture with dependency injection
- Models (Pydantic) → Generators (business logic) → LLM Providers (OpenAI/Anthropic) → Formatters (MDX/DOCX/HTML) → Repositories (file I/O)

**Key Features:**
- 9 CLI commands + REST API (FastAPI)
- Async/await with response caching (TTL-based)
- Batch processing with concurrency control
- Template management system

---

## Essential Commands

### Setup
```bash
# Install all dependencies
uv sync --all-extras

# Setup environment
cp .env.example .env
# Edit .env: Add OPENAI_API_KEY=sk-...

# Quick validation (requires API key)
python test_quick.py
```

### Development
```bash
# Run tests
pytest tests/ -v                    # All tests
pytest tests/unit/ -v               # Unit tests only
pytest --cov=src tests/            # With coverage
pytest tests/unit/test_models.py::TestBlogPost::test_valid -v  # Single test

# Quality checks
ruff format src/ tests/            # Format code
ruff check src/ tests/ --fix       # Lint and auto-fix
mypy src/                          # Type check
python scripts/quality-check.py    # Run all checks

# Run examples
python examples/async_demo.py --topics 5
python examples/cache_demo.py
```

### CLI Usage
```bash
# Generate content
blog-ai-blog "Topic" --sections 3 --verbose
blog-ai-book "Title" --chapters 5 --author "Name"
blog-ai-faq "Topic" --questions 10 --format markdown
blog-ai-batch topics.txt --concurrent 5

# Interactive/config
blog-ai-interactive                # Guided prompts
blog-ai-config                     # Setup wizard

# Template management
blog-ai-template init-defaults
blog-ai-template list

# REST API
blog-ai-server --host 0.0.0.0 --port 8000
# Then: http://localhost:8000/docs (Swagger)
```

---

## Architecture

### Data Flow
```
CLI/API → Generator → LLM Provider → [Cache?] → API Call → Pydantic Model → Formatter → Repository → File
```

### Key Design Patterns
1. **Dependency Injection** - Services receive dependencies via constructor
2. **Strategy Pattern** - Interchangeable LLM providers (`OpenAIProvider`, `AnthropicProvider`) and formatters
3. **Template Method** - Base generator (`ContentGenerator`) defines flow, subclasses implement `generate_structure()` and `generate_content()`
4. **Repository Pattern** - Abstract file I/O operations
5. **Retry Pattern** - Automatic retry with exponential backoff (`retry_with_backoff()`)

### Core Components

**Configuration (`src/config/settings.py`):**
- Pydantic `Settings` class loads from `.env` via `pydantic-settings`
- Validates API keys on startup with helpful error messages
- Single `settings` singleton imported throughout app

**LLM Providers (`src/services/llm/`):**
- Abstract `LLMProvider` interface with 3 methods: `generate()`, `generate_structured()`, `generate_with_memory()`
- `OpenAIProvider` uses LangChain, `AnthropicProvider` uses native API (optional)
- All providers support async via `*_async()` methods
- Integrated retry logic and caching

**Generators (`src/services/generators/`):**
- Abstract `ContentGenerator[TStructure]` base class with template method pattern
- Two-phase generation: 1) `generate_structure()` creates outline, 2) `generate_content()` fills details
- Subclasses: `BlogGenerator`, `BookGenerator`, `FAQGenerator`

**Models (`src/models/`):**
- All content as Pydantic v2 models with validation
- Shared models in `common.py` (Topic, Tag), base in `base.py`
- Content types: `BlogPost`, `Book`, `FAQ` with nested structures

**Formatters (`src/services/formatters/`):**
- `MDXFormatter` - React frontmatter for Next.js/Gatsby
- `DOCXFormatter` - Professional Word documents with styling
- `FAQMarkdownFormatter`, `FAQHTMLFormatter` (Schema.org markup)

**Utilities (`src/utils/`):**
- `CacheManager` - TTL-based caching with FIFO eviction
- `BatchProcessor` - Parallel processing with semaphore
- `TemplateManager` - Custom prompt templates
- `retry_with_backoff()` - Decorator for sync/async retry

---

## Adding New Features

### New Content Type (e.g., Newsletter)

1. **Model** (`src/models/newsletter.py`):
```python
from .base import ContentModel

class Newsletter(ContentModel):
    subject: str
    sections: list[NewsletterSection]
```

2. **Generator** (`src/services/generators/newsletter.py`):
```python
from .base import ContentGenerator

class NewsletterGenerator(ContentGenerator[Newsletter]):
    def generate_structure(self, topic: str, **kwargs) -> Newsletter:
        # LLM call to create structure
        pass

    def generate_content(self, structure: Newsletter, **kwargs) -> Newsletter:
        # Fill in content for each section
        pass
```

3. **Formatter** (`src/services/formatters/newsletter_html.py`):
```python
from .base import Formatter

class NewsletterHTMLFormatter(Formatter[Newsletter]):
    def format(self, content: Newsletter) -> str:
        # Convert to HTML
        pass
```

4. **CLI** (`src/cli/newsletter.py`):
```python
import argparse

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("topic")
    args = parser.parse_args()

    # Initialize generator, generate, format, save
    return 0
```

5. **Entry point** (`pyproject.toml`):
```toml
[project.scripts]
blog-ai-newsletter = "src.cli.newsletter:main"
```

6. **Update exports** in relevant `__init__.py` files

### New LLM Provider (e.g., Ollama)

1. **Provider** (`src/services/llm/ollama.py`):
```python
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        # Call Ollama API
        pass

    async def generate_async(self, prompt: str, **kwargs) -> str:
        return await asyncio.to_thread(self.generate, prompt, **kwargs)
```

2. **Config** (`src/config/settings.py`):
```python
ollama_url: str = Field(default="http://localhost:11434")
```

3. **Optional import** (`src/services/llm/__init__.py`):
```python
try:
    from .ollama import OllamaProvider
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
```

---

## Configuration

All settings via `.env` (see `.env.example`):

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional providers
ANTHROPIC_API_KEY=sk-ant-...

# Model settings
DEFAULT_MODEL=gpt-4
TEMPERATURE=0.9

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
```

Settings loaded by `Settings` class in `src/config/settings.py`. Validation errors on startup show helpful troubleshooting.

---

## Testing

### Test Structure
- `tests/unit/` - Mock all external calls (LLM, file I/O)
- `tests/integration/` - End-to-end with real API calls (use sparingly)
- `tests/fixtures/` - Reusable test data

### Writing Tests
```python
def test_blog_generation_with_mock(mock_llm_provider):
    """Test blog generation with mocked LLM."""
    generator = BlogGenerator(llm=mock_llm_provider, config=mock_settings)
    blog = generator.generate("Test Topic", sections=3)

    assert blog.title == "Test Topic"
    assert len(blog.sections) == 3
    assert mock_llm_provider.generate.call_count > 0
```

**Best practices:**
- Mock LLM calls to avoid API costs
- Use pytest fixtures from `tests/fixtures/`
- Target 80%+ coverage
- Test error cases with custom exceptions

---

## Common Issues

**"Configuration Error: OPENAI_API_KEY"**
- Create `.env`: `cp .env.example .env`
- Add real key: `OPENAI_API_KEY=sk-...`
- Get key at: https://platform.openai.com/api-keys

**"questionary not available"**
- `uv sync --extra interactive`

**"anthropic not available"**
- `uv sync --extra anthropic`

**Import errors after changes**
- `uv sync --all-extras`

**Windows hardlink issues**
- `uv sync --link-mode=copy`

---

## Project Status

**Version:** 0.1.0
**Status:** Feature complete, needs real-world testing with API keys
**See:** [TODO.md](TODO.md) for testing checklist and priorities

Code is implemented and should work, but needs validation that:
- All CLI commands work with real API keys
- All examples run successfully
- Test suite passes with real/mocked API calls
- REST API handles real requests correctly
