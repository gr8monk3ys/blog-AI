---
description: Analyze a GitHub issue and implement the fix with tests and validation
model: claude-sonnet-4-5
---

# Fix GitHub Issue

Analyze a GitHub issue and implement a complete fix with tests and validation.

## Issue Reference: $ARGUMENTS

## Workflow

### Step 1: Issue Analysis

First, retrieve and analyze the issue:

```bash
# If $ARGUMENTS is a URL like https://github.com/owner/repo/issues/123
gh issue view [issue-number] --json title,body,labels,comments,assignees

# Or if just a number
gh issue view $ARGUMENTS
```

**Extract from the issue:**
- **Problem Statement**: What is broken or missing?
- **Reproduction Steps**: How to trigger the issue?
- **Expected Behavior**: What should happen?
- **Actual Behavior**: What happens instead?
- **Environment**: OS, Node version, etc.
- **Related Context**: Links, screenshots, logs

### Step 2: Root Cause Investigation

Investigate the codebase to find the root cause:

```markdown
## Investigation Notes

### Suspected Files
1. `path/to/file.ts` - [why this file might be involved]
2. `path/to/other.ts` - [why this file might be involved]

### Hypothesis
The issue is likely caused by [hypothesis] because [evidence].

### Verification Steps
1. [Step to verify hypothesis]
2. [Step to confirm root cause]
```

### Step 3: Solution Design

Design the fix before implementing:

```markdown
## Proposed Solution

### Approach
[Description of how to fix the issue]

### Files to Modify
1. `path/to/file.ts` - [what changes]
2. `path/to/other.ts` - [what changes]

### New Files (if any)
- `path/to/new-file.ts` - [purpose]

### Risk Assessment
- **Breaking Changes**: [none / potential impacts]
- **Dependencies**: [any new dependencies needed]
- **Migration**: [any data migration needed]

### Alternative Approaches Considered
1. [Alternative 1] - Not chosen because [reason]
2. [Alternative 2] - Not chosen because [reason]
```

### Step 4: Write Tests First (TDD)

Create tests that will verify the fix:

```typescript
describe('Issue #[number]: [title]', () => {
  it('should [expected behavior that was broken]', () => {
    // This test should FAIL before the fix
    // and PASS after the fix
  });

  it('should not regress existing behavior', () => {
    // Ensure we don't break anything else
  });

  it('should handle edge case from issue', () => {
    // Test specific scenario from the issue
  });
});
```

### Step 5: Implement the Fix

Apply the fix with these guidelines:

1. **Minimal Changes** - Only change what's necessary
2. **Follow Conventions** - Match existing code style
3. **Add Comments** - Explain non-obvious fixes
4. **Update Types** - Ensure type safety

```typescript
// Before: (showing the problematic code)
function problematicFunction() {
  // Old implementation with bug
}

// After: (showing the fixed code)
function problematicFunction() {
  // Fixed implementation
  // Note: Fixed issue #123 - [brief explanation]
}
```

### Step 6: Validate the Fix

Run comprehensive validation:

```bash
# Run the specific test
npm run test -- --grep "Issue #[number]"

# Run related tests
npm run test -- path/to/affected/module

# Run full test suite
npm run test

# Type check
npm run typecheck

# Lint
npm run lint

# Build
npm run build
```

### Step 7: Create Commit

Create a well-documented commit:

```bash
git add -A
git commit -m "fix: [brief description]

Fixes #[issue-number]

Root cause: [explanation of what was wrong]

Solution: [explanation of the fix]

Testing: [how the fix was verified]"
```

### Step 8: Document the Fix

Add to PR description or issue comment:

```markdown
## Fix Summary

### Problem
[Clear description of the issue]

### Root Cause
[What was causing the problem]

### Solution
[How the fix addresses the root cause]

### Testing
- [ ] New tests added for the specific issue
- [ ] Existing tests still pass
- [ ] Manual testing completed
- [ ] Edge cases covered

### Screenshots/Logs (if applicable)
[Before/after screenshots or relevant logs]

### Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated (if needed)
- [ ] No breaking changes (or documented)
```

## Issue Categories

### Bug Fix Template
```markdown
**Type:** Bug Fix
**Severity:** [Critical/High/Medium/Low]
**Affected Area:** [Component/Module]

**Fix:** [Brief description]
**Test:** [How to verify]
```

### Feature Implementation Template
```markdown
**Type:** Feature
**Scope:** [Component/Module]

**Implementation:** [Brief description]
**Dependencies:** [Any new dependencies]
**Documentation:** [Docs to update]
```

### Performance Fix Template
```markdown
**Type:** Performance
**Metric:** [What metric improves]
**Before:** [Baseline measurement]
**After:** [Improved measurement]

**Approach:** [How performance was improved]
```

## Output Expectations

After running `/fix-issue`, you should have:

1. **Understanding** - Clear explanation of the issue
2. **Root Cause** - Identified source of the problem
3. **Tests** - Tests that verify the fix
4. **Implementation** - Clean, minimal fix
5. **Validation** - Proof that tests pass
6. **Commit** - Ready-to-push commit with proper message

## Tips

- Always reproduce the issue before fixing
- Write the test that would have caught this bug
- Consider if this bug could exist elsewhere
- Check if there are related issues to address
- Update documentation if the fix changes behavior
