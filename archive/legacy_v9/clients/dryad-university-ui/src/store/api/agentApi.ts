import { api } from '../../services/api'
import { Agent, TrainingSession, PerformanceMetrics } from '../../types'

export const agentApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getAgents: builder.query({
      query: () => '/agents',
      providesTags: ['Agent'],
    }),
    getAgent: builder.query({
      query: (id: string) => `/agents/${id}`,
      providesTags: ['Agent'],
    }),
    createAgent: builder.mutation({
      query: (agentData: Partial<Agent>) => ({
        url: '/agents',
        method: 'POST',
        body: agentData,
      }),
      invalidatesTags: ['Agent'],
    }),
    updateAgent: builder.mutation({
      query: ({ id, data }: { id: string; data: Partial<Agent> }) => ({
        url: `/agents/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Agent'],
    }),
    getTrainingSessions: builder.query({
      query: (agentId: string) => `/agents/${agentId}/training-sessions`,
      providesTags: ['TrainingSession'],
    }),
    startTraining: builder.mutation({
      query: (trainingData: { agentId: string; curriculumId: string }) => ({
        url: '/training-sessions',
        method: 'POST',
        body: trainingData,
      }),
      invalidatesTags: ['TrainingSession'],
    }),
  }),
})

export const {
  useGetAgentsQuery,
  useGetAgentQuery,
  useCreateAgentMutation,
  useUpdateAgentMutation,
  useGetTrainingSessionsQuery,
  useStartTrainingMutation,
} = agentApi