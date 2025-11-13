"""Metrics Export Module.

Provides comprehensive metrics export for monitoring and observability.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def export_metrics(orchestrator: Any) -> dict[str, Any]:
    """Export all metrics for monitoring.
    
    Args:
        orchestrator: The Orchestrator instance to export metrics from
        
    Returns:
        Dictionary containing all system metrics
    """
    metrics = {
        'timestamp': datetime.utcnow().isoformat(),
        'phase_metrics': {},
        'resource_usage': {},
        'abort_status': {},
        'phase_status': {},
    }
    
    # Export phase metrics
    try:
        if hasattr(orchestrator, 'get_phase_metrics'):
            metrics['phase_metrics'] = orchestrator.get_phase_metrics()
    except Exception as e:
        logger.error(f"Failed to export phase metrics: {e}")
        metrics['phase_metrics'] = {'error': str(e)}
    
    # Export resource usage history
    try:
        if hasattr(orchestrator, 'resource_limits') and hasattr(
            orchestrator.resource_limits, 'get_usage_history'
        ):
            metrics['resource_usage'] = orchestrator.resource_limits.get_usage_history()
    except Exception as e:
        logger.error(f"Failed to export resource usage: {e}")
        metrics['resource_usage'] = {'error': str(e)}
    
    # Export abort status
    try:
        if hasattr(orchestrator, 'abort_signal'):
            abort_signal = orchestrator.abort_signal
            metrics['abort_status'] = {
                'is_aborted': abort_signal.is_aborted(),
                'reason': abort_signal.get_reason() if hasattr(abort_signal, 'get_reason') else None,
                'timestamp': (
                    abort_signal.get_timestamp().isoformat()
                    if hasattr(abort_signal, 'get_timestamp') and abort_signal.get_timestamp()
                    else None
                ),
            }
    except Exception as e:
        logger.error(f"Failed to export abort status: {e}")
        metrics['abort_status'] = {'error': str(e)}
    
    # Export phase status
    try:
        if hasattr(orchestrator, '_phase_status'):
            metrics['phase_status'] = dict(orchestrator._phase_status)
    except Exception as e:
        logger.error(f"Failed to export phase status: {e}")
        metrics['phase_status'] = {'error': str(e)}
    
    return metrics
