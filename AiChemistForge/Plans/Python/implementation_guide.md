# Technical Implementation Guide

## 🏗️ Architecture Patterns & Code Examples

This guide provides specific implementation details for the unified MCP server refactoring plan.

## Core Infrastructure Implementation

### 1. Server Configuration (`server/config.py`)

```python
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseSettings, Field, validator
import os


class ServerConfig(BaseSettings):
    """Configuration for the unified MCP server."""

    # Server Settings
    server_name: str = Field(default="unified-mcp-server", env="MCP_SERVER_NAME")
    log_level: str = Field(default="INFO", env="MCP_LOG_LEVEL")
    transport_type: str = Field(default="stdio", env="MCP_TRANSPORT_TYPE")  # stdio or sse

    # Database Settings
    cursor_path: Optional[str] = Field(default=None, env="CURSOR_PATH")
    project_directories: List[str] = Field(default_factory=list, env="PROJECT_DIRS")

    # File System Settings
    allowed_paths: List[str] = Field(default_factory=list, env="ALLOWED_PATHS")
    max_file_size: int = Field(default=10_000_000, env="MAX_FILE_SIZE")  # 10MB

    # Security Settings
    enable_path_traversal_check: bool = Field(default=True, env="ENABLE_PATH_TRAVERSAL_CHECK")
    max_query_results: int = Field(default=1000, env="MAX_QUERY_RESULTS")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("project_directories", pre=True)
    def parse_project_directories(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @validator("allowed_paths", pre=True)
    def parse_allowed_paths(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v


# Global config instance
config = ServerConfig()
```

### 2. Logging Setup (`server/logging.py`)

```python
import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logging(
    name: str,
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[Path] = None
) -> logging.Logger:
    """Set up structured logging for MCP server components.

    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to file in addition to stderr
        log_file_path: Path to log file (defaults to logs/{name}.log)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stderr for MCP compatibility)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        if log_file_path is None:
            log_file_path = Path("logs") / f"{name}.log"

        log_file_path.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
```

### 3. Application Lifecycle (`server/lifecycle.py`)

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
import logging

from .config import config
from .logging import setup_logging
from ..tools.registry import ToolRegistry
from ..resources.registry import ResourceRegistry
from ..prompts.registry import PromptRegistry


logger = setup_logging(__name__, config.log_level)


@asynccontextmanager
async def app_lifespan() -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle for the unified MCP server."""

    logger.info("Starting unified MCP server initialization")

    # Initialize registries
    tool_registry = ToolRegistry()
    resource_registry = ResourceRegistry()
    prompt_registry = PromptRegistry()

    # Auto-discover and register components
    try:
        await tool_registry.discover_and_register()
        await resource_registry.discover_and_register()
        await prompt_registry.discover_and_register()

        logger.info(f"Registered {len(tool_registry.tools)} tools")
        logger.info(f"Registered {len(resource_registry.resources)} resources")
        logger.info(f"Registered {len(prompt_registry.prompts)} prompts")

    except Exception as e:
        logger.error(f"Failed to initialize registries: {e}")
        raise

    # Create shared context
    context = {
        "tool_registry": tool_registry,
        "resource_registry": resource_registry,
        "prompt_registry": prompt_registry,
        "config": config,
    }

    try:
        yield context

    finally:
        logger.info("Shutting down unified MCP server")

        # Cleanup registries
        await tool_registry.cleanup()
        await resource_registry.cleanup()
        await prompt_registry.cleanup()
```

### 4. FastMCP Application (`server/app.py`)

```python
from mcp.server.fastmcp import FastMCP
from .lifecycle import app_lifespan
from .config import config


def create_app() -> FastMCP:
    """Create and configure the FastMCP application."""

    app = FastMCP(
        name=config.server_name,
        version="1.0.0",
        lifespan=app_lifespan
    )

    return app


# Global app instance
mcp_app = create_app()
```

## Tool System Implementation

### 1. Base Tool Interface (`tools/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
import logging

from ..server.config import config
from ..server.logging import setup_logging


T = TypeVar('T', bound='BaseTool')
logger = setup_logging(__name__, config.log_level)


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class BaseTool(ABC):
    """Base class for all MCP tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = setup_logging(f"tool.{name}", config.log_level)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ToolValidationError: If parameters are invalid
            ToolExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters.

        Returns:
            JSON schema dictionary
        """
        pass

    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate tool parameters against schema.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Validated parameters

        Raises:
            ToolValidationError: If validation fails
        """
        # Implementation would use JSON schema validation
        # For now, return as-is
        return kwargs

    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """Safely execute tool with error handling.

        Args:
            **kwargs: Tool parameters

        Returns:
            Standardized tool result
        """
        try:
            # Validate parameters
            validated_params = self.validate_parameters(**kwargs)

            # Execute tool
            result = await self.execute(**validated_params)

            return {
                "success": True,
                "result": result,
                "tool": self.name
            }

        except ToolValidationError as e:
            self.logger.error(f"Validation error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Parameter validation failed: {e}",
                "tool": self.name
            }

        except ToolExecutionError as e:
            self.logger.error(f"Execution error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {e}",
                "tool": self.name
            }

        except Exception as e:
            self.logger.error(f"Unexpected error in {self.name}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "tool": self.name
            }
