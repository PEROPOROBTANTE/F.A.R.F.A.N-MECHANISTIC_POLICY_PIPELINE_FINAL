"""
SCORING MODULE - Question Scoring According to Questionnaire Monolith
======================================================================
File: scoring.py
Code: SC
Purpose: Apply scoring modalities to question results

This module implements the scoring system for policy assessment questions.
All scoring modalities and quality thresholds are defined in the questionnaire
monolith specification (lines 34512-34607).

SCORING MODALITIES (6 types):
------------------------------
1. TYPE_A: Count 4 elements and scale to 0-3 (threshold=0.7 ratio)
   - Used when 4 specific policy elements must be present
   - Threshold: 70% of elements must be found to receive partial credit

2. TYPE_B: Count up to 3 elements, each worth 1 point
   - Used for independent policy components
   - Each element contributes equally to the final score

3. TYPE_C: Count 2 elements and scale to 0-3 (threshold=0.5 ratio)
   - Used when 2 critical policy elements must be present
   - Threshold: 50% of elements must be found to receive partial credit

4. TYPE_D: Count 3 elements, weighted [0.4, 0.3, 0.3]
   - Used when policy elements have different importance
   - First element has highest weight (40%), others equal (30% each)

5. TYPE_E: Boolean presence check
   - Binary scoring: element is present (3 points) or absent (0 points)

6. TYPE_F: Semantic matching with cosine similarity (normalized_continuous)
   - Uses text similarity to assess policy alignment
   - Continuous score based on semantic similarity (0.0-1.0 range)

QUALITY LEVELS:
---------------
Quality levels are determined from normalized scores (0.0-1.0 scale):
- EXCELLENT: ≥ 0.85 (85th percentile) - green indicator
- GOOD: ≥ 0.70 (70th percentile) - blue indicator
- ACCEPTABLE: ≥ 0.55 (55th percentile) - yellow indicator
- INSUFFICIENT: < 0.55 (below 55th percentile) - red indicator

CORE METHODS:
-------------
1. MicroQuestionScorer.score_type_a() - TYPE_A scoring logic
2. MicroQuestionScorer.score_type_b() - TYPE_B scoring logic
3. MicroQuestionScorer.score_type_c() - TYPE_C scoring logic
4. MicroQuestionScorer.score_type_d() - TYPE_D scoring logic
5. MicroQuestionScorer.score_type_e() - TYPE_E scoring logic
6. MicroQuestionScorer.score_type_f() - TYPE_F scoring logic
7. MicroQuestionScorer.apply_scoring_modality() - Dispatcher for modalities
8. MicroQuestionScorer.determine_quality_level() - Maps scores to quality levels

DATA FLOW:
----------
Input: QuestionResult with evidence from Phase 2 evaluation
Output: ScoredResult with score (0-3 range) and quality level classification

REFERENCE:
----------
Questionnaire monolith specification lines 34512-34607
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS - EXACTOS DEL MONOLITH
# ============================================================================

class ScoringModality(Enum):
    """Modalidades de scoring del monolith (línea 34535)."""
    TYPE_A = "TYPE_A"  # Count 4 elements and scale to 0-3
    TYPE_B = "TYPE_B"  # Count up to 3 elements, each worth 1 point
    TYPE_C = "TYPE_C"  # Count 2 elements and scale to 0-3
    TYPE_D = "TYPE_D"  # Count 3 elements, weighted
    TYPE_E = "TYPE_E"  # Boolean presence check
    TYPE_F = "TYPE_F"  # Semantic matching with cosine similarity

class QualityLevel(Enum):
    """Niveles de calidad micro (línea 34513)."""
    EXCELENTE = "EXCELENTE"    # ≥ 0.85
    BUENO = "BUENO"           # ≥ 0.70
    ACEPTABLE = "ACEPTABLE"   # ≥ 0.55
    INSUFICIENTE = "INSUFICIENTE"  # < 0.55

# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class ScoringConfig:
    """
    Scoring configuration extracted from questionnaire monolith specification.

    This configuration defines all parameters for the six scoring modalities
    and quality level thresholds. All values are derived from the questionnaire
    monolith specification (lines 34512-34607).

    Attributes:
        TYPE_A Configuration (line 34568):
            type_a_threshold: Ratio threshold for partial credit (0.0-1.0 scale, default: 0.7)
                             Elements found / expected must exceed this to receive credit
            type_a_max_score: Maximum score achievable (default: 3.0 points)
            type_a_expected_elements: Number of elements expected (default: 4 elements)

        TYPE_B Configuration (line 34574):
            type_b_max_score: Maximum score achievable (default: 3.0 points)
            type_b_max_elements: Maximum elements to count (default: 3 elements)

        TYPE_C Configuration (line 34580):
            type_c_threshold: Ratio threshold for partial credit (0.0-1.0 scale, default: 0.5)
                             Elements found / expected must exceed this to receive credit
            type_c_max_score: Maximum score achievable (default: 3.0 points)
            type_c_expected_elements: Number of elements expected (default: 2 elements)

        TYPE_D Configuration (line 34586):
            type_d_weights: Importance weights for each element (0.0-1.0 scale per weight,
                           must sum to 1.0, default: [0.4, 0.3, 0.3])
                           First element weighted 40%, second and third 30% each
            type_d_max_score: Maximum score achievable (default: 3.0 points)
            type_d_expected_elements: Number of elements expected (default: 3 elements)

        TYPE_E Configuration (line 34596):
            type_e_max_score: Maximum score achievable (default: 3.0 points)
                             Binary: full score if present, 0 if absent

        TYPE_F Configuration (line 34601):
            type_f_max_score: Maximum score achievable (default: 3.0 points)
            type_f_normalization: Normalization method for similarity scores (default: "minmax")
                                 Options: "minmax", "zscore", "none"

        Quality Level Thresholds (line 34513):
            level_excelente_min: Minimum normalized score for EXCELLENT (0.0-1.0 scale, default: 0.85)
            level_bueno_min: Minimum normalized score for GOOD (0.0-1.0 scale, default: 0.70)
            level_aceptable_min: Minimum normalized score for ACCEPTABLE (0.0-1.0 scale, default: 0.55)
            level_insuficiente_min: Minimum normalized score for INSUFFICIENT (0.0-1.0 scale, default: 0.0)
    """

    # TYPE_A config (line 34568)
    type_a_threshold: float = 0.7  # Ratio (0.0-1.0): proportion of elements required
    type_a_max_score: float = 3.0  # Points: maximum achievable score
    type_a_expected_elements: int = 4  # Count: number of policy elements to check

    # TYPE_B config (line 34574)
    type_b_max_score: float = 3.0  # Points: maximum achievable score
    type_b_max_elements: int = 3  # Count: maximum elements to score

    # TYPE_C config (line 34580)
    type_c_threshold: float = 0.5  # Ratio (0.0-1.0): proportion of elements required
    type_c_max_score: float = 3.0  # Points: maximum achievable score
    type_c_expected_elements: int = 2  # Count: number of policy elements to check

    # TYPE_D config (line 34586)
    type_d_weights: list[float] = field(default_factory=lambda: [0.4, 0.3, 0.3])  # Weights (sum to 1.0): element importance
    type_d_max_score: float = 3.0  # Points: maximum achievable score
    type_d_expected_elements: int = 3  # Count: number of policy elements to check

    # TYPE_E config (line 34596)
    type_e_max_score: float = 3.0  # Points: maximum achievable score (binary: 3.0 or 0.0)

    # TYPE_F config (line 34601)
    type_f_max_score: float = 3.0  # Points: maximum achievable score
    type_f_normalization: str = "minmax"  # Method: "minmax", "zscore", or "none"

    # Quality levels (line 34513) - All thresholds are normalized scores (0.0-1.0 scale)
    level_excelente_min: float = 0.85  # Ratio (0.0-1.0): minimum for EXCELLENT quality
    level_bueno_min: float = 0.70  # Ratio (0.0-1.0): minimum for GOOD quality
    level_aceptable_min: float = 0.55  # Ratio (0.0-1.0): minimum for ACCEPTABLE quality
    level_insuficiente_min: float = 0.0  # Ratio (0.0-1.0): minimum for INSUFFICIENT quality

@dataclass
class Evidence:
    """
    Evidencia extraída para una pregunta.
    Producida por evaluadores en FASE 2.
    """
    elements_found: list[str] = field(default_factory=list)
    confidence_scores: list[float] = field(default_factory=list)
    semantic_similarity: float | None = None
    pattern_matches: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ScoredResult:
    """
    Resultado con score aplicado.
    Output de este módulo.
    """
    question_id: str
    question_global: int
    scoring_modality: ScoringModality
    raw_score: float  # 0-3
    normalized_score: float  # 0-1 (raw_score / 3.0)
    quality_level: QualityLevel
    quality_color: str  # "green", "blue", "yellow", "red"
    evidence: Evidence
    scoring_details: dict[str, Any] = field(default_factory=dict)

# ============================================================================
# CLASE: MicroQuestionScorer
# ============================================================================

class MicroQuestionScorer:
    """
    Aplicador de modalidades de scoring según monolith.

    Responsabilidades:
    - Aplicar TYPE_A, TYPE_B, TYPE_C, TYPE_D, TYPE_E, TYPE_F
    - Calcular score 0-3
    - Determinar nivel de calidad (EXCELENTE/BUENO/ACEPTABLE/INSUFICIENTE)
    """

    def __init__(self, config: ScoringConfig | None = None) -> None:
        """
        Inicializa scorer con configuración del monolith.

        Args:
            config: Configuración de scoring (defaults del monolith si None)
        """
        self.config = config or ScoringConfig()
        self.logger = logger

    # ========================================================================
    # MÉTODO 1: SCORE TYPE_A
    # ========================================================================

    def score_type_a(self, evidence: Evidence) -> tuple[float, dict[str, Any]]:
        """
        MÉTODO 1: TYPE_A - Count 4 elements and scale to 0-3.

        ESPECIFICACIÓN (línea 34568 del monolith):
        - Aggregation: "presence_threshold"
        - Threshold: 0.7
        - Max_score: 3
        - Expected_elements: 4

        LÓGICA:
        1. Contar elementos encontrados (expected: 4)
        2. Calcular ratio = found / 4
        3. Si ratio >= 0.7: aplicar escala proporcional
        4. Si ratio < 0.7: penalizar fuertemente

        ESCALA:
        - 4/4 elementos (100%) → 3.0
        - 3/4 elementos (75%) → 2.25
        - 2/4 elementos (50%) → penalizado
        - 1/4 elementos (25%) → penalizado
        - 0/4 elementos (0%) → 0.0

        Args:
            evidence: Evidencia extraída con elements_found

        Returns:
            Tuple de (score, details)
        """
        elements_found = len(evidence.elements_found)
        expected = self.config.type_a_expected_elements
        threshold = self.config.type_a_threshold
        max_score = self.config.type_a_max_score

        # Calcular ratio
        ratio = elements_found / expected if expected > 0 else 0.0

        # Aplicar threshold del monolith
        if ratio >= threshold:
            # Escala proporcional: ratio * max_score
            score = ratio * max_score
        else:
            # Penalización: escala cuadrática para ratios bajos
            score = (ratio / threshold) * (ratio * max_score)

        # Clip al rango [0, max_score]
        score = max(0.0, min(max_score, score))

        details = {
            'modality': 'TYPE_A',
            'elements_found': elements_found,
            'expected_elements': expected,
            'ratio': ratio,
            'threshold': threshold,
            'threshold_met': ratio >= threshold,
            'raw_score': score,
            'formula': 'ratio * max_score if ratio >= threshold else penalized'
        }

        self.logger.debug(f"TYPE_A: {elements_found}/{expected} elementos ({ratio:.2f}) → score={score:.2f}")

        return score, details

    # ========================================================================
    # MÉTODO 2: SCORE TYPE_B
    # ========================================================================

    def score_type_b(self, evidence: Evidence) -> tuple[float, dict[str, Any]]:
        """
        MÉTODO 2: TYPE_B - Count up to 3 elements, each worth 1 point.

        ESPECIFICACIÓN (línea 34574 del monolith):
        - Aggregation: "binary_sum"
        - Max_score: 3
        - Max_elements: 3

        LÓGICA:
        1. Contar elementos encontrados (max: 3)
        2. Cada elemento = 1 punto
        3. Score = min(elements_found, 3)

        ESCALA:
        - 3+ elementos → 3.0
        - 2 elementos → 2.0
        - 1 elemento → 1.0
        - 0 elementos → 0.0

        Args:
            evidence: Evidencia extraída con elements_found

        Returns:
            Tuple de (score, details)
        """
        elements_found = len(evidence.elements_found)
        max_elements = self.config.type_b_max_elements
        max_score = self.config.type_b_max_score

        # Binary sum: cada elemento vale 1 punto, hasta max_elements
        score = min(float(elements_found), max_elements)

        # Asegurar que no excede max_score
        score = min(score, max_score)

        details = {
            'modality': 'TYPE_B',
            'elements_found': elements_found,
            'max_elements': max_elements,
            'raw_score': score,
            'formula': 'min(elements_found, 3)'
        }

        self.logger.debug(f"TYPE_B: {elements_found} elementos → score={score:.2f}")

        return score, details

    # ========================================================================
    # MÉTODO 3: SCORE TYPE_C
    # ========================================================================

    def score_type_c(self, evidence: Evidence) -> tuple[float, dict[str, Any]]:
        """
        MÉTODO 3: TYPE_C - Count 2 elements and scale to 0-3.

        ESPECIFICACIÓN (línea 34580 del monolith):
        - Aggregation: "presence_threshold"
        - Threshold: 0.5
        - Max_score: 3
        - Expected_elements: 2

        LÓGICA:
        1. Contar elementos encontrados (expected: 2)
        2. Calcular ratio = found / 2
        3. Si ratio >= 0.5: aplicar escala proporcional
        4. Si ratio < 0.5: penalizar

        ESCALA:
        - 2/2 elementos (100%) → 3.0
        - 1/2 elementos (50%) → 1.5
        - 0/2 elementos (0%) → 0.0

        Args:
            evidence: Evidencia extraída con elements_found

        Returns:
            Tuple de (score, details)
        """
        elements_found = len(evidence.elements_found)
        expected = self.config.type_c_expected_elements
        threshold = self.config.type_c_threshold
        max_score = self.config.type_c_max_score

        # Calcular ratio
        ratio = elements_found / expected if expected > 0 else 0.0

        # Aplicar threshold del monolith
        if ratio >= threshold:
            # Escala proporcional
            score = ratio * max_score
        else:
            # Penalización cuadrática
            score = (ratio / threshold) * (ratio * max_score)

        # Clip al rango [0, max_score]
        score = max(0.0, min(max_score, score))

        details = {
            'modality': 'TYPE_C',
            'elements_found': elements_found,
            'expected_elements': expected,
            'ratio': ratio,
            'threshold': threshold,
            'threshold_met': ratio >= threshold,
            'raw_score': score,
            'formula': 'ratio * max_score if ratio >= threshold else penalized'
        }

        self.logger.debug(f"TYPE_C: {elements_found}/{expected} elementos ({ratio:.2f}) → score={score:.2f}")

        return score, details

    # ========================================================================
    # MÉTODO 4: SCORE TYPE_D
    # ========================================================================

    def score_type_d(self, evidence: Evidence) -> tuple[float, dict[str, Any]]:
        """
        MÉTODO 4: TYPE_D - Count 3 elements, weighted [0.4, 0.3, 0.3].

        ESPECIFICACIÓN (línea 34586 del monolith):
        - Aggregation: "weighted_sum"
        - Weights: [0.4, 0.3, 0.3]
        - Max_score: 3
        - Expected_elements: 3

        LÓGICA:
        1. Se esperan 3 elementos con importancia diferente
        2. Elemento 1: peso 0.4 (más importante)
        3. Elemento 2: peso 0.3
        4. Elemento 3: peso 0.3
        5. Score = (sum of weights for found elements) * max_score

        ESCALA:
        - 3 elementos (todos) → weights_sum=1.0 → 3.0
        - 2 elementos (ej: elem1+elem2) → weights_sum=0.7 → 2.1
        - 1 elemento (ej: elem1) → weights_sum=0.4 → 1.2
        - 0 elementos → 0.0

        Args:
            evidence: Evidencia extraída con elements_found y confidence_scores

        Returns:
            Tuple de (score, details)
        """
        elements_found = len(evidence.elements_found)
        expected = self.config.type_d_expected_elements
        weights = self.config.type_d_weights
        max_score = self.config.type_d_max_score

        # Calcular suma ponderada
        # Asumimos que elements_found está ordenado por importancia
        # o usamos confidence_scores si están disponibles
        if evidence.confidence_scores and len(evidence.confidence_scores) >= elements_found:
            # Ordenar por confidence (descendente) y aplicar pesos
            sorted_confidences = sorted(evidence.confidence_scores[:elements_found], reverse=True)
            weighted_sum = sum(
                conf * weights[i]
                for i, conf in enumerate(sorted_confidences)
                if i < len(weights)
            )
        else:
            # Sin confidence scores: asumir presencia binaria
            weighted_sum = sum(weights[:min(elements_found, len(weights))])

        # Score = weighted_sum * max_score
        score = weighted_sum * max_score

        # Clip al rango [0, max_score]
        score = max(0.0, min(max_score, score))

        details = {
            'modality': 'TYPE_D',
            'elements_found': elements_found,
            'expected_elements': expected,
            'weights': weights,
            'weighted_sum': weighted_sum,
            'raw_score': score,
            'formula': 'weighted_sum * max_score'
        }

        self.logger.debug(f"TYPE_D: {elements_found}/{expected} elementos, weighted_sum={weighted_sum:.2f} → score={score:.2f}")

        return score, details

    # ========================================================================
    # MÉTODO 5: SCORE TYPE_E
    # ========================================================================

    def score_type_e(self, evidence: Evidence) -> tuple[float, dict[str, Any]]:
        """
        MÉTODO 5: TYPE_E - Boolean presence check.

        ESPECIFICACIÓN (línea 34596 del monolith):
        - Aggregation: "binary_presence"
        - Max_score: 3

        LÓGICA:
        1. Verificar si existe evidencia (binario: sí/no)
        2. Si existe: 3.0
        3. Si no existe: 0.0

        ESCALA:
        - Evidencia presente → 3.0
        - Evidencia ausente → 0.0

        Args:
            evidence: Evidencia extraída

        Returns:
            Tuple de (score, details)
        """
        max_score = self.config.type_e_max_score

        # Verificar presencia de cualquier evidencia
        has_evidence = (
            len(evidence.elements_found) > 0 or
            bool(evidence.pattern_matches) or
            (evidence.semantic_similarity is not None and evidence.semantic_similarity > 0.5)
        )

        # Binary: todo o nada
        score = max_score if has_evidence else 0.0

        details = {
            'modality': 'TYPE_E',
            'has_evidence': has_evidence,
            'elements_found': len(evidence.elements_found),
            'pattern_matches': len(evidence.pattern_matches),
            'semantic_similarity': evidence.semantic_similarity,
            'raw_score': score,
            'formula': 'max_score if has_evidence else 0.0'
        }

        self.logger.debug(f"TYPE_E: evidencia={'presente' if has_evidence else 'ausente'} → score={score:.2f}")

        return score, details

    # ========================================================================
    # MÉTODO 6: SCORE TYPE_F
    # ========================================================================

    def score_type_f(self, evidence: Evidence) -> tuple[float, dict[str, Any]]:
        """
        MÉTODO 6: TYPE_F - Semantic matching with cosine similarity.

        ESPECIFICACIÓN (línea 34601 del monolith):
        - Aggregation: "normalized_continuous"
        - Normalization: "minmax"
        - Max_score: 3

        LÓGICA:
        1. Usar semantic_similarity (rango 0-1)
        2. Normalizar con minmax
        3. Score = normalized_similarity * max_score

        ESCALA:
        - Similarity = 1.0 → 3.0
        - Similarity = 0.75 → 2.25
        - Similarity = 0.5 → 1.5
        - Similarity = 0.25 → 0.75
        - Similarity = 0.0 → 0.0

        Args:
            evidence: Evidencia con semantic_similarity

        Returns:
            Tuple de (score, details)
        """
        max_score = self.config.type_f_max_score

        # Obtener similarity
        if evidence.semantic_similarity is not None:
            similarity = evidence.semantic_similarity
        else:
            # Fallback: calcular promedio de confidence_scores
            if evidence.confidence_scores:
                similarity = float(np.mean(evidence.confidence_scores))
            else:
                similarity = 0.0

        # Normalización minmax (ya está en rango 0-1)
        normalized_similarity = max(0.0, min(1.0, similarity))

        # Score continuo
        score = normalized_similarity * max_score

        details = {
            'modality': 'TYPE_F',
            'semantic_similarity': similarity,
            'normalized_similarity': normalized_similarity,
            'raw_score': score,
            'formula': 'normalized_similarity * max_score'
        }

        self.logger.debug(f"TYPE_F: similarity={similarity:.3f} → score={score:.2f}")

        return score, details

    # ========================================================================
    # MÉTODO 7: APPLY SCORING MODALITY (ORQUESTADOR)
    # ========================================================================

    def apply_scoring_modality(
        self,
        question_id: str,
        question_global: int,
        modality: ScoringModality,
        evidence: Evidence
    ) -> ScoredResult:
        """
        MÉTODO 7: Aplica la modalidad de scoring correspondiente.

        ORQUESTADOR que delega a métodos 1-6 según modality.

        Args:
            question_id: ID de pregunta (ej: "Q001")
            question_global: Número global (1-305)
            modality: Modalidad de scoring
            evidence: Evidencia extraída

        Returns:
            ScoredResult con score 0-3 y nivel de calidad
        """
        self.logger.info(f"Aplicando scoring {modality.value} a {question_id}")

        # Delegar a método específico
        if modality == ScoringModality.TYPE_A:
            raw_score, details = self.score_type_a(evidence)

        elif modality == ScoringModality.TYPE_B:
            raw_score, details = self.score_type_b(evidence)

        elif modality == ScoringModality.TYPE_C:
            raw_score, details = self.score_type_c(evidence)

        elif modality == ScoringModality.TYPE_D:
            raw_score, details = self.score_type_d(evidence)

        elif modality == ScoringModality.TYPE_E:
            raw_score, details = self.score_type_e(evidence)

        elif modality == ScoringModality.TYPE_F:
            raw_score, details = self.score_type_f(evidence)

        else:
            raise ValueError(f"Modalidad desconocida: {modality}")

        # Normalizar a 0-1
        normalized_score = raw_score / 3.0

        # Determinar nivel de calidad
        quality_level, quality_color = self.determine_quality_level(normalized_score)

        # Construir resultado
        scored_result = ScoredResult(
            question_id=question_id,
            question_global=question_global,
            scoring_modality=modality,
            raw_score=raw_score,
            normalized_score=normalized_score,
            quality_level=quality_level,
            quality_color=quality_color,
            evidence=evidence,
            scoring_details=details
        )

        self.logger.info(
            f"✓ {question_id}: score={raw_score:.2f}/3.0 "
            f"({normalized_score:.2%}), nivel={quality_level.value}"
        )

        return scored_result

    # ========================================================================
    # MÉTODO 8: DETERMINE QUALITY LEVEL
    # ========================================================================

    def determine_quality_level(self, normalized_score: float) -> tuple[QualityLevel, str]:
        """
        MÉTODO 8: Determina nivel de calidad según umbrales del monolith.

        UMBRALES (línea 34513 del monolith):
        - EXCELENTE: ≥ 0.85 (verde)
        - BUENO: ≥ 0.70 (azul)
        - ACEPTABLE: ≥ 0.55 (amarillo)
        - INSUFICIENTE: < 0.55 (rojo)

        Args:
            normalized_score: Score en rango 0-1

        Returns:
            Tuple de (QualityLevel, color)
        """
        if normalized_score >= self.config.level_excelente_min:
            return QualityLevel.EXCELENTE, "green"

        elif normalized_score >= self.config.level_bueno_min:
            return QualityLevel.BUENO, "blue"

        elif normalized_score >= self.config.level_aceptable_min:
            return QualityLevel.ACEPTABLE, "yellow"

        else:
            return QualityLevel.INSUFICIENTE, "red"

# ============================================================================
# FUNCIÓN DE CONVENIENCIA
# ============================================================================

def score_question(
    question_id: str,
    question_global: int,
    modality_str: str,
    evidence_dict: dict[str, Any]
) -> ScoredResult:
    """
    Función de conveniencia para scoring de una pregunta.

    Args:
        question_id: ID de pregunta
        question_global: Número global
        modality_str: String de modalidad ("TYPE_A", "TYPE_B", etc.)
        evidence_dict: Diccionario con evidencia

    Returns:
        ScoredResult
    """
    # Parsear modalidad
    modality = ScoringModality(modality_str)

    # Construir Evidence
    evidence = Evidence(
        elements_found=evidence_dict.get('elements_found', []),
        confidence_scores=evidence_dict.get('confidence_scores', []),
        semantic_similarity=evidence_dict.get('semantic_similarity'),
        pattern_matches=evidence_dict.get('pattern_matches', {}),
        metadata=evidence_dict.get('metadata', {})
    )

    # Aplicar scoring
    scorer = MicroQuestionScorer()
    result = scorer.apply_scoring_modality(
        question_id=question_id,
        question_global=question_global,
        modality=modality,
        evidence=evidence
    )

    return result

# ============================================================================
# EJEMPLO DE USO
# ============================================================================

# Note: Main entry point and examples removed to maintain I/O boundary separation.
    print("="*80)
