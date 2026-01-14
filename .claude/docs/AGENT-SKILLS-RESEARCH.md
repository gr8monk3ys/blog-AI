# Agent Skills System Research

> Research document for implementing Agent Skills and Multi-Agent Orchestration in lorenzos-claude-code plugin.

## Executive Summary

This document outlines the design and implementation strategy for enhancing the plugin with an Agent Skills System and Multi-Agent Orchestration patterns. The goal is to create a more intelligent, context-aware system that can automatically invoke appropriate agents and coordinate complex multi-step workflows.

## 1. Skills vs Commands vs Agents: Key Distinctions

### Current Architecture

| Component | Invocation | Format | Purpose |
|-----------|------------|--------|---------|
| **Commands** | Explicit (`/api-new`) | Markdown + YAML frontmatter | User-initiated tasks with `$ARGUMENTS` |
| **Agents** | Auto-activated by context | Markdown + YAML frontmatter | Specialized AI personalities for domains |
| **MCP Servers** | Tool calls | JSON config | External service integrations |

### Proposed Skills System

| Aspect | Commands | Skills | Agents |
|--------|----------|--------|--------|
| **Trigger** | User types `/command` | Auto-invoked by conversation context | Auto-activated by domain context |
| **Loading** | Full content on invoke | Progressive (name+description first) | Full content on activation |
| **Scope** | Single task execution | Task augmentation/enhancement | Behavioral/expertise overlay |
| **Tool Access** | Full | Configurable via `allowed-tools` | Full |
| **State** | Stateless | Can maintain session context | Stateless |

### When to Use Each

```
User: "Create a new API endpoint for users"
│
├─> Command (`/api-new users`) - Explicit, predictable generation
├─> Skill (auto-invokes "api-creation" skill) - Adds best practices, patterns
└─> Agent (api-architect activates) - Provides expertise overlay
```

## 2. SKILL.md Format Specification

### Basic Structure

```yaml
---
name: skill-name
description: Brief description for progressive disclosure (triggers auto-invocation)
allowed-tools:           # Optional: restrict available tools
  - Read
  - Edit
  - Grep
requires-context:        # Optional: context requirements
  - file-types: [".ts", ".tsx"]
  - patterns: ["api/", "routes/"]
priority: 100            # Optional: higher = checked first (default: 50)
---

## When to Activate

Clear criteria for when this skill should auto-invoke.

## Instructions

Step-by-step guidance for Claude when skill is active.

## Patterns

Code patterns and templates to apply.

## Examples

Concrete examples of skill application.

## Boundaries

What this skill will and won't do.
```

### Progressive Disclosure

Skills use a two-phase loading approach:

1. **Phase 1 (Startup)**: Only `name` and `description` loaded
   - Enables fast context matching
   - Minimal memory footprint
   - Description is the primary trigger mechanism

2. **Phase 2 (Activation)**: Full skill content loaded
   - Only when skill is determined relevant
   - Includes instructions, patterns, examples

### Tool Restrictions

Skills can limit available tools for safety:

```yaml
allowed-tools:
  - Read        # Can read files
  - Grep        # Can search
  - Edit        # Can modify existing files
  # Write not included = cannot create new files
  # Bash not included = cannot execute commands
```

## 3. Skill Bundle Design

### Bundle: API Development

Skills that work together for API development workflows.

#### Skill: api-creation

```yaml
---
name: api-creation
description: Auto-enhances API endpoint creation with Next.js 15 patterns, Zod validation, and consistent error handling
priority: 80
---

## When to Activate

- User creates files in `app/api/` directory
- Conversation mentions "API", "endpoint", "route handler"
- Files being edited contain `NextRequest` or `NextResponse`

## Instructions

When creating or modifying API routes:

1. **Structure Check**
   - Ensure route is in `app/api/[route]/route.ts`
   - Validate export of HTTP method handlers (GET, POST, etc.)

2. **Validation Layer**
   - Add Zod schema for request body/params
   - Validate before any database/external calls
   - Return 400 with clear error messages on validation failure

3. **Response Format**
   - Success: `{ data: T, success: true }`
   - Error: `{ error: string, success: false }`

4. **Error Handling**
   - Wrap handler in try/catch
   - Map known errors to appropriate status codes
   - Never expose stack traces in production

## Patterns

### Route Handler Template
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const RequestSchema = z.object({
  // Define expected fields
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = RequestSchema.safeParse(body);

    if (!validated.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: validated.error.flatten(), success: false },
        { status: 400 }
      );
    }

    // Business logic here
    const result = await processRequest(validated.data);

    return NextResponse.json({ data: result, success: true });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error', success: false },
      { status: 500 }
    );
  }
}
```
```

#### Skill: api-testing

```yaml
---
name: api-testing
description: Auto-generates comprehensive API tests with edge cases, error scenarios, and integration patterns
priority: 70
---

