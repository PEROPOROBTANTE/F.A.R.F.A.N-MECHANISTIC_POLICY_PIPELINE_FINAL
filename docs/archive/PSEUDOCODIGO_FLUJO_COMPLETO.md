# PSEUDOCÓDIGO COMPLETO DEL SISTEMA
## Flujo End-to-End con Indicadores de Existencia y Concurrencia

```
LEYENDA:
  *      = NO EXISTE (debe implementarse)
  ✓      = EXISTE en el catálogo actual
  SYNC   = Ejecución síncrona (secuencial, espera a que termine)
  ASYNC  = Ejecución asíncrona (paralelo, no bloquea)
  WAIT   = Barrera de sincronización (espera a que todos los ASYNC terminen)
```

---

## FUNCIÓN PRINCIPAL: process_development_plan

```python
* FUNCIÓN: process_development_plan(pdf_path: str) → CompleteReport
  """
  Pipeline completo para procesar un plan de desarrollo municipal
  y generar reporte con 305 respuestas (300 micro + 4 meso + 1 macro)
  """
  
  # ========================================================================
  # FASE 0: CARGA DE CONFIGURACIÓN
  # ========================================================================
  # SYNC
  
  PRINT "=== FASE 0: CARGA DE CONFIGURACIÓN ==="
  
  * monolith = load_json('questionnaire_monolith.json')
    * VERIFICAR: integrity_hash(monolith) == monolith['integrity']['monolith_hash']
    * SI hash_mismatch:
        RAISE "Monolith corrupted"
  
  * method_catalog = load_json('complete_canonical_catalog.json')
    * VERIFICAR: method_catalog['metadata']['total_methods'] == 416
  
  PRINT "✓ Monolith cargado: 305 preguntas"
  PRINT "✓ Catálogo cargado: 166 métodos únicos"
  
  
  # ========================================================================
  # FASE 1: INGESTIÓN DEL DOCUMENTO
  # ========================================================================
  # SYNC - Todo en esta fase es secuencial
  
  PRINT "=== FASE 1: INGESTIÓN DEL DOCUMENTO ==="
  
  # PASO 1.1: Cargar PDF crudo
  * raw_document = DI.DocumentLoader.load_pdf(pdf_path)
    """
    ENTRADA: pdf_path (string)
    PROCESO:
      - Leer bytes del PDF
      - Validar que es PDF válido
      - Extraer metadata básica (autor, fecha, páginas)
    SALIDA: RawDocument {bytes, metadata, num_pages}
    SYNC
    """
  
  PRINT "✓ PDF cargado: {raw_document.num_pages} páginas"
  
  
  # PASO 1.2: Extraer texto completo
  * full_text = DI.TextExtractor.extract_full_text(raw_document)
    """
    ENTRADA: RawDocument
    PROCESO:
      - Extraer texto de todas las páginas
      - Preservar estructura (párrafos, secciones)
      - Identificar headers/footers
    SALIDA: string (texto completo)
    SYNC
    """
  
  PRINT "✓ Texto extraído: {len(full_text)} caracteres"
  
  
  # PASO 1.3: Preprocesamiento completo
  * preprocessed_doc = DI.PreprocessingEngine.preprocess_document(raw_document)
    """
    ENTRADA: RawDocument
    PROCESO INTERNO (SYNC pero con llamadas a métodos existentes):
    
      # Sub-paso 1: Normalizar encoding
      * normalized_text = DI.PreprocessingEngine.normalize_encoding(full_text)
        LLAMA INTERNAMENTE A:
          ✓ PP.PolicyTextProcessor.normalize_unicode(full_text)
            # Limpia unicode, normaliza espacios
            SYNC
      
      # Sub-paso 2: Segmentar en oraciones
      ✓ sentences = PP.PolicyTextProcessor.segment_into_sentences(normalized_text)
        # Divide texto en oraciones con índices de ubicación
        SYNC
      
      # Sub-paso 3: Extraer todas las tablas del documento
      ✓ raw_tables = FV.PDETMunicipalPlanAnalyzer.extract_tables(raw_document)
        # Identifica y extrae todas las tablas del PDF
        SYNC
      
      # Sub-paso 4: Limpiar y clasificar tablas (PARALELO)
      ASYNC_START:
        PARA cada tabla en raw_tables (EN PARALELO):
          ✓ cleaned = FV.PDETMunicipalPlanAnalyzer._clean_dataframe(tabla)
            ASYNC
      WAIT
      
      ✓ classified_tables = FV.PDETMunicipalPlanAnalyzer._classify_tables(cleaned_tables)
        # Clasifica: actividades, presupuesto, cronograma, responsables
        SYNC
      
      # Sub-paso 5: Construir índices
      * document_indexes = BUILD_INDEXES(sentences, classified_tables)
        INCLUYE:
          - term_index: Map<palabra, [ubicaciones]>
          - numeric_index: Map<cifra, [ubicaciones]>
          - temporal_index: Map<fecha, [ubicaciones]>
          - table_index: Map<tipo_tabla, [tablas]>
        SYNC
      
      # Sub-paso 6: Ensamblar documento preprocesado
      RETURN PreprocessedDocument {
        document_id: generate_id(raw_document),
        raw_text: full_text,
        normalized_text: normalized_text,
        sentences: sentences,              # Lista de oraciones con metadata
        tables: classified_tables,         # Tablas limpias y clasificadas
        indexes: document_indexes,         # Índices para búsqueda rápida
        metadata: raw_document.metadata
      }
    
    SALIDA: PreprocessedDocument (inmutable, cache para todas las preguntas)
    SYNC (pero con paralelismo interno en limpieza de tablas)
    """
  
  PRINT "✓ Documento preprocesado:"
  PRINT "  - {len(preprocessed_doc.sentences)} oraciones"
  PRINT "  - {len(preprocessed_doc.tables)} tablas"
  PRINT "  - Índices construidos"
  
  
  # ========================================================================
  # FASE 2: EJECUCIÓN DE 300 MICRO PREGUNTAS
  # ========================================================================
  # ASYNC - Las 300 preguntas pueden procesarse en paralelo
  
  PRINT "=== FASE 2: EJECUCIÓN DE 300 MICRO PREGUNTAS ==="
  
  * all_micro_results = []
  
  ASYNC_START:
    PARA question_global EN range(1, 301) (EN PARALELO):
      
      * result = process_micro_question(
          question_global, 
          preprocessed_doc, 
          monolith, 
          method_catalog
        )
        # Ver función detallada más abajo
        ASYNC
      
      * all_micro_results.append(result)
  
  WAIT  # Esperar a que las 300 preguntas terminen
  
  PRINT "✓ 300 micro preguntas procesadas"
  PRINT "  - Tiempo promedio por pregunta: {avg_time}ms"
  PRINT "  - Tiempo total con paralelismo: {total_time}s"
  
  
  # ========================================================================
  # FASE 3: SCORING DE 300 MICRO PREGUNTAS
  # ========================================================================
  # ASYNC - Los 300 scorings pueden hacerse en paralelo
  
  PRINT "=== FASE 3: SCORING DE MICRO PREGUNTAS ==="
  
  * scoring_config = monolith['blocks']['scoring']
  * all_scored_results = []
  
  ASYNC_START:
    PARA micro_result EN all_micro_results (EN PARALELO):
      
      # Obtener metadata de la pregunta desde monolith
      * q_metadata = monolith['blocks']['micro_questions'][micro_result.question_global - 1]
      * scoring_modality = q_metadata['scoring_modality']  # TYPE_A, TYPE_B, etc.
      
      # Aplicar scoring
      * score = SC.MicroQuestionScorer.apply_scoring_modality(
          evidence=micro_result.evidence,
          modality=scoring_modality,
          config=scoring_config
        )
        ASYNC
      
      # Determinar nivel de calidad
      * quality_level = SC.MicroQuestionScorer.determine_quality_level(
          score=score,
          thresholds=scoring_config['quality_levels']
        )
        ASYNC
      
      * scored_result = ScoredResult {
          question_global: micro_result.question_global,
          base_slot: q_metadata['base_slot'],
          policy_area: q_metadata['policy_area'],
          dimension: q_metadata['dimension'],
          score: score,
          quality_level: quality_level,
          evidence: micro_result.evidence,
          raw_results: micro_result.raw_results
        }
      
      * all_scored_results.append(scored_result)
  
  WAIT
  
  PRINT "✓ 300 micro preguntas scored"
  
  # Estadísticas rápidas
  * stats = CALCULATE_STATS(all_scored_results)
  PRINT "  - EXCELENTE: {stats.excelente_count}"
  PRINT "  - BUENO: {stats.bueno_count}"
  PRINT "  - ACEPTABLE: {stats.aceptable_count}"
  PRINT "  - INSUFICIENTE: {stats.insuficiente_count}"
  
  
  # ========================================================================
  # FASE 4: AGREGACIÓN NIVEL 1 - DIMENSIONES
  # ========================================================================
  # ASYNC - Las 60 dimensiones (6×10) pueden procesarse en paralelo
  
  PRINT "=== FASE 4: AGREGACIÓN POR DIMENSIÓN ==="
  
  * all_dimension_scores = []
  
  ASYNC_START:
    PARA area_id EN ['P1', 'P2', ..., 'P10'] (EN PARALELO):
      PARA dimension_id EN ['D1', 'D2', ..., 'D6'] (EN PARALELO):
        
        # Obtener las 5 micro preguntas de esta dimensión/área
        * q_results_for_dim = FILTER(all_scored_results, {
            'policy_area': area_id,
            'dimension': dimension_id
          })
          # Debe retornar exactamente 5 resultados (Q1-Q5 de esa dim)
        
        # Agregar dimensión
        * dim_score = AG.DimensionAggregator.aggregate_dimension(
            dimension_id=dimension_id,
            area_id=area_id,
            q_results=q_results_for_dim,
            monolith=monolith
          )
          """
          PROCESO INTERNO (SYNC):
            # Extraer scores de las 5 preguntas
            scores = [r.score for r in q_results_for_dim]
            
            # Obtener pesos desde monolith
            weights = monolith['blocks']['dimension_weights'][dimension_id]
            
            # Calcular promedio ponderado
            weighted_avg = AG.DimensionAggregator.calculate_weighted_average(
              scores, weights
            )
            SYNC
            
            # Aplicar rubric thresholds
            quality = AG.DimensionAggregator.apply_rubric_thresholds(
              weighted_avg,
              monolith['blocks']['scoring']['rubric_matrices']['dimension_thresholds']
            )
            SYNC
            
            RETURN DimensionScore {
              dimension_id: dimension_id,
              area_id: area_id,
              score: weighted_avg,
              quality_level: quality,
              contributing_questions: [q.question_global for q in q_results_for_dim]
            }
          """
          ASYNC (toda la dimensión)
        
        * all_dimension_scores.append(dim_score)
  
  WAIT
  
  PRINT "✓ 60 dimensiones agregadas (6 dims × 10 áreas)"
  
  
  # ========================================================================
  # FASE 5: AGREGACIÓN NIVEL 2 - ÁREAS DE POLÍTICA
  # ========================================================================
  # ASYNC - Las 10 áreas pueden procesarse en paralelo
  
  PRINT "=== FASE 5: AGREGACIÓN POR ÁREA DE POLÍTICA ==="
  
  * all_area_scores = []
  
  ASYNC_START:
    PARA area_id EN ['P1', 'P2', ..., 'P10'] (EN PARALELO):
      
      # Obtener las 6 dimensiones de esta área
      * dim_scores_for_area = FILTER(all_dimension_scores, {
          'area_id': area_id
        })
        # Debe retornar exactamente 6 DimensionScores (D1-D6)
      
      # Agregar área
      * area_score = AG.AreaPolicyAggregator.aggregate_area(
          area_id=area_id,
          dim_scores=dim_scores_for_area,
          monolith=monolith
        )
        """
        PROCESO INTERNO (SYNC):
          # Normalizar scores de dimensiones
          normalized = AG.AreaPolicyAggregator.normalize_scores(dim_scores_for_area)
          SYNC
          
          # Aplicar rubric de área
          area_quality = APPLY_RUBRIC(
            normalized,
            monolith['blocks']['scoring']['rubric_matrices']['area_thresholds']
          )
          SYNC
          
          RETURN AreaScore {
            area_id: area_id,
            area_name: monolith['blocks']['niveles_abstraccion']['policy_areas'][area_id],
            score: AVERAGE(normalized),
            quality_level: area_quality,
            dimension_scores: dim_scores_for_area
          }
        """
        ASYNC (toda el área)
      
      * all_area_scores.append(area_score)
  
  WAIT
  
  PRINT "✓ 10 áreas de política agregadas"
  
  
  # ========================================================================
  # FASE 6: AGREGACIÓN NIVEL 3 - CLUSTERS (4 PREGUNTAS MESO)
  # ========================================================================
  # SYNC - Solo 4 clusters, no vale la pena paralelizar
  
  PRINT "=== FASE 6: AGREGACIÓN POR CLUSTER (MESO) ==="
  
  * cluster_definitions = monolith['blocks']['niveles_abstraccion']['clusters']
  * all_cluster_scores = []
  
  # CLUSTER 1: Seguridad y Paz (P2, P3, P7)
  * cluster1_areas = ['P2', 'P3', 'P7']
  * cluster1_area_scores = FILTER(all_area_scores, {'area_id': IN cluster1_areas})
  
  * cluster1_score = AG.ClusterAggregator.aggregate_cluster(
      cluster_id='CL01',
      area_scores=cluster1_area_scores,
      cluster_def=cluster_definitions['CL01'],
      monolith=monolith
    )
    """
    PROCESO INTERNO (SYNC):
      # Validar hermeticidad
      is_valid = AG.ClusterAggregator.validate_cluster_hermeticity(
        cluster_def,
        area_scores
      )
      SI NOT is_valid:
        RAISE "Cluster hermeticity violation"
      SYNC
      
      # Aplicar pesos específicos del cluster
      weighted_score = AG.ClusterAggregator.apply_cluster_weights(
        areas=cluster_def['areas'],
        scores=[a.score for a in area_scores],
        weights=cluster_def.get('weights', EQUAL_WEIGHTS)
      )
      SYNC
      
      # Analizar coherencia del cluster
      coherence = ANALYZE_COHERENCE(area_scores)
      SYNC
      
      RETURN ClusterScore {
        cluster_id: 'CL01',
        cluster_name: cluster_def['name'],
        areas: cluster1_areas,
        score: weighted_score,
        coherence: coherence,
        area_scores: area_scores
      }
    """
    SYNC
  
  * all_cluster_scores.append(cluster1_score)
  PRINT "✓ CL01 (Seguridad y Paz): {cluster1_score.score}"
  
  
  # CLUSTER 2: Grupos Poblacionales (P1, P5, P6)
  * cluster2_areas = ['P1', 'P5', 'P6']
  * cluster2_area_scores = FILTER(all_area_scores, {'area_id': IN cluster2_areas})
  * cluster2_score = AG.ClusterAggregator.aggregate_cluster(
      'CL02', cluster2_area_scores, cluster_definitions['CL02'], monolith
    )
    SYNC
  
  * all_cluster_scores.append(cluster2_score)
  PRINT "✓ CL02 (Grupos Poblacionales): {cluster2_score.score}"
  
  
  # CLUSTER 3: Territorio-Ambiente (P4, P8)
  * cluster3_areas = ['P4', 'P8']
  * cluster3_area_scores = FILTER(all_area_scores, {'area_id': IN cluster3_areas})
  * cluster3_score = AG.ClusterAggregator.aggregate_cluster(
      'CL03', cluster3_area_scores, cluster_definitions['CL03'], monolith
    )
    SYNC
  
  * all_cluster_scores.append(cluster3_score)
  PRINT "✓ CL03 (Territorio-Ambiente): {cluster3_score.score}"
  
  
  # CLUSTER 4: Derechos Sociales & Crisis (P9, P10)
  * cluster4_areas = ['P9', 'P10']
  * cluster4_area_scores = FILTER(all_area_scores, {'area_id': IN cluster4_areas})
  * cluster4_score = AG.ClusterAggregator.aggregate_cluster(
      'CL04', cluster4_area_scores, cluster_definitions['CL04'], monolith
    )
    SYNC
  
  * all_cluster_scores.append(cluster4_score)
  PRINT "✓ CL04 (Derechos Sociales): {cluster4_score.score}"
  
  PRINT "✓ 4 clusters MESO agregados (Q301-Q304 respondidas)"
  
  
  # ========================================================================
  # FASE 7: EVALUACIÓN MACRO (1 PREGUNTA HOLÍSTICA - Q305)
  # ========================================================================
  # SYNC - Solo 1 evaluación macro
  
  PRINT "=== FASE 7: EVALUACIÓN MACRO HOLÍSTICA ==="
  
  * macro_score = AG.MacroEvaluator.evaluate_holistic(
      cluster_scores=all_cluster_scores,
      monolith=monolith
    )
    """
    PROCESO INTERNO (SYNC con sub-análisis paralelos):
      
      # Sub-análisis en paralelo
      ASYNC_START:
        * coherence = AG.MacroEvaluator.assess_cross_cutting_coherence(
            all_cluster_scores
          )
          ASYNC
        
        * systemic_gaps = AG.MacroEvaluator.identify_systemic_gaps({
            'clusters': all_cluster_scores,
            'areas': all_area_scores,
            'dimensions': all_dimension_scores
          })
          ASYNC
      
      WAIT
      
      # Calcular índice de calidad global
      * global_quality_index = AG.MacroEvaluator.calculate_global_quality_index({
          'cluster_scores': [c.score for c in all_cluster_scores],
          'coherence': coherence,
          'gaps_penalty': len(systemic_gaps) * 0.05
        })
        SYNC
      
      RETURN MacroScore {
        question_global: 305,
        type: 'MACRO',
        global_quality_index: global_quality_index,
        cross_cutting_coherence: coherence,
        systemic_gaps: systemic_gaps,
        cluster_scores: all_cluster_scores
      }
    """
    SYNC (pero con paralelismo interno)
  
  PRINT "✓ Evaluación MACRO completada (Q305 respondida)"
  PRINT "  - Índice de calidad global: {macro_score.global_quality_index}/100"
  
  
  # ========================================================================
  # FASE 8: GENERACIÓN DE RECOMENDACIONES
  # ========================================================================
  # ASYNC - Recomendaciones de diferentes niveles en paralelo
  
  PRINT "=== FASE 8: GENERACIÓN DE RECOMENDACIONES ==="
  
  * all_recommendations = []
  
  ASYNC_START:
    
    # Nivel 1: Recomendaciones micro (300)
    PARA scored_result EN all_scored_results (EN PARALELO):
      * micro_recs = RA.RecommendationEngine.generate_micro_recommendations(
          q_result=scored_result,
          monolith=monolith
        )
        """
        Llama internamente a:
          ✓ FV.PDETMunicipalPlanAnalyzer.generate_recommendations()
          ✓ A1.PerformanceAnalyzer._generate_recommendations()
          ✓ A1.TextMiningEngine._generate_interventions()
          ✓ DB.OperationalizationAuditor._generate_optimal_remediations()
        """
        ASYNC
      * all_recommendations.extend(micro_recs)
    
    # Nivel 2-4: Dimension, Area, Cluster (en paralelo)
    PARA dim_score EN all_dimension_scores (EN PARALELO):
      * dim_recs = RA.RecommendationEngine.generate_dimension_recommendations(dim_score)
        ASYNC
      * all_recommendations.extend(dim_recs)
    
    PARA area_score EN all_area_scores (EN PARALELO):
      * area_recs = RA.RecommendationEngine.generate_area_recommendations(area_score)
        ASYNC
      * all_recommendations.extend(area_recs)
    
    PARA cluster_score EN all_cluster_scores (EN PARALELO):
      * cluster_recs = RA.RecommendationEngine.generate_cluster_recommendations(cluster_score)
        ASYNC
      * all_recommendations.extend(cluster_recs)
  
  WAIT
  
  # Nivel 5: Macro
  * macro_recs = RA.RecommendationEngine.generate_macro_recommendations(macro_score)
    SYNC
  * all_recommendations.extend(macro_recs)
  
  # Consolidar y priorizar
  * consolidated = RA.RecommendationEngine.consolidate_duplicate_recommendations(
      all_recommendations
    )
    SYNC
  
  * prioritized_recommendations = RA.RecommendationEngine.prioritize_recommendations(
      consolidated
    )
    SYNC
  
  PRINT "✓ Recomendaciones: {len(prioritized_recommendations)}"
  
  
  # ========================================================================
  # FASE 9: ENSAMBLADO DE REPORTE
  # ========================================================================
  # SYNC con sub-reportes ASYNC
  
  PRINT "=== FASE 9: ENSAMBLADO DE REPORTE ==="
  
  * complete_report = RA.ReportAssembler.assemble_full_report({
      'micro_results': all_scored_results,
      'dimension_scores': all_dimension_scores,
      'area_scores': all_area_scores,
      'cluster_scores': all_cluster_scores,
      'macro_score': macro_score,
      'recommendations': prioritized_recommendations
    })
    SYNC (con paralelismo interno)
  
  PRINT "✓ Reporte completo ensamblado"
  
  
  # ========================================================================
  # FASE 10: FORMATEO Y EXPORTACIÓN
  # ========================================================================
  # ASYNC - Diferentes formatos en paralelo
  
  PRINT "=== FASE 10: FORMATEO Y EXPORTACIÓN ==="
  
  ASYNC_START:
    * json_output = RA.ReportFormatter.format_as_json(complete_report)
      ASYNC
    * html_output = RA.ReportFormatter.format_as_html(complete_report)
      ASYNC
    * pdf_output = RA.ReportFormatter.format_as_pdf(complete_report)
      ASYNC
    * excel_output = RA.ReportFormatter.format_as_excel(complete_report)
      ASYNC
  WAIT
  
  * output_formats = {
      'json': json_output,
      'html': html_output,
      'pdf': pdf_output,
      'excel': excel_output
    }
  
  PRINT "✓ Formatos generados: JSON, HTML, PDF, Excel"
  
  
  # ========================================================================
  # RETORNO FINAL
  # ========================================================================
  
  PRINT "=== PROCESAMIENTO COMPLETO ==="
  PRINT "✓ 305 preguntas respondidas"
  PRINT "✓ Índice global: {macro_score.global_quality_index}/100"
  PRINT "✓ Tiempo total: {ELAPSED_TIME()}s"
  
  RETURN {
    'complete_report': complete_report,
    'output_formats': output_formats
  }

FIN process_development_plan
```

