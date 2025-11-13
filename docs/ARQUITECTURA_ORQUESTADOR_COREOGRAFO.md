# ARQUITECTURA: ORQUESTADOR VS COREÓGRAFO
## Diferencias, Responsabilidades y Características

---

## PARTE 1: VISIÓN GENERAL

### 1.1. DEFINICIÓN DE ROLES

```
┌────────────────────────────────────────────────────────────────┐
│                        ORQUESTADOR                             │
│                    (Control Centralizado)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  "EL DIRECTOR DE ORQUESTA"                                     │
│                                                                │
│  • Conoce TODA la partitura (questionnaire_monolith)          │
│  • Decide QUÉ preguntas procesar                              │
│  • Coordina el ORDEN de las fases                             │
│  • Maneja el estado GLOBAL del sistema                        │
│  • Es el ÚNICO punto de entrada                               │
│  • Toma decisiones estratégicas                               │
│  • Gestiona excepciones globales                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                              ↓ delega a
┌────────────────────────────────────────────────────────────────┐
│                        COREÓGRAFO                              │
│                   (Ejecución Distribuida)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  "EL ENSEMBLE DE BAILARINES"                                   │
│                                                                │
│  • Ejecuta UNA pregunta a la vez                              │
│  • NO conoce otras preguntas                                   │
│  • Interpreta el DAG de métodos                                │
│  • Coordina sync/async de métodos                             │
│  • Maneja estado LOCAL (una pregunta)                         │
│  • Puede ejecutarse en paralelo                               │
│  • Reporta resultados al Orquestador                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## PARTE 2: EL ORQUESTADOR (Orchestrator)

### 2.1. RESPONSABILIDADES PRINCIPALES

**ROL**: Gestor de alto nivel del pipeline completo

```python
RESPONSABILIDADES DEL ORQUESTADOR:

1. ✓ Cargar y validar configuración
   - questionnaire_monolith.json
   - complete_canonical_catalog.json
   - Verificar integrity hashes

2. ✓ Gestionar el ciclo de vida completo
   - Ingestión del documento
   - Ejecución de 300 micro preguntas
   - Agregaciones (dimensiones → áreas → clusters → macro)
   - Generación de reportes

3. ✓ Coordinar fases secuenciales
   - Fase 0 → Fase 1 → Fase 2 → ... → Fase 10
   - Decidir CUÁNDO pasar a la siguiente fase
   - Verificar pre-condiciones entre fases

4. ✓ Distribuir trabajo a Coreógrafos
   - Crear 300 instancias de Coreógrafo (una por pregunta)
   - Asignar pregunta_global + contexto
   - Esperar a que todos terminen (WAIT)

5. ✓ Agregar resultados globales
   - Recolectar 300 QuestionResults
   - Agregar dimensiones → áreas → clusters → macro
   - Calcular índice de calidad global

6. ✓ Manejar errores globales
   - Si un Coreógrafo falla críticamente → decidir si abortar
   - Retry logic
   - Degradación elegante

7. ✓ Generar reporte final
   - Ensamblar todos los niveles
   - Formatear salidas
   - Entregar al usuario
