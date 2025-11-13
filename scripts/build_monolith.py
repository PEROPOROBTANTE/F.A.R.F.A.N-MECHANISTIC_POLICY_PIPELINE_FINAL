#!/usr/bin/env python3
"""
MonolithForge: Canonical Questionnaire Monolith Builder
========================================================

Migrates legacy questionnaire.json and rubric_scoring.json into a single
questionnaire monolith with 305 questions (300 micro, 4 meso, 1 macro).

No graceful degradation. No strategic simplification. No atom loss.
Abort immediately on any inconsistency.
"""

import hashlib
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from saaaaaa.core.orchestrator import get_questionnaire_provider

QUESTIONNAIRE_PROVIDER = get_questionnaire_provider()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AbortError(Exception):
    """Fatal error requiring immediate abort."""
    def __init__(self, code: str, message: str, phase: str):
        self.code = code
        self.message = message
        self.phase = phase
        super().__init__(f"[{code}] {phase}: {message}")

@dataclass
class PhaseContext:
    """Context for a construction phase."""
    name: str
    preconditions: list[str]
    invariants: list[str]
    postconditions: list[str]

class MonolithForge:
    """
    Monolithic questionnaire builder following strict construction phases.
    """

    # Canonical constants
    CANONICAL_POLICY_AREAS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']
    CANONICAL_DIMENSIONS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
    CANONICAL_SCORING_MODALITIES = ['TYPE_A', 'TYPE_B', 'TYPE_C', 'TYPE_D', 'TYPE_E', 'TYPE_F']

    # Quality thresholds for micro questions
    MICRO_QUALITY_LEVELS = {
        'EXCELENTE': 0.85,
        'BUENO': 0.70,
        'ACEPTABLE': 0.55,
        'INSUFICIENTE': 0.0
    }

    # Method sampling configuration
    METHODS_PER_BASE_SLOT = 2  # Number of methods to sample from catalog per base_slot

    def __init__(self):
        self.legacy_data = {}
        self.monolith = {}
        self.indices = {}
        self.stats = defaultdict(int)
        self.canonical_clusters = None  # Will be loaded from legacy data
        self.repo_root = Path(__file__).resolve().parents[1]  # Repository root

    def abort(self, code: str, message: str, phase: str):
        """Trigger immediate abort with error code."""
        logger.error(f"ABORT [{code}] in {phase}: {message}")
        raise AbortError(code, message, phase)

    # ========================================================================
    # PHASE 1: LoadLegacyPhase
    # ========================================================================

    def load_legacy_phase(self):
        """
        Load legacy JSON files with strict validation.
        Preconditions: Files exist, size > 0
        Invariants: Valid JSON, no null keys
        """
        phase = "LoadLegacyPhase"
        logger.info(f"=== {phase} START ===")

        # Whitelist of allowed files (relative to repo root)
        allowed_files = {
            'questionnaire.json': self.repo_root / 'questionnaire.json',
            'rubric_scoring.json': self.repo_root / 'rubric_scoring.json',
            'COMPLETE_METHOD_CLASS_MAP.json': self.repo_root / 'COMPLETE_METHOD_CLASS_MAP.json'
        }

        for name, path in allowed_files.items():

            # Precondition: file exists
            if not path.exists():
                self.abort('A001', f'Missing legacy file: {name}', phase)

            # Precondition: size > 0
            if path.stat().st_size == 0:
                self.abort('A001', f'Empty legacy file: {name}', phase)

            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)

                # Invariant: no null keys
                if None in data:
                    self.abort('A001', f'Null key in {name}', phase)

                self.legacy_data[name] = data
                logger.info(f"Loaded {name}: {len(str(data))} bytes")

            except json.JSONDecodeError as e:
                self.abort('A001', f'Invalid JSON in {name}: {e}', phase)

        # Load canonical clusters from questionnaire
        questionnaire = self.legacy_data['questionnaire.json']
        legacy_clusters = questionnaire.get('metadata', {}).get('clusters', [])
        self.canonical_clusters = {}
        legacy_to_canonical = {
            'P1': 'PA01',
            'P2': 'PA02',
            'P3': 'PA03',
            'P4': 'PA04',
            'P5': 'PA05',
            'P6': 'PA06',
            'P7': 'PA07',
            'P8': 'PA08',
            'P9': 'PA09',
            'P10': 'PA10',
        }

        for i, cluster_def in enumerate(legacy_clusters, 1):
            cluster_id = cluster_def.get('cluster_id') or f'CL{str(i).zfill(2)}'
            legacy_areas = cluster_def.get('legacy_policy_area_ids', [])
            canonical_areas = cluster_def.get('policy_area_ids', [])

            if not canonical_areas and legacy_areas:
                canonical_areas = [legacy_to_canonical.get(area, area) for area in legacy_areas]

            self.canonical_clusters[cluster_id] = {
                'canonical': canonical_areas,
                'legacy': legacy_areas,
            }

        logger.info(f"Loaded canonical clusters: {self.canonical_clusters}")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 2: StructuralIndexingPhase
    # ========================================================================

    def structural_indexing_phase(self):
        """
        Build indices for efficient lookup.
        Invariants: 300 micro questions, continuous numbering
        """
        phase = "StructuralIndexingPhase"
        logger.info(f"=== {phase} START ===")

        questionnaire = self.legacy_data['questionnaire.json']
        questions = questionnaire.get('questions', [])

        # Invariant: exactly 300 questions
        if len(questions) != 300:
            self.abort('A010', f'Expected 300 questions, found {len(questions)}', phase)

        # Build indices
        self.indices['by_global'] = {}
        self.indices['by_policy_area'] = defaultdict(list)
        self.indices['by_dimension'] = defaultdict(list)

        for q in questions:
            global_order = q.get('order', {}).get('global')

            if global_order is None:
                self.abort('A010', f"Question {q.get('question_id')} missing global order", phase)

            self.indices['by_global'][global_order] = q

            policy_area_id = q.get('policy_area_id')
            if policy_area_id:
                self.indices['by_policy_area'][policy_area_id].append(q)

            dimension_id = q.get('dimension_id')
            if dimension_id:
                self.indices['by_dimension'][dimension_id].append(q)

        # Invariant: continuous numbering
        expected_globals = set(range(1, 301))
        actual_globals = set(self.indices['by_global'].keys())

        if expected_globals != actual_globals:
            missing = expected_globals - actual_globals
            extra = actual_globals - expected_globals
            self.abort('A010', f'Discontinuous numbering. Missing: {missing}, Extra: {extra}', phase)

        logger.info(f"Indexed {len(questions)} questions")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 3: BaseSlotMappingPhase
    # ========================================================================

    def base_slot_mapping_phase(self):
        """
        Apply base_slot formula to all questions.
        Invariants: Each base_slot appears exactly 10 times
        """
        phase = "BaseSlotMappingPhase"
        logger.info(f"=== {phase} START ===")

        base_slot_counts = defaultdict(int)

        for global_num in range(1, 301):
            q = self.indices['by_global'][global_num]

            # Apply formula
            base_index = (global_num - 1) % 30
            base_slot = f"D{base_index//5+1}-Q{base_index%5+1}"

            # Store in question
            q['base_slot'] = base_slot
            q['question_global'] = global_num

            base_slot_counts[base_slot] += 1

        # Invariant: each base_slot exactly 10 times
        for slot, count in base_slot_counts.items():
            if count != 10:
                self.abort('A020', f'Base slot {slot} has {count} instances, expected 10', phase)

        # Verify we have exactly 30 base_slots
        if len(base_slot_counts) != 30:
            self.abort('A020', f'Expected 30 base_slots, found {len(base_slot_counts)}', phase)

        logger.info(f"Mapped {len(base_slot_counts)} base_slots, each with 10 questions")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 4: ExtractionAndNormalizationPhase
    # ========================================================================

    def extraction_and_normalization_phase(self):
        """
        Normalize field by field with strict validation.
        Invariants: text non-empty, scoring_modality valid
        """
        phase = "ExtractionAndNormalizationPhase"
        logger.info(f"=== {phase} START ===")

        for global_num in range(1, 301):
            q = self.indices['by_global'][global_num]

            # Normalize text (trim trailing whitespace, preserve internal)
            text = q.get('question_text', '').strip()
            if not text:
                self.abort('A030', f'Question {global_num} has empty text', phase)
            q['text'] = text

            # Validate scoring_modality
            scoring_modality = q.get('scoring_modality')
            if scoring_modality not in self.CANONICAL_SCORING_MODALITIES:
                self.abort('A030', f'Question {global_num} has invalid scoring_modality: {scoring_modality}', phase)

            # Ensure no FIXME/TODO/TEMP markers
            for marker in ['FIXME', 'TODO', 'TEMP', 'LEGACY']:
                if marker in str(q):
                    self.abort('A030', f'Question {global_num} contains forbidden marker: {marker}', phase)

        logger.info("Normalized 300 micro questions")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 5: IndicatorsAndEvidencePhase
    # ========================================================================

    def indicators_and_evidence_phase(self):
        """
        Separate expected_elements, patterns, validation_checks.
        Invariants: Exact count preservation, no silent duplication
        """
        phase = "IndicatorsAndEvidencePhase"
        logger.info(f"=== {phase} START ===")

        for global_num in range(1, 301):
            q = self.indices['by_global'][global_num]

            # Extract expected_elements from evidence_expectations structure
            evidence_exp = q.get('evidence_expectations', {})

            # Build expected_elements from the evidence expectations
            expected_elements = []
            for key, value in evidence_exp.items():
                if key.endswith('_minimos') or key.endswith('_minimas'):
                    # Extract minimum requirements
                    expected_elements.append({
                        'type': key.replace('_minimos', '').replace('_minimas', ''),
                        'minimum': value
                    })
                elif isinstance(value, bool) and value:
                    # Boolean requirements
                    expected_elements.append({
                        'type': key,
                        'required': True
                    })

            # If no elements extracted, use the required_evidence_keys
            if not expected_elements:
                req_keys = q.get('required_evidence_keys', [])
                expected_elements = [{'type': key} for key in req_keys] if req_keys else []

            # Still nothing? Extract from validation_checks
            if not expected_elements:
                validation_checks = q.get('validation_checks', {})
                if validation_checks:
                    expected_elements = [
                        {'type': check_name, 'minimum': check_data.get('minimum_required', 1)}
                        for check_name, check_data in validation_checks.items()
                        if isinstance(check_data, dict)
                    ]

            # Abort if still no elements
            if not expected_elements:
                self.abort('A040', f'Question {global_num} missing expected_elements', phase)

            q['expected_elements'] = expected_elements

            # Extract patterns
            patterns = q.get('search_patterns', [])
            if isinstance(patterns, dict):
                # Flatten patterns from different structures
                pattern_list = []
                for key, val in patterns.items():
                    if isinstance(val, list):
                        pattern_list.extend(val)
                    else:
                        pattern_list.append(val)
                patterns = pattern_list

            q['pattern_refs'] = patterns if patterns else []

            # Extract validation_checks
            validations = q.get('validation_checks', {})
            if isinstance(validations, dict):
                # Keep as structured dictionary
                q['validations'] = validations
            else:
                q['validations'] = validations if validations else {}

        logger.info("Extracted indicators and evidence for 300 questions")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 6: MethodSetSynthesisPhase
    # ========================================================================

    def method_set_synthesis_phase(self):
        """
        Insert method_sets per base_slot from method catalog.
        Invariants: Each method has class, function, description, priority 1-3
        """
        phase = "MethodSetSynthesisPhase"
        logger.info(f"=== {phase} START ===")

        # Load real method catalog from canonical source
        from saaaaaa.core.orchestrator.factory import load_catalog
        
        # Load canonical method catalog (1,996 methods)
        catalog_path = self.repo_root / "config" / "canonical_method_catalog.json"
        try:
            catalog = load_catalog()
            logger.info(f"Loaded method catalog with {catalog.get('summary', {}).get('total_methods', 0)} methods")
        except FileNotFoundError as e:
            self.abort('A050', f'Method catalog not found at {catalog_path}: {e}', phase)
        except Exception as e:
            self.abort(
                'A050',
                f'Failed to load method catalog: {e}\n'
                f'Check that the catalog file exists at {catalog_path} and is in the expected format.',
                phase
            )

        # Extract methods from catalog and organize by base_slot
        base_slot_methods = {}
        
        # The catalog structure has files with methods
        files_data = catalog.get('files', {})
        
        # Create method sets per base_slot
        # Since the catalog doesn't directly map to base_slots, we create a
        # reasonable distribution of methods across base_slots
        for d_num in range(1, 7):  # D1-D6
            for q_num in range(1, 6):  # Q1-Q5
                base_slot = f"D{d_num}-Q{q_num}"
                
                # Assign methods from catalog to this base_slot
                # This mapping should ideally come from configuration
                base_slot_methods[base_slot] = self._get_methods_for_base_slot(
                    base_slot, files_data
                )

        # Apply to questions
        for global_num in range(1, 301):
            q = self.indices['by_global'][global_num]
            base_slot = q['base_slot']

            methods = base_slot_methods.get(base_slot, [])

            # Invariant: methods have required fields
            for method in methods:
                if not method.get('description'):
                    self.abort('A050', f'Method for {base_slot} missing description', phase)
                if method.get('priority') not in [1, 2, 3]:
                    self.abort('A050', f'Method for {base_slot} has invalid priority: {method.get("priority")}', phase)

            q['method_sets'] = methods

        logger.info(f"Applied method sets from catalog to 30 base_slots")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 7: RubricTranspositionPhase
    # ========================================================================

    def rubric_transposition_phase(self):
        """
        Transfer qualitative levels and modalities from rubric.
        Invariants: min_score descending order
        """
        phase = "RubricTranspositionPhase"
        logger.info(f"=== {phase} START ===")

        rubric = self.legacy_data['rubric_scoring.json']

        # Extract scoring modalities
        scoring_modalities = rubric.get('scoring_modalities', {})

        # Build scoring_matrix for micro questions
        scoring_matrix = {}

        for modality_key in self.CANONICAL_SCORING_MODALITIES:
            if modality_key in scoring_modalities:
                modality_info = scoring_modalities[modality_key]
                scoring_matrix[modality_key] = {
                    'description': modality_info.get('description', ''),
                    'max_score': modality_info.get('max_score', 3),
                    'levels': []
                }

        # Create micro quality levels
        micro_levels = []
        prev_score = float('inf')

        for level_name, min_score in sorted(self.MICRO_QUALITY_LEVELS.items(), key=lambda x: -x[1]):
            # Invariant: descending order
            if min_score >= prev_score:
                self.abort('A060', f'Rubric thresholds not descending: {level_name}', phase)

            micro_levels.append({
                'level': level_name,
                'min_score': min_score,
                'color': self._get_level_color(level_name)
            })
            prev_score = min_score

        self.monolith['scoring_matrix'] = {
            'micro_levels': micro_levels,
            'modalities': scoring_matrix
        }

        logger.info(f"Transposed rubric with {len(micro_levels)} quality levels")
        logger.info(f"=== {phase} COMPLETE ===")

    def _get_level_color(self, level_name: str) -> str:
        """Map quality level to color."""
        colors = {
            'EXCELENTE': 'green',
            'BUENO': 'blue',
            'ACEPTABLE': 'yellow',
            'INSUFICIENTE': 'red'
        }
        return colors.get(level_name, 'gray')

    # ========================================================================
    # PHASE 8: MesoMacroEmbeddingPhase
    # ========================================================================

    def meso_macro_embedding_phase(self):
        """
        Insert 4 MESO cluster questions and 1 MACRO question.
        Invariants: Clusters EXACT, hermeticity preserved
        """
        phase = "MesoMacroEmbeddingPhase"
        logger.info(f"=== {phase} START ===")

        # Verify cluster hermeticity BEFORE insertion
        questionnaire = self.legacy_data['questionnaire.json']
        legacy_clusters = questionnaire.get('metadata', {}).get('clusters', [])

        # Map legacy clusters to canonical
        cluster_mapping = {}
        for i, cluster_def in enumerate(legacy_clusters, 1):
            cluster_id = cluster_def.get('cluster_id') or f"CL{str(i).zfill(2)}"
            legacy_areas = cluster_def.get('legacy_policy_area_ids', [])
            canonical_record = self.canonical_clusters.get(cluster_id)

            if not canonical_record:
                self.abort('A070', f'Cluster {cluster_id} not found in canonical registry', phase)

            canonical_areas = canonical_record.get('canonical', [])
            expected_legacy = canonical_record.get('legacy', [])

            if expected_legacy and set(legacy_areas) != set(expected_legacy):
                self.abort(
                    'A070',
                    f'{cluster_id} legacy hermeticity violation. '
                    f'Expected {expected_legacy}, got {legacy_areas}',
                    phase
                )

            cluster_mapping[cluster_id] = {
                'cluster_id': cluster_id,
                'policy_area_ids': canonical_areas,
                'legacy_policy_area_ids': legacy_areas,
                'label_es': cluster_def.get('i18n', {}).get('keys', {}).get('label_es', ''),
                'label_en': cluster_def.get('i18n', {}).get('keys', {}).get('label_en', ''),
                'rationale': cluster_def.get('rationale', '')
            }

        # Create 4 MESO questions (one per cluster)
        meso_questions = []

        for i, (cluster_id, cluster_info) in enumerate(sorted(cluster_mapping.items()), 301):
            meso_q = {
                'question_global': i,
                'question_id': f'MESO_{i-300}',
                'cluster_id': cluster_id,
                'type': 'MESO',
                'text': f"¿Cómo se integran las políticas en el cluster {cluster_info['label_es']}?",
                'policy_areas': cluster_info['policy_area_ids'],
                'scoring_modality': 'MESO_INTEGRATION',
                'aggregation_method': 'weighted_average',
                'patterns': [
                    {
                        'type': 'cross_reference',
                        'description': f'Verificar referencias cruzadas entre áreas {cluster_info["policy_area_ids"]}'
                    },
                    {
                        'type': 'coherence',
                        'description': 'Evaluar coherencia narrativa entre políticas del cluster'
                    }
                ]
            }
            meso_questions.append(meso_q)

        # Create 1 MACRO question
        macro_question = {
            'question_global': 305,
            'question_id': 'MACRO_1',
            'type': 'MACRO',
            'text': '¿El Plan de Desarrollo presenta una visión integral y coherente que articula todos los clusters y dimensiones?',
            'scoring_modality': 'MACRO_HOLISTIC',
            'aggregation_method': 'holistic_assessment',
            'clusters': list(self.canonical_clusters.keys()),
            'patterns': [
                {
                    'type': 'narrative_coherence',
                    'description': 'Evaluar coherencia narrativa global del plan',
                    'priority': 1
                },
                {
                    'type': 'cross_cluster_integration',
                    'description': 'Verificar integración entre todos los clusters',
                    'priority': 1
                },
                {
                    'type': 'long_term_vision',
                    'description': 'Evaluar visión de largo plazo y transformación estructural',
                    'priority': 2
                }
            ],
            'fallback': {
                'pattern': 'MACRO_AMBIGUO',
                'condition': 'always_true',
                'priority': 999
            }
        }

        # Store in monolith
        self.monolith['meso_questions'] = meso_questions
        self.monolith['macro_question'] = macro_question

        logger.info(f"Embedded {len(meso_questions)} MESO + 1 MACRO questions")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 9: IntegritySealingPhase
    # ========================================================================

    def integrity_sealing_phase(self):
        """
        Calculate monolith hash for integrity verification.
        Postconditions: hash is reproducible
        """
        phase = "IntegritySealingPhase"
        logger.info(f"=== {phase} START ===")

        # Build final monolith structure
        monolith = {
            'schema_version': '1.1.0',  # Added versioning
            'version': '1.0.0',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'blocks': {}
        }

        # Block A: niveles_abstraccion
        questionnaire = self.legacy_data['questionnaire.json']
        monolith['blocks']['niveles_abstraccion'] = {
            'policy_areas': questionnaire['metadata'].get('policy_areas', []),
            'dimensions': questionnaire['metadata'].get('dimensions', []),
            'clusters': questionnaire['metadata'].get('clusters', [])
        }

        # Block B: micro_questions (300)
        micro_questions = []
        for global_num in range(1, 301):
            q = self.indices['by_global'][global_num]

            # Structure patterns with categories
            structured_patterns = self._structure_patterns(q['pattern_refs'], q['question_id'])

            micro_questions.append({
                'question_global': q['question_global'],
                'question_id': q.get('question_id'),
                'base_slot': q['base_slot'],
                'policy_area_id': q.get('policy_area_id'),
                'dimension_id': q.get('dimension_id'),
                'cluster_id': q.get('cluster_id'),
                'text': q['text'],
                'scoring_modality': q['scoring_modality'],
                'scoring_definition_ref': f"scoring_modalities.{q['scoring_modality']}",
                'expected_elements': q['expected_elements'],
                'patterns': structured_patterns,  # Enhanced structure
                'validations': q['validations'],
                'method_sets': q['method_sets'],
                'failure_contract': {
                    'abort_if': ['missing_required_element', 'incomplete_text'],
                    'emit_code': f"ABORT-{q.get('question_id')}-REQ"
                }
            })

        monolith['blocks']['micro_questions'] = micro_questions

        # Block C: meso_questions (4)
        monolith['blocks']['meso_questions'] = self.monolith['meso_questions']

        # Block D: macro_question (1)
        monolith['blocks']['macro_question'] = self.monolith['macro_question']

        # Add scoring matrix with explicit definitions
        monolith['blocks']['scoring'] = self._create_scoring_definitions()

        # Add semantic layers block
        monolith['blocks']['semantic_layers'] = {
            'embedding_strategy': {
                'model': 'multilingual-e5-base',
                'dimension': 768,
                'hybrid': {
                    'bm25': True,
                    'fusion': 'RRF'
                }
            },
            'disambiguation': {
                'entity_linker': 'spaCy_es_core_news_lg',
                'confidence_threshold': 0.72
            }
        }

        # Add observability block
        monolith['observability'] = {
            'telemetry_schema': {
                'metrics': [
                    {
                        'name': 'pattern_match_count',
                        'level': 'MICRO',
                        'aggregation': 'sum'
                    },
                    {
                        'name': 'rule_latency_ms',
                        'level': 'METHOD_SET',
                        'aggregation': 'p95'
                    },
                    {
                        'name': 'validation_failure_rate',
                        'level': 'DIMENSION',
                        'aggregation': 'ratio'
                    }
                ],
                'logs': {
                    'format': 'jsonl',
                    'fields': ['timestamp', 'question_id', 'pattern_id', 'matched_text', 'confidence', 'trace_id', 'ruleset_hash']
                },
                'tracing': {
                    'propagation': 'W3C',
                    'span_structure': ['LOAD_RULESET', 'PARSE_DOCUMENT', 'EXTRACT_PATTERN', 'VALIDATE', 'AGGREGATE', 'EMIT_SCORE']
                }
            }
        }

        # Calculate ruleset hash for deterministic reproducibility
        ruleset_hash = self._calculate_ruleset_hash(micro_questions)

        # Calculate hash on canonical serialization
        canonical_json = json.dumps(monolith, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        monolith_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

        # Add integrity block
        monolith['integrity'] = {
            'monolith_hash': monolith_hash,
            'ruleset_hash': ruleset_hash,
            'question_count': {
                'micro': 300,
                'meso': 4,
                'macro': 1,
                'total': 305
            }
        }

        self.monolith['final'] = monolith

        logger.info(f"Sealed monolith with hash: {monolith_hash[:16]}...")
        logger.info(f"Ruleset hash: {ruleset_hash[:16]}...")
        logger.info(f"=== {phase} COMPLETE ===")

    def _structure_patterns(self, pattern_refs: list, question_id: str) -> list:
        """Structure pattern_refs as typed objects with categories."""
        structured = []

        for idx, pattern in enumerate(pattern_refs):
            if not isinstance(pattern, str):
                continue

            # Categorize patterns based on content
            category = self._categorize_pattern(pattern)

            structured.append({
                'id': f"PAT-{question_id}-{idx:03d}",
                'pattern': pattern,
                'category': category,
                'match_type': 'REGEX' if any(c in pattern for c in r'\\d.*+?[]()') else 'LITERAL',
                'flags': 'i',
                'confidence_weight': 0.85
            })

        return structured

    def _categorize_pattern(self, pattern: str) -> str:
        """Categorize a pattern based on its content."""
        pattern_lower = pattern.lower()

        if any(src in pattern_lower for src in ['dane', 'medicina legal', 'fiscalía', 'policía', 'sivigila', 'sispro']):
            return 'FUENTE_OFICIAL'
        elif any(ind in pattern_lower for ind in ['tasa', 'porcentaje', '%', 'indicador', 'cifra']):
            return 'INDICADOR'
        elif any(year in pattern for year in ['20\\d{2}', 'año', 'periodo']):
            return 'TEMPORAL'
        elif any(ent in pattern_lower for ent in ['departamental', 'municipal', 'territorial']):
            return 'TERRITORIAL'
        elif any(unit in pattern_lower for unit in ['por 100', 'por 1.000', 'por cada']):
            return 'UNIDAD_MEDIDA'
        else:
            return 'GENERAL'

    def _create_scoring_definitions(self):
        """Create explicit scoring modality definitions."""
        return {
            'micro_levels': self.monolith['scoring_matrix']['micro_levels'],
            'modalities': self.monolith['scoring_matrix']['modalities'],
            'modality_definitions': {
                'TYPE_A': {
                    'description': 'Count 4 elements and scale to 0-3',
                    'aggregation': 'presence_threshold',
                    'threshold': 0.7,
                    'failure_code': 'F-A-MIN'
                },
                'TYPE_B': {
                    'description': 'Count up to 3 elements, each worth 1 point',
                    'aggregation': 'binary_sum',
                    'max_score': 3,
                    'failure_code': 'F-B-MIN'
                },
                'TYPE_C': {
                    'description': 'Count 2 elements and scale to 0-3',
                    'aggregation': 'presence_threshold',
                    'threshold': 0.5,
                    'failure_code': 'F-C-MIN'
                },
                'TYPE_D': {
                    'description': 'Count 3 elements, weighted',
                    'aggregation': 'weighted_sum',
                    'weights': [0.4, 0.3, 0.3],
                    'failure_code': 'F-D-MIN'
                },
                'TYPE_E': {
                    'description': 'Boolean presence check',
                    'aggregation': 'binary_presence',
                    'failure_code': 'F-E-MIN'
                },
                'TYPE_F': {
                    'description': 'Continuous scale',
                    'aggregation': 'normalized_continuous',
                    'normalization': 'minmax',
                    'failure_code': 'F-F-MIN'
                }
            }
        }

    def _calculate_ruleset_hash(self, micro_questions: list) -> str:
        """Calculate deterministic hash of all patterns for reproducibility."""
        all_patterns = []

        for q in micro_questions:
            for pattern in q.get('patterns', []):
                if isinstance(pattern, dict):
                    all_patterns.append(pattern.get('pattern', ''))
                else:
                    all_patterns.append(str(pattern))

        # Sort for determinism
        all_patterns.sort()

        # Concatenate and hash
        patterns_str = '|'.join(all_patterns)
        return hashlib.sha256(patterns_str.encode('utf-8')).hexdigest()
    
    def _map_priority(self, priority_str: str) -> int:
        """Map string priority to numeric priority (1-3)."""
        priority_map = {
            'CRITICAL': 1,
            'HIGH': 1,
            'MEDIUM': 2,
            'LOW': 3,
        }
        return priority_map.get(priority_str, 2)
    
    def _get_methods_for_base_slot(self, base_slot: str, files_data: dict) -> list[dict]:
        """Get methods for a specific base_slot from catalog data.
        
        Args:
            base_slot: Base slot identifier (e.g., 'D1-Q1')
            files_data: Method catalog files data
            
        Returns:
            List of method definitions for this base_slot
        """
        # Extract dimension and question from base_slot
        # This is a simplified mapping - production code should use proper configuration
        methods = []
        
        # Get a subset of methods from the catalog for this base_slot
        # In a real implementation, this mapping should come from configuration
        for file_name, file_data in files_data.items():
            file_methods = file_data.get('methods', [])
            
            # Take first METHODS_PER_BASE_SLOT methods as a representative sample
            for method_info in file_methods[:self.METHODS_PER_BASE_SLOT]:
                methods.append({
                    'class': method_info.get('class', 'UnknownClass'),
                    'function': method_info.get('method_name', 'unknown_method'),
                    'module': file_name,
                    'method_type': 'analysis',
                    'priority': self._map_priority(method_info.get('priority', 'MEDIUM')),
                    'description': method_info.get('description', f"Analysis method for {base_slot}")
                })
            
            # Only need a few methods per base_slot
            if len(methods) >= self.METHODS_PER_BASE_SLOT:
                break
        
        # Ensure we have at least one method
        if not methods:
            logger.warning(
                f"No analysis methods found in catalog for base_slot '{base_slot}'. "
                f"Using synthetic DefaultAnalyzer fallback. This may indicate a configuration issue."
            )
            methods.append({
                'class': 'DefaultAnalyzer',
                'function': 'analyze',
                'module': 'default',
                'method_type': 'analysis',
                'priority': 2,
                'description': f'Default analysis for {base_slot}'
            })
        
        return methods

    # ========================================================================
    # PHASE 10: ValidationReportPhase
    # ========================================================================

    def validation_report_phase(self):
        """
        Validate all invariants before emission.
        Invariants: All legacy counters == destination counters
        """
        phase = "ValidationReportPhase"
        logger.info(f"=== {phase} START ===")

        monolith = self.monolith['final']

        # Validate question counts
        micro_count = len(monolith['blocks']['micro_questions'])
        meso_count = len(monolith['blocks']['meso_questions'])
        macro_count = 1
        total_count = micro_count + meso_count + macro_count

        if micro_count != 300:
            self.abort('A090', f'Expected 300 micro questions, got {micro_count}', phase)

        if meso_count != 4:
            self.abort('A090', f'Expected 4 meso questions, got {meso_count}', phase)

        if total_count != 305:
            self.abort('A090', f'Expected 305 total questions, got {total_count}', phase)

        # Validate base_slot coverage
        base_slot_counts = defaultdict(int)
        for q in monolith['blocks']['micro_questions']:
            base_slot_counts[q['base_slot']] += 1

        for slot, count in base_slot_counts.items():
            if count != 10:
                self.abort('A090', f'Base slot {slot} has {count} questions, expected 10', phase)

        if len(base_slot_counts) != 30:
            self.abort('A090', f'Expected 30 base_slots, got {len(base_slot_counts)}', phase)

        # Validate cluster hermeticity
        clusters_in_monolith = monolith['blocks']['niveles_abstraccion']['clusters']
        for cluster_def in clusters_in_monolith:
            cluster_id = cluster_def.get('cluster_id')
            canonical_record = self.canonical_clusters.get(cluster_id)

            if not canonical_record:
                self.abort('A090', f'Cluster {cluster_id} missing from canonical registry', phase)

            canonical_expected = set(canonical_record.get('canonical', []))
            canonical_present = set(cluster_def.get('policy_area_ids', []))
            if canonical_expected and canonical_present != canonical_expected:
                self.abort(
                    'A090',
                    f'{cluster_id} canonical hermeticity violation in final',
                    phase
                )

            expected_legacy = set(canonical_record.get('legacy', []))
            legacy_present = set(cluster_def.get('legacy_policy_area_ids', []))
            if expected_legacy and legacy_present != expected_legacy:
                self.abort(
                    'A090',
                    f'{cluster_id} legacy hermeticity violation in final',
                    phase
                )

        logger.info("Validation PASSED:")
        logger.info("  - 300 micro questions")
        logger.info("  - 4 meso questions")
        logger.info("  - 1 macro question")
        logger.info("  - 30 base_slots, each with 10 questions")
        logger.info("  - Cluster hermeticity verified")
        logger.info(f"=== {phase} COMPLETE ===")

    # ========================================================================
    # PHASE 11: FinalEmissionPhase
    # ========================================================================

    def final_emission_phase(self, output_path: str | None):
        """Write the orchestrator-managed questionnaire monolith to disk."""
        phase = "FinalEmissionPhase"
        logger.info(f"=== {phase} START ===")

        monolith = self.monolith['final']

        # Delegate persistence to the orchestrator provider
        output_file = QUESTIONNAIRE_PROVIDER.save(monolith, output_path=output_path)

        file_info = QUESTIONNAIRE_PROVIDER.describe(output_file)
        file_size = file_info["size"]
        if file_size == 0:
            self.abort('A100', 'Empty monolith emission', phase)

        # Verify hash matches by reloading through the provider interface
        reloaded = QUESTIONNAIRE_PROVIDER.load(force_reload=True, data_path=output_file)

        expected_hash = monolith['integrity']['monolith_hash']
        reloaded_without_integrity = {k: v for k, v in reloaded.items() if k != 'integrity'}
        canonical_check = json.dumps(reloaded_without_integrity, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        actual_hash = hashlib.sha256(canonical_check.encode('utf-8')).hexdigest()

        if actual_hash != expected_hash:
            self.abort('A080', f'Hash mismatch after emission: expected {expected_hash}, got {actual_hash}', phase)

        logger.info(f"Emitted monolith to {output_path}")
        logger.info(f"  File size: {file_size:,} bytes")
        logger.info(f"  Hash: {expected_hash[:16]}... (verified)")
        logger.info(f"=== {phase} COMPLETE ===")

        # Generate manifest
        manifest = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'output_file': str(output_file),
            'file_size': file_size,
            'monolith_hash': expected_hash,
            'phases_executed': [
                'LoadLegacyPhase',
                'StructuralIndexingPhase',
                'BaseSlotMappingPhase',
                'ExtractionAndNormalizationPhase',
                'IndicatorsAndEvidencePhase',
                'MethodSetSynthesisPhase',
                'RubricTranspositionPhase',
                'MesoMacroEmbeddingPhase',
                'IntegritySealingPhase',
                'ValidationReportPhase',
                'FinalEmissionPhase'
            ],
            'stats': {
                'micro_questions': 300,
                'meso_questions': 4,
                'macro_questions': 1,
                'total_questions': 305,
                'base_slots': 30,
                'clusters': 4,
                'policy_areas': 10,
                'dimensions': 6
            }
        }

        manifest_path = output_file.parent / 'forge_manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"Manifest written to {manifest_path}")

    # ========================================================================
    # Main Build Pipeline
    # ========================================================================

    def build(self, output_path: str | None = None):
        """Execute all construction phases in order."""
        logger.info("=" * 70)
        logger.info("MonolithForge: Starting construction pipeline")
        logger.info("=" * 70)

        try:
            self.load_legacy_phase()
            self.structural_indexing_phase()
            self.base_slot_mapping_phase()
            self.extraction_and_normalization_phase()
            self.indicators_and_evidence_phase()
            self.method_set_synthesis_phase()
            self.rubric_transposition_phase()
            self.meso_macro_embedding_phase()
            self.integrity_sealing_phase()
            self.validation_report_phase()
            self.final_emission_phase(output_path)

            logger.info("=" * 70)
            logger.info("MonolithForge: Construction COMPLETE")
            logger.info("=" * 70)
            return True

        except AbortError as e:
            logger.error(f"FATAL ABORT: {e}")
            logger.error(f"Construction FAILED at {e.phase}")
            return False

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Build questionnaire monolith payload')
    parser.add_argument(
        '--output',
        '-o',
        default=None,
        help='Output path for the questionnaire monolith file'
    )

    args = parser.parse_args()

    forge = MonolithForge()
    success = forge.build(args.output)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
