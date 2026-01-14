---
name: api-development
description: Use this skill when creating, testing, or securing API endpoints. Activates for REST API routes, authentication, rate limiting, and API documentation tasks.
---

# API Development Skill

You are an expert in building production-ready REST APIs with Next.js App Router.

## Capabilities

### Route Creation
- App Router API routes (`app/api/*/route.ts`)
- Proper HTTP method handlers (GET, POST, PUT, PATCH, DELETE)
- Request/response typing with TypeScript
- Edge Runtime compatibility when needed

### Validation & Error Handling
- Zod schema validation for all inputs
- Structured error responses with proper HTTP status codes
- Input sanitization and type coercion
- Comprehensive error messages for debugging

### Authentication & Authorization
- JWT and session-based auth patterns
- Middleware-based protection
- Role-based access control (RBAC)
- API key authentication for external services

### Rate Limiting
- Upstash Redis rate limiting
- Sliding window and fixed window strategies
- IP-based and user-based limiting
- Graceful degradation

### Testing
- API route unit tests with Jest/Vitest
- Integration tests with supertest patterns
- Mock strategies for external services
- Test coverage for edge cases

## Best Practices

1. **Validate Early**: Use Zod at route entry points
2. **Type Everything**: Never use `any` types
3. **Handle Errors Consistently**: Use structured error format
4. **Document Inline**: JSDoc comments for complex logic
5. **Consider Edge Runtime**: Avoid Node.js-specific APIs when possible

## Response Format

```typescript
// Success
{ data: T, meta?: { pagination, etc } }

// Error
{ error: { code: string, message: string, details?: unknown } }
```

## Integration Points

- Supabase for database operations
- NextAuth.js for authentication
- Upstash for rate limiting and caching
- Zod for validation schemas
