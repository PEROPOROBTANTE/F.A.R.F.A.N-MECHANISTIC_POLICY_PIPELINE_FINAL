# ADVANCED TESTING STRATEGY
## Epistemologically Robust Validation of Method Parameterization
### F.A.R.F.A.N Mechanistic Policy Pipeline

**Version:** 1.0.0
**Date:** 2025-11-13
**Status:** COMPREHENSIVE SPECIFICATION

---

## EXECUTIVE SUMMARY

This testing strategy directly probes whether the new canonical parameterization is **correct** and **epistemically robust**. It goes beyond unit testing to validate that parameterization decisions respect the epistemological nature of each method (confirmatory vs. exploratory, causal vs. associational, diagnostic vs. inferential).

### Testing Philosophy

1. **Epistemic Correctness:** Tests validate that parameters preserve methodological integrity
2. **Reproducibility:** Bit-for-bit reproducible results with same parameters
3. **Robustness:** Small parameter perturbations yield stable (not brittle) behavior
4. **Transparency:** Parameter effects are measurable and interpretable

### Test Coverage Targets

- **Unit Tests:** 100% coverage of parameterized methods
- **Integration Tests:** All major pipelines with varied parameters
- **Property-Based Tests:** 80% of methods with identifiable mathematical properties
- **Regression Tests:** 100% coverage of previously validated behaviors

---

## PHASE 7.1: UNIT TESTS

### 7.1.1 Unit Test Structure

**Template:**
```python
class Test{MethodName}Parameterization:
    """Unit tests for {method_name} parameterization."""

    def test_default_values_load_from_json(self):
        """Verify default values match canonical JSON."""
        ...

    def test_boundary_values_valid(self):
        """Test behavior at allowed range boundaries."""
        ...

    def test_invalid_values_rejected(self):
        """Ensure invalid values raise clear errors."""
        ...

    def test_parameter_effect_interpretable(self):
        """Verify parameter changes have expected directional effect."""
        ...

    def test_reproducibility_with_same_params(self):
        """Bit-for-bit reproducibility with identical parameters."""
        ...
```

### 7.1.2 Per-Method Unit Test Specifications

#### **Test Suite:** `tests/test_semantic_analyzer_params.py`

**Method:** `ANALYZER.SemanticAnalyzer.extract_semantic_cube`

```python
import pytest
import numpy as np
from saaaaaa.analysis.Analyzer_one import SemanticAnalyzer, MunicipalOntology
from saaaaaa.utils.method_config_loader import MethodConfigLoader

@pytest.fixture
def config_loader():
    return MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")

@pytest.fixture
def sample_document_segments():
    return [
        "El diagnóstico municipal presenta una tasa de desempleo del 15%.",
        "Las actividades propuestas incluyen formación laboral y emprendimiento.",
        "Los productos esperados son 500 personas capacitadas en 2025."
    ]

class TestSemanticAnalyzerParameterization:
    """Unit tests for SemanticAnalyzer parameterization."""

    def test_default_similarity_threshold_from_json(self, config_loader):
        """Verify default similarity_threshold loads correctly from JSON."""
        expected = config_loader.get_method_parameter(
            "ANLZ.SA.extract_cube_v1",
            "similarity_threshold"
        )
        assert expected == 0.3, "Default threshold mismatch"

        analyzer = SemanticAnalyzer(
            ontology=MunicipalOntology(),
            config_loader=config_loader
        )
        assert analyzer.similarity_threshold == 0.3

    def test_similarity_threshold_boundaries(
        self,
        sample_document_segments,
        config_loader
    ):
        """Test behavior at threshold boundaries [0.0, 1.0]."""
        ontology = MunicipalOntology()

        # Minimum threshold (0.0) - should match everything
        analyzer_min = SemanticAnalyzer(
            ontology=ontology,
            similarity_threshold=0.0
        )
        cube_min = analyzer_min.extract_semantic_cube(sample_document_segments)
        assert len(cube_min["segments"]) > 0, "Zero threshold should capture segments"

        # Maximum threshold (1.0) - should match almost nothing
        analyzer_max = SemanticAnalyzer(
            ontology=ontology,
            similarity_threshold=1.0
        )
        cube_max = analyzer_max.extract_semantic_cube(sample_document_segments)
        # High threshold = fewer concepts detected
        assert len(cube_max.get("concepts", [])) <= len(cube_min.get("concepts", []))

    def test_invalid_threshold_rejected(self):
        """Ensure out-of-range thresholds raise ValueError."""
        with pytest.raises(ValueError, match="similarity_threshold"):
            SemanticAnalyzer(
                ontology=MunicipalOntology(),
                similarity_threshold=-0.1  # Invalid: below 0.0
            )

        with pytest.raises(ValueError, match="similarity_threshold"):
            SemanticAnalyzer(
                ontology=MunicipalOntology(),
                similarity_threshold=1.5  # Invalid: above 1.0
            )

    def test_threshold_effect_monotonic(self, sample_document_segments):
        """Verify higher thresholds detect fewer concepts (monotonicity)."""
        ontology = MunicipalOntology()
        thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
        concept_counts = []

        for thresh in thresholds:
            analyzer = SemanticAnalyzer(ontology=ontology, similarity_threshold=thresh)
            cube = analyzer.extract_semantic_cube(sample_document_segments)
            concept_counts.append(len(cube.get("concepts", [])))

        # Assert monotonic decrease (or stable)
        for i in range(len(concept_counts) - 1):
            assert concept_counts[i] >= concept_counts[i+1], \
                f"Non-monotonic: counts={concept_counts}, thresholds={thresholds}"

    def test_reproducibility_same_threshold(self, sample_document_segments):
        """Verify bit-for-bit reproducibility with same threshold."""
        ontology = MunicipalOntology()

        analyzer1 = SemanticAnalyzer(ontology=ontology, similarity_threshold=0.3)
        cube1 = analyzer1.extract_semantic_cube(sample_document_segments)

        analyzer2 = SemanticAnalyzer(ontology=ontology, similarity_threshold=0.3)
        cube2 = analyzer2.extract_semantic_cube(sample_document_segments)

        assert cube1 == cube2, "Non-reproducible results with identical parameters"

    def test_max_features_effect(self, sample_document_segments):
        """Verify max_features controls vocabulary size."""
        ontology = MunicipalOntology()

        analyzer_small = SemanticAnalyzer(ontology=ontology, max_features=100)
        analyzer_large = SemanticAnalyzer(ontology=ontology, max_features=5000)

        # Vocabulary size should differ
        vocab_small = analyzer_small.vectorizer.fit_transform(sample_document_segments)
        vocab_large = analyzer_large.vectorizer.fit_transform(sample_document_segments)

        assert vocab_small.shape[1] <= 100, "max_features not respected (small)"
        assert vocab_large.shape[1] <= 5000, "max_features not respected (large)"
        assert vocab_small.shape[1] <= vocab_large.shape[1], \
            "Larger max_features should allow more features"
```

