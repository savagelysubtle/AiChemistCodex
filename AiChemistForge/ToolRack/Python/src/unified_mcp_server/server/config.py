"""Server configuration management for the unified MCP server."""

import os
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Configuration for the unified MCP server."""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    # Server Settings
    server_name: str = Field(
        default="aichemistforge-mcp-server", description="MCP server name"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    transport_type: str = Field(
        default="stdio", description="Transport type (stdio or sse)"
    )

    # Database Settings
    cursor_path: Optional[str] = Field(
        default=None, description="Path to Cursor IDE directory"
    )
    project_directories: List[str] = Field(
        default_factory=list, description="Additional project directories"
    )

    # File System Settings
    allowed_paths: List[str] = Field(
        default_factory=list, description="Allowed file system paths"
    )
    max_file_size: int = Field(
        default=10_000_000, description="Maximum file size in bytes"
    )

    # Security Settings
    enable_path_traversal_check: bool = Field(
        default=True, description="Enable path traversal protection"
    )
    max_query_results: int = Field(default=1000, description="Maximum query results")

    @field_validator("project_directories", mode="before")
    @classmethod
    def parse_project_directories(cls, v):
        """Parse project directories from string or list."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @field_validator("allowed_paths", mode="before")
    @classmethod
    def parse_allowed_paths(cls, v):
        """Parse allowed paths from string or list."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v


def load_config() -> ServerConfig:
    """Load configuration from environment variables and .env file."""
    # Read environment variables
    config_data = {}

    # Map environment variables to config fields
    env_mapping = {
        "MCP_SERVER_NAME": "server_name",
        "MCP_LOG_LEVEL": "log_level",
        "MCP_TRANSPORT_TYPE": "transport_type",
        "CURSOR_PATH": "cursor_path",
        "PROJECT_DIRS": "project_directories",
        "ALLOWED_PATHS": "allowed_paths",
        "MAX_FILE_SIZE": "max_file_size",
        "ENABLE_PATH_TRAVERSAL_CHECK": "enable_path_traversal_check",
        "MAX_QUERY_RESULTS": "max_query_results",
    }

    for env_var, field_name in env_mapping.items():
        value = os.getenv(env_var)
        if value is not None:
            # Convert string values to appropriate types
            if field_name in ["max_file_size", "max_query_results"]:
                try:
                    config_data[field_name] = int(value)
                except ValueError:
                    pass
            elif field_name == "enable_path_traversal_check":
                config_data[field_name] = value.lower() in ("true", "1", "yes", "on")
            else:
                config_data[field_name] = value

    return ServerConfig(**config_data)


# Global config instance
config = load_config()
