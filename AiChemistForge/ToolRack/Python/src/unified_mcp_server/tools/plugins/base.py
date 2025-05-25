"""Base plugin interface for the unified MCP server."""

import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ...server.config import config
from ...server.logging import setup_logging
from ...utils.exceptions import ToolValidationError
from ...utils.validators import validate_path, validate_string


# Define ToolError locally to avoid circular import
class ToolError(Exception):
    """Base exception for tool-related errors."""

    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    pass


class PluginStatus(Enum):
    """Plugin lifecycle status."""

    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    description: str
    author: str = ""
    email: str = ""
    license: str = ""
    homepage: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    mcp_version: str = "2025-03-26"  # MCP protocol version
    python_version: str = ">=3.8"

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "email": self.email,
            "license": self.license,
            "homepage": self.homepage,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "mcp_version": self.mcp_version,
            "python_version": self.python_version,
        }


class BasePlugin(ABC):
    """Base class for all MCP plugins.

    Extends BaseTool functionality with plugin-specific features following
    MCP protocol specifications for dynamic tool registration.
    """

    def __init__(
        self, name: str, description: str, metadata: Optional[PluginMetadata] = None
    ):
        self.name = name
        self.description = description
        self.metadata = metadata or PluginMetadata(
            name=name, version="1.0.0", description=description
        )
        self.status = PluginStatus.DISCOVERED
        self.plugin_path: Optional[Path] = None
        self.configuration: Dict[str, Any] = {}
        self.permissions: Dict[str, bool] = {}

        # Plugin-specific logger
        self.logger = setup_logging(f"plugin.{name}", config.log_level)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the plugin with given parameters.

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
        """Get the JSON schema for plugin parameters.

        Returns:
            JSON schema dictionary
        """
        pass

    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate plugin parameters against schema.

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
        """Safely execute plugin with error handling.

        Args:
            **kwargs: Plugin parameters

        Returns:
            Standardized plugin result
        """
        try:
            # Validate parameters
            validated_params = self.validate_parameters(**kwargs)

            # Execute plugin
            result = await self.execute(**validated_params)

            return {"success": True, "result": result, "tool": self.name}

        except ToolValidationError as e:
            self.logger.error(f"Validation error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Parameter validation failed: {e}",
                "tool": self.name,
            }

        except ToolExecutionError as e:
            self.logger.error(f"Execution error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {e}",
                "tool": self.name,
            }

        except Exception as e:
            self.logger.error(f"Unexpected error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "tool": self.name,
            }

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin.

        Called when the plugin is loaded. Override to perform
        any setup required by the plugin.

        Raises:
            ToolError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup the plugin.

        Called when the plugin is unloaded. Override to perform
        any cleanup required by the plugin.
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get the plugin version.

        Returns:
            Version string
        """
        return self.metadata.version

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            Plugin metadata
        """
        return self.metadata

    def set_configuration(self, config: Dict[str, Any]) -> None:
        """Set plugin configuration.

        Args:
            config: Configuration dictionary
        """
        self.configuration = config.copy()
        self.logger.debug(f"Configuration set for plugin {self.name}")

    def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.configuration.get(key, default)

    def set_permissions(self, permissions: Dict[str, bool]) -> None:
        """Set plugin permissions.

        Args:
            permissions: Permission dictionary
        """
        self.permissions = permissions.copy()
        self.logger.debug(f"Permissions set for plugin {self.name}")

    def has_permission(self, permission: str) -> bool:
        """Check if plugin has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if permission is granted
        """
        return self.permissions.get(permission, False)

    def validate_mcp_compliance(self) -> bool:
        """Validate that the plugin follows MCP protocol specifications.

        Returns:
            True if plugin is MCP compliant

        Raises:
            ToolValidationError: If plugin is not compliant
        """
        # Check required methods
        required_methods = ["execute", "get_schema", "initialize", "cleanup"]
        for method in required_methods:
            if not hasattr(self, method) or not callable(getattr(self, method)):
                raise ToolValidationError(
                    f"Plugin {self.name} missing required method: {method}"
                )

        # Validate schema
        try:
            schema = self.get_schema()
            if not isinstance(schema, dict):
                raise ToolValidationError(
                    f"Plugin {self.name} schema must be a dictionary"
                )
        except Exception as e:
            raise ToolValidationError(
                f"Plugin {self.name} failed schema validation: {e}"
            )

        # Validate metadata
        if not self.metadata.name:
            raise ToolValidationError(f"Plugin {self.name} missing metadata name")

        if not self.metadata.version:
            raise ToolValidationError(f"Plugin {self.name} missing metadata version")

        self.logger.debug(f"Plugin {self.name} passed MCP compliance validation")
        return True

    def to_mcp_tool_definition(self) -> Dict[str, Any]:
        """Convert plugin to MCP tool definition format.

        Returns:
            MCP tool definition following protocol specifications
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.get_schema(),
            "metadata": self.metadata.to_dict(),
        }

    async def safe_initialize(self) -> Dict[str, Any]:
        """Safely initialize the plugin with error handling.

        Returns:
            Initialization result
        """
        try:
            self.status = PluginStatus.LOADING
            await self.initialize()
            self.status = PluginStatus.LOADED

            return {"success": True, "plugin": self.name, "status": self.status.value}

        except Exception as e:
            self.status = PluginStatus.ERROR
            self.logger.error(f"Failed to initialize plugin {self.name}: {e}")

            return {
                "success": False,
                "plugin": self.name,
                "status": self.status.value,
                "error": str(e),
            }

    async def safe_cleanup(self) -> Dict[str, Any]:
        """Safely cleanup the plugin with error handling.

        Returns:
            Cleanup result
        """
        try:
            self.status = PluginStatus.UNLOADING
            await self.cleanup()
            self.status = PluginStatus.UNLOADED

            return {"success": True, "plugin": self.name, "status": self.status.value}

        except Exception as e:
            self.status = PluginStatus.ERROR
            self.logger.error(f"Failed to cleanup plugin {self.name}: {e}")

            return {
                "success": False,
                "plugin": self.name,
                "status": self.status.value,
                "error": str(e),
            }


def load_plugin_from_file(plugin_path: Path) -> Type[BasePlugin]:
    """Load a plugin class from a Python file.

    Args:
        plugin_path: Path to the plugin file

    Returns:
        Plugin class

    Raises:
        ToolError: If plugin loading fails
    """
    try:
        # Validate path
        validated_path = validate_path(
            plugin_path, must_exist=True, must_be_file=True, allowed_extensions=[".py"]
        )

        # Load module from file
        spec = importlib.util.spec_from_file_location(
            f"plugin_{validated_path.stem}", validated_path
        )

        if spec is None or spec.loader is None:
            raise ToolError(f"Cannot load plugin spec from {validated_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin class
        plugin_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePlugin)
                and attr is not BasePlugin
            ):
                plugin_classes.append(attr)

        if not plugin_classes:
            raise ToolError(f"No plugin class found in {validated_path}")

        if len(plugin_classes) > 1:
            raise ToolError(f"Multiple plugin classes found in {validated_path}")

        return plugin_classes[0]

    except Exception as e:
        raise ToolError(f"Failed to load plugin from {plugin_path}: {e}")


def create_plugin_metadata_from_dict(metadata_dict: Dict[str, Any]) -> PluginMetadata:
    """Create plugin metadata from a dictionary.

    Args:
        metadata_dict: Metadata dictionary

    Returns:
        PluginMetadata instance
    """
    return PluginMetadata(
        name=validate_string(metadata_dict.get("name", ""), "name"),
        version=validate_string(metadata_dict.get("version", "1.0.0"), "version"),
        description=validate_string(
            metadata_dict.get("description", ""), "description"
        ),
        author=metadata_dict.get("author", ""),
        email=metadata_dict.get("email", ""),
        license=metadata_dict.get("license", ""),
        homepage=metadata_dict.get("homepage", ""),
        tags=metadata_dict.get("tags", []),
        dependencies=metadata_dict.get("dependencies", []),
        mcp_version=metadata_dict.get("mcp_version", "2025-03-26"),
        python_version=metadata_dict.get("python_version", ">=3.8"),
    )
