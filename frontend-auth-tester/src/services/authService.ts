// Authentication service for DRYAD.AI OAuth2/JWT testing
import axios, { AxiosInstance } from 'axios';
import { jwtDecode } from 'jwt-decode';
import { AuthTokens, User, TokenData } from '../types/auth';

class AuthService {
  private apiClient: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      withCredentials: true, // Enable cookies for refresh tokens
    });

    // Add request interceptor to include auth token
    this.apiClient.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for token refresh
    this.apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          try {
            await this.refreshAccessToken();
            // Retry the original request
            const originalRequest = error.config;
            const token = this.getAccessToken();
            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.apiClient.request(originalRequest);
          } catch (refreshError) {
            this.logout();
            throw refreshError;
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // OAuth2 Configuration
  async getOAuth2Config(): Promise<any> {
    const response = await this.apiClient.get('/api/v1/auth/config');
    return response.data;
  }

  // Exchange Google token for DRYAD.AI JWT
  async exchangeGoogleToken(googleToken: string): Promise<AuthTokens> {
    const response = await this.apiClient.post('/api/v1/auth/token', {
      google_token: googleToken
    });
    
    const tokens = response.data;
    this.storeTokens(tokens);
    return tokens;
  }

  // Get current user info
  async getCurrentUser(): Promise<User> {
    const response = await this.apiClient.get('/api/v1/auth/me');
    return response.data;
  }

  // Verify token validity
  async verifyToken(): Promise<{ valid: boolean; user?: User }> {
    const response = await this.apiClient.get('/api/v1/auth/verify');
    return response.data;
  }

  // Refresh access token
  async refreshAccessToken(): Promise<AuthTokens> {
    // No need to send refresh token - it's in HttpOnly cookie
    const response = await this.apiClient.post('/api/v1/auth/refresh', {
      remember_me: true // Keep the session alive
    });

    const tokens = response.data;
    this.storeTokens(tokens);
    return tokens;
  }

  // Logout
  async logout(): Promise<void> {
    try {
      await this.apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      this.clearTokens();
    }
  }

  // Token management
  private storeTokens(tokens: AuthTokens): void {
    localStorage.setItem('access_token', tokens.access_token);
    // Don't store refresh_token - it's in HttpOnly cookie
    localStorage.setItem('token_type', tokens.token_type);
    localStorage.setItem('expires_in', tokens.expires_in.toString());
  }

  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    // Refresh token is in HttpOnly cookie, not accessible via JavaScript
    return null;
  }

  private clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('expires_in');
  }

  // Decode JWT token
  decodeToken(token?: string): TokenData | null {
    const accessToken = token || this.getAccessToken();
    if (!accessToken) return null;

    try {
      return jwtDecode<TokenData>(accessToken);
    } catch (error) {
      console.error('Failed to decode token:', error);
      return null;
    }
  }

  // Check if token is expired
  isTokenExpired(token?: string): boolean {
    const tokenData = this.decodeToken(token);
    if (!tokenData) return true;

    const currentTime = Date.now() / 1000;
    return tokenData.exp < currentTime;
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    return token !== null && !this.isTokenExpired(token);
  }

  // Get API client for making authenticated requests
  getApiClient(): AxiosInstance {
    return this.apiClient;
  }
}

export default new AuthService();
