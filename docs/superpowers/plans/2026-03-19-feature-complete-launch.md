# Feature-Complete Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire all core backend capabilities to the frontend, fix persistence gaps, and ship a production-ready product where every advertised feature either works or is honestly flagged "Coming Soon."

**Architecture:** Vertical slices — each task group produces a working, testable feature. Infrastructure fixes (Tasks 1-3) must land before feature wiring (Tasks 4-10). Frontend uses Next.js 16 App Router with glassmorphic design system. Backend is FastAPI with Postgres + Redis.

**Tech Stack:** Next.js 16, React 18, TypeScript, Tailwind, HeadlessUI, Framer Motion | FastAPI, Python 3.12, Postgres (Neon), Redis, Pydantic

**Spec:** `docs/superpowers/specs/2026-03-19-feature-complete-launch-design.md`

---

## Task 1: Require Redis in Production

**Files:**
- Modify: `apps/api/src/storage/redis_client.py:27`
- Modify: `apps/api/src/config.py:769-849` (inside `validate_production_config()`)
- Test: `apps/api/tests/test_redis_production.py`

- [ ] **Step 1: Write failing test for Redis production guard**

```python
# apps/api/tests/test_redis_production.py
import os
import pytest
from unittest.mock import patch

def test_redis_raises_in_production_without_url():
    """In production, RedisClient must raise if REDIS_URL is unset."""
    with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
        env = os.environ.copy()
        env.pop("REDIS_URL", None)
        with patch.dict(os.environ, env, clear=True):
            from apps.api.src.storage.redis_client import RedisClient
            with pytest.raises(RuntimeError, match="REDIS_URL"):
                RedisClient()

def test_redis_allows_localhost_in_development():
    """In development, localhost fallback is fine."""
    with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
        env = os.environ.copy()
        env.pop("REDIS_URL", None)
        with patch.dict(os.environ, env, clear=True):
            from apps.api.src.storage.redis_client import RedisClient
            client = RedisClient()
            assert "localhost" in client.redis_url
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && pytest tests/test_redis_production.py -v`
Expected: FAIL — RedisClient currently doesn't check APP_ENV

- [ ] **Step 3: Implement Redis production guard**

In `apps/api/src/storage/redis_client.py`, change line 27 from:
```python
self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
```
to:
```python
self.redis_url = os.environ.get("REDIS_URL")
if not self.redis_url:
    if os.environ.get("APP_ENV") == "production":
        raise RuntimeError(
            "REDIS_URL is required in production. "
            "Bulk jobs and webhook subscriptions require Redis for persistence."
        )
    self.redis_url = "redis://localhost:6379/0"
```

- [ ] **Step 4: Add Redis check to validate_production_config()**

In `apps/api/src/config.py` inside `validate_production_config()` (around line 830, before the `sys.exit` block), add:

```python
if not os.environ.get("REDIS_URL"):
    errors.append(
        "REDIS_URL is not set. Bulk jobs and webhooks require Redis in production."
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/api && pytest tests/test_redis_production.py -v`
Expected: PASS

- [ ] **Step 6: Run full backend test suite**

Run: `cd apps/api && pytest -q`
Expected: All existing tests pass

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/storage/redis_client.py apps/api/src/config.py apps/api/tests/test_redis_production.py
git commit -m "fix: require REDIS_URL in production for bulk jobs and webhooks"
```

---

## Task 2: Add DEMO_DATA_ENABLED Env Var

**Files:**
- Modify: `apps/web/lib/server-mode.ts`
- Modify: `apps/web/app/api/history/route.ts`
- Modify: `apps/web/app/api/templates/route.ts` (if exists)
- Test: `apps/web/tests/lib/server-mode.test.ts` (create)

- [ ] **Step 1: Write failing test for DEMO_DATA_ENABLED**

```typescript
// apps/web/tests/lib/server-mode.test.ts
import { describe, it, expect, vi, afterEach } from 'vitest'

