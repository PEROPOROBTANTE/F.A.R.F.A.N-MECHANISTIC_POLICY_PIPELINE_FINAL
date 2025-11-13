"""
Tests for runtime contract validation using Pydantic models.

These tests ensure that:
1. Valid contracts pass validation
2. Invalid contracts fail validation with appropriate errors
3. Schema versioning is enforced
4. Field constraints are properly validated
"""

import pytest

# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Runtime contracts now in test_contracts_comprehensive.py")

from pydantic import ValidationError

from saaaaaa.utils.contracts_runtime import (
    CDAFFrameworkInputModel,
    CDAFFrameworkOutputModel,
    ContradictionDetectorInputModel,
    ContradictionDetectorOutputModel,
    EmbeddingPolicyInputModel,
    EmbeddingPolicyOutputModel,
    PDETAnalyzerInputModel,
    PDETAnalyzerOutputModel,
    PolicyProcessorInputModel,
    PolicyProcessorOutputModel,
    SemanticAnalyzerInputModel,
    SemanticAnalyzerOutputModel,
    SemanticChunkingInputModel,
    SemanticChunkingOutputModel,
    TeoriaCambioInputModel,
)

class TestSemanticAnalyzerContracts:
    """Test SemanticAnalyzer contract validation."""

    def test_valid_input_minimal(self):
        """Valid input with minimal required fields."""
        model = SemanticAnalyzerInputModel(
            text="Sample municipal plan text",
            schema_version="sem-1.0"
        )
        assert model.text == "Sample municipal plan text"
        assert model.schema_version == "sem-1.0"
        assert model.segments == []
        assert model.ontology_params == {}

    def test_valid_input_full(self):
        """Valid input with all fields populated."""
        model = SemanticAnalyzerInputModel(
            text="El plan de desarrollo municipal...",
            segments=["Segment 1", "Segment 2"],
            ontology_params={"domain": "municipal"},
            schema_version="sem-1.1"
        )
        assert len(model.segments) == 2
        assert model.ontology_params["domain"] == "municipal"

    def test_invalid_empty_text(self):
        """Empty text should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerInputModel(
                text="",
                schema_version="sem-1.0"
            )
        assert "text" in str(exc_info.value)

    def test_invalid_whitespace_text(self):
        """Whitespace-only text should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerInputModel(
                text="   ",
                schema_version="sem-1.0"
            )
        assert "text" in str(exc_info.value)

    def test_invalid_schema_version(self):
        """Invalid schema version format should fail."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerInputModel(
                text="Sample text",
                schema_version="v1.0"  # Wrong format
            )
        assert "schema_version" in str(exc_info.value)

    def test_unknown_field_rejected(self):
        """Unknown fields should be rejected (strict mode)."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerInputModel(
                text="Sample text",
                schema_version="sem-1.0",
                unknown_field="value"
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_valid_output(self):
        """Valid output contract."""
        model = SemanticAnalyzerOutputModel(
            semantic_cube={"key": "value"},
            coherence_score=0.85,
            complexity_score=2.5,
            domain_classification={"municipal": 0.8, "economic": 0.2},
            schema_version="sem-1.0"
        )
        assert model.coherence_score == 0.85
        assert 0.0 <= model.coherence_score <= 1.0

    def test_invalid_coherence_score(self):
        """Coherence score outside [0, 1] should fail."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerOutputModel(
                semantic_cube={},
                coherence_score=1.5,  # Invalid: > 1
                complexity_score=1.0,
                domain_classification={},
                schema_version="sem-1.0"
            )
        assert "coherence_score" in str(exc_info.value)

    def test_invalid_domain_probabilities(self):
        """Domain probabilities outside [0, 1] should fail."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerOutputModel(
                semantic_cube={},
                coherence_score=0.5,
                complexity_score=1.0,
                domain_classification={"domain1": 1.5},  # Invalid
                schema_version="sem-1.0"
            )
        assert "Probability" in str(exc_info.value)

class TestCDAFFrameworkContracts:
    """Test CDAF Framework contract validation."""

    def test_valid_input(self):
        """Valid CDAF input."""
        model = CDAFFrameworkInputModel(
            document_text="Plan document text",
            plan_metadata={"author": "Municipality"},
            schema_version="sem-1.0"
        )
        assert model.document_text == "Plan document text"

    def test_valid_output(self):
        """Valid CDAF output."""
        model = CDAFFrameworkOutputModel(
            causal_mechanisms=[{"type": "mechanism1"}],
            evidential_tests={"test1": "result"},
            bayesian_inference={"posterior": 0.8},
            audit_results={"status": "passed"},
            schema_version="sem-1.0"
        )
        assert len(model.causal_mechanisms) == 1

class TestPDETAnalyzerContracts:
    """Test PDET Analyzer contract validation."""

    def test_valid_input(self):
        """Valid PDET input."""
        model = PDETAnalyzerInputModel(
            document_content="Financial document",
            extract_tables=True,
            schema_version="sem-1.0"
        )
        assert model.extract_tables is True

    def test_valid_output(self):
        """Valid PDET output."""
        model = PDETAnalyzerOutputModel(
            extracted_tables=[{"table1": "data"}],
            financial_indicators={"indicator1": 100.0},
            viability_score=0.75,
            quality_scores={"quality1": 0.9},
            schema_version="sem-1.0"
        )
        assert 0.0 <= model.viability_score <= 1.0

    def test_invalid_viability_score(self):
        """Viability score outside [0, 1] should fail."""
        with pytest.raises(ValidationError) as exc_info:
            PDETAnalyzerOutputModel(
                extracted_tables=[],
                financial_indicators={},
                viability_score=1.2,  # Invalid
                quality_scores={},
                schema_version="sem-1.0"
            )
        assert "viability_score" in str(exc_info.value)

