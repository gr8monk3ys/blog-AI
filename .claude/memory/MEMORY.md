# Claude Memory System

This file serves as Claude's persistent memory for this project. It is automatically read at session start and updated throughout conversations.

## Memory Types

### Semantic Memory (Facts & Knowledge)
Long-term factual information about the project.

```yaml
project:
  name: lorenzos-claude-code
  type: claude-code-plugin
  version: 1.9.0

tech_stack:
  - Claude Code Plugin System
  - Markdown with YAML frontmatter
  - Node.js for scripts
  - GitHub Actions for CI

architecture:
  commands: 41 (27 unique + 14 aliases)
  agents: 19 specialized AI agents
  skills: 8 auto-activating skills
  orchestrators: 3 multi-agent workflows
  mcp_servers: 15 configured
  hooks: 6 automation scripts

key_directories:
  commands: .claude/commands/
  agents: .claude/agents/
  skills: .claude/skills/
  orchestrators: .claude/orchestrators/
  memory: .claude/memory/
  rules: .claude/rules/
  hooks: .claude/hooks/
  docs: .claude/docs/
```

### Episodic Memory (Session History)
Recent actions and their outcomes (auto-updated).

```yaml
recent_sessions:
  - date: 2026-01-13
    session: 2
    actions:
      - Added Context Management commands (/memory, /context)
      - Added Aider-inspired features (/architect, /ask, /map)
      - Added Cursor-inspired features (/rules, PROJECT-RULES.md)
      - Expanded MCP servers from 9 to 15
      - Released v1.9.0
    outcomes:
      - 6 new commands created
      - Memory system in .claude/memory/
      - Rules system in .claude/rules/
      - 6 new MCP servers configured
    learnings:
      - Memory types (semantic, episodic, procedural) help organize context
      - Project rules provide consistent Claude behavior
      - Read-only modes (/ask, /architect) useful for exploration

  - date: 2026-01-13
    session: 1
    actions:
      - Implemented Agent Skills System (8 skills)
      - Created Multi-Agent Orchestrators (3 workflows)
      - Updated documentation for v1.8.0
    outcomes:
      - All skills created in .claude/skills/
      - Orchestrators in .claude/orchestrators/
      - Research doc in .claude/docs/
    learnings:
      - Skills use progressive disclosure pattern
      - Orchestrators need clear handoff protocols
```

### Procedural Memory (Rules & Patterns)
Project-specific rules and conventions.

```yaml
conventions:
  commands:
    - Use YAML frontmatter with description and model
    - Include $ARGUMENTS placeholder for user input
    - Add aliases for common commands

  agents:
    - Description is critical for activation matching
    - Include Triggers, Behavioral Mindset, Focus Areas
    - Define clear Boundaries

  skills:
    - Higher priority = checked first
    - Use triggers for context matching
    - Document when skill auto-activates

  code_style:
    - TypeScript strict mode
    - No any types
    - Zod for validation
    - Error format: { data: T, success: true } | { error: string, success: false }

  versioning:
    - x.y.Z for patches
    - x.Y.0 for features
    - X.0.0 for breaking changes
```

## Working Memory (Current Session)

### Active Context
<!-- Auto-updated during session -->
```yaml
current_task: Demonstrating plugin implementation
files_in_focus:
  - .claude/memory/MEMORY.md
  - .claude/rules/PROJECT-RULES.md
  - .claude-plugin/plugin.json
recent_changes:
  - Updated memory with v1.9.0 architecture
  - Added session 2 episodic entry
pending_items:
  - Remaining TODO items (low priority)
```

### Session Notes
<!-- Add notes during session -->
- User wants to see the plugin working in action
- Demonstrating memory updates and context management


## User Preferences

### Learned Preferences
```yaml
preferences:
  skip_marketing_tasks: true
  prioritize_technical_features: true
  documentation_style: concise
```

### Communication Style
```yaml
communication:
  response_length: moderate
  code_comments: minimal
  explanation_depth: as_needed
```

---

## How to Use This File

### For Claude
1. Read this file at session start to understand project context
2. Update Episodic Memory after significant changes
3. Refer to Procedural Memory for conventions
4. Update Working Memory during active tasks

### For Users
1. Add project-specific facts to Semantic Memory
2. Document preferences in User Preferences section
3. Add important conventions to Procedural Memory
4. Review and clean up periodically

### Memory Maintenance
- Archive old episodic entries monthly
- Update semantic memory when architecture changes
- Review procedural rules quarterly
