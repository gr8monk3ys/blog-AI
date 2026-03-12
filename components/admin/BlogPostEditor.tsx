'use client'

import { useState } from 'react'

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

const normalizePost = (post: BlogPost): BlogPost => ({
  ...post,
  excerpt: post.excerpt || '',
  body: post.body || '',
  tags: post.tags || [],
  status: post.status || 'draft',
})

interface PostsSidebarProps {
  adminKey: string
  isConfigured: boolean
  loading: boolean
  posts: BlogPost[]
  activeSlug: string | null
  onAdminKeyChange: (value: string) => void
  onLoadPosts: () => void
  onSelectPost: (post: BlogPost) => void
}

function PostsSidebar({
  adminKey,
  isConfigured,
  loading,
  posts,
  activeSlug,
  onAdminKeyChange,
  onLoadPosts,
  onSelectPost,
}: PostsSidebarProps) {
  return (
    <aside className="bg-white border border-neutral-200 rounded-2xl p-4">
      <div className="text-sm font-semibold text-neutral-900 mb-3">Admin Access</div>
      <label htmlFor="blog-admin-key" className="sr-only">
        Admin key
      </label>
      <input
        id="blog-admin-key"
        type="password"
        value={adminKey}
        onChange={(event) => onAdminKeyChange(event.target.value)}
        placeholder="BLOG_ADMIN_KEY"
        className="w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
      />
      <button
        type="button"
        onClick={onLoadPosts}
        disabled={!isConfigured || loading}
        className="mt-3 w-full text-sm font-medium bg-amber-600 text-white rounded-lg py-2 disabled:opacity-50"
      >
        Load Posts
      </button>

      <div className="mt-6 text-xs font-medium text-neutral-500">Posts</div>
      <div className="mt-2 space-y-2 max-h-[520px] overflow-y-auto">
        {posts.length === 0 && (
          <div className="text-xs text-neutral-500">No posts loaded yet.</div>
        )}
        {posts.map((post) => (
          <button
            key={post.slug}
            type="button"
            onClick={() => onSelectPost(post)}
            className={`w-full text-left text-xs px-3 py-2 rounded-lg border ${
              post.slug === activeSlug
                ? 'border-amber-400 bg-amber-50 text-amber-700'
                : 'border-neutral-200 hover:bg-neutral-50'
            }`}
          >
            {post.title}
          </button>
        ))}
      </div>
    </aside>
  )
}

interface EditorFormProps {
  form: BlogPost
  activeSlug: string | null
  loading: boolean
  isConfigured: boolean
  status: string | null
  onUpdateForm: (patch: Partial<BlogPost>) => void
  onGenerateSlug: () => void
  onResetDraft: () => void
  onSavePost: () => void
  onDeletePost: () => void
}

function EditorForm({
  form,
  activeSlug,
  loading,
  isConfigured,
  status,
  onUpdateForm,
  onGenerateSlug,
  onResetDraft,
  onSavePost,
  onDeletePost,
}: EditorFormProps) {
  return (
    <section className="bg-white border border-neutral-200 rounded-2xl p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wide text-neutral-500">Post Editor</div>
          <div className="text-lg font-semibold text-neutral-900">{form.title || 'New Post'}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onGenerateSlug}
            className="text-xs px-3 py-2 rounded-lg border border-neutral-200 hover:bg-neutral-50"
          >
            Generate Slug
          </button>
          <button
            type="button"
            onClick={onResetDraft}
            className="text-xs px-3 py-2 rounded-lg border border-neutral-200 hover:bg-neutral-50"
          >
            New Draft
          </button>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="blog-post-title" className="text-xs text-neutral-500">
            Title
          </label>
          <input
            id="blog-post-title"
            type="text"
            value={form.title}
            onChange={(event) => onUpdateForm({ title: event.target.value })}
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="blog-post-slug" className="text-xs text-neutral-500">
            Slug
          </label>
          <input
            id="blog-post-slug"
            type="text"
            value={form.slug}
            onChange={(event) => onUpdateForm({ slug: event.target.value })}
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="blog-post-status" className="text-xs text-neutral-500">
            Status
          </label>
          <select
            id="blog-post-status"
            value={form.status}
            onChange={(event) =>
              onUpdateForm({ status: event.target.value as BlogPost['status'] })
            }
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
          >
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div>
          <label htmlFor="blog-post-published-at" className="text-xs text-neutral-500">
            Published At
          </label>
          <input
            id="blog-post-published-at"
            type="datetime-local"
            value={form.published_at ? form.published_at.slice(0, 16) : ''}
            onChange={(event) =>
              onUpdateForm({
                published_at: event.target.value
                  ? new Date(event.target.value).toISOString()
                  : null,
              })
            }
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
          />
        </div>
      </div>

      <div className="mt-4">
        <label htmlFor="blog-post-excerpt" className="text-xs text-neutral-500">
          Excerpt
        </label>
        <textarea
          id="blog-post-excerpt"
          value={form.excerpt}
          onChange={(event) => onUpdateForm({ excerpt: event.target.value })}
          className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2 min-h-[90px]"
        />
      </div>

      <div className="mt-4">
        <label htmlFor="blog-post-body" className="text-xs text-neutral-500">
          Body
        </label>
        <textarea
          id="blog-post-body"
          value={form.body}
          onChange={(event) => onUpdateForm({ body: event.target.value })}
          className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2 min-h-[240px]"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="blog-post-tags" className="text-xs text-neutral-500">
            Tags (comma separated)
          </label>
          <input
            id="blog-post-tags"
            type="text"
            value={form.tags.join(', ')}
            onChange={(event) =>
              onUpdateForm({
                tags: event.target.value
                  .split(',')
                  .map((tag) => tag.trim())
                  .filter(Boolean),
              })
            }
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="blog-post-seo-title" className="text-xs text-neutral-500">
            SEO Title
          </label>
          <input
            id="blog-post-seo-title"
            type="text"
            value={form.seo_title || ''}
            onChange={(event) => onUpdateForm({ seo_title: event.target.value })}
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="blog-post-seo-description" className="text-xs text-neutral-500">
            SEO Description
          </label>
          <textarea
            id="blog-post-seo-description"
            value={form.seo_description || ''}
            onChange={(event) => onUpdateForm({ seo_description: event.target.value })}
            className="mt-1 w-full text-sm border border-neutral-200 rounded-lg px-3 py-2 min-h-[80px]"
          />
        </div>
      </div>

      {status && <div className="mt-4 text-xs text-neutral-600">{status}</div>}

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onSavePost}
          disabled={!isConfigured || loading}
          className="px-4 py-2 text-sm font-medium bg-amber-600 text-white rounded-lg disabled:opacity-50"
        >
          Save Post
        </button>
        {activeSlug && (
          <button
            type="button"
            onClick={onDeletePost}
            disabled={!isConfigured || loading}
            className="px-4 py-2 text-sm font-medium border border-neutral-200 rounded-lg text-neutral-700 hover:bg-neutral-50 disabled:opacity-50"
          >
            Delete Post
          </button>
        )}
      </div>
    </section>
  )
}

