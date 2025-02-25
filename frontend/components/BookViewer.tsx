import { useState } from 'react';
import { Disclosure } from '@headlessui/react';
import { ChevronUpIcon } from '@heroicons/react/24/outline';
import { Book, BookDownloadOptions } from '../types/book';

interface BookViewerProps {
  book: Book;
  filePath: string;
}

export default function BookViewer({ book, filePath }: BookViewerProps) {
  const [downloadFormat, setDownloadFormat] = useState<'markdown' | 'json'>('markdown');

  const handleDownload = async () => {
    try {
      const response = await fetch(`http://localhost:8000/download-book`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: filePath,
          format: downloadFormat,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to download book');
      }

      // Create a download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${book.title}.${downloadFormat === 'markdown' ? 'md' : 'json'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading book:', error);
      alert('Failed to download book. Please try again.');
    }
  };

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">{book.title}</h1>
        <div className="flex items-center space-x-2">
          <select
            value={downloadFormat}
            onChange={(e) => setDownloadFormat(e.target.value as 'markdown' | 'json')}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="markdown">Markdown</option>
            <option value="json">JSON</option>
          </select>
          <button
            onClick={handleDownload}
            className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          >
            Download
          </button>
        </div>
      </div>

      {book.tags && book.tags.length > 0 && (
        <div className="mb-4">
          <span className="text-sm text-gray-500">Tags: </span>
          {book.tags.map((tag, index) => (
            <span key={index} className="inline-block bg-gray-200 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-2 mb-2">
              {tag}
            </span>
          ))}
        </div>
      )}

      {book.date && (
        <div className="mb-6 text-sm text-gray-500">
          Date: {book.date}
        </div>
      )}

      <div className="space-y-4">
        {book.chapters.map((chapter) => (
          <Disclosure key={chapter.number}>
            {({ open }) => (
              <>
                <Disclosure.Button className="flex justify-between w-full px-4 py-2 text-lg font-medium text-left text-indigo-900 bg-indigo-100 rounded-lg hover:bg-indigo-200 focus:outline-none focus-visible:ring focus-visible:ring-indigo-500 focus-visible:ring-opacity-75">
                  <span>{chapter.title}</span>
                  <ChevronUpIcon
                    className={`${
                      open ? 'transform rotate-180' : ''
                    } w-5 h-5 text-indigo-500`}
                  />
                </Disclosure.Button>
                <Disclosure.Panel className="px-4 pt-4 pb-2 text-gray-500">
                  {chapter.topics.map((topic, topicIndex) => (
                    <div key={topicIndex} className="mb-4">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">{topic.title}</h3>
                      <div className="prose prose-indigo">{topic.content}</div>
                    </div>
                  ))}
                </Disclosure.Panel>
              </>
            )}
          </Disclosure>
        ))}
      </div>

      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <p className="text-sm text-gray-600">
          Your book has been generated and saved to: <br />
          <code className="bg-gray-200 px-2 py-1 rounded">{filePath}</code>
        </p>
      </div>
    </div>
  );
}
