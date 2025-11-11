## Description

<!-- Provide a clear and concise description of your changes -->

## Related Issues

<!-- Link to related issues using #issue_number -->
<!-- Use keywords: Fixes #123, Closes #456, Resolves #789 -->

Fixes #

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] = Bug fix (non-breaking change that fixes an issue)
- [ ] ( New feature (non-breaking change that adds functionality)
- [ ] =¥ Breaking change (fix or feature that would cause existing functionality to change)
- [ ] =Ý Documentation update
- [ ] <¨ Code style update (formatting, renaming)
- [ ] { Refactoring (no functional changes)
- [ ] ¡ Performance improvement
- [ ]  Test update
- [ ] =' Configuration change
- [ ] =æ Dependency update

## Changes Made

<!-- Describe the changes in detail -->

### Added
-

### Changed
-

### Removed
-

### Fixed
-

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

### Test Environment
- Python version:
- OS:
- Dependencies:

### Tests Performed
- [ ] Ran existing test suite: `pytest tests/`
- [ ] Added new unit tests
- [ ] Added new integration tests
- [ ] Manually tested the changes
- [ ] Tested with different LLM providers (OpenAI, Anthropic)

### Test Commands
```bash
# Commands used to test the changes
pytest tests/
```

### Test Results
<!-- Paste relevant test output or screenshots -->

```
# Test output
```

## Code Quality Checklist

<!-- Mark completed items with an 'x' -->

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code performed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Documentation has been updated (README, CLAUDE.md, docstrings)
- [ ] No new warnings or errors introduced
- [ ] Type hints added to new functions
- [ ] Pydantic models used for data validation
- [ ] Error handling implemented with custom exceptions
- [ ] Logging added at appropriate levels

## Pre-commit Checks

<!-- All pre-commit hooks must pass -->

- [ ] `ruff format` - Code formatting
- [ ] `ruff check` - Linting
- [ ] `mypy` - Type checking
- [ ] `bandit` - Security checks
- [ ] All pre-commit hooks passed

## Documentation

<!-- Mark relevant documentation updates -->

- [ ] Updated README.md
- [ ] Updated CLAUDE.md
- [ ] Updated TODO.md (if implementing planned features)
- [ ] Updated CHANGELOG.md
- [ ] Added/updated docstrings
- [ ] Added/updated type hints
- [ ] Added/updated examples

## Screenshots / Examples

<!-- If applicable, add screenshots or example output -->

### Before
<!-- Show behavior before the change -->

### After
<!-- Show behavior after the change -->

## Performance Impact

<!-- Describe any performance implications -->

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance impact analyzed and acceptable
- [ ] Added benchmarks for performance-critical changes

## Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

### Impact
<!-- Describe what breaks and why -->

### Migration Guide
<!-- Provide step-by-step instructions for users to adapt to the changes -->

## Security Considerations

<!-- Address any security implications -->

- [ ] No security implications
- [ ] Security implications reviewed
- [ ] No sensitive data exposed
- [ ] API keys and secrets properly handled
- [ ] Input validation implemented

## Deployment Notes

<!-- Any special deployment considerations -->

- [ ] No special deployment steps required
- [ ] Dependencies added/updated (run `uv sync`)
- [ ] Environment variables added/changed (update `.env`)
- [ ] Database migrations required
- [ ] Configuration changes required

## Additional Context

<!-- Add any other context about the PR here -->

## Checklist

<!-- Final checklist before requesting review -->

- [ ] I have read the [CONTRIBUTING.md](../CONTRIBUTING.md) guide
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings
- [ ] I have checked for potential security issues
- [ ] I have added comments explaining complex logic

---

**Reviewer Notes:**
<!-- Anything specific you want reviewers to focus on -->
