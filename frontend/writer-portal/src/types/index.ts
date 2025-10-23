// Core Types for DRYAD.AI Writer's Assistant

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  emailVerified: boolean;
  roles: string[];
  permissions: string[];
  createdAt: string;
  lastLogin?: string;
  isActive: boolean;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
  editor: {
    fontSize: number;
    fontFamily: string;
    lineHeight: number;
    wordWrap: boolean;
  };
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

export interface Document {
  id: string;
  filename: string;
  originalName: string;
  size: number;
  mimeType: string;
  uploadedAt: string;
  processedAt?: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  tags: string[];
  folderId?: string;
  metadata: DocumentMetadata;
  content?: string;
  summary?: string;
}

export interface DocumentMetadata {
  pageCount?: number;
  wordCount?: number;
  language?: string;
  author?: string;
  title?: string;
  subject?: string;
  keywords?: string[];
  createdDate?: string;
  modifiedDate?: string;
}

export interface Folder {
  id: string;
  name: string;
  description?: string;
  parentId?: string;
  createdAt: string;
  updatedAt: string;
  documentCount: number;
  color?: string;
  icon?: string;
}

export interface UploadProgress {
  fileId: string;
  filename: string;
  progress: number;
  status: 'queued' | 'uploading' | 'processing' | 'completed' | 'failed' | 'cancelled';
  error?: string;
  speed?: number;
  timeRemaining?: number;
}

export interface RAGQuery {
  id: string;
  query: string;
  response: string;
  citations: Citation[];
  timestamp: string;
  processingTime: number;
  confidence: number;
  documentIds: string[];
}

export interface Citation {
  documentId: string;
  documentName: string;
  pageNumber?: number;
  excerpt: string;
  relevanceScore: number;
  startIndex: number;
  endIndex: number;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  lastMessage?: string;
  tags: string[];
}

export interface Message {
  id: string;
  conversationId: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  citations?: Citation[];
  metadata?: {
    processingTime?: number;
    confidence?: number;
    model?: string;
  };
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
    hasMore?: boolean;
  };
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  error?: Error | string;
  errorCode?: string;
  retryable?: boolean;
}

export interface NotificationState {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary';
}

export interface SearchFilters {
  query?: string;
  tags?: string[];
  folderId?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  fileTypes?: string[];
  status?: string[];
  sortBy?: 'name' | 'date' | 'size' | 'relevance';
  sortOrder?: 'asc' | 'desc';
}

export interface DashboardStats {
  totalDocuments: number;
  totalQueries: number;
  storageUsed: number;
  storageLimit: number;
  recentActivity: ActivityItem[];
  popularTags: TagStats[];
  processingQueue: number;
}

export interface ActivityItem {
  id: string;
  type: 'upload' | 'query' | 'folder_created' | 'document_processed';
  description: string;
  timestamp: string;
  metadata?: any;
}

export interface TagStats {
  tag: string;
  count: number;
  trend: 'up' | 'down' | 'stable';
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface InputProps extends BaseComponentProps {
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  error?: string;
  label?: string;
  required?: boolean;
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Utility Types
export type Theme = 'light' | 'dark' | 'system';
export type ViewMode = 'grid' | 'list' | 'table';
export type SortDirection = 'asc' | 'desc';
export type FileStatus = 'uploading' | 'processing' | 'completed' | 'failed';
export type UserRole = 'user' | 'admin' | 'moderator';
export type Permission = 'read' | 'write' | 'delete' | 'admin';