**Property Tested:**
- Monotonicity of threshold effect (epistemic property)
- Reproducibility (technical property)
- Boundary behavior (robustness property)

---

#### **Test Suite:** `tests/test_bayesian_updater_params.py`

**Method:** `BAYES.BayesianUpdater.update`

```python
import pytest
import numpy as np
from saaaaaa.analysis.bayesian_multilevel_system import (
    BayesianUpdater,
    ProbativeTest
)

class TestBayesianUpdaterParameterization:
    """Unit tests for Bayesian updater epistemic correctness."""

    @pytest.fixture
    def straw_in_the_wind_test(self):
        """Weak test: high sensitivity, low specificity."""
        return ProbativeTest(
            name="Straw in the wind",
            sensitivity=0.8,  # P(evidence | H)
            specificity=0.3   # P(~evidence | ~H)
        )

    @pytest.fixture
    def smoking_gun_test(self):
        """Strong test: low sensitivity, high specificity."""
        return ProbativeTest(
            name="Smoking gun",
            sensitivity=0.4,  # P(evidence | H)
            specificity=0.95  # P(~evidence | ~H)
        )

    def test_bayesian_update_prior_required(self):
        """Verify prior is required (no default makes epistemic sense)."""
        updater = BayesianUpdater()
        test = ProbativeTest(sensitivity=0.8, specificity=0.6)

        with pytest.raises(TypeError, match="prior"):
            updater.update(test=test, test_passed=True)  # Missing prior

    def test_prior_boundaries(self, straw_in_the_wind_test):
        """Test behavior at prior boundaries [0.0, 1.0]."""
        updater = BayesianUpdater()

        # Prior = 0.0 (impossible hypothesis)
        posterior_0 = updater.update(
            prior=0.0,
            test=straw_in_the_wind_test,
            test_passed=True
        )
        assert posterior_0 == 0.0, "Impossible prior should remain impossible"

        # Prior = 1.0 (certain hypothesis)
        posterior_1 = updater.update(
            prior=1.0,
            test=straw_in_the_wind_test,
            test_passed=False
        )
        # Even negative evidence shouldn't reduce certainty to zero instantly
        assert 0.0 < posterior_1 <= 1.0

    def test_positive_evidence_increases_posterior(
        self,
        straw_in_the_wind_test,
        smoking_gun_test
    ):
        """Verify positive evidence increases posterior (Bayesian property)."""
        updater = BayesianUpdater()
        prior = 0.5

        # Straw in the wind (weak test)
        posterior_weak = updater.update(prior, straw_in_the_wind_test, test_passed=True)
        assert posterior_weak > prior, "Positive evidence should increase belief"

        # Smoking gun (strong test)
        posterior_strong = updater.update(prior, smoking_gun_test, test_passed=True)
        assert posterior_strong > prior, "Strong positive evidence should increase belief"
        assert posterior_strong > posterior_weak, \
            "Stronger test should yield higher posterior"

    def test_negative_evidence_decreases_posterior(
        self,
        straw_in_the_wind_test,
        smoking_gun_test
    ):
        """Verify negative evidence decreases posterior (Bayesian property)."""
        updater = BayesianUpdater()
        prior = 0.5

        # Straw in the wind fails
        posterior_weak = updater.update(prior, straw_in_the_wind_test, test_passed=False)
        assert posterior_weak < prior, "Negative evidence should decrease belief"

        # Smoking gun fails (very damaging)
        posterior_strong = updater.update(prior, smoking_gun_test, test_passed=False)
        assert posterior_strong < prior
        # Failing a high-specificity test is very damaging
        assert posterior_strong < posterior_weak

    def test_reproducibility_bayesian_update(self, straw_in_the_wind_test):
        """Verify bit-for-bit reproducibility of Bayesian updates."""
        updater1 = BayesianUpdater()
        updater2 = BayesianUpdater()

        posterior1 = updater1.update(0.5, straw_in_the_wind_test, True)
        posterior2 = updater2.update(0.5, straw_in_the_wind_test, True)

        assert posterior1 == posterior2, "Bayesian update not reproducible"

    def test_sequential_update_consistency(self):
        """Verify sequential updates obey Bayesian algebra."""
        updater = BayesianUpdater()
        test1 = ProbativeTest(sensitivity=0.8, specificity=0.7)
        test2 = ProbativeTest(sensitivity=0.6, specificity=0.9)

        # Sequential update
        posterior_1 = updater.update(0.5, test1, True)
        posterior_2 = updater.update(posterior_1, test2, True)

        # Verify posterior in valid range
        assert 0.0 <= posterior_2 <= 1.0
        # Verify two positive tests increased belief
        assert posterior_2 > 0.5

    def test_epistemic_interpretation_preserved(self, smoking_gun_test):
        """
        EPISTEMIC TEST: Verify 'smoking gun' interpretation preserved.

        A smoking gun test (high specificity) passing should yield high posterior
        even with low prior, reflecting the evidential meaning of 'smoking gun'.
        """
        updater = BayesianUpdater()

        # Low prior (skeptical starting point)
        prior = 0.1

        # Smoking gun passes (should dramatically increase belief)
        posterior = updater.update(prior, smoking_gun_test, test_passed=True)

        # Epistemic claim: smoking gun should yield >0.5 posterior
        # even from skeptical 0.1 prior
        assert posterior > 0.5, \
            "Smoking gun failed to sufficiently update low prior—epistemic interpretation broken"
```

