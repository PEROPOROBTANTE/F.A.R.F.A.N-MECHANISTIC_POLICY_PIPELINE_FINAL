"""
Environment adapter - Concrete implementation of EnvPort.

Provides access to environment variables with type conversion.
For testing, use InMemoryEnvAdapter instead.
"""

import os


class SystemEnvAdapter:
    """Real environment adapter using os.environ.

    Example:
        >>> env_port = SystemEnvAdapter()
        >>> api_key = env_port.get_required("API_KEY")
        >>> debug = env_port.get_bool("DEBUG", default=False)
    """

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get environment variable."""
        return os.environ.get(key, default)

    def get_required(self, key: str) -> str:
        """Get required environment variable."""
        value = os.environ.get(key)
        if value is None:
            raise ValueError(f"Required environment variable not set: {key}")
        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = os.environ.get(key)
        if value is None:
            return default

        value_lower = value.lower()
        if value_lower in ('true', 'yes', '1', 'on'):
            return True
        elif value_lower in ('false', 'no', '0', 'off'):
            return False
        else:
            return default

class InMemoryEnvAdapter:
    """In-memory environment adapter for testing.

    Stores environment variables in a dictionary instead of os.environ.

    Example:
        >>> env_port = InMemoryEnvAdapter()
        >>> env_port.set("DEBUG", "true")
        >>> assert env_port.get_bool("DEBUG") is True
    """

    def __init__(self, initial_env: dict[str, str] | None = None) -> None:
        self._env = initial_env.copy() if initial_env else {}

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get environment variable."""
        return self._env.get(key, default)

    def get_required(self, key: str) -> str:
        """Get required environment variable."""
        value = self._env.get(key)
        if value is None:
            raise ValueError(f"Required environment variable not set: {key}")
        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = self._env.get(key)
        if value is None:
            return default

        value_lower = value.lower()
        if value_lower in ('true', 'yes', '1', 'on'):
            return True
        elif value_lower in ('false', 'no', '0', 'off'):
            return False
        else:
            return default

    def set(self, key: str, value: str) -> None:
        """Set environment variable (for testing)."""
        self._env[key] = value

    def clear(self) -> None:
        """Clear all environment variables (for testing)."""
        self._env.clear()

__all__ = [
    'SystemEnvAdapter',
    'InMemoryEnvAdapter',
]
