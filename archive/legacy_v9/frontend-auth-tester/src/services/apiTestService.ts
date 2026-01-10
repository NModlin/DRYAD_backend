// API testing service for comprehensive endpoint validation
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { EndpointTest, TestResult } from '../types/auth';

class ApiTestService {
  private apiClient: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
    });
  }

  // Set authentication token for testing
  setAuthToken(token: string): void {
    this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Clear authentication token
  clearAuthToken(): void {
    delete this.apiClient.defaults.headers.common['Authorization'];
  }

  // Test a single endpoint
  async testEndpoint(test: EndpointTest): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      let response: AxiosResponse;
      
      switch (test.method) {
        case 'GET':
          response = await this.apiClient.get(test.endpoint);
          break;
        case 'POST':
          response = await this.apiClient.post(test.endpoint, test.testData || {});
          break;
        case 'PUT':
          response = await this.apiClient.put(test.endpoint, test.testData || {});
          break;
        case 'DELETE':
          response = await this.apiClient.delete(test.endpoint);
          break;
        case 'PATCH':
          response = await this.apiClient.patch(test.endpoint, test.testData || {});
          break;
        default:
          throw new Error(`Unsupported method: ${test.method}`);
      }

      const responseTime = Date.now() - startTime;

      return {
        endpoint: test.endpoint,
        method: test.method,
        status: 'success',
        statusCode: response.status,
        responseTime,
        response: response.data,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      
      return {
        endpoint: test.endpoint,
        method: test.method,
        status: 'error',
        statusCode: error.response?.status,
        responseTime,
        error: error.message,
        response: error.response?.data,
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Test multiple endpoints
  async testEndpoints(tests: EndpointTest[]): Promise<TestResult[]> {
    const results: TestResult[] = [];
    
    for (const test of tests) {
      const result = await this.testEndpoint(test);
      results.push(result);
      
      // Small delay between requests to avoid overwhelming the server
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    return results;
  }

  // Test authentication-specific scenarios
  async testAuthenticationScenarios(token: string): Promise<TestResult[]> {
    const scenarios: EndpointTest[] = [
      // Test with valid token
      {
        name: 'Valid Token Test',
        endpoint: '/api/v1/auth/verify',
        method: 'GET',
        requiresAuth: true,
        category: 'Authentication',
        description: 'Test endpoint with valid JWT token'
      },
      // Test protected endpoint
      {
        name: 'Protected Endpoint Test',
        endpoint: '/api/v1/auth/me',
        method: 'GET',
        requiresAuth: true,
        category: 'Authentication',
        description: 'Test protected endpoint access'
      }
    ];

    this.setAuthToken(token);
    const results = await this.testEndpoints(scenarios);
    
    // Test without token
    this.clearAuthToken();
    const unauthorizedTest: EndpointTest = {
      name: 'Unauthorized Access Test',
      endpoint: '/api/v1/auth/me',
      method: 'GET',
      requiresAuth: true,
      category: 'Authentication',
      description: 'Test endpoint without authentication token'
    };
    
    const unauthorizedResult = await this.testEndpoint(unauthorizedTest);
    results.push(unauthorizedResult);
    
    return results;
  }

  // Get all available endpoints for testing
  getEndpointsToTest(): EndpointTest[] {
    return [
      // Authentication endpoints
      {
        name: 'OAuth2 Config',
        endpoint: '/api/v1/auth/config',
        method: 'GET',
        requiresAuth: false,
        category: 'Authentication',
        description: 'Get OAuth2 configuration'
      },
      {
        name: 'Current User',
        endpoint: '/api/v1/auth/me',
        method: 'GET',
        requiresAuth: true,
        category: 'Authentication',
        description: 'Get current user information'
      },
      {
        name: 'Verify Token',
        endpoint: '/api/v1/auth/verify',
        method: 'GET',
        requiresAuth: true,
        category: 'Authentication',
        description: 'Verify JWT token validity'
      },

      // Health endpoints
      {
        name: 'Health Check',
        endpoint: '/api/v1/health',
        method: 'GET',
        requiresAuth: false,
        category: 'Health',
        description: 'Basic health check'
      },
      {
        name: 'Health Status',
        endpoint: '/api/v1/health/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Health',
        description: 'Detailed health status'
      },
      {
        name: 'Health Metrics',
        endpoint: '/api/v1/health/metrics',
        method: 'GET',
        requiresAuth: true,
        category: 'Health',
        description: 'System metrics and performance data'
      },

      // Agent endpoints
      {
        name: 'Agent Chat',
        endpoint: '/api/v1/agent/chat',
        method: 'POST',
        requiresAuth: true,
        category: 'Agent',
        description: 'Chat with AI agent',
        testData: { message: 'Hello, this is a test message for authentication validation' }
      },
      {
        name: 'Agent Status',
        endpoint: '/api/v1/agent/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Agent',
        description: 'Get agent status'
      },
      {
        name: 'Agent Capabilities',
        endpoint: '/api/v1/agent/capabilities',
        method: 'GET',
        requiresAuth: true,
        category: 'Agent',
        description: 'Get agent capabilities'
      },
      {
        name: 'Agent History',
        endpoint: '/api/v1/agent/history',
        method: 'GET',
        requiresAuth: true,
        category: 'Agent',
        description: 'Get agent conversation history'
      },

      // Document endpoints
      {
        name: 'List Documents',
        endpoint: '/api/v1/documents',
        method: 'GET',
        requiresAuth: true,
        category: 'Documents',
        description: 'List user documents'
      },
      {
        name: 'Document Search',
        endpoint: '/api/v1/documents/search',
        method: 'POST',
        requiresAuth: true,
        category: 'Documents',
        description: 'Search documents',
        testData: { query: 'test search query', limit: 10 }
      },
      {
        name: 'Document Upload Status',
        endpoint: '/api/v1/documents/upload/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Documents',
        description: 'Get document upload status'
      },
      {
        name: 'Document Processing Status',
        endpoint: '/api/v1/documents/processing/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Documents',
        description: 'Get document processing status'
      },

      // Chat History endpoints
      {
        name: 'Chat History',
        endpoint: '/api/v1/history',
        method: 'GET',
        requiresAuth: true,
        category: 'Chat History',
        description: 'Get chat history'
      },
      {
        name: 'Chat History Search',
        endpoint: '/api/v1/history/search',
        method: 'POST',
        requiresAuth: true,
        category: 'Chat History',
        description: 'Search chat history',
        testData: { query: 'test', limit: 5 }
      },

      // Multi-agent endpoints
      {
        name: 'Multi-Agent Status',
        endpoint: '/api/v1/multi-agent/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Multi-Agent',
        description: 'Get multi-agent system status'
      },
      {
        name: 'Multi-Agent Workflows',
        endpoint: '/api/v1/multi-agent/workflows',
        method: 'GET',
        requiresAuth: true,
        category: 'Multi-Agent',
        description: 'List available workflows'
      },
      {
        name: 'Multi-Agent Execute',
        endpoint: '/api/v1/multi-agent/execute',
        method: 'POST',
        requiresAuth: true,
        category: 'Multi-Agent',
        description: 'Execute multi-agent workflow',
        testData: { workflow: 'test-workflow', input: 'test input' }
      },

      // Multimodal endpoints
      {
        name: 'Multimodal Status',
        endpoint: '/api/v1/multimodal/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Multimodal',
        description: 'Get multimodal processing status'
      },
      {
        name: 'Multimodal Search',
        endpoint: '/api/v1/multimodal/search',
        method: 'POST',
        requiresAuth: true,
        category: 'Multimodal',
        description: 'Cross-modal search',
        testData: { query: 'test image search', modality: 'text-to-image' }
      },
      {
        name: 'Multimodal Process',
        endpoint: '/api/v1/multimodal/process',
        method: 'POST',
        requiresAuth: true,
        category: 'Multimodal',
        description: 'Process multimodal content',
        testData: { type: 'image', content: 'test-content' }
      },

      // Orchestrator endpoints
      {
        name: 'Orchestrator Status',
        endpoint: '/api/v1/orchestrator/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Orchestrator',
        description: 'Get orchestrator status'
      },
      {
        name: 'Orchestrator Tasks',
        endpoint: '/api/v1/orchestrator/tasks',
        method: 'GET',
        requiresAuth: true,
        category: 'Orchestrator',
        description: 'List orchestrator tasks'
      },
      {
        name: 'Orchestrator Execute',
        endpoint: '/api/v1/orchestrator/execute',
        method: 'POST',
        requiresAuth: true,
        category: 'Orchestrator',
        description: 'Execute orchestrated task',
        testData: { task: 'test-task', parameters: {} }
      },

      // Real-time endpoints
      {
        name: 'Real-time Status',
        endpoint: '/api/v1/realtime/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Real-time',
        description: 'Get real-time system status'
      },
      {
        name: 'Real-time Connections',
        endpoint: '/api/v1/realtime/connections',
        method: 'GET',
        requiresAuth: true,
        category: 'Real-time',
        description: 'Get active real-time connections'
      },

      // Developer Portal endpoints
      {
        name: 'Developer Portal Status',
        endpoint: '/api/v1/developer-portal/status',
        method: 'GET',
        requiresAuth: true,
        category: 'Developer Portal',
        description: 'Get developer portal status'
      },
      {
        name: 'API Documentation',
        endpoint: '/docs/api',
        method: 'GET',
        requiresAuth: false,
        category: 'Documentation',
        description: 'API documentation endpoint'
      }
    ];
  }
}

export default new ApiTestService();
