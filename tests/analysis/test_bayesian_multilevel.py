"""
Unit tests for Bayesian Multilevel System (bayesian_multilevel_system.py)

Tests reconciliation validators, Bayesian updaters, probative tests,
dispersion engine, and posterior sampling validation.
"""
from unittest.mock import Mock

import pytest

from src.farfan_pipeline.analysis.bayesian_multilevel_system import (
    BayesianUpdater,
    DispersionEngine,
    MicroLevelAnalysis,
    ProbativeTest,
    ProbativeTestType,
    ReconciliationValidator,
    ValidationResult,
    ValidationRule,
    ValidatorType,
)


@pytest.fixture
def sample_validation_rules():
    """Create sample validation rules."""
    return [
        ValidationRule(
            validator_type=ValidatorType.RANGE,
            field_name='score',
            expected_range=(0.0, 100.0),
            penalty_factor=0.1
        ),
        ValidationRule(
            validator_type=ValidatorType.UNIT,
            field_name='unit',
            expected_unit='porcentaje',
            penalty_factor=0.05
        ),
        ValidationRule(
            validator_type=ValidatorType.PERIOD,
            field_name='period',
            expected_period='2024',
            penalty_factor=0.05
        )
    ]


@pytest.fixture
def reconciliation_validator(sample_validation_rules):
    """Create reconciliation validator."""
    return ReconciliationValidator(sample_validation_rules)


@pytest.fixture
def bayesian_updater():
    """Create Bayesian updater."""
    return BayesianUpdater()


class TestReconciliationValidator:
    """Test suite for ReconciliationValidator."""

    def test_validate_range_within_bounds(self, reconciliation_validator):
        """Test range validation with value within bounds."""
        rule = ValidationRule(
            validator_type=ValidatorType.RANGE,
            field_name='score',
            expected_range=(0.0, 100.0),
            penalty_factor=0.1
        )

        result = reconciliation_validator.validate_range(50.0, rule)

        assert result.passed is True
        assert result.violation_severity == 0.0
        assert result.penalty_applied == 0.0

    def test_validate_range_outside_bounds(self, reconciliation_validator):
        """Test range validation with value outside bounds."""
        rule = ValidationRule(
            validator_type=ValidatorType.RANGE,
            field_name='score',
            expected_range=(0.0, 100.0),
            penalty_factor=0.1
        )

        result = reconciliation_validator.validate_range(150.0, rule)

        assert result.passed is False
        assert result.violation_severity > 0.0
        assert result.penalty_applied > 0.0

    def test_validate_unit_matching(self, reconciliation_validator):
        """Test unit validation with matching unit."""
        rule = ValidationRule(
            validator_type=ValidatorType.UNIT,
            field_name='unit',
            expected_unit='porcentaje',
            penalty_factor=0.05
        )

        result = reconciliation_validator.validate_unit('porcentaje', rule)

        assert result.passed is True
        assert result.penalty_applied == 0.0

    def test_validate_unit_not_matching(self, reconciliation_validator):
        """Test unit validation with non-matching unit."""
        rule = ValidationRule(
            validator_type=ValidatorType.UNIT,
            field_name='unit',
            expected_unit='porcentaje',
            penalty_factor=0.05
        )

        result = reconciliation_validator.validate_unit('numero', rule)

        assert result.passed is False
        assert result.violation_severity == 1.0
        assert result.penalty_applied > 0.0

    def test_validate_data_multiple_rules(self, reconciliation_validator):
        """Test validation of data against multiple rules."""
        data = {
            'score': 85.0,
            'unit': 'porcentaje',
            'period': '2024'
        }

        results = reconciliation_validator.validate_data(data)

        assert isinstance(results, list)
        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_calculate_total_penalty(self, reconciliation_validator):
        """Test total penalty calculation."""
        results = [
            ValidationResult(
                rule=Mock(), passed=False, observed_value=150,
                expected_value=(0, 100), violation_severity=0.5,
                penalty_applied=0.05
            ),
            ValidationResult(
                rule=Mock(), passed=False, observed_value='wrong',
                expected_value='correct', violation_severity=1.0,
                penalty_applied=0.1
            )
        ]

        total_penalty = reconciliation_validator.calculate_total_penalty(results)

        assert total_penalty == 0.15


