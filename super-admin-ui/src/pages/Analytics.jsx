import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  UsersIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { superAdminAPI } from '../services/api';

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('30d');

  // Fetch platform statistics
  const { data: stats, isLoading: statsLoading } = useQuery(
    'analyticsStats',
    () => superAdminAPI.getPlatformStats(),
    { 
      staleTime: 60000,
      onError: (error) => {
        console.error('Failed to fetch analytics stats:', error);
      }
    }
  );

  // Fetch recent activity for trend analysis
  const { data: activity } = useQuery(
    'analyticsActivity',
    () => superAdminAPI.getRecentActivity(50),
    { 
      staleTime: 30000,
      onError: (error) => {
        console.error('Failed to fetch activity:', error);
      }
    }
  );

  // Calculate growth metrics
  const calculateGrowthRate = (current, previous) => {
    if (!previous || previous === 0) return 0;
    return ((current - previous) / previous * 100).toFixed(1);
  };

  // Mock historical data for charts (in production, this would come from a time-series API)
  const mockChartData = {
    queries: [
      { date: '2025-01-01', value: 15000 },
      { date: '2025-01-05', value: 18000 },
      { date: '2025-01-10', value: 22000 },
      { date: '2025-01-15', value: 25000 },
      { date: '2025-01-20', value: 28000 },
    ],
    customers: [
      { date: '2025-01-01', value: 120 },
      { date: '2025-01-05', value: 125 },
      { date: '2025-01-10', value: 132 },
      { date: '2025-01-15', value: 140 },
      { date: '2025-01-20', value: 148 },
    ],
    revenue: [
      { date: '2025-01-01', value: 65000 },
      { date: '2025-01-05', value: 68000 },
      { date: '2025-01-10', value: 72000 },
      { date: '2025-01-15', value: 75000 },
      { date: '2025-01-20', value: 78000 },
    ],
  };

  const metricCards = [
    {
      title: 'Total Customers',
      value: stats?.totalCustomers || 0,
      icon: UsersIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      growth: '+12.5%',
      description: 'Active customer accounts'
    },
    {
      title: 'Monthly Revenue',
      value: `$${Math.round(stats?.monthlyRevenue || 0).toLocaleString()}`,
      icon: CurrencyDollarIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      growth: '+18.2%',
      description: 'Recurring monthly revenue'
    },
    {
      title: 'Total Queries',
      value: (stats?.totalQueries || 0).toLocaleString(),
      icon: ChatBubbleLeftRightIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      growth: '+24.8%',
      description: `${(stats?.monthlyQueries || 0).toLocaleString()} this month`
    },
    {
      title: 'Documents Processed',
      value: (stats?.totalDocuments || 0).toLocaleString(),
      icon: DocumentTextIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      growth: '+15.3%',
      description: 'Total documents in system'
    },
  ];

  // Calculate customer distribution by plan
  const planDistribution = {
    starter: 45,
    pro: 35,
    enterprise: 20
  };

  if (statsLoading) {
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
        <h1 className="text-3xl font-bold text-gray-900">Platform Analytics</h1>
        <p className="mt-2 text-gray-600">
          Comprehensive insights and metrics for the SmartAssist Solutions platform
        </p>
      </div>

      {/* Time Range Selector */}
      <div className="mb-6 flex justify-end">
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            onClick={() => setTimeRange('7d')}
            className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${
              timeRange === '7d' 
                ? 'bg-indigo-600 text-white border-indigo-600' 
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => setTimeRange('30d')}
            className={`px-4 py-2 text-sm font-medium border-t border-b ${
              timeRange === '30d' 
                ? 'bg-indigo-600 text-white border-indigo-600' 
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            30 Days
          </button>
          <button
            onClick={() => setTimeRange('90d')}
            className={`px-4 py-2 text-sm font-medium rounded-r-lg border ${
              timeRange === '90d' 
                ? 'bg-indigo-600 text-white border-indigo-600' 
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            90 Days
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metricCards.map((metric) => (
          <div key={metric.title} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`${metric.bgColor} rounded-lg p-3`}>
                <metric.icon className={`h-6 w-6 ${metric.color}`} />
              </div>
              <span className="text-sm font-medium text-green-600">{metric.growth}</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-1">{metric.value}</h3>
            <p className="text-sm font-medium text-gray-600 mb-1">{metric.title}</p>
            <p className="text-xs text-gray-500">{metric.description}</p>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Query Volume Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Query Volume Trend</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center">
              <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">Chart visualization would go here</p>
              <p className="text-xs text-gray-400 mt-1">Integration with charting library pending</p>
            </div>
          </div>
        </div>

        {/* Customer Growth Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Growth</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center">
              <ArrowTrendingUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">Growth chart would go here</p>
              <p className="text-xs text-gray-400 mt-1">Integration with charting library pending</p>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Plan Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Distribution</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Starter Plan</span>
                <span className="font-medium">{planDistribution.starter}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${planDistribution.starter}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Pro Plan</span>
                <span className="font-medium">{planDistribution.pro}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${planDistribution.pro}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Enterprise Plan</span>
                <span className="font-medium">{planDistribution.enterprise}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full" style={{ width: `${planDistribution.enterprise}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Top Performing Customers */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Active Customers</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">TechCorp Inc.</span>
              <span className="text-sm font-medium">12,847 queries</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">HealthTech Solutions</span>
              <span className="text-sm font-medium">8,623 queries</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">RetailMax</span>
              <span className="text-sm font-medium">6,451 queries</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">EduPlatform</span>
              <span className="text-sm font-medium">4,892 queries</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">FinanceHub</span>
              <span className="text-sm font-medium">3,127 queries</span>
            </div>
          </div>
        </div>

        {/* System Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Performance</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Avg Response Time</span>
              <span className="text-sm font-medium">234ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Success Rate</span>
              <span className="text-sm font-medium text-green-600">99.8%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Active Sessions</span>
              <span className="text-sm font-medium">1,247</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Calls/min</span>
              <span className="text-sm font-medium">892</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Error Rate</span>
              <span className="text-sm font-medium text-red-600">0.2%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}