## When to Activate

- User mentions "test" in context of API
- Files in `__tests__/api/` or `*.test.ts` being created
- After api-creation skill completes

## Instructions

Generate tests covering:

1. **Happy Path** - Valid inputs, expected outputs
2. **Validation Errors** - Missing/invalid fields
3. **Authorization** - Unauthenticated, unauthorized access
4. **Edge Cases** - Empty arrays, null values, boundary conditions
5. **Error Handling** - Database failures, external service errors

## Patterns

### Test Template
```typescript
import { testApiHandler } from 'next-test-api-route-handler';
import * as handler from '@/app/api/[route]/route';

describe('API /api/[route]', () => {
  describe('POST', () => {
    it('creates resource with valid data', async () => {
      await testApiHandler({
        appHandler: handler,
        test: async ({ fetch }) => {
          const res = await fetch({ method: 'POST', body: JSON.stringify(validData) });
          expect(res.status).toBe(201);
          const json = await res.json();
          expect(json.success).toBe(true);
        },
      });
    });

    it('returns 400 for invalid data', async () => {
      // Validation error test
    });
  });
});
```
```

### Bundle: Frontend Development

#### Skill: component-patterns

```yaml
---
name: component-patterns
description: Applies React/Vue/Angular/Svelte best practices including accessibility, performance, and type safety
priority: 75
---

## When to Activate

- Creating/editing component files (*.tsx, *.vue, *.svelte, *.component.ts)
- Conversation mentions "component", "UI", "frontend"
- Working in src/components/ or similar directories

## Instructions

1. **Accessibility First**
   - Include ARIA attributes where needed
   - Ensure keyboard navigation
   - Provide alt text for images

2. **Performance**
   - Memoize expensive computations
   - Use lazy loading for heavy components
   - Avoid unnecessary re-renders

3. **Type Safety**
   - Define prop types explicitly
   - Use discriminated unions for variants
   - Export types for consumers
```

#### Skill: state-management

```yaml
---
name: state-management
description: Guides state management decisions between local state, context, and global stores (Zustand/Redux)
priority: 60
---

## When to Activate

- Discussion of state, store, context
- Creating state management files
- Components with complex state logic

## Decision Framework

| State Type | Use When | Solution |
|------------|----------|----------|
| Local | Single component | useState/useReducer |
| Feature | Feature module | React Context |
| Global | App-wide | Zustand (preferred) |
| Server | Remote data | TanStack Query |
```

### Bundle: Database Operations

#### Skill: query-optimization

```yaml
---
name: query-optimization
description: Optimizes database queries with indexing suggestions, N+1 prevention, and efficient data fetching
priority: 65
---

## When to Activate

- Database queries being written
- Performance discussions involving DB
- Files with Prisma/Drizzle/SQL operations

## Instructions

1. **N+1 Prevention**
   - Use includes/joins for related data
   - Batch queries where possible

2. **Index Recommendations**
   - Index frequently filtered columns
   - Composite indexes for multi-column queries

3. **Query Efficiency**
   - Select only needed columns
   - Use pagination for large datasets
   - Cache frequently accessed data
```

#### Skill: migration-safety

```yaml
---
name: migration-safety
description: Ensures database migrations are safe, reversible, and won't cause data loss
priority: 90
---

## When to Activate

- Creating migration files
- Schema changes discussed
- Prisma/Drizzle schema modifications

## Safety Checks

1. **Destructive Operation Warnings**
   - Column drops must be nullable first
   - Table drops require explicit confirmation
   - Rename operations need data migration

2. **Rollback Plan**
   - Every migration must have down migration
   - Test rollback in development

3. **Zero-Downtime Patterns**
   - Add column nullable → migrate data → add constraint
   - Never lock tables for extended periods
