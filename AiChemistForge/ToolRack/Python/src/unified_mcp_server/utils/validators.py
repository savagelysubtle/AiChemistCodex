"""Input validation utilities for the unified MCP server."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union
from urllib.parse import urlparse

from .exceptions import InputValidationError, validation_failed


class Validator:
    """Base validator class for input validation."""

    def __init__(self, required: bool = True, allow_none: bool = False):
        self.required = required
        self.allow_none = allow_none

    def validate(self, value: Any, field_name: str = "field") -> Any:
        """Validate a value.

        Args:
            value: Value to validate
            field_name: Name of the field being validated

        Returns:
            Validated value

        Raises:
            InputValidationError: If validation fails
        """
        if value is None:
            if self.allow_none:
                return None
            if self.required:
                raise validation_failed(field_name, value, "Field is required")
            return None

        return self._validate_value(value, field_name)

    def _validate_value(self, value: Any, field_name: str) -> Any:
        """Override in subclasses to implement specific validation."""
        return value


class StringValidator(Validator):
    """Validator for string values."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[Union[str, Pattern]] = None,
        choices: Optional[List[str]] = None,
        strip: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.choices = choices
        self.strip = strip

    def _validate_value(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise validation_failed(field_name, value, "Must be a string")

        if self.strip:
            value = value.strip()

        if self.min_length is not None and len(value) < self.min_length:
            raise validation_failed(
                field_name, value, f"Must be at least {self.min_length} characters"
            )

        if self.max_length is not None and len(value) > self.max_length:
            raise validation_failed(
                field_name, value, f"Must be at most {self.max_length} characters"
            )

        if self.pattern and not self.pattern.match(value):
            raise validation_failed(
                field_name, value, f"Must match pattern: {self.pattern.pattern}"
            )

        if self.choices and value not in self.choices:
            raise validation_failed(
                field_name, value, f"Must be one of: {', '.join(self.choices)}"
            )

        return value


class IntegerValidator(Validator):
    """Validator for integer values."""

    def __init__(
        self, min_value: Optional[int] = None, max_value: Optional[int] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def _validate_value(self, value: Any, field_name: str) -> int:
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise validation_failed(field_name, value, "Must be a valid integer")

        if not isinstance(value, int) or isinstance(value, bool):
            raise validation_failed(field_name, value, "Must be an integer")

        if self.min_value is not None and value < self.min_value:
            raise validation_failed(
                field_name, value, f"Must be at least {self.min_value}"
            )

        if self.max_value is not None and value > self.max_value:
            raise validation_failed(
                field_name, value, f"Must be at most {self.max_value}"
            )

        return value


class BooleanValidator(Validator):
    """Validator for boolean values."""

    def _validate_value(self, value: Any, field_name: str) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ("true", "1", "yes", "on"):
                return True
            elif lower_value in ("false", "0", "no", "off"):
                return False

        if isinstance(value, int):
            if value in (0, 1):
                return bool(value)

        raise validation_failed(field_name, value, "Must be a boolean value")


class ListValidator(Validator):
    """Validator for list values."""

    def __init__(
        self,
        item_validator: Optional[Validator] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length

    def _validate_value(self, value: Any, field_name: str) -> List[Any]:
        if not isinstance(value, list):
            raise validation_failed(field_name, value, "Must be a list")

        if self.min_length is not None and len(value) < self.min_length:
            raise validation_failed(
                field_name, value, f"Must have at least {self.min_length} items"
            )

        if self.max_length is not None and len(value) > self.max_length:
            raise validation_failed(
                field_name, value, f"Must have at most {self.max_length} items"
            )

        if self.item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = self.item_validator.validate(
                        item, f"{field_name}[{i}]"
                    )
                    validated_items.append(validated_item)
                except InputValidationError as e:
                    raise validation_failed(
                        field_name, value, f"Invalid item at index {i}: {e.message}"
                    )
            return validated_items

        return value


class DictValidator(Validator):
    """Validator for dictionary values."""

    def __init__(
        self,
        key_validator: Optional[Validator] = None,
        value_validator: Optional[Validator] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.key_validator = key_validator
        self.value_validator = value_validator

    def _validate_value(self, value: Any, field_name: str) -> Dict[Any, Any]:
        if not isinstance(value, dict):
            raise validation_failed(field_name, value, "Must be a dictionary")

        validated_dict = {}
        for key, val in value.items():
            validated_key = key
            validated_val = val

            if self.key_validator:
                validated_key = self.key_validator.validate(key, f"{field_name}.key")

            if self.value_validator:
                validated_val = self.value_validator.validate(
                    val, f"{field_name}[{key}]"
                )

            validated_dict[validated_key] = validated_val

        return validated_dict


class PathValidator(Validator):
    """Validator for file/directory path values."""

    def __init__(
        self,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        allowed_extensions: Optional[List[str]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.must_exist = must_exist
        self.must_be_file = must_be_file
        self.must_be_dir = must_be_dir
        self.allowed_extensions = allowed_extensions

    def _validate_value(self, value: Any, field_name: str) -> Path:
        if not isinstance(value, (str, Path)):
            raise validation_failed(field_name, value, "Must be a string or Path")

        try:
            path = Path(value).expanduser().resolve()
        except Exception as e:
            raise validation_failed(field_name, value, f"Invalid path: {e}")

        if self.must_exist and not path.exists():
            raise validation_failed(field_name, value, "Path must exist")

        if self.must_be_file and path.exists() and not path.is_file():
            raise validation_failed(field_name, value, "Path must be a file")

        if self.must_be_dir and path.exists() and not path.is_dir():
            raise validation_failed(field_name, value, "Path must be a directory")

        if self.allowed_extensions and path.suffix not in self.allowed_extensions:
            raise validation_failed(
                field_name,
                value,
                f"File extension must be one of: {', '.join(self.allowed_extensions)}",
            )

        return path


class URLValidator(Validator):
    """Validator for URL values."""

    def __init__(self, allowed_schemes: Optional[List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_schemes = allowed_schemes or ["http", "https"]

    def _validate_value(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise validation_failed(field_name, value, "Must be a string")

        try:
            parsed = urlparse(value)
        except Exception as e:
            raise validation_failed(field_name, value, f"Invalid URL: {e}")

        if not parsed.scheme:
            raise validation_failed(field_name, value, "URL must have a scheme")

        if self.allowed_schemes and parsed.scheme not in self.allowed_schemes:
            raise validation_failed(
                field_name,
                value,
                f"URL scheme must be one of: {', '.join(self.allowed_schemes)}",
            )

        if not parsed.netloc:
            raise validation_failed(field_name, value, "URL must have a domain")

        return value


class JSONValidator(Validator):
    """Validator for JSON string values."""

    def _validate_value(self, value: Any, field_name: str) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise validation_failed(field_name, value, f"Invalid JSON: {e}")

        # If it's already parsed, assume it's valid
        return value


# Convenience validator functions


def validate_string(
    value: Any,
    field_name: str = "field",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[Union[str, Pattern]] = None,
    choices: Optional[List[str]] = None,
    required: bool = True,
) -> str:
    """Validate a string value."""
    validator = StringValidator(
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        choices=choices,
        required=required,
    )
    return validator.validate(value, field_name)


def validate_integer(
    value: Any,
    field_name: str = "field",
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    required: bool = True,
) -> int:
    """Validate an integer value."""
    validator = IntegerValidator(
        min_value=min_value, max_value=max_value, required=required
    )
    return validator.validate(value, field_name)


def validate_boolean(
    value: Any, field_name: str = "field", required: bool = True
) -> bool:
    """Validate a boolean value."""
    validator = BooleanValidator(required=required)
    return validator.validate(value, field_name)


def validate_list(
    value: Any,
    field_name: str = "field",
    item_validator: Optional[Validator] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    required: bool = True,
) -> List[Any]:
    """Validate a list value."""
    validator = ListValidator(
        item_validator=item_validator,
        min_length=min_length,
        max_length=max_length,
        required=required,
    )
    return validator.validate(value, field_name)


def validate_path(
    value: Any,
    field_name: str = "field",
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
    allowed_extensions: Optional[List[str]] = None,
    required: bool = True,
) -> Path:
    """Validate a path value."""
    validator = PathValidator(
        must_exist=must_exist,
        must_be_file=must_be_file,
        must_be_dir=must_be_dir,
        allowed_extensions=allowed_extensions,
        required=required,
    )
    return validator.validate(value, field_name)


def validate_url(
    value: Any,
    field_name: str = "field",
    allowed_schemes: Optional[List[str]] = None,
    required: bool = True,
) -> str:
    """Validate a URL value."""
    validator = URLValidator(allowed_schemes=allowed_schemes, required=required)
    return validator.validate(value, field_name)


def validate_json(value: Any, field_name: str = "field", required: bool = True) -> Any:
    """Validate a JSON value."""
    validator = JSONValidator(required=required)
    return validator.validate(value, field_name)


# Schema-based validation


def validate_schema(
    data: Dict[str, Any], schema: Dict[str, Validator]
) -> Dict[str, Any]:
    """Validate data against a schema of validators.

    Args:
        data: Data to validate
        schema: Dictionary mapping field names to validators

    Returns:
        Validated data dictionary

    Raises:
        InputValidationError: If validation fails
    """
    validated_data = {}

    # Validate provided fields
    for field_name, validator in schema.items():
        value = data.get(field_name)
        validated_data[field_name] = validator.validate(value, field_name)

    # Check for unexpected fields
    unexpected_fields = set(data.keys()) - set(schema.keys())
    if unexpected_fields:
        raise validation_failed(
            "schema", data, f"Unexpected fields: {', '.join(unexpected_fields)}"
        )

    return validated_data
