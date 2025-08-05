import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useDropzone } from 'react-dropzone';
import { documentsAPI } from '../services/api';
import { useConfig } from '../context/ConfigContext';
import toast from 'react-hot-toast';
import {
  DocumentIcon,
  TrashIcon,
  ArrowUpTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

export default function Documents() {
  const [uploadingFiles, setUploadingFiles] = useState([]);
  const { config } = useConfig();
  const queryClient = useQueryClient();

  const { data: documents, isLoading, error } = useQuery('documents', documentsAPI.getDocuments);

  const uploadMutation = useMutation(
    ({ file, extractStructured }) => documentsAPI.uploadDocument(file, extractStructured),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('documents');
        toast.success('Document uploaded successfully!');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Upload failed');
      },
    }
  );

  const deleteMutation = useMutation(
    (documentId) => documentsAPI.deleteDocument(documentId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('documents');
        toast.success('Document deleted successfully!');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Delete failed');
      },
    }
  );

  const onDrop = useCallback((acceptedFiles) => {
    acceptedFiles.forEach((file) => {
      // Check file size
      if (file.size > config.max_file_size_mb * 1024 * 1024) {
        toast.error(`File ${file.name} is too large (max ${config.max_file_size_mb}MB)`);
        return;
      }

      // Add to uploading list
      const uploadId = Date.now() + Math.random();
      setUploadingFiles(prev => [...prev, { id: uploadId, file, progress: 0 }]);

      // Upload file
      uploadMutation.mutate(
        { file, extractStructured: false },
        {
          onSettled: () => {
            setUploadingFiles(prev => prev.filter(f => f.id !== uploadId));
          }
        }
      );
    });
  }, [config.max_file_size_mb, uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/x-rst': ['.rst'],
    },
    maxSize: config.max_file_size_mb * 1024 * 1024,
  });

  const handleDelete = (documentId, filename) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      deleteMutation.mutate(documentId);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <DocumentIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getFileTypeColor = (fileType) => {
    const colors = {
      PDF: 'bg-red-100 text-red-800',
      CSV: 'bg-green-100 text-green-800',
      Excel: 'bg-blue-100 text-blue-800',
      Text: 'bg-gray-100 text-gray-800',
    };
    return colors[fileType] || 'bg-gray-100 text-gray-800';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading documents: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <p className="mt-2 text-gray-600">
          Upload and manage your knowledge base documents. {documents?.total || 0} of {config.max_documents} documents used.
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload New Document</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragActive
              ? 'border-blue-400 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive
              ? 'Drop the files here...'
              : 'Drag & drop files here, or click to select files'}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            Supports PDF, CSV, Excel, and text files (max {config.max_file_size_mb}MB)
          </p>
        </div>

        {/* Uploading Files */}
        {uploadingFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            <h3 className="text-sm font-medium text-gray-700">Uploading...</h3>
            {uploadingFiles.map((upload) => (
              <div key={upload.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                <DocumentIcon className="h-5 w-5 text-gray-400" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{upload.file.name}</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Your Documents</h2>
        </div>
        {documents?.documents?.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {documents.documents.map((doc) => (
              <div key={doc.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {getStatusIcon(doc.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {doc.filename}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getFileTypeColor(doc.file_type)}`}>
                        {doc.file_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {Math.round(doc.file_size / 1024)}KB
                      </span>
                      <span className="text-xs text-gray-500">
                        {doc.chunk_count} chunks
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {doc.error_message && (
                      <p className="text-xs text-red-600 mt-1">{doc.error_message}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    doc.status === 'completed' 
                      ? 'bg-green-100 text-green-800'
                      : doc.status === 'processing'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {doc.status}
                  </span>
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    disabled={deleteMutation.isLoading}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">No documents uploaded yet.</p>
            <p className="text-xs text-gray-500">Upload your first document to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}