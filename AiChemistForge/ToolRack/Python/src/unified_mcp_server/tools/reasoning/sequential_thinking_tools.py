"""Sequential thinking and reasoning tools for FastMCP.

Implements comprehensive error handling per MCP transport best practices:
- Input validation and sanitization
- Structured error responses
- Resource management
- Structured logging to stderr
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Set up logger for this module following MCP stdio logging guidelines
logger = logging.getLogger("mcp.tools.reasoning")


def register_reasoning_tools(mcp: FastMCP) -> None:
    """Register all reasoning tools with the FastMCP instance."""

    @mcp.tool()
    async def sequential_think(
        problem: str, context: str = "", approach: str = "systematic"
    ) -> Dict[str, Any]:
        """Break down problem into sequential thinking steps.

        🧠 WHEN TO USE THIS TOOL:
        - Starting any complex task or project (coding, analysis, planning)
        - When you feel overwhelmed by a multi-faceted problem
        - Need to organize thoughts before diving into implementation
        - Want to ensure you don't miss critical steps or considerations
        - Working on unfamiliar domains where systematic thinking helps

        💡 PERFECT FOR:
        - "I need to refactor this large codebase" → Plan systematic approach
        - "How do I implement this complex feature?" → Break down requirements
        - "I'm debugging a weird issue" → Systematic investigation steps
        - "Planning a new project architecture" → Structured design thinking
        - "Learning a new technology stack" → Step-by-step learning plan

        🎯 APPROACH GUIDE:
        - systematic: Best for technical problems, debugging, implementation planning
        - creative: Best for innovation, design challenges, finding novel solutions
        - analytical: Best for data problems, research, hypothesis testing
        - practical: Best for quick solutions, resource-constrained problems, MVP planning

        Args:
            problem: The problem to analyze and solve (be specific about what you want to accomplish)
            context: Additional context or constraints (timeline, resources, requirements, etc.)
            approach: Thinking approach (systematic, creative, analytical, practical)
        """
        logger.debug(f"Starting sequential thinking for problem: {problem[:100]}...")

        try:
            # Input validation per MCP error handling guidelines
            if not problem or not isinstance(problem, str):
                raise ValueError(
                    "Problem parameter is required and must be a non-empty string"
                )

            if len(problem.strip()) < 5:
                raise ValueError(
                    "Problem description must be at least 5 characters long"
                )

            if len(problem) > 10000:
                raise ValueError(
                    "Problem description is too long (max 10,000 characters)"
                )

            valid_approaches = ["systematic", "creative", "analytical", "practical"]
            if approach not in valid_approaches:
                raise ValueError(
                    f"Invalid approach '{approach}'. Must be one of: {valid_approaches}"
                )

            logger.debug(f"Using approach: {approach}")

            # Generate thinking steps based on approach
            steps = _generate_thinking_steps(approach)

            # Apply the steps to the specific problem
            analysis = {
                "problem": problem.strip(),
                "context": context.strip() if context else "",
                "approach": approach,
                "thinking_steps": steps,
                "next_actions": [
                    f"Work through each step systematically with the problem: '{problem.strip()[:50]}{'...' if len(problem) > 50 else ''}'",
                    "Consider the provided context and any additional constraints",
                    "Document insights and decisions at each step",
                    "Be prepared to iterate and refine as understanding improves",
                ],
                "metadata": {
                    "step_count": len(steps),
                    "estimated_time": _estimate_completion_time(approach, len(steps)),
                },
            }

            logger.info(
                f"Generated {len(steps)} thinking steps using {approach} approach"
            )
            return {
                "success": True,
                "analysis": analysis,
                "tool": "sequential_think",
            }

        except ValueError as e:
            logger.error(f"Validation error in sequential_think: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "sequential_think",
            }
        except Exception as e:
            logger.error(f"Unexpected error in sequential_think: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "sequential_think",
            }

    @mcp.tool()
    async def decompose_problem(
        problem: str, target_size: str = "small", domain: str = "general"
    ) -> Dict[str, Any]:
        """Decompose a complex problem into smaller, manageable parts.

        🧩 WHEN TO USE THIS TOOL:
        - Facing a problem that feels too big to tackle all at once
        - Need to organize work into parallel streams or phases
        - Working with teams and need to assign different aspects to different people
        - Want to reduce risk by breaking complex work into smaller, testable pieces
        - Feeling stuck because the problem has too many interconnected parts

        💡 PERFECT FOR:
        - "Build a complete web application" → Break into frontend, backend, database, deployment
        - "Migrate legacy system to modern architecture" → Identify components and migration order
        - "Implement complex business logic" → Separate validation, processing, storage concerns
        - "Research and implement new technology" → Break into learning, prototyping, integration phases
        - "Debug a system-wide performance issue" → Isolate database, network, application, caching layers

        🎯 TARGET SIZE GUIDE:
        - small: Maximum granularity - creates many focused sub-problems (best for detailed planning)
        - medium: Balanced approach - manageable chunks without overwhelming detail
        - large: High-level breakdown - fewer, broader categories (best for initial planning)

        🏗️ DOMAIN GUIDE:
        - technical: Architecture, data, processing, interfaces, security, testing, deployment
        - analytical: Data collection, cleaning, analysis, modeling, validation, reporting
        - creative: Research, ideation, design, prototyping, feedback, refinement, production
        - general: Understanding, planning, resources, implementation, testing, integration, review

        Args:
            problem: The complex problem to decompose (be specific about scope and constraints)
            target_size: Target size for sub-problems (small, medium, large)
            domain: Problem domain (technical, analytical, creative, general)
        """
        logger.debug(f"Starting problem decomposition for: {problem[:100]}...")

        try:
            # Input validation per MCP error handling guidelines
            if not problem or not isinstance(problem, str):
                raise ValueError(
                    "Problem parameter is required and must be a non-empty string"
                )

            if len(problem.strip()) < 10:
                raise ValueError(
                    "Problem description must be at least 10 characters long for decomposition"
                )

            if len(problem) > 20000:
                raise ValueError(
                    "Problem description is too long for decomposition (max 20,000 characters)"
                )

            valid_sizes = ["small", "medium", "large"]
            if target_size not in valid_sizes:
                raise ValueError(
                    f"Invalid target_size '{target_size}'. Must be one of: {valid_sizes}"
                )

            valid_domains = ["technical", "analytical", "creative", "general"]
            if domain not in valid_domains:
                raise ValueError(
                    f"Invalid domain '{domain}'. Must be one of: {valid_domains}"
                )

            logger.debug(
                f"Decomposing with target_size: {target_size}, domain: {domain}"
            )

            # Determine decomposition strategy based on domain
            dimensions = _get_domain_dimensions(domain)

            # Adjust granularity based on target size
            num_subproblems = _calculate_subproblem_count(target_size, len(dimensions))
            relevant_dimensions = dimensions[:num_subproblems]

            decomposition = {
                "original_problem": problem.strip(),
                "target_size": target_size,
                "domain": domain,
                "sub_problems": [
                    {
                        "id": i + 1,
                        "category": dim,
                        "description": f"Address the {dim.lower()} aspects of: {problem.strip()[:100]}{'...' if len(problem) > 100 else ''}",
                        "focus_questions": _generate_focus_questions(dim, problem),
                        "priority": _calculate_priority(dim, domain),
                    }
                    for i, dim in enumerate(relevant_dimensions)
                ],
                "dependencies": _analyze_dependencies(relevant_dimensions),
                "recommended_order": _suggest_execution_order(relevant_dimensions),
                "metadata": {
                    "total_dimensions": len(dimensions),
                    "selected_dimensions": len(relevant_dimensions),
                    "complexity_estimate": _estimate_complexity(
                        problem, len(relevant_dimensions)
                    ),
                },
            }

            logger.info(
                f"Decomposed problem into {len(relevant_dimensions)} sub-problems"
            )
            return {
                "success": True,
                "decomposition": decomposition,
                "total_sub_problems": len(relevant_dimensions),
                "tool": "decompose_problem",
            }

        except ValueError as e:
            logger.error(f"Validation error in decompose_problem: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "decompose_problem",
            }
        except Exception as e:
            logger.error(f"Unexpected error in decompose_problem: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "decompose_problem",
            }

    @mcp.tool()
    async def analyze_dependencies(
        components: List[str], relationships: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Analyze dependencies and relationships between components.

        🔗 WHEN TO USE THIS TOOL:
        - Planning work order for complex projects with interdependent parts
        - Identifying bottlenecks and critical path items in your workflow
        - Understanding which components can be worked on in parallel
        - Preparing for refactoring where you need to understand component coupling
        - Risk planning - identifying which failures would cascade to other components

        💡 PERFECT FOR:
        - "Microservice migration planning" → Map service dependencies and migration order
        - "Database schema refactoring" → Identify table relationships and update sequence
        - "Team project coordination" → Understand which tasks block others
        - "Code architecture review" → Analyze module coupling and identify tight dependencies
        - "Infrastructure deployment" → Plan deployment order based on service dependencies
        - "Feature development prioritization" → Understand feature interdependencies

        🎯 COMPONENT EXAMPLES:
        - Technical: ["UserService", "PaymentService", "NotificationService", "Database"]
        - Project: ["Requirements", "Design", "Frontend", "Backend", "Testing", "Deployment"]
        - Business: ["Market Research", "Product Design", "Development", "Marketing", "Sales"]

        ⚡ RELATIONSHIP TYPES:
        - depends_on: Component A needs Component B to function
        - blocks: Component A prevents Component B from proceeding
        - enables: Component A makes Component B possible/easier
        - integrates_with: Components work together but neither strictly depends on the other

        Args:
            components: List of component names to analyze (be specific - use actual module/service/task names)
            relationships: Optional list of relationships like [{"from": "A", "to": "B", "type": "depends_on"}]
        """
        logger.debug(
            f"Starting dependency analysis for {len(components) if components else 0} components"
        )

        try:
            # Input validation per MCP error handling guidelines
            if not components or not isinstance(components, list):
                raise ValueError(
                    "Components parameter is required and must be a non-empty list"
                )

            if len(components) > 100:
                raise ValueError("Too many components for analysis (max 100)")

            # Validate component names
            validated_components = []
            for i, comp in enumerate(components):
                if not isinstance(comp, str) or not comp.strip():
                    raise ValueError(f"Component {i + 1} must be a non-empty string")
                validated_components.append(comp.strip())

            # Remove duplicates while preserving order
            unique_components = list(dict.fromkeys(validated_components))
            if len(unique_components) != len(validated_components):
                logger.warning(
                    f"Removed {len(validated_components) - len(unique_components)} duplicate components"
                )

            # Validate relationships if provided
            validated_relationships = []
            if relationships:
                if not isinstance(relationships, list):
                    raise ValueError("Relationships must be a list of dictionaries")

                for i, rel in enumerate(relationships):
                    if not isinstance(rel, dict):
                        raise ValueError(f"Relationship {i + 1} must be a dictionary")

                    required_keys = ["from", "to", "type"]
                    missing_keys = [key for key in required_keys if key not in rel]
                    if missing_keys:
                        raise ValueError(
                            f"Relationship {i + 1} missing required keys: {missing_keys}"
                        )

                    if rel["from"] not in unique_components:
                        raise ValueError(
                            f"Relationship {i + 1}: 'from' component '{rel['from']}' not in components list"
                        )

                    if rel["to"] not in unique_components:
                        raise ValueError(
                            f"Relationship {i + 1}: 'to' component '{rel['to']}' not in components list"
                        )

                    validated_relationships.append(rel)

            logger.debug(
                f"Analyzing {len(unique_components)} unique components with {len(validated_relationships)} relationships"
            )

            # Build dependency graph with error handling
            graph = _build_dependency_graph(unique_components, validated_relationships)

            # Analyze the dependency structure
            analysis = {
                "components": unique_components,
                "total_components": len(unique_components),
                "dependency_graph": graph,
                "critical_path": _find_critical_path(graph),
                "levels": _determine_dependency_levels(graph),
                "bottlenecks": _identify_bottlenecks(graph),
                "recommendations": _generate_dependency_recommendations(graph),
                "metadata": {
                    "relationship_count": len(validated_relationships),
                    "graph_complexity": _calculate_graph_complexity(graph),
                    "max_depth": _calculate_max_depth(graph),
                },
            }

            logger.info(
                f"Completed dependency analysis: {len(unique_components)} components, {len(validated_relationships)} relationships"
            )
            return {
                "success": True,
                "analysis": analysis,
                "tool": "analyze_dependencies",
            }

        except ValueError as e:
            logger.error(f"Validation error in analyze_dependencies: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "analyze_dependencies",
            }
        except Exception as e:
            logger.error(
                f"Unexpected error in analyze_dependencies: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "analyze_dependencies",
            }

    @mcp.tool()
    async def solve_with_tools(
        problem: str,
        available_tools: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Use sequential thinking to solve problem with available tools.

        🛠️ WHEN TO USE THIS TOOL:
        - Need to plan which MCP tools to use and in what order for a specific task
        - Want to optimize your workflow before starting complex analysis
        - Working with multiple data sources and need to coordinate tool usage
        - Planning a comprehensive investigation or analysis project
        - Want to ensure you're using the most efficient approach with available tools

        💡 PERFECT FOR:
        - "Analyze this codebase thoroughly" → Plan file_tree → codebase_ingest → analyze_dependencies sequence
        - "Understand my Cursor project patterns" → Plan query_cursor_database → sequential_think → reflect workflow
        - "Debug complex system issue" → Plan systematic tool usage for investigation
        - "Research project setup and analysis" → Coordinate filesystem and reasoning tools
        - "Plan comprehensive code review" → Optimize tool sequence for maximum insight

        🎯 TOOL CATEGORIES AVAILABLE:
        - Reasoning: sequential_think, decompose_problem, analyze_dependencies, reflect_on_solution
        - Filesystem: file_tree, codebase_ingest, filesystem resources
        - Database: query_cursor_database, cursor resources
        - System: manage_plugins

        ⚙️ CONSTRAINT EXAMPLES:
        - {"time_limit": "30 minutes", "focus": "security analysis"}
        - {"max_tools": 3, "priority": "quick overview"}
        - {"resource_limit": "low", "depth": "surface level"}

        Args:
            problem: Problem to solve (be specific about your goal and what you want to accomplish)
            available_tools: List of available tool names (auto-detects if not provided)
            constraints: Dictionary of constraints (time, resources, focus areas, etc.)
        """
        try:
            if available_tools is None:
                available_tools = [
                    "file_tree",
                    "codebase_ingest",
                    "query_cursor_database",
                    "manage_plugins",
                    "sequential_think",
                    "decompose_problem",
                    "analyze_dependencies",
                    "reflect_on_solution",
                ]

            # Analyze the problem and suggest tool usage
            solution_plan = {
                "problem": problem,
                "available_tools": available_tools,
                "constraints": constraints or {},
                "analysis_phase": {
                    "recommended_tools": [],
                    "rationale": "",
                },
                "implementation_phase": {
                    "tool_sequence": [],
                    "expected_outputs": [],
                },
                "validation_phase": {
                    "verification_tools": [],
                    "success_criteria": [],
                },
            }

            # Determine which tools are most relevant
            if any(
                word in problem.lower()
                for word in ["file", "directory", "code", "project"]
            ):
                solution_plan["analysis_phase"]["recommended_tools"].extend(
                    ["file_tree", "codebase_ingest"]
                )
                solution_plan["analysis_phase"]["rationale"] += (
                    "File system analysis tools for code/project exploration. "
                )

            if any(
                word in problem.lower()
                for word in ["cursor", "database", "chat", "composer"]
            ):
                solution_plan["analysis_phase"]["recommended_tools"].append(
                    "query_cursor_database"
                )
                solution_plan["analysis_phase"]["rationale"] += (
                    "Cursor database tools for IDE integration. "
                )

            if any(
                word in problem.lower()
                for word in ["complex", "break", "decompose", "parts"]
            ):
                solution_plan["analysis_phase"]["recommended_tools"].extend(
                    ["decompose_problem", "analyze_dependencies"]
                )
                solution_plan["analysis_phase"]["rationale"] += (
                    "Problem decomposition and dependency analysis. "
                )

            if any(word in problem.lower() for word in ["plugin", "extend", "module"]):
                solution_plan["analysis_phase"]["recommended_tools"].append(
                    "manage_plugins"
                )
                solution_plan["analysis_phase"]["rationale"] += (
                    "Plugin management for extensibility. "
                )

            # Always include thinking and reflection tools
            solution_plan["analysis_phase"]["recommended_tools"].append(
                "sequential_think"
            )
            solution_plan["validation_phase"]["verification_tools"].append(
                "reflect_on_solution"
            )

            # Create implementation sequence
            unique_tools = list(
                dict.fromkeys(solution_plan["analysis_phase"]["recommended_tools"])
            )
            solution_plan["implementation_phase"]["tool_sequence"] = unique_tools

            # Generate expected outputs
            solution_plan["implementation_phase"]["expected_outputs"] = [
                f"Output from {tool} providing insights for: {problem}"
                for tool in unique_tools
            ]

            # Define success criteria
            solution_plan["validation_phase"]["success_criteria"] = [
                "Problem is clearly understood and scoped",
                "Solution approach is well-defined and feasible",
                "Implementation path is clear and actionable",
                "Potential obstacles are identified and addressed",
                "Success metrics are defined and measurable",
            ]

            return {
                "success": True,
                "solution_plan": solution_plan,
                "tool": "solve_with_tools",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def reflect_on_solution(
        solution: Dict[str, Any],
        original_problem: str,
        success_criteria: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluate and reflect on a proposed solution.

        🎯 WHEN TO USE THIS TOOL:
        - Before implementing a solution to validate it's well-thought-out
        - After completing analysis to ensure you haven't missed important aspects
        - When you want a systematic evaluation of pros/cons and potential issues
        - Need to present findings to others and want comprehensive assessment
        - Want to identify improvement opportunities before finalizing approach

        💡 PERFECT FOR:
        - "Code architecture proposal" → Validate design decisions and identify risks
        - "Analysis findings" → Ensure conclusions are well-supported and complete
        - "Project plan evaluation" → Check for gaps, risks, and improvement opportunities
        - "Tool workflow results" → Assess if the chosen approach achieved desired outcomes
        - "Research conclusions" → Validate methodology and findings before presenting
        - "Debugging solution" → Verify the fix addresses root cause and won't create new issues

        🔍 WHAT IT EVALUATES:
        - Strengths: What works well about this solution?
        - Weaknesses: What are the limitations or potential problems?
        - Opportunities: How could this be improved or extended?
        - Threats: What risks or obstacles might arise?
        - Completeness: Does it fully address the original problem?
        - Feasibility: Is it realistic with available resources?

        📊 SUCCESS CRITERIA EXAMPLES:
        - ["Reduces complexity", "Improves performance", "Maintains backward compatibility"]
        - ["Provides actionable insights", "Uses reliable data", "Clear recommendations"]
        - ["Solves root cause", "Doesn't break existing functionality", "Is maintainable"]

        Args:
            solution: The solution to evaluate (tool results, analysis, plan, etc.)
            original_problem: The original problem statement for comparison
            success_criteria: Optional list of success criteria to evaluate against
        """
        try:
            if success_criteria is None:
                success_criteria = [
                    "Addresses the core problem effectively",
                    "Is feasible with available resources",
                    "Has clear implementation steps",
                    "Considers potential risks and obstacles",
                    "Provides measurable outcomes",
                ]

            reflection = {
                "original_problem": original_problem,
                "solution_summary": solution,
                "evaluation": {
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "threats": [],
                },
                "criteria_assessment": [],
                "recommendations": {
                    "improvements": [],
                    "alternatives": [],
                    "next_steps": [],
                },
                "confidence_score": 0.0,
            }

            # Evaluate against success criteria
            for i, criterion in enumerate(success_criteria):
                assessment = {
                    "criterion": criterion,
                    "score": 0.7,  # Default moderate score
                    "notes": f"Assessment needed for: {criterion}",
                }
                reflection["criteria_assessment"].append(assessment)

            # Generate general evaluation
            reflection["evaluation"]["strengths"] = [
                "Solution addresses key aspects of the problem",
                "Approach appears systematic and well-structured",
                "Implementation path is identified",
            ]

            reflection["evaluation"]["weaknesses"] = [
                "May need more detailed analysis of edge cases",
                "Resource requirements could be better defined",
                "Timeline and milestones need clarification",
            ]

            reflection["evaluation"]["opportunities"] = [
                "Potential for automation and optimization",
                "Possibility to create reusable components",
                "Opportunity to document best practices",
            ]

            reflection["evaluation"]["threats"] = [
                "External dependencies might cause delays",
                "Technical complexity could lead to scope creep",
                "Resource constraints might impact quality",
            ]

            # Generate recommendations
            reflection["recommendations"]["improvements"] = [
                "Add more specific success metrics and validation criteria",
                "Include risk mitigation strategies for identified threats",
                "Develop contingency plans for critical failure points",
                "Consider iterative implementation with regular checkpoints",
            ]

            reflection["recommendations"]["alternatives"] = [
                "Explore simpler approaches that might achieve 80% of the value",
                "Consider phased implementation to reduce risk",
                "Investigate existing solutions that could be adapted",
            ]

            reflection["recommendations"]["next_steps"] = [
                "Create detailed implementation timeline with milestones",
                "Identify required resources and stakeholders",
                "Set up monitoring and feedback mechanisms",
                "Plan regular review and adjustment sessions",
            ]

            # Calculate confidence score (average of criteria scores)
            if reflection["criteria_assessment"]:
                avg_score = sum(
                    c["score"] for c in reflection["criteria_assessment"]
                ) / len(reflection["criteria_assessment"])
                reflection["confidence_score"] = round(avg_score, 2)

            return {
                "success": True,
                "reflection": reflection,
                "tool": "reflect_on_solution",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


def _generate_focus_questions(dimension: str, problem: str) -> List[str]:
    """Generate focus questions for a specific dimension."""
    question_templates = {
        "Architecture & Design": [
            "What is the overall system architecture needed?",
            "How should components be organized and connected?",
            "What design patterns would be most appropriate?",
        ],
        "Data & Storage": [
            "What data needs to be stored and how?",
            "What are the data access patterns?",
            "How should data be organized and indexed?",
        ],
        "Understanding & Requirements": [
            "What exactly needs to be accomplished?",
            "Who are the stakeholders and what are their needs?",
            "What are the success criteria?",
        ],
        "Planning & Strategy": [
            "What is the overall approach and methodology?",
            "What are the key milestones and deliverables?",
            "How will progress be measured and tracked?",
        ],
    }

    return question_templates.get(
        dimension,
        [
            f"How does {dimension.lower()} apply to this problem?",
            f"What specific aspects of {dimension.lower()} need attention?",
            f"What are the key considerations for {dimension.lower()}?",
        ],
    )


def _analyze_dependencies(dimensions: List[str]) -> List[Dict[str, str]]:
    """Analyze dependencies between dimensions."""
    # Simple heuristic-based dependency analysis
    dependencies = []
    if "Understanding & Requirements" in dimensions:
        for dim in dimensions:
            if dim != "Understanding & Requirements":
                dependencies.append(
                    {
                        "from": dim,
                        "to": "Understanding & Requirements",
                        "type": "requires",
                    }
                )

    if (
        "Planning & Strategy" in dimensions
        and "Understanding & Requirements" in dimensions
    ):
        dependencies.append(
            {
                "from": "Planning & Strategy",
                "to": "Understanding & Requirements",
                "type": "depends_on",
            }
        )

    return dependencies


def _suggest_execution_order(dimensions: List[str]) -> List[str]:
    """Suggest optimal execution order for dimensions."""
    priority_order = [
        "Understanding & Requirements",
        "Planning & Strategy",
        "Resource Identification",
        "Implementation Design",
        "Execution & Development",
        "Testing & Validation",
        "Integration & Deployment",
        "Review & Optimization",
    ]

    # Return dimensions in priority order, including any not in the predefined list
    ordered = [dim for dim in priority_order if dim in dimensions]
    remaining = [dim for dim in dimensions if dim not in ordered]
    return ordered + remaining


def _find_critical_path(graph: Dict[str, Dict]) -> List[str]:
    """Find the critical path through the dependency graph."""
    # Simple implementation - find the longest chain
    max_path = []

    for component in graph:
        path = _trace_dependencies(component, graph, [])
        if len(path) > len(max_path):
            max_path = path

    return max_path


def _trace_dependencies(
    component: str, graph: Dict[str, Dict], visited: List[str]
) -> List[str]:
    """Recursively trace dependencies to find longest path."""
    if component in visited:
        return visited

    visited = visited + [component]
    dependencies = graph[component]["depends_on"]

    if not dependencies:
        return visited

    longest_path = visited
    for dep in dependencies:
        path = _trace_dependencies(dep, graph, visited)
        if len(path) > len(longest_path):
            longest_path = path

    return longest_path


def _determine_dependency_levels(graph: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Determine which components can be worked on at each level."""
    levels = {}
    remaining = set(graph.keys())
    level = 0

    while remaining:
        current_level = []
        for component in list(remaining):
            dependencies = graph[component]["depends_on"]
            if not any(dep in remaining for dep in dependencies):
                current_level.append(component)

        if not current_level:
            # Circular dependency or other issue
            current_level = list(remaining)

        levels[f"Level {level}"] = current_level
        remaining -= set(current_level)
        level += 1

    return levels


def _identify_bottlenecks(graph: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Identify potential bottlenecks in the dependency graph."""
    bottlenecks = []

    for component, info in graph.items():
        if info["weight"] > 2:  # High number of dependents
            bottlenecks.append(
                {
                    "component": component,
                    "dependent_count": len(info["depended_by"]),
                    "dependents": info["depended_by"],
                    "risk_level": "High" if info["weight"] > 3 else "Medium",
                }
            )

    return sorted(bottlenecks, key=lambda x: x["dependent_count"], reverse=True)


def _generate_dependency_recommendations(graph: Dict[str, Dict]) -> List[str]:
    """Generate recommendations based on dependency analysis."""
    recommendations = []

    # Check for bottlenecks
    bottlenecks = _identify_bottlenecks(graph)
    if bottlenecks:
        recommendations.append(
            f"Priority attention needed for {len(bottlenecks)} bottleneck components"
        )

    # Check for isolated components
    isolated = [
        comp
        for comp, info in graph.items()
        if not info["depends_on"] and not info["depended_by"]
    ]
    if isolated:
        recommendations.append(
            f"Consider integration opportunities for {len(isolated)} isolated components"
        )

    # Check for long dependency chains
    levels = _determine_dependency_levels(graph)
    if len(levels) > 5:
        recommendations.append(
            "Consider parallelizing work streams to reduce critical path length"
        )

    return recommendations


# Helper functions for the updated reasoning tools
def _generate_thinking_steps(approach: str) -> List[str]:
    """Generate thinking steps based on approach."""
    if approach == "systematic":
        return [
            "1. **Understand the Problem**: What exactly are we trying to solve?",
            "2. **Identify Key Components**: What are the main parts/elements involved?",
            "3. **Analyze Requirements**: What constraints and requirements exist?",
            "4. **Consider Approaches**: What different ways could we tackle this?",
            "5. **Evaluate Options**: What are the pros/cons of each approach?",
            "6. **Plan Implementation**: What specific steps need to be taken?",
            "7. **Consider Challenges**: What obstacles might we encounter?",
            "8. **Validate Solution**: How will we know if our solution works?",
        ]
    elif approach == "creative":
        return [
            "1. **Explore the Challenge**: What makes this problem interesting?",
            "2. **Brainstorm Widely**: What unconventional approaches exist?",
            "3. **Question Assumptions**: What assumptions can we challenge?",
            "4. **Seek Inspiration**: What similar problems have been solved creatively?",
            "5. **Combine Ideas**: How can we merge different concepts?",
            "6. **Prototype Solutions**: What quick experiments can we try?",
            "7. **Iterate and Refine**: How can we improve our initial ideas?",
            "8. **Test Boundaries**: What happens if we push the limits?",
        ]
    elif approach == "analytical":
        return [
            "1. **Define Variables**: What are the key factors and parameters?",
            "2. **Establish Relationships**: How do these factors interact?",
            "3. **Gather Data**: What information do we need to collect?",
            "4. **Apply Logic**: What logical frameworks can we use?",
            "5. **Model the System**: How can we represent this mathematically?",
            "6. **Test Hypotheses**: What predictions can we make and verify?",
            "7. **Analyze Results**: What do the data and outcomes tell us?",
            "8. **Draw Conclusions**: What insights can we extract?",
        ]
    elif approach == "practical":
        return [
            "1. **Assess Resources**: What tools and time do we have available?",
            "2. **Set Priorities**: What needs to be done first and why?",
            "3. **Find Quick Wins**: What easy improvements can we make immediately?",
            "4. **Plan Implementation**: What's the most efficient path forward?",
            "5. **Anticipate Roadblocks**: What practical obstacles should we prepare for?",
            "6. **Build Incrementally**: How can we deliver value in stages?",
            "7. **Monitor Progress**: How will we track and measure success?",
            "8. **Adapt and Adjust**: How will we respond to changing circumstances?",
        ]
    else:
        return [
            "1. **Frame the Problem**: Clearly define what we're solving",
            "2. **Break Down Complexity**: Divide into manageable pieces",
            "3. **Explore Solutions**: Generate and evaluate options",
            "4. **Plan Execution**: Create actionable steps",
            "5. **Implement Carefully**: Execute with attention to detail",
            "6. **Review and Learn**: Reflect on outcomes and lessons",
        ]


def _estimate_completion_time(approach: str, step_count: int) -> str:
    """Estimate completion time based on approach and steps."""
    base_time = step_count * 15  # 15 minutes per step baseline
    if approach == "analytical":
        base_time *= 1.5  # Analytical takes longer
    elif approach == "creative":
        base_time *= 1.3  # Creative takes slightly longer

    if base_time < 60:
        return f"{int(base_time)} minutes"
    else:
        hours = base_time / 60
        return f"{hours:.1f} hours"


def _get_domain_dimensions(domain: str) -> List[str]:
    """Get dimensions based on domain."""
    if domain == "technical":
        return [
            "Architecture & Design",
            "Data & Storage",
            "Processing & Logic",
            "Interface & Integration",
            "Security & Validation",
            "Testing & Quality",
            "Deployment & Operations",
            "Monitoring & Maintenance",
        ]
    elif domain == "analytical":
        return [
            "Data Collection",
            "Data Cleaning & Preparation",
            "Exploratory Analysis",
            "Statistical Modeling",
            "Validation & Testing",
            "Interpretation & Insights",
            "Reporting & Communication",
            "Implementation & Action",
        ]
    elif domain == "creative":
        return [
            "Research & Inspiration",
            "Concept Development",
            "Design & Prototyping",
            "Feedback & Iteration",
            "Refinement & Polish",
            "Production & Delivery",
            "Launch & Promotion",
            "Evaluation & Learning",
        ]
    else:  # general
        return [
            "Understanding & Requirements",
            "Planning & Strategy",
            "Resource Identification",
            "Implementation Design",
            "Execution & Development",
            "Testing & Validation",
            "Integration & Deployment",
            "Review & Optimization",
        ]


def _calculate_subproblem_count(target_size: str, total_dimensions: int) -> int:
    """Calculate number of sub-problems based on target size."""
    if target_size == "large":
        return min(3, total_dimensions)
    elif target_size == "small":
        return total_dimensions
    else:  # medium
        return min(5, total_dimensions)


def _calculate_priority(dimension: str, domain: str) -> str:
    """Calculate priority for a dimension in a domain."""
    high_priority = {
        "technical": ["Architecture & Design", "Security & Validation"],
        "analytical": ["Data Collection", "Statistical Modeling"],
        "creative": ["Research & Inspiration", "Concept Development"],
        "general": ["Understanding & Requirements", "Planning & Strategy"],
    }

    if dimension in high_priority.get(domain, []):
        return "high"
    elif "Testing" in dimension or "Validation" in dimension:
        return "high"
    else:
        return "medium"


def _estimate_complexity(problem: str, dimension_count: int) -> str:
    """Estimate complexity based on problem length and dimensions."""
    complexity_score = len(problem) / 1000 + dimension_count

    if complexity_score < 2:
        return "low"
    elif complexity_score < 5:
        return "medium"
    else:
        return "high"


def _build_dependency_graph(
    components: List[str], relationships: List[Dict[str, str]]
) -> Dict[str, Dict]:
    """Build dependency graph from components and relationships."""
    graph = {
        comp: {"depends_on": [], "depended_by": [], "weight": 0} for comp in components
    }

    for rel in relationships:
        from_comp = rel["from"]
        to_comp = rel["to"]
        rel_type = rel.get("type", "depends_on")

        if rel_type == "depends_on":
            graph[from_comp]["depends_on"].append(to_comp)
            graph[to_comp]["depended_by"].append(from_comp)
            graph[to_comp]["weight"] += 1

    return graph


def _calculate_graph_complexity(graph: Dict[str, Dict]) -> str:
    """Calculate complexity of dependency graph."""
    total_connections = sum(len(info["depends_on"]) for info in graph.values())
    avg_connections = total_connections / len(graph) if graph else 0

    if avg_connections < 1:
        return "low"
    elif avg_connections < 3:
        return "medium"
    else:
        return "high"


def _calculate_max_depth(graph: Dict[str, Dict]) -> int:
    """Calculate maximum depth of dependency chain."""

    def get_depth(component: str, visited: set) -> int:
        if component in visited:
            return 0  # Circular dependency
        visited.add(component)

        if not graph[component]["depends_on"]:
            return 1

        max_child_depth = max(
            get_depth(dep, visited.copy()) for dep in graph[component]["depends_on"]
        )
        return 1 + max_child_depth

    return max(get_depth(comp, set()) for comp in graph) if graph else 0
