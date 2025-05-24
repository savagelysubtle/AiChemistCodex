"""Tool registry for dynamic tool discovery and management."""

from typing import Dict, List, Optional, Type
import importlib
import pkgutil
from pathlib import Path

from .base import BaseTool
from ..server.config import config
from ..server.logging import setup_logging


class ToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self):
        self.logger = setup_logging("tool.registry", config.log_level)
        self._tools: Dict[str, BaseTool] = {}
        self._tool_modules: Dict[str, str] = {}

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
        await self._discover_tools_in_category("web")
        await self._discover_tools_in_category("system")

        self.logger.info(f"Initialized {len(self._tools)} tools")

    async def _discover_tools_in_category(self, category: str) -> None:
        """Discover tools in a specific category.

        Args:
            category: Tool category (database, filesystem, etc.)
        """
        try:
            category_path = f"unified_mcp_server.tools.{category}"
            category_module = importlib.import_module(category_path)

            # Get the package path for the category
            if hasattr(category_module, '__path__'):
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

                        if (isinstance(attr, type) and
                            issubclass(attr, BaseTool) and
                            attr is not BaseTool):

                            try:
                                # Instantiate the tool
                                tool_instance = attr()
                                self.register_tool(tool_instance)
                                self._tool_modules[tool_instance.name] = full_module_name

                                self.logger.debug(f"Loaded tool {tool_instance.name} from {full_module_name}")

                            except Exception as e:
                                self.logger.error(f"Failed to instantiate tool {attr_name}: {e}")

                except Exception as e:
                    self.logger.error(f"Failed to import module {full_module_name}: {e}")

        except ImportError as e:
            self.logger.warning(f"Category {category} not found or import error: {e}")

    def get_tool_info(self) -> List[Dict[str, str]]:
        """Get information about all registered tools.

        Returns:
            List of tool information dictionaries
        """
        tool_info = []
        for name, tool in self._tools.items():
            info = {
                "name": name,
                "description": tool.description,
                "module": self._tool_modules.get(name, "unknown"),
                "type": tool.__class__.__name__
            }
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