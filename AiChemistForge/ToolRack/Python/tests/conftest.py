"""Pytest configuration and shared fixtures for the test suite."""

import sys
from pathlib import Path

# Add the src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)
