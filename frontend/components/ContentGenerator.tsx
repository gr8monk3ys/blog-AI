import { useState } from 'react';
import { Switch } from '@headlessui/react';

interface ContentGeneratorProps {
  conversationId: string;
  setContent: (content: any) => void;
  setLoading: (loading: boolean) => void;
}

export default function ContentGenerator({ conversationId, setContent, setLoading }: ContentGeneratorProps) {
  const [topic, setTopic] = useState('');
  const [isBook, setIsBook] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic,
          type: isBook ? 'book' : 'blog',
          conversation_id: conversationId,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setContent(data);
      } else {
        throw new Error(data.detail || 'Failed to generate content');
      }
    } catch (error) {
      console.error('Error generating content:', error);
      alert('Failed to generate content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="topic" className="block text-sm font-medium text-gray-700">
            What would you like to write about?
          </label>
          <input
            type="text"
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="Enter your topic..."
            required
          />
        </div>

        <div className="flex items-center space-x-3">
          <Switch
            checked={isBook}
            onChange={setIsBook}
            className={`${
              isBook ? 'bg-indigo-600' : 'bg-gray-200'
            } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
          >
            <span
              className={`${
                isBook ? 'translate-x-6' : 'translate-x-1'
              } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
            />
          </Switch>
          <span className="text-sm text-gray-700">Generate a {isBook ? 'book' : 'blog post'}</span>
        </div>

        <button
          type="submit"
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Generate Content
        </button>
      </form>
    </div>
  );
}