**Property Tested:**
- Bayesian coherence (epistemic property: priors + evidence → posteriors)
- Monotonicity of evidence strength (epistemic property)
- Reproducibility (technical property)
- **CRITICAL:** Epistemic interpretation preservation

---

#### **Test Suite:** `tests/test_dispersion_engine_params.py`

**Method:** `BAYES.DispersionEngine.calculate_dispersion_penalty`

```python
import pytest
import numpy as np
from saaaaaa.analysis.bayesian_multilevel_system import DispersionEngine

class TestDispersionEngineParameterization:
    """Unit tests for dispersion penalty parameterization."""

    def test_default_thresholds_from_json(self, config_loader):
        """Verify default thresholds load from canonical JSON."""
        cv_thresh = config_loader.get_method_parameter(
            "BAYES.DE.calc_disp_penalty_v1",
            "cv_threshold"
        )
        max_gap = config_loader.get_method_parameter(
            "BAYES.DE.calc_disp_penalty_v1",
            "max_gap_threshold"
        )
        gini_thresh = config_loader.get_method_parameter(
            "BAYES.DE.calc_disp_penalty_v1",
            "gini_threshold"
        )

        assert cv_thresh == 0.3
        assert max_gap == 1.0
        assert gini_thresh == 0.3

    def test_zero_dispersion_yields_zero_penalty(self):
        """Perfect agreement (zero dispersion) should yield zero penalty."""
        engine = DispersionEngine(
            cv_threshold=0.3,
            max_gap_threshold=1.0,
            gini_threshold=0.3
        )

        # All scores identical = zero dispersion
        scores = [2.0, 2.0, 2.0, 2.0]
        penalty = engine.calculate_dispersion_penalty(scores)

        assert penalty == 0.0, "Zero dispersion should yield zero penalty"

    def test_high_dispersion_yields_nonzero_penalty(self):
        """High dispersion should yield non-zero penalty."""
        engine = DispersionEngine(
            cv_threshold=0.3,
            max_gap_threshold=1.0,
            gini_threshold=0.3
        )

        # High dispersion: wide range
        scores = [0.0, 1.0, 2.0, 3.0]
        penalty = engine.calculate_dispersion_penalty(scores)

        assert penalty > 0.0, "High dispersion should yield non-zero penalty"

    def test_threshold_effect_monotonic(self):
        """Lower thresholds → more penalties (monotonicity)."""
        scores = [1.0, 1.5, 2.0, 2.5, 3.0]  # Moderate dispersion

        # Strict thresholds (low values)
        engine_strict = DispersionEngine(
            cv_threshold=0.1,
            max_gap_threshold=0.5,
            gini_threshold=0.1
        )

        # Lenient thresholds (high values)
        engine_lenient = DispersionEngine(
            cv_threshold=0.5,
            max_gap_threshold=2.0,
            gini_threshold=0.5
        )

        penalty_strict = engine_strict.calculate_dispersion_penalty(scores)
        penalty_lenient = engine_lenient.calculate_dispersion_penalty(scores)

        assert penalty_strict >= penalty_lenient, \
            "Stricter thresholds should yield equal or higher penalties"

    def test_penalty_proportional_to_dispersion(self):
        """Penalty should increase with dispersion (proportionality)."""
        engine = DispersionEngine(cv_threshold=0.3, max_gap_threshold=1.0, gini_threshold=0.3)

        # Low dispersion
        scores_low = [1.8, 2.0, 2.2]
        penalty_low = engine.calculate_dispersion_penalty(scores_low)

        # High dispersion
        scores_high = [0.5, 2.0, 3.5]
        penalty_high = engine.calculate_dispersion_penalty(scores_high)

        assert penalty_high > penalty_low, \
            "Higher dispersion should yield higher penalty"

    def test_epistemic_property_dispersion_diagnostic(self):
        """
        EPISTEMIC TEST: Dispersion penalty detects score disagreement.

        Epistemic claim: If micro-level scores disagree substantively,
        dispersion penalty should flag this as a coherence issue.
        """
        engine = DispersionEngine(cv_threshold=0.3, max_gap_threshold=1.0, gini_threshold=0.3)

        # Substantive disagreement (scores span full range)
        scores_disagree = [0.0, 1.5, 3.0]
        penalty_disagree = engine.calculate_dispersion_penalty(scores_disagree)

        # Penalty should be non-trivial (>0.05 on 0-1 scale)
        assert penalty_disagree > 0.05, \
            "Substantive disagreement not flagged by dispersion penalty"
```

**Property Tested:**
- Monotonicity (stricter thresholds → more penalties)
- Proportionality (more dispersion → higher penalty)
- **EPISTEMIC:** Dispersion as diagnostic of score coherence

---

### 7.1.3 Comprehensive Unit Test Matrix

