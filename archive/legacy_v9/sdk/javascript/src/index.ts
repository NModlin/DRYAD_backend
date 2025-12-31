/**
 * DRYAD.AI JavaScript/TypeScript SDK
 * 
 * The official JavaScript/TypeScript SDK for the DRYAD.AI platform.
 * 
 * @example
 * ```typescript
 * import { DRYAD.AIClient } from '@gremlins-ai/sdk';
 * 
 * const client = new DRYAD.AIClient({
 *   baseUrl: 'http://localhost:8000',
 *   apiKey: 'your-api-key'
 * });
 * 
 * const response = await client.invokeAgent('Hello, AI!');
 * console.log(response.output);
 * ```
 */

// Main client exports
export { DRYAD.AIClient, DRYAD.AIWebSocket, createClient } from './client';

// Type exports
export type {
  // Core types
  Conversation,
  Message,
  Document,
  Agent,
  Task,
  SystemHealth,
  MultiAgentWorkflow,
  VectorSearchResult,
  MultiModalContent,
  
  // Request/Response types
  InvokeAgentRequest,
  InvokeAgentResponse,
  CreateConversationRequest,
  ListConversationsRequest,
  UploadDocumentRequest,
  QueryWithRAGRequest,
  QueryWithRAGResponse,
  ExecuteMultiAgentWorkflowRequest,
  ExecuteMultiAgentWorkflowResponse,
  VectorSearchRequest,
  VectorSearchResponse,
  UploadMultiModalRequest,
  AnalyzeMultiModalRequest,
  AnalyzeMultiModalResponse,
  
  // WebSocket types
  WebSocketMessage,
  ChatMessage,
  StatusMessage,
  ErrorMessage,
  WebSocketEvents,
  
  // Configuration types
  ClientConfig,
  WebSocketConfig,
  
  // Utility types
  HttpMethod,
  MediaType,
  AgentRole,
  WorkflowType,
  SortOrder,
  HealthStatus,
  TaskStatus,
  
  // Base types
  BaseResponse,
  PaginatedResponse,
} from './types';

// Exception exports
export {
  DRYAD.AIError,
  APIError,
  ValidationError,
  AuthenticationError,
  RateLimitError,
  ConnectionError,
  TimeoutError,
  WebSocketError,
  ConfigurationError,
  FileUploadError,
  createErrorFromResponse,
  isRetryableError,
  getRetryDelay,
} from './exceptions';

// Version information
export const VERSION = '1.0.0-beta.1';
export const USER_AGENT = `gremlins-ai-js-sdk/${VERSION}`;

// Default configuration
export const DEFAULT_CONFIG = {
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  maxRetries: 3,
  retryDelay: 1000,
  maxRetryDelay: 60000,
  userAgent: USER_AGENT,
} as const;

// Utility functions
export const utils = {
  /**
   * Check if the current environment is Node.js
   */
  isNode: (): boolean => {
    return typeof process !== 'undefined' && process.versions && process.versions.node;
  },

  /**
   * Check if the current environment is a browser
   */
  isBrowser: (): boolean => {
    return typeof window !== 'undefined' && typeof window.document !== 'undefined';
  },

  /**
   * Get the appropriate WebSocket implementation for the current environment
   */
  getWebSocketImplementation: (): any => {
    if (utils.isNode()) {
      try {
        return require('ws');
      } catch (error) {
        throw new Error('WebSocket implementation not found. Please install the "ws" package for Node.js.');
      }
    } else if (utils.isBrowser()) {
      return WebSocket;
    } else {
      throw new Error('WebSocket implementation not available in this environment.');
    }
  },

  /**
   * Format file size in human-readable format
   */
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  /**
   * Validate API key format
   */
  validateApiKey: (apiKey: string): boolean => {
    return typeof apiKey === 'string' && apiKey.length > 0;
  },

  /**
   * Validate URL format
   */
  validateUrl: (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Sleep for a specified number of milliseconds
   */
  sleep: (ms: number): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /**
   * Create a timeout promise that rejects after the specified time
   */
  timeout: <T>(promise: Promise<T>, ms: number): Promise<T> => {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error(`Operation timed out after ${ms}ms`)), ms)
      )
    ]);
  },
};

// Re-export everything for convenience
export default {
  DRYAD.AIClient,
  DRYAD.AIWebSocket,
  createClient,
  DRYAD.AIError,
  APIError,
  ValidationError,
  AuthenticationError,
  RateLimitError,
  ConnectionError,
  TimeoutError,
  WebSocketError,
  ConfigurationError,
  FileUploadError,
  VERSION,
  USER_AGENT,
  DEFAULT_CONFIG,
  utils,
};
