"""
Tests for Three-Pillar Calibration System

These tests validate the core calibration functionality according to
the SUPERPROMPT specification.

OBSOLETE: This test module uses the old calibration API that was refactored.
The new calibration system is tested in tests/calibration/ subdirectory.
See tests/calibration/test_gap0_complete.py for current calibration tests.
"""

import pytest

pytestmark = pytest.mark.skip(reason="obsolete - calibration API refactored, see tests/calibration/")

# Old imports (no longer valid):
# from calibration import (
#     calibrate, CalibrationEngine, validate_config_files,
#     Context, ComputationGraph, EvidenceStore,
#     LayerType, MethodRole
# )


# Test constants
TEST_METHOD_SCORE = "src.saaaaaa.flux.phases.run_score"
TEST_METHOD_AGGREGATE = "src.saaaaaa.flux.phases.run_aggregate"
TEST_METHOD_NORMALIZE = "src.saaaaaa.flux.phases.run_normalize"


class TestConfigValidation:
    """Test configuration file validation"""
    
    def test_config_files_exist_and_valid(self):
        """Test that all three pillar configs exist and pass validation"""
        is_valid, errors = validate_config_files()
        
        if not is_valid:
            print("\nValidation errors:")
            for error in errors:
                print(f"  - {error}")
        
        assert is_valid, f"Config validation failed: {errors}"
    
    def test_intrinsic_calibration_structure(self):
        """Test intrinsic calibration config structure"""
        engine = CalibrationEngine()
        config = engine.intrinsic_config
        
        # Check metadata
        assert "_metadata" in config
        assert "version" in config["_metadata"]
        
        # Check base weights
        assert "_base_weights" in config
        weights = config["_base_weights"]
        assert "w_th" in weights
        assert "w_imp" in weights
        assert "w_dep" in weights
        
        # Verify normalization
        weight_sum = weights["w_th"] + weights["w_imp"] + weights["w_dep"]
        assert abs(weight_sum - 1.0) < 1e-9, f"Weights don't sum to 1.0: {weight_sum}"
        
        # Check methods
        assert "methods" in config
        assert len(config["methods"]) > 0
    
    def test_contextual_parametrization_structure(self):
        """Test contextual parametrization config structure"""
        engine = CalibrationEngine()
        config = engine.contextual_config
        
        # Check all layer sections exist
        assert "layer_chain" in config
        assert "layer_unit_of_analysis" in config
        assert "layer_question" in config
        assert "layer_dimension" in config
        assert "layer_policy" in config
        assert "layer_interplay" in config
        assert "layer_meta" in config
        
        # Check anti-universality constraint
        assert "anti_universality_constraint" in config
    
    def test_fusion_specification_structure(self):
        """Test fusion specification config structure"""
        engine = CalibrationEngine()
        config = engine.fusion_config
        
        # Check metadata
        assert "_metadata" in config
        assert "_fusion_formula" in config
        
        # Check role parameters
        assert "role_fusion_parameters" in config
        roles = config["role_fusion_parameters"]
        
        # Verify all 8 roles have parameters
        expected_roles = {
            "INGEST_PDM", "STRUCTURE", "EXTRACT", "SCORE_Q",
            "AGGREGATE", "REPORT", "META_TOOL", "TRANSFORM"
        }
        assert expected_roles.issubset(set(roles.keys()))
        
        # Check each role has required fields
        for role_name, params in roles.items():
            assert "required_layers" in params
            assert "linear_weights" in params
            # interaction_weights is optional


class TestDataStructures:
    """Test core data structures"""
    
    def test_context_creation(self):
        """Test Context dataclass"""
        ctx = Context(
            question_id="Q001",
            dimension_id="DIM01",
            policy_id="PA01",
            unit_quality=0.85
        )
        
        assert ctx.question_id == "Q001"
        assert ctx.dimension_id == "DIM01"
        assert ctx.policy_id == "PA01"
        assert ctx.unit_quality == 0.85
    
    def test_context_validation(self):
        """Test Context validation"""
        # Unit quality must be in [0,1]
        with pytest.raises(ValueError):
            Context(unit_quality=1.5)
        
        with pytest.raises(ValueError):
            Context(unit_quality=-0.1)
    
    def test_computation_graph_dag_validation(self):
        """Test computation graph DAG validation"""
        # Valid DAG
        graph = ComputationGraph(
            nodes={"A", "B", "C"},
            edges=[("A", "B"), ("B", "C")]
        )
        assert graph.validate_dag() is True
        
        # Cycle detection
        graph_with_cycle = ComputationGraph(
            nodes={"A", "B", "C"},
            edges=[("A", "B"), ("B", "C"), ("C", "A")]
        )
        assert graph_with_cycle.validate_dag() is False


