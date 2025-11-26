# Questionnaire Signal Irrigation Design
## Diseño de Irrigación Estratégica y Transversal de Signals

**Versión:** 1.0.0
**Fecha:** 2025-11-24
**Estado:** Documento de Diseño

---

## 1. INVENTARIO DE CATEGORÍAS Y CLASES DE DATOS

### 1.1 Estructura Top-Level del Questionnaire Monolith

```
questionnaire_monolith.json
├── version: "1.0.0"
├── schema_version: "1.0.0"
├── generated_at: ISO timestamp
├── canonical_notation
│   ├── dimensions (D1-D6)
│   └── policy_areas (PA01-PA10)
├── integrity
│   ├── monolith_hash
│   ├── ruleset_hash
│   └── question_count {micro: 300, meso: 4, macro: 1, total: 305}
├── observability
│   └── telemetry_schema {logs, metrics, tracing}
└── blocks
    ├── macro_question (1)
    ├── meso_questions (4)
    ├── micro_questions (300)
    ├── niveles_abstraccion
    ├── scoring
    └── semantic_layers
```

### 1.2 Categorías de Datos por Bloque

#### A. MICRO QUESTIONS (300 preguntas)
Cada pregunta contiene:

| Campo | Tipo | Uso Principal |
|-------|------|---------------|
| `question_id` | Q001-Q300 | Identificación única |
| `question_global` | 1-300 | Orden global |
| `base_slot` | D1-Q1 a D6-Q5 | Matriz dimensión/pregunta |
| `policy_area_id` | PA01-PA10 | Área de política pública |
| `cluster_id` | CL01-CL04 | Agrupación temática |
| `dimension_id` | DIM01-DIM06 | Dimensión del marco lógico |
| `text` | string | Texto de la pregunta |
| `scoring_modality` | TYPE_A-F | Tipo de evaluación |
| `scoring_definition_ref` | reference | Referencia a definición |
| `patterns` | array | **PATRONES DE EXTRACCIÓN** |
| `expected_elements` | array | **ELEMENTOS ESPERADOS** |
| `method_sets` | array | Métodos de análisis |
| `failure_contract` | object | Contrato de fallo |
| `validations` | object | **VALIDACIONES** |

#### B. PATTERNS (2,207 patrones totales)
Categorías disponibles:

| Categoría | Descripción | Uso en Signals |
|-----------|-------------|----------------|
| `GENERAL` | Patrones generales | Extracción semántica |
| `TEMPORAL` | Años, períodos, series | Validación temporal |
| `INDICADOR` | Indicadores cuantitativos | Scoring y métricas |
| `FUENTE_OFICIAL` | Fuentes oficiales | Validación de fuentes |
| `TERRITORIAL` | Cobertura territorial | Geolocalización |
| `UNIDAD_MEDIDA` | Unidades de medición | Normalización |

Estructura de cada patrón:
```json
{
  "id": "PAT-Q001-001",
  "pattern": "regex o literal",
  "match_type": "REGEX|LITERAL",
  "confidence_weight": 0.85,
  "category": "INDICADOR|TEMPORAL|...",
  "flags": "i|m|s|x"
}
```

#### C. EXPECTED ELEMENTS (98 tipos únicos)
Ejemplos de tipos:
- `cobertura_territorial_especificada`
- `fuentes_oficiales`
- `indicadores_cuantitativos`
- `series_temporales_años`
- `cadena_causal_explicita`
- `alineacion_ods`
- `presupuesto_asignado`

#### D. VALIDATIONS (6 tipos)
| Tipo de Validación | Descripción |
|-------------------|-------------|
| `buscar_indicadores_cuantitativos` | Busca indicadores numéricos |
| `cobertura` | Valida cobertura territorial |
| `series_temporales` | Valida datos temporales |
| `unidades_medicion` | Valida unidades |
| `verificar_fuentes` | Verifica fuentes oficiales |
| `monitoring_keywords` | Palabras clave de monitoreo |

#### E. NIVELES DE ABSTRACCIÓN

