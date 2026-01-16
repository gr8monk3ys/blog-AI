# Contributing to Blog AI

Thank you for your interest in contributing to Blog AI! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install black isort flake8 mypy pytest pytest-cov pytest-asyncio

# Copy environment file
cp .env.example .env
# Edit .env and add your API keys
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running the Application

```bash
# Terminal 1: Start backend
DEV_MODE=true python server.py

# Terminal 2: Start frontend
cd frontend && npm run dev
```

## Code Style

### Python

We use the following tools for Python code quality:

- **Black** for formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black src/ tests/ server.py
isort src/ tests/ server.py

# Check linting
flake8 src/ tests/ server.py

# Type check
mypy src/ server.py --ignore-missing-imports
```

### TypeScript/JavaScript

We use ESLint and Prettier for frontend code:

```bash
cd frontend

# Lint code
npm run lint

# Type check
npx tsc --noEmit
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_blog.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the code style guidelines
4. **Add tests** for new functionality
5. **Run the test suite** to ensure all tests pass
6. **Commit your changes** using conventional commits:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug in generation"
   git commit -m "docs: update README"
   ```
7. **Push** to your fork and create a Pull Request

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests have been added/updated
- [ ] Documentation has been updated
- [ ] All tests pass
- [ ] No new linting warnings

## Project Structure

```
blog-AI/
├── src/                    # Python source code
│   ├── blog/              # Blog generation
│   ├── book/              # Book generation
│   ├── text_generation/   # LLM abstraction
│   ├── planning/          # Content planning
│   ├── research/          # Web research
│   ├── seo/               # SEO optimization
│   ├── post_processing/   # Content post-processing
│   ├── integrations/      # Publishing integrations
│   └── types/             # Type definitions
├── frontend/              # Next.js frontend
│   ├── app/               # App Router pages
│   ├── components/        # React components
│   ├── lib/               # Utility functions
│   └── types/             # TypeScript types
├── tests/                 # Python tests
├── server.py              # FastAPI server
└── docker-compose.yml     # Docker configuration
```

## Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Report security vulnerabilities privately to the maintainers

## Questions?

Feel free to open an issue for questions or discussions about contributing.
