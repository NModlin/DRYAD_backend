import { api } from '../../services/api'
import { CurriculumPath } from '../../types'

export const curriculumApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getCurricula: builder.query({
      query: (universityId?: string) => universityId ? `/curriculum?university_id=${universityId}` : '/curriculum',
      providesTags: ['Curriculum'],
    }),
    getCurriculum: builder.query({
      query: (id: string) => `/curriculum/${id}`,
      providesTags: ['Curriculum'],
    }),
    createCurriculum: builder.mutation({
      query: (curriculumData: Partial<CurriculumPath>) => ({
        url: '/curriculum',
        method: 'POST',
        body: curriculumData,
      }),
      invalidatesTags: ['Curriculum'],
    }),
    updateCurriculum: builder.mutation({
      query: ({ id, data }: { id: string; data: Partial<CurriculumPath> }) => ({
        url: `/curriculum/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Curriculum'],
    }),
  }),
})

export const {
  useGetCurriculaQuery,
  useGetCurriculumQuery,
  useCreateCurriculumMutation,
  useUpdateCurriculumMutation,
} = curriculumApi