import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import SetupWizard from './components/SetupWizard';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Analytics from './pages/Analytics';
import SystemHealth from './pages/SystemHealth';
import Settings from './pages/Settings';
import { superAdminAPI } from './services/api';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('super_admin_token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  const [setupRequired, setSetupRequired] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      const response = await superAdminAPI.checkSetupStatus();
      setSetupRequired(response.setup_required);
    } catch (error) {
      console.error('Error checking setup status:', error);
      // If we can't check, assume setup is needed
      setSetupRequired(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetupComplete = () => {
    // Reload the app after setup is complete
    window.location.href = '/superadmin/';
  };

  // Show loading screen while checking setup status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show setup wizard if setup is required
  if (setupRequired) {
    return (
      <QueryClientProvider client={queryClient}>
        <SetupWizard onComplete={handleSetupComplete} />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </QueryClientProvider>
    );
  }

  // Normal app flow
  return (
    <QueryClientProvider client={queryClient}>
      <Router basename="/superadmin">
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/customers" element={
              <ProtectedRoute>
                <Layout>
                  <Customers />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/analytics" element={
              <ProtectedRoute>
                <Layout>
                  <Analytics />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/system" element={
              <ProtectedRoute>
                <Layout>
                  <SystemHealth />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Layout>
                  <Settings />
                </Layout>
              </ProtectedRoute>
            } />
          </Routes>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;