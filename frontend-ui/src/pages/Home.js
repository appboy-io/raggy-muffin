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
  CodeBracketIcon,
  ChartBarIcon,
  GlobeAltIcon,
  UserGroupIcon,
  AcademicCapIcon,
  ShoppingCartIcon,
  PaintBrushIcon,
  BoltIcon,
  ShieldCheckIcon,
  CubeTransparentIcon,
} from '@heroicons/react/24/outline';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const { config } = useConfig();

  const features = [
    {
      name: 'Instant Widget Embedding',
      description: 'Add your AI chat agent to any website with a simple script tag. Works everywhere.',
      icon: CodeBracketIcon,
    },
    {
      name: 'Multi-Tenant Architecture',
      description: 'Create separate AI agents for different clients, brands, or use cases from one account.',
      icon: CubeTransparentIcon,
    },
    {
      name: 'Custom Branding',
      description: 'White-label your chat agents with custom colors, logos, and personality.',
      icon: PaintBrushIcon,
    },
    {
      name: 'Real-Time Streaming',
      description: 'Fast, responsive chat with streaming responses for better user experience.',
      icon: BoltIcon,
    },
    {
      name: 'Analytics & Insights',
      description: 'Track usage, popular questions, and optimize your AI agent performance.',
      icon: ChartBarIcon,
    },
    {
      name: 'Enterprise Security',
      description: 'SOC 2 compliant with data encryption, secure processing, and privacy controls.',
      icon: ShieldCheckIcon,
    },
  ];

  const useCases = [
    {
      title: 'Customer Support',
      description: 'Deploy AI agents that answer customer questions 24/7 using your knowledge base.',
      icon: UserGroupIcon,
      examples: ['FAQ bots', 'Product support', 'Troubleshooting guides'],
    },
    {
      title: 'Education & Training',
      description: 'Create intelligent tutors and training assistants from your course materials.',
      icon: AcademicCapIcon,
      examples: ['Course assistants', 'Onboarding bots', 'Study guides'],
    },
    {
      title: 'Sales & Marketing',
      description: 'Build product advisors and sales assistants that know your offerings inside out.',
      icon: ShoppingCartIcon,
      examples: ['Product recommendations', 'Lead qualification', 'Sales enablement'],
    },
    {
      title: 'Knowledge Management',
      description: 'Transform company wikis and documentation into interactive AI assistants.',
      icon: GlobeAltIcon,
      examples: ['Internal wikis', 'Policy guides', 'Process documentation'],
    },
  ];

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <div className="text-center">
        <div className="flex justify-center mb-8">
          {config.brand_logo_url ? (
            <img 
              src={config.brand_logo_url} 
              alt={config.brand_name}
              className="h-24 w-auto"
            />
          ) : (
            <span className="text-8xl">{config.brand_logo}</span>
          )}
        </div>
        <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
          Build AI Chat Agents from
          <span className="text-gradient block mt-2">Your Knowledge Base</span>
        </h1>
        <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
          Create, customize, and embed intelligent chat assistants trained on your data. No coding required.
        </p>
        <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
          {isAuthenticated ? (
            <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex">
              <Link
                to="/upload"
                className="btn-primary w-full sm:w-auto inline-flex items-center justify-center"
              >
                <SparklesIcon className="h-5 w-5 mr-2" />
                Build Your Agent
              </Link>
              <Link
                to="/chat"
                className="btn-secondary w-full sm:w-auto inline-flex items-center justify-center"
              >
                <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
                Test Your Agent
              </Link>
            </div>
          ) : (
            <div className="flex justify-center">
              <Link
                to="/register"
                className="btn-primary inline-flex items-center justify-center text-lg px-8 py-3"
              >
                Start Building Free
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Value Props Section */}
      <div className="mt-20 bg-gray-50 py-16 -mx-8 px-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="bg-primary-100 rounded-full p-4">
                  <CloudArrowUpIcon className="h-10 w-10 text-primary-600" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Train on Your Data</h3>
              <p className="mt-2 text-gray-600">
                Upload documents, websites, FAQs, and any text content. Your AI learns from your unique knowledge.
              </p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="bg-primary-100 rounded-full p-4">
                  <PaintBrushIcon className="h-10 w-10 text-primary-600" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Customize & Brand</h3>
              <p className="mt-2 text-gray-600">
                Match your brand colors, set the personality, and control how your AI responds to users.
              </p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="bg-primary-100 rounded-full p-4">
                  <CodeBracketIcon className="h-10 w-10 text-primary-600" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Embed Anywhere</h3>
              <p className="mt-2 text-gray-600">
                Add to your website with one line of code. Share via link or integrate with your apps.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Use Cases Section */}
      <div className="mt-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">
              Build AI Agents for Any Use Case
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              From customer support to internal knowledge bases, create AI that serves your specific needs
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
            {useCases.map((useCase) => (
              <div key={useCase.title} className="card hover:shadow-lg transition-shadow">
                <div className="card-body">
                  <div className="flex justify-center mb-4">
                    <useCase.icon className="h-12 w-12 text-primary-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                    {useCase.title}
                  </h3>
                  <p className="text-sm text-gray-600 text-center mb-4">
                    {useCase.description}
                  </p>
                  <div className="border-t pt-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Examples:</p>
                    <ul className="space-y-1">
                      {useCase.examples.map((example, idx) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start">
                          <span className="text-primary-500 mr-2">•</span>
                          {example}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="mt-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">
              Everything You Need to Succeed
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Professional features to build, deploy, and scale your AI agents
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.name} className="card animate-slide-up hover:shadow-md transition-shadow">
                <div className="card-body flex flex-row items-start">
                  <div className="flex-shrink-0">
                    <feature.icon className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      {feature.name}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="mt-20 bg-gradient-to-r from-primary-50 to-primary-100 py-16 -mx-8 px-8">
        <div className="max-w-5xl mx-auto">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">
              Launch Your AI Agent in Minutes
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              No technical expertise required. Just three simple steps.
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-white rounded-full p-4 shadow-md">
                  <DocumentArrowUpIcon className="h-10 w-10 text-primary-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-4xl font-bold text-primary-600 mb-2">1</div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Upload Your Knowledge
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  Add documents, FAQs, websites, or any content that contains your expertise.
                </p>
              </div>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-white rounded-full p-4 shadow-md">
                  <PaintBrushIcon className="h-10 w-10 text-primary-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-4xl font-bold text-primary-600 mb-2">2</div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Customize Your Agent
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  Set the personality, appearance, and behavior to match your brand.
                </p>
              </div>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-white rounded-full p-4 shadow-md">
                  <GlobeAltIcon className="h-10 w-10 text-primary-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-4xl font-bold text-primary-600 mb-2">3</div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Embed & Share
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  Add to your website with one line of code or share via a custom link.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      {!isAuthenticated && (
        <div className="mt-20 bg-gray-900 rounded-2xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold">
            Ready to Build Your First AI Agent?
          </h2>
          <p className="mt-4 text-lg text-gray-300 max-w-2xl mx-auto">
            Join thousands of businesses using {config.brand_name} to create intelligent chat experiences for their customers.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              to="/register"
              className="btn-primary bg-white text-gray-900 hover:bg-gray-100 inline-flex items-center justify-center text-lg px-8 py-3"
            >
              <SparklesIcon className="h-5 w-5 mr-2" />
              Start Building Free
            </Link>
          </div>
          <p className="mt-6 text-sm text-gray-400">
            No credit card required • Free plan available • Setup in minutes
          </p>
        </div>
      )}
    </div>
  );
};

export default Home;