```

---

### 2.2. INTERFAZ DEL ORQUESTADOR

```python
* CLASE: Orchestrator
  """
  Orquestador central del sistema de evaluación
  """
  
  # ========================================================================
  # INICIALIZACIÓN
  # ========================================================================
  
  * MÉTODO: __init__(
      monolith_path: str = 'questionnaire_monolith.json',
      catalog_path: str = 'complete_canonical_catalog.json',
      config: dict = None
    )
    """
    Inicializa el orquestador cargando configuración
    
    Args:
      monolith_path: Ruta al questionnaire monolith
      catalog_path: Ruta al catálogo de métodos
      config: Configuración adicional (timeouts, paralelismo, etc)
    
    Estado interno:
      - self.monolith: questionnaire_monolith cargado
      - self.method_catalog: metodos_completos cargado
      - self.config: configuración global
      - self.state: estado del procesamiento
      - self.metrics: métricas de ejecución
    """
    SYNC
  
  
  # ========================================================================
  # MÉTODO PRINCIPAL
  # ========================================================================
  
  * MÉTODO: process_document(pdf_path: str) → CompleteReport
    """
    Pipeline completo end-to-end
    
    Este es el ÚNICO punto de entrada público del sistema
    
    Args:
      pdf_path: Ruta al PDF del plan de desarrollo
    
    Returns:
      CompleteReport con 305 respuestas + recomendaciones + formatos
    
    Proceso:
      FASE 0: validate_configuration()
      FASE 1: ingest_document(pdf_path)
      FASE 2: execute_all_micro_questions()
      FASE 3: score_all_questions()
      FASE 4: aggregate_dimensions()
      FASE 5: aggregate_areas()
      FASE 6: aggregate_clusters()
      FASE 7: evaluate_macro()
      FASE 8: generate_recommendations()
      FASE 9: assemble_report()
      FASE 10: format_outputs()
    """
    SYNC (pero coordina ASYNC internamente)
  
  
  # ========================================================================
  # FASE 0: VALIDACIÓN
  # ========================================================================
  
  * MÉTODO: validate_configuration() → bool
    """
    Valida que toda la configuración sea correcta
    
    Verifica:
      - Integrity hash del monolith
      - Counts correctos (300 micro, 4 meso, 1 macro)
      - Catálogo de métodos completo (416 métodos)
      - Cluster hermeticity
      - Base slots mapping correcto
    
    Returns:
      True si válido, RAISE exception si no
    """
    SYNC
  
  
  # ========================================================================
  # FASE 1: INGESTIÓN
  # ========================================================================
  
  * MÉTODO: ingest_document(pdf_path: str) → PreprocessedDocument
    """
    Coordina la ingestión del documento
    
    Delega a:
      * DI.DocumentLoader.load_pdf()
      * DI.TextExtractor.extract_full_text()
      * DI.PreprocessingEngine.preprocess_document()
    
    Cachea el resultado para todas las preguntas
    
    Returns:
      PreprocessedDocument inmutable
    """
    SYNC
  
  
  # ========================================================================
  # FASE 2: EJECUCIÓN DE MICRO PREGUNTAS
  # ========================================================================
  
  * MÉTODO: execute_all_micro_questions(
      preprocessed_doc: PreprocessedDocument
    ) → list[QuestionResult]
    """
    Coordina la ejecución de las 300 micro preguntas
    
    Estrategia:
      1. Crear pool de Coreógrafos (workers)
      2. Distribuir 300 preguntas entre workers
      3. Ejecutar en PARALELO (configuración: max_workers)
      4. WAIT hasta que todas terminen
      5. Recolectar 300 QuestionResults
    
    Manejo de errores:
      - Si pregunta crítica falla → retry 3 veces
      - Si sigue fallando → marcar como FAILED
      - Continuar con otras preguntas
      - Al final, decidir si abortar o continuar
    
    Returns:
      list[QuestionResult] (300 elementos)
    """
    ASYNC (coordina 300 Coreógrafos)
  
  
  * MÉTODO: _create_choreographer_pool(
      max_workers: int = 50
    ) → ChoreographerPool
    """
    Crea pool de Coreógrafos para ejecución paralela
    
    Args:
      max_workers: Máximo de preguntas ejecutándose simultáneamente
    
    Returns:
      Pool de Coreógrafos listos para ejecutar
    """
    SYNC
  
  
  * MÉTODO: _distribute_questions(
      pool: ChoreographerPool,
      preprocessed_doc: PreprocessedDocument
    ) → list[Future[QuestionResult]]
    """
    Distribuye 300 preguntas al pool
    
    Para cada question_global (1-300):
      - Obtener metadata del monolith
      - Crear contexto de ejecución
      - Asignar a un Coreógrafo disponible
      - Retornar Future para resultado
    
    Returns:
      Lista de 300 Futures
    """
    ASYNC
  
  
  * MÉTODO: _wait_for_all_questions(
      futures: list[Future]
    ) → list[QuestionResult]
    """
    Espera a que todas las preguntas terminen
    
    Monitorea progreso:
      - Cada 10 segundos, reporta % completado
      - Timeout configurable (default: 30 minutos)
      - Si timeout → cancela pendientes, retorna completados
    
    Returns:
      Lista de QuestionResults (puede ser < 300 si hubo timeouts)
    """
    SYNC (bloquea hasta que todos terminen)
  
  
  # ========================================================================
  # FASE 3-7: AGREGACIONES
  # ========================================================================
  
  * MÉTODO: score_all_questions(
      micro_results: list[QuestionResult]
    ) → list[ScoredResult]
    """
    Aplica scoring a 300 preguntas
    
    Delega a SC.MicroQuestionScorer para cada pregunta
    """
    ASYNC (300 scorings en paralelo)
  
  
  * MÉTODO: aggregate_dimensions(
      scored_results: list[ScoredResult]
    ) → list[DimensionScore]
    """
    Agrega 60 dimensiones (6 dims × 10 áreas)
    
    Delega a AG.DimensionAggregator
    """
    ASYNC (60 agregaciones en paralelo)
  
  
  * MÉTODO: aggregate_areas(
      dimension_scores: list[DimensionScore]
    ) → list[AreaScore]
    """
    Agrega 10 áreas de política
    
    Delega a AG.AreaPolicyAggregator
    """
    ASYNC (10 agregaciones en paralelo)
  
  
  * MÉTODO: aggregate_clusters(
      area_scores: list[AreaScore]
    ) → list[ClusterScore]
    """
    Agrega 4 clusters (MESO questions)
    
    Delega a AG.ClusterAggregator
    """
    SYNC (solo 4, no vale la pena paralelizar)
  
  
  * MÉTODO: evaluate_macro(
      cluster_scores: list[ClusterScore]
    ) → MacroScore
    """
    Evaluación holística (MACRO question)
    
    Delega a AG.MacroEvaluator
    """
    SYNC
  
  
  # ========================================================================
  # FASE 8-10: REPORTE
  # ========================================================================
  
  * MÉTODO: generate_recommendations(
      all_scores: dict
    ) → list[Recommendation]
    """
    Genera recomendaciones en todos los niveles
    
    Delega a RA.RecommendationEngine
    """
    ASYNC (multinivel en paralelo)
  
  
  * MÉTODO: assemble_report(
      all_data: dict
    ) → CompleteReport
    """
    Ensambla reporte completo
    
    Delega a RA.ReportAssembler
    """
    SYNC (con paralelismo interno)
  
  
  * MÉTODO: format_outputs(
      report: CompleteReport
    ) → dict[str, bytes]
    """
    Genera 4 formatos: JSON, HTML, PDF, Excel
    
    Delega a RA.ReportFormatter
    """
    ASYNC (4 formatos en paralelo)
  
  
  # ========================================================================
  # MÉTODOS DE ESTADO Y MONITOREO
  # ========================================================================
  
  * MÉTODO: get_processing_status() → ProcessingStatus
    """
    Retorna estado actual del procesamiento
    
    Returns:
      {
        'current_phase': str,
        'progress': float (0-1),
        'questions_completed': int,
        'questions_total': int,
        'elapsed_time': float (seconds),
        'estimated_time_remaining': float
      }
    """
    SYNC
  
  
  * MÉTODO: get_metrics() → ProcessingMetrics
    """
    Retorna métricas detalladas
    
    Returns:
      {
        'total_time': float,
        'phase_times': dict[str, float],
        'avg_question_time': float,
        'parallelism_efficiency': float,
        'errors': list[Error],
        'warnings': list[Warning]
      }
    """
    SYNC
  
  
  # ========================================================================
  # MANEJO DE ERRORES
  # ========================================================================
  
  * MÉTODO: handle_critical_error(
      error: Exception,
      context: dict
    ) → ErrorResponse
    """
    Maneja errores críticos que no permiten continuar
    
    Decisiones:
      - Si < 10% de preguntas completadas → ABORT
      - Si >= 10% pero < 50% → PARTIAL report
      - Si >= 50% → CONTINUE con lo que se tiene
    """
    SYNC
  
  
  * MÉTODO: retry_failed_question(
      question_global: int,
      max_retries: int = 3
    ) → QuestionResult | None
    """
    Reintenta una pregunta que falló
    
    Estrategia de backoff exponencial:
      - Retry 1: inmediato
      - Retry 2: 5 segundos después
      - Retry 3: 15 segundos después
    """
    SYNC
