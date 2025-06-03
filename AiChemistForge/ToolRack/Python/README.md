# AiChemistForge - Python Unified MCP Server

A comprehensive Model Context Protocol (MCP) server built with Python 3.13+, providing a collection of organized tools designed to assist AI development workflows. This server is part of the larger AiChemistForge project but can be run and developed as a standalone service.

## Features

- **Modular Architecture**: Clean separation between the core server infrastructure and individual tools.
- **Auto-Discovery**: Tools are automatically discovered and registered by the server on startup.
- **Type Safety**: Leverages Python's type hinting for improved code quality and maintainability. Pydantic is used for data validation where applicable.
- **Robust Error Handling**: Designed with comprehensive error handling and detailed logging capabilities.
- **Extensible**: Easily add new tools and tool categories to expand functionality.
- **Configuration Management**: Supports environment variables for flexible configuration (see `.env.example`).
- **Stdio Transport**: Primarily uses stdio for communication, making it suitable for local development and integration with tools like Cursor.

## Current Tools

This server can host a variety of tools. As of the last update, it includes:

### Database Tools
- **`query_cursor_database`**: Allows querying and managing Cursor IDE's internal state databases.
  - List projects and workspaces.
  - Query chat history and composer information.
  - Access project-specific databases.

### Filesystem Tools
- **`file_tree`**: Generates a tree-like representation of a directory's structure.
- **`codebase_ingest`**: Processes an entire codebase to prepare it for Large Language Model (LLM) context.

*(This list can be expanded as more tools are added. Refer to the `src/unified_mcp_server/tools/` directory for current implementations.)*

## Installation