interface BlogPostEditorState {
  adminKey: string
  posts: BlogPost[]
  activeSlug: string | null
  loading: boolean
  status: string | null
}

export default function BlogPostEditor() {
  const [editorState, setEditorState] = useState<BlogPostEditorState>({
    adminKey: '',
    posts: [],
    activeSlug: null,
    loading: false,
    status: null,
  })
  const [form, setForm] = useState<BlogPost>(emptyPost)

  const { adminKey, posts, activeSlug, loading, status } = editorState
  const isConfigured = adminKey.length > 10

  const updateEditorState = (patch: Partial<BlogPostEditorState>) => {
    setEditorState((current) => ({ ...current, ...patch }))
  }

  const syncPosts = (nextPosts: BlogPost[], nextActiveSlug: string | null = activeSlug) => {
    updateEditorState({ posts: nextPosts })
    if (!nextActiveSlug) {
      return
    }

    const matchingPost = nextPosts.find((post) => post.slug === nextActiveSlug)
    if (matchingPost) {
      setForm(normalizePost(matchingPost))
    }
  }

  const selectPost = (post: BlogPost) => {
    updateEditorState({
      activeSlug: post.slug,
      status: null,
    })
    setForm(normalizePost(post))
  }

  const resetDraft = () => {
    updateEditorState({
      activeSlug: null,
      status: null,
    })
    setForm(emptyPost)
  }

  const updateForm = (patch: Partial<BlogPost>) => {
    setForm((current) => ({ ...current, ...patch }))
  }

  const loadPosts = async (nextActiveSlug: string | null = activeSlug) => {
    if (!isConfigured) return
    updateEditorState({
      loading: true,
      status: null,
    })
    try {
      const response = await fetch('/api/blog-posts', {
        headers: { 'x-admin-key': adminKey },
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || 'Failed to load posts')
      }
      syncPosts(payload.data || [], nextActiveSlug)
    } catch (err) {
      updateEditorState({
        status: err instanceof Error ? err.message : 'Failed to load posts',
      })
    } finally {
      updateEditorState({ loading: false })
    }
  }

  const savePost = async () => {
    if (!isConfigured) return
    updateEditorState({
      loading: true,
      status: null,
    })
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
      const savedSlug = payload.data?.slug || form.slug
      updateEditorState({
        activeSlug: savedSlug,
        status: 'Post saved.',
      })
      await loadPosts(savedSlug)
    } catch (err) {
      updateEditorState({
        status: err instanceof Error ? err.message : 'Failed to save post',
      })
    } finally {
      updateEditorState({ loading: false })
    }
  }

  const deletePost = async () => {
    if (!activeSlug || !isConfigured) return
    updateEditorState({
      loading: true,
      status: null,
    })
    try {
      const response = await fetch(`/api/blog-posts/${activeSlug}`, {
        method: 'DELETE',
        headers: { 'x-admin-key': adminKey },
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || 'Failed to delete post')
      }
      updateEditorState({
        activeSlug: null,
        status: 'Post deleted.',
      })
      setForm(emptyPost)
      await loadPosts(null)
    } catch (err) {
      updateEditorState({
        status: err instanceof Error ? err.message : 'Failed to delete post',
      })
    } finally {
      updateEditorState({ loading: false })
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[280px,1fr] gap-6">
      <PostsSidebar
        adminKey={adminKey}
        isConfigured={isConfigured}
        loading={loading}
        posts={posts}
        activeSlug={activeSlug}
        onAdminKeyChange={(value) => updateEditorState({ adminKey: value })}
        onLoadPosts={() => void loadPosts()}
        onSelectPost={selectPost}
      />

      <EditorForm
        form={form}
        activeSlug={activeSlug}
        loading={loading}
        isConfigured={isConfigured}
        status={status}
        onUpdateForm={updateForm}
        onGenerateSlug={() => updateForm({ slug: slugify(form.title) })}
        onResetDraft={resetDraft}
        onSavePost={() => void savePost()}
        onDeletePost={() => void deletePost()}
      />
    </div>
  )
}
