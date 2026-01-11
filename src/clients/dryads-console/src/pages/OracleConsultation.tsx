import React, { useState, useEffect } from 'react'
import { useQuery, useMutation } from 'react-query'
import { 
  Brain, 
  Send, 
  Settings, 
  Zap, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Users,
  BarChart3
} from 'lucide-react'
import { 
  OracleProvider, 
  ConsultationRequest, 
  ConsultationResponse,
  Grove,
  Branch
} from '../types'
import { dryadAPI } from '../services/api'

const OracleConsultation: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState<OracleProvider | null>(null)
  const [selectedGrove, setSelectedGrove] = useState<Grove | null>(null)
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null)
  const [query, setQuery] = useState('')
  const [consultationHistory, setConsultationHistory] = useState<ConsultationResponse[]>([])
  const [isMultiConsult, setIsMultiConsult] = useState(false)

  // Fetch available providers
  const { data: providers, isLoading: providersLoading } = useQuery(
    'oracle-providers',
    () => dryadAPI.listProviders(),
    {
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  )

  // Fetch user's groves
  const { data: groves, isLoading: grovesLoading } = useQuery(
    'user-groves',
    () => dryadAPI.listGroves(),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
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

  // Consultation mutation
  const consultationMutation = useMutation(
    (request: ConsultationRequest) => dryadAPI.consultOracle(request),
    {
      onSuccess: (response) => {
        setConsultationHistory(prev => [response, ...prev])
        setQuery('') // Clear query after successful consultation
      },
    }
  )

  // Multi-consultation mutation
  const multiConsultMutation = useMutation(
    (request: ConsultationRequest) => dryadAPI.multiConsult(request),
    {
      onSuccess: (responses) => {
        setConsultationHistory(prev => [...responses, ...prev])
        setQuery('')
      },
    }
  )

  // Auto-select first provider if available
  useEffect(() => {
    if (providers && providers.length > 0 && !selectedProvider) {
      setSelectedProvider(providers[0])
    }
  }, [providers, selectedProvider])

  // Auto-select first grove if available
  useEffect(() => {
    if (groves && groves.items && groves.items.length > 0 && !selectedGrove) {
      setSelectedGrove(groves.items[0])
    }
  }, [groves, selectedGrove])

  const handleConsult = async () => {
    if (!query.trim() || !selectedGrove || !selectedBranch) return

    const request: ConsultationRequest = {
      branchId: selectedBranch.id,
      query: query.trim(),
      providerId: isMultiConsult ? undefined : selectedProvider?.id,
      options: {
        maxTokens: 1000,
        temperature: 0.7,
        includeHistory: true,
      },
    }

    if (isMultiConsult) {
      multiConsultMutation.mutate(request)
    } else {
      consultationMutation.mutate(request)
    }
  }

  const isLoading = consultationMutation.isLoading || multiConsultMutation.isLoading

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-8 h-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Oracle Consultation</h1>
              <p className="text-gray-600">Consult AI providers for guidance and insights</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsMultiConsult(!isMultiConsult)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                isMultiConsult
                  ? 'bg-purple-100 border-purple-300 text-purple-700'
                  : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Multi-Provider</span>
            </button>
            <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Configuration */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Provider Selection */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">AI Provider</h3>
            {providersLoading ? (
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
                {providers?.map((provider) => (
                  <div
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedProvider?.id === provider.id
                        ? 'bg-purple-50 border-l-4 border-purple-600'
                        : 'hover:bg-gray-50 border-l-4 border-transparent'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">{provider.name}</h4>
                        <p className="text-sm text-gray-500">{provider.model}</p>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${
                        provider.status === 'available' ? 'bg-green-500' :
                        provider.status === 'unavailable' ? 'bg-red-500' :
                        'bg-yellow-500'
                      }`}></div>
                    </div>
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                      <span>{provider.responseTime}ms</span>
                      <span>${provider.costPerToken}/token</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Grove and Branch Selection */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">Knowledge Context</h3>
            
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
                <option value="">Select a branch</option>
                {branches?.items?.map((branch) => (
                  <option key={branch.id} value={branch.id}>{branch.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Provider Stats */}
          {selectedProvider && (
            <div className="p-4">
              <h3 className="font-medium text-gray-900 mb-3">Provider Capabilities</h3>
              <div className="space-y-2">
                {selectedProvider.capabilities.map((capability, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>{capability}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Query Input */}
          <div className="bg-white border-b border-gray-200 p-6">
            <div className="relative">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask the oracle for guidance, insights, or analysis..."
                className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                disabled={isLoading}
              />
              <div className="absolute bottom-4 right-4 flex items-center space-x-3">
                <span className="text-sm text-gray-500">
                  {query.length}/4000
                </span>
                <button
                  onClick={handleConsult}
                  disabled={!query.trim() || !selectedGrove || !selectedBranch || isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : isMultiConsult ? (
                    <Users className="w-4 h-4" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  <span>
                    {isLoading ? 'Consulting...' : 
                     isMultiConsult ? 'Multi-Consult' : 'Consult'}
                  </span>
                </button>
              </div>
            </div>
          </div>

          {/* Consultation Results */}
          <div className="flex-1 overflow-auto p-6">
            {consultationHistory.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Consultations Yet</h3>
                  <p className="text-gray-500">
                    Ask a question to see oracle responses here
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {consultationHistory.map((consultation) => (
                  <div
                    key={consultation.id}
                    className="bg-white rounded-lg shadow-soft border border-gray-200 overflow-hidden"
                  >
                    {/* Consultation Header */}
                    <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Zap className="w-4 h-4 text-purple-600" />
                          <span className="font-medium text-gray-900">
                            {consultation.providerId}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{consultation.responseTime}ms</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <BarChart3 className="w-3 h-3" />
                            <span>{consultation.tokensUsed} tokens</span>
                          </div>
                          <span>${consultation.cost.toFixed(4)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Query */}
                    <div className="px-6 py-4 border-b border-gray-100">
                      <h4 className="font-medium text-gray-900 mb-2">Query</h4>
                      <p className="text-gray-700">{consultation.query}</p>
                    </div>

                    {/* Response */}
                    <div className="px-6 py-4">
                      <h4 className="font-medium text-gray-900 mb-3">Response</h4>
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-700 whitespace-pre-wrap">
                          {consultation.response}
                        </p>
                      </div>
                    </div>

                    {/* Insights */}
                    {consultation.insights.length > 0 && (
                      <div className="px-6 py-4 bg-purple-50 border-t border-gray-100">
                        <h4 className="font-medium text-gray-900 mb-2">Key Insights</h4>
                        <ul className="space-y-1">
                          {consultation.insights.map((insight, index) => (
                            <li key={index} className="flex items-start space-x-2 text-sm text-gray-700">
                              <CheckCircle className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                              <span>{insight}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Confidence */}
                    <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Confidence</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${consultation.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-medium text-gray-900">
                            {(consultation.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
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

export default OracleConsultation