class TestBayesianUpdater:
    """Test suite for BayesianUpdater."""

    def test_initialization(self, bayesian_updater):
        """Test Bayesian updater initialization."""
        assert bayesian_updater is not None
        assert len(bayesian_updater.updates) == 0

    def test_update_with_straw_in_wind(self, bayesian_updater):
        """Test Bayesian update with straw-in-wind test."""
        test = ProbativeTest(
            test_type=ProbativeTestType.STRAW_IN_WIND,
            test_name='Weak evidence test',
            evidence_strength=0.6,
            prior_probability=0.5
        )

        posterior = bayesian_updater.update(0.5, test, test_passed=True)

        assert 0.0 <= posterior <= 1.0
        assert len(bayesian_updater.updates) == 1

    def test_update_with_hoop_test_pass(self, bayesian_updater):
        """Test Bayesian update with passing hoop test."""
        test = ProbativeTest(
            test_type=ProbativeTestType.HOOP_TEST,
            test_name='Necessary condition test',
            evidence_strength=0.8,
            prior_probability=0.5
        )

        posterior = bayesian_updater.update(0.5, test, test_passed=True)

        assert posterior > 0.0
        assert posterior <= 1.0

    def test_sequential_update(self, bayesian_updater):
        """Test sequential Bayesian updating."""
        tests = [
            (ProbativeTest(
                test_type=ProbativeTestType.STRAW_IN_WIND,
                test_name='Test 1',
                evidence_strength=0.6,
                prior_probability=0.5
            ), True),
            (ProbativeTest(
                test_type=ProbativeTestType.HOOP_TEST,
                test_name='Test 2',
                evidence_strength=0.8,
                prior_probability=0.5
            ), True)
        ]

        final_posterior = bayesian_updater.sequential_update(0.5, tests)

        assert 0.0 <= final_posterior <= 1.0
        assert len(bayesian_updater.updates) == 2

    def test_export_to_csv(self, bayesian_updater, tmp_path):
        """Test exporting posterior table to CSV."""
        test = ProbativeTest(
            test_type=ProbativeTestType.STRAW_IN_WIND,
            test_name='Test',
            evidence_strength=0.6,
            prior_probability=0.5
        )
        bayesian_updater.update(0.5, test, test_passed=True)

        output_path = tmp_path / 'posterior_table_micro.csv'
        bayesian_updater.export_to_csv(output_path)

        assert output_path.exists()


class TestDispersionEngine:
    """Test suite for DispersionEngine."""

    @pytest.fixture
    def dispersion_engine(self):
        """Create dispersion engine."""
        return DispersionEngine(dispersion_threshold=0.3)

    def test_calculate_cv(self, dispersion_engine):
        """Test coefficient of variation calculation."""
        scores = [80.0, 85.0, 90.0, 95.0, 100.0]
        cv = dispersion_engine.calculate_cv(scores)

        assert isinstance(cv, float)
        assert cv >= 0.0

    def test_calculate_cv_empty_list(self, dispersion_engine):
        """Test CV with empty list."""
        cv = dispersion_engine.calculate_cv([])
        assert cv == 0.0

    def test_calculate_max_gap(self, dispersion_engine):
        """Test maximum gap calculation."""
        scores = [60.0, 70.0, 85.0, 95.0]
        max_gap = dispersion_engine.calculate_max_gap(scores)

        assert isinstance(max_gap, float)
        assert max_gap > 0.0

    def test_calculate_gini(self, dispersion_engine):
        """Test Gini coefficient calculation."""
        scores = [50.0, 60.0, 70.0, 80.0, 90.0]
        gini = dispersion_engine.calculate_gini(scores)

        assert isinstance(gini, float)
        assert 0.0 <= gini <= 1.0


class TestIntegration:
    """Integration tests for Bayesian multilevel system."""

    def test_micro_level_analysis_pipeline(self, reconciliation_validator, bayesian_updater):
        """Test complete MICRO level analysis pipeline."""
        # Validation
        data = {'score': 75.0, 'unit': 'porcentaje', 'period': '2024'}
        validation_results = reconciliation_validator.validate_data(data)
        validation_penalty = reconciliation_validator.calculate_total_penalty(validation_results)

        # Bayesian updating
        test = ProbativeTest(
            test_type=ProbativeTestType.HOOP_TEST,
            test_name='Quality test',
            evidence_strength=0.8,
            prior_probability=0.5
        )
        final_posterior = bayesian_updater.update(0.5, test, test_passed=True)

        # Create MicroLevelAnalysis
        analysis = MicroLevelAnalysis(
            question_id='Q001',
            raw_score=75.0,
            validation_results=validation_results,
            validation_penalty=validation_penalty,
            bayesian_updates=bayesian_updater.updates,
            final_posterior=final_posterior,
            adjusted_score=75.0 - validation_penalty
        )

        assert analysis.question_id == 'Q001'
        assert analysis.final_posterior == final_posterior
        assert analysis.adjusted_score <= analysis.raw_score
