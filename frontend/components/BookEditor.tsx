import { useState } from 'react';
import { Disclosure, Dialog, Transition } from '@headlessui/react';
import { ChevronUpIcon, PencilIcon } from '@heroicons/react/24/outline';
import { Fragment } from 'react';
import { Book, BookEditResponse } from '../types/book';

interface BookEditorProps {
  book: Book;
  filePath: string;
  onSave: (updatedBook: Book) => void;
}

export default function BookEditor({ book, filePath, onSave }: BookEditorProps) {
  const [editingBook, setEditingBook] = useState<Book>({ ...book });
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [isEditingChapter, setIsEditingChapter] = useState<number | null>(null);
  const [isEditingTopic, setIsEditingTopic] = useState<{ chapterIndex: number; topicIndex: number } | null>(null);
  const [newTag, setNewTag] = useState('');

  const handleSaveBook = async () => {
    try {
      const response = await fetch(`http://localhost:8000/save-book`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: filePath,
          book: editingBook,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save book');
      }

      onSave(editingBook);
      alert('Book saved successfully!');
    } catch (error) {
      console.error('Error saving book:', error);
      alert('Failed to save book. Please try again.');
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() === '') return;
    
    const updatedBook = { ...editingBook };
    updatedBook.tags = [...(updatedBook.tags || []), newTag.trim()];
    setEditingBook(updatedBook);
    setNewTag('');
  };

  const handleRemoveTag = (index: number) => {
    const updatedBook = { ...editingBook };
    updatedBook.tags = (updatedBook.tags || []).filter((_, i) => i !== index);
    setEditingBook(updatedBook);
  };

  const handleUpdateChapterTitle = (chapterIndex: number, newTitle: string) => {
    const updatedBook = { ...editingBook };
    updatedBook.chapters[chapterIndex].title = newTitle;
    setEditingBook(updatedBook);
    setIsEditingChapter(null);
  };

  const handleUpdateTopicContent = (chapterIndex: number, topicIndex: number, newContent: string) => {
    const updatedBook = { ...editingBook };
    updatedBook.chapters[chapterIndex].topics[topicIndex].content = newContent;
    setEditingBook(updatedBook);
    setIsEditingTopic(null);
  };

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          {isEditingTitle ? (
            <div className="flex items-center">
              <input
                type="text"
                value={editingBook.title}
                onChange={(e) => setEditingBook({ ...editingBook, title: e.target.value })}
                className="text-3xl font-bold border-b border-indigo-500 focus:outline-none"
                autoFocus
              />
              <button
                onClick={() => setIsEditingTitle(false)}
                className="ml-2 text-indigo-600 hover:text-indigo-800"
              >
                Save
              </button>
            </div>
          ) : (
            <h1 className="text-3xl font-bold flex items-center">
              {editingBook.title}
              <button
                onClick={() => setIsEditingTitle(true)}
                className="ml-2 text-gray-400 hover:text-indigo-600"
              >
                <PencilIcon className="h-5 w-5" />
              </button>
            </h1>
          )}
        </div>
        <button
          onClick={handleSaveBook}
          className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          Save Book
        </button>
      </div>

      <div className="mb-4">
        <div className="flex items-center mb-2">
          <span className="text-sm text-gray-500 mr-2">Tags:</span>
          <button
            onClick={() => setIsEditingTags(!isEditingTags)}
            className="text-gray-400 hover:text-indigo-600"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
        </div>
        
        <div className="flex flex-wrap">
          {(editingBook.tags || []).map((tag, index) => (
            <span key={index} className="inline-flex items-center bg-gray-200 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-2 mb-2">
              {tag}
              {isEditingTags && (
                <button
                  onClick={() => handleRemoveTag(index)}
                  className="ml-1 text-gray-500 hover:text-red-500"
                >
                  &times;
                </button>
              )}
            </span>
          ))}
          
          {isEditingTags && (
            <div className="flex items-center">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                className="border border-gray-300 rounded-l px-2 py-1 text-sm"
                placeholder="Add tag..."
              />
              <button
                onClick={handleAddTag}
                className="bg-indigo-600 text-white rounded-r px-2 py-1 text-sm"
              >
                Add
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {editingBook.chapters.map((chapter, chapterIndex) => (
          <Disclosure key={chapter.number} defaultOpen={chapterIndex === 0}>
            {({ open }) => (
              <>
                <Disclosure.Button className="flex justify-between w-full px-4 py-2 text-lg font-medium text-left text-indigo-900 bg-indigo-100 rounded-lg hover:bg-indigo-200 focus:outline-none focus-visible:ring focus-visible:ring-indigo-500 focus-visible:ring-opacity-75">
                  <div className="flex items-center">
                    <span>{chapter.title}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsEditingChapter(chapterIndex);
                      }}
                      className="ml-2 text-gray-400 hover:text-indigo-600"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                  </div>
                  <ChevronUpIcon
                    className={`${
                      open ? 'transform rotate-180' : ''
                    } w-5 h-5 text-indigo-500`}
                  />
                </Disclosure.Button>
                <Disclosure.Panel className="px-4 pt-4 pb-2 text-gray-500">
                  {chapter.topics.map((topic, topicIndex) => (
                    <div key={topicIndex} className="mb-6">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{topic.title}</h3>
                        <button
                          onClick={() => setIsEditingTopic({ chapterIndex, topicIndex })}
                          className="ml-2 text-gray-400 hover:text-indigo-600"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="prose prose-indigo">{topic.content}</div>
                    </div>
                  ))}
                </Disclosure.Panel>
              </>
            )}
          </Disclosure>
        ))}
      </div>

      {/* Chapter Title Edit Modal */}
      <Transition appear show={isEditingChapter !== null} as={Fragment}>
        <Dialog as="div" className="relative z-10" onClose={() => setIsEditingChapter(null)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Edit Chapter Title
                  </Dialog.Title>
                  <div className="mt-2">
                    <input
                      type="text"
                      value={isEditingChapter !== null ? editingBook.chapters[isEditingChapter].title : ''}
                      onChange={(e) => {
                        if (isEditingChapter !== null) {
                          const updatedBook = { ...editingBook };
                          updatedBook.chapters[isEditingChapter].title = e.target.value;
                          setEditingBook(updatedBook);
                        }
                      }}
                      className="w-full p-2 border border-gray-300 rounded"
                      autoFocus
                    />
                  </div>

                  <div className="mt-4 flex justify-end space-x-2">
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-gray-200 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-300 focus:outline-none"
                      onClick={() => setIsEditingChapter(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none"
                      onClick={() => {
                        if (isEditingChapter !== null) {
                          handleUpdateChapterTitle(
                            isEditingChapter,
                            editingBook.chapters[isEditingChapter].title
                          );
                        }
                      }}
                    >
                      Save
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>

      {/* Topic Content Edit Modal */}
      <Transition appear show={isEditingTopic !== null} as={Fragment}>
        <Dialog as="div" className="relative z-10" onClose={() => setIsEditingTopic(null)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Edit Content
                  </Dialog.Title>
                  <div className="mt-2">
                    {isEditingTopic && (
                      <>
                        <h4 className="text-md font-medium text-gray-700 mb-2">
                          {editingBook.chapters[isEditingTopic.chapterIndex].topics[isEditingTopic.topicIndex].title}
                        </h4>
                        <textarea
                          value={editingBook.chapters[isEditingTopic.chapterIndex].topics[isEditingTopic.topicIndex].content}
                          onChange={(e) => {
                            const updatedBook = { ...editingBook };
                            updatedBook.chapters[isEditingTopic.chapterIndex].topics[isEditingTopic.topicIndex].content = e.target.value;
                            setEditingBook(updatedBook);
                          }}
                          className="w-full p-2 border border-gray-300 rounded"
                          rows={10}
                          autoFocus
                        />
                      </>
                    )}
                  </div>

                  <div className="mt-4 flex justify-end space-x-2">
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-gray-200 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-300 focus:outline-none"
                      onClick={() => setIsEditingTopic(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none"
                      onClick={() => {
                        if (isEditingTopic) {
                          handleUpdateTopicContent(
                            isEditingTopic.chapterIndex,
                            isEditingTopic.topicIndex,
                            editingBook.chapters[isEditingTopic.chapterIndex].topics[isEditingTopic.topicIndex].content
                          );
                        }
                      }}
                    >
                      Save
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>

      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <p className="text-sm text-gray-600">
          Your book is being edited from: <br />
          <code className="bg-gray-200 px-2 py-1 rounded">{filePath}</code>
        </p>
      </div>
    </div>
  );
}
