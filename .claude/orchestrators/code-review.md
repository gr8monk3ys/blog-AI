---
name: code-review-workflow
type: orchestrator
description: Multi-perspective code review covering security, performance, quality, and accessibility with parallel agent execution
triggers:
  - "review code"
  - "code review"
  - "PR review"
  - "review changes"
---

# Code Review Workflow Orchestrator

Performs comprehensive code review from multiple expert perspectives.

## Workflow Overview

```
                    ┌──────────────────┐
                    │   CODE CHANGES   │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    SECURITY     │ │   PERFORMANCE   │ │    QUALITY      │
│    ENGINEER     │ │    ENGINEER     │ │    REVIEWER     │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   AGGREGATION    │
                    │   & REPORTING    │
                    └──────────────────┘
```

## Parallel Review Stages

### Security Review
**Agent**: `security-engineer`
**Priority**: Critical

**Checks**:
```markdown
## Security Checklist

### Input Validation
- [ ] All user inputs validated
- [ ] Zod/Yup schemas for API inputs
- [ ] File upload restrictions enforced
- [ ] SQL/NoSQL injection prevented

### Authentication & Authorization
- [ ] Auth checks on all protected routes
- [ ] JWT tokens properly validated
- [ ] Session management secure
- [ ] RBAC correctly implemented

### Data Protection
- [ ] Sensitive data not logged
- [ ] Passwords properly hashed (bcrypt/argon2)
- [ ] PII handling compliant
- [ ] Secrets not in code

### OWASP Top 10
- [ ] Injection (A03)
- [ ] Broken Auth (A07)
- [ ] Sensitive Data Exposure (A02)
- [ ] XXE (A05)
- [ ] Broken Access Control (A01)
- [ ] Security Misconfiguration (A05)
- [ ] XSS (A03)
- [ ] Insecure Deserialization (A08)
- [ ] Vulnerable Components (A06)
- [ ] Insufficient Logging (A09)
```

**Output Format**:
```markdown
## Security Review: [PR/Files]

### Critical Issues (Must Fix)
- **[FILE:LINE]** [Description]
  - Risk: [High/Critical]
  - Fix: [Suggested fix]

### Important Issues (Should Fix)
- **[FILE:LINE]** [Description]

### Informational
- [Observations and suggestions]

### Security Score: [A-F]
```

### Performance Review
**Agent**: `performance-engineer`
**Priority**: High

**Checks**:
```markdown
## Performance Checklist

### Algorithm Complexity
- [ ] No O(n²) or worse in hot paths
- [ ] Appropriate data structures used
- [ ] Memoization for expensive computations

### Database
- [ ] N+1 queries prevented
- [ ] Proper indexes exist
- [ ] Pagination implemented
- [ ] Efficient queries (no SELECT *)

### Frontend
- [ ] Components properly memoized
- [ ] No unnecessary re-renders
- [ ] Images optimized
- [ ] Bundle size impact acceptable

### API
- [ ] Response times acceptable
- [ ] Caching implemented where appropriate
- [ ] Rate limiting considered
```

**Output Format**:
```markdown
## Performance Review: [PR/Files]

### Critical Issues
- **[FILE:LINE]** [Description]
  - Impact: [Latency/Memory/CPU]
  - Suggestion: [Optimization]

### Optimization Opportunities
- [List of improvements]

### Metrics Impact
- Bundle size: +/- X KB
- API latency: +/- X ms
- DB queries: +/- X

### Performance Score: [A-F]
```

### Quality Review
**Agent**: `code-reviewer`
**Priority**: High

**Checks**:
```markdown
## Quality Checklist

### Code Style
- [ ] Consistent naming conventions
- [ ] No magic numbers/strings
- [ ] Functions are focused (single responsibility)
- [ ] Comments explain "why", not "what"

### TypeScript
- [ ] No `any` types
- [ ] Proper type definitions
- [ ] Discriminated unions where appropriate
- [ ] Generics used effectively

### Architecture
- [ ] Follows project patterns
- [ ] Separation of concerns
- [ ] Dependencies flow correctly
- [ ] No circular dependencies

### Testing
- [ ] Tests cover happy path
- [ ] Edge cases tested
- [ ] Error scenarios tested
- [ ] Tests are maintainable

### Maintainability
- [ ] Code is readable
- [ ] Complex logic is documented
- [ ] No dead code
- [ ] No duplicated logic
```

**Output Format**:
```markdown
## Quality Review: [PR/Files]

### Issues Found
- **[FILE:LINE]** [Description]
  - Category: [Style/Architecture/Testing]
  - Suggestion: [Fix]

### Positive Observations
- [Good patterns observed]

### Technical Debt
- [Any debt introduced]

### Quality Score: [A-F]
```

### Accessibility Review (Optional)
**Agent**: `accessibility-auditor`
**Trigger**: Frontend changes detected

