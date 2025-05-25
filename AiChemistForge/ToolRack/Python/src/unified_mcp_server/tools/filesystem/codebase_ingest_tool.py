"""Codebase ingestion tool for FastMCP.

Implements comprehensive error handling per MCP transport best practices:
- File system error handling
- Encoding and binary file handling
- Memory management for large files
- Structured logging to stderr
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.tools.codebase_ingest")


def register_codebase_ingest_tool(mcp: FastMCP) -> None:
    """Register the codebase_ingest tool with the FastMCP instance."""

    @mcp.tool()
    async def codebase_ingest(
        path: str = ".",
        max_file_size: int = 1048576,
        include_binary: bool = False,
        output_format: str = "structured",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        show_tree: bool = True,
        max_files: int = 1000,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """Ingest entire codebase as structured text for LLM context.

        Following MCP transport best practices for error handling and logging.

        Args:
            path: Root directory path to ingest (defaults to current directory)
            max_file_size: Maximum file size in bytes to include (default: 1MB)
            include_binary: Whether to attempt reading binary files (default: False)
            output_format: 'structured' or 'markdown' (default: 'structured')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            show_tree: Whether to include directory tree (default: True)
            max_files: Maximum number of files to process (default: 1000)
            encoding: Text encoding to use (default: 'utf-8')
        """
        logger.debug(f"Starting codebase ingestion for path: {path}")

        try:
            # Input validation per MCP error handling guidelines
            if (
                not isinstance(max_file_size, int)
                or max_file_size < 1024
                or max_file_size > 100 * 1024 * 1024
            ):
                raise ValueError("max_file_size must be between 1KB and 100MB")

            if not isinstance(max_files, int) or max_files < 1 or max_files > 10000:
                raise ValueError("max_files must be between 1 and 10000")

            if output_format not in ["structured", "markdown"]:
                raise ValueError(
                    "output_format must be either 'structured' or 'markdown'"
                )

            # Path resolution with comprehensive error handling
            try:
                target_path = Path(path).expanduser().resolve()
            except (OSError, RuntimeError) as e:
                logger.error(f"Path resolution failed for '{path}': {e}")
                return {
                    "success": False,
                    "error": f"Invalid path: {str(e)}",
                    "path": path,
                    "tool": "codebase_ingest",
                }

            if not target_path.exists():
                logger.warning(f"Path does not exist: {target_path}")
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}",
                    "resolved_path": str(target_path),
                    "tool": "codebase_ingest",
                }

            if not target_path.is_dir():
                logger.warning(f"Path is not a directory: {target_path}")
                return {
                    "success": False,
                    "error": f"Path is not a directory: {path}",
                    "resolved_path": str(target_path),
                    "tool": "codebase_ingest",
                }

            # Set up default patterns
            if include_patterns is None:
                include_patterns = [
                    "*.py",
                    "*.md",
                    "*.txt",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                    "*.toml",
                    "*.cfg",
                    "*.ini",
                    "*.js",
                    "*.ts",
                    "*.jsx",
                    "*.tsx",
                    "*.html",
                    "*.css",
                    "*.scss",
                    "*.less",
                    "*.xml",
                    "*.sql",
                ]

            if exclude_patterns is None:
                exclude_patterns = [
                    "*.pyc",
                    "*.pyo",
                    "__pycache__",
                    ".git",
                    ".venv",
                    "venv",
                    "node_modules",
                    ".pytest_cache",
                    "*.log",
                    "*.tmp",
                    "*.temp",
                    "*.cache",
                    ".DS_Store",
                    "Thumbs.db",
                ]

            logger.debug(f"Using include patterns: {include_patterns}")
            logger.debug(f"Using exclude patterns: {exclude_patterns}")

            # Collect files with error handling
            files_to_process = await _collect_files(
                target_path, include_patterns, exclude_patterns, max_files
            )

            logger.info(f"Found {len(files_to_process)} files to process")

            # Build output with comprehensive error handling
            result_parts = []

            if show_tree:
                tree_result = await _generate_tree_view(target_path)
                result_parts.extend(tree_result)

            # Process files
            processed_files, file_errors = await _process_files(
                files_to_process,
                target_path,
                max_file_size,
                include_binary,
                output_format,
                encoding,
                max_files,
            )

            result_parts.extend(processed_files)
            final_result = "".join(result_parts)

            logger.info(
                f"Codebase ingestion completed: {len(processed_files)} files processed"
            )

            return {
                "success": True,
                "result": final_result,
                "metadata": {
                    "files_processed": len(processed_files),
                    "total_files_found": len(files_to_process),
                    "files_with_errors": len(file_errors),
                    "base_path": str(target_path),
                    "include_patterns": include_patterns,
                    "exclude_patterns": exclude_patterns,
                    "max_file_size": max_file_size,
                    "encoding": encoding,
                    "errors": file_errors if file_errors else None,
                },
                "tool": "codebase_ingest",
            }

        except ValueError as e:
            logger.error(f"Validation error in codebase_ingest: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "codebase_ingest",
            }
        except Exception as e:
            logger.error(f"Unexpected error in codebase_ingest: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "codebase_ingest",
            }


async def _collect_files(
    target_path: Path,
    include_patterns: List[str],
    exclude_patterns: List[str],
    max_files: int,
) -> List[Path]:
    """Collect files to process with comprehensive error handling."""
    files_to_process = []

    def should_include_file(file_path: Path) -> bool:
        """Determine if a file should be included."""
        try:
            # Check exclude patterns first (performance optimization)
            for pattern in exclude_patterns:
                if file_path.match(pattern) or any(
                    part.startswith(".") and part != "." for part in file_path.parts
                ):
                    return False

            # Check include patterns
            return any(file_path.match(pattern) for pattern in include_patterns)
        except (OSError, ValueError) as e:
            logger.debug(f"Error checking file inclusion for {file_path}: {e}")
            return False

    try:
        for file_path in target_path.rglob("*"):
            if len(files_to_process) >= max_files:
                logger.warning(f"Reached maximum file limit of {max_files}")
                break

            try:
                if file_path.is_file() and should_include_file(file_path):
                    files_to_process.append(file_path)
            except (OSError, ValueError) as e:
                logger.debug(f"Error processing file {file_path}: {e}")
                continue

    except (OSError, ValueError) as e:
        logger.error(f"Error collecting files from {target_path}: {e}")
        raise

    return files_to_process


async def _generate_tree_view(target_path: Path) -> List[str]:
    """Generate directory tree view with error handling."""
    tree_parts = ["## Directory Structure\n"]
    tree_lines = [f"{target_path.name}/"]

    def add_tree_items(dir_path: Path, prefix: str = "", depth: int = 0):
        """Add tree items with error handling."""
        if depth >= 5:  # Limit tree depth
            return
        try:
            items = [
                item for item in dir_path.iterdir() if not item.name.startswith(".")
            ]
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                item_name = f"{item.name}/" if item.is_dir() else item.name
                tree_lines.append(f"{prefix}{current_prefix}{item_name}")

                if item.is_dir() and depth + 1 < 5:
                    try:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        add_tree_items(item, next_prefix, depth + 1)
                    except (OSError, ValueError) as e:
                        logger.debug(f"Error processing subdirectory {item}: {e}")
                        error_prefix = prefix + ("    " if is_last else "│   ")
                        tree_lines.append(f"{error_prefix}├── [Error: {str(e)}]")

        except PermissionError:
            tree_lines.append(f"{prefix}├── [Permission Denied]")
        except (OSError, ValueError) as e:
            logger.debug(f"Error processing directory {dir_path}: {e}")
            tree_lines.append(f"{prefix}├── [Error: {str(e)}]")

    try:
        add_tree_items(target_path)
        tree_parts.append("\n".join(tree_lines))
        tree_parts.append("\n\n")
    except Exception as e:
        logger.warning(f"Error generating tree view: {e}")
        tree_parts.append("*Error generating directory tree*\n\n")

    return tree_parts


async def _process_files(
    files_to_process: List[Path],
    target_path: Path,
    max_file_size: int,
    include_binary: bool,
    output_format: str,
    encoding: str,
    max_files: int,
) -> tuple[List[str], List[Dict[str, str]]]:
    """Process files with comprehensive error handling."""
    result_parts = ["## File Contents\n\n"]
    file_errors = []
    processed_count = 0

    for file_path in files_to_process:
        if processed_count >= max_files:
            break

        try:
            relative_path = file_path.relative_to(target_path)
        except ValueError:
            # Handle case where file_path is not relative to target_path
            relative_path = file_path

        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_file_size:
                result_parts.append(f"### {relative_path}\n")
                result_parts.append(f"*File too large ({file_size:,} bytes)*\n\n")
                logger.debug(
                    f"Skipping large file: {relative_path} ({file_size} bytes)"
                )
                continue

            # Try to read file with comprehensive error handling
            content = await _read_file_content(file_path, encoding, include_binary)

            if content is None:
                # File was skipped (e.g., binary file when include_binary is False)
                continue

            # Format content based on output format
            if output_format == "markdown":
                result_parts.append(f"### {relative_path}\n")
                file_ext = file_path.suffix.lstrip(".")
                result_parts.append(f"```{file_ext}\n")
                result_parts.append(content)
                result_parts.append("\n```\n\n")
            else:  # structured
                result_parts.append(f"=== {relative_path} ===\n")
                result_parts.append(content)
                result_parts.append("\n\n")

            processed_count += 1
            logger.debug(f"Processed file: {relative_path}")

        except Exception as e:
            error_info = {
                "file": str(relative_path),
                "error": str(e),
                "type": e.__class__.__name__,
            }
            file_errors.append(error_info)
            logger.warning(f"Error processing file {relative_path}: {e}")

            # Add error placeholder in output
            result_parts.append(f"### {relative_path}\n")
            result_parts.append(f"*Error reading file: {e}*\n\n")

    return result_parts, file_errors


async def _read_file_content(
    file_path: Path, encoding: str, include_binary: bool
) -> Optional[str]:
    """Read file content with comprehensive error handling."""
    try:
        # First attempt: read as text with specified encoding
        return file_path.read_text(encoding=encoding)

    except UnicodeDecodeError:
        if include_binary:
            try:
                # Second attempt: read as binary and decode with latin-1 (preserves bytes)
                logger.debug(
                    f"Unicode decode failed for {file_path}, trying binary read"
                )
                return file_path.read_bytes().decode("latin-1", errors="replace")
            except Exception as e:
                logger.debug(f"Binary read failed for {file_path}: {e}")
                return f"*Binary file - decode error: {str(e)}*"
        else:
            # Skip binary files if not explicitly requested
            logger.debug(f"Skipping binary file: {file_path}")
            return None

    except PermissionError:
        logger.warning(f"Permission denied reading file: {file_path}")
        return "*Permission denied*"

    except FileNotFoundError:
        logger.warning(f"File not found (may have been deleted): {file_path}")
        return "*File not found*"

    except OSError as e:
        logger.warning(f"OS error reading file {file_path}: {e}")
        return f"*OS error: {str(e)}*"

    except Exception as e:
        logger.warning(f"Unexpected error reading file {file_path}: {e}")
        return f"*Unexpected error: {str(e)}*"
