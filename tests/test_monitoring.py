"""Tests for system health and metrics monitoring."""

import pytest

# Add src to path for imports
import sys
from pathlib import Path

# Suppress warnings about missing dependencies
import warnings
warnings.filterwarnings("ignore")

from saaaaaa.core.orchestrator.core import Orchestrator


def test_get_system_health():
    """Test that get_system_health returns proper structure."""
    orc = Orchestrator()
    health = orc.get_system_health()
    
    # Check top-level structure
    assert 'status' in health
    assert health['status'] in ['healthy', 'degraded', 'unhealthy']
    assert 'timestamp' in health
    assert 'components' in health
    assert isinstance(health['components'], dict)


def test_get_system_health_components():
    """Test that health check includes expected components."""
    orc = Orchestrator()
    health = orc.get_system_health()
    
    # Should check method_executor
    assert 'method_executor' in health['components']
    executor_health = health['components']['method_executor']
    assert 'status' in executor_health
    
    # Should check resources
    assert 'resources' in health['components']
    resources_health = health['components']['resources']
    assert 'status' in resources_health
    assert 'cpu_percent' in resources_health
    assert 'memory_mb' in resources_health


def test_export_metrics():
    """Test that export_metrics returns proper structure."""
    orc = Orchestrator()
    metrics = orc.export_metrics()
    
    # Check top-level structure
    assert 'timestamp' in metrics
    assert 'phase_metrics' in metrics
    assert 'resource_usage' in metrics
    assert 'abort_status' in metrics
    assert 'phase_status' in metrics


def test_export_metrics_abort_status():
    """Test abort status in metrics export."""
    orc = Orchestrator()
    metrics = orc.export_metrics()
    
    # Check abort status structure
    abort = metrics['abort_status']
    assert 'is_aborted' in abort
    assert 'reason' in abort
    assert 'timestamp' in abort
    
    # Initially not aborted
    assert abort['is_aborted'] is False
    assert abort['reason'] is None
    assert abort['timestamp'] is None


def test_export_metrics_phase_status():
    """Test phase status in metrics export."""
    orc = Orchestrator()
    metrics = orc.export_metrics()
    
    # Check phase status
    phase_status = metrics['phase_status']
    assert isinstance(phase_status, dict)
    
    # Should have entries for all 11 phases
    assert len(phase_status) == 11
    
    # All should start as not_started
    for phase_id, status in phase_status.items():
        assert status == 'not_started'


def test_health_check_backward_compatibility():
    """Test that old health_check method still works."""
    orc = Orchestrator()
    health = orc.health_check()
    
    # Should have legacy format
    assert 'score' in health
    assert 'resource_usage' in health
    assert 'abort' in health
    
    # Score should be a number between 0 and 100
    assert isinstance(health['score'], (int, float))
    assert 0 <= health['score'] <= 100


def test_system_health_with_abort():
    """Test system health when abort is triggered."""
    orc = Orchestrator()
    
    # Trigger abort
    orc.request_abort("Test abort")
    
    health = orc.get_system_health()
    
    # Status should be unhealthy when aborted
    assert health['status'] == 'unhealthy'
    assert 'abort_reason' in health
    assert health['abort_reason'] == "Test abort"


def test_export_metrics_with_abort():
    """Test metrics export with abort triggered."""
    orc = Orchestrator()
    
    # Trigger abort
    orc.request_abort("Test abort for metrics")
    
    metrics = orc.export_metrics()
    
    # Abort status should reflect the abort
    abort = metrics['abort_status']
    assert abort['is_aborted'] is True
    assert abort['reason'] == "Test abort for metrics"
    assert abort['timestamp'] is not None


def test_get_system_health_multiple_calls():
    """Test that health check can be called multiple times."""
    orc = Orchestrator()
    
    health1 = orc.get_system_health()
    health2 = orc.get_system_health()
    
    # Should return consistent structure
    assert health1.keys() == health2.keys()
    assert health1['components'].keys() == health2['components'].keys()


def test_export_metrics_multiple_calls():
    """Test that metrics can be exported multiple times."""
    orc = Orchestrator()
    
    metrics1 = orc.export_metrics()
    metrics2 = orc.export_metrics()
    
    # Should return consistent structure
    assert metrics1.keys() == metrics2.keys()
    
    # Timestamps should be different (or very close)
    assert metrics1['timestamp'] <= metrics2['timestamp']
