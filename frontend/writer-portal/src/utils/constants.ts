// Application Constants

export const APP_CONFIG = {
  name: 'DRYAD.AI Writer\'s Assistant',
  version: '2.0.0',
  description: 'AI-powered writing assistant with document analysis and RAG capabilities',
  author: 'DRYAD.AI',
  url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  apiUrl: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000',
} as const;

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  DOCUMENTS: '/documents',
  UPLOAD: '/upload',
  CHAT: '/chat',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  LOGIN: '/login',
  LOGOUT: '/logout',
} as const;

export const API_ENDPOINTS = {
  AUTH: {
    CONFIG: '/api/v1/auth/config',
    TOKEN: '/api/v1/auth/token',
    REFRESH: '/api/v1/auth/refresh',
    ME: '/api/v1/auth/me',
    LOGOUT: '/api/v1/auth/logout',
  },
  DOCUMENTS: {
    LIST: '/api/v1/documents',
    UPLOAD: '/api/v1/documents/upload',
    UPLOAD_REALTIME: '/api/v1/documents/upload/realtime',
    DELETE: '/api/v1/documents',
    SEARCH: '/api/v1/documents/search',
  },
  RAG: {
    QUERY: '/api/v1/rag/query',
    CONVERSATIONS: '/api/v1/conversations',
    MESSAGES: '/api/v1/conversations/messages',
  },
  FOLDERS: {
    LIST: '/api/v1/folders',
    CREATE: '/api/v1/folders',
    UPDATE: '/api/v1/folders',
    DELETE: '/api/v1/folders',
  },
  ANALYTICS: {
    DASHBOARD: '/api/v1/analytics/dashboard',
    USAGE: '/api/v1/analytics/usage',
  },
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'gremlins_token',
  USER_PREFERENCES: 'gremlins_preferences',
  THEME: 'gremlins_theme',
  SIDEBAR_STATE: 'gremlins_sidebar',
  RECENT_SEARCHES: 'gremlins_recent_searches',
} as const;

export const FILE_UPLOAD = {
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  MAX_FILES_PER_BATCH: 20,
  ALLOWED_TYPES: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
  ],
  CHUNK_SIZE: 1024 * 1024, // 1MB chunks
} as const;

export const UI_CONFIG = {
  ANIMATION_DURATION: 300,
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 5000,
  SIDEBAR_WIDTH: 280,
  HEADER_HEIGHT: 64,
  MOBILE_BREAKPOINT: 768,
} as const;

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
} as const;

export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
} as const;

export const DOCUMENT_STATUS = {
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export const USER_ROLES = {
  USER: 'user',
  ADMIN: 'admin',
  MODERATOR: 'moderator',
} as const;

export const PERMISSIONS = {
  READ: 'read',
  WRITE: 'write',
  DELETE: 'delete',
  ADMIN: 'admin',
} as const;

export const KEYBOARD_SHORTCUTS = {
  SEARCH: 'cmd+k',
  NEW_DOCUMENT: 'cmd+n',
  UPLOAD: 'cmd+u',
  SETTINGS: 'cmd+,',
  HELP: '?',
  TOGGLE_SIDEBAR: 'cmd+b',
  TOGGLE_THEME: 'cmd+shift+t',
} as const;

export const ERROR_CODES = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  UPLOAD_ERROR: 'UPLOAD_ERROR',
  PROCESSING_ERROR: 'PROCESSING_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

export const REGEX_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  FILENAME: /^[a-zA-Z0-9._-]+$/,
  TAG: /^[a-zA-Z0-9-_]+$/,
} as const;

export const DEFAULT_PREFERENCES = {
  theme: THEMES.SYSTEM,
  language: 'en',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  notifications: {
    email: true,
    push: true,
    desktop: false,
  },
  editor: {
    fontSize: 14,
    fontFamily: 'Inter',
    lineHeight: 1.5,
    wordWrap: true,
  },
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

export const SEARCH_CONFIG = {
  MIN_QUERY_LENGTH: 2,
  MAX_QUERY_LENGTH: 500,
  DEBOUNCE_DELAY: 300,
  MAX_RECENT_SEARCHES: 10,
} as const;