```

### Bundle: DevOps & Deployment

#### Skill: ci-cd-patterns

```yaml
---
name: ci-cd-patterns
description: Applies CI/CD best practices for GitHub Actions, testing pipelines, and deployment workflows
priority: 55
---

## When to Activate

- Working with .github/workflows/
- Discussion of CI/CD, deployment, pipelines
- Creating action or workflow files

## Patterns

1. **Job Dependencies**
   - Lint → Test → Build → Deploy
   - Fail fast on errors

2. **Caching**
   - Cache node_modules
   - Cache build artifacts
   - Use proper cache keys

3. **Environment Management**
   - Secrets for credentials
   - Environment-specific configs
   - Preview deployments for PRs
```

## 4. Multi-Agent Orchestration

### Workflow Orchestrators

#### Full-Stack Feature Workflow

```yaml
---
name: fullstack-feature-workflow
type: orchestrator
description: Coordinates full-stack feature implementation from planning through deployment
---

## Workflow Stages

1. **Planning** (requirements-analyst → system-architect)
   - Gather requirements
   - Design high-level architecture
   - Output: Feature specification

2. **API Development** (api-architect → backend-architect)
   - Design API contracts
   - Implement endpoints
   - Output: Working API with tests

3. **Frontend Development** (frontend-architect → accessibility-auditor)
   - Build UI components
   - Ensure accessibility
   - Output: Accessible UI components

4. **Testing** (test-strategist → code-reviewer)
   - Create test strategy
   - Implement tests
   - Review implementation
   - Output: Tested, reviewed code

5. **Documentation** (technical-writer)
   - API documentation
   - Component documentation
   - Output: Complete docs

## Handoff Protocol

Each stage must produce:
- Summary of work completed
- Files created/modified
- Issues encountered
- Recommendations for next stage
```

#### Code Review Workflow

```yaml
---
name: code-review-workflow
type: orchestrator
description: Multi-perspective code review covering security, performance, and quality
---

## Review Stages (Parallel)

1. **Security Review** (security-engineer)
   - OWASP top 10 check
   - Input validation
   - Authentication/authorization
   - Secrets exposure

2. **Performance Review** (performance-engineer)
   - Algorithm complexity
   - Memory usage
   - Database queries
   - Bundle size impact

3. **Quality Review** (code-reviewer)
   - Code style
   - Best practices
   - Maintainability
   - Test coverage

## Aggregation

Combine all reviews into unified report:
- Critical issues (must fix)
- Important issues (should fix)
- Suggestions (nice to have)
- Positive observations
```

#### Refactoring Workflow

```yaml
---
name: refactoring-workflow
type: orchestrator
description: Safe refactoring with analysis, planning, execution, and verification
---

## Stages

1. **Analysis** (code-reviewer → performance-profiler)
   - Identify code smells
   - Profile performance bottlenecks
   - Map dependencies
   - Output: Refactoring candidates

2. **Planning** (refactoring-expert → system-architect)
   - Prioritize refactoring targets
   - Design target architecture
   - Plan incremental changes
   - Output: Refactoring plan

3. **Execution** (refactoring-expert)
   - Apply refactoring patterns
   - Maintain test coverage
   - Preserve functionality
   - Output: Refactored code

4. **Verification** (test-strategist → code-reviewer)
   - Run all tests
   - Verify behavior unchanged
   - Review final code
   - Output: Verified refactoring
```

### Agent Scoring System

```typescript
interface AgentScore {
  agent: string;
  confidence: number;    // 0-100
  relevanceFactors: {
    keywordMatch: number;
    fileTypeMatch: number;
    contextMatch: number;
    historyMatch: number;
  };
}

// Scoring algorithm
function scoreAgent(agent: Agent, context: Context): AgentScore {
  const keywordScore = matchKeywords(agent.triggers, context.message);
  const fileTypeScore = matchFileTypes(agent.fileTypes, context.activeFiles);
  const contextScore = matchContext(agent.patterns, context.recentActions);
  const historyScore = matchHistory(agent.name, context.sessionHistory);

  return {
    agent: agent.name,
    confidence: weightedAverage([keywordScore, fileTypeScore, contextScore, historyScore]),
    relevanceFactors: { keywordScore, fileTypeScore, contextScore, historyScore }
  };
}

