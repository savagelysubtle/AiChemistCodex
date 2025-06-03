"""Codebase ingestion tool for FastMCP.

Implements comprehensive error handling per MCP transport best practices:
- File system error handling
- Encoding and binary file handling
- Memory management for large files
- Structured logging to stderr
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.tools.codebase_ingest")


def register_codebase_ingest_tool(mcp: FastMCP) -> None:
    """Register the codebase_ingest tool with the FastMCP instance."""

    def _estimate_tokens(content: str) -> int:
        """Estimate token count for content using simple regex."""
        try:
            # Simple token estimation: split on word boundaries and symbols
            tokens = len(re.findall(r"\b\w+\b|[^\w\s]", content))
            return int(tokens * 0.75)  # Rough GPT estimation
        except Exception:
            return len(content) // 4  # Fallback: character-based

    def _detect_language(file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "React",
            ".ts": "TypeScript",
            ".tsx": "React TypeScript",
            ".java": "Java",
            ".kt": "Kotlin",
            ".swift": "Swift",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sql": "SQL",
            ".sh": "Shell",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".json": "JSON",
            ".xml": "XML",
            ".md": "Markdown",
            ".txt": "Text",
        }
        return ext_map.get(file_path.suffix.lower(), "Unknown")

    def _extract_file_components(content: str, language: str) -> Dict[str, Any]:
        """Extract components (functions, classes) from file content."""
        components = {"functions": [], "classes": [], "imports": [], "exports": []}

        try:
            if language == "Python":
                components["functions"] = re.findall(
                    r"^\s*def\s+(\w+)", content, re.MULTILINE
                )
                components["classes"] = re.findall(
                    r"^\s*class\s+(\w+)", content, re.MULTILINE
                )
                components["imports"] = re.findall(
                    r"^\s*(?:from\s+\w+\s+)?import\s+([^\n]+)", content, re.MULTILINE
                )
            elif language in ["JavaScript", "TypeScript", "React", "React TypeScript"]:
                components["functions"] = re.findall(
                    r"(?:function\s+(\w+)|const\s+(\w+)\s*=|(\w+)\s*:\s*\()", content
                )
                components["functions"] = [
                    f for group in components["functions"] for f in group if f
                ]
                components["classes"] = re.findall(r"class\s+(\w+)", content)
                components["imports"] = re.findall(
                    r'import\s+.*?from\s+[\'"]([^\'"]+)', content
                )
                components["exports"] = re.findall(
                    r"export\s+(?:default\s+)?(?:class|function|const)?\s*(\w+)",
                    content,
                )
        except Exception as e:
            logger.debug(f"Error extracting components: {e}")

        return components

    def _calculate_file_complexity(content: str) -> str:
        """Calculate file complexity based on various metrics."""
        try:
            lines = len(content.splitlines())
            tokens = _estimate_tokens(content)

            # Complexity indicators
            control_structures = len(
                re.findall(
                    r"\b(if|for|while|switch|try|catch)\b", content, re.IGNORECASE
                )
            )
            nesting_indicators = (
                content.count("{") + content.count("[") + content.count("(")
            )

            # Calculate complexity score
            complexity_score = 0
            if lines > 100:
                complexity_score += 1
            if tokens > 1000:
                complexity_score += 1
            if control_structures > 15:
                complexity_score += 1
            if nesting_indicators > 50:
                complexity_score += 1

            if complexity_score >= 3:
                return "High"
            elif complexity_score >= 2:
                return "Medium"
            else:
                return "Low"
        except Exception:
            return "Unknown"

    def _chunk_content_intelligently(
        content: str, max_tokens: int, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Intelligently chunk file content based on structure."""
        chunks = []
        total_tokens = _estimate_tokens(content)

        if total_tokens <= max_tokens:
            return [
                {"content": content, "tokens": total_tokens, "chunk_info": "complete"}
            ]

        # Try to split on logical boundaries
        language = _detect_language(file_path)

        if language == "Python":
            # Split on class and function definitions
            patterns = [r"\n(?=class\s+\w+)", r"\n(?=def\s+\w+)", r"\n\n"]
        elif language in ["JavaScript", "TypeScript"]:
            # Split on function definitions and class definitions
            patterns = [
                r"\n(?=class\s+\w+)",
                r"\n(?=function\s+\w+)",
                r"\n(?=const\s+\w+\s*=)",
                r"\n\n",
            ]
        else:
            # Generic splitting on double newlines
            patterns = [r"\n\n\n", r"\n\n"]

        # Try splitting with each pattern
        for pattern in patterns:
            parts = re.split(pattern, content)
            if len(parts) > 1:
                current_chunk = ""
                chunk_tokens = 0

                for part in parts:
                    part_tokens = _estimate_tokens(part)

                    if chunk_tokens + part_tokens <= max_tokens and current_chunk:
                        current_chunk += pattern.replace(r"\n", "\n") + part
                        chunk_tokens += part_tokens
                    else:
                        if current_chunk:
                            chunks.append(
                                {
                                    "content": current_chunk,
                                    "tokens": chunk_tokens,
                                    "chunk_info": f"logical_split_{len(chunks) + 1}",
                                }
                            )
                        current_chunk = part
                        chunk_tokens = part_tokens

                if current_chunk:
                    chunks.append(
                        {
                            "content": current_chunk,
                            "tokens": chunk_tokens,
                            "chunk_info": f"logical_split_{len(chunks) + 1}",
                        }
                    )

                if all(chunk["tokens"] <= max_tokens for chunk in chunks):
                    return chunks

        # Fallback: simple line-based chunking
        lines = content.splitlines()
        current_chunk_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = _estimate_tokens(line)

            if current_tokens + line_tokens <= max_tokens:
                current_chunk_lines.append(line)
                current_tokens += line_tokens
            else:
                if current_chunk_lines:
                    chunks.append(
                        {
                            "content": "\n".join(current_chunk_lines),
                            "tokens": current_tokens,
                            "chunk_info": f"line_split_{len(chunks) + 1}",
                        }
                    )
                current_chunk_lines = [line]
                current_tokens = line_tokens

        if current_chunk_lines:
            chunks.append(
                {
                    "content": "\n".join(current_chunk_lines),
                    "tokens": current_tokens,
                    "chunk_info": f"line_split_{len(chunks) + 1}",
                }
            )

        return chunks

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
        # NEW: LLM-optimized features
        max_context_tokens: int = 100000,
        chunk_strategy: str = "intelligent",  # intelligent/simple/none
        include_components: bool = True,
        include_complexity: bool = True,
        llm_optimized: bool = True,
    ) -> Dict[str, Any]:
        """Ingest entire codebase as structured text for LLM context.

        Use Tool to ingest entire codebase as structured text for faster codebase context.

        IMPORTANT: When using "." as the path, it will use the MCP server's working directory,
        NOT your agent's current directory. For specific workspaces, always provide the FULL PATH.

        Examples:
        - path="." → Uses MCP server's directory (may not be your workspace)
        - path="D:\\AI_Dev_Hub\\AiResearchAgent" → Uses the specific workspace directory
        - path="/home/user/project" → Uses the specific project directory

        Args:
            path: Root directory path to ingest. Use FULL PATHS for specific workspaces (defaults to MCP server's current directory)
            max_file_size: Maximum file size in bytes to include (default: 1MB)
            include_binary: Whether to attempt reading binary files (default: False)
            output_format: 'structured' or 'markdown' (default: 'structured')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            show_tree: Whether to include directory tree (default: True)
            max_files: Maximum number of files to process (default: 1000)
            encoding: Text encoding to use (default: 'utf-8')
            max_context_tokens: Maximum number of tokens for LLM context (default: 100000)
            chunk_strategy: Strategy for chunking files (default: 'intelligent')
            include_components: Whether to include file components (default: True)
            include_complexity: Whether to include file complexity (default: True)
            llm_optimized: Whether to optimize for LLM context (default: True)
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
            processed_files, file_errors = await _process_files_enhanced(
                files_to_process,
                target_path,
                max_file_size,
                include_binary,
                output_format,
                encoding,
                max_files,
                max_context_tokens,
                chunk_strategy,
                include_components,
                include_complexity,
                llm_optimized,
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


async def _process_files_enhanced(
    files_to_process: List[Path],
    target_path: Path,
    max_file_size: int,
    include_binary: bool,
    output_format: str,
    encoding: str,
    max_files: int,
    max_context_tokens: int,
    chunk_strategy: str,
    include_components: bool,
    include_complexity: bool,
    llm_optimized: bool,
) -> tuple[List[str], List[Dict[str, str]]]:
    """Process files with enhanced LLM optimization and smart chunking."""
    result_parts = []
    if llm_optimized:
        result_parts.append("# 🗂️ Codebase Analysis Report\n\n")
    else:
        result_parts.append("## File Contents\n\n")

    file_errors = []
    processed_count = 0
    total_tokens = 0
    language_stats = {}
    complexity_stats = {"Low": 0, "Medium": 0, "High": 0}

    for file_path in files_to_process:
        if processed_count >= max_files:
            break

        try:
            relative_path = file_path.relative_to(target_path)
        except ValueError:
            relative_path = file_path

        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_file_size:
                if llm_optimized:
                    result_parts.append(f"### 📄 {relative_path}\n")
                    result_parts.append(
                        f"⚠️ *File too large ({file_size:,} bytes) - skipped*\n\n"
                    )
                else:
                    result_parts.append(f"### {relative_path}\n")
                    result_parts.append(f"*File too large ({file_size:,} bytes)*\n\n")
                logger.debug(
                    f"Skipping large file: {relative_path} ({file_size} bytes)"
                )
                continue

            # Read and analyze file content
            content = await _read_file_content(file_path, encoding, include_binary)
            if content is None:
                continue

            # Detect language and analyze
            language = _detect_language(file_path)
            language_stats[language] = language_stats.get(language, 0) + 1

            # Calculate metrics
            file_tokens = _estimate_tokens(content)
            total_tokens += file_tokens

            complexity = "Unknown"
            components = {}

            if include_complexity:
                complexity = _calculate_file_complexity(content)
                complexity_stats[complexity] = complexity_stats.get(complexity, 0) + 1

            if include_components:
                components = _extract_file_components(content, language)

            # Format file header with enhanced info
            if llm_optimized:
                header = f"### 📄 {relative_path}"
                if language != "Unknown":
                    header += f" ({language})"

                # Add metrics
                lines = len(content.splitlines())
                metrics = [f"{file_tokens:,} tokens", f"{lines:,} lines"]

                if include_complexity and complexity != "Unknown":
                    metrics.append(f"{complexity.lower()} complexity")

                if include_components and any(components.values()):
                    comp_info = []
                    if components.get("functions"):
                        comp_info.append(f"{len(components['functions'])} functions")
                    if components.get("classes"):
                        comp_info.append(f"{len(components['classes'])} classes")
                    if comp_info:
                        metrics.append(", ".join(comp_info))

                header += f"\n📊 **Metrics**: {' | '.join(metrics)}\n"

                # Add component details if requested
                if include_components and any(components.values()):
                    header += "\n🔧 **Components**:\n"
                    if components.get("functions"):
                        header += f"- **Functions**: {', '.join(components['functions'][:10])}"
                        if len(components["functions"]) > 10:
                            header += f" (+{len(components['functions']) - 10} more)"
                        header += "\n"
                    if components.get("classes"):
                        header += f"- **Classes**: {', '.join(components['classes'])}\n"
                    if components.get("imports"):
                        imports = components["imports"][:5]
                        header += f"- **Key Imports**: {', '.join(imports)}"
                        if len(components["imports"]) > 5:
                            header += f" (+{len(components['imports']) - 5} more)"
                        header += "\n"
                    header += "\n"
            else:
                header = f"### {relative_path}\n"

            result_parts.append(header)

            # Handle chunking
            if chunk_strategy != "none" and file_tokens > max_context_tokens // 10:
                # Chunk large files
                chunks = _chunk_content_intelligently(
                    content, max_context_tokens // 5, file_path
                )

                if len(chunks) > 1:
                    for i, chunk in enumerate(chunks):
                        chunk_header = f"#### Chunk {i + 1}/{len(chunks)}"
                        if llm_optimized:
                            chunk_header += (
                                f" ({chunk['tokens']:,} tokens, {chunk['chunk_info']})"
                            )
                        chunk_header += "\n"

                        result_parts.append(chunk_header)

                        if output_format == "markdown":
                            file_ext = file_path.suffix.lstrip(".")
                            result_parts.append(f"```{file_ext}\n")
                            result_parts.append(chunk["content"])
                            result_parts.append("\n```\n\n")
                        else:
                            result_parts.append(chunk["content"])
                            result_parts.append("\n" + "=" * 50 + "\n\n")
                else:
                    # Single chunk - process normally
                    if output_format == "markdown":
                        file_ext = file_path.suffix.lstrip(".")
                        result_parts.append(f"```{file_ext}\n")
                        result_parts.append(content)
                        result_parts.append("\n```\n\n")
                    else:
                        result_parts.append(content)
                        result_parts.append("\n\n")
            else:
                # No chunking - process normally
                if output_format == "markdown":
                    file_ext = file_path.suffix.lstrip(".")
                    result_parts.append(f"```{file_ext}\n")
                    result_parts.append(content)
                    result_parts.append("\n```\n\n")
                else:
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
            if llm_optimized:
                result_parts.append(f"### 📄 {relative_path}\n")
                result_parts.append(f"⚠️ *Error reading file: {e}*\n\n")
            else:
                result_parts.append(f"### {relative_path}\n")
                result_parts.append(f"*Error reading file: {e}*\n\n")

    # Add summary if LLM optimized
    if llm_optimized and processed_count > 0:
        result_parts.append("\n## 📊 Codebase Summary\n")
        result_parts.append(f"- **Files Processed**: {processed_count:,}\n")
        result_parts.append(f"- **Total Tokens**: {total_tokens:,}\n")

        if language_stats:
            langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
            result_parts.append(
                f"- **Languages**: {', '.join(f'{lang} ({count})' for lang, count in langs[:5])}\n"
            )

        if include_complexity and any(complexity_stats.values()):
            result_parts.append(
                f"- **Complexity Distribution**: "
                f"{complexity_stats.get('Low', 0)} Low, "
                f"{complexity_stats.get('Medium', 0)} Medium, "
                f"{complexity_stats.get('High', 0)} High\n"
            )

        if chunk_strategy != "none":
            result_parts.append(f"- **Chunking Strategy**: {chunk_strategy}\n")

        if file_errors:
            result_parts.append(
                f"- **Errors**: {len(file_errors)} files had processing errors\n"
            )

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
