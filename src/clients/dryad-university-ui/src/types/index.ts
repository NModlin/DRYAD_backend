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
  STUDENT = 'student', // Might map to generic user with agent view
  FACULTY = 'faculty', // Maps to user managing agents
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

// University System (Agent University)
export interface University {
  id: string
  name: string
  description?: string
  owner_user_id: string
  max_agents: number
  current_agents?: number // Computed in backend response
  settings: Record<string, any>
  status: UniversityStatus
  created_at: string
  updated_at: string
}

export type UniversityStatus = 'active' | 'inactive' | 'suspended'

// Replaces "Department" - Focus on Domain Expertise
export interface DomainExpertProfile {
  id: string
  agent_id: string
  domain_name: string
  expertise_level: string // beginner, intermediate, advanced, expert
  teaching_style: string
  success_rate: number
  created_at: string
}

// Replaces "Course"
export interface CurriculumPath {
  id: string
  university_id: string
  name: string
  description?: string
  difficulty_level: DifficultyLevel
  estimated_duration_hours: number
  prerequisites: string[]
  learning_objectives: string[]
  status: string
  created_at: string
  updated_at: string
}

export enum DifficultyLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert'
}

// Replaces "Student" and generic "Agent"
export interface UniversityAgent {
  id: string
  university_id: string
  name: string
  agent_type: string // student, professor, researcher, administrator
  status: AgentStatus
  specialization?: string
  competency_score: number
  training_hours: number
  current_curriculum_id?: string
  configuration?: Record<string, any>
  created_at: string
  updated_at: string
}

export enum AgentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  TRAINING = 'training'
}

// Competitions (New)
export interface Competition {
  id: string
  university_id: string
  name: string
  description?: string
  competition_type: string // individual, team
  status: CompetitionStatus
  participants: string[] // List of Agent IDs
  winner_id?: string
  created_at: string
}

export enum CompetitionStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

// Analytics (Updated)
export interface UniversityStats {
  total_agents: number
  active_agents: number
  total_curricula: number
  active_curricula: number
  total_competitions: number
  active_competitions: number
  capacity_usage: string
}

// Common Responses
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

// Frontend specific - keep for UI utility
export interface NavItem {
  label: string
  path: string
  icon?: any
  roles?: UserRole[]
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