"""FastMCP application setup for AiChemistForge."""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, AsyncIterator

from fastmcp import FastMCP
from .config import config
from .logging import setup_logging
from ..tools.registry import ToolRegistry


logger = setup_logging(__name__, config.log_level)


@asynccontextmanager
async def app_lifespan() -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle for the unified MCP server."""

    logger.info("Starting AiChemistForge MCP server initialization")

    # Initialize tool registry
    tool_registry = ToolRegistry()

    try:
        # Auto-discover and register tools
        await tool_registry.initialize_tools()

        logger.info(f"Registered {len(tool_registry.get_all_tools())} tools")

        # Create shared context
        context = {
            "tool_registry": tool_registry,
            "config": config,
        }

        yield context

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise
    finally:
        logger.info("Shutting down AiChemistForge MCP server")
        # Cleanup would go here


def create_fastmcp_app() -> FastMCP:
    """Create and configure the FastMCP application."""

    # Create FastMCP instance
    mcp = FastMCP(
        name=config.server_name,
        version="1.0.0",
        lifespan=app_lifespan
    )

    # Register cursor database tool
    @mcp.tool()
    async def query_cursor_database(
        operation: str,
        project_name: str = None,
        table_name: str = None,
        query_type: str = None,
        key: str = None,
        limit: int = 100,
        detailed: bool = False,
        composer_id: str = None
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
            composer_id=composer_id
        )

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
                        "mimeType": "application/json"
                    }
                    for name in projects.keys()
                ]
            }

        return {"contents": []}

    return mcp


# Global FastMCP app instance
fastmcp_app = create_fastmcp_app()