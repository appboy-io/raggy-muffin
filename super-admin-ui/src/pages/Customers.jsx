import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  PencilIcon,
  NoSymbolIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { superAdminAPI } from '../services/api';
import toast from 'react-hot-toast';

// Mock customer data (fallback for development)
const mockCustomers = [
  {
    id: '1',
    tenantId: '5418e478-60a1-70d7-7390-9c163fc0828b',
    companyName: 'Test Company Updated',
    contactEmail: 'brileydeveloper@gmail.com',
    contactName: 'John Doe',
    industry: 'Technology',
    subscriptionPlan: 'starter',
    isActive: true,
    onboardingCompleted: true,
    createdAt: '2025-01-15T10:30:00Z',
    documentsCount: 15,
    queriesThisMonth: 2847,
    lastActivity: '2025-01-20T14:22:00Z',
  },
  {
    id: '2',
    tenantId: 'customer-tenant-456',
    companyName: 'HealthTech Solutions',
    contactEmail: 'admin@healthtech.com',
    contactName: 'Sarah Chen',
    industry: 'Healthcare',
    subscriptionPlan: 'pro',
    isActive: true,
    onboardingCompleted: true,
    createdAt: '2025-01-10T08:15:00Z',
    documentsCount: 42,
    queriesThisMonth: 5623,
    lastActivity: '2025-01-20T16:45:00Z',
  },
  {
    id: '3',
    tenantId: 'customer-tenant-789',
    companyName: 'RetailMax Inc',
    contactEmail: 'support@retailmax.com',
    contactName: 'Marcus Rodriguez',
    industry: 'Retail',
    subscriptionPlan: 'enterprise',
    isActive: false,
    onboardingCompleted: true,
    createdAt: '2024-12-20T12:00:00Z',
    documentsCount: 128,
    queriesThisMonth: 0,
    lastActivity: '2025-01-18T09:30:00Z',
  },
  {
    id: '4',
    tenantId: 'customer-tenant-012',
    companyName: 'EduPlatform',
    contactEmail: 'admin@eduplatform.edu',
    contactName: 'Dr. Lisa Wang',
    industry: 'Education',
    subscriptionPlan: 'starter',
    isActive: true,
    onboardingCompleted: false,
    createdAt: '2025-01-19T16:20:00Z',
    documentsCount: 3,
    queriesThisMonth: 45,
    lastActivity: '2025-01-20T11:15:00Z',
  },
];

