"""Resource registry for dynamic resource discovery and management."""

from typing import Dict, List, Optional, Any, Callable, Awaitable
import importlib
import pkgutil

from ..server.config import config
from ..server.logging import setup_logging


logger = setup_logging(__name__, config.log_level)


class ResourceRegistry:
    """Registry for managing MCP resources."""

    def __init__(self):
        self.logger = setup_logging("resource.registry", config.log_level)
        self._resources: Dict[str, Callable[[], Awaitable[Dict[str, Any]]]] = {}
        self._resource_metadata: Dict[str, Dict[str, Any]] = {}

    def register_resource(
        self,
        uri: str,
        handler: Callable[[], Awaitable[Dict[str, Any]]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a resource handler.

        Args:
            uri: Resource URI (e.g., "cursor://projects")
            handler: Async function that returns resource data
            metadata: Optional metadata about the resource

        Raises:
            ValueError: If resource URI already exists
        """
        if uri in self._resources:
            raise ValueError(f"Resource '{uri}' is already registered")

        self._resources[uri] = handler
        self._resource_metadata[uri] = metadata or {}
        self.logger.debug(f"Registered resource: {uri}")

    def get_resource_handler(self, uri: str) -> Optional[Callable[[], Awaitable[Dict[str, Any]]]]:
        """Get a resource handler by URI.

        Args:
            uri: Resource URI

        Returns:
            Resource handler function or None if not found
        """
        return self._resources.get(uri)

    def get_all_resources(self) -> Dict[str, Callable[[], Awaitable[Dict[str, Any]]]]:
        """Get all registered resources.

        Returns:
            Dictionary of URI to resource handler
        """
        return self._resources.copy()

    def get_resource_uris(self) -> List[str]:
        """Get list of all registered resource URIs.

        Returns:
            List of resource URIs
        """
        return list(self._resources.keys())

    def unregister_resource(self, uri: str) -> bool:
        """Unregister a resource.

        Args:
            uri: Resource URI to unregister

        Returns:
            True if resource was unregistered, False if not found
        """
        if uri in self._resources:
            del self._resources[uri]
            self._resource_metadata.pop(uri, None)
            self.logger.debug(f"Unregistered resource: {uri}")
            return True
        return False

    async def initialize_resources(self) -> None:
        """Initialize all available resources by auto-discovery."""
        self.logger.info("Initializing resources via auto-discovery")

        # Discover and load resources from different categories
        await self._discover_resources_in_category("cursor")

        self.logger.info(f"Initialized {len(self._resources)} resources")

    async def _discover_resources_in_category(self, category: str) -> None:
        """Discover resources in a specific category.

        Args:
            category: Resource category (cursor, filesystem, etc.)
        """
        try:
            category_path = f"unified_mcp_server.resources.{category}"
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

                    # Look for resource registration function
                    if hasattr(module, 'register_resources'):
                        try:
                            await module.register_resources(self)
                            self.logger.debug(f"Registered resources from {full_module_name}")
                        except Exception as e:
                            self.logger.error(f"Failed to register resources from {module_name}: {e}")

                except Exception as e:
                    self.logger.error(f"Failed to import module {full_module_name}: {e}")

        except ImportError as e:
            self.logger.warning(f"Category {category} not found or import error: {e}")

    def get_resource_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered resources.

        Returns:
            List of resource information dictionaries
        """
        resource_info = []
        for uri, metadata in self._resource_metadata.items():
            info = {
                "uri": uri,
                "metadata": metadata,
            }
            resource_info.append(info)

        return resource_info

    def clear_all_resources(self) -> None:
        """Clear all registered resources."""
        count = len(self._resources)
        self._resources.clear()
        self._resource_metadata.clear()
        self.logger.info(f"Cleared {count} resources from registry")


# Global resource registry instance
resource_registry = ResourceRegistry()