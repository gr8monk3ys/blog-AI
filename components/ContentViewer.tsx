import { useCallback, useEffect, useMemo, useState } from 'react';
import { Popover } from '@headlessui/react';
import BookViewer from './BookViewer';
import BookEditor from './BookEditor';
import ContentEditor from './ContentEditor';
import ExportMenu, { ExportContent, ExportFormat } from './ExportMenu';
import ContentScore from './tools/ContentScore'
import PlagiarismCheck from './tools/PlagiarismCheck'
import ContentRating from './ContentRating'
import { Book } from '../types/book';
import { BlogContent, ContentGenerationResponse, BlogSection, BookContent } from '../types/content';
import { API_ENDPOINTS, apiFetch, getDefaultHeaders } from '../lib/api';
import { toolsApi } from '../lib/tools-api'
import type { ContentScoreResult } from './tools/ContentScore'
import type { PlagiarismCheckResponse, PlagiarismCheckResult } from '../types/plagiarism'

function blogToMarkdown(blog: BlogContent): string {
  let markdown = `# ${blog.title}\n\n`;
  if (blog.description) {
    markdown += `> ${blog.description}\n\n`;
  }
  for (const section of blog.sections || []) {
    markdown += `## ${section.title}\n\n`;
    for (const subtopic of section.subtopics || []) {
      markdown += `### ${subtopic.title}\n\n`;
      markdown += `${subtopic.content}\n\n`;
    }
  }
  if (blog.sources?.length) {
    markdown += `---\n\n## Sources\n\n`;
    for (const s of blog.sources) {
      markdown += `- [${s.id}] ${s.title} (${s.url})\n`;
    }
    markdown += `\n`;
  }
  return markdown;
}

function bookToMarkdown(book: BookContent): string {
  let markdown = `# ${book.title}\n\n`;
  if (book.description) {
    markdown += `> ${book.description}\n\n`;
  }
  for (const chapter of book.chapters || []) {
    markdown += `## Chapter ${chapter.number}: ${chapter.title}\n\n`;
    for (const topic of chapter.topics || []) {
      markdown += `### ${topic.title}\n\n`;
      markdown += `${topic.content}\n\n`;
    }
  }
  if (book.sources?.length) {
    markdown += `---\n\n## Sources\n\n`;
    for (const s of book.sources) {
      markdown += `- [${s.id}] ${s.title} (${s.url})\n`;
    }
    markdown += `\n`;
  }
  return markdown;
}

interface ContentViewerProps {
  content: ContentGenerationResponse;
  contentId?: string;
}

