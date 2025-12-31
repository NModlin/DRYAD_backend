import React, { useState, useEffect } from 'react'
import { useQuery, useMutation } from 'react-query'
import { 
  Brain, 
  Search, 
  Filter, 
  Plus, 
  Trash2, 
  Archive, 
  Star, 
  Clock,
  Users,
  MessageSquare,
  FileText,
  Database,
  Zap,
  Shield
} from 'lucide-react'
import { 
  MemoryContext, 
  MemorySearchRequest,
  MemoryUpdateRequest,
  AgentMemory,
  MemoryCategory
} from '../types'
import { dryadAPI } from '../services/api'

const MemoryKeeperPanel: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<MemoryCategory | 'all'>('all')
  const [selectedMemory, setSelectedMemory] = useState<AgentMemory | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [newMemoryContent, setNewMemoryContent] = useState('')
  const [newMemoryTags, setNewMemoryTags] = useState<string[]>([])

  // Fetch memory contexts
  const { data: contexts, isLoading: contextsLoading } = useQuery(
    'memory-contexts',
    () => dryadAPI.listMemoryContexts(),
    {
      staleTime: 2 * 60 * 1000,
    }
  )

  // Fetch agent memories
  const { data: memories, isLoading: memoriesLoading, refetch: refetchMemories } = useQuery(
    ['agent-memories', selectedCategory],
    () => dryadAPI.listAgentMemories({ category: selectedCategory === 'all' ? undefined : selectedCategory }),
    {
      staleTime: 1 * 60 * 1000,
    }
  )

  // Search memories mutation
  const searchMutation = useMutation(
    (request: MemorySearchRequest) => dryadAPI.searchMemories(request),
    {
      onSuccess: (results) => {
        // Handle search results
        console.log('Search results:', results)
      },
    }
  )

  // Create memory mutation
  const createMemoryMutation = useMutation(
    (content: string) => dryadAPI.createMemory({ content, tags: newMemoryTags }),
    {
      onSuccess: () => {
        setIsCreating(false)
        setNewMemoryContent('')
        setNewMemoryTags([])
        refetchMemories()
      },
    }
  )

  // Update memory mutation
  const updateMemoryMutation = useMutation(
    (request: MemoryUpdateRequest) => dryadAPI.updateMemory(request),
    {
      onSuccess: () => {
        setSelectedMemory(null)
        refetchMemories()
      },
    }
  )

  // Delete memory mutation
  const deleteMemoryMutation = useMutation(
    (memoryId: string) => dryadAPI.deleteMemory(memoryId),
    {
      onSuccess: () => {
        setSelectedMemory(null)
        refetchMemories()
      },
    }
  )

  const categories: MemoryCategory[] = [
    'conversation',
    'knowledge',
    'preference',
    'behavior',
    'context',
    'insight'
  ]

  const handleSearch = () => {
    if (!searchQuery.trim()) return

    const request: MemorySearchRequest = {
      query: searchQuery.trim(),
      category: selectedCategory === 'all' ? undefined : selectedCategory,
      limit: 50,
      includeContext: true,
    }

    searchMutation.mutate(request)
  }

  const handleCreateMemory = () => {
    if (!newMemoryContent.trim()) return
    createMemoryMutation.mutate(newMemoryContent.trim())
  }

  const handleUpdateMemory = () => {
    if (!selectedMemory || !newMemoryContent.trim()) return

    const request: MemoryUpdateRequest = {
      memoryId: selectedMemory.id,
      content: newMemoryContent.trim(),
      tags: newMemoryTags,
    }

    updateMemoryMutation.mutate(request)
  }

  const getCategoryColor = (category: MemoryCategory) => {
    const colors = {
      conversation: 'bg-blue-100 text-blue-800',
      knowledge: 'bg-green-100 text-green-800',
      preference: 'bg-purple-100 text-purple-800',
      behavior: 'bg-orange-100 text-orange-800',
      context: 'bg-indigo-100 text-indigo-800',
      insight: 'bg-pink-100 text-pink-800',
    }
    return colors[category]
  }

  const getCategoryIcon = (category: MemoryCategory) => {
    const icons = {
      conversation: MessageSquare,
      knowledge: Database,
      preference: Star,
      behavior: Zap,
      context: Brain,
      insight: Shield,
    }
    return icons[category]
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-8 h-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Memory Keeper Panel</h1>
              <p className="text-gray-600">Manage and explore agent memories and contexts</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>New Memory</span>
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Memory Contexts */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Search and Filter */}
          <div className="p-4 border-b border-gray-200">
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search memories..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value as MemoryCategory | 'all')}
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="all">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Memory Contexts */}
          <div className="flex-1 overflow-auto">
            <div className="p-4">
              <h3 className="font-medium text-gray-900 mb-3">Memory Contexts</h3>
              {contextsLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="p-3 bg-gray-100 rounded-lg animate-pulse">
                      <div className="h-4 bg-gray-300 rounded mb-2"></div>
                      <div className="h-3 bg-gray-300 rounded w-3/4"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {contexts?.items?.map((context) => (
                    <div
                      key={context.id}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">{context.agentId}</span>
                        <span className="text-xs text-gray-500">{context.memoryCount} memories</span>
                      </div>
                      <p className="text-sm text-gray-600 truncate">{context.description}</p>
                      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                        <span>Updated {context.lastUpdated}</span>
                        <span>{context.importance}/10</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content - Memories */}
        <div className="flex-1 flex flex-col">
          {/* Memories List */}
          <div className="flex-1 overflow-auto">
            {memoriesLoading ? (
              <div className="p-6 space-y-4">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="p-4 bg-white rounded-lg shadow-soft border border-gray-200 animate-pulse">
                    <div className="h-4 bg-gray-300 rounded mb-3 w-3/4"></div>
                    <div className="h-3 bg-gray-300 rounded mb-2"></div>
                    <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : memories?.items?.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Memories Found</h3>
                  <p className="text-gray-500 mb-4">
                    {selectedCategory === 'all' 
                      ? 'No memories have been created yet.'
                      : `No ${selectedCategory} memories found.`
                    }
                  </p>
                  <button
                    onClick={() => setIsCreating(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Create First Memory
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-6 space-y-4">
                {memories?.items?.map((memory) => {
                  const CategoryIcon = getCategoryIcon(memory.category)
                  return (
                    <div
                      key={memory.id}
                      onClick={() => {
                        setSelectedMemory(memory)
                        setNewMemoryContent(memory.content)
                        setNewMemoryTags(memory.tags || [])
                      }}
                      className={`p-4 bg-white rounded-lg shadow-soft border border-gray-200 cursor-pointer transition-all hover:shadow-md ${
                        selectedMemory?.id === memory.id ? 'ring-2 ring-purple-500' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <CategoryIcon className={`w-4 h-4 ${getCategoryColor(memory.category).split(' ')[1]}`} />
                          <span className={`text-xs px-2 py-1 rounded-full ${getCategoryColor(memory.category)}`}>
                            {memory.category}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{memory.createdAt}</span>
                        </div>
                      </div>

                      <p className="text-gray-700 mb-3 line-clamp-3">{memory.content}</p>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <div className="flex items-center space-x-1">
                            <Users className="w-3 h-3" />
                            <span>{memory.agentId}</span>
                          </div>
                          {memory.tags && memory.tags.length > 0 && (
                            <div className="flex items-center space-x-1">
                              <span>Tags: {memory.tags.join(', ')}</span>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteMemoryMutation.mutate(memory.id)
                            }}
                            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                            disabled={deleteMemoryMutation.isLoading}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Memory Editor Panel */}
        {(selectedMemory || isCreating) && (
          <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">
                  {isCreating ? 'Create Memory' : 'Edit Memory'}
                </h3>
                <button
                  onClick={() => {
                    setIsCreating(false)
                    setSelectedMemory(null)
                    setNewMemoryContent('')
                    setNewMemoryTags([])
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
              {/* Category Selection (for creation) */}
              {isCreating && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={selectedCategory === 'all' ? 'conversation' : selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value as MemoryCategory)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    {categories.map((category) => (
                      <option key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Content Editor */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Content</label>
                <textarea
                  value={newMemoryContent}
                  onChange={(e) => setNewMemoryContent(e.target.value)}
                  placeholder="Enter memory content..."
                  className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Tags Editor */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {newMemoryTags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                      {tag}
                      <button
                        onClick={() => setNewMemoryTags(newMemoryTags.filter((_, i) => i !== index))}
                        className="ml-1 text-gray-500 hover:text-gray-700"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add tag..."
                  className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const input = e.target as HTMLInputElement
                      const tag = input.value.trim()
                      if (tag && !newMemoryTags.includes(tag)) {
                        setNewMemoryTags([...newMemoryTags, tag])
                        input.value = ''
                      }
                    }
                  }}
                />
              </div>

              {/* Action Buttons */}
              <div className="space-y-2">
                {isCreating ? (
                  <button
                    onClick={handleCreateMemory}
                    disabled={!newMemoryContent.trim() || createMemoryMutation.isLoading}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    {createMemoryMutation.isLoading ? 'Creating...' : 'Create Memory'}
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleUpdateMemory}
                      disabled={!newMemoryContent.trim() || updateMemoryMutation.isLoading}
                      className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      {updateMemoryMutation.isLoading ? 'Updating...' : 'Update Memory'}
                    </button>
                    <button
                      onClick={() => deleteMemoryMutation.mutate(selectedMemory!.id)}
                      disabled={deleteMemoryMutation.isLoading}
                      className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      {deleteMemoryMutation.isLoading ? 'Deleting...' : 'Delete Memory'}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default MemoryKeeperPanel