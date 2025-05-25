"""File tree tool for showing directory structure."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import ToolExecutionError
from .base import BaseFilesystemTool


@dataclass
class TreeNode:
    """Represents a node in the file tree."""

    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    children: Optional[List["TreeNode"]] = None


class FileTreeTool(BaseFilesystemTool):
    """Tool for generating file tree structure from a directory."""

    tool_name = "file_tree"

    def __init__(self):
        super().__init__(
            name="file_tree",
            description="Generate a file tree structure from a directory path",
        )

    async def execute(self, **kwargs) -> Any:
        """Execute the file tree generation.

        Args:
            path: Directory path to analyze (defaults to current directory)
            max_depth: Maximum depth to traverse (default: 5)
            show_hidden: Whether to show hidden files (default: False)
            show_sizes: Whether to show file sizes (default: True)
            format: Output format 'tree' or 'json' (default: 'tree')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
        """
        path = kwargs.get("path", ".")
        max_depth = kwargs.get("max_depth", 5)
        show_hidden = kwargs.get("show_hidden", False)
        show_sizes = kwargs.get("show_sizes", True)
        output_format = kwargs.get("format", "tree")
        include_patterns = kwargs.get("include_patterns", [])
        exclude_patterns = kwargs.get("exclude_patterns", [])

        # Validate path
        resolved_path = self.validate_path(path)

        if not resolved_path.exists():
            raise ToolExecutionError(f"Path does not exist: {resolved_path}")

        if not resolved_path.is_dir():
            raise ToolExecutionError(f"Path is not a directory: {resolved_path}")

        # Generate tree structure
        tree_root = self._build_tree(
            resolved_path,
            max_depth,
            show_hidden,
            show_sizes,
            include_patterns,
            exclude_patterns,
        )

        if output_format == "json":
            return self._tree_to_dict(tree_root)
        else:
            return self._tree_to_string(tree_root)

    def _build_tree(
        self,
        path: Path,
        max_depth: int,
        show_hidden: bool,
        show_sizes: bool,
        include_patterns: List[str],
        exclude_patterns: List[str],
        current_depth: int = 0,
    ) -> TreeNode:
        """Build tree structure recursively."""

        # Create node for current path
        node = TreeNode(
            name=path.name or str(path), path=str(path), is_dir=path.is_dir()
        )

        # Add file size if requested and it's a file
        if show_sizes and path.is_file():
            try:
                node.size = path.stat().st_size
            except OSError:
                node.size = None

        # If it's a directory and we haven't reached max depth
        if path.is_dir() and current_depth < max_depth:
            node.children = []

            try:
                entries = sorted(
                    path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
                )

                for entry in entries:
                    # Skip if excluded directory
                    if entry.is_dir() and self.is_excluded_dir(entry):
                        continue

                    # Skip if excluded file
                    if entry.is_file() and self.is_excluded_file(entry):
                        continue

                    # Skip hidden files if not requested
                    if not show_hidden and entry.name.startswith("."):
                        continue

                    # Apply include/exclude patterns
                    if exclude_patterns and any(
                        entry.match(pattern) for pattern in exclude_patterns
                    ):
                        continue

                    if include_patterns and not any(
                        entry.match(pattern) for pattern in include_patterns
                    ):
                        continue

                    # Recursively build child nodes
                    child_node = self._build_tree(
                        entry,
                        max_depth,
                        show_hidden,
                        show_sizes,
                        include_patterns,
                        exclude_patterns,
                        current_depth + 1,
                    )
                    node.children.append(child_node)

            except PermissionError:
                # Can't read directory, leave children as empty list
                self.logger.warning(f"Permission denied reading directory: {path}")

        return node

    def _tree_to_string(
        self, node: TreeNode, prefix: str = "", is_last: bool = True
    ) -> str:
        """Convert tree to string representation."""
        lines = []

        # Current node line
        connector = "└── " if is_last else "├── "
        size_info = ""

        if node.size is not None:
            size_info = f" ({self.get_file_size_str(node.size)})"

        dir_indicator = "/" if node.is_dir else ""
        lines.append(f"{prefix}{connector}{node.name}{dir_indicator}{size_info}")

        # Children
        if node.children:
            child_prefix = prefix + ("    " if is_last else "│   ")

            for i, child in enumerate(node.children):
                is_last_child = i == len(node.children) - 1
                child_tree = self._tree_to_string(child, child_prefix, is_last_child)
                lines.append(child_tree)

        return "\n".join(lines)

    def _tree_to_dict(self, node: TreeNode) -> Dict[str, Any]:
        """Convert tree to dictionary representation."""
        result = {
            "name": node.name,
            "path": node.path,
            "is_dir": node.is_dir,
        }

        if node.size is not None:
            result["size"] = node.size
            result["size_human"] = self.get_file_size_str(node.size)

        if node.children:
            result["children"] = [self._tree_to_dict(child) for child in node.children]

        return result

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the file tree tool."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to analyze (defaults to current directory)",
                    "default": ".",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to traverse",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Whether to show hidden files",
                    "default": False,
                },
                "show_sizes": {
                    "type": "boolean",
                    "description": "Whether to show file sizes",
                    "default": True,
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["tree", "json"],
                    "default": "tree",
                },
                "include_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of glob patterns to include",
                    "default": [],
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of glob patterns to exclude",
                    "default": [],
                },
            },
        }
