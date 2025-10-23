import { api } from '../../services/api'
import { AnalyticsData, TrendData, ComparisonData } from '../../types'

export const analyticsApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getAnalytics: builder.query({
      query: (params: { period: string; metrics: string[] }) => ({
        url: '/analytics',
        params,
      }),
      providesTags: ['Analytics'],
    }),
    getTrends: builder.query({
      query: (params: { metric: string; period: string }) => ({
        url: '/analytics/trends',
        params,
      }),
      providesTags: ['Analytics'],
    }),
    getComparisons: builder.query({
      query: (params: { period: string }) => ({
        url: '/analytics/comparisons',
        params,
      }),
      providesTags: ['Analytics'],
    }),
    getAgentPerformance: builder.query({
      query: (agentId: string) => `/analytics/agents/${agentId}/performance`,
      providesTags: ['Analytics'],
    }),
    getSystemMetrics: builder.query({
      query: () => '/analytics/system',
      providesTags: ['Analytics'],
    }),
  }),
})

export const {
  useGetAnalyticsQuery,
  useGetTrendsQuery,
  useGetComparisonsQuery,
  useGetAgentPerformanceQuery,
  useGetSystemMetricsQuery,
} = analyticsApi