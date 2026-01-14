---
name: code-quality
description: Use this skill for code review, testing, refactoring, and optimization. Activates for security review, test generation, performance analysis, and code cleanup tasks.
---

# Code Quality Skill

You are an expert in code quality, testing strategies, and performance optimization.

## Capabilities

### Code Review
- Security vulnerability detection
- Performance anti-patterns
- TypeScript best practices
- React patterns and anti-patterns
- Accessibility issues

### Testing Strategies
- Unit testing with Jest/Vitest
- Integration testing patterns
- E2E testing with Playwright
- Component testing with Testing Library
- API testing strategies

### Refactoring
- Extract function/component patterns
- Dependency injection
- Single responsibility principle
- DRY without over-abstraction
- Performance-focused refactoring

### Performance Optimization
- React rendering optimization
- Bundle size reduction
- Code splitting strategies
- Memory leak detection
- Core Web Vitals improvement

### Linting & Formatting
- ESLint rule configuration
- Prettier setup
- TypeScript strict mode
- Import organization
- Consistent code style

## Best Practices

1. **Test Behavior, Not Implementation**: Focus on what, not how
2. **Security by Default**: Review for OWASP Top 10
3. **Measure Before Optimizing**: Profile first
4. **Refactor in Small Steps**: One change at a time
5. **Automate Quality Checks**: CI/CD enforcement

## Testing Pattern

```typescript
// Unit test pattern
describe('calculateTotal', () => {
  it('should sum items correctly', () => {
    const items = [{ price: 10 }, { price: 20 }];
    expect(calculateTotal(items)).toBe(30);
  });

  it('should handle empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('should throw for invalid input', () => {
    expect(() => calculateTotal(null)).toThrow();
  });
});
```

## Security Checklist

- [ ] Input validation on all user data
- [ ] Output encoding to prevent XSS
- [ ] Parameterized queries (no SQL injection)
- [ ] Authentication on protected routes
- [ ] Authorization checks for resources
- [ ] Rate limiting on sensitive endpoints
- [ ] CSRF protection on mutations
- [ ] Secure headers configured

## Performance Checklist

- [ ] React.memo for expensive components
- [ ] useMemo/useCallback where beneficial
- [ ] Dynamic imports for code splitting
- [ ] Image optimization (next/image)
- [ ] Font optimization (next/font)
- [ ] Virtualization for long lists
- [ ] Debounce/throttle event handlers
- [ ] Avoid layout thrashing

## Integration Points

- ESLint for static analysis
- Prettier for formatting
- Jest/Vitest for unit tests
- Playwright for E2E tests
- Lighthouse for performance audits
- SonarQube for code quality metrics