```

---

### 2.3. CARACTERÍSTICAS DEL ORQUESTADOR

```
┌─────────────────────────────────────────────────────────┐
│ CARACTERÍSTICAS CLAVE                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. ÚNICO PUNTO DE ENTRADA                              │
│    • process_document() es la única API pública        │
│    • Todo pasa por el Orquestador                      │
│                                                         │
│ 2. CONOCIMIENTO GLOBAL                                 │
│    • Conoce las 305 preguntas                          │
│    • Conoce el monolith completo                       │
│    • Conoce el estado de todo el sistema               │
│                                                         │
│ 3. CONTROL CENTRALIZADO                                │
│    • Decide orden de fases                             │
│    • Decide cuándo paralelizar                         │
│    • Decide cuándo abortar                             │
│                                                         │
│ 4. GESTIÓN DE RECURSOS                                 │
│    • Crea/destruye Coreógrafos                         │
│    • Limita paralelismo (max_workers)                  │
│    • Gestiona memoria y CPU                            │
│                                                         │
│ 5. TOLERANCIA A FALLOS                                 │
│    • Retry logic para fallos                           │
│    • Degradación elegante                              │
│    • Reportes parciales si es necesario                │
│                                                         │
│ 6. OBSERVABILIDAD                                      │
│    • Métricas de rendimiento                           │
│    • Logs estructurados                                │
│    • Status API                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## PARTE 3: EL COREÓGRAFO (Choreographer)

### 3.1. RESPONSABILIDADES PRINCIPALES

**ROL**: Ejecutor especializado de UNA pregunta individual

```python
RESPONSABILIDADES DEL COREÓGRAFO:

1. ✓ Recibir asignación de pregunta
   - question_global (1-300)
   - PreprocessedDocument
   - Contexto específico

2. ✓ Mapear pregunta a métodos
   - Usar base_slot para encontrar catálogo
   - Obtener flow_spec de métodos
   - Construir DAG de ejecución

3. ✓ Coordinar ejecución de métodos
   - Interpretar flow_spec (ej: "PP.O → CD.E+T → ...")
   - Identificar ramas paralelas (||)
   - Crear barreras WAIT donde necesario

4. ✓ Ejecutar métodos según DAG
   - Respetar dependencias
   - Paralelizar donde sea seguro
   - Manejar errores por prioridad

5. ✓ Extraer evidencias
   - De los resultados de métodos
   - Según indicators del monolith
   - Estructurar según scoring_modality

6. ✓ Retornar resultado al Orquestador
   - QuestionResult completo
   - Timing metrics
   - Errores/warnings si los hubo

7. ✓ NO conocer otras preguntas
   - Opera de forma aislada
   - No comparte estado con otros Coreógrafos
   - No sabe si es el primero o último
```

