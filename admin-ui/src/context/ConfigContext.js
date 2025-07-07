import React, { createContext, useContext, useState, useEffect } from 'react';
import { configAPI } from '../services/api';

const ConfigContext = createContext();

export function useConfig() {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
}

export function ConfigProvider({ children }) {
  const [config, setConfig] = useState({
    brand_name: 'Loading...',
    brand_logo: '🏥',
    primary_color: '#2E8B57',
    secondary_color: '#4682B4',
    max_documents: 100,
    max_queries_per_day: 1000,
    max_file_size_mb: 50
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await configAPI.getConfig();
      setConfig(response);
    } catch (error) {
      console.error('Failed to fetch config:', error);
      // Keep default config on error
    } finally {
      setLoading(false);
    }
  };

  const value = {
    config,
    loading,
    refreshConfig: fetchConfig
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
}