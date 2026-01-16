import { useState } from 'react';
import { Switch } from '@headlessui/react';
import { PencilIcon, LightBulbIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { BlogGenerationOptions } from '../types/blog';
import { BlogGenerationResponse, ContentGenerationResponse } from '../types/content';
import { API_ENDPOINTS, getDefaultHeaders, checkServerConnection } from '../lib/api';

interface ContentGeneratorProps {
  conversationId: string;
  setContent: (content: ContentGenerationResponse) => void;
  setLoading: (loading: boolean) => void;
}

export default function ContentGenerator({ conversationId, setContent, setLoading }: ContentGeneratorProps) {
  const [topic, setTopic] = useState('');
  const [keywords, setKeywords] = useState('');
  const [tone, setTone] = useState<BlogGenerationOptions['tone']>('informative');
  const [useResearch, setUseResearch] = useState(false);
  const [proofread, setProofread] = useState(true);
  const [humanize, setHumanize] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock blog post data for development or when server is not available
  const generateMockBlogPost = (): BlogGenerationResponse => {
    return {
      success: true,
      type: "blog",
      content: {
        title: topic || "How AI is Revolutionizing Content Creation",
        description: `A comprehensive look at how artificial intelligence is transforming the way we create and consume content in ${new Date().getFullYear()}.`,
        date: new Date().toISOString(),
        image: "https://example.com/ai-content-creation.jpg",
        tags: keywords.split(',').map(k => k.trim()).filter(k => k) || ["AI", "Content Creation", "Marketing"],
        sections: [
          {
            title: "Introduction",
            subtopics: [
              {
                title: "",
                content: "Artificial intelligence has rapidly evolved from a futuristic concept to a practical tool that's reshaping industries across the globe. In the realm of content creation and marketing, AI technologies are not just supplementing human efforts—they're revolutionizing the entire process from ideation to distribution. This transformation is enabling businesses and creators to produce more engaging, personalized, and effective content at unprecedented scale and speed."
              }
            ]
          },
          {
            title: "The Current State of AI in Content Creation",
            subtopics: [
              {
                title: "",
                content: "Today's AI tools can generate blog posts, social media updates, email newsletters, and even video scripts with minimal human input. Natural Language Processing (NLP) models like GPT-4 can produce human-like text that's increasingly difficult to distinguish from content written by people. These advancements have democratized content creation, allowing smaller businesses and individual creators to compete with larger organizations that have traditionally had more resources for content production."
              }
            ]
          },
          {
            title: "AI-Powered Content Personalization",
            subtopics: [
              {
                title: "",
                content: "One of the most significant impacts of AI on marketing is the ability to deliver highly personalized content at scale. Machine learning algorithms can analyze user behavior, preferences, and engagement patterns to tailor content for specific audience segments or even individual users. This level of personalization was previously impossible to achieve manually, but AI makes it not only possible but efficient and cost-effective."
              }
            ]
          },
          {
            title: "Challenges and Ethical Considerations",
            subtopics: [
              {
                title: "",
                content: "Despite its benefits, AI-generated content raises important questions about authenticity, creativity, and the role of human writers. There are concerns about potential biases in AI systems, copyright issues with AI-generated work, and the impact on employment in creative industries. Finding the right balance between automation and human creativity remains a challenge that content marketers must navigate carefully."
              }
            ]
          },
          {
            title: "Conclusion",
            subtopics: [
              {
                title: "",
                content: "AI is undeniably transforming content creation and marketing, offering unprecedented opportunities for efficiency, personalization, and scale. While it won't replace human creativity entirely, it's becoming an essential tool in the modern marketer's arsenal. Organizations that successfully integrate AI into their content strategies—while maintaining human oversight and creative direction—will be best positioned to thrive in this new era of content marketing."
              }
            ]
          },
          {
            title: "Frequently Asked Questions",
            subtopics: [
              {
                title: "Can AI completely replace human content creators?",
                content: "While AI can generate impressive content, it currently works best as a collaborative tool with human oversight. Human creativity, emotional intelligence, and cultural understanding remain difficult to replicate. The most effective approach is typically a hybrid model where AI handles routine content generation and humans provide strategic direction, editing, and creative input."
              },
              {
                title: "How can small businesses leverage AI for content marketing?",
                content: "Small businesses can use AI tools to scale their content production, analyze competitor content, generate ideas, and optimize existing content for SEO. Many affordable AI writing assistants, content generators, and analytics platforms are now available that don't require technical expertise to use."
              },
              {
                title: "What skills should content marketers develop in the age of AI?",
                content: "Content marketers should focus on developing skills that complement AI capabilities, such as strategic thinking, brand storytelling, emotional intelligence, ethical judgment, and the ability to effectively prompt and direct AI tools. Understanding how to review and edit AI-generated content is also becoming increasingly important."
              }
            ]
          }
        ]
      }
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Check if server is running
      const isServerConnected = await checkServerConnection();
      
      if (!isServerConnected) {
        // Use mock data if server is not running
        setTimeout(() => {
          setContent(generateMockBlogPost());
          setLoading(false);
        }, 3000); // Simulate generation delay
        return;
      }
      
      // Server is running, make the real request
      const response = await fetch(API_ENDPOINTS.generateBlog, {
        method: 'POST',
        headers: getDefaultHeaders(),
        body: JSON.stringify({
          topic,
          keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
          tone,
          research: useResearch,
          proofread,
          humanize,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.detail || 'Failed to generate content');
      }
      setContent(data);
    } catch (err) {
      console.error('Error generating content:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center mb-6">
        <DocumentTextIcon className="h-5 w-5 text-indigo-600 mr-2" />
        <h2 className="text-xl font-bold text-gray-800">Blog Post Generator</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
          <div className="flex items-center mb-2">
            <PencilIcon className="h-4 w-4 text-indigo-600 mr-2" />
            <label htmlFor="topic" className="block text-sm font-medium text-indigo-800">
              What would you like to write about?
            </label>
          </div>
          <input
            type="text"
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            placeholder="Enter your topic..."
            required
          />
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
              placeholder="SEO, marketing, content..."
            />
          </div>

          <div>
            <label htmlFor="tone" className="block text-sm font-medium text-gray-700">
              Tone
            </label>
            <select
              id="tone"
              value={tone}
              onChange={(e) => setTone(e.target.value as BlogGenerationOptions['tone'])}
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

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            <p className="font-medium">Error</p>
            <p>{error}</p>
            <button
              type="button"
              onClick={() => setError(null)}
              className="mt-2 text-xs bg-red-100 hover:bg-red-200 px-2 py-1 rounded transition-colors"
            >
              Dismiss
            </button>
          </div>
        )}

        <button
          type="submit"
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all"
        >
          Generate Blog Post
        </button>
      </form>
    </div>
  );
}
