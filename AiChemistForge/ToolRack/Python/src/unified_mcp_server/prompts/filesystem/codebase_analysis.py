"""Filesystem and codebase analysis prompts for MCP."""

import json
from typing import Any, Dict

from ...server.logging import setup_logging
from ...tools.registry import ToolRegistry

logger = setup_logging(__name__)


async def analyze_project_structure(**kwargs) -> Dict[str, Any]:
    """Generate a prompt for analyzing project structure and organization.

    Args:
        path: Directory path to analyze (defaults to current directory)
        max_depth: Maximum depth for directory tree analysis
        focus_area: Optional focus area (architecture, dependencies, patterns, etc.)
    """
    try:
        path = kwargs.get("path", ".")
        max_depth = kwargs.get("max_depth", 5)
        focus_area = kwargs.get("focus_area", "architecture")

        # Get tool registry and file tree tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        file_tree_tool = tool_registry.get_tool("file_tree")

        if not file_tree_tool:
            return {
                "description": "Analyze project structure",
                "content": "Error: file_tree tool not available",
            }

        # Get directory structure
        result = await file_tree_tool.safe_execute(
            path=path,
            max_depth=max_depth,
            show_hidden=False,
            show_sizes=True,
            format="tree",
        )

        if not result.get("success"):
            return {
                "description": f"Analyze project structure for {path}",
                "content": f"Error retrieving directory structure: {result.get('error')}",
            }

        directory_tree = result.get("result", "")

        # Generate analysis prompt based on focus area
        focus_prompts = {
            "architecture": "Analyze the architectural patterns, module organization, and overall code structure. Identify design patterns and architectural decisions.",
            "dependencies": "Focus on dependency relationships, import patterns, and potential circular dependencies. Analyze how modules interact.",
            "patterns": "Identify code organization patterns, naming conventions, and structural consistency across the codebase.",
            "maintainability": "Evaluate code organization for maintainability, scalability, and ease of navigation.",
            "structure": "Provide a comprehensive structural analysis including file organization, folder hierarchy, and logical groupings.",
        }

        focus_instruction = focus_prompts.get(focus_area, focus_prompts["architecture"])

        prompt_content = f"""# Project Structure Analysis

## Analysis Focus: {focus_area.replace("_", " ").title()}

{focus_instruction}

## Directory Structure

```
{directory_tree}
```

## Analysis Framework

### 1. Structural Overview
- Overall project organization and layout
- Key directories and their purposes
- File naming and organization patterns

### 2. Architectural Analysis
- Module and package structure
- Separation of concerns
- Design patterns evident in structure

### 3. Code Organization Assessment
- Logical grouping of related functionality
- Configuration and documentation placement
- Test and build artifact organization

### 4. Best Practices Evaluation
- Adherence to standard project layouts
- Clarity of structure for new developers
- Maintainability and scalability considerations

### 5. Recommendations
- Structural improvements
- Reorganization suggestions
- Missing components or directories

Please analyze the project structure following this framework and provide detailed insights about the codebase organization.
"""

        return {
            "description": f"Analyze project structure for {path} (focus: {focus_area})",
            "content": prompt_content,
        }

    except Exception as e:
        logger.error(f"Error generating project structure analysis prompt: {e}")
        return {
            "description": "Analyze project structure",
            "content": f"Error generating prompt: {e}",
        }


async def analyze_codebase_content(**kwargs) -> Dict[str, Any]:
    """Generate a prompt for analyzing codebase content and code quality.

    Args:
        path: Directory path to analyze
        include_patterns: File patterns to include in analysis
        max_files: Maximum number of files to analyze
        analysis_type: Type of content analysis (quality, patterns, documentation, etc.)
    """
    try:
        path = kwargs.get("path", ".")
        include_patterns = kwargs.get("include_patterns", ["*.py", "*.md", "*.json"])
        max_files = kwargs.get("max_files", 50)
        analysis_type = kwargs.get("analysis_type", "quality")

        # Get tool registry and codebase ingest tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        codebase_tool = tool_registry.get_tool("codebase_ingest")

        if not codebase_tool:
            return {
                "description": "Analyze codebase content",
                "content": "Error: codebase_ingest tool not available",
            }

        # Get codebase content
        result = await codebase_tool.safe_execute(
            path=path,
            max_files=max_files,
            max_file_size=200000,  # 200KB limit
            output_format="structured",
            include_patterns=include_patterns,
            show_tree=True,
        )

        if not result.get("success"):
            return {
                "description": f"Analyze codebase content for {path}",
                "content": f"Error retrieving codebase content: {result.get('error')}",
            }

        codebase_data = result.get("result", {})

        # Generate analysis prompt based on analysis type
        analysis_prompts = {
            "quality": "Evaluate code quality, best practices adherence, and potential improvements. Focus on code style, structure, and maintainability.",
            "patterns": "Identify common patterns, architectural decisions, and design choices throughout the codebase.",
            "documentation": "Analyze documentation quality, completeness, and clarity. Evaluate comments, docstrings, and README files.",
            "dependencies": "Examine import patterns, external dependencies, and module relationships.",
            "security": "Review code for potential security issues, input validation, and secure coding practices.",
        }

        analysis_instruction = analysis_prompts.get(
            analysis_type, analysis_prompts["quality"]
        )

        prompt_content = f"""# Codebase Content Analysis

## Analysis Type: {analysis_type.replace("_", " ").title()}

{analysis_instruction}

## Codebase Summary

- **Root Path**: `{codebase_data.get("root_path", path)}`
- **Total Files**: {codebase_data.get("total_files", 0)}
- **Text Files**: {codebase_data.get("text_files", 0)}
- **Total Size**: {codebase_data.get("total_size", 0)} bytes

## Directory Structure

```
{codebase_data.get("tree_structure", "Not available")}
```

## Analysis Framework

### 1. Code Quality Assessment
- Adherence to coding standards and best practices
- Code organization and readability
- Error handling and robustness

### 2. Architecture and Design
- Design patterns and architectural decisions
- Module coupling and cohesion
- Separation of concerns

### 3. Documentation Analysis
- Code documentation quality
- API documentation completeness
- User-facing documentation clarity

### 4. Maintainability Review
- Code complexity and readability
- Test coverage and quality
- Configuration management

### 5. Improvement Recommendations
- Code refactoring opportunities
- Documentation enhancements
- Architectural improvements

## Available Files for Analysis

```json
{json.dumps(codebase_data.get("files", [])[:10], indent=2)}
{"..." if len(codebase_data.get("files", [])) > 10 else ""}
```

Please analyze the codebase content following this framework and provide detailed insights about code quality and organization.
"""

        return {
            "description": f"Analyze codebase content for {path} (type: {analysis_type})",
            "content": prompt_content,
        }

    except Exception as e:
        logger.error(f"Error generating codebase content analysis prompt: {e}")
        return {
            "description": "Analyze codebase content",
            "content": f"Error generating prompt: {e}",
        }


