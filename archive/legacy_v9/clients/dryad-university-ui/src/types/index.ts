// Core user and authentication types
export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  firstName: string
  lastName: string
  avatar?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
}

export enum UserRole {
  STUDENT = 'student',
  FACULTY = 'faculty',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin'
}

// Authentication types
export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthResponse {
  user: User
  token: string
  refreshToken: string
  expiresIn: number
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

// University system types
export interface University {
  id: string
  name: string
  code: string
  description?: string
  logo?: string
  website?: string
  contactEmail: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface Department {
  id: string
  universityId: string
  name: string
  code: string
  description?: string
  headOfDepartment?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface Course {
  id: string
  departmentId: string
  name: string
  code: string
  description?: string
  credits: number
  duration: number // in weeks
  level: CourseLevel
  prerequisites?: string[]
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export enum CourseLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert'
}

export interface Enrollment {
  id: string
  studentId: string
  courseId: string
  enrollmentDate: string
  status: EnrollmentStatus
  progress: number // percentage
  grade?: number
  completedAt?: string
  createdAt: string
  updatedAt: string
}

export enum EnrollmentStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  DROPPED = 'dropped',
  SUSPENDED = 'suspended'
}

// Agent and AI training types
export interface Agent {
  id: string
  name: string
  description?: string
  type: AgentType
  status: AgentStatus
  model: string
  parameters: Record<string, any>
  trainingData?: string[]
  performanceMetrics: PerformanceMetrics
  createdBy: string
  createdAt: string
  updatedAt: string
}

export enum AgentType {
  CHATBOT = 'chatbot',
  ANALYTICAL = 'analytical',
  CREATIVE = 'creative',
  SPECIALIZED = 'specialized'
}

export enum AgentStatus {
  DRAFT = 'draft',
  TRAINING = 'training',
  ACTIVE = 'active',
  PAUSED = 'paused',
  ARCHIVED = 'archived'
}

export interface PerformanceMetrics {
  accuracy?: number
  precision?: number
  recall?: number
  f1Score?: number
  trainingTime?: number
  inferenceSpeed?: number
  uptime?: number
}

export interface TrainingSession {
  id: string
  agentId: string
  curriculumId: string
  status: TrainingStatus
  progress: number
  startTime: string
  endTime?: string
  metrics: TrainingMetrics
  logs: TrainingLog[]
  createdAt: string
  updatedAt: string
}

export enum TrainingStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface TrainingMetrics {
  loss: number[]
  accuracy: number[]
  learningRate: number
  epoch: number
  batchSize: number
}

export interface TrainingLog {
  timestamp: string
  level: LogLevel
  message: string
  metadata?: Record<string, any>
}

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

// Curriculum and learning path types
export interface Curriculum {
  id: string
  name: string
  description?: string
  level: CurriculumLevel
  duration: number // in weeks
  courses: CurriculumCourse[]
  prerequisites?: string[]
  learningObjectives: string[]
  assessmentCriteria: AssessmentCriteria[]
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export enum CurriculumLevel {
  FOUNDATION = 'foundation',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  MASTERY = 'mastery'
}

export interface CurriculumCourse {
  courseId: string
  order: number
  required: boolean
  weight: number // percentage of curriculum
}

export interface AssessmentCriteria {
  type: AssessmentType
  weight: number
  passingScore: number
  description: string
}

export enum AssessmentType {
  QUIZ = 'quiz',
  PROJECT = 'project',
  EXAM = 'exam',
  PRACTICAL = 'practical',
  PEER_REVIEW = 'peer_review'
}

// Analytics and reporting types
export interface AnalyticsData {
  period: string
  metrics: AnalyticsMetrics
  trends: TrendData[]
  comparisons: ComparisonData[]
}

export interface AnalyticsMetrics {
  totalUsers: number
  activeUsers: number
  newEnrollments: number
  completionRate: number
  averageProgress: number
  agentTrainingSuccessRate: number
  systemUptime: number
}

export interface TrendData {
  date: string
  value: number
  change?: number
}

export interface ComparisonData {
  metric: string
  current: number
  previous: number
  change: number
  changePercentage: number
}

// API response types
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
  timestamp: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface ErrorResponse {
  success: false
  error: string
  code: string
  details?: any
  timestamp: string
}

// Form and validation types
export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'date'
  required: boolean
  placeholder?: string
  options?: { value: string; label: string }[]
  validation?: {
    min?: number
    max?: number
    pattern?: string
    custom?: (value: any) => string | null
  }
}

export interface FormState {
  values: Record<string, any>
  errors: Record<string, string>
  touched: Record<string, boolean>
  isValid: boolean
  isSubmitting: boolean
}

// UI component types
export interface TableColumn<T> {
  key: keyof T | string
  label: string
  sortable?: boolean
  searchable?: boolean
  render?: (value: any, row: T) => React.ReactNode
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface TableConfig<T> {
  columns: TableColumn<T>[]
  data: T[]
  loading?: boolean
  pagination?: PaginationConfig
  sort?: SortConfig
  search?: SearchConfig
  onRowClick?: (row: T) => void
}

export interface PaginationConfig {
  current: number
  total: number
  limit: number
  onChange: (page: number) => void
}

export interface SortConfig {
  field: string
  direction: 'asc' | 'desc'
  onChange: (field: string, direction: 'asc' | 'desc') => void
}

export interface SearchConfig {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

// Chart and visualization types
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
}

export interface ChartOptions {
  responsive: boolean
  maintainAspectRatio?: boolean
  plugins?: {
    legend?: {
      position?: 'top' | 'bottom' | 'left' | 'right'
    }
    title?: {
      display: boolean
      text: string
    }
  }
  scales?: {
    x?: any
    y?: any
  }
}

// WebSocket and real-time types
export interface WebSocketMessage {
  type: string
  payload: any
  timestamp: string
}

export interface RealTimeUpdate {
  entity: string
  action: 'create' | 'update' | 'delete'
  data: any
  timestamp: string
}

// Notification types
export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  read: boolean
  actionUrl?: string
  createdAt: string
}

export enum NotificationType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
  SYSTEM = 'system'
}

// File and upload types
export interface FileUpload {
  id: string
  name: string
  size: number
  type: string
  url: string
  uploadDate: string
  status: 'uploading' | 'completed' | 'failed'
  progress: number
}