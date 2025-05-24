"""Prompt registry for dynamic prompt discovery and management."""

from typing import Dict, List, Optional, Any, Callable, Awaitable
import importlib
import pkgutil

from ..server.config import config
from ..server.logging import setup_logging


logger = setup_logging(__name__, config.log_level)


class PromptRegistry:
    """Registry for managing MCP prompts."""

    def __init__(self):
        self.logger = setup_logging("prompt.registry", config.log_level)
        self._prompts: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}
        self._prompt_metadata: Dict[str, Dict[str, Any]] = {}

    def register_prompt(
        self,
        name: str,
        handler: Callable[..., Awaitable[Dict[str, Any]]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a prompt handler.

        Args:
            name: Prompt name (e.g., "analyze_cursor_project")
            handler: Async function that returns prompt data
            metadata: Optional metadata about the prompt

        Raises:
            ValueError: If prompt name already exists
        """
        if name in self._prompts:
            raise ValueError(f"Prompt '{name}' is already registered")

        self._prompts[name] = handler
        self._prompt_metadata[name] = metadata or {}
        self.logger.debug(f"Registered prompt: {name}")

    def get_prompt_handler(self, name: str) -> Optional[Callable[..., Awaitable[Dict[str, Any]]]]:
        """Get a prompt handler by name.

        Args:
            name: Prompt name

        Returns:
            Prompt handler function or None if not found
        """
        return self._prompts.get(name)

    def get_all_prompts(self) -> Dict[str, Callable[..., Awaitable[Dict[str, Any]]]]:
        """Get all registered prompts.

        Returns:
            Dictionary of name to prompt handler
        """
        return self._prompts.copy()

    def get_prompt_names(self) -> List[str]:
        """Get list of all registered prompt names.

        Returns:
            List of prompt names
        """
        return list(self._prompts.keys())

    def unregister_prompt(self, name: str) -> bool:
        """Unregister a prompt.

        Args:
            name: Prompt name to unregister

        Returns:
            True if prompt was unregistered, False if not found
        """
        if name in self._prompts:
            del self._prompts[name]
            self._prompt_metadata.pop(name, None)
            self.logger.debug(f"Unregistered prompt: {name}")
            return True
        return False

    async def initialize_prompts(self) -> None:
        """Initialize all available prompts by auto-discovery."""
        self.logger.info("Initializing prompts via auto-discovery")

        # Discover and load prompts from different categories
        await self._discover_prompts_in_category("analysis")

        self.logger.info(f"Initialized {len(self._prompts)} prompts")

    async def _discover_prompts_in_category(self, category: str) -> None:
        """Discover prompts in a specific category.

        Args:
            category: Prompt category (analysis, workflow, etc.)
        """
        try:
            category_path = f"unified_mcp_server.prompts.{category}"
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

                    # Look for prompt registration function
                    if hasattr(module, 'register_prompts'):
                        try:
                            await module.register_prompts(self)
                            self.logger.debug(f"Registered prompts from {full_module_name}")
                        except Exception as e:
                            self.logger.error(f"Failed to register prompts from {module_name}: {e}")

                except Exception as e:
                    self.logger.error(f"Failed to import module {full_module_name}: {e}")

        except ImportError as e:
            self.logger.warning(f"Category {category} not found or import error: {e}")

    def get_prompt_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered prompts.

        Returns:
            List of prompt information dictionaries
        """
        prompt_info = []
        for name, metadata in self._prompt_metadata.items():
            info = {
                "name": name,
                "metadata": metadata,
            }
            prompt_info.append(info)

        return prompt_info

    def clear_all_prompts(self) -> None:
        """Clear all registered prompts."""
        count = len(self._prompts)
        self._prompts.clear()
        self._prompt_metadata.clear()
        self.logger.info(f"Cleared {count} prompts from registry")


# Global prompt registry instance
prompt_registry = PromptRegistry()