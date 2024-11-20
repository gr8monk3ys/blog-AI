'use client';

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ContentGenerator from '../components/ContentGenerator';
import ConversationHistory from '../components/ConversationHistory';
import ContentViewer from '../components/ContentViewer';

export default function Home() {
  const [conversationId] = useState(uuidv4());
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <main className="flex min-h-screen bg-gray-100">
      {/* Left sidebar - Conversation History */}
      <div className="w-1/4 bg-white border-r border-gray-200 p-4">
        <ConversationHistory conversationId={conversationId} />
      </div>

      {/* Main content area */}
      <div className="flex-1 p-4">
        <div className="max-w-4xl mx-auto">
          <ContentGenerator
            conversationId={conversationId}
            setContent={setContent}
            setLoading={setLoading}
          />
          
          {loading && (
            <div className="mt-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-4 text-gray-600">Generating your content...</p>
            </div>
          )}

          {content && !loading && (
            <ContentViewer content={content} />
          )}
        </div>
      </div>
    </main>
  );
}
