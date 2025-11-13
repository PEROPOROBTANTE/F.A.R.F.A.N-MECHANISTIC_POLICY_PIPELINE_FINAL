"""
Additional comprehensive tests for recommendation engine.

Expands test coverage for behavioral correctness, data integrity,
and edge cases.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

# Try to import recommendation_engine, skip tests if not available
pytest.importorskip("recommendation_engine", reason="recommendation_engine module not available")

from saaaaaa.analysis.recommendation_engine import (
    RecommendationEngine,
    RecommendationSet,
)


_ENHANCED_FEATURES = [
    "template_parameterization",
    "execution_logic",
    "measurable_indicators",
    "unambiguous_time_horizons",
    "testable_verification",
    "cost_tracking",
    "authority_mapping",
]


def build_strict_template(
    *,
    pa_id: str | None = "PA01",
    dim_id: str | None = "DIM01",
    question_id: str = "Q001",
    cluster_id: str | None = None,
) -> dict:
    """Return a deep copy of an enhanced template that satisfies strict validation."""

    template_params: dict[str, str] = {"question_id": question_id}
    if pa_id:
        template_params["pa_id"] = pa_id
    if dim_id:
        template_params["dim_id"] = dim_id
    if cluster_id:
        template_params["cluster_id"] = cluster_id

    base_identifier = f"{(pa_id or 'GEN')}-{(dim_id or cluster_id or 'GEN')}"

    template = {
        "problem": (
            "La dimensión evaluada evidencia déficit específico porque el diagnóstico carece de series "
            "históricas comparables, supuestos de validez y referencias a fuentes verificables que "
            "permitan cerrar la brecha priorizada."
        ),
        "intervention": (
            "Implementar un plan de acción secuenciado con responsables definidos, interoperabilidad de "
            "bases de datos sectoriales y entregables trazables para cerrar la brecha identificada en la "
            "dimensión prioritaria."
        ),
        "indicator": {
            "name": "Indicador estructurado de prueba",
            "baseline": None,
            "target": 0.75,
            "unit": "proporción",
            "formula": "COUNT(valid_items) / COUNT(total_items)",
            "acceptable_range": [0.5, 1.0],
            "baseline_measurement_date": "2024-01-01",
            "measurement_frequency": "mensual",
            "data_source": "Sistema de seguimiento",
            "data_source_query": "SELECT 1",
            "responsible_measurement": "Secretaría de Planeación",
            "escalation_if_below": 0.5,
        },
        "responsible": {
            "entity": "Secretaría de Planeación",
            "role": "Coordina seguimiento",
            "partners": ["Secretaría de Hacienda"],
            "legal_mandate": "Ley 152 de 1994",
            "approval_chain": [
                {"level": 1, "role": "Coordinador", "decision": "Valida alcance"},
                {"level": 2, "role": "Secretario", "decision": "Aprueba presupuesto"},
            ],
            "escalation_path": {
                "threshold_days_delay": 10,
                "escalate_to": "Secretaría de Gobierno",
                "final_escalation": "Despacho del Alcalde",
                "consequences": ["Reasignación de responsables"],
            },
        },
        "horizon": {
            "start": "T0",
            "end": "T1",
            "start_type": "plan_approval_date",
            "duration_months": 6,
            "milestones": [
                {
                    "name": "Inicio",
                    "offset_months": 1,
                    "deliverables": ["Plan de trabajo aprobado"],
                    "verification_required": True,
                }
            ],
            "dependencies": [],
            "critical_path": True,
        },
        "verification": [
            {
                "id": f"VER-{base_identifier}-001",
                "type": "DOCUMENT",
                "artifact": "Informe técnico firmado",
                "format": "PDF",
                "required_sections": ["Objetivo", "Resultados"],
                "approval_required": True,
                "approver": "Secretaría de Planeación",
                "due_date": "T1",
                "automated_check": False,
            }
        ],
        "template_id": f"TPL-{base_identifier}",
        "template_params": template_params,
    }

    return deepcopy(template)


def build_execution_block(
    *, pa_id: str | None = "PA01", dim_id: str | None = "DIM01", cluster_id: str | None = None
) -> dict:
    """Build a compliant execution block for enhanced rules."""

    conditions: list[str] = []
    if pa_id:
        conditions.append(f"pa_id = '{pa_id}'")
    if dim_id:
        conditions.append(f"dim_id = '{dim_id}'")
    if cluster_id:
        conditions.append(f"cluster_id = '{cluster_id}'")
    trigger = " AND ".join(conditions) if conditions else "TRUE"

    return {
        "trigger_condition": trigger,
        "blocking": False,
        "auto_apply": False,
        "requires_approval": True,
        "approval_roles": ["Secretaría de Planeación"],
    }


def build_budget_block(*, estimated_cost: float = 1_000_000.0) -> dict:
    """Return a minimal but valid enhanced budget block."""

    return {
        "estimated_cost_cop": estimated_cost,
        "cost_breakdown": {
            "personal": estimated_cost * 0.5,
            "tecnologia": estimated_cost * 0.3,
            "consultoria": estimated_cost * 0.2,
        },
        "funding_sources": [
            {"source": "Recursos propios", "amount": estimated_cost, "confirmed": False}
        ],
        "fiscal_year": 2025,
    }


class TestRecommendationEngineDataIntegrity:
    """Test data integrity and input validation."""

    def test_empty_micro_scores(self):
        """Test behavior with empty micro scores."""
        # Create minimal rules file for testing
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": []
        }

        # Create temp files
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        # Create minimal schema
        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Empty scores should not crash
            result = engine.generate_micro_recommendations({})

            assert isinstance(result, RecommendationSet)
            assert result.level == 'MICRO'
            assert len(result.recommendations) == 0
            assert result.rules_matched == 0
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

    def test_malformed_score_keys(self):
        """Test behavior with malformed score keys."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": [
                {
                    "rule_id": "TEST-001",
                    "level": "MICRO",
                    "when": {
                        "pa_id": "PA01",
                        "dim_id": "DIM01",
                        "score_lt": 2.0
                    },
                    "template": build_strict_template(pa_id="PA01", dim_id="DIM01"),
                    "execution": build_execution_block(pa_id="PA01", dim_id="DIM01"),
                    "budget": build_budget_block(),
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Malformed keys should be ignored, not crash
            malformed_scores = {
                "INVALID": 1.0,
                "PA01": 1.5,
                "PA01-DIM99": 1.0
            }

            result = engine.generate_micro_recommendations(malformed_scores)

            assert isinstance(result, RecommendationSet)
            # Should not match because keys don't match expected pattern
            assert result.rules_matched == 0
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

    def test_null_and_none_values(self):
        """Test handling of null/None values in data."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": []
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Test with None context
            result = engine.generate_micro_recommendations({}, context=None)
            assert isinstance(result, RecommendationSet)

            # Test MESO with None values
            cluster_data_with_none = {
                'CL01': {'score': None, 'variance': 0.1, 'weak_pa': None}
            }
            result = engine.generate_meso_recommendations(cluster_data_with_none)
            assert isinstance(result, RecommendationSet)
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

    def test_extreme_score_values(self):
        """Test handling of extreme score values."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": [
                {
                    "rule_id": "TEST-001",
                    "level": "MICRO",
                    "when": {
                        "pa_id": "PA01",
                        "dim_id": "DIM01",
                        "score_lt": 2.0
                    },
                    "template": build_strict_template(pa_id="PA01", dim_id="DIM01"),
                    "execution": build_execution_block(pa_id="PA01", dim_id="DIM01"),
                    "budget": build_budget_block(),
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Test with extreme values
            extreme_scores = {
                'PA01-DIM01': -1000.0,  # Negative
                'PA02-DIM01': 1000.0,   # Very high
                'PA03-DIM01': 0.0,      # Zero
            }

            result = engine.generate_micro_recommendations(extreme_scores)
            assert isinstance(result, RecommendationSet)
            # Rule should match for PA01-DIM01 since -1000 < 2.0
            assert result.rules_matched >= 1
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

class TestRecommendationEngineBehavioralCorrectness:
    """Test behavioral correctness of recommendation logic."""

    def test_score_threshold_boundary(self):
        """Test score threshold boundary conditions."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": [
                {
                    "rule_id": "BOUNDARY-001",
                    "level": "MICRO",
                    "when": {
                        "pa_id": "PA01",
                        "dim_id": "DIM01",
                        "score_lt": 2.0
                    },
                    "template": build_strict_template(pa_id="PA01", dim_id="DIM01"),
                    "execution": build_execution_block(pa_id="PA01", dim_id="DIM01"),
                    "budget": build_budget_block(),
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Test exact boundary
            result = engine.generate_micro_recommendations({'PA01-DIM01': 2.0})
            assert result.rules_matched == 0  # Should NOT match (not less than 2.0)

            # Test just below boundary
            result = engine.generate_micro_recommendations({'PA01-DIM01': 1.999})
            assert result.rules_matched == 1  # Should match

            # Test just above boundary
            result = engine.generate_micro_recommendations({'PA01-DIM01': 2.001})
            assert result.rules_matched == 0  # Should NOT match
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

    def test_meso_score_band_logic(self):
        """Test MESO score band categorization logic."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": [
                {
                    "rule_id": "MESO-BAJO",
                    "level": "MESO",
                    "when": {
                        "cluster_id": "CL01",
                        "score_band": "BAJO",
                        "variance_level": "BAJA"
                    },
                    "template": build_strict_template(pa_id=None, dim_id=None, cluster_id="CL01"),
                    "execution": build_execution_block(pa_id=None, dim_id=None, cluster_id="CL01"),
                    "budget": build_budget_block(),
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # BAJO band: score < 55
            result = engine.generate_meso_recommendations({
                'CL01': {'score': 54.0, 'variance': 0.05}
            })
            assert result.rules_matched == 1

            # Boundary: exactly 55 should NOT be BAJO
            result = engine.generate_meso_recommendations({
                'CL01': {'score': 55.0, 'variance': 0.05}
            })
            assert result.rules_matched == 0
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

    def test_template_variable_substitution(self):
        """Test template variable substitution correctness."""
        template = build_strict_template(pa_id="PA05", dim_id="DIM03")
        template['problem'] = (
            "El componente {{PAxx}}-{{DIMxx}} presenta rezago analítico en los insumos que "
            "deben sustentar la priorización territorial y poblacional."
        )
        template['intervention'] = (
            "Coordinar para {{PAxx}} sesiones técnicas que documenten criterios de {{DIMxx}} con "
            "metodologías cuantificables y responsables definidos."
        )

        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": [
                {
                    "rule_id": "VAR-001",
                    "level": "MICRO",
                    "when": {
                        "pa_id": "PA05",
                        "dim_id": "DIM03",
                        "score_lt": 2.0
                    },
                    "template": template,
                    "execution": build_execution_block(pa_id="PA05", dim_id="DIM03"),
                    "budget": build_budget_block(),
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            result = engine.generate_micro_recommendations({'PA05-DIM03': 1.5})

            assert result.rules_matched == 1
            rec = result.recommendations[0]
            assert "PA05" in rec.problem
            assert "DIM03" in rec.problem
            assert "PA05" in rec.intervention
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

class TestRecommendationEngineStressResponse:
    """Test stress response and scaling."""

    def test_large_number_of_scores(self):
        """Test with large number of scores."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": []
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Generate 1000 scores
            large_scores = {
                f'PA{i%10+1:02d}-DIM{i%6+1:02d}': float(i % 3)
                for i in range(1000)
            }

            result = engine.generate_micro_recommendations(large_scores)

            # Should handle without crashing
            assert isinstance(result, RecommendationSet)
            assert result.total_rules_evaluated >= 0
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

    def test_many_rules_evaluation(self):
        """Test evaluation with many rules."""
        # Generate 100 rules
        rules = []
        for i in range(100):
            pa_id = f"PA{(i % 10) + 1:02d}"
            dim_id = f"DIM{(i % 6) + 1:02d}"
            template = build_strict_template(pa_id=pa_id, dim_id=dim_id)
            template['problem'] = (
                f"El diagnóstico {i} evidencia carencias en datos trazables y en la modelación de "
                "riesgos necesarios para tomar decisiones."
            )
            template['intervention'] = (
                f"Ejecutar la intervención técnica {i} con cronograma verificable, metas "
                "cuantificadas y responsables designados."
            )
            rules.append({
                "rule_id": f"RULE-{i:03d}",
                "level": "MICRO",
                "when": {
                    "pa_id": pa_id,
                    "dim_id": dim_id,
                    "score_lt": 2.0
                },
                "template": template,
                "execution": build_execution_block(pa_id=pa_id, dim_id=dim_id),
                "budget": build_budget_block(estimated_cost=1_000_000.0 + i * 1000),
            })

        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": rules
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            # Should evaluate all 100 MICRO rules
            result = engine.generate_micro_recommendations({'PA01-DIM01': 1.0})

            assert result.total_rules_evaluated == 100
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()

class TestRecommendationMetadata:
    """Test recommendation metadata and tracking."""

    def test_metadata_populated(self):
        """Test that metadata is properly populated."""
        test_rules = {
            "version": "2.0",
            "enhanced_features": _ENHANCED_FEATURES,
            "rules": [
                {
                    "rule_id": "META-001",
                    "level": "MICRO",
                    "when": {
                        "pa_id": "PA01",
                        "dim_id": "DIM01",
                        "score_lt": 2.0
                    },
                    "template": build_strict_template(pa_id="PA01", dim_id="DIM01"),
                    "execution": build_execution_block(pa_id="PA01", dim_id="DIM01"),
                    "budget": build_budget_block(),
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            rules_path = f.name

        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            engine = RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

            result = engine.generate_micro_recommendations({'PA01-DIM01': 1.5})

            assert result.rules_matched == 1
            rec = result.recommendations[0]

            # Check metadata
            assert 'score_key' in rec.metadata
            assert 'actual_score' in rec.metadata
            assert 'threshold' in rec.metadata
            assert 'gap' in rec.metadata

            assert rec.metadata['score_key'] == 'PA01-DIM01'
            assert rec.metadata['actual_score'] == 1.5
            assert rec.metadata['threshold'] == 2.0
            assert rec.metadata['gap'] == pytest.approx(0.5)
        finally:
            Path(rules_path).unlink()
            Path(schema_path).unlink()
