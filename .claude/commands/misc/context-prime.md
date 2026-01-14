---
description: Load comprehensive project context to prime Claude with project understanding
model: claude-sonnet-4-5
---

# Context Prime

Prime Claude with comprehensive understanding of this project.

## Target: $ARGUMENTS

## Instructions

Systematically load and understand the project context by following these steps:

### 1. Project Structure Analysis

First, explore the project structure:
```bash
# Get directory tree (excluding common noise)
find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" -o -name "*.rs" | head -50

# Check for configuration files
ls -la package.json tsconfig.json .env.example Cargo.toml go.mod pyproject.toml 2>/dev/null
```

### 2. Key Files to Read

Load these critical files (if they exist):

**Project Configuration:**
- `package.json` - Dependencies, scripts, project metadata
- `tsconfig.json` / `jsconfig.json` - TypeScript/JS configuration
- `.env.example` - Environment variables needed

**Documentation:**
- `README.md` - Project overview and setup
- `CLAUDE.md` - AI-specific instructions
- `CONTRIBUTING.md` - Development guidelines

**Architecture:**
- `src/index.ts` or `src/main.ts` - Entry point
- `src/app/layout.tsx` - Next.js root layout
- `prisma/schema.prisma` - Database schema
- `supabase/migrations/` - Database migrations

### 3. Build Understanding

After reading files, document your understanding:

```markdown
## Project Summary

**Name:** [project name]
**Type:** [Next.js app / Node.js API / CLI tool / Library / etc.]
**Primary Language:** [TypeScript / JavaScript / Python / etc.]

## Tech Stack
- **Framework:** [Next.js 15 / Express / FastAPI / etc.]
- **Database:** [Supabase / Prisma / MongoDB / etc.]
- **Styling:** [Tailwind / CSS Modules / styled-components / etc.]
- **State:** [Zustand / Redux / Context / etc.]

## Key Directories
- `src/app/` - [description]
- `src/components/` - [description]
- `src/lib/` - [description]

## Important Patterns
1. [Pattern 1 observed in codebase]
2. [Pattern 2 observed in codebase]

## Development Commands
- `npm run dev` - [what it does]
- `npm run build` - [what it does]
- `npm run test` - [what it does]

## Environment Variables Required
- `DATABASE_URL` - [purpose]
- `API_KEY` - [purpose]
```

### 4. Focus Areas

If the user specified a focus area in $ARGUMENTS, dive deeper into:

**"api"** - Focus on API routes, middleware, authentication
**"frontend"** - Focus on components, pages, styling
**"database"** - Focus on schema, migrations, queries
**"auth"** - Focus on authentication and authorization
**"tests"** - Focus on test structure and coverage

### 5. Output Context Document

Provide a concise but comprehensive context document that can be referenced throughout the session. Include:

1. **Quick Reference** - Most important facts
2. **Architecture Overview** - How the system is organized
3. **Key Files** - Where to find important code
4. **Conventions** - Coding patterns used in this project
5. **Known Issues** - Any TODOs or technical debt noted

## Important Notes

- Read actual files rather than guessing content
- Note any inconsistencies or potential issues
- Highlight any security-sensitive areas
- Identify the "hot paths" - most critical code paths
- Document any non-obvious patterns or conventions

This context will help me assist you more effectively throughout our session.
