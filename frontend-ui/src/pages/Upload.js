import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '../context/AuthContext';
import { uploadWithProgress } from '../services/api';
import toast from 'react-hot-toast';
import {
  DocumentArrowUpIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

const Upload = () => {
  const { user, isAuthenticated } = useAuth();
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0,
      error: null,
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true,
  });

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const uploadFile = async (fileData) => {
    if (!user?.tenant_id) {
      toast.error('No tenant ID found. Please log in again.');
      return;
    }

    try {
      setFiles(prev => prev.map(f => 
        f.id === fileData.id ? { ...f, status: 'uploading' } : f
      ));

      const response = await uploadWithProgress(
        fileData.file,
        user.tenant_id,
        (progress) => {
          setFiles(prev => prev.map(f => 
            f.id === fileData.id ? { ...f, progress } : f
          ));
        }
      );

      setFiles(prev => prev.map(f => 
        f.id === fileData.id ? { ...f, status: 'completed', progress: 100 } : f
      ));

      toast.success(`${fileData.file.name} uploaded successfully!`);
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error.response?.data?.detail || 'Upload failed';
      
      setFiles(prev => prev.map(f => 
        f.id === fileData.id ? { ...f, status: 'error', error: errorMessage } : f
      ));

      toast.error(`Failed to upload ${fileData.file.name}: ${errorMessage}`);
    }
  };

  const uploadAll = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) return;

    setUploading(true);
    try {
      // Upload files sequentially to avoid overwhelming the server
      for (const fileData of pendingFiles) {
        await uploadFile(fileData);
      }
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file) => {
    const type = file.type.toLowerCase();
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('excel') || type.includes('sheet')) return '📊';
    if (type.includes('csv')) return '📋';
    return '📄';
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h2 className="mt-4 text-xl font-semibold text-gray-900">
          Please log in to upload documents
        </h2>
        <p className="mt-2 text-gray-600">
          You need to be authenticated to upload and process documents.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="text-center mb-8">
        <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-primary-600" />
        <h1 className="mt-4 text-3xl font-bold text-gray-900">
          Upload Documents
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Upload your documents to make them searchable and queryable
        </p>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`file-upload-area ${isDragActive ? 'dragover' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="text-center">
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          <div className="mt-4">
            <p className="text-lg font-medium text-gray-900">
              {isDragActive
                ? 'Drop the files here...'
                : 'Drag & drop files here, or click to select'}
            </p>
            <p className="mt-2 text-sm text-gray-500">
              Supports PDF, Word, Excel, CSV, and text files (max 50MB each)
            </p>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-8">
          <div className="card">
            <div className="card-header">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Files to Upload ({files.length})
                </h3>
                <div className="space-x-2">
                  <button
                    onClick={() => setFiles([])}
                    className="btn-ghost text-sm"
                    disabled={uploading}
                  >
                    Clear All
                  </button>
                  <button
                    onClick={uploadAll}
                    disabled={uploading || files.every(f => f.status !== 'pending')}
                    className="btn-primary text-sm"
                  >
                    {uploading ? 'Uploading...' : 'Upload All'}
                  </button>
                </div>
              </div>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                {files.map((fileData) => (
                  <div
                    key={fileData.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">
                        {getFileIcon(fileData.file)}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">
                          {fileData.file.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(fileData.file.size)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      {/* Status indicator */}
                      <div className="flex items-center space-x-2">
                        {fileData.status === 'pending' && (
                          <span className="badge badge-info">Pending</span>
                        )}
                        {fileData.status === 'uploading' && (
                          <div className="flex items-center space-x-2">
                            <span className="badge badge-warning">Uploading</span>
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${fileData.progress}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-500">
                              {fileData.progress}%
                            </span>
                          </div>
                        )}
                        {fileData.status === 'completed' && (
                          <div className="flex items-center space-x-1">
                            <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            <span className="badge badge-success">Completed</span>
                          </div>
                        )}
                        {fileData.status === 'error' && (
                          <div className="flex items-center space-x-1">
                            <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                            <span className="badge badge-error">Error</span>
                          </div>
                        )}
                      </div>

                      {/* Remove button */}
                      <button
                        onClick={() => removeFile(fileData.id)}
                        disabled={fileData.status === 'uploading'}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-3">
          What happens after upload?
        </h3>
        <ul className="text-sm text-blue-800 space-y-2">
          <li className="flex items-start">
            <span className="mr-2">1.</span>
            <span>Your documents are processed and analyzed by our AI</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">2.</span>
            <span>Key information is extracted and indexed for search</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">3.</span>
            <span>You can start asking questions about your documents in the Chat section</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default Upload;