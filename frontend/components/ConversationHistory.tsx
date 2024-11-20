import { useState, useEffect } from 'react';

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
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Load existing conversation
    fetch(`http://localhost:8000/conversations/${conversationId}`)
      .then(res => res.json())
      .then(data => setMessages(data.conversation || []));

    // Setup WebSocket connection
    const websocket = new WebSocket(`ws://localhost:8000/ws/conversation/${conversationId}`);
    setWs(websocket);

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'message') {
        setMessages(prev => [...prev, message]);
      }
    };

    return () => {
      websocket.close();
    };
  }, [conversationId]);

  return (
    <div className="h-full overflow-y-auto">
      <h2 className="text-lg font-semibold mb-4">Conversation History</h2>
      <div className="space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg ${
              message.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'
            }`}
          >
            <div className="text-sm font-medium text-gray-900">
              {message.role === 'user' ? 'You' : 'AI'}
            </div>
            <div className="mt-1 text-sm text-gray-700">{message.content}</div>
            <div className="mt-1 text-xs text-gray-500">{message.timestamp}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
