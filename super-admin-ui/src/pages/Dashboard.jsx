import React from 'react';
import { useQuery } from 'react-query';
import {
  UsersIcon,
  DocumentIcon,
  ChatBubbleLeftRightIcon,
  CurrencyDollarIcon,
  TrendingUpIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

// Mock data - in production this would come from the API
const mockStats = {
  totalCustomers: 156,
  activeCustomers: 142,
  totalDocuments: 45623,
  totalQueries: 892345,
  monthlyRevenue: 78650,
  systemHealth: 'healthy'
};

const mockRecentActivity = [
  {
    id: 1,
    type: 'customer_signup',
    description: 'New customer: TechCorp Inc. signed up',
    timestamp: '2 minutes ago',
    status: 'success'
  },
  {
    id: 2,
    type: 'usage_spike',
    description: 'RetailMax exceeded 80% of query limit',
    timestamp: '15 minutes ago',
    status: 'warning'
  },
  {
    id: 3,
    type: 'payment_success',
    description: 'Payment processed for HealthTech Solutions ($149)',
    timestamp: '1 hour ago',
    status: 'success'
  },
  {
    id: 4,
    type: 'system_alert',
    description: 'API response time increased to 450ms',
    timestamp: '2 hours ago',
    status: 'warning'
  },
];

export default function Dashboard() {
  // In production, these would be real API calls
  const { data: stats, isLoading: statsLoading } = useQuery('platformStats', 
    () => Promise.resolve(mockStats),
    { staleTime: 30000 }
  );

  const { data: activity, isLoading: activityLoading } = useQuery('recentActivity',
    () => Promise.resolve(mockRecentActivity),
    { staleTime: 15000 }
  );

  const statCards = [
    {
      name: 'Total Customers',
      value: stats?.totalCustomers || 0,
      change: '+12%',
      changeType: 'increase',
      icon: UsersIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Active Customers',
      value: stats?.activeCustomers || 0,
      change: '+8%',
      changeType: 'increase',
      icon: TrendingUpIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Total Documents',
      value: stats?.totalDocuments?.toLocaleString() || 0,
      change: '+15%',
      changeType: 'increase',
      icon: DocumentIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Total Queries',
      value: stats?.totalQueries?.toLocaleString() || 0,
      change: '+23%',
      changeType: 'increase',
      icon: ChatBubbleLeftRightIcon,
      color: 'bg-indigo-500',
    },
    {
      name: 'Monthly Revenue',
      value: `$${stats?.monthlyRevenue?.toLocaleString() || 0}`,
      change: '+18%',
      changeType: 'increase',
      icon: CurrencyDollarIcon,
      color: 'bg-yellow-500',
    },
  ];

  if (statsLoading || activityLoading) {
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
              <a
                href="/analytics"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all activity →
              </a>
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
                  <div className="h-2 w-2 bg-green-400 rounded-full mr-2"></div>
                  <span className="text-sm text-green-600">Healthy</span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="flex items-center">
                  <div className="h-2 w-2 bg-green-400 rounded-full mr-2"></div>
                  <span className="text-sm text-green-600">Online</span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Average Response Time</span>
                <span className="text-sm text-gray-900">234ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Uptime</span>
                <span className="text-sm text-gray-900">99.98%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Connections</span>
                <span className="text-sm text-gray-900">1,247</span>
              </div>
            </div>
            <div className="mt-6">
              <a
                href="/system"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View system details →
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
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <a
              href="/customers"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <UsersIcon className="h-6 w-6 text-blue-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Manage Customers</h4>
                <p className="text-sm text-gray-500">View and manage all customers</p>
              </div>
            </a>
            <a
              href="/analytics"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <TrendingUpIcon className="h-6 w-6 text-green-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">View Analytics</h4>
                <p className="text-sm text-gray-500">Platform usage and trends</p>
              </div>
            </a>
            <a
              href="/system"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">System Health</h4>
                <p className="text-sm text-gray-500">Monitor system performance</p>
              </div>
            </a>
            <a
              href="/settings"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <CurrencyDollarIcon className="h-6 w-6 text-purple-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Platform Settings</h4>
                <p className="text-sm text-gray-500">Configure platform options</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}