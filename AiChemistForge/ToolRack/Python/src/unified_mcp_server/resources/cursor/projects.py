"""Cursor IDE project resources for MCP."""

from typing import Dict, Any, List
import json

from ...server.logging import setup_logging
from ...tools.registry import ToolRegistry


logger = setup_logging(__name__)


async def list_cursor_projects() -> Dict[str, Any]:
    """List all available Cursor projects as MCP resource."""
    try:
        # Get tool registry and cursor tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        cursor_tool = tool_registry.get_tool("cursor_db")

        if not cursor_tool:
            return {
                "contents": [],
                "error": "cursor_db tool not available"
            }

        # Get project list
        result = await cursor_tool.safe_execute(operation="list_projects", detailed=True)

        if not result.get("success", False):
            return {
                "contents": [],
                "error": result.get("error", "Failed to list projects")
            }

        projects = result.get("result", {})
        contents = []

        for project_name, project_info in projects.items():
            contents.append({
                "uri": f"cursor://projects/{project_name}",
                "name": project_name,
                "mimeType": "application/json",
                "description": f"Cursor project: {project_name}",
                "metadata": {
                    "db_path": project_info.get("db_path"),
                    "workspace_dir": project_info.get("workspace_dir"),
                    "folder_uri": project_info.get("folder_uri")
                }
            })

        return {"contents": contents}

    except Exception as e:
        logger.error(f"Error listing cursor projects: {e}")
        return {
            "contents": [],
            "error": f"Internal error: {e}"
        }


async def get_cursor_project_data(project_name: str) -> Dict[str, Any]:
    """Get detailed data for a specific Cursor project."""
    try:
        # Get tool registry and cursor tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        cursor_tool = tool_registry.get_tool("cursor_db")

        if not cursor_tool:
            return {"error": "cursor_db tool not available"}

        # Get project chat data
        chat_result = await cursor_tool.safe_execute(
            operation="get_chat_data",
            project_name=project_name
        )

        # Get composer IDs
        composer_result = await cursor_tool.safe_execute(
            operation="get_composer_ids",
            project_name=project_name
        )

        project_data = {
            "project_name": project_name,
            "chat_data": chat_result.get("result") if chat_result.get("success") else None,
            "composer_data": composer_result.get("result") if composer_result.get("success") else None,
            "timestamp": "current"
        }

        return {
            "content": json.dumps(project_data, indent=2),
            "mimeType": "application/json"
        }

    except Exception as e:
        logger.error(f"Error getting project data for {project_name}: {e}")
        return {"error": f"Internal error: {e}"}


async def get_cursor_project_chat_data(project_name: str) -> Dict[str, Any]:
    """Get chat data for a specific Cursor project."""
    try:
        # Get tool registry and cursor tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        cursor_tool = tool_registry.get_tool("cursor_db")

        if not cursor_tool:
            return {"error": "cursor_db tool not available"}

        result = await cursor_tool.safe_execute(
            operation="get_chat_data",
            project_name=project_name
        )

        if result.get("success"):
            chat_data = result.get("result", {})
            return {
                "content": json.dumps(chat_data, indent=2),
                "mimeType": "application/json"
            }
        else:
            return {"error": result.get("error", "Failed to get chat data")}

    except Exception as e:
        logger.error(f"Error getting chat data for {project_name}: {e}")
        return {"error": f"Internal error: {e}"}


async def register_resources(registry) -> None:
    """Register all cursor resources with the resource registry."""

    # Register project list resource
    registry.register_resource(
        "cursor://projects",
        list_cursor_projects,
        {
            "description": "List all available Cursor IDE projects",
            "category": "cursor",
            "type": "project_list"
        }
    )

    logger.info("Registered Cursor project resources")


# Resource handlers for specific project URIs
async def handle_project_resource(uri: str) -> Dict[str, Any]:
    """Handle project-specific resource requests."""
    # Extract project name from URI like "cursor://projects/my-project"
    if uri.startswith("cursor://projects/") and len(uri.split("/")) >= 4:
        project_name = uri.split("/")[3]

        # Check if it's a chat data request
        if uri.endswith("/chat"):
            return await get_cursor_project_chat_data(project_name)
        else:
            return await get_cursor_project_data(project_name)

    return {"error": "Invalid project URI format"}