### Prerequisites
- Python 3.13 or newer
- [UV Package Manager](https://github.com/astral-sh/uv)

### Setup Instructions

1.  **Clone the Server Directory (if not already part of a larger clone):**
    If you are treating this server as a standalone project, you would clone its specific directory or the parent AiChemistForge repository and navigate here.
    ```bash
    # Example if AiChemistForge is cloned:
    # git clone https://github.com/your-username/AiChemistForge.git
    cd AiChemistForge/ToolRack/Python
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    While UV can manage global tools, it's good practice for project isolation.
    ```bash
    python -m venv .venv
    # On Windows
    .venv\\Scripts\\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies using UV:**
    This command installs all dependencies defined in `pyproject.toml`, including those for different groups (e.g., `dev` dependencies).
    ```bash
    uv sync --all-groups
    ```
    This step is crucial and ensures that all necessary packages, including the `unified_mcp_server` itself and its dependencies, are installed correctly. The `start_mcp_server.bat` script relies on `uv` being available within the environment (often via this installation step creating a shim or by having `uv` installed globally).

4.  **Set up Environment Variables (Optional but Recommended):**
    Copy the `.env.example` file to `.env` and customize the settings as needed.
    ```bash
    copy .env.example .env  # Windows
    # cp .env.example .env    # macOS/Linux
    ```
    Review and edit the `.env` file to configure server name, log levels, paths, etc.

## Usage

### Running the Server

There are a couple of ways to run the MCP server:

1.  **Using the Batch Script (Windows):**
    The `start_mcp_server.bat` script handles setting up the environment and running the server.
    ```bash
    start_mcp_server.bat
    ```
    You can also run it in debug mode for more verbose logging:
    ```bash
    start_mcp_server.bat --debug
    ```
    This script ensures `PYTHONPATH` is set correctly and uses `uv run` to execute the server module.

2.  **Running Manually with UV (Cross-Platform):**
    If you have activated a virtual environment where `uv` and project dependencies are installed:
    ```bash
    uv run python -m unified_mcp_server.main --stdio
    ```
    To enable debug logging similar to the batch script's debug mode, you might need to set the `MCP_LOG_LEVEL` environment variable to `DEBUG` (e.g., in your `.env` file or directly in the command line if supported by your shell).

### Connecting from an MCP Client (e.g., Cursor)

To make this server accessible to an MCP client like Cursor:

1.  **Cursor Settings:**
    Open Cursor settings and navigate to `Features > Model Context Protocol`.

2.  **Add Server Configuration:**
    Add a new server configuration pointing to the `start_mcp_server.bat` script (or the manual command if you prefer, though the batch script is often more robust for pathing).
    *   **Command:** Absolute path to `start_mcp_server.bat` (e.g., `D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\start_mcp_server.bat`).
    *   **CWD (Current Working Directory):** Absolute path to the `ToolRack/Python/` directory (e.g., `D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python`).

    Example JSON for Cursor settings:
    ```json
    {
      "mcpServers": {
        "aichemistforge-python-server": { // Choose a unique name
          "command": "D:\\path\\to\\AiChemistForge\\ToolRack\\Python\\start_mcp_server.bat",
          "cwd": "D:\\path\\to\\AiChemistForge\\ToolRack\\Python"
        }
      }
    }
    ```
    **Note:**
    *   Replace `D:\\path\\to\\` with the actual absolute path to your `AiChemistForge` directory.
    *   Use double backslashes (`\\\\`) for paths in JSON on Windows.
    *   Ensure there are no spaces in the path if possible, as it can sometimes cause issues with command execution in some environments.

3.  **Project-Level MCP (If applicable):**
    If you prefer project-specific MCP configurations in Cursor, enable "Allow Project Level MCP Servers" in Cursor's settings. Then, you can create a `.cursor/mcp.json` file in your target project with a similar configuration.

### Available Tools After Connection (Examples)
Once connected, tools provided by this server will be available in the client:
- `query_cursor_database`
- `file_tree`
- `codebase_ingest`
*(This list will reflect the tools currently enabled and discovered by the server.)*

### Configuration
The server behavior can be customized through environment variables. Key variables are listed in `.env.example`. These include:
- `MCP_SERVER_NAME`: Name of the MCP server.
- `MCP_LOG_LEVEL`: Logging verbosity (e.g., `DEBUG`, `INFO`).
- `MCP_TRANSPORT_TYPE`: Communication transport (typically `stdio`).
- `CURSOR_PATH`: Path to the Cursor application data directory (often auto-detected).
- `PROJECT_DIRS`: Comma-separated list of additional project directories for tools like `query_cursor_database`.
- `MAX_FILE_SIZE`: Maximum file size for file operations.
- `MAX_QUERY_RESULTS`: Maximum results for database queries.

## Development

### Project Structure
The server code is primarily located within the `src/unified_mcp_server` directory:
```
src/unified_mcp_server/
├── server/              # Core server infrastructure (config, logging, main server logic)
│   ├── config.py
│   ├── logging.py
│   └── mcp_server.py
├── tools/               # Tool implementations, organized by category
│   ├── base.py          # BaseTool class for all tools
│   ├── registry.py      # Tool discovery and registration mechanism
│   ├── database/        # Example: Database-related tools
│   └── filesystem/      # Example: Filesystem-related tools
└── main.py              # Main entry point for running the server
```

### Adding New Tools

1.  **Create a Tool Class:**
    Define a new Python class that inherits from `unified_mcp_server.tools.base.BaseTool`.
    ```python
    from ..base import BaseTool
    from pydantic import BaseModel, Field # For input schema validation

    class MyToolInput(BaseModel):
        param1: str = Field(description="Description for parameter 1")
        param2: int = Field(default=0, description="Optional parameter 2")

    class MyTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="my_tool_name", # Unique name for the tool
                description="A clear description of what my tool does.",
                input_schema=MyToolInput.model_json_schema() # Generate schema from Pydantic model
            )

        async def execute(self, validated_args: MyToolInput) -> dict:
            # Your tool's logic here, using validated_args
            # Example: result = await some_async_operation(validated_args.param1)
            return {"message": f"Tool executed with {validated_args.param1} and {validated_args.param2}"}

    ```

2.  **Place the Tool File:**
    Save your new tool file (e.g., `my_new_tool.py`) into an appropriate subdirectory within `src/unified_mcp_server/tools/` (e.g., `src/unified_mcp_server/tools/custom/`). Create a new subdirectory if a suitable category doesn't exist. Ensure the subdirectory has an `__init__.py` file so it's recognized as a package.

3.  **Automatic Discovery:**
    The `ToolRegistry` is designed to automatically discover and load tools from these directories. Ensure your tool class is imported in the `__init__.py` of its respective category folder or that the tool module itself is discoverable.

### Testing
Basic tests can be run to ensure server components are functioning.
```bash
# Example: If you have a test_server.py script
uv run python test_server.py
```
For more detailed testing or specific tool tests, you would typically use a test runner like `pytest`. Ensure development dependencies are installed (`uv sync --all-groups` should cover this if `pytest` is in `dev-dependencies`).

## Architecture

### Core Components
- **`UnifiedMCPServer` (in `mcp_server.py`):** The main class that handles the MCP protocol, connection management, and message dispatching.
- **`ToolRegistry` (in `registry.py`):** Responsible for discovering, loading, and managing all available tools.
- **`BaseTool` (in `tools/base.py`):** An abstract base class that all tools must inherit from, defining a common interface for tool execution and schema definition.
- **`ServerConfig` (in `config.py`):** Manages server configuration, primarily loading settings from environment variables (via `.env` file or system environment).

### Design Principles
- **Separation of Concerns**: The server's operational logic is distinct from the specific functionalities of the tools it hosts.
- **Type Safety**: Extensive use of Python type hints helps in maintaining code quality and catching errors early. Pydantic models are used for schema validation.
- **Extensibility**: The system is designed to be easily extendable with new tools without requiring modifications to the core server logic.
- **Configuration over Code**: Server behavior and tool parameters are managed through configuration where possible, promoting flexibility.

## Contributing
If you wish to contribute to this Python MCP server:
1. Adhere to the existing code structure and design patterns.
2. Ensure comprehensive type hints for all new code.
3. Implement proper error handling and logging for new functionalities.
4. Add tests for any new tools or significant changes to the core.
5. Update documentation (like this README) if your changes affect installation, usage, or add new tools/features.

## License
This project is typically licensed under an open-source license (e.g., MIT). Refer to the `LICENSE` file in the root of the AiChemistForge repository for specific details.

## Support
For issues, questions, or contributions, please refer to the issue tracker or contribution guidelines of the parent AiChemistForge project.