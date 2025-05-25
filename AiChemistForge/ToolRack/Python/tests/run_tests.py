#!/usr/bin/env python3
"""Test runner script for the Unified MCP Server."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run all tests with proper environment setup."""
    print("🧪 Running Unified MCP Server Tests")
    print("=" * 50)

    # Get the project root
    project_root = Path(__file__).parent

    try:
        # Run pytest with verbose output
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            cwd=project_root,
            check=False,
        )

        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")

        return result.returncode

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
