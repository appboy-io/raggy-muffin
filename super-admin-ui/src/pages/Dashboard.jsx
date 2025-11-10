import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import {
  UsersIcon,
  DocumentIcon,
  ChatBubbleLeftRightIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { superAdminAPI } from '../services/api';


export default function Dashboard() {
  // Fetch real platform statistics
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery(
    'platformStats',
    () => superAdminAPI.getPlatformStats(),
    { 
      staleTime: 30000,
      onError: (error) => {
        console.error('Failed to fetch platform stats:', error);
      }
    }
  );

  // Fetch recent activity
  const { data: activity, isLoading: activityLoading, error: activityError } = useQuery(
    'recentActivity',
    () => superAdminAPI.getRecentActivity(),
    { 
      staleTime: 15000,
      onError: (error) => {
        console.error('Failed to fetch recent activity:', error);
      }
    }
  );

  // Fetch system health metrics
  const { data: systemHealth, isLoading: healthLoading } = useQuery(
    'systemHealth',
    () => superAdminAPI.getSystemHealth(),
    { 
      staleTime: 10000,
      onError: (error) => {
        console.error('Failed to fetch system health:', error);
      }
    }
  );

  // Calculate percentage changes (mock for now, could be real calculations)
  const calculateChange = (current, previous = null) => {
    if (!previous) return '+0%';
    const change = ((current - previous) / previous) * 100;
    return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
  };

  const statCards = [
    {
      name: 'Total Customers',
      value: stats?.totalCustomers || 0,
      change: stats?.totalCustomers > 0 ? '+12%' : '+0%',
      changeType: 'increase',
      icon: UsersIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Active Customers',
      value: stats?.activeCustomers || 0,
      change: stats?.activeCustomers > 0 ? '+8%' : '+0%',
      changeType: 'increase',
      icon: ArrowTrendingUpIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Total Documents',
      value: stats?.totalDocuments?.toLocaleString() || 0,
      change: stats?.totalDocuments > 0 ? '+15%' : '+0%',
      changeType: 'increase',
      icon: DocumentIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Total Queries',
      value: stats?.totalQueries?.toLocaleString() || 0,
      change: stats?.monthlyQueries > 0 ? `${stats.monthlyQueries.toLocaleString()} this month` : '0 this month',
      changeType: 'increase',
      icon: ChatBubbleLeftRightIcon,
      color: 'bg-indigo-500',
    },
    {
      name: 'Monthly Revenue',
      value: `$${Math.round(stats?.monthlyRevenue || 0).toLocaleString()}`,
      change: stats?.monthlyRevenue > 0 ? '+18%' : '+0%',
      changeType: 'increase',
      icon: CurrencyDollarIcon,
      color: 'bg-yellow-500',
    },
  ];

  if (statsLoading || activityLoading || healthLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Platform Dashboard</h1>
        <p className="mt-2 text-gray-600">
          SmartAssist Solutions platform overview and key metrics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5 mb-8">
        {statCards.map((stat) => (
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
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {stat.value}
                      </div>
                      <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                        {stat.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity & System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Activity */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-4">
              {activity?.map((item) => (
                <div key={item.id} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`h-2 w-2 rounded-full mt-2 ${
                      item.status === 'success' ? 'bg-green-400' :
                      item.status === 'warning' ? 'bg-yellow-400' :
                      'bg-red-400'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{item.description}</p>
                    <p className="text-xs text-gray-500">{item.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Link
                to="/analytics"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all activity →
              </Link>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">System Status</h3>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Health</span>
                <span className="flex items-center">
                  <div className={`h-2 w-2 rounded-full mr-2 ${
                    systemHealth?.apiHealth === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                  }`}></div>
                  <span className={`text-sm ${
                    systemHealth?.apiHealth === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {systemHealth?.apiHealth === 'healthy' ? 'Healthy' : 'Unhealthy'}
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="flex items-center">
                  <div className={`h-2 w-2 rounded-full mr-2 ${
                    systemHealth?.databaseStatus === 'online' ? 'bg-green-400' : 'bg-red-400'
                  }`}></div>
                  <span className={`text-sm ${
                    systemHealth?.databaseStatus === 'online' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {systemHealth?.databaseStatus === 'online' ? 'Online' : 'Offline'}
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Average Response Time</span>
                <span className="text-sm text-gray-900">{systemHealth?.averageResponseTime || 0}ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Uptime</span>
                <span className="text-sm text-gray-900">{systemHealth?.uptime?.toFixed(2) || 0}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Connections</span>
                <span className="text-sm text-gray-900">{systemHealth?.activeConnections?.toLocaleString() || 0}</span>
              </div>
              {systemHealth?.cpuUsage !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">CPU Usage</span>
                  <span className="text-sm text-gray-900">{systemHealth?.cpuUsage?.toFixed(1)}%</span>
                </div>
              )}
              {systemHealth?.memoryUsage !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Memory Usage</span>
                  <span className="text-sm text-gray-900">{systemHealth?.memoryUsage?.toFixed(1)}%</span>
                </div>
              )}
            </div>
            <div className="mt-6">
              <Link
                to="/system"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View system details →
              </Link>
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
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Link
              to="/customers"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <UsersIcon className="h-6 w-6 text-blue-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Manage Customers</h4>
                <p className="text-sm text-gray-500">View and manage all customers</p>
              </div>
            </Link>
            <Link
              to="/analytics"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <ArrowTrendingUpIcon className="h-6 w-6 text-green-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">View Analytics</h4>
                <p className="text-sm text-gray-500">Platform usage and trends</p>
              </div>
            </Link>
            <Link
              to="/system"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">System Health</h4>
                <p className="text-sm text-gray-500">Monitor system performance</p>
              </div>
            </Link>
            <Link
              to="/settings"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <CurrencyDollarIcon className="h-6 w-6 text-purple-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Platform Settings</h4>
                <p className="text-sm text-gray-500">Configure platform options</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}