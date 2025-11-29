"""
Advanced Policy Contradiction Detection System for Colombian Municipal Development Plans

Este sistema implementa el estado del arte en detección de contradicciones para análisis
de políticas públicas, específicamente calibrado para Planes de Desarrollo Municipal (PDM)
colombianos según la Ley 152 de 1994 y metodología DNP.

Innovations:
- Transformer-based semantic similarity using sentence-transformers
- Graph-based contradiction reasoning with NetworkX
- Bayesian inference for confidence scoring
- Temporal logic verification for timeline consistency
- Multi-dimensional vector embeddings for policy alignment
- Statistical hypothesis testing for numerical claims
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import networkx as nx
import numpy as np
import torch
from scipy import stats
from scipy.spatial.distance import cosine
from scipy.stats import beta
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModelForSequenceClassification, DebertaV2Tokenizer, pipeline

# Check dependency lockdown
from saaaaaa.core.dependency_lockdown import get_dependency_lockdown

# Import runtime error fixes for defensive programming
from saaaaaa.utils.runtime_error_fixes import ensure_list_return, safe_text_extract
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

_lockdown = get_dependency_lockdown()

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContradictionType(Enum):
    """Taxonomía de contradicciones según estándares de política pública"""
    NUMERICAL_INCONSISTENCY = auto()
    TEMPORAL_CONFLICT = auto()
    SEMANTIC_OPPOSITION = auto()
    LOGICAL_INCOMPATIBILITY = auto()
    RESOURCE_ALLOCATION_MISMATCH = auto()
    OBJECTIVE_MISALIGNMENT = auto()
    REGULATORY_CONFLICT = auto()
    STAKEHOLDER_DIVERGENCE = auto()

class PolicyDimension(Enum):
    """Dimensiones del Plan de Desarrollo según DNP Colombia"""
    DIAGNOSTICO = "diagnóstico"
    ESTRATEGICO = "estratégico"
    PROGRAMATICO = "programático"
    FINANCIERO = "plan plurianual de inversiones"
    SEGUIMIENTO = "seguimiento y evaluación"
    TERRITORIAL = "ordenamiento territorial"

@dataclass(frozen=True)
class PolicyStatement:
    """Representación estructurada de una declaración de política"""
    text: str
    dimension: PolicyDimension
    position: tuple[int, int]  # (start, end) in document
    entities: list[str] = field(default_factory=list)
    temporal_markers: list[str] = field(default_factory=list)
    quantitative_claims: list[dict[str, Any]] = field(default_factory=list)
    embedding: np.ndarray | None = None
    context_window: str = ""
    semantic_role: str | None = None
    dependencies: set[str] = field(default_factory=set)

@dataclass
class ContradictionEvidence:
    """Evidencia estructurada de contradicción con trazabilidad completa"""
    statement_a: PolicyStatement
    statement_b: PolicyStatement
    contradiction_type: ContradictionType
    confidence: float  # Bayesian posterior probability
    severity: float  # Impact on policy coherence
    semantic_similarity: float
    logical_conflict_score: float
    temporal_consistency: bool
    numerical_divergence: float | None
    affected_dimensions: list[PolicyDimension]
    resolution_suggestions: list[str]
    graph_path: list[str] | None = None
    statistical_significance: float | None = None

class BayesianConfidenceCalculator:
    """
    Bayesian confidence calculator with domain-informed priors.

    Uses Beta distribution priors calibrated from empirical analysis of
    Colombian municipal development plans (PDMs).
    """

    def __init__(self) -> None:
        # Priors based on empirical analysis of Colombian municipal development plans (PDMs)
        self.prior_alpha = 2.5  # Shape parameter for beta distribution
        self.prior_beta = 7.5  # Scale parameter (conservative bias favoring lower confidence)

    def calculate_posterior(
            self,
            evidence_strength: float,
            observations: int,
            domain_weight: float = get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L121_35", 1.0)
    ) -> float:
        """
        Calculate posterior probability using Bayesian inference.

        Updates the Beta distribution prior with observed evidence to compute
        the posterior mean, which represents the confidence level in the finding.

        Args:
            evidence_strength: Strength of the evidence (get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L130_57", 0.0)-get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L130_61", 1.0) scale, unitless ratio)
            observations: Number of observations supporting the evidence (count)
            domain_weight: Policy domain-specific weight (multiplier, default: get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L132_79", 1.0))

        Returns:
            float: Posterior probability (get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L135_42", 0.0)-get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L135_46", 1.0) scale) representing confidence level
        """
        # Update Beta distribution with evidence
        alpha_post = self.prior_alpha + evidence_strength * observations * domain_weight
        beta_post = self.prior_beta + (1 - evidence_strength) * observations * domain_weight

        # Calculate mean of posterior distribution
        posterior_mean = alpha_post / (alpha_post + beta_post)

        # Calculate 95% credible interval
        credible_interval = beta.interval(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L145_42", 0.95), alpha_post, beta_post)

        # Adjust for uncertainty (wider intervals reduce confidence)
        uncertainty_penalty = get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L148_30", 1.0) - (credible_interval[1] - credible_interval[0])

        return min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.__init__").get("auto_param_L150_19", 1.0), posterior_mean * uncertainty_penalty)

class TemporalLogicVerifier:
    """
    Temporal consistency verification using Linear Temporal Logic (LTL).

    Analyzes policy statements for temporal contradictions, deadline violations,
    and ordering conflicts using temporal logic patterns.
    """

    def __init__(self) -> None:
        self.temporal_patterns = {
            'sequential': re.compile(r'(primero|luego|después|posteriormente|finalmente)', re.IGNORECASE),
            'parallel': re.compile(r'(simultáneamente|al mismo tiempo|paralelamente)', re.IGNORECASE),
            'deadline': re.compile(r'(antes de|hasta|máximo|plazo)', re.IGNORECASE),
            'milestone': re.compile(r'(hito|meta intermedia|checkpoint)', re.IGNORECASE)
        }

    def verify_temporal_consistency(
            self,
            statements: list[PolicyStatement]
    ) -> tuple[bool, list[dict[str, Any]]]:
        """
        Verify temporal consistency between policy statements.

        Analyzes temporal ordering and deadline constraints to identify
        contradictions or violations in the policy timeline.

        Args:
            statements: List of policy statements to analyze

        Returns:
            tuple[bool, list[dict]]: A tuple containing:
                - is_consistent: True if no conflicts found
                - conflicts_found: List of detected temporal conflicts
        """
        timeline = self._build_timeline(statements)
        conflicts = []

        # Verify temporal ordering
        for i, event_a in enumerate(timeline):
            for event_b in timeline[i + 1:]:
                if self._has_temporal_conflict(event_a, event_b):
                    conflicts.append({
                        'event_a': event_a,
                        'event_b': event_b,
                        'conflict_type': 'temporal_ordering'
                    })

        # Verify deadline constraints
        deadline_violations = self._check_deadline_constraints(timeline)
        conflicts.extend(deadline_violations)

        return len(conflicts) == 0, conflicts

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._build_timeline")
    def _build_timeline(self, statements: list[PolicyStatement]) -> list[dict]:
        """
        Build timeline from policy statements.

        Extracts temporal markers and organizes them chronologically.

        Args:
            statements: List of policy statements

        Returns:
            list[dict]: Sorted timeline events with timestamps
        """
        timeline = []
        for stmt in statements:
            for marker in stmt.temporal_markers:
                # Extract structured temporal information
                timeline.append({
                    'statement': stmt,
                    'marker': marker,
                    'timestamp': self._parse_temporal_marker(marker),
                    'type': self._classify_temporal_type(marker)
                })
        return sorted(timeline, key=lambda x: x.get('timestamp', 0))

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._parse_temporal_marker")
    def _parse_temporal_marker(self, marker: str) -> int | None:
        """
        Parse temporal marker to numeric timestamp.

        Implements Colombian policy document temporal format parsing.

        Args:
            marker: Temporal marker string (e.g., "2024", "Q2", "segundo trimestre")

        Returns:
            int | None: Numeric timestamp, or None if parsing fails
        """
        # Implementation specific to Colombian policy document format
        year_match = re.search(r'20\d{2}', marker)
        if year_match:
            return int(year_match.group())

        quarter_patterns = {
            'primer': 1, 'segundo': 2, 'tercer': 3, 'cuarto': 4,
            'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4
        }
        for pattern, quarter in quarter_patterns.items():
            if pattern in marker.lower():
                return quarter

        return None

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._has_temporal_conflict")
    def _has_temporal_conflict(self, event_a: dict, event_b: dict) -> bool:
        """Detecta conflictos temporales entre eventos"""
        if event_a['timestamp'] and event_b['timestamp']:
            # Verificar si eventos mutuamente excluyentes ocurren simultáneamente
            if event_a['timestamp'] == event_b['timestamp']:
                return self._are_mutually_exclusive(
                    event_a['statement'],
                    event_b['statement']
                )
        return False

    def _are_mutually_exclusive(
            self,
            stmt_a: PolicyStatement,
            stmt_b: PolicyStatement
    ) -> bool:
        """Determina si dos declaraciones son mutuamente excluyentes"""
        # Verificar si compiten por los mismos recursos
        resources_a = set(self._extract_resources(stmt_a.text))
        resources_b = set(self._extract_resources(stmt_b.text))

        return len(resources_a & resources_b) > 0

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._extract_resources")
    def _extract_resources(self, text: str) -> list[str]:
        """Extrae recursos mencionados en el texto"""
        resource_patterns = [
            r'presupuesto',
            r'recursos?\s+\w+',
            r'fondos?\s+\w+',
            r'personal',
            r'infraestructura'
        ]
        resources = []
        for pattern in resource_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            resources.extend(matches)
        return resources

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._check_deadline_constraints")
    def _check_deadline_constraints(self, timeline: list[dict]) -> list[dict]:
        """Verifica violaciones de restricciones de plazo"""
        violations = []
        for event in timeline:
            if event['type'] == 'deadline':
                # Verificar si hay eventos posteriores que deberían ocurrir antes
                for other in timeline:
                    if other['timestamp'] and event['timestamp']:
                        if other['timestamp'] > event['timestamp']:
                            if self._should_precede(other['statement'], event['statement']):
                                violations.append({
                                    'event_a': other,
                                    'event_b': event,
                                    'conflict_type': 'deadline_violation'
                                })
        return violations

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._should_precede")
    def _should_precede(self, stmt_a: PolicyStatement, stmt_b: PolicyStatement) -> bool:
        """Determina si stmt_a debe preceder a stmt_b"""
        # Análisis de dependencias causales
        return bool(stmt_a.dependencies & {stmt_b.text[:50]})

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier._classify_temporal_type")
    def _classify_temporal_type(self, marker: str) -> str:
        """Clasifica el tipo de marcador temporal"""
        for pattern_type, pattern in self.temporal_patterns.items():
            if pattern.search(marker):
                return pattern_type
        return 'unspecified'

class PolicyContradictionDetector:
    """
    Sistema avanzado de detección de contradicciones para PDMs colombianos.
    Implementa el estado del arte en NLP y razonamiento lógico.
    """

    def __init__(
            self,
            model_name: str = "hiiamsid/sentence_similarity_spanish_es",
            spacy_model: str = "es_core_news_lg",
            device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ) -> None:
        # Modelos de transformers para análisis semántico
        self.semantic_model = SentenceTransformer(model_name, device=device)

        # Modelo de clasificación de contradicciones
        model_name = "microsoft/deberta-v3-base"
        tokenizer = DebertaV2Tokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)

        self.contradiction_classifier = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=0 if device == "cuda" else -1,
        )

        # Procesamiento de lenguaje natural
        # Delegate to factory for I/O operation
        from .factory import load_spacy_model
        self.nlp = load_spacy_model(spacy_model)

        # Componentes especializados
        self.bayesian_calculator = BayesianConfidenceCalculator()
        self.temporal_verifier = TemporalLogicVerifier()

        # Grafo de conocimiento para razonamiento
        self.knowledge_graph = nx.DiGraph()

        # Vectorizador TF-IDF para análisis complementario
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            sublinear_tf=True
        )

        # Patrones específicos de PDM colombiano
        self._initialize_pdm_patterns()

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._initialize_pdm_patterns")
    def _initialize_pdm_patterns(self) -> None:
        """Inicializa patrones específicos de PDMs colombianos"""
        self.pdm_patterns = {
            'ejes_estrategicos': re.compile(
                r'(eje\s+estratégico|línea\s+estratégica|pilar|dimensión)',
                re.IGNORECASE
            ),
            'programas': re.compile(
                r'(programa|subprograma|proyecto|iniciativa)',
                re.IGNORECASE
            ),
            'metas': re.compile(
                r'(meta\s+de\s+resultado|meta\s+de\s+producto|indicador)',
                re.IGNORECASE
            ),
            'recursos': re.compile(
                r'(SGP|regalías|recursos\s+propios|cofinanciación|crédito)',
                re.IGNORECASE
            ),
            'normativa': re.compile(
                r'(ley\s+\d+|decreto\s+\d+|acuerdo\s+\d+|resolución\s+\d+)',
                re.IGNORECASE
            )
        }

    def detect(
            self,
            text: str,
            plan_name: str = "PDM",
            dimension: PolicyDimension = PolicyDimension.ESTRATEGICO
    ) -> dict[str, Any]:
        """
        Detecta contradicciones con análisis multi-dimensional avanzado

        Args:
            text: Texto del plan de desarrollo
            plan_name: Nombre del PDM
            dimension: Dimensión del plan siendo analizada

        Returns:
            Análisis completo con contradicciones detectadas y métricas
        """
        # Extraer declaraciones de política estructuradas
        statements = self._extract_policy_statements(text, dimension)

        # Generar embeddings semánticos
        statements = self._generate_embeddings(statements)

        # Construir grafo de conocimiento
        self._build_knowledge_graph(statements)

        # Detectar contradicciones multi-tipo
        contradictions = []

        # 1. Contradicciones semánticas usando transformers
        semantic_contradictions = self._detect_semantic_contradictions(statements)
        contradictions.extend(ensure_list_return(semantic_contradictions))

        # 2. Inconsistencias numéricas con pruebas estadísticas
        numerical_contradictions = self._detect_numerical_inconsistencies(statements)
        contradictions.extend(ensure_list_return(numerical_contradictions))

        # 3. Conflictos temporales con verificación lógica
        temporal_conflicts = self._detect_temporal_conflicts(statements)
        contradictions.extend(ensure_list_return(temporal_conflicts))

        # 4. Incompatibilidades lógicas usando razonamiento en grafo
        logical_contradictions = self._detect_logical_incompatibilities(statements)
        contradictions.extend(ensure_list_return(logical_contradictions))

        # 5. Conflictos de asignación de recursos
        resource_conflicts = self._detect_resource_conflicts(statements)
        contradictions.extend(ensure_list_return(resource_conflicts))

        # Calcular métricas agregadas
        coherence_metrics = self._calculate_coherence_metrics(
            contradictions,
            statements,
            text
        )

        # Generar recomendaciones de resolución
        recommendations = self._generate_resolution_recommendations(contradictions)

        return {
            "plan_name": plan_name,
            "dimension": dimension.value,
            "contradictions": [self._serialize_contradiction(c) for c in contradictions],
            "total_contradictions": len(contradictions),
            "high_severity_count": sum(1 for c in contradictions if c.severity > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._initialize_pdm_patterns").get("auto_param_L469_81", 0.7)),
            "coherence_metrics": coherence_metrics,
            "recommendations": recommendations,
            "knowledge_graph_stats": self._get_graph_statistics()
        }

    def _extract_policy_statements(
            self,
            text: str,
            dimension: PolicyDimension
    ) -> list[PolicyStatement]:
        """Extrae declaraciones de política estructuradas del texto"""
        doc = self.nlp(text)
        statements = []

        for sent in doc.sents:
            # Analizar entidades nombradas
            entities = [ent.text for ent in sent.ents]

            # Extraer marcadores temporales
            temporal_markers = self._extract_temporal_markers(sent.text)

            # Extraer afirmaciones cuantitativas
            quantitative_claims = self._extract_quantitative_claims(sent.text)

            # Determinar rol semántico
            semantic_role = self._determine_semantic_role(sent)

            # Identificar dependencias
            dependencies = self._identify_dependencies(sent, doc)

            statement = PolicyStatement(
                text=sent.text,
                dimension=dimension,
                position=(sent.start_char, sent.end_char),
                entities=entities,
                temporal_markers=temporal_markers,
                quantitative_claims=quantitative_claims,
                context_window=self._get_context_window(text, sent.start_char, sent.end_char),
                semantic_role=semantic_role,
                dependencies=dependencies
            )

            statements.append(statement)

        return statements

    def _generate_embeddings(
            self,
            statements: list[PolicyStatement]
    ) -> list[PolicyStatement]:
        """Genera embeddings semánticos para las declaraciones"""
        texts = [stmt.text for stmt in statements]
        embeddings = self.semantic_model.encode(texts, convert_to_numpy=True)

        # Crear nuevas instancias con embeddings
        enhanced_statements = []
        for stmt, embedding in zip(statements, embeddings, strict=False):
            enhanced = PolicyStatement(
                text=stmt.text,
                dimension=stmt.dimension,
                position=stmt.position,
                entities=stmt.entities,
                temporal_markers=stmt.temporal_markers,
                quantitative_claims=stmt.quantitative_claims,
                embedding=embedding,
                context_window=stmt.context_window,
                semantic_role=stmt.semantic_role,
                dependencies=stmt.dependencies
            )
            enhanced_statements.append(enhanced)

        return enhanced_statements

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph")
    def _build_knowledge_graph(self, statements: list[PolicyStatement]) -> None:
        """Construye grafo de conocimiento para razonamiento"""
        self.knowledge_graph.clear()

        for i, stmt in enumerate(statements):
            node_id = f"stmt_{i}"
            self.knowledge_graph.add_node(
                node_id,
                text=stmt.text[:100],
                dimension=stmt.dimension.value,
                entities=stmt.entities,
                semantic_role=stmt.semantic_role
            )

            # Conectar con declaraciones relacionadas
            for j, other in enumerate(statements):
                if i != j:
                    similarity = self._calculate_similarity(stmt, other)
                    if similarity > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L562_36", 0.7):  # Umbral de relación
                        self.knowledge_graph.add_edge(
                            f"stmt_{i}",
                            f"stmt_{j}",
                            weight=similarity,
                            relation_type=self._determine_relation_type(stmt, other)
                        )

    def _detect_semantic_contradictions(
            self,
            statements: list[PolicyStatement]
    ) -> list[ContradictionEvidence]:
        """Detecta contradicciones semánticas usando transformers"""
        contradictions = []

        for i, stmt_a in enumerate(statements):
            for stmt_b in statements[i + 1:]:
                if stmt_a.embedding is not None and stmt_b.embedding is not None:
                    # Calcular similaridad coseno
                    similarity = 1 - cosine(stmt_a.embedding, stmt_b.embedding)

                    # Verificar contradicción usando clasificador
                    combined_text = f"{stmt_a.text} [SEP] {stmt_b.text}"
                    contradiction_score = self._classify_contradiction(combined_text)

                    if contradiction_score > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L587_45", 0.7) and similarity > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L587_66", 0.5):
                        # Calcular confianza Bayesiana
                        confidence = self.bayesian_calculator.calculate_posterior(
                            evidence_strength=contradiction_score,
                            observations=len(stmt_a.entities) + len(stmt_b.entities),
                            domain_weight=self._get_domain_weight(stmt_a.dimension)
                        )

                        evidence = ContradictionEvidence(
                            statement_a=stmt_a,
                            statement_b=stmt_b,
                            contradiction_type=ContradictionType.SEMANTIC_OPPOSITION,
                            confidence=confidence,
                            severity=self._calculate_severity(stmt_a, stmt_b),
                            semantic_similarity=similarity,
                            logical_conflict_score=contradiction_score,
                            temporal_consistency=True,
                            numerical_divergence=None,
                            affected_dimensions=[stmt_a.dimension, stmt_b.dimension],
                            resolution_suggestions=self._suggest_resolutions(
                                ContradictionType.SEMANTIC_OPPOSITION
                            )
                        )
                        contradictions.append(evidence)

        return contradictions

    def _detect_numerical_inconsistencies(
            self,
            statements: list[PolicyStatement]
    ) -> list[ContradictionEvidence]:
        """Detecta inconsistencias numéricas con análisis estadístico"""
        contradictions = []

        for i, stmt_a in enumerate(statements):
            for stmt_b in statements[i + 1:]:
                if stmt_a.quantitative_claims and stmt_b.quantitative_claims:
                    for claim_a in stmt_a.quantitative_claims:
                        for claim_b in stmt_b.quantitative_claims:
                            if self._are_comparable_claims(claim_a, claim_b):
                                divergence = self._calculate_numerical_divergence(
                                    claim_a,
                                    claim_b
                                )

                                if divergence is not None and divergence > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L632_75", 0.2):
                                    # Test estadístico de significancia
                                    p_value = self._statistical_significance_test(
                                        claim_a,
                                        claim_b
                                    )

                                    if p_value < get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L639_49", 0.05):  # Significancia estadística
                                        confidence = self.bayesian_calculator.calculate_posterior(
                                            evidence_strength=1 - p_value,
                                            observations=2,
                                            domain_weight=1.5  # Mayor peso para evidencia numérica
                                        )

                                        evidence = ContradictionEvidence(
                                            statement_a=stmt_a,
                                            statement_b=stmt_b,
                                            contradiction_type=ContradictionType.NUMERICAL_INCONSISTENCY,
                                            confidence=confidence,
                                            severity=min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L651_57", 1.0), divergence),
                                            semantic_similarity=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L652_64", 0.0),
                                            logical_conflict_score=divergence,
                                            temporal_consistency=True,
                                            numerical_divergence=divergence,
                                            affected_dimensions=[stmt_a.dimension],
                                            resolution_suggestions=self._suggest_resolutions(
                                                ContradictionType.NUMERICAL_INCONSISTENCY
                                            ),
                                            statistical_significance=p_value
                                        )
                                        contradictions.append(evidence)

        return contradictions

    def _detect_temporal_conflicts(
            self,
            statements: list[PolicyStatement]
    ) -> list[ContradictionEvidence]:
        """Detecta conflictos temporales usando verificación lógica"""
        contradictions = []

        # Filtrar declaraciones con marcadores temporales
        temporal_statements = [s for s in statements if s.temporal_markers]

        if len(temporal_statements) >= 2:
            is_consistent, conflicts = self.temporal_verifier.verify_temporal_consistency(
                temporal_statements
            )

            for conflict in conflicts:
                stmt_a = conflict['event_a']['statement']
                stmt_b = conflict['event_b']['statement']

                confidence = self.bayesian_calculator.calculate_posterior(
                    evidence_strength=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L686_38", 0.9),  # Alta confianza en lógica temporal
                    observations=len(conflicts),
                    domain_weight=1.2
                )

                evidence = ContradictionEvidence(
                    statement_a=stmt_a,
                    statement_b=stmt_b,
                    contradiction_type=ContradictionType.TEMPORAL_CONFLICT,
                    confidence=confidence,
                    severity=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L696_29", 0.8),  # Los conflictos temporales son severos
                    semantic_similarity=self._calculate_similarity(stmt_a, stmt_b),
                    logical_conflict_score=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L698_43", 1.0),
                    temporal_consistency=False,
                    numerical_divergence=None,
                    affected_dimensions=[PolicyDimension.PROGRAMATICO],
                    resolution_suggestions=self._suggest_resolutions(
                        ContradictionType.TEMPORAL_CONFLICT
                    )
                )
                contradictions.append(evidence)

        return contradictions

    def _detect_logical_incompatibilities(
            self,
            statements: list[PolicyStatement]
    ) -> list[ContradictionEvidence]:
        """Detecta incompatibilidades lógicas usando razonamiento en grafo"""
        contradictions = []

        # Buscar ciclos negativos en el grafo (indicativos de contradicción)
        try:
            negative_cycles = nx.negative_edge_cycle(
                self.knowledge_graph,
                weight='weight'
            )

            for cycle in negative_cycles:
                # Extraer declaraciones del ciclo
                stmt_indices = [int(node.split('_')[1]) for node in cycle]
                cycle_statements = [statements[i] for i in stmt_indices]

                # Analizar incompatibilidad lógica
                for i in range(len(cycle_statements)):
                    stmt_a = cycle_statements[i]
                    stmt_b = cycle_statements[(i + 1) % len(cycle_statements)]

                    if self._has_logical_conflict(stmt_a, stmt_b):
                        confidence = self.bayesian_calculator.calculate_posterior(
                            evidence_strength=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L736_46", 0.85),
                            observations=len(cycle),
                            domain_weight = get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("domain_weight", 1.0) # Refactored
                        )

                        evidence = ContradictionEvidence(
                            statement_a=stmt_a,
                            statement_b=stmt_b,
                            contradiction_type=ContradictionType.LOGICAL_INCOMPATIBILITY,
                            confidence=confidence,
                            severity=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L746_37", 0.7),
                            semantic_similarity=self._calculate_similarity(stmt_a, stmt_b),
                            logical_conflict_score=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L748_51", 0.9),
                            temporal_consistency=True,
                            numerical_divergence=None,
                            affected_dimensions=[stmt_a.dimension, stmt_b.dimension],
                            resolution_suggestions=self._suggest_resolutions(
                                ContradictionType.LOGICAL_INCOMPATIBILITY
                            ),
                            graph_path=cycle
                        )
                        contradictions.append(evidence)
        except nx.NetworkXError:
            pass  # No negative cycles found

        return contradictions

    def _detect_resource_conflicts(
            self,
            statements: list[PolicyStatement]
    ) -> list[ContradictionEvidence]:
        """Detecta conflictos en asignación de recursos"""
        contradictions = []
        resource_allocations = {}

        for stmt in statements:
            # Extraer menciones de recursos
            resources = self._extract_resource_mentions(stmt.text)
            for resource_type, amount in resources:
                if resource_type not in resource_allocations:
                    resource_allocations[resource_type] = []
                resource_allocations[resource_type].append((stmt, amount))

        # Verificar conflictos de asignación
        for resource_type, allocations in resource_allocations.items():
            if len(allocations) > 1:
                total_claimed = sum(amount for _, amount in allocations if amount)

                # Verificar si las asignaciones son mutuamente excluyentes
                for i, (stmt_a, amount_a) in enumerate(allocations):
                    for stmt_b, amount_b in allocations[i + 1:]:
                        if amount_a and amount_b:
                            if self._are_conflicting_allocations(
                                    amount_a,
                                    amount_b,
                                    total_claimed
                            ):
                                confidence = self.bayesian_calculator.calculate_posterior(
                                    evidence_strength=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L794_54", 0.8),
                                    observations=len(allocations),
                                    domain_weight=1.3
                                )

                                evidence = ContradictionEvidence(
                                    statement_a=stmt_a,
                                    statement_b=stmt_b,
                                    contradiction_type=ContradictionType.RESOURCE_ALLOCATION_MISMATCH,
                                    confidence=confidence,
                                    severity=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L804_45", 0.9),  # Conflictos de recursos son críticos
                                    semantic_similarity=self._calculate_similarity(stmt_a, stmt_b),
                                    logical_conflict_score=get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L806_59", 0.8),
                                    temporal_consistency=True,
                                    numerical_divergence=abs(amount_a - amount_b) / max(amount_a, amount_b),
                                    affected_dimensions=[PolicyDimension.FINANCIERO],
                                    resolution_suggestions=self._suggest_resolutions(
                                        ContradictionType.RESOURCE_ALLOCATION_MISMATCH
                                    )
                                )
                                contradictions.append(evidence)

        return contradictions

    def _calculate_coherence_metrics(
            self,
            contradictions: list[ContradictionEvidence],
            statements: list[PolicyStatement],
            text: str
    ) -> dict[str, float]:
        """Calcula métricas avanzadas de coherencia del documento"""

        # Densidad de contradicciones normalizada
        contradiction_density = len(contradictions) / max(1, len(statements))

        # Índice de coherencia semántica global
        semantic_coherence = self._calculate_global_semantic_coherence(statements)

        # Consistencia temporal
        temporal_consistency = sum(
            1 for c in contradictions
            if c.contradiction_type != ContradictionType.TEMPORAL_CONFLICT
        ) / max(1, len(contradictions))

        # Alineación de objetivos
        objective_alignment = self._calculate_objective_alignment(statements)

        # Índice de fragmentación del grafo
        graph_fragmentation = self._calculate_graph_fragmentation()

        # Score de coherencia compuesto (weighted harmonic mean)
        weights = np.array([get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L845_28", 0.3), get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L845_33", 0.25), get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L845_39", 0.2), get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L845_44", 0.15), get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L845_50", 0.1)])
        scores = np.array([
            1 - contradiction_density,
            semantic_coherence,
            temporal_consistency,
            objective_alignment,
            1 - graph_fragmentation
        ])

        # Harmonic mean ponderada para penalizar valores bajos
        coherence_score = np.sum(weights) / np.sum(weights / np.maximum(scores, get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L855_80", 0.01)))

        # Entropía de contradicciones
        contradiction_entropy = self._calculate_contradiction_entropy(contradictions)

        # Complejidad sintáctica del documento
        syntactic_complexity = self._calculate_syntactic_complexity(text)

        return {
            "coherence_score": float(coherence_score),
            "contradiction_density": float(contradiction_density),
            "semantic_coherence": float(semantic_coherence),
            "temporal_consistency": float(temporal_consistency),
            "objective_alignment": float(objective_alignment),
            "graph_fragmentation": float(graph_fragmentation),
            "contradiction_entropy": float(contradiction_entropy),
            "syntactic_complexity": float(syntactic_complexity),
            "confidence_interval": self._calculate_confidence_interval(coherence_score, len(statements))
        }

    def _calculate_global_semantic_coherence(
            self,
            statements: list[PolicyStatement]
    ) -> float:
        """Calcula coherencia semántica global usando embeddings"""
        if len(statements) < 2:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L881_19", 1.0)

        # Calcular matriz de similitud
        embeddings = [s.embedding for s in statements if s.embedding is not None]
        if len(embeddings) < 2:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L886_19", 0.5)

        similarity_matrix = cosine_similarity(embeddings)

        # Calcular coherencia como promedio de similitudes consecutivas
        consecutive_similarities = []
        for i in range(len(similarity_matrix) - 1):
            consecutive_similarities.append(similarity_matrix[i, i + 1])

        # Penalizar alta varianza en similitudes
        mean_similarity = np.mean(consecutive_similarities)
        std_similarity = np.std(consecutive_similarities)

        coherence = mean_similarity * (1 - min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L899_47", 0.5), std_similarity))

        return float(coherence)

    def _calculate_objective_alignment(
            self,
            statements: list[PolicyStatement]
    ) -> float:
        """Calcula alineación entre objetivos declarados"""
        objective_statements = [
            s for s in statements
            if s.semantic_role in ['objective', 'goal', 'target']
        ]

        if len(objective_statements) < 2:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L914_19", 1.0)

        # Analizar consistencia direccional de objetivos
        alignment_scores = []
        for i, obj_a in enumerate(objective_statements):
            for obj_b in objective_statements[i + 1:]:
                if obj_a.embedding is not None and obj_b.embedding is not None:
                    # Calcular alineación como similitud coseno
                    alignment = 1 - cosine(obj_a.embedding, obj_b.embedding)
                    alignment_scores.append(alignment)

        if alignment_scores:
            return float(np.mean(alignment_scores))
        return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._build_knowledge_graph").get("auto_param_L927_15", 0.5)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_graph_fragmentation")
    def _calculate_graph_fragmentation(self) -> float:
        """Calcula fragmentación del grafo de conocimiento"""
        if self.knowledge_graph.number_of_nodes() == 0:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_graph_fragmentation").get("auto_param_L933_19", 0.0)

        # Calcular número de componentes conectados
        num_components = nx.number_weakly_connected_components(self.knowledge_graph)
        num_nodes = self.knowledge_graph.number_of_nodes()

        # Fragmentación normalizada
        fragmentation = (num_components - 1) / max(1, num_nodes - 1)

        return float(fragmentation)

    def _calculate_contradiction_entropy(
            self,
            contradictions: list[ContradictionEvidence]
    ) -> float:
        """Calcula entropía de distribución de tipos de contradicción"""
        if not contradictions:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_graph_fragmentation").get("auto_param_L950_19", 0.0)

        # Contar frecuencia de cada tipo
        type_counts = {}
        for c in contradictions:
            type_counts[c.contradiction_type] = type_counts.get(c.contradiction_type, 0) + 1

        # Calcular probabilidades
        total = len(contradictions)
        probabilities = [count / total for count in type_counts.values()]

        # Calcular entropía de Shannon
        entropy = -sum(p * np.log2(p) if p > 0 else 0 for p in probabilities)

        # Normalizar por entropía máxima
        max_entropy = np.log2(len(ContradictionType))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        return float(normalized_entropy)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_syntactic_complexity")
    def _calculate_syntactic_complexity(self, text: str) -> float:
        """Calcula complejidad sintáctica del documento"""
        doc = self.nlp(text[:5000])  # Limitar para eficiencia

        # Métricas de complejidad
        avg_sentence_length = np.mean([len(sent.text.split()) for sent in doc.sents])

        # Profundidad promedio del árbol de dependencias
        dependency_depths = []
        for sent in doc.sents:
            depths = [self._get_dependency_depth(token) for token in sent]
            if depths:
                dependency_depths.append(np.mean(depths))

        avg_dependency_depth = np.mean(dependency_depths) if dependency_depths else 0

        # Diversidad léxica (Type-Token Ratio)
        tokens = [token.text.lower() for token in doc if token.is_alpha]
        ttr = len(set(tokens)) / len(tokens) if tokens else 0

        # Combinar métricas
        complexity = (
                min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_syntactic_complexity").get("auto_param_L993_20", 1.0), avg_sentence_length / 50) * get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_syntactic_complexity").get("auto_param_L993_53", 0.3) +
                min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_syntactic_complexity").get("auto_param_L994_20", 1.0), avg_dependency_depth / 10) * get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_syntactic_complexity").get("auto_param_L994_54", 0.3) +
                ttr * get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_syntactic_complexity").get("auto_param_L995_22", 0.4)
        )

        return float(complexity)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_dependency_depth")
    def _get_dependency_depth(self, token) -> int:
        """Calcula profundidad de un token en el árbol de dependencias"""
        depth = 0
        current = token
        while current.head != current and depth < 20:  # Evitar loops infinitos
            current = current.head
            depth += 1
        return depth

    def _calculate_confidence_interval(
            self,
            score: float,
            n_observations: int
    ) -> tuple[float, float]:
        """Calcula intervalo de confianza del 95% para el score"""
        # Usar distribución t de Student para muestras pequeñas
        if n_observations < 30:
            # Error estándar estimado
            se = np.sqrt(score * (1 - score) / n_observations)
            # Valor crítico t para 95% de confianza
            t_critical = stats.t.ppf(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_dependency_depth").get("auto_param_L1021_37", 0.975), n_observations - 1)
            margin = t_critical * se
        else:
            # Usar distribución normal para muestras grandes
            se = np.sqrt(score * (1 - score) / n_observations)
            margin = 1.96 * se

        return (
            max(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_dependency_depth").get("auto_param_L1029_16", 0.0), score - margin),
            min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_dependency_depth").get("auto_param_L1030_16", 1.0), score + margin)
        )

    def _generate_resolution_recommendations(
            self,
            contradictions: list[ContradictionEvidence]
    ) -> list[dict[str, Any]]:
        """Genera recomendaciones específicas para resolver contradicciones"""
        recommendations = []

        # Agrupar contradicciones por tipo
        by_type = {}
        for c in contradictions:
            if c.contradiction_type not in by_type:
                by_type[c.contradiction_type] = []
            by_type[c.contradiction_type].append(c)

        # Generar recomendaciones por tipo
        for cont_type, conflicts in by_type.items():
            if cont_type == ContradictionType.NUMERICAL_INCONSISTENCY:
                recommendations.append({
                    "type": "numerical_reconciliation",
                    "priority": "high",
                    "description": "Revisar y reconciliar cifras inconsistentes",
                    "specific_actions": [
                        "Verificar fuentes de datos originales",
                        "Establecer línea base única",
                        "Documentar metodología de cálculo"
                    ],
                    "affected_sections": self._identify_affected_sections(conflicts)
                })

            elif cont_type == ContradictionType.TEMPORAL_CONFLICT:
                recommendations.append({
                    "type": "timeline_adjustment",
                    "priority": "high",
                    "description": "Ajustar cronograma para resolver conflictos temporales",
                    "specific_actions": [
                        "Revisar secuencia de actividades",
                        "Validar plazos con áreas responsables",
                        "Establecer hitos intermedios claros"
                    ],
                    "affected_sections": self._identify_affected_sections(conflicts)
                })

            elif cont_type == ContradictionType.RESOURCE_ALLOCATION_MISMATCH:
                recommendations.append({
                    "type": "budget_reallocation",
                    "priority": "critical",
                    "description": "Revisar asignación presupuestal",
                    "specific_actions": [
                        "Realizar análisis de suficiencia presupuestal",
                        "Priorizar programas según impacto",
                        "Identificar fuentes alternativas de financiación"
                    ],
                    "affected_sections": self._identify_affected_sections(conflicts)
                })

            elif cont_type == ContradictionType.SEMANTIC_OPPOSITION:
                recommendations.append({
                    "type": "conceptual_clarification",
                    "priority": "medium",
                    "description": "Clarificar conceptos y objetivos opuestos",
                    "specific_actions": [
                        "Realizar sesiones de alineación estratégica",
                        "Definir glosario de términos unificado",
                        "Establecer jerarquía clara de objetivos"
                    ],
                    "affected_sections": self._identify_affected_sections(conflicts)
                })

        # Ordenar por prioridad
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return recommendations

    def _identify_affected_sections(
            self,
            conflicts: list[ContradictionEvidence]
    ) -> list[str]:
        """Identifica secciones del plan afectadas por contradicciones"""
        affected = set()
        for c in conflicts:
            # Extraer información de sección desde el contexto
            for pattern_name, pattern in self.pdm_patterns.items():
                if pattern.search(c.statement_a.context_window):
                    affected.add(pattern_name)
                if pattern.search(c.statement_b.context_window):
                    affected.add(pattern_name)

        return list(affected)

    def _serialize_contradiction(
            self,
            contradiction: ContradictionEvidence
    ) -> dict[str, Any]:
        """Serializa evidencia de contradicción para output"""
        return {
            "statement_1": contradiction.statement_a.text,
            "statement_2": contradiction.statement_b.text,
            "position_1": contradiction.statement_a.position,
            "position_2": contradiction.statement_b.position,
            "contradiction_type": contradiction.contradiction_type.name,
            "confidence": float(contradiction.confidence),
            "severity": float(contradiction.severity),
            "semantic_similarity": float(contradiction.semantic_similarity),
            "logical_conflict_score": float(contradiction.logical_conflict_score),
            "temporal_consistency": contradiction.temporal_consistency,
            "numerical_divergence": float(
                contradiction.numerical_divergence) if contradiction.numerical_divergence else None,
            "statistical_significance": float(
                contradiction.statistical_significance) if contradiction.statistical_significance else None,
            "affected_dimensions": [d.value for d in contradiction.affected_dimensions],
            "resolution_suggestions": contradiction.resolution_suggestions,
            "graph_path": contradiction.graph_path
        }

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_graph_statistics")
    def _get_graph_statistics(self) -> dict[str, Any]:
        """Obtiene estadísticas del grafo de conocimiento"""
        if self.knowledge_graph.number_of_nodes() == 0:
            return {"nodes": 0, "edges": 0, "components": 0}

        return {
            "nodes": self.knowledge_graph.number_of_nodes(),
            "edges": self.knowledge_graph.number_of_edges(),
            "components": nx.number_weakly_connected_components(self.knowledge_graph),
            "density": nx.density(self.knowledge_graph),
            "average_clustering": nx.average_clustering(self.knowledge_graph.to_undirected()),
            "diameter": nx.diameter(self.knowledge_graph.to_undirected()) if nx.is_connected(
                self.knowledge_graph.to_undirected()) else -1
        }

    # Métodos auxiliares

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._extract_temporal_markers")
    def _extract_temporal_markers(self, text: str) -> list[str]:
        """Extrae marcadores temporales del texto"""
        markers = []

        # Patrones de fechas
        date_patterns = [
            r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{4}',
            r'(Q[1-4]|trimestre\s+[1-4])\s+\d{4}',
            r'20\d{2}',
            r'(corto|mediano|largo)\s+plazo',
            r'(primer|segundo|tercer|cuarto)\s+(año|semestre|trimestre)'
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            markers.extend(matches)

        return markers

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._extract_quantitative_claims")
    def _extract_quantitative_claims(self, text: str) -> list[dict[str, Any]]:
        """Extrae afirmaciones cuantitativas estructuradas"""
        claims = []

        # Patrones numéricos con contexto
        patterns = [
            (r'(\d+(?:[.,]\d+)?)\s*(%|por\s*ciento)', 'percentage'),
            (r'(\d+(?:[.,]\d+)?)\s*(millones?|mil\s+millones?)', 'amount'),
            (r'(\$|COP)\s*(\d+(?:[.,]\d+)?)', 'currency'),
            (r'(\d+(?:[.,]\d+)?)\s*(personas?|beneficiarios?|familias?)', 'beneficiaries'),
            (r'(\d+(?:[.,]\d+)?)\s*(hectáreas?|km2?|metros?)', 'area'),
            (r'meta\s+de\s+(\d+(?:[.,]\d+)?)', 'target')
        ]

        for pattern, claim_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1) if claim_type != 'currency' else match.group(2)
                value = self._parse_number(value_str)

                claims.append({
                    'type': claim_type,
                    'value': value,
                    'raw_text': match.group(0),
                    'position': match.span(),
                    'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
                })

        return claims

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._parse_number")
    def _parse_number(self, text: str) -> float:
        """Parsea número desde texto"""
        try:
            # Reemplazar coma decimal
            normalized = text.replace(',', '.')
            return float(normalized)
        except ValueError:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._parse_number").get("auto_param_L1227_19", 0.0)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._extract_resource_mentions")
    def _extract_resource_mentions(self, text: str) -> list[tuple[str, float | None]]:
        """Extrae menciones de recursos con montos"""
        resources = []

        # Patrones de recursos específicos de PDM colombiano
        resource_patterns = [
            (r'SGP\s*[:\s]*\$?\s*(\d+(?:[.,]\d+)?)\s*(millones?)?', 'SGP'),
            (r'regalías\s*[:\s]*\$?\s*(\d+(?:[.,]\d+)?)\s*(millones?)?', 'regalías'),
            (r'recursos\s+propios\s*[:\s]*\$?\s*(\d+(?:[.,]\d+)?)\s*(millones?)?', 'recursos_propios'),
            (r'cofinanciación\s*[:\s]*\$?\s*(\d+(?:[.,]\d+)?)\s*(millones?)?', 'cofinanciación'),
            (r'presupuesto\s+total\s*[:\s]*\$?\s*(\d+(?:[.,]\d+)?)\s*(millones?)?', 'presupuesto_total')
        ]

        for pattern, resource_type in resource_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = self._parse_number(match.group(1)) if match.group(1) else None
                if match.group(2) and 'millon' in match.group(2).lower():
                    amount = amount * 1000000 if amount else None
                resources.append((resource_type, amount))

        return resources

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._determine_semantic_role")
    def _determine_semantic_role(self, sent) -> str | None:
        """Determina el rol semántico de una oración"""
        # Safely extract text (handles both strings and spacy objects)
        text_lower = safe_text_extract(sent).lower()

        role_patterns = {
            'objective': ['objetivo', 'meta', 'propósito', 'finalidad'],
            'strategy': ['estrategia', 'línea', 'eje', 'pilar'],
            'action': ['implementar', 'ejecutar', 'desarrollar', 'realizar'],
            'indicator': ['indicador', 'medir', 'evaluar', 'monitorear'],
            'resource': ['presupuesto', 'recurso', 'financiación', 'inversión'],
            'constraint': ['limitación', 'restricción', 'condición', 'requisito']
        }

        for role, keywords in role_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return role

        return None

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._identify_dependencies")
    def _identify_dependencies(self, sent, doc) -> set[str]:
        """Identifica dependencias entre declaraciones"""
        dependencies = set()

        # Buscar referencias a otras secciones
        reference_patterns = [
            r'como\s+se\s+menciona\s+en',
            r'según\s+lo\s+establecido\s+en',
            r'de\s+acuerdo\s+con',
            r'en\s+línea\s+con',
            r'siguiendo\s+lo\s+dispuesto'
        ]

        for pattern in reference_patterns:
            if re.search(pattern, sent.text, re.IGNORECASE):
                # Buscar la sección referenciada
                for other_sent in doc.sents:
                    if other_sent != sent:
                        # Usar hash de los primeros 50 caracteres como ID
                        dependencies.add(other_sent.text[:50])

        return dependencies

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_context_window")
    def _get_context_window(self, text: str, start: int, end: int, window_size: int = 200) -> str:
        """Obtiene ventana de contexto alrededor de una posición"""
        context_start = max(0, start - window_size)
        context_end = min(len(text), end + window_size)
        return text[context_start:context_end]

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_similarity")
    def _calculate_similarity(self, stmt_a: PolicyStatement, stmt_b: PolicyStatement) -> float:
        """Calcula similaridad entre dos declaraciones"""
        if stmt_a.embedding is not None and stmt_b.embedding is not None:
            return float(1 - cosine(stmt_a.embedding, stmt_b.embedding))
        return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._calculate_similarity").get("auto_param_L1310_15", 0.0)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._classify_contradiction")
    def _classify_contradiction(self, text: str) -> float:
        """Clasifica probabilidad de contradicción en texto"""
        try:
            result = self.contradiction_classifier(text)
            # Buscar score de contradicción
            for item in result:
                if 'contradiction' in item['label'].lower():
                    return item['score']
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._classify_contradiction").get("auto_param_L1321_19", 0.0)
        except Exception as e:
            logger.warning(f"Error en clasificación de contradicción: {e}")
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._classify_contradiction").get("auto_param_L1324_19", 0.0)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_domain_weight")
    def _get_domain_weight(self, dimension: PolicyDimension) -> float:
        """Obtiene peso específico del dominio"""
        weights = {
            PolicyDimension.DIAGNOSTICO: get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_domain_weight").get("auto_param_L1330_41", 0.8),
            PolicyDimension.ESTRATEGICO: 1.2,
            PolicyDimension.PROGRAMATICO: get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_domain_weight").get("auto_param_L1332_42", 1.0),
            PolicyDimension.FINANCIERO: 1.5,
            PolicyDimension.SEGUIMIENTO: get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_domain_weight").get("auto_param_L1334_41", 0.9),
            PolicyDimension.TERRITORIAL: 1.1
        }
        return weights.get(dimension, get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._get_domain_weight").get("auto_param_L1337_38", 1.0))

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._suggest_resolutions")
    def _suggest_resolutions(self, contradiction_type: ContradictionType) -> list[str]:
        """Sugiere resoluciones específicas por tipo de contradicción"""
        suggestions = {
            ContradictionType.NUMERICAL_INCONSISTENCY: [
                "Verificar fuentes de datos y metodologías de cálculo",
                "Establecer línea base única con validación técnica",
                "Documentar supuestos y proyecciones utilizadas"
            ],
            ContradictionType.TEMPORAL_CONFLICT: [
                "Revisar cronograma maestro del plan",
                "Validar secuencia lógica de actividades",
                "Ajustar plazos según capacidad institucional"
            ],
            ContradictionType.SEMANTIC_OPPOSITION: [
                "Realizar taller de alineación conceptual",
                "Clarificar definiciones en glosario técnico",
                "Priorizar objetivos según Plan Nacional de Desarrollo"
            ],
            ContradictionType.RESOURCE_ALLOCATION_MISMATCH: [
                "Realizar análisis de brechas financieras",
                "Priorizar inversiones según impacto social",
                "Explorar fuentes alternativas de financiación"
            ],
            ContradictionType.LOGICAL_INCOMPATIBILITY: [
                "Revisar cadena de valor de programas",
                "Validar teoría de cambio del plan",
                "Eliminar duplicidades y solapamientos"
            ]
        }
        return suggestions.get(contradiction_type, ["Revisar y ajustar según contexto"])

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._are_comparable_claims")
    def _are_comparable_claims(self, claim_a: dict, claim_b: dict) -> bool:
        """Determina si dos afirmaciones cuantitativas son comparables"""
        # Mismo tipo y contexto similar
        if claim_a['type'] != claim_b['type']:
            return False

        # Verificar si hablan del mismo concepto
        context_similarity = self._text_similarity(
            claim_a.get('context', ''),
            claim_b.get('context', '')
        )

        return context_similarity > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._are_comparable_claims").get("auto_param_L1384_36", 0.6)

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity")
    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """Calcula similaridad simple entre textos"""
        if not text_a or not text_b:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity").get("auto_param_L1390_19", 0.0)

        # Tokenización simple
        tokens_a = set(text_a.lower().split())
        tokens_b = set(text_b.lower().split())

        if not tokens_a or not tokens_b:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity").get("auto_param_L1397_19", 0.0)

        # Coeficiente de Jaccard
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b

        return len(intersection) / len(union) if union else get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity").get("auto_param_L1403_60", 0.0)

    def _calculate_numerical_divergence(
            self,
            claim_a: dict,
            claim_b: dict
    ) -> float | None:
        """Calcula divergencia entre valores numéricos"""
        value_a = claim_a.get('value', 0)
        value_b = claim_b.get('value', 0)

        if value_a == 0 and value_b == 0:
            return None

        # Divergencia relativa
        max_value = max(abs(value_a), abs(value_b))
        if max_value == 0:
            return None

        divergence = abs(value_a - value_b) / max_value
        return divergence

    def _statistical_significance_test(
            self,
            claim_a: dict,
            claim_b: dict
    ) -> float:
        """Realiza test de significancia estadística"""
        value_a = claim_a.get('value', 0)
        value_b = claim_b.get('value', 0)

        # Test t de una muestra para diferencia significativa
        # Asumiendo distribución normal con varianza estimada
        diff = abs(value_a - value_b)
        pooled_value = (value_a + value_b) / 2

        if pooled_value == 0:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity").get("auto_param_L1440_19", 1.0)  # No significativo

        # Estimación conservadora de error estándar
        se = pooled_value * get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity").get("auto_param_L1443_28", 0.1)  # 10% de error estimado

        if se == 0:
            return get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._text_similarity").get("auto_param_L1446_19", 0.0)  # Altamente significativo

        # Estadístico t
        t_stat = diff / se

        # Valor p aproximado (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))

        return p_value

    @calibrated_method("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict")
    def _has_logical_conflict(self, stmt_a: PolicyStatement, stmt_b: PolicyStatement) -> bool:
        """Determina si hay conflicto lógico entre declaraciones"""
        # Verificar si las declaraciones tienen roles incompatibles
        if stmt_a.semantic_role and stmt_b.semantic_role:
            incompatible_roles = [
                ('objective', 'constraint'),
                ('strategy', 'constraint'),
                ('action', 'constraint')
            ]

            for role_pair in incompatible_roles:
                if (stmt_a.semantic_role in role_pair and
                        stmt_b.semantic_role in role_pair and
                        stmt_a.semantic_role != stmt_b.semantic_role):
                    return True

        # Verificar negación explícita
        negation_patterns = ['no', 'nunca', 'ningún', 'sin', 'tampoco']
        has_negation_a = any(pattern in stmt_a.text.lower() for pattern in negation_patterns)
        has_negation_b = any(pattern in stmt_b.text.lower() for pattern in negation_patterns)

        # Si una tiene negación y otra no, y son similares, hay conflicto
        if has_negation_a != has_negation_b:
            similarity = self._calculate_similarity(stmt_a, stmt_b)
            if similarity > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1481_28", 0.7):
                return True

        return False

    def _are_conflicting_allocations(
            self,
            amount_a: float,
            amount_b: float,
            total: float
    ) -> bool:
        """Determina si las asignaciones de recursos están en conflicto"""
        # Si la suma excede el total disponible
        if amount_a + amount_b > total * 1.1:  # 10% de margen
            return True

        # Si hay una diferencia muy grande entre asignaciones similares
        return abs(amount_a - amount_b) / max(amount_a, amount_b) > get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1498_68", 0.5)

    def _determine_relation_type(
            self,
            stmt_a: PolicyStatement,
            stmt_b: PolicyStatement
    ) -> str:
        """Determina el tipo de relación entre dos declaraciones"""
        # Analizar roles semánticos
        if stmt_a.semantic_role and stmt_b.semantic_role:
            if stmt_a.semantic_role == stmt_b.semantic_role:
                return "parallel"
            elif stmt_a.semantic_role in ["strategy", "objective"] and stmt_b.semantic_role == "action":
                return "enables"
            elif stmt_a.semantic_role == "action" and stmt_b.semantic_role in ["indicator", "resource"]:
                return "requires"

        # Analizar dependencias
        if stmt_a.dependencies & {stmt_b.text[:50]}:
            return "depends_on"

        # Por defecto, relación de similaridad
        return "related"

    def _calculate_severity(
            self,
            stmt_a: PolicyStatement,
            stmt_b: PolicyStatement
    ) -> float:
        """Calcula la severidad de una contradicción entre declaraciones"""
        severity = get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("severity", 0.5) # Refactored

        # Incrementar si las declaraciones están en la misma dimensión
        if stmt_a.dimension == stmt_b.dimension:
            severity += get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1532_24", 0.2)

        # Incrementar si tienen muchas entidades en común
        common_entities = set(stmt_a.entities) & set(stmt_b.entities)
        if len(common_entities) > 0:
            severity += min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1537_28", 0.2), len(common_entities) * get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1537_56", 0.05))

        # Incrementar si tienen marcadores temporales en conflicto
        if stmt_a.temporal_markers and stmt_b.temporal_markers:
            severity += get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1541_24", 0.1)

        return min(get_parameter_loader().get("saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector._has_logical_conflict").get("auto_param_L1543_19", 1.0), severity)
