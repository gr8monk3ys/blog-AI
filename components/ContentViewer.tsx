import { useEffect, useMemo, useState } from 'react';
import { Popover } from '@headlessui/react';
import BookViewer from './BookViewer';
import BookEditor from './BookEditor';
import ExportMenu, { ExportContent, ExportFormat } from './ExportMenu';
import ContentScore from './tools/ContentScore'
import PlagiarismCheck from './tools/PlagiarismCheck'
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
}

export default function ContentViewer({ content }: ContentViewerProps) {
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null);
  const [editInstructions, setEditInstructions] = useState('');
  const [isEditingBook, setIsEditingBook] = useState(false);
  const [contentScore, setContentScore] = useState<ContentScoreResult | null>(null)
  const [scoringLoading, setScoringLoading] = useState(false)
  const [plagiarismResult, setPlagiarismResult] = useState<PlagiarismCheckResult | null>(null)
  const [plagiarismLoading, setPlagiarismLoading] = useState(false)
  const [plagiarismError, setPlagiarismError] = useState<string | null>(null)

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

  const [bookData, setBookData] = useState<Book | null>(getBookData());
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
    const tags = (content?.content as any)?.tags;
    return Array.isArray(tags) ? tags : [];
  }, [content]);

  useEffect(() => {
    let mounted = true;
    const text = analysisText;

    setPlagiarismResult(null);
    setPlagiarismError(null);
    setContentScore(null);
    setScoringLoading(false);

    if (!text || text.trim().length < 50) {
      return () => {
        mounted = false;
      };
    }

    setScoringLoading(true);
    (async () => {
      try {
        const score = await toolsApi.scoreGenericContent({
          text,
          keywords: analysisTags.length > 0 ? analysisTags : undefined,
        });
        if (!mounted) return;
        setContentScore(score);
      } catch {
        if (!mounted) return;
        setContentScore(null);
      } finally {
        if (mounted) setScoringLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [analysisText, analysisTags]);

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
      const title = String((content.content as any)?.title || '');
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
    } catch (err: any) {
      const status = err?.status;
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

	        {/* Header with export button */}
	        <div className="flex items-center justify-between mb-6">
	          <h1 className="text-3xl font-bold text-gray-900">{content.content.title}</h1>
	          <ExportMenu
	            content={getExportContent()}
	            onExportComplete={handleExportComplete}
	          />
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
		        {content.content.sections.map((section: BlogSection, index: number) => (
          <Popover key={`section-${index}`} className="relative">
            <div
              className="hover:bg-gray-50 p-2 rounded transition-colors cursor-pointer group"
              onMouseEnter={() => setEditingSectionId(`section-${index}`)}
              onMouseLeave={() => setEditingSectionId(null)}
            >
              <h2 className="text-xl font-semibold">{section.title}</h2>
              <div className="prose">
                {section.subtopics.map((subtopic, subIndex) => (
                  <div key={subIndex}>
                    <h3>{subtopic.title}</h3>
                    <p>{subtopic.content}</p>
                  </div>
                ))}
              </div>

              {editingSectionId === `section-${index}` && (
                <Popover.Panel className="absolute z-10 w-96 px-4 mt-3 transform -translate-x-1/2 left-1/2">
                  <div className="overflow-hidden rounded-lg shadow-lg ring-1 ring-black ring-opacity-5">
                    <div className="relative bg-white p-4">
                      <textarea
                        className="w-full p-2 border rounded"
                        placeholder="How would you like to change this section?"
                        value={editInstructions}
                        onChange={(e) => setEditInstructions(e.target.value)}
                        rows={4}
                      />
                      <button
                        onClick={() => handleSectionEdit(`section-${index}`)}
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
	        ))}
	        </div>

        {sources.length > 0 && (
          <div className="mt-10 border-t border-gray-200 pt-6">
            <h2 className="text-lg font-semibold text-gray-900">Sources</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {sources.map((s) => (
                <li key={s.id} className="text-gray-700">
                  <span className="font-medium">[{s.id}]</span>{' '}
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-amber-700 hover:text-amber-800 underline"
                  >
                    {s.title}
                  </a>
                  {s.provider ? <span className="text-gray-400"> ({s.provider})</span> : null}
                  {s.snippet ? <div className="text-gray-500 mt-1">{s.snippet}</div> : null}
                </li>
              ))}
            </ul>
          </div>
        )}
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
                  <code className="bg-gray-100 px-2 py-1 rounded">{filePath}</code>
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
          <div className="mt-10 border-t border-gray-200 pt-6">
            <h2 className="text-lg font-semibold text-gray-900">Sources</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {sources.map((s) => (
                <li key={s.id} className="text-gray-700">
                  <span className="font-medium">[{s.id}]</span>{' '}
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-amber-700 hover:text-amber-800 underline"
                  >
                    {s.title}
                  </a>
                  {s.provider ? <span className="text-gray-400"> ({s.provider})</span> : null}
                  {s.snippet ? <div className="text-gray-500 mt-1">{s.snippet}</div> : null}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return null;
}
