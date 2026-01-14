---
description: View, edit, or create project-specific rules that customize Claude's behavior
model: claude-sonnet-4-5
---

# Project Rules Management

Manage project-specific rules that customize how Claude works in this codebase.

## Command: $ARGUMENTS

## Operations

### View Rules (`/rules` or `/rules view`)
Display current project rules from `.claude/rules/PROJECT-RULES.md`:
- Code style rules
- Architecture rules
- Framework-specific rules
- Testing rules
- Security rules

### Add Rule (`/rules add <category> <rule>`)
Add a new rule to the project:
```
/rules add typescript prefer_interfaces_over_types
/rules add testing minimum_coverage 90%
/rules add security require_csrf_protection
```

### Check Compliance (`/rules check [file]`)
Check if code follows project rules:
- Validates against all applicable rules
- Reports violations with suggestions
- Can check specific file or recent changes

### Initialize Rules (`/rules init`)
Create a new PROJECT-RULES.md file with:
- Detected project settings
- Recommended rules for tech stack
- Customizable template

## Rule Categories

### Code Style
```yaml
typescript:    # TypeScript-specific rules
formatting:    # Code formatting preferences
naming:        # Naming conventions
```

### Architecture
```yaml
structure:     # File organization
components:    # Component rules
api:           # API design rules
```

### Framework
```yaml
nextjs:        # Next.js specific
react:         # React patterns
vue:           # Vue patterns (if applicable)
```

### Quality
```yaml
testing:       # Test requirements
security:      # Security rules
performance:   # Performance rules
```

## Rule Format

Rules use YAML format:
```yaml
category:
  rule_name: value
  another_rule:
    option1: value1
    option2: value2
```

## Example Rules

### Strict TypeScript
```yaml
typescript:
  strict: true
  no_any: true
  explicit_return_types: true
```

### API Standards
```yaml
api:
  validation: zod_required
  error_format: "{ error: string, success: false }"
  versioning: url_prefix
```

### Testing Requirements
```yaml
testing:
  framework: vitest
  coverage_minimum: 80%
  require_integration_tests: true
```

## Rule Inheritance

Rules are checked in order:
1. `.claude/rules/PROJECT-RULES.md` (project-specific)
2. Plugin defaults (from lorenzos-claude-code)
3. Claude defaults

Project rules override plugin/default rules.

## Exceptions

Document exceptions in the rules file:
```yaml
exceptions:
  - file: legacy/old-code.ts
    rules_ignored: [strict_types, max_lines]
    reason: Legacy code pending refactor
```

## Best Practices

1. **Start Small**: Add rules incrementally
2. **Document Why**: Include rationale for non-obvious rules
3. **Review Regularly**: Update rules as project evolves
4. **Be Specific**: Vague rules are hard to follow
5. **Allow Exceptions**: Not all code fits all rules

## File Location

Project rules file: `.claude/rules/PROJECT-RULES.md`

This file should be committed to version control so all team members and Claude instances follow the same rules.
