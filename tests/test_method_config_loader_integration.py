"""
Test MethodConfigLoader integration with actual codebase modules.

Verifies that modules can successfully load parameters from the canonical spec.
"""
import pytest
from src.saaaaaa.utils.method_config_loader import MethodConfigLoader
from src.saaaaaa.analysis.Analyzer_one import SemanticAnalyzer, MunicipalOntology


class TestMethodConfigLoaderIntegration:
    """Test integration of MethodConfigLoader with codebase modules."""
    
    def test_semantic_analyzer_with_config_loader(self):
        """Verify SemanticAnalyzer can load params from MethodConfigLoader."""
        loader = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        ontology = MunicipalOntology()
        
        analyzer = SemanticAnalyzer(ontology, config_loader=loader)
        
        # Verify parameters were loaded from canonical spec
        assert analyzer.max_features == 1000
        assert analyzer.ngram_range == (1, 3)
        assert analyzer.similarity_threshold == 0.3
    
    def test_semantic_analyzer_without_config_loader(self):
        """Verify SemanticAnalyzer works without MethodConfigLoader (backward compat)."""
        ontology = MunicipalOntology()
        analyzer = SemanticAnalyzer(ontology)
        
        # Should use hard-coded defaults
        assert analyzer.max_features == 1000
        assert analyzer.ngram_range == (1, 3)
        assert analyzer.similarity_threshold == 0.3
    
    def test_semantic_analyzer_with_overrides(self):
        """Verify parameter overrides take precedence over config_loader."""
        loader = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        ontology = MunicipalOntology()
        
        # Override one parameter
        analyzer = SemanticAnalyzer(
            ontology, 
            config_loader=loader,
            similarity_threshold=0.5  # Override
        )
        
        # Overridden parameter should be used
        assert analyzer.similarity_threshold == 0.5
        # Non-overridden parameters should come from config_loader
        assert analyzer.max_features == 1000
        assert analyzer.ngram_range == (1, 3)
