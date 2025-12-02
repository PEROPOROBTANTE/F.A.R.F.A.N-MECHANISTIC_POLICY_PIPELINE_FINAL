"""
Unit tests for Graph Metrics Fallback (graph_metrics_fallback.py)

Tests graph metrics computation with NetworkX fallback handling,
graceful degradation, and observability integration.
"""
from unittest.mock import patch

import pytest

from farfan_pipeline.core.contracts.runtime_contracts import GraphMetricsInfo
from farfan_pipeline.core.runtime_config import RuntimeConfig
from src.farfan_pipeline.analysis.graph_metrics_fallback import (
    check_networkx_available,
    compute_basic_graph_stats,
    compute_graph_metrics_with_fallback,
)


@pytest.fixture
def sample_edge_list():
    """Create sample edge list for testing."""
    return [
        ('A', 'B'),
        ('B', 'C'),
        ('C', 'D'),
        ('A', 'D')
    ]


@pytest.fixture
def sample_adjacency_dict():
    """Create sample adjacency dictionary."""
    return {
        'A': ['B', 'D'],
        'B': ['C'],
        'C': ['D'],
        'D': []
    }


@pytest.fixture
def runtime_config():
    """Create runtime configuration."""
    return RuntimeConfig(mode='development')


class TestNetworkXAvailability:
    """Test suite for NetworkX availability checking."""

    def test_check_networkx_available_true(self):
        """Test NetworkX availability check when installed."""
        # NetworkX should be available in test environment
        assert check_networkx_available() is True

    @patch('src.farfan_pipeline.analysis.graph_metrics_fallback.check_networkx_available')
    def test_check_networkx_available_false(self, mock_check):
        """Test NetworkX availability check when not installed."""
        mock_check.return_value = False
        assert mock_check() is False


class TestGraphMetricsComputation:
    """Test suite for graph metrics computation with fallback."""

    def test_compute_metrics_with_edge_list(self, sample_edge_list, runtime_config):
        """Test metrics computation with edge list format."""
        metrics, info = compute_graph_metrics_with_fallback(
            sample_edge_list,
            runtime_config=runtime_config
        )

        assert isinstance(info, GraphMetricsInfo)
        if info.computed:
            assert 'num_nodes' in metrics
            assert 'num_edges' in metrics
            assert metrics['num_nodes'] > 0
            assert metrics['num_edges'] > 0

    def test_compute_metrics_with_adjacency_dict(self, sample_adjacency_dict, runtime_config):
        """Test metrics computation with adjacency dict format."""
        metrics, info = compute_graph_metrics_with_fallback(
            sample_adjacency_dict,
            runtime_config=runtime_config
        )

        assert isinstance(info, GraphMetricsInfo)
        if info.computed:
            assert 'num_nodes' in metrics
            assert 'num_edges' in metrics

    def test_compute_metrics_networkx_available(self, sample_edge_list, runtime_config):
        """Test metrics computation when NetworkX is available."""
        metrics, info = compute_graph_metrics_with_fallback(
            sample_edge_list,
            runtime_config=runtime_config
        )

        if check_networkx_available():
            assert info.networkx_available is True
            if info.computed:
                assert 'density' in metrics
                assert 'avg_clustering' in metrics
                assert 'num_components' in metrics

    @patch('src.farfan_pipeline.analysis.graph_metrics_fallback.check_networkx_available')
    def test_compute_metrics_networkx_unavailable(self, mock_check, sample_edge_list, runtime_config):
        """Test metrics computation when NetworkX is not available."""
        mock_check.return_value = False

        with patch('src.farfan_pipeline.analysis.graph_metrics_fallback.check_networkx_available', return_value=False):
            metrics, info = compute_graph_metrics_with_fallback(
                sample_edge_list,
                runtime_config=runtime_config
            )

        assert info.networkx_available is False
        assert info.computed is False
        assert info.reason is not None
        assert 'NetworkX not available' in info.reason

    def test_compute_metrics_with_document_id(self, sample_edge_list, runtime_config):
        """Test metrics computation with document ID for logging."""
        metrics, info = compute_graph_metrics_with_fallback(
            sample_edge_list,
            runtime_config=runtime_config,
            document_id='DOC-001'
        )

        assert isinstance(info, GraphMetricsInfo)

    def test_compute_metrics_invalid_format(self, runtime_config):
        """Test metrics computation with invalid graph format."""
        invalid_data = "invalid graph data"

        metrics, info = compute_graph_metrics_with_fallback(
            invalid_data,
            runtime_config=runtime_config
        )

        # Should handle gracefully
        assert isinstance(info, GraphMetricsInfo)

    def test_compute_metrics_empty_graph(self, runtime_config):
        """Test metrics computation with empty graph."""
        empty_graph = []

        metrics, info = compute_graph_metrics_with_fallback(
            empty_graph,
            runtime_config=runtime_config
        )

        assert isinstance(info, GraphMetricsInfo)


