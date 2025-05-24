"""Base tool interface for the unified MCP server."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
import logging

from ..server.config import config
from ..server.logging import setup_logging


T = TypeVar('T', bound='BaseTool')
logger = setup_logging(__name__, config.log_level)


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class BaseTool(ABC):
    """Base class for all MCP tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = setup_logging(f"tool.{name}", config.log_level)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ToolValidationError: If parameters are invalid
            ToolExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters.

        Returns:
            JSON schema dictionary
        """
        pass

    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate tool parameters against schema.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Validated parameters

        Raises:
            ToolValidationError: If validation fails
        """
        # Implementation would use JSON schema validation
        # For now, return as-is
        return kwargs

    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """Safely execute tool with error handling.

        Args:
            **kwargs: Tool parameters

        Returns:
            Standardized tool result
        """
        try:
            # Validate parameters
            validated_params = self.validate_parameters(**kwargs)

            # Execute tool
            result = await self.execute(**validated_params)

            return {
                "success": True,
                "result": result,
                "tool": self.name
            }

        except ToolValidationError as e:
            self.logger.error(f"Validation error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Parameter validation failed: {e}",
                "tool": self.name
            }

        except ToolExecutionError as e:
            self.logger.error(f"Execution error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {e}",
                "tool": self.name
            }

        except Exception as e:
            self.logger.error(f"Unexpected error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "tool": self.name
            }