# Project Rules

This file defines project-specific rules that Claude should follow when working in this repository. Similar to `.cursorrules` or `.editorconfig`, these rules customize Claude's behavior for this specific project.

## How to Use

1. Copy this file to your project root as `.claude/rules/PROJECT-RULES.md`
2. Customize the rules for your project
3. Claude will read and follow these rules

---

## Code Style Rules

### TypeScript
```yaml
typescript:
  strict: true
  no_any: true
  explicit_return_types: true
  prefer_const: true
  no_unused_vars: error
```

### Formatting
```yaml
formatting:
  indent: 2 spaces
  quotes: single
  semicolons: false
  trailing_comma: es5
  max_line_length: 100
```

### Naming Conventions
```yaml
naming:
  components: PascalCase
  functions: camelCase
  constants: SCREAMING_SNAKE_CASE
  files:
    components: PascalCase.tsx
    utilities: camelCase.ts
    types: camelCase.types.ts
    tests: *.test.ts or *.spec.ts
```

## Architecture Rules

### File Organization
```yaml
structure:
  components: src/components/
  hooks: src/hooks/
  utils: src/lib/
  types: src/types/
  api: app/api/
  pages: app/
```

### Component Rules
```yaml
components:
  max_lines: 200
  single_responsibility: true
  props_interface: required
  default_exports: false
  memo_threshold: 50_lines
```

### API Rules
```yaml
api:
  validation: zod_required
  error_format: "{ error: string, success: false }"
  success_format: "{ data: T, success: true }"
  auth_middleware: required_for_protected
```

## Framework-Specific Rules

### Next.js
```yaml
nextjs:
  version: 15
  router: app
  prefer_server_components: true
  use_server_actions: true
  image_component: next/image
```

### React
```yaml
react:
  hooks_only: true
  no_class_components: true
  use_memo_when: expensive_computation
  use_callback_when: passed_to_memoized_child
```

## Testing Rules

### Unit Tests
```yaml
testing:
  framework: vitest
  coverage_minimum: 80%
  test_file_location: adjacent
  mock_external_deps: true
```

### Test Structure
```yaml
test_structure:
  describe_component: true
  group_by_behavior: true
  use_testing_library: true
  no_implementation_details: true
```

## Security Rules

### General
```yaml
security:
  no_secrets_in_code: true
  validate_all_inputs: true
  sanitize_outputs: true
  use_https_only: true
```

### Authentication
```yaml
auth:
  jwt_in_httponly_cookies: true
  refresh_token_rotation: true
  password_hashing: bcrypt_or_argon2
```

## Documentation Rules

### Code Comments
```yaml
comments:
  when: non_obvious_logic_only
  format: jsdoc_for_public_apis
  no_commented_out_code: true
  no_todo_without_issue: true
```

### README
```yaml
readme:
  required_sections:
    - installation
    - usage
    - configuration
    - contributing
```

## Git Rules

### Commits
```yaml
commits:
  conventional_commits: true
  max_subject_length: 72
  require_body_for_features: true
  sign_commits: preferred
```

### Branches
```yaml
branches:
  main: protected
  naming: feature/*, bugfix/*, hotfix/*
  delete_after_merge: true
```

## Performance Rules

### General
```yaml
performance:
  lazy_load_routes: true
  optimize_images: true
  minimize_bundle: true
  cache_static_assets: true
```

### Database
```yaml
database:
  no_n_plus_one: true
  use_indexes: true
  paginate_lists: true
  connection_pooling: true
```

---

## Rule Priorities

When rules conflict, follow this priority:
1. Security rules (highest)
2. Correctness rules
3. Performance rules
4. Style rules (lowest)

## Exceptions

Document any exceptions to rules here:
```yaml
exceptions:
  - file: legacy/old-component.tsx
    rules_ignored: [max_lines, memo_threshold]
    reason: Legacy code, scheduled for refactor
```

---

## Custom Rules

Add project-specific rules here:

```yaml
custom:
  # Example:
  # always_use_feature_flags: true
  # require_analytics_events: true
```