---

## FUNCIÓN AUXILIAR: process_micro_question

```python
* FUNCIÓN: process_micro_question(
    question_global: int,
    preprocessed_doc: PreprocessedDocument,
    monolith: dict,
    method_catalog: dict
  ) → QuestionResult
  """
  Procesa UNA micro pregunta ejecutando su catálogo de métodos
  """
  
  # PASO 1: Mapeo (SYNC)
  * base_index = (question_global - 1) % 30
  * base_slot = f"D{base_index // 5 + 1}-Q{base_index % 5 + 1}"
  * q_metadata = monolith['blocks']['micro_questions'][question_global - 1]
  
  * dimension_index = base_index // 5
  * question_in_dimension = base_index % 5
  * base_question = method_catalog['dimensions'][dimension_index]['questions'][question_in_dimension]
  * method_packages = base_question['p']
  * flow_spec = base_question['flow']
  
  
  # PASO 2: Construcción del DAG (SYNC)
  * execution_plan = OR.FlowController.build_execution_dag(flow_spec)
    SYNC
  
  * parallel_branches = OR.FlowController.identify_parallel_branches(execution_plan)
    SYNC
  
  
  # PASO 3: Ejecución (HÍBRIDO según DAG)
  * context = {
      'preprocessed_doc': preprocessed_doc,
      'question_global': question_global,
      'base_slot': base_slot,
      'results_cache': {}
    }
  
  * all_method_results = {}
  
  PARA node EN TOPOLOGICAL_SORT(execution_plan):
    
    * parallel_group = FIND_PARALLEL_GROUP(node, parallel_branches)
    
    SI parallel_group:
      # Ejecutar grupo en paralelo
      ASYNC_START:
        PARA parallel_node EN parallel_group (EN PARALELO):
          * result = EXECUTE_NODE(parallel_node, method_packages, context)
            ASYNC
          * all_method_results[parallel_node.id] = result
      WAIT
    
    SINO:
      # Ejecutar secuencialmente
      * result = EXECUTE_NODE(node, method_packages, context)
        SYNC
      * all_method_results[node.id] = result
  
  
  # PASO 4: Extracción de evidencias (SYNC)
  * evidence = EXTRACT_EVIDENCE(all_method_results, q_metadata)
    SYNC
  
  
  RETURN QuestionResult {
    question_global: question_global,
    base_slot: base_slot,
    evidence: evidence,
    raw_results: all_method_results
  }

FIN process_micro_question


# ============================================================================
# FUNCIÓN AUXILIAR: EXECUTE_NODE
# ============================================================================

FUNCIÓN: EXECUTE_NODE(node: DAGNode, method_packages: list, context: dict) → dict
  """
  Ejecuta todos los métodos de un nodo del DAG
  """
  
  * node_results = {}
  * package = FIND_PACKAGE(method_packages, node.file, node.types)
  
  PARA i, method_name EN ENUMERATE(package['m']):
    * method_type = package['t'][i]
    * priority = package['pr'][i]
    
    SI method_type IN node.types:
      TRY:
        * result = OR.MethodExecutor.execute_method(
            file=package['f'],
            class_name=package['c'],
            method=method_name,
            context=context
          )
          """
          MAPEA Y EJECUTA MÉTODOS EXISTENTES:
            ✓ PP.policy_processor (12 métodos)
            ✓ CD.contradiction_deteccion (44 métodos)
            ✓ FV.financiero_viabilidad_tablas (27 métodos)
            ✓ DB.derek_beach (43 métodos)
            ✓ EP.embedding_policy (9 métodos)
            ✓ A1.Analyzer_one (16 métodos)
            ✓ TC.teoria_cambio (14 métodos)
            ✓ SC.semantic_chunking_policy (1 método)
          """
          SYNC
        
        * node_results[method_name] = result
      
      CATCH error:
        SI priority == 3:  # Crítico
          RAISE error
        ELIF priority == 2:  # Importante
          LOG(error)
          CONTINUE
        ELSE:  # Complementario
          SKIP
  
  RETURN node_results

FIN EXECUTE_NODE
```