| Method Canonical ID | Test File | Properties Tested | Priority |
|---------------------|-----------|------------------|----------|
| `ANLZ.SA.extract_cube_v1` | `test_semantic_analyzer_params.py` | Monotonicity, Reproducibility, Boundary | HIGH |
| `ANLZ.PA.detect_bottleneck_v1` | `test_performance_analyzer_params.py` | Threshold decision logic, Reproducibility | HIGH |
| `BAYES.BU.update_v1` | `test_bayesian_updater_params.py` | Bayesian coherence, Epistemic interpretation | CRITICAL |
| `BAYES.DE.calc_disp_penalty_v1` | `test_dispersion_engine_params.py` | Monotonicity, Proportionality | HIGH |
| `BAYES.PC.compare_peers_v1` | `test_peer_calibrator_params.py` | Statistical validity, z-score interpretation | HIGH |
| `BAYES.BRU.agg_micro_meso_v1` | `test_bayesian_rollup_params.py` | Aggregation correctness, Penalty application | HIGH |
| `BAYES.CS.scan_mm_v1` | `test_contradiction_scanner_params.py` | Coherence detection, Threshold sensitivity | MEDIUM |
| `SCORE.TYPE_A.compute_v1` | `test_scoring_type_a_params.py` | Scoring rule correctness, Reproducibility | HIGH |
| `SCORE.TYPE_B.compute_v1` | `test_scoring_type_b_params.py` | Scoring rule correctness | MEDIUM |
| `CALIBR.CO.calibrate_v1` | `test_calibration_orchestrator_params.py` | End-to-end calibration, Reproducibility | CRITICAL |
| `CAUSAL.EXTR.extract_hier_v2.1` | `test_causal_extractor_params.py` | Pattern matching, Threshold effects, Reproducibility | CRITICAL |
| `CAUSAL.BMI.infer_mech_v1` | `test_mechanism_inference_params.py` | Bayesian prior application, Convergence, Epistemic claims | CRITICAL |
| `EXEC.QPO.optimize_path_v1` | `test_quantum_optimizer_params.py` | Computational properties (no epistemic impact) | LOW |

**Total Unit Tests:** ~150 test functions across 13 test files

---

## PHASE 7.2: INTEGRATION / PIPELINE TESTS

### 7.2.1 Core Analysis Pipeline Tests

#### **Test Suite:** `tests/integration/test_d1_q1_pipeline_parameterization.py`

**Pipeline:** D1-Q1 (Baseline Indicators) complete analysis

```python
import pytest
from pathlib import Path
from saaaaaa.core.orchestrator.core import analyze_pdm_with_orchestrator
from saaaaaa.utils.method_config_loader import MethodConfigLoader

class TestD1Q1PipelineParameterization:
    """Integration tests for D1-Q1 pipeline with varied parameters."""

    @pytest.fixture
    def sample_pdm_document(self):
        return Path("tests/fixtures/sample_pdm_2024.pdf")

    @pytest.fixture
    def baseline_config_loader(self):
        return MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")

    def test_pipeline_with_default_parameters(
        self,
        sample_pdm_document,
        baseline_config_loader
    ):
        """Run full D1-Q1 pipeline with default parameters from JSON."""
        result = analyze_pdm_with_orchestrator(
            document_path=sample_pdm_document,
            question_id="D1_Q1",
            config_loader=baseline_config_loader
        )

        assert result["question_id"] == "D1_Q1"
        assert "score" in result
        assert 0.0 <= result["score"] <= 3.0
        assert "evidence" in result

    def test_pipeline_stability_with_conservative_thresholds(
        self,
        sample_pdm_document
    ):
        """
        CONFIRMATORY PIPELINE TEST: Conservative thresholds should be stable.

        Epistemic claim: Confirmatory analysis should produce stable results
        under small threshold perturbations.
        """
        results = []

        # Run with slightly varied thresholds
        for threshold_variant in [0.68, 0.70, 0.72]:  # ±2% around default 0.70
            config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
            # Override hard threshold for causal extraction
            config.override_parameter(
                "CAUSAL.EXTR.extract_hier_v2.1",
                "confidence_threshold_hard",
                threshold_variant
            )

            result = analyze_pdm_with_orchestrator(
                document_path=sample_pdm_document,
                question_id="D1_Q1",
                config_loader=config
            )
            results.append(result["score"])

        # Assert stability: max variance <= 5% of score range
        score_variance = max(results) - min(results)
        assert score_variance <= 0.15, \
            f"Confirmatory pipeline unstable under small perturbations: {results}"

    def test_pipeline_sensitivity_with_exploratory_thresholds(
        self,
        sample_pdm_document
    ):
        """
        EXPLORATORY PIPELINE TEST: Exploratory thresholds should affect coverage.

        Epistemic claim: Lowering soft threshold should increase concept coverage
        (more concepts detected, even if lower confidence).
        """
        config_strict = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        config_strict.override_parameter(
            "CAUSAL.EXTR.extract_hier_v2.1",
            "confidence_threshold_soft",
            0.70  # High soft threshold (strict)
        )

        config_lenient = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        config_lenient.override_parameter(
            "CAUSAL.EXTR.extract_hier_v2.1",
            "confidence_threshold_soft",
            0.40  # Low soft threshold (lenient)
        )

        result_strict = analyze_pdm_with_orchestrator(
            sample_pdm_document, "D1_Q1", config_strict
        )
        result_lenient = analyze_pdm_with_orchestrator(
            sample_pdm_document, "D1_Q1", config_lenient
        )

        # Lenient threshold should detect more concepts (higher coverage)
        coverage_strict = len(result_strict["evidence"].get("concepts", []))
        coverage_lenient = len(result_lenient["evidence"].get("concepts", []))

        assert coverage_lenient >= coverage_strict, \
            "Lenient threshold did not increase concept coverage as expected"

    def test_pipeline_reproducibility_same_config(self, sample_pdm_document):
        """Verify pipeline produces identical results with same configuration."""
        config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")

        result1 = analyze_pdm_with_orchestrator(
            sample_pdm_document, "D1_Q1", config
        )
        result2 = analyze_pdm_with_orchestrator(
            sample_pdm_document, "D1_Q1", config
        )

        assert result1["score"] == result2["score"], \
            "Pipeline not reproducible with identical configuration"
        assert result1["evidence"] == result2["evidence"]
```

**Properties Tested:**
- **Confirmatory stability** (small perturbations → stable results)
- **Exploratory sensitivity** (threshold changes → coverage changes)
- **Reproducibility**

