"""System Health Check Module.

Provides comprehensive health status for all system components.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def get_system_health(orchestrator: Any) -> dict[str, Any]:
    """
    Comprehensive system health check.
    
    Args:
        orchestrator: The Orchestrator instance to check health for
        
    Returns:
        Health status with component checks
    """
    health = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {}
    }
    
    # Check method executor
    try:
        if hasattr(orchestrator, 'executor'):
            executor_health = {
                'instances_loaded': len(orchestrator.executor.instances),
                'calibrations_loaded': len(orchestrator.executor.calibrations),
                'status': 'healthy'
            }
            health['components']['method_executor'] = executor_health
        else:
            health['components']['method_executor'] = {
                'status': 'unavailable',
                'error': 'No executor attribute found'
            }
    except Exception as e:
        health['status'] = 'unhealthy'
        health['components']['method_executor'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Check questionnaire provider
    try:
        from saaaaaa.core.orchestrator import get_questionnaire_provider
        provider = get_questionnaire_provider()
        questionnaire_health = {
            'has_data': provider.has_data(),
            'status': 'healthy' if provider.has_data() else 'unhealthy'
        }
        health['components']['questionnaire_provider'] = questionnaire_health
        
        if not provider.has_data():
            health['status'] = 'degraded'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['components']['questionnaire_provider'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Check resource limits
    try:
        if hasattr(orchestrator, 'resource_limits'):
            usage = orchestrator.resource_limits.get_resource_usage()
            resource_health = {
                'cpu_percent': usage.get('cpu_percent', 0),
                'memory_mb': usage.get('rss_mb', 0),
                'worker_budget': usage.get('worker_budget', 0),
                'status': 'healthy'
            }
            
            # Warning thresholds
            if usage.get('cpu_percent', 0) > 80:
                resource_health['status'] = 'degraded'
                health['status'] = 'degraded'
            
            if usage.get('rss_mb', 0) > 3500:  # Near 4GB limit
                resource_health['status'] = 'degraded'
                health['status'] = 'degraded'
            
            health['components']['resources'] = resource_health
        else:
            health['components']['resources'] = {
                'status': 'unavailable',
                'error': 'No resource_limits attribute found'
            }
    except Exception as e:
        health['status'] = 'unhealthy'
        health['components']['resources'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    return health
