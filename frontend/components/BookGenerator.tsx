import { useState } from 'react';
import { Switch } from '@headlessui/react';
import { BookOpenIcon, LightBulbIcon, PencilIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';
import { BookGenerationOptions } from '../types/book';

interface BookGeneratorProps {
  conversationId: string;
  setContent: (content: any) => void;
  setLoading: (loading: boolean) => void;
}

export default function BookGenerator({ conversationId, setContent, setLoading }: BookGeneratorProps) {
  const [title, setTitle] = useState('');
  const [numChapters, setNumChapters] = useState(5);
  const [sectionsPerChapter, setSectionsPerChapter] = useState(3);
  const [keywords, setKeywords] = useState('');
  const [tone, setTone] = useState<BookGenerationOptions['tone']>('informative');
  const [useResearch, setUseResearch] = useState(false);
  const [proofread, setProofread] = useState(true);
  const [humanize, setHumanize] = useState(true);

  // Function to check if the server is running
  const checkServerConnection = async (): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout
      
      const response = await fetch('http://localhost:8000/', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (err) {
      console.log('Server connection check failed:', err);
      return false;
    }
  };

  // Mock book data for development or when server is not available
  const generateMockBook = () => {
    const bookTitle = title || "The Future of Artificial Intelligence";
    const chapters = [];
    
    // Generate mock chapters
    for (let i = 1; i <= numChapters; i++) {
      const topics = [];
      
      // Generate topics for each chapter
      for (let j = 1; j <= sectionsPerChapter; j++) {
        topics.push({
          title: `Topic ${j}`,
          content: `This is sample content for Topic ${j} in Chapter ${i}. In a real book, this would contain several paragraphs of informative text about this specific topic. The content would be well-researched, engaging, and tailored to the book's overall theme and tone.

This paragraph provides additional details and examples to illustrate the main points of this topic. It might include statistics, case studies, or anecdotes that help the reader understand the concepts being presented.

Finally, this paragraph would wrap up the topic and potentially transition to the next section, ensuring a smooth flow throughout the chapter. The writing style would match the selected tone and incorporate relevant keywords naturally.`
        });
      }
      
      chapters.push({
        number: i,
        title: `Chapter ${i}: ${["Introduction to", "Understanding", "Exploring", "Advanced Concepts in", "The Future of"][i % 5]} ${["Artificial Intelligence", "Machine Learning", "Neural Networks", "Deep Learning", "Natural Language Processing"][i % 5]}`,
        topics
      });
    }
    
    return {
      success: true,
      type: "book",
      content: {
        title: bookTitle,
        description: `A comprehensive exploration of artificial intelligence, its current applications, and future potential in ${new Date().getFullYear()}.`,
        date: new Date().toISOString(),
        image: "https://example.com/ai-book-cover.jpg",
        tags: keywords.split(',').map(k => k.trim()).filter(k => k) || ["AI", "Technology", "Future"],
        chapters
      }
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Check if server is running
      const isServerConnected = await checkServerConnection();
      
      if (!isServerConnected) {
        // Use mock data if server is not running
        setTimeout(() => {
          setContent(generateMockBook());
          setLoading(false);
        }, 5000); // Simulate longer generation delay for books
        return;
      }
      
      // Server is running, make the real request
      const response = await fetch('http://localhost:8000/generate-book', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          num_chapters: numChapters,
          sections_per_chapter: sectionsPerChapter,
          keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
          tone,
          research: useResearch,
          proofread,
          humanize,
          conversation_id: conversationId,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setContent(data);
      } else {
        throw new Error(data.detail || 'Failed to generate book');
      }
    } catch (error) {
      console.error('Error generating book:', error);
      alert('Failed to generate book. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center mb-6">
        <BookOpenIcon className="h-5 w-5 text-indigo-600 mr-2" />
        <h2 className="text-xl font-bold text-gray-800">Book Generator</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
          <div className="flex items-center mb-2">
            <PencilIcon className="h-4 w-4 text-indigo-600 mr-2" />
            <label htmlFor="title" className="block text-sm font-medium text-indigo-800">
              Book Title
            </label>
          </div>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            placeholder="Enter book title..."
            required
          />
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center mb-3">
            <AdjustmentsHorizontalIcon className="h-4 w-4 text-indigo-600 mr-2" />
            <h3 className="text-sm font-medium text-gray-700">Book Structure</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="numChapters" className="block text-sm font-medium text-gray-700">
                Number of Chapters
              </label>
              <input
                type="number"
                id="numChapters"
                value={numChapters}
                onChange={(e) => setNumChapters(parseInt(e.target.value))}
                min={1}
                max={20}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="sectionsPerChapter" className="block text-sm font-medium text-gray-700">
                Topics per Chapter
              </label>
              <input
                type="number"
                id="sectionsPerChapter"
                value={sectionsPerChapter}
                onChange={(e) => setSectionsPerChapter(parseInt(e.target.value))}
                min={1}
                max={10}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="keywords" className="block text-sm font-medium text-gray-700">
              Keywords (comma separated)
            </label>
            <input
              type="text"
              id="keywords"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              placeholder="AI, technology, future..."
            />
          </div>

          <div>
            <label htmlFor="tone" className="block text-sm font-medium text-gray-700">
              Tone
            </label>
            <select
              id="tone"
              value={tone}
              onChange={(e) => setTone(e.target.value as BookGenerationOptions['tone'])}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="informative">Informative</option>
              <option value="conversational">Conversational</option>
              <option value="professional">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="authoritative">Authoritative</option>
              <option value="technical">Technical</option>
            </select>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center mb-3">
            <LightBulbIcon className="h-4 w-4 text-indigo-600 mr-2" />
            <h3 className="text-sm font-medium text-gray-700">Advanced Options</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <Switch
                checked={useResearch}
                onChange={setUseResearch}
                className={`${
                  useResearch ? 'bg-indigo-600' : 'bg-gray-200'
                } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
              >
                <span
                  className={`${
                    useResearch ? 'translate-x-6' : 'translate-x-1'
                  } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                />
              </Switch>
              <span className="text-sm text-gray-700">Use web research</span>
            </div>

            <div className="flex items-center space-x-3">
              <Switch
                checked={proofread}
                onChange={setProofread}
                className={`${
                  proofread ? 'bg-indigo-600' : 'bg-gray-200'
                } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
              >
                <span
                  className={`${
                    proofread ? 'translate-x-6' : 'translate-x-1'
                  } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                />
              </Switch>
              <span className="text-sm text-gray-700">Proofread content</span>
            </div>

            <div className="flex items-center space-x-3">
              <Switch
                checked={humanize}
                onChange={setHumanize}
                className={`${
                  humanize ? 'bg-indigo-600' : 'bg-gray-200'
                } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
              >
                <span
                  className={`${
                    humanize ? 'translate-x-6' : 'translate-x-1'
                  } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                />
              </Switch>
              <span className="text-sm text-gray-700">Humanize content</span>
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all"
        >
          Generate Book
        </button>
      </form>
    </div>
  );
}
