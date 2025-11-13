"""Tests for dependency lockdown enforcement.

Tests verify that:
1. HF_ONLINE environment variable controls online model access
2. Offline mode is enforced when HF_ONLINE=0 or not set
3. Clear errors are raised when online models are attempted offline
4. No silent fallback or "best effort" behavior
"""

import os
import pytest
from unittest import mock

from saaaaaa.core.dependency_lockdown import (
    DependencyLockdown,
    DependencyLockdownError,
    get_dependency_lockdown,
    reset_dependency_lockdown,
)


@pytest.fixture
def clean_env():
    """Fixture to clean up environment variables before and after each test."""
    # Clean before test
    for key in ["HF_ONLINE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"]:
        if key in os.environ:
            del os.environ[key]
    reset_dependency_lockdown()
    
    yield
    
    # Clean after test
    for key in ["HF_ONLINE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"]:
        if key in os.environ:
            del os.environ[key]
    reset_dependency_lockdown()


class TestDependencyLockdown:
    """Test dependency lockdown enforcement."""
    
    def test_offline_mode_default(self, clean_env):
        """Test that offline mode is enforced by default (HF_ONLINE not set)."""
        # Ensure HF_ONLINE is not set
        if "HF_ONLINE" in os.environ:
            del os.environ["HF_ONLINE"]
        
        lockdown = DependencyLockdown()
        
        assert lockdown.hf_allowed is False
        assert os.getenv("HF_HUB_OFFLINE") == "1"
        assert os.getenv("TRANSFORMERS_OFFLINE") == "1"
    
    def test_offline_mode_explicit_zero(self, clean_env):
        """Test that offline mode is enforced when HF_ONLINE=0."""
        os.environ["HF_ONLINE"] = "0"
        
        lockdown = DependencyLockdown()
        
        assert lockdown.hf_allowed is False
        assert os.getenv("HF_HUB_OFFLINE") == "1"
        assert os.getenv("TRANSFORMERS_OFFLINE") == "1"
    
    def test_online_mode_enabled(self, clean_env):
        """Test that online mode is enabled when HF_ONLINE=1."""
        os.environ["HF_ONLINE"] = "1"
        
        lockdown = DependencyLockdown()
        
        assert lockdown.hf_allowed is True
        # HF_HUB_OFFLINE should NOT be set to "1" in online mode
        # (it might be unset or set to something else)
    
    def test_check_online_model_access_offline_raises(self, clean_env):
        """Test that checking online model access raises error when offline."""
        os.environ["HF_ONLINE"] = "0"
        
        lockdown = DependencyLockdown()
        
        with pytest.raises(DependencyLockdownError) as exc_info:
            lockdown.check_online_model_access(
                model_name="test-model",
                operation="test operation"
            )
        
        assert "Online model download disabled" in str(exc_info.value)
        assert "test-model" in str(exc_info.value)
        assert "HF_ONLINE=1" in str(exc_info.value)
        assert "No fallback" in str(exc_info.value)
    
    def test_check_online_model_access_online_succeeds(self, clean_env):
        """Test that checking online model access succeeds when online."""
        os.environ["HF_ONLINE"] = "1"
        
        lockdown = DependencyLockdown()
        
        # Should not raise
        lockdown.check_online_model_access(
            model_name="test-model",
            operation="test operation"
        )
    
    def test_check_critical_dependency_missing_raises(self, clean_env):
        """Test that missing critical dependency raises error."""
        lockdown = DependencyLockdown()
        
        with pytest.raises(DependencyLockdownError) as exc_info:
            lockdown.check_critical_dependency(
                module_name="nonexistent_module_xyz",
                pip_package="nonexistent-package",
                phase="test_phase"
            )
        
        assert "Critical dependency" in str(exc_info.value)
        assert "nonexistent_module_xyz" in str(exc_info.value)
        assert "test_phase" in str(exc_info.value)
        assert "No degraded mode" in str(exc_info.value)
    
    def test_check_critical_dependency_present_succeeds(self, clean_env):
        """Test that present critical dependency check succeeds."""
        lockdown = DependencyLockdown()
        
        # Should not raise (os is always available)
        lockdown.check_critical_dependency(
            module_name="os",
            pip_package="builtin",
            phase="test_phase"
        )
    
    def test_check_optional_dependency_missing_returns_false(self, clean_env):
        """Test that missing optional dependency returns False and logs warning."""
        lockdown = DependencyLockdown()
        
        result = lockdown.check_optional_dependency(
            module_name="nonexistent_optional_xyz",
            pip_package="nonexistent-optional",
            feature="test_feature"
        )
        
        assert result is False
    
    def test_check_optional_dependency_present_returns_true(self, clean_env):
        """Test that present optional dependency returns True."""
        lockdown = DependencyLockdown()
        
        # os is always available
        result = lockdown.check_optional_dependency(
            module_name="os",
            pip_package="builtin",
            feature="test_feature"
        )
        
        assert result is True
    
    def test_get_mode_description(self, clean_env):
        """Test mode description contains expected keys."""
        os.environ["HF_ONLINE"] = "0"
        
        lockdown = DependencyLockdown()
        mode_desc = lockdown.get_mode_description()
        
        assert "hf_online_allowed" in mode_desc
        assert "hf_hub_offline" in mode_desc
        assert "transformers_offline" in mode_desc
        assert "mode" in mode_desc
        assert mode_desc["hf_online_allowed"] is False
        assert mode_desc["mode"] == "offline_enforced"
    
    def test_singleton_get_dependency_lockdown(self, clean_env):
        """Test that get_dependency_lockdown returns singleton instance."""
        os.environ["HF_ONLINE"] = "0"
        
        lockdown1 = get_dependency_lockdown()
        lockdown2 = get_dependency_lockdown()
        
        assert lockdown1 is lockdown2
    
    def test_reset_dependency_lockdown(self, clean_env):
        """Test that reset creates new instance."""
        os.environ["HF_ONLINE"] = "0"
        
        lockdown1 = get_dependency_lockdown()
        reset_dependency_lockdown()
        lockdown2 = get_dependency_lockdown()
        
        assert lockdown1 is not lockdown2