**Checks**:
```markdown
## Accessibility Checklist

### Semantic HTML
- [ ] Proper heading hierarchy
- [ ] Semantic elements used (nav, main, article)
- [ ] Lists for list content

### Interactive Elements
- [ ] All clickable with keyboard
- [ ] Focus states visible
- [ ] ARIA labels where needed

### Content
- [ ] Alt text for images
- [ ] Color contrast sufficient
- [ ] Text resizable

### Forms
- [ ] Labels associated with inputs
- [ ] Error messages accessible
- [ ] Required fields indicated
```

## Aggregation & Reporting

### Combined Report Structure

```markdown
# Code Review Report

## Summary
- **Overall Rating**: [A-F]
- **Recommendation**: [Approve/Request Changes/Reject]
- **Critical Issues**: [count]
- **Important Issues**: [count]
- **Suggestions**: [count]

## Security Review
[Security agent output]
**Score**: [A-F]

## Performance Review
[Performance agent output]
**Score**: [A-F]

## Quality Review
[Quality agent output]
**Score**: [A-F]

## Accessibility Review (if applicable)
[Accessibility agent output]
**Score**: [A-F]

## Action Items

### Must Fix Before Merge
1. [Critical issue 1]
2. [Critical issue 2]

### Should Fix
1. [Important issue 1]
2. [Important issue 2]

### Consider for Future
1. [Suggestion 1]
2. [Suggestion 2]

## Positive Highlights
- [Good pattern 1]
- [Good pattern 2]
```

### Scoring Algorithm

```typescript
interface ReviewScore {
  security: Grade;
  performance: Grade;
  quality: Grade;
  accessibility?: Grade;
}

type Grade = 'A' | 'B' | 'C' | 'D' | 'F';

function calculateOverallGrade(scores: ReviewScore): Grade {
  // Security has highest weight
  const weights = {
    security: 0.35,
    performance: 0.25,
    quality: 0.25,
    accessibility: 0.15,
  };

  const gradeValues: Record<Grade, number> = {
    'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0
  };

  let weightedSum = 0;
  let totalWeight = 0;

  for (const [category, weight] of Object.entries(weights)) {
    const grade = scores[category as keyof ReviewScore];
    if (grade) {
      weightedSum += gradeValues[grade] * weight;
      totalWeight += weight;
    }
  }

  const average = weightedSum / totalWeight;

  if (average >= 3.5) return 'A';
  if (average >= 2.5) return 'B';
  if (average >= 1.5) return 'C';
  if (average >= 0.5) return 'D';
  return 'F';
}

function getRecommendation(scores: ReviewScore): string {
  // Any critical security issue = reject
  if (scores.security === 'F') return 'Reject - Critical Security Issues';

  // Multiple low scores = request changes
  const lowScores = Object.values(scores).filter(g => g === 'D' || g === 'F');
  if (lowScores.length >= 2) return 'Request Changes';

  // Security D or any F = request changes
  if (scores.security === 'D' || Object.values(scores).includes('F')) {
    return 'Request Changes';
  }

  return 'Approve';
}
```

## Usage

### Trigger Review

```typescript
async function runCodeReview(context: ReviewContext) {
  // Run parallel reviews
  const [security, performance, quality, accessibility] = await Promise.all([
    runAgent('security-engineer', { mode: 'review', ...context }),
    runAgent('performance-engineer', { mode: 'review', ...context }),
    runAgent('code-reviewer', { mode: 'review', ...context }),
    context.hasFrontendChanges
      ? runAgent('accessibility-auditor', { mode: 'review', ...context })
      : null,
  ]);

  // Aggregate results
  const report = aggregateReviews({
    security,
    performance,
    quality,
    accessibility,
  });

  // Generate recommendation
  const recommendation = getRecommendation(report.scores);

  return {
    report,
    recommendation,
    scores: report.scores,
  };
}
```

## Example Output

```markdown
# Code Review Report

## Summary
- **Overall Rating**: B
- **Recommendation**: Approve with suggestions
- **Critical Issues**: 0
- **Important Issues**: 3
- **Suggestions**: 7

## Security Review
No critical issues found. Minor suggestions for input validation.
**Score**: A

## Performance Review
One N+1 query detected in UserList component.
**Score**: B

## Quality Review
Code follows patterns well. Some opportunities for abstraction.
**Score**: B

## Action Items

### Should Fix
1. `components/UserList.tsx:45` - N+1 query in user posts fetch
2. `lib/api.ts:23` - Consider adding input validation
3. `pages/dashboard.tsx:89` - Extract repeated logic to hook

### Consider for Future
1. Add unit tests for new utility functions
2. Consider memoizing expensive UserCard computation

## Positive Highlights
- Clean component structure
- Good TypeScript usage
- Comprehensive error handling
```
