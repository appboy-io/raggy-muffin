import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('super_admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('super_admin_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Super Admin API
export const superAdminAPI = {
  // Authentication
  login: async (credentials) => {
    const response = await api.post('/api/v1/super-admin/login', credentials);
    return response.data;
  },

  // Customer Management
  getAllCustomers: async () => {
    const response = await api.get('/api/v1/super-admin/customers');
    return response.data;
  },

  getCustomer: async (tenantId) => {
    const response = await api.get(`/api/v1/super-admin/customers/${tenantId}`);
    return response.data;
  },

  updateCustomer: async (tenantId, updates) => {
    const response = await api.put(`/api/v1/super-admin/customers/${tenantId}`, updates);
    return response.data;
  },

  suspendCustomer: async (tenantId) => {
    const response = await api.post(`/api/v1/super-admin/customers/${tenantId}/suspend`);
    return response.data;
  },

  reactivateCustomer: async (tenantId) => {
    const response = await api.post(`/api/v1/super-admin/customers/${tenantId}/reactivate`);
    return response.data;
  },

  // Platform Analytics
  getPlatformStats: async () => {
    const response = await api.get('/api/v1/super-admin/analytics/platform');
    return response.data;
  },

  getUsageStats: async (period = '30d') => {
    const response = await api.get(`/api/v1/super-admin/analytics/usage?period=${period}`);
    return response.data;
  },

  getRevenueStats: async (period = '30d') => {
    const response = await api.get(`/api/v1/super-admin/analytics/revenue?period=${period}`);
    return response.data;
  },

  // System Health
  getSystemHealth: async () => {
    const response = await api.get('/api/v1/super-admin/system/health');
    return response.data;
  },

  // Support & Billing
  getBillingData: async (tenantId) => {
    const response = await api.get(`/api/v1/super-admin/billing/${tenantId}`);
    return response.data;
  },

  createSupportTicket: async (tenantId, ticket) => {
    const response = await api.post(`/api/v1/super-admin/support/${tenantId}/tickets`, ticket);
    return response.data;
  },

  // Config Management
  getSystemConfig: async () => {
    const response = await api.get('/api/v1/super-admin/config');
    return response.data;
  },

  updateSystemConfig: async (config) => {
    const response = await api.put('/api/v1/super-admin/config', config);
    return response.data;
  },
};

export default api;