---

### 3.2. INTERFAZ DEL COREÓGRAFO

```python
* CLASE: Choreographer
  """
  Ejecutor especializado de una pregunta individual
  """
  
  # ========================================================================
  # INICIALIZACIÓN
  # ========================================================================
  
  * MÉTODO: __init__(
      method_catalog: dict,
      monolith: dict,
      config: dict = None
    )
    """
    Inicializa un Coreógrafo
    
    Args:
      method_catalog: complete_canonical_catalog.json
      monolith: questionnaire_monolith.json
      config: Configuración (timeouts, etc)
    
    Estado interno:
      - self.method_catalog: catálogo de métodos
      - self.monolith: monolith para metadata
      - self.method_executor: ejecutor de métodos individuales
      - self.flow_controller: controlador de flujo DAG
    """
    SYNC
  
  
  # ========================================================================
  # MÉTODO PRINCIPAL
  # ========================================================================
  
  * MÉTODO: execute_question(
      question_global: int,
      preprocessed_doc: PreprocessedDocument
    ) → QuestionResult
    """
    Ejecuta UNA pregunta completa
    
    Este es el método principal del Coreógrafo
    
    Args:
      question_global: Número de pregunta (1-300)
      preprocessed_doc: Documento preprocesado
    
    Returns:
      QuestionResult con evidencias y resultados
    
    Proceso:
      PASO 1: map_question_to_methods()
      PASO 2: build_execution_plan()
      PASO 3: execute_methods_dag()
      PASO 4: extract_evidence()
      PASO 5: construct_result()
    """
    HÍBRIDO (SYNC para coordinación, ASYNC para métodos paralelos)
  
  
  # ========================================================================
  # PASO 1: MAPEO
  # ========================================================================
  
  * MÉTODO: map_question_to_methods(
      question_global: int
    ) → QuestionMethodMapping
    """
    Mapea pregunta a su catálogo de métodos
    
    Proceso:
      1. Calcular base_slot
         base_index = (question_global - 1) % 30
         base_slot = f"D{base_index//5+1}-Q{base_index%5+1}"
      
      2. Obtener metadata del monolith
         q_metadata = monolith['blocks']['micro_questions'][question_global-1]
      
      3. Validar base_slot
         ASSERT q_metadata['base_slot'] == base_slot
      
      4. Obtener catálogo de métodos
         dimension_idx = base_index // 5
         question_idx = base_index % 5
         base_q = method_catalog['dimensions'][dimension_idx]['questions'][question_idx]
      
      5. Extraer method_packages y flow_spec
         packages = base_q['p']
         flow = base_q['flow']
    
    Returns:
      QuestionMethodMapping {
        question_global: int,
        base_slot: str,
        metadata: dict,
        method_packages: list,
        flow_spec: str
      }
    """
    SYNC
  
  
  # ========================================================================
  # PASO 2: PLANIFICACIÓN
  # ========================================================================
  
  * MÉTODO: build_execution_plan(
      mapping: QuestionMethodMapping
    ) → ExecutionPlan
    """
    Construye plan de ejecución desde flow_spec
    
    Usa:
      - FlowController.build_execution_dag(flow_spec)
      - FlowController.identify_parallel_branches(dag)
      - FlowController.create_sync_barriers(dag)
    
    Returns:
      ExecutionPlan {
        dag: DAG,
        parallel_groups: list[list[Node]],
        sync_barriers: list[Barrier],
        topological_order: list[Node]
      }
    """
    SYNC
  
  
  # ========================================================================
  # PASO 3: EJECUCIÓN
  # ========================================================================
  
  * MÉTODO: execute_methods_dag(
      plan: ExecutionPlan,
      preprocessed_doc: PreprocessedDocument,
      mapping: QuestionMethodMapping
    ) → dict[str, MethodResult]
    """
    Ejecuta todos los métodos según el DAG
    
    Algoritmo:
      context = {
        'preprocessed_doc': preprocessed_doc,
        'question_global': mapping.question_global,
        'base_slot': mapping.base_slot,
        'metadata': mapping.metadata,
        'results_cache': {}
      }
      
      all_results = {}
      
      PARA node EN plan.topological_order:
        
        SI node EN parallel_group:
          # Ejecutar grupo en paralelo
          ASYNC_START:
            PARA parallel_node EN parallel_group:
              result = execute_node(parallel_node, mapping.method_packages, context)
              all_results[parallel_node.id] = result
          WAIT
        
        SINO:
          # Ejecutar secuencialmente
          result = execute_node(node, mapping.method_packages, context)
          all_results[node.id] = result
          context['results_cache'][node.id] = result
      
      RETURN all_results
    """
    HÍBRIDO (SYNC + ASYNC según DAG)
  
  
  * MÉTODO: execute_node(
      node: DAGNode,
      method_packages: list,
      context: dict
    ) → dict[str, Any]
    """
    Ejecuta todos los métodos de un nodo
    
    Proceso:
      1. Encontrar package correspondiente al nodo
         package = FIND_PACKAGE(method_packages, node.file, node.types)
      
      2. Para cada método en package['m']:
         - Verificar que tipo coincida con node.types
         - Ejecutar método usando MethodExecutor
         - Manejar errores según prioridad
      
      3. Retornar resultados del nodo
    
    Returns:
      dict[method_name, result]
    """
    SYNC (dentro de este nodo)
  
  
  # ========================================================================
  # PASO 4: EXTRACCIÓN DE EVIDENCIAS
  # ========================================================================
  
  * MÉTODO: extract_evidence(
      method_results: dict,
      q_metadata: dict
    ) → Evidence
    """
    Extrae evidencias de los resultados de métodos
    
    Proceso:
      1. Obtener indicators esperados
         indicators = q_metadata['indicators']
      
      2. Obtener evidence_patterns
         patterns = q_metadata['evidence_patterns']
      
      3. Obtener scoring_modality
         modality = q_metadata['scoring_modality']
      
      4. Buscar en method_results las evidencias
         Para cada indicator:
           - Buscar en resultados de métodos relevantes
           - Extraer valor/presencia
      
      5. Estructurar según modality
         TYPE_A: {elements: [lista de 4]}
         TYPE_B: {elements: [lista hasta 3]}
         TYPE_C: {elements: [lista de 2]}
         TYPE_D: {elements: [...], weights: {...}}
         TYPE_E: {present: bool}
         TYPE_F: {value: float, min: float, max: float}
    
    Returns:
      Evidence estructurada según scoring_modality
    """
    SYNC
  
  
  # ========================================================================
  # PASO 5: CONSTRUCCIÓN DEL RESULTADO
  # ========================================================================
  
  * MÉTODO: construct_result(
      mapping: QuestionMethodMapping,
      method_results: dict,
      evidence: Evidence,
      execution_time: float
    ) → QuestionResult
    """
    Construye el resultado final de la pregunta
    
    Returns:
      QuestionResult {
        question_global: int,
        base_slot: str,
        policy_area: str,
        dimension: str,
        evidence: Evidence,
        raw_results: dict,
        execution_time: float,
        methods_executed: int,
        errors: list[Error],
        warnings: list[Warning]
      }
    """
    SYNC
  
  
  # ========================================================================
  # DELEGACIÓN A EJECUTOR DE MÉTODOS
  # ========================================================================
  
  * MÉTODO: _execute_single_method(
      file_code: str,
      class_name: str,
      method_name: str,
      context: dict
    ) → Any
    """
    Ejecuta UN método individual
    
    Delega a:
      OR.MethodExecutor.execute_method()
    
    Este es el punto donde se llaman los 166 métodos existentes:
      ✓ PP (12 métodos)
      ✓ CD (44 métodos)
      ✓ FV (27 métodos)
      ✓ DB (43 métodos)
      ✓ EP (9 métodos)
      ✓ A1 (16 métodos)
      ✓ TC (14 métodos)
      ✓ SC (1 método)
    """
    SYNC
  
  
  # ========================================================================
  # MANEJO DE ERRORES
  # ========================================================================
  
  * MÉTODO: handle_method_error(
      error: Exception,
      method_spec: dict
    ) → ErrorHandlingDecision
    """
    Decide qué hacer cuando un método falla
    
    Estrategia según prioridad:
      - priority == 3 (Crítico) → RAISE error
      - priority == 2 (Importante) → LOG + CONTINUE
      - priority == 1 (Complementario) → SKIP silently
    
    Returns:
      ErrorHandlingDecision {
        action: 'RAISE' | 'CONTINUE' | 'SKIP',
        logged: bool,
        retry_count: int
      }
    """
    SYNC
```

