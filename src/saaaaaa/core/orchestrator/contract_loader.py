"""
JSON Contract Loader: Directory-based JSON configuration loader with validation.

This module implements a robust loader for JSON contract/configuration files with:
1. Path resolution and validation
2. Directory globbing for batch loading
3. Error aggregation for comprehensive reporting
4. Schema validation support
5. Deterministic loading order
"""

from __future__ import annotations

import glob
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class LoadError:
    """Represents an error that occurred during loading."""

    file_path: str
    error_type: str
    message: str
    line_number: int | None = None

    def __str__(self) -> str:
        """Format error for display."""
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        return f"{location}: {self.error_type}: {self.message}"

@dataclass
class LoadResult:
    """Result of a loading operation."""

    success: bool
    data: dict[str, Any] | None = None
    errors: list[LoadError] = field(default_factory=list)
    files_loaded: list[str] = field(default_factory=list)

    def add_error(self, file_path: str, error_type: str, message: str, line_number: int | None = None) -> None:
        """Add an error to the result."""
        self.errors.append(LoadError(file_path, error_type, message, line_number))

    def merge(self, other: LoadResult) -> None:
        """Merge another LoadResult into this one."""
        if other.data:
            if self.data is None:
                self.data = {}
            self.data.update(other.data)
        self.errors.extend(other.errors)
        self.files_loaded.extend(other.files_loaded)
        self.success = self.success and other.success

