// GraphQL testing service for authentication validation
import axios, { AxiosInstance } from 'axios';
import { GraphQLTestResult } from '../types/auth';

class GraphQLTestService {
  private apiClient: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Set authentication token
  setAuthToken(token: string): void {
    this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Clear authentication token
  clearAuthToken(): void {
    delete this.apiClient.defaults.headers.common['Authorization'];
  }

  // Execute GraphQL query
  async executeQuery(query: string, variables?: any): Promise<GraphQLTestResult> {
    const startTime = Date.now();
    
    try {
      const response = await this.apiClient.post('/graphql', {
        query,
        variables: variables || {}
      });

      const responseTime = Date.now() - startTime;

      return {
        query,
        status: response.data.errors ? 'error' : 'success',
        data: response.data.data,
        errors: response.data.errors,
        timestamp: new Date().toISOString()
      };
    } catch (error: any) {
      return {
        query,
        status: 'error',
        errors: [{ message: error.message, statusCode: error.response?.status }],
        timestamp: new Date().toISOString()
      };
    }
  }

  // Test GraphQL authentication scenarios
  async testAuthenticationScenarios(token: string): Promise<GraphQLTestResult[]> {
    const results: GraphQLTestResult[] = [];

    // Test 1: Schema introspection without auth
    this.clearAuthToken();
    const introspectionQuery = `
      query IntrospectionQuery {
        __schema {
          types {
            name
            kind
          }
        }
      }
    `;
    
    const introspectionResult = await this.executeQuery(introspectionQuery);
    results.push({
      ...introspectionResult,
      query: 'Schema Introspection (No Auth)'
    });

    // Test 2: Schema introspection with auth
    this.setAuthToken(token);
    const introspectionWithAuthResult = await this.executeQuery(introspectionQuery);
    results.push({
      ...introspectionWithAuthResult,
      query: 'Schema Introspection (With Auth)'
    });

    // Test 3: User query with auth
    const userQuery = `
      query GetCurrentUser {
        currentUser {
          id
          email
          name
          roles
        }
      }
    `;
    
    const userResult = await this.executeQuery(userQuery);
    results.push({
      ...userResult,
      query: 'Current User Query (With Auth)'
    });

    // Test 4: User query without auth
    this.clearAuthToken();
    const userNoAuthResult = await this.executeQuery(userQuery);
    results.push({
      ...userNoAuthResult,
      query: 'Current User Query (No Auth)'
    });

    // Test 5: Documents query with auth
    this.setAuthToken(token);
    const documentsQuery = `
      query GetDocuments($limit: Int) {
        documents(limit: $limit) {
          id
          title
          content
          createdAt
        }
      }
    `;
    
    const documentsResult = await this.executeQuery(documentsQuery, { limit: 10 });
    results.push({
      ...documentsResult,
      query: 'Documents Query (With Auth)'
    });

    // Test 6: Chat history query with auth
    const chatHistoryQuery = `
      query GetChatHistory($limit: Int) {
        chatHistory(limit: $limit) {
          id
          message
          response
          timestamp
        }
      }
    `;
    
    const chatHistoryResult = await this.executeQuery(chatHistoryQuery, { limit: 5 });
    results.push({
      ...chatHistoryResult,
      query: 'Chat History Query (With Auth)'
    });

    // Test 7: Agent status query
    const agentStatusQuery = `
      query GetAgentStatus {
        agentStatus {
          isActive
          currentTasks
          capabilities
        }
      }
    `;
    
    const agentStatusResult = await this.executeQuery(agentStatusQuery);
    results.push({
      ...agentStatusResult,
      query: 'Agent Status Query (With Auth)'
    });

    // Test 8: Mutation with auth
    const createDocumentMutation = `
      mutation CreateDocument($input: DocumentInput!) {
        createDocument(input: $input) {
          id
          title
          success
        }
      }
    `;
    
    const mutationResult = await this.executeQuery(createDocumentMutation, {
      input: {
        title: 'Test Document',
        content: 'This is a test document for authentication validation'
      }
    });
    results.push({
      ...mutationResult,
      query: 'Create Document Mutation (With Auth)'
    });

    // Test 9: Mutation without auth
    this.clearAuthToken();
    const mutationNoAuthResult = await this.executeQuery(createDocumentMutation, {
      input: {
        title: 'Test Document',
        content: 'This should fail without authentication'
      }
    });
    results.push({
      ...mutationNoAuthResult,
      query: 'Create Document Mutation (No Auth)'
    });

    // Test 10: Subscription test (if supported)
    this.setAuthToken(token);
    const subscriptionQuery = `
      subscription TaskUpdates($taskId: String!) {
        taskUpdates(taskId: $taskId) {
          id
          status
          progress
        }
      }
    `;
    
    const subscriptionResult = await this.executeQuery(subscriptionQuery, {
      taskId: 'test-task-id'
    });
    results.push({
      ...subscriptionResult,
      query: 'Task Updates Subscription (With Auth)'
    });

    return results;
  }

  // Get predefined test queries
  getTestQueries(): { name: string; query: string; variables?: any; requiresAuth: boolean }[] {
    return [
      {
        name: 'Schema Types',
        query: `
          query {
            __schema {
              types {
                name
                kind
                description
              }
            }
          }
        `,
        requiresAuth: false
      },
      {
        name: 'Current User',
        query: `
          query {
            currentUser {
              id
              email
              name
              roles
              permissions
            }
          }
        `,
        requiresAuth: true
      },
      {
        name: 'User Documents',
        query: `
          query GetUserDocuments($limit: Int) {
            documents(limit: $limit) {
              id
              title
              content
              createdAt
              updatedAt
            }
          }
        `,
        variables: { limit: 10 },
        requiresAuth: true
      },
      {
        name: 'Chat History',
        query: `
          query GetChatHistory($limit: Int) {
            chatHistory(limit: $limit) {
              id
              message
              response
              timestamp
              userId
            }
          }
        `,
        variables: { limit: 5 },
        requiresAuth: true
      },
      {
        name: 'Agent Capabilities',
        query: `
          query {
            agentCapabilities {
              name
              description
              enabled
            }
          }
        `,
        requiresAuth: true
      },
      {
        name: 'System Health',
        query: `
          query {
            systemHealth {
              status
              uptime
              version
              services {
                name
                status
                lastCheck
              }
            }
          }
        `,
        requiresAuth: true
      }
    ];
  }

  // Test all predefined queries
  async testAllQueries(token: string): Promise<GraphQLTestResult[]> {
    const queries = this.getTestQueries();
    const results: GraphQLTestResult[] = [];

    for (const testQuery of queries) {
      // Test with auth if required
      if (testQuery.requiresAuth) {
        this.setAuthToken(token);
      } else {
        this.clearAuthToken();
      }

      const result = await this.executeQuery(testQuery.query, testQuery.variables);
      results.push({
        ...result,
        query: `${testQuery.name} (${testQuery.requiresAuth ? 'With Auth' : 'No Auth'})`
      });

      // Also test protected queries without auth to verify they fail
      if (testQuery.requiresAuth) {
        this.clearAuthToken();
        const noAuthResult = await this.executeQuery(testQuery.query, testQuery.variables);
        results.push({
          ...noAuthResult,
          query: `${testQuery.name} (No Auth - Should Fail)`
        });
      }

      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return results;
  }
}

export default new GraphQLTestService();
