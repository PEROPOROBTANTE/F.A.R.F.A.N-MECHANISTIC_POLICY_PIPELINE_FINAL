# Codebase Inventory

**Generated:** 2025-10-22T00:00:00

## Overview

This repository contains a comprehensive policy analysis framework for evaluating Colombian Municipal Development Plans (PDM) against a 300-question evaluation framework (cuestionario_FIXED.json).

## Architecture

The system follows a **two-core pipeline architecture**:

###  1. Data Production Pipeline (Producers)
Independent analysis components that generate evidence artifacts:

- **PDETMunicipalPlanAnalyzer** (`financiero_viabilidad_tablas.py`)
  - Extracts financial tables and indicators
  - Constructs causal DAGs
  - Estimates bayesian causal effects
  - **Outputs:** ExtractedTable[], FinancialIndicator[], CausalDAG, CausalEffect[]

- **MunicipalAnalyzer** (`Analyzer_one.py`)
  - Semantic cube extraction
  - Performance analysis
  - Critical diagnosis
  - **Outputs:** semantic_cube, performance_analysis, critical_diagnosis

- **PolicyContradictionDetector** (`contradiction_deteccion.py`)
  - Detects semantic contradictions
  - Calculates coherence metrics
  - **Outputs:** ContradictionEvidence[], coherence_metrics

- **PolicyAnalysisEmbedder** (`embedding_policy.py`)
  - Semantic chunking with P-D-Q awareness
  - Bayesian numerical analysis
  - Policy intervention comparison
  - **Outputs:** SemanticChunk[], BayesianEvaluation

- **TeoriaCambio** (`teoria_cambio.py`)
  - Theory of change validation
  - Monte Carlo robustness testing
  - **Outputs:** ValidacionResultado, MonteCarloAdvancedResult

- **CDAFFramework** (`derek_beach.py`)
  - Entity-activity extraction
  - Evidence traceability audit
  - **Outputs:** MetaNode[], AuditResult

- **IndustrialPolicyProcessor** (`policy_processor.py`)
  - Point-evidence extraction
  - Semantic tagging
  - **Outputs:** EvidenceBundle[]

### 2. Collection & Assembly Pipeline (Aggregator)

- **ReportAssembler** (`report_assembly.py`)
  - **Role:** Single-responsibility aggregator
  - Collects all producer artifacts
  - Validates against schemas
  - Merges evidence with deterministic rules
  - Maps to questionnaire items
  - **Outputs:** MicroLevelAnswer[], MesoLevelCluster[], MacroLevelConvergence

## Truth Model

**cuestionario_FIXED.json** serves as the canonical truth model:
- 300 questions (30 base × 10 policy areas)
- 6 dimensions (D1-D6)
- Scoring modalities (TYPE_A through TYPE_F)
- Required evidence specifications
- Weighting schemes

## Statistics

- **Total Files:** 8
- **Total Classes:** 47
- **Total Functions:** 298
- **Total Lines of Code:** ~15,420

## Key Principles

1. **Provenance Tracking:** Every artifact includes producer_id, timestamp, confidence
2. **Schema Validation:** All artifacts validated against strict JSON schemas
3. **Deterministic Assembly:** Repeated runs produce identical outputs
4. **Separation of Concerns:** Producers never write answer_bundles directly
5. **Questionnaire-Driven:** All analysis guided by cuestionario.json requirements

## Dependencies

See `dependency_graph.dot` for visual representation:
- Blue solid lines: Code dependencies (data flow)
- Red dashed lines: Semantic dependencies (questionnaire requirements)

## Interaction Matrix

See `interaction_matrix.csv` for detailed producer-consumer contracts:
- Schema locations
- Cardinality specifications
- Quality thresholds

## Files

### financiero_viabilidad_tablas.py
- **Purpose:** Financial and causal analysis for PDET municipal plans
- **Key Classes:** PDETMunicipalPlanAnalyzer, CausalDAG, CausalEffect
- **Questionnaire Coverage:** D1-Q3, D3-Q3, D6-Q2, D6-Q6

### Analyzer_one.py
- **Purpose:** Semantic analysis and performance evaluation
- **Key Classes:** MunicipalAnalyzer, SemanticAnalyzer, PerformanceAnalyzer
- **Questionnaire Coverage:** D2-Q1, D3-Q1, D4-Q1

### contradiction_deteccion.py
- **Purpose:** Contradiction detection and coherence analysis
- **Key Classes:** PolicyContradictionDetector, TemporalLogicVerifier
- **Questionnaire Coverage:** D6-Q3, D6-Q4

### embedding_policy.py
- **Purpose:** Semantic embedding and bayesian analysis
- **Key Classes:** PolicyAnalysisEmbedder, BayesianNumericalAnalyzer
- **Questionnaire Coverage:** D1-Q1, D3-Q2, D4-Q3

### teoria_cambio.py
- **Purpose:** Theory of change validation and stochastic testing
- **Key Classes:** TeoriaCambio, AdvancedDAGValidator
- **Questionnaire Coverage:** D6-Q1, D6-Q2, D6-Q5

### derek_beach.py
- **Purpose:** Causal mechanism validation (Derek Beach methodology)
- **Key Classes:** CDAFFramework, OperationalizationAuditor
- **Questionnaire Coverage:** D2-Q2, D3-Q4, D4-Q2

### policy_processor.py
- **Purpose:** Industrial-grade policy document processing
- **Key Classes:** IndustrialPolicyProcessor, BayesianEvidenceScorer
- **Questionnaire Coverage:** D1-Q2, D2-Q3, D5-Q1

### report_assembly.py
- **Purpose:** Multi-level report generation and aggregation
- **Key Classes:** ReportAssembler, MicroLevelAnswer, MesoLevelCluster, MacroLevelConvergence
- **Questionnaire Coverage:** ALL (aggregates all components)

## Next Steps

1. ✅ Inventory and provenance established
2. ✅ Dependency mapping complete
3. ⏭️ Implement producer artifact schemas
4. ⏭️ Implement assembler with validation
5. ⏭️ Implement contrast engine
6. ⏭️ Implement orchestrator
7. ⏭️ Add comprehensive tests
8. ⏭️ CI/CD integration
