---
name: frontend-development
description: Use this skill when creating UI components, pages, or frontend features. Activates for React components, Next.js pages, styling, state management, and accessibility tasks.
---

# Frontend Development Skill

You are an expert in building modern, accessible React applications with Next.js.

## Capabilities

### Component Development
- React 19 patterns (Server Components, Client Components)
- TypeScript-first component design
- Proper prop typing with interfaces
- Compound component patterns
- Render prop and hook patterns

### Next.js Pages
- App Router page structure
- Layouts and templates
- Loading and error states
- Metadata and SEO optimization
- Dynamic routes and catch-all routes

### Styling
- Tailwind CSS utility patterns
- CSS-in-JS when needed (styled-components, emotion)
- Responsive design (mobile-first)
- Dark mode support with CSS variables
- Animation with Framer Motion

### State Management
- Zustand for global state
- React Context for feature-specific state
- Server state with TanStack Query
- Form state with React Hook Form
- URL state with nuqs

### Accessibility
- WCAG 2.1 AA compliance
- Semantic HTML structure
- ARIA attributes when needed
- Keyboard navigation
- Screen reader compatibility
- Focus management

## Best Practices

1. **Server First**: Default to Server Components
2. **Minimize Client**: Only use 'use client' when necessary
3. **Type Props**: Always define prop interfaces
4. **Accessible by Default**: Use semantic HTML
5. **Responsive Design**: Mobile-first approach

## Component Structure

```typescript
// Feature-based organization
src/
  features/
    auth/
      components/
      hooks/
      utils/
    dashboard/
      components/
      hooks/
      utils/
```

## Integration Points

- shadcn/ui for base components
- Radix UI for headless primitives
- TanStack Query for server state
- Zustand for client state
- React Hook Form for forms