---

#### **Test Suite:** `tests/integration/test_full_questionnaire_pipeline.py`

**Pipeline:** Complete 300-question analysis with parameter variations

```python
class TestFullQuestionnairePipeline:
    """Integration tests for complete questionnaire analysis."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_300_questions_with_defaults(self, sample_pdm):
        """Run all 300 questions with default parameters (baseline)."""
        config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")

        results = analyze_complete_questionnaire(sample_pdm, config)

        assert len(results) == 300
        assert all("score" in r for r in results)
        assert all(0.0 <= r["score"] <= 3.0 for r in results)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_parameter_sweep_critical_thresholds(self, sample_pdm):
        """
        ROBUSTNESS TEST: Sweep critical thresholds, verify stable macro-level results.

        Tests that macro-level aggregated scores are robust to micro-level
        threshold variations (confirmatory robustness property).
        """
        threshold_variants = [0.65, 0.70, 0.75]  # ±5% around default 0.70
        macro_scores = []

        for threshold in threshold_variants:
            config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
            config.override_parameter(
                "CAUSAL.EXTR.extract_hier_v2.1",
                "confidence_threshold_hard",
                threshold
            )

            results = analyze_complete_questionnaire(sample_pdm, config)
            macro_score = aggregate_to_macro_level(results)
            macro_scores.append(macro_score)

        # Macro-level should be stable (variance <= 3%)
        variance = max(macro_scores) - min(macro_scores)
        assert variance <= 0.09, \
            f"Macro-level not robust to threshold variations: {macro_scores}"
```

---

### 7.2.2 Integration Test Matrix

| Pipeline | Test File | Parameter Variations Tested | Priority |
|----------|-----------|---------------------------|----------|
| D1-Q1 (Baseline) | `test_d1_q1_pipeline_parameterization.py` | Causal extraction thresholds, semantic similarity | CRITICAL |
| D2-Q1 (Activities) | `test_d2_q1_pipeline_parameterization.py` | Mechanism inference priors, convergence criteria | HIGH |
| D3-Q1 (Products) | `test_d3_q1_pipeline_parameterization.py` | Scoring modality thresholds, aggregation penalties | HIGH |
| Full 300Q | `test_full_questionnaire_pipeline.py` | Multi-level threshold sweep, macro-level robustness | CRITICAL |
| Calibration | `test_calibration_pipeline_integration.py` | Calibration context variations, method compatibility | HIGH |

**Total Integration Tests:** ~30 test functions across 5 test suites

---

## PHASE 7.3: PROPERTY-BASED / GENERATIVE TESTS

### 7.3.1 Property-Based Testing with Hypothesis

**Library:** `hypothesis` (Python property-based testing)

#### **Test Suite:** `tests/property/test_bayesian_properties.py`

```python
from hypothesis import given, strategies as st
import pytest
from saaaaaa.analysis.bayesian_multilevel_system import BayesianUpdater, ProbativeTest

class TestBayesianMathematicalProperties:
    """Property-based tests for Bayesian inference properties."""

    @given(
        prior=st.floats(min_value=0.0, max_value=1.0),
        sensitivity=st.floats(min_value=0.0, max_value=1.0),
        specificity=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_posterior_in_valid_range(self, prior, sensitivity, specificity):
        """
        PROPERTY: Posterior must always be in [0, 1] for valid inputs.

        Mathematical invariant of Bayesian updating.
        """
        updater = BayesianUpdater()
        test = ProbativeTest(sensitivity=sensitivity, specificity=specificity)

        posterior_pos = updater.update(prior, test, test_passed=True)
        posterior_neg = updater.update(prior, test, test_passed=False)

        assert 0.0 <= posterior_pos <= 1.0, \
            f"Posterior out of range: {posterior_pos} (prior={prior})"
        assert 0.0 <= posterior_neg <= 1.0, \
            f"Posterior out of range: {posterior_neg} (prior={prior})"

    @given(
        prior=st.floats(min_value=0.01, max_value=0.99),
        sensitivity=st.floats(min_value=0.5, max_value=1.0),  # Good test
        specificity=st.floats(min_value=0.5, max_value=1.0)
    )
    def test_positive_evidence_increases_belief(self, prior, sensitivity, specificity):
        """
        PROPERTY: Positive evidence from good test increases posterior.

        Fundamental Bayesian property.
        """
        updater = BayesianUpdater()
        test = ProbativeTest(sensitivity=sensitivity, specificity=specificity)

        posterior = updater.update(prior, test, test_passed=True)

        # Positive evidence from a decent test should increase belief
        # (may not hold for very weak tests, hence constrained strategy)
        assert posterior >= prior, \
            f"Positive evidence decreased belief: prior={prior}, posterior={posterior}"

    @given(
        prior=st.floats(min_value=0.01, max_value=0.99),
        test_quality=st.floats(min_value=0.5, max_value=1.0)
    )
    def test_stronger_evidence_yields_stronger_update(self, prior, test_quality):
        """
        PROPERTY: Higher quality test yields larger belief update.

        Test quality = (sensitivity + specificity) / 2
        """
        updater = BayesianUpdater()

        weak_test = ProbativeTest(sensitivity=0.6, specificity=0.6)
        strong_test = ProbativeTest(sensitivity=0.9, specificity=0.9)

        posterior_weak = updater.update(prior, weak_test, test_passed=True)
        posterior_strong = updater.update(prior, strong_test, test_passed=True)

        # Stronger test should yield larger update
        assert abs(posterior_strong - prior) >= abs(posterior_weak - prior), \
            f"Stronger test yielded weaker update"

    @given(
        prior=st.floats(min_value=0.0, max_value=1.0),
        sensitivity=st.floats(min_value=0.0, max_value=1.0),
        specificity=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_double_negation_returns_to_prior(self, prior, sensitivity, specificity):
        """
        PROPERTY: Pos then neg evidence (or vice versa) partially cancels.

        Not exact return, but should be closer to prior than single update.
        """
        updater = BayesianUpdater()
        test = ProbativeTest(sensitivity=sensitivity, specificity=specificity)

        # Update with positive evidence
        posterior_pos = updater.update(prior, test, test_passed=True)
        # Then update with negative evidence
        posterior_final = updater.update(posterior_pos, test, test_passed=False)

        # Final should be between prior and posterior_pos (partial cancellation)
        if posterior_pos > prior:
            assert prior <= posterior_final <= posterior_pos + 0.01  # Small numerical tolerance
        elif posterior_pos < prior:
            assert posterior_pos - 0.01 <= posterior_final <= prior
```

