"""File tree generation tool for FastMCP.

Implements comprehensive error handling per MCP transport best practices:
- Path validation and security
- Permission error handling
- Resource cleanup
- Structured logging to stderr
- Token counting and LLM optimization
- Smart chunking for large codebases
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.tools.file_tree")

# Token estimation patterns for different file types
TOKEN_PATTERNS = {
    "python": r"\b\w+\b|[^\w\s]",
    "javascript": r"\b\w+\b|[^\w\s]",
    "typescript": r"\b\w+\b|[^\w\s]",
    "java": r"\b\w+\b|[^\w\s]",
    "default": r"\b\w+\b|[^\w\s]",
}


def register_file_tree_tool(mcp: FastMCP) -> None:
    """Register the file_tree tool with the FastMCP instance."""

    def _estimate_tokens(content: str, file_type: str = "default") -> int:
        """Estimate token count for file content."""
        try:
            pattern = TOKEN_PATTERNS.get(file_type, TOKEN_PATTERNS["default"])
            tokens = re.findall(pattern, content)
            # Rough GPT-style token estimation: ~0.75 tokens per word
            return int(len(tokens) * 0.75)
        except Exception:
            # Fallback: rough character-based estimation
            return len(content) // 4

    def _detect_file_type(file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
        }
        return ext_map.get(file_path.suffix.lower(), "default")

    def _extract_components(content: str, file_type: str) -> Dict[str, int]:
        """Extract component counts (functions, classes, etc.) from file content."""
        components = {"functions": 0, "classes": 0, "methods": 0, "exports": 0}

        try:
            if file_type == "python":
                components["functions"] = len(
                    re.findall(r"^\s*def\s+\w+", content, re.MULTILINE)
                )
                components["classes"] = len(
                    re.findall(r"^\s*class\s+\w+", content, re.MULTILINE)
                )
                components["methods"] = len(
                    re.findall(r"^\s+def\s+\w+", content, re.MULTILINE)
                )
            elif file_type in ["javascript", "typescript"]:
                components["functions"] = len(
                    re.findall(
                        r"function\s+\w+|const\s+\w+\s*=\s*\(|export\s+function",
                        content,
                    )
                )
                components["classes"] = len(
                    re.findall(r"class\s+\w+|export\s+class", content)
                )
                components["exports"] = len(re.findall(r"export\s+", content))
            elif file_type == "java":
                components["functions"] = len(
                    re.findall(
                        r"(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(",
                        content,
                    )
                )
                components["classes"] = len(
                    re.findall(r"(public|private)?\s*class\s+\w+", content)
                )
        except Exception as e:
            logger.debug(f"Error extracting components: {e}")

        return components

    def _calculate_complexity(content: str, file_type: str) -> str:
        """Calculate file complexity based on various metrics."""
        try:
            lines = len(content.splitlines())
            tokens = _estimate_tokens(content, file_type)

            # Complexity indicators
            cyclomatic_indicators = len(
                re.findall(r"\b(if|for|while|catch|except|switch|case)\b", content)
            )
            nesting_depth = max(
                len(line) - len(line.lstrip())
                for line in content.splitlines()
                if line.strip()
            )

            # Calculate complexity score
            complexity_score = (
                (lines > 100) * 1
                + (tokens > 1000) * 1
                + (cyclomatic_indicators > 10) * 1
                + (nesting_depth > 20) * 1
            )

            if complexity_score >= 3:
                return "high"
            elif complexity_score >= 2:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"

    def _format_file_info(
        file_path: Path,
        show_tokens: bool,
        show_components: bool,
        show_sizes: bool,
        llm_optimized: bool,
    ) -> str:
        """Format file information with optional LLM optimizations."""
        try:
            # Basic info
            size_info = ""
            if show_sizes:
                try:
                    size = file_path.stat().st_size
                    if size < 1024:
                        size_info = f" ({size:,} B)"
                    elif size < 1024 * 1024:
                        size_info = f" ({size / 1024:.1f} KB)"
                    else:
                        size_info = f" ({size / (1024 * 1024):.1f} MB)"
                except Exception:
                    size_info = " (size unknown)"

            # Read file for token and component analysis
            token_info = ""
            component_info = ""

            if show_tokens or show_components:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    file_type = _detect_file_type(file_path)

                    if show_tokens:
                        tokens = _estimate_tokens(content, file_type)
                        lines = len(content.splitlines())
                        complexity = _calculate_complexity(content, file_type)

                        if llm_optimized:
                            token_info = f" 📊 {tokens:,} tokens, {lines} lines, {complexity} complexity"
                        else:
                            token_info = f" ({tokens:,} tokens, {lines} lines)"

                    if show_components:
                        components = _extract_components(content, file_type)
                        if any(components.values()):
                            comp_parts = []
                            if components["functions"]:
                                comp_parts.append(f"{components['functions']} fn")
                            if components["classes"]:
                                comp_parts.append(f"{components['classes']} cls")
                            if components["methods"]:
                                comp_parts.append(f"{components['methods']} methods")
                            if components["exports"]:
                                comp_parts.append(f"{components['exports']} exports")

                            if comp_parts and llm_optimized:
                                component_info = f" 🔧 {', '.join(comp_parts)}"
                            elif comp_parts:
                                component_info = f" [{', '.join(comp_parts)}]"

                except Exception as e:
                    logger.debug(f"Could not analyze file {file_path}: {e}")
                    if show_tokens:
                        token_info = " (analysis failed)"

            # Format filename with emoji if LLM optimized
            filename = file_path.name
            if llm_optimized:
                emoji = "📄" if file_path.is_file() else "📁"
                filename = f"{emoji} {filename}"

            return f"{filename}{size_info}{token_info}{component_info}"

        except Exception as e:
            logger.debug(f"Error formatting file info for {file_path}: {e}")
            return str(file_path.name)

    @mcp.tool()
    async def file_tree(
        path: str = ".",
        max_depth: int = 5,
        show_hidden: bool = False,
        show_sizes: bool = True,
        format: str = "tree",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        show_tokens: bool = True,
        show_components: bool = True,
        llm_optimized: bool = True,
        max_context_tokens: int = 100000,
        complexity_filter: str = "all",
    ) -> Dict[str, Any]:
        """Generate a file tree structure from a directory path.

        Use Tool to generate a file tree structure from a directory path. Use Often When Beginning a Task or Debugging.

        IMPORTANT: When using "." as the path, it will use the MCP server's working directory,
        NOT your agent's current directory. For specific workspaces, always provide the FULL PATH.

        Examples:
        - path="." → Uses MCP server's directory (may not be your workspace)
        - path="D:\\AI_Dev_Hub\\AiResearchAgent" → Uses the specific workspace directory
        - path="/home/user/project" → Uses the specific project directory

        Args:
            path: Directory path to analyze. Use FULL PATHS for specific workspaces (defaults to MCP server's current directory)
            max_depth: Maximum depth to traverse (default: 5)
            show_hidden: Whether to show hidden files (default: False)
            show_sizes: Whether to show file sizes (default: True)
            format: Output format 'tree' or 'json' (default: 'tree')
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            show_tokens: Whether to show token counts
            show_components: Whether to show component counts
            llm_optimized: Whether to optimize for LLM usage
            max_context_tokens: Maximum number of tokens in a context
            complexity_filter: Filter for complexity levels
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
                result_text, metadata = await _build_text_tree_enhanced(
                    target_path,
                    should_include,
                    show_sizes,
                    max_depth,
                    show_tokens,
                    show_components,
                    llm_optimized,
                    max_context_tokens,
                    complexity_filter,
                )
                logger.info(f"Generated enhanced text tree for {target_path}")
                return {
                    "success": True,
                    "result": result_text,
                    "metadata": {
                        "format": "tree",
                        "path": str(target_path),
                        "max_depth": max_depth,
                        **metadata,
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


async def _build_text_tree_enhanced(
    target_path: Path,
    should_include,
    show_sizes: bool,
    max_depth: int,
    show_tokens: bool,
    show_components: bool,
    llm_optimized: bool,
    max_context_tokens: int,
    complexity_filter: str,
) -> Tuple[str, Dict[str, Any]]:
    """Build enhanced text tree structure with LLM optimizations and smart chunking."""

    metadata = {
        "total_tokens": 0,
        "total_files": 0,
        "chunks_created": 0,
        "complexity_distribution": {"low": 0, "medium": 0, "high": 0, "unknown": 0},
        "languages_detected": set(),
        "warnings": [],
    }

    tree_lines = []
    current_tokens = 0

    # Add project header if LLM optimized
    if llm_optimized:
        tree_lines.append(f"# 📂 Project: {target_path.name}")
        tree_lines.append("")
    else:
        tree_lines.append(f"{target_path.name}/")

    def add_tree_items(dir_path: Path, prefix: str = "", depth: int = 0):
        """Recursively add tree items with enhanced formatting and chunking."""
        nonlocal current_tokens, metadata

        if depth >= max_depth:
            return

        try:
            items = [item for item in dir_path.iterdir() if should_include(item)]
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "

                # Enhanced file formatting with LLM optimizations
                if item.is_file():
                    try:
                        # Get enhanced file info
                        file_info = _format_file_info(
                            item,
                            show_tokens,
                            show_components,
                            show_sizes,
                            llm_optimized,
                        )

                        # Track metadata if analyzing tokens
                        if show_tokens:
                            try:
                                content = item.read_text(
                                    encoding="utf-8", errors="ignore"
                                )
                                file_type = _detect_file_type(item)
                                tokens = _estimate_tokens(content, file_type)
                                complexity = _calculate_complexity(content, file_type)

                                # Apply complexity filter
                                if (
                                    complexity_filter != "all"
                                    and complexity != complexity_filter
                                ):
                                    continue

                                current_tokens += tokens
                                metadata["total_tokens"] += tokens
                                metadata["complexity_distribution"][complexity] += 1
                                metadata["languages_detected"].add(file_type)

                                # Smart chunking: warn if approaching context limit
                                if current_tokens > max_context_tokens * 0.8:
                                    metadata["warnings"].append(
                                        f"Approaching token limit at file: {item.name}"
                                    )

                                # Chunk if exceeding limit
                                if current_tokens > max_context_tokens:
                                    metadata["chunks_created"] += 1
                                    tree_lines.append(
                                        f"\n--- CHUNK {metadata['chunks_created']} BREAK ---"
                                    )
                                    tree_lines.append(
                                        f"(Continuing from {item.name}...)\n"
                                    )
                                    current_tokens = tokens

                            except Exception as e:
                                logger.debug(
                                    f"Could not analyze tokens for {item}: {e}"
                                )

                        metadata["total_files"] += 1
                        tree_lines.append(f"{prefix}{current_prefix}{file_info}")

                    except Exception as e:
                        logger.debug(f"Error processing file {item}: {e}")
                        item_name = f"📄 {item.name}" if llm_optimized else item.name
                        tree_lines.append(
                            f"{prefix}{current_prefix}{item_name} (error reading)"
                        )

                else:  # Directory
                    try:
                        # Count directory contents for LLM optimization
                        dir_info = ""
                        if llm_optimized:
                            try:
                                dir_contents = list(item.iterdir())
                                file_count = sum(1 for x in dir_contents if x.is_file())
                                subdir_count = sum(
                                    1 for x in dir_contents if x.is_dir()
                                )
                                if file_count or subdir_count:
                                    dir_info = (
                                        f" ({file_count} files, {subdir_count} dirs)"
                                    )
                            except Exception:
                                dir_info = " (access limited)"

                        dir_name = (
                            f"📁 {item.name}/" if llm_optimized else f"{item.name}/"
                        )
                        tree_lines.append(
                            f"{prefix}{current_prefix}{dir_name}{dir_info}"
                        )

                        # Recurse into directories
                        if depth + 1 < max_depth:
                            try:
                                next_prefix = prefix + ("    " if is_last else "│   ")
                                add_tree_items(item, next_prefix, depth + 1)
                            except Exception as e:
                                logger.debug(f"Error recursing into {item}: {e}")
                                error_prefix = prefix + ("    " if is_last else "│   ")
                                tree_lines.append(
                                    f"{error_prefix}├── [Error: {str(e)}]"
                                )

                    except Exception as e:
                        logger.debug(f"Error processing directory {item}: {e}")
                        dir_name = (
                            f"📁 {item.name}/" if llm_optimized else f"{item.name}/"
                        )
                        tree_lines.append(f"{prefix}{current_prefix}{dir_name} (error)")

        except PermissionError:
            tree_lines.append(f"{prefix}├── [Permission Denied]")
        except Exception as e:
            logger.debug(f"Error processing directory {dir_path}: {e}")
            tree_lines.append(f"{prefix}├── [Error: {str(e)}]")

    add_tree_items(target_path)

    # Add summary if LLM optimized
    if llm_optimized and metadata["total_files"] > 0:
        tree_lines.append("")
        tree_lines.append("## 📊 Project Summary")
        tree_lines.append(f"- **Total Files**: {metadata['total_files']:,}")
        tree_lines.append(f"- **Total Tokens**: {metadata['total_tokens']:,}")

        if metadata["complexity_distribution"]:
            tree_lines.append(
                f"- **Complexity**: {metadata['complexity_distribution']['low']} low, "
                f"{metadata['complexity_distribution']['medium']} medium, "
                f"{metadata['complexity_distribution']['high']} high"
            )

        if metadata["languages_detected"]:
            langs = sorted(metadata["languages_detected"])
            tree_lines.append(f"- **Languages**: {', '.join(langs)}")

        if metadata["chunks_created"] > 0:
            tree_lines.append(
                f"- **Chunks Created**: {metadata['chunks_created']} (due to size)"
            )

        if metadata["warnings"]:
            tree_lines.append(
                f"- **Warnings**: {len(metadata['warnings'])} context limit warnings"
            )

    # Convert metadata languages set to list for JSON serialization
    metadata["languages_detected"] = list(metadata["languages_detected"])

    return "\n".join(tree_lines), metadata
