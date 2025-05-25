"""Codebase ingestion tool for reading entire projects as structured text."""

import fnmatch
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import ToolExecutionError
from .base import BaseFilesystemTool


@dataclass
class FileInfo:
    """Information about a file in the codebase."""

    path: str
    relative_path: str
    size: int
    is_text: bool
    content: Optional[str] = None
    error: Optional[str] = None


class CodebaseIngestTool(BaseFilesystemTool):
    """Tool for ingesting entire codebases as structured text for LLMs."""

    tool_name = "codebase_ingest"

    def __init__(self):
        super().__init__(
            name="codebase_ingest",
            description="Ingest entire codebase as structured text for LLM context",
        )

        # Common text file extensions
        self.text_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".md",
            ".rst",
            ".txt",
            ".xml",
            ".svg",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".kt",
            ".swift",
            ".dart",
            ".scala",
            ".clj",
            ".hs",
            ".sql",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".dockerfile",
            ".gitignore",
            ".gitattributes",
            ".editorconfig",
            ".env",
            ".env.example",
            ".env.local",
            ".env.production",
            ".makefile",
            ".cmake",
            ".gradle",
            ".maven",
        }

        # Binary/large file extensions to always skip
        self.binary_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".ico",
            ".svg",
            ".webp",
            ".mp4",
            ".mp3",
            ".wav",
            ".avi",
            ".mov",
            ".mkv",
            ".webm",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".zip",
            ".tar",
            ".gz",
            ".7z",
            ".rar",
            ".bz2",
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".app",
            ".dmg",
            ".pkg",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot",
            ".otf",
        }

    async def execute(self, **kwargs) -> Any:
        """Execute codebase ingestion.

        Args:
            path: Root directory path to ingest (defaults to current directory)
            max_file_size: Maximum file size in bytes to include (default: 1MB)
            include_binary: Whether to attempt reading binary files (default: False)
            output_format: 'structured' or 'markdown' (default: 'structured')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude (in addition to defaults)
            show_tree: Whether to include directory tree (default: True)
            max_files: Maximum number of files to process (default: 1000)
            encoding: Text encoding to use (default: 'utf-8')
        """
        path = kwargs.get("path", ".")
        max_file_size = kwargs.get("max_file_size", 1024 * 1024)  # 1MB default
        include_binary = kwargs.get("include_binary", False)
        output_format = kwargs.get("output_format", "structured")
        include_patterns = kwargs.get("include_patterns", [])
        exclude_patterns = kwargs.get("exclude_patterns", [])
        show_tree = kwargs.get("show_tree", True)
        max_files = kwargs.get("max_files", 1000)
        encoding = kwargs.get("encoding", "utf-8")

        # Validate path
        resolved_path = self.validate_path(path)

        if not resolved_path.exists():
            raise ToolExecutionError(f"Path does not exist: {resolved_path}")

        if not resolved_path.is_dir():
            raise ToolExecutionError(f"Path is not a directory: {resolved_path}")

        # Collect files
        files = self._collect_files(
            resolved_path,
            max_file_size,
            include_binary,
            include_patterns,
            exclude_patterns,
            max_files,
        )

        # Read file contents
        processed_files = self._read_files(files, encoding, max_file_size)

        # Generate output
        if output_format == "markdown":
            return self._generate_markdown_output(
                resolved_path, processed_files, show_tree
            )
        else:
            return self._generate_structured_output(
                resolved_path, processed_files, show_tree
            )

    def _collect_files(
        self,
        root_path: Path,
        max_file_size: int,
        include_binary: bool,
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_files: int,
    ) -> List[Path]:
        """Collect all files that should be processed."""
        files = []
        file_count = 0

        for file_path in root_path.rglob("*"):
            if file_count >= max_files:
                self.logger.warning(f"Reached maximum file limit of {max_files}")
                break

            if not file_path.is_file():
                continue

            # Skip if in excluded directory
            if any(self.is_excluded_dir(parent) for parent in file_path.parents):
                continue

            # Skip excluded files
            if self.is_excluded_file(file_path):
                continue

            # Check file size
            try:
                if file_path.stat().st_size > max_file_size:
                    self.logger.debug(f"Skipping large file: {file_path}")
                    continue
            except OSError:
                continue

            # Apply include/exclude patterns
            relative_path = file_path.relative_to(root_path)
            relative_str = str(relative_path)

            # Check exclude patterns
            if exclude_patterns and any(
                fnmatch.fnmatch(relative_str, pattern) for pattern in exclude_patterns
            ):
                continue

            # Check include patterns
            if include_patterns and not any(
                fnmatch.fnmatch(relative_str, pattern) for pattern in include_patterns
            ):
                continue

            # Skip binary files unless explicitly included
            if not include_binary and self._is_binary_file(file_path):
                continue

            files.append(file_path)
            file_count += 1

        return sorted(files)

    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is likely binary."""
        # Check extension first
        if file_path.suffix.lower() in self.binary_extensions:
            return True

        if file_path.suffix.lower() in self.text_extensions:
            return False

        # Use mimetypes to guess
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type.startswith(("text/", "application/json", "application/xml")):
                return False
            if mime_type.startswith(("image/", "video/", "audio/", "application/")):
                return True

        # Sample first few bytes to detect binary content
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:  # Null bytes indicate binary
                    return True
        except (OSError, PermissionError):
            return True

        return False

    def _read_files(
        self, files: List[Path], encoding: str, max_file_size: int
    ) -> List[FileInfo]:
        """Read content from all files."""
        processed_files = []

        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                relative_path = file_path.relative_to(
                    file_path.parents[len(file_path.parents) - 1]
                )

                file_info = FileInfo(
                    path=str(file_path),
                    relative_path=str(relative_path),
                    size=file_size,
                    is_text=not self._is_binary_file(file_path),
                )

                if file_info.is_text and file_size <= max_file_size:
                    try:
                        with open(
                            file_path, "r", encoding=encoding, errors="ignore"
                        ) as f:
                            file_info.content = f.read()
                    except (OSError, UnicodeDecodeError) as e:
                        file_info.error = str(e)
                        self.logger.warning(f"Could not read {file_path}: {e}")

                processed_files.append(file_info)

            except OSError as e:
                self.logger.warning(f"Could not process {file_path}: {e}")

        return processed_files

    def _generate_tree_structure(self, root_path: Path, files: List[FileInfo]) -> str:
        """Generate a tree structure representation."""
        tree_lines = [f"📁 {root_path.name}/"]

        # Build directory structure
        dirs = set()
        for file_info in files:
            parts = Path(file_info.relative_path).parts
            for i in range(len(parts)):
                dir_path = "/".join(parts[: i + 1])
                if i < len(parts) - 1:  # Not the file itself
                    dirs.add(dir_path)

        # Sort and display
        all_paths = list(dirs) + [f.relative_path for f in files]
        all_paths.sort()

        for path in all_paths:
            depth = path.count("/")
            indent = "  " * depth
            name = path.split("/")[-1]
            if path in dirs:
                tree_lines.append(f"{indent}📁 {name}/")
            else:
                tree_lines.append(f"{indent}📄 {name}")

        return "\n".join(tree_lines)

    def _generate_structured_output(
        self, root_path: Path, files: List[FileInfo], show_tree: bool
    ) -> Dict[str, Any]:
        """Generate structured output format."""
        result = {
            "root_path": str(root_path),
            "total_files": len(files),
            "text_files": len([f for f in files if f.is_text]),
            "total_size": sum(f.size for f in files),
            "files": [],
        }

        if show_tree:
            result["tree_structure"] = self._generate_tree_structure(root_path, files)

        for file_info in files:
            file_data = {
                "path": file_info.relative_path,
                "size": file_info.size,
                "size_human": self.get_file_size_str(file_info.size),
                "is_text": file_info.is_text,
            }

            if file_info.content is not None:
                file_data["content"] = file_info.content
                file_data["line_count"] = len(file_info.content.splitlines())

            if file_info.error:
                file_data["error"] = file_info.error

            result["files"].append(file_data)

        return result

    def _generate_markdown_output(
        self, root_path: Path, files: List[FileInfo], show_tree: bool
    ) -> str:
        """Generate markdown format output."""
        lines = [
            f"# Codebase: {root_path.name}",
            "",
            f"**Root Path:** `{root_path}`",
            f"**Total Files:** {len(files)}",
            f"**Text Files:** {len([f for f in files if f.is_text])}",
            f"**Total Size:** {self.get_file_size_str(sum(f.size for f in files))}",
            "",
        ]

        if show_tree:
            lines.extend(
                [
                    "## Directory Structure",
                    "",
                    "```",
                    self._generate_tree_structure(root_path, files),
                    "```",
                    "",
                ]
            )

        lines.extend(["## File Contents", ""])

        for file_info in files:
            if file_info.content is not None:
                # Determine language for syntax highlighting
                lang = self._get_language_from_extension(
                    Path(file_info.relative_path).suffix
                )

                lines.extend(
                    [
                        f"### {file_info.relative_path}",
                        "",
                        f"**Size:** {self.get_file_size_str(file_info.size)} | **Lines:** {len(file_info.content.splitlines())}",
                        "",
                        f"```{lang}",
                        file_info.content,
                        "```",
                        "",
                    ]
                )
            elif file_info.error:
                lines.extend(
                    [
                        f"### {file_info.relative_path} ⚠️",
                        "",
                        f"**Error:** {file_info.error}",
                        "",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"### {file_info.relative_path} (Binary)",
                        "",
                        f"**Size:** {self.get_file_size_str(file_info.size)}",
                        "",
                    ]
                )

        return "\n".join(lines)

    def _get_language_from_extension(self, ext: str) -> str:
        """Get language identifier for syntax highlighting."""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "fish",
            ".ps1": "powershell",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".kt": "kotlin",
            ".swift": "swift",
            ".dart": "dart",
        }
        return lang_map.get(ext.lower(), "text")

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the codebase ingest tool."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Root directory path to ingest (defaults to current directory)",
                    "default": ".",
                },
                "max_file_size": {
                    "type": "integer",
                    "description": "Maximum file size in bytes to include",
                    "default": 1048576,  # 1MB
                    "minimum": 1024,
                    "maximum": 10485760,  # 10MB
                },
                "include_binary": {
                    "type": "boolean",
                    "description": "Whether to attempt reading binary files",
                    "default": False,
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["structured", "markdown"],
                    "default": "structured",
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
                "show_tree": {
                    "type": "boolean",
                    "description": "Whether to include directory tree",
                    "default": True,
                },
                "max_files": {
                    "type": "integer",
                    "description": "Maximum number of files to process",
                    "default": 1000,
                    "minimum": 1,
                    "maximum": 5000,
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding to use",
                    "default": "utf-8",
                    "enum": ["utf-8", "latin-1", "ascii"],
                },
            },
        }