**Properties Tested:**
- Range invariance [0, 1]
- Monotonicity of evidence
- Proportionality of test strength
- Partial cancellation (reversibility)

---

#### **Test Suite:** `tests/property/test_dispersion_properties.py`

```python
from hypothesis import given, strategies as st
from saaaaaa.analysis.bayesian_multilevel_system import DispersionEngine

class TestDispersionMathematicalProperties:
    """Property-based tests for dispersion metrics."""

    @given(
        scores=st.lists(
            st.floats(min_value=0.0, max_value=3.0),
            min_size=2,
            max_size=20
        )
    )
    def test_cv_non_negative(self, scores):
        """PROPERTY: Coefficient of variation is always non-negative."""
        engine = DispersionEngine()
        cv = engine.calculate_cv(scores)
        assert cv >= 0.0, f"CV negative: {cv} for scores {scores}"

    @given(
        scores=st.lists(
            st.floats(min_value=0.0, max_value=3.0),
            min_size=2,
            max_size=20
        )
    )
    def test_gini_bounded(self, scores):
        """PROPERTY: Gini coefficient is always in [0, 1]."""
        engine = DispersionEngine()
        gini = engine.calculate_gini(scores)
        assert 0.0 <= gini <= 1.0, f"Gini out of range: {gini}"

    @given(
        score=st.floats(min_value=0.0, max_value=3.0),
        count=st.integers(min_value=2, max_value=10)
    )
    def test_zero_dispersion_for_identical_scores(self, score, count):
        """PROPERTY: Identical scores yield zero dispersion."""
        engine = DispersionEngine()
        scores = [score] * count

        cv = engine.calculate_cv(scores)
        gini = engine.calculate_gini(scores)
        penalty = engine.calculate_dispersion_penalty(scores)

        assert cv == 0.0, "CV non-zero for identical scores"
        assert gini == 0.0, "Gini non-zero for identical scores"
        assert penalty == 0.0, "Penalty non-zero for identical scores"

    @given(
        scores=st.lists(
            st.floats(min_value=0.0, max_value=3.0),
            min_size=2,
            max_size=20
        ).filter(lambda s: len(set(s)) > 1)  # Ensure non-identical
    )
    def test_adding_extreme_increases_dispersion(self, scores):
        """PROPERTY: Adding an extreme value increases dispersion."""
        engine = DispersionEngine()

        gini_before = engine.calculate_gini(scores)

        # Add extreme value
        scores_with_extreme = scores + [0.0]  # Add minimum
        gini_after = engine.calculate_gini(scores_with_extreme)

        # Adding extreme should increase or maintain Gini
        assert gini_after >= gini_before - 1e-6, \
            f"Adding extreme decreased Gini: before={gini_before}, after={gini_after}"
```

---

### 7.3.2 Property Test Matrix

| Method | Property File | Properties Tested |
|--------|---------------|------------------|
| Bayesian Updater | `test_bayesian_properties.py` | Range, Monotonicity, Reversibility |
| Dispersion Engine | `test_dispersion_properties.py` | Non-negativity, Bounds, Monotonicity |
| Scoring TYPE_A | `test_scoring_properties.py` | Determinism, Monotonicity, Range |
| Contradiction Scanner | `test_contradiction_properties.py` | Coherence detection, Symmetry |
| Semantic Analyzer | `test_semantic_properties.py` | Similarity symmetry, Triangle inequality |

**Total Property Tests:** ~50 property-based tests (each runs 100-1000 random examples)

---

## PHASE 7.4: REGRESSION TESTS

### 7.4.1 Golden Master Regression Tests

**Concept:** Capture known-good outputs with previous YAML configuration, ensure new JSON configuration produces identical results.

#### **Test Suite:** `tests/regression/test_yaml_to_json_regression.py`

```python
import pytest
import json
from pathlib import Path

class TestYAMLToJSONMigrationRegression:
    """Regression tests ensuring YAML→JSON migration preserves behavior."""

    @pytest.fixture
    def golden_master_results(self):
        """Load pre-computed results from YAML configuration era."""
        with open("tests/fixtures/golden_master_results.json") as f:
            return json.load(f)

    def test_d1_q1_score_matches_golden_master(self, golden_master_results):
        """Verify D1-Q1 score matches pre-migration golden master."""
        config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        result = analyze_pdm_with_orchestrator(
            "tests/fixtures/sample_pdm_2024.pdf",
            "D1_Q1",
            config
        )

        expected_score = golden_master_results["D1_Q1"]["score"]
        actual_score = result["score"]

        assert abs(actual_score - expected_score) < 1e-6, \
            f"Score diverged: expected={expected_score}, actual={actual_score}"

    def test_bayesian_posterior_matches_golden_master(self, golden_master_results):
        """Verify Bayesian posteriors match pre-migration values."""
        config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        updater = BayesianUpdater(config_loader=config)

        for test_case in golden_master_results["bayesian_test_cases"]:
            posterior = updater.update(
                test_case["prior"],
                test_case["test"],
                test_case["test_passed"]
            )

            expected = test_case["expected_posterior"]
            assert abs(posterior - expected) < 1e-10, \
                f"Posterior diverged for test case {test_case['name']}"

    def test_full_pipeline_output_hash_matches(self, golden_master_results):
        """Verify full pipeline output hash matches (comprehensive regression)."""
        config = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        result = analyze_complete_questionnaire(
            "tests/fixtures/sample_pdm_2024.pdf",
            config
        )

        # Compute hash of complete output
        import hashlib
        output_json = json.dumps(result, sort_keys=True)
        output_hash = hashlib.sha256(output_json.encode()).hexdigest()

        expected_hash = golden_master_results["full_pipeline_hash"]
        assert output_hash == expected_hash, \
            f"Full pipeline output changed: expected={expected_hash}, actual={output_hash}"
```