**Clusters (4):**
| Cluster | Nombre | Policy Areas |
|---------|--------|--------------|
| CL01 | Seguridad y Paz | PA02, PA03, PA07 |
| CL02 | Grupos Poblacionales | PA01, PA05, PA06 |
| CL03 | Territorio-Ambiente | PA04, PA08 |
| CL04 | Derechos Sociales & Crisis | PA09, PA10 |

**Dimensions (6):**
| Dimension | Nombre | Descripción |
|-----------|--------|-------------|
| DIM01 | Insumos | Diagnóstico y Líneas Base |
| DIM02 | Actividades | Diseño de Intervención |
| DIM03 | Productos | Productos Verificables |
| DIM04 | Resultados | Resultados Medibles |
| DIM05 | Impactos | Impactos de Largo Plazo |
| DIM06 | Causalidad | Teoría de Cambio |

**Policy Areas (10):**
Cada una con `required_evidence_keys`:
- `official_stats`
- `official_documents`
- `third_party_research`
- `monitoring_tables`
- `geo_maps`

#### F. SCORING

**Micro Levels (4):**
| Nivel | Min Score | Color |
|-------|-----------|-------|
| EXCELENTE | 0.85 | green |
| BUENO | 0.70 | blue |
| ACEPTABLE | 0.55 | yellow |
| INSUFICIENTE | 0.0 | red |

**Modalities (6):**
| Type | Aggregation | Descripción |
|------|-------------|-------------|
| TYPE_A | presence_threshold | Cuenta 4 elementos, threshold 0.7 |
| TYPE_B | binary_sum | Cuenta hasta 3 elementos |
| TYPE_C | presence_threshold | Cuenta 2 elementos, threshold 0.5 |
| TYPE_D | weighted_sum | 3 elementos con pesos [0.4, 0.3, 0.3] |
| TYPE_E | binary_presence | Presencia binaria |
| TYPE_F | normalized_continuous | Matching semántico |

#### G. SEMANTIC LAYERS

```json
{
  "embedding_strategy": {
    "model": "multilingual-e5-base",
    "dimension": 768,
    "hybrid": {"bm25": true, "fusion": "RRF"}
  },
  "disambiguation": {
    "entity_linker": "spaCy_es_core_news_lg",
    "confidence_threshold": 0.72
  }
}
```

---

## 2. ARQUITECTURA DE CONCENTRACIÓN DE ACCESO

### 2.1 Principio de Concentración Tripartita

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QUESTIONNAIRE_MONOLITH.JSON                       │
│                     (Single Source of Truth)                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FACTORY                                      │
│  (questionnaire.py + factory.py)                                    │
│  ─────────────────────────────────────────────────────────────────  │
│  RESPONSABILIDAD:                                                    │
│  • Carga única del questionnaire (CanonicalQuestionnaire)           │
│  • Verificación de integridad (SHA-256)                             │
│  • Construcción de contracts de entrada                              │
│  • Inyección de dependencias a componentes                          │
│                                                                      │
│  DATOS EXPUESTOS:                                                    │
│  • Preguntas completas (micro, meso, macro)                         │
│  • Dimensiones y notación canónica                                  │
│  • Policy areas con evidence keys                                    │
│  • Version y metadata de integridad                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│     ORCHESTRATOR     │  │     SIGNALS      │  │    COMPONENTS        │
│   (Acceso Micro/     │  │  (Acceso a       │  │   (Consumidores)     │
│    Meso/Macro)       │  │   Patrones)      │  │                      │
└──────────────────────┘  └──────────────────┘  └──────────────────────┘
```

### 2.2 Responsabilidades por Capa

#### FACTORY (`questionnaire.py` + `factory.py`)
```python
# Único punto de carga
def load_questionnaire() -> CanonicalQuestionnaire:
    """Carga única con verificación de integridad."""

# Exposición de datos estructurales
def get_canonical_dimensions() -> dict[str, dict]
def get_canonical_policy_areas() -> dict[str, dict]

# Construcción de bundles
def build_processor() -> ProcessorBundle
```

**Datos que maneja:**
- `data` completo (inmutable)
- `micro_questions`, `meso_questions`, `macro_question`
- `version`, `schema_version`
- Hash SHA-256 para integridad

#### ORCHESTRATOR (Acceso a Preguntas)
```python
# Acceso a preguntas por nivel
def get_micro_question(question_id: str) -> MappingProxyType
def get_meso_question(cluster_id: str) -> MappingProxyType
def get_macro_question() -> MappingProxyType

