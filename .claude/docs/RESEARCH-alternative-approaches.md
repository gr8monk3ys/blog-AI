# Research: Alternative Approaches

This document explores experimental features and architectural improvements for the lorenzos-claude-code plugin.

## 1. Command Composition Patterns

### Current State

Commands are independent units that don't know about each other. Users must manually chain them:

```bash
/api-new users endpoint
# ... review output ...
/api-test users endpoint
# ... review output ...
/api-protect users endpoint
```

### Proposed: Workflow Compositions

Define command workflows that chain multiple commands together.

#### Option A: Workflow Commands

Create meta-commands that orchestrate multiple commands:

```markdown
---
description: Create a complete API endpoint with tests and protection
model: claude-opus-4-5
workflow:
  - command: api-new
    args: $ARGUMENTS
  - command: api-test
    args: $ARGUMENTS
    condition: previous.success
  - command: api-protect
    args: $ARGUMENTS
    condition: previous.success
---
```

**Pros:**
- Explicit workflow definition
- Conditional execution based on previous results
- Can skip steps if user requests

**Cons:**
- Requires workflow engine in Claude Code (not currently supported)
- Complex error handling between steps

#### Option B: Command Suggestions

After each command completes, suggest related commands:

```markdown
## Next Steps
- Run `/api-test $ARGUMENTS` to generate tests
- Run `/api-protect $ARGUMENTS` to add security
- Run `/docs users-api` to document the endpoint
```

**Pros:**
- Works today without infrastructure changes
- User maintains control
- Educational (teaches workflow)

**Cons:**
- Manual execution required
- No automation

#### Option C: Compound Arguments

Add flags to trigger related commands:

```bash
/api-new users endpoint --with-tests --with-protection
```

The command template would include conditional sections:

```markdown
$ARGUMENTS

{{#if with-tests}}
## Also Generate Tests
Generate comprehensive API tests...
{{/if}}

{{#if with-protection}}
## Also Add Protection
Add authentication middleware...
{{/if}}
```

**Pros:**
- Single command invocation
- User opts into additional functionality
- Could work with current infrastructure

**Cons:**
- Commands become bloated
- Flag parsing complexity

### Recommendation

**Short-term:** Implement Option B (suggestions) by adding "Next Steps" sections to commands.

**Long-term:** Propose workflow composition feature to Claude Code team.

---

## 2. Plugin Extension System for Community Commands

### Current State

Users fork the entire plugin to add commands. No mechanism for extensions.

### Proposed: Extension Architecture

#### Extension Structure

```
.claude/
├── commands/           # Core plugin commands
├── agents/             # Core plugin agents
└── extensions/         # User/community extensions
    ├── my-company/
    │   ├── extension.json
    │   ├── commands/
    │   │   └── internal-api.md
    │   └── agents/
    │       └── company-standards.md
    └── community-pack/
        ├── extension.json
        └── commands/
            └── graphql-codegen.md
```

#### Extension Manifest (extension.json)

```json
{
  "name": "my-company-extensions",
  "version": "1.0.0",
  "description": "Company-specific commands and agents",
  "extends": "lorenzos-claude-code",
  "commands": [
    {
      "name": "internal-api",
      "path": "commands/internal-api.md",
      "description": "Create internal API following company standards"
    }
  ],
  "agents": [
    {
      "name": "company-standards",
      "path": "agents/company-standards.md",
      "description": "Enforce company coding standards"
    }
  ]
}
```

#### Extension Discovery

```javascript
// scripts/load-extensions.js
function loadExtensions() {
  const extensionsDir = '.claude/extensions'
  const extensions = fs.readdirSync(extensionsDir)

  return extensions.map(ext => {
    const manifest = JSON.parse(
      fs.readFileSync(`${extensionsDir}/${ext}/extension.json`)
    )
    return {
      ...manifest,
      basePath: `${extensionsDir}/${ext}`
    }
  })
}
```

#### Conflict Resolution

When multiple extensions define the same command name:

1. **Namespace prefixing:** `my-company:api-new`
2. **Priority ordering:** Core > User > Community
3. **User config:** Allow overrides in settings

### Benefits

- Companies can add proprietary commands without forking
- Community can share specialized commands
- Core plugin stays focused and maintainable
- Easy upgrades (extensions survive plugin updates)

### Implementation Complexity

**High** - Requires changes to how plugin.json is loaded and merged.

### Recommendation

Document the extension pattern as a convention. Create a `CONTRIBUTING-EXTENSIONS.md` guide. Actual extension loading would require Claude Code platform support.

---

## 3. Plugin Themes/Presets for Different Tech Stacks

### Current State

Plugin is optimized for Next.js + React + Supabase. Other stacks require manual customization.

### Proposed: Stack Presets

#### Preset Structure

```
.claude/
├── presets/
│   ├── nextjs-supabase/     # Current default
│   │   └── preset.json
│   ├── vue-nuxt-prisma/
│   │   ├── preset.json
│   │   └── overrides/
│   │       └── component-new.md
│   ├── angular-nestjs/
│   │   ├── preset.json
│   │   └── overrides/
│   ├── svelte-sveltekit/
│   │   └── preset.json
│   └── react-remix/
│       └── preset.json
```

#### Preset Configuration (preset.json)

