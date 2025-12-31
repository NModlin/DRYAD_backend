import { api } from '../../services/api'
import { Curriculum, Course, AssessmentCriteria } from '../../types'

export const curriculumApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getCurriculums: builder.query({
      query: () => '/curriculums',
      providesTags: ['Curriculum'],
    }),
    getCurriculum: builder.query({
      query: (id: string) => `/curriculums/${id}`,
      providesTags: ['Curriculum'],
    }),
    createCurriculum: builder.mutation({
      query: (curriculumData: Partial<Curriculum>) => ({
        url: '/curriculums',
        method: 'POST',
        body: curriculumData,
      }),
      invalidatesTags: ['Curriculum'],
    }),
    updateCurriculum: builder.mutation({
      query: ({ id, data }: { id: string; data: Partial<Curriculum> }) => ({
        url: `/curriculums/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Curriculum'],
    }),
    getCourses: builder.query({
      query: () => '/courses',
      providesTags: ['Course'],
    }),
    getCourse: builder.query({
      query: (id: string) => `/courses/${id}`,
      providesTags: ['Course'],
    }),
  }),
})

export const {
  useGetCurriculumsQuery,
  useGetCurriculumQuery,
  useCreateCurriculumMutation,
  useUpdateCurriculumMutation,
  useGetCoursesQuery,
  useGetCourseQuery,
} = curriculumApi