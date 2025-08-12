import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useConfig } from '../context/ConfigContext';
import { chatAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  UserIcon,
  SparklesIcon,
  DocumentTextIcon,
  PhoneIcon,
  EnvelopeIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';

const Chat = () => {
  const { user, isAuthenticated } = useAuth();
  const { config } = useConfig();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Cleanup EventSource on component unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;
    
    if (!user?.tenant_id) {
      toast.error('No tenant ID found. Please log in again.');
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    const currentMessage = inputMessage;
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Close any existing EventSource
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      // Create streaming assistant message
      const assistantMessageId = Date.now() + 1;
      const assistantMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: '',
        isStreaming: true,
        sources: [],
        contact_info: {},
        categories: [],
        providers: [],
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessageId(assistantMessageId);

      // Set up streaming
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const streamUrl = `${apiUrl}/api/v1/chat/${user.tenant_id}/stream`;
      
      // Use fetch with streaming instead of EventSource for better error handling
      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(user.access_token && { 'Authorization': `Bearer ${user.access_token}` })
        },
        body: JSON.stringify({
          message: currentMessage,
          session_id: sessionId
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
                        sources: data.sources || [],
                        contact_info: data.contact_info || {},
                        categories: data.categories || [],
                        providers: data.providers || []
                      }
                    : msg
                ));
                
                // Set session ID for future messages
                if (data.session_id && !sessionId) {
                  setSessionId(data.session_id);
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
        id: Date.now() + 2,
        type: 'error',
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  const formatContactInfo = (contactInfo) => {
    const items = [];
    
    if (contactInfo.phones && contactInfo.phones.length > 0) {
      items.push(...contactInfo.phones.map(phone => ({
        type: 'phone',
        value: phone,
        icon: PhoneIcon,
      })));
    }
    
    if (contactInfo.emails && contactInfo.emails.length > 0) {
      items.push(...contactInfo.emails.map(email => ({
        type: 'email',
        value: email,
        icon: EnvelopeIcon,
      })));
    }
    
    if (contactInfo.websites && contactInfo.websites.length > 0) {
      items.push(...contactInfo.websites.map(website => ({
        type: 'website',
        value: website,
        icon: GlobeAltIcon,
      })));
    }
    
    return items;
  };

  const formatMessageContent = (content) => {
    // Function to parse markdown-style bold text
    const parseTextWithBold = (text) => {
      // Replace **text** with bold spans
      const parts = text.split(/\*\*([^*]+)\*\*/g);
      return parts.map((part, index) => {
        // Odd indices are the bold text (captured groups)
        if (index % 2 === 1) {
          return <strong key={index}>{part}</strong>;
        }
        return part;
      });
    };
    
    // Split content into paragraphs by double newlines
    const paragraphs = content.split('\n\n');
    
    return paragraphs.map((paragraph, pIndex) => {
      // Check if this is a header (ends with colon)
      const lines = paragraph.split('\n');
      
      return (
        <div key={pIndex} className={pIndex > 0 ? 'mt-3' : ''}>
          {lines.map((line, lIndex) => {
            const trimmedLine = line.trim();
            
            // Empty line
            if (!trimmedLine) return null;
            
            // Header line (ends with colon or has markdown bold)
            if ((trimmedLine.endsWith(':') && !trimmedLine.startsWith('•')) || 
                (trimmedLine.includes('**') && trimmedLine.endsWith(':'))) {
              // Remove markdown formatting and make it a header
              const headerText = trimmedLine.replace(/\*\*/g, '');
              return (
                <div key={lIndex} className="font-semibold mb-1">
                  {headerText}
                </div>
              );
            }
            
            // Bullet point
            if (trimmedLine.startsWith('•')) {
              return (
                <div key={lIndex} className="flex ml-2 mb-1">
                  <span className="mr-2">•</span>
                  <span className="flex-1">{parseTextWithBold(trimmedLine.substring(1).trim())}</span>
                </div>
              );
            }
            
            // Regular text
            return (
              <div key={lIndex} className={lIndex > 0 ? 'mt-1' : ''}>
                {parseTextWithBold(trimmedLine)}
              </div>
            );
          })}
        </div>
      );
    });
  };

  const MessageBubble = ({ message }) => {
    const isUser = message.type === 'user';
    const isError = message.type === 'error';
    
    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`flex max-w-xs lg:max-w-md ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 ${isUser ? 'ml-2' : 'mr-2'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              isUser ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-600'
            }`}>
              {isUser ? (
                <UserIcon className="h-5 w-5" />
              ) : (
                <span className="text-lg">{config.brand_logo}</span>
              )}
            </div>
          </div>
          
          {/* Message Content */}
          <div className={`px-4 py-2 rounded-lg ${
            isUser 
              ? 'bg-primary-500 text-white' 
              : isError 
                ? 'bg-red-100 text-red-800 border border-red-200'
                : 'bg-white text-gray-800 border border-gray-200'
          }`}>
            {/* Message text */}
            <div className="chat-message">
              {isUser || isError ? (
                // For user and error messages, keep simple text rendering
                <div className="whitespace-pre-wrap">
                  {message.content}
                </div>
              ) : (
                // For assistant messages, use formatted rendering
                <>
                  {formatMessageContent(message.content)}
                  {/* Streaming cursor */}
                  {message.isStreaming && (
                    <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></span>
                  )}
                </>
              )}
            </div>
            
            {/* Additional info for assistant messages */}
            {!isUser && !isError && (
              <div className="mt-3 space-y-2">
                {/* Categories */}
                {message.categories && message.categories.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {message.categories.map((category, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* Providers */}
                {message.providers && message.providers.length > 0 && (
                  <div className="text-xs text-gray-600">
                    <strong>Providers:</strong> {message.providers.join(', ')}
                  </div>
                )}
                
                {/* Contact Info */}
                {message.contact_info && Object.keys(message.contact_info).length > 0 && (
                  <div className="space-y-1">
                    {formatContactInfo(message.contact_info).map((contact, index) => (
                      <div key={index} className="flex items-center space-x-2 text-xs">
                        <contact.icon className="h-3 w-3 text-gray-500" />
                        <span className="text-gray-600">
                          {contact.type === 'email' ? (
                            <a href={`mailto:${contact.value}`} className="text-blue-600 hover:text-blue-800">
                              {contact.value}
                            </a>
                          ) : contact.type === 'phone' ? (
                            <a href={`tel:${contact.value}`} className="text-blue-600 hover:text-blue-800">
                              {contact.value}
                            </a>
                          ) : contact.type === 'website' ? (
                            <a href={contact.value} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                              {contact.value}
                            </a>
                          ) : (
                            contact.value
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Timestamp */}
            <div className={`text-xs mt-2 ${isUser ? 'text-primary-200' : 'text-gray-500'}`}>
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h2 className="mt-4 text-xl font-semibold text-gray-900">
          Please log in to start chatting
        </h2>
        <p className="mt-2 text-gray-600">
          You need to be authenticated to chat with your documents.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-200px)] flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{config.brand_logo}</span>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Chat with {config.brand_name}
            </h1>
            <p className="text-gray-600">
              Ask questions about your uploaded documents
            </p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="btn-secondary text-sm"
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg p-4 mb-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <SparklesIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-600 mb-4">
              Ask me anything about your uploaded documents
            </p>
            <div className="text-left max-w-md mx-auto">
              <p className="text-sm text-gray-500 mb-2">Example questions:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• "What services are available for healthcare?"</li>
                <li>• "How can I contact the housing assistance program?"</li>
                <li>• "What are the requirements for financial aid?"</li>
              </ul>
            </div>
          </div>
        ) : (
          <div>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="flex flex-row">
                  <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center mr-2">
                    <span className="text-lg">{config.brand_logo}</span>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={sendMessage} className="flex space-x-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 input-field"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!inputMessage.trim() || isLoading}
          className="btn-primary px-4 py-2"
        >
          <PaperAirplaneIcon className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
};

export default Chat;