# Acceso a metadata estructural
def get_dimension_info(dimension_id: str) -> dict
def get_policy_area_info(policy_area_id: str) -> dict
def get_cluster_info(cluster_id: str) -> dict
```

**Datos que maneja:**
- Preguntas individuales
- Dimensiones (DIM01-DIM06)
- Policy areas (PA01-PA10)
- Clusters (CL01-CL04)
- Relaciones jerárquicas

#### SIGNALS (Acceso a Patrones y Scoring)
```python
# SignalPack para cada policy area
class SignalPack:
    patterns: list[str]      # Patrones regex
    indicators: list[str]    # Indicadores
    regex: list[str]         # Expresiones regex
    entities: list[str]      # Entidades
    thresholds: dict         # Umbrales de scoring

# Funciones de extracción
def build_signal_pack_from_monolith(policy_area: str) -> SignalPack
def build_all_signal_packs() -> dict[str, SignalPack]
```

**Datos que maneja:**
- Patrones por categoría (TEMPORAL, INDICADOR, etc.)
- Thresholds de scoring (confidence_weight)
- Merkle roots para verificación
- Metadata de consumo

---

## 3. DISEÑO DE IRRIGACIÓN POR COMPONENTE

### 3.1 Irrigación hacia Smart Policy Chunking

**Componente:** `semantic_chunking_policy.py`

**Estado Actual:**
- Usa constants hardcodeados para weights
- No accede a patrones del questionnaire

**Señales Requeridas:**

| Signal | Origen | Uso |
|--------|--------|-----|
| `dimension_patterns` | patterns[GENERAL] | Detectar secciones PDM |
| `temporal_patterns` | patterns[TEMPORAL] | Identificar referencias temporales |
| `territorial_patterns` | patterns[TERRITORIAL] | Segmentar por territorio |
| `section_weights` | scoring.modalities | Ponderar chunks por sección |

**Diseño de SignalPack para Chunking:**

```python
@dataclass
class ChunkingSignalPack:
    """Signals para Smart Policy Chunking."""

    # Patrones de sección (derivados de PDMSection)
    section_detection_patterns: dict[str, list[str]]

    # Pesos calibrados por tipo de sección
    section_weights: dict[str, float]  # {DIAGNOSTICO: 0.92, PLAN_INVERSIONES: 1.25}

    # Patrones para preservar integridad
    table_patterns: list[str]
    numerical_patterns: list[str]

    # Configuración semántica
    embedding_config: dict  # semantic_layers.embedding_strategy
```

**Punto de Irrigación:**

```python
# En SemanticProcessor.__init__
def __init__(self, config: SemanticConfig, signal_pack: ChunkingSignalPack = None):
    self.signals = signal_pack or self._load_default_signals()

def _detect_pdm_structure(self, text: str) -> list[dict]:
    """Usa signals para detectar estructura."""
    for section_type, patterns in self.signals.section_detection_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Aplicar peso de signal
                weight = self.signals.section_weights.get(section_type, 1.0)
```

### 3.2 Irrigación hacia Micro Answering

**Componente:** Ejecutores por dimensión

**Señales Requeridas:**

| Signal | Origen | Uso |
|--------|--------|-----|
| `question_patterns` | micro_questions.patterns | Búsqueda de evidencia |
| `expected_elements` | micro_questions.expected_elements | Validación de completitud |
| `indicators` | patterns[INDICADOR] | Extracción de indicadores |
| `official_sources` | patterns[FUENTE_OFICIAL] | Validación de fuentes |

**Diseño de SignalPack para Micro Answering:**

```python
@dataclass
class MicroAnsweringSignalPack:
    """Signals para Micro Answering."""

    # Patrones específicos por pregunta
    question_patterns: dict[str, list[PatternItem]]  # {Q001: [...]}

    # Elementos esperados con metadata
    expected_elements: dict[str, list[ExpectedElement]]

    # Indicadores por policy area
    indicators_by_pa: dict[str, list[str]]

    # Fuentes oficiales reconocidas
    official_sources: list[str]

    # Confidence weights para cada patrón
    pattern_weights: dict[str, float]