class TestLayerComputation:
    """Test individual layer computation functions"""
    
    @pytest.fixture
    def engine(self):
        """Create calibration engine"""
        return CalibrationEngine()
    
    def test_base_layer_computation(self, engine):
        """Test base layer (@b) computation"""
        from saaaaaa.core.calibration.layer_computers import compute_base_layer
        
        # Use a method that exists in config
        score = compute_base_layer(TEST_METHOD_SCORE, engine.intrinsic_config)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should have some positive score
    
    def test_chain_layer_computation(self, engine):
        """Test chain layer (@chain) computation"""
        from saaaaaa.core.calibration.layer_computers import compute_chain_layer
        
        graph = ComputationGraph(
            nodes={"node1"},
            edges=[],
            node_signatures={"node1": {"required_inputs": []}}
        )
        
        score = compute_chain_layer("node1", graph, engine.contextual_config)
        assert 0.0 <= score <= 1.0
    
    def test_unit_layer_computation(self, engine):
        """Test unit layer (@u) computation"""
        from saaaaaa.core.calibration.layer_computers import compute_unit_layer
        
        # Test identity function (INGEST_PDM)
        score = compute_unit_layer(
            "test_method",
            MethodRole.INGEST_PDM,
            0.75,
            engine.contextual_config
        )
        assert abs(score - 0.75) < 1e-9  # Should return U directly
        
        # Test constant function (AGGREGATE)
        score = compute_unit_layer(
            "test_method",
            MethodRole.AGGREGATE,
            0.5,
            engine.contextual_config
        )
        assert abs(score - 1.0) < 1e-9  # Should return 1.0