```

### 2. Tool Registry (`tools/registry.py`)

```python
from typing import Dict, List, Type, Any, Optional
import importlib
import pkgutil
import inspect
from pathlib import Path

from .base import BaseTool
from ..server.logging import setup_logging
from ..server.config import config


logger = setup_logging(__name__, config.log_level)


class ToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_classes: Dict[str, Type[BaseTool]] = {}

    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class.

        Args:
            tool_class: Tool class to register
        """
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"Tool {tool_class} must inherit from BaseTool")

        # Extract tool name from class
        tool_name = getattr(tool_class, 'tool_name', tool_class.__name__.lower())

        self.tool_classes[tool_name] = tool_class
        logger.info(f"Registered tool class: {tool_name}")

    async def instantiate_tool(self, tool_name: str, **kwargs) -> BaseTool:
        """Create tool instance.

        Args:
            tool_name: Name of tool to instantiate
            **kwargs: Tool initialization parameters

        Returns:
            Tool instance
        """
        if tool_name not in self.tool_classes:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_class = self.tool_classes[tool_name]
        tool_instance = tool_class(**kwargs)

        self.tools[tool_name] = tool_instance
        return tool_instance

    async def discover_and_register(self) -> None:
        """Auto-discover and register tools from tools package."""

        # Import tools package
        import unified_mcp_server.tools as tools_package

        # Discover tool modules
        for module_info in pkgutil.walk_packages(
            tools_package.__path__,
            tools_package.__name__ + "."
        ):
            try:
                module = importlib.import_module(module_info.name)

                # Find tool classes in module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseTool) and
                        obj != BaseTool):

                        self.register_tool(obj)

            except Exception as e:
                logger.warning(f"Failed to load tool module {module_info.name}: {e}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool instance by name.

        Args:
            tool_name: Name of tool

        Returns:
            Tool instance or None
        """
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    async def cleanup(self) -> None:
        """Cleanup all tool instances."""
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                try:
                    await tool.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up tool {tool.name}: {e}")

        self.tools.clear()
```

### 3. Database Tool Implementation (`tools/database/cursor_db.py`)

```python
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
        self._refresh_db_paths()

    def _get_cursor_path(self) -> Optional[Path]:
        """Get the default Cursor path based on OS."""
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

    def _refresh_db_paths(self) -> None:
        """Scan and refresh database paths."""
        self.db_paths.clear()
        self.projects_info.clear()

        if not self.cursor_path:
            return

        workspace_storage = self.cursor_path / "workspaceStorage"
        if not workspace_storage.exists():
            return

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

                        self.db_paths[project_name] = str(state_db)
                        self.projects_info[project_name] = {
                            "name": project_name,
                            "db_path": str(state_db),
                            "workspace_dir": str(workspace_dir),
                            "folder_uri": folder_uri,
                        }

                except Exception as e:
                    self.logger.error(f"Error processing workspace {workspace_dir}: {e}")

    async def execute(self, **kwargs) -> Any:
        """Execute cursor database operations."""
        operation = kwargs.get("operation")

        if operation == "list_projects":
            return self._list_projects(kwargs.get("detailed", False))
        elif operation == "query_table":
            return await self._query_table(**kwargs)
        elif operation == "refresh_databases":
            return self._refresh_databases()
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
                    "enum": ["list_projects", "query_table", "refresh_databases"],
                    "description": "Operation to perform"
                },
                "project_name": {
                    "type": "string",
                    "description": "Name of the project (required for query_table)"
                },
                "table_name": {
                    "type": "string",
                    "enum": ["ItemTable", "cursorDiskKV"],
                    "description": "Database table to query"
                },
                "query_type": {
                    "type": "string",
                    "enum": ["get_all", "get_by_key", "search_keys"],
                    "description": "Type of query to perform"
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
                    "description": "Return detailed project information"
                }
            },
            "required": ["operation"]
        }
```

## Integration with FastMCP

### Main Server Entry Point (`main.py`)

```python
import asyncio
import argparse
from mcp.server.fastmcp import FastMCP

from .server.app import mcp_app
from .server.config import config
from .server.logging import setup_logging
from .tools.registry import ToolRegistry
from .resources.registry import ResourceRegistry
from .prompts.registry import PromptRegistry


