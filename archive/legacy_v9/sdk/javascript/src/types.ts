/**
 * DRYAD.AI JavaScript/TypeScript SDK Types
 * 
 * Type definitions for the DRYAD.AI platform API.
 */

// Base types
export interface BaseResponse {
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> extends BaseResponse {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Core model types
export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Document {
  id: string;
  filename: string;
  content_type: string;
  size: number;
  upload_date: string;
  processed: boolean;
  metadata?: Record<string, any>;
}

export interface Agent {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
  status: 'active' | 'inactive';
  created_at: string;
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  result?: any;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: Record<string, string>;
  version?: string;
  uptime?: number;
}

export interface MultiAgentWorkflow {
  id: string;
  name: string;
  description?: string;
  agents: string[];
  workflow_type: 'sequential' | 'parallel' | 'conditional';
  status: 'active' | 'inactive';
  created_at: string;
}

export interface VectorSearchResult {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
  document_id?: string;
}

export interface MultiModalContent {
  id: string;
  media_type: 'image' | 'audio' | 'video' | 'document';
  filename: string;
  content_type: string;
  size: number;
  processed: boolean;
  analysis_results?: Record<string, any>;
  created_at: string;
}

// Request types
export interface InvokeAgentRequest {
  input: string;
  conversation_id?: string;
  save_conversation?: boolean;
  context?: Record<string, any>;
  max_tokens?: number;
  temperature?: number;
}

export interface InvokeAgentResponse extends BaseResponse {
  output: string;
  conversation_id?: string;
  execution_time: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  metadata?: Record<string, any>;
}

export interface CreateConversationRequest {
  title?: string;
  metadata?: Record<string, any>;
}

export interface ListConversationsRequest {
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: 'created_at' | 'updated_at' | 'title';
  sort_order?: 'asc' | 'desc';
}

export interface UploadDocumentRequest {
  file: File | Buffer | Blob;
  filename: string;
  processForRAG?: boolean;
  metadata?: Record<string, any>;
}

export interface QueryWithRAGRequest {
  query: string;
  document_ids?: string[];
  max_results?: number;
  similarity_threshold?: number;
  include_metadata?: boolean;
}

export interface QueryWithRAGResponse extends BaseResponse {
  answer: string;
  sources?: Array<{
    document_id: string;
    filename: string;
    relevance_score: number;
    excerpt: string;
    metadata?: Record<string, any>;
  }>;
  query_metadata?: Record<string, any>;
}

export interface ExecuteMultiAgentWorkflowRequest {
  task: string;
  agents?: string[];
  workflow_type?: 'sequential' | 'parallel' | 'conditional';
  context?: Record<string, any>;
  max_iterations?: number;
}

export interface ExecuteMultiAgentWorkflowResponse extends BaseResponse {
  final_output: string;
  agent_interactions: Array<{
    agent_id: string;
    input: string;
    output: string;
    execution_time: number;
    metadata?: Record<string, any>;
  }>;
  total_execution_time: number;
  workflow_metadata?: Record<string, any>;
}

export interface VectorSearchRequest {
  query: string;
  limit?: number;
  similarity_threshold?: number;
  filter?: Record<string, any>;
  include_metadata?: boolean;
}

export interface VectorSearchResponse extends BaseResponse {
  results: VectorSearchResult[];
  query_metadata?: Record<string, any>;
}

export interface UploadMultiModalRequest {
  file: File | Buffer | Blob;
  filename: string;
  media_type: 'image' | 'audio' | 'video' | 'document';
  process_content?: boolean;
  extract_text?: boolean;
  metadata?: Record<string, any>;
}

export interface AnalyzeMultiModalRequest {
  content_id: string;
  analysis_type: 'transcription' | 'object_detection' | 'text_extraction' | 'sentiment_analysis';
  options?: Record<string, any>;
}

export interface AnalyzeMultiModalResponse extends BaseResponse {
  content_id: string;
  analysis_type: string;
  results: Record<string, any>;
  confidence_score?: number;
  processing_time: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  id?: string;
}

export interface ChatMessage extends WebSocketMessage {
  type: 'chat';
  data: {
    content: string;
    conversation_id?: string;
    metadata?: Record<string, any>;
  };
}

export interface StatusMessage extends WebSocketMessage {
  type: 'status';
  data: {
    status: string;
    message?: string;
    details?: Record<string, any>;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  data: {
    error: string;
    code?: string;
    details?: Record<string, any>;
  };
}

// Configuration types
export interface ClientConfig {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
  maxRetryDelay?: number;
  userAgent?: string;
  headers?: Record<string, string>;
}

export interface WebSocketConfig {
  url?: string;
  protocols?: string[];
  headers?: Record<string, string>;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

// Utility types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export type MediaType = 'image' | 'audio' | 'video' | 'document';

export type AgentRole = 'user' | 'assistant' | 'system';

export type WorkflowType = 'sequential' | 'parallel' | 'conditional';

export type SortOrder = 'asc' | 'desc';

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

// Event types for WebSocket
export interface WebSocketEvents {
  connected: () => void;
  disconnected: (event: { code: number; reason: string }) => void;
  message: (message: WebSocketMessage) => void;
  error: (error: Error) => void;
  reconnecting: (attempt: number) => void;
  reconnectFailed: () => void;
}

// Export all types
export * from './exceptions';
