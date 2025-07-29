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
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(
        user.tenant_id,
        inputMessage,
        sessionId
      );

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        contact_info: response.data.contact_info || {},
        categories: response.data.categories || [],
        providers: response.data.providers || [],
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Set session ID for future messages
      if (response.data.session_id && !sessionId) {
        setSessionId(response.data.session_id);
      }

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
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
              {message.content.split('\n').map((line, index) => (
                <p key={index} className="mb-1 last:mb-0">
                  {line}
                </p>
              ))}
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