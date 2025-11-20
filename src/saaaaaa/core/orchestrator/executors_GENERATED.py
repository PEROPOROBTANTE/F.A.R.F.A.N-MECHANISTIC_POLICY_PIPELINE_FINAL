# ============================================================================
# ALL 30 EXECUTORS - CANONICAL METHOD SEQUENCES + ANSWER ASSEMBLY
# Generated from canonical_executor_catalog.json
# ============================================================================

class D1Q1_Executor(AdvancedDataFlowExecutor):
    """D1-Q1: ¿El diagnóstico presenta datos numéricos (tasas de VBG, porcentajes de participa"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q2_Executor(AdvancedDataFlowExecutor):
    """D1-Q2: ¿El texto dimensiona el problema de la desigualdad de género cuantificando la br"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q3_Executor(AdvancedDataFlowExecutor):
    """D1-Q3: ¿Se identifican en el Plan Plurianual de Inversiones (PPI) o en tablas presupues"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q4_Executor(AdvancedDataFlowExecutor):
    """D1-Q4: ¿El PDM describe las capacidades para gestionar la política de género, mencionan"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q5_Executor(AdvancedDataFlowExecutor):
    """D1-Q5: ¿El plan justifica su alcance en materia de género mencionando el marco legal (e"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q1_Executor(AdvancedDataFlowExecutor):
    """D2-Q1: ¿Las actividades para la equidad de género se presentan en un formato estructura"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q2_Executor(AdvancedDataFlowExecutor):
    """D2-Q2: ¿La descripción de las actividades de género detalla el instrumento ('mediante t"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q3_Executor(AdvancedDataFlowExecutor):
    """D2-Q3: ¿El PDM vincula explícitamente las actividades propuestas con las 'causas raíz' """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q4_Executor(AdvancedDataFlowExecutor):
    """D2-Q4: ¿El plan identifica posibles riesgos, 'obstáculos' o 'barreras' en la implementa"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q5_Executor(AdvancedDataFlowExecutor):
    """D2-Q5: ¿El conjunto de actividades de género demuestra una estrategia coherente? Se deb"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q1_Executor(AdvancedDataFlowExecutor):
    """D3-Q1: ¿Los indicadores de producto para género (ej. mujeres capacitadas, kits entregad"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q2_Executor(AdvancedDataFlowExecutor):
    """D3-Q2: ¿Las metas de los productos de género (ej. 'cobertura del 15% de mujeres rurales"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q3_Executor(AdvancedDataFlowExecutor):
    """D3-Q3: ¿Los productos de género tienen trazabilidad presupuestal (vinculados a códigos """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q4_Executor(AdvancedDataFlowExecutor):
    """D3-Q4: ¿Existe una relación factible entre la actividad (ej. 'un taller de formación') """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q5_Executor(AdvancedDataFlowExecutor):
    """D3-Q5: ¿El PDM explica cómo los productos de la política de género (ej. 'mujeres capaci"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q1_Executor(AdvancedDataFlowExecutor):
    """D4-Q1: ¿Los indicadores de resultado para género (ej. 'tasa de participación política',"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q2_Executor(AdvancedDataFlowExecutor):
    """D4-Q2: ¿Se explicita la cadena causal que lleva a los resultados de género, mencionando"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q3_Executor(AdvancedDataFlowExecutor):
    """D4-Q3: ¿La ambición de las metas de resultado en materia de género (ej. 'reducir la bre"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q4_Executor(AdvancedDataFlowExecutor):
    """D4-Q4: ¿Los resultados propuestos para la igualdad de género (ej. 'aumento de la autono"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q5_Executor(AdvancedDataFlowExecutor):
    """D4-Q5: ¿El plan declara la alineación de sus resultados de género con marcos superiores"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q1_Executor(AdvancedDataFlowExecutor):
    """D5-Q1: ¿El PDM define 'impactos' o 'transformaciones estructurales' de largo plazo en e"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q2_Executor(AdvancedDataFlowExecutor):
    """D5-Q2: ¿Se utilizan 'índices' (ej. Índice de Equidad de Género) o 'proxies' para medir """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q3_Executor(AdvancedDataFlowExecutor):
    """D5-Q3: Cuando un impacto en género es difícil de medir (ej. 'cambio en patrones cultura"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q4_Executor(AdvancedDataFlowExecutor):
    """D5-Q4: ¿Los impactos en género se alinean con marcos nacionales/globales y consideran '"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q5_Executor(AdvancedDataFlowExecutor):
    """D5-Q5: ¿La ambición del impacto para la igualdad de género es realista? Se debe buscar """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q1_Executor(AdvancedDataFlowExecutor):
    """D6-Q1: ¿Existe una 'teoría de cambio' explícita para la política de género, preferiblem"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q1 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q2_Executor(AdvancedDataFlowExecutor):
    """D6-Q2: ¿Los saltos en la cadena causal de género son proporcionales y realistas (ej. un"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q2 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q3_Executor(AdvancedDataFlowExecutor):
    """D6-Q3: ¿El plan reconoce 'inconsistencias' en su lógica causal para género y propone 'p"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q3 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q4_Executor(AdvancedDataFlowExecutor):
    """D6-Q4: ¿Se describe un sistema de monitoreo para la política de género que incluya 'mec"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q4 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q5_Executor(AdvancedDataFlowExecutor):
    """D6-Q5: ¿La lógica causal para la equidad de género considera el contexto, reconociendo """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q5 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []

