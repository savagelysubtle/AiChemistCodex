"""Tool composition utilities for the unified MCP server."""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .exceptions import ToolNotFoundError


class CompositionMode(Enum):
    """Modes for tool composition."""

    SEQUENTIAL = "sequential"  # Execute tools one after another
    PARALLEL = "parallel"  # Execute tools in parallel
    CONDITIONAL = "conditional"  # Execute based on conditions


@dataclass
class CompositionStep:
    """Represents a step in a tool composition."""

    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    transform: Optional[Callable[[Any], Dict[str, Any]]] = None
    error_handler: Optional[Callable[[Exception], Any]] = None
    timeout: Optional[float] = None


@dataclass
class CompositionResult:
    """Result of a tool composition execution."""

    success: bool
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, Exception] = field(default_factory=dict)
    execution_time: float = 0.0
    steps_executed: List[str] = field(default_factory=list)


class ToolComposer:
    """Composes and executes tool workflows."""

    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        self.compositions: Dict[str, "Composition"] = {}

    def register_composition(self, name: str, composition: "Composition") -> None:
        """Register a named composition.

        Args:
            name: Name of the composition
            composition: Composition instance
        """
        self.compositions[name] = composition

    def get_composition(self, name: str) -> Optional["Composition"]:
        """Get a registered composition by name.

        Args:
            name: Name of the composition

        Returns:
            Composition instance or None if not found
        """
        return self.compositions.get(name)

    async def execute_composition(
        self,
        composition: Union[str, "Composition"],
        context: Optional[Dict[str, Any]] = None,
    ) -> CompositionResult:
        """Execute a composition.

        Args:
            composition: Composition name or instance
            context: Initial context for the composition

        Returns:
            Composition execution result
        """
        if isinstance(composition, str):
            comp = self.get_composition(composition)
            if comp is None:
                raise ToolNotFoundError(f"Composition '{composition}' not found")
        else:
            comp = composition

        return await comp.execute(self.tool_registry, context or {})

    def create_sequential_composition(
        self, name: str, steps: List[CompositionStep], description: str = ""
    ) -> "Composition":
        """Create a sequential composition.

        Args:
            name: Name of the composition
            steps: List of composition steps
            description: Description of the composition

        Returns:
            Sequential composition instance
        """
        composition = SequentialComposition(name, steps, description)
        self.register_composition(name, composition)
        return composition

    def create_parallel_composition(
        self,
        name: str,
        steps: List[CompositionStep],
        description: str = "",
        wait_for_all: bool = True,
    ) -> "Composition":
        """Create a parallel composition.

        Args:
            name: Name of the composition
            steps: List of composition steps
            description: Description of the composition
            wait_for_all: Whether to wait for all steps to complete

        Returns:
            Parallel composition instance
        """
        composition = ParallelComposition(name, steps, description, wait_for_all)
        self.register_composition(name, composition)
        return composition

    def create_conditional_composition(
        self, name: str, steps: List[CompositionStep], description: str = ""
    ) -> "Composition":
        """Create a conditional composition.

        Args:
            name: Name of the composition
            steps: List of composition steps
            description: Description of the composition

        Returns:
            Conditional composition instance
        """
        composition = ConditionalComposition(name, steps, description)
        self.register_composition(name, composition)
        return composition


class Composition:
    """Base class for tool compositions."""

    def __init__(self, name: str, steps: List[CompositionStep], description: str = ""):
        self.name = name
        self.steps = steps
        self.description = description

    async def execute(
        self, tool_registry, context: Dict[str, Any]
    ) -> CompositionResult:
        """Execute the composition.

        Args:
            tool_registry: Tool registry for accessing tools
            context: Execution context

        Returns:
            Composition result
        """
        raise NotImplementedError("Subclasses must implement execute method")

    async def _execute_step(
        self, step: CompositionStep, tool_registry, context: Dict[str, Any]
    ) -> Any:
        """Execute a single composition step.

        Args:
            step: Step to execute
            tool_registry: Tool registry
            context: Current context

        Returns:
            Step execution result
        """
        # Get the tool
        tool = tool_registry.get_tool(step.tool_name)
        if tool is None:
            raise ToolNotFoundError(f"Tool '{step.tool_name}' not found")

        # Prepare parameters
        parameters = step.parameters.copy()

        # Apply parameter transformation if provided
        if step.transform:
            transformed = step.transform(context)
            parameters.update(transformed)

        # Execute with timeout if specified
        try:
            if step.timeout:
                result = await asyncio.wait_for(
                    tool.safe_execute(**parameters), timeout=step.timeout
                )
            else:
                result = await tool.safe_execute(**parameters)

            return result

        except Exception as e:
            if step.error_handler:
                return step.error_handler(e)
            raise


class SequentialComposition(Composition):
    """Sequential tool composition - executes tools one after another."""

    async def execute(
        self, tool_registry, context: Dict[str, Any]
    ) -> CompositionResult:
        """Execute steps sequentially."""
        import time

        start_time = time.time()
        result = CompositionResult(success=True)
        current_context = context.copy()

        for step in self.steps:
            try:
                # Check condition if provided
                if step.condition and not step.condition(current_context):
                    continue

                # Execute step
                step_result = await self._execute_step(
                    step, tool_registry, current_context
                )

                # Store result
                result.results[step.tool_name] = step_result
                result.steps_executed.append(step.tool_name)

                # Update context with result
                current_context[f"{step.tool_name}_result"] = step_result

                # If step failed, stop execution
                if isinstance(step_result, dict) and not step_result.get(
                    "success", True
                ):
                    result.success = False
                    break

            except Exception as e:
                result.errors[step.tool_name] = e
                result.success = False
                break

        result.execution_time = time.time() - start_time
        return result


