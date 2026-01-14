---
name: fullstack-feature-workflow
type: orchestrator
description: Coordinates full-stack feature implementation from requirements through deployment with multi-agent collaboration
triggers:
  - "implement feature"
  - "build new feature"
  - "full-stack"
  - "end-to-end"
---

# Full-Stack Feature Workflow Orchestrator

Coordinates complete feature implementation across the stack using specialized agents.

## Workflow Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PLANNING   │───▶│    BUILD    │───▶│   VERIFY    │
│             │    │             │    │             │
│ requirements│    │ api + tests │    │ review +    │
│ + design    │    │ + frontend  │    │ docs        │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Stage 1: Planning (Sequential)

### 1.1 Requirements Analysis
**Agent**: `requirements-analyst`
**Purpose**: Transform user request into concrete specifications

**Inputs**:
- User's feature description
- Existing codebase context
- Project constraints

**Outputs**:
- User stories with acceptance criteria
- Edge cases identified
- Technical constraints documented

**Handoff Document**:
```markdown
## Feature: [Name]

### User Stories
- As a [user], I want [action] so that [benefit]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Edge Cases
- Case 1: [description]
- Case 2: [description]

### Technical Constraints
- [Constraint 1]
- [Constraint 2]
```

### 1.2 Architecture Design
**Agent**: `system-architect`
**Purpose**: Design high-level technical approach

**Inputs**:
- Requirements document from 1.1
- Existing architecture patterns
- Technology stack

**Outputs**:
- Component diagram
- Data flow description
- API contracts overview
- File structure plan

**Handoff Document**:
```markdown
## Architecture: [Feature Name]

### Components
- Component A: [purpose]
- Component B: [purpose]

### Data Flow
1. User action triggers...
2. API endpoint receives...
3. Database updates...
4. Response returns...

### Files to Create/Modify
- `app/api/[route]/route.ts` - New API endpoint
- `components/[Feature]/` - New components
- `lib/[feature].ts` - Business logic

### API Contracts
- `POST /api/feature`: Create resource
- `GET /api/feature/:id`: Get resource
```

## Stage 2: Build (Parallel Where Possible)

### 2.1 API Development
**Agent**: `api-architect` → `backend-architect`
**Purpose**: Implement backend functionality

**Skills Activated**:
- `api-creation` - Endpoint patterns
- `api-security` - Authentication/authorization
- `query-optimization` - Database efficiency

**Inputs**:
- Architecture document
- API contracts

**Outputs**:
- Route handlers with validation
- Database queries/mutations
- Error handling
- API tests

**Handoff Document**:
```markdown
## API Implementation: [Feature]

### Endpoints Created
- `POST /api/feature` - [status: complete]
  - Validation: Zod schema
  - Auth: JWT required
  - Tests: 15 passing

### Database Changes
- New table: `features`
- New index: `idx_features_user_id`

### Known Limitations
- [Any limitations or TODOs]
```

### 2.2 Frontend Development
**Agent**: `frontend-architect`
**Purpose**: Build user interface components

**Skills Activated**:
- `component-patterns` - React/Vue/Svelte patterns
- `state-management` - State architecture
- `accessibility-patterns` - A11y compliance

**Inputs**:
- Architecture document
- API contracts
- Design requirements

**Outputs**:
- UI components
- State management
- API integration
- Component tests

**Handoff Document**:
```markdown
## Frontend Implementation: [Feature]

### Components Created
- `FeatureForm.tsx` - Main form component
- `FeatureList.tsx` - List display
- `FeatureCard.tsx` - Individual item

### State Management
- Local state for form
- TanStack Query for server state

### Accessibility
- ARIA labels: ✓
- Keyboard nav: ✓
- Focus management: ✓

### Tests
- Unit tests: 12 passing
- Integration: 5 passing
```

### 2.3 Testing Implementation
**Agent**: `test-strategist`
**Purpose**: Create comprehensive test coverage

**Skills Activated**:
- `api-testing` - API test patterns

**Inputs**:
- API implementation
- Frontend implementation
- Acceptance criteria

**Outputs**:
- E2E test scenarios
- Integration tests
- Edge case coverage

## Stage 3: Verify (Sequential)

### 3.1 Code Review
**Agent**: `code-reviewer`
**Purpose**: Quality and security review

