import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store/store'
import { useAuthQuery } from '../store/api/authApi'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (credentials: { email: string; password: string }) => void
  logout: () => void
  refreshToken: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthenticationProviderProps {
  children: ReactNode
}

export const AuthenticationProvider: React.FC<AuthenticationProviderProps> = ({ children }) => {
  const dispatch = useDispatch<AppDispatch>()
  const { user, token, isAuthenticated, isLoading, error } = useSelector((state: RootState) => state.auth)
  
  const { data: userData, error: authError, refetch } = useAuthQuery(undefined, {
    skip: !token,
  })

  useEffect(() => {
    if (token && !user) {
      refetch()
    }
  }, [token, user, refetch])

  useEffect(() => {
    if (userData) {
      // Update user data in store
      // This would typically be handled by the auth slice
    }
  }, [userData, dispatch])

  const login = async (credentials: { email: string; password: string }) => {
    // This would dispatch the login action
    // For now, we'll handle it through the API
    console.log('Login attempt:', credentials)
  }

  const logout = () => {
    dispatch({ type: 'auth/logout' })
  }

  const refreshToken = async () => {
    // Token refresh logic would go here
    console.log('Refreshing token...')
  }

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
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
    throw new Error('useAuth must be used within an AuthenticationProvider')
  }
  return context
}