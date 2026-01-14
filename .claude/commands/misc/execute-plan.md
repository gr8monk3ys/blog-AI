---
description: Execute an implementation plan step by step with verification at each stage
model: claude-sonnet-4-5
---

# Execute Plan

Systematically execute the implementation plan with verification at each step.

## Plan Reference: $ARGUMENTS

## Execution Protocol

### Before Starting

1. **Verify Plan Exists**
   - Check for existing plan in conversation
   - Or use `/write-plan` first to create one

2. **Confirm Current State**
   ```bash
   git status
   npm run test
   npm run build
   ```

3. **Create Feature Branch** (if not already)
   ```bash
   git checkout -b feature/[feature-name]
   ```

---

## Execution Loop

For each task in the plan, I will:

### 1. Announce Task
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 TASK [X.Y]: [Task Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Description: [What we're doing]
Files: [Files to modify]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Implement
- Write the code for this specific task
- Follow existing patterns in codebase
- Add tests as specified

### 3. Verify
```
✅ Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass
- [ ] No lint errors
```

### 4. Commit (Optional)
```bash
git add -A
git commit -m "feat: [description of task]"
```

### 5. Move to Next Task
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ TASK [X.Y] COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progress: [X/Y tasks] | Phase: [N/M]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase Checkpoints

After each phase, verify:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏁 PHASE [N] CHECKPOINT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Checklist:
- [ ] All phase tasks complete
- [ ] Tests passing
- [ ] No regressions
- [ ] Build succeeds
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Run verification commands:
```bash
npm run test
npm run lint
npm run build
```

---

## Error Handling

### If a Task Fails

1. **Stop and Assess**
   ```
   ⚠️ TASK [X.Y] BLOCKED
   Issue: [Description of problem]
   ```

2. **Options:**
   - A) Fix the issue and retry
   - B) Adjust the plan
   - C) Skip and document for later
   - D) Rollback and reconsider approach

3. **Document Decision**
   ```
   Decision: [What we chose]
   Reason: [Why]
   Impact: [Any changes to plan]
   ```

### If Tests Fail

1. **Identify failure**
   ```bash
   npm run test -- --reporter=verbose
   ```

2. **Fix or adjust**
   - Fix the implementation, OR
   - Update the test if spec changed

3. **Verify fix**
   ```bash
   npm run test
   ```

---

## Progress Tracking

### Status Board
```
┌─────────────────────────────────────────────────┐
│ EXECUTION STATUS                                │
├─────────────────────────────────────────────────┤
│ Phase 1: Foundation          [████████░░] 80%   │
│ Phase 2: Core Implementation [░░░░░░░░░░]  0%   │
│ Phase 3: Integration         [░░░░░░░░░░]  0%   │
│ Phase 4: Polish              [░░░░░░░░░░]  0%   │
├─────────────────────────────────────────────────┤
│ Overall Progress             [██░░░░░░░░] 20%   │
└─────────────────────────────────────────────────┘
```

### Task Log
| Task | Status | Notes |
|------|--------|-------|
| 1.1 | ✅ Done | - |
| 1.2 | 🔄 In Progress | Working on validation |
| 1.3 | ⏳ Pending | - |
| 2.1 | ⏳ Pending | - |

---

## Completion

### Final Verification
```bash
# Full test suite
npm run test

# Type checking
npm run typecheck

# Linting
npm run lint

# Build
npm run build
```

### Summary Report
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 EXECUTION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tasks Completed: [X/Y]
Tests Added: [N]
Files Modified: [M]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Changes Made:
- [File 1]: [What changed]
- [File 2]: [What changed]

## Tests Added:
- [Test 1]
- [Test 2]

## Next Steps:
- [ ] Code review
- [ ] QA testing
- [ ] Deploy to staging
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Commands Reference

| Action | Command |
|--------|---------|
| Create plan | `/write-plan [goal]` |
| Brainstorm first | `/brainstorm [topic]` |
| Run tests | `npm run test` |
| Type check | `npm run typecheck` |
| Lint | `npm run lint` |
| Build | `npm run build` |

---

*Ready to execute! I'll work through each task systematically, verifying as I go.*
