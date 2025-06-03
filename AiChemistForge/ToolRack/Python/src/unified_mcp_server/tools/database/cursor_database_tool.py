"""Cursor database query tool for FastMCP.

Implements comprehensive error handling per MCP transport best practices:
- Connection error handling
- Query validation and sanitization
- Resource cleanup
- Structured logging to stderr
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.tools.cursor_database")


def register_cursor_database_tool(mcp: FastMCP) -> None:
    """Register the query_cursor_database tool with the FastMCP instance."""

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
    ) -> Dict[str, Any]:
        """Query Cursor IDE databases and manage database operations.

        Use Tool to query Cursor IDE databases and manage database operations.

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
        logger.debug(f"Starting cursor database operation: {operation}")

        try:
            # Input validation per MCP error handling guidelines
            if not operation:
                raise ValueError("Operation parameter is required")

            # Validate limit parameter
            if not isinstance(limit, int) or limit < 1 or limit > 10000:
                raise ValueError("Limit must be an integer between 1 and 10000")

            # Find Cursor database with comprehensive error handling
            db_path = await _find_cursor_database()
            if db_path is None:
                logger.warning("Cursor database not found in standard locations")
                return {
                    "success": False,
                    "error": "Cursor database not found in common locations",
                    "searched_paths": _get_cursor_search_paths(),
                    "tool": "query_cursor_database",
                }

            logger.debug(f"Using Cursor database at: {db_path}")

            # Route to appropriate operation handler with error context
            operation_handlers = {
                "list_projects": lambda: _list_cursor_projects(db_path, detailed),
                "query_table": lambda: _query_project_table(
                    db_path, project_name, table_name, query_type, key, limit
                ),
                "get_chat_data": lambda: _get_chat_data(db_path, project_name, limit),
                "get_composer_ids": lambda: _get_composer_ids(
                    db_path, project_name, limit
                ),
                "get_composer_data": lambda: _get_composer_data(
                    db_path, project_name, composer_id
                ),
            }

            handler = operation_handlers.get(operation)
            if handler is None:
                available_ops = list(operation_handlers.keys())
                logger.warning(
                    f"Unknown operation '{operation}', available: {available_ops}"
                )
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}",
                    "available_operations": available_ops,
                    "tool": "query_cursor_database",
                }

            # Execute operation with comprehensive error handling
            result = await handler()
            logger.debug(f"Operation {operation} completed successfully")
            return result

        except ValueError as e:
            logger.error(f"Validation error in operation {operation}: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "operation": operation,
                "tool": "query_cursor_database",
            }
        except sqlite3.Error as e:
            logger.error(f"Database error in operation {operation}: {e}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "operation": operation,
                "tool": "query_cursor_database",
            }
        except Exception as e:
            logger.error(
                f"Unexpected error in operation {operation}: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "operation": operation,
                "tool": "query_cursor_database",
            }


async def _find_cursor_database() -> Optional[Path]:
    """Find Cursor database with comprehensive error handling."""
    search_paths = _get_cursor_search_paths()

    for path_str in search_paths:
        try:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_file():
                logger.debug(f"Found Cursor database at: {path}")
                return path
        except (OSError, RuntimeError) as e:
            logger.debug(f"Error checking path {path_str}: {e}")
            continue

    return None


def _get_cursor_search_paths() -> list[str]:
    """Get list of standard Cursor database search paths."""
    return [
        "~/AppData/Roaming/Cursor/User/globalStorage/state.vscdb",
        "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb",
        "~/.config/Cursor/User/globalStorage/state.vscdb",
    ]


async def _list_cursor_projects(
    db_path: Path, detailed: bool = False
) -> Dict[str, Any]:
    """List all Cursor projects with comprehensive error handling."""
    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            # Get all table names with error handling
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row["name"] for row in cursor.fetchall()]

            project_tables = [
                table for table in all_tables if table.startswith("project_")
            ]

            projects = []
            for table in project_tables:
                project_name = table.replace("project_", "").replace("_", "/")
                project_info = {"name": project_name, "table": table}

                if detailed:
                    try:
                        # Get project stats with timeout
                        cursor.execute(f"SELECT COUNT(*) as count FROM `{table}`")
                        count_result = cursor.fetchone()
                        project_info["total_records"] = (
                            count_result["count"] if count_result else 0
                        )

                        # Get table schema
                        cursor.execute(f"PRAGMA table_info(`{table}`)")
                        schema = cursor.fetchall()
                        project_info["schema"] = [
                            {"name": col["name"], "type": col["type"]} for col in schema
                        ]
                    except sqlite3.Error as e:
                        logger.warning(f"Could not get detailed info for {table}: {e}")
                        project_info["error"] = f"Could not get detailed info: {str(e)}"

                projects.append(project_info)

            logger.info(f"Found {len(projects)} Cursor projects")
            return {
                "success": True,
                "projects": projects,
                "total_projects": len(projects),
                "tool": "query_cursor_database",
            }

    except sqlite3.Error as e:
        logger.error(f"Database error listing projects: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing projects: {e}")
        raise


