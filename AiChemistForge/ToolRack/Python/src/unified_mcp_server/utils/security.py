"""Security utilities for the unified MCP server."""

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import Optional, Set, Union
from urllib.parse import urlparse

from .exceptions import PathTraversalError, SecurityError, path_traversal_detected


class PathSecurity:
    """Path security utilities for preventing traversal attacks."""

    def __init__(self, allowed_paths: Optional[Set[str]] = None):
        self.allowed_paths = allowed_paths or set()
        # Add current working directory by default
        self.allowed_paths.add(str(Path.cwd().resolve()))

    def add_allowed_path(self, path: Union[str, Path]) -> None:
        """Add a path to the allowed paths set."""
        resolved_path = Path(path).expanduser().resolve()
        self.allowed_paths.add(str(resolved_path))

    def validate_path(self, path: Union[str, Path]) -> Path:
        """Validate a path against security constraints.

        Args:
            path: Path to validate

        Returns:
            Resolved Path object

        Raises:
            PathTraversalError: If path traversal is detected
            SecurityError: If path is not allowed
        """
        try:
            # Convert to Path and resolve
            resolved_path = Path(path).expanduser().resolve()
        except Exception as e:
            raise SecurityError(f"Invalid path: {path} - {e}")

        # Check for obvious traversal attempts
        path_str = str(path)
        if ".." in path_str or path_str.startswith("/"):
            # Allow absolute paths only if they're in allowed_paths
            if not any(
                str(resolved_path).startswith(allowed) for allowed in self.allowed_paths
            ):
                raise path_traversal_detected(str(path))

        # Ensure the resolved path is within allowed directories
        if self.allowed_paths:
            if not any(
                str(resolved_path).startswith(allowed) for allowed in self.allowed_paths
            ):
                raise SecurityError(
                    f"Path not in allowed directories: {resolved_path}",
                    error_code="PATH_NOT_ALLOWED",
                    context={
                        "path": str(resolved_path),
                        "allowed_paths": list(self.allowed_paths),
                    },
                )

        return resolved_path

    def is_safe_path(self, path: Union[str, Path]) -> bool:
        """Check if a path is safe without raising exceptions."""
        try:
            self.validate_path(path)
            return True
        except (SecurityError, PathTraversalError):
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename by removing dangerous characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace dangerous characters
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(dangerous_chars, "_", filename)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Ensure it's not empty
        if not sanitized:
            sanitized = "unnamed_file"

        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            max_name_len = 255 - len(ext)
            sanitized = name[:max_name_len] + ext

        return sanitized


class InputSanitizer:
    """Input sanitization utilities."""

    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*\b=\b.*\bOR\b)",
        r"(\bAND\b.*\b=\b.*\bAND\b)",
        r"(\'.*\'.*=.*\'.*\')",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"(;|\||\&\&|\|\|)",
        r"(`.*`)",
        r"(\$\(.*\))",
        r"(\\x[0-9a-fA-F]{2})",
    ]

    XSS_PATTERNS = [
        r"(<script.*?>.*?</script>)",
        r"(javascript:)",
        r"(on\w+\s*=)",
        r"(<.*?>)",
    ]

    def __init__(self):
        self.sql_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.SQL_INJECTION_PATTERNS
        ]
        self.cmd_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.COMMAND_INJECTION_PATTERNS
        ]
        self.xss_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS
        ]

    def sanitize_string(self, value: str, max_length: Optional[int] = None) -> str:
        """Sanitize a string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)

        # Remove null bytes
        sanitized = value.replace("\x00", "")

        # Limit length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    def check_sql_injection(self, value: str) -> bool:
        """Check if string contains SQL injection patterns.

        Args:
            value: String to check

        Returns:
            True if potential SQL injection detected
        """
        return any(pattern.search(value) for pattern in self.sql_patterns)

    def check_command_injection(self, value: str) -> bool:
        """Check if string contains command injection patterns.

        Args:
            value: String to check

        Returns:
            True if potential command injection detected
        """
        return any(pattern.search(value) for pattern in self.cmd_patterns)

    def check_xss(self, value: str) -> bool:
        """Check if string contains XSS patterns.

        Args:
            value: String to check

        Returns:
            True if potential XSS detected
        """
        return any(pattern.search(value) for pattern in self.xss_patterns)

    def validate_input(self, value: str, allow_html: bool = False) -> str:
        """Validate input against common injection attacks.

        Args:
            value: Input to validate
            allow_html: Whether to allow HTML content

        Returns:
            Validated input

        Raises:
            SecurityError: If malicious content is detected
        """
        if self.check_sql_injection(value):
            raise SecurityError(
                "Potential SQL injection detected",
                error_code="SQL_INJECTION",
                context={"input": value[:100]},
            )

        if self.check_command_injection(value):
            raise SecurityError(
                "Potential command injection detected",
                error_code="COMMAND_INJECTION",
                context={"input": value[:100]},
            )

        if not allow_html and self.check_xss(value):
            raise SecurityError(
                "Potential XSS detected",
                error_code="XSS_DETECTED",
                context={"input": value[:100]},
            )

        return value


class SecureRandom:
    """Secure random generation utilities."""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token.

        Args:
            length: Length of the token in bytes

        Returns:
            Hex-encoded token
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Generate a secure random password.

        Args:
            length: Length of the password

        Returns:
            Random password
        """
        alphabet = (
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        )
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def generate_id() -> str:
        """Generate a secure random ID.

        Returns:
            Random ID string
        """
        return secrets.token_urlsafe(16)