class TestEmbeddingPolicyIntegration:
    """Test that embedding policy respects dependency lockdown."""
    
    def test_embedding_model_init_offline_no_cache_raises(self, clean_env):
        """Test that embedding model init raises error when offline and model not cached."""
        os.environ["HF_ONLINE"] = "0"
        
        from saaaaaa.processing.embedding_policy import (
            PolicyEmbeddingConfig,
            PolicyAnalysisEmbedder,
        )
        
        config = PolicyEmbeddingConfig(
            embedding_model="fake-model-that-does-not-exist"
        )
        
        # Mock _is_model_cached to return False
        with mock.patch(
            "saaaaaa.core.dependency_lockdown._is_model_cached",
            return_value=False
        ):
            with pytest.raises(DependencyLockdownError) as exc_info:
                PolicyAnalysisEmbedder(config)
            
            assert "Online model download disabled" in str(exc_info.value)
            assert "fake-model-that-does-not-exist" in str(exc_info.value)
    
    def test_cross_encoder_init_offline_no_cache_raises(self, clean_env):
        """Test that cross encoder init raises error when offline and model not cached."""
        os.environ["HF_ONLINE"] = "0"
        
        from saaaaaa.processing.embedding_policy import PolicyCrossEncoderReranker
        
        # Mock _is_model_cached to return False
        with mock.patch(
            "saaaaaa.core.dependency_lockdown._is_model_cached",
            return_value=False
        ):
            with pytest.raises(DependencyLockdownError) as exc_info:
                PolicyCrossEncoderReranker(
                    model_name="fake-cross-encoder-model"
                )
            
            assert "Online model download disabled" in str(exc_info.value)
            assert "fake-cross-encoder-model" in str(exc_info.value)


class TestOrchestratorIntegration:
    """Test that orchestrator initializes dependency lockdown."""
    
    def test_orchestrator_initializes_lockdown(self, clean_env):
        """Test that Orchestrator initializes dependency lockdown on construction."""
        os.environ["HF_ONLINE"] = "0"
        
        from saaaaaa.core.orchestrator import Orchestrator
        
        # Create minimal orchestrator
        orchestrator = Orchestrator()
        
        # Verify lockdown is initialized
        assert hasattr(orchestrator, "dependency_lockdown")
        assert orchestrator.dependency_lockdown is not None
        assert orchestrator.dependency_lockdown.hf_allowed is False
    
    def test_orchestrator_respects_hf_online(self, clean_env):
        """Test that Orchestrator respects HF_ONLINE setting."""
        os.environ["HF_ONLINE"] = "1"
        
        from saaaaaa.core.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        assert orchestrator.dependency_lockdown.hf_allowed is True
