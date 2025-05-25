"""Tool registry for dynamic tool discovery and management."""

import importlib
import pkgutil
from typing import TYPE_CHECKING, Dict, List, Optional

from ..server.config import config
from ..server.logging import setup_logging
from .base import BaseTool

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    pass


class ToolRegistry:
    """Registry for managing MCP tools and plugins."""

    def __init__(self):
        self.logger = setup_logging("tool.registry", config.log_level)
        self._tools: Dict[str, BaseTool] = {}
        self._tool_modules: Dict[str, str] = {}

        # Plugin system integration
        self._plugin_registry = None

    def set_plugin_registry(self, plugin_registry) -> None:
        """Set the plugin registry for integration.

        Args:
            plugin_registry: PluginRegistry instance
        """
        self._plugin_registry = plugin_registry
        self.logger.debug("Plugin registry integration enabled")

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools.

        Returns:
            Dictionary of tool name to tool instance
        """
        return self._tools.copy()

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    async def initialize_tools(self) -> None:
        """Initialize all available tools by auto-discovery."""
        self.logger.info("Initializing tools via auto-discovery")

        # Discover and load tools from different categories
        await self._discover_tools_in_category("database")
        await self._discover_tools_in_category("filesystem")
        # Remove non-existent categories to prevent import errors
        # await self._discover_tools_in_category("web")
        # await self._discover_tools_in_category("system")

        # Initialize plugins if plugin registry is available
        if self._plugin_registry:
            await self._initialize_plugins()

        self.logger.info(f"Initialized {len(self._tools)} tools")

    async def _initialize_plugins(self) -> None:
        """Initialize plugin system if available."""
        try:
            self.logger.info("Initializing plugin system...")
            result = await self._plugin_registry.initialize_plugins()

            plugin_count = result.get("loaded", 0)
            if plugin_count > 0:
                self.logger.info(f"Loaded {plugin_count} plugins successfully")

            if result.get("failed", 0) > 0:
                self.logger.warning(f"Failed to load {result['failed']} plugins")

        except Exception as e:
            self.logger.error(f"Plugin system initialization failed: {e}")

    async def _discover_tools_in_category(self, category: str) -> None:
        """Discover tools in a specific category.

        Args:
            category: Tool category (database, filesystem, etc.)
        """
        try:
            category_path = f"unified_mcp_server.tools.{category}"
            category_module = importlib.import_module(category_path)

            # Get the package path for the category
            if hasattr(category_module, "__path__"):
                package_path = category_module.__path__
            else:
                self.logger.warning(f"Category {category} is not a package")
                return

            # Iterate through modules in the category
            for finder, module_name, ispkg in pkgutil.iter_modules(package_path):
                if ispkg:
                    continue

                full_module_name = f"{category_path}.{module_name}"

                try:
                    # Import the module
                    module = importlib.import_module(full_module_name)

                    # Look for tool classes that inherit from BaseTool
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseTool)
                            and attr is not BaseTool
                        ):
                            try:
                                # Instantiate the tool
                                tool_instance = attr()
                                self.register_tool(tool_instance)
                                self._tool_modules[tool_instance.name] = (
                                    full_module_name
                                )

                                self.logger.debug(
                                    f"Loaded tool {tool_instance.name} from {full_module_name}"
                                )

                            except Exception as e:
                                self.logger.error(
                                    f"Failed to instantiate tool {attr_name}: {e}"
                                )

                except Exception as e:
                    self.logger.error(
                        f"Failed to import module {full_module_name}: {e}"
                    )

        except ImportError as e:
            self.logger.warning(f"Category {category} not found or import error: {e}")

    def get_tool_info(self) -> List[Dict[str, str]]:
        """Get information about all registered tools.

        Returns:
            List of tool information dictionaries
        """
        tool_info = []
        for name, tool in self._tools.items():
            # Check if it's a plugin by checking for plugin-specific attributes
            is_plugin = hasattr(tool, "plugin_path") and hasattr(tool, "metadata")

            info = {
                "name": name,
                "description": tool.description,
                "module": self._tool_modules.get(name, "unknown"),
                "type": tool.__class__.__name__,
                "category": "plugin" if is_plugin else "builtin",
            }

            # Add plugin-specific information only if it's actually a plugin
            if is_plugin:
                plugin_path = getattr(tool, "plugin_path", None)
                if plugin_path:
                    info["plugin_path"] = str(plugin_path)

                # Get version safely
                if hasattr(tool, "get_version"):
                    try:
                        info["plugin_version"] = tool.get_version()
                    except Exception:
                        info["plugin_version"] = "unknown"
                else:
                    info["plugin_version"] = "unknown"

            tool_info.append(info)

        return tool_info

    def reload_tool(self, name: str) -> bool:
        """Reload a specific tool (useful for development).

        Args:
            name: Tool name to reload

        Returns:
            True if reloaded successfully, False otherwise
        """
        if name not in self._tools:
            self.logger.error(f"Tool {name} not found for reload")
            return False

        tool = self._tools[name]

        # Check if it's a plugin
        if hasattr(tool, "plugin_path") and tool.plugin_path is not None:
            # Delegate plugin reload to plugin registry
            if self._plugin_registry:
                try:
                    import asyncio

                    result = asyncio.create_task(
                        self._plugin_registry.reload_plugin(name)
                    )
                    return result.result().get("success", False)
                except Exception as e:
                    self.logger.error(f"Failed to reload plugin {name}: {e}")
                    return False
            else:
                self.logger.error("Plugin registry not available for reload")
                return False

        # Handle builtin tool reload
        module_name = self._tool_modules.get(name)
        if not module_name:
            self.logger.error(f"Module for tool {name} not found")
            return False

        try:
            # Remove the tool
            tool_class = self._tools[name].__class__
            self.unregister_tool(name)

            # Reload the module
            module = importlib.import_module(module_name)
            importlib.reload(module)

            # Find and reinstantiate the tool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if attr is tool_class:
                    new_instance = attr()
                    self.register_tool(new_instance)
                    self._tool_modules[new_instance.name] = module_name
                    self.logger.info(f"Reloaded tool: {name}")
                    return True

            self.logger.error(f"Could not find tool class after reload: {name}")
            return False

        except Exception as e:
            self.logger.error(f"Failed to reload tool {name}: {e}")
            return False

    def clear_all_tools(self) -> None:
        """Clear all registered tools."""
        count = len(self._tools)
        self._tools.clear()
        self._tool_modules.clear()
        self.logger.info(f"Cleared {count} tools from registry")

    def get_plugins(self) -> Dict[str, BaseTool]:
        """Get all registered plugins.

        Returns:
            Dictionary of plugin name to plugin instance
        """
        plugins = {}
        for name, tool in self._tools.items():
            if hasattr(tool, "plugin_path") and tool.plugin_path is not None:
                plugins[name] = tool
        return plugins

    def get_builtin_tools(self) -> Dict[str, BaseTool]:
        """Get all builtin (non-plugin) tools.

        Returns:
            Dictionary of tool name to tool instance
        """
        builtin_tools = {}
        for name, tool in self._tools.items():
            if not (hasattr(tool, "plugin_path") and tool.plugin_path is not None):
                builtin_tools[name] = tool
        return builtin_tools

    async def load_plugin_from_path(self, plugin_path: str) -> bool:
        """Load a plugin from a specific path.

        Args:
            plugin_path: Path to plugin file or directory

        Returns:
            True if plugin was loaded successfully
        """
        if not self._plugin_registry:
            self.logger.error("Plugin registry not available")
            return False

        try:
            result = await self._plugin_registry.load_plugin_from_path(plugin_path)
            return result.get("success", False)
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            return False

    def get_tool_summary(self) -> Dict[str, any]:
        """Get a summary of all registered tools.

        Returns:
            Summary dictionary with counts and categories
        """
        total_tools = len(self._tools)
        plugins = self.get_plugins()
        builtin_tools = self.get_builtin_tools()

        return {
            "total_tools": total_tools,
            "builtin_tools": len(builtin_tools),
            "plugins": len(plugins),
            "categories": {
                "database": len(
                    [
                        t
                        for t in builtin_tools.values()
                        if "database" in t.__class__.__module__
                    ]
                ),
                "filesystem": len(
                    [
                        t
                        for t in builtin_tools.values()
                        if "filesystem" in t.__class__.__module__
                    ]
                ),
                "plugins": len(plugins),
            },
            "tool_names": list(self._tools.keys()),
        }
