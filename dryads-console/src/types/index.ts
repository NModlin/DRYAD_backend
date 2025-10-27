// User and authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin' | 'agent';
  avatar?: string;
  lastLogin?: string;
  createdAt: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  role?: 'user' | 'admin' | 'agent';
}

// DRYAD API types
export interface Grove {
  id: string;
  name: string;
  description?: string;
  isFavorite: boolean;
  branchCount: number;
  vesselCount: number;
  dialogueCount: number;
  createdAt: string;
  updatedAt: string;
  lastAccessedAt: string;
}

export interface Branch {
  id: string;
  groveId: string;
  parentId?: string;
  name: string;
  description?: string;
  status: 'active' | 'archived' | 'completed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  depth: number;
  createdAt: string;
  updatedAt: string;
}

export interface Vessel {
  id: string;
  branchId: string;
  content: string;
  summary?: string;
  context?: Record<string, any>;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Dialogue {
  id: string;
  branchId: string;
  providerId: string;
  query: string;
  response: string;
  insights: string[];
  confidence: number;
  createdAt: string;
}

export interface OracleProvider {
  id: string;
  name: string;
  type: 'openai' | 'anthropic' | 'google' | 'local' | 'custom';
  model: string;
  status: 'available' | 'unavailable' | 'degraded';
  responseTime: number;
  costPerToken: number;
  capabilities: string[];
}

export interface ConsultationRequest {
  branchId: string;
  query: string;
  providerId?: string;
  context?: Record<string, any>;
  options?: {
    maxTokens?: number;
    temperature?: number;
    includeHistory?: boolean;
  };
}

export interface ConsultationResponse {
  id: string;
  branchId: string;
  providerId: string;
  query: string;
  response: string;
  insights: string[];
  confidence: number;
  tokensUsed: number;
  responseTime: number;
  cost: number;
  createdAt: string;
}

// Memory Keeper types
export type MemoryCategory = 'conversation' | 'knowledge' | 'preference' | 'behavior' | 'context' | 'insight';

export interface MemoryContext {
  id: string;
  agentId?: string;
  description: string;
  memoryCount: number;
  lastUpdated: string;
  importance: number;
  contextData: Record<string, any>;
  parentContextId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgentMemory {
  id: string;
  agentId: string;
  category: MemoryCategory;
  content: string;
  tags: string[];
  importance: number;
  confidence: number;
  createdAt: string;
  updatedAt: string;
}

export interface MemorySearchRequest {
  query: string;
  category?: MemoryCategory;
  limit?: number;
  includeContext?: boolean;
}

export interface MemoryUpdateRequest {
  memoryId: string;
  content: string;
  tags: string[];
}

export interface MemoryCreateRequest {
  content: string;
  category?: MemoryCategory;
  tags?: string[];
  agentId?: string;
}

// File management types
export interface FileRecord {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
  storage: 'local' | 'google_drive' | 'both';
  googleDriveId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FileUploadOptions {
  storage: 'local' | 'google_drive' | 'both';
  groveId?: string;
  branchId?: string;
  tags?: string[];
}

// Feature flag types
export interface FeatureFlag {
  name: string;
  description: string;
  enabled: boolean;
  rolloutPercentage: number;
  targetUsers?: string[];
  targetRoles?: string[];
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// WebSocket types
export interface WebSocketMessage {
  type: 'notification' | 'update' | 'error' | 'progress';
  data: any;
  timestamp: string;
}

// University system integration types
export interface UniversityAgent {
  id: string;
  name: string;
  role: 'student' | 'professor' | 'researcher' | 'memory_keeper';
  specialization: string;
  capabilities: string[];
  currentTask?: string;
  status: 'available' | 'busy' | 'offline';
}

export interface AgentCompetition {
  id: string;
  title: string;
  description: string;
  participants: UniversityAgent[];
  rules: Record<string, any>;
  status: 'pending' | 'active' | 'completed';
  results?: Record<string, any>;
}

// Chat Interface Types
export interface ChatMessage {
  id: string;
  type: 'user' | 'system' | 'agent' | 'error';
  content: string;
  timestamp: string;
  sender: string;
  context?: Record<string, any>;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
  context?: Record<string, any>;
}

export interface CommandSuggestion {
  id: string;
  command: string;
  description: string;
  icon: any; // Lucide icon component
  action: () => void;
}

export interface Agent {
  id: string;
  name: string;
  type: 'memory_keeper' | 'professor' | 'researcher' | 'assistant';
  status: 'available' | 'busy' | 'offline';
  capabilities: string[];
  currentTask?: string;
}