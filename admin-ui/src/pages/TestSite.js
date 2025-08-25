import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useConfig } from '../context/ConfigContext';
import {
  ComputerDesktopIcon,
  DevicePhoneMobileIcon,
  DeviceTabletIcon,
  ArrowLeftIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';

export default function TestSite() {
  const { user } = useAuth();
  const { config } = useConfig();
  const [deviceView, setDeviceView] = useState('desktop'); // desktop, tablet, mobile
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load the widget script dynamically
    if (user?.tenant_id) {
      const script = document.createElement('script');
      script.src = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/widgets/${user.tenant_id}/embed.js`;
      script.async = true;
      script.onload = () => {
        setIsLoading(false);
      };
      script.onerror = () => {
        setIsLoading(false);
        console.error('Failed to load widget script');
      };
      
      // Append to the test site container specifically
      const container = document.getElementById('test-site-container');
      if (container) {
        container.appendChild(script);
      }

      return () => {
        // Cleanup: remove the script and widget when component unmounts
        if (script.parentNode) {
          script.parentNode.removeChild(script);
        }
        // Remove any widget elements that were added
        const widgetElements = document.querySelectorAll('[id^="smartassist-widget"]');
        widgetElements.forEach(el => el.remove());
      };
    }
  }, [user?.tenant_id]);

  const getDeviceClasses = () => {
    switch(deviceView) {
      case 'mobile':
        return 'w-[375px] h-[667px]';
      case 'tablet':
        return 'w-[768px] h-[1024px]';
      default:
        return 'w-full h-full';
    }
  };

  const openInNewTab = () => {
    const previewUrl = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/widgets/${user?.tenant_id}/preview`;
    window.open(previewUrl, '_blank');
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              to="/widgets"
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeftIcon className="h-5 w-5 mr-2" />
              Back to Widget Settings
            </Link>
            <div className="border-l border-gray-300 h-6"></div>
            <h1 className="text-xl font-semibold text-gray-900">
              Widget Test Site
            </h1>
          </div>

          <div className="flex items-center space-x-4">
            {/* Device View Selector */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setDeviceView('desktop')}
                className={`p-2 rounded ${
                  deviceView === 'desktop'
                    ? 'bg-white shadow-sm text-primary'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Desktop View"
              >
                <ComputerDesktopIcon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setDeviceView('tablet')}
                className={`p-2 rounded ${
                  deviceView === 'tablet'
                    ? 'bg-white shadow-sm text-primary'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Tablet View"
              >
                <DeviceTabletIcon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setDeviceView('mobile')}
                className={`p-2 rounded ${
                  deviceView === 'mobile'
                    ? 'bg-white shadow-sm text-primary'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Mobile View"
              >
                <DevicePhoneMobileIcon className="h-5 w-5" />
              </button>
            </div>

            <button
              onClick={openInNewTab}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <ArrowTopRightOnSquareIcon className="h-4 w-4 mr-2" />
              Open in New Tab
            </button>
          </div>
        </div>

        {/* Info Banner */}
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Test Environment:</strong> This is a preview of how your chat widget will appear on a customer's website. 
            The widget is fully functional - try clicking on it to test the chat interface.
          </p>
        </div>
      </div>

      {/* Preview Container */}
      <div className="flex-1 bg-gray-100 p-6 overflow-auto">
        <div className="flex justify-center">
          <div 
            className={`bg-white shadow-xl transition-all duration-300 ${
              deviceView === 'mobile' ? 'rounded-[2rem] border-8 border-gray-800' : 
              deviceView === 'tablet' ? 'rounded-xl border-8 border-gray-800' : 
              'rounded-lg'
            } ${getDeviceClasses()} overflow-hidden`}
          >
            {/* Sample Website Content */}
            <div id="test-site-container" className="h-full overflow-auto bg-white">
              {/* Sample Header */}
              <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6">
                <div className="max-w-6xl mx-auto">
                  <h1 className="text-3xl font-bold mb-2">Sample Business Website</h1>
                  <p className="text-blue-100">Testing {config.brand_name} Chat Widget Integration</p>
                </div>
              </header>

              {/* Sample Navigation */}
              <nav className="bg-white shadow-sm border-b">
                <div className="max-w-6xl mx-auto px-6 py-4">
                  <div className="flex space-x-8">
                    <a href="#" className="text-gray-700 hover:text-blue-600 font-medium">Home</a>
                    <a href="#" className="text-gray-700 hover:text-blue-600 font-medium">About</a>
                    <a href="#" className="text-gray-700 hover:text-blue-600 font-medium">Services</a>
                    <a href="#" className="text-gray-700 hover:text-blue-600 font-medium">Contact</a>
                  </div>
                </div>
              </nav>

              {/* Sample Content */}
              <main className="max-w-6xl mx-auto px-6 py-12">
                <section className="mb-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Our Services</h2>
                  <p className="text-gray-600 mb-4">
                    This is a sample website demonstrating how the chat widget appears to your visitors. 
                    The widget should appear in the bottom-right corner of this preview.
                  </p>
                  <p className="text-gray-600 mb-4">
                    Your customers can click on the widget to start a conversation and get instant help 
                    with their questions about your services.
                  </p>
                </section>

                <section className="grid md:grid-cols-3 gap-6 mb-12">
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Feature One</h3>
                    <p className="text-gray-600">
                      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt.
                    </p>
                  </div>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Feature Two</h3>
                    <p className="text-gray-600">
                      Ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.
                    </p>
                  </div>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Feature Three</h3>
                    <p className="text-gray-600">
                      Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat.
                    </p>
                  </div>
                </section>

                <section className="bg-blue-50 p-8 rounded-lg">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Need Help?</h2>
                  <p className="text-gray-700 mb-4">
                    Try our chat assistant! Look for the chat widget in the bottom-right corner of this page. 
                    Our AI-powered assistant can help answer your questions instantly.
                  </p>
                  <div className="flex items-center space-x-2 text-sm text-blue-700">
                    <span className="inline-block w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                    <span>Widget Status: {isLoading ? 'Loading...' : 'Active'}</span>
                  </div>
                </section>
              </main>

              {/* Sample Footer */}
              <footer className="bg-gray-800 text-white p-6 mt-12">
                <div className="max-w-6xl mx-auto text-center">
                  <p className="text-gray-400">© 2024 Sample Business. All rights reserved.</p>
                  <p className="text-gray-500 text-sm mt-2">
                    This is a test environment for {config.brand_name} chat widget
                  </p>
                </div>
              </footer>
            </div>
          </div>
        </div>

        {/* Device Frame Labels */}
        {deviceView !== 'desktop' && (
          <div className="text-center mt-4">
            <p className="text-sm text-gray-600">
              {deviceView === 'mobile' ? 'Mobile View (375x667)' : 'Tablet View (768x1024)'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}