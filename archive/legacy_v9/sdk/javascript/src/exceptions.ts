/**
 * DRYAD.AI JavaScript/TypeScript SDK Exceptions
 * 
 * Custom error classes for the DRYAD.AI platform.
 */

/**
 * Base exception class for all DRYAD.AI errors
 */
export class DRYAD.AIError extends Error {
  public readonly name: string;
  public readonly statusCode?: number;
  public readonly details?: any;

  constructor(message: string, statusCode?: number, details?: any) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.details = details;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert error to JSON representation
   */
  toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      statusCode: this.statusCode,
      details: this.details,
      stack: this.stack,
    };
  }

  /**
   * Get a user-friendly error message
   */
  getUserMessage(): string {
    return this.message;
  }
}

/**
 * API-related errors (4xx, 5xx HTTP status codes)
 */
export class APIError extends DRYAD.AIError {
  constructor(message: string, statusCode: number, details?: any) {
    super(message, statusCode, details);
  }

  getUserMessage(): string {
    switch (this.statusCode) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication failed. Please check your API key.';
      case 403:
        return 'Access denied. You do not have permission to perform this action.';
      case 404:
        return 'Resource not found. Please check the URL and try again.';
      case 429:
        return 'Rate limit exceeded. Please wait before making more requests.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.';
      case 503:
        return 'Service unavailable. Please try again later.';
      case 504:
        return 'Gateway timeout. The request took too long to process.';
      default:
        return this.message;
    }
  }
}

/**
 * Validation errors (400 Bad Request)
 */
export class ValidationError extends APIError {
  public readonly validationErrors?: Record<string, string[]>;

  constructor(message: string, statusCode: number = 400, validationErrors?: Record<string, string[]>) {
    super(message, statusCode, { validationErrors });
    this.validationErrors = validationErrors;
  }

  getUserMessage(): string {
    if (this.validationErrors) {
      const errors = Object.entries(this.validationErrors)
        .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
        .join('; ');
      return `Validation failed: ${errors}`;
    }
    return 'Invalid input data. Please check your request and try again.';
  }
}

/**
 * Authentication errors (401 Unauthorized)
 */
export class AuthenticationError extends APIError {
  constructor(message: string, statusCode: number = 401, details?: any) {
    super(message, statusCode, details);
  }

  getUserMessage(): string {
    return 'Authentication failed. Please check your API key and try again.';
  }
}

/**
 * Rate limiting errors (429 Too Many Requests)
 */
export class RateLimitError extends APIError {
  public readonly retryAfter?: number;

  constructor(message: string, statusCode: number = 429, retryAfter?: number) {
    super(message, statusCode, { retryAfter });
    this.retryAfter = retryAfter;
  }

  getUserMessage(): string {
    if (this.retryAfter) {
      return `Rate limit exceeded. Please wait ${this.retryAfter} seconds before trying again.`;
    }
    return 'Rate limit exceeded. Please wait before making more requests.';
  }
}

/**
 * Connection errors (network issues, timeouts)
 */
export class ConnectionError extends DRYAD.AIError {
  constructor(message: string, details?: any) {
    super(message, undefined, details);
  }

  getUserMessage(): string {
    return 'Connection failed. Please check your internet connection and try again.';
  }
}

/**
 * Timeout errors
 */
export class TimeoutError extends DRYAD.AIError {
  public readonly timeout?: number;

  constructor(message: string, timeout?: number) {
    super(message, undefined, { timeout });
    this.timeout = timeout;
  }

  getUserMessage(): string {
    if (this.timeout) {
      return `Request timed out after ${this.timeout}ms. Please try again.`;
    }
    return 'Request timed out. Please try again.';
  }
}

/**
 * WebSocket-related errors
 */
export class WebSocketError extends DRYAD.AIError {
  public readonly code?: number;

  constructor(message: string, code?: number, details?: any) {
    super(message, undefined, details);
    this.code = code;
  }

  getUserMessage(): string {
    switch (this.code) {
      case 1000:
        return 'WebSocket connection closed normally.';
      case 1001:
        return 'WebSocket connection closed due to endpoint going away.';
      case 1002:
        return 'WebSocket connection closed due to protocol error.';
      case 1003:
        return 'WebSocket connection closed due to unsupported data type.';
      case 1006:
        return 'WebSocket connection closed abnormally.';
      case 1011:
        return 'WebSocket connection closed due to server error.';
      default:
        return this.message || 'WebSocket connection error occurred.';
    }
  }
}

/**
 * Configuration errors
 */
export class ConfigurationError extends DRYAD.AIError {
  constructor(message: string, details?: any) {
    super(message, undefined, details);
  }

  getUserMessage(): string {
    return 'Configuration error. Please check your client configuration.';
  }
}

/**
 * File upload errors
 */
export class FileUploadError extends DRYAD.AIError {
  public readonly filename?: string;
  public readonly fileSize?: number;

  constructor(message: string, filename?: string, fileSize?: number) {
    super(message, undefined, { filename, fileSize });
    this.filename = filename;
    this.fileSize = fileSize;
  }

  getUserMessage(): string {
    if (this.filename) {
      return `Failed to upload file "${this.filename}". ${this.message}`;
    }
    return `File upload failed. ${this.message}`;
  }
}

/**
 * Utility function to create appropriate error from HTTP response
 */
export function createErrorFromResponse(
  status: number,
  message: string,
  data?: any
): DRYAD.AIError {
  switch (status) {
    case 400:
      return new ValidationError(message, status, data?.validation_errors);
    case 401:
      return new AuthenticationError(message, status, data);
    case 429:
      return new RateLimitError(message, status, data?.retry_after);
    case 404:
    case 403:
    case 500:
    case 502:
    case 503:
    case 504:
      return new APIError(message, status, data);
    default:
      return new DRYAD.AIError(message, status, data);
  }
}

/**
 * Utility function to check if error is retryable
 */
export function isRetryableError(error: DRYAD.AIError): boolean {
  if (error instanceof ConnectionError || error instanceof TimeoutError) {
    return true;
  }

  if (error instanceof APIError) {
    // Retry on server errors (5xx) but not client errors (4xx)
    return error.statusCode ? error.statusCode >= 500 : false;
  }

  return false;
}

/**
 * Utility function to get retry delay for retryable errors
 */
export function getRetryDelay(error: DRYAD.AIError, attempt: number, baseDelay: number = 1000): number {
  if (error instanceof RateLimitError && error.retryAfter) {
    return error.retryAfter * 1000; // Convert to milliseconds
  }

  // Exponential backoff with jitter
  const delay = baseDelay * Math.pow(2, attempt - 1);
  const jitter = Math.random() * 0.1 * delay;
  return delay + jitter;
}

// Export all error types
export {
  DRYAD.AIError as default,
  DRYAD.AIError,
  APIError,
  ValidationError,
  AuthenticationError,
  RateLimitError,
  ConnectionError,
  TimeoutError,
  WebSocketError,
  ConfigurationError,
  FileUploadError,
};