class TestContradictionDetectorContracts:
    """Test Contradiction Detector contract validation."""

    def test_valid_input(self):
        """Valid contradiction detector input."""
        model = ContradictionDetectorInputModel(
            text="Policy document text",
            plan_name="Municipal Plan 2024",
            dimension="economic",
            schema_version="sem-1.0"
        )
        assert model.plan_name == "Municipal Plan 2024"

    def test_valid_output(self):
        """Valid contradiction detector output."""
        model = ContradictionDetectorOutputModel(
            contradictions=[{"id": 1, "description": "Contradiction A"}],
            confidence_scores={"contradiction_1": 0.9},
            temporal_conflicts=[],
            severity_scores={"contradiction_1": 0.8},
            schema_version="sem-1.0"
        )
        assert len(model.contradictions) == 1

class TestEmbeddingPolicyContracts:
    """Test Embedding Policy contract validation."""

    def test_valid_input(self):
        """Valid embedding policy input."""
        model = EmbeddingPolicyInputModel(
            text="Policy text",
            dimensions=["economic", "social"],
            schema_version="sem-1.0"
        )
        assert len(model.dimensions) == 2

    def test_valid_output(self):
        """Valid embedding policy output."""
        model = EmbeddingPolicyOutputModel(
            embeddings=[[0.1, 0.2, 0.3]],
            similarity_scores={"score1": 0.8},
            bayesian_evaluation={},
            policy_metrics={},
            schema_version="sem-1.0"
        )
        assert len(model.embeddings) == 1

class TestSemanticChunkingContracts:
    """Test Semantic Chunking contract validation."""

    def test_valid_input(self):
        """Valid semantic chunking input."""
        model = SemanticChunkingInputModel(
            text="Document to chunk",
            preserve_structure=True,
            schema_version="sem-1.0"
        )
        assert model.preserve_structure is True

    def test_valid_output(self):
        """Valid semantic chunking output."""
        model = SemanticChunkingOutputModel(
            chunks=[{"id": 1, "text": "Chunk 1"}],
            causal_dimensions={},
            key_excerpts={},
            summary={},
            schema_version="sem-1.0"
        )
        assert len(model.chunks) == 1

class TestPolicyProcessorContracts:
    """Test Policy Processor contract validation."""

    def test_valid_input(self):
        """Valid policy processor input."""
        model = PolicyProcessorInputModel(
            data={"key": "value"},
            text="Policy text",
            sentences=["Sentence 1", "Sentence 2"],
            schema_version="sem-1.0"
        )
        assert len(model.sentences) == 2

    def test_valid_output(self):
        """Valid policy processor output."""
        model = PolicyProcessorOutputModel(
            processed_data={"result": "data"},
            evidence_bundles=[],
            bayesian_scores={},
            matched_patterns=[],
            schema_version="sem-1.0"
        )
        assert model.processed_data["result"] == "data"

class TestSchemaVersioning:
    """Test schema versioning across all contracts."""

    @pytest.mark.parametrize("model_class", [
        SemanticAnalyzerInputModel,
        CDAFFrameworkInputModel,
        PDETAnalyzerInputModel,
        TeoriaCambioInputModel,
        ContradictionDetectorInputModel,
        EmbeddingPolicyInputModel,
        SemanticChunkingInputModel,
        PolicyProcessorInputModel,
    ])
    def test_default_schema_version(self, model_class):
        """All contracts default to sem-1.0."""
        # Create minimal valid instance
        kwargs = {}
        if hasattr(model_class.model_fields.get('text'), 'annotation'):
            kwargs['text'] = "Sample text"
        if hasattr(model_class.model_fields.get('document_text'), 'annotation'):
            kwargs['document_text'] = "Sample document"
        if hasattr(model_class.model_fields.get('document_content'), 'annotation'):
            kwargs['document_content'] = "Sample content"
        if hasattr(model_class.model_fields.get('plan_name'), 'annotation'):
            kwargs['plan_name'] = "Plan"
        if hasattr(model_class.model_fields.get('data'), 'annotation'):
            kwargs['data'] = {}
            kwargs['text'] = "Sample text"

        model = model_class(**kwargs)
        assert model.schema_version == "sem-1.0"

    @pytest.mark.parametrize("version", ["sem-1.0", "sem-1.1", "sem-2.0", "sem-10.5"])
    def test_valid_version_formats(self, version):
        """Test various valid version formats."""
        model = SemanticAnalyzerInputModel(
            text="Test",
            schema_version=version
        )
        assert model.schema_version == version

    @pytest.mark.parametrize("invalid_version", ["v1.0", "1.0", "sem-1", "sem-a.b"])
    def test_invalid_version_formats(self, invalid_version):
        """Test that invalid version formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerInputModel(
                text="Test",
                schema_version=invalid_version
            )
        assert "schema_version" in str(exc_info.value)

class TestStrictMode:
    """Test that strict mode rejects unknown fields."""

    def test_reject_extra_input_fields(self):
        """Extra fields in input contracts should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerInputModel(
                text="Test",
                schema_version="sem-1.0",
                extra_field="not allowed"
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_reject_extra_output_fields(self):
        """Extra fields in output contracts should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SemanticAnalyzerOutputModel(
                semantic_cube={},
                coherence_score=0.5,
                complexity_score=1.0,
                domain_classification={},
                schema_version="sem-1.0",
                extra_result="not allowed"
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)
