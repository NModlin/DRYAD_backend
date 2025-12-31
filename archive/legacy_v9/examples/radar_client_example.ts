/**
 * RADAR Client Example
 * 
 * Example TypeScript/JavaScript code showing how to integrate with Dryad.AI backend
 * from the RADAR Dryad Adapter (Port 3003).
 */

import axios, { AxiosInstance } from 'axios';

// Configuration
const DRYAD_API_URL = process.env.DRYAD_API_URL || 'http://localhost:8000';
const DRYAD_API_BASE = `${DRYAD_API_URL}/api/v1/radar`;

/**
 * Dryad.AI Client for RADAR Integration
 */
export class DryadClient {
  private client: AxiosInstance;

  constructor(apiUrl: string = DRYAD_API_BASE) {
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Set authentication token for requests
   */
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Health check - verify Dryad.AI backend is available
   */
  async healthCheck(): Promise<{
    status: string;
    database: string;
    dryad: string;
    llm?: string;
    timestamp: string;
  }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * Send a chat message and get AI response
   */
  async sendChatMessage(params: {
    conversationId?: string | null;
    message: string;
    context?: {
      userId?: string;
      username?: string;
      department?: string;
      user?: any;
      session?: any;
      environment?: any;
      recentActions?: any[];
    };
  }): Promise<{
    success: boolean;
    conversationId: string;
    messageId: string;
    response: string;
    suggestions?: string[];
    metadata: {
      model: string;
      provider: string;
      tokensUsed: number;
      responseTime: number;
    };
  }> {
    const response = await this.client.post('/api/chat/message', {
      conversationId: params.conversationId || null,
      message: params.message,
      context: params.context,
    });
    return response.data;
  }

  /**
   * Get list of conversations for current user
   */
  async getConversations(params?: {
    limit?: number;
    offset?: number;
  }): Promise<{
    success: boolean;
    conversations: Array<{
      id: string;
      title: string;
      created_at: string;
      updated_at: string;
      message_count: number;
      is_active: boolean;
    }>;
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await this.client.get('/api/chat/conversations', {
      params: {
        limit: params?.limit || 50,
        offset: params?.offset || 0,
      },
    });
    return response.data;
  }

  /**
   * Get messages for a specific conversation
   */
  async getConversationMessages(
    conversationId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<{
    success: boolean;
    conversationId: string;
    messages: Array<{
      id: string;
      role: string;
      content: string;
      created_at: string;
      metadata?: any;
    }>;
    total: number;
  }> {
    const response = await this.client.get(
      `/api/chat/conversations/${conversationId}/messages`,
      {
        params: {
          limit: params?.limit || 100,
          offset: params?.offset || 0,
        },
      }
    );
    return response.data;
  }

  /**
   * Search knowledge base using RAG
   */
  async searchKnowledge(params: {
    query: string;
    filters?: {
      category?: string;
      tags?: string[];
      source?: string;
    };
    limit?: number;
  }): Promise<{
    success: boolean;
    results: Array<{
      id: string;
      title: string;
      content: string;
      relevanceScore: number;
      source: string;
      url?: string;
      metadata?: any;
    }>;
    totalResults: number;
    queryTime: number;
  }> {
    const response = await this.client.post('/api/knowledge/search', {
      query: params.query,
      filters: params.filters,
      limit: params.limit || 5,
    });
    return response.data;
  }

  /**
   * Submit user feedback for a message
   */
  async submitFeedback(params: {
    messageId: string;
    rating: 'positive' | 'negative';
    comment?: string;
  }): Promise<{
    success: boolean;
    feedbackId: string;
    message: string;
  }> {
    const response = await this.client.post('/api/chat/feedback', {
      messageId: params.messageId,
      rating: params.rating,
      comment: params.comment,
    });
    return response.data;
  }
}

/**
 * Example usage in RADAR Dryad Adapter
 */
export async function exampleUsage() {
  // Initialize client
  const dryad = new DryadClient();

  // Set authentication token (from RADAR Auth Service)
  const radarToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
  dryad.setAuthToken(radarToken);

  try {
    // 1. Health check
    console.log('Checking Dryad.AI health...');
    const health = await dryad.healthCheck();
    console.log('Health:', health);

    // 2. Send chat message with RADAR context
    console.log('\nSending chat message...');
    const chatResponse = await dryad.sendChatMessage({
      conversationId: null, // New conversation
      message: 'How do I reset a user password in Active Directory?',
      context: {
        userId: 'user-123',
        username: 'jsmith',
        department: 'IT Support',
        environment: {
          adDomain: 'RPL.Local',
          adaxesConnected: true,
          jiraConnected: true,
        },
        recentActions: [
          {
            type: 'script_execution',
            scriptName: 'Get-ADUser',
            timestamp: new Date().toISOString(),
          },
        ],
      },
    });
    console.log('AI Response:', chatResponse.response);
    console.log('Suggestions:', chatResponse.suggestions);
    console.log('Metadata:', chatResponse.metadata);

    const conversationId = chatResponse.conversationId;
    const messageId = chatResponse.messageId;

    // 3. Get conversation history
    console.log('\nFetching conversation messages...');
    const messages = await dryad.getConversationMessages(conversationId);
    console.log(`Found ${messages.total} messages`);

    // 4. Search knowledge base
    console.log('\nSearching knowledge base...');
    const searchResults = await dryad.searchKnowledge({
      query: 'Active Directory password policy',
      filters: {
        category: 'IT Support',
        tags: ['AD', 'passwords'],
      },
      limit: 5,
    });
    console.log(`Found ${searchResults.totalResults} results in ${searchResults.queryTime}ms`);
    if (searchResults.results.length > 0) {
      console.log('Top result:', searchResults.results[0].title);
    }

    // 5. Submit positive feedback
    console.log('\nSubmitting feedback...');
    const feedback = await dryad.submitFeedback({
      messageId: messageId,
      rating: 'positive',
      comment: 'Very helpful response!',
    });
    console.log('Feedback submitted:', feedback.feedbackId);

    // 6. Get all conversations
    console.log('\nFetching all conversations...');
    const conversations = await dryad.getConversations({ limit: 10 });
    console.log(`User has ${conversations.total} conversations`);

  } catch (error: any) {
    console.error('Error:', error.response?.data || error.message);
  }
}

/**
 * Express.js middleware example for RADAR Dryad Adapter
 */
export function createDryadMiddleware() {
  const dryad = new DryadClient();

  return {
    /**
     * Middleware to forward RADAR requests to Dryad.AI
     */
    async forwardToDryad(req: any, res: any, next: any) {
      try {
        // Extract JWT token from RADAR request
        const token = req.headers.authorization?.replace('Bearer ', '');
        if (!token) {
          return res.status(401).json({ error: 'Unauthorized' });
        }

        // Set token for Dryad client
        dryad.setAuthToken(token);

        // Forward request based on route
        const route = req.path;
        const method = req.method;

        let result;

        if (route === '/api/chat/message' && method === 'POST') {
          result = await dryad.sendChatMessage(req.body);
        } else if (route === '/api/chat/conversations' && method === 'GET') {
          result = await dryad.getConversations(req.query);
        } else if (route.startsWith('/api/chat/conversations/') && method === 'GET') {
          const conversationId = route.split('/')[4];
          result = await dryad.getConversationMessages(conversationId, req.query);
        } else if (route === '/api/knowledge/search' && method === 'POST') {
          result = await dryad.searchKnowledge(req.body);
        } else if (route === '/api/chat/feedback' && method === 'POST') {
          result = await dryad.submitFeedback(req.body);
        } else {
          return res.status(404).json({ error: 'Route not found' });
        }

        res.json(result);
      } catch (error: any) {
        console.error('Dryad API error:', error);
        res.status(error.response?.status || 500).json({
          success: false,
          error: error.response?.data || error.message,
        });
      }
    },

    /**
     * Health check endpoint
     */
    async healthCheck(req: any, res: any) {
      try {
        const health = await dryad.healthCheck();
        res.json(health);
      } catch (error: any) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message,
        });
      }
    },
  };
}

// Export for use in RADAR Dryad Adapter
export default DryadClient;

