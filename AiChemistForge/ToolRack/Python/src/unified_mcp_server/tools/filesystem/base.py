"""Base filesystem tool interface with security utilities."""

from pathlib import Path
from typing import Optional, Set

from ..base import BaseTool, ToolError, ToolValidationError


class FilesystemError(ToolError):
    """Base exception for filesystem tool errors."""

    pass


class PathTraversalError(FilesystemError):
    """Raised when path traversal attack is detected."""

    pass


class BaseFilesystemTool(BaseTool):
    """Base class for filesystem tools with security features."""

    def __init__(
        self, name: str, description: str, allowed_paths: Optional[Set[str]] = None
    ):
        super().__init__(name, description)
        self.allowed_paths = allowed_paths or set()

        # Add current working directory by default
        self.allowed_paths.add(str(Path.cwd()))

        # Common file extensions to exclude by default
        self.excluded_extensions = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".dylib",
            ".exe",
            ".bin",
            ".obj",
            ".o",
            ".a",
            ".lib",
            ".class",
            ".jar",
            ".war",
            ".ear",
            ".log",
            ".tmp",
            ".temp",
            ".cache",
            ".git",
            ".svn",
            ".hg",
            ".bzr",
            ".ds_store",
            ".desktop.ini",
            "thumbs.db",
            ".lock",
            ".swp",
            ".swo",
            "~",
        }

        # Common directories to exclude
        self.excluded_dirs = {
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            ".bzr",
            "node_modules",
            ".npm",
            ".yarn",
            ".venv",
            "venv",
            ".virtualenv",
            "virtualenv",
            ".tox",
            ".pytest_cache",
            ".coverage",
            "dist",
            "build",
            ".build",
            "target",
            ".idea",
            ".vscode",
            ".vs",
            "logs",
            "log",
            "tmp",
            "temp",
            "cache",
        }

    def validate_path(self, path: str) -> Path:
        """Validate and resolve a file path securely.

        Args:
            path: The path to validate

        Returns:
            Resolved Path object

        Raises:
            PathTraversalError: If path traversal is detected
            ToolValidationError: If path is invalid or not allowed
        """
        try:
            # Convert to Path object and resolve
            resolved_path = Path(path).expanduser().resolve()

            # Check for path traversal attempts
            if ".." in path or path.startswith("/"):
                # Allow absolute paths only if they're in allowed_paths
                if not any(
                    str(resolved_path).startswith(allowed)
                    for allowed in self.allowed_paths
                ):
                    raise PathTraversalError(
                        f"Path traversal detected or not in allowed paths: {path}"
                    )

            # Ensure the resolved path is within allowed directories
            if self.allowed_paths and not any(
                str(resolved_path).startswith(allowed) for allowed in self.allowed_paths
            ):
                raise ToolValidationError(
                    f"Path not in allowed directories: {resolved_path}"
                )

            return resolved_path

        except (OSError, ValueError) as e:
            raise ToolValidationError(f"Invalid path: {path} - {e}")

    def add_allowed_path(self, path: str) -> None:
        """Add a path to the allowed paths set.

        Args:
            path: Path to add to allowed paths
        """
        resolved_path = Path(path).expanduser().resolve()
        self.allowed_paths.add(str(resolved_path))
        self.logger.info(f"Added allowed path: {resolved_path}")

    def is_excluded_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on extension or name.

        Args:
            file_path: Path to check

        Returns:
            True if file should be excluded
        """
        # Check extension
        if file_path.suffix.lower() in self.excluded_extensions:
            return True

        # Check if it's a hidden file (starts with .)
        if file_path.name.startswith(".") and file_path.name not in {
            ".env",
            ".gitignore",
            ".gitattributes",
        }:
            return True

        return False

    def is_excluded_dir(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded.

        Args:
            dir_path: Directory path to check

        Returns:
            True if directory should be excluded
        """
        return dir_path.name.lower() in self.excluded_dirs

    def get_file_size_str(self, size_bytes: int) -> str:
        """Convert file size to human readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human readable size string
        """
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
