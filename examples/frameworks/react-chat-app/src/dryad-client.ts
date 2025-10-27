/**
 * Dryad.AI API Client for React Chat Interface
 * 
 * This client replaces the GremlinsAI SDK with direct API calls to Dryad backend.
 */

import axios from 'axios';

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tool_calls?: any;
  extra_data?: any;
}

export interface AgentConversationRequest {
  input: string;
  conversation_id?: string;
  save_conversation?: boolean;
  use_multi_agent?: boolean;
}

export interface AgentConversationResponse {
  output: string;
  conversation_id?: string;
  message_id?: string;
  context_used: boolean;
  execution_time?: number;
}

export interface SystemAgent {
  id: string;
  agent_id: string;
  name: string;
  display_name: string;
  tier: 'orchestrator' | 'specialist' | 'execution';
  category: string;
  capabilities: string[];
  description?: string;
  status: 'active' | 'inactive' | 'maintenance' | 'error';
}

export class DryadAIClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(config: { baseUrl: string; apiKey?: string }) {
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;
  }

  /**
   * Test connection to Dryad backend
   */
  async getSystemHealth(): Promise<any> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/health/`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to connect to Dryad.AI: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Create a new conversation
   */
  async createConversation(title: string): Promise<Conversation> {
    try {
      const response = await axios.post(`${this.baseUrl}/api/v1/chat-history/conversations`, {
        title,
        initial_message: null
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create conversation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Invoke agent with conversation context
   */
  async invokeAgent(request: AgentConversationRequest): Promise<AgentConversationResponse> {
    try {
      const response = await axios.post(`${this.baseUrl}/api/v1/agent/chat`, request, {
        params: {
          use_multi_agent: request.use_multi_agent || false
        }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to invoke agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get list of available agents
   */
  async getAgents(): Promise<SystemAgent[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/agent-registry/agents`);
      return response.data;
    } catch (error) {
      console.warn('Failed to fetch agents, returning empty list:', error);
      return [];
    }
  }

  /**
   * Get conversation messages
   */
  async getConversationMessages(conversationId: string, limit: number = 100): Promise<Message[]> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/v1/chat-history/conversations/${conversationId}/messages`,
        { params: { limit } }
      );
      return response.data.messages || [];
    } catch (error) {
      throw new Error(`Failed to get conversation messages: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get conversation context for AI agents
   */
  async getConversationContext(conversationId: string, maxMessages: number = 20): Promise<any> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/v1/chat-history/conversations/${conversationId}/context`,
        { params: { max_messages: maxMessages } }
      );
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get conversation context: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get list of conversations
   */
  async getConversations(limit: number = 50, offset: number = 0): Promise<Conversation[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/chat-history/conversations`, {
        params: { limit, offset, active_only: true }
      });
      return response.data.conversations || [];
    } catch (error) {
      throw new Error(`Failed to get conversations: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Simple agent invocation (backward compatibility)
   */
  async invokeAgentSimple(input: string): Promise<{ output: string; execution_time: number }> {
    try {
      const response = await axios.post(`${this.baseUrl}/api/v1/agent/invoke`, { input });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to invoke simple agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

export default DryadAIClient;