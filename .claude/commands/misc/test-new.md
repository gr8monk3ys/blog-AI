---
description: Generate test files for Jest, Vitest, or Playwright
model: claude-opus-4-5
---

Generate a comprehensive test file for the specified code.

## Test Target

$ARGUMENTS

## Options (if not specified above, ask or use defaults)

| Option | Choices | Default |
|--------|---------|---------|
| **Framework** | Jest, Vitest, Playwright | Auto-detect from project |
| **Test Type** | Unit, Integration, E2E | Unit for functions, Integration for components |
| **Coverage** | Happy path only, Full coverage | Full coverage |
| **Mocking** | Mock externals, Use real implementations | Mock externals |

If the test framework is unclear, ask: "Which testing framework should I use: Jest, Vitest, or Playwright?"

## Testing Framework Selection

Automatically detect or ask which framework to use:
- **Jest** - Popular React/Node.js testing (most common)
- **Vitest** - Fast Vite-native testing framework
- **Playwright** - E2E and browser testing

## Test File Structure

### Unit/Integration Tests (Jest/Vitest)

```typescript
import { describe, it, expect, beforeEach, afterEach } from '@testing-library/jest-dom' // or vitest
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ComponentName } from './ComponentName'

describe('ComponentName', () => {
  beforeEach(() => {
    // Setup before each test
  })

  afterEach(() => {
    // Cleanup after each test
  })

  describe('Feature: Core Functionality', () => {
    it('should render with default props', () => {
      // Arrange
      // Act
      // Assert
    })

    it('should handle user interactions', async () => {
      // Test user interactions
    })
  })

  describe('Feature: Edge Cases', () => {
    it('should handle error states', () => {
      // Test error handling
    })

    it('should handle loading states', () => {
      // Test loading states
    })
  })
})
```

### E2E Tests (Playwright)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to page or setup state
    await page.goto('/path')
  })

  test('should complete user flow successfully', async ({ page }) => {
    // Arrange
    // Act
    // Assert
  })

  test('should handle errors gracefully', async ({ page }) => {
    // Test error scenarios
  })
})
```

## Test Coverage Guidelines

### What to Test

**Components**:
- ✅ Rendering with different props
- ✅ User interactions (clicks, typing, etc.)
- ✅ State changes and updates
- ✅ Error boundaries and error states
- ✅ Loading and empty states
- ✅ Accessibility (a11y) requirements

**Functions/Utils**:
- ✅ Expected inputs and outputs
- ✅ Edge cases (null, undefined, empty)
- ✅ Error conditions
- ✅ Type safety validation

**API Routes**:
- ✅ Success responses with valid data
- ✅ Error responses (400, 401, 404, 500)
- ✅ Input validation
- ✅ Authentication/authorization
- ✅ Rate limiting

**E2E Flows**:
- ✅ Happy path user journeys
- ✅ Form submissions and validation
- ✅ Navigation and routing
- ✅ Error handling and recovery

### What NOT to Test

- ❌ Third-party library internals
- ❌ Browser APIs
- ❌ Framework internals (React, Next.js)
- ❌ Implementation details (internal state, private methods)
- ❌ Styling/CSS (unless critical to functionality)

## Best Practices

### Test Organization
- Use `describe` blocks to group related tests
- Use clear, descriptive test names: "should [expected behavior] when [condition]"
- Follow Arrange-Act-Assert pattern
- One assertion per test when possible

### Test Data
- Use factories or fixtures for complex test data
- Mock external dependencies (APIs, databases)
- Use meaningful test data that reflects real usage

### Mocking
```typescript
// Mock external modules
vi.mock('./api', () => ({
  fetchUser: vi.fn()
}))

// Mock implementation
const mockFetchUser = vi.mocked(fetchUser)
mockFetchUser.mockResolvedValue({ id: 1, name: 'Test' })
```

### Async Testing
```typescript
// Wait for elements
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Wait for async operations
await expect(asyncFunction()).resolves.toBe(expected)
```

### Accessibility Testing
```typescript
// Check for accessible names
expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument()

// Check ARIA attributes
expect(button).toHaveAttribute('aria-label', 'Close dialog')
```

## Test Utilities

### Common Testing Library Queries (Preferred Order)
1. `getByRole` - Most accessible
2. `getByLabelText` - Form elements
3. `getByPlaceholderText` - Inputs
4. `getByText` - Non-interactive elements
5. `getByTestId` - Last resort

### User Event Simulation
```typescript
import { userEvent } from '@testing-library/user-event'

const user = userEvent.setup()
await user.click(button)
await user.type(input, 'text')
await user.selectOptions(select, 'value')
```

## Output Format

Generate:
1. **Test File** - Complete test file with proper imports
2. **Test Cases** - Comprehensive coverage of functionality
3. **Mocks** - Necessary mocks for external dependencies
4. **Setup/Teardown** - beforeEach/afterEach when needed
5. **Comments** - Explain complex test logic

## File Naming Conventions

- Unit/Integration: `ComponentName.test.ts(x)` or `ComponentName.spec.ts(x)`
- E2E: `feature-name.e2e.ts` or `feature-name.spec.ts`
- Place tests alongside source files or in `__tests__` directory

## Code Quality

- ✅ TypeScript strict typing (no `any`)
- ✅ Proper async/await handling
- ✅ Clean up side effects
- ✅ Avoid test interdependence
- ✅ Keep tests fast and focused
- ✅ Use descriptive variable names

Generate production-ready, comprehensive test files that follow testing best practices and provide confidence in code quality.
