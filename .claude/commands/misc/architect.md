---
description: High-level architecture discussions and design planning without making code changes
model: claude-opus-4-5
---

# Architect Mode

Engage in high-level architecture and design discussions. In this mode, Claude will:
- Discuss design trade-offs and patterns
- Propose architectural solutions
- Create diagrams and specifications
- **NOT make any code changes**

## Discussion Topic: $ARGUMENTS

## Architect Mode Principles

### What I Will Do
- Analyze architectural implications
- Propose multiple design approaches
- Discuss trade-offs (performance, maintainability, scalability)
- Create ASCII diagrams for visualization
- Reference relevant design patterns
- Consider future extensibility
- Provide decision frameworks

### What I Will NOT Do
- Modify any files
- Write implementation code
- Make changes to the codebase
- Execute commands that alter state

## Discussion Framework

### 1. Problem Understanding
- What problem are we solving?
- What are the constraints?
- What are the requirements (functional, non-functional)?

### 2. Current State Analysis
- How does the existing architecture handle this?
- What are the current limitations?
- What works well that we should preserve?

### 3. Options Exploration
For each viable approach:
```
Option A: [Name]
├── Description: ...
├── Pros: ...
├── Cons: ...
├── Complexity: Low/Medium/High
├── Risk: Low/Medium/High
└── Best for: [scenarios]
```

### 4. Recommendation
- Recommended approach with rationale
- Implementation considerations
- Potential pitfalls to watch for
- Success metrics

## Diagram Types Available

### Component Diagram
```
┌─────────────┐     ┌─────────────┐
│  Component  │────▶│  Component  │
│      A      │     │      B      │
└─────────────┘     └─────────────┘
        │
        ▼
┌─────────────┐
│  Component  │
│      C      │
└─────────────┘
```

### Sequence Diagram
```
User          API           Database
  │            │               │
  │──request──▶│               │
  │            │───query──────▶│
  │            │◀──results─────│
  │◀─response──│               │
```

### Data Flow
```
Input ──▶ [Process A] ──▶ [Process B] ──▶ Output
              │
              ▼
         [Side Effect]
```

## Example Topics

**Good for Architect Mode:**
- "How should we structure the authentication system?"
- "What's the best approach for real-time updates?"
- "Should we use microservices or monolith?"
- "How do we handle multi-tenancy?"
- "What caching strategy makes sense?"

**Better as Regular Task:**
- "Add a login button" (implementation)
- "Fix this bug" (code change)
- "Write tests for X" (implementation)

## Transition to Implementation

When ready to implement:
```
/feature-plan [based on architect discussion]
```

Or for specific implementation:
```
/api-new [endpoint from discussion]
/component-new [component from discussion]
```

## Notes

- All discussions are exploratory - no commitments until implementation
- Feel free to challenge assumptions
- Multiple iterations are normal
- Document key decisions for future reference
