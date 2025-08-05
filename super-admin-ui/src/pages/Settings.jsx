import React from 'react';
import {
  CogIcon,
  KeyIcon,
  BellIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

export default function Settings() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Platform Settings</h1>
        <p className="mt-2 text-gray-600">
          Configure platform-wide settings and preferences
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-8 text-center">
        <CogIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration Management</h3>
        <p className="text-gray-600 mb-4">
          Platform configuration, security settings, billing configuration, and system preferences.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-md mx-auto">
          <div className="text-center">
            <CogIcon className="h-8 w-8 text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">General</p>
          </div>
          <div className="text-center">
            <ShieldCheckIcon className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Security</p>
          </div>
          <div className="text-center">
            <BellIcon className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Notifications</p>
          </div>
          <div className="text-center">
            <KeyIcon className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">API Keys</p>
          </div>
        </div>
      </div>
    </div>
  );
}