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
  CogIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

const Chat = () => {
  const { user, isAuthenticated } = useAuth();
  const { config } = useConfig();
  
  // Tab state
  const [activeTab, setActiveTab] = useState('chat');
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);
  
  // Agent settings state
  const [agentConfig, setAgentConfig] = useState(null);
  const [agentConfigLoading, setAgentConfigLoading] = useState(false);
  const [personalityOptions, setPersonalityOptions] = useState(null);
  const [previewPrompt, setPreviewPrompt] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);

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

  // Load agent config and personality options on tab change
  useEffect(() => {
    if (activeTab === 'settings' && user?.access_token) {
      loadAgentConfig();
      loadPersonalityOptions();
    }
  }, [activeTab, user?.access_token]);

  const loadAgentConfig = async () => {
    setAgentConfigLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/agent/config`, {
        headers: {
          'Authorization': `Bearer ${user.access_token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const config = await response.json();
        setAgentConfig(config);
      } else {
        throw new Error('Failed to load agent config');
      }
    } catch (error) {
      console.error('Error loading agent config:', error);
      toast.error('Failed to load agent settings');
    } finally {
      setAgentConfigLoading(false);
    }
  };

  const loadPersonalityOptions = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/agent/personality-options`);
      
      if (response.ok) {
        const options = await response.json();
        setPersonalityOptions(options);
      }
    } catch (error) {
      console.error('Error loading personality options:', error);
    }
  };

  const updateAgentConfig = async (configData) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/agent/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${user.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
      });
      
      if (response.ok) {
        const updatedConfig = await response.json();
        setAgentConfig(updatedConfig);
        toast.success('Agent settings saved successfully!');
        return true;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update agent config');
      }
    } catch (error) {
      console.error('Error updating agent config:', error);
      toast.error(error.message || 'Failed to save agent settings');
      return false;
    }
  };

  const generatePreview = async (configData) => {
    setPreviewLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/agent/preview-prompt`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
      });
      
      if (response.ok) {
        const preview = await response.json();
        setPreviewPrompt(preview.preview);
      } else {
        throw new Error('Failed to generate preview');
      }
    } catch (error) {
      console.error('Error generating preview:', error);
      toast.error('Failed to generate preview');
    } finally {
      setPreviewLoading(false);
    }
  };

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

  const AgentSettings = () => {
    const [localConfig, setLocalConfig] = useState(null);
    const [showPreview, setShowPreview] = useState(false);

    useEffect(() => {
      if (agentConfig) {
        setLocalConfig({ ...agentConfig });
      }
    }, [agentConfig]);

    const handleConfigChange = (field, value) => {
      setLocalConfig(prev => ({
        ...prev,
        [field]: value
      }));
    };

    const handlePersonalityTraitToggle = (trait) => {
      const currentTraits = localConfig?.personality_traits || [];
      const newTraits = currentTraits.includes(trait)
        ? currentTraits.filter(t => t !== trait)
        : [...currentTraits, trait];
      
      if (newTraits.length <= 5) {
        handleConfigChange('personality_traits', newTraits);
      } else {
        toast.error('Maximum 5 personality traits allowed');
      }
    };

    const handleSave = async () => {
      if (!localConfig) return;
      
      const success = await updateAgentConfig(localConfig);
      if (success) {
        setShowPreview(false);
      }
    };

    const handleGeneratePreview = async () => {
      if (!localConfig) return;
      
      await generatePreview({
        agent_name: localConfig.agent_name,
        agent_role: localConfig.agent_role,
        personality_traits: localConfig.personality_traits,
        custom_instructions: localConfig.custom_instructions,
        response_style: localConfig.response_style,
        industry: localConfig.industry
      });
      setShowPreview(true);
    };

    if (agentConfigLoading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-2">Loading agent settings...</span>
        </div>
      );
    }

    if (!localConfig || !personalityOptions) {
      return (
        <div className="text-center py-12">
          <CogIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            Unable to load settings
          </h3>
          <p className="mt-2 text-gray-600">
            Please try refreshing the page.
          </p>
        </div>
      );
    }

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Agent Name
              </label>
              <input
                type="text"
                value={localConfig.agent_name || ''}
                onChange={(e) => handleConfigChange('agent_name', e.target.value)}
                className="input-field"
                placeholder="Assistant"
                maxLength={50}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Agent Role
              </label>
              <input
                type="text"
                value={localConfig.agent_role || ''}
                onChange={(e) => handleConfigChange('agent_role', e.target.value)}
                className="input-field"
                placeholder="helpful assistant"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Greeting Message
            </label>
            <textarea
              value={localConfig.greeting_message || ''}
              onChange={(e) => handleConfigChange('greeting_message', e.target.value)}
              className="input-field"
              rows={3}
              maxLength={500}
              placeholder="Hello! How can I help you today?"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Personality & Style</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Personality Traits (Max 5)
            </label>
            <div className="flex flex-wrap gap-2">
              {personalityOptions.personality_traits.map((trait) => (
                <button
                  key={trait.value}
                  onClick={() => handlePersonalityTraitToggle(trait.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                    (localConfig.personality_traits || []).includes(trait.value)
                      ? 'bg-primary-100 border-primary-200 text-primary-700'
                      : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {trait.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Response Style
              </label>
              <select
                value={localConfig.response_style || 'conversational'}
                onChange={(e) => handleConfigChange('response_style', e.target.value)}
                className="input-field"
              >
                {personalityOptions.response_styles.map((style) => (
                  <option key={style.value} value={style.value}>
                    {style.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <select
                value={localConfig.industry || 'general'}
                onChange={(e) => handleConfigChange('industry', e.target.value)}
                className="input-field"
              >
                {personalityOptions.industries.map((industry) => (
                  <option key={industry.value} value={industry.value}>
                    {industry.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Advanced Settings</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Instructions
            </label>
            <textarea
              value={localConfig.custom_instructions || ''}
              onChange={(e) => handleConfigChange('custom_instructions', e.target.value)}
              className="input-field"
              rows={4}
              placeholder="Add any specific instructions for your agent..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              System Prompt Override (Advanced)
            </label>
            <textarea
              value={localConfig.system_prompt || ''}
              onChange={(e) => handleConfigChange('system_prompt', e.target.value)}
              className="input-field"
              rows={6}
              maxLength={5000}
              placeholder="Leave empty to use auto-generated prompt based on settings above..."
            />
            <p className="text-sm text-gray-500 mt-1">
              If provided, this will override the auto-generated prompt entirely.
            </p>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <button
            onClick={handleGeneratePreview}
            disabled={previewLoading}
            className="btn-secondary flex items-center space-x-2"
          >
            <EyeIcon className="h-4 w-4" />
            <span>{previewLoading ? 'Generating...' : 'Preview Prompt'}</span>
          </button>

          <button
            onClick={handleSave}
            className="btn-primary"
          >
            Save Settings
          </button>
        </div>

        {showPreview && previewPrompt && (
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
            <h4 className="text-lg font-medium text-gray-900 mb-3">Generated Prompt Preview</h4>
            <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-white p-4 rounded border">
              {previewPrompt}
            </pre>
          </div>
        )}
      </div>
    );
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
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{config.brand_logo}</span>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Chat with {config.brand_name}
            </h1>
            <p className="text-gray-600">
              Manage your AI assistant and chat with your documents
            </p>
          </div>
        </div>
        {activeTab === 'chat' && messages.length > 0 && (
          <button
            onClick={clearChat}
            className="btn-secondary text-sm"
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('chat')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'chat'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
              <span>Chat</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'settings'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <CogIcon className="h-5 w-5" />
              <span>Agent Settings</span>
            </div>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'chat' ? (
        <div className="h-[calc(100vh-280px)] flex flex-col">
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
      ) : (
        <AgentSettings />
      )}
    </div>
  );
};

export default Chat;