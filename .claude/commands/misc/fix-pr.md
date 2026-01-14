---
description: Address PR reviewer feedback and resolve requested changes
model: claude-sonnet-4-5
---

# Fix PR Feedback

Address reviewer feedback on a pull request and resolve all requested changes.

## PR Reference: $ARGUMENTS

## Workflow

### Step 1: Retrieve PR Feedback

Get all review comments and requested changes:

```bash
# Get PR details and reviews
gh pr view $ARGUMENTS --json title,body,reviews,comments,reviewDecision

# Get specific review comments
gh api repos/{owner}/{repo}/pulls/{pr-number}/comments

# Get the diff
gh pr diff $ARGUMENTS
```

### Step 2: Categorize Feedback

Organize feedback by type and priority:

```markdown
## PR Feedback Summary

### Blocking (Must Fix)
- [ ] [Reviewer]: "[Comment]" - File: `path/to/file.ts:L42`
- [ ] [Reviewer]: "[Comment]" - File: `path/to/other.ts:L15`

### Suggestions (Should Consider)
- [ ] [Reviewer]: "[Comment]" - File: `path/to/file.ts:L78`

### Questions (Need Response)
- [ ] [Reviewer]: "[Question]" - Will respond with [answer/clarification]

### Nitpicks (Optional)
- [ ] [Reviewer]: "[Comment]" - Will/Won't address because [reason]
```

### Step 3: Address Each Item

For each piece of feedback:

#### Code Changes
```typescript
// Before: (code that received feedback)
function originalCode() {
  // Implementation that needs change
}

// After: (updated code addressing feedback)
function updatedCode() {
  // Implementation with requested changes
  // Addresses review comment about [topic]
}
```

#### Responding to Comments
```markdown
## Response Template

**For code changes:**
> [Original comment]

Fixed in [commit SHA]. Changed [what was changed] to [new approach] because [reasoning].

**For questions:**
> [Original question]

[Clear answer with context]. [Optional: link to documentation or code]

**For disagreements (respectful pushback):**
> [Original suggestion]

I considered this approach, but chose [current approach] because:
1. [Reason 1]
2. [Reason 2]

Happy to discuss further or change if you feel strongly about this.
```

### Step 4: Make Changes

Apply all accepted changes:

```bash
# Ensure you're on the PR branch
gh pr checkout $ARGUMENTS

# Make the changes
# ... edit files ...

# Stage and commit with descriptive message
git add -A
git commit -m "address PR feedback

- Fix [issue 1] per [reviewer] feedback
- Update [component] to [change]
- Add [missing item] as suggested

Addresses review comments on PR #$ARGUMENTS"
```

### Step 5: Re-run Validation

Ensure changes don't break anything:

```bash
# Run tests
npm run test

# Type check
npm run typecheck

# Lint (with auto-fix for style issues)
npm run lint -- --fix

# Build
npm run build
```

### Step 6: Push and Request Re-review

```bash
# Push the changes
git push

# Request re-review from reviewers
gh pr review $ARGUMENTS --request-review reviewer1,reviewer2

# Or add a comment requesting re-review
gh pr comment $ARGUMENTS --body "Addressed all feedback. Ready for re-review.

Changes made:
- [Summary of change 1]
- [Summary of change 2]
- [Summary of change 3]"
```

## Common Feedback Patterns

### Style/Formatting Issues
```bash
# Usually auto-fixable
npm run lint -- --fix
npm run format
```

### Missing Tests
```typescript
// Add tests for the feedback
describe('[Component/Function]', () => {
  it('should [behavior mentioned in feedback]', () => {
    // Test implementation
  });
});
```

### Type Safety Concerns
```typescript
// Before: loose typing
function process(data: any) { ... }

// After: strict typing
interface ProcessInput {
  field1: string;
  field2: number;
}
function process(data: ProcessInput) { ... }
```

### Error Handling
```typescript
// Before: missing error handling
async function fetchData() {
  const response = await api.get('/data');
  return response.data;
}

// After: proper error handling
async function fetchData() {
  try {
    const response = await api.get('/data');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw new DataFetchError(`Failed to fetch data: ${error.message}`);
    }
    throw error;
  }
}
```

### Performance Concerns
```typescript
// Before: inefficient
const result = items.filter(x => x.active).map(x => x.name);

// After: optimized (single pass)
const result = items.reduce((acc, x) => {
  if (x.active) acc.push(x.name);
  return acc;
}, []);
```

### Documentation
```typescript
// Before: no documentation
function complexFunction(input: Input): Output { ... }

// After: with JSDoc
/**
 * Processes the input according to [business rule].
 *
 * @param input - The input data to process
 * @returns Processed output ready for [next step]
 * @throws {ValidationError} If input is invalid
 * @example
 * const result = complexFunction({ field: 'value' });
 */
function complexFunction(input: Input): Output { ... }
```

## Response Templates

### Agreeing with Feedback
```
Good catch! Fixed in [commit]. Thanks for the review.
```

### Clarifying Intent
```
The reason I did it this way is [explanation]. However, I see your point about [their concern]. I've updated it to [new approach] which addresses both concerns.
```

### Respectful Disagreement
```
I understand the suggestion to [their approach]. I chose [current approach] because:
- [Reason 1]
- [Reason 2]

That said, I'm open to changing it if you feel strongly. What do you think?
```

### Deferring to Future PR
```
Great suggestion! I'd like to address this in a follow-up PR to keep this one focused. Created issue #[number] to track it.
```

## Output Expectations

After running `/fix-pr`, you should have:

1. **Categorized Feedback** - All comments organized by priority
2. **Addressed Changes** - Code updated per feedback
3. **Responses Ready** - Comment replies drafted
4. **Tests Pass** - All validations green
5. **Ready for Re-review** - PR updated and reviewers notified
