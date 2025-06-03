import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';

// First, let's create a dedicated errors module
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export interface ErrorMetadata {
  command?: string;
  originalCommand?: string;
  workingDir?: string;
  shell?: string;
  errorCode?: number;
  severity: ErrorSeverity;
  timestamp: string;
  [key: string]: unknown;
}

export class CLIServerError extends Error {
  public readonly severity: ErrorSeverity;
  public readonly metadata: ErrorMetadata;
  public readonly originalError?: Error;

  constructor(
    message: string,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    metadata: Partial<ErrorMetadata> = {},
    originalError?: Error
  ) {
    super(message);
    this.name = 'CLIServerError';
    this.severity = severity;
    this.originalError = originalError;
    this.metadata = {
      ...metadata,
      severity,
      timestamp: new Date().toISOString()
    };
  }

  toMcpError(): McpError {
    return new McpError(
      ErrorCode.InvalidRequest,
      this.message,
      this.metadata
    );
  }
}