import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, AuthState, LoginCredentials, RegisterData } from '../types'
import { authAPI } from '../services/api'

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // Check for existing token on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('dryad_token')
        if (token) {
          // Verify token is still valid
          const user = await authAPI.verifyToken(token)
          setAuthState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          })
        } else {
          setAuthState(prev => ({ ...prev, isLoading: false }))
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
        localStorage.removeItem('dryad_token')
        setAuthState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        })
      }
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }))
      
      const response = await authAPI.login(credentials)
      const { user, token } = response

      localStorage.setItem('dryad_token', token)
      setAuthState({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }))
      throw error
    }
  }

  const register = async (data: RegisterData) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }))
      
      const response = await authAPI.register(data)
      const { user, token } = response

      localStorage.setItem('dryad_token', token)
      setAuthState({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }))
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('dryad_token')
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
  }

  const refreshToken = async () => {
    try {
      const token = authState.token
      if (!token) throw new Error('No token available')

      const response = await authAPI.refreshToken(token)
      const { user, token: newToken } = response

      localStorage.setItem('dryad_token', newToken)
      setAuthState({
        user,
        token: newToken,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      logout()
      throw error
    }
  }

  const value: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}