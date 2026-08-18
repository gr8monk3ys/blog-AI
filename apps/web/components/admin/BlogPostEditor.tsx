'use client'

import { useEffect, useMemo, useState } from 'react'

interface BlogPost {
  id?: string
  title: string
  slug: string
  excerpt: string
  body: string
  tags: string[]
  status: 'draft' | 'published' | 'archived'
  published_at?: string | null
  seo_title?: string | null
  seo_description?: string | null
}

const emptyPost: BlogPost = {
  title: '',
  slug: '',
  excerpt: '',
  body: '',
  tags: [],
  status: 'draft',
}

const slugify = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')

export default function BlogPostEditor() {
  const [adminKey, setAdminKey] = useState('')
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [activeSlug, setActiveSlug] = useState<string | null>(null)
  const [form, setForm] = useState<BlogPost>(emptyPost)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  const isConfigured = adminKey.length > 10

  const activePost = useMemo(
    () => posts.find((post) => post.slug === activeSlug) || null,
    [posts, activeSlug]
  )

  useEffect(() => {
    if (activePost) {
      setForm({
        ...activePost,
        excerpt: activePost.excerpt || '',
        body: activePost.body || '',
        tags: activePost.tags || [],
        status: activePost.status || 'draft',
      })
    }
  }, [activePost])

  const loadPosts = async () => {
    if (!isConfigured) return
    setLoading(true)
    setStatus(null)
    try {
      const response = await fetch('/api/blog-posts', {
        headers: { 'x-admin-key': adminKey },
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || 'Failed to load posts')
      }
      setPosts(payload.data || [])
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setLoading(false)
    }
  }

  const savePost = async () => {
    if (!isConfigured) return
    setLoading(true)
    setStatus(null)
    try {
      const response = await fetch('/api/blog-posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-admin-key': adminKey,
        },
        body: JSON.stringify({
          ...form,
          tags: form.tags,
        }),
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || 'Failed to save post')
      }
      setStatus('Post saved.')
      await loadPosts()
      setActiveSlug(payload.data?.slug || form.slug)
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Failed to save post')
    } finally {
      setLoading(false)
    }
  }

  const deletePost = async () => {
    if (!activeSlug || !isConfigured) return
    setLoading(true)
    setStatus(null)
    try {
      const response = await fetch(`/api/blog-posts/${activeSlug}`, {
        method: 'DELETE',
        headers: { 'x-admin-key': adminKey },
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || 'Failed to delete post')
      }
      setStatus('Post deleted.')
      setActiveSlug(null)
      setForm(emptyPost)
      await loadPosts()
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[280px,1fr] gap-6">
      <aside className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Admin Access</div>
        <input
          type="password"
          value={adminKey}
          onChange={(event) => setAdminKey(event.target.value)}
          placeholder="BLOG_ADMIN_KEY"
          className="w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
        />
        <button
          type="button"
          onClick={loadPosts}
          disabled={!isConfigured || loading}
          className="mt-3 w-full text-sm font-medium bg-amber-600 text-white rounded-lg py-2 disabled:opacity-50"
        >
          Load Posts
        </button>

        <div className="mt-6 text-xs font-medium text-gray-500 dark:text-gray-400">Posts</div>
        <div className="mt-2 space-y-2 max-h-[520px] overflow-y-auto">
          {posts.length === 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-400">No posts loaded yet.</div>
          )}
          {posts.map((post) => (
            <button
              key={post.slug}
              type="button"
              onClick={() => setActiveSlug(post.slug)}
              className={`w-full text-left text-xs px-3 py-2 rounded-lg border ${
                post.slug === activeSlug
                  ? 'border-amber-400 dark:border-amber-600 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                  : 'border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              {post.title}
            </button>
          ))}
        </div>
      </aside>

      <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Post Editor</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{form.title || 'New Post'}</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => {
                setForm({ ...form, slug: slugify(form.title) })
              }}
              className="text-xs px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              Generate Slug
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveSlug(null)
                setForm(emptyPost)
              }}
              className="text-xs px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              New Draft
            </button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">Title</label>
            <input
              type="text"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">Slug</label>
            <input
              type="text"
              value={form.slug}
              onChange={(event) => setForm({ ...form, slug: event.target.value })}
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">Status</label>
            <select
              value={form.status}
              onChange={(event) =>
                setForm({ ...form, status: event.target.value as BlogPost['status'] })
              }
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">Published At</label>
            <input
              type="datetime-local"
              value={form.published_at ? form.published_at.slice(0, 16) : ''}
              onChange={(event) =>
                setForm({
                  ...form,
                  published_at: event.target.value
                    ? new Date(event.target.value).toISOString()
                    : null,
                })
              }
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="text-xs text-gray-500 dark:text-gray-400">Excerpt</label>
          <textarea
            value={form.excerpt}
            onChange={(event) => setForm({ ...form, excerpt: event.target.value })}
            className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 min-h-[90px]"
          />
        </div>

        <div className="mt-4">
          <label className="text-xs text-gray-500 dark:text-gray-400">Body</label>
          <textarea
            value={form.body}
            onChange={(event) => setForm({ ...form, body: event.target.value })}
            className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 min-h-[240px]"
          />
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">Tags (comma separated)</label>
            <input
              type="text"
              value={form.tags.join(', ')}
              onChange={(event) =>
                setForm({
                  ...form,
                  tags: event.target.value
                    .split(',')
                    .map((tag) => tag.trim())
                    .filter(Boolean),
                })
              }
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">SEO Title</label>
            <input
              type="text"
              value={form.seo_title || ''}
              onChange={(event) => setForm({ ...form, seo_title: event.target.value })}
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">SEO Description</label>
            <textarea
              value={form.seo_description || ''}
              onChange={(event) =>
                setForm({ ...form, seo_description: event.target.value })
              }
              className="mt-1 w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 min-h-[80px]"
            />
          </div>
        </div>

        {status && <div className="mt-4 text-xs text-gray-600 dark:text-gray-400">{status}</div>}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={savePost}
            disabled={!isConfigured || loading}
            className="px-4 py-2 text-sm font-medium bg-amber-600 text-white rounded-lg disabled:opacity-50"
          >
            Save Post
          </button>
          {activeSlug && (
            <button
              type="button"
              onClick={deletePost}
              disabled={!isConfigured || loading}
              className="px-4 py-2 text-sm font-medium border border-gray-200 dark:border-gray-800 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50"
            >
              Delete Post
            </button>
          )}
        </div>
      </section>
    </div>
  )
}
