"""Infrastructure package - Adapters for ports.

This package contains concrete implementations of port interfaces.
Adapters handle external dependencies like file systems, databases, and APIs.

Structure:
- filesystem.py: File system operations
- environment.py: Environment variable access
- clock.py: Time operations
- log_adapters.py: Logging operations (renamed from logging.py to avoid shadowing)
"""

__all__ = []
