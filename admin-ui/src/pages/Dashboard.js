import React from 'react';
import { useQuery } from 'react-query';
import { useConfig } from '../context/ConfigContext';
import { useAuth } from '../context/AuthContext';
import { documentsAPI, chatAPI, customerAPI } from '../services/api';
import {
  DocumentIcon,
  ChatBubbleLeftRightIcon,
  PuzzlePieceIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

export default function Dashboard() {
  const { config } = useConfig();

  const { data: dashboard, isLoading: dashboardLoading } = useQuery('dashboard', customerAPI.getDashboard);
  const { data: documents } = useQuery('documents', documentsAPI.getDocuments);
  const { data: chatSessions } = useQuery('chatSessions', chatAPI.getChatSessions);

  // Use dashboard stats if available, otherwise fallback to direct API calls
  const stats = [
    {
      name: 'Total Documents',
      value: dashboard?.stats?.document_count || documents?.total || 0,
      icon: DocumentIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Chat Messages',
      value: dashboard?.stats?.message_count || chatSessions?.length || 0,
      icon: ChatBubbleLeftRightIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Storage Used',
      value: `${Math.round((documents?.documents?.reduce((acc, doc) => acc + doc.file_size, 0) || 0) / 1024 / 1024)}MB`,
      icon: ChartBarIcon,
      color: 'bg-yellow-500',
    },
    {
      name: 'Widget Status',
      value: dashboard?.stats?.widget_enabled ? 'Active' : 'Inactive',
      icon: PuzzlePieceIcon,
      color: dashboard?.stats?.widget_enabled ? 'bg-purple-500' : 'bg-gray-500',
    },
  ];

  const recentDocuments = documents?.documents?.slice(0, 5) || [];
  const recentSessions = chatSessions?.slice(0, 5) || [];

  if (dashboardLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome to {dashboard?.profile?.company_name || 'Your Dashboard'}!
        </h1>
        <p className="mt-2 text-gray-600">
          {dashboard?.profile?.onboarding_completed 
            ? `Here's what's happening with your ${config.brand_name} workspace.`
            : 'Complete your onboarding to get started with your AI assistant.'}
        </p>
        {dashboard?.profile && (
          <div className={`mt-4 border-l-4 p-4 ${
            dashboard.profile.onboarding_completed 
              ? 'bg-blue-50 border-blue-400' 
              : 'bg-yellow-50 border-yellow-400'
          }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                <div className={`h-5 w-5 ${
                  dashboard.profile.onboarding_completed ? 'text-blue-400' : 'text-yellow-400'
                }`}>
                  {config.brand_logo}
                </div>
              </div>
              <div className="ml-3 flex-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm ${
                      dashboard.profile.onboarding_completed ? 'text-blue-700' : 'text-yellow-700'
                    }`}>
                      <strong>Company:</strong> {dashboard.profile.company_name} 
                      {dashboard.profile.company_website && (
                        <span className="ml-2">
                          • <strong>Website:</strong> 
                          <a href={dashboard.profile.company_website} target="_blank" rel="noopener noreferrer" className="underline">
                            {dashboard.profile.company_website}
                          </a>
                        </span>
                      )}
                    </p>
                    <p className={`text-sm mt-1 ${
                      dashboard.profile.onboarding_completed ? 'text-blue-700' : 'text-yellow-700'
                    }`}>
                      <strong>Plan:</strong> {dashboard.profile.subscription_plan} 
                      • <strong>Contact:</strong> {dashboard.profile.contact_email}
                      {dashboard.profile.industry && (
                        <span className="ml-2">• <strong>Industry:</strong> {dashboard.profile.industry}</span>
                      )}
                    </p>
                  </div>
                  {!dashboard.profile.onboarding_completed && (
                    <a
                      href="/profile"
                      className="ml-4 bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 text-sm whitespace-nowrap"
                    >
                      Complete Setup
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`${stat.color} rounded-md p-3`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Documents */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Documents</h3>
          </div>
          <div className="px-6 py-4">
            {recentDocuments.length > 0 ? (
              <div className="space-y-3">
                {recentDocuments.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <DocumentIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 truncate max-w-xs">
                          {doc.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {doc.file_type} • {Math.round(doc.file_size / 1024)}KB
                        </p>
                      </div>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      doc.status === 'completed' 
                        ? 'bg-green-100 text-green-800'
                        : doc.status === 'processing'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No documents uploaded yet.
              </p>
            )}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <a
                href="/documents"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all documents →
              </a>
            </div>
          </div>
        </div>

        {/* Recent Chat Sessions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Chat Sessions</h3>
          </div>
          <div className="px-6 py-4">
            {recentSessions.length > 0 ? (
              <div className="space-y-3">
                {recentSessions.map((session) => (
                  <div key={session.session_id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <ChatBubbleLeftRightIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Session {session.session_id.slice(0, 8)}...
                        </p>
                        <p className="text-xs text-gray-500">
                          {session.messages.length} messages
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(session.last_activity).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No chat sessions yet.
              </p>
            )}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <a
                href="/chat"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all sessions →
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
        </div>
        <div className="px-6 py-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <a
              href="/documents"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <DocumentIcon className="h-8 w-8 text-blue-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Upload Document</h4>
                <p className="text-sm text-gray-500">Add new content to your knowledge base</p>
              </div>
            </a>
            <a
              href="/chat"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-green-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Test Chat</h4>
                <p className="text-sm text-gray-500">Try out your AI assistant</p>
              </div>
            </a>
            <a
              href="/widgets"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <PuzzlePieceIcon className="h-8 w-8 text-purple-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Configure Widget</h4>
                <p className="text-sm text-gray-500">Customize your embeddable chat</p>
              </div>
            </a>
          </div>
          
          {/* Widget Integration Info */}
          {dashboard?.stats && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Widget Integration</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Embed URL:</p>
                  <code className="bg-white px-2 py-1 rounded text-xs break-all">{dashboard.stats.embed_url}</code>
                </div>
                <div>
                  <p className="text-gray-600">Preview:</p>
                  <a href={dashboard.stats.preview_url} target="_blank" rel="noopener noreferrer" 
                     className="text-blue-600 hover:text-blue-500 underline">
                    View Widget Preview →
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}