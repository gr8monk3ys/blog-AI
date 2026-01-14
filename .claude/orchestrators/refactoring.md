---
name: refactoring-workflow
type: orchestrator
description: Safe, systematic refactoring with analysis, planning, execution, and verification to improve code quality without breaking functionality
triggers:
  - "refactor"
  - "improve code"
  - "clean up"
  - "reduce technical debt"
  - "restructure"
---

# Refactoring Workflow Orchestrator

Safely refactors code through systematic analysis, planning, and verification.

## Workflow Overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   ANALYZE    │───▶│     PLAN     │───▶│   EXECUTE    │───▶│   VERIFY     │
│              │    │              │    │              │    │              │
│ Find issues  │    │ Design fix   │    │ Apply changes│    │ Test & review│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

## Stage 1: Analysis

### Agent Collaboration
**Primary**: `code-reviewer`
**Support**: `performance-profiler`

### Analysis Checklist

```markdown
## Code Analysis Report

### Code Smells Detected

#### Complexity Issues
- [ ] Long methods (>50 lines)
- [ ] Deep nesting (>3 levels)
- [ ] High cyclomatic complexity (>10)
- [ ] God classes (>500 lines)

#### Duplication
- [ ] Copy-paste code blocks
- [ ] Similar logic in multiple places
- [ ] Repeated patterns that could be abstracted

#### Design Issues
- [ ] Tight coupling between modules
- [ ] Circular dependencies
- [ ] Incorrect abstraction levels
- [ ] Violation of SOLID principles

#### Naming Issues
- [ ] Unclear variable names
- [ ] Inconsistent naming conventions
- [ ] Misleading names

#### Performance Concerns
- [ ] Unnecessary re-renders
- [ ] Missing memoization
- [ ] N+1 queries
- [ ] Large bundle size contributors
```

### Analysis Output

```markdown
## Analysis: [Scope]

### Summary
- Files analyzed: X
- Issues found: Y
- Priority breakdown: [Critical: X, High: Y, Medium: Z]

### Refactoring Candidates

#### Critical (Must Fix)
1. **[file:line]** [Issue description]
   - Smell: [Type]
   - Impact: [Description]
   - Effort: [Low/Medium/High]

#### High Priority
1. **[file:line]** [Issue description]
   ...

#### Medium Priority
1. **[file:line]** [Issue description]
   ...

### Dependency Map
```
ModuleA
├── depends on: ModuleB, ModuleC
└── depended by: ModuleD

ModuleB (circular!)
├── depends on: ModuleA
└── ...
```

### Metrics
- Average complexity: X
- Duplication ratio: Y%
- Test coverage: Z%
```

## Stage 2: Planning

### Agent
**Primary**: `refactoring-expert`
**Support**: `system-architect`

### Planning Principles

1. **Small, Incremental Changes**: Each step should be independently testable
2. **Behavior Preservation**: Tests must pass after each step
3. **Reversibility**: Each change can be rolled back
4. **Prioritization**: Fix highest impact issues first

### Refactoring Patterns to Apply

```markdown
## Common Refactoring Patterns

### Extract Method
Before:
```typescript
function processOrder(order: Order) {
  // 50 lines of validation
  // 30 lines of calculation
  // 20 lines of persistence
}
```

After:
```typescript
function processOrder(order: Order) {
  validateOrder(order);
  const total = calculateTotal(order);
  persistOrder(order, total);
}
```

### Extract Component
Before:
```tsx
function Dashboard() {
  return (
    <div>
      {/* 100 lines of user stats */}
      {/* 80 lines of activity feed */}
      {/* 60 lines of notifications */}
    </div>
  );
}
```

After:
```tsx
function Dashboard() {
  return (
    <div>
      <UserStats />
      <ActivityFeed />
      <Notifications />
    </div>
  );
}
```

### Replace Conditional with Polymorphism
Before:
```typescript
function getPrice(type: string, base: number) {
  if (type === 'premium') return base * 1.5;
  if (type === 'basic') return base;
  if (type === 'free') return 0;
}
```

After:
```typescript
const pricingStrategies = {
  premium: (base) => base * 1.5,
  basic: (base) => base,
  free: () => 0,
};

function getPrice(type: PricingTier, base: number) {
  return pricingStrategies[type](base);
}
```

### Introduce Parameter Object
Before:
```typescript
function createUser(
  name: string,
  email: string,
  password: string,
  role: string,
  department: string,
  managerId: string
) { ... }
```

After:
```typescript
interface CreateUserParams {
  name: string;
  email: string;
  password: string;
  role: string;
  department: string;
  managerId?: string;
}

function createUser(params: CreateUserParams) { ... }
```
```

### Refactoring Plan Format

