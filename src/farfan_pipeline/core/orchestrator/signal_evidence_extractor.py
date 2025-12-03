"""
Evidence Structure Enforcer - PROPOSAL #5 (Refactored)
========================================================

Exploits 'expected_elements' field (1,200 specs) to extract structured
evidence instead of unstructured text blobs.

ARCHITECTURE V2 - INTELLIGENCE-DRIVEN:
- Uses actual patterns from questionnaire_monolith.json
- Respects element type definitions (required, minimum)
- Leverages confidence_weight, category, and semantic_expansion metadata
- NO HARDCODED EXTRACTORS - all intelligence from monolith
- Pattern-driven extraction with confidence propagation

Intelligence Unlocked: 1,200 element specifications + 4,200 patterns
Impact: Structured dict with completeness metrics (0.0-1.0)
ROI: From text blob → structured evidence with measurable completeness

Author: F.A.R.F.A.N Pipeline
Date: 2025-12-02
Refactoring: Surgical #5 - Full monolith integration
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class EvidenceExtractionResult:
    """Structured evidence extraction result."""
    
    evidence: dict[str, list[dict[str, Any]]]  # element_type → list of matches
    completeness: float  # 0.0 - 1.0
    missing_required: list[str]  # Required elements not found
    under_minimum: list[tuple[str, int, int]]  # (type, found, minimum)
    extraction_metadata: dict[str, Any] = field(default_factory=dict)


def extract_structured_evidence(
    text: str,
    signal_node: dict[str, Any],
    document_context: dict[str, Any] | None = None
) -> EvidenceExtractionResult:
    """
    Extract structured evidence using monolith patterns.
    
    Core Algorithm:
    1. Parse expected_elements (type, required, minimum)
    2. For each element type, filter relevant patterns
    3. Apply patterns with confidence weights
    4. Validate requirements (required, minimum cardinality)
    5. Compute completeness score
    
    Args:
        text: Source text to extract from
        signal_node: Signal node from questionnaire_monolith.json
        document_context: Optional document-level context
    
    Returns:
        EvidenceExtractionResult with structured evidence
    
    Example:
        >>> node = {
        ...     'expected_elements': [
        ...         {'type': 'fuentes_oficiales', 'minimum': 2},
        ...         {'type': 'cobertura_territorial_especificada', 'required': True}
        ...     ],
        ...     'patterns': [...]
        ... }
        >>> result = extract_structured_evidence(text, node)
        >>> result.completeness
        0.85
    """
    expected_elements = signal_node.get('expected_elements', [])
    all_patterns = signal_node.get('patterns', [])
    validations = signal_node.get('validations', {})
    
    evidence = {}
    missing_required = []
    under_minimum = []
    
    logger.debug(
        "structured_extraction_start",
        expected_count=len(expected_elements),
        pattern_count=len(all_patterns),
        text_length=len(text)
    )
    
    # Extract evidence for each expected element
    for element_spec in expected_elements:
        # Support both dict format (v2) and string format (legacy)
        if isinstance(element_spec, str):
            element_type = element_spec
            is_required = False
            minimum_count = 0
        elif isinstance(element_spec, dict):
            element_type = element_spec.get('type', '')
            is_required = element_spec.get('required', False)
            minimum_count = element_spec.get('minimum', 0)
        else:
            logger.warning("element_spec_invalid_type", spec=element_spec)
            continue
        
        if not element_type:
            logger.warning("element_spec_missing_type", spec=element_spec)
            continue
        
        # Extract all matches for this element type
        matches = extract_evidence_for_element_type(
            element_type=element_type,
            text=text,
            all_patterns=all_patterns,
            validations=validations
        )
        
        evidence[element_type] = matches
        
        # Validate requirements
        found_count = len(matches)
        
        if is_required and found_count == 0:
            missing_required.append(element_type)
            logger.debug(
                "required_element_missing",
                element_type=element_type
            )
        
        if minimum_count > 0 and found_count < minimum_count:
            under_minimum.append((element_type, found_count, minimum_count))
            logger.debug(
                "element_under_minimum",
                element_type=element_type,
                found=found_count,
                minimum=minimum_count
            )
    
    # Compute completeness
    completeness = compute_completeness(
        evidence=evidence,
        expected_elements=expected_elements
    )
    
    logger.info(
        "extraction_complete",
        completeness=completeness,
        evidence_types=len(evidence),
        missing_required=len(missing_required),
        under_minimum=len(under_minimum)
    )
    
    return EvidenceExtractionResult(
        evidence=evidence,
        completeness=completeness,
        missing_required=missing_required,
        under_minimum=under_minimum,
        extraction_metadata={
            'expected_count': len(expected_elements),
            'pattern_count': len(all_patterns),
            'total_matches': sum(len(v) for v in evidence.values())
        }
    )


def extract_evidence_for_element_type(
    element_type: str,
    text: str,
    all_patterns: list[dict[str, Any]],
    validations: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Extract evidence for a specific element type using monolith patterns.
    
    Strategy:
    1. Filter patterns by category/flags that match element type
    2. Apply each pattern with its confidence_weight
    3. Return all matches with metadata
    
    Args:
        element_type: Type from expected_elements (e.g., 'fuentes_oficiales')
        text: Source text
        all_patterns: All patterns from signal node
        validations: Validation rules
    
    Returns:
        List of evidence matches with confidence scores
    """
    matches = []
    
    # Category heuristics (can be improved with explicit mapping in monolith)
    category_hints = _infer_pattern_categories_for_element(element_type)
    
    for pattern_spec in all_patterns:
        pattern_str = pattern_spec.get('pattern', '')
        confidence_weight = pattern_spec.get('confidence_weight', 0.5)
        category = pattern_spec.get('category', 'GENERAL')
        pattern_id = pattern_spec.get('id', 'unknown')
        
        # Filter: only use patterns relevant to this element type
        if category_hints and category not in category_hints:
            continue
        
        # Check if pattern is relevant to element type by keywords
        if not _is_pattern_relevant_to_element(pattern_str, element_type, pattern_spec):
            continue
        
        # Apply pattern (handle pipe-separated alternatives)
        alternatives = [p.strip() for p in pattern_str.split('|') if p.strip()]
        
        for alt in alternatives:
            # Escape regex special chars if match_type is not 'regex'
            match_type = pattern_spec.get('match_type', 'substring')
            if match_type == 'regex':
                regex_pattern = alt
            else:
                regex_pattern = re.escape(alt)
            
            try:
                for match in re.finditer(regex_pattern, text, re.IGNORECASE):
                    matches.append({
                        'value': match.group(0),
                        'raw_text': match.group(0),
                        'confidence': confidence_weight,
                        'pattern_id': pattern_id,
                        'category': category,
                        'span': match.span(),
                        # Signal lineage tracking
                        'lineage': {
                            'pattern_id': pattern_id,
                            'pattern_text': pattern_str[:50] + '...' if len(pattern_str) > 50 else pattern_str,
                            'match_type': match_type,
                            'confidence_weight': confidence_weight,
                            'element_type': element_type,
                            'extraction_phase': 'microanswering',
                        }
                    })
            except re.error as e:
                logger.warning(
                    "pattern_regex_error",
                    pattern_id=pattern_id,
                    error=str(e)
                )
                continue
    
    # Deduplicate overlapping matches, keeping highest confidence
    return _deduplicate_matches(matches)


