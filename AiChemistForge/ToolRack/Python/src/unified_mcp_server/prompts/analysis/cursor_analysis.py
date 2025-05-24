"""Cursor IDE analysis prompts for MCP."""

from typing import Dict, Any, List, Optional
import json

from ...server.logging import setup_logging
from ...tools.registry import ToolRegistry


logger = setup_logging(__name__)


async def explore_cursor_projects(**kwargs) -> Dict[str, Any]:
    """Generate a prompt for exploring Cursor IDE projects.

    Args:
        project_filter: Optional filter for project names
        include_metadata: Whether to include detailed project metadata
    """
    try:
        project_filter = kwargs.get("project_filter")
        include_metadata = kwargs.get("include_metadata", False)

        # Get tool registry and cursor tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        cursor_tool = tool_registry.get_tool("cursor_db")

        if not cursor_tool:
            return {
                "description": "Explore Cursor IDE projects",
                "content": "Error: cursor_db tool not available"
            }

        # Get project list
        result = await cursor_tool.safe_execute(
            operation="list_projects",
            detailed=include_metadata
        )

        if not result.get("success"):
            return {
                "description": "Explore Cursor IDE projects",
                "content": f"Error retrieving projects: {result.get('error')}"
            }

        projects = result.get("result", {})

        # Filter projects if specified
        if project_filter:
            projects = {
                name: info for name, info in projects.items()
                if project_filter.lower() in name.lower()
            }

        prompt_content = f"""# Cursor IDE Projects Analysis

## Available Projects ({len(projects)} found)

"""

        for project_name, project_info in projects.items():
            prompt_content += f"### {project_name}\n"

            if include_metadata and isinstance(project_info, dict):
                prompt_content += f"- **Database Path**: `{project_info.get('db_path', 'N/A')}`\n"
                prompt_content += f"- **Workspace Directory**: `{project_info.get('workspace_dir', 'N/A')}`\n"
                prompt_content += f"- **Folder URI**: `{project_info.get('folder_uri', 'N/A')}`\n"

            prompt_content += "\n"

        prompt_content += """
## Analysis Suggestions

You can analyze these projects by:

1. **Chat Data Analysis**: Examine AI chat conversations
   - Use operation: `get_chat_data` with project name
   - Look for conversation patterns, frequently asked questions, and user behavior

2. **Composer Analysis**: Review AI composer usage
   - Use operation: `get_composer_ids` to get composer sessions
   - Use operation: `get_composer_data` with composer ID for detailed analysis

3. **Database Exploration**: Query project databases directly
   - Use operation: `query_table` with table name (ItemTable or cursorDiskKV)
   - Search for specific keys or browse all entries

4. **Cross-Project Patterns**: Compare usage across multiple projects
   - Identify common workflows and pain points
   - Analyze tool usage patterns

Choose a project and analysis type to begin exploration.
"""

        return {
            "description": f"Explore Cursor IDE projects{' (filtered)' if project_filter else ''}",
            "content": prompt_content
        }

    except Exception as e:
        logger.error(f"Error generating explore projects prompt: {e}")
        return {
            "description": "Explore Cursor IDE projects",
            "content": f"Error generating prompt: {e}"
        }


