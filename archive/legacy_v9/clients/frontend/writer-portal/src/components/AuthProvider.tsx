"use client";
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { exchangeGoogleToken, getAuthConfig, getMe, setAuthToken } from '@/lib/auth';
import { apiClient } from '@/lib/apiClient';

export type AuthState = {
  user: any | null;
  token: string | null;
  login: () => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
};

const AuthCtx = createContext<AuthState>({ user: null, token: null, login: async () => {}, logout: () => {}, refreshAuth: async () => {} });
export function useAuth() { return useContext(AuthCtx); }

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Restore token and fetch user
    (async () => {
      const me = await getMe();
      if (me) {
        setUser(me);
        const t = localStorage.getItem('gremlins_token');
        setToken(t);
      } else {
        setUser(null);
        setToken(null);
      }
    })();
  }, []);

  const login = async () => {
    try {
      // Fetch OAuth configuration from backend
      const cfg = await getAuthConfig();

      if (!cfg.google_client_id) {
        throw new Error('Google Client ID not configured on backend. Please set GOOGLE_CLIENT_ID in .env file.');
      }

      const libUrl = 'https://accounts.google.com/gsi/client';

      // Load Google script
      await new Promise<void>((resolve, reject) => {
        if (document.getElementById('google-gsi')) return resolve();
        const s = document.createElement('script');
        s.src = libUrl; s.async = true; s.defer = true; s.id = 'google-gsi';
        s.onload = () => resolve();
        s.onerror = () => reject(new Error('Failed to load Google SDK. Check your internet connection.'));
        document.head.appendChild(s);
      });

      // @ts-ignore
      if (!window.google || !window.google.accounts || !window.google.accounts.id) {
        throw new Error('Google SDK not available after loading');
      }

      // Always use the rendered button approach to avoid One Tap issues
      const showRenderedButtonFallback = () => {
        // Avoid duplicate modal
        if (document.getElementById('gsi-fallback-modal')) return;
        const overlay = document.createElement('div');
        overlay.id = 'gsi-fallback-modal';
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.background = 'rgba(0,0,0,0.5)';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.zIndex = '9999';
        const panel = document.createElement('div');
        panel.style.background = 'white';
        panel.style.padding = '16px';
        panel.style.borderRadius = '8px';
        panel.style.minWidth = '280px';
        panel.style.textAlign = 'center';
        const title = document.createElement('div');
        title.textContent = 'Sign in with Google';
        title.style.marginBottom = '12px';
        const btnHost = document.createElement('div');
        btnHost.id = 'gsi-fallback-button';
        const close = document.createElement('button');
        close.textContent = 'Cancel';
        close.style.marginTop = '12px';
        close.onclick = () => overlay.remove();
        panel.appendChild(title);
        panel.appendChild(btnHost);
        panel.appendChild(close);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
        try {
          // @ts-ignore
          window.google.accounts.id.renderButton(btnHost, { theme: 'outline', size: 'large', type: 'standard', shape: 'rectangular' });
        } catch (e) {
          console.error('Failed to render Google button fallback', e);
        }
      };

      // Initialize Google OAuth with callback
      // @ts-ignore
      window.google.accounts.id.initialize({
        client_id: cfg.google_client_id,
        callback: async (resp: any) => {
          try {
            const tr = await exchangeGoogleToken(resp.credential);
            setUser(tr.user);
            setToken(tr.access_token);
            // Remove modal if present
            const modal = document.getElementById('gsi-fallback-modal');
            if (modal) modal.remove();
          } catch (e) {
            console.error('Google OAuth callback failed:', e);
            alert(`Sign-in failed: ${e instanceof Error ? e.message : String(e)}`);
          }
        }
      });

      // Always show the rendered button (skip problematic One Tap)
      showRenderedButtonFallback();
    } catch (e) {
      console.error('Login failed', e);
      alert(`Google sign-in failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const refreshAuth = async () => {
    const me = await getMe();
    if (me) {
      setUser(me);
      const t = localStorage.getItem('gremlins_token');
      setToken(t);
    } else {
      setUser(null);
      setToken(null);
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setToken(null);
      setUser(null);
    }
  };

  const value = useMemo(() => ({ user, token, login, logout, refreshAuth }), [user, token]);
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