**Review Checklist**:
- [ ] Code follows project patterns
- [ ] No security vulnerabilities
- [ ] Tests are comprehensive
- [ ] Error handling is complete
- [ ] Performance is acceptable
- [ ] Accessibility requirements met

**Handoff Document**:
```markdown
## Code Review: [Feature]

### Status: [Approved/Changes Requested]

### Findings
- **Critical**: [none/list]
- **Important**: [list]
- **Suggestions**: [list]

### Security Check
- [ ] Input validation
- [ ] Authorization
- [ ] SQL injection
- [ ] XSS prevention

### Recommendations
- [Any suggestions for improvement]
```

### 3.2 Documentation
**Agent**: `technical-writer`
**Purpose**: Create user and developer documentation

**Outputs**:
- API documentation
- Component documentation
- Usage examples
- Changelog entry

## Orchestration Protocol

### Starting the Workflow

```typescript
interface WorkflowContext {
  featureRequest: string;
  projectPath: string;
  techStack: TechStack;
  constraints?: string[];
}

async function startFullStackWorkflow(context: WorkflowContext) {
  // Stage 1: Planning
  const requirements = await runAgent('requirements-analyst', context);
  const architecture = await runAgent('system-architect', {
    ...context,
    requirements,
  });

  // Stage 2: Build (parallel)
  const [api, frontend] = await Promise.all([
    runAgent('api-architect', { ...context, architecture }),
    runAgent('frontend-architect', { ...context, architecture }),
  ]);

  const tests = await runAgent('test-strategist', {
    ...context,
    api,
    frontend,
  });

  // Stage 3: Verify
  const review = await runAgent('code-reviewer', {
    ...context,
    api,
    frontend,
    tests,
  });

  if (review.status === 'changes-requested') {
    // Loop back to relevant stage
    return handleReviewFeedback(review);
  }

  const docs = await runAgent('technical-writer', {
    ...context,
    api,
    frontend,
  });

  return { success: true, artifacts: { api, frontend, tests, docs } };
}
```

### Agent Handoff Protocol

Each agent must produce:

1. **Summary**: Brief description of work completed
2. **Artifacts**: List of files created/modified with paths
3. **Decisions**: Key decisions made and rationale
4. **Issues**: Any blockers or concerns encountered
5. **Next Steps**: Recommendations for subsequent agents

### Error Handling

```typescript
// If any stage fails:
if (stageResult.error) {
  // 1. Document the error
  logError(stageResult.error);

  // 2. Determine if recoverable
  if (isRecoverable(stageResult.error)) {
    // Retry with modified approach
    return retryStage(stage, modifiedContext);
  }

  // 3. Escalate to user
  return requestUserIntervention(stageResult.error);
}
```

## Usage Examples

### Example 1: User Authentication Feature

```
User: "Add user authentication with email/password"

Stage 1 (Planning):
- requirements-analyst: User stories for login, signup, logout, password reset
- system-architect: JWT-based auth, middleware design, protected routes

Stage 2 (Build):
- api-architect: /api/auth/login, /api/auth/signup, /api/auth/logout
- frontend-architect: LoginForm, SignupForm, AuthProvider, ProtectedRoute
- test-strategist: Auth flow tests, edge cases

Stage 3 (Verify):
- code-reviewer: Security audit, token handling review
- technical-writer: Auth documentation, setup guide
```

### Example 2: Dashboard Feature

```
User: "Build an analytics dashboard showing user metrics"

Stage 1:
- requirements-analyst: Metrics to display, refresh rates, user roles
- system-architect: Data aggregation strategy, caching, chart library

Stage 2:
- api-architect: /api/analytics endpoints with aggregations
- frontend-architect: Dashboard layout, chart components, filters
- test-strategist: Data accuracy tests, loading states

Stage 3:
- code-reviewer: Performance review, data accuracy
- technical-writer: Dashboard user guide, API docs
```

## Boundaries

**This orchestrator handles:**
- Complete feature implementation workflows
- Multi-agent coordination
- Quality verification
- Documentation generation

**This orchestrator does NOT handle:**
- Infrastructure setup (use devops-engineer)
- Database migrations (use migration-planner)
- Deployment (use ci-cd-patterns skill)
- Bug fixes (use simpler single-agent flows)
