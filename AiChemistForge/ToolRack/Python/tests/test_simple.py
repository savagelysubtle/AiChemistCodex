#!/usr/bin/env python3
"""Simple test for file tree tool."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from unified_mcp_server.tools.filesystem.file_tree import FileTreeTool


async def test_file_tree():
    """Test the file tree tool directly."""
    print("Testing FileTreeTool directly...")

    tool = FileTreeTool()
    result = await tool.safe_execute(
        path=".", max_depth=2, show_sizes=True, format="tree"
    )

    print("Result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(test_file_tree())
