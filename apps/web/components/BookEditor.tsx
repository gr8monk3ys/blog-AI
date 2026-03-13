import { useState } from 'react';
import { Disclosure, Dialog, Transition } from '@headlessui/react';
import { ChevronUpIcon, PencilIcon } from '@heroicons/react/24/outline';
import { Fragment } from 'react';
import { Book } from '../types/book';
import { useToast } from '../hooks/useToast';
import { API_ENDPOINTS, getDefaultHeaders } from '../lib/api';

interface BookEditorProps {
  book: Book;
  filePath: string;
  onSave: (updatedBook: Book) => void;
}

function useBookEditorView({ book, filePath, onSave }: BookEditorProps) {
  const { showToast, ToastComponent } = useToast();
  const [editingBook, setEditingBook] = useState<Book>({ ...book });
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [isEditingChapter, setIsEditingChapter] = useState<number | null>(null);
  const [isEditingTopic, setIsEditingTopic] = useState<{ chapterIndex: number; topicIndex: number } | null>(null);
  const [newTag, setNewTag] = useState('');

  const handleSaveBook = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.saveBook, {
        method: 'POST',
        headers: await getDefaultHeaders(),
        body: JSON.stringify({
          file_path: filePath,
          book: editingBook,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save book');
      }

      onSave(editingBook);
      showToast({
        message: 'Book saved successfully!',
        variant: 'success',
      });
    } catch (error) {
      console.error('Error saving book:', error);
      showToast({
        message: 'Failed to save book. Please try again.',
        variant: 'error',
      });
    }
  };

  const handleAddTag = () => {
    const trimmedTag = newTag.trim();
    if (trimmedTag === '') return;
    
    const updatedBook = { ...editingBook };
    const existingTags = new Set(updatedBook.tags || []);
    if (existingTags.has(trimmedTag)) return;
    updatedBook.tags = [...existingTags, trimmedTag];
    setEditingBook(updatedBook);
    setNewTag('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const updatedBook = { ...editingBook };
    updatedBook.tags = (updatedBook.tags || []).filter((tag) => tag !== tagToRemove);
    setEditingBook(updatedBook);
  };

  const handleUpdateChapterTitle = (chapterIndex: number, newTitle: string) => {
    const updatedBook = { ...editingBook };
    if (updatedBook.chapters[chapterIndex]) {
      updatedBook.chapters[chapterIndex].title = newTitle;
      setEditingBook(updatedBook);
    }
    setIsEditingChapter(null);
  };

  const handleUpdateTopicContent = (chapterIndex: number, topicIndex: number, newContent: string) => {
    const updatedBook = { ...editingBook };
    if (updatedBook.chapters[chapterIndex]?.topics[topicIndex]) {
      updatedBook.chapters[chapterIndex].topics[topicIndex].content = newContent;
      setEditingBook(updatedBook);
    }
    setIsEditingTopic(null);
  };

  return (
    <div className="mt-8">
      {/* Toast notifications */}
      <ToastComponent />

      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          {isEditingTitle ? (
            <div className="flex items-center">
              <input
                type="text"
                value={editingBook.title}
                onChange={(e) => setEditingBook({ ...editingBook, title: e.target.value })}
                className="text-3xl font-bold border-b border-amber-500 focus:outline-none dark:bg-transparent dark:text-gray-100"
              />
              <button
                onClick={() => setIsEditingTitle(false)}
                className="ml-2 text-amber-600 hover:text-amber-800"
              >
                Save
              </button>
            </div>
          ) : (
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
              {editingBook.title}
              <button
                onClick={() => setIsEditingTitle(true)}
                className="ml-2 text-gray-400 hover:text-amber-600"
              >
                <PencilIcon className="h-5 w-5" />
              </button>
            </h1>
          )}
        </div>
        <button
          onClick={handleSaveBook}
          className="bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700"
        >
          Save Book
        </button>
      </div>

      <div className="mb-4">
        <div className="flex items-center mb-2">
          <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">Tags:</span>
          <button
            onClick={() => setIsEditingTags(!isEditingTags)}
            className="text-gray-400 hover:text-amber-600"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
        </div>
        
        <div className="flex flex-wrap">
          {Array.from(new Set(editingBook.tags || [])).map((tag) => (
            <span key={tag} className="inline-flex items-center bg-gray-200 dark:bg-gray-800 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 dark:text-gray-300 mr-2 mb-2">
              {tag}
              {isEditingTags && (
                <button
                  onClick={() => handleRemoveTag(tag)}
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
                className="border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 rounded-l px-2 py-1 text-sm"
                placeholder="Add tag..."
              />
              <button
                onClick={handleAddTag}
                className="bg-amber-600 text-white rounded-r px-2 py-1 text-sm"
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
                <Disclosure.Button className="flex justify-between w-full px-4 py-2 text-lg font-medium text-left text-amber-900 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded-lg hover:bg-amber-200 dark:hover:bg-amber-900/50 focus:outline-none focus-visible:ring focus-visible:ring-amber-500 focus-visible:ring-opacity-75">
                  <div className="flex items-center">
                    <span>{chapter.title}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsEditingChapter(chapterIndex);
                      }}
                      className="ml-2 text-gray-400 hover:text-amber-600"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                  </div>
                  <ChevronUpIcon
                    className={`${
                      open ? 'transform rotate-180' : ''
                    } w-5 h-5 text-amber-500`}
                  />
                </Disclosure.Button>
                <Disclosure.Panel className="px-4 pt-4 pb-2 text-gray-500 dark:text-gray-400">
                  {chapter.topics.map((topic, topicIndex) => (
                    <div key={topicIndex} className="mb-6">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">{topic.title}</h3>
                        <button
                          onClick={() => setIsEditingTopic({ chapterIndex, topicIndex })}
                          className="ml-2 text-gray-400 hover:text-amber-600"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="prose prose-indigo dark:prose-invert">{topic.content}</div>
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
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-900 p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900 dark:text-gray-100"
                  >
                    Edit Chapter Title
                  </Dialog.Title>
                  <div className="mt-2">
                    <input
                      type="text"
                      value={isEditingChapter !== null ? editingBook.chapters[isEditingChapter]?.title ?? '' : ''}
                      onChange={(e) => {
                        if (isEditingChapter !== null) {
                          const chapter = editingBook.chapters[isEditingChapter];
                          if (chapter) {
                            const updatedBook = { ...editingBook };
                            updatedBook.chapters[isEditingChapter] = { ...chapter, title: e.target.value };
                            setEditingBook(updatedBook);
                          }
                        }
                      }}
                      className="w-full p-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 rounded"
                    />
                  </div>

                  <div className="mt-4 flex justify-end space-x-2">
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-gray-200 dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-700 focus:outline-none"
                      onClick={() => setIsEditingChapter(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 focus:outline-none"
                      onClick={() => {
                        if (isEditingChapter !== null && editingBook.chapters[isEditingChapter]) {
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
                <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-900 p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900 dark:text-gray-100"
                  >
                    Edit Content
                  </Dialog.Title>
                  <div className="mt-2">
                    {isEditingTopic && (() => {
                      const chapter = editingBook.chapters[isEditingTopic.chapterIndex];
                      const topic = chapter?.topics[isEditingTopic.topicIndex];
                      if (!topic) return null;
                      return (
                        <>
                          <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-2">
                            {topic.title}
                          </h4>
                          <textarea
                            value={topic.content}
                            onChange={(e) => {
                              const updatedBook = { ...editingBook };
                              const chapterToUpdate = updatedBook.chapters[isEditingTopic.chapterIndex];
                              const topicToUpdate = chapterToUpdate?.topics[isEditingTopic.topicIndex];
                              if (topicToUpdate) {
                                topicToUpdate.content = e.target.value;
                                setEditingBook(updatedBook);
                              }
                            }}
                            className="w-full p-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 rounded"
                            rows={10}
                          />
                        </>
                      );
                    })()}
                  </div>

                  <div className="mt-4 flex justify-end space-x-2">
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-gray-200 dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-700 focus:outline-none"
                      onClick={() => setIsEditingTopic(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 focus:outline-none"
                      onClick={() => {
                        if (isEditingTopic) {
                          const chapter = editingBook.chapters[isEditingTopic.chapterIndex];
                          const topic = chapter?.topics[isEditingTopic.topicIndex];
                          if (topic) {
                            handleUpdateTopicContent(
                              isEditingTopic.chapterIndex,
                              isEditingTopic.topicIndex,
                              topic.content
                            );
                          }
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

      <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-900 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Your book is being edited from: <br />
          <code className="bg-gray-200 dark:bg-gray-800 dark:text-gray-300 px-2 py-1 rounded">{filePath}</code>
        </p>
      </div>
    </div>
  );
}

export default function BookEditor(props: BookEditorProps) {
  return useBookEditorView(props)
}
