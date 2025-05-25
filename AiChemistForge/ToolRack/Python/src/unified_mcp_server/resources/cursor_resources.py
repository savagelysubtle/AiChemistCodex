"""Cursor IDE resources for FastMCP."""

import sqlite3
from pathlib import Path

from fastmcp import FastMCP


def register_cursor_resources(mcp: FastMCP) -> None:
    """Register cursor resources with the FastMCP instance."""

    @mcp.resource("cursor://projects")
    async def list_cursor_projects() -> str:
        """Provide a list of Cursor IDE projects."""
        try:
            # Common Cursor database paths
            cursor_paths = [
                Path.home() / "AppData/Roaming/Cursor/User/globalStorage/state.vscdb",
                Path.home()
                / "Library/Application Support/Cursor/User/globalStorage/state.vscdb",
                Path.home() / ".config/Cursor/User/globalStorage/state.vscdb",
            ]

            # Find existing database
            db_path = None
            for path in cursor_paths:
                if path.exists():
                    db_path = path
                    break

            if not db_path:
                return "Cursor database not found in common locations"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                all_tables = [row[0] for row in cursor.fetchall()]

                project_tables = [
                    table for table in all_tables if table.startswith("project_")
                ]

                if not project_tables:
                    return "No Cursor projects found in database"

                project_list = ["# Cursor IDE Projects"]
                for table in project_tables:
                    project_name = table.replace("project_", "").replace("_", "/")

                    # Get record count for this project
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        record_count = cursor.fetchone()[0]
                        project_list.append(
                            f"- **{project_name}** ({record_count} records)"
                        )
                    except:
                        project_list.append(
                            f"- **{project_name}** (unable to count records)"
                        )

                return "\n".join(project_list)

        except Exception as e:
            return f"Error accessing Cursor projects: {e}"