async def compare_directory_structures(**kwargs) -> Dict[str, Any]:
    """Generate a prompt for comparing directory structures across multiple paths.

    Args:
        paths: List of directory paths to compare
        comparison_type: Type of comparison (structure, size, content, etc.)
    """
    try:
        paths = kwargs.get("paths", [])
        comparison_type = kwargs.get("comparison_type", "structure")

        if not paths or len(paths) < 2:
            return {
                "description": "Compare directory structures",
                "content": "Error: At least 2 directory paths are required for comparison",
            }

        # Get tool registry and file tree tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        file_tree_tool = tool_registry.get_tool("file_tree")

        if not file_tree_tool:
            return {
                "description": "Compare directory structures",
                "content": "Error: file_tree tool not available",
            }

        # Gather data for each path
        path_data = {}
        for path in paths:
            try:
                result = await file_tree_tool.safe_execute(
                    path=path,
                    max_depth=4,
                    show_hidden=False,
                    show_sizes=True,
                    format="json",
                )

                if result.get("success"):
                    path_data[path] = result.get("result")
                else:
                    path_data[path] = {"error": result.get("error")}

            except Exception as e:
                logger.warning(f"Could not analyze path {path}: {e}")
                path_data[path] = {"error": str(e)}

        prompt_content = f"""# Directory Structure Comparison

## Comparison Type: {comparison_type.replace("_", " ").title()}

## Directories Being Compared
{chr(10).join([f"- **{path}**" for path in paths])}

## Comparison Framework

### 1. Structural Differences
- Organization patterns
- Directory hierarchies
- File distribution

### 2. Size and Content Analysis
- File count comparisons
- Size distributions
- Content type patterns

### 3. Organizational Patterns
- Common structures across directories
- Unique organizational approaches
- Best practices evident

### 4. Recommendations
- Standardization opportunities
- Organizational improvements
- Consistency enhancements

## Directory Data for Analysis

```json
{json.dumps(path_data, indent=2)[:3000]}{"..." if len(json.dumps(path_data)) > 3000 else ""}
```

Please analyze the directory structures and provide comparative insights following the framework above.
"""

        return {
            "description": f"Compare {len(paths)} directory structures",
            "content": prompt_content,
        }

    except Exception as e:
        logger.error(f"Error generating directory comparison prompt: {e}")
        return {
            "description": "Compare directory structures",
            "content": f"Error generating prompt: {e}",
        }


async def register_prompts(registry) -> None:
    """Register all filesystem analysis prompts with the prompt registry."""

    # Register project structure analysis prompt
    registry.register_prompt(
        "analyze_project_structure",
        analyze_project_structure,
        {
            "description": "Generate a prompt for analyzing project structure and organization",
            "category": "filesystem",
            "type": "structure_analysis",
            "parameters": {
                "path": {"type": "string", "optional": True},
                "max_depth": {"type": "integer", "optional": True},
                "focus_area": {"type": "string", "optional": True},
            },
        },
    )

    # Register codebase content analysis prompt
    registry.register_prompt(
        "analyze_codebase_content",
        analyze_codebase_content,
        {
            "description": "Generate a prompt for analyzing codebase content and code quality",
            "category": "filesystem",
            "type": "content_analysis",
            "parameters": {
                "path": {"type": "string", "optional": True},
                "include_patterns": {"type": "array", "optional": True},
                "max_files": {"type": "integer", "optional": True},
                "analysis_type": {"type": "string", "optional": True},
            },
        },
    )

    # Register directory structure comparison prompt
    registry.register_prompt(
        "compare_directory_structures",
        compare_directory_structures,
        {
            "description": "Generate a prompt for comparing directory structures across multiple paths",
            "category": "filesystem",
            "type": "comparison",
            "parameters": {
                "paths": {"type": "array", "required": True},
                "comparison_type": {"type": "string", "optional": True},
            },
        },
    )

    logger.info("Registered filesystem analysis prompts")
