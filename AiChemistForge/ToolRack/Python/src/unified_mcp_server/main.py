"""Main entry point for the AiChemistForge MCP server."""

import argparse
import signal
import sys
from pathlib import Path

from .server.config import config
from .server.logging import setup_logging
from .server.app import fastmcp_app


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger = setup_logging("main", config.log_level)
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="AiChemistForge MCP Server")
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
    parser.add_argument("--version", action="version", version="1.0.0")

    args = parser.parse_args()

    logger = setup_logging("main", config.log_level)
    logger.info("Starting AiChemistForge MCP Server")

    # Setup signal handlers
    setup_signal_handlers()

    # Log configuration
    logger.info(f"Server configuration:")
    logger.info(f"  - Server name: {config.server_name}")
    logger.info(f"  - Transport: {args.transport}")
    logger.info(f"  - Log level: {config.log_level}")
    logger.info(f"  - Cursor path: {config.cursor_path}")
    logger.info(f"  - Project directories: {config.project_directories}")

    try:
        if args.transport == "stdio":
            # Run FastMCP with stdio transport
            fastmcp_app.run()
        else:
            logger.error("SSE transport not yet implemented")
            return 1

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

    return 0


def dev_main() -> None:
    """Development entry point with additional debugging."""
    # Enable more verbose logging for development
    import os
    os.environ["MCP_LOG_LEVEL"] = "DEBUG"

    logger = setup_logging("dev", "DEBUG")
    logger.info("Starting server in development mode")

    main()


if __name__ == "__main__":
    exit(main())