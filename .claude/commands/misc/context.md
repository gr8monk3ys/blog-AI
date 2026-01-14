---
description: Manage conversation context - summarize, compact, or load relevant files just-in-time
model: claude-sonnet-4-5
---

# Context Management

Manage conversation context for optimal performance.

## Command: $ARGUMENTS

## Context Operations

### Summarize Context (`/context summarize`)
Create a compact summary of the current conversation:
1. Identify key decisions made
2. List files modified
3. Note pending tasks
4. Capture important learnings
5. Output as structured summary

### Load Context (`/context load <path>`)
Just-in-time load relevant files:
1. Read the specified file or directory
2. Extract key information
3. Summarize for working memory
4. Don't include full file contents unless needed

### Focus Context (`/context focus <topic>`)
Narrow context to specific topic:
1. Identify files related to topic
2. Load relevant sections only
3. Ignore unrelated context
4. Optimize for the focused task

### Budget Status (`/context budget`)
Show context usage:
1. Estimate tokens used in conversation
2. Suggest what can be compacted
3. Recommend context optimizations

## Context Loading Patterns

### For Code Review
```
/context load src/components/
Focus: Component patterns, accessibility, performance
```

### For API Work
```
/context load app/api/
Focus: Route handlers, validation, error handling
```

### For Database Work
```
/context load prisma/ drizzle/
Focus: Schema, migrations, queries
```

## Best Practices

### When to Summarize
- After completing a major task
- Before switching to different area of codebase
- When conversation feels slow
- Before asking complex questions

### What to Keep in Context
- Current task requirements
- Recently modified files
- Active decisions/trade-offs
- User preferences

### What to Offload
- Completed tasks (summarize outcomes)
- Read-only reference files
- Historical discussions
- Exploration that didn't lead anywhere

## Context Budget Guidelines

| Context Type | Priority | Keep? |
|--------------|----------|-------|
| Current task | High | Yes |
| Recent changes | High | Yes |
| User preferences | Medium | Summary |
| File contents | Medium | On-demand |
| Past discussions | Low | Archive |
| Exploration | Low | Discard |

## Example Workflows

### Starting a New Task
```
/context summarize
/context load <relevant-directory>
/context focus <task-topic>
```

### Mid-Session Optimization
```
/context budget
/context summarize
Continue with optimized context
```

### Switching Contexts
```
/context summarize
/memory note: switching from X to Y
/context load <new-area>
```
