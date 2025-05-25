"""Plugin registry for managing MCP plugin lifecycle."""

from typing import Any, Dict, List, Optional

from ...server.config import config
from ...server.logging import setup_logging
from ...utils.exceptions import ToolRegistrationError
from ..registry import ToolRegistry
from .base import BasePlugin, PluginStatus
from .discovery import PluginDiscovery
from .security import PluginSecurity


class PluginRegistry:
    """Registry for managing MCP plugin lifecycle and integration."""

    def __init__(self, tool_registry: ToolRegistry):
        self.logger = setup_logging("plugin.registry", config.log_level)
        self.tool_registry = tool_registry

        # Plugin management
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_info: Dict[str, Dict[str, Any]] = {}

        # Plugin system components
        self.discovery = PluginDiscovery()
        self.security = PluginSecurity()

        # Plugin directories from config
        plugin_dirs = getattr(config, "plugin_directories", [])
        for directory in plugin_dirs:
            self.discovery.add_plugin_directory(directory)

    async def initialize_plugins(self) -> Dict[str, Any]:
        """Initialize and load all discovered plugins.

        Returns:
            Summary of plugin initialization
        """
        self.logger.info("Starting plugin initialization...")

        # Discover plugins
        discovered = self.discovery.discover_plugins()

        results = {
            "discovered": len(discovered),
            "loaded": 0,
            "failed": 0,
            "errors": [],
        }

        # Load and register each plugin
        for plugin_info in discovered:
            try:
                plugin = await self._load_and_register_plugin(plugin_info)
                if plugin:
                    results["loaded"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"plugin": plugin_info.get("name", "unknown"), "error": str(e)}
                )
                self.logger.error(
                    f"Failed to load plugin {plugin_info.get('name')}: {e}"
                )

        self.logger.info(
            f"Plugin initialization complete. Loaded: {results['loaded']}, Failed: {results['failed']}"
        )
        return results

    async def _load_and_register_plugin(
        self, plugin_info: Dict[str, Any]
    ) -> Optional[BasePlugin]:
        """Load and register a single plugin.

        Args:
            plugin_info: Plugin information from discovery

        Returns:
            Loaded plugin instance or None if failed
        """
        plugin_name = plugin_info.get("name", "unknown")

        try:
            # Security validation
            plugin_path = plugin_info["path"]
            if not self.security.validate_plugin(plugin_path):
                self.logger.warning(f"Plugin {plugin_name} failed security validation")
                return None

            # Load plugin
            plugin = self.discovery.load_plugin(plugin_info)

            # Set plugin permissions
            permissions = self.security.get_plugin_permissions(plugin_name)
            plugin.set_permissions(permissions)

            # Set plugin configuration
            plugin_config = self._get_plugin_config(plugin_name)
            plugin.set_configuration(plugin_config)

            # Initialize plugin
            init_result = await plugin.safe_initialize()
            if not init_result.get("success", False):
                self.logger.error(
                    f"Plugin {plugin_name} initialization failed: {init_result.get('error')}"
                )
                return None

            # Register with tool registry
            self.tool_registry.register_tool(plugin)

            # Store plugin and info
            self.plugins[plugin_name] = plugin
            self.plugin_info[plugin_name] = plugin_info

            # Update status
            plugin.status = PluginStatus.ACTIVE

            self.logger.info(
                f"Successfully loaded and registered plugin: {plugin_name}"
            )
            return plugin

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise ToolRegistrationError(f"Plugin registration failed: {e}")

    async def reload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Reload a specific plugin.

        Args:
            plugin_name: Name of plugin to reload

        Returns:
            Reload operation result
        """
        try:
            if plugin_name not in self.plugins:
                return {"success": False, "error": f"Plugin {plugin_name} not found"}

            # Get plugin info for reloading
            plugin_info = self.plugin_info[plugin_name]

            # Unload existing plugin
            unload_result = await self.unload_plugin(plugin_name)
            if not unload_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Failed to unload plugin: {unload_result.get('error')}",
                }

            # Reload plugin
            new_plugin = await self._load_and_register_plugin(plugin_info)
            if new_plugin:
                return {
                    "success": True,
                    "plugin": plugin_name,
                    "status": new_plugin.status.value,
                }
            else:
                return {"success": False, "error": "Failed to reload plugin"}

        except Exception as e:
            self.logger.error(f"Failed to reload plugin {plugin_name}: {e}")
            return {"success": False, "error": str(e)}

    async def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Unload a specific plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            Unload operation result
        """
        try:
            if plugin_name not in self.plugins:
                return {"success": False, "error": f"Plugin {plugin_name} not found"}

            plugin = self.plugins[plugin_name]

            # Cleanup plugin
            cleanup_result = await plugin.safe_cleanup()

            # Unregister from tool registry
            self.tool_registry.unregister_tool(plugin_name)

            # Remove from plugin registry
            del self.plugins[plugin_name]
            del self.plugin_info[plugin_name]

            self.logger.info(f"Unloaded plugin: {plugin_name}")

            return {
                "success": True,
                "plugin": plugin_name,
                "cleanup_result": cleanup_result,
            }

        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return {"success": False, "error": str(e)}

    async def load_plugin_from_path(self, plugin_path: str) -> Dict[str, Any]:
        """Dynamically load a plugin from a specific path.

        Args:
            plugin_path: Path to plugin file or directory

        Returns:
            Load operation result
        """
        try:
            # Security validation
            if not self.security.validate_plugin(plugin_path):
                return {"success": False, "error": "Plugin failed security validation"}

            # Try to discover plugin at path
            from pathlib import Path

            path = Path(plugin_path)

            if path.is_file():
                plugin_info = self.discovery._discover_file_plugin(path)
            elif path.is_dir():
                plugin_info = self.discovery._discover_directory_plugin(path)
            else:
                return {
                    "success": False,
                    "error": f"Invalid plugin path: {plugin_path}",
                }

            if plugin_info is None:
                return {"success": False, "error": "No valid plugin found at path"}

            # Load and register plugin
            plugin = await self._load_and_register_plugin(plugin_info)
            if plugin:
                return {
                    "success": True,
                    "plugin": plugin.name,
                    "status": plugin.status.value,
                }
            else:
                return {"success": False, "error": "Failed to load plugin"}

        except Exception as e:
            self.logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            return {"success": False, "error": str(e)}

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins.

        Returns:
            Dictionary of plugin name to plugin instance
        """
        return self.plugins.copy()

    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get status information for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin status information or None if not found
        """
        plugin = self.plugins.get(plugin_name)
        if plugin is None:
            return None

        return {
            "name": plugin.name,
            "status": plugin.status.value,
            "version": plugin.get_version(),
            "description": plugin.description,
            "metadata": plugin.get_metadata().to_dict(),
            "path": str(plugin.plugin_path) if plugin.plugin_path else None,
            "permissions": plugin.permissions,
            "configuration": plugin.configuration,
        }

    def get_all_plugin_status(self) -> List[Dict[str, Any]]:
        """Get status information for all plugins.

        Returns:
            List of plugin status information
        """
        statuses = []
        for plugin_name in self.plugins:
            status = self.get_plugin_status(plugin_name)
            if status:
                statuses.append(status)
        return statuses

    def _get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin configuration dictionary
        """
        # Look for plugin-specific environment variables
        import os

        config_dict = {}

        # Plugin-specific config prefix
        prefix = f"PLUGIN_{plugin_name.upper().replace('-', '_')}_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()
                config_dict[config_key] = value

        return config_dict

    async def shutdown_all_plugins(self) -> Dict[str, Any]:
        """Shutdown all loaded plugins.

        Returns:
            Shutdown operation summary
        """
        self.logger.info("Shutting down all plugins...")

        results = {"total": len(self.plugins), "success": 0, "failed": 0, "errors": []}

        # Shutdown plugins in reverse order of loading
        plugin_names = list(self.plugins.keys())

        for plugin_name in reversed(plugin_names):
            try:
                unload_result = await self.unload_plugin(plugin_name)
                if unload_result.get("success", False):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {
                            "plugin": plugin_name,
                            "error": unload_result.get("error", "Unknown error"),
                        }
                    )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"plugin": plugin_name, "error": str(e)})

        self.logger.info(
            f"Plugin shutdown complete. Success: {results['success']}, Failed: {results['failed']}"
        )
        return results