class ParallelComposition(Composition):
    """Parallel tool composition - executes tools concurrently."""

    def __init__(
        self,
        name: str,
        steps: List[CompositionStep],
        description: str = "",
        wait_for_all: bool = True,
    ):
        super().__init__(name, steps, description)
        self.wait_for_all = wait_for_all

    async def execute(
        self, tool_registry, context: Dict[str, Any]
    ) -> CompositionResult:
        """Execute steps in parallel."""
        import time

        start_time = time.time()
        result = CompositionResult(success=True)

        # Filter steps based on conditions
        executable_steps = []
        for step in self.steps:
            if not step.condition or step.condition(context):
                executable_steps.append(step)

        # Create tasks for parallel execution
        tasks = []
        for step in executable_steps:
            task = asyncio.create_task(
                self._execute_step_with_error_handling(step, tool_registry, context)
            )
            tasks.append((step.tool_name, task))

        # Wait for completion
        if self.wait_for_all:
            # Wait for all tasks
            for step_name, task in tasks:
                try:
                    step_result = await task
                    result.results[step_name] = step_result
                    result.steps_executed.append(step_name)
                except Exception as e:
                    result.errors[step_name] = e
                    result.success = False
        else:
            # Wait for first completion
            done, pending = await asyncio.wait(
                [task for _, task in tasks], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # Process completed task
            for step_name, task in tasks:
                if task in done:
                    try:
                        step_result = await task
                        result.results[step_name] = step_result
                        result.steps_executed.append(step_name)
                        break
                    except Exception as e:
                        result.errors[step_name] = e
                        result.success = False

        result.execution_time = time.time() - start_time
        return result

    async def _execute_step_with_error_handling(
        self, step: CompositionStep, tool_registry, context: Dict[str, Any]
    ) -> Any:
        """Execute a step with error handling."""
        try:
            return await self._execute_step(step, tool_registry, context)
        except Exception as e:
            if step.error_handler:
                return step.error_handler(e)
            raise


class ConditionalComposition(Composition):
    """Conditional tool composition - executes tools based on conditions."""

    async def execute(
        self, tool_registry, context: Dict[str, Any]
    ) -> CompositionResult:
        """Execute steps conditionally."""
        import time

        start_time = time.time()
        result = CompositionResult(success=True)
        current_context = context.copy()

        for step in self.steps:
            try:
                # Check condition
                if step.condition and not step.condition(current_context):
                    continue

                # Execute step
                step_result = await self._execute_step(
                    step, tool_registry, current_context
                )

                # Store result
                result.results[step.tool_name] = step_result
                result.steps_executed.append(step.tool_name)

                # Update context
                current_context[f"{step.tool_name}_result"] = step_result
                current_context["last_result"] = step_result

            except Exception as e:
                result.errors[step.tool_name] = e
                if not step.error_handler:
                    result.success = False
                    break

        result.execution_time = time.time() - start_time
        return result


# Utility functions for creating common compositions


def create_analysis_workflow(
    tool_composer: ToolComposer, project_path: str
) -> Composition:
    """Create a workflow for analyzing a project.

    Args:
        tool_composer: Tool composer instance
        project_path: Path to the project to analyze

    Returns:
        Analysis workflow composition
    """
    steps = [
        CompositionStep(
            tool_name="file_tree", parameters={"path": project_path, "max_depth": 3}
        ),
        CompositionStep(
            tool_name="codebase_ingest",
            parameters={"path": project_path, "max_files": 50},
            transform=lambda ctx: {"include_patterns": ["*.py", "*.md", "*.json"]},
        ),
    ]

    return tool_composer.create_sequential_composition(
        "project_analysis", steps, "Analyze project structure and codebase"
    )


def create_cursor_analysis_workflow(
    tool_composer: ToolComposer, project_name: str
) -> Composition:
    """Create a workflow for analyzing Cursor project data.

    Args:
        tool_composer: Tool composer instance
        project_name: Name of the Cursor project

    Returns:
        Cursor analysis workflow composition
    """
    steps = [
        CompositionStep(
            tool_name="cursor_db",
            parameters={"operation": "get_chat_data", "project_name": project_name},
        ),
        CompositionStep(
            tool_name="cursor_db",
            parameters={"operation": "get_composer_ids", "project_name": project_name},
        ),
    ]

    return tool_composer.create_parallel_composition(
        "cursor_analysis", steps, f"Analyze Cursor project data for {project_name}"
    )


# Global tool composer instance (will be initialized with tool registry)
tool_composer: Optional[ToolComposer] = None


def initialize_composer(tool_registry) -> ToolComposer:
    """Initialize the global tool composer.

    Args:
        tool_registry: Tool registry instance

    Returns:
        Initialized tool composer
    """
    global tool_composer
    tool_composer = ToolComposer(tool_registry)
    return tool_composer


def get_composer() -> Optional[ToolComposer]:
    """Get the global tool composer instance."""
    return tool_composer
