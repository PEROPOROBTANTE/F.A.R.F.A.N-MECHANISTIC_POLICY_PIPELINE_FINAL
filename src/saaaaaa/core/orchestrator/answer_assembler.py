"""
Answer Assembler for F.A.R.F.A.N Mechanistic Policy Pipeline
=============================================================

This module synthesizes method outputs into doctoral-level answers.

Core responsibilities:
1. Extract evidence from method execution results
2. Apply answer templates to synthesize responses
3. Generate structured doctoral answers with citations
4. Validate answer completeness and quality

Author: F.A.R.F.A.N Team
Date: 2025-11-20
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AnswerAssembler:
    """
    Assembles doctoral-level answers from method execution outputs.

    Takes raw method results and synthesizes them according to answer templates
    into structured, evidence-based responses suitable for policy analysis.
    """

    def __init__(self, templates_path: Optional[str] = None):
        """
        Initialize the AnswerAssembler.

        Args:
            templates_path: Path to answer_templates.json file
        """
        self.templates_path = templates_path or self._get_default_templates_path()
        self.templates = self._load_templates()

    def _get_default_templates_path(self) -> str:
        """Get default path for answer templates."""
        base_path = Path(__file__).parent.parent.parent.parent.parent
        return str(base_path / "config" / "answer_templates.json")

    def _load_templates(self) -> Dict[str, Any]:
        """Load answer templates from JSON file."""
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            logger.info(f"Loaded {len(templates.get('templates', {}))} answer templates")
            return templates
        except FileNotFoundError:
            logger.warning(f"Template file not found: {self.templates_path}")
            return {"templates": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing template file: {e}")
            return {"templates": {}}

    def assemble_answer(
        self,
        question_id: str,
        method_results: Dict[str, Any],
        policy_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assemble a doctoral-level answer from method results.

        Args:
            question_id: Question identifier (e.g., "D1-Q1")
            method_results: Dictionary of method execution results
            policy_area: Policy area code (e.g., "PA01") for area-specific synthesis

        Returns:
            Structured answer dictionary with:
            - verdict: Direct answer (SI/NO/PARCIAL/NO_DETERMINABLE)
            - evidence: List of evidence items with citations
            - confidence: Bayesian confidence score
            - limitations: List of data quality issues or gaps
            - synthesis: Doctoral-level narrative synthesis
        """
        template = self._get_template(question_id, policy_area)

        if not template:
            logger.warning(f"No template found for {question_id}")
            return self._create_fallback_answer(question_id, method_results)

        # Extract evidence according to template requirements
        evidence = self._extract_evidence(method_results, template)

        # Compute verdict based on synthesis rules
        verdict = self._compute_verdict(evidence, template)

        # Calculate confidence score
        confidence = self._calculate_confidence(evidence, method_results)

        # Identify limitations
        limitations = self._identify_limitations(evidence, method_results, template)

        # Generate doctoral synthesis
        synthesis = self._generate_synthesis(
            verdict, evidence, confidence, limitations, template
        )

        return {
            "question_id": question_id,
            "policy_area": policy_area,
            "verdict": verdict,
            "evidence": evidence,
            "confidence": confidence,
            "limitations": limitations,
            "synthesis": synthesis,
            "method_count": len(method_results),
            "template_version": template.get("version", "1.0")
        }

    def _get_template(
        self,
        question_id: str,
        policy_area: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve answer template for question.

        Supports policy-area-specific templates if available.
        """
        templates = self.templates.get("templates", {})

        # Try area-specific template first
        if policy_area:
            area_key = f"{question_id}_{policy_area}"
            if area_key in templates:
                return templates[area_key]

        # Fall back to base template
        return templates.get(question_id)

    def _extract_evidence(
        self,
        method_results: Dict[str, Any],
        template: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract evidence items from method results based on template requirements.

        Returns list of evidence dictionaries with:
        - type: Evidence type (quantitative_data, source, temporal_reference, etc.)
        - value: The actual evidence value
        - source_method: Which method produced this evidence
        - location: Page/section location if available
        - confidence: Method-specific confidence score
        """
        evidence_items = []
        required_evidence = template.get("required_evidence", [])

        for evidence_type in required_evidence:
            items = self._extract_evidence_type(
                evidence_type,
                method_results,
                template
            )
            evidence_items.extend(items)

        return evidence_items

    def _extract_evidence_type(
        self,
        evidence_type: str,
        method_results: Dict[str, Any],
        template: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract specific type of evidence from method results."""
        items = []

        # Map evidence types to method result keys
        evidence_mapping = template.get("evidence_mapping", {})
        source_keys = evidence_mapping.get(evidence_type, [])

        for key in source_keys:
            value = self._deep_get(method_results, key)
            if value is not None:
                items.append({
                    "type": evidence_type,
                    "value": value,
                    "source_method": key.split('.')[0] if '.' in key else key,
                    "location": self._extract_location(method_results, key),
                    "confidence": self._extract_confidence(method_results, key)
                })

        return items

    def _deep_get(self, data: Dict, key_path: str, default=None) -> Any:
        """
        Get value from nested dictionary using dot notation.

        Example: _deep_get(data, "PP.quantitative_baseline.values")
        """
        keys = key_path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default

            if value is None:
                return default

        return value

    def _extract_location(
        self,
        method_results: Dict[str, Any],
        key: str
    ) -> Optional[Dict[str, Any]]:
        """Extract location metadata (page, section) from method results."""
        # Look for location metadata in result
        location_key = f"{key}_location"
        location = self._deep_get(method_results, location_key)

        if location:
            return location

        # Try to find location in parent result structure
        base_key = '.'.join(key.split('.')[:-1])
        if base_key:
            parent = self._deep_get(method_results, base_key)
            if isinstance(parent, dict):
                return parent.get("location") or parent.get("metadata", {}).get("location")

        return None

    def _extract_confidence(
        self,
        method_results: Dict[str, Any],
        key: str
    ) -> Optional[float]:
        """Extract confidence score from method results."""
        confidence_key = f"{key}_confidence"
        confidence = self._deep_get(method_results, confidence_key)

        if confidence is not None:
            return float(confidence)

        # Look for Bayesian posterior or other confidence metrics
        base_key = '.'.join(key.split('.')[:-1])
        if base_key:
            parent = self._deep_get(method_results, base_key)
            if isinstance(parent, dict):
                for conf_key in ["confidence", "posterior", "probability", "score"]:
                    if conf_key in parent:
                        return float(parent[conf_key])

        return None

    def _compute_verdict(
        self,
        evidence: List[Dict[str, Any]],
        template: Dict[str, Any]
    ) -> str:
        """
        Compute answer verdict based on evidence and synthesis rules.

        Returns: SI, NO, PARCIAL, or NO_DETERMINABLE
        """
        synthesis_rules = template.get("synthesis_rules", {})
        verdict_rule = synthesis_rules.get("verdict")

        if not verdict_rule:
            return self._default_verdict(evidence)

        # Evaluate verdict rule
        # Rules can be Python expressions or declarative logic
        if isinstance(verdict_rule, str):
            return self._evaluate_verdict_rule(verdict_rule, evidence)
        elif isinstance(verdict_rule, dict):
            return self._evaluate_verdict_conditions(verdict_rule, evidence)

        return "NO_DETERMINABLE"

    def _evaluate_verdict_rule(
        self,
        rule: str,
        evidence: List[Dict[str, Any]]
    ) -> str:
        """Evaluate string-based verdict rule."""
        # Create context for rule evaluation
        context = self._create_evidence_context(evidence)

        # Safe evaluation of verdict rule
        try:
            # For safety, use simple conditional logic
            if "SI si" in rule:
                conditions = rule.split("SI si")[1].strip()
                if self._evaluate_conditions(conditions, context):
                    return "SI"
                elif any(context.values()):
                    return "PARCIAL"
                else:
                    return "NO"
        except Exception as e:
            logger.error(f"Error evaluating verdict rule: {e}")

        return "NO_DETERMINABLE"

    def _evaluate_verdict_conditions(
        self,
        conditions: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> str:
        """Evaluate dictionary-based verdict conditions."""
        context = self._create_evidence_context(evidence)

        for verdict, condition in conditions.items():
            if self._evaluate_conditions(condition, context):
                return verdict

        return "NO_DETERMINABLE"

    def _create_evidence_context(
        self,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create context dictionary for verdict evaluation."""
        context = {}

        for item in evidence:
            evidence_type = item.get("type")
            value = item.get("value")

            # Count evidence items of each type
            count_key = f"{evidence_type}_count"
            context[count_key] = context.get(count_key, 0) + 1

            # Store boolean presence
            context[evidence_type] = True

            # Store actual values if useful
            if isinstance(value, (int, float)):
                values_key = f"{evidence_type}_values"
                if values_key not in context:
                    context[values_key] = []
                context[values_key].append(value)

        return context

    def _evaluate_conditions(
        self,
        conditions: str,
        context: Dict[str, Any]
    ) -> bool:
        """Safely evaluate conditions against context."""
        # Simple AND/OR logic evaluation
        # Replace with safer parser if needed

        # Handle simple cases
        if "AND" in conditions:
            parts = [p.strip() for p in conditions.split("AND")]
            return all(self._evaluate_simple_condition(p, context) for p in parts)
        elif "OR" in conditions:
            parts = [p.strip() for p in conditions.split("OR")]
            return any(self._evaluate_simple_condition(p, context) for p in parts)
        else:
            return self._evaluate_simple_condition(conditions, context)

    def _evaluate_simple_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a simple condition like 'quantitative_data > 0'."""
        condition = condition.strip('()')

        # Handle 'exists' checks
        if " exists" in condition:
            key = condition.replace(" exists", "").strip()
            return context.get(key, False)

        # Handle comparisons
        for op in [" > ", " >= ", " < ", " <= ", " == ", " != "]:
            if op in condition:
                left, right = condition.split(op)
                left_val = context.get(left.strip(), 0)
                right_val = int(right.strip()) if right.strip().isdigit() else 0

                if op == " > ":
                    return left_val > right_val
                elif op == " >= ":
                    return left_val >= right_val
                elif op == " < ":
                    return left_val < right_val
                elif op == " <= ":
                    return left_val <= right_val
                elif op == " == ":
                    return left_val == right_val
                elif op == " != ":
                    return left_val != right_val

        # Default: check if key exists and is truthy
        return bool(context.get(condition.strip(), False))

    def _default_verdict(self, evidence: List[Dict[str, Any]]) -> str:
        """Compute default verdict when no rules specified."""
        if not evidence:
            return "NO"

        # Check if we have strong evidence (multiple types)
        evidence_types = set(item.get("type") for item in evidence)

        if len(evidence_types) >= 3:
            return "SI"
        elif len(evidence_types) >= 1:
            return "PARCIAL"
        else:
            return "NO"

    def _calculate_confidence(
        self,
        evidence: List[Dict[str, Any]],
        method_results: Dict[str, Any]
    ) -> float:
        """
        Calculate overall confidence score.

        Combines Bayesian posteriors and evidence quality metrics.
        """
        confidence_scores = []

        # Extract confidence from evidence items
        for item in evidence:
            conf = item.get("confidence")
            if conf is not None:
                confidence_scores.append(conf)

        # Look for Bayesian posteriors in method results
        bayesian_keys = [
            "BayesianConfidenceCalculator.posterior",
            "BayesianEvidenceScorer.score",
            "BayesianNumericalAnalyzer.confidence"
        ]

        for key in bayesian_keys:
            value = self._deep_get(method_results, key)
            if value is not None:
                confidence_scores.append(float(value))

        # Compute weighted average or use maximum
        if confidence_scores:
            # Use maximum Bayesian posterior as primary confidence
            return max(confidence_scores)

        # Default confidence based on evidence count
        evidence_count = len(evidence)
        if evidence_count >= 5:
            return 0.8
        elif evidence_count >= 3:
            return 0.6
        elif evidence_count >= 1:
            return 0.4
        else:
            return 0.1

    def _identify_limitations(
        self,
        evidence: List[Dict[str, Any]],
        method_results: Dict[str, Any],
        template: Dict[str, Any]
    ) -> List[str]:
        """
        Identify limitations and data quality issues.

        Returns list of human-readable limitation descriptions.
        """
        limitations = []

        # Check for missing required evidence types
        required = set(template.get("required_evidence", []))
        found = set(item.get("type") for item in evidence)
        missing = required - found

        for missing_type in missing:
            limitations.append(
                f"No se encontró: {self._humanize_evidence_type(missing_type)}"
            )

        # Check for data quality issues from PolicyContradictionDetector
        quality_issues = self._deep_get(
            method_results,
            "PolicyContradictionDetector.data_quality_issues"
        )
        if quality_issues:
            limitations.extend(quality_issues)

        # Check for source credibility issues
        credibility_issues = self._deep_get(
            method_results,
            "IndustrialPolicyProcessor.credibility_issues"
        )
        if credibility_issues:
            limitations.extend(credibility_issues)

        # Check for incomplete validation
        validation_incomplete = self._deep_get(
            method_results,
            "SemanticAnalyzer.validation_incomplete"
        )
        if validation_incomplete:
            limitations.append("Validación semántica incompleta")

        return limitations

    def _humanize_evidence_type(self, evidence_type: str) -> str:
        """Convert evidence type code to human-readable Spanish."""
        mapping = {
            "quantitative_data": "datos cuantitativos",
            "sources_found": "fuentes de información",
            "baseline_year": "año de línea base",
            "data_quality": "validación de calidad de datos",
            "temporal_reference": "referencia temporal",
            "geographic_scope": "alcance geográfico",
            "target_population": "población objetivo",
            "causal_mechanism": "mecanismo causal",
            "resource_allocation": "asignación de recursos",
            "institutional_capacity": "capacidad institucional"
        }
        return mapping.get(evidence_type, evidence_type.replace("_", " "))

    def _generate_synthesis(
        self,
        verdict: str,
        evidence: List[Dict[str, Any]],
        confidence: float,
        limitations: List[str],
        template: Dict[str, Any]
    ) -> str:
        """
        Generate doctoral-level narrative synthesis.

        Creates a coherent narrative that:
        - States the verdict clearly
        - Presents evidence systematically
        - Discusses confidence and limitations
        - Provides policy-relevant interpretation
        """
        lines = []

        # Opening statement
        verdict_text = self._verdict_to_spanish(verdict)
        lines.append(f"RESPUESTA: {verdict_text}")
        lines.append("")

        # Evidence section
        if evidence:
            lines.append("EVIDENCIA:")
            evidence_by_type = self._group_evidence_by_type(evidence)

            for evidence_type, items in evidence_by_type.items():
                type_label = self._humanize_evidence_type(evidence_type)
                lines.append(f"\n{type_label.upper()}:")

                for item in items:
                    value_str = self._format_evidence_value(item.get("value"))
                    location = item.get("location")

                    if location:
                        loc_str = self._format_location(location)
                        lines.append(f"  - {value_str} [{loc_str}]")
                    else:
                        lines.append(f"  - {value_str}")

            lines.append("")

        # Confidence section
        confidence_pct = int(confidence * 100)
        lines.append(f"CONFIANZA: {confidence:.2f} ({confidence_pct}% - Bayesiano)")
        lines.append("")

        # Limitations section
        if limitations:
            lines.append("LIMITACIONES:")
            for limitation in limitations:
                lines.append(f"  - {limitation}")

        return "\n".join(lines)

    def _verdict_to_spanish(self, verdict: str) -> str:
        """Convert verdict code to Spanish."""
        mapping = {
            "SI": "SÍ",
            "NO": "NO",
            "PARCIAL": "PARCIAL",
            "NO_DETERMINABLE": "NO DETERMINABLE"
        }
        return mapping.get(verdict, verdict)

    def _group_evidence_by_type(
        self,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group evidence items by type."""
        grouped = {}
        for item in evidence:
            evidence_type = item.get("type", "unknown")
            if evidence_type not in grouped:
                grouped[evidence_type] = []
            grouped[evidence_type].append(item)
        return grouped

    def _format_evidence_value(self, value: Any) -> str:
        """Format evidence value for display."""
        if isinstance(value, dict):
            # Handle structured evidence
            if "text" in value:
                return value["text"]
            elif "value" in value and "unit" in value:
                return f"{value['value']} {value['unit']}"
            else:
                return str(value)
        elif isinstance(value, list):
            return ", ".join(str(v) for v in value)
        else:
            return str(value)

    def _format_location(self, location: Dict[str, Any]) -> str:
        """Format location metadata for citation."""
        parts = []

        if "page" in location:
            parts.append(f"Pág. {location['page']}")
        if "section" in location:
            parts.append(f"Sección: {location['section']}")
        if "paragraph" in location:
            parts.append(f"Párrafo {location['paragraph']}")

        return ", ".join(parts) if parts else "Ubicación no especificada"

    def _create_fallback_answer(
        self,
        question_id: str,
        method_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback answer when template is missing."""
        logger.warning(f"Using fallback answer for {question_id}")

        evidence_count = len(method_results)

        return {
            "question_id": question_id,
            "verdict": "NO_DETERMINABLE",
            "evidence": [],
            "confidence": 0.0,
            "limitations": [
                f"Template no disponible para {question_id}",
                f"Se ejecutaron {evidence_count} métodos pero no se pudo sintetizar respuesta"
            ],
            "synthesis": f"No se pudo generar respuesta doctoral para {question_id} (template faltante)",
            "method_count": evidence_count,
            "fallback": True
        }