class HashUtils:
    """Hashing and verification utilities."""

    @staticmethod
    def hash_string(value: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash a string with a salt.

        Args:
            value: String to hash
            salt: Optional salt (will generate if not provided)

        Returns:
            Tuple of (hashed_value, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        hash_obj = hashlib.pbkdf2_hmac(
            "sha256", value.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hash_obj.hex(), salt

    @staticmethod
    def verify_string(value: str, hashed_value: str, salt: str) -> bool:
        """Verify a string against its hash.

        Args:
            value: Original string
            hashed_value: Hashed value to compare against
            salt: Salt used in hashing

        Returns:
            True if verification succeeds
        """
        computed_hash, _ = HashUtils.hash_string(value, salt)
        return secrets.compare_digest(computed_hash, hashed_value)

    @staticmethod
    def hash_file(file_path: Union[str, Path]) -> str:
        """Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex-encoded SHA-256 hash
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


class URLSecurity:
    """URL security utilities."""

    ALLOWED_SCHEMES = {"http", "https", "ftp", "ftps"}
    DANGEROUS_DOMAINS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "metadata.google.internal",
        "169.254.169.254",  # AWS metadata
    }

    @classmethod
    def validate_url(
        cls,
        url: str,
        allowed_schemes: Optional[Set[str]] = None,
        block_private: bool = True,
    ) -> str:
        """Validate a URL for security concerns.

        Args:
            url: URL to validate
            allowed_schemes: Set of allowed schemes
            block_private: Whether to block private/internal URLs

        Returns:
            Validated URL

        Raises:
            SecurityError: If URL is not safe
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise SecurityError(f"Invalid URL: {e}")

        # Check scheme
        allowed = allowed_schemes or cls.ALLOWED_SCHEMES
        if parsed.scheme not in allowed:
            raise SecurityError(
                f"URL scheme '{parsed.scheme}' not allowed",
                error_code="INVALID_SCHEME",
                context={"url": url, "allowed_schemes": list(allowed)},
            )

        # Check for dangerous domains
        if block_private and parsed.hostname in cls.DANGEROUS_DOMAINS:
            raise SecurityError(
                f"Access to internal/metadata URLs blocked: {parsed.hostname}",
                error_code="BLOCKED_DOMAIN",
                context={"url": url, "hostname": parsed.hostname},
            )

        # Check for private IP ranges
        if block_private and parsed.hostname:
            if cls._is_private_ip(parsed.hostname):
                raise SecurityError(
                    f"Access to private IP ranges blocked: {parsed.hostname}",
                    error_code="PRIVATE_IP_BLOCKED",
                    context={"url": url, "hostname": parsed.hostname},
                )

        return url

    @staticmethod
    def _is_private_ip(hostname: str) -> bool:
        """Check if hostname is a private IP address."""
        import ipaddress

        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            return False


# Global instances for convenience
path_security = PathSecurity()
input_sanitizer = InputSanitizer()


# Convenience functions
def validate_path(path: Union[str, Path]) -> Path:
    """Validate a path using the global path security instance."""
    return path_security.validate_path(path)


def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize input using the global input sanitizer."""
    sanitized = input_sanitizer.sanitize_string(value, max_length)
    return input_sanitizer.validate_input(sanitized)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure token."""
    return SecureRandom.generate_token(length)


def hash_password(password: str) -> tuple[str, str]:
    """Hash a password securely."""
    return HashUtils.hash_string(password)


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify a password against its hash."""
    return HashUtils.verify_string(password, hashed_password, salt)
