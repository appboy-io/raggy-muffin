import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

// Helper function to format Cognito error messages into user-friendly text
const formatCognitoError = (errorMessage) => {
  if (!errorMessage) return null;
  
  const message = errorMessage.toLowerCase();
  
  if (message.includes('incorrect username or password')) {
    return 'Invalid email or password. Please check your credentials and try again.';
  }
  if (message.includes('user not confirmed')) {
    return 'Please check your email and confirm your account before signing in.';
  }
  if (message.includes('user does not exist')) {
    return 'No account found with this email address.';
  }
  if (message.includes('invalid verification code')) {
    return 'Invalid confirmation code. Please check your email and try again.';
  }
  if (message.includes('code has expired')) {
    return 'Confirmation code has expired. Please request a new one.';
  }
  if (message.includes('user already exists')) {
    return 'An account with this email already exists. Please try logging in instead.';
  }
  if (message.includes('password does not conform')) {
    return 'Password must be at least 8 characters with uppercase, lowercase, and numbers.';
  }
  if (message.includes('limit exceeded')) {
    return 'Too many attempts. Please try again later.';
  }
  
  // Return original message if no specific formatting applies
  return errorMessage;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // Verify token with API
          const response = await authAPI.verifyToken(token);
          
          // Handle Cognito verify response format
          if (response.data.success && response.data.data) {
            const userData = {
              email: response.data.data.email || 'user@example.com',
              tenant_id: response.data.data.tenant_id || 'default'
            };
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            localStorage.removeItem('auth_token');
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('auth_token');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      
      // Handle Cognito response format: { success: boolean, message: string, data: {...} }
      if (response.data.success && response.data.data) {
        const token = response.data.data.access_token;
        const userData = {
          email: email,
          tenant_id: response.data.data.tenant_id || email
        };
        
        localStorage.setItem('auth_token', token);
        setUser(userData);
        setIsAuthenticated(true);
        
        return { success: true, user: userData };
      } else {
        return { 
          success: false, 
          error: formatCognitoError(response.data.message) || 'Login failed' 
        };
      }
    } catch (error) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message;
      return { 
        success: false, 
        error: formatCognitoError(errorMessage) || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      
      // Handle Cognito response format - registration doesn't provide token until confirmed
      if (response.data.success) {
        return { 
          success: true, 
          requiresConfirmation: true,
          email: userData.email,
          message: response.data.message || 'Registration successful. Please check your email for verification code.'
        };
      } else {
        return { 
          success: false, 
          error: formatCognitoError(response.data.message) || 'Registration failed' 
        };
      }
    } catch (error) {
      console.error('Registration failed:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message;
      return { 
        success: false, 
        error: formatCognitoError(errorMessage) || 'Registration failed' 
      };
    }
  };

  const confirmSignup = async (email, confirmationCode) => {
    try {
      const response = await authAPI.confirmSignup(email, confirmationCode);
      
      if (response.data.success) {
        return { success: true, message: 'Email confirmed successfully. You can now login.' };
      } else {
        return { 
          success: false, 
          error: formatCognitoError(response.data.message) || 'Confirmation failed' 
        };
      }
    } catch (error) {
      console.error('Confirmation failed:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message;
      return { 
        success: false, 
        error: formatCognitoError(errorMessage) || 'Confirmation failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('auth_token');
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    confirmSignup,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};