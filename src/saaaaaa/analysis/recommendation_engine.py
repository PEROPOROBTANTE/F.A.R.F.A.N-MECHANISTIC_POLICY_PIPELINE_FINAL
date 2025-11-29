# recommendation_engine.py - Rule-Based Recommendation Engine
"""
Recommendation Engine - Multi-Level Rule-Based Recommendations
================================================================

This module implements a rule-based recommendation engine that:
1. Loads and validates recommendation rules from JSON files
2. Evaluates conditions against score data at MICRO, MESO, and MACRO levels
3. Generates actionable recommendations with specific interventions
4. Renders templates with context-specific variable substitution

Supports three levels of recommendations:
- MICRO: Question-level recommendations (PA-DIM combinations)
- MESO: Cluster-level recommendations (CL01-CL04)
- MACRO: Plan-level strategic recommendations

Author: Integration Team
Version: 2.0.0
Python: 3.10+
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

logger = logging.getLogger(__name__)

_REQUIRED_ENHANCED_FEATURES = {
    "template_parameterization",
    "execution_logic",
    "measurable_indicators",
    "unambiguous_time_horizons",
    "testable_verification",
    "cost_tracking",
    "authority_mapping",
}

# ============================================================================
# DATA STRUCTURES FOR RECOMMENDATIONS
# ============================================================================

@dataclass
class Recommendation:
    """
    Structured recommendation with full intervention details.

    Supports both v1.0 (simple) and v2.0 (enhanced with 7 advanced features):
    1. Template parameterization
    2. Execution logic
    3. Measurable indicators
    4. Unambiguous time horizons
    5. Testable verification
    6. Cost tracking
    7. Authority mapping
    """
    rule_id: str
    level: str  # MICRO, MESO, or MACRO
    problem: str
    intervention: str
    indicator: dict[str, Any]
    responsible: dict[str, Any]
    horizon: dict[str, Any]  # Changed from Dict[str, str] to support enhanced fields
    verification: list[Any]  # Changed from List[str] to support structured verification
    metadata: dict[str, Any] = field(default_factory=dict)

    # Enhanced fields (v2.0) - optional for backward compatibility
    execution: dict[str, Any] | None = None
    budget: dict[str, Any] | None = None
    template_id: str | None = None
    template_params: dict[str, Any] | None = None

    @calibrated_method("saaaaaa.analysis.recommendation_engine.Recommendation.to_dict")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}

@dataclass
class RecommendationSet:
    """
    Collection of recommendations with metadata
    """
    level: str
    recommendations: list[Recommendation]
    generated_at: str
    total_rules_evaluated: int
    rules_matched: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationSet.to_dict")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'level': self.level,
            'recommendations': [r.to_dict() for r in self.recommendations],
            'generated_at': self.generated_at,
            'total_rules_evaluated': self.total_rules_evaluated,
            'rules_matched': self.rules_matched,
            'metadata': self.metadata
        }

# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class RecommendationEngine:
    """
    Core recommendation engine that evaluates rules and generates recommendations.

    Uses canonical notation for dimension and policy area validation.
    """

    def __init__(
        self,
        rules_path: str = "config/recommendation_rules_enhanced.json",
        schema_path: str = "rules/recommendation_rules.schema.json",
        questionnaire_provider=None,
        orchestrator=None
    ) -> None:
        """
        Initialize recommendation engine

        Args:
            rules_path: Path to recommendation rules JSON file
            schema_path: Path to JSON schema for validation
            questionnaire_provider: QuestionnaireResourceProvider instance (injected via DI)
            orchestrator: Orchestrator instance for accessing thresholds and patterns

        ARCHITECTURAL NOTE: Thresholds should come from questionnaire monolith
        via QuestionnaireResourceProvider, not from hardcoded values.
        """
        self.rules_path = Path(rules_path)
        self.schema_path = Path(schema_path)
        self.questionnaire_provider = questionnaire_provider
        self.orchestrator = orchestrator
        self.rules: dict[str, Any] = {}
        self.schema: dict[str, Any] = {}
        self.rules_by_level: dict[str, list[dict[str, Any]]] = {
            'MICRO': [],
            'MESO': [],
            'MACRO': []
        }

        # Load canonical notation for validation
        self._load_canonical_notation()

        # Load rules and schema
        self._load_schema()
        self._load_rules()

        logger.info(
            f"Recommendation engine initialized with "
            f"{len(self.rules_by_level['MICRO'])} MICRO, "
            f"{len(self.rules_by_level['MESO'])} MESO, "
            f"{len(self.rules_by_level['MACRO'])} MACRO rules"
        )

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._load_canonical_notation")
    def _load_canonical_notation(self) -> None:
        """Load canonical notation for validation"""
        try:
            from saaaaaa.core.canonical_notation import get_all_dimensions, get_all_policy_areas
            self.canonical_dimensions = get_all_dimensions()
            self.canonical_policy_areas = get_all_policy_areas()
            logger.info(
                f"Canonical notation loaded: {len(self.canonical_dimensions)} dimensions, "
                f"{len(self.canonical_policy_areas)} policy areas"
            )
        except Exception as e:
            logger.warning(f"Could not load canonical notation: {e}")
            self.canonical_dimensions = {}
            self.canonical_policy_areas = {}

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._load_schema")
    def _load_schema(self) -> None:
        """Load JSON schema for rule validation"""
        # Delegate to factory for I/O operation
        from .factory import load_json

        try:
            self.schema = load_json(self.schema_path)
            logger.info(f"Loaded recommendation rules schema from {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._load_rules")
    def _load_rules(self) -> None:
        """Load and validate recommendation rules"""
        # Delegate to factory for I/O operation
        from .factory import load_json

        try:
            self.rules = load_json(self.rules_path)

            # Validate against schema
            jsonschema.validate(instance=self.rules, schema=self.schema)
            self._validate_ruleset_metadata()

            # Organize rules by level
            for rule in self.rules.get('rules', []):
                self._validate_rule(rule)
                level = rule.get('level')
                if level in self.rules_by_level:
                    self.rules_by_level[level].append(rule)

            logger.info(f"Loaded and validated {len(self.rules.get('rules', []))} rules from {self.rules_path}")
        except jsonschema.ValidationError as e:
            logger.error(f"Rule validation failed: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            raise

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine.reload_rules")
    def reload_rules(self) -> None:
        """Reload rules from disk (useful for hot-reloading)"""
        self.rules_by_level = {'MICRO': [], 'MESO': [], 'MACRO': []}
        self._load_rules()

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith")
    def get_thresholds_from_monolith(self) -> dict[str, Any]:
        """
        Get scoring thresholds from questionnaire monolith.

        Returns:
            Dictionary of thresholds by question_id or default thresholds

        ARCHITECTURAL NOTE: This method demonstrates proper access to
        questionnaire data via QuestionnaireResourceProvider, not direct I/O.
        """
        if self.questionnaire_provider is None:
            logger.warning("No questionnaire provider attached, using default thresholds")
            return {
                'default_micro_threshold': 2.0,
                'default_meso_threshold': 55.0,
                'default_macro_threshold': 65.0
            }

        # Get questionnaire data via provider
        questionnaire_data = self.questionnaire_provider.get_data()

        # Extract thresholds from monolith structure
        thresholds = {}
        blocks = questionnaire_data.get('blocks', {})
        micro_questions = blocks.get('micro_questions', [])

        for question in micro_questions:
            question_id = question.get('question_id')
            scoring_info = question.get('scoring', {})
            threshold = scoring_info.get('threshold')

            if question_id and threshold is not None:
                thresholds[question_id] = threshold

        logger.info(f"Loaded {len(thresholds)} thresholds from questionnaire monolith")
        return thresholds

    # ========================================================================
    # MICRO LEVEL RECOMMENDATIONS
    # ========================================================================

    def generate_micro_recommendations(
        self,
        scores: dict[str, float],
        context: dict[str, Any] | None = None
    ) -> RecommendationSet:
        """
        Generate MICRO-level recommendations based on PA-DIM scores

        Args:
            scores: Dictionary mapping "PA##-DIM##" to scores (get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L279_63", 0.0)-3.0)
            context: Additional context for template rendering

        Returns:
            RecommendationSet with matched recommendations
        """
        recommendations = []
        rules_evaluated = 0

        for rule in self.rules_by_level['MICRO']:
            rules_evaluated += 1

            # Extract condition
            when = rule.get('when', {})
            pa_id = when.get('pa_id')
            dim_id = when.get('dim_id')
            score_lt = when.get('score_lt')

            # Build score key
            score_key = f"{pa_id}-{dim_id}"

            # Check if condition matches
            if score_key in scores and scores[score_key] < score_lt:
                # Render template
                template = rule.get('template', {})
                rendered = self._render_micro_template(template, pa_id, dim_id, context)

                # Create recommendation with enhanced fields (v2.0) if available
                rec = Recommendation(
                    rule_id=rule.get('rule_id'),
                    level='MICRO',
                    problem=rendered['problem'],
                    intervention=rendered['intervention'],
                    indicator=rendered['indicator'],
                    responsible=rendered['responsible'],
                    horizon=rendered['horizon'],
                    verification=rendered['verification'],
                    metadata={
                        'score_key': score_key,
                        'actual_score': scores[score_key],
                        'threshold': score_lt,
                        'gap': score_lt - scores[score_key]
                    },
                    # Enhanced fields (v2.0)
                    execution=rule.get('execution'),
                    budget=rule.get('budget'),
                    template_id=rendered.get('template_id'),
                    template_params=rendered.get('template_params')
                )
                recommendations.append(rec)

        return RecommendationSet(
            level='MICRO',
            recommendations=recommendations,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_rules_evaluated=rules_evaluated,
            rules_matched=len(recommendations)
        )

    def _render_micro_template(
        self,
        template: dict[str, Any],
        pa_id: str,
        dim_id: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Render MICRO template with variable substitution

        Variables supported:
        - {{PAxx}}: Policy area (e.g., PA01)
        - {{DIMxx}}: Dimension (e.g., DIM01)
        - {{Q###}}: Question number (from context)
        """
        ctx = context or {}

        substitutions = {
            'PAxx': pa_id,
            'DIMxx': dim_id,
            'pa_id': pa_id,
            'dim_id': dim_id,
        }

        question_hint = ctx.get('question_id')
        template_params = template.get('template_params', {}) if isinstance(template, dict) else {}
        if isinstance(template_params, dict):
            for key, value in template_params.items():
                if isinstance(value, str):
                    substitutions.setdefault(key, value)
                    substitutions.setdefault(key.upper(), value)
                    if key == 'question_id':
                        question_hint = value

        if isinstance(question_hint, str):
            substitutions.setdefault(question_hint, question_hint)
            substitutions.setdefault('question_id', question_hint)
            substitutions.setdefault('Q001', question_hint)

        for key, value in ctx.items():
            if isinstance(value, str):
                substitutions.setdefault(key, value)

        return self._render_template(template, substitutions)

    # ========================================================================
    # MESO LEVEL RECOMMENDATIONS
    # ========================================================================

    def generate_meso_recommendations(
        self,
        cluster_data: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> RecommendationSet:
        """
        Generate MESO-level recommendations based on cluster performance

        Args:
            cluster_data: Dictionary with cluster metrics:
                {
                    'CL01': {'score': 75.0, 'variance': get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L398_56", 0.15), 'weak_pa': 'PA02'},
                    'CL02': {'score': 62.0, 'variance': get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L399_56", 0.22), 'weak_pa': 'PA05'},
                    ...
                }
            context: Additional context for template rendering

        Returns:
            RecommendationSet with matched recommendations
        """
        recommendations = []
        rules_evaluated = 0

        for rule in self.rules_by_level['MESO']:
            rules_evaluated += 1

            # Extract condition
            when = rule.get('when', {})
            cluster_id = when.get('cluster_id')
            score_band = when.get('score_band')
            variance_level = when.get('variance_level')
            variance_threshold = when.get('variance_threshold')
            weak_pa_id = when.get('weak_pa_id')

            # Get cluster data
            cluster = cluster_data.get(cluster_id, {})
            cluster_score = cluster.get('score', 0)
            cluster_variance = cluster.get('variance', 0)
            cluster_weak_pa = cluster.get('weak_pa')

            # Check conditions
            if not self._check_meso_conditions(
                cluster_score, cluster_variance, cluster_weak_pa,
                score_band, variance_level, variance_threshold, weak_pa_id
            ):
                continue

            # Render template
            template = rule.get('template', {})
            rendered = self._render_meso_template(template, cluster_id, context)

            # Create recommendation with enhanced fields (v2.0) if available
            rec = Recommendation(
                rule_id=rule.get('rule_id'),
                level='MESO',
                problem=rendered['problem'],
                intervention=rendered['intervention'],
                indicator=rendered['indicator'],
                responsible=rendered['responsible'],
                horizon=rendered['horizon'],
                verification=rendered['verification'],
                metadata={
                    'cluster_id': cluster_id,
                    'score': cluster_score,
                    'score_band': score_band,
                    'variance': cluster_variance,
                    'variance_level': variance_level,
                    'weak_pa': cluster_weak_pa
                },
                # Enhanced fields (v2.0)
                execution=rule.get('execution'),
                budget=rule.get('budget'),
                template_id=rendered.get('template_id'),
                template_params=rendered.get('template_params')
            )
            recommendations.append(rec)

        return RecommendationSet(
            level='MESO',
            recommendations=recommendations,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_rules_evaluated=rules_evaluated,
            rules_matched=len(recommendations)
        )

    def _check_meso_conditions(
        self,
        score: float,
        variance: float,
        weak_pa: str | None,
        score_band: str,
        variance_level: str,
        variance_threshold: float | None,
        weak_pa_id: str | None
    ) -> bool:
        """Check if MESO conditions are met"""
        # Check score band
        if score_band == 'BAJO' and score >= 55 or score_band == 'MEDIO' and (score < 55 or score >= 75) or score_band == 'ALTO' and score < 75:
            return False

        # Check variance level
        if variance_level == 'BAJA' and variance >= get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L488_52", 0.08) or variance_level == 'MEDIA' and (variance < get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L488_102", 0.08) or variance >= get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L488_122", 0.18)):
            return False
        elif variance_level == 'ALTA':
            if variance_threshold and variance < variance_threshold / 100 or not variance_threshold and variance < get_parameter_loader().get("saaaaaa.analysis.recommendation_engine.RecommendationEngine.get_thresholds_from_monolith").get("auto_param_L491_115", 0.18):
                return False

        # Check weak PA if specified
        return not (weak_pa_id and weak_pa != weak_pa_id)

    def _render_meso_template(
        self,
        template: dict[str, Any],
        cluster_id: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Render MESO template with variable substitution"""

        substitutions = {
            'cluster_id': cluster_id,
        }

        if isinstance(template, dict):
            params = template.get('template_params', {})
            if isinstance(params, dict):
                for key, value in params.items():
                    if isinstance(value, str):
                        substitutions.setdefault(key, value)
                        substitutions.setdefault(key.upper(), value)

        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    substitutions.setdefault(key, value)

        return self._render_template(template, substitutions)

    # ========================================================================
    # MACRO LEVEL RECOMMENDATIONS
    # ========================================================================

    def generate_macro_recommendations(
        self,
        macro_data: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> RecommendationSet:
        """
        Generate MACRO-level strategic recommendations

        Args:
            macro_data: Dictionary with plan-level metrics:
                {
                    'macro_band': 'SATISFACTORIO',
                    'clusters_below_target': ['CL02', 'CL03'],
                    'variance_alert': 'MODERADA',
                    'priority_micro_gaps': ['PA01-DIM05', 'PA04-DIM04']
                }
            context: Additional context for template rendering

        Returns:
            RecommendationSet with matched recommendations
        """
        recommendations = []
        rules_evaluated = 0

        for rule in self.rules_by_level['MACRO']:
            rules_evaluated += 1

            # Extract condition
            when = rule.get('when', {})
            macro_band = when.get('macro_band')
            clusters_below = set(when.get('clusters_below_target', []))
            variance_alert = when.get('variance_alert')
            priority_gaps = set(when.get('priority_micro_gaps', []))

            # Get macro data
            actual_band = macro_data.get('macro_band')
            actual_clusters = set(macro_data.get('clusters_below_target', []))
            actual_variance = macro_data.get('variance_alert')
            actual_gaps = set(macro_data.get('priority_micro_gaps', []))

            # Check conditions
            if macro_band and macro_band != actual_band:
                continue
            if variance_alert and variance_alert != actual_variance:
                continue

            # Check if clusters match (subset or exact match)
            if clusters_below and not clusters_below.issubset(actual_clusters):
                # For MACRO, we want exact match or the rule's clusters to be present
                if clusters_below != actual_clusters and not actual_clusters.issubset(clusters_below):
                    continue

            # Check if priority gaps match (subset)
            if priority_gaps and not priority_gaps.issubset(actual_gaps):
                continue

            # Render template
            template = rule.get('template', {})
            rendered = self._render_macro_template(template, context)

            # Create recommendation with enhanced fields (v2.0) if available
            rec = Recommendation(
                rule_id=rule.get('rule_id'),
                level='MACRO',
                problem=rendered['problem'],
                intervention=rendered['intervention'],
                indicator=rendered['indicator'],
                responsible=rendered['responsible'],
                horizon=rendered['horizon'],
                verification=rendered['verification'],
                metadata={
                    'macro_band': actual_band,
                    'clusters_below_target': list(actual_clusters),
                    'variance_alert': actual_variance,
                    'priority_micro_gaps': list(actual_gaps)
                },
                # Enhanced fields (v2.0)
                execution=rule.get('execution'),
                budget=rule.get('budget'),
                template_id=rendered.get('template_id'),
                template_params=rendered.get('template_params')
            )
            recommendations.append(rec)

        return RecommendationSet(
            level='MACRO',
            recommendations=recommendations,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_rules_evaluated=rules_evaluated,
            rules_matched=len(recommendations)
        )

    def _render_macro_template(
        self,
        template: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Render MACRO template with variable substitution"""

        substitutions = {}

        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    substitutions.setdefault(key, value)

        if isinstance(template, dict):
            params = template.get('template_params', {})
            if isinstance(params, dict):
                for key, value in params.items():
                    if isinstance(value, str):
                        substitutions.setdefault(key, value)
                        substitutions.setdefault(key.upper(), value)

        return self._render_template(template, substitutions)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._substitute_variables")
    def _substitute_variables(self, text: str, substitutions: dict[str, str]) -> str:
        """
        Substitute variables in text using {{variable}} syntax

        Args:
            text: Text with variables
            substitutions: Dictionary of variable_name -> value

        Returns:
            Text with variables substituted
        """
        result = text
        for var, value in substitutions.items():
            pattern = r'\{\{' + re.escape(var) + r'\}\}'
            result = re.sub(pattern, value, result)
        return result

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._render_template")
    def _render_template(self, template: dict[str, Any], substitutions: dict[str, str]) -> dict[str, Any]:
        """Recursively render a template applying substitutions to nested structures."""

        def render_value(value: Any) -> Any:
            if isinstance(value, str):
                return self._substitute_variables(value, substitutions)
            if isinstance(value, list):
                return [render_value(item) for item in value]
            if isinstance(value, dict):
                return {k: render_value(v) for k, v in value.items()}
            return value

        return render_value(template)

    # ========================================================================
    # VALIDATION UTILITIES
    # ========================================================================

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_rule")
    def _validate_rule(self, rule: dict[str, Any]) -> None:
        """Apply structural validation to guarantee rigorous recommendations."""
        rule_id = rule.get('rule_id')
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError("Recommendation rule missing rule_id")

        level = rule.get('level')
        if level not in self.rules_by_level:
            raise ValueError(f"Rule {rule_id} declares unsupported level: {level}")

        when = rule.get('when', {})
        if not isinstance(when, dict):
            raise ValueError(f"Rule {rule_id} has invalid 'when' definition")

        if level == 'MICRO':
            self._validate_micro_when(rule_id, when)
        elif level == 'MESO':
            self._validate_meso_when(rule_id, when)
        elif level == 'MACRO':
            self._validate_macro_when(rule_id, when)

        template = rule.get('template')
        if not isinstance(template, dict):
            raise ValueError(f"Rule {rule_id} lacks a structured template")

        self._validate_template(rule_id, template, level)

        execution = rule.get('execution')
        if execution is None:
            raise ValueError(f"Rule {rule_id} is missing execution block required for enhanced rules")
        self._validate_execution(rule_id, execution)

        budget = rule.get('budget')
        if budget is None:
            raise ValueError(f"Rule {rule_id} is missing budget block required for enhanced rules")
        self._validate_budget(rule_id, budget)

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_micro_when")
    def _validate_micro_when(self, rule_id: str, when: dict[str, Any]) -> None:
        required_keys = ('pa_id', 'dim_id', 'score_lt')
        for key in required_keys:
            if key not in when:
                raise ValueError(f"Rule {rule_id} missing '{key}' in MICRO condition")

        pa_id = when['pa_id']
        dim_id = when['dim_id']
        if not isinstance(pa_id, str) or not pa_id.strip():
            raise ValueError(f"Rule {rule_id} has invalid pa_id")
        if not isinstance(dim_id, str) or not dim_id.strip():
            raise ValueError(f"Rule {rule_id} has invalid dim_id")

        score_lt = when['score_lt']
        if not self._is_number(score_lt):
            raise ValueError(f"Rule {rule_id} has non-numeric MICRO threshold")
        if not 0 <= float(score_lt) <= 3:
            raise ValueError(f"Rule {rule_id} MICRO threshold must be between 0 and 3")

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_meso_when")
    def _validate_meso_when(self, rule_id: str, when: dict[str, Any]) -> None:
        cluster_id = when.get('cluster_id')
        if not isinstance(cluster_id, str) or not cluster_id.strip():
            raise ValueError(f"Rule {rule_id} missing cluster_id for MESO condition")

        condition_counter = 0

        score_band = when.get('score_band')
        if score_band is not None:
            if score_band not in {'BAJO', 'MEDIO', 'ALTO'}:
                raise ValueError(f"Rule {rule_id} has invalid MESO score_band")
            condition_counter += 1

        variance_level = when.get('variance_level')
        if variance_level is not None:
            if variance_level not in {'BAJA', 'MEDIA', 'ALTA'}:
                raise ValueError(f"Rule {rule_id} has invalid MESO variance_level")
            condition_counter += 1

        variance_threshold = when.get('variance_threshold')
        if variance_threshold is not None and not self._is_number(variance_threshold):
            raise ValueError(f"Rule {rule_id} has non-numeric variance_threshold")

        weak_pa_id = when.get('weak_pa_id')
        if weak_pa_id is not None:
            if not isinstance(weak_pa_id, str) or not weak_pa_id.strip():
                raise ValueError(f"Rule {rule_id} has invalid weak_pa_id")
            condition_counter += 1

        if condition_counter == 0:
            raise ValueError(
                f"Rule {rule_id} must specify at least one discriminant condition for MESO"
            )

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_macro_when")
    def _validate_macro_when(self, rule_id: str, when: dict[str, Any]) -> None:
        discriminants = 0

        macro_band = when.get('macro_band')
        if macro_band is not None:
            if not isinstance(macro_band, str) or not macro_band.strip():
                raise ValueError(f"Rule {rule_id} has invalid macro_band")
            discriminants += 1

        clusters = when.get('clusters_below_target')
        if clusters is not None:
            if not isinstance(clusters, list) or not clusters:
                raise ValueError(f"Rule {rule_id} must declare non-empty clusters_below_target")
            if not all(isinstance(item, str) and item.strip() for item in clusters):
                raise ValueError(f"Rule {rule_id} has invalid cluster identifiers")
            discriminants += 1

        variance_alert = when.get('variance_alert')
        if variance_alert is not None:
            if not isinstance(variance_alert, str) or not variance_alert.strip():
                raise ValueError(f"Rule {rule_id} has invalid variance_alert")
            discriminants += 1

        priority_gaps = when.get('priority_micro_gaps')
        if priority_gaps is not None:
            if not isinstance(priority_gaps, list) or not priority_gaps:
                raise ValueError(f"Rule {rule_id} must declare non-empty priority_micro_gaps")
            if not all(isinstance(item, str) and item.strip() for item in priority_gaps):
                raise ValueError(f"Rule {rule_id} has invalid priority_micro_gaps entries")
            discriminants += 1

        if discriminants == 0:
            raise ValueError(
                f"Rule {rule_id} must specify at least one MACRO discriminant condition"
            )

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_template")
    def _validate_template(self, rule_id: str, template: dict[str, Any], level: str) -> None:
        required_fields = ['problem', 'intervention', 'indicator', 'responsible', 'horizon', 'verification', 'template_id', 'template_params']
        for field in required_fields:
            if field not in template:
                raise ValueError(f"Rule {rule_id} template missing '{field}'")

        for text_field in ('problem', 'intervention'):
            value = template[text_field]
            if not isinstance(value, str):
                raise ValueError(f"Rule {rule_id} template field '{text_field}' must be text")
            stripped = value.strip()
            if len(stripped) < 40 or len(stripped.split()) < 12:
                raise ValueError(
                    f"Rule {rule_id} template field '{text_field}' lacks actionable detail"
                )

        indicator = template['indicator']
        if not isinstance(indicator, dict):
            raise ValueError(f"Rule {rule_id} indicator must be an object")
        for key in ('name', 'target', 'unit'):
            if key not in indicator:
                raise ValueError(f"Rule {rule_id} indicator missing '{key}' field")

        if not isinstance(indicator['name'], str) or len(indicator['name'].strip()) < 5:
            raise ValueError(f"Rule {rule_id} indicator name too short")

        target = indicator['target']
        if not self._is_number(target):
            raise ValueError(f"Rule {rule_id} indicator target must be numeric")

        unit = indicator['unit']
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError(f"Rule {rule_id} indicator unit missing or empty")

        acceptable_range = indicator.get('acceptable_range')
        if acceptable_range is not None:
            if not isinstance(acceptable_range, list) or len(acceptable_range) != 2:
                raise ValueError(f"Rule {rule_id} acceptable_range must have two numeric bounds")
            if not all(self._is_number(bound) for bound in acceptable_range):
                raise ValueError(f"Rule {rule_id} acceptable_range values must be numeric")
            lower, upper = acceptable_range
            if float(lower) >= float(upper):
                raise ValueError(f"Rule {rule_id} acceptable_range lower bound must be < upper bound")

        template_id = template['template_id']
        if not isinstance(template_id, str) or not template_id.strip():
            raise ValueError(f"Rule {rule_id} template_id must be a non-empty string")

        template_params = template['template_params']
        if not isinstance(template_params, dict):
            raise ValueError(f"Rule {rule_id} template_params must be an object")
        allowed_param_keys = {'pa_id', 'dim_id', 'cluster_id', 'question_id'}
        unknown_params = set(template_params) - allowed_param_keys
        if unknown_params:
            raise ValueError(f"Rule {rule_id} template_params contains unsupported keys: {sorted(unknown_params)}")

        required_params: set[str] = set()
        if level == 'MICRO':
            required_params = {'pa_id', 'dim_id', 'question_id'}
        elif level == 'MESO':
            required_params = {'cluster_id'}

        missing_params = required_params - set(template_params)
        if missing_params:
            raise ValueError(
                f"Rule {rule_id} template_params missing required keys for {level}: {sorted(missing_params)}"
            )

        if level != 'MACRO' and not template_params:
            raise ValueError(f"Rule {rule_id} template_params cannot be empty for {level} level")

        responsible = template['responsible']
        if not isinstance(responsible, dict):
            raise ValueError(f"Rule {rule_id} responsible must be an object")
        for key in ('entity', 'role'):
            value = responsible.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Rule {rule_id} responsible missing '{key}'")

        partners = responsible.get('partners')
        if partners is None or not isinstance(partners, list) or not partners:
            raise ValueError(f"Rule {rule_id} responsible must enumerate partners")
        if any(not isinstance(partner, str) or not partner.strip() for partner in partners):
            raise ValueError(f"Rule {rule_id} responsible partners must be non-empty strings")

        horizon = template['horizon']
        if not isinstance(horizon, dict):
            raise ValueError(f"Rule {rule_id} horizon must be an object")
        for key in ('start', 'end'):
            value = horizon.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Rule {rule_id} horizon missing '{key}'")

        verification = template['verification']
        if not isinstance(verification, list) or not verification:
            raise ValueError(f"Rule {rule_id} must define verification artifacts")
        for artifact in verification:
            if not isinstance(artifact, dict):
                raise ValueError(
                    f"Rule {rule_id} verification entries must be structured dictionaries"
                )
            required_artifact_fields = (
                'id',
                'type',
                'artifact',
                'format',
                'approval_required',
                'approver',
                'due_date',
                'required_sections',
                'automated_check',
            )
            for key in required_artifact_fields:
                if key not in artifact:
                    raise ValueError(
                        f"Rule {rule_id} verification artifact missing required field '{key}'"
                    )
                # Special handling for boolean fields - they can be False
                if key in ('approval_required', 'automated_check'):
                    if not isinstance(artifact[key], bool):
                        raise ValueError(
                            f"Rule {rule_id} verification artifact field '{key}' must be a boolean"
                        )
                # Special handling for required_sections - must be a list
                elif key == 'required_sections':
                    if not isinstance(artifact[key], list) or not all(isinstance(s, str) and s.strip() for s in artifact[key]):
                        raise ValueError(
                            f"Rule {rule_id} verification required_sections must be a list of strings (may be empty)"
                        )
                # For other non-boolean fields, check for empty values
                elif not artifact[key]:
                    raise ValueError(
                        f"Rule {rule_id} verification artifact field '{key}' cannot be empty"
                    )

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_execution")
    def _validate_execution(self, rule_id: str, execution: dict[str, Any]) -> None:
        if not isinstance(execution, dict):
            raise ValueError(f"Rule {rule_id} execution block must be an object")

        required_keys = {
            'trigger_condition',
            'blocking',
            'auto_apply',
            'requires_approval',
            'approval_roles',
        }
        missing = required_keys - execution.keys()
        if missing:
            raise ValueError(f"Rule {rule_id} execution block missing keys: {sorted(missing)}")

        if not isinstance(execution['trigger_condition'], str) or not execution['trigger_condition'].strip():
            raise ValueError(f"Rule {rule_id} execution trigger_condition must be a non-empty string")
        for flag in ('blocking', 'auto_apply', 'requires_approval'):
            if not isinstance(execution[flag], bool):
                raise ValueError(f"Rule {rule_id} execution field '{flag}' must be boolean")

        roles = execution['approval_roles']
        if not isinstance(roles, list) or not roles:
            raise ValueError(f"Rule {rule_id} execution approval_roles must be a non-empty list")
        if any(not isinstance(role, str) or not role.strip() for role in roles):
            raise ValueError(f"Rule {rule_id} execution approval_roles must contain non-empty strings")

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_budget")
    def _validate_budget(self, rule_id: str, budget: dict[str, Any]) -> None:
        if not isinstance(budget, dict):
            raise ValueError(f"Rule {rule_id} budget block must be an object")

        required_keys = {'estimated_cost_cop', 'cost_breakdown', 'funding_sources', 'fiscal_year'}
        missing = required_keys - budget.keys()
        if missing:
            raise ValueError(f"Rule {rule_id} budget block missing keys: {sorted(missing)}")

        if not self._is_number(budget['estimated_cost_cop']):
            raise ValueError(f"Rule {rule_id} budget estimated_cost_cop must be numeric")

        cost_breakdown = budget['cost_breakdown']
        if not isinstance(cost_breakdown, dict) or not cost_breakdown:
            raise ValueError(f"Rule {rule_id} cost_breakdown must be a non-empty object")
        for key, value in cost_breakdown.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Rule {rule_id} cost_breakdown keys must be non-empty strings")
            if not self._is_number(value):
                raise ValueError(f"Rule {rule_id} cost_breakdown values must be numeric")

        funding_sources = budget['funding_sources']
        if not isinstance(funding_sources, list) or not funding_sources:
            raise ValueError(f"Rule {rule_id} funding_sources must be a non-empty list")
        for source in funding_sources:
            if not isinstance(source, dict):
                raise ValueError(f"Rule {rule_id} funding source entries must be objects")
            for key in ('source', 'amount', 'confirmed'):
                if key not in source:
                    raise ValueError(f"Rule {rule_id} funding source missing '{key}'")
            if not isinstance(source['source'], str) or not source['source'].strip():
                raise ValueError(f"Rule {rule_id} funding source name must be a non-empty string")
            if not self._is_number(source['amount']):
                raise ValueError(f"Rule {rule_id} funding source amount must be numeric")
            if not isinstance(source['confirmed'], bool):
                raise ValueError(f"Rule {rule_id} funding source confirmed flag must be boolean")

        fiscal_year = budget['fiscal_year']
        if not isinstance(fiscal_year, int):
            raise ValueError(f"Rule {rule_id} fiscal_year must be an integer")

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._validate_ruleset_metadata")
    def _validate_ruleset_metadata(self) -> None:
        version = self.rules.get('version')
        if not isinstance(version, str) or not version.startswith('2.0'):
            raise ValueError(
                "Enhanced recommendation engine requires ruleset version 2.0"
            )

        features = self.rules.get('enhanced_features')
        if not isinstance(features, list) or not features:
            raise ValueError("Enhanced recommendation engine requires enhanced_features list")

        feature_set = {feature for feature in features if isinstance(feature, str)}
        missing = _REQUIRED_ENHANCED_FEATURES - feature_set
        if missing:
            raise ValueError(
                f"Enhanced recommendation rules missing required features: {sorted(missing)}"
            )

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def generate_all_recommendations(
        self,
        micro_scores: dict[str, float],
        cluster_data: dict[str, Any],
        macro_data: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, RecommendationSet]:
        """
        Generate recommendations at all three levels

        Args:
            micro_scores: PA-DIM scores for MICRO recommendations
            cluster_data: Cluster metrics for MESO recommendations
            macro_data: Plan-level metrics for MACRO recommendations
            context: Additional context

        Returns:
            Dictionary with 'MICRO', 'MESO', and 'MACRO' recommendation sets
        """
        return {
            'MICRO': self.generate_micro_recommendations(micro_scores, context),
            'MESO': self.generate_meso_recommendations(cluster_data, context),
            'MACRO': self.generate_macro_recommendations(macro_data, context)
        }

    def export_recommendations(
        self,
        recommendations: dict[str, RecommendationSet],
        output_path: str,
        format: str = 'json'
    ) -> None:
        """
        Export recommendations to file

        Args:
            recommendations: Dictionary of recommendation sets
            output_path: Path to output file
            format: Output format ('json' or 'markdown')
        """
        # Delegate to factory for I/O operation
        from .factory import save_json, write_text_file

        if format == 'json':
            save_json(
                {level: rec_set.to_dict() for level, rec_set in recommendations.items()},
                output_path
            )
        elif format == 'markdown':
            write_text_file(
                self._format_as_markdown(recommendations),
                output_path
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported recommendations to {output_path} in {format} format")

    @calibrated_method("saaaaaa.analysis.recommendation_engine.RecommendationEngine._format_as_markdown")
    def _format_as_markdown(self, recommendations: dict[str, RecommendationSet]) -> str:
        """Format recommendations as Markdown"""
        lines = ["# Recomendaciones del Plan de Desarrollo\n"]

        for level in ['MICRO', 'MESO', 'MACRO']:
            rec_set = recommendations.get(level)
            if not rec_set:
                continue

            lines.append(f"\n## Nivel {level}\n")
            lines.append(f"**Generado:** {rec_set.generated_at}\n")
            lines.append(f"**Reglas evaluadas:** {rec_set.total_rules_evaluated}\n")
            lines.append(f"**Recomendaciones:** {rec_set.rules_matched}\n")

            for i, rec in enumerate(rec_set.recommendations, 1):
                lines.append(f"\n### {i}. {rec.rule_id}\n")
                lines.append(f"**Problema:** {rec.problem}\n")
                lines.append(f"\n**Intervención:** {rec.intervention}\n")
                lines.append("\n**Indicador:**")
                lines.append(f"- Nombre: {rec.indicator.get('name')}")
                lines.append(f"- Meta: {rec.indicator.get('target')} {rec.indicator.get('unit')}\n")
                lines.append(f"\n**Responsable:** {rec.responsible.get('entity')} ({rec.responsible.get('role')})\n")
                lines.append(f"**Socios:** {', '.join(rec.responsible.get('partners', []))}\n")
                lines.append(f"\n**Horizonte:** {rec.horizon.get('start')} → {rec.horizon.get('end')}\n")
                lines.append("\n**Verificación:**")
                for v in rec.verification:
                    if isinstance(v, dict):
                        descriptor = f"[{v.get('type', 'ARTIFACT')}] {v.get('artifact', 'Sin artefacto')}"
                        due = v.get('due_date')
                        approver = v.get('approver')
                        suffix_parts: list[str] = []
                        if due:
                            suffix_parts.append(f"entrega: {due}")
                        if approver:
                            suffix_parts.append(f"aprueba: {approver}")
                        suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
                        lines.append(f"- {descriptor}{suffix}")
                        sections = v.get('required_sections') or []
                        if sections:
                            lines.append(
                                "  - Secciones requeridas: " + ", ".join(str(section) for section in sections)
                            )
                    else:
                        lines.append(f"- {v}")
                lines.append("")

        return "\n".join(lines)

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def load_recommendation_engine(
    rules_path: str = "config/recommendation_rules_enhanced.json",
    schema_path: str = "rules/recommendation_rules.schema.json"
) -> RecommendationEngine:
    """
    Convenience function to load recommendation engine

    Args:
        rules_path: Path to rules JSON
        schema_path: Path to schema JSON

    Returns:
        Initialized RecommendationEngine
    """
    return RecommendationEngine(rules_path=rules_path, schema_path=schema_path)

# Note: Main entry point removed to maintain I/O boundary separation.
# For usage examples, see examples/ directory.