async def analyze_chat_data(**kwargs) -> Dict[str, Any]:
    """Generate a prompt for analyzing chat data from a Cursor project.

    Args:
        project_name: Name of the project to analyze
        focus_area: Optional focus area (conversations, patterns, errors, etc.)
    """
    try:
        project_name = kwargs.get("project_name")
        focus_area = kwargs.get("focus_area", "general")

        if not project_name:
            return {
                "description": "Analyze Cursor chat data",
                "content": "Error: project_name parameter is required"
            }

        # Get tool registry and cursor tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        cursor_tool = tool_registry.get_tool("cursor_db")

        if not cursor_tool:
            return {
                "description": "Analyze Cursor chat data",
                "content": "Error: cursor_db tool not available"
            }

        # Get chat data
        result = await cursor_tool.safe_execute(
            operation="get_chat_data",
            project_name=project_name
        )

        if not result.get("success"):
            return {
                "description": f"Analyze chat data for {project_name}",
                "content": f"Error retrieving chat data: {result.get('error')}"
            }

        chat_data = result.get("result", {})

        # Generate analysis prompt based on focus area
        focus_prompts = {
            "general": "Provide a comprehensive analysis of the chat interactions, including common themes, user questions, and AI responses.",
            "conversations": "Focus on the conversation flow and dialogue patterns. Identify the most productive conversations and common question types.",
            "patterns": "Identify usage patterns, peak activity times, and recurring topics or problems.",
            "errors": "Look for error messages, failed requests, and troubleshooting conversations.",
            "productivity": "Analyze how the AI chat is being used to improve productivity and identify successful workflows."
        }

        focus_instruction = focus_prompts.get(focus_area, focus_prompts["general"])

        prompt_content = f"""# Chat Data Analysis for Project: {project_name}

## Analysis Focus: {focus_area.title()}

{focus_instruction}

## Available Chat Data

```json
{json.dumps(chat_data, indent=2)[:2000]}{"..." if len(json.dumps(chat_data)) > 2000 else ""}
```

## Analysis Framework

### 1. Data Overview
- Total number of conversations
- Date range of interactions
- User activity patterns

### 2. Content Analysis
- Most common topics discussed
- Types of questions asked
- AI response effectiveness

### 3. Pattern Recognition
- Conversation length patterns
- Time-based usage patterns
- Recurring themes or issues

### 4. Insights and Recommendations
- How is the AI chat being utilized?
- What are the most successful interaction patterns?
- Areas for improvement in AI assistance

### 5. Actionable Findings
- Workflow optimizations
- Common pain points to address
- Training or documentation needs

Please analyze the chat data following this framework and provide detailed insights.
"""

        return {
            "description": f"Analyze chat data for {project_name} (focus: {focus_area})",
            "content": prompt_content
        }

    except Exception as e:
        logger.error(f"Error generating chat analysis prompt: {e}")
        return {
            "description": "Analyze Cursor chat data",
            "content": f"Error generating prompt: {e}"
        }