class TestCalibrationEngine:
    """Test main calibration engine"""
    
    def test_calibrate_basic(self):
        """Test basic calibration flow"""
        # Create simple test setup
        ctx = Context(
            question_id="Q001",
            dimension_id="DIM01",
            policy_id="PA01",
            unit_quality=0.85
        )
        
        graph = ComputationGraph(
            nodes={"node1"},
            edges=[],
            node_signatures={"node1": {}}
        )
        
        evidence = EvidenceStore(
            runtime_metrics={"runtime_ms": 500}
        )
        
        # Calibrate using a method that exists in intrinsic config
        certificate = calibrate(
            method_id=TEST_METHOD_SCORE,
            node_id="node1",
            graph=graph,
            context=ctx,
            evidence_store=evidence
        )
        
        # Validate certificate
        assert certificate is not None
        assert certificate.method_id == TEST_METHOD_SCORE
        assert certificate.node_id == "node1"
        assert 0.0 <= certificate.calibrated_score <= 1.0
        assert 0.0 <= certificate.intrinsic_score <= 1.0
    
    def test_certificate_structure(self):
        """Test that certificate contains all required fields"""
        ctx = Context()
        graph = ComputationGraph(nodes={"n1"})
        evidence = EvidenceStore()
        
        certificate = calibrate(
            method_id="src.saaaaaa.flux.phases.run_score",
            node_id="n1",
            graph=graph,
            context=ctx,
            evidence_store=evidence
        )
        
        # Check required fields
        assert hasattr(certificate, 'instance_id')
        assert hasattr(certificate, 'method_id')
        assert hasattr(certificate, 'layer_scores')
        assert hasattr(certificate, 'calibrated_score')
        assert hasattr(certificate, 'fusion_formula')
        assert hasattr(certificate, 'parameter_provenance')
        assert hasattr(certificate, 'evidence_trail')
        assert hasattr(certificate, 'config_hash')
        assert hasattr(certificate, 'graph_hash')
        
        # Check layer scores
        assert LayerType.BASE.value in certificate.layer_scores
        assert LayerType.CHAIN.value in certificate.layer_scores
        assert LayerType.META.value in certificate.layer_scores
    
    def test_fusion_formula_structure(self):
        """Test fusion formula details"""
        ctx = Context()
        graph = ComputationGraph(nodes={"n1"})
        evidence = EvidenceStore()
        
        certificate = calibrate(
            method_id=TEST_METHOD_SCORE,
            node_id="n1",
            graph=graph,
            context=ctx,
            evidence_store=evidence
        )
        
        fusion = certificate.fusion_formula
        
        # Check structure
        assert "symbolic" in fusion
        assert "linear_terms" in fusion
        assert "interaction_terms" in fusion
        assert "linear_sum" in fusion
        assert "interaction_sum" in fusion
        assert "total" in fusion
        
        # Verify totals match
        assert abs(fusion["total"] - certificate.calibrated_score) < 1e-9
    
    def test_determinism(self):
        """Test that calibration is deterministic"""
        ctx = Context(unit_quality=0.75)
        graph = ComputationGraph(nodes={"n1"})
        evidence = EvidenceStore(runtime_metrics={"runtime_ms": 300})
        
        # Run calibration twice
        cert1 = calibrate(
            method_id=TEST_METHOD_SCORE,
            node_id="n1",
            graph=graph,
            context=ctx,
            evidence_store=evidence
        )
        
        cert2 = calibrate(
            method_id=TEST_METHOD_SCORE,
            node_id="n1",
            graph=graph,
            context=ctx,
            evidence_store=evidence
        )
        
        # Scores should be identical
        assert cert1.calibrated_score == cert2.calibrated_score
        assert cert1.layer_scores == cert2.layer_scores
        assert cert1.intrinsic_score == cert2.intrinsic_score
    
    def test_boundedness_property(self):
        """Test P1: Boundedness - Cal(I) ∈ [0,1]"""
        ctx = Context()
        graph = ComputationGraph(nodes={"n1"})
        evidence = EvidenceStore()
        
        # Test with different methods
        for method_id in [TEST_METHOD_SCORE, TEST_METHOD_AGGREGATE, TEST_METHOD_NORMALIZE]:
            certificate = calibrate(
                method_id=method_id,
                node_id="n1",
                graph=graph,
                context=ctx,
                evidence_store=evidence
            )
            
            # All scores must be bounded
            assert 0.0 <= certificate.calibrated_score <= 1.0
            for layer, score in certificate.layer_scores.items():
                assert 0.0 <= score <= 1.0, f"Layer {layer} out of bounds: {score}"


class TestValidators:
    """Test validation functions"""
    
    def test_fusion_weight_validation(self):
        """Test fusion weight validation"""
        from saaaaaa.core.calibration.validators import CalibrationValidator
        
        validator = CalibrationValidator()
        
        # Valid weights
        valid_params = {
            "linear_weights": {"@b": 0.5, "@chain": 0.3},
            "interaction_weights": {"(@b, @chain)": 0.2}
        }
        is_valid, errors = validator.validate_fusion_weights(valid_params, "TEST")
        assert is_valid
        
        # Invalid: don't sum to 1.0
        invalid_params = {
            "linear_weights": {"@b": 0.5, "@chain": 0.3},
            "interaction_weights": {"(@b, @chain)": 0.1}
        }
        is_valid, errors = validator.validate_fusion_weights(invalid_params, "TEST")
        assert not is_valid
        assert len(errors) > 0
    
    def test_boundedness_validation(self):
        """Test boundedness validation"""
        from saaaaaa.core.calibration.validators import CalibrationValidator
        
        validator = CalibrationValidator()
        
        # Valid scores
        valid_layers = {"@b": 0.5, "@chain": 0.8}
        valid_cal = 0.75
        is_valid, errors = validator.validate_boundedness(valid_layers, valid_cal)
        assert is_valid
        
        # Invalid: out of bounds
        invalid_layers = {"@b": 1.5, "@chain": 0.8}
        is_valid, errors = validator.validate_boundedness(invalid_layers, 0.75)
        assert not is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
