import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useConfig } from '../context/ConfigContext';
import {
  DocumentArrowUpIcon,
  ChatBubbleLeftRightIcon,
  CloudArrowUpIcon,
  LockClosedIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const { config } = useConfig();

  const features = [
    {
      name: 'Smart Document Processing',
      description: 'Upload PDFs, Word docs, and text files. Our AI extracts key information and makes it searchable.',
      icon: CloudArrowUpIcon,
    },
    {
      name: 'Intelligent Chat Interface',
      description: 'Ask questions about your documents in natural language and get accurate, contextual answers.',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      name: 'Secure & Private',
      description: 'Your documents are processed securely and remain private. We never use your data for training.',
      icon: LockClosedIcon,
    },
    {
      name: 'AI-Powered Search',
      description: 'Advanced semantic search finds relevant information even when exact keywords aren\'t used.',
      icon: SparklesIcon,
    },
  ];

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <div className="text-center">
        <div className="flex justify-center mb-8">
          <span className="text-8xl">{config.brand_logo}</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
          Welcome to{' '}
          <span className="text-gradient">{config.brand_name}</span>
        </h1>
        <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
          Transform your documents into intelligent conversations. Upload, ask questions, and get instant answers from your knowledge base.
        </p>
        <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
          {isAuthenticated ? (
            <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex">
              <Link
                to="/upload"
                className="btn-primary w-full sm:w-auto inline-flex items-center justify-center"
              >
                <DocumentArrowUpIcon className="h-5 w-5 mr-2" />
                Upload Document
              </Link>
              <Link
                to="/chat"
                className="btn-secondary w-full sm:w-auto inline-flex items-center justify-center"
              >
                <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
                Start Chatting
              </Link>
            </div>
          ) : (
            <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex">
              <Link
                to="/register"
                className="btn-primary w-full sm:w-auto inline-flex items-center justify-center"
              >
                Get Started Free
              </Link>
              <Link
                to="/login"
                className="btn-secondary w-full sm:w-auto inline-flex items-center justify-center"
              >
                Sign In
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="mt-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">
              Powerful Features
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Everything you need to make your documents intelligent and searchable
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <div key={feature.name} className="card animate-slide-up">
                <div className="card-body text-center">
                  <div className="flex justify-center">
                    <feature.icon className="h-12 w-12 text-primary-600" />
                  </div>
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    {feature.name}
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="mt-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">
              How It Works
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Get started in just three simple steps
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-primary-100 rounded-full p-3">
                  <DocumentArrowUpIcon className="h-8 w-8 text-primary-600" />
                </div>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                1. Upload Documents
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Upload your PDFs, Word documents, or text files. Our AI will process and analyze them automatically.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-primary-100 rounded-full p-3">
                  <SparklesIcon className="h-8 w-8 text-primary-600" />
                </div>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                2. AI Processing
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Our advanced AI extracts key information, creates embeddings, and makes your content searchable.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-primary-100 rounded-full p-3">
                  <ChatBubbleLeftRightIcon className="h-8 w-8 text-primary-600" />
                </div>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                3. Ask Questions
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Start asking questions about your documents. Get instant, accurate answers with source citations.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      {!isAuthenticated && (
        <div className="mt-16 bg-primary-50 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900">
            Ready to Get Started?
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            Join thousands of users who are already using AI to unlock insights from their documents.
          </p>
          <div className="mt-6">
            <Link
              to="/register"
              className="btn-primary inline-flex items-center justify-center text-lg px-8 py-3"
            >
              Create Free Account
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;