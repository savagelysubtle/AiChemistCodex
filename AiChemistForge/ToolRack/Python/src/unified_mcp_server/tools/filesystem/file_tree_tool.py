"""File tree generation tool for FastMCP.

Implements comprehensive error handling per MCP transport best practices:
- Path validation and security
- Permission error handling
- Resource cleanup
- Structured logging to stderr
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.tools.file_tree")


def register_file_tree_tool(mcp: FastMCP) -> None:
    """Register the file_tree tool with the FastMCP instance."""

    @mcp.tool()
    async def file_tree(
        path: str = ".",
        max_depth: int = 5,
        show_hidden: bool = False,
        show_sizes: bool = True,
        format: str = "tree",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a file tree structure from a directory path.

        Following MCP transport best practices for error handling and logging.

        Args:
            path: Directory path to analyze (defaults to current directory)
            max_depth: Maximum depth to traverse (default: 5)
            show_hidden: Whether to show hidden files (default: False)
            show_sizes: Whether to show file sizes (default: True)
            format: Output format 'tree' or 'json' (default: 'tree')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
        """
        logger.debug(f"Starting file tree generation for path: {path}")

        try:
            # Input validation per MCP error handling guidelines
            if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 20:
                raise ValueError("max_depth must be an integer between 1 and 20")

            if format not in ["tree", "json"]:
                raise ValueError("format must be either 'tree' or 'json'")

            # Path resolution with comprehensive error handling
            try:
                target_path = Path(path).expanduser().resolve()
            except (OSError, RuntimeError) as e:
                logger.error(f"Path resolution failed for '{path}': {e}")
                return {
                    "success": False,
                    "error": f"Invalid path: {str(e)}",
                    "path": path,
                    "tool": "file_tree",
                }

            if not target_path.exists():
                logger.warning(f"Path does not exist: {target_path}")
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}",
                    "resolved_path": str(target_path),
                    "tool": "file_tree",
                }

            if not target_path.is_dir():
                logger.warning(f"Path is not a directory: {target_path}")
                return {
                    "success": False,
                    "error": f"Path is not a directory: {path}",
                    "resolved_path": str(target_path),
                    "tool": "file_tree",
                }

            # Access permission check
            try:
                list(target_path.iterdir())
            except PermissionError:
                logger.error(f"Permission denied accessing directory: {target_path}")
                return {
                    "success": False,
                    "error": f"Permission denied accessing directory: {path}",
                    "resolved_path": str(target_path),
                    "tool": "file_tree",
                }

            logger.debug(f"Processing directory: {target_path} with format: {format}")

            def should_include(item_path: Path) -> bool:
                """Determine if a path should be included in the tree."""
                try:
                    if not show_hidden and item_path.name.startswith("."):
                        return False
                    if include_patterns:
                        return any(
                            item_path.match(pattern) for pattern in include_patterns
                        )
                    if exclude_patterns:
                        return not any(
                            item_path.match(pattern) for pattern in exclude_patterns
                        )
                    return True
                except (OSError, ValueError) as e:
                    logger.debug(f"Error checking include status for {item_path}: {e}")
                    return False

            if format == "json":
                result_data = await _build_json_tree(
                    target_path, should_include, show_sizes, max_depth
                )
                logger.info(f"Generated JSON tree for {target_path}")
                return {
                    "success": True,
                    "result": result_data,
                    "metadata": {
                        "format": "json",
                        "path": str(target_path),
                        "max_depth": max_depth,
                    },
                    "tool": "file_tree",
                }
            else:  # tree format
                result_text = await _build_text_tree(
                    target_path, should_include, show_sizes, max_depth
                )
                logger.info(f"Generated text tree for {target_path}")
                return {
                    "success": True,
                    "result": result_text,
                    "metadata": {
                        "format": "tree",
                        "path": str(target_path),
                        "max_depth": max_depth,
                    },
                    "tool": "file_tree",
                }

        except ValueError as e:
            logger.error(f"Validation error in file_tree: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "file_tree",
            }
        except Exception as e:
            logger.error(f"Unexpected error in file_tree: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "file_tree",
            }


