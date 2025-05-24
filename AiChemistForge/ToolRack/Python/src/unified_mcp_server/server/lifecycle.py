"""Application lifecycle management for the unified MCP server."""

import asyncio
import signal
import sys
from typing import Any, Dict, Optional, Callable, Awaitable
from contextlib import asynccontextmanager

from .config import config
from .logging import setup_logging
from ..tools.registry import ToolRegistry


logger = setup_logging(__name__, config.log_level)


class LifecycleManager:
    """Manages application lifecycle events and graceful shutdown."""

    def __init__(self):
        self.tool_registry: Optional[ToolRegistry] = None
        self.shutdown_event = asyncio.Event()
        self.startup_tasks: list[Callable[[], Awaitable[Any]]] = []
        self.shutdown_tasks: list[Callable[[], Awaitable[Any]]] = []
        self._signal_handlers_registered = False

    def add_startup_task(self, task: Callable[[], Awaitable[Any]]) -> None:
        """Add a task to run during startup."""
        self.startup_tasks.append(task)

    def add_shutdown_task(self, task: Callable[[], Awaitable[Any]]) -> None:
        """Add a task to run during shutdown."""
        self.shutdown_tasks.append(task)

    def register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        if self._signal_handlers_registered:
            return

        def signal_handler(signum: int, frame) -> None:
            """Handle shutdown signals."""
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_event.set()

        # Register signal handlers for graceful shutdown
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            self._signal_handlers_registered = True
            logger.debug("Signal handlers registered")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")

    async def startup(self) -> Dict[str, Any]:
        """Run startup sequence and return application context."""
        logger.info("Starting application lifecycle...")

        # Initialize tool registry
        self.tool_registry = ToolRegistry()

        try:
            # Run startup tasks
            for task in self.startup_tasks:
                try:
                    await task()
                except Exception as e:
                    logger.error(f"Startup task failed: {e}")
                    raise

            # Auto-discover and register tools
            await self.tool_registry.initialize_tools()
            logger.info(f"Registered {len(self.tool_registry.get_all_tools())} tools")

            # Create application context
            context = {
                "tool_registry": self.tool_registry,
                "config": config,
                "lifecycle_manager": self,
            }

            logger.info("Application startup completed successfully")
            return context

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Run shutdown sequence and cleanup resources."""
        logger.info("Starting application shutdown...")

        # Run shutdown tasks in reverse order
        for task in reversed(self.shutdown_tasks):
            try:
                await task()
            except Exception as e:
                logger.error(f"Shutdown task failed: {e}")

        # Clear tool registry
        if self.tool_registry:
            self.tool_registry.clear_all_tools()

        logger.info("Application shutdown completed")

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()

    @asynccontextmanager
    async def lifespan(self):
        """Async context manager for application lifespan."""
        context = await self.startup()
        try:
            yield context
        finally:
            await self.shutdown()


# Global lifecycle manager instance
lifecycle_manager = LifecycleManager()