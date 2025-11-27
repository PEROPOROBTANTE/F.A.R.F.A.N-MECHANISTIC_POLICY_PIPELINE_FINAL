"""
Tests for boot checks with runtime configuration integration.

Tests boot check behavior across different runtime modes (PROD, DEV, EXPLORATORY)
and validates proper error handling and fallback behavior.
"""

import pytest
from unittest.mock import patch, MagicMock

from saaaaaa.core.runtime_config import RuntimeConfig, RuntimeMode
from saaaaaa.core.boot_checks import (
    run_boot_checks,
    get_boot_check_summary,
    BootCheckError,
    check_contradiction_module_available,
    check_wiring_validator_available,
    check_spacy_model_available,
    check_networkx_available,
)


class TestBootChecksInProdMode:
    """Test boot checks in PROD mode (strict enforcement)."""
    
    def test_all_checks_pass_in_prod(self):
        """All checks passing should succeed in PROD mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.PROD,
            allow_contradiction_fallback=False,
            allow_execution_estimates=False,
            allow_dev_ingestion_fallbacks=False,
            allow_aggregation_defaults=False,
            strict_calibration=True,
            allow_validator_disable=False,
            allow_hash_fallback=False,
            preferred_spacy_model="es_core_news_lg"
        )
        
        # Should not raise if all dependencies available
        results = run_boot_checks(config)
        
        # All checks should pass
        assert all(result["status"] == "passed" for result in results.values())
        
        # Summary should show success
        summary = get_boot_check_summary(results)
        assert "passed" in summary.lower()
    
    def test_missing_critical_module_fails_in_prod(self):
        """Missing critical module should raise BootCheckError in PROD."""
        config = RuntimeConfig(
            mode=RuntimeMode.PROD,
            allow_contradiction_fallback=False,
            allow_execution_estimates=False,
            allow_dev_ingestion_fallbacks=False,
            allow_aggregation_defaults=False,
            strict_calibration=True,
            allow_validator_disable=False,
            allow_hash_fallback=False,
            preferred_spacy_model="es_core_news_lg"
        )
        
        # Mock contradiction module as unavailable
        with patch('saaaaaa.core.boot_checks.check_contradiction_module_available') as mock_check:
            mock_check.return_value = {
                "status": "failed",
                "component": "contradiction_module",
                "reason": "Module not found",
                "code": "MODULE_NOT_FOUND"
            }
            
            # Should raise in PROD mode
            with pytest.raises(BootCheckError) as exc_info:
                run_boot_checks(config)
            
            assert exc_info.value.component == "contradiction_module"
            assert "MODULE_NOT_FOUND" in exc_info.value.code
    
    def test_spacy_model_missing_fails_in_prod(self):
        """Missing spaCy model should fail in PROD mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.PROD,
            allow_contradiction_fallback=False,
            allow_execution_estimates=False,
            allow_dev_ingestion_fallbacks=False,
            allow_aggregation_defaults=False,
            strict_calibration=True,
            allow_validator_disable=False,
            allow_hash_fallback=False,
            preferred_spacy_model="es_core_news_lg"
        )
        
        with patch('saaaaaa.core.boot_checks.check_spacy_model_available') as mock_check:
            mock_check.return_value = {
                "status": "failed",
                "component": "spacy_model",
                "reason": "Model es_core_news_lg not found",
                "code": "SPACY_MODEL_NOT_FOUND"
            }
            
            with pytest.raises(BootCheckError):
                run_boot_checks(config)


class TestBootChecksInDevMode:
    """Test boot checks in DEV mode (permissive with warnings)."""
    
    def test_missing_module_warns_in_dev(self):
        """Missing module should warn but not fail in DEV mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.DEV,
            allow_contradiction_fallback=True,
            allow_execution_estimates=True,
            allow_dev_ingestion_fallbacks=True,
            allow_aggregation_defaults=True,
            strict_calibration=False,
            allow_validator_disable=True,
            allow_hash_fallback=True,
            preferred_spacy_model="es_core_news_lg"
        )
        
        with patch('saaaaaa.core.boot_checks.check_contradiction_module_available') as mock_check:
            mock_check.return_value = {
                "status": "warning",
                "component": "contradiction_module",
                "reason": "Module not found but fallback allowed",
                "code": "MODULE_NOT_FOUND_FALLBACK_ALLOWED"
            }
            
            # Should not raise in DEV mode
            results = run_boot_checks(config)
            
            # Check should show warning status
            assert results["contradiction_module"]["status"] == "warning"
    
    def test_networkx_missing_allowed_in_dev(self):
        """NetworkX missing should be allowed in DEV mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.DEV,
            allow_contradiction_fallback=True,
            allow_execution_estimates=True,
            allow_dev_ingestion_fallbacks=True,
            allow_aggregation_defaults=True,
            strict_calibration=False,
            allow_validator_disable=True,
            allow_hash_fallback=True,
            preferred_spacy_model="es_core_news_lg"
        )
        
        with patch('saaaaaa.core.boot_checks.check_networkx_available') as mock_check:
            mock_check.return_value = {
                "status": "warning",
                "component": "networkx",
                "reason": "NetworkX not available, graph metrics will be skipped",
                "code": "NETWORKX_NOT_FOUND"
            }
            
            results = run_boot_checks(config)
            
            # Should complete without raising
            assert results["networkx"]["status"] == "warning"