```

**Punto de Irrigación:**

```python
# En MethodExecutor.execute_for_question
def execute_for_question(
    self,
    question_id: str,
    text: str,
    signals: MicroAnsweringSignalPack
) -> ExecutionResult:
    """Ejecuta con signals inyectados."""

    # Obtener patrones específicos para esta pregunta
    patterns = signals.question_patterns.get(question_id, [])

    # Buscar cada patrón con su peso de confianza
    for pattern in patterns:
        matches = self._find_matches(text, pattern.pattern)
        confidence = pattern.confidence_weight
```

### 3.3 Irrigación hacia Validación de Respuesta

**Componente:** `validation_engine.py`

**Señales Requeridas:**

| Signal | Origen | Uso |
|--------|--------|-----|
| `validations` | micro_questions.validations | Reglas de validación |
| `failure_contracts` | micro_questions.failure_contract | Condiciones de aborto |
| `thresholds` | scoring.modality_definitions | Umbrales mínimos |

**Diseño de SignalPack para Validación:**

```python
@dataclass
class ValidationSignalPack:
    """Signals para Validación de Respuesta."""

    # Validaciones por pregunta
    validation_rules: dict[str, dict[str, ValidationCheck]]

    # Contratos de fallo
    failure_contracts: dict[str, FailureContract]

    # Umbrales de scoring por modality
    modality_thresholds: dict[str, float]

    # Códigos de aborto
    abort_codes: dict[str, str]  # {Q001: "ABORT-Q001-REQ"}

    # Patrones de verificación
    verification_patterns: dict[str, list[str]]
```

**Punto de Irrigación:**

```python
# En ValidationEngine.validate_scoring_preconditions
def validate_scoring_preconditions(
    self,
    question_spec: dict,
    execution_results: dict,
    signals: ValidationSignalPack
) -> ValidationResult:
    """Valida con signals inyectados."""

    question_id = question_spec.get('question_id')

    # Obtener reglas de validación
    rules = signals.validation_rules.get(question_id, {})

    # Verificar cada regla
    for rule_name, rule in rules.items():
        patterns = rule.get('patterns', [])
        minimum = rule.get('minimum_required', 1)
        # Aplicar validación
```

### 3.4 Irrigación hacia Ensamblaje de Respuesta

**Componente:** Aggregation / Response Assembly

**Señales Requeridas:**

| Signal | Origen | Uso |
|--------|--------|-----|
| `aggregation_methods` | meso/macro.aggregation_method | Método de agregación |
| `cluster_composition` | niveles_abstraccion.clusters | Composición de clusters |
| `evidence_keys` | policy_areas.required_evidence_keys | Keys de evidencia |
| `cross_reference_patterns` | meso_questions.patterns | Patrones de referencia cruzada |

**Diseño de SignalPack para Ensamblaje:**

```python
@dataclass
class AssemblySignalPack:
    """Signals para Ensamblaje de Respuesta."""

    # Métodos de agregación por nivel
    aggregation_methods: dict[str, str]  # {MESO_1: "weighted_average"}

    # Composición de clusters
    cluster_policy_areas: dict[str, list[str]]  # {CL01: [PA02, PA03, PA07]}

    # Pesos por dimensión
    dimension_weights: dict[str, float]

    # Keys de evidencia requeridas
    evidence_keys_by_pa: dict[str, list[str]]

    # Patrones de coherencia
    coherence_patterns: list[dict]

    # Fallbacks por nivel
    fallback_patterns: dict[str, dict]
```

**Punto de Irrigación:**

```python
# En ResponseAssembler.assemble_meso_response
def assemble_meso_response(
    self,
    cluster_id: str,
    micro_results: list[MicroResult],
    signals: AssemblySignalPack
) -> MesoResponse:
    """Ensambla respuesta meso con signals."""

    # Obtener método de agregación
    agg_method = signals.aggregation_methods.get(cluster_id, "weighted_average")

    # Obtener policy areas del cluster
    policy_areas = signals.cluster_policy_areas.get(cluster_id, [])

    # Aplicar agregación según señal
    if agg_method == "weighted_average":
        return self._weighted_average(micro_results, signals.dimension_weights)
