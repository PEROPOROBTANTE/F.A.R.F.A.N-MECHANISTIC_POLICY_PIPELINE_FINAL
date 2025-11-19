"""Test that class registry paths are correctly configured.

This test validates that the import path fix described in the problem statement
has been correctly applied. It checks that all 22 classes have the proper
saaaaaa. prefix in their import paths.
"""

import pytest


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Registry system refactored")

def test_class_registry_paths_have_saaaaaa_prefix():
    """Verify all class paths use absolute imports with saaaaaa. prefix."""
    from saaaaaa.core.orchestrator.class_registry import get_class_paths

    paths = get_class_paths()

    # All paths should start with "saaaaaa."
    for class_name, import_path in paths.items():
        assert import_path.startswith("saaaaaa."), \
            f"{class_name} has invalid path: {import_path} (should start with 'saaaaaa.')"

def test_class_registry_has_all_expected_classes():
    """Verify all 22 classes from problem statement are registered."""
    from saaaaaa.core.orchestrator.class_registry import get_class_paths

    paths = get_class_paths()

    # Expected classes by category (from problem statement)
    expected_classes = {
        # Derek Beach (5 classes)
        "CDAFFramework",
        "CausalExtractor",
        "OperationalizationAuditor",
        "FinancialAuditor",
        "BayesianMechanismInference",

        # Contradiction Detection (3 classes)
        "PolicyContradictionDetector",
        "TemporalLogicVerifier",
        "BayesianConfidenceCalculator",

        # Analyzer_one (4 classes)
        "SemanticAnalyzer",
        "PerformanceAnalyzer",
        "TextMiningEngine",
        "MunicipalOntology",

        # Theory of Change (2 classes)
        "TeoriaCambio",
        "AdvancedDAGValidator",

        # Embedding Policy (3 classes + 1 alias)
        "BayesianNumericalAnalyzer",
        "PolicyAnalysisEmbedder",
        "AdvancedSemanticChunker",
        "SemanticChunker",  # Alias

        # Financial Analysis (1 class)
        "PDETMunicipalPlanAnalyzer",

        # Policy Processor (3 classes)
        "IndustrialPolicyProcessor",
        "PolicyTextProcessor",
        "BayesianEvidenceScorer",
    }

    # Check all expected classes are present
    actual_classes = set(paths.keys())
    missing_classes = expected_classes - actual_classes
    extra_classes = actual_classes - expected_classes

    assert not missing_classes, f"Missing classes: {missing_classes}"
    assert not extra_classes, f"Unexpected classes: {extra_classes}"
    assert len(paths) == 22, f"Expected 22 classes, got {len(paths)}"

def test_class_registry_paths_match_expected_modules():
    """Verify classes are mapped to the correct analysis/processing modules."""
    from saaaaaa.core.orchestrator.class_registry import get_class_paths

    paths = get_class_paths()

    # Derek Beach classes should be in saaaaaa.analysis.derek_beach
    derek_beach_classes = [
        "CDAFFramework", "CausalExtractor", "OperationalizationAuditor",
        "FinancialAuditor", "BayesianMechanismInference"
    ]
    for class_name in derek_beach_classes:
        assert paths[class_name].startswith("saaaaaa.analysis.derek_beach."), \
            f"{class_name} should be in saaaaaa.analysis.derek_beach"

    # Contradiction detection classes should be in saaaaaa.analysis.contradiction_deteccion
    contradiction_classes = [
        "PolicyContradictionDetector", "TemporalLogicVerifier", "BayesianConfidenceCalculator"
    ]
    for class_name in contradiction_classes:
        assert paths[class_name].startswith("saaaaaa.analysis.contradiction_deteccion."), \
            f"{class_name} should be in saaaaaa.analysis.contradiction_deteccion"

    # Analyzer_one classes should be in saaaaaa.analysis.Analyzer_one
    analyzer_classes = [
        "SemanticAnalyzer", "PerformanceAnalyzer", "TextMiningEngine", "MunicipalOntology"
    ]
    for class_name in analyzer_classes:
        assert paths[class_name].startswith("saaaaaa.analysis.Analyzer_one."), \
            f"{class_name} should be in saaaaaa.analysis.Analyzer_one"

    # Theory of Change classes should be in saaaaaa.analysis.teoria_cambio
    teoria_classes = ["TeoriaCambio", "AdvancedDAGValidator"]
    for class_name in teoria_classes:
        assert paths[class_name].startswith("saaaaaa.analysis.teoria_cambio."), \
            f"{class_name} should be in saaaaaa.analysis.teoria_cambio"

    # Financial class should be in saaaaaa.analysis.financiero_viabilidad_tablas
    assert paths["PDETMunicipalPlanAnalyzer"].startswith(
        "saaaaaa.analysis.financiero_viabilidad_tablas."
    ), "PDETMunicipalPlanAnalyzer should be in saaaaaa.analysis.financiero_viabilidad_tablas"

    # Embedding policy classes should be in saaaaaa.processing.embedding_policy
    embedding_classes = [
        "BayesianNumericalAnalyzer", "PolicyAnalysisEmbedder",
        "AdvancedSemanticChunker", "SemanticChunker"
    ]
    for class_name in embedding_classes:
        assert paths[class_name].startswith("saaaaaa.processing.embedding_policy."), \
            f"{class_name} should be in saaaaaa.processing.embedding_policy"

    # Policy processor classes should be in saaaaaa.processing.policy_processor
    processor_classes = [
        "IndustrialPolicyProcessor", "PolicyTextProcessor", "BayesianEvidenceScorer"
    ]
    for class_name in processor_classes:
        assert paths[class_name].startswith("saaaaaa.processing.policy_processor."), \
            f"{class_name} should be in saaaaaa.processing.policy_processor"

def test_class_registry_import_structure():
    """Test that class registry can be imported and has correct structure."""
    from saaaaaa.core.orchestrator.class_registry import (
        ClassRegistryError,
        build_class_registry,
        get_class_paths,
    )

    # Verify functions exist
    assert callable(build_class_registry)
    assert callable(get_class_paths)

    # Verify exception exists
    assert issubclass(ClassRegistryError, RuntimeError)

    # Verify get_class_paths returns a mapping
    paths = get_class_paths()
    assert isinstance(paths, dict) or hasattr(paths, '__getitem__')
    assert len(paths) > 0

def test_semantic_chunker_alias():
    """Verify SemanticChunker is an alias for AdvancedSemanticChunker."""
    from saaaaaa.core.orchestrator.class_registry import get_class_paths

    paths = get_class_paths()

    # Both should point to the same class
    assert paths["SemanticChunker"] == paths["AdvancedSemanticChunker"], \
        "SemanticChunker should be an alias for AdvancedSemanticChunker"
    assert paths["SemanticChunker"] == "saaaaaa.processing.embedding_policy.AdvancedSemanticChunker"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
