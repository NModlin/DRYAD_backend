import { useState, useCallback } from 'react';
import Head from 'next/head';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentArrowUpIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import clsx from 'clsx';

import { GremlinsAIClient, Document, QueryWithRAGResponse } from '@gremlins-ai/sdk';

interface UploadedDocument {
  id: string;
  filename: string;
  size: number;
  uploadedAt: Date;
  processed: boolean;
}

interface SearchResult {
  query: string;
  answer: string;
  sources: Array<{
    document_id: string;
    filename: string;
    relevance_score: number;
    excerpt: string;
  }>;
  timestamp: Date;
}

export default function RAGApp() {
  const [client] = useState(() => new GremlinsAIClient({
    baseUrl: process.env.NEXT_PUBLIC_GREMLINS_AI_URL || 'http://localhost:8000',
    apiKey: process.env.NEXT_PUBLIC_GREMLINS_AI_API_KEY,
  }));

  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const uploadPromises = acceptedFiles.map(async (file) => {
        const uploadedDoc = await client.uploadDocument({
          file,
          filename: file.name,
          processForRAG: true,
        });

        return {
          id: uploadedDoc.id,
          filename: file.name,
          size: file.size,
          uploadedAt: new Date(),
          processed: true, // Assume processed for demo
        };
      });

      const newDocuments = await Promise.all(uploadPromises);
      setDocuments(prev => [...prev, ...newDocuments]);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, [client]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
  });

  // Search handler
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || documents.length === 0) return;

    setIsSearching(true);
    setSearchError(null);

    try {
      const response = await client.queryWithRAG({
        query: searchQuery,
        document_ids: documents.map(doc => doc.id),
        max_results: 5,
      });

      const newResult: SearchResult = {
        query: searchQuery,
        answer: response.answer,
        sources: response.sources || [],
        timestamp: new Date(),
      };

      setSearchResults(prev => [newResult, ...prev]);
      setSearchQuery('');
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <>
      <Head>
        <title>GremlinsAI RAG Demo - Document Q&A</title>
        <meta name="description" content="Upload documents and ask questions using GremlinsAI RAG" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              🤖 GremlinsAI RAG Demo
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Upload your documents and ask questions. Our AI will search through your content 
              and provide accurate answers with source citations.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Column - Upload & Documents */}
            <div className="space-y-6">
              {/* Upload Area */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                  📄 Upload Documents
                </h2>
                
                <div
                  {...getRootProps()}
                  className={clsx(
                    'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                    isDragActive
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  )}
                >
                  <input {...getInputProps()} />
                  <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  {isDragActive ? (
                    <p className="text-blue-600">Drop the files here...</p>
                  ) : (
                    <div>
                      <p className="text-gray-600 mb-2">
                        Drag & drop files here, or click to select
                      </p>
                      <p className="text-sm text-gray-500">
                        Supports PDF, TXT, DOC, DOCX files
                      </p>
                    </div>
                  )}
                </div>

                {isUploading && (
                  <div className="mt-4 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-blue-600">Uploading and processing...</span>
                  </div>
                )}

                {uploadError && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex">
                      <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                      <div className="ml-3">
                        <p className="text-sm text-red-800">{uploadError}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Documents List */}
              {documents.length > 0 && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">
                    📚 Uploaded Documents ({documents.length})
                  </h3>
                  <div className="space-y-3">
                    {documents.map((doc) => (
                      <motion.div
                        key={doc.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center p-3 bg-gray-50 rounded-lg"
                      >
                        <DocumentTextIcon className="h-8 w-8 text-blue-500 mr-3" />
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{doc.filename}</p>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(doc.size)} • {doc.uploadedAt.toLocaleDateString()}
                          </p>
                        </div>
                        {doc.processed && (
                          <CheckCircleIcon className="h-5 w-5 text-green-500" />
                        )}
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - Search & Results */}
            <div className="space-y-6">
              {/* Search Form */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                  🔍 Ask Questions
                </h2>
                
                <form onSubmit={handleSearch} className="space-y-4">
                  <div>
                    <textarea
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Ask a question about your documents..."
                      className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                      disabled={documents.length === 0 || isSearching}
                    />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={!searchQuery.trim() || documents.length === 0 || isSearching}
                    className="w-full flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSearching ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Searching...
                      </>
                    ) : (
                      <>
                        <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                        Search Documents
                      </>
                    )}
                  </button>
                </form>

                {documents.length === 0 && (
                  <p className="text-sm text-gray-500 mt-4 text-center">
                    Upload documents first to start asking questions
                  </p>
                )}

                {searchError && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex">
                      <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                      <div className="ml-3">
                        <p className="text-sm text-red-800">{searchError}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Search Results */}
              <AnimatePresence>
                {searchResults.map((result, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="bg-white rounded-xl shadow-lg p-6"
                  >
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Q: {result.query}
                      </h3>
                      <div className="prose prose-blue max-w-none">
                        <ReactMarkdown
                          components={{
                            code({ node, inline, className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '');
                              return !inline && match ? (
                                <SyntaxHighlighter
                                  style={tomorrow}
                                  language={match[1]}
                                  PreTag="div"
                                  {...props}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              );
                            },
                          }}
                        >
                          {result.answer}
                        </ReactMarkdown>
                      </div>
                    </div>

                    {result.sources.length > 0 && (
                      <div className="border-t pt-4">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">
                          📖 Sources:
                        </h4>
                        <div className="space-y-2">
                          {result.sources.map((source, sourceIndex) => (
                            <div key={sourceIndex} className="text-sm bg-gray-50 p-3 rounded">
                              <div className="flex justify-between items-start mb-1">
                                <span className="font-medium text-gray-900">
                                  {source.filename}
                                </span>
                                <span className="text-gray-500">
                                  {Math.round(source.relevance_score * 100)}% match
                                </span>
                              </div>
                              <p className="text-gray-600 italic">"{source.excerpt}"</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="text-xs text-gray-500 mt-4">
                      {result.timestamp.toLocaleString()}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
