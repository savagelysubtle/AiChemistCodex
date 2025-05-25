"""Filesystem resources for FastMCP."""

from pathlib import Path

from fastmcp import FastMCP


def register_filesystem_resources(mcp: FastMCP) -> None:
    """Register filesystem resources with the FastMCP instance."""

    @mcp.resource("filesystem://current-tree")
    async def current_directory_tree() -> str:
        """Provide the current directory tree structure."""
        try:
            current_path = Path.cwd()
            tree_lines = [f"{current_path.name}/"]

            def add_items(dir_path: Path, prefix: str = "", depth: int = 0):
                if depth >= 3:  # Limit depth for resource
                    return
                try:
                    items = [
                        item
                        for item in dir_path.iterdir()
                        if not item.name.startswith(".")
                    ]
                    items.sort(key=lambda x: (x.is_file(), x.name.lower()))

                    for i, item in enumerate(items):
                        is_last = i == len(items) - 1
                        current_prefix = "└── " if is_last else "├── "
                        item_name = f"{item.name}/" if item.is_dir() else item.name
                        tree_lines.append(f"{prefix}{current_prefix}{item_name}")

                        if item.is_dir() and depth + 1 < 3:
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            add_items(item, next_prefix, depth + 1)

                except PermissionError:
                    tree_lines.append(f"{prefix}├── [Permission Denied]")

            add_items(current_path)
            return "\n".join(tree_lines)

        except Exception as e:
            return f"Error generating directory tree: {e}"

    @mcp.resource("filesystem://project-summary")
    async def project_summary() -> str:
        """Provide a summary of the current project structure."""
        try:
            current_path = Path.cwd()

            # Count different file types
            file_counts = {}
            total_files = 0
            total_dirs = 0

            for item in current_path.rglob("*"):
                if item.is_file():
                    total_files += 1
                    ext = item.suffix.lower()
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                elif item.is_dir():
                    total_dirs += 1

            # Look for common project indicators
            project_files = []
            common_files = [
                "README.md",
                "README.txt",
                "pyproject.toml",
                "requirements.txt",
                "package.json",
                "Cargo.toml",
                "pom.xml",
                "build.gradle",
                ".gitignore",
                "LICENSE",
                "setup.py",
                "main.py",
            ]

            for file_name in common_files:
                file_path = current_path / file_name
                if file_path.exists():
                    project_files.append(file_name)

            # Generate summary
            summary_parts = [
                f"# Project Summary: {current_path.name}",
                f"**Location**: {current_path}",
                f"**Total Files**: {total_files}",
                f"**Total Directories**: {total_dirs}",
                "",
                "## File Types:",
            ]

            # Show top file types
            sorted_counts = sorted(
                file_counts.items(), key=lambda x: x[1], reverse=True
            )
            for ext, count in sorted_counts[:10]:
                ext_name = ext if ext else "(no extension)"
                summary_parts.append(f"- {ext_name}: {count} files")

            if project_files:
                summary_parts.extend(
                    [
                        "",
                        "## Project Files Found:",
                    ]
                )
                for file_name in project_files:
                    summary_parts.append(f"- {file_name}")

            return "\n".join(summary_parts)

        except Exception as e:
            return f"Error generating project summary: {e}"