```markdown
## Refactoring Plan: [Scope]

### Goals
1. [Goal 1]
2. [Goal 2]

### Approach
[High-level description]

### Steps (in order)

#### Step 1: [Description]
- **Target**: [file:function/class]
- **Pattern**: [Refactoring pattern name]
- **Changes**:
  - Extract X to new function Y
  - Rename Z to W
- **Tests to verify**:
  - [ ] Existing test suite passes
  - [ ] New unit test for extracted function
- **Rollback**: Delete new function, restore original

#### Step 2: [Description]
...

### Risk Assessment
- **Breaking change risk**: [Low/Medium/High]
- **Data migration needed**: [Yes/No]
- **Deployment considerations**: [Notes]

### Success Criteria
- [ ] All tests pass
- [ ] No new type errors
- [ ] Code coverage maintained or improved
- [ ] Performance not degraded
```

## Stage 3: Execution

### Agent
**Primary**: `refactoring-expert`

### Execution Protocol

```typescript
interface RefactoringStep {
  id: string;
  description: string;
  files: string[];
  testCommand: string;
  rollbackPlan: string;
}

async function executeRefactoring(steps: RefactoringStep[]) {
  const completed: string[] = [];

  for (const step of steps) {
    console.log(`Executing step: ${step.description}`);

    try {
      // 1. Make changes
      await applyChanges(step);

      // 2. Run tests immediately
      const testResult = await runTests(step.testCommand);

      if (!testResult.success) {
        // 3. Rollback on failure
        await rollback(step);
        throw new Error(`Tests failed after step: ${step.id}`);
      }

      // 4. Record success
      completed.push(step.id);
      console.log(`✓ Step ${step.id} complete`);

    } catch (error) {
      // Rollback all completed steps if needed
      console.error(`Failed at step ${step.id}:`, error);
      return { success: false, completedSteps: completed, failedStep: step.id };
    }
  }

  return { success: true, completedSteps: completed };
}
```

### Change Documentation

After each step:
```markdown
## Change Log

### Step 1: Extract calculateTotal function
- **Files modified**: `lib/orders.ts`
- **Lines changed**: +15, -45
- **Tests**: All 23 passing
- **Commit**: abc123

### Step 2: Introduce OrderProcessor class
- **Files modified**: `lib/orders.ts`, `lib/types.ts`
- **Lines changed**: +60, -80
- **Tests**: All 27 passing (4 new)
- **Commit**: def456
```

## Stage 4: Verification

### Agent Collaboration
**Primary**: `test-strategist`
**Support**: `code-reviewer`

### Verification Checklist

```markdown
## Verification Report

### Test Results
- **Before refactoring**: X tests passing
- **After refactoring**: Y tests passing
- **New tests added**: Z

### Behavior Verification
- [ ] All existing tests pass
- [ ] No new type errors
- [ ] No console errors/warnings
- [ ] No runtime exceptions

### Quality Metrics
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Complexity | X | Y | -Z% |
| Duplication | X% | Y% | -Z% |
| Coverage | X% | Y% | +Z% |
| Bundle size | X KB | Y KB | -Z KB |

### Performance Verification
- [ ] No performance regression
- [ ] Load times acceptable
- [ ] Memory usage stable

### Code Review
- [ ] Changes follow project patterns
- [ ] New code is well-documented
- [ ] No new technical debt introduced
```

### Final Report

```markdown
## Refactoring Complete: [Scope]

### Summary
- **Steps completed**: X/Y
- **Files modified**: Z
- **Lines changed**: +A, -B (net: -C)

### Improvements
1. Reduced complexity in OrderProcessor by 40%
2. Eliminated 3 instances of duplicated validation logic
3. Extracted reusable hooks for data fetching

### Test Impact
- Added 12 new unit tests
- Coverage increased from 75% to 82%

### Remaining Items
- [ ] Consider further extraction of payment logic
- [ ] Document new patterns in ADR

### Commits
1. `abc123` - Extract calculateTotal function
2. `def456` - Introduce OrderProcessor class
3. `ghi789` - Remove duplicated validation
```

## Usage Examples

### Example 1: Component Refactoring

```
User: "The Dashboard component is too large and hard to maintain"

Analysis:
- Dashboard.tsx: 800 lines
- 5 distinct feature areas
- No component extraction
- Mixed concerns

Plan:
1. Extract UserStats component (lines 50-200)
2. Extract ActivityFeed component (lines 201-400)
3. Extract Notifications component (lines 401-550)
4. Extract shared hooks
5. Clean up Dashboard as orchestrator

Execute:
- Step-by-step extraction with tests after each

Verify:
- All tests pass
- No visual regression
- Performance maintained
```

### Example 2: API Refactoring

```
User: "Our API handlers have a lot of duplicated error handling"

Analysis:
- 15 route handlers with similar try/catch
- Inconsistent error response format
- No centralized error handling

Plan:
1. Create ErrorHandler utility
2. Create typed error classes
3. Extract common middleware
4. Update handlers one by one

Execute:
- Create utilities first
- Migrate handlers incrementally
- Add tests for new error handling

Verify:
- All endpoints return consistent errors
- Error logging improved
- Code reduced by 200 lines
```

## Boundaries

**This orchestrator handles:**
- Code cleanup and restructuring
- Pattern application
- Technical debt reduction
- Safe, incremental changes

**This orchestrator does NOT handle:**
- Feature additions (use fullstack-feature)
- Bug fixes (use simpler flows)
- Architecture redesign (use system-architect directly)
- Database schema changes (use migration-safety skill)
