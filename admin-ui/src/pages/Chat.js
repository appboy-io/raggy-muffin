import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from 'react-query';
import { chatAPI, customerAPI } from '../services/api';
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
  ChatBubbleLeftRightIcon,
  CogIcon,
  EyeIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

// Component to format assistant messages with proper styling
function FormattedAssistantMessage({ content, isStreaming = false }) {
  const formatContent = (text) => {
    // Handle case where newlines might be missing or text is on one line
    // First, try to detect if this is improperly formatted single-line text
    if (!text.includes('\n') && text.includes('**') && text.includes('•')) {
      // Try to reconstruct formatting from markdown patterns
      text = text
        .replace(/\*\*([^*]+)\*\*/g, '\n\n$1\n') // Add newlines around headers
        .replace(/•/g, '\n•') // Add newlines before bullets
        .trim();
    }
    
    // Split by double newlines to separate sections
    const sections = text.split('\n\n');
    const formatted = [];
    
    sections.forEach((section, sectionIndex) => {
      const lines = section.split('\n');
      const sectionElements = [];
      
      lines.forEach((line, lineIndex) => {
        const trimmedLine = line.trim();
        if (!trimmedLine) return;
        
        // Check for headers (with ** or ending with :)
        if ((trimmedLine.startsWith('**') && trimmedLine.endsWith(':**')) || 
            (trimmedLine.startsWith('**') && trimmedLine.endsWith('**'))) {
          // Header section
          const headerText = trimmedLine.replace(/\*\*/g, '');
          sectionElements.push(
            <div key={`${sectionIndex}-${lineIndex}`} className="font-semibold text-gray-900 mt-3 mb-2 first:mt-0">
              {headerText}
            </div>
          );
        } else if (trimmedLine.endsWith(':') && !trimmedLine.startsWith('•')) {
          // Plain header without markdown
          sectionElements.push(
            <div key={`${sectionIndex}-${lineIndex}`} className="font-semibold text-gray-900 mt-3 mb-2 first:mt-0">
              {trimmedLine}
            </div>
          );
        } else if (trimmedLine.startsWith('•')) {
          // Bullet point
          const bulletText = trimmedLine.substring(1).trim();
          
          // Check if it's contact info based on content
          if (bulletText.match(/^(Call|Email|Visit|Location):/i)) {
            sectionElements.push(
              <div key={`${sectionIndex}-${lineIndex}`} className="flex items-center gap-2 py-1 ml-2">
                {getContactIcon(bulletText)}
                <span className="text-gray-700">{formatContactInfo(bulletText)}</span>
              </div>
            );
          } else {
            sectionElements.push(
              <div key={`${sectionIndex}-${lineIndex}`} className="flex items-start gap-2 py-1 ml-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span className="text-gray-700 flex-1">{bulletText}</span>
              </div>
            );
          }
        } else {
          // Regular content
          sectionElements.push(
            <div key={`${sectionIndex}-${lineIndex}`} className="text-gray-700 leading-relaxed">
              {trimmedLine}
            </div>
          );
        }
      });
      
      // Add section with spacing
      if (sectionElements.length > 0) {
        formatted.push(
          <div key={sectionIndex} className={sectionIndex > 0 ? 'mt-3' : ''}>
            {sectionElements}
          </div>
        );
      }
    });
    
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
    if (text.toLowerCase().startsWith('email:')) {
      const email = text.replace(/^email:\s*/i, '').trim();
      return (
        <span>
          Email: <a href={`mailto:${email}`} className="text-blue-600 hover:underline">{email}</a>
        </span>
      );
    } else if (text.toLowerCase().startsWith('call:')) {
      const phone = text.replace(/^call:\s*/i, '').trim();
      return (
        <span>
          Call: <a href={`tel:${phone}`} className="text-green-600 hover:underline">{phone}</a>
        </span>
      );
    } else if (text.toLowerCase().startsWith('phone:')) {
      const phone = text.replace(/^phone:\s*/i, '').trim();
      return (
        <span>
          Phone: <a href={`tel:${phone}`} className="text-green-600 hover:underline">{phone}</a>
        </span>
      );
    } else if (text.toLowerCase().startsWith('visit:')) {
      const website = text.replace(/^visit:\s*/i, '').trim();
      return (
        <span>
          Visit: <a href={website} target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">{website}</a>
        </span>
      );
    } else if (text.toLowerCase().startsWith('website:')) {
      const website = text.replace(/^website:\s*/i, '').trim();
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

// Tooltip component for agent settings
function Tooltip({ children, content, position = "right" }) {
  const [isVisible, setIsVisible] = useState(false);
  
  const positionClasses = {
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2"
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>
      {isVisible && (
        <div className={`absolute z-50 ${positionClasses[position]}`}>
          <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 max-w-xs shadow-lg">
            <div className="relative">
              {content}
              {/* Arrow pointer */}
              {position === "right" && (
                <div className="absolute top-1/2 -left-1 -translate-y-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
              )}
              {position === "left" && (
                <div className="absolute top-1/2 -right-1 -translate-y-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
              )}
              {position === "top" && (
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
              )}
              {position === "bottom" && (
                <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Chat() {
  // Tab state
  const [activeTab, setActiveTab] = useState('chat');
  
  // Chat state
  const [message, setMessage] = useState('');
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const { config } = useConfig();
  
  // Agent settings state
  const [agentConfig, setAgentConfig] = useState(null);
  const [agentConfigLoading, setAgentConfigLoading] = useState(false);
  const [personalityOptions, setPersonalityOptions] = useState(null);
  const [previewPrompt, setPreviewPrompt] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);

  const { data: sessions } = useQuery('chatSessions', chatAPI.getChatSessions);
  const { data: dashboard } = useQuery('dashboard', customerAPI.getDashboard);
  
  // Debug logging
  console.log('Dashboard data:', dashboard);

  // Load agent config and personality options on tab change
  useEffect(() => {
    if (activeTab === 'settings') {
      loadAgentConfig();
      loadPersonalityOptions();
    }
  }, [activeTab]);

  const loadAgentConfig = async () => {
    setAgentConfigLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/agent/config`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
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
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
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
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
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
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
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
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
            <Tooltip content="Configure your agent's basic identity and role. This determines how your agent introduces itself to users.">
              <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Agent Name
                </label>
                <Tooltip content="The name your agent will use when introducing itself to users. Keep it simple and memorable." position="top">
                  <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </Tooltip>
              </div>
              <input
                type="text"
                value={localConfig.agent_name || ''}
                onChange={(e) => handleConfigChange('agent_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Assistant"
                maxLength={50}
              />
            </div>
            
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Agent Role
                </label>
                <Tooltip content="Describes what your agent's primary function is (e.g., 'Customer Support Assistant', 'Healthcare Navigator'). This helps set user expectations." position="top">
                  <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </Tooltip>
              </div>
              <input
                type="text"
                value={localConfig.agent_role || ''}
                onChange={(e) => handleConfigChange('agent_role', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="helpful assistant"
              />
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Agent First Response
              </label>
              <Tooltip content="The initial message your AI agent will send when starting a new conversation. This is different from the widget's welcome message that users see before chatting." position="top">
                <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
              </Tooltip>
            </div>
            <textarea
              value={localConfig.greeting_message || ''}
              onChange={(e) => handleConfigChange('greeting_message', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              rows={3}
              maxLength={500}
              placeholder="Hello! I'm here to help you with any questions you have."
            />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-medium text-gray-900">Personality & Style</h3>
            <Tooltip content="Define how your agent communicates and behaves. These settings shape the tone and style of responses.">
              <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Personality Traits (Max 5)
              </label>
              <Tooltip content="Select up to 5 traits that define your agent's personality. These influence how the agent expresses itself and interacts with users." position="top">
                <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
              </Tooltip>
            </div>
            <div className="flex flex-wrap gap-2">
              {personalityOptions.personality_traits.map((trait) => (
                <button
                  key={trait.value}
                  onClick={() => handlePersonalityTraitToggle(trait.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                    (localConfig.personality_traits || []).includes(trait.value)
                      ? 'bg-indigo-100 border-indigo-200 text-indigo-700'
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
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Response Style
                </label>
                <Tooltip content="Controls how formal or casual your agent's responses are. This affects sentence structure, vocabulary, and overall tone." position="top">
                  <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </Tooltip>
              </div>
              <select
                value={localConfig.response_style || 'conversational'}
                onChange={(e) => handleConfigChange('response_style', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                {personalityOptions.response_styles.map((style) => (
                  <option key={style.value} value={style.value}>
                    {style.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Industry
                </label>
                <Tooltip content="Select the industry context for your agent. This helps the agent use appropriate terminology and understand industry-specific concepts." position="top">
                  <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </Tooltip>
              </div>
              <select
                value={localConfig.industry || 'general'}
                onChange={(e) => handleConfigChange('industry', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
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
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-medium text-gray-900">Advanced Settings</h3>
            <Tooltip content="Fine-tune your agent's behavior with custom instructions and advanced prompting. These settings require technical knowledge.">
              <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Custom Instructions
              </label>
              <Tooltip content="Add specific guidelines or rules for your agent to follow. For example: 'Always ask for clarification before providing medical advice' or 'Limit responses to 100 words'." position="top">
                <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
              </Tooltip>
            </div>
            <textarea
              value={localConfig.custom_instructions || ''}
              onChange={(e) => handleConfigChange('custom_instructions', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              rows={4}
              placeholder="Add any specific instructions for your agent..."
            />
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-gray-700">
                System Prompt Override (Advanced)
              </label>
              <Tooltip content="⚠️ Advanced users only. This completely replaces the auto-generated system prompt. Leave empty to use the settings above. Incorrect prompts can break your agent's functionality." position="top">
                <InformationCircleIcon className="h-4 w-4 text-yellow-500 hover:text-yellow-600 cursor-help" />
              </Tooltip>
            </div>
            <textarea
              value={localConfig.system_prompt || ''}
              onChange={(e) => handleConfigChange('system_prompt', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
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
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md font-medium flex items-center space-x-2"
          >
            <EyeIcon className="h-4 w-4" />
            <span>{previewLoading ? 'Generating...' : 'Preview Prompt'}</span>
          </button>

          <button
            onClick={handleSave}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md font-medium"
          >
            Save Settings
          </button>
        </div>

        {showPreview && previewPrompt && (
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
            <h4 className="text-lg font-medium text-gray-900 mb-3">Generated Prompt Preview</h4>
            <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-white p-4 rounded border max-h-96 overflow-y-auto">
              {previewPrompt}
            </pre>
          </div>
        )}
      </div>
    );
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
                {config.brand_name} Assistant
              </h1>
              <p className="text-sm text-gray-500">
                Test your AI assistant and manage its settings
              </p>
            </div>
            {activeTab === 'chat' && currentSession && (
              <div className="text-sm text-gray-500">
                Session: {currentSession.slice(0, 8)}...
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200 px-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'border-indigo-500 text-indigo-600'
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
                  ? 'border-indigo-500 text-indigo-600'
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

        {/* Main Content Area */}
        {activeTab === 'chat' ? (
          <>
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
                            ) : dashboard?.widget_config?.avatar_url ? (
                              <img
                                src={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}${dashboard.widget_config.avatar_url}`}
                                alt="Assistant avatar"
                                className="w-5 h-5 rounded-full object-cover"
                              />
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
          </>
        ) : (
          <AgentSettings />
        )}
      </div>
    </div>
  );
}