---

### 3.3. CARACTERÍSTICAS DEL COREÓGRAFO

```
┌─────────────────────────────────────────────────────────┐
│ CARACTERÍSTICAS CLAVE                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. ESPECIALIZACIÓN                                     │
│    • Experto en ejecutar UNA pregunta                  │
│    • Conoce el flow_spec en profundidad                │
│    • Interpreta DAG de métodos                         │
│                                                         │
│ 2. AISLAMIENTO                                         │
│    • NO conoce otras preguntas                         │
│    • NO comparte estado con otros Coreógrafos          │
│    • Opera de forma independiente                      │
│                                                         │
│ 3. COORDINACIÓN LOCAL                                  │
│    • Coordina métodos DENTRO de una pregunta           │
│    • Decide sync/async de métodos                      │
│    • Maneja dependencias locales                       │
│                                                         │
│ 4. EJECUCIÓN HÍBRIDA                                   │
│    • Métodos críticos en secuencia                     │
│    • Métodos independientes en paralelo                │
│    • Respeta el DAG del flow_spec                      │
│                                                         │
│ 5. MANEJO DE ERRORES LOCAL                            │
│    • Decide según prioridad del método                 │
│    • Reporta errores al Orquestador                    │
│    • NO toma decisiones globales                       │
│                                                         │
│ 6. STATELESS                                           │
│    • No mantiene estado entre preguntas                │
│    • Puede ser destruido después de ejecutar           │
│    • Pool de Coreógrafos reutilizables                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## PARTE 4: INTERACCIÓN ORQUESTADOR ↔ COREÓGRAFO

### 4.1. FLUJO DE COMUNICACIÓN

```
┌──────────────────────────────────────────────────────────────────┐
│ ORQUESTADOR                                                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ 1. Crear pool
                              ↓
                    ┌─────────────────────┐
                    │ ChoreographerPool   │
                    │ (50 workers)        │
                    └─────────────────────┘
                              │
                              │ 2. Distribuir 300 preguntas
                              ↓
     ┌────────────────────────┼────────────────────────┐
     │                        │                        │
     ↓                        ↓                        ↓