**Golden Master Generation Script:**

```bash
# Before migration, generate golden master results
python scripts/generate_golden_master.py \
  --config config/schemas/dereck_beach/config.yaml \
  --output tests/fixtures/golden_master_results.json
```

---

### 7.4.2 Regression Test Matrix

| Test | Golden Master Source | Priority |
|------|---------------------|----------|
| D1-Q1 score | `golden_master_results.json` | CRITICAL |
| D2-Q1 causal DAG | `golden_master_results.json` | HIGH |
| D3-Q1 product indicators | `golden_master_results.json` | HIGH |
| Bayesian posteriors | `golden_master_results.json` | CRITICAL |
| Dispersion penalties | `golden_master_results.json` | MEDIUM |
| Full 300Q pipeline hash | `golden_master_results.json` | CRITICAL |

**Total Regression Tests:** ~20 golden master comparisons

---

## PHASE 7.5: TEST EXECUTION AND REPORTING

### 7.5.1 Test Execution Matrix

**Command Structure:**

```bash
# Unit tests only (fast)
pytest tests/test_*_params.py -v --tb=short

# Integration tests (slow)
pytest tests/integration/ -v --tb=short -m integration

# Property-based tests (comprehensive)
pytest tests/property/ -v --tb=short -m property

# Regression tests (golden master validation)
pytest tests/regression/ -v --tb=short -m regression

# Full test suite
pytest tests/ -v --tb=short --cov=src/saaaaaa --cov-report=html

# Critical tests only (pre-commit)
pytest tests/ -v -m critical
```

**Test Markers:**

```python
# In pytest.ini
[pytest]
markers =
    critical: Critical tests that must pass before any commit
    integration: Integration tests (slow)
    property: Property-based tests (hypothesis)
    regression: Regression tests (golden master)
    slow: Slow tests (skip in development)
    epistemic: Tests validating epistemic properties
```

---

### 7.5.2 Test Coverage Requirements

| Coverage Type | Target | Measurement |
|---------------|--------|-------------|
| Statement Coverage | 95% | pytest-cov |
| Branch Coverage | 90% | pytest-cov --cov-branch |
| Parameter Coverage | 100% | All parameters in JSON tested |
| Epistemic Property Coverage | 80% | Manual audit of epistemic tests |

**Coverage Report Generation:**

```bash
pytest tests/ --cov=src/saaaaaa --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html
```

---

### 7.5.3 Continuous Integration (CI) Configuration

**.github/workflows/parameterization_tests.yml:**

```yaml
name: Parameterization Testing Suite

on:
  push:
    branches: [main, develop, claude/*]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/test_*_params.py -v --tb=short --cov=src/saaaaaa
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements-all.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short -m integration

  property-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt hypothesis
      - name: Run property-based tests
        run: pytest tests/property/ -v --tb=short -m property

  regression-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements-all.txt
      - name: Download golden master
        run: wget https://artifacts.example.com/golden_master_results.json -O tests/fixtures/golden_master_results.json
      - name: Run regression tests
        run: pytest tests/regression/ -v --tb=short -m regression
```

---

## PHASE 7.6: EPISTEMIC VALIDATION TESTS

### 7.6.1 Confirmatory vs. Exploratory Validation

**Concept:** Separate test suites validate that:
- Confirmatory methods are **stable** under parameter perturbations
- Exploratory methods are **sensitive** to parameter changes (as intended)

#### **Test Suite:** `tests/epistemic/test_confirmatory_stability.py`

```python
class TestConfirmatoryMethodStability:
    """Validate confirmatory methods are stable under perturbations."""

    def test_bayesian_mechanism_inference_stable(self):
        """
        EPISTEMIC TEST: Bayesian mechanism inference is confirmatory.

        Claim: Small changes to prior probabilities should NOT dramatically
        change posterior conclusions if evidence is strong.
        """
        # Strong evidence scenario
        evidence = load_strong_evidence_scenario()

        priors_base = {
            "administrativo": 0.30,
            "tecnico": 0.25,
            "financiero": 0.20,
            "politico": 0.15,
            "mixto": 0.10
        }

        # Perturb priors slightly (±5%)
        priors_variant = {
            "administrativo": 0.32,
            "tecnico": 0.23,
            "financiero": 0.21,
            "politico": 0.14,
            "mixto": 0.10
        }

        inference_base = BayesianMechanismInference(priors=priors_base)
        inference_variant = BayesianMechanismInference(priors=priors_variant)

        posterior_base = inference_base.infer(evidence)
        posterior_variant = inference_variant.infer(evidence)

        # With strong evidence, posteriors should be similar
        for mechanism_type in priors_base.keys():
            diff = abs(
                posterior_base[mechanism_type] -
                posterior_variant[mechanism_type]
            )
            assert diff < 0.10, \
                f"Confirmatory method unstable: {mechanism_type} diff={diff}"

    def test_scoring_type_a_stable_under_threshold_perturbations(self):
        """
        EPISTEMIC TEST: TYPE_A scoring (confirmatory) is threshold-stable.

        Claim: Small threshold changes should not flip quality classifications
        when evidence is clear (well above or below thresholds).
        """
        # Clear high-quality evidence (4/4 elements present)
        evidence_high = {"elements_present": 4, "total_elements": 4}

        thresholds = [0.83, 0.85, 0.87]  # ±2% around EXCELENTE threshold 0.85
        quality_levels = []

        for threshold in thresholds:
            scorer = ScoringTYPE_A(excelente_threshold=threshold)
            result = scorer.compute(evidence_high)
            quality_levels.append(result["quality_level"])

        # All should classify as EXCELENTE (stable)
        assert all(q == "EXCELENTE" for q in quality_levels), \
            f"Confirmatory scoring unstable: {quality_levels}"
```

