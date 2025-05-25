"""Analysis prompts for FastMCP.

Enhanced with dynamic tool integration and improved MCP resource referencing.
Following MCP prompt best practices with structured guidance and tool orchestration.
"""

import logging

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.prompts.analysis")


def register_analysis_prompts(mcp: FastMCP) -> None:
    """Register analysis prompts with the FastMCP instance."""

    @mcp.prompt()
    async def analyze_codebase(focus_area: str = "architecture") -> str:
        """Generate prompts for codebase analysis with specific focus areas.

        Args:
            focus_area: The aspect to focus on (architecture, performance, security, maintainability)
        """
        logger.debug(
            f"Generating codebase analysis prompt for focus_area: {focus_area}"
        )

        base_prompt = """
# Codebase Analysis Assistant

I'll help you analyze your codebase systematically using our integrated MCP tools and resources.

## Step 1: Gather Project Information
First, let's understand your project structure using our available tools:
- Use `file_tree` tool to see the overall organization with configurable depth
- Use `codebase_ingest` tool to get detailed file contents with smart filtering
- Check `filesystem://project-summary` resource for quick overview
- Check `filesystem://current-tree` resource for immediate directory structure

## Step 2: Pre-Analysis Planning
Use our reasoning tools to plan the analysis:
- `sequential_think` with the analysis task to break it down systematically
- `decompose_problem` if the codebase is complex and needs structured analysis
- `solve_with_tools` to plan the optimal tool usage sequence for this specific analysis

## Step 3: Focused Analysis
"""

        # Enhanced focus area strategies with tool integration
        focus_strategies = {
            "architecture": """
            ### Architecture Analysis Focus:
            - **Component Structure**: How are major components organized?
            - **Dependencies**: What are the relationships between modules?
            - **Design Patterns**: What patterns are being used?
            - **Modularity**: How well separated are concerns?
            - **Scalability**: How well does the structure support growth?

            ### Key Questions to Explore:
            1. What is the overall architectural pattern (MVC, microservices, etc.)?
            2. How are dependencies managed and what's the dependency flow?
            3. Are there any circular dependencies or tight coupling issues?
            4. How are cross-cutting concerns (logging, security, etc.) handled?
            5. What would be the impact of major changes to core components?

            ### Recommended Tool Sequence:
            - `analyze_dependencies` - Map component relationships systematically
            - `file_tree` with deep scanning for dependency analysis
            - `codebase_ingest` targeting import statements and class definitions
            """,
            "performance": """
            ### Performance Analysis Focus:
            - **Algorithms**: Are efficient algorithms being used?
            - **Data Structures**: Are appropriate data structures chosen?
            - **I/O Operations**: How are file and network operations handled?
            - **Memory Usage**: Are there potential memory leaks or excessive usage?
            - **Bottlenecks**: Where might performance bottlenecks occur?

            ### Key Questions to Explore:
            1. Where are the computationally expensive operations?
            2. How is data being processed and transformed?
            3. Are there opportunities for caching or memoization?
            4. How are concurrent operations handled?
            5. What are the time and space complexity characteristics?

            ### Recommended Tool Sequence:
            - `codebase_ingest` with pattern filtering for loops and algorithms
            - `sequential_think` for systematic performance review methodology
            - `reflect_on_solution` for performance impact assessment
            """,
            "security": """
            ### Security Analysis Focus:
            - **Input Validation**: How is user input sanitized and validated?
            - **Authentication**: How are users authenticated and authorized?
            - **Data Protection**: How is sensitive data protected?
            - **Error Handling**: Do error messages leak sensitive information?
            - **Dependencies**: Are third-party libraries secure and up-to-date?

            ### Key Questions to Explore:
            1. How are secrets and credentials managed?
            2. What input validation mechanisms are in place?
            3. How is data encrypted in transit and at rest?
            4. Are there any potential injection vulnerabilities?
            5. How are security updates and patches managed?

            ### Recommended Tool Sequence:
            - `codebase_ingest` filtering for authentication and validation code
            - `file_tree` to identify configuration and credential files
            - `sequential_think` for systematic security review process
            """,
            "maintainability": """
            ### Maintainability Analysis Focus:
            - **Code Quality**: How readable and well-documented is the code?
            - **Testing**: What is the test coverage and quality?
            - **Documentation**: How well is the system documented?
            - **Code Duplication**: Are there repeated patterns that could be refactored?
            - **Complexity**: How complex are individual functions and classes?

            ### Key Questions to Explore:
            1. How consistent is the coding style and conventions?
            2. What is the test coverage and are tests meaningful?
            3. How easy would it be for a new developer to understand the code?
            4. Are there areas with high cyclomatic complexity?
            5. How well are business requirements reflected in the code structure?

            ### Recommended Tool Sequence:
            - `codebase_ingest` to analyze documentation and comments
            - `file_tree` to identify test files and documentation structure
            - `decompose_problem` for complex refactoring planning
            """,
        }

        # Get the appropriate focus strategy
        focus_prompt = focus_strategies.get(
            focus_area,
            """
            ### General Analysis Focus:
            - **Overall Structure**: How is the codebase organized?
            - **Code Quality**: What is the general quality level?
            - **Best Practices**: Are industry best practices being followed?
            - **Potential Issues**: What problems might exist?
            - **Improvement Opportunities**: Where could things be better?

            ### Key Questions to Explore:
            1. What is the overall health of the codebase?
            2. Are there any obvious red flags or concerns?
            3. How well does the code follow established conventions?
            4. What would be the priority areas for improvement?
            5. How does this compare to similar projects or industry standards?

            ### Recommended Tool Sequence:
            - `sequential_think` for systematic general review
            - `file_tree` for overall structure assessment
            - `codebase_ingest` for representative code sampling
            """,
        )

        conclusion = """

        ## Step 4: Advanced Analysis Tools
        Consider using these reasoning tools for deeper insights:
        - `analyze_dependencies` to understand component relationships and identify coupling issues
        - `solve_with_tools` to create a structured analysis plan using our available tools
        - `reflect_on_solution` to evaluate findings and generate actionable recommendations

        ## Step 5: Generate Comprehensive Recommendations
        Based on your analysis, provide:
        - **Specific actionable recommendations** with clear implementation steps
        - **Priority levels** for different improvements (Critical/High/Medium/Low)
        - **Potential risks** and mitigation strategies for proposed changes
        - **Implementation approaches** with estimated effort and dependencies
        - **Success metrics** to measure improvement progress

        Would you like me to start the analysis with any specific aspect or tool sequence?
        """

        full_prompt = base_prompt + focus_prompt + conclusion
        logger.info(f"Generated comprehensive {focus_area} analysis prompt")
        return full_prompt

    @mcp.prompt()
    async def explore_cursor_projects(project_filter: str = "") -> str:
        """Generate prompts for exploring Cursor IDE project data.

        Args:
            project_filter: Optional filter for specific project patterns
        """
        logger.debug(
            f"Generating Cursor project exploration prompt with filter: {project_filter}"
        )

        filter_text = f" matching '{project_filter}'" if project_filter else ""

        return f"""
# Cursor Project Explorer

Let's explore your Cursor IDE projects{filter_text} systematically using our integrated MCP tools:

## Step 1: Discover Available Projects
Start by getting an overview using our resources and tools:
- Check the `cursor://projects` resource for a quick project list
- Use `query_cursor_database` with operation "list_projects" for detailed project info
- Use `sequential_think` to plan your exploration approach based on your goals

## Step 2: Deep Project Analysis
For projects of interest, use our comprehensive toolset:
- **Chat History**: `query_cursor_database` with operation "get_chat_data"
- **Composer Sessions**: `query_cursor_database` with operation "get_composer_ids"
- **Detailed Interactions**: Use composer IDs to get specific session data
- **Project Structure**: `file_tree` tool for any accessible project directories
- **Reasoning Analysis**: `analyze_dependencies` to understand project relationships

## Step 3: Systematic Analysis Opportunities
Apply our reasoning tools for deeper insights:
- **Pattern Analysis**: Use `decompose_problem` to break down coding pattern analysis
- **Learning Insights**: Use `sequential_think` to systematically review interaction patterns
- **Productivity Trends**: Use `reflect_on_solution` to evaluate productivity insights
- **Project Comparison**: Use `solve_with_tools` to plan comparative analysis

## Step 4: Advanced Exploration Workflow
Use our integrated tool ecosystem:
1. Start with `cursor://projects` resource to get project overview
2. Use `sequential_think` to plan exploration based on your specific interests
3. Apply `query_cursor_database` systematically for data gathering
4. Use `analyze_dependencies` if exploring project relationships
5. Apply `decompose_problem` for complex analysis questions
6. Use `reflect_on_solution` to synthesize insights and learnings

## Suggested Exploration Questions:
1. What are your most active projects and what patterns make them successful?
2. What types of problems do you solve most frequently across different domains?
3. How do your AI interactions evolve and improve over time?
4. What coding patterns and practices appear most often in your successful projects?
5. Are there unexplored projects that might contain valuable insights or techniques?

## Privacy and Security Note:
This exploration respects your privacy - all analysis happens locally on your machine.
No data is sent externally, and you control what information to examine.
Use our MCP tools to maintain data locality while gaining powerful insights.

Ready to start exploring? Choose a specific project focus or let me guide you through the systematic exploration process!
"""

    @mcp.prompt()
    async def guided_problem_solving(problem: str, domain: str = "general") -> str:
        """Generate prompts for guided problem-solving workflows.

        Args:
            problem: The problem to address
            domain: Problem domain (technical, analytical, creative, business, research)
        """
        logger.debug(f"Generating guided problem solving prompt for domain: {domain}")

        return f"""
# Guided Problem Solving for: {problem}

Let's approach this problem systematically using our comprehensive MCP toolkit:

## Step 1: Problem Understanding and Strategic Planning
Use our reasoning tools to build a solid foundation:
- **Initial Analysis**: `sequential_think` with the problem to break it down step by step
- **Complexity Assessment**: `decompose_problem` if it's complex and needs structured breakdown
- **Tool Planning**: `solve_with_tools` to identify optimal tool sequences for this problem type
- **Domain Context**: Consider the {domain} domain characteristics for approach selection

## Step 2: Information Gathering and Context Building
Leverage our data gathering tools based on problem type:

### For Code/Technical Problems:
- **Project Overview**: `filesystem://project-summary` and `filesystem://current-tree` resources
- **Detailed Analysis**: `file_tree` tool for structure exploration
- **Code Investigation**: `codebase_ingest` tool for targeted code analysis
- **Dependency Mapping**: `analyze_dependencies` for relationship understanding

### For Data/Research Problems:
- **Cursor Integration**: `cursor://projects` resource and `query_cursor_database` tool
- **Historical Context**: Previous project patterns and solutions
- **Systematic Investigation**: `sequential_think` for research methodology

### For General Problems:
- **Structured Approach**: `decompose_problem` to break into manageable parts
- **Resource Planning**: `solve_with_tools` for optimal approach planning

## Step 3: Analysis and Solution Development
Apply systematic thinking with our reasoning tools:
- **Systematic Analysis**: Use `sequential_think` with {domain}-specific approach
- **Component Analysis**: Use `analyze_dependencies` if multiple factors are involved
- **Solution Architecture**: Use `decompose_problem` for complex solution design
- **Tool Integration**: Use `solve_with_tools` to orchestrate multiple approaches

## Step 4: Validation and Refinement
Before implementing, use our reflection capabilities:
- **Solution Review**: `reflect_on_solution` to evaluate proposed approaches
- **Risk Assessment**: Consider edge cases and potential issues systematically
- **Implementation Planning**: Use reasoning tools to plan execution steps
- **Success Criteria**: Define measurable outcomes and validation approaches

## Domain-Specific Considerations for {domain}:
"""

        # Add domain-specific guidance
        domain_guidance = {
            "technical": [
                "Focus on code quality, performance, and maintainability",
                "Consider scalability and security implications",
                "Use `codebase_ingest` and `analyze_dependencies` heavily",
                "Validate solutions against technical best practices",
            ],
            "analytical": [
                "Emphasize data-driven decision making",
                "Use systematic breakdown and dependency analysis",
                "Focus on measurable outcomes and validation",
                "Consider multiple hypothesis and validation approaches",
            ],
            "creative": [
                "Balance structure with innovative thinking",
                "Use decomposition to explore solution space systematically",
                "Consider multiple perspectives and approaches",
                "Use reflection to refine and improve creative solutions",
            ],
            "business": [
                "Focus on stakeholder needs and business value",
                "Consider resource constraints and timelines",
                "Use systematic analysis for risk assessment",
                "Validate solutions against business objectives",
            ],
            "research": [
                "Emphasize thorough investigation and documentation",
                "Use systematic methodology for knowledge gathering",
                "Consider existing work and build upon previous insights",
                "Use reflection tools for methodology validation",
            ],
            "general": [
                "Apply systematic thinking across all aspects",
                "Use appropriate tools based on problem characteristics",
                "Balance thorough analysis with practical constraints",
                "Adapt approach based on emerging insights",
            ],
        }

        guidance = domain_guidance.get(domain, domain_guidance["general"])
        guidance_text = "\n".join(f"- {item}" for item in guidance)

        final_section = f"""
{guidance_text}

## Problem-Specific Analysis for: "{problem}"
Consider these key aspects:
- **Core Requirements**: What are the essential constraints and success criteria?
- **Stakeholder Impact**: Who is affected and what are their needs?
- **Resource Availability**: What tools, time, and resources are available?
- **Risk Factors**: What could go wrong and how can we mitigate risks?
- **Success Metrics**: How will we know when the problem is solved effectively?

## Recommended Tool Sequence:
1. **Planning Phase**: Start with `sequential_think` for systematic problem breakdown
2. **Analysis Phase**: Use `solve_with_tools` to plan optimal tool usage for your specific case
3. **Investigation Phase**: Apply domain-appropriate data gathering tools
4. **Solution Phase**: Use `decompose_problem` for complex solution architecture
5. **Validation Phase**: Apply `reflect_on_solution` for thorough solution evaluation

## Integration Benefits:
- **Systematic Approach**: Our reasoning tools ensure no critical aspects are missed
- **Tool Orchestration**: Optimal sequencing of analysis and investigation tools
- **Quality Assurance**: Built-in reflection and validation throughout the process
- **Scalable Methodology**: Approach works for simple to highly complex problems

Ready to begin the systematic problem-solving process? I recommend starting with `sequential_think` to establish a clear analytical framework, then proceeding with `solve_with_tools` to plan your specific approach.
"""

        logger.info(
            f"Generated comprehensive problem solving prompt for {domain} domain"
        )
        return final_section

    @mcp.prompt()
    async def mcp_tool_orchestration(
        task: str, available_tools: str = "auto-detect"
    ) -> str:
        """Generate prompts for optimal MCP tool orchestration and workflow planning.

        Args:
            task: The task or workflow to optimize
            available_tools: Comma-separated list of tools, or 'auto-detect' to use all available
        """
        logger.debug(f"Generating tool orchestration prompt for task: {task}")

        return f"""
# MCP Tool Orchestration for: {task}

Let's design an optimal workflow using our complete MCP toolkit systematically:

## Step 1: Workflow Analysis and Planning
Start with systematic planning using our reasoning tools:
- **Task Breakdown**: Use `sequential_think` to analyze the task requirements systematically
- **Complexity Assessment**: Use `decompose_problem` to identify sub-tasks and dependencies
- **Tool Planning**: Use `solve_with_tools` to design optimal tool sequences

## Step 2: Available Tool Assessment
Our integrated MCP server provides these tool categories:

### Reasoning and Planning Tools:
- `sequential_think` - Systematic problem breakdown and step-by-step analysis
- `decompose_problem` - Complex problem decomposition with dependency analysis
- `analyze_dependencies` - Component relationship mapping and critical path analysis
- `solve_with_tools` - Tool orchestration planning and workflow optimization
- `reflect_on_solution` - Solution validation and improvement recommendations

### Filesystem and Code Analysis Tools:
- `file_tree` - Directory structure analysis with configurable depth and filtering
- `codebase_ingest` - Intelligent code analysis with pattern matching and summarization
- Resources: `filesystem://project-summary`, `filesystem://current-tree`

### Database and IDE Integration Tools:
- `query_cursor_database` - Cursor IDE data access for projects, chats, and composer sessions
- Resources: `cursor://projects` for project discovery and analysis

### System Extension Tools:
- `manage_plugins` - Plugin management for extending MCP server capabilities

## Step 3: Workflow Design Patterns
Based on task type, consider these proven patterns:

### For Code Analysis Tasks:
```
1. filesystem://project-summary → Overview
2. sequential_think → Plan analysis approach
3. file_tree → Structure understanding
4. codebase_ingest → Detailed code analysis
5. analyze_dependencies → Relationship mapping
6. reflect_on_solution → Validate findings
```

### For Problem Solving Tasks:
```
1. sequential_think → Problem breakdown
2. decompose_problem → Sub-task identification
3. solve_with_tools → Tool sequence planning
4. [Apply domain tools] → Execute analysis
5. reflect_on_solution → Solution validation
```

### For Research and Investigation Tasks:
```
1. cursor://projects → Available data discovery
2. sequential_think → Research methodology planning
3. query_cursor_database → Data collection
4. analyze_dependencies → Pattern analysis
5. reflect_on_solution → Insight synthesis
```

## Step 4: Optimization Strategies
Design your workflow for maximum effectiveness:

### Parallel Processing Opportunities:
- Combine `filesystem://project-summary` with `cursor://projects` for comprehensive context
- Use `file_tree` alongside `sequential_think` for simultaneous structure and strategy analysis
- Apply `analyze_dependencies` in parallel with detailed code analysis

### Sequential Dependencies:
- Always use `sequential_think` or `decompose_problem` before complex tool orchestration
- Apply `solve_with_tools` after understanding requirements but before execution
- Use `reflect_on_solution` as final validation after main analysis is complete

### Feedback Loops:
- Use `reflect_on_solution` outputs to inform subsequent `sequential_think` iterations
- Apply insights from `analyze_dependencies` to refine `decompose_problem` strategies
- Use `solve_with_tools` to continuously optimize workflow based on intermediate results

## Step 5: Task-Specific Orchestration for: "{task}"

### Recommended Workflow:
1. **Planning**: Start with `sequential_think` to understand task requirements
2. **Strategy**: Use `solve_with_tools` to design optimal approach for this specific task
3. **Context**: Gather relevant information using appropriate data tools
4. **Analysis**: Apply analytical tools based on task domain and requirements
5. **Integration**: Use `analyze_dependencies` if multiple components are involved
6. **Validation**: Apply `reflect_on_solution` to ensure quality and completeness

### Success Metrics:
- **Efficiency**: Minimal tool calls while maximizing information gathering
- **Completeness**: All task aspects addressed systematically
- **Quality**: Validated results with clear reasoning and evidence
- **Reusability**: Approach can be adapted for similar future tasks

## Advanced Integration Techniques:
- **Chained Analysis**: Use output from one tool as input to the next in the sequence
- **Parallel Context Building**: Gather different types of context simultaneously
- **Iterative Refinement**: Use reflection to improve analysis quality progressively
- **Adaptive Sequencing**: Adjust tool sequence based on intermediate findings

Ready to design your optimal workflow? Start with `sequential_think` to analyze your specific task requirements, then use `solve_with_tools` to create a customized orchestration plan.
"""

        logger.info("Generated comprehensive tool orchestration prompt for task")
        return f"""# MCP Tool Orchestration for: {task}

Let's design an optimal workflow using our complete MCP toolkit systematically:

## Step 1: Workflow Analysis and Planning
Start with systematic planning using our reasoning tools:
- **Task Breakdown**: Use `sequential_think` to analyze the task requirements systematically
- **Complexity Assessment**: Use `decompose_problem` to identify sub-tasks and dependencies
- **Tool Planning**: Use `solve_with_tools` to design optimal tool sequences

## Step 2: Available Tool Assessment
Tool categories: Reasoning, Filesystem/Code Analysis, Database/IDE Integration, System Extension

## Step 3: Workflow Design Patterns
Consider proven patterns based on task type (Code Analysis, Problem Solving, Research/Investigation)

## Step 4: Optimization Strategies
Design for parallel processing, sequential dependencies, and feedback loops

## Step 5: Task-Specific Orchestration
Apply systematic workflow: Planning → Strategy → Context → Analysis → Integration → Validation

Ready to design your optimal workflow? Start with `sequential_think` to analyze your specific task requirements, then use `solve_with_tools` to create a customized orchestration plan.
"""
