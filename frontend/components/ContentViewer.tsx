import { useState } from 'react';
import { Popover } from '@headlessui/react';
import BookViewer from './BookViewer';
import BookEditor from './BookEditor';
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
      <div className="mt-8 prose prose-lg max-w-none">
        <h1>{content.content.title}</h1>
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
        <div className="flex justify-end mb-4">
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
