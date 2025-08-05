import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from 'react-query';
import { chatAPI } from '../services/api';
import { useConfig } from '../context/ConfigContext';
import toast from 'react-hot-toast';
import {
  PaperAirplaneIcon,
  UserIcon,
  ComputerDesktopIcon,
  PhoneIcon,
  EnvelopeIcon,
  GlobeAltIcon,
  MapPinIcon,
} from '@heroicons/react/24/outline';

// Component to format assistant messages with proper styling
function FormattedAssistantMessage({ content, isStreaming = false }) {
  const formatContent = (text) => {
    const lines = text.split('\n');
    const formatted = [];
    let currentSection = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (line.startsWith('**') && line.endsWith('**')) {
        // Header section
        const headerText = line.replace(/\*\*/g, '');
        currentSection = headerText.toLowerCase();
        formatted.push(
          <div key={i} className="font-semibold text-gray-900 mt-4 mb-2 first:mt-0">
            {headerText}
          </div>
        );
      } else if (line.startsWith('•')) {
        // Bullet point
        const bulletText = line.substring(1).trim();
        if (currentSection === 'contact information:') {
          formatted.push(
            <div key={i} className="flex items-center gap-2 py-1">
              {getContactIcon(bulletText)}
              <span className="text-gray-700">{formatContactInfo(bulletText)}</span>
            </div>
          );
        } else {
          formatted.push(
            <div key={i} className="flex items-start gap-2 py-1">
              <span className="text-indigo-500 font-bold">•</span>
              <span className="text-gray-700">{bulletText}</span>
            </div>
          );
        }
      } else if (line && !line.startsWith('**')) {
        // Regular content
        formatted.push(
          <div key={i} className="text-gray-700 leading-relaxed mb-2">
            {line}
          </div>
        );
      }
    }
    
    return formatted;
  };

  const getContactIcon = (text) => {
    if (text.toLowerCase().includes('phone:')) {
      return <PhoneIcon className="w-4 h-4 text-green-500" />;
    } else if (text.toLowerCase().includes('email:')) {
      return <EnvelopeIcon className="w-4 h-4 text-blue-500" />;
    } else if (text.toLowerCase().includes('website:')) {
      return <GlobeAltIcon className="w-4 h-4 text-purple-500" />;
    } else if (text.toLowerCase().includes('address:')) {
      return <MapPinIcon className="w-4 h-4 text-red-500" />;
    }
    return null;
  };

  const formatContactInfo = (text) => {
    // Make contact information clickable
    if (text.toLowerCase().includes('email:')) {
      const email = text.replace(/email:\s*/i, '');
      return (
        <span>
          Email: <a href={`mailto:${email}`} className="text-blue-600 hover:underline">{email}</a>
        </span>
      );
    } else if (text.toLowerCase().includes('phone:')) {
      const phone = text.replace(/phone:\s*/i, '');
      return (
        <span>
          Phone: <a href={`tel:${phone}`} className="text-green-600 hover:underline">{phone}</a>
        </span>
      );
    } else if (text.toLowerCase().includes('website:')) {
      const website = text.replace(/website:\s*/i, '');
      return (
        <span>
          Website: <a href={website} target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">{website}</a>
        </span>
      );
    }
    return text;
  };

  return (
    <div className="space-y-1">
      {formatContent(content)}
      {/* Streaming cursor */}
      {isStreaming && (
        <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></span>
      )}
    </div>
  );
}