```json
{
  "name": "vue-nuxt-prisma",
  "description": "Vue 3 + Nuxt 3 + Prisma stack",
  "framework": "vue",
  "metaFramework": "nuxt",
  "database": "prisma",
  "styling": "tailwind",
  "testing": "vitest",
  "commandOverrides": {
    "component-new": "overrides/component-new.md",
    "page-new": "overrides/page-new.md"
  },
  "disabledCommands": [
    "edge-function-new"
  ],
  "additionalCommands": [
    {
      "name": "composable-new",
      "path": "overrides/composable-new.md",
      "description": "Create Vue composable"
    }
  ],
  "variables": {
    "COMPONENT_STYLE": "vue-sfc",
    "STATE_MANAGEMENT": "pinia",
    "API_STYLE": "nuxt-server-routes"
  }
}
```

#### How Presets Work

1. User sets active preset in `plugin-settings.json`:
   ```json
   {
     "activePreset": "vue-nuxt-prisma"
   }
   ```

2. Commands reference preset variables:
   ```markdown
   Create a new {{COMPONENT_STYLE}} component using {{STATE_MANAGEMENT}} for state.
   ```

3. Override commands replace default implementations

#### Available Presets

| Preset | Framework | Meta-Framework | Database | Styling |
|--------|-----------|----------------|----------|---------|
| nextjs-supabase | React | Next.js 15 | Supabase | Tailwind |
| vue-nuxt-prisma | Vue 3 | Nuxt 3 | Prisma | Tailwind |
| angular-nestjs | Angular 17+ | - | TypeORM | Angular Material |
| svelte-sveltekit | Svelte 5 | SvelteKit | Drizzle | Tailwind |
| react-remix | React | Remix | Prisma | Tailwind |
| react-vite | React | Vite | - | CSS Modules |

### Implementation

Create preset files and a preset loader that:
1. Reads active preset from settings
2. Merges command overrides
3. Injects variables into command templates
4. Enables/disables commands based on preset

### Recommendation

**Phase 1:** Create preset configuration files documenting each stack.

**Phase 2:** Implement variable injection in command templates.

**Phase 3:** Full preset switching with command overrides.

---

## 4. Agent Specialization Based on Project Type Detection

### Current State

Agents activate based on conversation context matching their descriptions. No awareness of project type.

### Proposed: Project-Aware Agents

#### Detection Strategy

Analyze project files to determine stack:

```javascript
// scripts/detect-project.js
function detectProjectType() {
  const indicators = {
    nextjs: ['next.config.js', 'next.config.mjs', 'next.config.ts'],
    nuxt: ['nuxt.config.ts', 'nuxt.config.js'],
    angular: ['angular.json', 'nx.json'],
    sveltekit: ['svelte.config.js'],
    remix: ['remix.config.js'],
    vite: ['vite.config.ts', 'vite.config.js']
  }

  const databases = {
    supabase: ['.env.local:SUPABASE_URL', 'supabase/'],
    prisma: ['prisma/schema.prisma'],
    drizzle: ['drizzle.config.ts'],
    mongodb: ['.env:MONGODB_URI']
  }

  const testing = {
    jest: ['jest.config.js', 'jest.config.ts'],
    vitest: ['vitest.config.ts'],
    playwright: ['playwright.config.ts']
  }

  // Check for presence of indicator files
  return {
    framework: detectFramework(indicators),
    database: detectDatabase(databases),
    testing: detectTesting(testing)
  }
}
```

#### Agent Specialization

Agents receive project context and adapt recommendations:

```markdown
---
name: backend-architect
description: Design reliable backend systems
model: claude-sonnet-4-5
specializations:
  nextjs:
    focus: ["API Routes", "Server Actions", "Edge Runtime"]
    patterns: ["app/api structure", "middleware.ts"]
  nuxt:
    focus: ["Server Routes", "Nitro", "H3"]
    patterns: ["server/api structure", "server middleware"]
  angular:
    focus: ["NestJS", "Express", "Services"]
    patterns: ["controllers", "providers", "modules"]
---
```

#### Context Injection

Before agent activation, inject detected project context:

```markdown
## Project Context (Auto-detected)
- Framework: Next.js 15 (App Router)
- Database: Supabase
- Testing: Vitest + Playwright
- Styling: Tailwind CSS

## Your Task
[Original user request]
```

### Benefits

- Agents provide more relevant recommendations
- No manual configuration needed
- Adapts to different parts of monorepo
- Better code examples matching actual stack

### Implementation

1. Create `scripts/detect-project.js`
2. Add project context to agent prompts
3. Update agent templates with specialization sections
4. Run detection on conversation start

### Recommendation

Implement detection script and context injection. This would significantly improve agent relevance without requiring user configuration.

---

## Implementation Priority

| Feature | Effort | Impact | Priority |
|---------|--------|--------|----------|
| Command suggestions (Option B) | Low | Medium | P1 |
| Project type detection | Medium | High | P1 |
| Preset configuration files | Medium | Medium | P2 |
| Extension documentation | Low | Medium | P2 |
| Variable injection in templates | High | High | P3 |
| Full extension loading | Very High | Medium | P4 |

## Next Steps

1. **P1 Items:**
   - Add "Next Steps" sections to API commands
   - Create `scripts/detect-project.js`
   - Add project context injection to agent prompts

2. **P2 Items:**
   - Create preset JSON files for each stack
   - Write `CONTRIBUTING-EXTENSIONS.md`

3. **Future:**
   - Propose workflow composition to Claude Code team
   - Implement variable injection when template engine is available
