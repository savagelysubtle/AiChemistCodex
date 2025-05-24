---
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [mcp, python, sdk, guide, server, stdio, tools]
parent: [[_index]]
up: [[_index]]
references: [[[Python SDK Overview]], [[Python Server Development]]]
---

# Building the Ultimate Python STDIN/STDOUT MCP Server

This guide details how to construct a robust, maintainable, and "ultimate" Model Context Protocol (MCP) server in Python. It focuses on communication via STDIN/STDOUT, clear separation of server logic from tool implementations, and incorporates best practices gleaned from the MCP documentation.

## Core Philosophy

An "ultimate" MCP server should be:
-   **Reliable**: Handles errors gracefully and predictably.
-   **Understandable**: Code is well-structured, documented, and uses clear naming.
-   **Scalable**: Tools can be added or modified without major overhauls to the core server.
-   **Secure**: Validates inputs and considers potential security implications.
-   **Efficient**: Uses asynchronous operations for I/O-bound tasks.
-   **Testable**: Designed with testability in mind.

## Prerequisites

1.  **Python**: Version 3.10 or newer.
2.  **UV Package Manager**: `pip install uv` (or use pip directly).
3.  **MCP Libraries**: `mcp` (and `smithery` if not automatically included as a dependency, though `mcp` usually suffices for server creation).

## Project Structure

We'll follow a structure that promotes separation of concerns. This structure is similar to what `create-mcp-server` might generate but emphasizes modularity for tools.

```
mcp_ultimate_stdio_server/
├── pyproject.toml        # Project metadata and dependencies
├── .gitignore            # Standard Python gitignore
└── src/
    └── my_mcp_server/
        ├── __init__.py
        ├── __main__.py     # Server entry point (handles STDIN/STDOUT)
        ├── server.py       # Core FastMCP server instance and tool registration
        └── tools/          # Directory for individual tool modules
            ├── __init__.py
            ├── general_tools.py
            └── data_processing_tools.py
            # ... other tool modules
```

## Step 1: `pyproject.toml` Setup

This file defines your project, its dependencies, and how to run it.

```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
description = "An ultimate MCP server communicating via STDIN/STDOUT."
authors = [
    { name = "Your Name", email = "you@example.com" },
]
requires-python = ">=3.10"
dependencies = [
    "mcp>=0.3.0", # Check for the latest version
    # Add other dependencies your tools might need, e.g.:
    # "aiofiles>=23.0",
    # "httpx>=0.25.0",
]

[project.scripts]
# This allows running the server using 'python -m my_mcp_server' or 'uv run my_mcp_server'
# if 'uv run .' is set up to call the module.
# For direct execution via `python src/my_mcp_server/__main__.py`, this section isn't strictly needed
# but is good practice for packaging.
# If using `uv create-mcp-server`, it might set this up differently.
# For a simple stdio server, direct execution of __main__.py is common.

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

# If using UV for task running (optional, but convenient)
# [tool.uv.scripts]
# start = "python -m src.my_mcp_server"
```

**To install dependencies:**
Using UV: `uv pip install -r requirements.txt` (if you generate one) or `uv sync` (if `pyproject.toml` is complete).
Using Pip: `pip install .` (from the `mcp_ultimate_stdio_server` root directory).

## Step 2: Tool Implementation (`src/my_mcp_server/tools/`)

Create separate Python files for logical groups of tools.

### Example: `src/my_mcp_server/tools/general_tools.py`

```python
# src/my_mcp_server/tools/general_tools.py
import asyncio
from datetime import datetime

async def get_current_time(timezone: str | None = None) -> str:
    """
    Retrieves the current time.
    Optionally, a timezone can be specified (e.g., 'UTC', 'America/New_York').
    If no timezone is provided, returns server's local time.
    """
    # Note: For real timezone handling, you'd use libraries like 'pytz' or 'zoneinfo' (Python 3.9+)
    # This is a simplified example.
    if timezone:
        # Placeholder for actual timezone logic
        return f"Current time in {timezone} (simulated): {datetime.now().isoformat()}"
    return datetime.now().isoformat()

async def echo_message(message: str, repeat: int = 1) -> str:
    """
    Echoes back the provided message, optionally repeating it.
    """
    if not isinstance(message, str):
        raise ValueError("Message must be a string.")
    if not isinstance(repeat, int) or repeat < 1:
        raise ValueError("Repeat count must be a positive integer.")

    await asyncio.sleep(0.01) # Simulate some async work
    return " ".join([message] * repeat)

# You can add more tools here
```

