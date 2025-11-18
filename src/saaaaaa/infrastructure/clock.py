"""
Clock adapter - Concrete implementation of ClockPort.

Provides access to current time.
For testing, use FrozenClockAdapter instead.
"""

from datetime import datetime, timezone


class SystemClockAdapter:
    """Real clock adapter using datetime.now().

    Example:
        >>> clock_port = SystemClockAdapter()
        >>> now = clock_port.now()
        >>> utc_now = clock_port.utcnow()
    """

    def now(self) -> datetime:
        """Get current datetime."""
        return datetime.now()

    def utcnow(self) -> datetime:
        """Get current UTC datetime."""
        return datetime.now(timezone.utc)

class FrozenClockAdapter:
    """Frozen clock adapter for testing.

    Returns a fixed time that can be updated manually.

    Example:
        >>> clock_port = FrozenClockAdapter(datetime(2024, 1, 1, 12, 0, 0))
        >>> assert clock_port.now() == datetime(2024, 1, 1, 12, 0, 0)
        >>> clock_port.advance(hours=1)
        >>> assert clock_port.now() == datetime(2024, 1, 1, 13, 0, 0)
    """

    def __init__(self, frozen_time: datetime | None = None) -> None:
        self._frozen_time = frozen_time or datetime.now()

    def now(self) -> datetime:
        """Get frozen datetime."""
        return self._frozen_time

    def utcnow(self) -> datetime:
        """Get frozen UTC datetime."""
        # If frozen_time is naive, assume it's UTC
        if self._frozen_time.tzinfo is None:
            return self._frozen_time.replace(tzinfo=timezone.utc)
        return self._frozen_time.astimezone(timezone.utc)

    def set_time(self, new_time: datetime) -> None:
        """Set the frozen time (for testing)."""
        self._frozen_time = new_time

    def advance(self, **kwargs: int) -> None:
        """Advance the frozen time by a timedelta (for testing).

        Args:
            **kwargs: Arguments to timedelta (days, hours, minutes, seconds, etc.)
        """
        from datetime import timedelta
        self._frozen_time += timedelta(**kwargs)

__all__ = [
    'SystemClockAdapter',
    'FrozenClockAdapter',
]
