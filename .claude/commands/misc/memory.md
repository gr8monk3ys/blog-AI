---
description: View, update, or manage Claude's persistent memory for this project
model: claude-sonnet-4-5
---

# Memory Management

Manage Claude's persistent memory system for this project.

## Command: $ARGUMENTS

## Memory Operations

### View Memory
If the user wants to view memory, read and summarize `.claude/memory/MEMORY.md`:
- Show current project facts (Semantic Memory)
- Show recent session history (Episodic Memory)
- Show active conventions (Procedural Memory)

### Update Memory
If the user provides information to remember:
1. Determine the appropriate memory type:
   - **Semantic**: Facts, architecture, tech stack
   - **Episodic**: Session actions and outcomes
   - **Procedural**: Rules, conventions, patterns
2. Update the relevant section in `.claude/memory/MEMORY.md`
3. Confirm what was stored

### Clear/Reset Memory
If the user wants to clear memory:
- Archive current memory to `.claude/memory/archive/`
- Reset to clean template
- Confirm the reset

### Add Session Note
If the user provides a quick note:
- Add to "Session Notes" in Working Memory section
- Include timestamp

## Memory File Location

The memory file is at: `.claude/memory/MEMORY.md`

## Examples

**View memory:**
```
/memory view
/memory show preferences
/memory what do you know about this project
```

**Update memory:**
```
/memory remember that we use Prisma for database
/memory add convention: always use server components first
/memory note: user prefers minimal comments
```

**Session notes:**
```
/memory note: working on auth feature today
/memory note: blocked on API design decision
```

## Best Practices

1. **Keep it relevant**: Only store information that helps future sessions
2. **Be specific**: Vague memories are less useful
3. **Update regularly**: Memory is most useful when current
4. **Archive old entries**: Don't let memory grow unbounded