### `src/my_mcp_server/tools/__init__.py`

This file makes the `tools` directory a package and can be used to conveniently import all tool functions.

```python
# src/my_mcp_server/tools/__init__.py
from .general_tools import get_current_time, echo_message
# from .data_processing_tools import process_data_tool

# Add other tool imports here

__all__ = [
    "get_current_time",
    "echo_message",
    # "process_data_tool",
]
```

## Step 3: Server Setup (`src/my_mcp_server/server.py`)

This file initializes the `FastMCP` instance and registers the tools.

```python
# src/my_mcp_server/server.py
from mcp.server.fastmcp import FastMCP

# Import tools from your tool modules
from .tools import get_current_time, echo_message
# from .tools import process_data_tool # Example for another tool

# Initialize the MCP Server
# The name "MyUltimateServer" will be used by clients to identify this server.
mcp_server = FastMCP(
    name="MyUltimateStdioServer",
    description="An advanced MCP server demonstrating best practices.",
    version="1.0.0"
)

# Register Tools
# The decorator registers the function as an MCP tool.
# The function's docstring is used as the tool's description for the LLM.
# Type hints are crucial for the LLM to understand parameter types and return values.

@mcp_server.tool()
async def get_time(timezone: str | None = None) -> str:
    """
    Retrieves the current time.
    You can optionally specify a timezone string (e.g., 'UTC', 'America/New_York').
    If no timezone is provided, it returns the server's local time.
    """
    # Input validation can be added here or within the tool function itself
    if timezone is not None and not isinstance(timezone, str):
        raise TypeError("Timezone must be a string if provided.")
    return await get_current_time(timezone)

@mcp_server.tool(name="utility.echoMessage") # Explicitly naming the tool
async def custom_echo(text_to_echo: str, repetitions: int = 1) -> str:
    """
    Repeats a given text a specified number of times.
    - text_to_echo: The string you want to repeat.
    - repetitions: How many times to repeat the text. Defaults to 1.
    """
    if not isinstance(text_to_echo, str):
        raise TypeError("text_to_echo must be a string.")
    if not isinstance(repetitions, int) or repetitions <= 0:
        raise ValueError("repetitions must be a positive integer.")

    try:
        return await echo_message(message=text_to_echo, repeat=repetitions)
    except ValueError as e:
        # It's good practice to catch specific errors from your tool logic
        # and potentially re-raise them or return an MCP-friendly error.
        # For now, FastMCP will handle converting this to an MCP error.
        raise e


# Example of a resource
@mcp_server.resource(uri="system://server_status")
async def get_server_status() -> dict:
    """
    Provides the current status of the server.
    Returns a dictionary with status information.
    """
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "active_tools": [tool.name for tool in mcp_server.tools.values()]
    }

# You would also register tools from other modules here, e.g.:
# @mcp_server.tool()
# async def process_data(...) -> ...:
#     return await process_data_tool(...)

```

## Step 4: Server Entry Point (`src/my_mcp_server/__main__.py`)

This script runs the server and handles STDIN/STDOUT communication.

```python
# src/my_mcp_server/__main__.py
import asyncio
import sys
import logging

from mcp.server.fastmcp import run_stdio_server
from .server import mcp_server # Import your configured FastMCP instance

# Configure logging for better diagnostics
logging.basicConfig(
    level=logging.INFO, # Change to DEBUG for more verbosity
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stderr # MCP communication is on stdout, so log to stderr
)
logger = logging.getLogger(__name__)

async def main():
    logger.info(f"Starting {mcp_server.name} v{mcp_server.version} on STDIN/STDOUT...")
    try:
        # run_stdio_server handles the communication loop over stdin/stdout
        await run_stdio_server(mcp_server)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Unhandled error in server: {e}", exc_info=True)
    finally:
        logger.info("Server stopped.")

if __name__ == "__main__":
    # On Windows, default event loop policy might cause issues with stdio.
    # ProactorEventLoop is generally recommended for subprocess and pipe handling.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())

```

## Step 5: Running and Testing

1.  **Navigate to the project root** (`mcp_ultimate_stdio_server/`).
2.  **Install dependencies** (if not already done):
    *   `uv sync` or `uv pip install .`
    *   or `pip install .`
3.  **Run the server**:
    *   `python src/my_mcp_server/__main__.py`
    *   Or, if you configured `[project.scripts]` or `[tool.uv.scripts]` in `pyproject.toml`:
        *   `python -m my_mcp_server` (if `src` is in `PYTHONPATH` or installed)
        *   `uv run my_mcp_server` (using UV scripts)
        *   `uv run start` (if you named the UV script `start`)

4.  **Testing with an MCP Client**:
    *   Use an MCP client tool (like `mcp-inspector` if available, or a custom client script as shown in the MCP documentation).
    *   Example client snippet (conceptual, adapt from MCP docs):

        ```python
        # client_test.py (run in a separate terminal)
        import asyncio
        import mcp
        from mcp.client.stdio import stdio_client

        async def run_client():
            server_params = mcp.StdioServerParameters(
                command=sys.executable, # Path to Python interpreter
                args=["src/my_mcp_server/__main__.py"], # Relative path to your server's main
                cwd="/path/to/mcp_ultimate_stdio_server" # Absolute path to server project root
            )
            async with stdio_client(server_params) as (read, write):
                async with mcp.ClientSession(read, write) as session:
                    # Discover tools
                    init_response = await session.initialize()
                    print("Server Info:", init_response.server_info)
                    print("Available Tools:", init_response.tools)

                    # Call a tool
                    try:
                        time_result = await session.call_tool("get_time", {"timezone": "UTC"})
                        print("Time (UTC):", time_result)

                        echo_result = await session.call_tool("utility.echoMessage", {"text_to_echo": "Hello MCP", "repetitions": 3})
                        print("Echo Result:", echo_result)

                        # Try to call with invalid params to test error handling
                        # invalid_echo = await session.call_tool("utility.echoMessage", {"text_to_echo": 123})
                        # print("Invalid Echo:", invalid_echo)

                    except mcp.MCPError as e:
                        print(f"MCP Error: {e.code} - {e.message} - {e.data}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")

        if __name__ == "__main__":
            asyncio.run(run_client())
        ```

## Best Practices for an "Ultimate" Server

*   **Comprehensive Docstrings**: For every tool, clearly describe its purpose, parameters (including types), and what it returns. This is what the LLM sees.
*   **Robust Type Hinting**: Use precise type hints. For complex objects, consider using Pydantic models (and add `pydantic` to dependencies) for automatic validation and serialization if `FastMCP` supports it directly or if you handle it in your tool logic.
*   **Asynchronous All The Way**: Ensure all I/O-bound operations within your tools are `async` and use `await`. This is critical for STDIN/STDOUT servers to remain responsive.
*   **Configuration Management**: For more complex servers, externalize configuration (e.g., API keys, default paths) rather than hardcoding. Use environment variables or config files.
*   **Structured Logging**: Use the `logging` module. Log to `sys.stderr` because `sys.stdout` is used for MCP communication. Include timestamps, log levels, and relevant context.
*   **Detailed Error Handling**:
    *   Inside tools, catch expected exceptions and either handle them gracefully or raise custom, informative exceptions.
    *   `FastMCP` will convert Python exceptions into MCP error responses. Ensure your exceptions provide enough context.
    *   Consider defining a set of standard error codes/messages for your server's domain.
*   **Input Validation**: Don't trust client inputs. Validate parameter types, ranges, formats, and constraints (e.g., for file paths, ensure they are within allowed directories to prevent traversal attacks).
*   **Tool Naming and Organization**:
    *   Use clear, descriptive names for tools.
    *   Use the `name` parameter in `@mcp_server.tool(name="my.custom.tool_name")` to create namespaces for tools, improving organization as the number of tools grows (e.g., `filesystem.readFile`, `database.queryUser`).
*   **Resource URIs**: For `@mcp_server.resource()`, use clear and consistent URI patterns.
*   **Modularity**: Keep tool implementations in separate modules as shown. For very large servers, consider breaking these modules into sub-packages.
*   **Testing**:
    *   **Unit Tests**: Test individual tool functions (the underlying logic, not the MCP-decorated part) with various inputs, including edge cases and invalid data.
    *   **Integration Tests**: Write tests that run the MCP server and use an MCP client (like the example `client_test.py`) to call tools and verify responses, including error conditions.
*   **Security Considerations**:
    *   Be especially careful with tools that interact with the file system, execute commands, or access sensitive data.
    *   Always validate and sanitize paths.
    *   Avoid running external commands with unsanitized user input.
    *   If handling sensitive data, ensure it's not inadvertently logged or exposed.
*   **Documentation**: Maintain external documentation (like this guide!) for your server, explaining its capabilities, how to run it, and any specific tool behaviors.

This guide provides a solid foundation. As your MCP server grows in complexity, you can adapt and expand upon these principles to maintain an "ultimate" level of quality and maintainability.
---

*This guide is based on information from [[Python SDK Overview]] and [[Python Server Development]].*