# Contributing to blog-AI

Thank you for your interest in contributing to blog-AI! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)

## Code of Conduct

This project follows a simple code of conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment for all contributors

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Quick Setup

The easiest way to set up your development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/blog-ai.git
cd blog-ai

# Run the setup script
python scripts/dev-setup.py
```

This script will:
- Install all dependencies
- Set up pre-commit hooks
- Create a `.env` file from template
- Run validation tests

## Development Setup

### Manual Setup

If you prefer manual setup:

1. **Install dependencies:**

```bash
# Install with all extras (dev dependencies)
uv sync --all-extras
```

2. **Set up pre-commit hooks:**

```bash
# Install pre-commit
uv run pre-commit install

# Test it works
uv run pre-commit run --all-files
```

3. **Configure environment:**

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

4. **Verify installation:**

```bash
# Run quick validation
python test_quick.py

# Or use make
make test-quick
```

## Making Changes

### Branch Naming

Use descriptive branch names with one of these prefixes:

- `feature/` - New features
- `bugfix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

Example: `feature/add-async-support` or `bugfix/fix-metadata-validation`

### Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(generators): add async support for blog generation

- Implement async/await in BlogGenerator
- Update tests for async operations
- Add performance benchmarks

Closes #123
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
uv run pytest tests/unit/ -v

# Run integration tests only
uv run pytest tests/integration/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_models.py -v

# Run specific test
uv run pytest tests/unit/test_models.py::TestBlogPost::test_valid_blog_post -v
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Mock external dependencies (LLM API calls, file I/O)
- Aim for 80%+ code coverage

Example test:

```python
def test_blog_post_creation_with_valid_data_succeeds():
    """Test that BlogPost can be created with valid data."""
    post = BlogPost(
        metadata=BlogMetadata(
            title="Test Post",
            description="Test description",
            tags=["test"],
        ),
        sections=[
            BlogSection(
                title="Section",
                subtopics=[Topic(title="Topic", content="Content")],
            )
        ],
    )

    assert post.title == "Test Post"
    assert len(post.sections) == 1
```

## Code Quality

### Running Quality Checks

```bash
# Run all quality checks
python scripts/quality-check.py

# Or run individually:

# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/

# Security scan
uv run bandit -r src/
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

- Code formatting (ruff)
- Linting (ruff)
- Type checking (mypy)
- Security checks (bandit)
- YAML/JSON validation
- Trailing whitespace removal

To run manually:

```bash
uv run pre-commit run --all-files
```

## Submitting Changes

### Pull Request Process

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**

- Write clean, documented code
- Add/update tests
- Update documentation if needed

3. **Run quality checks:**

```bash
python scripts/quality-check.py
```

4. **Commit your changes:**

```bash
git add .
git commit -m "feat: add your feature"
```

5. **Push to your fork:**

```bash
git push origin feature/your-feature-name
```

6. **Create Pull Request:**

- Go to GitHub and create a PR
- Fill out the PR template
- Link any related issues
- Wait for CI checks to pass
- Address review comments

### Pull Request Guidelines

- Keep PRs focused on a single feature/fix
- Update relevant documentation
- Ensure all tests pass
- Maintain or improve code coverage
- Follow the existing code style
- Add a clear description of changes

## Project Structure

```
blog-ai/
├── src/                    # Source code
│   ├── cli/               # Command-line interfaces
│   ├── config/            # Configuration and settings
│   ├── exceptions/        # Custom exceptions
│   ├── models/            # Pydantic models
│   ├── repositories/      # Data persistence layer
│   ├── services/          # Business logic
│   │   ├── formatters/   # Output formatters (MDX, DOCX)
│   │   ├── generators/   # Content generators
│   │   └── llm/          # LLM provider integrations
│   └── utils/            # Utility functions
├── tests/                 # Test suite
│   ├── fixtures/         # Test data and fixtures
│   ├── integration/      # Integration tests
│   └── unit/            # Unit tests
├── scripts/              # Development scripts
└── docs/                # Documentation
```

## Coding Standards

### Style Guide

- Follow PEP 8 (enforced by ruff)
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes
- Prefer composition over inheritance
- Keep functions small and focused

### Type Hints

Always use type hints:

```python
def generate_blog(topic: str, sections: int = 3) -> BlogPost:
    """Generate a blog post about the given topic.

    Args:
        topic: The main topic for the blog post
        sections: Number of sections to generate

    Returns:
        A complete BlogPost instance

    Raises:
        ValidationError: If topic is empty
        LLMError: If generation fails
    """
    ...
```

### Docstrings

Use Google-style docstrings:

```python
class BlogGenerator:
    """Generates blog posts using LLM providers.

    This class orchestrates the blog generation process by creating
    structure, filling content, and validating the result.

    Attributes:
        llm_provider: The LLM provider to use for generation
        settings: Configuration settings

    Example:
        >>> generator = BlogGenerator(provider, settings)
        >>> blog = generator.generate("AI in 2024")
    """
```

### Error Handling

- Use custom exceptions from `src.exceptions`
- Always include context in exceptions
- Handle errors at appropriate levels
- Log errors with appropriate levels

```python
try:
    result = self.llm_provider.generate(prompt)
except Exception as e:
    raise GenerationError(
        f"Failed to generate content: {e}",
        details={"topic": topic, "provider": self.llm_provider.model_name},
    )
```

### Import Organization

Organize imports in this order:

1. Standard library
2. Third-party packages
3. Local imports

Use absolute imports for local modules:

```python
# Standard library
import json
from pathlib import Path

# Third-party
from pydantic import BaseModel

# Local
from src.models import BlogPost
from src.services import BlogGenerator
```

## Performance Benchmarking

Run performance benchmarks to ensure changes don't degrade performance:

```bash
python scripts/benchmark.py
```

Expected performance targets:
- Model creation: <1ms
- MDX formatting: <50ms
- DOCX formatting: <200ms
- Validation: <1ms

## Documentation

### Updating Documentation

When adding features:

1. Update relevant docstrings
2. Update README.md if user-facing
3. Update SYSTEM_DESIGN.md for architecture changes
4. Add examples to documentation
5. Update CHANGELOG.md

### Building Documentation

```bash
# Generate API documentation (if using Sphinx)
cd docs
make html
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security@example.com

## Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- GitHub contributors page
- Release notes

Thank you for contributing to blog-AI! 🎉