export default function Chat() {
  const [message, setMessage] = useState('');
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const { config } = useConfig();

  const { data: sessions } = useQuery('chatSessions', chatAPI.getChatSessions);

  const sendMessageMutation = useMutation(
    ({ message, sessionId }) => chatAPI.sendMessage(message, sessionId),
    {
      onSuccess: (response) => {
        // Add user message and assistant response to current conversation
        setMessages(prev => [
          ...prev,
          {
            id: Date.now() + '-user',
            type: 'user',
            content: message,
            created_at: new Date().toISOString(),
          },
          {
            id: response.message_id,
            type: 'assistant',
            content: response.answer,
            created_at: new Date().toISOString(),
            metadata: {
              sources: response.sources,
              contact_info: response.contact_info,
              categories: response.categories,
              providers: response.providers,
            }
          }
        ]);
        
        // Update current session ID
        if (!currentSession) {
          setCurrentSession(response.session_id);
        }
        
        setMessage('');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to send message');
      },
    }
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isStreaming) return;

    const userMessage = {
      id: Date.now() + '-user',
      type: 'user',
      content: message.trim(),
      created_at: new Date().toISOString(),
    };

    const currentMessage = message.trim();
    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsStreaming(true);

    try {
      // Create streaming assistant message
      const assistantMessageId = Date.now() + '-assistant';
      const assistantMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: '',
        isStreaming: true,
        created_at: new Date().toISOString(),
        metadata: {
          sources: [],
          contact_info: {},
          categories: [],
          providers: []
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessageId(assistantMessageId);

      // Set up streaming
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const streamUrl = `${apiUrl}/api/v1/chat/stream`;
      
      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message: currentMessage,
          session_id: currentSession
        })
      });

      if (!response.ok) {
        throw new Error('Failed to start streaming');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              
              if (data.type === 'chunk') {
                // Update streaming message content
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: msg.content + data.content }
                    : msg
                ));
              } else if (data.type === 'complete') {
                // Update message with final metadata
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { 
                        ...msg, 
                        isStreaming: false,
                        metadata: {
                          sources: data.sources || [],
                          contact_info: data.contact_info || {},
                          categories: data.categories || [],
                          providers: data.providers || []
                        }
                      }
                    : msg
                ));
                
                // Set session ID for future messages
                if (data.session_id && !currentSession) {
                  setCurrentSession(data.session_id);
                }
              } else if (data.type === 'error') {
                throw new Error(data.message);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }

    } catch (error) {
      console.error('Streaming chat error:', error);
      
      // Remove the streaming message and add error message
      setMessages(prev => prev.filter(msg => msg.id !== streamingMessageId));
      
      const errorMessage = {
        id: Date.now() + '-error',
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsStreaming(false);
      setStreamingMessageId(null);
    }
  };

  const startNewSession = () => {
    setCurrentSession(null);
    setMessages([]);
  };

  const loadSession = async (sessionId) => {
    try {
      const session = await chatAPI.getChatSession(sessionId);
      setCurrentSession(sessionId);
      setMessages(session.messages);
    } catch (error) {
      toast.error('Failed to load session');
    }
  };

  return (
    <div className="h-screen flex">
      {/* Sidebar - Sessions */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={startNewSession}
            className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700"
          >
            New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Sessions</h3>
            <div className="space-y-2">
              {sessions?.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => loadSession(session.session_id)}
                  className={`w-full text-left p-3 rounded-md text-sm hover:bg-gray-50 ${
                    currentSession === session.session_id ? 'bg-indigo-50 border border-indigo-200' : ''
                  }`}
                >
                  <div className="font-medium text-gray-900 truncate">
                    Session {session.session_id.slice(0, 8)}...
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {session.messages.length} messages • {new Date(session.last_activity).toLocaleDateString()}
                  </div>
                </button>
              )) || (
                <p className="text-sm text-gray-500">No sessions yet</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-medium text-gray-900">
                Test Your {config.brand_name} Assistant
              </h1>
              <p className="text-sm text-gray-500">
                Try out your AI assistant before sharing with users
              </p>
            </div>
            {currentSession && (
              <div className="text-sm text-gray-500">
                Session: {currentSession.slice(0, 8)}...
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="bg-white rounded-lg p-8 shadow-sm">
                  <ComputerDesktopIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Welcome to {config.brand_name}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Start a conversation to test your AI assistant. Ask questions about your uploaded documents.
                  </p>
                  <div className="text-sm text-gray-500">
                    <p>Try asking:</p>
                    <ul className="mt-2 space-y-1">
                      <li>• "What services are available?"</li>
                      <li>• "How can I get help with housing?"</li>
                      <li>• "What medical resources do you have?"</li>
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex max-w-xs lg:max-w-2xl ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex-shrink-0 ${msg.type === 'user' ? 'ml-3' : 'mr-3'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        msg.type === 'user' ? 'bg-indigo-500' : 'bg-gray-400'
                      }`}>
                        {msg.type === 'user' ? (
                          <UserIcon className="w-5 h-5 text-white" />
                        ) : (
                          <span className="text-white text-sm">{config.brand_logo}</span>
                        )}
                      </div>
                    </div>
                    <div className={`rounded-lg px-4 py-2 ${
                      msg.type === 'user'
                        ? 'bg-indigo-500 text-white'
                        : 'bg-white border border-gray-200'
                    }`}>
                      <div className="text-sm">
                        {msg.type === 'assistant' ? (
                          <FormattedAssistantMessage content={msg.content} isStreaming={msg.isStreaming} />
                        ) : (
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        )}
                      </div>
                      
                      {/* Show metadata for assistant messages */}
                      {msg.type === 'assistant' && msg.metadata && (
                        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                          {msg.metadata.categories?.length > 0 && (
                            <div className="mb-2">
                              <strong>Categories:</strong> {msg.metadata.categories.join(', ')}
                            </div>
                          )}
                          {msg.metadata.providers?.length > 0 && (
                            <div className="mb-2">
                              <strong>Providers:</strong> {msg.metadata.providers.join(', ')}
                            </div>
                          )}
                          {msg.metadata.sources?.length > 0 && (
                            <div>
                              <strong>Sources:</strong> {msg.metadata.sources.length} document chunks
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="flex space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={isStreaming}
                />
              </div>
              <button
                type="submit"
                disabled={!message.trim() || isStreaming}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isStreaming ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <PaperAirplaneIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}