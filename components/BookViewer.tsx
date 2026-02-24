import { useState } from 'react';
import { Disclosure } from '@headlessui/react';
import { ChevronUpIcon } from '@heroicons/react/24/outline';
import { Book } from '../types/book';
import { useToast } from '../hooks/useToast';
import { API_ENDPOINTS, getDefaultHeaders } from '../lib/api';

interface BookViewerProps {
  book: Book;
  filePath: string;
}

export default function BookViewer({ book, filePath }: BookViewerProps) {
  const { showToast, ToastComponent } = useToast();
  const [downloadFormat, setDownloadFormat] = useState<'markdown' | 'json'>('markdown');

  const handleDownload = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.downloadBook, {
        method: 'POST',
        headers: await getDefaultHeaders(),
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
      showToast({
        message: 'Failed to download book. Please try again.',
        variant: 'error',
      });
    }
  };

  return (
    <div className="mt-8">
      {/* Toast notifications */}
      <ToastComponent />

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{book.title}</h1>
        <div className="flex items-center space-x-2">
          <select
            value={downloadFormat}
            onChange={(e) => setDownloadFormat(e.target.value as 'markdown' | 'json')}
            className="rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 shadow-sm focus:border-amber-500 focus:ring-amber-500"
          >
            <option value="markdown">Markdown</option>
            <option value="json">JSON</option>
          </select>
          <button
            onClick={handleDownload}
            className="bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700"
          >
            Download
          </button>
        </div>
      </div>

      {book.tags && book.tags.length > 0 && (
        <div className="mb-4">
          <span className="text-sm text-gray-500 dark:text-gray-400">Tags: </span>
          {Array.from(new Set(book.tags)).map((tag) => (
            <span key={tag} className="inline-block bg-gray-200 dark:bg-gray-800 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 dark:text-gray-300 mr-2 mb-2">
              {tag}
            </span>
          ))}
        </div>
      )}

      {book.date && (
        <div className="mb-6 text-sm text-gray-500 dark:text-gray-400">
          Date: {book.date}
        </div>
      )}

      <div className="space-y-4">
        {book.chapters.map((chapter) => (
          <Disclosure key={chapter.number}>
            {({ open }) => (
              <>
                <Disclosure.Button className="flex justify-between w-full px-4 py-2 text-lg font-medium text-left text-amber-900 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded-lg hover:bg-amber-200 dark:hover:bg-amber-900/50 focus:outline-none focus-visible:ring focus-visible:ring-amber-500 focus-visible:ring-opacity-75">
                  <span>{chapter.title}</span>
                  <ChevronUpIcon
                    className={`${
                      open ? 'transform rotate-180' : ''
                    } w-5 h-5 text-amber-500`}
                  />
                </Disclosure.Button>
                <Disclosure.Panel className="px-4 pt-4 pb-2 text-gray-500 dark:text-gray-400">
                  {chapter.topics.map((topic, topicIndex) => (
                    <div key={topicIndex} className="mb-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">{topic.title}</h3>
                      <div className="prose prose-indigo dark:prose-invert">{topic.content}</div>
                    </div>
                  ))}
                </Disclosure.Panel>
              </>
            )}
          </Disclosure>
        ))}
      </div>

      <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-900 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Your book has been generated and saved to: <br />
          <code className="bg-gray-200 dark:bg-gray-800 dark:text-gray-300 px-2 py-1 rounded">{filePath}</code>
        </p>
      </div>
    </div>
  );
}
