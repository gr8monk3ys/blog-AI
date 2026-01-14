---
description: Test-Driven Development workflow with Red-Green-Refactor discipline
model: claude-sonnet-4-5
---

# Test-Driven Development

Implement features using strict TDD methodology: Red → Green → Refactor.

## Feature to Implement: $ARGUMENTS

## TDD Workflow

### Phase 1: RED - Write Failing Tests First

Before writing ANY implementation code, create tests that define the expected behavior:

```typescript
// Example test structure
describe('Feature: $ARGUMENTS', () => {
  describe('when [scenario]', () => {
    it('should [expected behavior]', () => {
      // Arrange
      const input = /* test input */;

      // Act
      const result = /* call the function/method */;

      // Assert
      expect(result).toBe(/* expected output */);
    });

    it('should handle edge case: [description]', () => {
      // Test edge cases
    });

    it('should throw error when [invalid condition]', () => {
      // Test error handling
    });
  });
});
```

**Test Categories to Consider:**
1. **Happy Path** - Normal successful operation
2. **Edge Cases** - Boundary conditions, empty inputs, max values
3. **Error Cases** - Invalid inputs, missing data, failures
4. **Integration** - Interaction with dependencies

### Phase 2: GREEN - Minimal Implementation

Write the MINIMUM code needed to make tests pass:

```typescript
// Implementation rules:
// 1. Only write code to pass the current failing test
// 2. No premature optimization
// 3. No extra features "while you're at it"
// 4. Keep it simple and obvious

function featureName(input: InputType): OutputType {
  // Minimal implementation to pass tests
}
```

**Green Phase Checklist:**
- [ ] All tests pass
- [ ] No new functionality beyond test requirements
- [ ] Code compiles without errors
- [ ] No skipped or commented-out tests

### Phase 3: REFACTOR - Improve Without Breaking

With green tests as safety net, improve code quality:

```typescript
// Refactoring targets:
// - Remove duplication (DRY)
// - Improve naming
// - Extract functions/methods
// - Simplify conditionals
// - Optimize performance (if needed)

// IMPORTANT: Run tests after EVERY change
```

**Refactoring Checklist:**
- [ ] Tests still pass after each change
- [ ] No behavior changes (tests prove this)
- [ ] Code is more readable
- [ ] No new functionality added

## Test File Structure

### Jest/Vitest Setup
```typescript
// __tests__/feature.test.ts or feature.test.ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { featureName } from '../src/feature';

describe('featureName', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
  });

  // Tests organized by scenario
});
```

### React Component Testing
```typescript
// ComponentName.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  it('renders correctly', () => {
    render(<ComponentName />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    render(<ComponentName />);
    await fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Updated')).toBeInTheDocument();
  });
});
```

### API Route Testing
```typescript
// api/endpoint.test.ts
import { POST } from './route';
import { NextRequest } from 'next/server';

describe('POST /api/endpoint', () => {
  it('returns 200 for valid request', async () => {
    const request = new NextRequest('http://localhost/api/endpoint', {
      method: 'POST',
      body: JSON.stringify({ data: 'test' })
    });

    const response = await POST(request);
    expect(response.status).toBe(200);
  });

  it('returns 400 for invalid request', async () => {
    const request = new NextRequest('http://localhost/api/endpoint', {
      method: 'POST',
      body: JSON.stringify({})
    });

    const response = await POST(request);
    expect(response.status).toBe(400);
  });
});
```

## TDD Cycle Commands

```bash
# Run tests in watch mode
npm run test -- --watch

# Run specific test file
npm run test -- feature.test.ts

# Run with coverage
npm run test -- --coverage

# Run only failed tests
npm run test -- --onlyFailures
```

## Best Practices

### Test Naming Convention
```typescript
// Pattern: "should [expected behavior] when [condition]"
it('should return empty array when input is empty', () => {});
it('should throw ValidationError when email is invalid', () => {});
it('should update state when button is clicked', () => {});
```

### Arrange-Act-Assert (AAA) Pattern
```typescript
it('should calculate total correctly', () => {
  // Arrange - Set up test data
  const items = [{ price: 10 }, { price: 20 }];

  // Act - Execute the code under test
  const total = calculateTotal(items);

  // Assert - Verify the result
  expect(total).toBe(30);
});
```

### Mock External Dependencies
```typescript
// Mock API calls
vi.mock('../lib/api', () => ({
  fetchData: vi.fn().mockResolvedValue({ data: 'mocked' })
}));

// Mock environment
vi.stubEnv('API_KEY', 'test-key');

// Mock timers
vi.useFakeTimers();
vi.advanceTimersByTime(1000);
```

## Output Expectations

After running `/tdd`, you should have:

1. **Test File** - Comprehensive tests covering:
   - Happy path scenarios
   - Edge cases
   - Error handling
   - Integration points

2. **Implementation** - Minimal code that:
   - Makes all tests pass
   - Follows project conventions
   - Is type-safe (no `any`)

3. **Refactored Code** - Clean implementation:
   - DRY (no duplication)
   - Clear naming
   - Proper abstractions

## TDD Mantras

1. **"Red, Green, Refactor"** - Never skip a phase
2. **"Write the test you wish you had"** - Tests define requirements
3. **"Make it work, make it right, make it fast"** - In that order
4. **"Test behavior, not implementation"** - Tests shouldn't break when refactoring
5. **"If you can't test it, you can't ship it"** - Untested code is broken code
