"""Resource Pressure Alerting and Observability.

Provides comprehensive alerting and monitoring for resource management:
- Structured logging for resource events
- Alert thresholds and notifications
- Integration with external monitoring systems
- Historical trend analysis
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from farfan_pipeline.core.orchestrator.resource_manager import (
    ResourcePressureEvent,
    ResourcePressureLevel,
)

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels."""
    
    LOG = "log"
    WEBHOOK = "webhook"
    SIGNAL = "signal"
    STDOUT = "stdout"


class ResourceAlert:
    """Individual resource alert."""
    
    def __init__(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        event: ResourcePressureEvent,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.severity = severity
        self.title = title
        self.message = message
        self.event = event
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.alert_id = f"alert_{self.timestamp.isoformat()}_{id(self)}"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "event": {
                "timestamp": self.event.timestamp.isoformat(),
                "pressure_level": self.event.pressure_level.value,
                "cpu_percent": self.event.cpu_percent,
                "memory_mb": self.event.memory_mb,
                "memory_percent": self.event.memory_percent,
                "worker_count": self.event.worker_count,
                "active_executors": self.event.active_executors,
                "degradation_applied": self.event.degradation_applied,
                "circuit_breakers_open": self.event.circuit_breakers_open,
            },
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert alert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AlertThresholds:
    """Configurable alert thresholds."""
    
    def __init__(
        self,
        memory_warning_percent: float = 75.0,
        memory_critical_percent: float = 85.0,
        cpu_warning_percent: float = 75.0,
        cpu_critical_percent: float = 85.0,
        circuit_breaker_warning_count: int = 3,
        degradation_critical_count: int = 3,
    ) -> None:
        self.memory_warning_percent = memory_warning_percent
        self.memory_critical_percent = memory_critical_percent
        self.cpu_warning_percent = cpu_warning_percent
        self.cpu_critical_percent = cpu_critical_percent
        self.circuit_breaker_warning_count = circuit_breaker_warning_count
        self.degradation_critical_count = degradation_critical_count


class ResourceAlertManager:
    """Manages resource pressure alerts and notifications."""
    
    def __init__(
        self,
        thresholds: AlertThresholds | None = None,
        channels: list[AlertChannel] | None = None,
        webhook_url: str | None = None,
        signal_callback: Callable[[ResourceAlert], None] | None = None,
    ) -> None:
        self.thresholds = thresholds or AlertThresholds()
        self.channels = channels or [AlertChannel.LOG]
        self.webhook_url = webhook_url
        self.signal_callback = signal_callback
        
        self.alert_history: list[ResourceAlert] = []
        self.alert_counts: dict[str, int] = defaultdict(int)
        self.suppressed_alerts: set[str] = set()
        self.last_alert_times: dict[str, datetime] = {}
    
    def process_event(self, event: ResourcePressureEvent) -> list[ResourceAlert]:
        """Process resource pressure event and generate alerts."""
        alerts: list[ResourceAlert] = []
        
        memory_alert = self._check_memory_threshold(event)
        if memory_alert:
            alerts.append(memory_alert)
        
        cpu_alert = self._check_cpu_threshold(event)
        if cpu_alert:
            alerts.append(cpu_alert)
        
        pressure_alert = self._check_pressure_level(event)
        if pressure_alert:
            alerts.append(pressure_alert)
        
        circuit_breaker_alert = self._check_circuit_breakers(event)
        if circuit_breaker_alert:
            alerts.append(circuit_breaker_alert)
        
        degradation_alert = self._check_degradation(event)
        if degradation_alert:
            alerts.append(degradation_alert)
        
        for alert in alerts:
            self._dispatch_alert(alert)
            self.alert_history.append(alert)
            self.alert_counts[alert.severity.value] += 1
        
        return alerts
    
    def _check_memory_threshold(
        self, event: ResourcePressureEvent
    ) -> ResourceAlert | None:
        """Check if memory usage exceeds thresholds."""
        if event.memory_percent >= self.thresholds.memory_critical_percent:
            return ResourceAlert(
                severity=AlertSeverity.CRITICAL,
                title="Critical Memory Usage",
                message=f"Memory usage at {event.memory_percent:.1f}% "
                f"({event.memory_mb:.1f} MB)",
                event=event,
                metadata={"threshold": self.thresholds.memory_critical_percent},
            )
        
        if event.memory_percent >= self.thresholds.memory_warning_percent:
            if self._should_alert("memory_warning", minutes=5):
                return ResourceAlert(
                    severity=AlertSeverity.WARNING,
                    title="High Memory Usage",
                    message=f"Memory usage at {event.memory_percent:.1f}% "
                    f"({event.memory_mb:.1f} MB)",
                    event=event,
                    metadata={"threshold": self.thresholds.memory_warning_percent},
                )
        
        return None
    
    def _check_cpu_threshold(
        self, event: ResourcePressureEvent
    ) -> ResourceAlert | None:
        """Check if CPU usage exceeds thresholds."""
        if event.cpu_percent >= self.thresholds.cpu_critical_percent:
            return ResourceAlert(
                severity=AlertSeverity.CRITICAL,
                title="Critical CPU Usage",
                message=f"CPU usage at {event.cpu_percent:.1f}%",
                event=event,
                metadata={"threshold": self.thresholds.cpu_critical_percent},
            )
        
        if event.cpu_percent >= self.thresholds.cpu_warning_percent:
            if self._should_alert("cpu_warning", minutes=5):
                return ResourceAlert(
                    severity=AlertSeverity.WARNING,
                    title="High CPU Usage",
                    message=f"CPU usage at {event.cpu_percent:.1f}%",
                    event=event,
                    metadata={"threshold": self.thresholds.cpu_warning_percent},
                )
        
        return None
    
    def _check_pressure_level(
        self, event: ResourcePressureEvent
    ) -> ResourceAlert | None:
        """Check if pressure level warrants alert."""
        if event.pressure_level == ResourcePressureLevel.EMERGENCY:
            return ResourceAlert(
                severity=AlertSeverity.CRITICAL,
                title="Emergency Resource Pressure",
                message="System under emergency resource pressure",
                event=event,
            )
        
        if event.pressure_level == ResourcePressureLevel.CRITICAL:
            if self._should_alert("pressure_critical", minutes=2):
                return ResourceAlert(
                    severity=AlertSeverity.ERROR,
                    title="Critical Resource Pressure",
                    message="System under critical resource pressure",
                    event=event,
                )
        
        if event.pressure_level == ResourcePressureLevel.HIGH:
            if self._should_alert("pressure_high", minutes=10):
                return ResourceAlert(
                    severity=AlertSeverity.WARNING,
                    title="High Resource Pressure",
                    message="System experiencing high resource pressure",
                    event=event,
                )
        
        return None
    
    def _check_circuit_breakers(
        self, event: ResourcePressureEvent
    ) -> ResourceAlert | None:
        """Check if circuit breakers warrant alert."""
        open_count = len(event.circuit_breakers_open)
        
        if open_count >= self.thresholds.circuit_breaker_warning_count:
            return ResourceAlert(
                severity=AlertSeverity.ERROR,
                title="Multiple Circuit Breakers Open",
                message=f"{open_count} circuit breakers are open: "
                f"{', '.join(event.circuit_breakers_open)}",
                event=event,
                metadata={
                    "open_count": open_count,
                    "executors": event.circuit_breakers_open,
                },
            )
        
        if open_count > 0:
            if self._should_alert("circuit_breaker", minutes=5):
                return ResourceAlert(
                    severity=AlertSeverity.WARNING,
                    title="Circuit Breaker Opened",
                    message=f"Circuit breakers open for: "
                    f"{', '.join(event.circuit_breakers_open)}",
                    event=event,
                    metadata={"executors": event.circuit_breakers_open},
                )
        
        return None
    
    def _check_degradation(
        self, event: ResourcePressureEvent
    ) -> ResourceAlert | None:
        """Check if degradation strategies warrant alert."""
        degradation_count = len(event.degradation_applied)
        
        if degradation_count >= self.thresholds.degradation_critical_count:
            return ResourceAlert(
                severity=AlertSeverity.ERROR,
                title="Multiple Degradation Strategies Active",
                message=f"{degradation_count} degradation strategies applied: "
                f"{', '.join(event.degradation_applied)}",
                event=event,
                metadata={
                    "count": degradation_count,
                    "strategies": event.degradation_applied,
                },
            )
        
        if degradation_count > 0:
            if self._should_alert("degradation", minutes=10):
                return ResourceAlert(
                    severity=AlertSeverity.INFO,
                    title="Degradation Strategies Active",
                    message=f"Active degradation: "
                    f"{', '.join(event.degradation_applied)}",
                    event=event,
                    metadata={"strategies": event.degradation_applied},
                )
        
        return None
    
    def _should_alert(self, alert_type: str, minutes: int = 5) -> bool:
        """Check if alert should be sent (with rate limiting)."""
        now = datetime.utcnow()
        last_time = self.last_alert_times.get(alert_type)
        
        if not last_time:
            self.last_alert_times[alert_type] = now
            return True
        
        elapsed = (now - last_time).total_seconds() / 60
        if elapsed >= minutes:
            self.last_alert_times[alert_type] = now
            return True
        
        return False
    
    def _dispatch_alert(self, alert: ResourceAlert) -> None:
        """Dispatch alert to configured channels."""
        for channel in self.channels:
            try:
                if channel == AlertChannel.LOG:
                    self._log_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook(alert)
                elif channel == AlertChannel.SIGNAL:
                    self._send_signal(alert)
                elif channel == AlertChannel.STDOUT:
                    self._print_alert(alert)
            except Exception as exc:
                logger.error(
                    f"Failed to dispatch alert to {channel.value}: {exc}"
                )
    
    def _log_alert(self, alert: ResourceAlert) -> None:
        """Log alert with appropriate severity."""
        extra = {
            "alert_id": alert.alert_id,
            "alert_severity": alert.severity.value,
            "pressure_level": alert.event.pressure_level.value,
            "cpu_percent": alert.event.cpu_percent,
            "memory_mb": alert.event.memory_mb,
        }
        
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(f"{alert.title}: {alert.message}", extra=extra)
        elif alert.severity == AlertSeverity.ERROR:
            logger.error(f"{alert.title}: {alert.message}", extra=extra)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(f"{alert.title}: {alert.message}", extra=extra)
        else:
            logger.info(f"{alert.title}: {alert.message}", extra=extra)
    
    def _send_webhook(self, alert: ResourceAlert) -> None:
        """Send alert via webhook."""
        if not self.webhook_url:
            return
        
        try:
            import requests
            
            requests.post(
                self.webhook_url,
                json=alert.to_dict(),
                timeout=5,
            )
        except Exception as exc:
            logger.error(f"Webhook alert failed: {exc}")
    
    def _send_signal(self, alert: ResourceAlert) -> None:
        """Send alert via signal callback."""
        if not self.signal_callback:
            return
        
        try:
            self.signal_callback(alert)
        except Exception as exc:
            logger.error(f"Signal callback failed: {exc}")
    
    def _print_alert(self, alert: ResourceAlert) -> None:
        """Print alert to stdout."""
        severity_colors = {
            AlertSeverity.INFO: "\033[94m",
            AlertSeverity.WARNING: "\033[93m",
            AlertSeverity.ERROR: "\033[91m",
            AlertSeverity.CRITICAL: "\033[95m",
        }
        reset = "\033[0m"
        
        color = severity_colors.get(alert.severity, reset)
        print(
            f"{color}[{alert.severity.value.upper()}] {alert.title}: "
            f"{alert.message}{reset}"
        )
    
    def get_alert_summary(self) -> dict[str, Any]:
        """Get summary of alert history."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_alerts = [
            alert for alert in self.alert_history if alert.timestamp >= hour_ago
        ]
        
        daily_alerts = [
            alert for alert in self.alert_history if alert.timestamp >= day_ago
        ]
        
        return {
            "total_alerts": len(self.alert_history),
            "last_hour": len(recent_alerts),
            "last_24_hours": len(daily_alerts),
            "by_severity": dict(self.alert_counts),
            "recent_alerts": [alert.to_dict() for alert in recent_alerts[-10:]],
        }
    
    def clear_history(self) -> None:
        """Clear alert history."""
        self.alert_history.clear()
        self.alert_counts.clear()
        self.last_alert_times.clear()
