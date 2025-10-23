// Main testing dashboard component
import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import { TestResult, EndpointTest, WebSocketTestResult, GraphQLTestResult } from '../types/auth';
import apiTestService from '../services/apiTestService';
import WebSocketTestService from '../services/websocketTestService';
import graphqlTestService from '../services/graphqlTestService';
import { CheckCircleIcon, XCircleIcon, ClockIcon, PlayIcon } from '@heroicons/react/24/outline';

interface TestDashboardProps {
  className?: string;
}

export function TestDashboard({ className = '' }: TestDashboardProps) {
  const { user, tokens, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<'rest' | 'websocket' | 'graphql'>('rest');
  const [restResults, setRestResults] = useState<TestResult[]>([]);
  const [wsResults, setWsResults] = useState<WebSocketTestResult[]>([]);
  const [graphqlResults, setGraphqlResults] = useState<GraphQLTestResult[]>([]);
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [wsTestService] = useState(() => new WebSocketTestService());

  // REST API Tests
  const runRestApiTests = async () => {
    if (!tokens?.access_token) return;

    setIsRunningTests(true);
    setRestResults([]);

    try {
      // Test authentication scenarios first
      const authResults = await apiTestService.testAuthenticationScenarios(tokens.access_token);
      setRestResults(prev => [...prev, ...authResults]);

      // Test all endpoints
      const endpoints = apiTestService.getEndpointsToTest();
      
      for (const endpoint of endpoints) {
        if (endpoint.requiresAuth) {
          apiTestService.setAuthToken(tokens.access_token);
        } else {
          apiTestService.clearAuthToken();
        }

        const result = await apiTestService.testEndpoint(endpoint);
        setRestResults(prev => [...prev, result]);

        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Test unauthorized access
      apiTestService.clearAuthToken();
      const unauthorizedTests = endpoints.filter(e => e.requiresAuth).slice(0, 3);
      for (const endpoint of unauthorizedTests) {
        const result = await apiTestService.testEndpoint({
          ...endpoint,
          name: `${endpoint.name} (Unauthorized)`
        });
        setRestResults(prev => [...prev, result]);
      }

    } catch (error) {
      console.error('REST API tests failed:', error);
    } finally {
      setIsRunningTests(false);
    }
  };

  // WebSocket Tests
  const runWebSocketTests = async () => {
    if (!tokens?.access_token) return;

    setIsRunningTests(true);
    setWsResults([]);
    wsTestService.clearTestResults();

    try {
      // Test 1: Connect with valid token
      const connectResult = await wsTestService.connectWithAuth(tokens.access_token);
      setWsResults(prev => [...prev, connectResult]);

      if (wsTestService.isConnected()) {
        // Test 2: Send message
        const messageResult = await wsTestService.sendMessage({
          type: 'test',
          message: 'Hello WebSocket!'
        });
        setWsResults(prev => [...prev, messageResult]);

        // Wait for potential responses
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        wsTestService.disconnect();
      }

      // Test 3: Connect without auth
      const noAuthResult = await wsTestService.connectWithoutAuth();
      setWsResults(prev => [...prev, noAuthResult]);

      // Test 4: Connect with expired/invalid token
      const expiredResult = await wsTestService.connectWithExpiredToken('invalid.token.here');
      setWsResults(prev => [...prev, expiredResult]);

      // Get all results from service
      const allResults = wsTestService.getTestResults();
      setWsResults(allResults);

    } catch (error) {
      console.error('WebSocket tests failed:', error);
    } finally {
      setIsRunningTests(false);
    }
  };

  // GraphQL Tests
  const runGraphQLTests = async () => {
    if (!tokens?.access_token) return;

    setIsRunningTests(true);
    setGraphqlResults([]);

    try {
      // Test authentication scenarios
      const authResults = await graphqlTestService.testAuthenticationScenarios(tokens.access_token);
      setGraphqlResults(authResults);

      // Test all predefined queries
      const allResults = await graphqlTestService.testAllQueries(tokens.access_token);
      setGraphqlResults(allResults);

    } catch (error) {
      console.error('GraphQL tests failed:', error);
    } finally {
      setIsRunningTests(false);
    }
  };

  // Run all tests
  const runAllTests = async () => {
    await runRestApiTests();
    await runWebSocketTests();
    await runGraphQLTests();
  };

  const getStatusIcon = (status: 'success' | 'error' | 'pending') => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: 'success' | 'error' | 'pending') => {
    switch (status) {
      case 'success':
        return 'bg-green-50 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-50 text-red-800 border-red-200';
      case 'pending':
        return 'bg-yellow-50 text-yellow-800 border-yellow-200';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Authentication Required</h2>
          <p className="text-gray-600">Please log in to run authentication tests.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Authentication Test Dashboard</h2>
          <div className="flex space-x-2">
            <button
              onClick={runAllTests}
              disabled={isRunningTests}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              {isRunningTests ? 'Running Tests...' : 'Run All Tests'}
            </button>
          </div>
        </div>
        
        {/* User Info */}
        {user && (
          <div className="mt-4 p-3 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Authenticated as:</span> {user.name} ({user.email})
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Roles:</span> {user.roles.join(', ')}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Token expires:</span> {tokens ? new Date(Date.now() + tokens.expires_in * 1000).toLocaleString() : 'Unknown'}
            </p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-6">
          {[
            { id: 'rest', name: 'REST API', count: restResults.length },
            { id: 'websocket', name: 'WebSocket', count: wsResults.length },
            { id: 'graphql', name: 'GraphQL', count: graphqlResults.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
              {tab.count > 0 && (
                <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'rest' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">REST API Tests</h3>
              <button
                onClick={runRestApiTests}
                disabled={isRunningTests}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <PlayIcon className="h-4 w-4 mr-2" />
                Run REST Tests
              </button>
            </div>
            
            <div className="space-y-3">
              {restResults.map((result, index) => (
                <div key={index} className={`border rounded-lg p-4 ${getStatusColor(result.status)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(result.status)}
                      <span className="ml-2 font-medium">{result.method} {result.endpoint}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm">
                      {result.statusCode && (
                        <span className="font-mono">{result.statusCode}</span>
                      )}
                      {result.responseTime && (
                        <span>{result.responseTime}ms</span>
                      )}
                    </div>
                  </div>
                  {result.error && (
                    <p className="mt-2 text-sm text-red-600">{result.error}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'websocket' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">WebSocket Tests</h3>
              <button
                onClick={runWebSocketTests}
                disabled={isRunningTests}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <PlayIcon className="h-4 w-4 mr-2" />
                Run WebSocket Tests
              </button>
            </div>
            
            <div className="space-y-3">
              {wsResults.map((result, index) => (
                <div key={index} className={`border rounded-lg p-4 ${getStatusColor(result.status)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(result.status)}
                      <span className="ml-2 font-medium">{result.event}</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(result.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {result.message && (
                    <p className="mt-2 text-sm">{result.message}</p>
                  )}
                  {result.error && (
                    <p className="mt-2 text-sm text-red-600">{result.error}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'graphql' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">GraphQL Tests</h3>
              <button
                onClick={runGraphQLTests}
                disabled={isRunningTests}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <PlayIcon className="h-4 w-4 mr-2" />
                Run GraphQL Tests
              </button>
            </div>
            
            <div className="space-y-3">
              {graphqlResults.map((result, index) => (
                <div key={index} className={`border rounded-lg p-4 ${getStatusColor(result.status)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(result.status)}
                      <span className="ml-2 font-medium">{result.query}</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(result.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {result.errors && result.errors.length > 0 && (
                    <div className="mt-2">
                      {result.errors.map((error, errorIndex) => (
                        <p key={errorIndex} className="text-sm text-red-600">{error.message}</p>
                      ))}
                    </div>
                  )}
                  {result.data && (
                    <details className="mt-2">
                      <summary className="text-sm font-medium cursor-pointer">Response Data</summary>
                      <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-auto">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
