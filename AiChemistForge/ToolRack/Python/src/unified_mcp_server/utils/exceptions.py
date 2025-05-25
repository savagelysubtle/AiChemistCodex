"""Custom exceptions for the unified MCP server."""

from typing import Any, Dict, Optional


class UnifiedMCPError(Exception):
    """Base exception for all unified MCP server errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }


class ServerError(UnifiedMCPError):
    """Raised when server infrastructure encounters an error."""

    pass


class ConfigurationError(ServerError):
    """Raised when configuration is invalid or missing."""

    pass


class ToolError(UnifiedMCPError):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found."""

    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    pass


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    pass


class ToolRegistrationError(ToolError):
    """Raised when tool registration fails."""

    pass


class ResourceError(UnifiedMCPError):
    """Base exception for resource-related errors."""

    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource is not found."""

    pass


class ResourceAccessError(ResourceError):
    """Raised when resource access is denied or fails."""

    pass


class PromptError(UnifiedMCPError):
    """Base exception for prompt-related errors."""

    pass


class PromptNotFoundError(PromptError):
    """Raised when a requested prompt is not found."""

    pass


class PromptExecutionError(PromptError):
    """Raised when prompt execution fails."""

    pass


class SecurityError(UnifiedMCPError):
    """Base exception for security-related errors."""

    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal attack is detected."""

    pass


class ValidationError(UnifiedMCPError):
    """Base exception for validation errors."""

    pass


class InputValidationError(ValidationError):
    """Raised when input validation fails."""

    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""

    pass


class DatabaseError(UnifiedMCPError):
    """Base exception for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class DatabaseQueryError(DatabaseError):
    """Raised when database query fails."""

    pass


class FilesystemError(UnifiedMCPError):
    """Base exception for filesystem-related errors."""

    pass


class FileNotFoundError(FilesystemError):
    """Raised when a file is not found."""

    pass


class DirectoryNotFoundError(FilesystemError):
    """Raised when a directory is not found."""

    pass


class PermissionError(FilesystemError):
    """Raised when file/directory permission is denied."""

    pass


class TransportError(UnifiedMCPError):
    """Base exception for transport-related errors."""

    pass


class StdioTransportError(TransportError):
    """Raised when stdio transport encounters an error."""

    pass


class SSETransportError(TransportError):
    """Raised when SSE transport encounters an error."""

    pass


class CacheError(UnifiedMCPError):
    """Base exception for cache-related errors."""

    pass


class CacheMissError(CacheError):
    """Raised when cache entry is not found."""

    pass


class CacheInvalidationError(CacheError):
    """Raised when cache invalidation fails."""

    pass


class MetricsError(UnifiedMCPError):
    """Base exception for metrics-related errors."""

    pass


class MonitoringError(UnifiedMCPError):
    """Base exception for monitoring-related errors."""

    pass


# Convenience functions for creating common exceptions


def tool_not_found(tool_name: str) -> ToolNotFoundError:
    """Create a ToolNotFoundError with consistent formatting."""
    return ToolNotFoundError(
        message=f"Tool '{tool_name}' not found",
        error_code="TOOL_NOT_FOUND",
        context={"tool_name": tool_name},
    )


def resource_not_found(resource_uri: str) -> ResourceNotFoundError:
    """Create a ResourceNotFoundError with consistent formatting."""
    return ResourceNotFoundError(
        message=f"Resource '{resource_uri}' not found",
        error_code="RESOURCE_NOT_FOUND",
        context={"resource_uri": resource_uri},
    )


def prompt_not_found(prompt_name: str) -> PromptNotFoundError:
    """Create a PromptNotFoundError with consistent formatting."""
    return PromptNotFoundError(
        message=f"Prompt '{prompt_name}' not found",
        error_code="PROMPT_NOT_FOUND",
        context={"prompt_name": prompt_name},
    )


def path_traversal_detected(path: str) -> PathTraversalError:
    """Create a PathTraversalError with consistent formatting."""
    return PathTraversalError(
        message=f"Path traversal attack detected: {path}",
        error_code="PATH_TRAVERSAL",
        context={"attempted_path": path},
    )


def validation_failed(field: str, value: Any, reason: str) -> InputValidationError:
    """Create an InputValidationError with consistent formatting."""
    return InputValidationError(
        message=f"Validation failed for field '{field}': {reason}",
        error_code="VALIDATION_FAILED",
        context={"field": field, "value": str(value), "reason": reason},
    )
