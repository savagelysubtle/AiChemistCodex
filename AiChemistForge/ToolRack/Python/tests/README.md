# Tests for Unified MCP Server

This directory contains the test suite for the AiChemistForge Unified MCP Server.

## Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Pytest configuration and shared fixtures
├── test_filesystem_tools.py # Tests for filesystem tools
├── test_registry.py         # Tests for tool registry
├── test_server.py          # Tests for MCP server functionality
└── README.md               # This file
```

## Running Tests

### Prerequisites

1. Ensure you have the virtual environment activated:
   ```bash
   # On Windows
   .venv\Scripts\Activate.ps1

   # On Unix/macOS
   source .venv/bin/activate
   ```

2. Install development dependencies:
   ```bash
   uv sync --all-groups
   ```

### Running All Tests

```bash
# Using pytest directly
python -m pytest tests/ -v

# Using the test runner script
python run_tests.py
```

### Running Specific Tests

```bash
# Run only filesystem tool tests
python -m pytest tests/test_filesystem_tools.py -v

# Run only registry tests
python -m pytest tests/test_registry.py -v

# Run only server tests
python -m pytest tests/test_server.py -v
```

### Test Coverage

To run tests with coverage reporting:

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Categories

### Unit Tests
- **test_registry.py**: Tests tool registry initialization and tool discovery
- **test_filesystem_tools.py**: Tests individual filesystem tools (file_tree, codebase_ingest)

### Integration Tests
- **test_server.py**: Tests MCP server startup, module imports, and basic functionality

## Test Configuration

The test suite is configured via:
- `pyproject.toml`: Main pytest configuration
- `conftest.py`: Shared fixtures and Python path setup

Key configuration:
- Async mode: Auto (pytest-asyncio)
- Test paths: `tests/` directory
- Minimum pytest version: 7.0

## Writing New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py`
2. Use descriptive test function names: `test_should_do_something_when_condition()`
3. Add `@pytest.mark.asyncio` for async tests
4. Use proper assertions instead of print statements
5. Clean up resources in test teardown

### Example Test Structure

```python
import pytest
from unified_mcp_server.tools.registry import ToolRegistry

@pytest.mark.asyncio
async def test_tool_functionality():
    """Test that a tool works correctly."""
    # Arrange
    registry = ToolRegistry()
    await registry.initialize_tools()

    # Act
    tool = registry.get_tool("tool_name")
    result = await tool.safe_execute(param="value")

    # Assert
    assert result["success"], f"Tool should succeed: {result.get('error', '')}"
    assert "expected_data" in result["result"]
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure virtual environment is activated and package is installed in development mode:
   ```bash
   uv pip install -e .
   ```

2. **Import errors**: Check that `conftest.py` is properly setting up the Python path

3. **Async test issues**: Ensure `@pytest.mark.asyncio` decorator is used for async tests

4. **Server startup failures**: Check that all dependencies are installed and the server can run independently:
   ```bash
   python -m unified_mcp_server.main --help
   ```