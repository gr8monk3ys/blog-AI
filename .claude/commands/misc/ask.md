---
description: Ask questions about the codebase without making any changes - pure exploration and learning
model: claude-sonnet-4-5
---

# Ask Mode

Ask questions about the codebase. In this mode, Claude will:
- Answer questions about how code works
- Explain patterns and implementations
- Find relevant code sections
- **NOT make any code changes**

## Question: $ARGUMENTS

## Ask Mode Principles

### What I Will Do
- Read and analyze code
- Search for patterns and implementations
- Explain how things work
- Find connections between components
- Trace data flow
- Identify dependencies
- Answer "why" and "how" questions

### What I Will NOT Do
- Modify any files
- Suggest changes (unless explicitly asked)
- Write new code
- Execute commands that alter state

## Question Types

### How Does X Work?
I'll trace through the code and explain:
- Entry points
- Data transformations
- Key functions/methods
- Dependencies
- Edge cases handled

### Where Is X Defined/Used?
I'll search the codebase and show:
- Definition location
- All usage sites
- Import/export relationships
- Test coverage

### Why Is X Done This Way?
I'll analyze and provide:
- Historical context (if available)
- Technical rationale
- Trade-offs considered
- Alternative approaches

### What Happens When X?
I'll trace the execution path:
- Starting point
- Each step in sequence
- Data transformations
- Final outcome

## Response Format

### For Code Explanations
```
📍 Location: path/to/file.ts:42

📝 Summary:
[Brief explanation]

🔍 Details:
[Detailed walkthrough]

🔗 Related:
- Related file A
- Related file B
```

### For Searches
```
Found X occurrences:

1. path/to/file.ts:42
   [Context snippet]

2. path/to/other.ts:88
   [Context snippet]
```

### For Architectural Questions
```
Overview:
[High-level explanation]

Components Involved:
- Component A: [role]
- Component B: [role]

Data Flow:
[Step-by-step flow]
```

## Example Questions

**Understanding Code:**
- "How does authentication work in this project?"
- "What happens when a user submits the form?"
- "How are API errors handled?"

**Finding Things:**
- "Where is the User type defined?"
- "What files use the database connection?"
- "Where are environment variables loaded?"

**Learning:**
- "Why do we use Zustand instead of Redux?"
- "What pattern is used for API calls?"
- "How is validation handled?"

## Transition to Action

When ready to make changes:
```
# For specific implementations
/api-new [endpoint]
/component-new [component]

# For planned changes
/feature-plan [feature]

# For architecture discussions
/architect [topic]
```

## Notes

- No question is too basic
- I'll search thoroughly before answering
- I'll admit when I'm uncertain
- I'll point to relevant documentation