┌─────────┐              ┌─────────┐              ┌─────────┐
│Coreógrafo│              │Coreógrafo│    ...      │Coreógrafo│
│   #1    │              │   #2    │              │  #50    │
│         │              │         │              │         │
│  Q1     │              │  Q2     │              │  Q50    │
└─────────┘              └─────────┘              └─────────┘
     │                        │                        │
     │ 3. Ejecutar pregunta   │                        │
     ↓                        ↓                        ↓
┌─────────┐              ┌─────────┐              ┌─────────┐
│ Mapear  │              │ Mapear  │              │ Mapear  │
│ métodos │              │ métodos │              │ métodos │
└─────────┘              └─────────┘              └─────────┘
     ↓                        ↓                        ↓
┌─────────┐              ┌─────────┐              ┌─────────┐
│Construir│              │Construir│              │Construir│
│   DAG   │              │   DAG   │              │   DAG   │
└─────────┘              └─────────┘              └─────────┘
     ↓                        ↓                        ↓
┌─────────┐              ┌─────────┐              ┌─────────┐
│Ejecutar │              │Ejecutar │              │Ejecutar │
│ métodos │              │ métodos │              │ métodos │
│ según   │              │ según   │              │ según   │
│  DAG    │              │  DAG    │              │  DAG    │
└─────────┘              └─────────┘              └─────────┘
     ↓                        ↓                        ↓
┌─────────┐              ┌─────────┐              ┌─────────┐
│Extraer  │              │Extraer  │              │Extraer  │
│evidencia│              │evidencia│              │evidencia│
└─────────┘              └─────────┘              └─────────┘
     │                        │                        │
     │ 4. Retornar resultado  │                        │
     ↓                        ↓                        ↓
     └────────────────────────┼────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ ORQUESTADOR                                                      │
│ 5. Recolectar 300 QuestionResults                               │
│ 6. Continuar con siguiente fase                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

### 4.2. PROTOCOLO DE COMUNICACIÓN

```python
# ============================================================================
# PROTOCOLO ORQUESTADOR → COREÓGRAFO
# ============================================================================

MENSAJE: ExecuteQuestionRequest
{
  "question_global": int,                    # 1-300
  "preprocessed_doc": PreprocessedDocument,  # Documento preprocesado
  "timeout": float,                          # Timeout en segundos (default: 300)
  "retry_on_failure": bool,                  # Si retry automáticamente
  "context": {                               # Contexto adicional
    "area": str,                             # ej: "P1"
    "dimension": str,                        # ej: "D1"
    "base_slot": str                         # ej: "D1-Q1"
  }
}


# ============================================================================
# PROTOCOLO COREÓGRAFO → ORQUESTADOR
# ============================================================================

MENSAJE: QuestionResult (ÉXITO)
{
  "question_global": int,
  "base_slot": str,
  "policy_area": str,
  "dimension": str,
  "evidence": Evidence,
  "raw_results": dict,
  "execution_time": float,
  "methods_executed": int,
  "status": "SUCCESS",
  "metrics": {
    "methods_total": int,
    "methods_succeeded": int,
    "methods_failed": int,
    "methods_skipped": int,
    "parallel_efficiency": float  # 0-1
  }
}


MENSAJE: QuestionResult (FALLO)
{
  "question_global": int,
  "base_slot": str,
  "status": "FAILED",
  "error": {
    "type": str,
    "message": str,
    "stacktrace": str,
    "failed_method": {
      "file": str,
      "class": str,
      "method": str,
      "priority": int
    }
  },
  "partial_results": dict | null,  # Resultados parciales si los hay
  "execution_time": float
}


MENSAJE: QuestionResult (TIMEOUT)
{
  "question_global": int,
  "base_slot": str,
  "status": "TIMEOUT",
  "partial_results": dict,
  "completed_methods": int,
  "total_methods": int,
  "execution_time": float
}
```

---

### 4.3. MANEJO DE ESCENARIOS ESPECIALES