async def _query_project_table(
    db_path: Path,
    project_name: Optional[str],
    table_name: Optional[str],
    query_type: Optional[str],
    key: Optional[str],
    limit: int,
) -> Dict[str, Any]:
    """Query a specific project table with comprehensive validation."""
    # Validate required parameters
    if not project_name:
        raise ValueError("project_name is required for query_table operation")
    if not table_name:
        raise ValueError("table_name is required for query_table operation")

    # Sanitize table name
    safe_table_name = f"project_{project_name.replace('/', '_')}"

    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Verify table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (safe_table_name,),
            )
            if not cursor.fetchone():
                raise ValueError(f"Table {safe_table_name} does not exist")

            if query_type == "get_all":
                cursor.execute(f"SELECT * FROM `{safe_table_name}` LIMIT ?", (limit,))
                rows = cursor.fetchall()

                return {
                    "success": True,
                    "data": [dict(row) for row in rows],
                    "count": len(rows),
                    "table": safe_table_name,
                    "tool": "query_cursor_database",
                }

            elif query_type == "get_by_key":
                if not key:
                    raise ValueError("key parameter is required for get_by_key query")

                cursor.execute(
                    f"SELECT * FROM `{safe_table_name}` WHERE key = ?", (key,)
                )
                row = cursor.fetchone()

                if row:
                    return {
                        "success": True,
                        "data": dict(row),
                        "table": safe_table_name,
                        "tool": "query_cursor_database",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"No record found for key: {key}",
                        "table": safe_table_name,
                        "tool": "query_cursor_database",
                    }

            elif query_type == "search_keys":
                if not key:
                    raise ValueError("key parameter is required for search_keys query")

                cursor.execute(
                    f"SELECT * FROM `{safe_table_name}` WHERE key LIKE ? LIMIT ?",
                    (f"%{key}%", limit),
                )
                rows = cursor.fetchall()

                return {
                    "success": True,
                    "data": [dict(row) for row in rows],
                    "count": len(rows),
                    "search_pattern": key,
                    "table": safe_table_name,
                    "tool": "query_cursor_database",
                }

            else:
                raise ValueError(
                    f"Invalid query_type: {query_type}. Must be one of: get_all, get_by_key, search_keys"
                )

    except sqlite3.Error as e:
        logger.error(f"Database error querying table {safe_table_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying table {safe_table_name}: {e}")
        raise


async def _get_chat_data(
    db_path: Path, project_name: Optional[str], limit: int
) -> Dict[str, Any]:
    """Get chat data for a project with validation."""
    if not project_name:
        raise ValueError("project_name is required for get_chat_data operation")

    safe_table_name = f"project_{project_name.replace('/', '_')}"

    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT * FROM `{safe_table_name}` WHERE key LIKE ? LIMIT ?",
                ("chat%", limit),
            )
            rows = cursor.fetchall()

            logger.info(
                f"Retrieved {len(rows)} chat records for project {project_name}"
            )
            return {
                "success": True,
                "chat_data": [dict(row) for row in rows],
                "count": len(rows),
                "project": project_name,
                "tool": "query_cursor_database",
            }

    except sqlite3.Error as e:
        logger.error(f"Database error getting chat data for {project_name}: {e}")
        raise


async def _get_composer_ids(
    db_path: Path, project_name: Optional[str], limit: int
) -> Dict[str, Any]:
    """Get composer IDs for a project with validation."""
    if not project_name:
        raise ValueError("project_name is required for get_composer_ids operation")

    safe_table_name = f"project_{project_name.replace('/', '_')}"

    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT key FROM `{safe_table_name}` WHERE key LIKE ? LIMIT ?",
                ("composer%", limit),
            )
            rows = cursor.fetchall()

            composer_ids = [row["key"] for row in rows]
            logger.info(
                f"Retrieved {len(composer_ids)} composer IDs for project {project_name}"
            )

            return {
                "success": True,
                "composer_ids": composer_ids,
                "count": len(composer_ids),
                "project": project_name,
                "tool": "query_cursor_database",
            }

    except sqlite3.Error as e:
        logger.error(f"Database error getting composer IDs for {project_name}: {e}")
        raise


async def _get_composer_data(
    db_path: Path, project_name: Optional[str], composer_id: Optional[str]
) -> Dict[str, Any]:
    """Get specific composer data with validation."""
    if not project_name:
        raise ValueError("project_name is required for get_composer_data operation")
    if not composer_id:
        raise ValueError("composer_id is required for get_composer_data operation")

    safe_table_name = f"project_{project_name.replace('/', '_')}"

    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT * FROM `{safe_table_name}` WHERE key = ?", (composer_id,)
            )
            row = cursor.fetchone()

            if row:
                logger.info(
                    f"Retrieved composer data for {composer_id} in project {project_name}"
                )
                return {
                    "success": True,
                    "composer_data": dict(row),
                    "project": project_name,
                    "composer_id": composer_id,
                    "tool": "query_cursor_database",
                }
            else:
                return {
                    "success": False,
                    "error": f"No composer data found for ID: {composer_id}",
                    "project": project_name,
                    "composer_id": composer_id,
                    "tool": "query_cursor_database",
                }

    except sqlite3.Error as e:
        logger.error(f"Database error getting composer data for {composer_id}: {e}")
        raise