export default function Customers() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  // Fetch customers from API
  const { data: apiResponse, isLoading, error } = useQuery(
    ['customers', page, searchTerm, filterStatus],
    () => {
      const params = {
        page,
        limit: 20
      };
      
      // Only add search if it has a value
      if (searchTerm && searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      
      // Only add status if it's not 'all'
      if (filterStatus && filterStatus !== 'all') {
        params.status = filterStatus;
      }
      
      return superAdminAPI.getAllCustomers(params);
    },
    { 
      staleTime: 30000,
      keepPreviousData: true,
      onError: (error) => {
        console.error('Failed to fetch customers:', error);
        // Note: onError doesn't return data, fallback logic is handled below
      }
    }
  );

  // Use API data if available, otherwise use mock data
  const customers = apiResponse?.customers || mockCustomers;
  const totalCustomers = apiResponse?.total || mockCustomers.length;

  // Suspend customer mutation
  const suspendMutation = useMutation(
    (tenantId) => superAdminAPI.suspendCustomer(tenantId),
    {
      onSuccess: () => {
        toast.success('Customer suspended successfully');
        queryClient.invalidateQueries('customers');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to suspend customer');
      }
    }
  );

  // Activate customer mutation
  const activateMutation = useMutation(
    (tenantId) => superAdminAPI.activateCustomer(tenantId),
    {
      onSuccess: () => {
        toast.success('Customer activated successfully');
        queryClient.invalidateQueries('customers');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to activate customer');
      }
    }
  );

  // Client-side filtering is handled by API now, so we just use the results directly
  const filteredCustomers = customers || [];

  const handleViewCustomer = (customer) => {
    setSelectedCustomer(customer);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (customer) => {
    if (!customer.onboarding_completed) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Pending</span>;
    }
    if (!customer.is_active) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Suspended</span>;
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>;
  };

  const handleSuspend = async (customer) => {
    if (window.confirm(`Are you sure you want to suspend ${customer.company_name}?`)) {
      suspendMutation.mutate(customer.tenant_id);
    }
  };

  const handleActivate = async (customer) => {
    if (window.confirm(`Are you sure you want to activate ${customer.company_name}?`)) {
      activateMutation.mutate(customer.tenant_id);
    }
  };

  if (isLoading) {
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
        <h1 className="text-3xl font-bold text-gray-900">Customer Management</h1>
        <p className="mt-2 text-gray-600">
          Manage all customer accounts and subscriptions
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search customers..."
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <div className="flex items-center">
          <FunnelIcon className="h-5 w-5 text-gray-400 mr-2" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="all">All Customers</option>
            <option value="active">Active</option>
            <option value="inactive">Suspended</option>
            <option value="pending">Pending Onboarding</option>
          </select>
        </div>
      </div>

      {/* Customer Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Plan
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Usage
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Joined
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredCustomers.map((customer) => (
              <tr key={customer.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {customer.company_name || customer.companyName}
                    </div>
                    <div className="text-sm text-gray-500">
                      {customer.industry || 'Not specified'}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm text-gray-900">{customer.contact_name || customer.contactName || 'N/A'}</div>
                    <div className="text-sm text-gray-500">{customer.contact_email || customer.contactEmail}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                    {customer.subscription_plan || customer.subscriptionPlan || 'starter'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(customer)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div>{customer.documents_count || customer.documentsCount || 0} docs</div>
                  <div className="text-xs text-gray-500">{(customer.queries_this_month || customer.queriesThisMonth || 0).toLocaleString()} queries</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(customer.created_at || customer.createdAt)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => handleViewCustomer(customer)}
                      className="text-indigo-600 hover:text-indigo-900"
                      title="View Details"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                      className="text-gray-600 hover:text-gray-900"
                      title="Edit"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    {(customer.is_active ?? customer.isActive) ? (
                      <button
                        onClick={() => handleSuspend(customer)}
                        className="text-red-600 hover:text-red-900"
                        title="Suspend"
                        disabled={suspendMutation.isLoading}
                      >
                        <NoSymbolIcon className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleActivate(customer)}
                        className="text-green-600 hover:text-green-900"
                        title="Activate"
                        disabled={activateMutation.isLoading}
                      >
                        <CheckCircleIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Customer Details</h3>
                <button
                  onClick={() => setSelectedCustomer(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Company Name</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.company_name || selectedCustomer.companyName}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Industry</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.industry || 'Not specified'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Contact Name</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.contact_name || selectedCustomer.contactName || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Contact Email</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.contact_email || selectedCustomer.contactEmail}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Subscription Plan</label>
                    <p className="text-sm text-gray-900 capitalize">{selectedCustomer.subscription_plan || selectedCustomer.subscriptionPlan || 'starter'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
                    <p className="text-sm text-gray-900 font-mono">{selectedCustomer.tenant_id || selectedCustomer.tenantId}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Documents Uploaded</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.documents_count || selectedCustomer.documentsCount || 0}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Queries This Month</label>
                    <p className="text-sm text-gray-900">{(selectedCustomer.queries_this_month || selectedCustomer.queriesThisMonth || 0).toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Account Created</label>
                    <p className="text-sm text-gray-900">{formatDate(selectedCustomer.created_at || selectedCustomer.createdAt)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Activity</label>
                    <p className="text-sm text-gray-900">{formatDate(selectedCustomer.last_activity || selectedCustomer.lastActivity || selectedCustomer.created_at || selectedCustomer.createdAt)}</p>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    onClick={() => setSelectedCustomer(null)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Close
                  </button>
                  <button className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
                    Edit Customer
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}