describe('canServeDemoData', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('returns false when DEMO_DATA_ENABLED is "false"', async () => {
    vi.stubEnv('DEMO_DATA_ENABLED', 'false')
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(false)
  })

  it('returns true when DEMO_DATA_ENABLED is "true"', async () => {
    vi.stubEnv('DEMO_DATA_ENABLED', 'true')
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(true)
  })

  it('defaults to true in non-production', async () => {
    vi.stubEnv('NODE_ENV', 'development')
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(true)
  })

  it('defaults to false in production when DEMO_DATA_ENABLED unset', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    // Ensure DEMO_DATA_ENABLED is not set
    delete process.env.DEMO_DATA_ENABLED
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(false)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && bunx vitest run tests/lib/server-mode.test.ts`
Expected: FAIL — current implementation ignores DEMO_DATA_ENABLED

- [ ] **Step 3: Update canServeDemoData()**

Replace `apps/web/lib/server-mode.ts` contents with:

```typescript
export function isProductionEnv(): boolean {
  return process.env.NODE_ENV === 'production'
}

export function canServeDemoData(): boolean {
  const explicit = process.env.DEMO_DATA_ENABLED
  if (explicit !== undefined) {
    return explicit === 'true'
  }
  // Default: allow in dev/test, disallow in production
  return !isProductionEnv()
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && bunx vitest run tests/lib/server-mode.test.ts`
Expected: PASS

- [ ] **Step 5: Update history and templates routes to use consistent pattern**

In `apps/web/app/api/history/route.ts`, find the GET handler's demo data fallback and ensure it follows the `brand-profiles` pattern:
```typescript
if (!sql) {
  if (!canServeDemoData()) {
    return databaseUnavailableResponse('Content history')
  }
  // existing demo data return
}
```

Do the same for `apps/web/app/api/templates/route.ts` if it has a similar pattern.

- [ ] **Step 6: Add DEMO_DATA_ENABLED to .env.example**

Add this line to `.env.example`:
```
# Set to "false" in production to disable demo data fallbacks (default: true in dev, false in production)
# DEMO_DATA_ENABLED=true
```

- [ ] **Step 7: Run full frontend test suite**

Run: `bun run test:run`
Expected: All tests pass

- [ ] **Step 8: Commit**

```bash
git add apps/web/lib/server-mode.ts apps/web/tests/lib/server-mode.test.ts apps/web/app/api/history/route.ts .env.example
git commit -m "fix: add DEMO_DATA_ENABLED env var to control demo data in production"
```

---

## Task 3: Add Migration Runner to server.py

**Files:**
- Modify: `apps/api/server.py`
- Test: `apps/api/tests/test_migration_runner.py`

- [ ] **Step 1: Write failing test for migration runner**

```python
# apps/api/tests/test_migration_runner.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

def test_apply_migrations_runs_sql_files_in_order():
    """Migration runner should apply SQL files in numeric order."""
    from apps.api.server import get_pending_migrations

    # get_pending_migrations should return sorted list of .sql files
    # excluding rollback files
    migrations = get_pending_migrations("apps/api/migrations")
    filenames = [m.name for m in migrations]

    assert "001_create_webhook_tables.sql" in filenames
    assert "002_knowledge_base.sql" in filenames
    # Rollback files should be excluded
    assert all("rollback" not in f for f in filenames)
    # Should be sorted
    assert filenames == sorted(filenames)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && pytest tests/test_migration_runner.py -v`
Expected: FAIL — `get_pending_migrations` doesn't exist yet

- [ ] **Step 3: Implement migration runner**

Add to `apps/api/server.py` before the app creation:

```python
from pathlib import Path

def get_pending_migrations(migrations_dir: str) -> list[Path]:
    """Return migration SQL files sorted by name, excluding rollbacks."""
    migrations_path = Path(migrations_dir)
    if not migrations_path.exists():
        return []
    return sorted(
        f for f in migrations_path.glob("*.sql")
        if "rollback" not in f.name
    )

async def apply_migrations(database_url: str, migrations_dir: str = "migrations") -> int:
    """Apply pending migrations. Returns count of migrations applied."""
    import asyncpg

    migrations = get_pending_migrations(migrations_dir)
    if not migrations:
        return 0

    conn = await asyncpg.connect(database_url)
    try:
        # Create migrations tracking table if it doesn't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                name TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        applied = set(
            row["name"] for row in
            await conn.fetch("SELECT name FROM _migrations")
        )

        count = 0
        for migration in migrations:
            if migration.name not in applied:
                sql = migration.read_text()
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO _migrations (name) VALUES ($1)",
                    migration.name
                )
                logger.info(f"Applied migration: {migration.name}")
                count += 1

        return count
    finally:
        await conn.close()
```

Add CLI handling at the bottom of `server.py`:

```python
if __name__ == "__main__":
    import sys
    if "--migrate" in sys.argv:
        import asyncio
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("ERROR: DATABASE_URL is required for migrations")
            sys.exit(1)
        count = asyncio.run(apply_migrations(db_url))
        print(f"Applied {count} migration(s)")
        sys.exit(0)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && pytest tests/test_migration_runner.py -v`
Expected: PASS

- [ ] **Step 5: Run full backend test suite**

Run: `cd apps/api && pytest -q`
Expected: All existing tests pass

- [ ] **Step 6: Commit**

```bash
git add apps/api/server.py apps/api/tests/test_migration_runner.py
git commit -m "feat: add --migrate flag to server.py for applying SQL migrations"
```

---

## Task 4: Wire ContentGenerator Into /generate Page

**Files:**
- Create: `apps/web/app/generate/page.tsx`
- Create: `apps/web/app/generate/GeneratePageClient.tsx`
- Modify: `apps/web/components/SiteHeader.tsx:15-24` (navLinks array)
- Modify: `apps/web/app/HomePageClient.tsx` (signed-in CTA)

- [ ] **Step 1: Create the server component shell**

```typescript
// apps/web/app/generate/page.tsx
import type { Metadata } from 'next'
import GeneratePageClient from './GeneratePageClient'

export const metadata: Metadata = {
  title: 'Generate Content | Blog AI',
  description: 'Generate brand-consistent blog posts with AI-powered research, fact-checking, and SEO optimization.',
}

export default function GeneratePage() {
  return <GeneratePageClient />
}
```

- [ ] **Step 2: Create the client component**

```typescript
// apps/web/app/generate/GeneratePageClient.tsx
'use client'

import { useState, useId } from 'react'
import ContentGenerator from '../../components/ContentGenerator'
import ExportMenu from '../../components/ExportMenu'
import SEOScorePanel from '../../components/seo/SEOScorePanel'
import type { ContentGenerationResponse, BlogContent } from '../../types/content'
import type { ExportContent } from '../../components/ExportMenu'

function isBlogContent(content: ContentGenerationResponse): content is { success: true; type: 'blog'; content: BlogContent } {
  return content.success && content.type === 'blog'
}

function blogToSections(blog: BlogContent): string {
  return blog.sections
    .map((s) => {
      const heading = s.title ? `## ${s.title}\n\n` : ''
      const body = (s.subtopics || [])
        .map((sub) => {
          const subHead = sub.title ? `### ${sub.title}\n\n` : ''
          return subHead + sub.content
        })
        .join('\n\n')
      return heading + body
    })
    .join('\n\n')
}

export default function GeneratePageClient() {
  const conversationId = useId()
  const [content, setContent] = useState<ContentGenerationResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const blogContent = content && isBlogContent(content) ? content.content : null

  const exportContent: ExportContent | null = blogContent
    ? {
        title: blogContent.title,
        content: blogToSections(blogContent),
        type: 'blog',
        metadata: {
          date: blogContent.date,
          description: blogContent.description,
          tags: blogContent.tags,
        },
      }
    : null

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <ContentGenerator
        conversationId={conversationId}
        setContent={setContent}
        setLoading={setLoading}
      />

      {loading && (
        <div className="mt-8 text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-amber-600 border-t-transparent" />
          <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Generating your content...</p>
        </div>
      )}

      {blogContent && !loading && (
        <div className="mt-10 space-y-8">
          {/* Export bar */}
          {exportContent && (
            <div className="flex justify-end">
              <ExportMenu content={exportContent} />
            </div>
          )}

          {/* Rendered blog post */}
          <article className="glass-card rounded-2xl p-8 prose prose-gray dark:prose-invert max-w-none">
            <h1>{blogContent.title}</h1>
            {blogContent.description && (
              <p className="lead text-lg text-gray-600 dark:text-gray-400">
                {blogContent.description}
              </p>
            )}
            {blogContent.sections.map((section, i) => (
              <section key={i}>
                {section.title && <h2>{section.title}</h2>}
                {(section.subtopics || []).map((sub, j) => (
                  <div key={j}>
                    {sub.title && <h3>{sub.title}</h3>}
                    <p>{sub.content}</p>
                  </div>
                ))}
              </section>
            ))}
          </article>

          {/* SEO Score (if available) */}
          {blogContent.seo_score && (
            <SEOScorePanel score={blogContent.seo_score} />
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Update SiteHeader nav links**

In `apps/web/components/SiteHeader.tsx`, change line 21 from:
```typescript
  { href: '/tools', label: 'Generate', authRequired: true },
```
to:
```typescript
  { href: '/generate', label: 'Generate', authRequired: true },
  { href: '/tools', label: 'Tools', authRequired: true },
```

- [ ] **Step 4: Update HomePageClient signed-in CTA**

In `apps/web/app/HomePageClient.tsx`, find the `<SignedIn>` block with `href="/bulk"` (around line 373) and change to `href="/generate"`. Also change the label from "Run Bulk Workflow" to "Start Generating".

Do the same for the bottom-of-page signed-in CTA (around line 584).

- [ ] **Step 5: Run type check and lint**

Run: `bun run type-check && bun run lint`
Expected: Clean

- [ ] **Step 6: Run all tests**

Run: `bun run test:run`
Expected: All 182+ tests pass. SiteHeader tests may need minor updates if they assert on the exact nav link count or text.

- [ ] **Step 7: Build**

Run: `bun run build`
Expected: Clean build with `/generate` route appearing in the output

- [ ] **Step 8: Commit**

```bash
git add apps/web/app/generate/ apps/web/components/SiteHeader.tsx apps/web/app/HomePageClient.tsx
git commit -m "feat: wire ContentGenerator into /generate page route"
```

---

## Task 5: Brand Voice Scoring Page

**Files:**
- Create: `apps/web/app/brand/score/page.tsx`
- Create: `apps/web/app/brand/score/ScorePageClient.tsx`

- [ ] **Step 1: Pre-implementation check**

Read `apps/api/app/routes/brand_voice.py` and confirm:
- `POST /brand-voice/score` exists (should be at line ~577)
- Request takes `{ profile_id, content, content_type?, provider? }`
- Response returns `{ success, score, grade, passed }`

If the endpoint path or schema differs, adjust the code in Step 2 accordingly.

- [ ] **Step 2: Create the scoring page server component**

```typescript
// apps/web/app/brand/score/page.tsx
import type { Metadata } from 'next'
import ScorePageClient from './ScorePageClient'

export const metadata: Metadata = {
  title: 'Score Content | Brand Voice | Blog AI',
  description: 'Score your content against your trained brand voice profile.',
}

export default function ScorePage() {
  return <ScorePageClient />
}
```

- [ ] **Step 3: Create the scoring page client component**

```typescript
// apps/web/app/brand/score/ScorePageClient.tsx
'use client'

import { useState, useEffect } from 'react'
import { DocumentTextIcon } from '@heroicons/react/24/outline'
import ScoreResult from '../../../components/brand/ScoreResult'
import { API_BASE_URL } from '../../../lib/api'
import type { BrandProfile } from '../../../types/brand'

interface ScoreResponse {
  success: boolean
  score: {
    overall_score: number
    vocabulary_score: number
    tone_score: number
    style_score: number
  }
  grade: string
  passed: boolean
}

export default function ScorePageClient() {
  const [profiles, setProfiles] = useState<BrandProfile[]>([])
  const [selectedProfileId, setSelectedProfileId] = useState('')
  const [content, setContent] = useState('')
  const [result, setResult] = useState<ScoreResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/brand-profiles')
      .then((r) => r.json())
      .then((data) => {
        if (data.success && data.data) setProfiles(data.data)
      })
      .catch(() => {})
  }, [])

  const handleScore = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProfileId || !content.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch(`${API_BASE_URL}/brand-voice/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_id: selectedProfileId,
          content: content.trim(),
        }),
      })

      if (!res.ok) throw new Error(`Score request failed: ${res.status}`)
      const data: ScoreResponse = await res.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to score content')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center mb-6">
        <DocumentTextIcon className="h-5 w-5 text-amber-600 mr-2" />
        <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100">
          Score Content Against Brand Voice
        </h1>
      </div>

      <form onSubmit={handleScore} className="space-y-6">
        <div>
          <label htmlFor="profile" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Brand Profile
          </label>
          <select
            id="profile"
            value={selectedProfileId}
            onChange={(e) => setSelectedProfileId(e.target.value)}
            className="mt-1 block w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white/70 dark:bg-gray-800/70 dark:text-gray-100 backdrop-blur-sm"
            required
          >
            <option value="">Select a profile...</option>
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="content" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Content to Score
          </label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={10}
            className="mt-1 block w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white/70 dark:bg-gray-800/70 dark:text-gray-100 backdrop-blur-sm"
            placeholder="Paste your content here..."
            required
            minLength={20}
          />
        </div>

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-xl shadow-sm shadow-amber-600/20 text-sm font-medium text-white bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-all disabled:opacity-50"
        >
          {loading ? 'Scoring...' : 'Score Content'}
        </button>
      </form>

      {result && (
        <div className="mt-8">
          <ScoreResult
            score={result.score}
            grade={result.grade}
            passed={result.passed}
          />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run type check**

Run: `bun run type-check`
Expected: Clean. If `ScoreResult` props don't match, adjust the props passed in Step 3 to match `ScoreResult.tsx`'s actual interface.

- [ ] **Step 5: Build**

Run: `bun run build`
Expected: Clean build with `/brand/score` in output

- [ ] **Step 6: Commit**

```bash
git add apps/web/app/brand/score/
git commit -m "feat: add brand voice scoring page at /brand/score"
```

---

## Task 6: Enable Knowledge Base by Default

**Files:**
- Modify: `apps/api/src/config.py:578` (KnowledgeBaseSettings.enable_knowledge_base default)
- Modify: `apps/web/app/knowledge/KnowledgePage.tsx`

**Prerequisite:** Task 3 (migration runner) must be complete.

- [ ] **Step 1: Flip the Knowledge Base default**

In `apps/api/src/config.py`, change the `KnowledgeBaseSettings` class:
```python
enable_knowledge_base: bool = Field(default=False)
```
to:
```python
enable_knowledge_base: bool = Field(default=True)
```

- [ ] **Step 2: Add error state to KnowledgePage**

Read `apps/web/app/knowledge/KnowledgePage.tsx` first. Then add error handling for when the KB backend returns 404 or 500. The exact change depends on the current implementation — look for the API fetch calls and wrap them with error state:

```typescript
const [backendError, setBackendError] = useState<string | null>(null)

// In the fetch effect, catch errors:
.catch((err) => {
  if (err.status === 404 || err.status === 500) {
    setBackendError('Knowledge Base requires database setup. Please run migrations and restart the server.')
  }
})

// In the render, show error state:
{backendError && (
  <div className="glass-card rounded-2xl p-8 text-center">
    <p className="text-sm text-gray-600 dark:text-gray-400">{backendError}</p>
  </div>
)}
```

- [ ] **Step 3: Run backend tests**

Run: `cd apps/api && pytest -q`
Expected: All pass. Some tests may need `ENABLE_KNOWLEDGE_BASE=false` env override if they expect KB to be disabled.

- [ ] **Step 4: Run frontend checks**

Run: `bun run type-check && bun run test:run && bun run build`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/config.py apps/web/app/knowledge/KnowledgePage.tsx
git commit -m "feat: enable Knowledge Base by default, add error state for missing migrations"
```

---

## Task 7: Fact-Check Results Component

**Files:**
- Create: `apps/web/components/content-generator/FactCheckResults.tsx`
- Modify: `apps/web/app/generate/GeneratePageClient.tsx` (import and render)

- [ ] **Step 1: Create the FactCheckResults component**

```typescript
// apps/web/components/content-generator/FactCheckResults.tsx
'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, ExclamationCircleIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import type { FactCheckResult, ClaimVerification, VerificationStatus } from '../../types/factCheck'

interface FactCheckResultsProps {
  result: FactCheckResult
}

const STATUS_CONFIG: Record<VerificationStatus, { icon: React.ElementType; color: string; label: string }> = {
  verified: { icon: CheckCircleIcon, color: 'text-emerald-500', label: 'Verified' },
  unverified: { icon: QuestionMarkCircleIcon, color: 'text-amber-500', label: 'Unverified' },
  contradicted: { icon: ExclamationCircleIcon, color: 'text-red-500', label: 'Contradicted' },
}

function ClaimRow({ claim }: { claim: ClaimVerification }) {
  const config = STATUS_CONFIG[claim.status]
  const Icon = config.icon

  return (
    <div className="flex items-start gap-3 py-3 border-b border-black/[0.04] dark:border-white/[0.04] last:border-0">
      <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${config.color}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 dark:text-gray-200">{claim.text}</p>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{claim.explanation}</p>
        <div className="mt-1 flex items-center gap-3">
          <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
          <span className="text-xs text-gray-400">{Math.round(claim.confidence * 100)}% confidence</span>
        </div>
      </div>
    </div>
  )
}

export default function FactCheckResults({ result }: FactCheckResultsProps) {
  const [expanded, setExpanded] = useState(false)
  const ToggleIcon = expanded ? ChevronUpIcon : ChevronDownIcon

  return (
    <div className="glass-panel rounded-2xl overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 text-left"
      >
        <div>
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
            Fact Check Results
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {result.verified_count} verified, {result.unverified_count} unverified, {result.contradicted_count} contradicted
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {Math.round(result.overall_confidence * 100)}%
          </span>
          <ToggleIcon className="h-4 w-4 text-gray-400" />
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{result.summary}</p>
          <div className="space-y-0">
            {result.claims.map((claim, i) => (
              <ClaimRow key={i} claim={claim} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Wire into GeneratePageClient**

In `apps/web/app/generate/GeneratePageClient.tsx`, add the import:
```typescript
import FactCheckResults from '../../components/content-generator/FactCheckResults'
```

Then after the SEO score panel in the render, add:
```typescript
{/* Fact Check (if available) */}
{blogContent.fact_check && (
  <FactCheckResults result={blogContent.fact_check} />
)}
```

- [ ] **Step 3: Run type check and build**

Run: `bun run type-check && bun run build`
Expected: Clean

- [ ] **Step 4: Commit**

```bash
git add apps/web/components/content-generator/FactCheckResults.tsx apps/web/app/generate/GeneratePageClient.tsx
git commit -m "feat: add fact-check results display in generation view"
```

---

## Task 8: "Coming Soon" Badges

**Files:**
- Modify: `apps/web/app/HomePageClient.tsx` (capabilities showcase)

- [ ] **Step 1: Add Coming Soon badge to capabilities**

In `apps/web/app/HomePageClient.tsx`, find the `CAPABILITIES` array (around line 246). The items "AI Image Generation" and "Webhooks & Integrations" need a `comingSoon: true` flag.

Update the `Capability` interface:
```typescript
interface Capability {
  icon: React.ElementType
  title: string
  description: string
  tier: 'Starter+' | 'Pro'
  comingSoon?: boolean
}
```

Add `comingSoon: true` to the "AI Image Generation" and "Webhooks & Integrations" entries.

- [ ] **Step 2: Render the badge in CapabilitiesShowcase**

In the `CapabilitiesShowcase` function, after the tier badge, add:
```typescript
{cap.comingSoon && (
  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100/80 text-gray-500 dark:bg-gray-800/60 dark:text-gray-400">
    Coming Soon
  </span>
)}
```

- [ ] **Step 3: Run type check and build**

Run: `bun run type-check && bun run build`
Expected: Clean

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/HomePageClient.tsx
git commit -m "feat: add Coming Soon badges to unfinished capabilities on homepage"
```

---

## Task 9: Honest Empty States

**Files:**
- Modify: `apps/web/app/analytics/AnalyticsPageClient.tsx` (or equivalent)
- Modify: `apps/web/app/history/HistoryPageClient.tsx` (or equivalent)

- [ ] **Step 1: Read the analytics and history page files**

Read the actual files to understand their current empty state handling. The exact paths may be `apps/web/app/analytics/` and `apps/web/app/history/`.

- [ ] **Step 2: Add empty state to analytics**

When analytics data returns zero records or an empty response, render:
```typescript
<div className="glass-card rounded-2xl p-8 text-center">
  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No content generated yet</p>
  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
    Create your first blog post to see analytics here.
  </p>
</div>
```

- [ ] **Step 3: Add empty state to history**

When history returns zero items, render:
```typescript
<div className="glass-card rounded-2xl p-8 text-center">
  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No generation history</p>
  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
    Your content will appear here after you generate something.
  </p>
</div>
```

- [ ] **Step 4: Run type check and build**

Run: `bun run type-check && bun run build`
Expected: Clean

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/analytics/ apps/web/app/history/
git commit -m "fix: add honest empty states for analytics and history pages"
```

---

## Task 10: Feature Flag Error States

**Files:**
- Modify: `apps/web/app/pricing/PricingPageClient.tsx` (or equivalent)
- Modify: `apps/web/components/content-generator/AdvancedOptions.tsx`

- [ ] **Step 1: Read the pricing page file**

Read the actual pricing page to understand how it handles Stripe checkout. When Stripe is not configured, change checkout buttons to show "Contact us" instead.

- [ ] **Step 2: Add research toggle tooltip**

In `apps/web/components/content-generator/AdvancedOptions.tsx`, the research toggle should indicate when research API keys are missing. This requires the backend to expose whether research is available.

For now, keep the toggle functional — the backend already returns a helpful error if research keys are missing when the user tries to generate with research enabled.

- [ ] **Step 3: Run all verification checks**

Run: `bun run type-check && bun run lint && bun run test:run && bun run build`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/pricing/ apps/web/components/content-generator/AdvancedOptions.tsx
git commit -m "fix: show Contact us when Stripe is not configured, improve feature flag UX"
```

---

## Final Verification

After all tasks are complete:

- [ ] **Run full frontend verification**

```bash
bun run lint && bun run type-check && bun run test:run && bun run build
```

- [ ] **Run full backend verification**

```bash
cd apps/api && pytest -q
```

- [ ] **Verify success criteria against spec**

Walk through each of the 9 success criteria in the spec and confirm they're met.
