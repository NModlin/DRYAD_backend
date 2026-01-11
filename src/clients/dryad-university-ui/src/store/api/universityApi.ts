import { api } from '../../services/api'
import { University } from '../../types'

export const universityApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getUniversities: builder.query({
      query: () => '/universities',
      providesTags: ['University'],
    }),
    getUniversity: builder.query({
      query: (id: string) => `/universities/${id}`,
      providesTags: ['University'],
    }),
    getUniversityStats: builder.query({
      query: (id: string) => `/universities/${id}/stats`,
      providesTags: ['University'],
    }),
    getAgents: builder.query({
      query: (universityId: string) => `/universities/${universityId}/agents`,
      providesTags: ['Agent'],
    }),
    getCurricula: builder.query({
      query: (universityId: string) => `/curriculum?university_id=${universityId}`,
      providesTags: ['Curriculum'],
    }),
    getCompetitions: builder.query({
      query: (universityId: string) => `/competitions?university_id=${universityId}`, // Assuming endpoint supports filtering
      providesTags: ['Competition'],
    }),
    createUniversity: builder.mutation({
      query: (data: Partial<University>) => ({
        url: '/universities',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['University'],
    }),
  }),
})

export const {
  useGetUniversitiesQuery,
  useGetUniversityQuery,
  useGetUniversityStatsQuery,
  useGetAgentsQuery,
  useGetCurriculaQuery,
  useGetCompetitionsQuery,
  useCreateUniversityMutation,
} = universityApi