```

### 3.5 Irrigación hacia Scoring

**Componente:** `scoring.py`

**Señales Requeridas:**

| Signal | Origen | Uso |
|--------|--------|-----|
| `scoring_modality` | micro_questions.scoring_modality | Tipo de scoring |
| `modality_config` | scoring.modality_definitions | Configuración detallada |
| `quality_levels` | scoring.micro_levels | Niveles de calidad |
| `failure_codes` | modality_definitions.failure_code | Códigos de fallo |

**Diseño de SignalPack para Scoring:**

```python
@dataclass
class ScoringSignalPack:
    """Signals para Scoring."""

    # Modalidad por pregunta
    question_modalities: dict[str, str]  # {Q001: "TYPE_A"}

    # Configuración de modalidades
    modality_configs: dict[str, ModalityConfig]

    # Niveles de calidad
    quality_levels: list[QualityLevel]

    # Códigos de fallo
    failure_codes: dict[str, str]

    # Thresholds
    thresholds: dict[str, float]  # {TYPE_A: 0.7, TYPE_C: 0.5}

    # Weights para TYPE_D
    type_d_weights: list[float]  # [0.4, 0.3, 0.3]

@dataclass
class ModalityConfig:
    """Configuración de modalidad desde monolith."""
    aggregation: str
    description: str
    failure_code: str
    threshold: float | None
    max_score: int
    weights: list[float] | None
```

**Punto de Irrigación:**

```python
# En MicroQuestionScorer.apply_scoring_modality
def apply_scoring_modality(
    self,
    question_id: str,
    elements_found: list[str],
    signals: ScoringSignalPack
) -> ScoredResult:
    """Aplica scoring con signals inyectados."""

    # Obtener modalidad desde signal
    modality = signals.question_modalities.get(question_id, "TYPE_A")

    # Obtener configuración
    config = signals.modality_configs.get(modality)

    # Aplicar según tipo
    if modality == "TYPE_A":
        threshold = config.threshold or signals.thresholds.get("TYPE_A", 0.7)
        return self._score_type_a(elements_found, threshold, config.max_score)
    elif modality == "TYPE_D":
        weights = config.weights or signals.type_d_weights
        return self._score_type_d(elements_found, weights, config.max_score)
