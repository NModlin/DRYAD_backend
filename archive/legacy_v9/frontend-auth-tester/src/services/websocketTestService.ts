// WebSocket testing service for real-time communication validation
import { WebSocketTestResult } from '../types/auth';

class WebSocketTestService {
  private ws: WebSocket | null = null;
  private baseURL: string;
  private connectionId: string;
  private testResults: WebSocketTestResult[] = [];
  private eventListeners: { [key: string]: ((data: any) => void)[] } = {};

  constructor(baseURL: string = 'ws://localhost:8000') {
    this.baseURL = baseURL.replace('http://', 'ws://').replace('https://', 'wss://');
    this.connectionId = this.generateConnectionId();
  }

  private generateConnectionId(): string {
    return 'test-' + Math.random().toString(36).substr(2, 9);
  }

  // Connect to WebSocket with authentication
  async connectWithAuth(token: string): Promise<WebSocketTestResult> {
    const startTime = Date.now();
    
    try {
      const wsUrl = `${this.baseURL}/api/v1/ws/ws?token=${encodeURIComponent(token)}&client_id=${this.connectionId}&client_type=test`;
      
      this.ws = new WebSocket(wsUrl);
      
      return new Promise((resolve) => {
        if (!this.ws) {
          resolve({
            event: 'connect_with_auth',
            status: 'error',
            error: 'Failed to create WebSocket connection',
            timestamp: new Date().toISOString()
          });
          return;
        }

        this.ws.onopen = () => {
          const result: WebSocketTestResult = {
            event: 'connect_with_auth',
            status: 'success',
            message: `Connected with authentication in ${Date.now() - startTime}ms`,
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          resolve(result);
        };

        this.ws.onerror = (error) => {
          const result: WebSocketTestResult = {
            event: 'connect_with_auth',
            status: 'error',
            error: 'WebSocket connection failed',
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          resolve(result);
        };

        this.ws.onclose = (event) => {
          if (event.code === 4001) {
            const result: WebSocketTestResult = {
              event: 'connect_with_auth',
              status: 'error',
              error: 'Authentication failed - Invalid or expired token',
              timestamp: new Date().toISOString()
            };
            this.testResults.push(result);
            resolve(result);
          }
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        // Timeout after 10 seconds
        setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            resolve({
              event: 'connect_with_auth',
              status: 'error',
              error: 'Connection timeout',
              timestamp: new Date().toISOString()
            });
          }
        }, 10000);
      });
    } catch (error: any) {
      const result: WebSocketTestResult = {
        event: 'connect_with_auth',
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
      return result;
    }
  }

  // Connect without authentication (should fail)
  async connectWithoutAuth(): Promise<WebSocketTestResult> {
    const startTime = Date.now();
    
    try {
      const wsUrl = `${this.baseURL}/api/v1/ws/ws?client_id=${this.connectionId}&client_type=test`;
      
      const testWs = new WebSocket(wsUrl);
      
      return new Promise((resolve) => {
        testWs.onopen = () => {
          const result: WebSocketTestResult = {
            event: 'connect_without_auth',
            status: 'success',
            message: `Connected without authentication in ${Date.now() - startTime}ms`,
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          testWs.close();
          resolve(result);
        };

        testWs.onerror = () => {
          const result: WebSocketTestResult = {
            event: 'connect_without_auth',
            status: 'error',
            error: 'Connection failed (expected for unauthenticated access)',
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          resolve(result);
        };

        testWs.onclose = (event) => {
          const result: WebSocketTestResult = {
            event: 'connect_without_auth',
            status: event.code === 4001 ? 'success' : 'error',
            message: event.code === 4001 ? 'Correctly rejected unauthenticated connection' : 'Unexpected close code',
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          resolve(result);
        };

        // Timeout after 5 seconds
        setTimeout(() => {
          if (testWs.readyState === WebSocket.CONNECTING) {
            testWs.close();
            resolve({
              event: 'connect_without_auth',
              status: 'error',
              error: 'Connection timeout',
              timestamp: new Date().toISOString()
            });
          }
        }, 5000);
      });
    } catch (error: any) {
      const result: WebSocketTestResult = {
        event: 'connect_without_auth',
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
      return result;
    }
  }

  // Test with expired token
  async connectWithExpiredToken(expiredToken: string): Promise<WebSocketTestResult> {
    const startTime = Date.now();
    
    try {
      const wsUrl = `${this.baseURL}/api/v1/ws/ws?token=${encodeURIComponent(expiredToken)}&client_id=${this.connectionId}&client_type=test`;
      
      const testWs = new WebSocket(wsUrl);
      
      return new Promise((resolve) => {
        testWs.onopen = () => {
          const result: WebSocketTestResult = {
            event: 'connect_with_expired_token',
            status: 'error',
            error: 'Connection should have been rejected with expired token',
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          testWs.close();
          resolve(result);
        };

        testWs.onclose = (event) => {
          const result: WebSocketTestResult = {
            event: 'connect_with_expired_token',
            status: event.code === 4001 ? 'success' : 'error',
            message: event.code === 4001 ? 'Correctly rejected expired token' : `Unexpected close code: ${event.code}`,
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          resolve(result);
        };

        testWs.onerror = () => {
          const result: WebSocketTestResult = {
            event: 'connect_with_expired_token',
            status: 'success',
            message: 'Connection correctly failed with expired token',
            timestamp: new Date().toISOString()
          };
          this.testResults.push(result);
          resolve(result);
        };

        // Timeout after 5 seconds
        setTimeout(() => {
          if (testWs.readyState === WebSocket.CONNECTING) {
            testWs.close();
            resolve({
              event: 'connect_with_expired_token',
              status: 'error',
              error: 'Connection timeout',
              timestamp: new Date().toISOString()
            });
          }
        }, 5000);
      });
    } catch (error: any) {
      const result: WebSocketTestResult = {
        event: 'connect_with_expired_token',
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
      return result;
    }
  }

  // Send test message
  async sendMessage(message: any): Promise<WebSocketTestResult> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      const result: WebSocketTestResult = {
        event: 'send_message',
        status: 'error',
        error: 'WebSocket not connected',
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
      return result;
    }

    try {
      this.ws.send(JSON.stringify(message));
      const result: WebSocketTestResult = {
        event: 'send_message',
        status: 'success',
        message: 'Message sent successfully',
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
      return result;
    } catch (error: any) {
      const result: WebSocketTestResult = {
        event: 'send_message',
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
      return result;
    }
  }

  // Handle incoming messages
  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      const result: WebSocketTestResult = {
        event: 'message_received',
        status: 'success',
        message: `Received: ${JSON.stringify(data)}`,
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);

      // Trigger event listeners
      const eventType = data.type || 'message';
      if (this.eventListeners[eventType]) {
        this.eventListeners[eventType].forEach(listener => listener(data));
      }
    } catch (error: any) {
      const result: WebSocketTestResult = {
        event: 'message_received',
        status: 'error',
        error: `Failed to parse message: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      this.testResults.push(result);
    }
  }

  // Add event listener
  addEventListener(event: string, listener: (data: any) => void): void {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(listener);
  }

  // Get test results
  getTestResults(): WebSocketTestResult[] {
    return [...this.testResults];
  }

  // Clear test results
  clearTestResults(): void {
    this.testResults = [];
  }

  // Close connection
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export default WebSocketTestService;