def _infer_pattern_categories_for_element(element_type: str) -> list[str] | None:
    """
    Infer which pattern categories are relevant for an element type.
    
    Returns None to accept all categories if no specific hint exists.
    """
    # Temporal elements
    if any(kw in element_type.lower() for kw in ['temporal', 'año', 'años', 'plazo', 'cronograma', 'series']):
        return ['TEMPORAL', 'GENERAL']
    
    # Quantitative elements
    if any(kw in element_type.lower() for kw in ['cuantitativo', 'indicador', 'meta', 'brecha', 'baseline']):
        return ['QUANTITATIVE', 'GENERAL']
    
    # Geographic/territorial
    if any(kw in element_type.lower() for kw in ['territorial', 'cobertura', 'geographic', 'región']):
        return ['GEOGRAPHIC', 'GENERAL']
    
    # Sources/entities
    if any(kw in element_type.lower() for kw in ['fuente', 'entidad', 'responsable', 'oficial']):
        return ['ENTITY', 'GENERAL']
    
    # Accept all if no specific hint
    return None


def _is_pattern_relevant_to_element(
    pattern_str: str,
    element_type: str,
    pattern_spec: dict[str, Any]
) -> bool:
    """
    Determine if a pattern is relevant to extracting a specific element type.
    
    Uses keyword overlap between pattern and element type.
    """
    # Extract keywords from element type
    element_keywords = set(re.findall(r'\w+', element_type.lower()))
    
    # Extract keywords from pattern
    pattern_keywords = set(re.findall(r'\w+', pattern_str.lower()))
    
    # Check validation_rule field
    validation_rule = pattern_spec.get('validation_rule', '')
    if validation_rule:
        pattern_keywords.update(re.findall(r'\w+', validation_rule.lower()))
    
    # Check context_requirement
    context_req = pattern_spec.get('context_requirement', '')
    if context_req:
        pattern_keywords.update(re.findall(r'\w+', context_req.lower()))
    
    # Overlap heuristic
    overlap = element_keywords & pattern_keywords
    
    # If there's keyword overlap, it's relevant
    if overlap:
        return True
    
    # Fallback: if element type is very generic, accept pattern
    if len(element_keywords) <= 2:
        return True
    
    return False


def _deduplicate_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Remove overlapping matches, keeping the one with highest confidence.
    """
    if not matches:
        return []
    
    # Sort by start position, then by confidence descending
    sorted_matches = sorted(matches, key=lambda m: (m['span'][0], -m['confidence']))
    
    deduplicated = []
    last_end = -1
    
    for match in sorted_matches:
        start, end = match['span']
        
        # If no overlap with previous, keep it
        if start >= last_end:
            deduplicated.append(match)
            last_end = end
        # If overlap, only keep if significantly higher confidence
        elif deduplicated and match['confidence'] > deduplicated[-1]['confidence'] + 0.2:
            deduplicated[-1] = match
            last_end = end
    
    return deduplicated


def compute_completeness(
    evidence: dict[str, list[dict[str, Any]]],
    expected_elements: list[dict[str, Any]]
) -> float:
    """
    Compute completeness score (0.0 - 1.0).
    
    Algorithm:
    - For required elements: 1.0 if found, 0.0 if not
    - For minimum elements: found_count / minimum
    - Weighted average across all elements
    """
    if not expected_elements:
        return 1.0
    
    scores = []
    
    for element_spec in expected_elements:
        element_type = element_spec.get('type', '')
        is_required = element_spec.get('required', False)
        minimum_count = element_spec.get('minimum', 0)
        
        found = evidence.get(element_type, [])
        found_count = len(found)
        
        if is_required:
            # Binary: found or not
            score = 1.0 if found_count > 0 else 0.0
        elif minimum_count > 0:
            # Proportional: found / minimum, capped at 1.0
            score = min(1.0, found_count / minimum_count)
        else:
            # Optional element: presence is bonus
            score = 1.0 if found_count > 0 else 0.5
        
        scores.append(score)
    
    return sum(scores) / len(scores) if scores else 0.0


# Public API
__all__ = [
    'extract_structured_evidence',
    'EvidenceExtractionResult'
]
