import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  role: string;
  content: string;
  timestamp: string;
}

interface ConversationHistoryProps {
  conversationId: string;
}

export default function ConversationHistory({ conversationId }: ConversationHistoryProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAiTyping, setIsAiTyping] = useState<boolean>(false);
  const [isServerConnected, setIsServerConnected] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Format timestamp to relative time (e.g., "2 minutes ago")
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  };

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Group messages by sender
  const groupedMessages = messages.reduce((groups, message, index) => {
    const prevMessage = messages[index - 1];
    const isSameSender = prevMessage && prevMessage.role === message.role;
    
    if (isSameSender) {
      const lastGroup = groups[groups.length - 1];
      lastGroup.messages.push(message);
      return groups;
    } else {
      return [...groups, { role: message.role, messages: [message] }];
    }
  }, [] as { role: string; messages: Message[] }[]);

  // Mock data for development or when server is not available
  const mockMessages: Message[] = [
    {
      role: 'user',
      content: 'Can you write a blog post about artificial intelligence?',
      timestamp: new Date(Date.now() - 3600000).toISOString()
    },
    {
      role: 'assistant',
      content: 'I\'ll create a comprehensive blog post about AI for you. What specific aspects would you like me to focus on?',
      timestamp: new Date(Date.now() - 3500000).toISOString()
    },
    {
      role: 'user',
      content: 'Focus on how AI is changing content creation and marketing.',
      timestamp: new Date(Date.now() - 3400000).toISOString()
    },
    {
      role: 'assistant',
      content: 'I\'ve generated a blog post titled "How AI is Revolutionizing Content Creation and Marketing" with 5 sections covering the latest trends and applications.',
      timestamp: new Date(Date.now() - 3300000).toISOString()
    }
  ];

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

  useEffect(() => {
    let isMounted = true;
    
    const initializeConversation = async () => {
      setIsLoading(true);
      
      // Check if server is running
      const isConnected = await checkServerConnection();
      if (isMounted) setIsServerConnected(isConnected);
      
      if (!isConnected) {
        // Use mock data if server is not running
        setTimeout(() => {
          if (isMounted) {
            setMessages(mockMessages);
            setIsLoading(false);
          }
        }, 1000); // Simulate loading delay
        return;
      }
      
      // Server is running, try to load conversation
      try {
        const response = await fetch(`http://localhost:8000/conversations/${conversationId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to load conversation: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (isMounted) {
          setMessages(data.conversation || []);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Error loading conversation:', err);
          setError('Failed to load conversation history. Please try again.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    const setupWebSocket = () => {
      // Only attempt to connect if server is running
      if (!isServerConnected) return null;
      
      try {
        const websocket = new WebSocket(`ws://localhost:8000/ws/conversation/${conversationId}`);
        
        websocket.onopen = () => {
          if (isMounted) {
            console.log('WebSocket connection established');
            setWs(websocket);
          }
        };
        
        websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'message') {
            if (isMounted) {
              setMessages(prev => [...prev, message]);
              setIsAiTyping(false);
            }
          } else if (message.type === 'typing') {
            if (isMounted) setIsAiTyping(true);
          }
        };
        
        websocket.onerror = (error) => {
          if (isMounted) {
            console.error('WebSocket error:', error);
            setError('Connection error. Messages may not update in real-time.');
          }
        };
        
        websocket.onclose = () => {
          if (isMounted) {
            console.log('WebSocket connection closed');
          }
        };
        
        return websocket;
      } catch (err) {
        console.error('Error setting up WebSocket:', err);
        if (isMounted) {
          setError('Failed to establish real-time connection.');
        }
        return null;
      }
    };

    initializeConversation();
    
    // Setup WebSocket after checking server connection
    let websocket: WebSocket | null = null;
    if (isServerConnected) {
      websocket = setupWebSocket();
    }
    
    return () => {
      isMounted = false;
      if (websocket) websocket.close();
    };
  }, [conversationId, isServerConnected]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 px-1">
        <h2 className="text-xl font-bold text-indigo-800">Conversation</h2>
        {messages.length > 0 && (
          <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full">
            {messages.length} messages
          </span>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 space-y-4 mb-2">
        {isLoading ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-pulse flex space-x-2">
              <div className="h-2 w-2 bg-indigo-400 rounded-full"></div>
              <div className="h-2 w-2 bg-indigo-500 rounded-full"></div>
              <div className="h-2 w-2 bg-indigo-600 rounded-full"></div>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
            <p className="font-medium">Error</p>
            <p>{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 text-xs bg-red-100 hover:bg-red-200 px-2 py-1 rounded transition-colors"
            >
              Retry
            </button>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-10 text-gray-500">
            <p className="text-sm">No messages yet</p>
            <p className="text-xs mt-1">Start a conversation by generating content</p>
          </div>
        ) : (
          <AnimatePresence>
            {groupedMessages.map((group, groupIndex) => (
              <motion.div
                key={groupIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${group.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-[85%] ${
                    group.role === 'user' 
                      ? 'bg-gradient-to-br from-indigo-500 to-indigo-600 text-white' 
                      : 'bg-white border border-gray-200 shadow-sm'
                  } rounded-2xl overflow-hidden`}
                >
                  <div className="px-4 py-2 text-xs font-medium border-b border-opacity-10 flex justify-between items-center">
                    <span className={group.role === 'user' ? 'text-indigo-100' : 'text-indigo-700'}>
                      {group.role === 'user' ? 'You' : 'AI Assistant'}
                    </span>
                  </div>
                  
                  <div className="space-y-2 p-3">
                    {group.messages.map((message, messageIndex) => (
                      <div key={messageIndex} className="space-y-2">
                        <div className={`text-sm ${group.role === 'user' ? 'text-white' : 'text-gray-800'}`}>
                          {message.content}
                        </div>
                        
                        {messageIndex === group.messages.length - 1 && (
                          <div className={`text-xs ${group.role === 'user' ? 'text-indigo-200' : 'text-gray-500'}`}>
                            {formatTimestamp(message.timestamp)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        
        {isAiTyping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
              <div className="flex space-x-2">
                <div className="h-2 w-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="h-2 w-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="h-2 w-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
