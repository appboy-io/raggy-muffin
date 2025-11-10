import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  CpuChipIcon,
  ServerIcon,
  CloudIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  SignalIcon,
} from '@heroicons/react/24/outline';
import { superAdminAPI } from '../services/api';

export default function SystemHealth() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch system health metrics
  const { data: health, isLoading, error, refetch } = useQuery(
    'systemHealth',
    () => superAdminAPI.getSystemHealth(),
    {
      refetchInterval: autoRefresh ? 5000 : false, // Auto-refresh every 5 seconds
      staleTime: 3000,
      onError: (error) => {
        console.error('Failed to fetch system health:', error);
      }
    }
  );

  // Fetch platform stats for additional metrics
  const { data: stats } = useQuery(
    'systemStats',
    () => superAdminAPI.getPlatformStats(),
    {
      refetchInterval: autoRefresh ? 30000 : false, // Auto-refresh every 30 seconds
      staleTime: 15000,
    }
  );

  const getStatusColor = (status) => {
    if (status === 'healthy' || status === 'online') return 'text-green-600';
    if (status === 'degraded') return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusBgColor = (status) => {
    if (status === 'healthy' || status === 'online') return 'bg-green-100';
    if (status === 'degraded') return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getCPUStatusColor = (usage) => {
    if (usage < 50) return 'text-green-600';
    if (usage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMemoryStatusColor = (usage) => {
    if (usage < 60) return 'text-green-600';
    if (usage < 85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getResponseTimeColor = (ms) => {
    if (ms < 200) return 'text-green-600';
    if (ms < 500) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load system health metrics. Please try again.</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm text-red-600 hover:text-red-800"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
            <p className="mt-2 text-gray-600">
              Monitor platform performance, uptime, and system resources in real-time
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Refresh
            </button>
            <label className="inline-flex items-center">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Auto-refresh</span>
            </label>
          </div>
        </div>
      </div>

      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {/* API Status */}
        <div className={`bg-white rounded-lg shadow p-6 ${getStatusBgColor(health?.apiHealth)}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">API Status</p>
              <p className={`text-2xl font-bold mt-1 ${getStatusColor(health?.apiHealth)}`}>
                {health?.apiHealth === 'healthy' ? 'Healthy' : 'Unhealthy'}
              </p>
            </div>
            {health?.apiHealth === 'healthy' ? (
              <CheckCircleIcon className="h-8 w-8 text-green-500" />
            ) : (
              <XCircleIcon className="h-8 w-8 text-red-500" />
            )}
          </div>
        </div>

        {/* Database Status */}
        <div className={`bg-white rounded-lg shadow p-6 ${getStatusBgColor(health?.databaseStatus)}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Database</p>
              <p className={`text-2xl font-bold mt-1 ${getStatusColor(health?.databaseStatus)}`}>
                {health?.databaseStatus === 'online' ? 'Online' : 'Offline'}
              </p>
            </div>
            <CloudIcon className={`h-8 w-8 ${health?.databaseStatus === 'online' ? 'text-green-500' : 'text-red-500'}`} />
          </div>
        </div>

        {/* Uptime */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Uptime</p>
              <p className="text-2xl font-bold mt-1 text-gray-900">
                {health?.uptime?.toFixed(2)}%
              </p>
            </div>
            <ClockIcon className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        {/* Active Connections */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Connections</p>
              <p className="text-2xl font-bold mt-1 text-gray-900">
                {health?.activeConnections?.toLocaleString() || 0}
              </p>
            </div>
            <SignalIcon className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Resource Usage */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Resource Usage</h3>
          <div className="space-y-4">
            {/* CPU Usage */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">CPU Usage</span>
                <span className={`text-sm font-bold ${getCPUStatusColor(health?.cpuUsage)}`}>
                  {health?.cpuUsage?.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health?.cpuUsage < 50 ? 'bg-green-500' :
                    health?.cpuUsage < 80 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(health?.cpuUsage || 0, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Memory Usage */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">Memory Usage</span>
                <span className={`text-sm font-bold ${getMemoryStatusColor(health?.memoryUsage)}`}>
                  {health?.memoryUsage?.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health?.memoryUsage < 60 ? 'bg-green-500' :
                    health?.memoryUsage < 85 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(health?.memoryUsage || 0, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Response Time */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">Avg Response Time</span>
                <span className={`text-sm font-bold ${getResponseTimeColor(health?.averageResponseTime)}`}>
                  {health?.averageResponseTime}ms
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health?.averageResponseTime < 200 ? 'bg-green-500' :
                    health?.averageResponseTime < 500 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((health?.averageResponseTime / 1000) * 100, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Error Rate */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">Error Rate</span>
                <span className={`text-sm font-bold ${
                  health?.errorRate < 1 ? 'text-green-600' :
                  health?.errorRate < 5 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {health?.errorRate}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health?.errorRate < 1 ? 'bg-green-500' :
                    health?.errorRate < 5 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(health?.errorRate * 10, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Platform Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Platform Activity</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-sm text-gray-600">Total Customers</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.totalCustomers || 0}</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-sm text-gray-600">Active Customers</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.activeCustomers || 0}</p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <p className="text-sm text-gray-600">Total Queries</p>
              <p className="text-2xl font-bold text-gray-900">{(stats?.totalQueries || 0).toLocaleString()}</p>
            </div>
            <div className="border-l-4 border-orange-500 pl-4">
              <p className="text-sm text-gray-600">Monthly Queries</p>
              <p className="text-2xl font-bold text-gray-900">{(stats?.monthlyQueries || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">System Information</h3>
        </div>
        <div className="px-6 py-4">
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">API Health Check</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.apiHealth === 'healthy' ? '✅ Passing' : '❌ Failing'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Database Connection</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.databaseStatus === 'online' ? '✅ Connected' : '❌ Disconnected'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">System Uptime</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.uptime?.toFixed(3)}%</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Active Sessions</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.activeConnections || 0}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">CPU Load</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.cpuUsage?.toFixed(2)}%</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Memory Usage</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.memoryUsage?.toFixed(2)}%</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Response Time</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.averageResponseTime}ms avg</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Error Rate</dt>
              <dd className="mt-1 text-sm text-gray-900">{health?.errorRate}%</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Recent Incidents */}
      {health?.lastIncident && (
        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Last Incident</h3>
              <p className="mt-2 text-sm text-yellow-700">{health.lastIncident}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}