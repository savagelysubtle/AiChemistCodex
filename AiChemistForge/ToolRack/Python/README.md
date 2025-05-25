# AiChemistForge - Unified MCP Server

A comprehensive Model Context Protocol (MCP) server that provides organized tools for AI development workflows. Built with Python 3.13 and designed for extensibility and maintainability.

## Features

- **Modular Architecture**: Clean separation between server infrastructure and tools
- **Auto-Discovery**: Automatic tool registration and discovery
- **Type Safety**: Full type hints and Pydantic validation
- **Robust Error Handling**: Comprehensive error handling with detailed logging
- **Extensible**: Easy to add new tools and categories
- **Production Ready**: Proper configuration management and logging
- **Cross-Project Compatible**: Easy setup for multiple projects

## Current Tools

### Database Tools
- **cursor_db**: Query and manage Cursor IDE state databases
  - List projects and workspaces
  - Query chat data and composer information
  - Access project-specific databases

### Filesystem Tools
- **file_tree**: Generate directory tree structures
- **codebase_ingest**: Process entire codebases for LLM context

## Installation

### Prerequisites
- Python 3.13+
- UV package manager

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd ToolRack/Python

# Install dependencies
uv sync --all-groups

# Test the installation
python test_mcp_server.py
```

## Usage

### Running the Server
```bash
# Run with default configuration
uv run python -m unified_mcp_server.main

# Or use the batch script (Windows)
start_mcp_server.bat
```

## Cross-Project Usage

### For Other Projects to Connect to This Server

#### Method 1: Global Configuration (Recommended)
1. Add to **Cursor Settings > Features > Model Context Protocol**:
```json
{
  "mcpServers": {
    "aichemistforge-server": {
      "command": "D:\\path\\to\\AiChemistForge\\ToolRack\\Python\\start_mcp_server.bat",
      "cwd": "D:\\path\\to\\AiChemistForge\\ToolRack\\Python"
    }
  }
}
```

#### Method 2: Project-Level Configuration
1. **Enable project-level MCP** in Cursor settings
2. Copy `mcp_config_template.json` to your project's `.cursor/mcp.json`
3. Update the `ABSOLUTE_PATH_TO_AICHEMISTFORGE` placeholders
4. Restart Cursor

#### Method 3: Use the Template
```bash
# Copy template to your project
cp ToolRack/Python/mcp_config_template.json /path/to/your/project/.cursor/mcp.json

# Edit the file and replace ABSOLUTE_PATH_TO_AICHEMISTFORGE with:
# D:\\Coding\\AiChemistCodex\\AiChemistForge
```

### Important Notes for Cross-Project Setup
- **Absolute paths required** - Cursor doesn't support relative paths well
- **Enable project MCP** - Must be enabled in Cursor settings
- **No spaces in paths** - Avoid paths with spaces for best compatibility
- **Double backslashes** - Use `\\\\` in JSON configurations
- **Tool limit** - Cursor supports max 40 tools simultaneously

### Available Tools After Connection
- `query_cursor_database` - Access Cursor project databases
- `file_tree` - Generate directory structures
- `codebase_ingest` - Process codebases for AI context
- `manage_plugins` - Plugin management (when available)

### Configuration
The server can be configured via environment variables:

```bash
# Server settings
export MCP_SERVER_NAME="my-custom-server"
export MCP_LOG_LEVEL="DEBUG"
export MCP_TRANSPORT_TYPE="stdio"

# Database settings
export CURSOR_PATH="/path/to/cursor"
export PROJECT_DIRS="/path/to/project1,/path/to/project2"

# Security settings
export MAX_FILE_SIZE="20000000"  # 20MB
export MAX_QUERY_RESULTS="2000"
```

### Troubleshooting Cross-Project Issues
See `.cursor/mcp_troubleshooting.md` for comprehensive Windows 11 troubleshooting guide.

Common issues:
- **"Client Closed" errors**: Use `cmd /c` wrapper or batch script
- **Path not found**: Ensure absolute paths and no spaces
- **Tools not visible**: Enable project-level MCP in settings
- **Server timeout**: Check Windows command execution format

## Development

### Project Structure
```
Python/src/unified_mcp_server/
├── server/              # Core server infrastructure
│   ├── config.py       # Configuration management
│   ├── logging.py      # Logging setup
│   └── mcp_server.py   # Main MCP server implementation
├── tools/              # Tool implementations
│   ├── base.py         # Base tool interface
│   ├── registry.py     # Tool discovery and registration
│   ├── database/       # Database tools
│   ├── filesystem/     # File system tools (planned)
│   ├── web/           # Web tools (planned)
│   └── system/        # System tools (planned)
└── main.py            # Entry point
```

### Adding New Tools

1. Create a new tool class inheriting from `BaseTool`:

```python
from ..base import BaseTool

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Description of what my tool does"
        )

    async def execute(self, **kwargs):
        # Tool implementation
        return {"result": "success"}

    def get_schema(self):
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param1"]
        }
```

2. Place the tool in the appropriate category directory
3. The tool will be automatically discovered and registered

### Testing

```bash
# Run basic tests
python test_server.py

# Run with development logging
python -c "import os; os.environ['MCP_LOG_LEVEL']='DEBUG'; exec(open('test_server.py').read())"
```

## Architecture

### Core Components

- **UnifiedMCPServer**: Main server class handling MCP protocol
- **ToolRegistry**: Manages tool discovery and registration
- **BaseTool**: Abstract base class for all tools
- **ServerConfig**: Configuration management with environment variable support

### Design Principles

- **Separation of Concerns**: Clear boundaries between server infrastructure and tools
- **Type Safety**: Comprehensive type hints throughout
- **Error Handling**: Graceful error handling with detailed logging
- **Extensibility**: Easy to add new tools and modify existing ones
- **Configuration**: Environment-based configuration for different deployment scenarios

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive type hints
3. Include proper error handling
4. Add tests for new functionality
5. Update documentation

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please use the project's issue tracker.