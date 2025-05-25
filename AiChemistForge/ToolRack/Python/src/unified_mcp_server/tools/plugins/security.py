"""Plugin security system for the unified MCP server."""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

from ...server.config import config
from ...server.logging import setup_logging
from ...utils.security import validate_path


class PluginPermission(Enum):
    """Standard plugin permissions."""

    # File system access
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    EXECUTE_COMMANDS = "execute_commands"

    # Network access
    NETWORK_ACCESS = "network_access"
    HTTP_REQUESTS = "http_requests"

    # System access
    SYSTEM_INFO = "system_info"
    ENVIRONMENT_VARS = "environment_vars"

    # Tool access
    TOOL_COMPOSITION = "tool_composition"
    OTHER_TOOLS = "other_tools"

    # Database access
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"

    # Configuration access
    CONFIG_READ = "config_read"
    CONFIG_WRITE = "config_write"


class PluginSecurity:
    """Security system for plugin validation and permission management."""

    def __init__(self):
        self.logger = setup_logging("plugin.security", config.log_level)

        # Default permission policies
        self.default_permissions = {
            PluginPermission.READ_FILES: False,
            PluginPermission.WRITE_FILES: False,
            PluginPermission.EXECUTE_COMMANDS: False,
            PluginPermission.NETWORK_ACCESS: False,
            PluginPermission.HTTP_REQUESTS: False,
            PluginPermission.SYSTEM_INFO: True,  # Generally safe
            PluginPermission.ENVIRONMENT_VARS: False,
            PluginPermission.TOOL_COMPOSITION: True,  # Core MCP functionality
            PluginPermission.OTHER_TOOLS: False,
            PluginPermission.DATABASE_READ: False,
            PluginPermission.DATABASE_WRITE: False,
            PluginPermission.CONFIG_READ: True,  # Plugin config access
            PluginPermission.CONFIG_WRITE: False,
        }

        # Plugin-specific permission overrides
        self.plugin_permissions: Dict[str, Dict[str, bool]] = {}
        self._load_permission_config()

    def _load_permission_config(self) -> None:
        """Load plugin permission configuration from environment variables."""
        # Look for plugin permission environment variables
        # Format: PLUGIN_SECURITY_{PLUGIN_NAME}_{PERMISSION} = true/false

        for key, value in os.environ.items():
            if key.startswith("PLUGIN_SECURITY_"):
                parts = key.split("_")
                if len(parts) >= 4:
                    plugin_name = "_".join(parts[2:-1]).lower()
                    permission = parts[-1].lower()

                    # Convert permission to enum if valid
                    try:
                        perm_enum = PluginPermission(permission)
                        enabled = value.lower() in ("true", "1", "yes", "on")

                        if plugin_name not in self.plugin_permissions:
                            self.plugin_permissions[plugin_name] = {}

                        self.plugin_permissions[plugin_name][permission] = enabled
                        self.logger.debug(
                            f"Set permission {permission} = {enabled} for plugin {plugin_name}"
                        )

                    except ValueError:
                        self.logger.warning(f"Unknown permission: {permission}")

    def validate_plugin(self, plugin_path: str) -> bool:
        """Validate plugin security requirements.

        Args:
            plugin_path: Path to plugin file or directory

        Returns:
            True if plugin passes security validation
        """
        try:
            path = Path(plugin_path)

            # Path security validation
            validate_path(path)

            # Check if path exists and is readable
            if not path.exists():
                self.logger.error(f"Plugin path does not exist: {path}")
                return False

            # Validate plugin is in allowed location
            if not self._is_plugin_path_allowed(path):
                self.logger.error(f"Plugin path not in allowed locations: {path}")
                return False

            # Check file permissions
            if not self._validate_file_permissions(path):
                self.logger.error(f"Plugin file permissions are invalid: {path}")
                return False

            self.logger.debug(f"Plugin security validation passed: {path}")
            return True

        except Exception as e:
            self.logger.error(
                f"Plugin security validation failed for {plugin_path}: {e}"
            )
            return False

    def _is_plugin_path_allowed(self, path: Path) -> bool:
        """Check if plugin path is in allowed locations.

        Args:
            path: Plugin path to check

        Returns:
            True if path is allowed
        """
        # Get allowed plugin directories from config
        allowed_dirs = getattr(config, "plugin_directories", [])

        # Add default safe directories
        default_dirs = ["plugins/", "~/.aichemistforge/plugins/", "./custom_plugins/"]

        all_dirs = allowed_dirs + default_dirs

        resolved_path = path.resolve()

        for allowed_dir in all_dirs:
            try:
                allowed_path = Path(allowed_dir).expanduser().resolve()
                if str(resolved_path).startswith(str(allowed_path)):
                    return True
            except Exception:
                continue

        return False

    def _validate_file_permissions(self, path: Path) -> bool:
        """Validate file permissions for security.

        Args:
            path: Path to validate

        Returns:
            True if permissions are acceptable
        """
        try:
            # Check that file is readable
            if not os.access(path, os.R_OK):
                return False

            # For security, plugins should not be executable by default
            # They should be loaded as modules, not executed directly
            stat_info = path.stat()

            # Check if file is world-writable (security risk)
            if stat_info.st_mode & 0o002:
                self.logger.warning(f"Plugin file is world-writable: {path}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating file permissions for {path}: {e}")
            return False

    def get_plugin_permissions(self, plugin_name: str) -> Dict[str, bool]:
        """Get permissions for a specific plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Dictionary of permission name to boolean
        """
        # Start with default permissions
        permissions = {}
        for perm, default_value in self.default_permissions.items():
            permissions[perm.value] = default_value

        # Apply plugin-specific overrides
        plugin_specific = self.plugin_permissions.get(plugin_name.lower(), {})
        permissions.update(plugin_specific)

        return permissions

    def check_permission(self, plugin_name: str, permission: PluginPermission) -> bool:
        """Check if a plugin has a specific permission.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to check

        Returns:
            True if permission is granted
        """
        permissions = self.get_plugin_permissions(plugin_name)
        return permissions.get(permission.value, False)

    def grant_permission(self, plugin_name: str, permission: PluginPermission) -> None:
        """Grant a permission to a plugin.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to grant
        """
        if plugin_name.lower() not in self.plugin_permissions:
            self.plugin_permissions[plugin_name.lower()] = {}

        self.plugin_permissions[plugin_name.lower()][permission.value] = True
        self.logger.info(
            f"Granted permission {permission.value} to plugin {plugin_name}"
        )

    def revoke_permission(self, plugin_name: str, permission: PluginPermission) -> None:
        """Revoke a permission from a plugin.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to revoke
        """
        if plugin_name.lower() not in self.plugin_permissions:
            self.plugin_permissions[plugin_name.lower()] = {}

        self.plugin_permissions[plugin_name.lower()][permission.value] = False
        self.logger.info(
            f"Revoked permission {permission.value} from plugin {plugin_name}"
        )

    def create_sandbox_environment(self, plugin_name: str) -> Dict[str, Any]:
        """Create a sandboxed environment for plugin execution.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Sandbox environment configuration
        """
        permissions = self.get_plugin_permissions(plugin_name)

        sandbox = {
            "plugin_name": plugin_name,
            "permissions": permissions,
            "restricted_modules": [],
            "allowed_modules": [],
            "environment_vars": {},
            "temp_directory": None,
        }

        # Restrict dangerous modules based on permissions
        if not permissions.get(PluginPermission.EXECUTE_COMMANDS.value, False):
            sandbox["restricted_modules"].extend(
                ["subprocess", "os.system", "commands", "popen2"]
            )

        if not permissions.get(PluginPermission.NETWORK_ACCESS.value, False):
            sandbox["restricted_modules"].extend(
                ["socket", "urllib", "requests", "httplib", "http.client"]
            )

        if not permissions.get(PluginPermission.WRITE_FILES.value, False):
            sandbox["restricted_modules"].extend(
                ["shutil.rmtree", "os.remove", "os.unlink"]
            )

        # Set up allowed modules
        sandbox["allowed_modules"] = [
            "json",
            "re",
            "datetime",
            "math",
            "random",
            "string",
            "typing",
        ]

        # Create temporary directory if needed
        if permissions.get(PluginPermission.WRITE_FILES.value, False):
            import tempfile

            sandbox["temp_directory"] = tempfile.mkdtemp(
                prefix=f"plugin_{plugin_name}_"
            )

        return sandbox

    def validate_plugin_code(self, plugin_path: Path) -> List[str]:
        """Perform static analysis on plugin code for security issues.

        Args:
            plugin_path: Path to plugin file

        Returns:
            List of security warnings
        """
        warnings = []

        try:
            with open(plugin_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for dangerous imports
            dangerous_imports = [
                "import os",
                "from os import",
                "import subprocess",
                "import sys",
                "import socket",
                "import pickle",
            ]

            for dangerous in dangerous_imports:
                if dangerous in content:
                    warnings.append(
                        f"Potentially dangerous import detected: {dangerous}"
                    )

            # Check for dangerous function calls
            dangerous_calls = [
                "eval(",
                "exec(",
                "compile(",
                "__import__(",
                "getattr(",
                "setattr(",
                "delattr(",
            ]

            for dangerous in dangerous_calls:
                if dangerous in content:
                    warnings.append(f"Potentially dangerous function call: {dangerous}")

            # Check for file operations
            file_operations = ["open(", "file(", "with open"]

            for operation in file_operations:
                if operation in content:
                    warnings.append(f"File operation detected: {operation}")

        except Exception as e:
            warnings.append(f"Error reading plugin file: {e}")

        return warnings

    def get_security_report(self, plugin_name: str) -> Dict[str, Any]:
        """Generate a security report for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Security report dictionary
        """
        permissions = self.get_plugin_permissions(plugin_name)

        # Count granted permissions
        granted_count = sum(1 for granted in permissions.values() if granted)
        total_count = len(permissions)

        risk_level = "LOW"
        if granted_count > total_count * 0.7:
            risk_level = "HIGH"
        elif granted_count > total_count * 0.4:
            risk_level = "MEDIUM"

        return {
            "plugin_name": plugin_name,
            "risk_level": risk_level,
            "permissions_granted": granted_count,
            "permissions_total": total_count,
            "permissions": permissions,
            "recommendations": self._get_security_recommendations(permissions),
        }

    def _get_security_recommendations(self, permissions: Dict[str, bool]) -> List[str]:
        """Get security recommendations based on permissions.

        Args:
            permissions: Plugin permissions

        Returns:
            List of security recommendations
        """
        recommendations = []

        high_risk_perms = [
            PluginPermission.EXECUTE_COMMANDS.value,
            PluginPermission.WRITE_FILES.value,
            PluginPermission.DATABASE_WRITE.value,
            PluginPermission.CONFIG_WRITE.value,
        ]

        for perm in high_risk_perms:
            if permissions.get(perm, False):
                recommendations.append(
                    f"Consider revoking high-risk permission: {perm}"
                )

        if permissions.get(PluginPermission.NETWORK_ACCESS.value, False):
            recommendations.append("Monitor network access for suspicious activity")

        if not any(permissions.values()):
            recommendations.append(
                "Plugin has minimal permissions - good security posture"
            )

        return recommendations