class TestBootChecksInExploratoryMode:
    """Test boot checks in EXPLORATORY mode (maximum flexibility)."""
    
    def test_all_fallbacks_allowed_in_exploratory(self):
        """All fallbacks should be allowed in EXPLORATORY mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.EXPLORATORY,
            allow_contradiction_fallback=True,
            allow_execution_estimates=True,
            allow_dev_ingestion_fallbacks=True,
            allow_aggregation_defaults=True,
            strict_calibration=False,
            allow_validator_disable=True,
            allow_hash_fallback=True,
            preferred_spacy_model="es_core_news_sm"  # Can use smaller model
        )
        
        # Even with multiple missing dependencies, should not fail
        with patch('saaaaaa.core.boot_checks.check_contradiction_module_available') as mock1, \
             patch('saaaaaa.core.boot_checks.check_networkx_available') as mock2:
            
            mock1.return_value = {"status": "warning", "component": "contradiction_module", 
                                 "reason": "Fallback allowed", "code": "FALLBACK"}
            mock2.return_value = {"status": "warning", "component": "networkx",
                                 "reason": "Fallback allowed", "code": "FALLBACK"}
            
            results = run_boot_checks(config)
            
            # Should complete with warnings
            assert results["contradiction_module"]["status"] == "warning"
            assert results["networkx"]["status"] == "warning"


class TestIndividualBootChecks:
    """Test individual boot check functions."""
    
    def test_check_contradiction_module_available(self):
        """Test contradiction module availability check."""
        result = check_contradiction_module_available()
        
        assert "status" in result
        assert "component" in result
        assert result["component"] == "contradiction_module"
        
        # Status should be either passed or failed
        assert result["status"] in ["passed", "failed", "warning"]
    
    def test_check_wiring_validator_available(self):
        """Test wiring validator availability check."""
        result = check_wiring_validator_available()
        
        assert "status" in result
        assert "component" in result
        assert result["component"] == "wiring_validator"
    
    def test_check_spacy_model_with_preferred(self):
        """Test spaCy model check with preferred model."""
        # Test with LG model
        result = check_spacy_model_available("es_core_news_lg")
        
        assert "status" in result
        assert "component" in result
        assert result["component"] == "spacy_model"
        
        if result["status"] == "passed":
            assert "model" in result
            assert result["model"] in ["es_core_news_lg", "es_core_news_md", "es_core_news_sm"]
    
    def test_check_networkx_available(self):
        """Test NetworkX availability check."""
        result = check_networkx_available()
        
        assert "status" in result
        assert "component" in result
        assert result["component"] == "networkx"


class TestBootCheckSummary:
    """Test boot check summary generation."""
    
    def test_summary_all_passed(self):
        """Test summary when all checks pass."""
        results = {
            "check1": {"status": "passed", "component": "check1"},
            "check2": {"status": "passed", "component": "check2"},
            "check3": {"status": "passed", "component": "check3"},
        }
        
        summary = get_boot_check_summary(results)
        
        assert "3/3 passed" in summary or "passed" in summary.lower()
        assert "✓" in summary or "check1" in summary
    
    def test_summary_with_failures(self):
        """Test summary when some checks fail."""
        results = {
            "check1": {"status": "passed", "component": "check1"},
            "check2": {"status": "failed", "component": "check2", "reason": "Not found"},
            "check3": {"status": "warning", "component": "check3", "reason": "Degraded"},
        }
        
        summary = get_boot_check_summary(results)
        
        # Should show failure count
        assert "failed" in summary.lower() or "✗" in summary
        assert "check2" in summary or "Not found" in summary
    
    def test_summary_with_warnings(self):
        """Test summary with warnings."""
        results = {
            "check1": {"status": "passed", "component": "check1"},
            "check2": {"status": "warning", "component": "check2", "reason": "Degraded"},
        }
        
        summary = get_boot_check_summary(results)
        
        assert "warning" in summary.lower() or "⚠" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
