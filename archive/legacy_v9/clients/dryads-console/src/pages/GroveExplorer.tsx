import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { TreePine, Plus, Search, Filter, Star, Archive, Trash2, Settings } from 'lucide-react'
import { Grove, Branch } from '../types'
import { dryadAPI } from '../services/api'

const GroveExplorer: React.FC = () => {
  const [selectedGrove, setSelectedGrove] = useState<Grove | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'list' | 'tree' | 'grid'>('tree')

  // Fetch groves
  const { data: groves, isLoading: grovesLoading } = useQuery(
    'groves',
    () => dryadAPI.listGroves(),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  )

  // Fetch branches for selected grove
  const { data: branches, isLoading: branchesLoading } = useQuery(
    ['branches', selectedGrove?.id],
    () => selectedGrove ? dryadAPI.getBranchTree(selectedGrove.id) : [],
    {
      enabled: !!selectedGrove,
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  )

  // Create a new grove
  const handleCreateGrove = async () => {
    try {
      const newGrove = await dryadAPI.createGrove({
        name: 'New Grove',
        description: 'A new knowledge exploration space',
      })
      // Refresh groves list
      // queryClient.invalidateQueries('groves')
      setSelectedGrove(newGrove)
    } catch (error) {
      console.error('Failed to create grove:', error)
    }
  }

  // Filter groves based on search
  const filteredGroves = groves?.items?.filter(grove => 
    grove.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    grove.description?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  if (grovesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-gray-600">Loading groves...</span>
      </div>
    )
  }

  return (
    <div className="h-full flex">
      {/* Sidebar - Grove List */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Groves</h2>
            <button
              onClick={handleCreateGrove}
              className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
              title="Create New Grove"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search groves..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Grove List */}
        <div className="flex-1 overflow-auto">
          {filteredGroves.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              {searchQuery ? 'No groves match your search' : 'No groves found'}
            </div>
          ) : (
            <div className="space-y-1 p-2">
              {filteredGroves.map((grove) => (
                <div
                  key={grove.id}
                  onClick={() => setSelectedGrove(grove)}
                  className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                    selectedGrove?.id === grove.id
                      ? 'bg-primary-50 border-l-4 border-primary-600'
                      : 'hover:bg-gray-50 border-l-4 border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <TreePine className={`w-5 h-5 ${
                        selectedGrove?.id === grove.id ? 'text-primary-600' : 'text-gray-400'
                      }`} />
                      <div>
                        <h3 className="font-medium text-gray-900">{grove.name}</h3>
                        <p className="text-sm text-gray-500 truncate">
                          {grove.description || 'No description'}
                        </p>
                      </div>
                    </div>
                    {grove.isFavorite && (
                      <Star className="w-4 h-4 text-yellow-500 fill-current" />
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                    <span>{grove.branchCount} branches</span>
                    <span>{grove.dialogueCount} dialogues</span>
                  </div>
                  
                  <div className="text-xs text-gray-400 mt-1">
                    Updated {new Date(grove.updatedAt).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content - Grove Details */}
      <div className="flex-1 flex flex-col">
        {!selectedGrove ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <TreePine className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Grove</h3>
              <p className="text-gray-500">Choose a grove from the sidebar to explore its branches</p>
            </div>
          </div>
        ) : (
          <>
            {/* Grove Header */}
            <div className="bg-white border-b border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{selectedGrove.name}</h1>
                  <p className="text-gray-600 mt-1">{selectedGrove.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    <Star className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    <Settings className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              {/* Grove Stats */}
              <div className="flex items-center space-x-6 mt-4 text-sm text-gray-600">
                <span>Branches: {selectedGrove.branchCount}</span>
                <span>Vessels: {selectedGrove.vesselCount}</span>
                <span>Dialogues: {selectedGrove.dialogueCount}</span>
                <span>Last accessed: {new Date(selectedGrove.lastAccessedAt).toLocaleDateString()}</span>
              </div>
            </div>

            {/* View Mode Toggle */}
            <div className="bg-gray-50 border-b border-gray-200 p-4">
              <div className="flex items-center space-x-4">
                <span className="text-sm font-medium text-gray-700">View:</span>
                <div className="flex space-x-1">
                  {['tree', 'list', 'grid'].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setViewMode(mode as any)}
                      className={`px-3 py-1 text-sm rounded-md capitalize ${
                        viewMode === mode
                          ? 'bg-primary-600 text-white'
                          : 'text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
                
                <div className="flex-1"></div>
                
                <button className="p-2 text-gray-600 hover:bg-white rounded-lg border border-gray-300">
                  <Filter className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Branch Explorer */}
            <div className="flex-1 overflow-auto p-6">
              {branchesLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                  <span className="ml-3 text-gray-600">Loading branches...</span>
                </div>
              ) : branches && branches.length > 0 ? (
                <div className="space-y-4">
                  {/* Tree View */}
                  {viewMode === 'tree' && (
                    <div className="tree-explorer">
                      {branches.map((branch) => (
                        <BranchTreeNode 
                          key={branch.id} 
                          branch={branch} 
                          depth={0} 
                        />
                      ))}
                    </div>
                  )}
                  
                  {/* List View */}
                  {viewMode === 'list' && (
                    <div className="space-y-2">
                      {branches.map((branch) => (
                        <div
                          key={branch.id}
                          className="p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium text-gray-900">{branch.name}</h4>
                              <p className="text-sm text-gray-500">{branch.description}</p>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                branch.status === 'active' ? 'bg-green-100 text-green-800' :
                                branch.status === 'archived' ? 'bg-gray-100 text-gray-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {branch.status}
                              </span>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                branch.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                branch.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                branch.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {branch.priority}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Grid View */}
                  {viewMode === 'grid' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {branches.map((branch) => (
                        <div
                          key={branch.id}
                          className="p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                        >
                          <h4 className="font-medium text-gray-900 mb-2">{branch.name}</h4>
                          <p className="text-sm text-gray-500 mb-3">{branch.description}</p>
                          <div className="flex items-center justify-between text-xs text-gray-600">
                            <span>Depth: {branch.depth}</span>
                            <span>{branch.status}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32">
                  <div className="text-center">
                    <TreePine className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-500">No branches found in this grove</p>
                    <button className="mt-2 text-primary-600 hover:text-primary-700 text-sm">
                      Create first branch
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// Recursive branch tree component
interface BranchTreeNodeProps {
  branch: Branch;
  depth: number;
}

const BranchTreeNode: React.FC<BranchTreeNodeProps> = ({ branch, depth }) => {
  const [isExpanded, setIsExpanded] = useState(depth < 2) // Auto-expand first two levels
  
  // In a real implementation, you would fetch child branches here
  const childBranches: Branch[] = [] // Mock data
  
  return (
    <div className="tree-node">
      <div 
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
        style={{ paddingLeft: `${depth * 24 + 12}px` }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="tree-connector w-4 flex items-center justify-center">
          {childBranches.length > 0 && (
            <button className="text-gray-400 hover:text-gray-600">
              {isExpanded ? '−' : '+'}
            </button>
          )}
        </div>
        
        <TreePine className="w-4 h-4 text-gray-400" />
        
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 truncate">{branch.name}</h4>
          {branch.description && (
            <p className="text-sm text-gray-500 truncate">{branch.description}</p>
          )}
        </div>
        
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <span className={`px-1 rounded ${
            branch.status === 'active' ? 'bg-green-100 text-green-800' :
            branch.status === 'archived' ? 'bg-gray-100 text-gray-800' :
            'bg-blue-100 text-blue-800'
          }`}>
            {branch.status}
          </span>
        </div>
      </div>
      
      {/* Child branches */}
      {isExpanded && childBranches.length > 0 && (
        <div className="space-y-1">
          {childBranches.map((child) => (
            <BranchTreeNode key={child.id} branch={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export default GroveExplorer