class JSONContractLoader:
    """
    Loader for JSON contract/configuration files with robust error handling.

    Features:
    - Path resolution with multiple search paths
    - Directory globbing for batch loading
    - Error aggregation for comprehensive reporting
    - Deterministic loading order (alphabetical)
    - Schema validation hooks
    """

    def __init__(
        self,
        base_paths: list[Path] | None = None,
        validate_schema: bool = False,
        schema_validator: callable | None = None,
    ) -> None:
        """
        Initialize the contract loader.

        Args:
            base_paths: List of base paths to search for files (default: [.])
            validate_schema: Whether to validate loaded JSON against schemas
            schema_validator: Optional function(data, file_path) -> Tuple[bool, Optional[str]]
        """
        self.base_paths = base_paths or [Path(".")]
        self.validate_schema = validate_schema
        self.schema_validator = schema_validator

        logger.debug(f"JSONContractLoader initialized with base_paths={self.base_paths}")

    def _resolve_path(self, path: str | Path) -> Path | None:
        """
        Resolve a path by searching through base paths.

        Args:
            path: Path to resolve (can be relative or absolute)

        Returns:
            Resolved Path object or None if not found
        """
        path = Path(path)

        # If absolute and exists, return it
        if path.is_absolute():
            return path if path.exists() else None

        # Search through base paths
        for base_path in self.base_paths:
            candidate = base_path / path
            if candidate.exists():
                return candidate.resolve()

        return None

    def _read_payload(self, file_path: Path) -> tuple[dict[str, Any] | None, LoadError | None]:
        """
        Read and parse JSON payload from a file.

        Args:
            file_path: Path to JSON file

        Returns:
            Tuple of (data, error) where one is always None
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            # Validate it's a dictionary
            if not isinstance(data, dict):
                return None, LoadError(
                    str(file_path),
                    "InvalidFormat",
                    f"Expected JSON object (dict), got {type(data).__name__}"
                )

            # Schema validation if enabled
            if self.validate_schema and self.schema_validator:
                is_valid, error_msg = self.schema_validator(data, str(file_path))
                if not is_valid:
                    return None, LoadError(
                        str(file_path),
                        "SchemaValidation",
                        error_msg or "Schema validation failed"
                    )

            return data, None

        except json.JSONDecodeError as e:
            return None, LoadError(
                str(file_path),
                "JSONDecodeError",
                str(e),
                e.lineno
            )
        except FileNotFoundError:
            return None, LoadError(
                str(file_path),
                "FileNotFound",
                "File does not exist"
            )
        except PermissionError:
            return None, LoadError(
                str(file_path),
                "PermissionError",
                "Permission denied"
            )
        except Exception as e:
            return None, LoadError(
                str(file_path),
                type(e).__name__,
                str(e)
            )

    def load_file(self, file_path: str | Path) -> LoadResult:
        """
        Load a single JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            LoadResult with data or errors
        """
        result = LoadResult(success=False)

        # Resolve path
        resolved_path = self._resolve_path(file_path)
        if resolved_path is None:
            result.add_error(
                str(file_path),
                "PathResolution",
                "Could not resolve path in any base directory"
            )
            return result

        # Validate it's a file
        if not resolved_path.is_file():
            result.add_error(
                str(resolved_path),
                "NotAFile",
                "Path exists but is not a file"
            )
            return result

        # Read payload
        data, error = self._read_payload(resolved_path)

        if error:
            result.errors.append(error)
            return result

        result.success = True
        result.data = data
        result.files_loaded.append(str(resolved_path))

        return result

    def load_directory(
        self,
        directory: str | Path,
        pattern: str = "*.json",
        recursive: bool = False,
        aggregate_errors: bool = True,
    ) -> LoadResult:
        """
        Load all JSON files from a directory with globbing support.

        Args:
            directory: Directory path to load from
            pattern: Glob pattern for matching files (default: *.json)
            recursive: Whether to search recursively (default: False)
            aggregate_errors: Whether to aggregate all errors or fail fast (default: True)

        Returns:
            LoadResult with aggregated data from all files or errors
        """
        result = LoadResult(success=True, data={})

        # Resolve directory path
        resolved_dir = self._resolve_path(directory)
        if resolved_dir is None:
            result.success = False
            result.add_error(
                str(directory),
                "PathResolution",
                "Could not resolve directory path"
            )
            return result

        # Validate it's a directory
        if not resolved_dir.is_dir():
            result.success = False
            result.add_error(
                str(resolved_dir),
                "NotADirectory",
                "Path exists but is not a directory"
            )
            return result

        # Build glob pattern
        if recursive:
            glob_pattern = str(resolved_dir / "**" / pattern)
        else:
            glob_pattern = str(resolved_dir / pattern)

        # Find matching files
        matching_files = glob.glob(glob_pattern, recursive=recursive)

        if not matching_files:
            logger.warning(f"No files matching pattern '{pattern}' found in {resolved_dir}")
            return result

        # Sort for deterministic ordering
        matching_files.sort()

        logger.info(f"Loading {len(matching_files)} files from {resolved_dir}")

        # Load each file
        for file_path in matching_files:
            file_result = self.load_file(file_path)

            if file_result.success and file_result.data:
                # Use filename (without extension) as key
                file_key = Path(file_path).stem

                # Check for key collisions
                if file_key in result.data:
                    result.add_error(
                        file_path,
                        "KeyCollision",
                        f"Key '{file_key}' already exists in loaded data"
                    )
                    if not aggregate_errors:
                        result.success = False
                        return result
                else:
                    result.data[file_key] = file_result.data
                    result.files_loaded.append(file_path)
            else:
                # Aggregate errors
                result.errors.extend(file_result.errors)

                if not aggregate_errors:
                    # Fail fast
                    result.success = False
                    return result

        # Mark as failed if any errors occurred
        if result.errors:
            result.success = False

        return result

    def load_multiple(
        self,
        paths: list[str | Path],
        aggregate_errors: bool = True,
    ) -> LoadResult:
        """
        Load multiple files or directories.

        Args:
            paths: List of file or directory paths
            aggregate_errors: Whether to aggregate errors or fail fast

        Returns:
            LoadResult with aggregated data and errors
        """
        result = LoadResult(success=True, data={})

        for path in paths:
            path_obj = Path(path)

            # Check if it's a directory
            resolved = self._resolve_path(path_obj)
            if resolved and resolved.is_dir():
                sub_result = self.load_directory(path, aggregate_errors=aggregate_errors)
            else:
                sub_result = self.load_file(path)

                # Wrap single file data with filename as key
                if sub_result.success and sub_result.data:
                    file_key = Path(path).stem
                    sub_result.data = {file_key: sub_result.data}

            result.merge(sub_result)

            if not aggregate_errors and not sub_result.success:
                return result

        return result

    def format_errors(self, result: LoadResult) -> str:
        """
        Format errors from a LoadResult for display.

        Args:
            result: LoadResult with errors

        Returns:
            Formatted error string
        """
        if not result.errors:
            return "No errors"

        lines = [f"Found {len(result.errors)} error(s):"]
        for error in result.errors:
            lines.append(f"  - {error}")

        return "\n".join(lines)

__all__ = [
    "LoadError",
    "LoadResult",
    "JSONContractLoader",
]
