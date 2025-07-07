import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  const isAuthenticated = !!token && !!user;

  useEffect(() => {
    if (token) {
      // Verify token on app load
      verifyToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      // Verify token with backend API
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/auth/verify`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setUser(data.data);
        } else {
          logout();
        }
      } else {
        logout();
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const parseTokenPayload = (token) => {
    try {
      // Simple JWT parsing (in production, verify signature)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      
      if (payload.exp && payload.exp < now) {
        return null; // Token expired
      }
      
      return {
        userId: payload.user_id || payload.sub,
        tenantId: payload.tenant_id,
        username: payload.username,
        email: payload.email
      };
    } catch (error) {
      return null;
    }
  };

  const login = async (username, password) => {
    try {
      const response = await authAPI.signIn(username, password);
      
      if (response.success && response.data) {
        const { access_token, user_id, tenant_id, username: user } = response.data;
        
        setToken(access_token);
        localStorage.setItem('token', access_token);
        
        const userData = {
          userId: user_id,
          tenantId: tenant_id,
          username: user,
          email: username // Assuming username is email
        };
        
        setUser(userData);
        return { success: true };
      } else {
        return { success: false, message: response.message || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const signup = async (username, email, password) => {
    try {
      const response = await authAPI.signUp(username, email, password);
      return response;
    } catch (error) {
      console.error('Signup error:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Signup failed' 
      };
    }
  };

  const confirmSignup = async (username, code) => {
    try {
      const response = await authAPI.confirmSignUp(username, code);
      return response;
    } catch (error) {
      console.error('Confirm signup error:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Confirmation failed' 
      };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    signup,
    confirmSignup,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}