logger = setup_logging(__name__, config.log_level)


# Register all tools, resources, and prompts with FastMCP decorators
@mcp_app.tool()
async def query_cursor_database(
    operation: str,
    project_name: str = None,
    table_name: str = None,
    query_type: str = None,
    key: str = None,
    limit: int = 100,
    detailed: bool = False
) -> dict:
    """Query Cursor IDE state databases."""

    # Get tool registry from app context
    tool_registry = mcp_app.get_context()["tool_registry"]
    cursor_tool = tool_registry.get_tool("cursor_db")

    if not cursor_tool:
        # Instantiate if not exists
        cursor_tool = await tool_registry.instantiate_tool("cursor_db")

    return await cursor_tool.safe_execute(
        operation=operation,
        project_name=project_name,
        table_name=table_name,
        query_type=query_type,
        key=key,
        limit=limit,
        detailed=detailed
    )


@mcp_app.resource("cursor://projects")
async def list_cursor_projects() -> dict:
    """List all available Cursor projects."""
    tool_registry = mcp_app.get_context()["tool_registry"]
    cursor_tool = tool_registry.get_tool("cursor_db")

    if not cursor_tool:
        cursor_tool = await tool_registry.instantiate_tool("cursor_db")

    result = await cursor_tool.safe_execute(operation="list_projects")
    return {
        "contents": [
            {
                "uri": f"cursor://projects/{name}",
                "name": name,
                "mimeType": "application/json"
            }
            for name in result.get("result", {}).keys()
        ]
    }


def main():
    """Main entry point for the unified MCP server."""
    parser = argparse.ArgumentParser(description="Unified MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=config.transport_type,
        help="Transport type to use"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport"
    )

    args = parser.parse_args()

    logger.info(f"Starting unified MCP server with {args.transport} transport")

    if args.transport == "stdio":
        mcp_app.run()
    else:
        # SSE transport implementation would go here
        logger.error("SSE transport not yet implemented")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
```

## Testing Strategy

### Unit Tests Example (`tests/test_cursor_db_tool.py`)

```python
import pytest
import tempfile
import sqlite3
import json
from pathlib import Path

from unified_mcp_server.tools.database.cursor_db import CursorDBTool


@pytest.fixture
async def cursor_tool():
    """Create a CursorDBTool instance for testing."""
    tool = CursorDBTool()
    return tool


@pytest.fixture
def mock_cursor_workspace(tmp_path):
    """Create a mock Cursor workspace structure."""
    workspace_storage = tmp_path / "workspaceStorage" / "test_workspace"
    workspace_storage.mkdir(parents=True)

    # Create workspace.json
    workspace_json = workspace_storage / "workspace.json"
    workspace_data = {
        "folder": "file:///home/user/test_project"
    }
    with open(workspace_json, 'w') as f:
        json.dump(workspace_data, f)

    # Create state.vscdb
    db_path = workspace_storage / "state.vscdb"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create test tables
    cursor.execute("""
        CREATE TABLE ItemTable (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        INSERT INTO ItemTable (key, value) VALUES
        ('test_key', '{"data": "test_value"}'),
        ('another_key', '{"data": "another_value"}')
    """)

    conn.commit()
    conn.close()

    return tmp_path


@pytest.mark.asyncio
async def test_list_projects(cursor_tool, mock_cursor_workspace):
    """Test listing projects."""
    # Mock the cursor path
    cursor_tool.cursor_path = mock_cursor_workspace
    cursor_tool._refresh_db_paths()

    result = await cursor_tool.execute(operation="list_projects")

    assert isinstance(result, dict)
    assert "test_project" in result


@pytest.mark.asyncio
async def test_query_table(cursor_tool, mock_cursor_workspace):
    """Test querying database table."""
    cursor_tool.cursor_path = mock_cursor_workspace
    cursor_tool._refresh_db_paths()

    result = await cursor_tool.execute(
        operation="query_table",
        project_name="test_project",
        table_name="ItemTable",
        query_type="get_all",
        limit=10
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["key"] == "test_key"
    assert result[0]["value"]["data"] == "test_value"


@pytest.mark.asyncio
async def test_invalid_operation(cursor_tool):
    """Test handling of invalid operations."""
    with pytest.raises(Exception):  # Should raise ToolExecutionError
        await cursor_tool.execute(operation="invalid_operation")
```

This implementation guide provides:

1. **Concrete code examples** for each architectural component
2. **Error handling patterns** throughout the system
3. **Configuration management** with environment variables
4. **Tool registry system** for dynamic discovery
5. **FastMCP integration** patterns
6. **Testing strategies** with pytest fixtures

The architecture ensures clean separation of concerns while maintaining the flexibility to add new tool types and extend functionality as needed.