import React, { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from 'react-query'
import { 
  Folder, 
  File, 
  Upload, 
  Download, 
  Trash2, 
  Share, 
  Copy, 
  Move,
  Search,
  Filter,
  Grid,
  List,
  Settings,
  HardDrive,
  Cloud,
  Sync
} from 'lucide-react'
import { 
  FileRecord,
  FileUploadOptions,
  Grove,
  Branch
} from '../types'
import { dryadAPI } from '../services/api'

const FileManager: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedGrove, setSelectedGrove] = useState<Grove | null>(null)
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid')
  const [storagePreference, setStoragePreference] = useState<'local' | 'google_drive' | 'both'>('both')
  const [uploadOptions, setUploadOptions] = useState<FileUploadOptions>({
    storage: 'both',
    groveId: undefined,
    branchId: undefined,
    tags: []
  })
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  // Fetch files
  const { data: files, isLoading: filesLoading, refetch: refetchFiles } = useQuery(
    ['files', selectedGrove?.id],
    () => dryadAPI.listFiles(selectedGrove?.id),
    {
      enabled: !!selectedGrove,
      staleTime: 1 * 60 * 1000,
    }
  )

  // File upload mutation
  const uploadMutation = useMutation(
    (formData: FormData) => dryadAPI.uploadFile(formData.get('file') as File, uploadOptions),
    {
      onSuccess: () => {
        refetchFiles()
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      },
    }
  )

  // Auto-select first grove if available
  useEffect(() => {
    if (groves && groves.items && groves.items.length > 0 && !selectedGrove) {
      setSelectedGrove(groves.items[0])
      setUploadOptions(prev => ({ ...prev, groveId: groves.items[0].id }))
    }
  }, [groves, selectedGrove])

  // Update upload options when grove/branch changes
  useEffect(() => {
    setUploadOptions(prev => ({
      ...prev,
      groveId: selectedGrove?.id,
      branchId: selectedBranch?.id,
      storage: storagePreference
    }))
  }, [selectedGrove, selectedBranch, storagePreference])

  const filteredFiles = files?.filter(file => 
    file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.storage.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStorageIcon = (storage: string) => {
    switch (storage) {
      case 'local': return <HardDrive className="w-4 h-4 text-blue-500" />
      case 'google_drive': return <Cloud className="w-4 h-4 text-green-500" />
      case 'both': return <Sync className="w-4 h-4 text-purple-500" />
      default: return <HardDrive className="w-4 h-5 text-gray-500" />
    }
  }

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <File className="w-5 h-5 text-red-500" />
    if (type.includes('word') || type.includes('document')) return <File className="w-5 h-5 text-blue-500" />
    if (type.includes('sheet') || type.includes('excel')) return <File className="w-5 h-5 text-green-500" />
    if (type.includes('presentation') || type.includes('powerpoint')) return <File className="w-5 h-5 text-orange-500" />
    if (type.includes('image')) return <File className="w-5 h-5 text-purple-500" />
    if (type.includes('folder')) return <Folder className="w-5 h-5 text-yellow-500" />
    return <File className="w-5 h-5 text-gray-500" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleFileSelect = (fileId: string, isSelected: boolean) => {
    const newSelected = new Set(selectedFiles)
    if (isSelected) {
      newSelected.add(fileId)
    } else {
      newSelected.delete(fileId)
    }
    setSelectedFiles(newSelected)
  }

  const handleSelectAll = (select: boolean) => {
    if (select && filteredFiles) {
      setSelectedFiles(new Set(filteredFiles.map(f => f.id)))
    } else {
      setSelectedFiles(new Set())
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    const formData = new FormData()
    formData.append('file', files[0])
    formData.append('options', JSON.stringify(uploadOptions))

    uploadMutation.mutate(formData)
  }

  const handleStorageSync = () => {
    // Placeholder for storage synchronization logic
    console.log('Initiating storage synchronization...')
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Folder className="w-8 h-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">File Manager</h1>
              <p className="text-gray-600">Hybrid file storage with local and Google Drive integration</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleStorageSync}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Sync className="w-4 h-4" />
              <span>Sync Storage</span>
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isLoading}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>{uploadMutation.isLoading ? 'Uploading...' : 'Upload File'}</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Configuration */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Storage Configuration */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">Storage Configuration</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Storage Preference</span>
                <select
                  value={storagePreference}
                  onChange={(e) => setStoragePreference(e.target.value as any)}
                  className="text-sm p-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="local">Local Only</option>
                  <option value="google_drive">Google Drive</option>
                  <option value="both">Both (Hybrid)</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <HardDrive className="w-4 h-4" />
                <span>Local Storage: 2.3 GB / 10 GB</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Cloud className="w-4 h-4" />
                <span>Google Drive: 15.7 GB / 15 GB</span>
              </div>
            </div>
          </div>

          {/* Grove and Branch Selection */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">Location</h3>
            
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

          {/* Upload Options */}
          <div className="p-4">
            <h3 className="font-medium text-gray-900 mb-3">Upload Options</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>Storage:</span>
                <span className="font-medium capitalize">{uploadOptions.storage}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Grove:</span>
                <span className="font-medium">{selectedGrove?.name || 'Not selected'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Branch:</span>
                <span className="font-medium">{selectedBranch?.name || 'All branches'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Toolbar */}
          <div className="bg-white border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search files..."
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleSelectAll(true)}
                    disabled={!filteredFiles || filteredFiles.length === 0}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => handleSelectAll(false)}
                    disabled={selectedFiles.size === 0}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                  >
                    Clear Selection
                  </button>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  {selectedFiles.size > 0 ? `${selectedFiles.size} selected` : `${filteredFiles?.length || 0} files`}
                </span>
                <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded-md transition-colors ${
                      viewMode === 'grid' ? 'bg-white shadow-sm text-purple-600' : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Grid className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded-md transition-colors ${
                      viewMode === 'list' ? 'bg-white shadow-sm text-purple-600' : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <List className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Files Grid/List */}
          <div className="flex-1 overflow-auto p-6">
            {filesLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="p-4 bg-white rounded-lg shadow-soft border border-gray-200 animate-pulse">
                    <div className="h-4 bg-gray-300 rounded mb-3 w-3/4"></div>
                    <div className="h-3 bg-gray-300 rounded mb-2"></div>
                    <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : filteredFiles?.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Folder className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Files Found</h3>
                  <p className="text-gray-500 mb-4">
                    {searchQuery ? 'No files match your search.' : 'No files in this location.'}
                  </p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Upload First File
                  </button>
                </div>
              </div>
            ) : viewMode === 'list' ? (
              <div className="space-y-2">
                {filteredFiles?.map((file) => (
                  <div
                    key={file.id}
                    className={`p-4 bg-white rounded-lg border border-gray-200 transition-all ${
                      selectedFiles.has(file.id) ? 'bg-purple-50 border-purple-300' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedFiles.has(file.id)}
                          onChange={(e) => handleFileSelect(file.id, e.target.checked)}
                          className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                        />
                        {getFileIcon(file.type)}
                        <div>
                          <h3 className="font-medium text-gray-900">{file.name}</h3>
                          <p className="text-sm text-gray-500">
                            {file.type} • {formatFileSize(file.size)} • {file.storage}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStorageIcon(file.storage)}
                        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                          <Download className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                          <Share className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-red-600 transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredFiles?.map((file) => (
                  <div
                    key={file.id}
                    className={`bg-white rounded-lg shadow-soft border border-gray-200 cursor-pointer transition-all hover:shadow-md overflow-hidden ${
                      selectedFiles.has(file.id) ? 'ring-2 ring-purple-500' : ''
                    }`}
                    onClick={() => handleFileSelect(file.id, !selectedFiles.has(file.id))}
                  >
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <input
                          type="checkbox"
                          checked={selectedFiles.has(file.id)}
                          onChange={(e) => {
                            e.stopPropagation()
                            handleFileSelect(file.id, e.target.checked)
                          }}
                          className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                        />
                        {getStorageIcon(file.storage)}
                      </div>
                      <div className="text-center mb-3">
                        {getFileIcon(file.type)}
                      </div>
                      <div className="text-center">
                        <h3 className="font-medium text-gray-900 text-sm truncate mb-1">{file.name}</h3>
                        <p className="text-xs text-gray-500 truncate">{file.type}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <div className="border-t border-gray-200 px-3 py-2 bg-gray-50 flex justify-between">
                      <button 
                        className="text-xs text-gray-600 hover:text-gray-900"
                        onClick={(e) => e.stopPropagation()}
                      >
                        View
                      </button>
                      <button 
                        className="text-xs text-gray-600 hover:text-gray-900"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileManager