"""Main entry point for the AiChemistForge MCP server."""

import argparse
import logging
import signal
import sys

from fastmcp import FastMCP

# Create single FastMCP server instance
mcp = FastMCP("AiChemistForge")

# Import and register all tools, resources, and prompts
# This keeps the single FastMCP instance while maintaining modular code
from unified_mcp_server.prompts.analysis_prompts import register_analysis_prompts
from unified_mcp_server.resources.cursor_resources import register_cursor_resources
from unified_mcp_server.resources.filesystem_resources import (
    register_filesystem_resources,
)
from unified_mcp_server.tools.database.cursor_database_tool import (
    register_cursor_database_tool,
)
from unified_mcp_server.tools.filesystem.codebase_ingest_tool import (
    register_codebase_ingest_tool,
)
from unified_mcp_server.tools.filesystem.file_tree_tool import register_file_tree_tool
from unified_mcp_server.tools.reasoning.sequential_thinking_tools import (
    register_reasoning_tools,
)

# Register all tools with our FastMCP instance
register_file_tree_tool(mcp)
register_codebase_ingest_tool(mcp)
register_cursor_database_tool(mcp)
register_reasoning_tools(mcp)

# Register all resources
register_filesystem_resources(mcp)
register_cursor_resources(mcp)

# Register all prompts
register_analysis_prompts(mcp)


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown following MCP best practices."""

    def signal_handler(signum: int, frame) -> None:
        """Handle shutdown signals gracefully with proper resource cleanup."""
        # Log shutdown for debugging (will go to stderr)
        logging.getLogger("mcp.server").info(
            f"Received signal {signum}, shutting down gracefully"
        )
        try:
            # Perform any necessary cleanup here
            sys.exit(0)
        except Exception as e:
            logging.getLogger("mcp.server").error(f"Error during shutdown: {e}")
            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def configure_stdio_logging(debug: bool = False) -> None:
    """Configure logging for stdio transport following MCP best practices.

    Per 1000-mcp-stdio-logging.mdc: logs should be easily viewable in the console
    while not interfering with stdio JSON-RPC communication.
    """
    # Create root logger
    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Set appropriate log level
    log_level = logging.DEBUG if debug else logging.INFO
    root_logger.setLevel(log_level)

    # Create stderr handler for MCP compatibility
    # Per 1000-mcp-stdio-logging rule: use stderr for logs to keep stdout clear for JSON-RPC
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log_level)

    # Simple formatter for stdio - avoid complexity per MCP guidelines
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    )
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    # Configure FastMCP logging to be visible but not overwhelming
    fastmcp_logger = logging.getLogger("fastmcp")
    fastmcp_logger.setLevel(logging.WARNING if not debug else logging.DEBUG)

    # Create server logger for our specific use
    server_logger = logging.getLogger("mcp.server")
    server_logger.setLevel(log_level)


def setup_error_handling() -> None:
    """Setup comprehensive error handling per MCP transport best practices."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler for unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle keyboard interrupt gracefully
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log unhandled exceptions
        logger = logging.getLogger("mcp.server")
        logger.critical(
            "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


def main() -> int:
    """Main entry point for the MCP server following MCP best practices."""
    parser = argparse.ArgumentParser(description="AiChemistForge MCP Server")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on"
    )
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host to bind the server to"
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport (default for MCP clients)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup error handling first
    setup_error_handling()

    # Configure logging based on transport type
    if not args.stdio:
        # For HTTP mode, we can use more verbose logging
        logging.basicConfig(
            level=logging.DEBUG if args.debug else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stderr,
        )
    else:
        # For stdio mode, configure per MCP guidelines
        configure_stdio_logging(args.debug)

    # Setup signal handlers
    setup_signal_handlers()

    # Get logger for this module
    logger = logging.getLogger("mcp.server")

    try:
        if args.stdio or not any([args.host != "localhost", args.port != 8000]):
            # Default to stdio for MCP compatibility per 1000-mcp-stdio-logging rule
            logger.info("Starting AiChemistForge MCP server with stdio transport")
            logger.info("Stdio transport selected - logs will appear on stderr")
            logger.debug(
                "Debug logging enabled" if args.debug else "Standard logging level"
            )

            # Use stdio transport for MCP clients (like Cursor) - preferred per MCP guidelines
            mcp.run()  # FastMCP uses stdio by default
        else:
            # Use HTTP transport for web access
            logger.info(
                f"Starting AiChemistForge MCP server with HTTP transport on {args.host}:{args.port}"
            )
            mcp.run(host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        return 0
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
