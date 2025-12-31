/**
 * DRYAD.AI JavaScript/TypeScript SDK Client
 * 
 * Main client class for interacting with the DRYAD.AI API.
 * Supports REST, GraphQL, and WebSocket APIs with automatic error handling,
 * retry logic, and connection management.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import WebSocket from 'ws';
import FormData from 'form-data';
import { EventEmitter } from 'eventemitter3';

import {
  DRYAD.AIError,
  APIError,
  ValidationError,
  RateLimitError,
  AuthenticationError,
  ConnectionError,
  TimeoutError,
} from './exceptions';

import {
  Conversation,
  Message,
  Document,
  Agent,
  Task,
  SystemHealth,
  MultiAgentWorkflow,
  VectorSearchResult,
  MultiModalContent,
  InvokeAgentRequest,
  InvokeAgentResponse,
  CreateConversationRequest,
  ListConversationsRequest,
  UploadDocumentRequest,
  QueryWithRAGRequest,
  QueryWithRAGResponse,
  ExecuteMultiAgentWorkflowRequest,
  ExecuteMultiAgentWorkflowResponse,
} from './types';

export interface DRYAD.AIClientConfig {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
  maxRetryDelay?: number;
  userAgent?: string;
}

export class DRYAD.AIClient extends EventEmitter {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly retryDelay: number;
  private readonly maxRetryDelay: number;
  private readonly httpClient: AxiosInstance;

  constructor(config: DRYAD.AIClientConfig = {}) {
    super();

    this.baseUrl = config.baseUrl?.replace(/\/$/, '') || 'http://localhost:8000';
    this.apiKey = config.apiKey || process.env.GREMLINS_AI_API_KEY;
    this.timeout = config.timeout || 30000;
    this.maxRetries = config.maxRetries || 3;
    this.retryDelay = config.retryDelay || 1000;
    this.maxRetryDelay = config.maxRetryDelay || 60000;

    // Create HTTP client
    this.httpClient = axios.create({
      baseURL: this.baseUrl,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': config.userAgent || `gremlins-ai-js-sdk/1.0.0-beta.1`,
        ...(this.apiKey && { Authorization: `Bearer ${this.apiKey}` }),
      },
    });

    // Add response interceptor for error handling
    this.httpClient.interceptors.response.use(
      (response) => response,
      (error) => this.handleHttpError(error)
    );
  }

  /**
   * Handle HTTP errors and convert to appropriate DRYAD.AI exceptions
   */
  private handleHttpError(error: any): never {
    if (error.response) {
      const { status, data } = error.response;
      const message = data?.message || data?.error || error.message;

      switch (status) {
        case 400:
          throw new ValidationError(message, status);
        case 401:
          throw new AuthenticationError(message, status);
        case 429:
          const retryAfter = parseInt(error.response.headers['retry-after']) || 60;
          throw new RateLimitError(message, status, retryAfter);
        case 500:
        case 502:
        case 503:
        case 504:
          throw new APIError(message, status);
        default:
          throw new APIError(message, status);
      }
    } else if (error.code === 'ECONNABORTED') {
      throw new TimeoutError('Request timed out');
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      throw new ConnectionError(`Connection failed: ${error.message}`);
    } else {
      throw new DRYAD.AIError(error.message);
    }
  }

  /**
   * Make HTTP request with retry logic
   */
  private async makeRequest<T>(
    method: string,
    endpoint: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    let lastError: Error;
    let delay = this.retryDelay;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response: AxiosResponse<T> = await this.httpClient.request({
          method,
          url: endpoint,
          data,
          ...config,
        });

        return response.data;
      } catch (error) {
        lastError = error as Error;

        // Don't retry on certain errors
        if (
          error instanceof AuthenticationError ||
          error instanceof ValidationError ||
          attempt === this.maxRetries
        ) {
          throw error;
        }

        // Wait before retry
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(delay * 2, this.maxRetryDelay);
      }
    }

    throw lastError!;
  }

  /**
   * Invoke the AI agent with a message
   */
  async invokeAgent(request: InvokeAgentRequest): Promise<InvokeAgentResponse>;
  async invokeAgent(
    input: string,
    conversationId?: string,
    saveConversation?: boolean
  ): Promise<InvokeAgentResponse>;
  async invokeAgent(
    requestOrInput: InvokeAgentRequest | string,
    conversationId?: string,
    saveConversation?: boolean
  ): Promise<InvokeAgentResponse> {
    const request: InvokeAgentRequest =
      typeof requestOrInput === 'string'
        ? {
            input: requestOrInput,
            conversation_id: conversationId,
            save_conversation: saveConversation,
          }
        : requestOrInput;

    return this.makeRequest<InvokeAgentResponse>('POST', '/api/v1/agent/invoke', request);
  }

  /**
   * Create a new conversation
   */
  async createConversation(request: CreateConversationRequest): Promise<Conversation>;
  async createConversation(title?: string): Promise<Conversation>;
  async createConversation(
    requestOrTitle?: CreateConversationRequest | string
  ): Promise<Conversation> {
    const request: CreateConversationRequest =
      typeof requestOrTitle === 'string' ? { title: requestOrTitle } : requestOrTitle || {};

    return this.makeRequest<Conversation>('POST', '/api/v1/conversations', request);
  }

  /**
   * List conversations
   */
  async listConversations(request: ListConversationsRequest = {}): Promise<Conversation[]> {
    const params = new URLSearchParams();
    if (request.limit) params.append('limit', request.limit.toString());
    if (request.offset) params.append('offset', request.offset.toString());
    if (request.search) params.append('search', request.search);

    const queryString = params.toString();
    const endpoint = `/api/v1/conversations${queryString ? `?${queryString}` : ''}`;

    return this.makeRequest<Conversation[]>('GET', endpoint);
  }

  /**
   * Get a specific conversation
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    return this.makeRequest<Conversation>('GET', `/api/v1/conversations/${conversationId}`);
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await this.makeRequest<void>('DELETE', `/api/v1/conversations/${conversationId}`);
  }

  /**
   * Upload a document
   */
  async uploadDocument(request: UploadDocumentRequest): Promise<Document> {
    const formData = new FormData();
    formData.append('file', request.file, request.filename);
    if (request.processForRAG) formData.append('process_for_rag', 'true');
    if (request.metadata) formData.append('metadata', JSON.stringify(request.metadata));

    return this.makeRequest<Document>('POST', '/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  /**
   * Query with RAG (Retrieval-Augmented Generation)
   */
  async queryWithRAG(request: QueryWithRAGRequest): Promise<QueryWithRAGResponse> {
    return this.makeRequest<QueryWithRAGResponse>('POST', '/api/v1/rag/query', request);
  }

  /**
   * Execute multi-agent workflow
   */
  async executeMultiAgentWorkflow(
    request: ExecuteMultiAgentWorkflowRequest
  ): Promise<ExecuteMultiAgentWorkflowResponse> {
    return this.makeRequest<ExecuteMultiAgentWorkflowResponse>(
      'POST',
      '/api/v1/multi-agent/execute',
      request
    );
  }

  /**
   * Get system health
   */
  async getSystemHealth(): Promise<SystemHealth> {
    return this.makeRequest<SystemHealth>('GET', '/api/v1/health');
  }

  /**
   * Connect to real-time WebSocket endpoint
   */
  connectRealtime(endpoint: string = '/ws'): DRYAD.AIWebSocket {
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + endpoint;
    const headers: Record<string, string> = {};
    
    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }

    return new DRYAD.AIWebSocket(wsUrl, { headers });
  }

  /**
   * Close the client and clean up resources
   */
  async close(): Promise<void> {
    // Clean up any resources if needed
    this.removeAllListeners();
  }
}

