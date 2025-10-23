// Automated test runner component for comprehensive authentication testing
import React, { useState, useCallback } from 'react';
import { useAuth } from './AuthProvider';
import { TestResult, EndpointTest, WebSocketTestResult, GraphQLTestResult } from '../types/auth';
import apiTestService from '../services/apiTestService';
import WebSocketTestService from '../services/websocketTestService';
import graphqlTestService from '../services/graphqlTestService';
import { 
  PlayIcon, 
  StopIcon, 
  DocumentArrowDownIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

interface TestSuite {
  name: string;
  tests: EndpointTest[];
  category: string;
}

interface TestRunnerProps {
  onTestComplete?: (results: {
    rest: TestResult[];
    websocket: WebSocketTestResult[];
    graphql: GraphQLTestResult[];
    summary: {
      total: number;
      passed: number;
      failed: number;
    };
  }) => void;
}

export function TestRunner({ onTestComplete }: TestRunnerProps) {
  const { tokens, isAuthenticated } = useAuth();
  const [isRunning, setIsRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<{
    rest: TestResult[];
    websocket: WebSocketTestResult[];
    graphql: GraphQLTestResult[];
  }>({
    rest: [],
    websocket: [],
    graphql: []
  });
  const [testSuites] = useState<TestSuite[]>([
    {
      name: 'Authentication Flow',
      category: 'Authentication',
      tests: [
        {
          name: 'OAuth2 Config',
          endpoint: '/api/v1/auth/config',
          method: 'GET',
          requiresAuth: false,
          category: 'Authentication',
          description: 'Verify OAuth2 configuration endpoint'
        },
        {
          name: 'Token Verification',
          endpoint: '/api/v1/auth/verify',
          method: 'GET',
          requiresAuth: true,
          category: 'Authentication',
          description: 'Verify JWT token validity'
        },
        {
          name: 'User Profile',
          endpoint: '/api/v1/auth/me',
          method: 'GET',
          requiresAuth: true,
          category: 'Authentication',
          description: 'Get authenticated user profile'
        }
      ]
    },
    {
      name: 'Core API Endpoints',
      category: 'API',
      tests: apiTestService.getEndpointsToTest().filter(test => 
        ['Agent', 'Documents', 'Health'].includes(test.category)
      )
    },
    {
      name: 'Advanced Features',
      category: 'Advanced',
      tests: apiTestService.getEndpointsToTest().filter(test => 
        ['Multi-Agent', 'Multimodal', 'Orchestrator', 'Real-time'].includes(test.category)
      )
    }
  ]);

  const runComprehensiveTests = useCallback(async () => {
    if (!tokens?.access_token || !isAuthenticated) {
      alert('Please authenticate first');
      return;
    }

    setIsRunning(true);
    setProgress(0);
    setResults({ rest: [], websocket: [], graphql: [] });

    try {
      // Calculate total tests
      const totalRestTests = apiTestService.getEndpointsToTest().length;
      const totalWsTests = 4; // Connect with auth, without auth, expired token, message test
      const totalGraphqlTests = 10; // Estimated GraphQL test count
      const totalTests = totalRestTests + totalWsTests + totalGraphqlTests;
      let completedTests = 0;

      // 1. Run REST API Tests
      setCurrentTest('Running REST API Tests...');
      const endpoints = apiTestService.getEndpointsToTest();
      const restResults: TestResult[] = [];

      for (const endpoint of endpoints) {
        setCurrentTest(`Testing ${endpoint.method} ${endpoint.endpoint}`);
        
        if (endpoint.requiresAuth) {
          apiTestService.setAuthToken(tokens.access_token);
        } else {
          apiTestService.clearAuthToken();
        }

        const result = await apiTestService.testEndpoint(endpoint);
        restResults.push(result);
        
        completedTests++;
        setProgress((completedTests / totalTests) * 100);
        
        // Update results in real-time
        setResults(prev => ({ ...prev, rest: [...restResults] }));
        
        // Small delay to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Test unauthorized access
      apiTestService.clearAuthToken();
      const unauthorizedTests = endpoints.filter(e => e.requiresAuth).slice(0, 3);
      for (const endpoint of unauthorizedTests) {
        setCurrentTest(`Testing unauthorized access to ${endpoint.endpoint}`);
        const result = await apiTestService.testEndpoint({
          ...endpoint,
          name: `${endpoint.name} (Unauthorized)`
        });
        restResults.push(result);
        completedTests++;
        setProgress((completedTests / totalTests) * 100);
        setResults(prev => ({ ...prev, rest: [...restResults] }));
      }

      // 2. Run WebSocket Tests
      setCurrentTest('Running WebSocket Tests...');
      const wsTestService = new WebSocketTestService();
      const wsResults: WebSocketTestResult[] = [];

      // Test authenticated connection
      setCurrentTest('Testing WebSocket authenticated connection...');
      const authConnectResult = await wsTestService.connectWithAuth(tokens.access_token);
      wsResults.push(authConnectResult);
      completedTests++;
      setProgress((completedTests / totalTests) * 100);

      if (wsTestService.isConnected()) {
        // Test message sending
        setCurrentTest('Testing WebSocket message sending...');
        const messageResult = await wsTestService.sendMessage({
          type: 'test',
          message: 'Authentication test message',
          timestamp: new Date().toISOString()
        });
        wsResults.push(messageResult);
        completedTests++;
        setProgress((completedTests / totalTests) * 100);
        
        wsTestService.disconnect();
      }

      // Test unauthenticated connection
      setCurrentTest('Testing WebSocket unauthenticated connection...');
      const noAuthResult = await wsTestService.connectWithoutAuth();
      wsResults.push(noAuthResult);
      completedTests++;
      setProgress((completedTests / totalTests) * 100);

      // Test expired token
      setCurrentTest('Testing WebSocket with expired token...');
      const expiredResult = await wsTestService.connectWithExpiredToken('expired.token.here');
      wsResults.push(expiredResult);
      completedTests++;
      setProgress((completedTests / totalTests) * 100);

      setResults(prev => ({ ...prev, websocket: wsResults }));

      // 3. Run GraphQL Tests
      setCurrentTest('Running GraphQL Tests...');
      const graphqlResults = await graphqlTestService.testAuthenticationScenarios(tokens.access_token);
      
      for (let i = 0; i < graphqlResults.length; i++) {
        completedTests++;
        setProgress((completedTests / totalTests) * 100);
        setCurrentTest(`GraphQL Test ${i + 1}/${graphqlResults.length}`);
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      setResults(prev => ({ ...prev, graphql: graphqlResults }));

      // Complete
      setCurrentTest('Tests completed successfully!');
      setProgress(100);

      // Call completion callback
      if (onTestComplete) {
        onTestComplete({
          rest: restResults,
          websocket: wsResults,
          graphql: graphqlResults,
          summary: {
            total: totalTests,
            passed: [...restResults, ...wsResults, ...graphqlResults].filter(r => r.status === 'success').length,
            failed: [...restResults, ...wsResults, ...graphqlResults].filter(r => r.status === 'error').length
          }
        });
      }

    } catch (error) {
      console.error('Test execution failed:', error);
      setCurrentTest(`Test execution failed: ${error}`);
    } finally {
      setIsRunning(false);
    }
  }, [tokens, isAuthenticated, onTestComplete]);

  const stopTests = () => {
    setIsRunning(false);
    setCurrentTest('Tests stopped by user');
  };

  const exportResults = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      user: tokens ? 'authenticated' : 'anonymous',
      results: results,
      summary: {
        rest: {
          total: results.rest.length,
          passed: results.rest.filter(r => r.status === 'success').length,
          failed: results.rest.filter(r => r.status === 'error').length
        },
        websocket: {
          total: results.websocket.length,
          passed: results.websocket.filter(r => r.status === 'success').length,
          failed: results.websocket.filter(r => r.status === 'error').length
        },
        graphql: {
          total: results.graphql.length,
          passed: results.graphql.filter(r => r.status === 'success').length,
          failed: results.graphql.filter(r => r.status === 'error').length
        }
      }
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gremlinsai-auth-test-results-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getTotalResults = () => {
    return results.rest.length + results.websocket.length + results.graphql.length;
  };

  const getPassedResults = () => {
    return [...results.rest, ...results.websocket, ...results.graphql]
      .filter(r => r.status === 'success').length;
  };

  const getFailedResults = () => {
    return [...results.rest, ...results.websocket, ...results.graphql]
      .filter(r => r.status === 'error').length;
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Authentication Required</h3>
          <p className="text-gray-600">Please authenticate to run comprehensive tests.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Automated Test Runner</h2>
          <p className="text-sm text-gray-600">Comprehensive OAuth2 & JWT authentication testing</p>
        </div>
        <div className="flex items-center space-x-3">
          {getTotalResults() > 0 && (
            <button
              onClick={exportResults}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export Results
            </button>
          )}
          {isRunning ? (
            <button
              onClick={stopTests}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
            >
              <StopIcon className="h-4 w-4 mr-2" />
              Stop Tests
            </button>
          ) : (
            <button
              onClick={runComprehensiveTests}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              Run All Tests
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Test Progress</span>
            <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          {currentTest && (
            <p className="mt-2 text-sm text-gray-600 flex items-center">
              <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
              {currentTest}
            </p>
          )}
        </div>
      )}

      {/* Test Suites Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {testSuites.map((suite, index) => (
          <div key={index} className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">{suite.name}</h3>
            <p className="text-sm text-gray-600 mb-2">{suite.tests.length} tests</p>
            <div className="text-xs text-gray-500">
              Category: {suite.category}
            </div>
          </div>
        ))}
      </div>

      {/* Results Summary */}
      {getTotalResults() > 0 && (
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Test Results Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <ClockIcon className="h-5 w-5 text-blue-400 mr-2" />
                <span className="text-sm font-medium text-blue-900">Total Tests</span>
              </div>
              <p className="mt-1 text-2xl font-semibold text-blue-900">{getTotalResults()}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
                <span className="text-sm font-medium text-green-900">Passed</span>
              </div>
              <p className="mt-1 text-2xl font-semibold text-green-900">{getPassedResults()}</p>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center">
                <XCircleIcon className="h-5 w-5 text-red-400 mr-2" />
                <span className="text-sm font-medium text-red-900">Failed</span>
              </div>
              <p className="mt-1 text-2xl font-semibold text-red-900">{getFailedResults()}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900">Success Rate</span>
              </div>
              <p className="mt-1 text-2xl font-semibold text-gray-900">
                {getTotalResults() > 0 ? Math.round((getPassedResults() / getTotalResults()) * 100) : 0}%
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