```python
# ============================================================================
# ESCENARIO 1: PREGUNTA CON MUCHOS MÉTODOS (ej: D6-Q1 con 32 métodos)
# ============================================================================

ORQUESTADOR:
  • Asigna timeout mayor (5 minutos en vez de 3)
  • Monitorea progreso más de cerca
  • Permite más memoria al Coreógrafo

COREÓGRAFO:
  • Agrupa métodos en más ramas paralelas
  • Reporta progreso intermedio cada 10 métodos
  • Libera memoria de resultados intermedios no necesarios


# ============================================================================
# ESCENARIO 2: MÉTODO CRÍTICO FALLA (priority=3)
# ============================================================================

COREÓGRAFO:
  • Intenta retry inmediato (1 vez)
  • Si falla nuevamente → RAISE exception
  • Retorna QuestionResult con status="FAILED"

ORQUESTADOR:
  • Recibe FAILED result
  • Decide si retry la pregunta completa (máx 3 veces)
  • Si sigue fallando → marca pregunta como FAILED
  • Continúa con otras preguntas
  • Al final, decide si el reporte es viable con preguntas faltantes


# ============================================================================
# ESCENARIO 3: SISTEMA BICAMERAL (D6-Q3 y D6-Q4 con 2 rutas)
# ============================================================================

COREÓGRAFO:
  • Detecta que flow_spec tiene dos rutas independientes
  • Ejecuta RUTA 1 y RUTA 2 en PARALELO
  • WAIT hasta que ambas terminen
  • Sintetiza resultados de ambas rutas
  • Retorna evidencia combinada

ORQUESTADOR:
  • No necesita saber que es bicameral
  • Recibe QuestionResult normal
  • El Coreógrafo maneja la complejidad internamente


# ============================================================================
# ESCENARIO 4: VALIDACIÓN ANTI-MILAGRO (D6-Q2)
# ============================================================================

COREÓGRAFO:
  • Ejecuta métodos normalmente
  • Al final, aplica validación anti-milagro
  • Si detecta "milagro" (salto lógico) → score = 0.0
  • Añade warning en QuestionResult

ORQUESTADOR:
  • Recibe QuestionResult con warning
  • Incluye warning en reporte final
  • No interfiere con la validación


# ============================================================================
# ESCENARIO 5: CARGA ALTA (300 preguntas simultáneas)
# ============================================================================

ORQUESTADOR:
  • Limita paralelismo con max_workers (ej: 50)
  • Cola de 250 preguntas esperando
  • Conforme Coreógrafos terminan, asigna nuevas preguntas
  • Monitorea uso de CPU/memoria
  • Si recursos escasos → reduce max_workers dinámicamente

COREÓGRAFO:
  • No es consciente de la cola
  • Ejecuta su pregunta independientemente
  • Libera recursos al terminar
```

---

## PARTE 5: COMPARACIÓN LADO A LADO

```
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ ASPECTO              │ ORQUESTADOR          │ COREÓGRAFO           │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Alcance              │ TODO el sistema      │ UNA pregunta         │
│                      │ (305 preguntas)      │                      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Conocimiento         │ Global               │ Local                │
│                      │ • 10 fases           │ • 1 pregunta         │
│                      │ • 300 preguntas      │ • N métodos          │
│                      │ • Monolith completo  │ • 1 flow_spec        │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Decisiones           │ Estratégicas         │ Tácticas             │
│                      │ • Cuándo agregar     │ • Cómo ejecutar      │
│                      │ • Cuándo abortar     │ • Orden de métodos   │
│                      │ • Cuándo paralelizar │ • Manejo de errores  │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Estado               │ Stateful             │ Stateless            │
│                      │ • Mantiene historial │ • Solo su pregunta   │
│                      │ • Progreso global    │ • Se destruye        │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Paralelismo          │ Coordina             │ Ejecuta              │
│                      │ • Crea 300 Coreógraf.│ • Métodos internos   │
│                      │ • Distribuye trabajo │ • Según DAG          │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Complejidad          │ Alta                 │ Media                │
│                      │ • 10 fases           │ • 5 pasos            │
│                      │ • Múltiples niveles  │ • 1 nivel            │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ API pública          │ 1 método             │ 1 método             │
│                      │ process_document()   │ execute_question()   │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Tolerancia fallos    │ Global               │ Local                │
│                      │ • Retry preguntas    │ • Retry métodos      │
│                      │ • Reportes parciales │ • Raise si crítico   │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Dependencias         │ Todo                 │ Limitadas            │
│                      │ • DI, OR, SC, AG, RA │ • OR (MethodExecutor)│
│                      │ • Coreógrafos        │ • FlowController     │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Ciclo de vida        │ Único                │ Múltiple             │
│                      │ • 1 por procesamiento│ • N por procesamiento│
│                      │ • Vive todo el tiempo│ • Pool reutilizable  │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Responsabilidad      │ QUÉ procesar         │ CÓMO procesar        │
│                      │ CUÁNDO procesar      │ 1 pregunta           │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## PARTE 6: BENEFICIOS DE ESTA ARQUITECTURA

### 6.1. SEPARACIÓN DE RESPONSABILIDADES

```
✓ ORQUESTADOR se enfoca en:
  - Estrategia global
  - Gestión de recursos
  - Decisiones de alto nivel
  - Agregaciones multinivel
  - Generación de reportes

