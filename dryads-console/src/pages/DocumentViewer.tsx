import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  Share, 
  Bookmark, 
  Eye,
  BookOpen,
  Zap,
  Brain,
  Users
} from 'lucide-react'
import { 
  FileRecord,
  Grove,
  Branch
} from '../types'
import { dryadAPI } from '../services/api'

const DocumentViewer: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedGrove, setSelectedGrove] = useState<Grove | null>(null)
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<FileRecord | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'grid' | 'preview'>('list')
  const [isPerplexityEnabled, setIsPerplexityEnabled] = useState(false)

  // Fetch user's groves
  const { data: groves, isLoading: grovesLoading } = useQuery(
    'user-groves',
    () => dryadAPI.listGroves(),
    {
      staleTime: 5 * 60 * 1000,
    }
  )

  // Fetch branches for selected grove
  const { data: branches, isLoading: branchesLoading } = useQuery(
    ['grove-branches', selectedGrove?.id],
    () => selectedGrove ? dryadAPI.listBranches(selectedGrove.id) : { items: [] },
    {
      enabled: !!selectedGrove,
      staleTime: 2 * 60 * 1000,
    }
  )

  // Fetch documents
  const { data: documents, isLoading: documentsLoading } = useQuery(
    ['documents', selectedGrove?.id, selectedBranch?.id],
    () => dryadAPI.listFiles(selectedGrove?.id),
    {
      enabled: !!selectedGrove,
      staleTime: 1 * 60 * 1000,
    }
  )

  // Auto-select first grove if available
  useEffect(() => {
    if (groves && groves.items && groves.items.length > 0 && !selectedGrove) {
      setSelectedGrove(groves.items[0])
    }
  }, [groves, selectedGrove])

  const filteredDocuments = documents?.filter(doc => 
    doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />
    if (type.includes('word') || type.includes('document')) return <FileText className="w-5 h-5 text-blue-500" />
    if (type.includes('sheet') || type.includes('excel')) return <FileText className="w-5 h-5 text-green-500" />
    if (type.includes('presentation') || type.includes('powerpoint')) return <FileText className="w-5 h-5 text-orange-500" />
    if (type.includes('image')) return <FileText className="w-5 h-5 text-purple-500" />
    return <FileText className="w-5 h-5 text-gray-500" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleDocumentSelect = (doc: FileRecord) => {
    setSelectedDocument(doc)
    if (viewMode !== 'preview') {
      setViewMode('preview')
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BookOpen className="w-8 h-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Document Viewer</h1>
              <p className="text-gray-600">Browse and analyze scientific documents with AI integration</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="perplexity-toggle"
                checked={isPerplexityEnabled}
                onChange={(e) => setIsPerplexityEnabled(e.target.checked)}
                className="w-4 h-4 text-purple-600 focus:ring-purple-500"
              />
              <label htmlFor="perplexity-toggle" className="flex items-center space-x-1 text-sm text-gray-700">
                <Brain className="w-4 h-4" />
                <span>Perplexity AI</span>
              </label>
            </div>
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'list' ? 'bg-white shadow-sm text-purple-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <FileText className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'grid' ? 'bg-white shadow-sm text-purple-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <BookOpen className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('preview')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'preview' ? 'bg-white shadow-sm text-purple-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Eye className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Navigation */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Search and Filter */}
          <div className="p-4 border-b border-gray-200">
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Grove Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Grove</label>
              <select
                value={selectedGrove?.id || ''}
                onChange={(e) => {
                  const grove = groves?.items?.find(g => g.id === e.target.value)
                  setSelectedGrove(grove || null)
                  setSelectedBranch(null)
                }}
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Select a grove</option>
                {groves?.items?.map((grove) => (
                  <option key={grove.id} value={grove.id}>{grove.name}</option>
                ))}
              </select>
            </div>

            {/* Branch Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Branch</label>
              <select
                value={selectedBranch?.id || ''}
                onChange={(e) => {
                  const branch = branches?.items?.find(b => b.id === e.target.value)
                  setSelectedBranch(branch || null)
                }}
                disabled={!selectedGrove || branchesLoading}
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100"
              >
                <option value="">All branches</option>
                {branches?.items?.map((branch) => (
                  <option key={branch.id} value={branch.id}>{branch.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Document Statistics */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">Document Statistics</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>Total Documents</span>
                <span className="font-medium">{documents?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>PDF Files</span>
                <span className="font-medium">
                  {documents?.filter(d => d.type.includes('pdf')).length || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Total Size</span>
                <span className="font-medium">
                  {formatFileSize(documents?.reduce((sum, d) => sum + d.size, 0) || 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Perplexity AI Integration */}
          {isPerplexityEnabled && (
            <div className="p-4">
              <h3 className="font-medium text-gray-900 mb-3">AI Analysis</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span>Real-time research</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Brain className="w-4 h-4 text-purple-500" />
                  <span>Scientific insights</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4 text-blue-500" />
                  <span>Multi-source validation</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Documents List/Grid */}
          {viewMode !== 'preview' && (
            <div className="flex-1 overflow-auto p-6">
              {documentsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="p-4 bg-white rounded-lg shadow-soft border border-gray-200 animate-pulse">
                      <div className="h-4 bg-gray-300 rounded mb-3 w-3/4"></div>
                      <div className="h-3 bg-gray-300 rounded mb-2"></div>
                      <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : filteredDocuments?.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Documents Found</h3>
                    <p className="text-gray-500">
                      {searchQuery ? 'No documents match your search.' : 'No documents in this grove.'}
                    </p>
                  </div>
                </div>
              ) : viewMode === 'list' ? (
                <div className="space-y-4">
                  {filteredDocuments?.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => handleDocumentSelect(doc)}
                      className="p-4 bg-white rounded-lg shadow-soft border border-gray-200 cursor-pointer transition-all hover:shadow-md"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getFileIcon(doc.type)}
                          <div>
                            <h3 className="font-medium text-gray-900">{doc.name}</h3>
                            <p className="text-sm text-gray-500">
                              {doc.type} • {formatFileSize(doc.size)} • {doc.storage}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                            <Download className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                            <Share className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-yellow-600 transition-colors">
                            <Bookmark className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredDocuments?.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => handleDocumentSelect(doc)}
                      className="bg-white rounded-lg shadow-soft border border-gray-200 cursor-pointer transition-all hover:shadow-md overflow-hidden"
                    >
                      <div className="p-4">
                        <div className="flex items-center space-x-3 mb-3">
                          {getFileIcon(doc.type)}
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-gray-900 truncate">{doc.name}</h3>
                            <p className="text-sm text-gray-500 truncate">{doc.type}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-sm text-gray-500">
                          <span>{formatFileSize(doc.size)}</span>
                          <span>{doc.storage}</span>
                        </div>
                      </div>
                      <div className="border-t border-gray-200 px-4 py-2 bg-gray-50 flex justify-between">
                        <button className="text-xs text-gray-600 hover:text-gray-900">View</button>
                        <button className="text-xs text-gray-600 hover:text-gray-900">Download</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Document Preview */}
          {viewMode === 'preview' && selectedDocument && (
            <div className="flex-1 flex flex-col">
              {/* Preview Header */}
              <div className="bg-white border-b border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getFileIcon(selectedDocument.type)}
                    <div>
                      <h2 className="font-medium text-gray-900">{selectedDocument.name}</h2>
                      <p className="text-sm text-gray-500">
                        {selectedDocument.type} • {formatFileSize(selectedDocument.size)} • {selectedDocument.storage}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                      <Download className="w-4 h-4 inline mr-1" />
                      Download
                    </button>
                    <button className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                      <Share className="w-4 h-4 inline mr-1" />
                      Share
                    </button>
                  </div>
                </div>
              </div>

              {/* Preview Content */}
              <div className="flex-1 flex overflow-hidden">
                {/* Document Viewer */}
                <div className="flex-1 bg-white p-6 overflow-auto">
                  <div className="max-w-4xl mx-auto">
                    {/* Placeholder for document content */}
                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                      <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Document Preview</h3>
                      <p className="text-gray-500 mb-4">
                        Document content would be displayed here with AI-powered analysis.
                      </p>
                      {isPerplexityEnabled && (
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                          <div className="flex items-center space-x-2 mb-2">
                            <Brain className="w-5 h-5 text-purple-600" />
                            <span className="font-medium text-purple-700">Perplexity AI Analysis</span>
                          </div>
                          <p className="text-sm text-purple-600">
                            Real-time research and scientific insights would be integrated here.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* AI Analysis Panel */}
                {isPerplexityEnabled && (
                  <div className="w-80 bg-white border-l border-gray-200 p-4 overflow-auto">
                    <h3 className="font-medium text-gray-900 mb-4">AI Insights</h3>
                    <div className="space-y-4">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <h4 className="font-medium text-blue-900 mb-1">Key Findings</h4>
                        <p className="text-sm text-blue-700">
                          AI would extract and summarize key scientific findings from this document.
                        </p>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <h4 className="font-medium text-green-900 mb-1">Related Research</h4>
                        <p className="text-sm text-green-700">
                          Perplexity AI would find and link to related scientific papers.
                        </p>
                      </div>
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                        <h4 className="font-medium text-purple-900 mb-1">Methodology Analysis</h4>
                        <p className="text-sm text-purple-700">
                          AI would analyze and validate the research methodology used.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DocumentViewer