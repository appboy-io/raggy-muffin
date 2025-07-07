import React from 'react';
import {
  ChartBarIcon,
  TrendingUpIcon,
  UsersIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';

export default function Analytics() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Platform Analytics</h1>
        <p className="mt-2 text-gray-600">
          Detailed analytics and insights for the SmartAssist Solutions platform
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-8 text-center">
        <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Dashboard</h3>
        <p className="text-gray-600 mb-4">
          Advanced analytics including usage trends, revenue insights, and customer behavior will be displayed here.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-md mx-auto">
          <div className="text-center">
            <TrendingUpIcon className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Usage Trends</p>
          </div>
          <div className="text-center">
            <UsersIcon className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">User Growth</p>
          </div>
          <div className="text-center">
            <CurrencyDollarIcon className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Revenue</p>
          </div>
          <div className="text-center">
            <ChartBarIcon className="h-8 w-8 text-purple-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Performance</p>
          </div>
        </div>
      </div>
    </div>
  );
}