✓ COREÓGRAFO se enfoca en:
  - Ejecución eficiente de 1 pregunta
  - Interpretación del DAG
  - Coordinación sync/async de métodos
  - Extracción de evidencias
```

---

### 6.2. ESCALABILIDAD

```
✓ Paralelismo natural:
  - 300 Coreógrafos pueden ejecutarse simultáneamente
  - Limitado solo por max_workers
  - CPU/memoria se aprovecha al máximo

✓ Distribución futura:
  - Coreógrafos pueden ejecutarse en diferentes máquinas
  - Orquestador coordina remotamente
  - Cloud-ready architecture
```

---

### 6.3. MANTENIBILIDAD

```
✓ Módulos independientes:
  - Cambios en Orquestador no afectan Coreógrafos
  - Cambios en Coreógrafos no afectan agregaciones
  - Fácil debugging (aislamiento)

✓ Testing aislado:
  - Test Orquestador con Coreógrafos mock
  - Test Coreógrafo con 1 pregunta
  - Test métodos individuales aisladamente
```

---

### 6.4. TOLERANCIA A FALLOS

```
✓ Fallo de Coreógrafo:
  - Solo afecta 1 pregunta
  - Orquestador puede retry
  - Sistema continúa con otras 299 preguntas

✓ Fallo de Orquestador:
  - Sistema completo se detiene
  - Pero es único punto de fallo
  - Puede guardarse estado y reiniciar
```

---

## PARTE 7: CONFIGURACIÓN RECOMENDADA

```python
# ============================================================================
# CONFIGURACIÓN DEL ORQUESTADOR
# ============================================================================

ORCHESTRATOR_CONFIG = {
  # Pool de Coreógrafos
  'max_workers': 50,              # Máximo de preguntas en paralelo
  'min_workers': 10,              # Mínimo para mantener calientes
  
  # Timeouts
  'default_question_timeout': 180,   # 3 minutos por pregunta
  'complex_question_timeout': 300,   # 5 minutos para D6-Q1, D6-Q2, etc
  'global_timeout': 3600,            # 1 hora para todo el proceso
  
  # Retry logic
  'max_question_retries': 3,
  'retry_backoff_factor': 2,         # Exponential backoff
  
  # Tolerancia a fallos
  'min_completion_rate': 0.9,        # Mínimo 90% de preguntas completas
  'allow_partial_report': True,      # Generar reporte parcial si es necesario
  
  # Recursos
  'memory_limit_per_worker': '2GB',
  'cpu_cores_per_worker': 1,
  
  # Monitoreo
  'progress_report_interval': 30,    # Segundos
  'enable_metrics': True,
  'log_level': 'INFO'
}


# ============================================================================
# CONFIGURACIÓN DEL COREÓGRAFO
# ============================================================================

CHOREOGRAPHER_CONFIG = {
  # Timeouts de métodos
  'method_timeout': 30,              # 30 segundos por método
  'critical_method_timeout': 60,     # 1 minuto para métodos críticos
  
  # Paralelismo interno
  'enable_internal_parallelism': True,
  'max_parallel_methods': 5,         # Máximo de métodos en paralelo
  
  # Retry de métodos
  'retry_critical_methods': True,
  'max_method_retries': 1,           # Solo 1 retry inmediato
  
  # Memoria
  'cache_method_results': True,
  'clear_cache_after_execution': True,
  
  # Logging
  'log_method_execution': True,
  'log_level': 'DEBUG'
}
```

---

## RESUMEN EJECUTIVO

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA ORQUESTADOR/COREÓGRAFO          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ORQUESTADOR (1 único)                                          │
│  ├─ Conocimiento: GLOBAL (305 preguntas)                        │
│  ├─ Control: CENTRALIZADO                                       │
│  ├─ Responsabilidad: QUÉ y CUÁNDO                               │
│  └─ API: process_document(pdf) → CompleteReport                │
│                                                                 │
│  COREÓGRAFO (Pool de N workers)                                 │
│  ├─ Conocimiento: LOCAL (1 pregunta)                            │
│  ├─ Control: DISTRIBUIDO                                        │
│  ├─ Responsabilidad: CÓMO                                       │
│  └─ API: execute_question(q_num, doc) → QuestionResult         │
│                                                                 │
│  BENEFICIOS                                                     │
│  ✓ Separación clara de responsabilidades                       │
│  ✓ Paralelismo natural (300 preguntas)                         │
│  ✓ Escalabilidad horizontal (más workers)                      │
│  ✓ Tolerancia a fallos (aislamiento)                           │
│  ✓ Mantenibilidad (módulos independientes)                     │
│  ✓ Testing facilitado (unidades pequeñas)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
