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
  const token = localStorage.getItem('token');
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
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signIn: async (username, password) => {
    const response = await api.post('/api/v1/auth/signin', {
      username,
      password,
    });
    return response.data;
  },

  signUp: async (username, email, password) => {
    const response = await api.post('/api/v1/auth/signup', {
      username,
      email,
      password,
    });
    return response.data;
  },

  confirmSignUp: async (username, confirmation_code) => {
    const response = await api.post('/api/v1/auth/confirm-signup', {
      username,
      confirmation_code,
    });
    return response.data;
  },

  changePassword: async (passwordData) => {
    const response = await api.post('/api/v1/auth/change-password', passwordData);
    return response.data;
  },

  deleteAccount: async () => {
    const response = await api.delete('/api/v1/auth/account');
    return response.data;
  },
};

// Config API
export const configAPI = {
  getConfig: async () => {
    const response = await api.get('/api/v1/config');
    return response.data;
  },
};

// Documents API
export const documentsAPI = {
  getDocuments: async () => {
    const response = await api.get('/api/v1/documents/');
    return response.data;
  },

  uploadDocument: async (file, extractStructured = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('extract_structured', extractStructured);

    const response = await api.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteDocument: async (documentId) => {
    const response = await api.delete(`/api/v1/documents/${documentId}`);
    return response.data;
  },

  getDocument: async (documentId) => {
    const response = await api.get(`/api/v1/documents/${documentId}`);
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (message, sessionId = null) => {
    const response = await api.post('/api/v1/chat/query', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },

  getChatSessions: async () => {
    const response = await api.get('/api/v1/chat/sessions');
    return response.data;
  },

  getChatSession: async (sessionId) => {
    const response = await api.get(`/api/v1/chat/sessions/${sessionId}`);
    return response.data;
  },
};

// Widgets API
export const widgetsAPI = {
  getWidgetConfig: async () => {
    const response = await api.get('/api/v1/widgets/config');
    return response.data;
  },

  updateWidgetConfig: async (config) => {
    const response = await api.put('/api/v1/widgets/config', config);
    return response.data;
  },
};

// Customer API
export const customerAPI = {
  getProfile: async () => {
    const response = await api.get('/api/v1/customer/profile');
    return response.data;
  },

  updateProfile: async (profile) => {
    const response = await api.put('/api/v1/customer/profile', profile);
    return response.data;
  },

  getDashboard: async () => {
    const response = await api.get('/api/v1/customer/dashboard');
    return response.data;
  },
};

export default api;