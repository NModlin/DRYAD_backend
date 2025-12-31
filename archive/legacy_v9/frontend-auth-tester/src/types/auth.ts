// Authentication types for DRYAD.AI OAuth2/JWT testing

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  roles: string[];
  permissions: string[];
  email_verified: boolean;
  created_at: string;
  last_login: string;
  is_active: boolean;
}

export interface TokenData {
  user_id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
  exp: number;
  iat: number;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface GoogleCredentialResponse {
  credential: string;
  select_by: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  tokens: AuthTokens | null;
  loading: boolean;
  error: string | null;
}

export interface TestResult {
  endpoint: string;
  method: string;
  status: 'success' | 'error' | 'pending';
  statusCode?: number;
  responseTime?: number;
  error?: string;
  response?: any;
  timestamp: string;
}

export interface EndpointTest {
  name: string;
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  requiresAuth: boolean;
  category: string;
  description: string;
  testData?: any;
}

export interface WebSocketTestResult {
  event: string;
  status: 'success' | 'error' | 'pending';
  message?: string;
  error?: string;
  timestamp: string;
}

export interface GraphQLTestResult {
  query: string;
  status: 'success' | 'error' | 'pending';
  data?: any;
  errors?: any[];
  timestamp: string;
}
