---
description: Generate a comprehensive Product Requirements Document (PRD) from a feature idea
model: claude-sonnet-4-5
---

# Create Product Requirements Document

Generate a comprehensive PRD for a feature or product idea.

## Feature/Product: $ARGUMENTS

## PRD Template

---

# Product Requirements Document

## Document Info
| Field | Value |
|-------|-------|
| **Feature Name** | $ARGUMENTS |
| **Author** | [Name] |
| **Created** | [Date] |
| **Status** | Draft |
| **Version** | 1.0 |

---

## 1. Executive Summary

### 1.1 Overview
[2-3 sentence summary of what this feature/product does and why it matters]

### 1.2 Goals
| Goal | Metric | Target |
|------|--------|--------|
| Primary Goal | [Metric] | [Target] |
| Secondary Goal | [Metric] | [Target] |

### 1.3 Non-Goals
- [What this feature explicitly will NOT do]
- [Scope limitations]

---

## 2. Background & Problem Statement

### 2.1 Current State
[Description of how things work today]

### 2.2 Problem
[Clear articulation of the problem being solved]

### 2.3 User Pain Points
1. **Pain Point 1**: [Description] - Impact: [High/Medium/Low]
2. **Pain Point 2**: [Description] - Impact: [High/Medium/Low]
3. **Pain Point 3**: [Description] - Impact: [High/Medium/Low]

### 2.4 Opportunity
[Why solving this problem matters now]

---

## 3. User Research

### 3.1 Target Users

#### Primary Persona
| Attribute | Value |
|-----------|-------|
| **Name** | [Persona name] |
| **Role** | [Job title/role] |
| **Goals** | [What they want to achieve] |
| **Frustrations** | [Current pain points] |
| **Tech Savvy** | [Low/Medium/High] |

#### Secondary Persona
[Similar table for secondary users]

### 3.2 User Stories

#### Must Have (P0)
```
As a [user type],
I want to [action],
So that [benefit].

Acceptance Criteria:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]
```

#### Should Have (P1)
[Additional user stories]

#### Nice to Have (P2)
[Additional user stories]

### 3.3 User Journey

```
[Current State] → [Trigger] → [Action 1] → [Action 2] → [Success State]
     ↓                              ↓
 [Pain Point]                 [Opportunity]
```

---

## 4. Proposed Solution

### 4.1 Solution Overview
[High-level description of the solution]

### 4.2 Key Features

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| Feature 1 | [Description] | P0 | [Low/Med/High] |
| Feature 2 | [Description] | P0 | [Low/Med/High] |
| Feature 3 | [Description] | P1 | [Low/Med/High] |

### 4.3 User Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Entry     │ ──→ │   Action    │ ──→ │   Result    │
│   Point     │     │   Step      │     │   State     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 4.4 Wireframes/Mockups
[Placeholder for visual designs]

---

## 5. Technical Requirements

### 5.1 Architecture Overview
```
┌──────────────────────────────────────────┐
│                Frontend                   │
├──────────────────────────────────────────┤
│                  API                      │
├──────────────────────────────────────────┤
│               Database                    │
└──────────────────────────────────────────┘
```

### 5.2 Technical Specifications

| Component | Technology | Notes |
|-----------|------------|-------|
| Frontend | [React/Next.js] | [Specific requirements] |
| Backend | [Node.js/Python] | [Specific requirements] |
| Database | [PostgreSQL/MongoDB] | [Schema changes needed] |
| APIs | [REST/GraphQL] | [New endpoints needed] |

### 5.3 Data Requirements

#### New Data Models
```typescript
interface NewEntity {
  id: string;
  // Fields...
  createdAt: Date;
  updatedAt: Date;
}
```

#### Database Changes
- [ ] New table: `table_name`
- [ ] New column: `existing_table.new_column`
- [ ] New index: `table_name(column)`

### 5.4 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/resource` | Create resource | Required |
| GET | `/api/resource/:id` | Get resource | Required |
| PUT | `/api/resource/:id` | Update resource | Required |

### 5.5 Dependencies
- [ ] External API: [API name] - [Purpose]
- [ ] Library: [Package name] - [Purpose]
- [ ] Service: [Service name] - [Purpose]

---

## 6. Design Requirements

### 6.1 UI/UX Principles
1. [Principle 1]: [How it applies]
2. [Principle 2]: [How it applies]

### 6.2 Accessibility Requirements
- [ ] WCAG 2.1 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Color contrast ratios

### 6.3 Responsive Design
| Breakpoint | Layout | Priority Features |
|------------|--------|-------------------|
| Mobile (<768px) | [Layout] | [Features] |
| Tablet (768-1024px) | [Layout] | [Features] |
| Desktop (>1024px) | [Layout] | [Features] |

---

## 7. Success Metrics

### 7.1 Key Performance Indicators (KPIs)

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| [Metric 1] | [Value] | [Value] | [How measured] |
| [Metric 2] | [Value] | [Value] | [How measured] |

### 7.2 Success Criteria
- [ ] [Criterion 1]: [Definition of done]
- [ ] [Criterion 2]: [Definition of done]

### 7.3 Analytics Events
| Event | Trigger | Properties |
|-------|---------|------------|
| `feature_viewed` | Page load | `user_id`, `timestamp` |
| `action_completed` | User action | `user_id`, `action_type` |

---

## 8. Launch Plan

### 8.1 Rollout Strategy
| Phase | Audience | Duration | Success Gate |
|-------|----------|----------|--------------|
| Alpha | Internal | 1 week | [Criteria] |
| Beta | 10% users | 2 weeks | [Criteria] |
| GA | 100% | - | [Criteria] |

### 8.2 Feature Flags
- `feature_name_enabled` - Master toggle
- `feature_name_beta` - Beta access

### 8.3 Rollback Plan
[Description of how to rollback if issues occur]

---

## 9. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | [H/M/L] | [H/M/L] | [Strategy] |
| [Risk 2] | [H/M/L] | [H/M/L] | [Strategy] |

---

## 10. Timeline

### 10.1 Milestones

| Milestone | Description | Dependencies |
|-----------|-------------|--------------|
| M1: Design Complete | Finalized designs | Design review |
| M2: API Complete | Backend ready | Schema migration |
| M3: Frontend Complete | UI implemented | API complete |
| M4: Testing Complete | QA passed | All development |
| M5: Launch | Feature live | All testing |

### 10.2 Dependencies
- [ ] [Dependency 1]: [Owner] - [Status]
- [ ] [Dependency 2]: [Owner] - [Status]

---

## 11. Open Questions

| Question | Owner | Due Date | Status |
|----------|-------|----------|--------|
| [Question 1] | [Name] | [Date] | Open |
| [Question 2] | [Name] | [Date] | Open |

---

## 12. Appendix

### 12.1 Glossary
| Term | Definition |
|------|------------|
| [Term 1] | [Definition] |
| [Term 2] | [Definition] |

### 12.2 References
- [Document/Link 1]
- [Document/Link 2]

### 12.3 Change Log
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Name] | Initial draft |

---

## Instructions for Claude

When generating this PRD:

1. **Research First** - Look at the codebase to understand existing patterns
2. **Be Specific** - Fill in concrete details, not just placeholders
3. **Think E2E** - Consider the full user journey
4. **Technical Depth** - Include realistic technical requirements
5. **Measure Success** - Define clear, measurable success criteria

Ask clarifying questions if the feature idea is ambiguous.