```

---

## 4. IMPLEMENTACIÓN DE SIGNAL REGISTRY

### 4.1 Registro Centralizado

```python
class QuestionnaireSignalRegistry:
    """Registro centralizado de signals desde questionnaire."""

    def __init__(self, questionnaire: CanonicalQuestionnaire):
        self._questionnaire = questionnaire
        self._signal_packs: dict[str, SignalPack] = {}
        self._manifests: dict[str, SignalManifest] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Inicializa todos los signal packs."""
        if self._initialized:
            return

        # Build signal packs por policy area
        for pa in [f"PA{i:02d}" for i in range(1, 11)]:
            self._signal_packs[pa] = self._build_signal_pack(pa)

        # Generate manifests con Merkle roots
        self._manifests = generate_signal_manifests(
            dict(self._questionnaire.data)
        )

        self._initialized = True

    def get_chunking_signals(self) -> ChunkingSignalPack:
        """Obtiene signals para chunking."""
        return ChunkingSignalPack(
            section_detection_patterns=self._extract_section_patterns(),
            section_weights=self._extract_section_weights(),
            table_patterns=self._extract_table_patterns(),
            numerical_patterns=self._extract_numerical_patterns(),
            embedding_config=self._get_embedding_config(),
        )

    def get_micro_answering_signals(self, question_id: str) -> MicroAnsweringSignalPack:
        """Obtiene signals para micro answering."""
        question = self._get_question(question_id)
        pa = question.get('policy_area_id', 'PA01')

        return MicroAnsweringSignalPack(
            question_patterns={question_id: question.get('patterns', [])},
            expected_elements={question_id: question.get('expected_elements', [])},
            indicators_by_pa={pa: self._signal_packs[pa].indicators},
            official_sources=self._extract_official_sources(pa),
            pattern_weights=self._extract_pattern_weights(question),
        )

    def get_validation_signals(self, question_id: str) -> ValidationSignalPack:
        """Obtiene signals para validación."""
        question = self._get_question(question_id)

        return ValidationSignalPack(
            validation_rules={question_id: question.get('validations', {})},
            failure_contracts={question_id: question.get('failure_contract', {})},
            modality_thresholds=self._get_modality_thresholds(),
            abort_codes={question_id: question.get('failure_contract', {}).get('emit_code')},
            verification_patterns=self._extract_verification_patterns(question),
        )

    def get_assembly_signals(self, level: str) -> AssemblySignalPack:
        """Obtiene signals para ensamblaje."""
        blocks = self._questionnaire.data.get('blocks', {})
        niveles = blocks.get('niveles_abstraccion', {})

        return AssemblySignalPack(
            aggregation_methods=self._extract_aggregation_methods(),
            cluster_policy_areas=self._extract_cluster_composition(niveles),
            dimension_weights=self._extract_dimension_weights(),
            evidence_keys_by_pa=self._extract_evidence_keys(niveles),
            coherence_patterns=self._extract_coherence_patterns(),
            fallback_patterns=self._extract_fallback_patterns(),
        )

    def get_scoring_signals(self, question_id: str) -> ScoringSignalPack:
        """Obtiene signals para scoring."""
        question = self._get_question(question_id)
        blocks = self._questionnaire.data.get('blocks', {})
        scoring = blocks.get('scoring', {})

        return ScoringSignalPack(
            question_modalities={question_id: question.get('scoring_modality')},
            modality_configs=self._extract_modality_configs(scoring),
            quality_levels=self._extract_quality_levels(scoring),
            failure_codes=self._extract_failure_codes(scoring),
            thresholds=self._extract_thresholds(scoring),
            type_d_weights=scoring.get('modality_definitions', {})
                                    .get('TYPE_D', {})
                                    .get('weights', [0.4, 0.3, 0.3]),
        )
```

### 4.2 Integración con Factory

```python
# En factory.py

def build_processor(
    *,
    enable_signals: bool = True,
    executor_config: ExecutorConfig | None = None,
) -> ProcessorBundle:
    """Construye processor con signal registry integrado."""

    canonical_q = load_questionnaire()

    # Inicializar signal registry
    signal_registry = None
    if enable_signals:
        signal_registry = QuestionnaireSignalRegistry(canonical_q)
        signal_registry.initialize()

    executor = MethodExecutor(signal_registry=signal_registry)

    return ProcessorBundle(
        method_executor=executor,
        questionnaire=canonical_q,
        signal_registry=signal_registry,
        executor_config=executor_config or ExecutorConfig(),
    )
```

---

## 5. FLUJO DE IRRIGACIÓN COMPLETO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE EXECUTION FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ┌──────────────┐
   │   FACTORY    │──► load_questionnaire() → CanonicalQuestionnaire
   └──────────────┘
          │
          ▼
   ┌──────────────────────────┐
   │ QuestionnaireSignalRegistry │──► initialize() → Signal Packs
   └──────────────────────────┘

2. SMART POLICY CHUNKING
   ┌──────────────┐     ┌─────────────────────┐
   │  Document    │────►│  SemanticProcessor   │
   └──────────────┘     │  + ChunkingSignalPack │
                        └─────────────────────┘
                                │
                        signals.section_detection_patterns
                        signals.section_weights
                                │
                                ▼
                        ┌───────────────┐
                        │ Smart Chunks  │
                        └───────────────┘

3. MICRO ANSWERING (per question Q001-Q300)
   ┌───────────────┐    ┌─────────────────────────┐
   │ Smart Chunks  │───►│    MethodExecutor        │
   │ + Question ID │    │  + MicroAnsweringSignalPack │
   └───────────────┘    └─────────────────────────┘
                                │
                        signals.question_patterns[Qxxx]
                        signals.expected_elements[Qxxx]
                        signals.indicators_by_pa[PAxx]
                                │
                                ▼
                        ┌───────────────┐
                        │ Evidence Found│
                        └───────────────┘

4. VALIDATION
   ┌───────────────┐    ┌─────────────────────────┐
   │ Evidence Found│───►│   ValidationEngine       │
   │ + Question ID │    │  + ValidationSignalPack   │
   └───────────────┘    └─────────────────────────┘
                                │
                        signals.validation_rules[Qxxx]
                        signals.failure_contracts[Qxxx]
                                │
                                ▼
                        ┌───────────────────┐
                        │ Validated Evidence│
                        └───────────────────┘

5. SCORING
   ┌───────────────────┐  ┌─────────────────────────┐
   │ Validated Evidence│─►│   MicroQuestionScorer   │
   │ + Question ID     │  │  + ScoringSignalPack     │
   └───────────────────┘  └─────────────────────────┘
                                │
                        signals.question_modalities[Qxxx]
                        signals.modality_configs[TYPE_x]
                        signals.thresholds[TYPE_x]
                                │
                                ▼
                        ┌───────────────┐
                        │ Micro Score   │
                        │ + Quality Level│
                        └───────────────┘

6. ASSEMBLY (Meso/Macro)
   ┌───────────────┐    ┌─────────────────────────┐
   │ Micro Scores  │───►│   ResponseAssembler      │
   │ + Cluster ID  │    │  + AssemblySignalPack    │
   └───────────────┘    └─────────────────────────┘
                                │
                        signals.aggregation_methods[cluster]
                        signals.cluster_policy_areas[cluster]
                        signals.evidence_keys_by_pa[PAxx]
                                │
                                ▼
                        ┌───────────────────┐
                        │ Meso/Macro Response│
                        └───────────────────┘
```

---

## 6. TRAZABILIDAD Y OBSERVABILIDAD

### 6.1 Consumption Proofs

```python
# Cada uso de signal genera prueba criptográfica
proof = SignalConsumptionProof(
    executor_id="Q001_executor",
    question_id="Q001",
    policy_area="PA01",
)

# Al usar un patrón
for pattern in signals.question_patterns["Q001"]:
    if match := re.search(pattern, text):
        proof.record_pattern_match(pattern, match.group())

# Exportar prueba
proof_data = proof.get_consumption_proof()
# {
#   "executor_id": "Q001_executor",
#   "patterns_consumed": 5,
#   "proof_chain_head": "abc123...",
#   "timestamp": 1732403200.0
# }
```

### 6.2 Métricas de Irrigación

```python
# Métricas disponibles en signal_quality_metrics.py
metrics = {
    "signal_hit_rate": 0.95,      # % de signals usados
    "pattern_match_rate": 0.82,   # % de patrones que matchearon
    "cache_efficiency": 0.98,     # % de hits en cache
    "staleness_avg_s": 120.0,     # Tiempo promedio en cache
    "consumption_count": {
        "chunking": 1,
        "micro_answering": 300,
        "validation": 300,
        "scoring": 300,
        "assembly": 5
    }
}
```

---

## 7. PRÓXIMOS PASOS

1. **Implementar `QuestionnaireSignalRegistry`** en `signal_registry.py`
2. **Crear signal pack builders** específicos por componente
3. **Refactorizar componentes** para aceptar signal packs inyectados
4. **Agregar consumption tracking** en cada punto de irrigación
5. **Implementar métricas** de cobertura de signals
6. **Crear tests** de integración para verificar irrigación completa

---

## APÉNDICE A: Mapeo de Datos Questionnaire → Signals

| Sección Questionnaire | SignalPack Target | Campos Usados |
|----------------------|-------------------|---------------|
| `micro_questions.patterns` | Todos | pattern, category, confidence_weight |
| `micro_questions.expected_elements` | MicroAnswering, Validation | type, required, minimum |
| `micro_questions.validations` | Validation | patterns, minimum_required, specificity |
| `micro_questions.failure_contract` | Validation | abort_if, emit_code |
| `micro_questions.scoring_modality` | Scoring | TYPE_A-F |
| `scoring.micro_levels` | Scoring | level, min_score, color |
| `scoring.modality_definitions` | Scoring | aggregation, threshold, weights |
| `niveles_abstraccion.clusters` | Assembly | cluster_id, policy_area_ids |
| `niveles_abstraccion.dimensions` | All | dimension_id, description |
| `niveles_abstraccion.policy_areas` | Assembly | required_evidence_keys |
| `semantic_layers` | Chunking | embedding_strategy, disambiguation |
| `meso_questions.patterns` | Assembly | type, description |
| `macro_question.fallback` | Assembly | condition, pattern, priority |
