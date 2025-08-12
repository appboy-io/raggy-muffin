import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useConfig } from '../context/ConfigContext';
import { customerAPI } from '../services/api';
import {
  BuildingOfficeIcon,
  GlobeAltIcon,
  EnvelopeIcon,
  UserIcon,
  BriefcaseIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export default function Profile() {
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    company_name: '',
    company_website: '',
    contact_email: '',
    contact_name: '',
    industry: '',
    allowed_domains: [],
  });
  
  const [errors, setErrors] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [newDomain, setNewDomain] = useState('');

  // Fetch current profile
  const { data: profile, isLoading, error } = useQuery('customerProfile', customerAPI.getProfile);

  // Update profile mutation
  const updateProfileMutation = useMutation(customerAPI.updateProfile, {
    onSuccess: (data) => {
      queryClient.invalidateQueries('customerProfile');
      queryClient.invalidateQueries('dashboard');
      setIsEditing(false);
      setErrors({});
    },
    onError: (error) => {
      setErrors({ submit: error.response?.data?.detail || 'Failed to update profile' });
    },
  });

  // Initialize form data when profile loads
  useEffect(() => {
    if (profile) {
      setFormData({
        company_name: profile.company_name || '',
        company_website: profile.company_website || '',
        contact_email: profile.contact_email || '',
        contact_name: profile.contact_name || '',
        industry: profile.industry || '',
        allowed_domains: profile.allowed_domains || ['*'],
      });
      
      // Auto-enable editing if profile is incomplete
      if (!profile.onboarding_completed) {
        setIsEditing(true);
      }
    }
  }, [profile]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.company_name.trim()) {
      newErrors.company_name = 'Company name is required';
    }
    
    if (!formData.contact_email.trim()) {
      newErrors.contact_email = 'Contact email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.contact_email)) {
      newErrors.contact_email = 'Please enter a valid email address';
    }
    
    if (formData.company_website && !formData.company_website.match(/^https?:\/\/.+/)) {
      newErrors.company_website = 'Website must start with http:// or https://';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    updateProfileMutation.mutate(formData);
  };

  const addDomain = () => {
    if (newDomain.trim() && !formData.allowed_domains.includes(newDomain.trim())) {
      // Remove '*' if adding specific domains
      const domains = formData.allowed_domains.filter(d => d !== '*');
      setFormData(prev => ({
        ...prev,
        allowed_domains: [...domains, newDomain.trim()]
      }));
      setNewDomain('');
    }
  };

  const removeDomain = (domain) => {
    setFormData(prev => ({
      ...prev,
      allowed_domains: prev.allowed_domains.filter(d => d !== domain)
    }));
  };

  const resetToAllowAll = () => {
    setFormData(prev => ({
      ...prev,
      allowed_domains: ['*']
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading profile</h3>
            <p className="mt-2 text-sm text-red-700">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  const isOnboarding = !profile?.onboarding_completed;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          {isOnboarding ? 'Complete Your Setup' : 'Company Profile'}
        </h1>
        <p className="mt-2 text-gray-600">
          {isOnboarding 
            ? 'Tell us about your company to get started with your AI assistant.'
            : 'Manage your company information and widget settings.'
          }
        </p>
      </div>

      {/* Progress indicator for onboarding */}
      {isOnboarding && (
        <div className="mb-8 bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-5 w-5 text-blue-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>Step 1 of 1:</strong> Complete your company profile to unlock all features
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Profile Form */}
      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Company Information</h3>
              {!isOnboarding && !isEditing && (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                >
                  Edit Profile
                </button>
              )}
            </div>
          </div>
          
          <div className="px-6 py-4 space-y-6">
            {/* Company Name */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <BuildingOfficeIcon className="h-4 w-4 mr-2" />
                Company Name *
              </label>
              <input
                type="text"
                value={formData.company_name}
                onChange={(e) => handleInputChange('company_name', e.target.value)}
                disabled={!isEditing && !isOnboarding}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  (!isEditing && !isOnboarding) ? 'bg-gray-50' : ''
                } ${errors.company_name ? 'border-red-300' : 'border-gray-300'}`}
                placeholder="Enter your company name"
              />
              {errors.company_name && (
                <p className="mt-1 text-sm text-red-600">{errors.company_name}</p>
              )}
            </div>

            {/* Company Website */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <GlobeAltIcon className="h-4 w-4 mr-2" />
                Company Website
              </label>
              <input
                type="url"
                value={formData.company_website}
                onChange={(e) => handleInputChange('company_website', e.target.value)}
                disabled={!isEditing && !isOnboarding}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  (!isEditing && !isOnboarding) ? 'bg-gray-50' : ''
                } ${errors.company_website ? 'border-red-300' : 'border-gray-300'}`}
                placeholder="https://yourcompany.com"
              />
              {errors.company_website && (
                <p className="mt-1 text-sm text-red-600">{errors.company_website}</p>
              )}
            </div>

            {/* Contact Email */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <EnvelopeIcon className="h-4 w-4 mr-2" />
                Contact Email *
              </label>
              <input
                type="email"
                value={formData.contact_email}
                onChange={(e) => handleInputChange('contact_email', e.target.value)}
                disabled={!isEditing && !isOnboarding}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  (!isEditing && !isOnboarding) ? 'bg-gray-50' : ''
                } ${errors.contact_email ? 'border-red-300' : 'border-gray-300'}`}
                placeholder="contact@yourcompany.com"
              />
              {errors.contact_email && (
                <p className="mt-1 text-sm text-red-600">{errors.contact_email}</p>
              )}
            </div>

            {/* Contact Name */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <UserIcon className="h-4 w-4 mr-2" />
                Contact Person
              </label>
              <input
                type="text"
                value={formData.contact_name}
                onChange={(e) => handleInputChange('contact_name', e.target.value)}
                disabled={!isEditing && !isOnboarding}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  (!isEditing && !isOnboarding) ? 'bg-gray-50' : ''
                }`}
                placeholder="John Smith"
              />
            </div>

            {/* Industry */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <BriefcaseIcon className="h-4 w-4 mr-2" />
                Industry
              </label>
              <select
                value={formData.industry}
                onChange={(e) => handleInputChange('industry', e.target.value)}
                disabled={!isEditing && !isOnboarding}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  (!isEditing && !isOnboarding) ? 'bg-gray-50' : ''
                }`}
              >
                <option value="">Select an industry</option>
                <option value="Technology">Technology</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Finance">Finance</option>
                <option value="Education">Education</option>
                <option value="Retail">Retail</option>
                <option value="Manufacturing">Manufacturing</option>
                <option value="Real Estate">Real Estate</option>
                <option value="Legal">Legal</option>
                <option value="Consulting">Consulting</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
        </div>

        {/* Widget Domain Restrictions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Widget Security</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Control which domains can embed your chat widget
                </p>
              </div>
              {!isEditing && !isOnboarding && (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 text-sm"
                >
                  Edit Domains
                </button>
              )}
            </div>
          </div>
          
          <div className="px-6 py-4 space-y-4">
            {/* Current Domains - Always visible */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Currently Allowed Domains
              </label>
              <div className="flex flex-wrap gap-2 mb-3">
                {formData.allowed_domains.map((domain, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {domain === '*' ? 'All domains (*)' : domain}
                  </span>
                ))}
              </div>
            </div>
            
            {/* Editing interface - only when editing */}
            {(isEditing || isOnboarding) && (
              <div>
                {/* Remove existing domains option */}
                {formData.allowed_domains.includes('*') && (
                  <div className="mb-4">
                    <button
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, allowed_domains: [] }))}
                      className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 text-sm"
                    >
                      Switch to Specific Domains
                    </button>
                    <p className="text-xs text-gray-500 mt-2">
                      Click above to restrict widget to specific domains
                    </p>
                  </div>
                )}

                {/* Add Domain */}
                {!formData.allowed_domains.includes('*') && (
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={newDomain}
                      onChange={(e) => setNewDomain(e.target.value)}
                      placeholder="cleona.ragamuffin.app"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      type="button"
                      onClick={addDomain}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                    >
                      Add
                    </button>
                  </div>
                )}

                {/* Allow All Domains Option */}
                {!formData.allowed_domains.includes('*') && formData.allowed_domains.length > 0 && (
                  <button
                    type="button"
                    onClick={resetToAllowAll}
                    className="text-sm text-gray-600 hover:text-gray-800 underline"
                  >
                    Allow all domains instead
                  </button>
                )}

                <p className="text-xs text-gray-500">
                  Add "cleona.ragamuffin.app" to allow your test site to use the widget
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Form Actions */}
        {(isEditing || isOnboarding) && (
          <div className="flex justify-end space-x-4">
            {!isOnboarding && (
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={updateProfileMutation.isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateProfileMutation.isLoading ? 'Saving...' : isOnboarding ? 'Complete Setup' : 'Save Changes'}
            </button>
          </div>
        )}

        {/* Error Message */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="mt-2 text-sm text-red-700">{errors.submit}</p>
              </div>
            </div>
          </div>
        )}
      </form>

      {/* Success Message for completed onboarding */}
      {profile?.onboarding_completed && !isEditing && (
        <div className="mt-8 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Profile Complete</h3>
              <p className="mt-2 text-sm text-green-700">
                Your company profile is set up and your AI assistant is ready to use. 
                You can now upload documents, customize your widget, and start embedding it on your website.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}