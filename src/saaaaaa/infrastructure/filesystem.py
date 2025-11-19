"""
File system adapter - Concrete implementation of FilePort.

Provides real file system access using pathlib.Path.
For testing, use InMemoryFileAdapter instead.
"""

import json
from pathlib import Path
from typing import Any


class LocalFileAdapter:
    """Real file system adapter using pathlib.

    Example:
        >>> file_port = LocalFileAdapter()
        >>> content = file_port.read_text("data/plan.txt")
        >>> file_port.write_text("output/result.txt", content)
    """

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text from a file."""
        return Path(path).read_text(encoding=encoding)

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write text to a file."""
        Path(path).write_text(content, encoding=encoding)

    def read_bytes(self, path: str) -> bytes:
        """Read bytes from a file."""
        return Path(path).read_bytes()

    def write_bytes(self, path: str, content: bytes) -> None:
        """Write bytes to a file."""
        Path(path).write_bytes(content)

    def exists(self, path: str) -> bool:
        """Check if a file or directory exists."""
        return Path(path).exists()

    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

class JsonAdapter:
    """JSON serialization adapter.

    Example:
        >>> json_port = JsonAdapter()
        >>> data = json_port.loads('{"key": "value"}')
        >>> text = json_port.dumps(data, indent=2)
    """

    def loads(self, text: str) -> Any:
        """Parse JSON from string."""
        return json.loads(text)

    def dumps(self, obj: Any, indent: int | None = None) -> str:
        """Serialize object to JSON string."""
        if indent is not None:
            return json.dumps(obj, indent=indent, ensure_ascii=False, default=str)
        return json.dumps(obj, ensure_ascii=False, default=str)

class InMemoryFileAdapter:
    """In-memory file adapter for testing.

    Stores files in a dictionary instead of disk.

    Example:
        >>> file_port = InMemoryFileAdapter()
        >>> file_port.write_text("test.txt", "content")
        >>> content = file_port.read_text("test.txt")
        >>> assert content == "content"
    """

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}
        self._dirs: set[str] = set()

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text from in-memory storage."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path].decode(encoding)

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write text to in-memory storage."""
        self._files[path] = content.encode(encoding)

    def read_bytes(self, path: str) -> bytes:
        """Read bytes from in-memory storage."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]

    def write_bytes(self, path: str, content: bytes) -> None:
        """Write bytes to in-memory storage."""
        self._files[path] = content

    def exists(self, path: str) -> bool:
        """Check if a file or directory exists in memory."""
        return path in self._files or path in self._dirs

    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory in memory."""
        if path in self._dirs and not exist_ok:
            raise FileExistsError(f"Directory already exists: {path}")
        self._dirs.add(path)

        if parents:
            # Add all parent directories
            parts = Path(path).parts
            for i in range(1, len(parts) + 1):
                parent = str(Path(*parts[:i]))
                self._dirs.add(parent)

__all__ = [
    'LocalFileAdapter',
    'JsonAdapter',
    'InMemoryFileAdapter',
]
