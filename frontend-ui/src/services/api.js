import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/api/v1/auth/login', { email, password }),
  register: (userData) => api.post('/api/v1/auth/register', userData),
  logout: () => api.post('/api/v1/auth/logout'),
  verifyToken: (token) => api.get('/api/v1/auth/verify', {
    headers: { Authorization: `Bearer ${token}` }
  }),
};

// Config API
export const configAPI = {
  getConfig: () => api.get('/api/v1/config'),
};

// Documents API
export const documentsAPI = {
  getDocuments: () => api.get('/api/v1/documents'),
  uploadDocument: (formData, tenantId) => api.post(`/api/v1/documents/${tenantId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 2 minutes for file upload
  }),
  deleteDocument: (documentId) => api.delete(`/api/v1/documents/${documentId}`),
  getDocumentStatus: (documentId) => api.get(`/api/v1/documents/${documentId}/status`),
};

// Chat API
export const chatAPI = {
  sendMessage: (tenantId, message, sessionId = null) => api.post(`/api/v1/chat/${tenantId}/query`, {
    message,
    session_id: sessionId,
  }),
  getChatSessions: () => api.get('/api/v1/chat/sessions'),
  getChatSession: (sessionId) => api.get(`/api/v1/chat/sessions/${sessionId}`),
};

// Customer API
export const customerAPI = {
  getProfile: () => api.get('/api/v1/customer/profile'),
  updateProfile: (profileData) => api.put('/api/v1/customer/profile', profileData),
  getDashboard: () => api.get('/api/v1/customer/dashboard'),
};

// Widget API
export const widgetAPI = {
  getWidgetConfig: () => api.get('/api/v1/widgets/config'),
  updateWidgetConfig: (config) => api.put('/api/v1/widgets/config', config),
  getWidgetPreview: () => api.get('/api/v1/widgets/preview'),
};

// Utility functions
export const uploadWithProgress = (file, tenantId, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post(`/api/v1/documents/${tenantId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 2 minutes
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percentCompleted);
    },
  });
};

export default api;