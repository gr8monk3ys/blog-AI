import { useState } from 'react';
import { Popover } from '@headlessui/react';
import BookViewer from './BookViewer';
import BookEditor from './BookEditor';
import ExportMenu, { ExportContent, ExportFormat } from './ExportMenu';
import { Book, Chapter } from '../types/book';
import { ContentGenerationResponse, BlogSection, BookContent } from '../types/content';

interface ContentViewerProps {
  content: ContentGenerationResponse;
}

export default function ContentViewer({ content }: ContentViewerProps) {
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null);
  const [editInstructions, setEditInstructions] = useState('');
  const [isEditingBook, setIsEditingBook] = useState(false);

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

  // Convert blog content to markdown for export
  const convertBlogToMarkdown = (): string => {
    if (content.type !== 'blog') return '';
    const blog = content.content;
    let markdown = `# ${blog.title}\n\n`;
    if (blog.description) {
      markdown += `> ${blog.description}\n\n`;
    }
    for (const section of blog.sections) {
      markdown += `## ${section.title}\n\n`;
      for (const subtopic of section.subtopics) {
        markdown += `### ${subtopic.title}\n\n`;
        markdown += `${subtopic.content}\n\n`;
      }
    }
    return markdown;
  };

  // Convert book content to markdown for export
  const convertBookToMarkdown = (): string => {
    if (content.type !== 'book') return '';
    const book = content.content as BookContent;
    let markdown = `# ${book.title}\n\n`;
    if (book.description) {
      markdown += `> ${book.description}\n\n`;
    }
    for (const chapter of book.chapters) {
      markdown += `## Chapter ${chapter.number}: ${chapter.title}\n\n`;
      for (const topic of chapter.topics) {
        markdown += `### ${topic.title}\n\n`;
        markdown += `${topic.content}\n\n`;
      }
    }
    return markdown;
  };

  // Get export content based on content type
  const getExportContent = (): ExportContent => {
    if (content.type === 'blog') {
      return {
        title: content.content.title,
        content: convertBlogToMarkdown(),
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
        content: convertBookToMarkdown(),
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
      const response = await fetch('http://localhost:8000/edit-section', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
      alert('Failed to update section. Please try again.');
    }
  };

  const handleBookSave = (updatedBook: Book): void => {
    setBookData(updatedBook);
    setIsEditingBook(false);
  };

  if (content.type === 'blog') {
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
                        className="mt-2 w-full bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
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
      </div>
    );
  }

  if (content.type === 'book') {
    const filePath = content.file_path || '';

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
            className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          >
            Edit Book
          </button>
        </div>

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
                  className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
                >
                  Download Book
                </button>
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  return null;
}
