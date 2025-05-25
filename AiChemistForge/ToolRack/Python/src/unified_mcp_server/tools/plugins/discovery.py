"""Plugin discovery system for the unified MCP server."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...server.config import config
from ...server.logging import setup_logging
from ...utils.exceptions import SecurityError, ToolError
from ...utils.security import validate_path
from .base import (
    BasePlugin,
    PluginMetadata,
    create_plugin_metadata_from_dict,
    load_plugin_from_file,
)


class PluginDiscovery:
    """Discovers and loads plugins from external directories."""

    def __init__(self, plugin_directories: Optional[List[str]] = None):
        self.logger = setup_logging("plugin.discovery", config.log_level)

        # Default plugin directories
        self.plugin_directories = plugin_directories or [
            "plugins/",
            "~/.aichemistforge/plugins/",
            "./custom_plugins/",
        ]

        # Convert to Path objects and validate
        self.validated_directories: List[Path] = []
        self._validate_plugin_directories()

    def _validate_plugin_directories(self) -> None:
        """Validate and resolve plugin directories."""
        for directory in self.plugin_directories:
            try:
                path = Path(directory).expanduser().resolve()
                if path.exists() and path.is_dir():
                    self.validated_directories.append(path)
                    self.logger.debug(f"Added plugin directory: {path}")
                else:
                    self.logger.warning(f"Plugin directory does not exist: {path}")
            except Exception as e:
                self.logger.error(f"Invalid plugin directory {directory}: {e}")

    def add_plugin_directory(self, directory: str) -> bool:
        """Add a new plugin directory.

        Args:
            directory: Path to plugin directory

        Returns:
            True if directory was added successfully
        """
        try:
            path = Path(directory).expanduser().resolve()

            # Security validation
            validate_path(path)

            if not path.exists():
                self.logger.warning(f"Plugin directory does not exist: {path}")
                return False

            if not path.is_dir():
                self.logger.error(f"Plugin path is not a directory: {path}")
                return False

            if path not in self.validated_directories:
                self.validated_directories.append(path)
                self.logger.info(f"Added plugin directory: {path}")
                return True
            else:
                self.logger.debug(f"Plugin directory already exists: {path}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to add plugin directory {directory}: {e}")
            return False

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """Discover all plugins in configured directories.

        Returns:
            List of discovered plugin information
        """
        discovered_plugins = []

        for directory in self.validated_directories:
            self.logger.debug(f"Scanning plugin directory: {directory}")

            try:
                plugins_in_dir = self._scan_directory(directory)
                discovered_plugins.extend(plugins_in_dir)

            except Exception as e:
                self.logger.error(f"Error scanning plugin directory {directory}: {e}")

        self.logger.info(f"Discovered {len(discovered_plugins)} plugins")
        return discovered_plugins

    def _scan_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Scan a single directory for plugins.

        Args:
            directory: Directory to scan

        Returns:
            List of plugin information dictionaries
        """
        plugins = []

        # Look for Python files and plugin directories
        for item in directory.iterdir():
            try:
                if (
                    item.is_file()
                    and item.suffix == ".py"
                    and not item.name.startswith("_")
                ):
                    # Single file plugin
                    plugin_info = self._discover_file_plugin(item)
                    if plugin_info:
                        plugins.append(plugin_info)

                elif item.is_dir() and not item.name.startswith("."):
                    # Directory-based plugin
                    plugin_info = self._discover_directory_plugin(item)
                    if plugin_info:
                        plugins.append(plugin_info)

            except Exception as e:
                self.logger.warning(f"Error processing plugin {item}: {e}")

        return plugins

    def _discover_file_plugin(self, plugin_file: Path) -> Optional[Dict[str, Any]]:
        """Discover a single-file plugin.

        Args:
            plugin_file: Path to plugin file

        Returns:
            Plugin information dictionary or None
        """
        try:
            # Security validation
            validate_path(plugin_file)

            # Try to load the plugin class
            plugin_class = load_plugin_from_file(plugin_file)

            # Get metadata from class attributes
            class_metadata = getattr(plugin_class, "metadata", None)

            if class_metadata is None:
                # Create default metadata from class attributes
                metadata = PluginMetadata(
                    name=getattr(plugin_class, "tool_name", plugin_file.stem),
                    version=getattr(plugin_class, "version", "1.0.0"),
                    description=getattr(plugin_class, "__doc__", "").strip()
                    or plugin_file.stem,
                )
            else:
                metadata = class_metadata

            return {
                "type": "file",
                "path": str(plugin_file),
                "class": plugin_class,
                "metadata": metadata,
                "name": metadata.name,
            }

        except Exception as e:
            self.logger.warning(f"Failed to discover file plugin {plugin_file}: {e}")
            return None

    def _discover_directory_plugin(self, plugin_dir: Path) -> Optional[Dict[str, Any]]:
        """Discover a directory-based plugin.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Plugin information dictionary or None
        """
        try:
            # Security validation
            validate_path(plugin_dir)

            # Look for plugin.py or __init__.py
            plugin_files = [plugin_dir / "plugin.py", plugin_dir / "__init__.py"]

            plugin_file = None
            for file_path in plugin_files:
                if file_path.exists():
                    plugin_file = file_path
                    break

            if plugin_file is None:
                self.logger.debug(f"No plugin entry point found in {plugin_dir}")
                return None

            # Look for metadata file
            metadata_file = plugin_dir / "plugin.json"
            metadata = None

            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata_dict = json.load(f)
                    metadata = create_plugin_metadata_from_dict(metadata_dict)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to load metadata from {metadata_file}: {e}"
                    )

            # Load plugin class
            plugin_class = load_plugin_from_file(plugin_file)

            # Use metadata from file or create default
            if metadata is None:
                class_metadata = getattr(plugin_class, "metadata", None)

                if class_metadata is None:
                    metadata = PluginMetadata(
                        name=getattr(plugin_class, "tool_name", plugin_dir.name),
                        version=getattr(plugin_class, "version", "1.0.0"),
                        description=getattr(plugin_class, "__doc__", "").strip()
                        or plugin_dir.name,
                    )
                else:
                    metadata = class_metadata

            return {
                "type": "directory",
                "path": str(plugin_dir),
                "entry_point": str(plugin_file),
                "metadata_file": str(metadata_file) if metadata_file.exists() else None,
                "class": plugin_class,
                "metadata": metadata,
                "name": metadata.name,
            }

        except Exception as e:
            self.logger.warning(
                f"Failed to discover directory plugin {plugin_dir}: {e}"
            )
            return None

    def load_plugin(self, plugin_info: Dict[str, Any]) -> BasePlugin:
        """Load a plugin from discovery information.

        Args:
            plugin_info: Plugin information from discovery

        Returns:
            Loaded plugin instance

        Raises:
            ToolError: If plugin loading fails
        """
        try:
            plugin_class = plugin_info["class"]
            metadata = plugin_info["metadata"]

            # Create plugin instance
            plugin = plugin_class(
                name=metadata.name, description=metadata.description, metadata=metadata
            )

            # Set plugin path for reference
            plugin.plugin_path = Path(plugin_info["path"])

            # Validate MCP compliance
            plugin.validate_mcp_compliance()

            self.logger.debug(f"Loaded plugin: {plugin.name}")
            return plugin

        except Exception as e:
            raise ToolError(f"Failed to load plugin {plugin_info['name']}: {e}")

    def get_plugin_directories(self) -> List[str]:
        """Get list of configured plugin directories.

        Returns:
            List of plugin directory paths
        """
        return [str(directory) for directory in self.validated_directories]

    def validate_plugin_security(self, plugin_path: Path) -> bool:
        """Validate plugin security requirements.

        Args:
            plugin_path: Path to plugin

        Returns:
            True if plugin passes security validation

        Raises:
            SecurityError: If security validation fails
        """
        try:
            # Path traversal check
            validate_path(plugin_path)

            # Ensure plugin is in allowed directories
            plugin_resolved = plugin_path.resolve()
            allowed = False

            for allowed_dir in self.validated_directories:
                if str(plugin_resolved).startswith(str(allowed_dir.resolve())):
                    allowed = True
                    break

            if not allowed:
                raise SecurityError(
                    f"Plugin {plugin_path} not in allowed directories",
                    error_code="PLUGIN_PATH_NOT_ALLOWED",
                    context={
                        "plugin_path": str(plugin_path),
                        "allowed_directories": [
                            str(d) for d in self.validated_directories
                        ],
                    },
                )

            # Check file permissions (readable but not executable for security)
            if not plugin_path.is_file():
                raise SecurityError(f"Plugin {plugin_path} is not a regular file")

            return True

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Plugin security validation failed: {e}")
