import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useAuth } from '../context/AuthContext';
import { useConfig } from '../context/ConfigContext';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
  UserIcon,
  KeyIcon,
  CogIcon,
  TrashIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export default function Settings() {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showDeleteAccount, setShowDeleteAccount] = useState(false);
  const [passwords, setPasswords] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  
  const { user, logout } = useAuth();
  const { config } = useConfig();
  const queryClient = useQueryClient();

  const changePasswordMutation = useMutation(
    (passwordData) => authAPI.changePassword(passwordData),
    {
      onSuccess: () => {
        toast.success('Password changed successfully!');
        setShowPasswordForm(false);
        setPasswords({
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        });
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to change password');
      },
    }
  );

  const deleteAccountMutation = useMutation(
    () => authAPI.deleteAccount(),
    {
      onSuccess: () => {
        toast.success('Account deleted successfully');
        logout();
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to delete account');
      },
    }
  );

  const handlePasswordChange = (e) => {
    e.preventDefault();
    if (passwords.newPassword !== passwords.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (passwords.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }
    
    changePasswordMutation.mutate({
      current_password: passwords.currentPassword,
      new_password: passwords.newPassword,
    });
  };

  const handleDeleteAccount = () => {
    if (deleteConfirmation !== 'DELETE') {
      toast.error('Please type DELETE to confirm');
      return;
    }
    deleteAccountMutation.mutate();
  };

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswords(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage your account settings and preferences.
        </p>
      </div>

      {/* Account Information */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center">
            <UserIcon className="h-5 w-5 mr-2" />
            Account Information
          </h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Username</label>
            <div className="mt-1 text-sm text-gray-900">{user?.username}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <div className="mt-1 text-sm text-gray-900">{user?.email}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
            <div className="mt-1 text-sm text-gray-900 font-mono">{user?.tenantId}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Account Created</label>
            <div className="mt-1 text-sm text-gray-900">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Password Management */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center">
            <KeyIcon className="h-5 w-5 mr-2" />
            Password & Security
          </h2>
        </div>
        <div className="px-6 py-4">
          {!showPasswordForm ? (
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Keep your account secure with a strong password.
              </p>
              <button
                onClick={() => setShowPasswordForm(true)}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700"
              >
                Change Password
              </button>
            </div>
          ) : (
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  name="currentPassword"
                  value={passwords.currentPassword}
                  onChange={handlePasswordInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  name="newPassword"
                  value={passwords.newPassword}
                  onChange={handlePasswordInputChange}
                  required
                  minLength="8"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={passwords.confirmPassword}
                  onChange={handlePasswordInputChange}
                  required
                  minLength="8"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="submit"
                  disabled={changePasswordMutation.isLoading}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  {changePasswordMutation.isLoading ? 'Changing...' : 'Change Password'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordForm(false);
                    setPasswords({
                      currentPassword: '',
                      newPassword: '',
                      confirmPassword: '',
                    });
                  }}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Application Settings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center">
            <CogIcon className="h-5 w-5 mr-2" />
            Application Settings
          </h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Brand Name</label>
            <div className="mt-1 text-sm text-gray-900">{config.brand_name}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Primary Color</label>
            <div className="mt-1 flex items-center space-x-2">
              <div 
                className="w-6 h-6 rounded border"
                style={{ backgroundColor: config.primary_color }}
              ></div>
              <span className="text-sm text-gray-900">{config.primary_color}</span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Document Limit</label>
            <div className="mt-1 text-sm text-gray-900">{config.max_documents} documents</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Max File Size</label>
            <div className="mt-1 text-sm text-gray-900">{config.max_file_size_mb}MB</div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white shadow rounded-lg border border-red-200">
        <div className="px-6 py-4 border-b border-red-200">
          <h2 className="text-lg font-medium text-red-900 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            Danger Zone
          </h2>
        </div>
        <div className="px-6 py-4">
          {!showDeleteAccount ? (
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Once you delete your account, there is no going back. This will permanently delete your account and all associated data.
              </p>
              <button
                onClick={() => setShowDeleteAccount(true)}
                className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 flex items-center"
              >
                <TrashIcon className="h-4 w-4 mr-2" />
                Delete Account
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <h3 className="text-sm font-medium text-red-800">
                  This action cannot be undone
                </h3>
                <p className="text-sm text-red-700 mt-1">
                  This will permanently delete your account, all documents, chat sessions, and widget configurations.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type <span className="font-mono font-bold">DELETE</span> to confirm
                </label>
                <input
                  type="text"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="DELETE"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleteAccountMutation.isLoading || deleteConfirmation !== 'DELETE'}
                  className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  {deleteAccountMutation.isLoading ? 'Deleting...' : 'Delete Account'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteAccount(false);
                    setDeleteConfirmation('');
                  }}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}