---

## RESUMEN DE CONCURRENCIA POR FASE

```
┌────────────────────────┬─────────────┬──────────────────┐
│ FASE                   │ MODO        │ PARALELISMO      │
├────────────────────────┼─────────────┼──────────────────┤
│ 0. Carga config        │ SYNC        │ Ninguno          │
│ 1. Ingestión           │ SYNC        │ (tablas interno) │
│ 2. 300 micro preguntas │ ASYNC       │ 300 paralelo     │
│    └─ Cada pregunta    │ HÍBRIDO     │ Según DAG        │
│ 3. 300 scorings        │ ASYNC       │ 300 paralelo     │
│ 4. 60 dimensiones      │ ASYNC       │ 60 paralelo      │
│ 5. 10 áreas            │ ASYNC       │ 10 paralelo      │
│ 6. 4 clusters          │ SYNC        │ Ninguno          │
│ 7. 1 macro             │ SYNC        │ (interno ASYNC)  │
│ 8. Recomendaciones     │ ASYNC       │ Multinivel       │
│ 9. Ensamblado          │ SYNC        │ (interno ASYNC)  │
│ 10. Formateo           │ ASYNC       │ 4 formatos       │
└────────────────────────┴─────────────┴──────────────────┘
```

---

## COMPONENTES NO EXISTENTES (*)

```
ARCHIVOS NUEVOS:
  * document_ingestion.py (DI) - 9 métodos
  * orchestration.py (OR) - 10 métodos
  * method_mapper.py (MM) - 3 métodos
  * scoring.py (SC) - 8 métodos
  * aggregation.py (AG) - 12 métodos

ARCHIVOS A REFACTORIZAR:
  ⚠ report_assembly.py (RA) - 18 métodos nuevos

TOTAL MÉTODOS NUEVOS: ~56
TOTAL MÉTODOS EXISTENTES: 166
```