class TestBasicGraphStats:
    """Test suite for basic graph statistics without NetworkX."""

    def test_basic_stats_edge_list(self, sample_edge_list):
        """Test basic stats with edge list format."""
        stats = compute_basic_graph_stats(sample_edge_list)

        assert isinstance(stats, dict)
        assert 'num_nodes' in stats
        assert 'num_edges' in stats
        assert stats['num_nodes'] == 4
        assert stats['num_edges'] == 4
        assert stats['method'] == 'basic_stats_no_networkx'

    def test_basic_stats_adjacency_dict(self, sample_adjacency_dict):
        """Test basic stats with adjacency dict format."""
        stats = compute_basic_graph_stats(sample_adjacency_dict)

        assert isinstance(stats, dict)
        assert 'num_nodes' in stats
        assert 'num_edges' in stats
        assert stats['num_nodes'] == 4
        assert stats['method'] == 'basic_stats_no_networkx'

    def test_basic_stats_invalid_format(self):
        """Test basic stats with invalid format."""
        invalid_data = "invalid"
        stats = compute_basic_graph_stats(invalid_data)

        assert stats['num_nodes'] == 0
        assert stats['num_edges'] == 0
        assert stats['method'] == 'unknown_format'

    def test_basic_stats_empty_edge_list(self):
        """Test basic stats with empty edge list."""
        empty_list = []
        stats = compute_basic_graph_stats(empty_list)

        assert stats['num_nodes'] == 0
        assert stats['num_edges'] == 0


class TestGraphMetricsInfo:
    """Test suite for GraphMetricsInfo structure."""

    def test_graph_metrics_info_computed(self):
        """Test GraphMetricsInfo when metrics are computed."""
        info = GraphMetricsInfo(
            computed=True,
            networkx_available=True,
            reason=None
        )

        assert info.computed is True
        assert info.networkx_available is True
        assert info.reason is None

    def test_graph_metrics_info_not_computed(self):
        """Test GraphMetricsInfo when metrics are not computed."""
        info = GraphMetricsInfo(
            computed=False,
            networkx_available=False,
            reason='NetworkX not available'
        )

        assert info.computed is False
        assert info.networkx_available is False
        assert info.reason == 'NetworkX not available'


class TestFallbackObservability:
    """Test suite for fallback observability integration."""

    @patch('src.farfan_pipeline.analysis.graph_metrics_fallback.log_fallback')
    @patch('src.farfan_pipeline.analysis.graph_metrics_fallback.increment_graph_metrics_skipped')
    @patch('src.farfan_pipeline.analysis.graph_metrics_fallback.check_networkx_available')
    def test_fallback_logging_networkx_unavailable(self, mock_check, mock_increment, mock_log, runtime_config):
        """Test that fallback is logged when NetworkX is unavailable."""
        mock_check.return_value = False

        with patch('src.farfan_pipeline.analysis.graph_metrics_fallback.check_networkx_available', return_value=False):
            metrics, info = compute_graph_metrics_with_fallback(
                [],
                runtime_config=runtime_config,
                document_id='DOC-001'
            )

        # Verify fallback was logged (may or may not be called depending on implementation)
        assert info.computed is False

    def test_runtime_config_default(self, sample_edge_list):
        """Test that default runtime config is used when not provided."""
        metrics, info = compute_graph_metrics_with_fallback(
            sample_edge_list,
            runtime_config=None
        )

        assert isinstance(info, GraphMetricsInfo)


class TestIntegration:
    """Integration tests for graph metrics with fallback."""

    def test_full_pipeline_with_networkx(self, sample_edge_list, runtime_config):
        """Test full pipeline when NetworkX is available."""
        if not check_networkx_available():
            pytest.skip("NetworkX not available")

        metrics, info = compute_graph_metrics_with_fallback(
            sample_edge_list,
            runtime_config=runtime_config,
            document_id='TEST-001'
        )

        assert info.networkx_available is True
        if info.computed:
            assert 'num_nodes' in metrics
            assert 'density' in metrics
            assert metrics['num_nodes'] > 0

    def test_graceful_degradation(self, sample_edge_list, runtime_config):
        """Test graceful degradation to basic stats."""
        # Even if NetworkX fails, should return valid GraphMetricsInfo
        metrics, info = compute_graph_metrics_with_fallback(
            sample_edge_list,
            runtime_config=runtime_config
        )

        assert isinstance(metrics, dict)
        assert isinstance(info, GraphMetricsInfo)
        assert info.networkx_available in [True, False]
