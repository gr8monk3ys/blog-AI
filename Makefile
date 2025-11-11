# Makefile for blog-AI

# Installation and setup
.PHONY: init
init:
	uv sync --link-mode=copy

.PHONY: init-dev
init-dev:
	uv sync --all-extras
	uv run pre-commit install

.PHONY: setup
setup:
	python scripts/dev-setup.py

# Testing
.PHONY: test-quick
test-quick:
	uv run python test_quick.py

.PHONY: test-blog
test-blog:
	uv run python test_blog.py

.PHONY: test-book
test-book:
	uv run python test_book.py

.PHONY: test
test:
	uv run pytest tests/ -v

.PHONY: test-unit
test-unit:
	uv run pytest tests/unit/ -v

.PHONY: test-integration
test-integration:
	uv run pytest tests/integration/ -v

.PHONY: test-cov
test-cov:
	uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

.PHONY: coverage
coverage:
	python scripts/coverage-report.py

# Code quality
.PHONY: format
format:
	uv run ruff format src/ tests/

.PHONY: format-check
format-check:
	uv run ruff format --check src/ tests/

.PHONY: lint
lint:
	uv run ruff check src/ tests/

.PHONY: lint-fix
lint-fix:
	uv run ruff check src/ tests/ --fix

.PHONY: type-check
type-check:
	uv run mypy src/

.PHONY: security
security:
	uv run bandit -r src/ -c pyproject.toml

.PHONY: quality
quality:
	python scripts/quality-check.py

.PHONY: pre-commit
pre-commit:
	uv run pre-commit run --all-files

# Benchmarking
.PHONY: benchmark
benchmark:
	python scripts/benchmark.py

# Utilities
.PHONY: templates
templates:
	python scripts/template-manager.py list

.PHONY: bump-version
bump-version:
	python scripts/bump-version.py

.PHONY: changelog
changelog:
	python scripts/update-changelog.py

.PHONY: bump-patch
bump-patch:
	python scripts/bump-version.py patch

.PHONY: bump-minor
bump-minor:
	python scripts/bump-version.py minor

.PHONY: bump-major
bump-major:
	python scripts/bump-version.py major

# Cleaning
.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf htmlcov coverage.xml .coverage

.PHONY: clean-all
clean-all: clean
	rm -rf .venv dist build *.egg-info

# Building and distribution
.PHONY: build
build:
	uv build

.PHONY: install-local
install-local:
	uv pip install -e .

# Documentation
.PHONY: docs
docs:
	@echo "Documentation files:"
	@echo "  - README.md"
	@echo "  - CONTRIBUTING.md"
	@echo "  - SECURITY.md"
	@echo "  - CHANGELOG.md"
	@echo "  - SYSTEM_DESIGN.md"

# Help
.PHONY: help
help:
	@echo "blog-AI Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make init          - Install dependencies"
	@echo "  make init-dev      - Install dev dependencies and setup pre-commit"
	@echo "  make setup         - Run interactive setup script"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make coverage      - Generate detailed coverage report"
	@echo "  make test-quick    - Quick validation test"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format        - Format code with ruff"
	@echo "  make format-check  - Check code formatting"
	@echo "  make lint          - Lint code with ruff"
	@echo "  make lint-fix      - Lint and auto-fix issues"
	@echo "  make type-check    - Run mypy type checking"
	@echo "  make security      - Run security scan with bandit"
	@echo "  make quality       - Run all quality checks"
	@echo "  make pre-commit    - Run pre-commit hooks"
	@echo ""
	@echo "Utilities:"
	@echo "  make templates     - List available prompt templates"
	@echo "  make bump-version  - Bump version (interactive)"
	@echo "  make bump-patch    - Bump patch version (X.Y.Z+1)"
	@echo "  make bump-minor    - Bump minor version (X.Y+1.0)"
	@echo "  make bump-major    - Bump major version (X+1.0.0)"
	@echo "  make changelog     - Update CHANGELOG.md"
	@echo ""
	@echo "Other:"
	@echo "  make benchmark     - Run performance benchmarks"
	@echo "  make clean         - Remove cache files"
	@echo "  make clean-all     - Remove all generated files including venv"
	@echo "  make build         - Build distribution packages"
	@echo "  make help          - Show this help message"
