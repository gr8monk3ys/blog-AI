# Feature map

Every feature a user can reach in the web app, one row each, in the user's words. Other loops
name features by the first column; `pr-review` and `fuzz` walk this table.

"Where" is the route in `apps/web` (Next.js) and, when the page calls it, the FastAPI route in
`apps/api`. Run locally as in `CLAUDE.md` (`bun dev` on :3000, API on :8000). Several actions
need things a bare local run does not have: a signed-in user, a Blog AI API key, an LLM
key, or `DATABASE_URL`. The last column says what you see when it works.

Not mapped yet: the browser extension (`apps/extension`) and the public REST API.

## Public pages

| Feature | Where | How to reach it | How to check it works |
|---|---|---|---|
| Landing page | `/` | Open the site | Hero reads "Brand-Consistent AI Content For Lean Marketing Teams"; header nav and footer links render |
| Light / dark / system theme | header theme button | Click the round theme button in the header | Its label changes from "System theme" to "Light mode" and the page colours follow |
| Pricing | `/pricing`; API `GET /api/payments/pricing` | Header → Pricing | Free, Starter and Pro plans with "What's included", a feature comparison and an FAQ |
| Blog | `/blog`, `/blog/<slug>` | Header → Blog | Lists posts from `apps/web/content/blog/*.md`; with none, says "Nothing has been published here yet." |
| RSS feed | `/rss` | Open `/rss` | `200` with `application/rss+xml`, channel title "Blog AI" |
| Tool directory | `/tool-directory` | Footer → Tool Directory | "Browse Every AI Tool in One Place", tools grouped by category with links |
| Privacy policy and terms | `/privacy`, `/terms` | Footer → Privacy Policy / Terms of Service | Headings "Privacy Policy" / "Terms of Service" with numbered sections |
| Sign in / sign up | `/sign-in`, `/sign-up` (`/auth` redirects to `/sign-in`) | Header sign-in button | Email + password forms. Sign-up lands on `/verify-email` ("Check your inbox"); the emailed link signs you in and shows "You are in." |
| Password reset | `/forgot-password` → emailed link → `/reset-password` | "Forgot password?" on `/sign-in` | "If an account uses that address, a reset link is on its way", then "Set a new password." and back to `/sign-in` |
| Account menu | header, signed in | Account icon | Your email, Settings, Sign out |

## Writing

| Feature | Where | How to reach it | How to check it works |
|---|---|---|---|
| Browse and search AI tools | `/tools` | Header → Tools | 29 tools with category chips (Blog, Email, Social Media, …) and a "Free Only" chip; typing "email" in Search tools leaves only email tools |
| Tools by category | `/tools/category/<category>` | Open a category, e.g. `/tools/category/email` | "Email Tools" heading listing only that category's tools |
| Run a single tool | `/tools/<slug>`; API `/api/v1/tools/*` | Click a tool card on `/tools` | The tool workspace opens with its input form; submitting returns the generated text (needs sign-in, API key and LLM key) |
| Generate a blog post | `/generate`; API `POST /api/v1/generate-blog` | Header → Generate | Topic, keywords, tone and provider fields plus research / proofread / humanize / SEO / fact-check toggles; "Generate Blog Post" returns a post (needs API key and LLM key; otherwise an error alert) |
| Bulk generation from CSV | `/bulk`; API `/api/v1/batch/*` | Header → Bulk | "Bulk SEO Content Workflow": Upload CSV, Download Template, Add Topic; the "Generate N Posts" count follows the topics added |
| Content templates | `/templates`; `/api/templates` | Header → Templates | Six starter templates with category filters (Email shows 2); "Use Template" opens the matching tool with the template's presets in the URL |
| Remix content into other formats | `/remix`; API `/api/v1/remix/*` | Open `/remix` | Source content box and the 12 target formats from `GET /api/v1/remix/formats`; picking one updates "Select Target Formats (1/6 selected)"; Analyze/Remix return results (needs API key and LLM key) |
| Plagiarism check | `/plagiarism`; API `/api/v1/content/check-plagiarism` | Open `/plagiarism` | Content, title, provider and exclude-URL fields; "Check for Plagiarism" returns a similarity report (needs API key and a provider key) |
| AI images | `/images`; API `/api/v1/images/*` | Header → Images | Single Image / Blog Images / Custom Prompt / From Content modes with type, provider, style, quality and size; "Generate Image" returns an image (needs API key and image provider key) |
| Knowledge base | `/knowledge`; API `/api/v1/knowledge/*` | Header → Knowledge Base (shown when `NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE=true`) | Documents / Search / Usage tabs and an upload drop zone; without a migrated database it says "Knowledge Base Unavailable" |

## Brand voice

| Feature | Where | How to reach it | How to check it works |
|---|---|---|---|
| Brand voice profiles | `/brand`; `/api/brand-profiles` | Header → Brand Voice | Your profiles plus three examples; "Create Profile" opens a form (name, style, industry, audience, examples, preferred and banned words, values); saving lists the profile (needs sign-in and database) |
| Train a brand voice | `/brand/train`; API `/api/v1/brand-voice/*` | Open `/brand/train` | "Voice Training Studio": pick a profile, add voice samples, "Train Voice", then score test content (needs a saved profile and API key) |
| Score content against a voice | `/brand/score`; API `POST /api/v1/brand-voice/score` | Open `/brand/score` | Profile, content type and content fields; "Score Content" returns a voice score (needs a trained profile and API key) |

## Workspace

| Feature | Where | How to reach it | How to check it works |
|---|---|---|---|
| Onboarding wizard | `/onboarding` | Open `/onboarding` | Four steps (Welcome, Brand Voice, First Generation, Done); entering a name and pressing Next moves to "Define Your Brand Voice" |
| Content history | `/history`; `/api/history` | Footer → Content History | Signed in: your past generations. Signed out: "Sign In Required" |
| Usage analytics | `/analytics` | Footer → Analytics | "Analytics Dashboard" with total generations, active today, popular tool and response time; the 7/30/90-day and all-time buttons switch the range |
| Social scheduling | `/social`; API `/api/social/*` | Header → Social | Accounts / Schedule / Campaigns / Analytics tabs; with no accounts it says "No Accounts Connected" and offers "Connect Account" |
| Team and organizations | `/team`; API `/api/v1/organizations` | Header → Team | With none it says "No Organizations"; "New Organization" opens a "Create Organization" form (needs sign-in and database to save) |
| Webhooks | `/settings/webhooks`; API `/api/v1/webhooks/*` | Open `/settings/webhooks` | Lists webhooks, or "No Webhooks Configured"; "Add Webhook" and "Event Type Reference" (needs API key to save) |
| Blog admin | `/admin/blog`; `/api/blog-posts` | Open `/admin/blog` | Signed in: create and edit blog posts stored in Postgres. Signed out: "You need to sign in to view this page" |
