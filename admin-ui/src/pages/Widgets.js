import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { widgetsAPI } from '../services/api';
import { useConfig } from '../context/ConfigContext';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  EyeIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

export default function Widgets() {
  const [copied, setCopied] = useState(false);
  const { config } = useConfig();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: widgetConfig, isLoading } = useQuery(
    'widgetConfig',
    widgetsAPI.getWidgetConfig
  );

  const updateMutation = useMutation(
    (config) => widgetsAPI.updateWidgetConfig(config),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('widgetConfig');
        toast.success('Widget configuration updated!');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Update failed');
      },
    }
  );

  const [formData, setFormData] = useState({
    widget_title: '',
    widget_subtitle: '',
    primary_color: '',
    secondary_color: '',
    welcome_message: '',
    placeholder_text: '',
    is_enabled: true,
  });

  React.useEffect(() => {
    if (widgetConfig) {
      setFormData({
        widget_title: widgetConfig.widget_title || '',
        widget_subtitle: widgetConfig.widget_subtitle || '',
        primary_color: widgetConfig.primary_color || config.primary_color,
        secondary_color: widgetConfig.secondary_color || config.secondary_color,
        welcome_message: widgetConfig.welcome_message || '',
        placeholder_text: widgetConfig.placeholder_text || '',
        is_enabled: widgetConfig.is_enabled ?? true,
      });
    }
  }, [widgetConfig, config]);

  const handleSubmit = (e) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const embedCode = `<script src="${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/widgets/${user?.tenantId}/embed.js"></script>`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    toast.success('Embed code copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const openPreview = () => {
    const previewUrl = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/widgets/${user?.tenantId}/preview`;
    window.open(previewUrl, '_blank');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Widget Configuration</h1>
        <p className="mt-2 text-gray-600">
          Customize your embeddable chat widget and get the code to add to your website.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Configuration Form */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Widget Settings</h2>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Widget Title
              </label>
              <input
                type="text"
                name="widget_title"
                value={formData.widget_title}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., Cleona Assistant"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Widget Subtitle
              </label>
              <input
                type="text"
                name="widget_subtitle"
                value={formData.widget_subtitle}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., How can I help you?"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Color
                </label>
                <div className="flex space-x-2">
                  <input
                    type="color"
                    name="primary_color"
                    value={formData.primary_color}
                    onChange={handleInputChange}
                    className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    name="primary_color"
                    value={formData.primary_color}
                    onChange={handleInputChange}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="#2E8B57"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secondary Color
                </label>
                <div className="flex space-x-2">
                  <input
                    type="color"
                    name="secondary_color"
                    value={formData.secondary_color}
                    onChange={handleInputChange}
                    className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    name="secondary_color"
                    value={formData.secondary_color}
                    onChange={handleInputChange}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="#4682B4"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Welcome Message
              </label>
              <textarea
                name="welcome_message"
                value={formData.welcome_message}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Hello! How can I assist you today?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Input Placeholder
              </label>
              <input
                type="text"
                name="placeholder_text"
                value={formData.placeholder_text}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Type your message..."
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="is_enabled"
                checked={formData.is_enabled}
                onChange={handleInputChange}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">
                Enable widget (users can access the chat)
              </label>
            </div>

            <button
              type="submit"
              disabled={updateMutation.isLoading}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {updateMutation.isLoading ? 'Saving...' : 'Save Configuration'}
            </button>
          </form>
        </div>

        {/* Preview & Embed Code */}
        <div className="space-y-6">
          {/* Widget Status */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Widget Status</h2>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Current Status</p>
                <p className={`text-lg font-medium ${formData.is_enabled ? 'text-green-600' : 'text-red-600'}`}>
                  {formData.is_enabled ? 'Active' : 'Disabled'}
                </p>
              </div>
              <div className={`w-3 h-3 rounded-full ${formData.is_enabled ? 'bg-green-400' : 'bg-red-400'}`}></div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={openPreview}
                className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-500"
              >
                <EyeIcon className="h-5 w-5" />
                <span>Preview Widget</span>
              </button>
            </div>
          </div>

          {/* Embed Code */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Embed Code</h2>
            <p className="text-sm text-gray-600 mb-4">
              Copy this code and paste it into your website's HTML where you want the chat widget to appear.
            </p>
            <div className="relative">
              <pre className="bg-gray-100 p-4 rounded-md text-sm overflow-x-auto border">
                <code>{embedCode}</code>
              </pre>
              <button
                onClick={copyToClipboard}
                className="absolute top-2 right-2 p-2 text-gray-500 hover:text-gray-700"
              >
                {copied ? (
                  <CheckIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <ClipboardDocumentIcon className="h-5 w-5" />
                )}
              </button>
            </div>
            {copied && (
              <p className="text-sm text-green-600 mt-2">Copied to clipboard!</p>
            )}
          </div>

          {/* Widget Preview */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Widget Preview</h2>
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div 
                className="inline-flex items-center px-4 py-2 rounded-lg shadow-sm text-white text-sm"
                style={{ backgroundColor: formData.primary_color }}
              >
                <span className="mr-2">{config.brand_logo}</span>
                {formData.widget_title || 'Chat Assistant'}
              </div>
              <div className="mt-2 text-sm text-gray-600">
                {formData.widget_subtitle || 'How can I help you?'}
              </div>
              <div className="mt-3 p-3 bg-white rounded border text-sm">
                {formData.welcome_message || 'Hello! How can I assist you today?'}
              </div>
              <div className="mt-3">
                <input
                  type="text"
                  placeholder={formData.placeholder_text || 'Type your message...'}
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                  disabled
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}