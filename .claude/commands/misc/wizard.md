---
description: Interactive wizard to help build command specifications
model: claude-opus-4-5
---

Help me determine the right command and options for my task.

## My Request

$ARGUMENTS

## Wizard Process

Based on my request, guide me through these steps:

### Step 1: Identify the Task Type

Determine which category best fits:
- **Component/UI** → `/component-new`, `/page-new`, `/component-vue`, `/component-angular`, `/component-svelte`
- **API Development** → `/api-new`, `/api-test`, `/api-protect`
- **Database** → `/migration-new`, `/types-gen`
- **Testing** → `/test-new`
- **Code Quality** → `/lint`, `/code-cleanup`, `/code-optimize`
- **Documentation** → `/docs-generate`, `/code-explain`
- **Planning** → `/feature-plan`, `/new-task`
- **Deployment** → `/deploy`
- **Hooks** → `/hook-new`
- **Edge Functions** → `/edge-function-new`

### Step 2: Gather Requirements

For the identified command, ask me about:

**For Components:**
- Framework preference (React/Vue/Angular/Svelte)?
- Styling approach (Tailwind/CSS Modules/Styled Components)?
- Need state management?
- Is this a Server or Client component?
- Should I include tests?

**For API Endpoints:**
- HTTP methods needed (GET/POST/PUT/DELETE)?
- Authentication required?
- What data will it handle?
- Need validation with Zod?
- Should I generate tests too?

**For Database:**
- ORM/database (Supabase/Prisma/Drizzle)?
- What tables/columns?
- Need RLS policies?
- Migration direction (up/down)?

**For Testing:**
- Test framework (Vitest/Jest/Playwright)?
- Unit, integration, or E2E?
- What scenarios to cover?

**For Deployment:**
- Platform (Vercel/Netlify/AWS/Docker)?
- CI/CD needed?
- Environment variables?

### Step 3: Build the Command

Once I've answered the questions, construct the full command with all options specified. Format as:

```
/command-name detailed specification with all gathered requirements
```

### Step 4: Explain What Will Be Generated

Briefly describe what files and code will be created.

---

## Quick Reference

If my request is already clear, suggest the command directly:

| Task | Command | Example |
|------|---------|---------|
| React component | `/component-new` | `/component-new UserProfile card with avatar and bio` |
| Vue component | `/component-vue` | `/component-vue TodoList with Pinia store` |
| Angular component | `/component-angular` | `/component-angular DataTable with pagination` |
| Svelte component | `/component-svelte` | `/component-svelte Counter with runes` |
| Next.js page | `/page-new` | `/page-new dashboard with sidebar layout` |
| API endpoint | `/api-new` | `/api-new POST /users with email validation` |
| API tests | `/api-test` | `/api-test users endpoint all CRUD operations` |
| Database migration | `/migration-new` | `/migration-new add posts table with Prisma` |
| React hook | `/hook-new` | `/hook-new useDebounce for search input` |
| Test file | `/test-new` | `/test-new UserService with Vitest` |
| Feature plan | `/feature-plan` | `/feature-plan user authentication with OAuth` |

Guide me to the right command with the right options!
