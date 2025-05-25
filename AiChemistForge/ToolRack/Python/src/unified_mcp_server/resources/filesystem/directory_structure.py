"""Filesystem directory structure resources for MCP."""

import json
from typing import Any, Dict

from ...server.logging import setup_logging
from ...tools.registry import ToolRegistry

logger = setup_logging(__name__)


async def list_directory_structure() -> Dict[str, Any]:
    """List directory structure as MCP resource."""
    try:
        # Get tool registry and file tree tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        file_tree_tool = tool_registry.get_tool("file_tree")

        if not file_tree_tool:
            return {"contents": [], "error": "file_tree tool not available"}

        # Get current directory structure with limited depth
        result = await file_tree_tool.safe_execute(
            path=".", max_depth=3, show_hidden=False, format="json"
        )

        if not result.get("success", False):
            return {
                "contents": [],
                "error": result.get("error", "Failed to list directory structure"),
            }

        directory_data = result.get("result", {})

        # Convert to MCP resource format
        contents = [
            {
                "uri": "filesystem://directory-structure",
                "name": "Directory Structure",
                "mimeType": "application/json",
                "description": "Current directory structure with files and folders",
                "metadata": {
                    "root_path": directory_data.get("path", "."),
                    "is_dir": directory_data.get("is_dir", True),
                    "generated_at": "current",
                },
            }
        ]

        return {"contents": contents}

    except Exception as e:
        logger.error(f"Error listing directory structure: {e}")
        return {"contents": [], "error": f"Internal error: {e}"}


async def get_codebase_summary() -> Dict[str, Any]:
    """Get codebase summary as MCP resource."""
    try:
        # Get tool registry and codebase ingest tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        codebase_tool = tool_registry.get_tool("codebase_ingest")

        if not codebase_tool:
            return {"contents": [], "error": "codebase_ingest tool not available"}

        # Get codebase summary with limited files
        result = await codebase_tool.safe_execute(
            path=".",
            max_files=50,
            max_file_size=100000,  # 100KB limit
            output_format="structured",
            show_tree=True,
            include_patterns=["*.py", "*.md", "*.json", "*.yaml", "*.toml"],
        )

        if not result.get("success", False):
            return {
                "contents": [],
                "error": result.get("error", "Failed to generate codebase summary"),
            }

        codebase_data = result.get("result", {})

        # Convert to MCP resource format
        contents = [
            {
                "uri": "filesystem://codebase-summary",
                "name": "Codebase Summary",
                "mimeType": "application/json",
                "description": f"Summary of {codebase_data.get('total_files', 0)} files in codebase",
                "metadata": {
                    "root_path": codebase_data.get("root_path", "."),
                    "total_files": codebase_data.get("total_files", 0),
                    "text_files": codebase_data.get("text_files", 0),
                    "total_size": codebase_data.get("total_size", 0),
                },
            }
        ]

        return {"contents": contents}

    except Exception as e:
        logger.error(f"Error generating codebase summary: {e}")
        return {"contents": [], "error": f"Internal error: {e}"}


async def get_directory_structure_data(path: str = ".") -> Dict[str, Any]:
    """Get detailed directory structure data for a specific path."""
    try:
        # Get tool registry and file tree tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        file_tree_tool = tool_registry.get_tool("file_tree")

        if not file_tree_tool:
            return {"error": "file_tree tool not available"}

        result = await file_tree_tool.safe_execute(
            path=path, max_depth=5, show_hidden=False, show_sizes=True, format="json"
        )

        if result.get("success"):
            directory_data = result.get("result", {})
            return {
                "content": json.dumps(directory_data, indent=2),
                "mimeType": "application/json",
            }
        else:
            return {"error": result.get("error", "Failed to get directory structure")}

    except Exception as e:
        logger.error(f"Error getting directory structure for {path}: {e}")
        return {"error": f"Internal error: {e}"}


async def get_codebase_data(path: str = ".") -> Dict[str, Any]:
    """Get detailed codebase data for a specific path."""
    try:
        # Get tool registry and codebase ingest tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        codebase_tool = tool_registry.get_tool("codebase_ingest")

        if not codebase_tool:
            return {"error": "codebase_ingest tool not available"}

        result = await codebase_tool.safe_execute(
            path=path,
            max_files=100,
            max_file_size=500000,  # 500KB limit for detailed view
            output_format="structured",
            show_tree=True,
        )

        if result.get("success"):
            codebase_data = result.get("result", {})
            return {
                "content": json.dumps(codebase_data, indent=2),
                "mimeType": "application/json",
            }
        else:
            return {"error": result.get("error", "Failed to get codebase data")}

    except Exception as e:
        logger.error(f"Error getting codebase data for {path}: {e}")
        return {"error": f"Internal error: {e}"}


async def register_resources(registry) -> None:
    """Register all filesystem resources with the resource registry."""

    # Register directory structure resource
    registry.register_resource(
        "filesystem://directory-structure",
        list_directory_structure,
        {
            "description": "Current directory structure with files and folders",
            "category": "filesystem",
            "type": "directory_structure",
        },
    )

    # Register codebase summary resource
    registry.register_resource(
        "filesystem://codebase-summary",
        get_codebase_summary,
        {
            "description": "Summary of codebase files and structure",
            "category": "filesystem",
            "type": "codebase_summary",
        },
    )

    logger.info("Registered filesystem resources")


# Resource handlers for specific filesystem URIs
async def handle_filesystem_resource(uri: str) -> Dict[str, Any]:
    """Handle filesystem-specific resource requests."""
    # Extract path from URI like "filesystem://directory-structure/src"
    if uri.startswith("filesystem://directory-structure"):
        if "/" in uri[len("filesystem://directory-structure") :]:
            path = uri[len("filesystem://directory-structure/") :]
            return await get_directory_structure_data(path)
        else:
            return await get_directory_structure_data(".")

    elif uri.startswith("filesystem://codebase-summary"):
        if "/" in uri[len("filesystem://codebase-summary") :]:
            path = uri[len("filesystem://codebase-summary/") :]
            return await get_codebase_data(path)
        else:
            return await get_codebase_data(".")

    return {"error": "Invalid filesystem URI format"}