#### **Test Suite:** `tests/epistemic/test_exploratory_sensitivity.py`

```python
class TestExploratoryMethodSensitivity:
    """Validate exploratory methods are appropriately sensitive."""

    def test_semantic_analyzer_sensitive_to_threshold(self):
        """
        EPISTEMIC TEST: Semantic analysis (exploratory) is threshold-sensitive.

        Claim: Lowering similarity threshold should increase concept coverage
        (exploratory methods should be tunable for different discovery goals).
        """
        text = load_sample_policy_text()
        ontology = MunicipalOntology()

        thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]
        concept_counts = []

        for threshold in thresholds:
            analyzer = SemanticAnalyzer(
                ontology=ontology,
                similarity_threshold=threshold
            )
            cube = analyzer.extract_semantic_cube([text])
            concept_counts.append(len(cube["concepts"]))

        # Assert monotonic decrease (sensitivity)
        for i in range(len(concept_counts) - 1):
            assert concept_counts[i] >= concept_counts[i+1], \
                f"Exploratory method not sensitive: {concept_counts}"

        # Assert substantial range (not flat)
        coverage_range = max(concept_counts) - min(concept_counts)
        assert coverage_range > 5, \
            f"Exploratory method insufficiently sensitive: range={coverage_range}"
```

---

### 7.6.2 Causal vs. Associational Validation

**Test:** Ensure causal inference methods respect causal assumptions

```python
class TestCausalInferenceValidity:
    """Validate causal methods respect causal assumptions."""

    def test_causal_dag_acyclicity_enforced(self):
        """
        EPISTEMIC TEST: Causal DAG extraction enforces acyclicity.

        Claim: Causal graphs must be directed acyclic graphs (DAGs).
        Cyclical relationships violate causal logic.
        """
        extractor = CausalExtractor()

        # Text with cyclical reference (should be rejected or broken)
        text_with_cycle = (
            "Producto A conduce a Resultado B. "
            "Resultado B conduce a Actividad C. "
            "Actividad C conduce a Producto A."  # Cycle!
        )

        causal_graph = extractor.extract_causal_hierarchy(text_with_cycle)

        # Check acyclicity
        assert nx.is_directed_acyclic_graph(causal_graph), \
            "Causal extractor allowed cyclical graph"

    def test_causal_order_respects_eslabon_hierarchy(self):
        """
        EPISTEMIC TEST: Causal chain respects eslabon order.

        Claim: Insumos → Actividades → Productos → Resultados → Impactos
        This order is foundational to causal logic in policy theory.
        """
        extractor = CausalExtractor()

        # Well-formed text
        text = (
            "Diagnóstico de desempleo (Insumo). "
            "Capacitación laboral (Actividad). "
            "500 personas capacitadas (Producto). "
            "Reducción de tasa de desempleo (Resultado). "
            "Crecimiento económico sostenible (Impacto)."
        )

        causal_graph = extractor.extract_causal_hierarchy(text)

        # Verify topological order matches eslabon hierarchy
        expected_order = ["Insumos", "Actividades", "Productos", "Resultados", "Impactos"]
        actual_order = [
            node["eslabon"]
            for node in nx.topological_sort(causal_graph)
        ]

        # Check order preserved
        for i, eslabon in enumerate(expected_order):
            if eslabon in actual_order:
                assert actual_order.index(eslabon) >= i, \
                    f"Causal order violated: {actual_order}"
```

---

## SUMMARY

### Test Suite Statistics

| Test Type | Test Files | Test Functions | Estimated Runtime |
|-----------|-----------|----------------|------------------|
| Unit Tests | 13 | ~150 | 30 seconds |
| Integration Tests | 5 | ~30 | 5 minutes |
| Property-Based Tests | 5 | ~50 (×100 examples each) | 10 minutes |
| Regression Tests | 1 | ~20 | 15 minutes |
| Epistemic Validation Tests | 2 | ~15 | 5 minutes |
| **TOTAL** | **26** | **~265** | **~35 minutes** |

### Coverage Targets

- **Unit Test Coverage:** 100% of parameterized methods
- **Epistemic Property Coverage:** 80% of inferential/confirmatory methods
- **Regression Coverage:** 100% of golden master behaviors

### Key Epistemic Properties Validated

1. **Bayesian Coherence:** Priors + evidence → valid posteriors
2. **Confirmatory Stability:** Small parameter perturbations → stable conclusions
3. **Exploratory Sensitivity:** Threshold tuning → coverage tuning
4. **Causal Validity:** DAG acyclicity, eslabon hierarchy
5. **Aggregation Correctness:** Penalties apply correctly, reproducible aggregation
6. **Monotonicity:** Threshold/penalty relationships preserve expected ordering
7. **Reproducibility:** Bit-for-bit identical results with same parameters

### Implementation Priority

**Phase 1 (Week 1):** Unit tests for CRITICAL methods
- Bayesian updater
- Causal extractor
- Scoring modalities
- Calibration orchestrator

**Phase 2 (Week 2):** Integration tests
- D1-Q1, D2-Q1, D3-Q1 pipelines
- Full 300Q pipeline

**Phase 3 (Week 3):** Property-based and epistemic tests
- Bayesian properties
- Confirmatory/exploratory validation
- Causal validity

**Phase 4 (Week 4):** Regression tests and CI integration
- Golden master generation
- CI pipeline setup
- Coverage reporting

---

**Prepared by:** Claude (Senior Research Engineer - AI Agent)
**Date:** 2025-11-13
**Status:** READY FOR IMPLEMENTATION
