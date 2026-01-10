'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Log error to external service
    this.logErrorToService(error, errorInfo);
    
    // Call custom error handler
    this.props.onError?.(error, errorInfo);
    
    this.setState({ errorInfo });
  }

  private logErrorToService(error: Error, errorInfo: ErrorInfo) {
    // In production, send to error tracking service like Sentry
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
    
    // For now, just log to console
    console.error('Error logged:', errorData);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReportBug = () => {
    const subject = encodeURIComponent(`Bug Report: ${this.state.error?.message || 'Unknown Error'}`);
    const body = encodeURIComponent(`
Error Details:
- Message: ${this.state.error?.message || 'Unknown'}
- Stack: ${this.state.error?.stack || 'Not available'}
- Component Stack: ${this.state.errorInfo?.componentStack || 'Not available'}
- URL: ${window.location.href}
- User Agent: ${navigator.userAgent}
- Timestamp: ${new Date().toISOString()}

Please describe what you were doing when this error occurred:
[Your description here]
    `);
    
    window.open(`mailto:support@gremlinsai.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow-soft sm:rounded-lg sm:px-10">
              <div className="text-center">
                <AlertTriangle className="mx-auto h-12 w-12 text-error-500 mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Something went wrong
                </h2>
                <p className="text-gray-600 mb-6">
                  We're sorry, but something unexpected happened. Our team has been notified.
                </p>
                
                {process.env.NODE_ENV === 'development' && (
                  <div className="bg-gray-100 rounded-lg p-4 mb-6 text-left">
                    <h3 className="font-semibold text-gray-900 mb-2">Error Details:</h3>
                    <p className="text-sm text-gray-700 font-mono break-all">
                      {this.state.error?.message}
                    </p>
                    {this.state.error?.stack && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-sm text-gray-600">
                          Stack Trace
                        </summary>
                        <pre className="mt-2 text-xs text-gray-600 whitespace-pre-wrap">
                          {this.state.error.stack}
                        </pre>
                      </details>
                    )}
                  </div>
                )}
                
                <div className="space-y-3">
                  <button
                    onClick={this.handleRetry}
                    className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Try Again
                  </button>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={this.handleGoHome}
                      className="flex-1 flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                    >
                      <Home className="w-4 h-4 mr-2" />
                      Go Home
                    </button>
                    
                    <button
                      onClick={this.handleReload}
                      className="flex-1 flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Reload
                    </button>
                  </div>
                  
                  <button
                    onClick={this.handleReportBug}
                    className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-500 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                  >
                    <Bug className="w-4 h-4 mr-2" />
                    Report Bug
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export function useErrorHandler() {
  return (error: Error, errorInfo?: ErrorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    
    // In production, send to error tracking service
    const errorData = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
    
    console.error('Error logged:', errorData);
  };
}

export default ErrorBoundary;
