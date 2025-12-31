// Main application component for GremlinsAI OAuth2/JWT Authentication Tester
import React, { useState } from 'react';
import { AuthProvider, GoogleLoginButton, useAuth } from './components/AuthProvider';
import { TestDashboard } from './components/TestDashboard';
import { TokenInspector } from './components/TokenInspector';
import { TestRunner } from './components/TestRunner';
import { GoogleCredentialResponse } from './types/auth';
import {
  UserCircleIcon,
  KeyIcon,
  ClipboardDocumentListIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon,
  PlayIcon
} from '@heroicons/react/24/outline';

function AppContent() {
  const { isAuthenticated, user, login, logout, loading, error } = useAuth();
  const [activeView, setActiveView] = useState<'dashboard' | 'tokens' | 'runner'>('dashboard');

  const handleGoogleLogin = async (response: GoogleCredentialResponse) => {
    try {
      await login(response.credential);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleGoogleLoginError = () => {
    console.error('Google login failed');
  };

  const handleLogout = async () => {
    try {
      await logout();
      setActiveView('dashboard');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <KeyIcon className="h-8 w-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">GremlinsAI Auth Tester</h1>
                <p className="text-sm text-gray-600">OAuth2 & JWT Authentication Validation</p>
              </div>
            </div>

            {isAuthenticated && user ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <UserCircleIcon className="h-6 w-6 text-gray-400" />
                  <div className="text-sm">
                    <p className="font-medium text-gray-900">{user.name}</p>
                    <p className="text-gray-500">{user.email}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <ArrowRightOnRectangleIcon className="h-4 w-4 mr-2" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-3">Sign in with Google to start testing</p>
                <GoogleLoginButton
                  onSuccess={handleGoogleLogin}
                  onError={handleGoogleLoginError}
                  disabled={loading}
                />
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Authentication Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isAuthenticated ? (
          <div>
            {/* Navigation Tabs */}
            <div className="mb-8">
              <nav className="flex space-x-8">
                <button
                  onClick={() => setActiveView('dashboard')}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeView === 'dashboard'
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <ClipboardDocumentListIcon className="h-5 w-5 mr-2" />
                  Test Dashboard
                </button>
                <button
                  onClick={() => setActiveView('runner')}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeView === 'runner'
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <PlayIcon className="h-5 w-5 mr-2" />
                  Automated Runner
                </button>
                <button
                  onClick={() => setActiveView('tokens')}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeView === 'tokens'
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <KeyIcon className="h-5 w-5 mr-2" />
                  Token Inspector
                </button>
              </nav>
            </div>

            {/* Content Views */}
            {activeView === 'dashboard' && <TestDashboard />}
            {activeView === 'runner' && <TestRunner />}
            {activeView === 'tokens' && <TokenInspector />}
          </div>
        ) : (
          <div className="text-center py-12">
            <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h2 className="mt-4 text-xl font-semibold text-gray-900">Welcome to GremlinsAI Auth Tester</h2>
            <p className="mt-2 text-gray-600 max-w-2xl mx-auto">
              This comprehensive testing application validates OAuth2 and JWT authentication across all GremlinsAI backend capabilities.
              Sign in with your Google account to begin testing.
            </p>
            
            <div className="mt-8 bg-white rounded-lg shadow p-6 max-w-4xl mx-auto">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Test Coverage Includes:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-left">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900">Authentication Flow</h4>
                  <ul className="mt-2 text-sm text-gray-600 space-y-1">
                    <li>• Google OAuth2 login/logout</li>
                    <li>• JWT token exchange</li>
                    <li>• Token refresh handling</li>
                    <li>• Token expiration testing</li>
                  </ul>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900">REST API Endpoints</h4>
                  <ul className="mt-2 text-sm text-gray-600 space-y-1">
                    <li>• All 103 protected endpoints</li>
                    <li>• Agent interactions</li>
                    <li>• Document management</li>
                    <li>• Multi-agent workflows</li>
                  </ul>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900">Real-time Communication</h4>
                  <ul className="mt-2 text-sm text-gray-600 space-y-1">
                    <li>• WebSocket authentication</li>
                    <li>• GraphQL API testing</li>
                    <li>• Connection handling</li>
                    <li>• Error scenarios</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>GremlinsAI Authentication Tester - Comprehensive OAuth2 & JWT Validation</p>
            <p className="mt-1">
              Tests {isAuthenticated ? 'authenticated' : 'unauthenticated'} access across REST, WebSocket, and GraphQL APIs
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
