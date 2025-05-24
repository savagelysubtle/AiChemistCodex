"""Cursor IDE database tool for the unified MCP server."""

from typing import List, Dict, Any, Optional
import sqlite3
import json
import platform
from pathlib import Path

from ..base import BaseTool, ToolError, ToolExecutionError
from ...server.config import config


class CursorDBTool(BaseTool):
    """Tool for managing Cursor IDE database operations."""

    tool_name = "cursor_db"

    def __init__(self):
        super().__init__(
            name="cursor_db",
            description="Query and manage Cursor IDE state databases"
        )
        self.cursor_path = self._get_cursor_path()
        self.db_paths: Dict[str, str] = {}
        self.projects_info: Dict[str, Dict[str, Any]] = {}
        self.global_db_path: Optional[str] = None
        self._refresh_db_paths()

    def _get_cursor_path(self) -> Optional[Path]:
        """Get the Cursor path based on config or OS defaults."""
        if config.cursor_path:
            return Path(config.cursor_path).expanduser().resolve()

        system = platform.system()
        home = Path.home()

        paths = {
            "Darwin": home / "Library/Application Support/Cursor/User",
            "Windows": home / "AppData/Roaming/Cursor/User",
            "Linux": home / ".config/Cursor/User",
        }

        default_path = paths.get(system)
        if default_path and default_path.exists():
            return default_path

        self.logger.warning(f"Could not find Cursor path for {system}")
        return None

    def _detect_cursor_projects(self) -> List[Dict[str, Any]]:
        """Detect Cursor projects by scanning the workspaceStorage directory."""
        if not self.cursor_path:
            self.logger.error("No Cursor path available")
            return []

        if not self.cursor_path.exists():
            self.logger.error(f"Cursor path does not exist: {self.cursor_path}")
            return []

        workspace_storage = self.cursor_path / "workspaceStorage"
        if not workspace_storage.exists():
            self.logger.warning(f"Workspace storage directory not found: {workspace_storage}")
            return []

        self.logger.info(f"Found workspace storage directory: {workspace_storage}")
        projects = []

        for workspace_dir in workspace_storage.iterdir():
            if not workspace_dir.is_dir():
                continue

            workspace_json = workspace_dir / "workspace.json"
            state_db = workspace_dir / "state.vscdb"

            if workspace_json.exists() and state_db.exists():
                try:
                    with open(workspace_json) as f:
                        workspace_data = json.load(f)

                    folder_uri = workspace_data.get("folder")
                    if folder_uri:
                        project_name = folder_uri.rstrip("/").split("/")[-1]

                        projects.append({
                            "name": project_name,
                            "db_path": str(state_db),
                            "workspace_dir": str(workspace_dir),
                            "folder_uri": folder_uri,
                        })
                        self.logger.info(f"Found project: {project_name} at {state_db}")
                except Exception as e:
                    self.logger.error(f"Error processing workspace {workspace_dir}: {e}")

        return projects

    def _refresh_db_paths(self) -> None:
        """Scan and refresh database paths."""
        self.db_paths.clear()
        self.projects_info.clear()

        if not self.cursor_path:
            return

        # Detect projects from Cursor directory
        cursor_projects = self._detect_cursor_projects()
        for project in cursor_projects:
            project_name = project["name"]
            self.db_paths[project_name] = project["db_path"]
            self.projects_info[project_name] = project

        # Set global storage database path
        global_storage_path = self.cursor_path / "globalStorage" / "state.vscdb"
        if global_storage_path.exists():
            self.global_db_path = str(global_storage_path)
            self.logger.info(f"Found global storage database at {self.global_db_path}")
        else:
            self.logger.warning(f"Global storage database not found at {global_storage_path}")

        # Add explicitly specified project directories from config
        for project_dir in config.project_directories:
            project_path = Path(project_dir).expanduser().resolve()
            db_path = project_path / "state.vscdb"

            if db_path.exists():
                project_name = project_path.name
                self.db_paths[project_name] = str(db_path)
                self.projects_info[project_name] = {
                    "name": project_name,
                    "db_path": str(db_path),
                    "workspace_dir": None,
                    "folder_uri": None,
                }
                self.logger.info(f"Found database: {project_name} at {db_path}")
            else:
                self.logger.warning(f"No state.vscdb found in {project_path}")

    async def execute(self, **kwargs) -> Any:
        """Execute cursor database operations."""
        operation = kwargs.get("operation")

        if operation == "list_projects":
            return self._list_projects(kwargs.get("detailed", False))
        elif operation == "query_table":
            return await self._query_table(**kwargs)
        elif operation == "refresh_databases":
            return self._refresh_databases()
        elif operation == "get_chat_data":
            return self._get_chat_data(kwargs.get("project_name"))
        elif operation == "get_composer_ids":
            return self._get_composer_ids(kwargs.get("project_name"))
        elif operation == "get_composer_data":
            return self._get_composer_data(kwargs.get("composer_id"))
        else:
            raise ToolExecutionError(f"Unknown operation: {operation}")

    def _list_projects(self, detailed: bool = False) -> Dict[str, Any]:
        """List available projects."""
        if detailed:
            return self.projects_info
        return self.db_paths

    async def _query_table(
        self,
        project_name: str,
        table_name: str,
        query_type: str,
        key: Optional[str] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Query a specific project's database table."""

        if project_name not in self.db_paths:
            raise ToolExecutionError(f"Project '{project_name}' not found")

        if table_name not in ["ItemTable", "cursorDiskKV"]:
            raise ToolExecutionError("Table must be 'ItemTable' or 'cursorDiskKV'")

        db_path = self.db_paths[project_name]

        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if query_type == "get_all":
                    query = f"SELECT * FROM {table_name} LIMIT ?"
                    cursor.execute(query, (limit,))

                elif query_type == "get_by_key":
                    if not key:
                        raise ToolExecutionError("Key required for get_by_key operation")
                    query = f"SELECT * FROM {table_name} WHERE key = ?"
                    cursor.execute(query, (key,))

                elif query_type == "search_keys":
                    if not key:
                        raise ToolExecutionError("Key pattern required for search_keys")
                    query = f"SELECT * FROM {table_name} WHERE key LIKE ? LIMIT ?"
                    cursor.execute(query, (f"%{key}%", limit))

                else:
                    raise ToolExecutionError(f"Unknown query type: {query_type}")

                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Try to parse JSON values
                    if 'value' in row_dict and row_dict['value']:
                        try:
                            row_dict['value'] = json.loads(row_dict['value'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    results.append(row_dict)

                return results

        except sqlite3.Error as e:
            raise ToolExecutionError(f"Database error: {e}")

    def _get_chat_data(self, project_name: str) -> Dict[str, Any]:
        """Retrieve AI chat data from a project."""
        if project_name not in self.db_paths:
            raise ToolExecutionError(f"Project '{project_name}' not found")

        try:
            results = self._execute_query_sync(
                project_name,
                "ItemTable",
                "get_by_key",
                "workbench.panel.aichat.view.aichat.chatdata",
            )

            if results and len(results) > 0:
                return results[0]["value"]
            else:
                return {"error": "No chat data found for this project"}

        except Exception as e:
            self.logger.error(f"Error retrieving chat data: {e}")
            raise ToolExecutionError(f"Error retrieving chat data: {e}")

    def _get_composer_ids(self, project_name: str) -> Dict[str, Any]:
        """Retrieve composer IDs from a project."""
        if project_name not in self.db_paths:
            raise ToolExecutionError(f"Project '{project_name}' not found")

        try:
            results = self._execute_query_sync(
                project_name, "ItemTable", "get_by_key", "composer.composerData"
            )

            if results and len(results) > 0:
                composer_data = results[0]["value"]
                composer_ids = []
                if "allComposers" in composer_data:
                    for composer in composer_data["allComposers"]:
                        if "composerId" in composer:
                            composer_ids.append(composer["composerId"])
                return {"composer_ids": composer_ids, "full_data": composer_data}
            else:
                return {"error": "No composer data found for this project"}

        except Exception as e:
            self.logger.error(f"Error retrieving composer IDs: {e}")
            raise ToolExecutionError(f"Error retrieving composer IDs: {e}")

    def _get_composer_data(self, composer_id: str) -> Dict[str, Any]:
        """Retrieve composer data from global storage."""
        if not self.global_db_path:
            raise ToolExecutionError("Global storage database not found")

        try:
            with sqlite3.connect(self.global_db_path) as conn:
                cursor = conn.cursor()

                key = f"composerData:{composer_id}"
                cursor.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (key,))

                row = cursor.fetchone()

                if row:
                    try:
                        return {"composer_id": composer_id, "data": json.loads(row[0])}
                    except json.JSONDecodeError:
                        return {"composer_id": composer_id, "data": row[0]}
                else:
                    return {"error": f"No data found for composer ID: {composer_id}"}

        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {e}")
            raise ToolExecutionError(f"SQLite error: {e}")

    def _execute_query_sync(self, project_name: str, table_name: str, query_type: str, key: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Synchronous version of query execution for internal use."""
        if project_name not in self.db_paths:
            raise ValueError(f"Project '{project_name}' not found")

        if table_name not in ["ItemTable", "cursorDiskKV"]:
            raise ValueError("Table name must be either 'ItemTable' or 'cursorDiskKV'")

        db_path = self.db_paths[project_name]

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            if query_type == "get_all":
                cursor.execute(f"SELECT key, value FROM {table_name} LIMIT ?", (limit,))
            elif query_type == "get_by_key" and key:
                cursor.execute(f"SELECT key, value FROM {table_name} WHERE key = ?", (key,))
            elif query_type == "search_keys" and key:
                search_term = f"%{key}%"
                cursor.execute(f"SELECT key, value FROM {table_name} WHERE key LIKE ? LIMIT ?", (search_term, limit))
            else:
                raise ValueError("Invalid query type or missing key parameter")

            results = []
            for row in cursor.fetchall():
                key_val, value = row
                try:
                    parsed_value = json.loads(value)
                    results.append({"key": key_val, "value": parsed_value})
                except json.JSONDecodeError:
                    results.append({"key": key_val, "value": value})

            conn.close()
            return results

        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {e}")
            raise

    def _refresh_databases(self) -> Dict[str, Any]:
        """Refresh database paths and return status."""
        old_count = len(self.db_paths)
        self._refresh_db_paths()
        new_count = len(self.db_paths)

        return {
            "message": "Database paths refreshed",
            "projects_found": new_count,
            "change": new_count - old_count
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list_projects", "query_table", "refresh_databases", "get_chat_data", "get_composer_ids", "get_composer_data"],
                    "description": "Operation to perform"
                },
                "project_name": {
                    "type": "string",
                    "description": "Name of the project (required for project-specific operations)"
                },
                "table_name": {
                    "type": "string",
                    "enum": ["ItemTable", "cursorDiskKV"],
                    "description": "Database table to query (for query_table operation)"
                },
                "query_type": {
                    "type": "string",
                    "enum": ["get_all", "get_by_key", "search_keys"],
                    "description": "Type of query to perform (for query_table operation)"
                },
                "key": {
                    "type": "string",
                    "description": "Key for get_by_key or search pattern for search_keys"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100,
                    "description": "Maximum number of results"
                },
                "detailed": {
                    "type": "boolean",
                    "default": false,
                    "description": "Return detailed project information (for list_projects)"
                },
                "composer_id": {
                    "type": "string",
                    "description": "Composer ID (for get_composer_data operation)"
                }
            },
            "required": ["operation"]
        }