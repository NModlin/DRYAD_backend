// Authentication context provider for managing auth state
import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, User, AuthTokens, GoogleCredentialResponse } from '../types/auth';
import authService from '../services/authService';

interface AuthContextType extends AuthState {
  login: (googleToken: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  verifyToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; tokens: AuthTokens } }
  | { type: 'LOGIN_ERROR'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'TOKEN_REFRESH_SUCCESS'; payload: AuthTokens }
  | { type: 'TOKEN_REFRESH_ERROR'; payload: string }
  | { type: 'VERIFY_TOKEN_SUCCESS'; payload: User }
  | { type: 'VERIFY_TOKEN_ERROR' }
  | { type: 'CLEAR_ERROR' };

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  tokens: null,
  loading: false,
  error: null,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        loading: true,
        error: null,
      };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        tokens: action.payload.tokens,
        loading: false,
        error: null,
      };
    case 'LOGIN_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        tokens: null,
        loading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...initialState,
      };
    case 'TOKEN_REFRESH_SUCCESS':
      return {
        ...state,
        tokens: action.payload,
        error: null,
      };
    case 'TOKEN_REFRESH_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    case 'VERIFY_TOKEN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload,
        error: null,
      };
    case 'VERIFY_TOKEN_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        tokens: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for existing authentication on mount
  useEffect(() => {
    const checkExistingAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          const user = await authService.getCurrentUser();
          const tokens = {
            access_token: authService.getAccessToken() || '',
            refresh_token: authService.getRefreshToken() || '',
            token_type: 'Bearer',
            expires_in: 3600, // Default value
          };
          dispatch({ type: 'LOGIN_SUCCESS', payload: { user, tokens } });
        } catch (error) {
          // Token is expired or invalid, clear everything and logout
          console.log('Existing token invalid, clearing auth state');
          await authService.logout();
          dispatch({ type: 'LOGOUT' });
        }
      }
    };

    checkExistingAuth();
  }, []);

  const login = async (googleToken: string): Promise<void> => {
    console.log('Starting login with Google token:', googleToken?.substring(0, 50) + '...');
    dispatch({ type: 'LOGIN_START' });

    try {
      // Exchange Google token for GremlinsAI JWT
      console.log('Exchanging Google token for GremlinsAI JWT...');
      const tokens = await authService.exchangeGoogleToken(googleToken);
      console.log('Token exchange successful:', tokens);

      // Get user information
      console.log('Getting user information...');
      const user = await authService.getCurrentUser();
      console.log('User information retrieved:', user);

      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, tokens } });
    } catch (error: any) {
      console.error('Login failed:', error);
      dispatch({ type: 'LOGIN_ERROR', payload: error.message || 'Login failed' });
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const tokens = await authService.refreshAccessToken();
      dispatch({ type: 'TOKEN_REFRESH_SUCCESS', payload: tokens });
    } catch (error: any) {
      dispatch({ type: 'TOKEN_REFRESH_ERROR', payload: error.message || 'Token refresh failed' });
      throw error;
    }
  };

  const verifyToken = async (): Promise<boolean> => {
    try {
      const result = await authService.verifyToken();
      if (result.valid && result.user) {
        dispatch({ type: 'VERIFY_TOKEN_SUCCESS', payload: result.user });
        return true;
      } else {
        dispatch({ type: 'VERIFY_TOKEN_ERROR' });
        return false;
      }
    } catch (error) {
      dispatch({ type: 'VERIFY_TOKEN_ERROR' });
      return false;
    }
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    verifyToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Google OAuth2 integration
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, config: any) => void;
          prompt: () => void;
        };
      };
    };
  }
}

interface GoogleLoginButtonProps {
  onSuccess: (response: GoogleCredentialResponse) => void;
  onError: () => void;
  disabled?: boolean;
}

export function GoogleLoginButton({ onSuccess, onError, disabled }: GoogleLoginButtonProps) {
  const buttonRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (window.google && buttonRef.current) {
      console.log('Initializing Google Sign-In with client ID:', process.env.REACT_APP_GOOGLE_CLIENT_ID);

      window.google.accounts.id.initialize({
        client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
        callback: (response: any) => {
          console.log('Google Sign-In response received:', response);
          onSuccess(response);
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'rectangular',
        logo_alignment: 'left',
      });
    } else {
      console.log('Google Sign-In not ready:', {
        google: !!window.google,
        buttonRef: !!buttonRef.current
      });
    }
  }, [onSuccess, onError]);

  return (
    <div className={`${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <div ref={buttonRef}></div>
    </div>
  );
}