// Activation threshold
const ACTIVATION_THRESHOLD = 70;
const AUTO_ACTIVATE_THRESHOLD = 85;
```

### Parallel Agent Execution

For independent tasks, multiple agents can work simultaneously:

```typescript
interface ParallelExecution {
  tasks: AgentTask[];
  dependencies: Map<string, string[]>;  // task -> dependencies
  results: Map<string, AgentResult>;
}

// Example: Code review workflow
const codeReviewTasks = [
  { agent: 'security-engineer', task: 'security-review', dependencies: [] },
  { agent: 'performance-engineer', task: 'performance-review', dependencies: [] },
  { agent: 'code-reviewer', task: 'quality-review', dependencies: [] },
];

// All three run in parallel, then results aggregated
```

## 5. Implementation Plan

### Phase 1: Skill Infrastructure (Week 1)

1. **Create Skills Directory Structure**
   ```
   .claude/
   ├── skills/
   │   ├── api/
   │   │   ├── api-creation.md
   │   │   └── api-testing.md
   │   ├── frontend/
   │   │   ├── component-patterns.md
   │   │   └── state-management.md
   │   ├── database/
   │   │   ├── query-optimization.md
   │   │   └── migration-safety.md
   │   └── devops/
   │       └── ci-cd-patterns.md
   ```

2. **Update Plugin Manifest**
   - Add `skills` array to plugin.json
   - Define skill registration format

3. **Document Skills System**
   - Update CLAUDE.md with skills documentation
   - Create skills authoring guide

### Phase 2: Core Skills Implementation (Week 2)

1. **API Bundle**
   - api-creation skill
   - api-testing skill
   - api-documentation skill

2. **Frontend Bundle**
   - component-patterns skill
   - state-management skill
   - accessibility-patterns skill

### Phase 3: Orchestration System (Week 3)

1. **Create Orchestrator Format**
   - Define ORCHESTRATOR.md format
   - Implement workflow stages
   - Add handoff protocols

2. **Implement Core Workflows**
   - fullstack-feature-workflow
   - code-review-workflow
   - refactoring-workflow

### Phase 4: Scoring & Discovery (Week 4)

1. **Agent Scoring System**
   - Implement confidence scoring
   - Add context matching
   - Create activation thresholds

2. **Skill Discovery**
   - Auto-suggest relevant skills
   - Learn from user patterns
   - Improve over time

## 6. File Changes Required

### New Files

| File | Purpose |
|------|---------|
| `.claude/skills/api/api-creation.md` | API creation enhancement skill |
| `.claude/skills/api/api-testing.md` | API testing generation skill |
| `.claude/skills/frontend/component-patterns.md` | Component best practices |
| `.claude/skills/frontend/state-management.md` | State management guidance |
| `.claude/skills/database/query-optimization.md` | DB query optimization |
| `.claude/skills/database/migration-safety.md` | Safe migration patterns |
| `.claude/skills/devops/ci-cd-patterns.md` | CI/CD best practices |
| `.claude/orchestrators/fullstack-feature.md` | Full-stack workflow |
| `.claude/orchestrators/code-review.md` | Review workflow |
| `.claude/orchestrators/refactoring.md` | Refactoring workflow |

### Modified Files

| File | Changes |
|------|---------|
| `.claude-plugin/plugin.json` | Add `skills` and `orchestrators` arrays |
| `CLAUDE.md` | Document skills and orchestration systems |
| `README.md` | Update feature counts and descriptions |
| `TODO.md` | Mark tasks complete, add new items |

## 7. Success Metrics

1. **Skill Activation Rate**: % of relevant contexts where skills activate
2. **User Satisfaction**: Feedback on skill usefulness
3. **Code Quality**: Measured improvements in generated code
4. **Workflow Completion**: % of orchestrated workflows completing successfully
5. **Context Reduction**: Decrease in repeated instructions

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-activation | Skills trigger unnecessarily | Tunable confidence thresholds |
| Conflicting skills | Multiple skills compete | Priority system, mutual exclusion |
| Performance | Slow skill matching | Progressive disclosure, caching |
| Complexity | Hard to maintain | Clear documentation, tests |

---

*Document created: 2026-01-13*
*Last updated: 2026-01-13*
*Status: Research Complete - Ready for Implementation*