async def compare_project_usage(**kwargs) -> Dict[str, Any]:
    """Generate a prompt for comparing usage patterns across multiple Cursor projects.

    Args:
        project_names: List of project names to compare
        analysis_type: Type of comparison (chat_activity, composer_usage, general)
    """
    try:
        project_names = kwargs.get("project_names", [])
        analysis_type = kwargs.get("analysis_type", "general")

        if not project_names or len(project_names) < 2:
            return {
                "description": "Compare project usage patterns",
                "content": "Error: At least 2 project names are required for comparison"
            }

        # Get tool registry and cursor tool
        tool_registry = ToolRegistry()
        await tool_registry.initialize_tools()
        cursor_tool = tool_registry.get_tool("cursor_db")

        if not cursor_tool:
            return {
                "description": "Compare project usage patterns",
                "content": "Error: cursor_db tool not available"
            }

        # Gather data for each project
        project_data = {}
        for project_name in project_names:
            try:
                # Get basic project info
                project_result = await cursor_tool.safe_execute(
                    operation="list_projects",
                    detailed=True
                )

                # Get chat data
                chat_result = await cursor_tool.safe_execute(
                    operation="get_chat_data",
                    project_name=project_name
                )

                # Get composer data
                composer_result = await cursor_tool.safe_execute(
                    operation="get_composer_ids",
                    project_name=project_name
                )

                project_data[project_name] = {
                    "project_info": project_result.get("result", {}).get(project_name, {}),
                    "chat_data": chat_result.get("result") if chat_result.get("success") else None,
                    "composer_data": composer_result.get("result") if composer_result.get("success") else None
                }

            except Exception as e:
                logger.warning(f"Could not gather data for project {project_name}: {e}")
                project_data[project_name] = {"error": str(e)}

        prompt_content = f"""# Cross-Project Usage Analysis

## Comparison Type: {analysis_type.replace('_', ' ').title()}

## Projects Being Compared
{chr(10).join([f"- **{name}**" for name in project_names])}

## Project Data Summary

"""

        for project_name, data in project_data.items():
            prompt_content += f"### {project_name}\n"

            if "error" in data:
                prompt_content += f"❌ Error: {data['error']}\n\n"
                continue

            # Basic project info
            project_info = data.get("project_info", {})
            prompt_content += f"- **Database Path**: `{project_info.get('db_path', 'N/A')}`\n"

            # Chat data summary
            chat_data = data.get("chat_data")
            if chat_data:
                prompt_content += "- **Chat Data**: Available ✅\n"
            else:
                prompt_content += "- **Chat Data**: Not available ❌\n"

            # Composer data summary
            composer_data = data.get("composer_data")
            if composer_data and isinstance(composer_data, dict):
                composer_count = len(composer_data.get("composer_ids", []))
                prompt_content += f"- **Composer Sessions**: {composer_count}\n"
            else:
                prompt_content += "- **Composer Sessions**: Not available ❌\n"

            prompt_content += "\n"

        prompt_content += f"""
## Analysis Framework for {analysis_type.replace('_', ' ').title()}

### 1. Comparative Metrics
- Usage frequency and patterns
- Feature adoption rates
- Activity timelines

### 2. Usage Patterns
- How is each project utilizing Cursor's AI features?
- What are the different workflow patterns?
- Which projects show higher engagement?

### 3. Feature Utilization
- Chat vs Composer usage preferences
- Types of interactions in each project
- Effectiveness of AI assistance

### 4. Insights and Patterns
- Common workflows across projects
- Project-specific needs and patterns
- Best practices that could be shared

### 5. Recommendations
- Optimization opportunities for each project
- Features that could benefit all projects
- Training or documentation needs

## Available Data for Analysis

```json
{json.dumps(project_data, indent=2)[:3000]}{"..." if len(json.dumps(project_data)) > 3000 else ""}
```

Please analyze the cross-project data and provide comparative insights following the framework above.
"""

        return {
            "description": f"Compare usage patterns across {len(project_names)} projects",
            "content": prompt_content
        }

    except Exception as e:
        logger.error(f"Error generating comparison prompt: {e}")
        return {
            "description": "Compare project usage patterns",
            "content": f"Error generating prompt: {e}"
        }


async def register_prompts(registry) -> None:
    """Register all cursor analysis prompts with the prompt registry."""

    # Register project exploration prompt
    registry.register_prompt(
        "explore_cursor_projects",
        explore_cursor_projects,
        {
            "description": "Generate a prompt for exploring available Cursor IDE projects",
            "category": "analysis",
            "type": "exploration",
            "parameters": {
                "project_filter": {"type": "string", "optional": True},
                "include_metadata": {"type": "boolean", "optional": True}
            }
        }
    )

    # Register chat data analysis prompt
    registry.register_prompt(
        "analyze_chat_data",
        analyze_chat_data,
        {
            "description": "Generate a prompt for analyzing chat data from a Cursor project",
            "category": "analysis",
            "type": "chat_analysis",
            "parameters": {
                "project_name": {"type": "string", "required": True},
                "focus_area": {"type": "string", "optional": True}
            }
        }
    )

    # Register project comparison prompt
    registry.register_prompt(
        "compare_project_usage",
        compare_project_usage,
        {
            "description": "Generate a prompt for comparing usage patterns across multiple projects",
            "category": "analysis",
            "type": "comparison",
            "parameters": {
                "project_names": {"type": "array", "required": True},
                "analysis_type": {"type": "string", "optional": True}
            }
        }
    )

    logger.info("Registered Cursor analysis prompts")