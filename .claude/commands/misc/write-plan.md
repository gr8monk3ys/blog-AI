---
description: Create a detailed implementation plan with actionable steps and milestones
model: claude-sonnet-4-5
---

# Write Implementation Plan

Create a comprehensive, actionable implementation plan.

## Goal: $ARGUMENTS

## Planning Process

### Step 1: Analyze Requirements

First, let me understand what needs to be built:

**Core Requirements:**
- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]

**Technical Requirements:**
- [ ] [Tech requirement 1]
- [ ] [Tech requirement 2]

**Non-Functional Requirements:**
- Performance: [Criteria]
- Security: [Criteria]
- Scalability: [Criteria]

### Step 2: Research Codebase

Before planning, I need to understand:

```bash
# Files to examine
- [path/to/relevant/file1]
- [path/to/relevant/file2]
- [path/to/relevant/file3]
```

**Existing Patterns Found:**
- [Pattern 1]: Used in [file]
- [Pattern 2]: Used in [file]

**Dependencies:**
- [Dependency 1]: [Why needed]
- [Dependency 2]: [Why needed]

---

## Implementation Plan

### Overview

```
Phase 1: [Foundation] ──→ Phase 2: [Core] ──→ Phase 3: [Integration] ──→ Phase 4: [Polish]
```

---

### Phase 1: Foundation

**Objective:** Set up the groundwork for the feature

#### Task 1.1: [Task Name]
- **Description:** [What to do]
- **Files to create/modify:**
  - `path/to/file.ts` - [Changes]
- **Acceptance criteria:**
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]

#### Task 1.2: [Task Name]
- **Description:** [What to do]
- **Files to create/modify:**
  - `path/to/file.ts` - [Changes]
- **Acceptance criteria:**
  - [ ] [Criterion 1]

**Phase 1 Checkpoint:**
- [ ] All foundation tasks complete
- [ ] No regressions in existing tests
- [ ] Code compiles without errors

---

### Phase 2: Core Implementation

**Objective:** Build the main functionality

#### Task 2.1: [Task Name]
- **Description:** [What to do]
- **Dependencies:** Task 1.1, Task 1.2
- **Files to create/modify:**
  - `path/to/file.ts` - [Changes]
- **Code outline:**
  ```typescript
  // Pseudocode or structure
  function featureName() {
    // Step 1: ...
    // Step 2: ...
    // Step 3: ...
  }
  ```
- **Acceptance criteria:**
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]

#### Task 2.2: [Task Name]
- **Description:** [What to do]
- **Dependencies:** Task 2.1
- **Files to create/modify:**
  - `path/to/file.ts` - [Changes]
- **Acceptance criteria:**
  - [ ] [Criterion 1]

**Phase 2 Checkpoint:**
- [ ] Core functionality works
- [ ] Unit tests written and passing
- [ ] Manual testing completed

---

### Phase 3: Integration

**Objective:** Connect components and ensure they work together

#### Task 3.1: [Integration Task]
- **Description:** [What to integrate]
- **Dependencies:** Phase 2 complete
- **Files to modify:**
  - `path/to/file.ts` - [Changes]
- **Testing approach:**
  - [ ] Integration test 1
  - [ ] Integration test 2

#### Task 3.2: [API/UI Integration]
- **Description:** [What to connect]
- **Files to modify:**
  - `path/to/file.ts` - [Changes]

**Phase 3 Checkpoint:**
- [ ] All components integrated
- [ ] Integration tests passing
- [ ] No performance regressions

---

### Phase 4: Polish & Documentation

**Objective:** Final refinements and documentation

#### Task 4.1: Error Handling
- [ ] Add comprehensive error handling
- [ ] User-friendly error messages
- [ ] Logging for debugging

#### Task 4.2: Documentation
- [ ] Code comments for complex logic
- [ ] Update README if needed
- [ ] API documentation

#### Task 4.3: Testing
- [ ] Edge case tests
- [ ] Error scenario tests
- [ ] Performance tests (if applicable)

**Phase 4 Checkpoint:**
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Ready for review

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Strategy] |
| [Risk 2] | Low/Med/High | Low/Med/High | [Strategy] |

## Dependencies & Blockers

**External Dependencies:**
- [ ] [Dependency 1] - Status: [Ready/Blocked]
- [ ] [Dependency 2] - Status: [Ready/Blocked]

**Potential Blockers:**
- [Blocker 1]: [How to resolve]

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] No known bugs
- [ ] Performance acceptable

---

## Execution

Ready to start? Use `/execute-plan` to work through this plan step by step.

The plan will be saved and referenced as we implement each task.
