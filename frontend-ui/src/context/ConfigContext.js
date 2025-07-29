import React, { createContext, useContext, useState, useEffect } from 'react';
import { configAPI } from '../services/api';

const ConfigContext = createContext();

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

export const ConfigProvider = ({ children }) => {
  const [config, setConfig] = useState({
    brand_name: process.env.REACT_APP_BRAND_NAME || 'AI Assistant',
    brand_logo: process.env.REACT_APP_BRAND_LOGO || '🤖',
    primary_color: process.env.REACT_APP_PRIMARY_COLOR || '#3b82f6',
    secondary_color: process.env.REACT_APP_SECONDARY_COLOR || '#6b7280',
    widget_domain: process.env.REACT_APP_WIDGET_DOMAIN || 'http://localhost:3000',
    api_base_url: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        // Try to load config from API
        const response = await configAPI.getConfig();
        setConfig(prevConfig => ({
          ...prevConfig,
          ...response.data,
        }));
      } catch (err) {
        console.warn('Failed to load config from API, using defaults:', err);
        setError('Failed to load configuration');
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, []);

  // Apply theme colors to CSS variables
  useEffect(() => {
    if (config.primary_color) {
      document.documentElement.style.setProperty('--primary-color', config.primary_color);
    }
    if (config.secondary_color) {
      document.documentElement.style.setProperty('--secondary-color', config.secondary_color);
    }
  }, [config.primary_color, config.secondary_color]);

  const value = {
    config,
    loading,
    error,
    updateConfig: setConfig,
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
};