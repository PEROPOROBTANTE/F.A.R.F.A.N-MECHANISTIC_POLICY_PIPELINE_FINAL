import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import Phase 1 models for reference/typing
from saaaaaa.core.phases.phase1_models import SmartChunk
from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage

class FatalPhase2Error(Exception):
    """Irrecoverable fatal error in Phase 2."""
    pass

@dataclass
class Phase2MissionContract:
    """
    CRITICAL WEIGHT: 10000
    PHASE 2 PROCESSES EXACTLY 300 MICRO QUESTIONS
    ANY DEVIATION = IMMEDIATE PIPELINE TERMINATION
    """
    
    IMMUTABLE_CONSTANTS = {
        "TOTAL_QUESTIONS": 300,
        "CHUNKS_AVAILABLE": 60,
        "DIMENSIONS": 6,
        "POLICY_AREAS": 10,
        "QUESTIONS_PER_DIMENSION": 50,  # 300/6
        "QUESTIONS_PER_PA_PER_DIM": 5   # 50/10
    }
    
    PRIMARY_OBJECTIVES = {
        "QUESTION_ANSWERING": {
            "requirement": "Answer ALL 300 micro questions using 60 PA×DIM chunks",
            "hard_constraints": [
                "EXACTLY 300 questions answered",
                "STRICT dimension-first ordering",
                "STRICT policy-area scoping within dimension",
                "ALL evidence from Phase-1 CPP chunks",
                "ZERO re-computation of Phase-1 outputs",
                "FULL signal integration",
                "COMPLETE execution traceability"
            ],
            "weight": 10000,
            "failure_mode": "FATAL_PIPELINE_ABORT"
        },
        
        "EVIDENCE_PIPELINE": {
            "requirement": "Use canonical evidence from CPP chunks",
            "hard_constraints": [
                "Evidence ONLY from PreprocessedDocument",
                "Evidence ONLY from 60 SmartPolicyChunks",
                "PA×DIM isolation enforced",
                "Signal-driven selection",
                "Full provenance tracking",
                "Zero hallucination"
            ],
            "weight": 10000,
            "failure_mode": "FATAL_EVIDENCE_CORRUPTION"
        },
        
        "EXECUTION_ORDER": {
            "requirement": "Dimension-first, PA-scoped processing",
            "execution_sequence": [
                "DIM1: PA1-10 questions (50 total)",
                "DIM2: PA1-10 questions (50 total)",
                "DIM3: PA1-10 questions (50 total)",
                "DIM4: PA1-10 questions (50 total)",
                "DIM5: PA1-10 questions (50 total)",
                "DIM6: PA1-10 questions (50 total)"
            ],
            "weight": 10000,
            "failure_mode": "FATAL_ORDER_VIOLATION"
        }
    }
    
    FAILURE_CONDITIONS = {
        "wrong_question_count": "questions_answered != 300 → PHASE 2 FAILED",
        "order_violation": "dimension_sequence broken → PHASE 2 FAILED",
        "pa_contamination": "cross-PA evidence leak → PHASE 2 FAILED",
        "phase1_recomputation": "ANY Phase-1 re-derivation → PHASE 2 FAILED",
        "missing_evidence": "unanswerable question → PHASE 2 FAILED",
        "signal_failure": "signal routing broken → PHASE 2 FAILED"
    }

class Phase2OperatingContext:
    """
    STRICT DEFINITION OF WHAT PHASE 2 CAN ACCESS
    WEIGHT: 10000 - NO UNAUTHORIZED DATA ACCESS
    """
    
    AUTHORIZED_INPUTS = {
        "cpp_from_phase1": {
            "type": "CanonPolicyPackage",
            "contents": [
                "60 SmartPolicyChunk objects",
                "chunk metadata (causal, temporal, args, discourse)",
                "execution_trace from Phase 1",
                "subphase_results[0:16]",
                "signals_summary"
            ],
            "access_mode": "READ_ONLY",
            "modification": "FORBIDDEN"
        },
        
        "preprocessed_document": {
            "type": "PreprocessedDocument",
            "contents": [
                "sentence-level tokenization",
                "paragraph structure",
                "span mappings",
                "linguistic annotations"
            ],
            "access_mode": "READ_ONLY",
            "usage": "sentence-level evidence extraction"
        },
        
        "canonical_json": {
            "type": "JSON Factory outputs",
            "contents": [
                "serialized chunks",
                "metadata registries",
                "signal states",
                "evidence mappings"
            ],
            "access_mode": "READ_ONLY",
            "requirement": "MUST use Factory, NEVER parse manually"
        }
    }
    
    FORBIDDEN_OPERATIONS = [
        "Re-running ANY Phase-1 subphase",
        "Re-computing causal graphs",
        "Re-extracting arguments",
        "Re-doing temporal analysis",
        "Re-calculating strategic ranks",
        "Modifying chunk boundaries",
        "Creating new chunks",
        "Deleting existing chunks"
    ]
    
    @staticmethod
    def validate_data_access(operation: str, data_source: str) -> bool:
        """
        ENFORCE DATA ACCESS RULES
        """
        if operation in Phase2OperatingContext.FORBIDDEN_OPERATIONS:
            raise FatalPhase2Error(f"FORBIDDEN: {operation}")
        
        if data_source not in Phase2OperatingContext.AUTHORIZED_INPUTS:
            raise FatalPhase2Error(f"UNAUTHORIZED DATA: {data_source}")
        
        return True

@dataclass
class MicroQuestion:
    question_id: str          # Unique identifier
    dimension_id: str         # D1-D6
    policy_area_id: str       # PA01-PA10
    question_text: str        # Actual question
    question_type: str        # Type/template
    required_evidence: List[str]  # Evidence types needed
    signal_requirements: Dict[str, float]  # Min signal thresholds

@dataclass
class Evidence:
    evidence_id: str
    source_chunk_id: str
    policy_area: str
    dimension: str
    evidence_type: str
    content: Any
    provenance: Dict[str, Any]

@dataclass
class Signal:
    signal_id: str
    signal_type: str
    value: float = 0.0
    metadata: Dict = field(default_factory=dict)
    computation_trace: List[str] = field(default_factory=list)
    
    def __init__(self, signal_id: str, signal_type: str):
        self.signal_id = signal_id
        self.signal_type = signal_type
        self.value = 0.0
        self.metadata = {}
        self.computation_trace = []

@dataclass
class ExecutorConfig:
    executor_id: str
    executor_type: str
    supported_dimensions: List[str]
    supported_policy_areas: List[str]
    required_evidence_types: List[str]
    method_whitelist: List[str]  # From MethodRegistry
    signal_requirements: Dict[str, float]
    version: str

@dataclass
class ExecutedContract:
    """
    RUNTIME RECORD OF EXECUTION
    """
    contract_id: str
    executor_id: str
    question_id: str
    input_evidence_ids: List[str]
    input_signals: Dict[str, float]
    methods_called: List[str]
    output_answer: str
    output_confidence: float
    output_metrics: Dict[str, Any]
    execution_timestamp: str
    execution_duration_ms: int

@dataclass
class Phase2Results:
    total_questions_answered: int = 0
    execution_log: List[Dict] = field(default_factory=list)
    answers: Dict[str, str] = field(default_factory=dict)
    dimension_coverage: Dict[str, int] = field(default_factory=dict)
    pa_coverage: Dict[str, int] = field(default_factory=dict)
    total_evidence_used: int = 0
    avg_confidence: float = 0.0
    verification: Dict[str, Any] = field(default_factory=dict)
    verification_manifest: Dict[str, Any] = field(default_factory=dict)