function useContentViewerView({ content, contentId }: ContentViewerProps) {
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null);
  const [editInstructions, setEditInstructions] = useState('');
  const [isEditingBook, setIsEditingBook] = useState(false);
  const [isInlineEditing, setIsInlineEditing] = useState(false);
  const [contentScore, setContentScore] = useState<ContentScoreResult | null>(null)
  const [scoringLoading, setScoringLoading] = useState(false)
  const [plagiarismResult, setPlagiarismResult] = useState<PlagiarismCheckResult | null>(null)
  const [plagiarismLoading, setPlagiarismLoading] = useState(false)
  const [plagiarismError, setPlagiarismError] = useState<string | null>(null)

  // Derive a stable identifier for the feedback system
  const feedbackContentId = useMemo(() => {
    if (contentId) return contentId
    // Fall back to a slug of the title + type
    const title = content.content?.title || ''
    return `${content.type}-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 80)}`
  }, [contentId, content])

  // Stable key for the inline content editor localStorage persistence
  const editorStorageKey = `editor-${feedbackContentId}`

  // Convert BookContent to Book type for the editor
  const getBookData = (): Book | null => {
    if (content.type === 'book') {
      const bookContent = content.content as BookContent;
      return {
        title: bookContent.title,
        chapters: bookContent.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          topics: ch.topics
        })),
        tags: bookContent.tags,
        date: bookContent.date
      };
    }
    return null;
  };

  const [bookData, setBookData] = useState<Book | null>(() => getBookData());
  const [exportToast, setExportToast] = useState<{
    show: boolean;
    message: string;
    type: 'success' | 'error';
  }>({ show: false, message: '', type: 'success' });

  const analysisText = useMemo((): string => {
    if (content.type === 'blog') {
      return blogToMarkdown(content.content as BlogContent);
    }
    if (content.type === 'book') {
      return bookToMarkdown(content.content as BookContent);
    }
    return '';
  }, [content]);

  const analysisTags = useMemo((): string[] => {
    const tags = content?.content?.tags;
    return Array.isArray(tags) ? tags : [];
  }, [content]);

  const resetAnalysisState = useCallback(() => {
    setPlagiarismResult(null);
    setPlagiarismError(null);
    setContentScore(null);
    setScoringLoading(false);
  }, []);

  const beginScoring = useCallback(() => {
    setScoringLoading(true);
  }, []);

  const applyScoringResult = useCallback((score: ContentScoreResult | null) => {
    setContentScore(score);
    setScoringLoading(false);
  }, []);

  useEffect(() => {
    let mounted = true;
    const text = analysisText;

    resetAnalysisState();

    if (!text || text.trim().length < 50) {
      return () => {
        mounted = false;
      };
    }

    beginScoring();
    (async () => {
      try {
        const score = await toolsApi.scoreGenericContent({
          text,
          keywords: analysisTags.length > 0 ? analysisTags : undefined,
        });
        if (!mounted) return;
        applyScoringResult(score);
      } catch {
        if (!mounted) return;
        applyScoringResult(null);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [analysisText, analysisTags, applyScoringResult, beginScoring, resetAnalysisState]);

  const runPlagiarismCheck = async (opts?: { skipCache?: boolean }) => {
    const text = analysisText;
    if (!text?.trim()) return;
    if (text.trim().length < 50) {
      setPlagiarismError('Add more content before running a plagiarism check (min 50 characters).');
      return;
    }

    setPlagiarismLoading(true);
    setPlagiarismError(null);

    try {
      const title = String(content.content?.title || '');
      const payload = await apiFetch<PlagiarismCheckResponse>(
        API_ENDPOINTS.content.checkPlagiarism,
        {
          method: 'POST',
          body: JSON.stringify({
            content: text,
            title,
            exclude_urls: [],
            skip_cache: opts?.skipCache === true,
          }),
        }
      );

      if (!payload.success) {
        throw new Error(payload.error || 'Plagiarism check failed');
      }

      setPlagiarismResult(payload.data || null);
    } catch (err) {
      const status = (err as Error & { status?: number })?.status;
      if (status === 401 || status === 403) {
        setPlagiarismError('Sign in required to run checks.');
      } else if (status === 429) {
        setPlagiarismError('Usage limit reached. Upgrade your plan to run checks.');
      } else {
        setPlagiarismError(err instanceof Error ? err.message : 'Plagiarism check failed');
      }
    } finally {
      setPlagiarismLoading(false);
    }
  };

  // Get export content based on content type
  const getExportContent = (): ExportContent => {
    if (content.type === 'blog') {
      return {
        title: content.content.title,
        content: analysisText,
        type: 'blog',
        metadata: {
          date: content.content.date,
          description: content.content.description,
          tags: content.content.tags,
        },
      };
    } else {
      const book = content.content as BookContent;
      return {
        title: book.title,
        content: analysisText,
        type: 'book',
        metadata: {
          date: book.date,
          description: book.description,
          tags: book.tags,
        },
      };
    }
  };

  // Handle export completion with toast notification
  const handleExportComplete = (format: ExportFormat, success: boolean) => {
    const formatNames: Record<ExportFormat, string> = {
      markdown: 'Markdown',
      html: 'HTML',
      text: 'Plain Text',
      pdf: 'PDF',
      clipboard: 'Clipboard',
      wordpress: 'WordPress',
      medium: 'Medium',
    };

    if (success) {
      const action = ['clipboard', 'wordpress', 'medium'].includes(format)
        ? 'copied'
        : 'downloaded';
      setExportToast({
        show: true,
        message: `${formatNames[format]} ${action} successfully`,
        type: 'success',
      });
    } else {
      setExportToast({
        show: true,
        message: `Failed to export as ${formatNames[format]}`,
        type: 'error',
      });
    }

    setTimeout(() => setExportToast({ show: false, message: '', type: 'success' }), 3000);
  };

  const handleSectionEdit = async (sectionId: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.editSection, {
        method: 'POST',
        headers: await getDefaultHeaders(),
        body: JSON.stringify({
          file_path: content.file_path || '',
          section_id: sectionId,
          instructions: editInstructions,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // Refresh content or update locally
        setEditingSectionId(null);
        setEditInstructions('');
      } else {
        throw new Error(data.detail || 'Failed to update section');
      }
    } catch (error) {
      console.error('Error updating section:', error);
      setExportToast({
        show: true,
        message: 'Failed to update section. Please try again.',
        type: 'error',
      });
      setTimeout(() => setExportToast({ show: false, message: '', type: 'success' }), 3000);
    }
  };

  const handleBookSave = (updatedBook: Book): void => {
    setBookData(updatedBook);
    setIsEditingBook(false);
  };

  if (content.type === 'blog') {
    const sources = content.content.sources || []

    // When the inline editor is active, render ContentEditor with the full
    // markdown representation of the blog post.
    if (isInlineEditing) {
      return (
        <div className="mt-8">
          {/* Toast notification */}
          {exportToast.show && (
            <div
              className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
                exportToast.type === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : 'bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300'
              }`}
            >
              <span className="text-sm font-medium">{exportToast.message}</span>
            </div>
          )}

          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{content.content.title}</h1>
            <div className="flex items-center gap-3">
              <ExportMenu
                content={getExportContent()}
                onExportComplete={handleExportComplete}
              />
              <button
                type="button"
                onClick={() => setIsInlineEditing(false)}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors"
              >
                Back to View
              </button>
            </div>
          </div>

          <ContentEditor
            initialContent={analysisText}
            storageKey={editorStorageKey}
            title={content.content.title}
          />

          <ContentRating contentId={feedbackContentId} />
        </div>
      )
    }

    return (
      <div className="mt-8">
        {/* Toast notification */}
        {exportToast.show && (
          <div
            className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
              exportToast.type === 'success'
                ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}
          >
            <span className="text-sm font-medium">{exportToast.message}</span>
          </div>
        )}

        {/* Header with export + edit buttons */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900">{content.content.title}</h1>
          <div className="flex items-center gap-3">
            <ExportMenu
              content={getExportContent()}
              onExportComplete={handleExportComplete}
            />
            <button
              type="button"
              onClick={() => setIsInlineEditing(true)}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-amber-600 border border-transparent rounded-lg hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors"
            >
              Edit Content
            </button>
          </div>
        </div>

        {/* Content analysis */}
        {(contentScore || scoringLoading) && (
          <div className="mb-6">
            <ContentScore
              scores={contentScore!}
              isLoading={scoringLoading}
              showDetails={true}
            />
          </div>
        )}

        <PlagiarismCheck
          result={plagiarismResult}
          loading={plagiarismLoading}
          error={plagiarismError}
          onRun={runPlagiarismCheck}
        />

        <div className="prose prose-lg max-w-none">
          {content.content.sections.map((section: BlogSection) => {
            const sectionId = `${section.title}-${section.subtopics.length}`
            return (
            <Popover key={sectionId} className="relative">
              <div
                className="hover:bg-gray-50 dark:hover:bg-gray-800 p-2 rounded transition-colors cursor-pointer group"
                onMouseEnter={() => setEditingSectionId(sectionId)}
                onMouseLeave={() => setEditingSectionId(null)}
              >
                <h2 className="text-xl font-semibold">{section.title}</h2>
                <div className="prose">
                  {section.subtopics.map((subtopic) => (
                    <div key={`${subtopic.title}-${subtopic.content.slice(0, 24)}`}>
                      <h3>{subtopic.title}</h3>
                      <p>{subtopic.content}</p>
                    </div>
                  ))}
                </div>

                {editingSectionId === sectionId && (
                  <Popover.Panel className="absolute z-10 w-96 px-4 mt-3 transform -translate-x-1/2 left-1/2">
                    <div className="overflow-hidden rounded-lg shadow-lg ring-1 ring-black ring-opacity-5">
                      <div className="relative bg-white dark:bg-gray-900 p-4">
                        <textarea
                          className="w-full p-2 border dark:border-gray-700 rounded dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
                          placeholder="How would you like to change this section?"
                          value={editInstructions}
                          onChange={(e) => setEditInstructions(e.target.value)}
                          rows={4}
                        />
                        <button
                          onClick={() => handleSectionEdit(sectionId)}
                          className="mt-2 w-full bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700"
                        >
                          Update Section
                        </button>
                      </div>
                    </div>
                  </Popover.Panel>
                )}
              </div>
            </Popover>
            )
          })}
        </div>

        {sources.length > 0 && (
          <div className="mt-10 border-t border-gray-200 dark:border-gray-800 pt-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Sources</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {sources.map((s) => (
                <li key={s.id} className="text-gray-700 dark:text-gray-300">
                  <span className="font-medium">[{s.id}]</span>{' '}
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-amber-700 hover:text-amber-800 underline"
                  >
                    {s.title}
                  </a>
                  {s.provider ? <span className="text-gray-400 dark:text-gray-500"> ({s.provider})</span> : null}
                  {s.snippet ? <div className="text-gray-500 dark:text-gray-400 mt-1">{s.snippet}</div> : null}
                </li>
              ))}
            </ul>
          </div>
        )}

        <ContentRating contentId={feedbackContentId} />
      </div>
    );
  }

  if (content.type === 'book') {
    const filePath = content.file_path || '';
    const sources = (content.content as BookContent).sources || []

    if (isEditingBook && bookData) {
      return (
        <BookEditor
          book={bookData}
          filePath={filePath}
          onSave={handleBookSave}
        />
      );
    }

    // Book inline markdown editor
    if (isInlineEditing) {
      return (
        <div className="mt-8">
          {exportToast.show && (
            <div
              className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
                exportToast.type === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : 'bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300'
              }`}
            >
              <span className="text-sm font-medium">{exportToast.message}</span>
            </div>
          )}

          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{content.content.title}</h1>
            <div className="flex items-center gap-3">
              <ExportMenu
                content={getExportContent()}
                onExportComplete={handleExportComplete}
              />
              <button
                type="button"
                onClick={() => setIsInlineEditing(false)}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors"
              >
                Back to View
              </button>
            </div>
          </div>

          <ContentEditor
            initialContent={analysisText}
            storageKey={editorStorageKey}
            title={content.content.title}
          />

          <ContentRating contentId={feedbackContentId} />
        </div>
      )
    }

    return (
      <div className="mt-8">
        {/* Toast notification */}
        {exportToast.show && (
          <div
            className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
              exportToast.type === 'success'
                ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}
          >
            <span className="text-sm font-medium">{exportToast.message}</span>
          </div>
        )}

        <div className="flex justify-end gap-3 mb-4">
          <ExportMenu
            content={getExportContent()}
            onExportComplete={handleExportComplete}
          />
          <button
            type="button"
            onClick={() => setIsInlineEditing(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-amber-600 border border-transparent rounded-lg hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors"
          >
            Edit Content
          </button>
          <button
            onClick={() => setIsEditingBook(true)}
            className="bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700"
          >
            Edit Book
          </button>
        </div>

          {/* Content analysis */}
          {(contentScore || scoringLoading) && (
            <div className="mb-6">
              <ContentScore
                scores={contentScore!}
                isLoading={scoringLoading}
                showDetails={true}
              />
            </div>
          )}

          <PlagiarismCheck
            result={plagiarismResult}
            loading={plagiarismLoading}
            error={plagiarismError}
            onRun={runPlagiarismCheck}
          />

		        {bookData ? (
		          <BookViewer book={bookData} filePath={filePath} />
		        ) : (
          <div>
            <h1 className="text-3xl font-bold">{content.content.title}</h1>
            {filePath && (
              <>
                <p className="mt-4">
                  Your book has been generated and saved to: <br />
                  <code className="bg-gray-100 dark:bg-gray-800 dark:text-gray-200 px-2 py-1 rounded">{filePath}</code>
                </p>
                <button
                  onClick={() => window.open(`/api/download?path=${encodeURIComponent(filePath)}`)}
                  className="mt-4 bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700"
                >
                  Download Book
                </button>
              </>
            )}
          </div>
	        )}

        {sources.length > 0 && (
          <div className="mt-10 border-t border-gray-200 dark:border-gray-800 pt-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Sources</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {sources.map((s) => (
                <li key={s.id} className="text-gray-700 dark:text-gray-300">
                  <span className="font-medium">[{s.id}]</span>{' '}
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-amber-700 hover:text-amber-800 underline"
                  >
                    {s.title}
                  </a>
                  {s.provider ? <span className="text-gray-400 dark:text-gray-500"> ({s.provider})</span> : null}
                  {s.snippet ? <div className="text-gray-500 dark:text-gray-400 mt-1">{s.snippet}</div> : null}
                </li>
              ))}
            </ul>
          </div>
        )}

        <ContentRating contentId={feedbackContentId} />
      </div>
    );
  }

  return null;
}

export default function ContentViewer(props: ContentViewerProps) {
  return useContentViewerView(props)
}
