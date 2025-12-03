"""Resource Management Integration.

Factory functions and helpers to integrate adaptive resource management
with the existing orchestrator infrastructure.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.core import MethodExecutor, Orchestrator, ResourceLimits

from farfan_pipeline.core.orchestrator.resource_alerts import (
    AlertChannel,
    AlertThresholds,
    ResourceAlertManager,
)
from farfan_pipeline.core.orchestrator.resource_aware_executor import ResourceAwareExecutor
from farfan_pipeline.core.orchestrator.resource_manager import (
    AdaptiveResourceManager,
    ExecutorPriority,
    ResourceAllocationPolicy,
)

logger = logging.getLogger(__name__)


def create_resource_manager(
    resource_limits: ResourceLimits,
    enable_circuit_breakers: bool = True,
    enable_degradation: bool = True,
    enable_alerts: bool = True,
    alert_channels: list[AlertChannel] | None = None,
    alert_webhook_url: str | None = None,
) -> tuple[AdaptiveResourceManager, ResourceAlertManager | None]:
    """Create and configure adaptive resource manager with alerts.
    
    Args:
        resource_limits: Existing ResourceLimits instance
        enable_circuit_breakers: Enable circuit breaker protection
        enable_degradation: Enable graceful degradation
        enable_alerts: Enable alerting system
        alert_channels: Alert delivery channels
        alert_webhook_url: Webhook URL for external alerts
        
    Returns:
        Tuple of (AdaptiveResourceManager, ResourceAlertManager)
    """
    alert_manager = None
    
    if enable_alerts:
        thresholds = AlertThresholds(
            memory_warning_percent=75.0,
            memory_critical_percent=85.0,
            cpu_warning_percent=75.0,
            cpu_critical_percent=85.0,
            circuit_breaker_warning_count=3,
            degradation_critical_count=3,
        )
        
        alert_manager = ResourceAlertManager(
            thresholds=thresholds,
            channels=alert_channels or [AlertChannel.LOG],
            webhook_url=alert_webhook_url,
        )
        
        alert_callback = alert_manager.process_event
    else:
        alert_callback = None
    
    resource_manager = AdaptiveResourceManager(
        resource_limits=resource_limits,
        enable_circuit_breakers=enable_circuit_breakers,
        enable_degradation=enable_degradation,
        alert_callback=alert_callback,
    )
    
    register_default_policies(resource_manager)
    
    logger.info(
        "Resource management system initialized",
        extra={
            "circuit_breakers": enable_circuit_breakers,
            "degradation": enable_degradation,
            "alerts": enable_alerts,
        },
    )
    
    return resource_manager, alert_manager


def register_default_policies(
    resource_manager: AdaptiveResourceManager,
) -> None:
    """Register default resource allocation policies for critical executors."""
    policies = [
        ResourceAllocationPolicy(
            executor_id="D3-Q3",
            priority=ExecutorPriority.CRITICAL,
            min_memory_mb=256.0,
            max_memory_mb=1024.0,
            min_workers=2,
            max_workers=8,
            is_memory_intensive=True,
        ),
        ResourceAllocationPolicy(
            executor_id="D4-Q2",
            priority=ExecutorPriority.CRITICAL,
            min_memory_mb=256.0,
            max_memory_mb=1024.0,
            min_workers=2,
            max_workers=8,
            is_memory_intensive=True,
        ),
        ResourceAllocationPolicy(
            executor_id="D3-Q2",
            priority=ExecutorPriority.HIGH,
            min_memory_mb=128.0,
            max_memory_mb=512.0,
            min_workers=1,
            max_workers=6,
        ),
        ResourceAllocationPolicy(
            executor_id="D4-Q1",
            priority=ExecutorPriority.HIGH,
            min_memory_mb=128.0,
            max_memory_mb=512.0,
            min_workers=1,
            max_workers=6,
        ),
        ResourceAllocationPolicy(
            executor_id="D2-Q3",
            priority=ExecutorPriority.HIGH,
            min_memory_mb=128.0,
            max_memory_mb=512.0,
            min_workers=1,
            max_workers=6,
            is_cpu_intensive=True,
        ),
        ResourceAllocationPolicy(
            executor_id="D1-Q1",
            priority=ExecutorPriority.NORMAL,
            min_memory_mb=64.0,
            max_memory_mb=256.0,
            min_workers=1,
            max_workers=4,
        ),
        ResourceAllocationPolicy(
            executor_id="D1-Q2",
            priority=ExecutorPriority.NORMAL,
            min_memory_mb=64.0,
            max_memory_mb=256.0,
            min_workers=1,
            max_workers=4,
        ),
        ResourceAllocationPolicy(
            executor_id="D5-Q1",
            priority=ExecutorPriority.NORMAL,
            min_memory_mb=128.0,
            max_memory_mb=384.0,
            min_workers=1,
            max_workers=4,
        ),
        ResourceAllocationPolicy(
            executor_id="D6-Q1",
            priority=ExecutorPriority.NORMAL,
            min_memory_mb=128.0,
            max_memory_mb=384.0,
            min_workers=1,
            max_workers=4,
        ),
    ]
    
    for policy in policies:
        resource_manager.register_allocation_policy(policy)


def wrap_method_executor(
    method_executor: MethodExecutor,
    resource_manager: AdaptiveResourceManager,
) -> ResourceAwareExecutor:
    """Wrap MethodExecutor with resource management.
    
    Args:
        method_executor: Existing MethodExecutor instance
        resource_manager: Configured AdaptiveResourceManager
        
    Returns:
        ResourceAwareExecutor wrapping the method executor
    """
    return ResourceAwareExecutor(
        method_executor=method_executor,
        resource_manager=resource_manager,
    )


def integrate_with_orchestrator(
    orchestrator: Orchestrator,
    enable_circuit_breakers: bool = True,
    enable_degradation: bool = True,
    enable_alerts: bool = True,
) -> dict[str, Any]:
    """Integrate resource management with existing Orchestrator.
    
    Args:
        orchestrator: Existing Orchestrator instance
        enable_circuit_breakers: Enable circuit breaker protection
        enable_degradation: Enable graceful degradation
        enable_alerts: Enable alerting system
        
    Returns:
        Dictionary with resource management components
    """
    if not hasattr(orchestrator, "resource_limits"):
        raise RuntimeError(
            "Orchestrator must have resource_limits attribute"
        )
    
    resource_manager, alert_manager = create_resource_manager(
        resource_limits=orchestrator.resource_limits,
        enable_circuit_breakers=enable_circuit_breakers,
        enable_degradation=enable_degradation,
        enable_alerts=enable_alerts,
    )
    
    setattr(orchestrator, "_resource_manager", resource_manager)
    setattr(orchestrator, "_alert_manager", alert_manager)
    
    logger.info("Resource management integrated with orchestrator")
    
    return {
        "resource_manager": resource_manager,
        "alert_manager": alert_manager,
        "resource_limits": orchestrator.resource_limits,
    }


def get_resource_status(orchestrator: Orchestrator) -> dict[str, Any]:
    """Get comprehensive resource management status from orchestrator.
    
    Args:
        orchestrator: Orchestrator with integrated resource management
        
    Returns:
        Complete resource management status
    """
    status: dict[str, Any] = {
        "resource_management_enabled": False,
        "resource_limits": {},
        "resource_manager": {},
        "alerts": {},
    }
    
    if hasattr(orchestrator, "resource_limits"):
        status["resource_limits"] = {
            "max_memory_mb": orchestrator.resource_limits.max_memory_mb,
            "max_cpu_percent": orchestrator.resource_limits.max_cpu_percent,
            "max_workers": orchestrator.resource_limits.max_workers,
            "current_usage": orchestrator.resource_limits.get_resource_usage(),
        }
    
    if hasattr(orchestrator, "_resource_manager"):
        status["resource_management_enabled"] = True
        status["resource_manager"] = (
            orchestrator._resource_manager.get_resource_status()
        )
    
    if hasattr(orchestrator, "_alert_manager") and orchestrator._alert_manager:
        status["alerts"] = orchestrator._alert_manager.get_alert_summary()
    
    return status


def reset_circuit_breakers(orchestrator: Orchestrator) -> dict[str, bool]:
    """Reset all circuit breakers in orchestrator.
    
    Args:
        orchestrator: Orchestrator with integrated resource management
        
    Returns:
        Dictionary mapping executor_id to reset success status
    """
    if not hasattr(orchestrator, "_resource_manager"):
        return {}
    
    resource_manager = orchestrator._resource_manager
    results = {}
    
    for executor_id in resource_manager.circuit_breakers:
        success = resource_manager.reset_circuit_breaker(executor_id)
        results[executor_id] = success
        
        if success:
            logger.info(f"Reset circuit breaker for {executor_id}")
    
    return results
