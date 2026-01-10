// Token inspector component for JWT analysis and validation
import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import { TokenData } from '../types/auth';
import authService from '../services/authService';
import { 
  KeyIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  DocumentDuplicateIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

export function TokenInspector() {
  const { tokens, user, refreshToken } = useAuth();
  const [tokenData, setTokenData] = useState<TokenData | null>(null);
  const [showRawToken, setShowRawToken] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);

  useEffect(() => {
    if (tokens?.access_token) {
      const decoded = authService.decodeToken(tokens.access_token);
      setTokenData(decoded);
    }
  }, [tokens]);

  const handleRefreshToken = async () => {
    setIsRefreshing(true);
    setRefreshError(null);
    
    try {
      await refreshToken();
    } catch (error: any) {
      setRefreshError(error.message || 'Token refresh failed');
    } finally {
      setIsRefreshing(false);
    }
  };

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(type);
      setTimeout(() => setCopySuccess(null), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const isTokenExpired = () => {
    if (!tokenData) return true;
    return tokenData.exp < Date.now() / 1000;
  };

  const getTimeUntilExpiry = () => {
    if (!tokenData) return 0;
    return Math.max(0, tokenData.exp - Date.now() / 1000);
  };

  const formatDuration = (seconds: number) => {
    if (seconds <= 0) return 'Expired';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  if (!tokens || !tokenData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No Token Available</h3>
          <p className="mt-2 text-gray-600">Please authenticate to inspect JWT tokens.</p>
        </div>
      </div>
    );
  }

  const expired = isTokenExpired();
  const timeUntilExpiry = getTimeUntilExpiry();

  return (
    <div className="space-y-6">
      {/* Token Status Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">JWT Token Inspector</h2>
          <div className="flex items-center space-x-2">
            {expired ? (
              <div className="flex items-center text-red-600">
                <XCircleIcon className="h-5 w-5 mr-1" />
                <span className="text-sm font-medium">Expired</span>
              </div>
            ) : (
              <div className="flex items-center text-green-600">
                <CheckCircleIcon className="h-5 w-5 mr-1" />
                <span className="text-sm font-medium">Valid</span>
              </div>
            )}
          </div>
        </div>

        {/* Token Expiry Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center">
              <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
              <span className="text-sm font-medium text-gray-900">Time Until Expiry</span>
            </div>
            <p className={`mt-1 text-lg font-semibold ${expired ? 'text-red-600' : 'text-green-600'}`}>
              {formatDuration(timeUntilExpiry)}
            </p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center">
              <KeyIcon className="h-5 w-5 text-gray-400 mr-2" />
              <span className="text-sm font-medium text-gray-900">Token Type</span>
            </div>
            <p className="mt-1 text-lg font-semibold text-gray-900">{tokens.token_type}</p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center">
              <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
              <span className="text-sm font-medium text-gray-900">Expires In</span>
            </div>
            <p className="mt-1 text-lg font-semibold text-gray-900">{tokens.expires_in}s</p>
          </div>
        </div>

        {/* Refresh Token Button */}
        <div className="flex items-center justify-between">
          <div>
            {refreshError && (
              <p className="text-sm text-red-600">{refreshError}</p>
            )}
          </div>
          <button
            onClick={handleRefreshToken}
            disabled={isRefreshing}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRefreshing ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
            ) : (
              <KeyIcon className="h-4 w-4 mr-2" />
            )}
            {isRefreshing ? 'Refreshing...' : 'Refresh Token'}
          </button>
        </div>
      </div>

      {/* Token Details */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Token Details</h3>
        
        <div className="space-y-4">
          {/* User Information */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">User Information</h4>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">User ID:</span>
                <span className="text-sm font-mono text-gray-900">{tokenData.user_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Email:</span>
                <span className="text-sm text-gray-900">{tokenData.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Name:</span>
                <span className="text-sm text-gray-900">{tokenData.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Roles:</span>
                <span className="text-sm text-gray-900">{tokenData.roles.join(', ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Permissions:</span>
                <span className="text-sm text-gray-900">{tokenData.permissions.join(', ')}</span>
              </div>
            </div>
          </div>

          {/* Token Timestamps */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">Token Timestamps</h4>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Issued At (iat):</span>
                <span className="text-sm text-gray-900">{formatTimestamp(tokenData.iat)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Expires At (exp):</span>
                <span className={`text-sm ${expired ? 'text-red-600' : 'text-gray-900'}`}>
                  {formatTimestamp(tokenData.exp)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Valid Duration:</span>
                <span className="text-sm text-gray-900">
                  {formatDuration(tokenData.exp - tokenData.iat)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Raw Token Display */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Raw JWT Token</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowRawToken(!showRawToken)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              {showRawToken ? (
                <>
                  <EyeSlashIcon className="h-4 w-4 mr-2" />
                  Hide Token
                </>
              ) : (
                <>
                  <EyeIcon className="h-4 w-4 mr-2" />
                  Show Token
                </>
              )}
            </button>
            {showRawToken && (
              <button
                onClick={() => copyToClipboard(tokens.access_token, 'access_token')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <DocumentDuplicateIcon className="h-4 w-4 mr-2" />
                {copySuccess === 'access_token' ? 'Copied!' : 'Copy'}
              </button>
            )}
          </div>
        </div>

        {showRawToken && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Access Token</label>
              <textarea
                readOnly
                value={tokens.access_token}
                className="w-full h-32 p-3 border border-gray-300 rounded-md font-mono text-xs bg-gray-50 resize-none"
              />
            </div>
            
            {tokens.refresh_token && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">Refresh Token</label>
                  <button
                    onClick={() => copyToClipboard(tokens.refresh_token, 'refresh_token')}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    {copySuccess === 'refresh_token' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <textarea
                  readOnly
                  value={tokens.refresh_token}
                  className="w-full h-20 p-3 border border-gray-300 rounded-md font-mono text-xs bg-gray-50 resize-none"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
