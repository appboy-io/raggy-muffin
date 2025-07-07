import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  PencilIcon,
  NoSymbolIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

// Mock customer data
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

  const { data: customers, isLoading } = useQuery('customers', 
    () => Promise.resolve(mockCustomers),
    { staleTime: 30000 }
  );

  const filteredCustomers = customers?.filter(customer => {
    const matchesSearch = customer.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         customer.contactEmail.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && customer.isActive) ||
                         (filterStatus === 'inactive' && !customer.isActive) ||
                         (filterStatus === 'pending' && !customer.onboardingCompleted);
    return matchesSearch && matchesFilter;
  }) || [];

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
    if (!customer.onboardingCompleted) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Pending</span>;
    }
    if (!customer.isActive) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Suspended</span>;
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>;
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
                      {customer.companyName}
                    </div>
                    <div className="text-sm text-gray-500">
                      {customer.industry}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm text-gray-900">{customer.contactName}</div>
                    <div className="text-sm text-gray-500">{customer.contactEmail}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                    {customer.subscriptionPlan}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(customer)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div>{customer.documentsCount} docs</div>
                  <div className="text-xs text-gray-500">{customer.queriesThisMonth.toLocaleString()} queries</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(customer.createdAt)}
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
                    {customer.isActive ? (
                      <button
                        className="text-red-600 hover:text-red-900"
                        title="Suspend"
                      >
                        <NoSymbolIcon className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        className="text-green-600 hover:text-green-900"
                        title="Reactivate"
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
                    <p className="text-sm text-gray-900">{selectedCustomer.companyName}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Industry</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.industry}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Contact Name</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.contactName}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Contact Email</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.contactEmail}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Subscription Plan</label>
                    <p className="text-sm text-gray-900 capitalize">{selectedCustomer.subscriptionPlan}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
                    <p className="text-sm text-gray-900 font-mono">{selectedCustomer.tenantId}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Documents Uploaded</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.documentsCount}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Queries This Month</label>
                    <p className="text-sm text-gray-900">{selectedCustomer.queriesThisMonth.toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Account Created</label>
                    <p className="text-sm text-gray-900">{formatDate(selectedCustomer.createdAt)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Activity</label>
                    <p className="text-sm text-gray-900">{formatDate(selectedCustomer.lastActivity)}</p>
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