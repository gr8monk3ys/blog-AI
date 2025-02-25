import { useState } from 'react';
import { Popover } from '@headlessui/react';
import BookViewer from './BookViewer';
import BookEditor from './BookEditor';
import { Book } from '../types/book';
import { Section, BlogPost, SectionEditOptions } from '../types/blog';

interface ContentViewerProps {
  content: {
    type: 'blog' | 'book';
    content?: BlogPost | any;
    title?: string;
    file_path: string;
  };
}

export default function ContentViewer({ content }: ContentViewerProps) {
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null);
  const [editInstructions, setEditInstructions] = useState('');
  const [isEditingBook, setIsEditingBook] = useState(false);
  const [bookData, setBookData] = useState<Book | null>(content.content?.book || null);

  const handleSectionEdit = async (sectionId: string) => {
    try {
      const response = await fetch('http://localhost:8000/edit-section', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: content.file_path,
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
        {content.content.sections.map((section: Section) => (
          <Popover key={section.id} className="relative">
            <div
              className="hover:bg-gray-50 p-2 rounded transition-colors cursor-pointer group"
              onMouseEnter={() => setEditingSectionId(section.id)}
              onMouseLeave={() => setEditingSectionId(null)}
            >
              <div className="prose">{section.content}</div>
              
              {editingSectionId === section.id && (
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
                        onClick={() => handleSectionEdit(section.id)}
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
    if (isEditingBook) {
      return (
        <BookEditor 
          book={bookData} 
          filePath={content.file_path} 
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
          <BookViewer book={bookData} filePath={content.file_path} />
        ) : (
          <div>
            <h1 className="text-3xl font-bold">{content.title}</h1>
            <p className="mt-4">
              Your book has been generated and saved to: <br />
              <code className="bg-gray-100 px-2 py-1 rounded">{content.file_path}</code>
            </p>
            <button
              onClick={() => window.open(`/api/download?path=${encodeURIComponent(content.file_path)}`)}
              className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
            >
              Download Book
            </button>
          </div>
        )}
      </div>
    );
  }

  return null;
}
