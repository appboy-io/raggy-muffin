import React from 'react';
import {
  CpuChipIcon,
  ServerIcon,
  CloudIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export default function SystemHealth() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
        <p className="mt-2 text-gray-600">
          Monitor platform performance, uptime, and system resources
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-8 text-center">
        <CpuChipIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">System Monitoring</h3>
        <p className="text-gray-600 mb-4">
          Real-time system health metrics, performance monitoring, and alert management.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-md mx-auto">
          <div className="text-center">
            <ServerIcon className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">API Health</p>
          </div>
          <div className="text-center">
            <CloudIcon className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Database</p>
          </div>
          <div className="text-center">
            <CpuChipIcon className="h-8 w-8 text-purple-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Performance</p>
          </div>
          <div className="text-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Alerts</p>
          </div>
        </div>
      </div>
    </div>
  );
}