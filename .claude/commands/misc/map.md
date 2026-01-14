---
description: Generate a map of the codebase structure showing files, dependencies, and architecture
model: claude-sonnet-4-5
---

# Codebase Map

Generate a comprehensive map of the codebase.

## Scope: $ARGUMENTS

If no scope provided, map the entire project.

## Map Types

### 1. Directory Structure
Show file organization:
```
project/
├── src/
│   ├── components/     # UI components
│   ├── lib/            # Utilities
│   ├── hooks/          # Custom hooks
│   └── types/          # TypeScript types
├── app/
│   ├── api/            # API routes
│   └── (routes)/       # Page routes
└── tests/              # Test files
```

### 2. Component Tree
Show component hierarchy:
```
App
├── Layout
│   ├── Header
│   │   ├── Navigation
│   │   └── UserMenu
│   ├── Sidebar
│   └── Footer
└── MainContent
    ├── Dashboard
    └── Settings
```

### 3. Dependency Graph
Show module dependencies:
```
UserProfile
├── imports: useUser, UserAvatar, formatDate
├── imported by: Dashboard, Settings
└── external deps: react, date-fns
```

### 4. API Map
Show API structure:
```
/api
├── /auth
│   ├── POST /login
│   ├── POST /logout
│   └── POST /register
├── /users
│   ├── GET /         (list)
│   ├── POST /        (create)
│   ├── GET /:id      (read)
│   ├── PATCH /:id    (update)
│   └── DELETE /:id   (delete)
└── /posts
    └── ...
```

### 5. Data Flow Map
Show how data moves:
```
User Action
    ↓
Component (state update)
    ↓
API Call (fetch/mutation)
    ↓
Server (route handler)
    ↓
Database (query)
    ↓
Response → Component Update → UI
```

## Output Options

### Quick Overview
```
/map
```
Shows: Directory structure + key file counts

### Focused Map
```
/map components
/map api
/map hooks
```
Shows: Detailed map of specific area

### Full Analysis
```
/map full
```
Shows: All map types with statistics

## Statistics Included

- File counts by type
- Lines of code estimates
- Test coverage hints
- Dependency counts
- Component complexity hints

## Use Cases

### New to Codebase
```
/map
```
Get oriented with project structure

### Planning New Feature
```
/map components
/map api
```
Understand where to add code

### Refactoring
```
/map dependencies <module>
```
Understand impact of changes

### Code Review
```
/map <changed-directory>
```
Understand context of changes

## Output Format

The map will be output as:
1. ASCII tree diagrams (for structure)
2. Tables (for statistics)
3. Mermaid diagrams (if complex relationships)

## Notes

- Large codebases may show summarized views
- Use scope to focus on specific areas
- Maps are point-in-time snapshots
- Run after major changes to update mental model
