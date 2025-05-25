"""FastMCP application setup for AiChemistForge."""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

from fastmcp import FastMCP

# Remove plugin registry import to avoid circular dependency
# from ..tools.plugins.registry import PluginRegistry
from ..tools.registry import ToolRegistry
from .config import config
from .logging import setup_logging

logger = setup_logging(__name__, config.log_level)


@asynccontextmanager
async def app_lifespan(app) -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle for the unified MCP server."""

    logger.info("Starting AiChemistForge MCP server initialization")

    # Initialize tool registry
    tool_registry = ToolRegistry()

    # Import plugin registry here to avoid circular dependency
    try:
        from ..tools.plugins.registry import PluginRegistry

        # Initialize plugin registry
        plugin_registry = PluginRegistry(tool_registry)
        # Connect plugin registry to tool registry
        tool_registry.set_plugin_registry(plugin_registry)
    except ImportError as e:
        logger.warning(f"Plugin system not available: {e}")
        plugin_registry = None

    try:
        # Auto-discover and register tools (including plugins)
        await tool_registry.initialize_tools()

        logger.info(f"Registered {len(tool_registry.get_all_tools())} total tools")

        # Log summary
        summary = tool_registry.get_tool_summary()
        logger.info(
            f"Tool summary: {summary['builtin_tools']} builtin, {summary['plugins']} plugins"
        )

        # Create shared context
        context = {
            "tool_registry": tool_registry,
            "plugin_registry": plugin_registry,
            "config": config,
        }

        yield context

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise
    finally:
        logger.info("Shutting down AiChemistForge MCP server")

        # Shutdown plugins first
        if plugin_registry:
            try:
                await plugin_registry.shutdown_all_plugins()
                logger.info("Plugin system shutdown completed")
            except Exception as e:
                logger.error(f"Error shutting down plugins: {e}")


def create_fastmcp_app() -> FastMCP:
    """Create and configure the FastMCP application."""

    # Create FastMCP instance
    mcp = FastMCP(name=config.server_name, version="1.0.0", lifespan=app_lifespan)

    # Register cursor database tool
    @mcp.tool()
    async def query_cursor_database(
        operation: str,
        project_name: Optional[str] = None,
        table_name: Optional[str] = None,
        query_type: Optional[str] = None,
        key: Optional[str] = None,
        limit: int = 100,
        detailed: bool = False,
        composer_id: Optional[str] = None,
    ) -> dict:
        """Query Cursor IDE databases and manage database operations.

        Args:
            operation: Operation to perform (list_projects, query_table, refresh_databases, get_chat_data, get_composer_ids, get_composer_data)
            project_name: Name of the project (required for project-specific operations)
            table_name: Database table to query (ItemTable or cursorDiskKV)
            query_type: Type of query (get_all, get_by_key, search_keys)
            key: Key for get_by_key or search pattern for search_keys
            limit: Maximum number of results (default: 100)
            detailed: Return detailed project information (default: False)
            composer_id: Composer ID for get_composer_data operation
        """

        # Get tool registry from context
        context = mcp.get_context()
        if not context:
            return {"error": "Server context not available"}

        tool_registry = context.get("tool_registry")
        if not tool_registry:
            return {"error": "Tool registry not available"}

        cursor_tool = tool_registry.get_tool("cursor_db")
        if not cursor_tool:
            return {"error": "cursor_db tool not available"}

        return await cursor_tool.safe_execute(
            operation=operation,
            project_name=project_name,
            table_name=table_name,
            query_type=query_type,
            key=key,
            limit=limit,
            detailed=detailed,
            composer_id=composer_id,
        )

    # Register file tree tool
    @mcp.tool()
    async def file_tree(
        path: str = ".",
        max_depth: int = 5,
        show_hidden: bool = False,
        show_sizes: bool = True,
        format: str = "tree",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> dict:
        """Generate a file tree structure from a directory path.

        Args:
            path: Directory path to analyze (defaults to current directory)
            max_depth: Maximum depth to traverse (default: 5)
            show_hidden: Whether to show hidden files (default: False)
            show_sizes: Whether to show file sizes (default: True)
            format: Output format 'tree' or 'json' (default: 'tree')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
        """
        context = mcp.get_context()
        if not context:
            return {"error": "Server context not available"}

        tool_registry = context.get("tool_registry")
        if not tool_registry:
            return {"error": "Tool registry not available"}

        file_tree_tool = tool_registry.get_tool("file_tree")
        if not file_tree_tool:
            return {"error": "file_tree tool not available"}

        return await file_tree_tool.safe_execute(
            path=path,
            max_depth=max_depth,
            show_hidden=show_hidden,
            show_sizes=show_sizes,
            format=format,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
        )

    # Register codebase ingest tool
    @mcp.tool()
    async def codebase_ingest(
        path: str = ".",
        max_file_size: int = 1048576,
        include_binary: bool = False,
        output_format: str = "structured",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        show_tree: bool = True,
        max_files: int = 1000,
        encoding: str = "utf-8",
    ) -> dict:
        """Ingest entire codebase as structured text for LLM context.

        Args:
            path: Root directory path to ingest (defaults to current directory)
            max_file_size: Maximum file size in bytes to include (default: 1MB)
            include_binary: Whether to attempt reading binary files (default: False)
            output_format: 'structured' or 'markdown' (default: 'structured')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            show_tree: Whether to include directory tree (default: True)
            max_files: Maximum number of files to process (default: 1000)
            encoding: Text encoding to use (default: 'utf-8')
        """
        context = mcp.get_context()
        if not context:
            return {"error": "Server context not available"}

        tool_registry = context.get("tool_registry")
        if not tool_registry:
            return {"error": "Tool registry not available"}

        codebase_tool = tool_registry.get_tool("codebase_ingest")
        if not codebase_tool:
            return {"error": "codebase_ingest tool not available"}

        return await codebase_tool.safe_execute(
            path=path,
            max_file_size=max_file_size,
            include_binary=include_binary,
            output_format=output_format,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
            show_tree=show_tree,
            max_files=max_files,
            encoding=encoding,
        )

    # Register plugin management tool
    @mcp.tool()
    async def manage_plugins(
        operation: str,
        plugin_name: Optional[str] = None,
        plugin_path: Optional[str] = None,
    ) -> dict:
        """Manage plugins (load, unload, reload, status).

        Args:
            operation: Operation to perform (list, status, load, unload, reload, load_from_path)
            plugin_name: Name of the plugin (required for plugin-specific operations)
            plugin_path: Path to plugin file or directory (required for load_from_path)
        """
        context = mcp.get_context()
        if not context:
            return {"error": "Server context not available"}

        plugin_registry = context.get("plugin_registry")
        if not plugin_registry:
            return {"error": "Plugin registry not available"}

        try:
            if operation == "list":
                plugins = plugin_registry.get_all_plugins()
                return {
                    "success": True,
                    "plugins": list(plugins.keys()),
                    "count": len(plugins),
                }

            elif operation == "status":
                if plugin_name:
                    status = plugin_registry.get_plugin_status(plugin_name)
                    if status:
                        return {"success": True, "status": status}
                    else:
                        return {
                            "success": False,
                            "error": f"Plugin {plugin_name} not found",
                        }
                else:
                    statuses = plugin_registry.get_all_plugin_status()
                    return {"success": True, "statuses": statuses}

            elif operation == "load_from_path":
                if not plugin_path:
                    return {
                        "success": False,
                        "error": "plugin_path required for load_from_path operation",
                    }

                result = await plugin_registry.load_plugin_from_path(plugin_path)
                return result

            elif operation == "unload":
                if not plugin_name:
                    return {
                        "success": False,
                        "error": "plugin_name required for unload operation",
                    }

                result = await plugin_registry.unload_plugin(plugin_name)
                return result

            elif operation == "reload":
                if not plugin_name:
                    return {
                        "success": False,
                        "error": "plugin_name required for reload operation",
                    }

                result = await plugin_registry.reload_plugin(plugin_name)
                return result

            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"Plugin management error: {e}")
            return {"success": False, "error": str(e)}

    # Register resources
    @mcp.resource("cursor://projects")
    async def list_cursor_projects() -> dict:
        """List all available Cursor projects."""
        context = mcp.get_context()
        if not context:
            return {"error": "Server context not available"}

        tool_registry = context.get("tool_registry")
        cursor_tool = tool_registry.get_tool("cursor_db") if tool_registry else None

        if not cursor_tool:
            return {"contents": []}

        result = await cursor_tool.safe_execute(operation="list_projects")

        if result.get("success", False):
            projects = result.get("result", {})
            return {
                "contents": [
                    {
                        "uri": f"cursor://projects/{name}",
                        "name": name,
                        "mimeType": "application/json",
                    }
                    for name in projects.keys()
                ]
            }

        return {"contents": []}

    return mcp


# Global FastMCP app instance
fastmcp_app = create_fastmcp_app()