/**
 * WebSocket wrapper for real-time communication
 */
export class DRYAD.AIWebSocket extends EventEmitter {
  private ws: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(url: string, options?: WebSocket.ClientOptions) {
    super();
    this.ws = new WebSocket(url, options);
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.ws.on('open', () => {
      this.reconnectAttempts = 0;
      this.emit('connected');
    });

    this.ws.on('message', (data: WebSocket.Data) => {
      try {
        const message = JSON.parse(data.toString());
        this.emit('message', message);
      } catch (error) {
        this.emit('error', new Error('Failed to parse WebSocket message'));
      }
    });

    this.ws.on('close', (code: number, reason: Buffer) => {
      this.emit('disconnected', { code, reason: reason.toString() });
      this.attemptReconnect();
    });

    this.ws.on('error', (error: Error) => {
      this.emit('error', error);
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.emit('reconnecting', this.reconnectAttempts);
        // Reconnection logic would go here
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      this.emit('reconnectFailed');
    }
  }

  /**
   * Send a message through the WebSocket
   */
  send(message: any): void {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  /**
   * Close the WebSocket connection
   */
  close(): void {
    this.ws.close();
    this.removeAllListeners();
  }

  /**
   * Get the current connection state
   */
  get readyState(): number {
    return this.ws.readyState;
  }

  /**
   * Check if the WebSocket is connected
   */
  get isConnected(): boolean {
    return this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * Create a DRYAD.AI client with default configuration
 */
export function createClient(config?: DRYAD.AIClientConfig): DRYAD.AIClient {
  return new DRYAD.AIClient(config);
}
