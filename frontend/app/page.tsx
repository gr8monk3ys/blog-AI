'use client';

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Tab } from '@headlessui/react';
import ContentGenerator from '../components/ContentGenerator';
import BookGenerator from '../components/BookGenerator';
import ConversationHistory from '../components/ConversationHistory';
import ContentViewer from '../components/ContentViewer';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function Home() {
  const [conversationId] = useState(uuidv4());
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <main className="flex min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Left sidebar - Conversation History */}
      <div className="w-1/4 bg-white border-r border-gray-200 shadow-sm p-6">
        <ConversationHistory conversationId={conversationId} />
      </div>

      {/* Main content area */}
      <div className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <Tab.Group>
              <Tab.List className="flex space-x-1 rounded-xl bg-indigo-50 p-1 mb-6">
                <Tab
                  className={({ selected }) =>
                    classNames(
                      'w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all',
                      'ring-white ring-opacity-60 ring-offset-2 ring-offset-indigo-400 focus:outline-none focus:ring-2',
                      selected
                        ? 'bg-white shadow-sm text-indigo-700'
                        : 'text-indigo-500 hover:bg-white/[0.12] hover:text-indigo-600'
                    )
                  }
                >
                  Blog Post
                </Tab>
                <Tab
                  className={({ selected }) =>
                    classNames(
                      'w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all',
                      'ring-white ring-opacity-60 ring-offset-2 ring-offset-indigo-400 focus:outline-none focus:ring-2',
                      selected
                        ? 'bg-white shadow-sm text-indigo-700'
                        : 'text-indigo-500 hover:bg-white/[0.12] hover:text-indigo-600'
                    )
                  }
                >
                  Book
                </Tab>
              </Tab.List>
              <Tab.Panels>
                <Tab.Panel>
                  <ContentGenerator
                    conversationId={conversationId}
                    setContent={setContent}
                    setLoading={setLoading}
                  />
                </Tab.Panel>
                <Tab.Panel>
                  <BookGenerator
                    conversationId={conversationId}
                    setContent={setContent}
                    setLoading={setLoading}
                  />
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          </div>
          
          {loading && (
            <div className="mt-8 text-center bg-white rounded-xl shadow-sm p-10">
              <div className="flex justify-center items-center space-x-2">
                <div className="h-3 w-3 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="h-3 w-3 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="h-3 w-3 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <p className="mt-6 text-gray-600 font-medium">Generating your content...</p>
              <p className="text-xs text-gray-500 mt-2">This may take a few moments</p>
            </div>
          )}

          {content && !loading && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <ContentViewer content={content} />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
