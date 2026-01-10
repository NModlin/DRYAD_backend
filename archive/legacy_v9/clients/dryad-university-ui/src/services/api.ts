import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { RootState } from '../store/store'
import { AuthResponse } from '../types'

const baseQuery = fetchBaseQuery({
  baseUrl: 'http://localhost:8000/api/v1',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    headers.set('content-type', 'application/json')
    return headers
  },
})

const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  let result = await baseQuery(args, api, extraOptions)
  
  if (result.error && result.error.status === 401) {
    // Try to refresh token
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
        body: { refreshToken: localStorage.getItem('refreshToken') },
      },
      api,
      extraOptions
    )
    
    if (refreshResult.data) {
      const authData = refreshResult.data as AuthResponse
      localStorage.setItem('token', authData.token)
      localStorage.setItem('refreshToken', authData.refreshToken)
      
      // Retry the original request with new token
      result = await baseQuery(args, api, extraOptions)
    } else {
      // Refresh failed, logout user
      api.dispatch({ type: 'auth/logout' })
    }
  }
  
  return result
}

export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'User',
    'University',
    'Department',
    'Course',
    'Enrollment',
    'Agent',
    'TrainingSession',
    'Curriculum',
    'Analytics',
  ],
  endpoints: () => ({}),
})

// Error handling utility
export const handleApiError = (error: any): string => {
  if (typeof error === 'string') {
    return error
  }
  
  if (error?.data?.error) {
    return error.data.error
  }
  
  if (error?.status === 401) {
    return 'Authentication failed. Please log in again.'
  }
  
  if (error?.status === 403) {
    return 'You do not have permission to perform this action.'
  }
  
  if (error?.status === 404) {
    return 'Resource not found.'
  }
  
  if (error?.status === 500) {
    return 'Server error. Please try again later.'
  }
  
  return 'An unexpected error occurred. Please try again.'
}