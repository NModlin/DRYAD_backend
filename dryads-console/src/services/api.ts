import axios, { AxiosInstance, AxiosResponse } from 'axios'
import {
  User,
  Grove,
  Branch,
  Vessel,
  Dialogue,
  OracleProvider,
  ConsultationRequest,
  ConsultationResponse,
  MemoryContext,
  AgentMemory,
  MemorySearchRequest,
  MemoryUpdateRequest,
  MemoryCreateRequest,
  FileRecord,
  FeatureFlag,
  ChatMessage,
  ChatSession,
  Agent,
  ApiResponse,
  PaginatedResponse,
  LoginCredentials,
  RegisterData
} from '../types'

class DryadAPI {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('dryad_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Handle token expiration
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('dryad_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Authentication endpoints
  async login(credentials: LoginCredentials): Promise<{ user: User; token: string }> {
    const response: AxiosResponse<ApiResponse<{ user: User; token: string }>> = 
      await this.client.post('/auth/login', credentials)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Login failed')
    }
    
    return response.data.data!
  }

  async register(data: RegisterData): Promise<{ user: User; token: string }> {
    const response: AxiosResponse<ApiResponse<{ user: User; token: string }>> = 
      await this.client.post('/auth/register', data)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Registration failed')
    }
    
    return response.data.data!
  }

  async verifyToken(token: string): Promise<User> {
    const response: AxiosResponse<ApiResponse<User>> = 
      await this.client.get('/auth/verify', {
        headers: { Authorization: `Bearer ${token}` }
      })
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Token verification failed')
    }
    
    return response.data.data!
  }

  async refreshToken(token: string): Promise<{ user: User; token: string }> {
    const response: AxiosResponse<ApiResponse<{ user: User; token: string }>> = 
      await this.client.post('/auth/refresh', { token })
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Token refresh failed')
    }
    
    return response.data.data!
  }

  // Grove endpoints
  async listGroves(): Promise<PaginatedResponse<Grove>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<Grove>>> = 
      await this.client.get('/dryad/groves')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch groves')
    }
    
    return response.data.data!
  }

  async createGrove(data: Partial<Grove>): Promise<Grove> {
    const response: AxiosResponse<ApiResponse<Grove>> = 
      await this.client.post('/dryad/groves', data)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to create grove')
    }
    
    return response.data.data!
  }

  async getGrove(id: string): Promise<Grove> {
    const response: AxiosResponse<ApiResponse<Grove>> = 
      await this.client.get(`/dryad/groves/${id}`)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch grove')
    }
    
    return response.data.data!
  }

  // Branch endpoints
  async listBranches(groveId: string): Promise<PaginatedResponse<Branch>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<Branch>>> = 
      await this.client.get(`/dryad/groves/${groveId}/branches`)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch branches')
    }
    
    return response.data.data!
  }

  async getBranchTree(groveId: string): Promise<Branch[]> {
    const response: AxiosResponse<ApiResponse<Branch[]>> = 
      await this.client.get(`/dryad/groves/${groveId}/tree`)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch branch tree')
    }
    
    return response.data.data!
  }

  // Oracle endpoints
  async listProviders(): Promise<OracleProvider[]> {
    const response: AxiosResponse<ApiResponse<OracleProvider[]>> = 
      await this.client.get('/dryad/oracle/providers')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch providers')
    }
    
    return response.data.data!
  }

  async consultOracle(request: ConsultationRequest): Promise<ConsultationResponse> {
    const response: AxiosResponse<ApiResponse<ConsultationResponse>> = 
      await this.client.post('/dryad/oracle/consult', request)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Oracle consultation failed')
    }
    
    return response.data.data!
  }

  async multiConsult(request: ConsultationRequest): Promise<ConsultationResponse[]> {
    const response: AxiosResponse<ApiResponse<ConsultationResponse[]>> = 
      await this.client.post('/dryad/oracle/multi-consult', request)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Multi-provider consultation failed')
    }
    
    return response.data.data!
  }

  // Memory endpoints
  async listMemoryContexts(): Promise<PaginatedResponse<MemoryContext>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<MemoryContext>>> =
      await this.client.get('/memory/contexts')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch memory contexts')
    }
    
    return response.data.data!
  }

  async listAgentMemories(params?: { category?: string }): Promise<PaginatedResponse<AgentMemory>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<AgentMemory>>> =
      await this.client.get('/memory/agent-memories', { params })
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch agent memories')
    }
    
    return response.data.data!
  }

  async searchMemories(request: MemorySearchRequest): Promise<PaginatedResponse<AgentMemory>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<AgentMemory>>> =
      await this.client.post('/memory/search', request)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Memory search failed')
    }
    
    return response.data.data!
  }

  async createMemory(request: MemoryCreateRequest): Promise<AgentMemory> {
    const response: AxiosResponse<ApiResponse<AgentMemory>> =
      await this.client.post('/memory', request)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to create memory')
    }
    
    return response.data.data!
  }

  async updateMemory(request: MemoryUpdateRequest): Promise<AgentMemory> {
    const response: AxiosResponse<ApiResponse<AgentMemory>> =
      await this.client.put(`/memory/${request.memoryId}`, request)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to update memory')
    }
    
    return response.data.data!
  }

  async deleteMemory(memoryId: string): Promise<void> {
    const response: AxiosResponse<ApiResponse<void>> =
      await this.client.delete(`/memory/${memoryId}`)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to delete memory')
    }
  }

  // File management endpoints
  async listFiles(groveId?: string): Promise<FileRecord[]> {
    const params = groveId ? { grove_id: groveId } : {}
    const response: AxiosResponse<ApiResponse<FileRecord[]>> = 
      await this.client.get('/files', { params })
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch files')
    }
    
    return response.data.data!
  }

  async uploadFile(file: File, options: any): Promise<FileRecord> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('options', JSON.stringify(options))

    const response: AxiosResponse<ApiResponse<FileRecord>> = 
      await this.client.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'File upload failed')
    }
    
    return response.data.data!
  }

  // Feature flags
  async getFeatureFlags(): Promise<FeatureFlag[]> {
    const response: AxiosResponse<ApiResponse<FeatureFlag[]>> = 
      await this.client.get('/features')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch feature flags')
    }
    
    return response.data.data!
  }

  // Agent endpoints
  async listAgents(): Promise<PaginatedResponse<Agent>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<Agent>>> =
      await this.client.get('/agents')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch agents')
    }
    
    return response.data.data!
  }

  // Chat endpoints
  async sendChatMessage(message: { content: string; context?: any }): Promise<ChatMessage> {
    const response: AxiosResponse<ApiResponse<ChatMessage>> =
      await this.client.post('/chat/messages', message)
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to send message')
    }
    
    return response.data.data!
  }

  async getChatSessions(): Promise<PaginatedResponse<ChatSession>> {
    const response: AxiosResponse<ApiResponse<PaginatedResponse<ChatSession>>> =
      await this.client.get('/chat/sessions')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch chat sessions')
    }
    
    return response.data.data!
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response: AxiosResponse<ApiResponse<{ status: string; version: string }>> =
      await this.client.get('/health')
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Health check failed')
    }
    
    return response.data.data!
  }
}

export const authAPI = new DryadAPI()
export const dryadAPI = new DryadAPI()
export default DryadAPI