async def _build_json_tree(
    target_path: Path, should_include, show_sizes: bool, max_depth: int
) -> Dict[str, Any]:
    """Build JSON tree structure with comprehensive error handling."""

    def build_tree_dict(dir_path: Path, depth: int = 0) -> Dict[str, Any]:
        """Recursively build tree dictionary with error handling."""
        if depth >= max_depth:
            return {}

        node = {
            "name": dir_path.name,
            "path": str(dir_path),
            "is_dir": dir_path.is_dir(),
            "children": [],
        }

        # Get file size with error handling
        if show_sizes and dir_path.is_file():
            try:
                node["size"] = dir_path.stat().st_size
            except (OSError, ValueError) as e:
                logger.debug(f"Could not get size for {dir_path}: {e}")
                node["size"] = 0

        # Process directory children with error handling
        if dir_path.is_dir() and depth < max_depth:
            try:
                items = sorted(
                    dir_path.iterdir(),
                    key=lambda x: (x.is_file(), x.name.lower()),
                )

                for item in items:
                    if should_include(item):
                        try:
                            child = build_tree_dict(item, depth + 1)
                            if child:  # Only add non-empty children
                                node["children"].append(child)
                        except (OSError, ValueError) as e:
                            logger.debug(f"Error processing child {item}: {e}")
                            # Add error node for failed children
                            node["children"].append(
                                {
                                    "name": item.name,
                                    "path": str(item),
                                    "error": str(e),
                                    "is_dir": False,
                                    "children": [],
                                }
                            )

            except PermissionError:
                node["error"] = "Permission denied"
            except (OSError, ValueError) as e:
                logger.debug(f"Error accessing directory {dir_path}: {e}")
                node["error"] = str(e)

        return node

    return build_tree_dict(target_path)


async def _build_text_tree(
    target_path: Path, should_include, show_sizes: bool, max_depth: int
) -> str:
    """Build text tree structure with comprehensive error handling."""
    tree_lines = [f"{target_path.name}/"]

    def add_tree_items(dir_path: Path, prefix: str = "", depth: int = 0):
        """Recursively add tree items with error handling."""
        if depth >= max_depth:
            return

        try:
            items = [item for item in dir_path.iterdir() if should_include(item)]
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "

                # Get size info with error handling
                size_str = ""
                if show_sizes and item.is_file():
                    try:
                        size = item.stat().st_size
                        if size < 1024:
                            size_str = f" ({size:,} B)"
                        elif size < 1024 * 1024:
                            size_str = f" ({size / 1024:.1f} KB)"
                        else:
                            size_str = f" ({size / (1024 * 1024):.1f} MB)"
                    except (OSError, ValueError) as e:
                        logger.debug(f"Could not get size for {item}: {e}")
                        size_str = " (size unknown)"

                item_name = f"{item.name}/" if item.is_dir() else item.name
                tree_lines.append(f"{prefix}{current_prefix}{item_name}{size_str}")

                # Recurse into directories
                if item.is_dir() and depth + 1 < max_depth:
                    try:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        add_tree_items(item, next_prefix, depth + 1)
                    except (OSError, ValueError) as e:
                        logger.debug(f"Error recursing into {item}: {e}")
                        error_prefix = prefix + ("    " if is_last else "│   ")
                        tree_lines.append(f"{error_prefix}├── [Error: {str(e)}]")

        except PermissionError:
            tree_lines.append(f"{prefix}├── [Permission Denied]")
        except (OSError, ValueError) as e:
            logger.debug(f"Error processing directory {dir_path}: {e}")
            tree_lines.append(f"{prefix}├── [Error: {str(e)}]")

    add_tree_items(target_path)
    return "\n".join(tree_lines)
