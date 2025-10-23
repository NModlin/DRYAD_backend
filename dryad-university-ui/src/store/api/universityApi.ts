import { api } from '../../services/api'
import { University, Department, Course, Enrollment, PaginatedResponse } from '../../types'

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
    getDepartments: builder.query({
      query: (universityId: string) => `/universities/${universityId}/departments`,
      providesTags: ['Department'],
    }),
    getCourses: builder.query({
      query: (departmentId: string) => `/departments/${departmentId}/courses`,
      providesTags: ['Course'],
    }),
    getEnrollments: builder.query({
      query: (studentId: string) => `/students/${studentId}/enrollments`,
      providesTags: ['Enrollment'],
    }),
    createEnrollment: builder.mutation({
      query: (enrollmentData: { studentId: string; courseId: string }) => ({
        url: '/enrollments',
        method: 'POST',
        body: enrollmentData,
      }),
      invalidatesTags: ['Enrollment'],
    }),
  }),
})

export const {
  useGetUniversitiesQuery,
  useGetUniversityQuery,
  useGetDepartmentsQuery,
  useGetCoursesQuery,
  useGetEnrollmentsQuery,
  useCreateEnrollmentMutation,
} = universityApi