import { api } from '../../services/api'
import { UniversityAgent } from '../../types'

export const agentApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getAgents: builder.query({
      query: (universityId: string) => `/universities/${universityId}/agents`,
      providesTags: ['Agent'],
    }),
    getAgent: builder.query({
      query: (id: string) => `/agents/${id}`, // NOTE: Backend might need this endpoint exposed globally or under university
      providesTags: ['Agent'],
    }),
    createAgent: builder.mutation({
      query: (agentData: Partial<UniversityAgent>) => ({
        url: '/agents', // specific endpoint to be verified
        method: 'POST',
        body: agentData,
      }),
      invalidatesTags: ['Agent'],
    }),
    updateAgent: builder.mutation({
      query: ({ id, data }: { id: string; data: Partial<UniversityAgent> }) => ({
        url: `/agents/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Agent'],
    }),
    // Training sessions might be under specific expert sessions now
  }),
})

export const {
  useGetAgentsQuery,
  useGetAgentQuery,
  useCreateAgentMutation,
  useUpdateAgentMutation,
} = agentApi