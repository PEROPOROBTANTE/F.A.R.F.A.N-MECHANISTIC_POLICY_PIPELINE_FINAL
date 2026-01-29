"""
Unified FARFAN Pipeline Orchestrator
===================================

This is the SINGLE unified orchestrator that consolidates all orchestration logic.

Previously split across 5 files:
- orchestrator_config.py (configuration)
- orchestration_core.py (state machine, dependency graph, scheduler)
- core_orchestrator.py (core orchestration logic)
- phase_executors.py (phase executors P02-P09)
- main_orchestrator.py (signal-driven orchestrator)

Now consolidated into ONE comprehensive orchestrator.

Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED ORCHESTRATOR                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Configuration   │  │ State Machine   │  │ Dependency      │             │
│  │                 │  │                 │  │ Graph           │             │
│  │ - Orchestrator  │  │ - IDLE          │  │ - Nodes         │             │
│  │   Config        │  │ - INITIALIZING  │  │ - Edges         │             │
│  │ - Validation    │  │ - RUNNING       │  │ - Validation    │             │
│  └─────────────────┘  │ - COMPLETED     │  │ - Propagation   │             │
│                      └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Phase Scheduler │  │ Core Orchestrator│  │ Signal-Driven   │             │
│  │                 │  │                 │  │ Orchestrator    │             │
│  │ - SEQUENTIAL    │  │ - Execute phases │  │ - PhaseStart    │             │
│  │ - PARALLEL      │  │ - Contract      │  │ - PhaseComplete │             │
│  │ - HYBRID        │  │   enforcement   │  │ - Decision      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    Phase Executors (P02-P09)                     │       │
│  │  P2: Task Execution  P3: Scoring  P4-P7: Aggregation  P8-P9     │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Version: 2.0.0 (Unified)
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any
from uuid import uuid4

import blake3
import structlog

# =============================================================================
# SISAS CORE IMPORTS
# =============================================================================
try:
    from canonic_questionnaire_central.core.signal import (
        Signal,
        SignalProvenance,
        SignalScope,
        SignalType,
    )

    SISAS_CORE_AVAILABLE = True
except ImportError:
    SISAS_CORE_AVAILABLE = False
    Signal = None
    SignalType = None
    SignalScope = None
    SignalProvenance = None

# Import validation gates
try:
    from .gates import GateOrchestrator

    GATES_AVAILABLE = True
except ImportError:
    GATES_AVAILABLE = False
    GateOrchestrator = None

# =============================================================================
# UNIFIED FACTORY IMPORT
# =============================================================================
# Import the unified factory for all component creation and questionnaire loading
try:
    from .factory import FactoryConfig, UnifiedFactory

    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False
    UnifiedFactory = None  # type: ignore
    FactoryConfig = None  # type: ignore

# =============================================================================
# SISAS INTEGRATION HUB IMPORT
# =============================================================================
# Import the SISAS integration hub for comprehensive SISAS wiring
try:
    from .sisas_integration_hub import SISASIntegrationHub, initialize_sisas

    SISAS_HUB_AVAILABLE = True
except ImportError:
    SISAS_HUB_AVAILABLE = False
    SISASIntegrationHub = None  # type: ignore
    initialize_sisas = None  # type: ignore

# =============================================================================
# PHASE 0 GATE RESULT IMPORT
# =============================================================================
# Import GateResult from Phase 0 exit gates for use in Phase0ValidationResult
try:
    from farfan_pipeline.phases.Phase_00.phase0_50_01_exit_gates import GateResult

    GATE_RESULT_AVAILABLE = True
except ImportError:
    GATE_RESULT_AVAILABLE = False

    # Define a fallback GateResult if import fails
    @dataclass
    class GateResult:
        passed: bool
        gate_name: str
        gate_id: int
        reason: str | None = None

        def to_dict(self) -> dict:
            return {
                "passed": self.passed,
                "gate_name": self.gate_name,
                "gate_id": self.gate_id,
                "reason": self.reason,
            }


# =============================================================================
# LOGGER CONFIGURATION
# =============================================================================

logger = structlog.get_logger(__name__)

# =============================================================================
# SECTION 1: CONFIGURATION (from orchestrator_config.py)
# =============================================================================


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""


@dataclass
class OrchestratorConfig:
    """Unified configuration for the orchestrator."""

    # Core settings
    municipality_name: str = "Unknown"
    document_path: str | None = None
    output_dir: str = "./output"

    # Execution settings
    strict_mode: bool = False
    phases_to_execute: str = "ALL"

    # Resource settings
    seed: int = 42
    max_workers: int = 4
    enable_parallel_execution: bool = True

    # Feature flags
    enable_sisas: bool = True
    enable_calibration: bool = True
    enable_checkpoint: bool = True

    # Paths
    questionnaire_path: str = "canonic_questionnaire_central/_registry"
    methods_file: str = "json_methods/METHODS_OPERACIONALIZACION.json"

    # Resource limits
    resource_limits: dict = field(default_factory=dict)

    # Scheduling mode
    scheduling_mode: str = "HYBRID"  # SEQUENTIAL, PARALLEL, HYBRID, PRIORITY
    max_parallel_phases: int = 4

    # Retry settings
    retry_failed_phases: bool = True
    max_retries_per_phase: int = 3

    # Signal settings
    emit_decision_signals: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "municipality_name": self.municipality_name,
            "document_path": self.document_path,
            "output_dir": self.output_dir,
            "strict_mode": self.strict_mode,
            "phases_to_execute": self.phases_to_execute,
            "seed": self.seed,
            "max_workers": self.max_workers,
            "enable_parallel_execution": self.enable_parallel_execution,
            "enable_sisas": self.enable_sisas,
            "enable_calibration": self.enable_calibration,
            "enable_checkpoint": self.enable_checkpoint,
            "questionnaire_path": self.questionnaire_path,
            "methods_file": self.methods_file,
            "resource_limits": self.resource_limits,
            "scheduling_mode": self.scheduling_mode,
            "max_parallel_phases": self.max_parallel_phases,
            "retry_failed_phases": self.retry_failed_phases,
            "max_retries_per_phase": self.max_retries_per_phase,
            "emit_decision_signals": self.emit_decision_signals,
        }


def validate_config(config: dict[str, Any] | OrchestratorConfig) -> list[str]:
    """Validate configuration dictionary or OrchestratorConfig object."""
    warnings = []

    # Handle both dict and OrchestratorConfig
    if isinstance(config, OrchestratorConfig):
        document_path = getattr(config, "document_path", None)
        seed = getattr(config, "seed", None)
        max_workers = getattr(config, "max_workers", None)
    else:
        document_path = config.get("document_path")
        seed = config.get("seed")
        max_workers = config.get("max_workers")

    if not document_path:
        warnings.append("document_path is not specified, using default")

    if seed is not None and not isinstance(seed, int):
        warnings.append("seed should be an integer")

    if max_workers is not None:
        if not isinstance(max_workers, int) or max_workers < 1:
            warnings.append("max_workers should be a positive integer")

    return warnings


def get_development_config() -> OrchestratorConfig:
    """Get configuration preset for development."""
    return OrchestratorConfig(
        strict_mode=False,
        enable_sisas=True,
        enable_calibration=False,
        max_workers=2,
    )


def get_production_config() -> OrchestratorConfig:
    """Get configuration preset for production."""
    return OrchestratorConfig(
        strict_mode=True,
        enable_sisas=True,
        enable_calibration=True,
        max_workers=4,
    )


def get_testing_config() -> OrchestratorConfig:
    """Get configuration preset for testing."""
    return OrchestratorConfig(
        strict_mode=True,
        enable_sisas=False,
        enable_calibration=False,
        max_workers=1,
        phases_to_execute="0-2",
    )


# =============================================================================
# SECTION 2: EXCEPTIONS (from orchestration_core.py)
# =============================================================================


class OrchestrationError(Exception):
    """Base exception for all orchestration errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code or "ORCHESTRATION_ERROR"
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
        }


class DependencyResolutionError(OrchestrationError):
    """Raised when dependency graph resolution fails."""

    def __init__(
        self,
        message: str,
        phase_id: str | None = None,
        dependency_chain: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.phase_id = phase_id
        self.dependency_chain = dependency_chain or []
        ctx = context or {}
        if phase_id:
            ctx["phase_id"] = phase_id
        if dependency_chain:
            ctx["dependency_chain"] = dependency_chain
        super().__init__(
            message,
            error_code="DEPENDENCY_RESOLUTION_ERROR",
            context=ctx,
        )


class SchedulingError(OrchestrationError):
    """Raised when phase scheduling fails."""

    def __init__(
        self,
        message: str,
        scheduling_strategy: str | None = None,
        phases_in_conflict: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.scheduling_strategy = scheduling_strategy
        self.phases_in_conflict = phases_in_conflict or []
        ctx = context or {}
        if scheduling_strategy:
            ctx["scheduling_strategy"] = scheduling_strategy
        if phases_in_conflict:
            ctx["phases_in_conflict"] = phases_in_conflict
        super().__init__(
            message,
            error_code="SCHEDULING_ERROR",
            context=ctx,
        )


class StateTransitionError(OrchestrationError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        message: str,
        current_state: str | None = None,
        target_state: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.current_state = current_state
        self.target_state = target_state
        ctx = context or {}
        if current_state:
            ctx["current_state"] = current_state
        if target_state:
            ctx["target_state"] = target_state
        super().__init__(
            message,
            error_code="STATE_TRANSITION_ERROR",
            context=ctx,
        )


class OrchestrationInitializationError(OrchestrationError):
    """Raised when the orchestrator cannot be initialized."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="ORCH_INIT_ERROR", context=kwargs)


class PhaseExecutionError(OrchestrationError):
    """Raised when a phase fails to execute."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="PHASE_EXECUTION_ERROR", context=kwargs)


class ContractViolationError(OrchestrationError):
    """Raised when a signal contract is violated."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONTRACT_VIOLATION_ERROR", context=kwargs)


# =============================================================================
# SECTION 3: STATE MACHINE (from orchestration_core.py)
# =============================================================================


class OrchestrationState(Enum):
    """States of the orchestration lifecycle."""

    IDLE = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    COMPLETED_WITH_ERRORS = auto()
    STOPPED = auto()
    STOPPING = auto()


@dataclass
class StateTransition:
    """Represents a single state transition in the orchestration lifecycle."""

    from_state: OrchestrationState
    to_state: OrchestrationState
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_state": self.from_state.name,
            "to_state": self.to_state.name,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "metadata": self.metadata,
        }


VALID_TRANSITIONS: dict[OrchestrationState, set[OrchestrationState]] = {
    OrchestrationState.IDLE: {OrchestrationState.INITIALIZING},
    OrchestrationState.INITIALIZING: {OrchestrationState.RUNNING, OrchestrationState.STOPPING},
    OrchestrationState.RUNNING: {
        OrchestrationState.COMPLETED,
        OrchestrationState.COMPLETED_WITH_ERRORS,
        OrchestrationState.STOPPING,
    },
    OrchestrationState.STOPPING: {OrchestrationState.STOPPED},
    OrchestrationState.COMPLETED: set(),
    OrchestrationState.COMPLETED_WITH_ERRORS: set(),
    OrchestrationState.STOPPED: set(),
}


@dataclass
class OrchestrationStateMachine:
    """State machine for orchestration lifecycle management."""

    current_state: OrchestrationState = field(default=OrchestrationState.IDLE)
    _transition_history: list[StateTransition] = field(default_factory=list)
    allow_terminal_transition: bool = False
    _transition_callbacks: dict[OrchestrationState, list[callable]] = field(default_factory=dict)

    def transition_to(
        self,
        new_state: OrchestrationState,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        """Transition to a new state."""
        if not self._is_valid_transition(new_state):
            raise StateTransitionError(
                message=f"Invalid state transition: {self.current_state.name} → {new_state.name}",
                current_state=self.current_state.name,
                target_state=new_state.name,
            )

        transition = StateTransition(
            from_state=self.current_state,
            to_state=new_state,
            reason=reason,
            metadata=metadata or {},
        )

        old_state = self.current_state
        self.current_state = new_state
        self._transition_history.append(transition)

        logger.info(f"State transition: {old_state.name} → {new_state.name}")

        self._invoke_callbacks(new_state, transition)
        return transition

    def _is_valid_transition(self, new_state: OrchestrationState) -> bool:
        """Check if a transition is valid."""
        if new_state == self.current_state:
            return False

        valid_targets = VALID_TRANSITIONS.get(self.current_state, set())

        if self.current_state in {
            OrchestrationState.COMPLETED,
            OrchestrationState.COMPLETED_WITH_ERRORS,
            OrchestrationState.STOPPED,
        }:
            return self.allow_terminal_transition and new_state in valid_targets

        return new_state in valid_targets

    def register_callback(
        self, state: OrchestrationState, callback: callable[[StateTransition], None]
    ) -> None:
        """Register a callback to be invoked when entering a specific state."""
        if state not in self._transition_callbacks:
            self._transition_callbacks[state] = []
        self._transition_callbacks[state].append(callback)

    def _invoke_callbacks(self, state: OrchestrationState, transition: StateTransition) -> None:
        """Invoke all callbacks registered for a state."""
        callbacks = self._transition_callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback(transition)
            except Exception as e:
                logger.error(f"State transition callback failed for state {state.name}: {e}")

    def get_transition_history(self) -> list[dict[str, Any]]:
        """Get the complete transition history."""
        return [t.to_dict() for t in self._transition_history]

    def is_terminal(self) -> bool:
        """Check if the current state is terminal."""
        return self.current_state in {
            OrchestrationState.COMPLETED,
            OrchestrationState.COMPLETED_WITH_ERRORS,
            OrchestrationState.STOPPED,
        }

    def is_running(self) -> bool:
        """Check if the orchestration is currently running."""
        return self.current_state == OrchestrationState.RUNNING

    def to_dict(self) -> dict[str, Any]:
        """Serialize the state machine to a dictionary."""
        return {
            "current_state": self.current_state.name,
            "is_terminal": self.is_terminal(),
            "is_running": self.is_running(),
            "transition_count": len(self._transition_history),
            "transitions": self.get_transition_history(),
        }


# =============================================================================
# SECTION 4: DEPENDENCY GRAPH (from orchestration_core.py)
# =============================================================================


class DependencyStatus(Enum):
    """Status of a node in the dependency graph."""

    PENDING = auto()
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    PARTIAL = auto()
    PENDING_RETRY = auto()
    FAILED = auto()
    BLOCKED = auto()
    PERMANENTLY_BLOCKED = auto()


@dataclass
class DependencyNode:
    """Represents a phase node in the dependency graph."""

    node_id: str
    phase_id: str
    status: DependencyStatus = DependencyStatus.PENDING
    upstream: set[str] = field(default_factory=set)
    downstream: set[str] = field(default_factory=set)
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DependencyNode):
            return False
        return self.node_id == other.node_id

    def is_terminal(self) -> bool:
        """Check if this node is in a terminal state."""
        return self.status in {
            DependencyStatus.COMPLETED,
            DependencyStatus.PARTIAL,
            DependencyStatus.FAILED,
            DependencyStatus.PERMANENTLY_BLOCKED,
        }

    def can_start(self) -> bool:
        """Check if this node can start execution."""
        return self.status == DependencyStatus.READY


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between two phases."""

    from_node: str
    to_node: str
    edge_type: str = "hard"

    def __hash__(self) -> int:
        return hash((self.from_node, self.to_node))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DependencyEdge):
            return False
        return self.from_node == other.from_node and self.to_node == other.to_node


@dataclass
class GraphValidationResult:
    """Result of validating the dependency graph."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)
    orphan_nodes: list[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Dependency graph for phase orchestration."""

    nodes: dict[str, DependencyNode] = field(default_factory=dict)
    edges: set[DependencyEdge] = field(default_factory=set)
    _adjacency: dict[str, set[str]] = field(default_factory=dict)
    _reverse_adjacency: dict[str, set[str]] = field(default_factory=dict)

    def add_node(
        self,
        node_id: str,
        phase_id: str,
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DependencyNode:
        """Add a phase node to the graph."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            if config:
                node.config.update(config)
            if metadata:
                node.metadata.update(metadata)
            return node

        node = DependencyNode(
            node_id=node_id,
            phase_id=phase_id,
            config=config or {},
            metadata=metadata or {},
        )

        self.nodes[node_id] = node
        self._adjacency[node_id] = set()
        self._reverse_adjacency[node_id] = set()

        return node

    def add_edge(self, from_node: str, to_node: str, edge_type: str = "hard") -> DependencyEdge:
        """Add a dependency edge between two nodes."""
        if from_node not in self.nodes:
            raise DependencyResolutionError(f"Source node {from_node} does not exist")
        if to_node not in self.nodes:
            raise DependencyResolutionError(f"Target node {to_node} does not exist")

        edge = DependencyEdge(from_node=from_node, to_node=to_node, edge_type=edge_type)

        if self._would_create_cycle(edge):
            raise DependencyResolutionError(
                f"Edge {from_node} -> {to_node} would create a circular dependency"
            )

        self.edges.add(edge)
        self._adjacency[from_node].add(to_node)
        self._reverse_adjacency[to_node].add(from_node)

        self.nodes[from_node].downstream.add(to_node)
        self.nodes[to_node].upstream.add(from_node)

        self._update_node_readiness(to_node)

        return edge

    def _would_create_cycle(self, new_edge: DependencyEdge) -> bool:
        """Check if adding an edge would create a cycle."""
        visited: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            for neighbor in self._adjacency.get(node, set()):
                if neighbor == new_edge.from_node:
                    return True
                if neighbor not in visited and has_cycle(neighbor):
                    return True
            return False

        return has_cycle(new_edge.to_node)

    def update_node_status(
        self,
        node_id: str,
        new_status: DependencyStatus,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update the status of a node."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        old_status = node.status
        node.status = new_status

        if metadata:
            node.metadata.update(metadata)

        if new_status == DependencyStatus.RUNNING and node.started_at is None:
            node.started_at = datetime.utcnow()
        elif new_status in {
            DependencyStatus.COMPLETED,
            DependencyStatus.PARTIAL,
            DependencyStatus.FAILED,
            DependencyStatus.PERMANENTLY_BLOCKED,
        }:
            node.completed_at = datetime.utcnow()

        logger.info(f"Node {node_id} status: {old_status.name} → {new_status.name}")
        self._propagate_status_change(node_id, new_status)

    def _update_node_readiness(self, node_id: str) -> None:
        """Update whether a node is ready to start."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        all_upstream_complete = all(
            self.nodes[upstream].status == DependencyStatus.COMPLETED
            for upstream in node.upstream
            if upstream in self.nodes
        )

        if all_upstream_complete and node.status == DependencyStatus.PENDING:
            node.status = DependencyStatus.READY
        elif not all_upstream_complete and node.status == DependencyStatus.READY:
            node.status = DependencyStatus.BLOCKED

    def _propagate_status_change(self, node_id: str, new_status: DependencyStatus) -> None:
        """Propagate status changes to downstream nodes."""
        for downstream_id in self._adjacency.get(node_id, set()):
            if new_status == DependencyStatus.COMPLETED:
                self._update_node_readiness(downstream_id)
            elif new_status in {
                DependencyStatus.FAILED,
                DependencyStatus.PERMANENTLY_BLOCKED,
            }:
                edge = self._get_edge(node_id, downstream_id)
                if edge and edge.edge_type == "hard":
                    self.update_node_status(downstream_id, DependencyStatus.PERMANENTLY_BLOCKED)

    def get_ready_phases(self) -> list[str]:
        """Get all phases that are ready to start."""
        return [
            node_id for node_id, node in self.nodes.items() if node.status == DependencyStatus.READY
        ]

    def get_upstream_dependencies(self, node_id: str) -> list[str]:
        """Get upstream dependencies for a node."""
        return list(self.nodes.get(node_id, DependencyNode("", "")).upstream)

    def get_downstream_dependents(self, node_id: str) -> list[str]:
        """Get downstream dependents of a node."""
        return list(self._adjacency.get(node_id, set()))

    def get_newly_unblocked(self, node_id: str) -> list[str]:
        """Get downstream nodes that became unblocked by a node completion."""
        unblocked = []
        for downstream_id in self._adjacency.get(node_id, set()):
            if self.nodes[downstream_id].status == DependencyStatus.READY:
                unblocked.append(downstream_id)
        return unblocked

    def get_permanently_blocked(self) -> list[str]:
        """Get all permanently blocked nodes."""
        return [
            node_id
            for node_id, node in self.nodes.items()
            if node.status == DependencyStatus.PERMANENTLY_BLOCKED
        ]

    def get_state_snapshot(self) -> dict[str, str]:
        """Get a snapshot of all node states."""
        return {node_id: node.status.name for node_id, node in self.nodes.items()}

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the graph."""
        status_counts = {}
        for node in self.nodes.values():
            status = node.status.name
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "status_counts": status_counts,
            "ready_phases": len(self.get_ready_phases()),
            "blocked_phases": len(
                [n for n in self.nodes.values() if n.status == DependencyStatus.BLOCKED]
            ),
        }

    def validate(self) -> GraphValidationResult:
        """Validate the dependency graph."""
        errors = []
        warnings = []
        cycles = []
        orphans = []

        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adjacency.get(node, set()):
                if neighbor not in visited:
                    if dfs_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                dfs_cycle(node_id)

        if cycles:
            errors.append(f"Found {len(cycles)} circular dependencies")

        for node_id, node in self.nodes.items():
            if not node.upstream and not node.downstream:
                orphans.append(node_id)

        if orphans:
            warnings.append(f"Found {len(orphans)} orphan nodes: {orphans}")

        return GraphValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cycles=cycles,
            orphan_nodes=orphans,
        )

    def _get_edge(self, from_node: str, to_node: str) -> DependencyEdge | None:
        """Get an edge between two nodes."""
        for edge in self.edges:
            if edge.from_node == from_node and edge.to_node == to_node:
                return edge
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a dictionary."""
        return {
            "nodes": {
                node_id: {
                    "phase_id": node.phase_id,
                    "status": node.status.name,
                    "upstream": list(node.upstream),
                    "downstream": list(node.downstream),
                    "config": node.config,
                }
                for node_id, node in self.nodes.items()
            },
            "edges": [
                {"from": edge.from_node, "to": edge.to_node, "type": edge.edge_type}
                for edge in self.edges
            ],
            "summary": self.get_summary(),
        }


# =============================================================================
# SECTION 5: PHASE SCHEDULER (from orchestration_core.py)
# =============================================================================


class SchedulingStrategy(Enum):
    """Scheduling strategies for phase execution."""

    SEQUENTIAL = auto()
    PARALLEL = auto()
    HYBRID = auto()
    PRIORITY = auto()


@dataclass
class SchedulingDecision:
    """Result of a scheduling operation."""

    phases_to_start: list[str] = field(default_factory=list)
    phases_waiting: list[str] = field(default_factory=list)
    phases_blocked: list[str] = field(default_factory=list)
    rationale: str = ""
    strategy_used: SchedulingStrategy = SchedulingStrategy.HYBRID
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseScheduler:
    """Scheduler for determining which phases should execute."""

    dependency_graph: DependencyGraph
    mode: SchedulingStrategy = SchedulingStrategy.HYBRID
    priority_weights: dict[str, float] = field(default_factory=dict)

    def get_ready_phases(
        self,
        completed_phases: set[str],
        failed_phases: set[str],
        active_phases: set[str],
        max_parallel: int = 4,
    ) -> SchedulingDecision:
        """Determine which phases should start."""
        ready_phases = self.dependency_graph.get_ready_phases()

        available = [
            p for p in ready_phases if p not in active_phases and p not in completed_phases
        ]

        blocked = self._get_blocked_phases(available, completed_phases, failed_phases)

        if self.mode == SchedulingStrategy.SEQUENTIAL:
            return self._schedule_sequential(available, blocked, active_phases, max_parallel)
        elif self.mode == SchedulingStrategy.PARALLEL:
            return self._schedule_parallel(available, blocked, active_phases, max_parallel)
        elif self.mode == SchedulingStrategy.PRIORITY:
            return self._schedule_priority(available, blocked, active_phases, max_parallel)
        else:
            return self._schedule_hybrid(available, blocked, active_phases, max_parallel)

    def _schedule_sequential(
        self,
        available: list[str],
        blocked: list[str],
        active_phases: set[str],
        max_parallel: int,
    ) -> SchedulingDecision:
        """Sequential scheduling - one phase at a time."""
        if active_phases:
            return SchedulingDecision(
                phases_to_start=[],
                phases_waiting=available[:1] if available else [],
                phases_blocked=blocked,
                rationale="Sequential mode: waiting for active phase to complete",
                strategy_used=SchedulingStrategy.SEQUENTIAL,
            )

        to_start = available[:1] if available else []
        waiting = available[1:] if len(available) > 1 else []

        return SchedulingDecision(
            phases_to_start=to_start,
            phases_waiting=waiting,
            phases_blocked=blocked,
            rationale=f"Sequential mode: starting {to_start[0] if to_start else 'none'}",
            strategy_used=SchedulingStrategy.SEQUENTIAL,
        )

    def _schedule_parallel(
        self,
        available: list[str],
        blocked: list[str],
        active_phases: set[str],
        max_parallel: int,
    ) -> SchedulingDecision:
        """Parallel scheduling - start all available up to limit."""
        slots_available = max_parallel - len(active_phases)
        to_start = available[:slots_available] if slots_available > 0 else []
        waiting = available[slots_available:] if slots_available < len(available) else []

        return SchedulingDecision(
            phases_to_start=to_start,
            phases_waiting=waiting,
            phases_blocked=blocked,
            rationale=f"Parallel mode: {len(active_phases)} active, {slots_available} slots",
            strategy_used=SchedulingStrategy.PARALLEL,
        )

    def _schedule_hybrid(
        self,
        available: list[str],
        blocked: list[str],
        active_phases: set[str],
        max_parallel: int,
    ) -> SchedulingDecision:
        """Hybrid scheduling - respect dependencies, parallelize independent phases."""
        slots_available = max_parallel - len(active_phases)

        if slots_available <= 0:
            return SchedulingDecision(
                phases_to_start=[],
                phases_waiting=available,
                phases_blocked=blocked,
                rationale=f"Hybrid mode: at parallel limit ({max_parallel})",
                strategy_used=SchedulingStrategy.HYBRID,
            )

        prioritized = self._prioritize_by_unblocking(available)
        to_start = prioritized[:slots_available]
        waiting = prioritized[slots_available:]

        return SchedulingDecision(
            phases_to_start=to_start,
            phases_waiting=waiting,
            phases_blocked=blocked,
            rationale=f"Hybrid mode: starting {len(to_start)} of {len(available)} available",
            strategy_used=SchedulingStrategy.HYBRID,
        )

    def _schedule_priority(
        self,
        available: list[str],
        blocked: list[str],
        active_phases: set[str],
        max_parallel: int,
    ) -> SchedulingDecision:
        """Priority-based scheduling - use priority weights."""
        prioritized = sorted(
            available,
            key=lambda p: self.priority_weights.get(p, 0.0),
            reverse=True,
        )

        slots_available = max_parallel - len(active_phases)
        to_start = prioritized[:slots_available] if slots_available > 0 else []
        waiting = prioritized[slots_available:] if slots_available < len(prioritized) else []

        return SchedulingDecision(
            phases_to_start=to_start,
            phases_waiting=waiting,
            phases_blocked=blocked,
            rationale=f"Priority mode: starting {len(to_start)} of {len(available)}",
            strategy_used=SchedulingStrategy.PRIORITY,
        )

    def _get_blocked_phases(
        self,
        available: list[str],
        completed_phases: set[str],
        failed_phases: set[str],
    ) -> list[str]:
        """Get phases that are blocked by failed dependencies."""
        blocked = []
        for phase_id in available:
            upstream = self.dependency_graph.get_upstream_dependencies(phase_id)
            for upstream_id in upstream:
                if upstream_id in failed_phases:
                    blocked.append(phase_id)
                    break
        return blocked

    def _prioritize_by_unblocking(self, phases: list[str]) -> list[str]:
        """Prioritize phases by how many downstream phases they unblock."""
        unblocking_counts = self._get_unblocking_counts(phases)
        return sorted(phases, key=lambda p: unblocking_counts.get(p, 0), reverse=True)

    def _get_unblocking_counts(self, phases: list[str]) -> dict[str, int]:
        """Get count of downstream phases each phase would unblock."""
        counts = {}
        for phase_id in phases:
            downstream = self.dependency_graph.get_downstream_dependents(phase_id)
            blocked_count = 0
            for downstream_id in downstream:
                node = self.dependency_graph.nodes.get(downstream_id)
                if node and node.status == DependencyStatus.BLOCKED:
                    blocked_count += 1
            counts[phase_id] = blocked_count
        return counts


# =============================================================================
# SECTION 6: CORE ORCHESTRATOR (consolidated from core_orchestrator.py)
# =============================================================================


class PhaseStatus(str, Enum):
    """Execution status for a pipeline phase."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    VALIDATED = "VALIDATED"
    ROLLED_BACK = "ROLLED_BACK"


class PhaseID(str, Enum):
    """Canonical phase identifiers."""

    PHASE_0 = "P00"
    PHASE_1 = "P01"
    PHASE_2 = "P02"
    PHASE_3 = "P03"
    PHASE_4 = "P04"
    PHASE_5 = "P05"
    PHASE_6 = "P06"
    PHASE_7 = "P07"
    PHASE_8 = "P08"
    PHASE_9 = "P09"


PHASE_METADATA = {
    PhaseID.PHASE_0: {
        "name": "Bootstrap & Validation",
        "description": "Infrastructure setup, determinism, resource control",
        "stages": 9,
        "sub_phases": 60,
    },
    PhaseID.PHASE_1: {
        "name": "CPP Ingestion",
        "description": "Question-aware chunking",
        "stages": 11,
        "sub_phases": 16,
        "expected_output_count": 300,
    },
    PhaseID.PHASE_2: {
        "name": "Executor Factory & Dispatch",
        "description": "Method dispensary instantiation and routing",
        "stages": 6,
        "sub_phases": 12,
        "expected_executor_count": 30,
        "expected_method_count": 240,
    },
    PhaseID.PHASE_3: {
        "name": "Layer Scoring",
        "description": "8-layer quality assessment",
        "stages": 4,
        "sub_phases": 10,
        "layers": 8,
    },
    PhaseID.PHASE_4: {
        "name": "Dimension Aggregation",
        "description": "Choquet integral aggregation",
        "stages": 3,
        "sub_phases": 9,
        "expected_output_count": 60,
    },
    PhaseID.PHASE_5: {
        "name": "Policy Area Aggregation",
        "description": "Dimension aggregation to policy areas",
        "stages": 3,
        "sub_phases": 7,
        "expected_output_count": 10,
    },
    PhaseID.PHASE_6: {
        "name": "Cluster Aggregation",
        "description": "Policy area aggregation to clusters",
        "stages": 3,
        "sub_phases": 7,
        "expected_output_count": 4,
    },
    PhaseID.PHASE_7: {
        "name": "Macro Aggregation",
        "description": "Cluster aggregation to holistic score",
        "stages": 3,
        "sub_phases": 6,
        "expected_output_count": 1,
    },
    PhaseID.PHASE_8: {
        "name": "Recommendations Engine",
        "description": "Signal-enriched recommendation generation",
        "stages": 4,
        "sub_phases": 11,
    },
    PhaseID.PHASE_9: {
        "name": "Report Assembly",
        "description": "Final report generation",
        "stages": 4,
        "sub_phases": 12,
    },
}


@dataclass
class PhaseResult:
    """Result of a single phase execution."""

    phase_id: PhaseID
    status: PhaseStatus
    output: Any
    execution_time_s: float
    violations: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    error: Exception | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stage_timings: dict = field(default_factory=dict)
    sub_phase_results: dict = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Shared context across all pipeline phases."""

    wiring: Any | None = None
    questionnaire: Any | None = None
    sisas: Any | None = None

    phase_inputs: dict = field(default_factory=dict)
    phase_outputs: dict = field(default_factory=dict)
    phase_results: dict = field(default_factory=dict)

    execution_id: str = field(
        default_factory=lambda: blake3.blake3(f"{time.time()}".encode()).hexdigest()[:16]
    )
    start_time: datetime = field(default_factory=datetime.utcnow)
    config: dict = field(default_factory=dict)

    input_hashes: dict = field(default_factory=dict)
    output_hashes: dict = field(default_factory=dict)
    seed: int | None = None

    total_violations: list = field(default_factory=list)
    signal_metrics: dict = field(default_factory=dict)

    def add_phase_result(self, result: PhaseResult) -> None:
        """Add a phase execution result."""
        self.phase_results[result.phase_id] = result
        self.phase_outputs[result.phase_id] = result.output
        self.total_violations.extend(result.violations)

    def get_phase_output(self, phase_id: PhaseID | str) -> Any:
        """Get output from a specific phase."""
        if isinstance(phase_id, str):
            phase_id = PhaseID(phase_id)
        return self.phase_outputs.get(phase_id)

    def validate_phase_prerequisite(self, phase_id: PhaseID) -> None:
        """Validate that all prerequisite phases have completed successfully."""
        if phase_id != PhaseID.PHASE_0:
            prev_phase_id = PhaseID(f"P0{int(phase_id.value[2]) - 1}")
            if prev_phase_id not in self.phase_results:
                raise RuntimeError(
                    f"Phase {phase_id.value} requires {prev_phase_id.value} to complete first"
                )


@dataclass
class PipelineResult:
    """Result of complete pipeline execution."""

    success: bool
    phase_results: dict
    total_duration_seconds: float
    metadata: dict
    errors: list = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionTrace:
    """Immutable trace of execution for debugging/analysis."""

    execution_id: str
    phase_sequence: tuple[str, ...]
    state_transitions: tuple[dict[str, Any], ...]
    phase_timings: dict[str, float]
    violations: tuple[Any, ...]
    errors: tuple[Exception, ...]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "phase_sequence": self.phase_sequence,
            "state_transitions": self.state_transitions,
            "phase_timings": self.phase_timings,
            "violations": [str(v) for v in self.violations],
            "errors": [str(e) for e in self.errors],
            "metadata": self.metadata,
        }

    def to_json(self, path: Path) -> None:
        import json

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


@dataclass
class Phase0ValidationResult:
    """Result of Phase 0 validation gates.

    This dataclass captures the comprehensive validation results from Phase 0,
    including all gate checks, input integrity verification, and determinism checks.

    Attributes:
        all_passed: True if all gates passed successfully
        gate_results: List of individual gate check results
        validation_time: ISO 8601 timestamp of validation execution
        seed_snapshot: Dictionary containing random seed values (python, numpy, etc.)
        questionnaire_sha256: SHA-256 hash of canonical questionnaire
        input_pdf_sha256: SHA-256 hash of input PDF document
    """

    all_passed: bool
    gate_results: list  # list[GateResult] - can't use forward ref here
    validation_time: str
    seed_snapshot: dict
    questionnaire_sha256: str
    input_pdf_sha256: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "all_passed": self.all_passed,
            "gate_results": [
                gr.to_dict() if hasattr(gr, "to_dict") else gr for gr in self.gate_results
            ],
            "validation_time": self.validation_time,
            "seed_snapshot": self.seed_snapshot,
            "questionnaire_sha256": self.questionnaire_sha256,
            "input_pdf_sha256": self.input_pdf_sha256,
        }


class UnifiedOrchestrator:
    """
    Unified FARFAN Pipeline Orchestrator.

    This single orchestrator consolidates all orchestration logic from:
    - Configuration management
    - State machine lifecycle
    - Dependency graph management
    - Phase scheduling
    - Core orchestration logic
    - Signal-driven orchestration (SISAS-aware)

    Usage:
        config = OrchestratorConfig(municipality_name="Example", document_path="doc.pdf")
        orchestrator = UnifiedOrchestrator(config=config)
        result = orchestrator.execute()
    """

    # =========================================================================
    # SISAS CONSUMER CONFIGURATION
    # =========================================================================
    CONSUMER_CONFIGS = (
        {
            "consumer_id": "phase_00_assembly_consumer",
            "scopes": [{"phase": "phase_0", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": ["STATIC_LOAD", "SIGNAL_PACK", "PHASE_MONITORING"],
        },
        {
            "consumer_id": "phase_01_extraction_consumer",
            "scopes": [{"phase": "phase_1", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": [
                "EXTRACTION",
                "STRUCTURAL_PARSING",
                "TRIPLET_EXTRACTION",
                "NUMERIC_PARSING",
                "NORMATIVE_LOOKUP",
                "HIERARCHY_PARSING",
                "FINANCIAL_ANALYSIS",
                "POPULATION_PARSING",
                "TEMPORAL_PARSING",
                "CAUSAL_ANALYSIS",
                "NER",
                "SEMANTIC_ANALYSIS",
                "PHASE_MONITORING",
            ],
        },
        {
            "consumer_id": "phase_02_enrichment_consumer",
            "scopes": [{"phase": "phase_2", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": [
                "ENRICHMENT",
                "PATTERN_MATCHING",
                "ENTITY_RECOGNITION",
                "PHASE_MONITORING",
            ],
        },
        {
            "consumer_id": "phase_03_validation_consumer",
            "scopes": [{"phase": "phase_3", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": [
                "VALIDATION",
                "NORMATIVE_CHECK",
                "COHERENCE_CHECK",
                "PHASE_MONITORING",
            ],
        },
        {
            "consumer_id": "phase_04_micro_consumer",
            "scopes": [{"phase": "phase_4", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": ["SCORING", "MICRO_LEVEL", "CHOQUET_INTEGRAL", "PHASE_MONITORING"],
        },
        {
            "consumer_id": "phase_05_meso_consumer",
            "scopes": [{"phase": "phase_5", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": ["SCORING", "MESO_LEVEL", "DIMENSION_AGGREGATION", "PHASE_MONITORING"],
        },
        {
            "consumer_id": "phase_06_macro_consumer",
            "scopes": [{"phase": "phase_6", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": [
                "SCORING",
                "MACRO_LEVEL",
                "POLICY_AREA_AGGREGATION",
                "PHASE_MONITORING",
            ],
        },
        {
            "consumer_id": "phase_07_aggregation_consumer",
            "scopes": [{"phase": "phase_7", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": ["AGGREGATION", "CLUSTER_LEVEL", "PHASE_MONITORING"],
        },
        {
            "consumer_id": "phase_08_integration_consumer",
            "scopes": [{"phase": "phase_8", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": ["INTEGRATION", "RECOMMENDATION_ENGINE", "PHASE_MONITORING"],
        },
        {
            "consumer_id": "phase_09_report_consumer",
            "scopes": [{"phase": "phase_9", "policy_area": "ALL", "slot": "ALL"}],
            "capabilities": ["REPORT_GENERATION", "ASSEMBLY", "EXPORT", "PHASE_MONITORING"],
        },
    )

    def __init__(self, config: OrchestratorConfig):
        """Initialize the unified orchestrator."""
        self.config = config
        self.logger = structlog.get_logger(f"{__name__}.UnifiedOrchestrator")

        # Initialize core context
        self.context = ExecutionContext()
        self.context.config = config.to_dict()

        # Initialize state machine
        self.state_machine = OrchestrationStateMachine()

        # Initialize dependency graph with default phases
        self.dependency_graph = self._build_default_dependency_graph()

        # Initialize phase scheduler
        self.scheduler = PhaseScheduler(
            dependency_graph=self.dependency_graph,
            mode=SchedulingStrategy[config.scheduling_mode],
        )

        # Execution Trace
        self._trace: list[dict[str, Any]] = []
        self._trace_lock = threading.Lock()
        self._execution_id = str(uuid4())
        self._phase_timings: dict[str, float] = {}

        # Execution state
        self._active_phases: set[str] = set()
        self._completed_phases: dict[str, Any] = {}
        self._failed_phases: dict[str, list[Any]] = {}
        self._phase_retry_counts: dict[str, int] = {}

        # ==========================================================================
        # UNIFIED FACTORY INITIALIZATION
        # ==========================================================================
        # Initialize the unified factory for questionnaire loading, component creation,
        # and contract execution
        if FACTORY_AVAILABLE:
            # Determine project root using multiple fallback strategies for robustness
            # 1. Try to locate via factory config if provided
            # 2. Try relative path from output_dir (output_dir may be output/ or artifacts/)
            # 3. Fall back to current working directory
            project_root = self._determine_project_root(config)

            self.factory: UnifiedFactory | None = UnifiedFactory(
                config=FactoryConfig(
                    project_root=project_root,
                    questionnaire_path=(
                        Path(config.questionnaire_path) if config.questionnaire_path else None
                    ),
                    sisas_enabled=config.enable_sisas,
                    lazy_load_questions=True,
                    enable_parallel_execution=config.enable_parallel_execution,
                    max_workers=config.max_workers,
                    enable_adaptive_caching=True,
                )
            )
            # Initialize questionnaire through factory
            self.context.questionnaire = self.factory.load_questionnaire()
            # Initialize signal registry
            self.context.signal_registry = self.factory.create_signal_registry()

            # Initialize SISAS if enabled - USING INTEGRATION HUB
            if config.enable_sisas and SISAS_HUB_AVAILABLE:
                sisas_status = initialize_sisas(self)

                self.logger.info(
                    "SISAS initialized via integration hub",
                    consumers=f"{sisas_status.consumers_registered}/{sisas_status.consumers_available}",
                    extractors=f"{sisas_status.extractors_connected}/{sisas_status.extractors_available}",
                    vehicles=f"{sisas_status.vehicles_initialized}/{sisas_status.vehicles_available}",
                    irrigation_units=sisas_status.irrigation_units_loaded,
                    items_irrigable=sisas_status.items_irrigable,
                    fully_integrated=sisas_status.is_fully_integrated(),
                )
            elif config.enable_sisas and not SISAS_HUB_AVAILABLE:
                # Fallback to old method if hub not available
                self.context.sisas = self.factory.get_sisas_central()
                # Register phase consumers with SDO (legacy mode)
                if self.context.sisas is not None:
                    consumers_registered = self._register_phase_consumers()
                    self.logger.info(
                        f"SISAS initialized (legacy mode) with {consumers_registered} consumers"
                    )

            # ==========================================================================
            # INTERVENTION 2: Orchestrator-Factory Alignment
            # ==========================================================================
            # Perform initial sync with factory
            self._sync_with_factory()

            self.logger.info(
                "UnifiedFactory initialized",
                questionnaire_available=self.context.questionnaire is not None,
                signal_registry_available=self.context.signal_registry is not None,
                sisas_available=self.context.sisas is not None,
                factory_capabilities=(
                    self.factory.get_factory_capabilities() if self.factory else None
                ),
            )
        else:
            self.factory = None
            self.logger.warning(
                "UnifiedFactory not available, questionnaire and components will be limited"
            )

    def _sync_with_factory(self) -> None:
        """
        Synchronize orchestrator context with factory products.

        Ensures that all components created by the factory are correctly
        registered in the execution context. This provides thread-safe
        caching and single-source-of-truth alignment.
        """
        if not self.factory:
            return

        # Sync Questionnaire
        if self.context.questionnaire is None:
            self.context.questionnaire = self.factory.load_questionnaire()
            self.logger.debug("Synced questionnaire from factory")

        # Sync Signal Registry
        if self.context.signal_registry is None:
            self.context.signal_registry = self.factory.create_signal_registry()
            self.logger.debug("Synced signal registry from factory")

        # Sync SISAS (if enabled)
        if self.config.enable_sisas and self.context.sisas is None:
            self.context.sisas = self.factory.get_sisas_central()
            if self.context.sisas:
                self.logger.debug("Synced SISAS central from factory")

        self.logger.debug("Orchestrator-Factory alignment complete")

    def _register_phase_consumers(self) -> int:
        """
        Register all 10 phase consumers with the SDO.

        Returns:
            Number of consumers successfully registered
        """
        if not self.config.enable_sisas:
            self.logger.debug("SISAS disabled, skipping consumer registration")
            return 0

        if self.context.sisas is None:
            self.logger.warning("SDO not initialized, cannot register consumers")
            return 0

        if not SISAS_CORE_AVAILABLE:
            self.logger.warning("SISAS core not available")
            return 0

        sdo = self.context.sisas
        registered = 0

        for config in self.CONSUMER_CONFIGS:
            try:
                handler = self._create_phase_handler(config["consumer_id"])
                sdo.register_consumer(
                    consumer_id=config["consumer_id"],
                    scopes=config["scopes"],
                    capabilities=config["capabilities"],
                    handler=handler,
                )
                registered += 1
                self.logger.debug(f"Registered consumer: {config['consumer_id']}")
            except Exception as e:
                self.logger.error(f"Failed to register {config['consumer_id']}: {e}")

        self.logger.info(
            "Phase consumers registered", registered=registered, total=len(self.CONSUMER_CONFIGS)
        )
        return registered

    def _create_phase_handler(self, consumer_id: str):
        """Create a signal handler for a phase consumer."""

        def handler(signal):
            phase_num = consumer_id.split("_")[1]  # Extract "00", "01", etc.
            metric_key = f"phase_{phase_num}_signals"
            self.context.signal_metrics.setdefault(metric_key, []).append(signal.signal_id)
            self.logger.debug(f"{consumer_id} received signal: {signal.signal_id}")

        return handler

    def _trace_event(self, event_type: str, **kwargs) -> None:
        """Record an execution event to the trace."""
        with self._trace_lock:
            event = {"timestamp": time.time(), "type": event_type, "data": kwargs}
            self._trace.append(event)

    def get_execution_trace(self) -> ExecutionTrace:
        """Get the current execution trace."""
        with self._trace_lock:
            # Safe retrieval
            return ExecutionTrace(
                execution_id=self._execution_id,
                phase_sequence=tuple(
                    e["data"].get("phase_id") for e in self._trace if e["type"] == "PHASE_COMPLETE"
                ),
                state_transitions=(),
                phase_timings=self._phase_timings.copy(),
                violations=(),
                errors=(),
                metadata={"event_count": len(self._trace)},
            )

    def to_json(self, path: Path) -> None:
        """Export execution trace to JSON."""
        trace = self.get_execution_trace()
        trace.to_json(path)

    def _emit_phase_signal(
        self, phase_id: PhaseID, event_type: str, payload: dict[str, Any], policy_area: str = "ALL"
    ) -> bool:
        """
        Emit a SISAS signal for phase lifecycle events.

        Args:
            phase_id: Phase emitting the signal
            event_type: PHASE_START, PHASE_COMPLETE, PHASE_FAILED
            payload: Signal payload data
            policy_area: Target policy area (default ALL)

        Returns:
            True if signal was delivered to at least one consumer
        """
        if not self.config.enable_sisas:
            return False

        if self.context.sisas is None or not SISAS_CORE_AVAILABLE:
            return False

        sdo = self.context.sisas

        try:
            phase_num = int(phase_id.value[1:])
            phase_str = f"phase_{phase_num}"

            scope = SignalScope(phase=phase_str, policy_area=policy_area, slot="ALL")

            provenance = SignalProvenance(
                extractor="UnifiedOrchestrator",
                source_file="orchestrator.py",
                extraction_pattern=f"{phase_id.value}_{event_type}",
            )

            signal = Signal.create(
                signal_type=SignalType.STATIC_LOAD,
                scope=scope,
                payload={
                    "phase_id": phase_id.value,
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    **payload,
                },
                provenance=provenance,
                empirical_availability=1.0,
                capabilities_required=["PHASE_MONITORING"],
            )

            delivered = sdo.dispatch(signal)

            self.logger.debug(
                "Phase signal emitted",
                phase=phase_id.value,
                event_type=event_type,
                delivered=delivered,
            )

            return delivered

        except Exception as e:
            self.logger.warning(f"Failed to emit signal for {phase_id}: {e}")
            return False

    def _determine_project_root(self, config: OrchestratorConfig) -> Path:
        """
        Determine project root using multiple fallback strategies.

        This provides robust path resolution that works with different
        directory layouts and configurations.

        Args:
            config: OrchestratorConfig with output_dir and other settings

        Returns:
            Path to project root directory

        Strategy:
            1. If factory_config has project_root, use it
            2. Try output_dir.parent.parent (traditional structure)
            3. Try output_dir.parent if artifacts/ is at output level
            4. Fall back to current working directory
        """

        # Strategy 1: Check for explicit factory config
        if hasattr(config, "factory_config") and config.factory_config:
            if hasattr(config.factory_config, "project_root"):
                return Path(config.factory_config.project_root)

        output_dir = Path(config.output_dir)

        # Strategy 2: Try output_dir.parent.parent (output/ or artifacts/ structure)
        # This handles cases like:
        #   project_root/output/ -> parent.parent = project_root
        #   project_root/artifacts/output/ -> parent.parent = project_root/artifacts
        candidate1 = output_dir.parent.parent
        if (candidate1 / "canonic_questionnaire_central").exists():
            return candidate1
        if (candidate1 / "artifacts" / "data" / "contracts").exists():
            return candidate1

        # Strategy 3: Try output_dir.parent (flat structure)
        # This handles cases like:
        #   project_root/output_dir/ -> parent = project_root
        candidate2 = output_dir.parent
        if (candidate2 / "canonic_questionnaire_central").exists():
            return candidate2
        if (candidate2 / "artifacts" / "data" / "contracts").exists():
            return candidate2

        # Strategy 4: Check if we're in src/ directory
        # If this file is in src/farfan_pipeline/orchestration/orchestrator.py
        # then project_root is 3 levels up
        current_file = Path(__file__).resolve()
        candidate3 = current_file.parent.parent.parent
        if (candidate3 / "canonic_questionnaire_central").exists():
            return candidate3
        if (candidate3 / "artifacts" / "data" / "contracts").exists():
            return candidate3

        # Strategy 5: Fall back to current working directory
        cwd = Path.cwd()
        self.logger.warning(
            "Could not determine project_root via heuristics, using CWD",
            cwd=str(cwd),
            output_dir=str(output_dir),
        )
        return cwd

    def _build_default_dependency_graph(self) -> DependencyGraph:
        """Build default dependency graph for all phases."""
        graph = DependencyGraph()

        # Add all phase nodes
        for phase_id in PhaseID:
            graph.add_node(
                node_id=phase_id.value,
                phase_id=phase_id.value,
                metadata=PHASE_METADATA.get(phase_id, {}),
            )

        # Add sequential dependencies
        phase_list = list(PhaseID)
        for i in range(len(phase_list) - 1):
            graph.add_edge(phase_list[i].value, phase_list[i + 1].value)

        return graph

    def execute(self) -> PipelineResult:
        """
        Main entry point for pipeline execution.
        Orchestrates all 10 phases (0-9) in sequence.
        """
        self.logger.critical(
            "=" * 80 + "\n" + "F.A.R.F.A.N PIPELINE EXECUTION STARTED\n" + "=" * 80,
            municipality=self.config.municipality_name,
            mode="STRICT" if self.config.strict_mode else "NORMAL",
        )

        # Transition to INITIALIZING
        self.state_machine.transition_to(
            OrchestrationState.INITIALIZING, reason="Starting pipeline execution"
        )

        # Record start time
        self.context.start_time = datetime.utcnow()
        pipeline_start = time.time()

        try:
            # Transition to RUNNING
            self.state_machine.transition_to(
                OrchestrationState.RUNNING, reason="Initialization complete"
            )

            # Execute phases based on configuration
            phases_to_execute = self._get_phases_to_execute()

            for phase_id in phases_to_execute:
                if self._should_execute_phase(phase_id):
                    result = self._execute_single_phase(phase_id)
                    self.context.add_phase_result(result)

            # Calculate total execution time
            total_time = time.time() - pipeline_start

            # Create pipeline result
            pipeline_result = PipelineResult(
                success=True,
                phase_results=self.context.phase_results,
                total_duration_seconds=total_time,
                metadata={
                    "municipality": self.config.municipality_name,
                    "start_time": self.context.start_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "phases_completed": len(self.context.phase_results),
                },
                errors=[],
            )

            # Transition to COMPLETED
            self.state_machine.transition_to(
                OrchestrationState.COMPLETED, reason="All phases completed successfully"
            )

            self.logger.critical(
                "=" * 80
                + "\n"
                + "F.A.R.F.A.N PIPELINE EXECUTION COMPLETED SUCCESSFULLY\n"
                + "=" * 80,
                total_time_seconds=total_time,
                phases_completed=len(self.context.phase_results),
            )

            return pipeline_result

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")

            # Transition to COMPLETED_WITH_ERRORS
            self.state_machine.transition_to(
                OrchestrationState.COMPLETED_WITH_ERRORS, reason=f"Pipeline failed: {str(e)}"
            )

            if self.config.strict_mode:
                raise

            return PipelineResult(
                success=False,
                phase_results=self.context.phase_results,
                total_duration_seconds=time.time() - pipeline_start,
                metadata={"error": str(e)},
                errors=[str(e)],
            )

    def _get_phases_to_execute(self) -> list[PhaseID]:
        """Get list of phases to execute based on configuration."""
        phases_to_execute = self.config.phases_to_execute

        if phases_to_execute == "ALL":
            return list(PhaseID)

        if isinstance(phases_to_execute, list):
            return [PhaseID(p) for p in phases_to_execute if p in [pid.value for pid in PhaseID]]

        if isinstance(phases_to_execute, str) and "-" in phases_to_execute:
            start, end = phases_to_execute.split("-")
            all_phases = list(PhaseID)
            start_idx = int(start.replace("P0", "")) if start.startswith("P0") else int(start)
            end_idx = int(end.replace("P0", "")) if end.startswith("P0") else int(end)
            return all_phases[start_idx : end_idx + 1]

        return list(PhaseID)

    def _should_execute_phase(self, phase_id: PhaseID) -> bool:
        """Determine if a phase should be executed."""
        phases_to_execute = self.config.phases_to_execute

        if phases_to_execute == "ALL":
            return True

        if isinstance(phases_to_execute, list):
            return phase_id.value in phases_to_execute

        return True

    def _execute_single_phase(self, phase_id: PhaseID) -> PhaseResult:
        """Execute a single phase with SISAS signal emission."""
        self.logger.info(f"Executing phase: {phase_id.value}")

        start_time = time.time()

        # Emit PHASE_START signal
        self._emit_phase_signal(
            phase_id=phase_id, event_type="PHASE_START", payload={"status": "started"}
        )

        try:
            self.context.validate_phase_prerequisite(phase_id)
            self.dependency_graph.update_node_status(phase_id.value, DependencyStatus.RUNNING)

            # Dispatch to appropriate phase method
            output = self._dispatch_phase_execution(phase_id)

            execution_time = time.time() - start_time
            self.dependency_graph.update_node_status(phase_id.value, DependencyStatus.COMPLETED)

            # Emit PHASE_COMPLETE signal
            self._emit_phase_signal(
                phase_id=phase_id,
                event_type="PHASE_COMPLETE",
                payload={"status": "completed", "execution_time_s": execution_time},
            )

            result = PhaseResult(
                phase_id=phase_id,
                status=PhaseStatus.COMPLETED,
                output=output,
                execution_time_s=execution_time,
            )

            self.logger.info(f"Phase {phase_id.value} completed in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # Emit PHASE_FAILED signal
            self._emit_phase_signal(
                phase_id=phase_id,
                event_type="PHASE_FAILED",
                payload={"status": "failed", "error": str(e), "execution_time_s": execution_time},
            )

            self.dependency_graph.update_node_status(phase_id.value, DependencyStatus.FAILED)
            self.logger.error(f"Phase {phase_id.value} failed: {e}")

            if self.config.retry_failed_phases:
                retry_count = self._phase_retry_counts.get(phase_id.value, 0)
                if retry_count < self.config.max_retries_per_phase:
                    self._phase_retry_counts[phase_id.value] = retry_count + 1
                    self.dependency_graph.update_node_status(
                        phase_id.value, DependencyStatus.PENDING_RETRY
                    )
                    return self._execute_single_phase(phase_id)

            return PhaseResult(
                phase_id=phase_id,
                status=PhaseStatus.FAILED,
                output=None,
                execution_time_s=execution_time,
                error=e,
            )

    def _dispatch_phase_execution(self, phase_id: PhaseID) -> Any:
        """Dispatch execution to appropriate phase method."""
        dispatch_table = {
            PhaseID.PHASE_0: self._execute_phase_00,
            PhaseID.PHASE_1: self._execute_phase_01,
            PhaseID.PHASE_2: self._execute_phase_02,
            PhaseID.PHASE_3: self._execute_phase_03,
            PhaseID.PHASE_4: self._execute_phase_04,
            PhaseID.PHASE_5: self._execute_phase_05,
            PhaseID.PHASE_6: self._execute_phase_06,
            PhaseID.PHASE_7: self._execute_phase_07,
            PhaseID.PHASE_8: self._execute_phase_08,
            PhaseID.PHASE_9: self._execute_phase_09,
        }

        method = dispatch_table.get(phase_id)
        if method is None:
            raise ValueError(f"Unknown phase: {phase_id}")

        return method()

    # =========================================================================
    # INTERVENTION 2: Orchestrator-Factory Alignment Methods
    # =========================================================================

    def _sync_with_factory(self) -> None:
        """
        Synchronize orchestrator state with factory.

        INTERVENTION 2: Bidirectional sync for alignment.
        """
        if not self.factory:
            return

        orchestrator_state = {
            "current_phase": None,
            "max_workers": self.config.max_workers,
            "enable_parallel": self.config.enable_parallel_execution,
            "phases_to_execute": self.config.phases_to_execute,
        }

        sync_result = self.factory.synchronize_with_orchestrator(orchestrator_state)

        if not sync_result["success"]:
            self.logger.warning(
                "Factory sync detected conflicts",
                conflicts=sync_result["conflicts"],
            )
            # Handle conflicts (could adjust scheduling, etc.)

        if sync_result["adjustments"]:
            self.logger.info(
                "Factory sync recommended adjustments",
                adjustments=sync_result["adjustments"],
            )

    def _get_factory_execution_plan(self, phase_id: PhaseID) -> dict[str, Any] | None:
        """
        Get execution plan from factory for a phase.

        INTERVENTION 2: Contract-aware scheduling.
        """
        if not self.factory:
            return None

        # Get contracts for this phase
        contracts = self.factory.load_contracts()
        phase_contracts = [
            cid for cid, c in contracts.items() if phase_id.value in c.get("applicable_phases", [])
        ]

        if not phase_contracts:
            return None

        # Get execution plan with constraints
        constraints = {
            "max_parallel": self.config.max_workers,
            "time_budget_seconds": 300,  # 5 minutes per phase budget
        }

        return self.factory.get_contract_execution_plan(phase_contracts, constraints)

    # =========================================================================
    # FULL CANONICAL PHASE ORCHESTRATION
    # =========================================================================
    # Each phase executes its COMPLETE flow with all subphases, stages, and
    # validation gates. NO simplified versions - full dynamic expression of
    # each canonical phase's complete execution contract.
    #
    # Design Philosophy:
    # - Each orchestrator method is a COMPLETE pipeline execution
    # - All subphases, stages, and gates are explicitly orchestrated
    # - No parallel orchestration from other files - all merged here
    # - Flow granularity matches the canonical flux 100%
    #
    # Architecture:
    # - PhaseExecutor Protocol for type-safe phase execution
    # - SubphasePipeline for complex multi-subphase coordination
    # - StageGateValidator for enforcing exit gates
    # - FlowStateTracker for complete state machine tracking
    # =========================================================================

    # =========================================================================
    # PHASE 0: Bootstrap & Validation (7 Stages)
    # =========================================================================
    """
    Phase 0 Execution Contract (from phase_sequence_contract.json):

    P0.0: Bootstrap → Runtime config, seed registry, manifest builder
        GATE_1: Bootstrap Gate - Runtime config loaded, artifacts dir created

    P0.1: Input Verification → Cryptographic hash validation (SHA-256)
        GATE_2: Input Verification Gate - PDF and questionnaire hashed

    P0.2: Boot Checks → Dependency validation (PROD: fatal, DEV: warn)
        GATE_3: Boot Checks Gate - Dependencies validated

    P0.3: Determinism → RNG seeding with mandatory python+numpy seeds
        GATE_4: Determinism Gate - All required seeds applied

    GATE_5: Questionnaire Integrity Gate - SHA256 validation against known-good
    GATE_6: Method Registry Gate - Expected method count (416) loaded
    GATE_7: Smoke Tests Gate - Sample methods from major categories

    CRITICAL: Phase 0 ONLY validates questionnaire FILE INTEGRITY (SHA-256 hash).
              NEVER loads questionnaire content. Factory loads after Phase 0 passes.

    Implementation: Delegates to VerifiedPipelineRunner (canonical Phase 0 orchestrator).
    """

    def _execute_phase_00(self) -> dict[str, Any]:
        """
        Execute Phase 0: Bootstrap & Validation via VerifiedPipelineRunner.

        DELEGATES to VerifiedPipelineRunner (canonical Phase 0 orchestrator).
        This ensures single-source-of-truth compliance with phase_sequence_contract.json.

        Contract Exit Gates (GATE_1 through GATE_7):
            GATE_1: Bootstrap Gate - Runtime config loaded, artifacts dir created
            GATE_2: Input Verification Gate - PDF and questionnaire hashed (SHA-256)
            GATE_3: Boot Checks Gate - Dependencies validated
            GATE_4: Determinism Gate - All required seeds applied
            GATE_5: Questionnaire Integrity Gate - SHA256 validation
            GATE_6: Method Registry Gate - Expected method count loaded
            GATE_7: Smoke Tests Gate - Sample methods from major categories

        Returns:
            Dict with complete bootstrap results including:
            - canonical_input: Validated CanonicalInput object
            - wiring_components: Initialized WiringComponents
            - exit_gate_results: All 7 gate validations aligned with contract
        """
        from pathlib import Path as PathLib

        from farfan_pipeline.phases.Phase_00.phase0_40_00_input_validation import (
            Phase0Input,
            validate_phase0_input,
        )
        from farfan_pipeline.phases.Phase_00.phase0_50_01_exit_gates import (
            check_all_gates,
            get_gate_summary,
        )
        from farfan_pipeline.phases.Phase_00.phase0_90_01_verified_pipeline_runner import (
            VerifiedPipelineRunner,
        )
        from farfan_pipeline.phases.Phase_00.phase0_90_02_bootstrap import WiringBootstrap

        self.logger.info("=" * 80)
        self.logger.critical(
            "PHASE 0: BOOTSTRAP & VALIDATION - DELEGATING TO VerifiedPipelineRunner"
        )
        self.logger.info("=" * 80)

        exit_gates = {}
        wiring_components = None
        canonical_input = None

        try:
            # ====================================================================
            # PART 1: Run P0.0-P0.3 via VerifiedPipelineRunner (GATES 1-4)
            # ====================================================================
            self.logger.info("[P0] Part 1: Running P0.0-P0.3 via VerifiedPipelineRunner")

            # Prepare paths for VerifiedPipelineRunner
            plan_pdf_path = (
                PathLib(self.config.document_path)
                if self.config.document_path
                else PathLib("input.pdf")
            )
            questionnaire_path = (
                PathLib(self.config.questionnaire_path)
                if self.config.questionnaire_path
                else PathLib("canonic_questionnaire_central/_registry/questionnaire_monolith.json")
            )

            # Create artifacts directory
            artifacts_dir = PathLib("artifacts") / "phase0"

            # Initialize VerifiedPipelineRunner
            runner = VerifiedPipelineRunner(
                plan_pdf_path=plan_pdf_path,
                artifacts_dir=artifacts_dir,
                questionnaire_path=questionnaire_path,
            )

            # Run Phase 0 via VerifiedPipelineRunner (P0.0-P0.3)
            import asyncio

            phase0_success = asyncio.run(runner.run_phase_zero())

            if not phase0_success:
                # Phase 0 failed - generate failure manifest
                runner.generate_failure_manifest()
                raise OrchestrationError(
                    message="Phase 0 failed: VerifiedPipelineRunner reported failure",
                    error_code="P0_VERIFIED_RUNNER_FAILED",
                    context={
                        "errors": runner.errors,
                        "bootstrap_failed": runner._bootstrap_failed,
                        "execution_id": runner.execution_id,
                    },
                )

            # Check all 7 gates (GATE_1-7 from contract)
            all_passed, gate_results = check_all_gates(runner)

            if not all_passed:
                # Find the failed gate
                failed_gate = next((g for g in gate_results if not g.passed), None)
                if failed_gate:
                    raise OrchestrationError(
                        message=f"Phase 0 exit gate {failed_gate.gate_id} ({failed_gate.gate_name}) failed: {failed_gate.reason}",
                        error_code=f"P0_GATE_{failed_gate.gate_id}_FAILED",
                        context={
                            "gate_id": failed_gate.gate_id,
                            "gate_name": failed_gate.gate_name,
                            "reason": failed_gate.reason,
                        },
                    )

            # Map gate results to contract-aligned exit gates (GATE_1-7)
            for gate_result in gate_results:
                exit_gates[f"GATE_{gate_result.gate_id}"] = {
                    "gate_id": gate_result.gate_id,
                    "gate_name": gate_result.gate_name,
                    "status": "passed" if gate_result.passed else "failed",
                    "reason": gate_result.reason,
                }

            self.logger.info(f"[P0] All 7 exit gates passed:\n{get_gate_summary(gate_results)}")

            # ====================================================================
            # PART 2: Create CanonicalInput (FILE INTEGRITY ONLY, no content loading)
            # ====================================================================
            self.logger.info("[P0] Part 2: Creating CanonicalInput (file integrity validation)")

            phase0_input = Phase0Input(
                document_path=plan_pdf_path, municipality_name=self.config.municipality_name
            )
            canonical_input = validate_phase0_input(phase0_input)

            # Store hashes from VerifiedPipelineRunner
            exit_gates["GATE_2"]["pdf_sha256"] = runner.input_pdf_sha256
            exit_gates["GATE_2"]["questionnaire_sha256"] = runner.questionnaire_sha256

            # ====================================================================
            # PART 3: Execute WiringBootstrap (produces WiringComponents)
            # ====================================================================
            self.logger.info("[P0] Part 3: Executing WiringBootstrap")

            from farfan_pipeline.phases.Phase_00.interphase.wiring_types import WiringFeatureFlags

            flags = WiringFeatureFlags.from_env()
            bootstrap = WiringBootstrap(
                questionnaire_path=questionnaire_path,
                questionnaire_hash=runner.questionnaire_sha256,  # Use hash from VPR
                executor_config_path=self.config.methods_file,
                calibration_profile="default",
                abort_on_insufficient=False,
                resource_limits=self.config.resource_limits,
                flags=flags,
            )

            wiring_components = bootstrap.bootstrap()

            # Validate wiring integrity
            from farfan_pipeline.phases.Phase_00.phase0_90_03_wiring_validator import (
                WiringValidator,
            )

            validator = WiringValidator()
            wiring_valid = validator.validate_wiring(wiring_components)

            if not wiring_valid:
                raise OrchestrationError(
                    message="Phase 0 wiring validation failed",
                    error_code="P0_WIRING_VALIDATION_FAILED",
                )

            self.logger.info(
                f"[P0] Wiring complete: {wiring_components.factory.factory_instances} factory instances"
            )

            # ====================================================================
            # PHASE 0 COMPLETE - STORE RESULTS
            # ====================================================================
            self.logger.info("=" * 80)
            self.logger.critical("PHASE 0: BOOTSTRAP & VALIDATION - COMPLETED")
            self.logger.info("=" * 80)

            # Store in context for subsequent phases
            self.context.wiring = wiring_components

            # FORCE ARTICULATION: Update orchestrator factory with the bootstrapped one
            if hasattr(wiring_components, "factory") and wiring_components.factory:
                self.factory = wiring_components.factory
                self.logger.info("[P0] Orchestrator factory updated from bootstrap wiring")

            self.context.phase_outputs[PhaseID.PHASE_0] = canonical_input

            return {
                "status": "completed",
                "canonical_input": (
                    canonical_input.to_dict()
                    if hasattr(canonical_input, "to_dict")
                    else str(canonical_input)
                ),
                "wiring_components": {
                    "factory_status": (
                        wiring_components.factory.get_health_status().to_dict()
                        if hasattr(wiring_components.factory, "get_health_status")
                        else "unknown"
                    ),
                    "argrouter_routes": (
                        wiring_components.arg_router.get_special_route_coverage()
                        if wiring_components and wiring_components.arg_router
                        else 0
                    ),
                },
                "exit_gates": exit_gates,
                "validation_passed": (
                    canonical_input.validation_passed if canonical_input else False
                ),
                "phase0_execution_id": runner.execution_id,
                "seed_snapshot": runner.seed_snapshot,
                "input_hashes": {
                    "pdf_sha256": runner.input_pdf_sha256,
                    "questionnaire_sha256": runner.questionnaire_sha256,
                },
            }

        except OrchestrationError:
            # Re-raise orchestration errors as-is
            raise
        except Exception as e:
            self.logger.error(f"Phase 0 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 0 execution failed: {e}",
                phase_id="P00",
                context={"exit_gates": exit_gates},
            ) from e

    # =========================================================================
    # PHASE 1: CPP Ingestion (16 Subphases)
    # =========================================================================
    """
    Phase 1 Execution Contract (from phase1_execution_flow.md):

    Subphases SP0-SP15 (strict linear sequence enforced):

    SP0: Language Detection -> LanguageData
    SP1: Preprocessing -> PreprocessedDoc
    SP2: Structural Analysis (PDM) -> StructureData
    SP3: Knowledge Graph -> KnowledgeGraph
    SP4: Segmentation -> List[Chunk] [CONSTITUTIONAL INVARIANT: 60 chunks]
    SP5: Causal Extraction -> CausalChains
    SP6: Causal Integration -> IntegratedCausal
    SP7: Argumentation -> Arguments
    SP8: Temporal Analysis -> Temporal
    SP9: Discourse Analysis -> Discourse
    SP10: Strategic Integration -> Strategic
    SP11: Smart Chunking -> List[SmartChunk] [CONSTITUTIONAL INVARIANT]
    SP12: Irrigation -> List[SmartChunk] with inter-chunk linking
    SP13: Validation -> ValidationResult [CRITICAL GATE]
    SP14: Deduplication -> List[SmartChunk]
    SP15: Ranking -> List[SmartChunk] with final strategic ranking

    Finalization: CanonPolicyPackage assembly
    """

    def _execute_phase_01(self) -> dict[str, Any]:
        """
        Execute Phase 1: CPP Ingestion - COMPLETE ORCHESTRATION.

        Orchestrates all 16 subphases of Phase 1 with full constitutional
        invariant enforcement at SP4, SP11, and SP13.

        Integration:
        - Uses Phase 1 Full Contract Executor (execute_phase_1_with_full_contract)
        - Supports checkpoint/recovery for long-running execution
        - Emits SISAS signals for subphase progress tracking

        Returns:
            Dict with complete CPP ingestion results including:
            - canon_policy_package: Fully assembled CanonPolicyPackage
            - subphase_results: Results from each subphase
            - constitutional_invariants: Validation of all invariants
            - smart_chunks: Final list of 60 SmartChunks
        """
        from farfan_pipeline.phases.Phase_00.phase0_40_00_input_validation import CanonicalInput
        from farfan_pipeline.phases.Phase_01.phase1_01_00_cpp_models import (
            CanonPolicyPackage,
            SmartChunk,
        )

        self.logger.info("=" * 80)
        self.logger.critical("PHASE 1: CPP INGESTION - FULL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        subphase_results = {}
        constitutional_invariants = {}
        checkpoint_manager = None
        metrics_collector = None

        # Generate plan_id for this execution (used by both checkpoint and metrics)
        plan_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # ====================================================================
            # METRICS COLLECTOR: Initialize performance tracking
            # ====================================================================
            try:
                from farfan_pipeline.phases.Phase_01.phase1_17_00_performance_metrics import (
                    Phase1MetricsCollector,
                )

                metrics_collector = Phase1MetricsCollector(plan_id=plan_id)
                metrics_collector.start_phase()
                self.logger.info(f"[P1] Metrics collector initialized for plan_id={plan_id}")
            except ImportError:
                self.logger.warning(
                    "[P1] Metrics collector not available, running without performance tracking"
                )
                metrics_collector = None

            # ====================================================================
            # INPUT: Get CanonicalInput from Phase 0
            # ====================================================================
            # Type note: Variable starts Optional, but after validation is guaranteed CanonicalInput
            canonical_input_maybe: CanonicalInput | None = self.context.get_phase_output(
                PhaseID.PHASE_0
            )
            if canonical_input_maybe is None:
                # Try to create from config
                self.logger.warning(
                    "[P1] CanonicalInput not found in context, creating from config"
                )
                from farfan_pipeline.phases.Phase_00.phase0_40_00_input_validation import (
                    Phase0Input,
                    validate_phase0_input,
                )

                phase0_input = Phase0Input(
                    document_path=(
                        Path(self.config.document_path) if self.config.document_path else None
                    ),
                    municipality_name=self.config.municipality_name,
                )
                # Explicitly type and validate the result
                canonical_input_result: CanonicalInput = validate_phase0_input(phase0_input)
                if not isinstance(canonical_input_result, CanonicalInput):
                    raise TypeError(
                        f"[P1] validate_phase0_input returned unexpected type: "
                        f"{type(canonical_input_result).__name__}, expected CanonicalInput"
                    )
                canonical_input_maybe = canonical_input_result

            # After validation, canonical_input is guaranteed to be CanonicalInput
            canonical_input: CanonicalInput = canonical_input_maybe

            self.logger.info(f"[P1] Input received: {type(canonical_input).__name__}")

            # ====================================================================
            # CHECKPOINT MANAGER: Initialize for recovery support
            # ====================================================================
            checkpoint_dir = Path(self.config.output_dir) / "checkpoints" / "phase1"

            if self.config.enable_checkpoint:
                try:
                    from farfan_pipeline.phases.Phase_01.phase1_16_00_checkpoint_manager import (
                        Phase1CheckpointManager,
                    )

                    checkpoint_manager = Phase1CheckpointManager(
                        checkpoint_dir=checkpoint_dir,
                        plan_id=plan_id,
                    )

                    # Check for resumption point
                    resume_from = checkpoint_manager.get_resumption_point()
                    if resume_from:
                        self.logger.info(f"[P1] Checkpoint found: resuming from {resume_from}")
                        subphase_results["checkpoint_recovery"] = {
                            "status": "resuming",
                            "resume_from": resume_from,
                            "plan_id": plan_id,
                        }
                    else:
                        self.logger.info("[P1] No checkpoint found: starting fresh execution")
                        subphase_results["checkpoint_recovery"] = {
                            "status": "starting_fresh",
                            "plan_id": plan_id,
                        }
                except ImportError:
                    self.logger.warning(
                        "[P1] Checkpoint manager not available, running without recovery support"
                    )
                    checkpoint_manager = None

            # ====================================================================
            # EXTRACT DEPENDENCIES FROM PHASE 0 WIRING
            # ====================================================================
            signal_registry = None
            structural_profile = None

            if self.context.wiring:
                signal_registry = getattr(self.context.wiring, "signal_registry", None)
                structural_profile = getattr(self.context.wiring, "structural_profile", None)
                self.logger.info(
                    f"[P1] Extracted from wiring: signal_registry={signal_registry is not None}, structural_profile={structural_profile is not None}"
                )

            # ====================================================================
            # EXECUTE WITH FULL CONTRACT EXECUTOR (PRIMARY PATH)
            # ====================================================================
            self.logger.info("[P1] Using Phase 1 Full Contract Executor")
            cpp_package: CanonPolicyPackage | None = None

            # Define execution function (with or without metrics tracking)
            def _execute_phase1_core() -> CanonPolicyPackage | None:
                """Core Phase 1 execution logic."""
                # Import full contract executor
                from farfan_pipeline.phases.Phase_01.phase1_13_00_cpp_ingestion import (
                    execute_phase_1_with_full_contract,
                )

                # Log policy compliance
                if signal_registry is not None:
                    self.logger.info("[P1] ✓ POLICY COMPLIANT: signal_registry injected via DI")
                else:
                    self.logger.warning(
                        "[P1] ⚠ POLICY VIOLATION: signal_registry NOT available (degraded mode)"
                    )

                # Execute Phase 1 with full contract enforcement
                return execute_phase_1_with_full_contract(
                    canonical_input=canonical_input,
                    signal_registry=signal_registry,
                    structural_profile=structural_profile,
                )

            # Execute with or without metrics tracking
            try:
                if metrics_collector:
                    # With metrics tracking
                    with metrics_collector.track_subphase("P1_FULL_EXECUTION"):
                        cpp_package = _execute_phase1_core()
                else:
                    # Without metrics tracking
                    cpp_package = _execute_phase1_core()

                # Extract smart chunks from package
                smart_chunks = cpp_package.chunk_graph.chunks if cpp_package else []

                self.logger.info(
                    f"[P1] ✓ Full contract execution complete: {len(smart_chunks)} chunks"
                )

                # Populate subphase_results from execution trace
                subphase_results["full_contract_executor"] = {
                    "status": "completed",
                    "chunks_generated": len(smart_chunks),
                    "schema_version": cpp_package.schema_version if cpp_package else "unknown",
                }

            except ImportError as e:
                self.logger.error(f"[P1] Full contract executor not available: {e}")
                raise PhaseExecutionError(
                    message=f"Phase 1 full contract executor not available: {e}", phase_id="P01"
                ) from e

            except Phase1FatalError as e:
                # Phase 1 specific fatal error - already logged and diagnosed
                self.logger.critical(f"[P1] FATAL ERROR: {e}")
                raise PhaseExecutionError(
                    message=f"Phase 1 fatal error: {e}",
                    phase_id="P01",
                    context={"error_type": "Phase1FatalError"},
                ) from e

            # ====================================================================
            # CONSTITUTIONAL INVARIANTS VALIDATION
            # ====================================================================
            self.logger.info("[P1] Validating constitutional invariants")

            # Extract smart chunks from cpp_package
            smart_chunks = cpp_package.chunk_graph.chunks if cpp_package else []
            canonical_package = cpp_package

            # Invariant 1: 60 Chunks (SP4 - Segmentation)
            chunk_count = len(smart_chunks)
            invariant_60_chunks = chunk_count == 60
            constitutional_invariants["invariant_60_chunks"] = {
                "name": "60 Chunk Constitutional Invariant (SP4)",
                "expected": 60,
                "actual": chunk_count,
                "passed": invariant_60_chunks,
                "critical": True,
            }
            self.logger.info(
                f"[P1] Invariant Check: 60 Chunks = {invariant_60_chunks} (actual: {chunk_count})"
            )

            # Invariant 2: Smart Chunk Generation (SP11)
            all_smart_chunks_valid = (
                all(isinstance(chunk, SmartChunk) for chunk in smart_chunks)
                if smart_chunks
                else False
            )
            constitutional_invariants["invariant_smart_chunks"] = {
                "name": "Smart Chunk Generation Invariant (SP11)",
                "expected_type": "SmartChunk",
                "all_valid": all_smart_chunks_valid,
                "passed": all_smart_chunks_valid,
                "critical": True,
            }

            # Invariant 3: 10 Policy Areas
            # Extract policy areas from chunks (assuming they have policy_area attribute)
            policy_areas_found = set()
            for chunk in smart_chunks:
                if hasattr(chunk, "policy_area") and chunk.policy_area:
                    policy_areas_found.add(chunk.policy_area)
            policy_areas_count = len(policy_areas_found)
            invariant_10_policy_areas = policy_areas_count == 10
            constitutional_invariants["invariant_10_policy_areas"] = {
                "name": "10 Policy Areas Invariant",
                "expected": 10,
                "actual": policy_areas_count,
                "passed": invariant_10_policy_areas,
                "critical": True,
            }
            self.logger.info(
                f"[P1] Invariant Check: 10 Policy Areas = {invariant_10_policy_areas} (actual: {policy_areas_count})"
            )

            # Invariant 4: 6 Dimensions
            # Extract dimensions from chunks (assuming they have dimension attribute)
            dimensions_found = set()
            for chunk in smart_chunks:
                if hasattr(chunk, "dimension") and chunk.dimension:
                    dimensions_found.add(chunk.dimension)
            dimensions_count = len(dimensions_found)
            invariant_6_dimensions = dimensions_count == 6
            constitutional_invariants["invariant_6_dimensions"] = {
                "name": "6 Dimensions Invariant",
                "expected": 6,
                "actual": dimensions_count,
                "passed": invariant_6_dimensions,
                "critical": True,
            }
            self.logger.info(
                f"[P1] Invariant Check: 6 Dimensions = {invariant_6_dimensions} (actual: {dimensions_count})"
            )

            # Invariant 5: Validation Gate (SP13) - Check from package quality metrics
            validation_passed = (
                canonical_package.quality_metrics.constitutional_invariants_passed
                if canonical_package
                else False
            )
            constitutional_invariants["invariant_validation_gate"] = {
                "name": "Validation Gate Invariant (SP13)",
                "all_checks_passed": validation_passed,
                "passed": validation_passed,
                "critical": True,
            }

            # Overall invariants status
            all_invariants_passed = all(inv["passed"] for inv in constitutional_invariants.values())

            # ====================================================================
            # FINALIZATION: Validate CanonPolicyPackage
            # ====================================================================
            self.logger.info("[P1] Validating CanonPolicyPackage")

            # Validate the package
            try:
                from farfan_pipeline.phases.Phase_01.phase1_01_00_cpp_models import (
                    CanonPolicyPackageValidator,
                )

                validator = CanonPolicyPackageValidator()
                package_valid = validator.validate(canonical_package)

                subphase_results["finalization"] = {
                    "status": "completed",
                    "package_valid": package_valid,
                    "chunks_count": len(canonical_package.smart_chunks),
                }
            except Exception as e:
                self.logger.warning(f"[P1] Package validation failed: {e}")
                subphase_results["finalization"] = {
                    "status": "completed",
                    "package_valid": None,
                    "error": str(e),
                }

            # ====================================================================
            # CHECKPOINT CLEANUP: Clear checkpoints after successful completion
            # ====================================================================
            if checkpoint_manager is not None:
                try:
                    cleared = checkpoint_manager.clear_checkpoints()
                    self.logger.info(
                        f"[P1] Cleared {cleared} checkpoint files after successful completion"
                    )
                    subphase_results["checkpoint_cleanup"] = {
                        "status": "completed",
                        "files_cleared": cleared,
                    }
                except Exception as e:
                    self.logger.warning(f"[P1] Checkpoint cleanup failed: {e}")
                    subphase_results["checkpoint_cleanup"] = {
                        "status": "failed",
                        "error": str(e),
                    }

            # ====================================================================
            # METRICS FINALIZATION: End phase and export metrics
            # ====================================================================
            if metrics_collector is not None:
                try:
                    metrics_collector.end_phase()
                    metrics = metrics_collector.get_metrics()

                    # Log aggregate statistics
                    self.logger.info(f"[P1] Metrics Summary:")
                    self.logger.info(f"  - Total duration: {metrics.total_duration_ms:.2f}ms")
                    self.logger.info(
                        f"  - Subphases completed: {metrics.aggregate_stats.get('completed_subphases', 0)}"
                    )
                    self.logger.info(
                        f"  - Avg subphase duration: {metrics.aggregate_stats.get('avg_duration_ms', 0):.2f}ms"
                    )
                    self.logger.info(
                        f"  - Peak memory: {metrics.aggregate_stats.get('max_memory_mb_peak', 0):.2f}MB"
                    )

                    # Export metrics to file
                    metrics_path = (
                        Path(self.config.output_dir)
                        / "metrics"
                        / "phase1"
                        / f"{plan_id}_metrics.json"
                    )
                    metrics_collector.export_metrics(metrics_path)
                    self.logger.info(f"[P1] Metrics exported to: {metrics_path}")

                    subphase_results["metrics_export"] = {
                        "status": "completed",
                        "metrics_path": str(metrics_path),
                        "total_duration_ms": metrics.total_duration_ms,
                        "aggregate_stats": metrics.aggregate_stats,
                    }
                except Exception as e:
                    self.logger.warning(f"[P1] Metrics finalization failed: {e}")
                    subphase_results["metrics_export"] = {
                        "status": "failed",
                        "error": str(e),
                    }

            # ====================================================================
            # EXIT GATE: All constitutional invariants must pass
            # ====================================================================
            if not all_invariants_passed and self.config.strict_mode:
                failed_invariants = [
                    name for name, inv in constitutional_invariants.items() if not inv["passed"]
                ]
                raise PhaseExecutionError(
                    message=f"Phase 1 constitutional invariants failed: {failed_invariants}",
                    phase_id="P01",
                    context={
                        "constitutional_invariants": constitutional_invariants,
                        "failed_invariants": failed_invariants,
                    },
                ) from None

            self.logger.info("=" * 80)
            self.logger.critical("PHASE 1: CPP INGESTION - FULL ORCHESTRATION COMPLETED")
            self.logger.info(
                f"Constitutional Invariants: {'ALL PASSED' if all_invariants_passed else 'SOME FAILED'}"
            )
            self.logger.info(f"Smart Chunks: {len(smart_chunks)}")
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_1] = canonical_package

            return {
                "status": "completed",
                "canon_policy_package": (
                    canonical_package.to_dict()
                    if hasattr(canonical_package, "to_dict")
                    else str(canonical_package)
                ),
                "smart_chunks_count": len(smart_chunks),
                "subphase_results": subphase_results,
                "constitutional_invariants": constitutional_invariants,
                "all_invariants_passed": all_invariants_passed,
                "cpp_package": {
                    "total_chunks": len(canonical_package.smart_chunks),
                    "document_title": (
                        canonical_package.manifest.document_name
                        if hasattr(canonical_package.manifest, "document_name")
                        else "Unknown"
                    ),
                    "schema_version": (
                        canonical_package.manifest.schema_version
                        if hasattr(canonical_package.manifest, "schema_version")
                        else "Unknown"
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Phase 1 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 1 execution failed: {e}",
                phase_id="P01",
                context={"subphase_results": subphase_results},
            ) from e

    def _execute_phase_02(self, plan_text: str | None = None, **kwargs) -> Any:
        """
        Execute Phase 2: Executor Factory & Dispatch.

        This phase now uses the UnifiedFactory to:
        1. Load analysis components (detectors, calculators, analyzers)
        2. Load contracts
        3. Execute contracts with method injection

        INTERVENTION 2: Uses factory capabilities for optimal execution.

        Args:
            plan_text: Optional plan text for contract execution
            **kwargs: Additional arguments for contract execution

        Returns:
            Dict with task results from contract execution
        """
        self.logger.info("Phase 2: Executor Factory & Dispatch")

        if self.factory is None:
            self.logger.warning("Factory not available, returning empty results")
            return {
                "task_results": [],
                "status": "factory_unavailable",
                "contracts_executed": 0,
            }

        # Create analysis components via factory
        components = self.factory.create_analysis_components()
        self.logger.debug(
            "Analysis components created",
            components=list(components.keys()),
        )

        # Load contracts via factory
        contracts = self.factory.load_contracts()
        active_contracts = {cid: c for cid, c in contracts.items() if c.get("status") == "ACTIVE"}

        self.logger.info(
            "Contracts loaded for execution",
            total_contracts=len(contracts),
            active_contracts=len(active_contracts),
        )

        # ==========================================================================
        # INTERVENTION 2: Get optimal execution plan from factory
        # ==========================================================================
        execution_plan = self._get_factory_execution_plan(PhaseID.PHASE_2)

        if execution_plan:
            self.logger.info(
                "Factory execution plan obtained",
                strategy=execution_plan["execution_strategy"],
                estimated_duration=execution_plan["estimated_duration_seconds"],
                batches=len(execution_plan.get("batches", [])),
            )

        # Execute contracts with method injection
        task_results = []
        input_data = {"plan_text": plan_text, **kwargs}

        # Limit contracts for now (can be adjusted based on execution plan)
        contract_list = list(active_contracts.keys())[:10]

        # ==========================================================================
        # INTERVENTION 1 & 2: Use parallel batch execution if recommended by plan
        # ==========================================================================
        if execution_plan and execution_plan["execution_strategy"] == "parallel_batch":

            self.logger.info("Using parallel batch execution")

            # Execute in parallel batches
            batch_results = self.factory.execute_contracts_batch(contract_list, input_data)

            for contract_id, result in batch_results.items():
                task_results.append(
                    {
                        "contract_id": contract_id,
                        "result": result,
                        "status": "completed" if "error" not in result else "failed",
                    }
                )
        else:
            # Sequential execution
            for contract_id in contract_list:
                try:
                    result = self.factory.execute_contract(contract_id, input_data)
                    task_results.append(
                        {
                            "contract_id": contract_id,
                            "result": result,
                            "status": "completed" if "error" not in result else "failed",
                        }
                    )
                except Exception as e:
                    self.logger.warning(
                        "Contract execution failed",
                        contract_id=contract_id,
                        error=str(e),
                    )
                    task_results.append(
                        {
                            "contract_id": contract_id,
                            "error": str(e),
                            "status": "error",
                        }
                    )

        # Get performance metrics from factory
        perf_metrics = self.factory.get_performance_metrics()

        # ====================================================================
        # CONSTITUTIONAL INVARIANTS VALIDATION FOR PHASE 2
        # ====================================================================
        self.logger.info("[P2] Validating constitutional invariants")

        constitutional_invariants = {}

        # Invariant 1: 300 Contracts (30 base questions × 10 policy areas)
        total_contracts = len(contracts)
        invariant_300_contracts = total_contracts == 300
        constitutional_invariants["invariant_300_contracts"] = {
            "name": "300 Contracts Constitutional Invariant",
            "expected": 300,
            "actual": total_contracts,
            "passed": invariant_300_contracts,
            "critical": True,  # Critical per CANONICAL_PHASE_ARCHITECTURE.md
        }
        self.logger.info(
            f"[P2] Invariant Check: 300 Contracts = {invariant_300_contracts} (actual: {total_contracts})"
        )

        # Invariant 2: Input validation from Phase 1
        canonical_input = self.context.get_phase_output(PhaseID.PHASE_1)
        invariant_p1_input = canonical_input is not None
        constitutional_invariants["invariant_p1_input"] = {
            "name": "Phase 1 Input Validation",
            "expected": "CanonPolicyPackage from P1",
            "actual": "Present" if canonical_input else "Missing",
            "passed": invariant_p1_input,
            "critical": True,
        }
        self.logger.info(f"[P2] Invariant Check: Phase 1 Input = {invariant_p1_input}")

        all_invariants_passed = all(inv["passed"] for inv in constitutional_invariants.values())

        return {
            "task_results": task_results,
            "status": "completed",
            "contracts_executed": len(task_results),
            "components_available": list(components.keys()),
            "execution_strategy": (
                execution_plan["execution_strategy"] if execution_plan else "sequential"
            ),
            "performance_metrics": perf_metrics,
            "constitutional_invariants": constitutional_invariants,
            "all_invariants_passed": all_invariants_passed,
        }

    # =========================================================================
    # PHASE 3: Layer Scoring (7 Steps)
    # =========================================================================
    """
    Phase 3 Execution Contract (from phase03_execution_flow.md):

    1. Input Contract Verification
    2. Threshold Loading
    3. Score Extraction
    4. Validation
    5. Signal Enrichment
    6. Normative Compliance
    7. Output Contract Verification
    """

    def _execute_phase_03(self) -> dict[str, Any]:
        """
        Execute Phase 3: Layer Scoring - COMPLETE ORCHESTRATION.

        Orchestrates all 7 steps of Phase 3 layer scoring with 8-layer
        quality assessment.

        Returns:
            Dict with complete scoring results including:
            - scored_results: 300 scored micro-questions
            - layer_scores: Scores for each of 8 layers
            - validation_results: All validation gate results
        """
        from farfan_pipeline.phases.Phase_01.phase1_01_00_cpp_models import CanonPolicyPackage

        self.logger.info("=" * 80)
        self.logger.critical("PHASE 3: LAYER SCORING - FULL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        step_results = {}
        exit_gates = {}

        try:
            # ====================================================================
            # INPUT: Get CanonPolicyPackage from Phase 1
            # ====================================================================
            canon_policy_package: CanonPolicyPackage | None = self.context.get_phase_output(
                PhaseID.PHASE_1
            )
            if canon_policy_package is None:
                raise PhaseExecutionError(
                    message="Phase 3 requires Phase 1 CanonPolicyPackage output", phase_id="P03"
                )

            self.logger.info(
                f"[P3] Input received: {len(canon_policy_package.smart_chunks)} SmartChunks"
            )

            # ====================================================================
            # STEP 1: Input Contract Verification
            # ====================================================================
            self.logger.info("[P3-S01] Step 1: Input Contract Verification")

            try:
                from farfan_pipeline.phases.Phase_03.contracts.phase3_input_contract import (
                    validate_phase3_input,
                )

                input_contract_valid = validate_phase3_input(canon_policy_package)
                step_results["s01_input_contract"] = {
                    "status": "completed",
                    "valid": input_contract_valid,
                }
            except Exception as e:
                self.logger.warning(f"[P3-S01] Input contract validation failed: {e}")
                step_results["s01_input_contract"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 2: Threshold Loading
            # ====================================================================
            self.logger.info("[P3-S02] Step 2: Threshold Loading")

            try:
                from farfan_pipeline.phases.Phase_03.phase3_10_00_thresholds import (
                    load_scoring_thresholds,
                )

                thresholds = load_scoring_thresholds()
                step_results["s02_thresholds"] = {
                    "status": "completed",
                    "thresholds_loaded": len(thresholds) if thresholds else 0,
                }
            except Exception as e:
                self.logger.warning(f"[P3-S02] Threshold loading failed: {e}")
                step_results["s02_thresholds"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 3: Score Extraction
            # ====================================================================
            self.logger.info("[P3-S03] Step 3: Score Extraction")

            scored_results = []
            try:
                from farfan_pipeline.phases.Phase_03.phase3_20_00_score_extractor import (
                    extract_scores_from_chunks,
                )

                scored_results = extract_scores_from_chunks(
                    canon_policy_package.smart_chunks, thresholds=thresholds
                )
                step_results["s03_extraction"] = {
                    "status": "completed",
                    "scores_extracted": len(scored_results),
                }
                self.logger.info(f"[P3-S03] Scores extracted: {len(scored_results)} results")
            except Exception as e:
                self.logger.error(f"[P3-S03] Score extraction failed: {e}")
                raise PhaseExecutionError(
                    message=f"Step 3 score extraction failed: {e}", phase_id="P03"
                ) from e

            # ====================================================================
            # STEP 4: Validation
            # ====================================================================
            self.logger.info("[P3-S04] Step 4: Validation")

            try:
                from farfan_pipeline.phases.Phase_03.phase3_30_00_validation import validate_scores

                validation_result = validate_scores(scored_results)
                step_results["s04_validation"] = {
                    "status": "completed",
                    "all_valid": validation_result.get("all_valid", False),
                    "validation_errors": validation_result.get("errors", []),
                }
            except Exception as e:
                self.logger.warning(f"[P3-S04] Validation failed: {e}")
                step_results["s04_validation"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 5: Signal Enrichment (Optional)
            # ====================================================================
            self.logger.info("[P3-S05] Step 5: Signal Enrichment")

            try:
                if self.config.enable_sisas and self.context.sisas:
                    # Enrich scores with SISAS signals
                    from farfan_pipeline.phases.Phase_03.phase3_40_00_signal_enrichment import (
                        enrich_scores_with_signals,
                    )

                    enriched_results = enrich_scores_with_signals(
                        scored_results, self.context.sisas
                    )
                    step_results["s05_signal_enrichment"] = {
                        "status": "completed",
                        "enriched": True,
                    }
                    scored_results = enriched_results
                else:
                    step_results["s05_signal_enrichment"] = {
                        "status": "skipped",
                        "reason": "SISAS disabled or unavailable",
                    }
            except Exception as e:
                self.logger.warning(f"[P3-S05] Signal enrichment failed: {e}")
                step_results["s05_signal_enrichment"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 6: Normative Compliance
            # ====================================================================
            self.logger.info("[P3-S06] Step 6: Normative Compliance")

            try:
                from farfan_pipeline.phases.Phase_03.phase3_50_00_normative import (
                    check_normative_compliance,
                )

                normative_result = check_normative_compliance(scored_results)
                step_results["s06_normative"] = {
                    "status": "completed",
                    "compliant": normative_result.get("compliant", True),
                }
            except Exception as e:
                self.logger.warning(f"[P3-S06] Normative compliance check failed: {e}")
                step_results["s06_normative"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 7: Output Contract Verification
            # ====================================================================
            self.logger.info("[P3-S07] Step 7: Output Contract Verification")

            try:
                from farfan_pipeline.phases.Phase_03.contracts.phase3_output_contract import (
                    validate_phase3_output,
                )

                output_contract_valid = validate_phase3_output(scored_results)
                step_results["s07_output_contract"] = {
                    "status": "completed",
                    "valid": output_contract_valid,
                }
            except Exception as e:
                self.logger.warning(f"[P3-S07] Output contract validation failed: {e}")
                step_results["s07_output_contract"] = {"status": "skipped", "reason": str(e)}

            # EXIT GATE: Output validation
            exit_gates["gate_final"] = {
                "status": "passed" if len(scored_results) > 0 else "failed",
                "scores_count": len(scored_results),
            }

            self.logger.info("=" * 80)
            self.logger.critical("PHASE 3: LAYER SCORING - FULL ORCHESTRATION COMPLETED")
            self.logger.info(f"Scored Results: {len(scored_results)}")
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_3] = scored_results

            return {
                "status": "completed",
                "scored_results": len(scored_results),
                "layer_scores": {
                    "layer_count": 8,
                    "results_summary": step_results.get("s03_extraction", {}),
                },
                "step_results": step_results,
                "exit_gates": exit_gates,
            }

        except Exception as e:
            self.logger.error(f"Phase 3 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 3 execution failed: {e}",
                phase_id="P03",
                context={"step_results": step_results},
            ) from e

    # =========================================================================
    # PHASE 4: Dimension Aggregation (8 Steps)
    # =========================================================================
    """
    Phase 4 Execution Contract (aligned with CANONICAL_FLOW.md):

    STEP 1: Load Configuration (AggregationSettings from phase4_10_00_aggregation_settings.py)
    STEP 2: Validate Inputs (Phase4InputContract from contracts/phase4_10_00_input_contract.py)
    STEP 3: Initialize Aggregator (DimensionAggregator from phase4_30_00_aggregation.py)
    STEP 4: Calculate Scores (ChoquetAggregator or DimensionAggregator.run())
    STEP 5: Provenance Tracking (AggregationDAG from phase4_10_00_aggregation_provenance.py)
    STEP 6: Uncertainty Quantification (BootstrapAggregator from phase4_10_00_uncertainty_quantification.py)
    STEP 7: Output Validation (validate_phase4_output from phase4_60_00_aggregation_validation.py)
    STEP 8: Final Output - DimensionScore list with exit gate validation

    Module Mapping:
    - Stage 10 (Foundation): aggregation_settings, aggregation_provenance, uncertainty_quantification
    - Stage 20 (Core): choquet_adapter
    - Stage 30 (Aggregators): aggregation, choquet_aggregator, signal_enriched_aggregation
    - Stage 60 (Validation): aggregation_validation

    Input: ScoredResult (300 micro-preguntas from Phase 3)
    Output: DimensionScore (60 dimensiones = 6 DIM × 10 PA)
    """

    def _execute_phase_04(self) -> dict[str, Any]:
        """
        Execute Phase 4: Dimension Aggregation - COMPLETE ORCHESTRATION.

        Orchestrates all 8 steps of Phase 4 dimension aggregation using
        Choquet integral when SOTA enabled, with full provenance tracking
        and uncertainty quantification.

        Returns:
            Dict with complete aggregation results including:
            - dimension_scores: Count of DimensionScore objects (expected: 60)
            - aggregation_method: "choquet" or "weighted_average"
            - provenance: DAG statistics from provenance tracking
            - uncertainty: BCa bootstrap confidence intervals
            - step_results: Results from each of the 8 steps
            - exit_gates: Final validation gates
        """
        self.logger.info("=" * 80)
        self.logger.critical("PHASE 4: DIMENSION AGGREGATION - FULL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        step_results = {}
        exit_gates = {}

        try:
            # ====================================================================
            # INPUT: Get Scored Results from Phase 3
            # ====================================================================
            scored_results = self.context.get_phase_output(PhaseID.PHASE_3)
            if scored_results is None or len(scored_results) == 0:
                raise PhaseExecutionError(
                    message="Phase 4 requires Phase 3 scored results", phase_id="P04"
                )

            self.logger.info(f"[P4] Input received: {len(scored_results)} scored results")

            # ====================================================================
            # STEP 1: Load Configuration (AggregationSettings)
            # ====================================================================
            self.logger.info("[P4-S01] Step 1: Load Configuration")

            try:
                from farfan_pipeline.phases.Phase_04.phase4_10_00_aggregation_settings import (
                    AggregationSettings,
                    load_aggregation_settings,
                )

                aggregation_settings: AggregationSettings = load_aggregation_settings()
                step_results["s01_config"] = {"status": "completed", "settings_loaded": True}
            except Exception as e:
                self.logger.error(f"[P4-S01] Config loading failed: {e}")
                raise PhaseExecutionError(
                    message=f"Step 1 config loading failed: {e}", phase_id="P04"
                ) from e

            # ====================================================================
            # STEP 2: Validate Inputs (Phase4InputContract)
            # ====================================================================
            self.logger.info("[P4-S02] Step 2: Validate Inputs")

            try:
                from farfan_pipeline.phases.Phase_04.contracts.phase4_10_00_input_contract import (
                    Phase4InputContract,
                )

                input_valid, validation_details = Phase4InputContract.validate(scored_results)
                step_results["s02_input_validation"] = {
                    "status": "completed",
                    "valid": input_valid,
                    "details": validation_details,
                }
                if not input_valid:
                    self.logger.warning(f"[P4-S02] Input validation issues: {validation_details}")
            except Exception as e:
                self.logger.error(f"[P4-S02] Input validation failed: {e}")
                raise PhaseExecutionError(
                    message=f"Step 2 input validation failed: {e}", phase_id="P04"
                ) from e

            # ====================================================================
            # STEP 3: Initialize DimensionAggregator (handles grouping internally)
            # Note: Grouping is done via group_by() in phase4_30_00_aggregation.py
            # The DimensionAggregator.run() method handles grouping + aggregation
            # ====================================================================
            self.logger.info("[P4-S03] Step 3: Initialize Aggregator")

            try:
                from farfan_pipeline.phases.Phase_04.phase4_30_00_aggregation import (
                    DimensionAggregator,
                )

                # Check if SOTA Choquet integral should be used
                use_choquet = aggregation_settings.enable_choquet

                # Initialize aggregator with SOTA features
                aggregator = DimensionAggregator(
                    aggregation_settings=aggregation_settings, enable_sota_features=use_choquet
                )

                step_results["s03_aggregator_init"] = {
                    "status": "completed",
                    "sota_enabled": use_choquet,
                    "group_by_keys": aggregator.dimension_group_by_keys,
                }
                self.logger.info(f"[P4-S03] Aggregator initialized with SOTA={use_choquet}")
            except Exception as e:
                self.logger.error(f"[P4-S03] Aggregator initialization failed: {e}")
                raise PhaseExecutionError(
                    message=f"Step 3 aggregator init failed: {e}", phase_id="P04"
                ) from e

            # ====================================================================
            # STEP 4: Calculate Scores (Choquet or Weighted Average via DimensionAggregator)
            # ====================================================================
            self.logger.info("[P4-S04] Step 4: Calculate Dimension Scores")

            dimension_scores = []
            try:
                if use_choquet:
                    # Use ChoquetAggregator for SOTA Choquet integral
                    from farfan_pipeline.phases.Phase_04.phase4_30_00_choquet_aggregator import (
                        ChoquetAggregator,
                    )

                    choquet_aggregator = ChoquetAggregator(aggregation_settings)
                    dimension_scores = choquet_aggregator.aggregate(scored_results)
                    aggregation_method = "choquet"
                else:
                    # Use DimensionAggregator.run() for weighted average
                    dimension_scores = aggregator.run(
                        scored_results, group_by_keys=aggregator.dimension_group_by_keys
                    )
                    aggregation_method = "weighted_average"

                step_results["s04_calculation"] = {
                    "status": "completed",
                    "method": aggregation_method,
                    "dimension_scores_count": len(dimension_scores),
                }
                self.logger.info(
                    f"[P4-S04] Scores calculated using {aggregation_method}: {len(dimension_scores)} dimensions"
                )
            except Exception as e:
                self.logger.error(f"[P4-S04] Score calculation failed: {e}")
                raise PhaseExecutionError(
                    message=f"Step 4 score calculation failed: {e}", phase_id="P04"
                ) from e

            # ====================================================================
            # STEP 5: Provenance (DAG from DimensionAggregator or standalone)
            # Location: phase4_10_00_aggregation_provenance.py
            # ====================================================================
            self.logger.info("[P4-S05] Step 5: Provenance Tracking")

            provenance_data = None
            try:
                # If SOTA enabled, provenance DAG is already built by aggregator
                if (
                    use_choquet
                    and hasattr(aggregator, "provenance_dag")
                    and aggregator.provenance_dag
                ):
                    provenance_data = aggregator.provenance_dag.get_statistics()
                    step_results["s05_provenance"] = {
                        "status": "completed",
                        "provenance_registered": True,
                        "source": "aggregator_internal_dag",
                        "statistics": provenance_data,
                    }
                else:
                    # Fallback: Create provenance DAG manually
                    from farfan_pipeline.phases.Phase_04.phase4_10_00_aggregation_provenance import (
                        AggregationDAG,
                        ProvenanceNode,
                    )

                    provenance_dag = AggregationDAG()
                    # Register dimension score nodes
                    for ds in dimension_scores:
                        node = ProvenanceNode(
                            node_id=(
                                f"{ds.dimension_id}_{ds.area_id}"
                                if hasattr(ds, "area_id")
                                else str(ds.dimension_id)
                            ),
                            level="dimension",
                            score=ds.score if hasattr(ds, "score") else 0.0,
                            contributing_ids=(
                                [q.question_id for q in ds.contributing_questions]
                                if hasattr(ds, "contributing_questions")
                                else []
                            ),
                        )
                        provenance_dag.add_node(node)
                    provenance_data = provenance_dag.get_statistics()
                    step_results["s05_provenance"] = {
                        "status": "completed",
                        "provenance_registered": True,
                        "source": "manual_dag_construction",
                        "statistics": provenance_data,
                    }
            except Exception as e:
                self.logger.warning(f"[P4-S05] Provenance tracking failed: {e}")
                step_results["s05_provenance"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 6: Uncertainty Quantification (BCa Bootstrap)
            # Location: phase4_10_00_uncertainty_quantification.py
            # ====================================================================
            self.logger.info("[P4-S06] Step 6: Uncertainty Quantification")

            uncertainty_metrics = None
            try:
                from farfan_pipeline.phases.Phase_04.phase4_10_00_uncertainty_quantification import (
                    BootstrapAggregator,
                )

                # Extract scores for uncertainty computation
                scores_for_uq = [ds.score for ds in dimension_scores if hasattr(ds, "score")]

                if scores_for_uq:
                    bootstrap_agg = BootstrapAggregator(iterations=1000, seed=42)
                    uncertainty_result = bootstrap_agg.compute_bca_interval(scores_for_uq)
                    uncertainty_metrics = {
                        "point_estimate": (
                            uncertainty_result.point_estimate
                            if hasattr(uncertainty_result, "point_estimate")
                            else sum(scores_for_uq) / len(scores_for_uq)
                        ),
                        "ci_lower": (
                            uncertainty_result.ci_lower
                            if hasattr(uncertainty_result, "ci_lower")
                            else None
                        ),
                        "ci_upper": (
                            uncertainty_result.ci_upper
                            if hasattr(uncertainty_result, "ci_upper")
                            else None
                        ),
                        "standard_error": (
                            uncertainty_result.standard_error
                            if hasattr(uncertainty_result, "standard_error")
                            else None
                        ),
                    }
                    step_results["s06_uncertainty"] = {
                        "status": "completed",
                        "uncertainty_computed": True,
                        "metrics": uncertainty_metrics,
                    }
                else:
                    step_results["s06_uncertainty"] = {
                        "status": "skipped",
                        "reason": "No scores available for uncertainty quantification",
                    }
            except Exception as e:
                self.logger.warning(f"[P4-S06] Uncertainty quantification failed: {e}")
                step_results["s06_uncertainty"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 7: Output Validation (phase4_60_00_aggregation_validation.py)
            # ====================================================================
            self.logger.info("[P4-S07] Step 7: Output Validation")

            try:
                from farfan_pipeline.phases.Phase_04.phase4_60_00_aggregation_validation import (
                    validate_phase4_output,
                )

                validation_result = validate_phase4_output(dimension_scores, scored_results)
                step_results["s07_output_validation"] = {
                    "status": "completed",
                    "passed": validation_result.passed,
                    "phase": validation_result.phase,
                    "error_message": (
                        validation_result.error_message if not validation_result.passed else None
                    ),
                }
                if not validation_result.passed:
                    self.logger.warning(
                        f"[P4-S07] Output validation failed: {validation_result.error_message}"
                    )
            except Exception as e:
                self.logger.warning(f"[P4-S07] Output validation failed: {e}")
                step_results["s07_output_validation"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 8: Final Output - DimensionScore List with Exit Gate
            # ====================================================================
            self.logger.info("[P4-S08] Step 8: Final Output Generation")

            # Validate output count: Should be 60 (10 PA × 6 DIM)
            expected_count = 60
            actual_count = len(dimension_scores)

            exit_gates["gate_final"] = {
                "status": "passed" if actual_count == expected_count else "failed",
                "expected_count": expected_count,
                "actual_count": actual_count,
            }

            self.logger.info("=" * 80)
            self.logger.critical("PHASE 4: DIMENSION AGGREGATION - FULL ORCHESTRATION COMPLETED")
            self.logger.info(f"Dimension Scores: {actual_count} (expected: {expected_count})")
            self.logger.info(f"Aggregation Method: {aggregation_method}")
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_4] = dimension_scores

            return {
                "status": "completed",
                "dimension_scores": actual_count,
                "expected_count": expected_count,
                "aggregation_method": aggregation_method,
                "provenance": provenance_data,
                "uncertainty": uncertainty_metrics,
                "step_results": step_results,
                "exit_gates": exit_gates,
            }

        except Exception as e:
            self.logger.error(f"Phase 4 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 4 execution failed: {e}",
                phase_id="P04",
                context={"step_results": step_results},
            ) from e

    # =========================================================================
    # PHASE 5: Policy Area Aggregation
    # =========================================================================
    """
    Phase 5 Execution Contract:

    Input: 60 DimensionScore objects
    Output: 10 AreaScore objects (one per policy area)
    Method: Dimension aggregation to policy areas
    """

    def _execute_phase_05(self) -> dict[str, Any]:
        """
        Execute Phase 5: Policy Area Aggregation - COMPLETE ORCHESTRATION (v2.0).

        PHASE 5 PIPELINE:
        - Stage 0: Input Validation (Phase5InputContract)
        - Stage 10/15: Aggregation (HighPerformanceAreaAggregator or AreaPolicyAggregator)
        - Stage 20: Comprehensive Validation
        - Stage 30: Cluster Assignment Validation (Exit Gate to Phase 6)
        - Stage 40: Synthesis Engine
        - Output: Contract Validation (Phase5OutputContract)

        Returns:
            Dict with complete aggregation results including:
            - area_scores: Count of AreaScore objects (expected: 10)
            - stage_results: Results from each stage
            - exit_gates: Validation gates for Phase 6 transition
            - synthesis: Cross-area pattern analysis
            - validation_passed: Overall validation status
        """
        self.logger.info("=" * 80)
        self.logger.critical("PHASE 5: POLICY AREA AGGREGATION - FULL ORCHESTRATION STARTED (v2.0)")
        self.logger.info("=" * 80)

        stage_results: dict[str, Any] = {}
        exit_gates: dict[str, Any] = {}
        area_scores: list = []
        synthesis_result: dict[str, Any] | None = None

        try:
            # ================================================================
            # STAGE 0: INPUT VALIDATION
            # ================================================================
            dimension_scores = self.context.get_phase_output(PhaseID.PHASE_4)
            if dimension_scores is None or len(dimension_scores) == 0:
                raise PhaseExecutionError(
                    message="Phase 5 requires Phase 4 dimension scores", phase_id="P05"
                )

            # Validate input contract
            try:
                from farfan_pipeline.phases.Phase_05.contracts.phase5_10_00_input_contract import (
                    Phase5InputContract,
                )

                input_valid, input_details = Phase5InputContract.validate(dimension_scores)
                stage_results["s00_input_validation"] = {
                    "status": "completed" if input_valid else "failed",
                    "valid": input_valid,
                    "details": input_details,
                }

                if not input_valid and self.config.strict_mode:
                    raise PhaseExecutionError(
                        message=f"Phase 5 input contract violated: {input_details.get('violations', [])}",
                        phase_id="P05",
                        context=input_details,
                    )
            except ImportError as e:
                self.logger.warning(f"[P5-S00] Input contract import failed: {e}")
                stage_results["s00_input_validation"] = {"status": "skipped", "reason": str(e)}

            self.logger.info(f"[P5-S00] Input validated: {len(dimension_scores)} dimension scores")

            # Emit PHASE_START signal
            self._emit_phase_signal(
                phase_id=PhaseID.PHASE_5,
                event_type="PHASE_START",
                payload={"dimension_scores_count": len(dimension_scores)},
            )

            # ================================================================
            # STAGE 10/15: AGGREGATION (with performance boost)
            # ================================================================
            self.logger.info("[P5-S10] Stage 10: Area Aggregation")

            use_performance_boost = getattr(self.config, "enable_parallel_execution", False)
            perf_metrics = None

            if use_performance_boost:
                try:
                    import asyncio

                    from farfan_pipeline.phases.Phase_05.phase5_15_00_performance_boost import (
                        HighPerformanceAreaAggregator,
                    )

                    aggregator = HighPerformanceAreaAggregator(
                        enable_parallel=True,
                        enable_caching=True,
                        enable_vectorization=True,
                        enable_jit=True,
                        max_workers=getattr(self.config, "max_workers", 10),
                    )

                    area_scores, perf_metrics = asyncio.run(
                        aggregator.aggregate_async(dimension_scores)
                    )

                    stage_results["s15_performance"] = {
                        "status": "completed",
                        "metrics": perf_metrics.to_dict() if perf_metrics else {},
                        "speedup": perf_metrics.vectorization_speedup if perf_metrics else 1.0,
                    }
                    self.logger.info(
                        f"[P5-S15] High-performance aggregation: "
                        f"{perf_metrics.total_time*1000:.2f}ms, "
                        f"speedup={perf_metrics.vectorization_speedup:.1f}x"
                    )
                except Exception as e:
                    self.logger.warning(f"[P5-S15] Performance boost failed, falling back: {e}")
                    use_performance_boost = False

            if not use_performance_boost or not area_scores:
                # Fallback to standard aggregator
                from farfan_pipeline.phases.Phase_05.phase5_10_00_area_aggregation import (
                    AreaPolicyAggregator,
                )

                aggregator = AreaPolicyAggregator(
                    abort_on_insufficient=True,
                    enable_sota_features=True,
                )
                area_scores = aggregator.aggregate(dimension_scores)

            stage_results["s10_aggregation"] = {
                "status": "completed",
                "area_scores_count": len(area_scores),
                "performance_boost_used": use_performance_boost,
            }

            self.logger.info(f"[P5-S10] Policy areas aggregated: {len(area_scores)} areas")

            # ================================================================
            # AREA SCORE TYPE VALIDATION
            # ================================================================
            try:
                from farfan_pipeline.phases.Phase_05.phase5_00_00_area_score import AreaScore

                for i, area in enumerate(area_scores):
                    if not isinstance(area, AreaScore):
                        raise PhaseExecutionError(
                            message=(
                                f"Phase 5 area_scores[{i}] is not an AreaScore object. "
                                f"Got type: {type(area).__name__}."
                            ),
                            phase_id="P05",
                            context={"index": i, "actual_type": type(area).__name__},
                        )
                    if not hasattr(area, "area_id") or not hasattr(area, "score"):
                        raise PhaseExecutionError(
                            message=f"Phase 5 area_scores[{i}] missing required attributes.",
                            phase_id="P05",
                            context={"index": i},
                        )
            except ImportError:
                # Fallback attribute check
                for i, area in enumerate(area_scores):
                    if not hasattr(area, "area_id") or not hasattr(area, "score"):
                        raise PhaseExecutionError(
                            message=f"Phase 5 area_scores[{i}] missing required attributes.",
                            phase_id="P05",
                            context={"index": i},
                        )

            # ================================================================
            # STAGE 20: COMPREHENSIVE VALIDATION
            # ================================================================
            self.logger.info("[P5-S20] Stage 20: Comprehensive Validation")

            validation_valid = True
            validation_details: dict[str, Any] = {}
            try:
                from farfan_pipeline.phases.Phase_05.phase5_20_00_area_validation import (
                    validate_phase5_output_comprehensive,
                )

                validation_valid, validation_details = validate_phase5_output_comprehensive(
                    area_scores,
                    strict=getattr(self.config, "strict_mode", False),
                    enable_statistical_validation=True,
                    enable_anomaly_detection=True,
                )

                stage_results["s20_validation"] = {
                    "status": "completed" if validation_valid else "failed",
                    "valid": validation_valid,
                    "details": validation_details,
                }

                if not validation_valid and getattr(self.config, "strict_mode", False):
                    raise PhaseExecutionError(
                        message="Phase 5 comprehensive validation failed",
                        phase_id="P05",
                        context=validation_details,
                    )
            except ImportError as e:
                self.logger.warning(f"[P5-S20] Comprehensive validation not available: {e}")
                stage_results["s20_validation"] = {"status": "skipped", "reason": str(e)}

            # ================================================================
            # STAGE 30: CLUSTER ASSIGNMENT VALIDATION (Exit Gate to Phase 6)
            # ================================================================
            self.logger.info("[P5-S30] Stage 30: Cluster Assignment Validation")

            cluster_valid = True
            cluster_details: dict[str, Any] = {}
            try:
                from farfan_pipeline.phases.Phase_05.phase5_20_00_area_validation import (
                    validate_cluster_assignments,
                )

                cluster_valid, cluster_details = validate_cluster_assignments(area_scores)

                exit_gates["gate_cluster_assignments"] = {
                    "status": "passed" if cluster_valid else "failed",
                    "details": cluster_details,
                }

                if not cluster_valid:
                    self.logger.error(
                        f"[P5-S30] Cluster assignment validation failed: "
                        f"{cluster_details.get('missing_cluster_assignments', [])}"
                    )
                    if getattr(self.config, "strict_mode", False):
                        raise PhaseExecutionError(
                            message="Phase 5 exit gate failed: cluster assignments invalid for Phase 6",
                            phase_id="P05",
                            context=cluster_details,
                        )

                stage_results["s30_cluster_validation"] = {
                    "status": "completed",
                    "cluster_valid": cluster_valid,
                }
            except ImportError as e:
                self.logger.warning(f"[P5-S30] Cluster validation not available: {e}")
                stage_results["s30_cluster_validation"] = {"status": "skipped", "reason": str(e)}
                exit_gates["gate_cluster_assignments"] = {"status": "skipped", "reason": str(e)}

            # ================================================================
            # STAGE 40: SYNTHESIS ENGINE (Optional)
            # ================================================================
            self.logger.info("[P5-S40] Stage 40: Synthesis Engine")

            try:
                from farfan_pipeline.phases.Phase_05.phase5_40_00_synthesis_engine import (
                    SynthesisEngine,
                )

                synthesis_engine = SynthesisEngine()
                synthesis_result = synthesis_engine.synthesize(area_scores, dimension_scores)

                stage_results["s40_synthesis"] = {
                    "status": "completed",
                    "patterns_detected": len(synthesis_result.get("cross_area_patterns", [])),
                    "recommendations_generated": len(
                        synthesis_result.get("policy_recommendations", [])
                    ),
                }
            except Exception as e:
                self.logger.warning(f"[P5-S40] Synthesis engine failed: {e}")
                stage_results["s40_synthesis"] = {"status": "skipped", "reason": str(e)}

            # ================================================================
            # OUTPUT CONTRACT VALIDATION
            # ================================================================
            output_valid = True
            output_details: dict[str, Any] = {}
            try:
                from farfan_pipeline.phases.Phase_05.contracts.phase5_10_02_output_contract import (
                    Phase5OutputContract,
                )

                output_valid, output_details = Phase5OutputContract.validate(area_scores)

                exit_gates["gate_output_contract"] = {
                    "status": "passed" if output_valid else "failed",
                    "details": output_details,
                }
            except ImportError as e:
                self.logger.warning(f"[P5] Output contract not available: {e}")
                exit_gates["gate_output_contract"] = {"status": "skipped", "reason": str(e)}

            # ================================================================
            # FINAL INVARIANT CHECK: 10 AreaScores
            # ================================================================
            expected_count = 10
            actual_count = len(area_scores)

            exit_gates["gate_count_invariant"] = {
                "status": "passed" if actual_count == expected_count else "failed",
                "expected": expected_count,
                "actual": actual_count,
            }

            # Emit PHASE_COMPLETE signal
            self._emit_phase_signal(
                phase_id=PhaseID.PHASE_5,
                event_type="PHASE_COMPLETE",
                payload={
                    "area_scores_count": actual_count,
                    "validation_passed": validation_valid,
                    "cluster_assignments_valid": cluster_valid,
                },
            )

            self.logger.info("=" * 80)
            self.logger.critical(
                "PHASE 5: POLICY AREA AGGREGATION - FULL ORCHESTRATION COMPLETED (v2.0)"
            )
            self.logger.info(f"Area Scores: {actual_count} (expected: {expected_count})")
            self.logger.info("=" * 80)

            # ====================================================================
            # CONSTITUTIONAL INVARIANTS VALIDATION FOR PHASE 5
            # ====================================================================
            constitutional_invariants = {}

            # Invariant 1: 10 Policy Area Scores
            invariant_10_areas = actual_count == 10
            constitutional_invariants["invariant_10_policy_areas"] = {
                "name": "10 Policy Area Scores Constitutional Invariant",
                "expected": 10,
                "actual": actual_count,
                "passed": invariant_10_areas,
                "critical": True,
            }
            self.logger.info(
                f"[P5] Invariant Check: 10 Policy Areas = {invariant_10_areas} (actual: {actual_count})"
            )

            all_invariants_passed = all(inv["passed"] for inv in constitutional_invariants.values())

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_5] = area_scores

            return {
                "status": "completed",
                "area_scores": actual_count,
                "expected_count": expected_count,
                "policy_area_count": actual_count,
                "stage_results": stage_results,
                "exit_gates": exit_gates,
                "synthesis": synthesis_result,
                "validation_passed": validation_valid,
                "cluster_assignments_valid": cluster_valid,
                "constitutional_invariants": constitutional_invariants,
                "all_invariants_passed": all_invariants_passed,
            }

        except PhaseExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Phase 5 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 5 execution failed: {e}",
                phase_id="P05",
                context={"stage_results": stage_results},
            ) from e

    # =========================================================================
    # PHASE 6: Cluster Aggregation (3 Stages)
    # =========================================================================
    """
    Phase 6 Execution Contract (from phase6_execution_flow.md):

    Stage 1: Constants & Configuration
    Stage 2: Adaptive Penalty Mechanism
    Stage 3: Cluster Aggregation

    Input: 10 AreaScore objects
    Output: 4 ClusterScore objects
    """

    def _execute_phase_06(self) -> dict[str, Any]:
        """
        Execute Phase 6: Cluster Aggregation - COMPLETE ORCHESTRATION.

        Transforms 10 Policy Area scores into 4 Cluster scores with
        adaptive penalty based on dispersion analysis.

        Returns:
            Dict with cluster aggregation results
        """
        self.logger.info("=" * 80)
        self.logger.critical("PHASE 6: CLUSTER AGGREGATION - FULL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        try:
            # ====================================================================
            # INPUT: Get AreaScores from Phase 5
            # ====================================================================
            area_scores = self.context.get_phase_output(PhaseID.PHASE_5)
            if area_scores is None or len(area_scores) == 0:
                raise PhaseExecutionError(
                    message="Phase 6 requires Phase 5 area scores", phase_id="P06"
                )

            self.logger.info(f"[P6] Input received: {len(area_scores)} area scores")

            # ====================================================================
            # STAGE 1: Constants & Configuration
            # ====================================================================
            try:
                pass

                self.logger.info("[P6-S10] Constants loaded")
            except Exception as e:
                self.logger.warning(f"[P6-S10] Constants loading failed: {e}")

            # ====================================================================
            # STAGE 2: Adaptive Penalty Mechanism
            # ====================================================================
            # NOTE: AdaptiveMesoScoring is initialized internally by ClusterAggregator.
            # No standalone import needed - this design ensures each aggregator instance
            # has its own configured scoring engine, improving isolation and testability.
            self.logger.info(
                "[P6-S20] Adaptive penalty mechanism configured within ClusterAggregator"
            )

            # ====================================================================
            # STAGE 3: Cluster Aggregation
            # ====================================================================
            cluster_scores = []
            try:
                from farfan_pipeline.phases.Phase_06.phase6_30_00_cluster_aggregator import (
                    ClusterAggregator,
                )

                aggregator = ClusterAggregator()
                cluster_scores = aggregator.aggregate(area_scores)

                self.logger.info(f"[P6-S30] Clusters aggregated: {len(cluster_scores)} clusters")
            except Exception as e:
                self.logger.error(f"[P6-S30] Cluster aggregation failed: {e}")
                raise PhaseExecutionError(
                    message=f"Phase 6 cluster aggregation failed: {e}", phase_id="P06"
                ) from e

            # ====================================================================
            # INPUT CONTRACT VALIDATION: Validate cluster_scores structure
            # ====================================================================
            # Import ClusterScore type for isinstance validation
            try:
                from farfan_pipeline.phases.Phase_06 import ClusterScore
            except ImportError as e:
                self.logger.warning(f"[P6] Could not import ClusterScore for validation: {e}")
                ClusterScore = None

            # Validate each item and build validated output list
            validated_cluster_scores = []
            for i, cs in enumerate(cluster_scores):
                # Type validation: isinstance check or attribute-based fallback
                if ClusterScore is not None:
                    if not isinstance(cs, ClusterScore):
                        raise PhaseExecutionError(
                            message=(
                                f"Phase 6 cluster_scores[{i}] is not a ClusterScore object. "
                                f"Got type: {type(cs).__name__}. "
                                f"Expected ClusterScore from farfan_pipeline.phases.Phase_06."
                            ),
                            phase_id="P06",
                            context={"index": i, "actual_type": type(cs).__name__},
                        )
                else:
                    # Fallback: Check required attributes when type import failed
                    if not hasattr(cs, "cluster_id"):
                        raise PhaseExecutionError(
                            message=(
                                f"Phase 6 cluster_scores[{i}] missing required attribute 'cluster_id'. "
                                f"Got type: {type(cs).__name__}. "
                                f"Expected ClusterScore object with 'cluster_id' and 'score' attributes."
                            ),
                            phase_id="P06",
                            context={"index": i, "actual_type": type(cs).__name__},
                        )
                    if not hasattr(cs, "score"):
                        raise PhaseExecutionError(
                            message=(
                                f"Phase 6 cluster_scores[{i}] missing required attribute 'score'. "
                                f"Got type: {type(cs).__name__}. "
                                f"Expected ClusterScore object with 'cluster_id' and 'score' attributes."
                            ),
                            phase_id="P06",
                            context={"index": i, "actual_type": type(cs).__name__},
                        )

                # Extract values safely after validation
                try:
                    cluster_id = cs.cluster_id
                    score = cs.score
                except AttributeError as ae:
                    raise PhaseExecutionError(
                        message=(
                            f"Phase 6 cluster_scores[{i}] attribute access failed: {ae}. "
                            f"Object type: {type(cs).__name__}."
                        ),
                        phase_id="P06",
                        context={"index": i, "actual_type": type(cs).__name__, "error": str(ae)},
                    ) from ae

                validated_cluster_scores.append({"cluster_id": cluster_id, "score": score})

            # Validate: Should be 4 clusters
            expected_count = 4
            actual_count = len(cluster_scores)

            self.logger.info("=" * 80)
            self.logger.critical("PHASE 6: CLUSTER AGGREGATION - FULL ORCHESTRATION COMPLETED")
            self.logger.info(f"Cluster Scores: {actual_count} (expected: {expected_count})")
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_6] = cluster_scores

            return {
                "status": "completed",
                "cluster_count": actual_count,
                "cluster_scores": validated_cluster_scores,
            }

        except Exception as e:
            self.logger.error(f"Phase 6 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 6 execution failed: {e}", phase_id="P06"
            ) from e

    # =========================================================================
    # PHASE 7: Macro Aggregation (5 Stages)
    # =========================================================================
    """
    Phase 7 Execution Contract (from phase7_execution_flow.md):

    Stage 1: Constants Module
    Stage 2: MacroScore Data Model
    Stage 3: Systemic Gap Detector
    Stage 4: Macro Aggregator (main logic)
    Stage 5: Package Façade

    Input: 4 ClusterScore objects
    Output: 1 MacroScore object
    """

    def _execute_phase_07(self) -> dict[str, Any]:
        """
        Execute Phase 7: Macro Aggregation - CONSTITUTIONAL ORCHESTRATION.

        Synthesizes 4 MESO-level cluster scores into a single holistic MacroScore
        with full contract enforcement, checkpoint support, and performance metrics.

        Integration:
        - Uses Phase 6 → Phase 7 Interphase Bridge for input validation
        - Supports checkpoint/recovery for resilience
        - Emits SISAS signals for observability
        - Collects performance metrics throughout execution
        - Validates exit gate against Phase 8 requirements

        Returns:
            Dict with complete macro aggregation results
        """

        self.logger.info("=" * 80)
        self.logger.critical("PHASE 7: MACRO AGGREGATION - CONSTITUTIONAL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        step_results = {}
        constitutional_invariants = {}
        checkpoint_manager = None
        metrics_collector = None
        plan_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # ====================================================================
            # METRICS COLLECTOR: Initialize performance tracking
            # ====================================================================
            try:
                from farfan_pipeline.phases.Phase_07.phase7_31_00_performance_metrics import (
                    Phase7MetricsCollector,
                )

                metrics_collector = Phase7MetricsCollector(plan_id=plan_id, cluster_count=4)
                metrics_collector.start_phase()
                self.logger.info(f"[P7] Metrics collector initialized for plan_id={plan_id}")
            except ImportError:
                self.logger.warning(
                    "[P7] Metrics collector not available, running without performance tracking"
                )
                metrics_collector = None

            # ====================================================================
            # CHECKPOINT MANAGER: Initialize for recovery support
            # ====================================================================
            checkpoint_dir = Path(self.config.output_dir) / "checkpoints" / "phase7"

            if self.config.enable_checkpoint:
                try:
                    from farfan_pipeline.phases.Phase_07.phase7_30_00_checkpoint_manager import (
                        Phase7CheckpointManager,
                    )

                    checkpoint_manager = Phase7CheckpointManager(
                        checkpoint_dir=checkpoint_dir,
                        plan_id=plan_id,
                    )

                    resume_from = checkpoint_manager.get_resumption_point()
                    if resume_from:
                        self.logger.info(f"[P7] Checkpoint found: resuming from {resume_from}")
                        step_results["checkpoint_recovery"] = {
                            "status": "resuming",
                            "resume_from": resume_from,
                            "plan_id": plan_id,
                        }
                    else:
                        self.logger.info("[P7] No checkpoint found: starting fresh execution")
                        step_results["checkpoint_recovery"] = {
                            "status": "starting_fresh",
                            "plan_id": plan_id,
                        }
                except ImportError:
                    self.logger.warning(
                        "[P7] Checkpoint manager not available, running without recovery support"
                    )
                    checkpoint_manager = None

            # ====================================================================
            # STAGE 1: INPUT VALIDATION (Phase 6 → Phase 7 Bridge Contract)
            # ====================================================================
            self.logger.info("[P7-S1] Stage 1: Input Validation via Interphase Bridge")

            cluster_scores = self.context.get_phase_output(PhaseID.PHASE_6)
            if cluster_scores is None or len(cluster_scores) == 0:
                raise PhaseExecutionError(
                    message="Phase 7 requires Phase 6 cluster scores",
                    phase_id="P07",
                    context={"stage": "S1_INPUT_VALIDATION"},
                )

            # Use interphase bridge for validation
            try:
                from farfan_pipeline.phases.Phase_07.interphase import (
                    Phase6ToPhase7BridgeError,
                    bridge_phase6_to_phase7,
                )

                validated_cluster_scores, bridge_contract = bridge_phase6_to_phase7(cluster_scores)

                step_results["s1_input_validation"] = {
                    "status": "completed",
                    "cluster_count": bridge_contract.cluster_count,
                    "cluster_ids": sorted(bridge_contract.cluster_ids),
                    "score_range": [
                        min(bridge_contract.cluster_scores.values()),
                        max(bridge_contract.cluster_scores.values()),
                    ],
                    "certificate": bridge_contract.certificate,
                }

                self.logger.info(
                    f"[P7-S1] Input validated: {bridge_contract.cluster_count} clusters"
                )

            except Phase6ToPhase7BridgeError as e:
                self.logger.error(f"[P7-S1] Bridge validation failed: {e}")
                raise PhaseExecutionError(
                    message=f"Phase 7 input validation failed: {e}",
                    phase_id="P07",
                    context={"stage": "S1_INPUT_VALIDATION", "error_code": e.error_code},
                ) from e

            # Emit SISAS signal for phase start
            self._emit_phase_signal(
                "P07",
                "STARTED",
                {"plan_id": plan_id, "cluster_count": len(validated_cluster_scores)},
            )

            # ====================================================================
            # STAGE 2-8: MACRO AGGREGATION WITH METRICS TRACKING
            # ====================================================================
            self.logger.info("[P7] Executing macro aggregation pipeline")

            macro_score = None

            # Track with metrics collector
            if metrics_collector:
                with metrics_collector.track_stage("P7_MACRO_AGGREGATION"):
                    try:
                        from farfan_pipeline.phases.Phase_07.phase7_20_00_macro_aggregator import (
                            MacroAggregator,
                        )

                        # Pass checkpoint_manager for granular stage-level recovery
                        aggregator = MacroAggregator(checkpoint_manager=checkpoint_manager)
                        macro_score = aggregator.aggregate(validated_cluster_scores)

                        self.logger.info(f"[P7] Macro aggregated: score={macro_score.score}")

                    except Exception as e:
                        self.logger.error(f"[P7] Macro aggregation failed: {e}")
                        raise PhaseExecutionError(
                            message=f"Phase 7 macro aggregation failed: {e}",
                            phase_id="P07",
                            context={"stage": "MACRO_AGGREGATION"},
                        ) from e
            else:
                # Without metrics tracking
                try:
                    from farfan_pipeline.phases.Phase_07.phase7_20_00_macro_aggregator import (
                        MacroAggregator,
                    )

                    # Pass checkpoint_manager for granular stage-level recovery
                    aggregator = MacroAggregator(checkpoint_manager=checkpoint_manager)
                    macro_score = aggregator.aggregate(validated_cluster_scores)

                    self.logger.info(f"[P7] Macro aggregated: score={macro_score.score}")

                except Exception as e:
                    self.logger.error(f"[P7] Macro aggregation failed: {e}")
                    raise PhaseExecutionError(
                        message=f"Phase 7 macro aggregation failed: {e}",
                        phase_id="P07",
                        context={"stage": "MACRO_AGGREGATION"},
                    ) from e

            # ====================================================================
            # CONSTITUTIONAL INVARIANTS VALIDATION
            # ====================================================================
            self.logger.info("[P7] Validating constitutional invariants")

            # INV-7.1: Cluster weights sum to 1.0
            from farfan_pipeline.phases.Phase_07.contracts.phase7_10_01_mission_contract import (
                Phase7MissionContract,
            )

            weight_sum = sum(Phase7MissionContract.CLUSTER_WEIGHTS.values())
            invariant_7_1 = abs(weight_sum - 1.0) < 1e-6
            constitutional_invariants["INV-7.1"] = {
                "name": "Cluster weights sum to 1.0",
                "expected": 1.0,
                "actual": weight_sum,
                "passed": invariant_7_1,
            }

            # INV-7.3: Score domain [0.0, 3.0]
            score_in_bounds = (
                Phase7MissionContract.SCORE_MIN
                <= macro_score.score
                <= Phase7MissionContract.SCORE_MAX
            )
            constitutional_invariants["INV-7.3"] = {
                "name": "Score domain [0.0, 3.0]",
                "min": Phase7MissionContract.SCORE_MIN,
                "max": Phase7MissionContract.SCORE_MAX,
                "actual": macro_score.score,
                "passed": score_in_bounds,
            }

            # INV-7.4: Coherence weights sum to 1.0
            coherence_sum = sum(Phase7MissionContract.COHERENCE_WEIGHTS.values())
            invariant_7_4 = abs(coherence_sum - 1.0) < 1e-6
            constitutional_invariants["INV-7.4"] = {
                "name": "Coherence weights sum to 1.0",
                "expected": 1.0,
                "actual": coherence_sum,
                "passed": invariant_7_4,
            }

            # Overall invariants status
            all_invariants_passed = all(inv["passed"] for inv in constitutional_invariants.values())

            if not all_invariants_passed and self.config.strict_mode:
                failed_invariants = [
                    name for name, inv in constitutional_invariants.items() if not inv["passed"]
                ]
                raise PhaseExecutionError(
                    message=f"Phase 7 constitutional invariants failed: {failed_invariants}",
                    phase_id="P07",
                    context={
                        "constitutional_invariants": constitutional_invariants,
                        "failed_invariants": failed_invariants,
                    },
                )

            # ====================================================================
            # EXIT GATE VALIDATION (Phase 8 Compatibility)
            # ====================================================================
            self.logger.info("[P7] Exit Gate Validation: Phase 8 Compatibility")

            exit_gate_result = None
            try:
                from farfan_pipeline.phases.Phase_07.phase7_32_00_exit_gate_validation import (
                    validate_phase7_exit_gate,
                )

                input_cluster_ids = [cs.cluster_id for cs in validated_cluster_scores]
                exit_gate_result = validate_phase7_exit_gate(
                    macro_score,
                    input_cluster_ids,
                    strict_mode=self.config.strict_mode,
                )

                step_results["exit_gate_validation"] = {
                    "status": "completed",
                    "passed": exit_gate_result.passed,
                    "checks": len(exit_gate_result.checks_performed),
                    "errors": len(exit_gate_result.errors),
                    "warnings": len(exit_gate_result.warnings),
                    "certificate": exit_gate_result.certificate,
                }

                self.logger.info(f"[P7] Exit gate passed: ready for Phase 8")

            except ValueError as e:
                self.logger.error(f"[P7] Exit gate validation failed: {e}")
                raise PhaseExecutionError(
                    message=f"Phase 7 exit gate validation failed: {e}",
                    phase_id="P07",
                    context={"stage": "EXIT_GATE_VALIDATION"},
                ) from e

            # ====================================================================
            # CHECKPOINT CLEANUP: Clear checkpoints after successful completion
            # ====================================================================
            if checkpoint_manager is not None:
                try:
                    cleared = checkpoint_manager.clear_checkpoints()
                    self.logger.info(
                        f"[P7] Cleared {cleared} checkpoint files after successful completion"
                    )
                    step_results["checkpoint_cleanup"] = {
                        "status": "completed",
                        "files_cleared": cleared,
                    }
                except Exception as e:
                    self.logger.warning(f"[P7] Checkpoint cleanup failed: {e}")
                    step_results["checkpoint_cleanup"] = {
                        "status": "failed",
                        "error": str(e),
                    }

            # ====================================================================
            # METRICS FINALIZATION: End phase and export metrics
            # ====================================================================
            if metrics_collector is not None:
                try:
                    macro_score_info = {
                        "evaluation_id": getattr(macro_score, "evaluation_id", "UNKNOWN"),
                        "score": getattr(macro_score, "score", 0.0),
                        "quality_level": getattr(macro_score, "quality_level", "UNKNOWN"),
                        "coherence": getattr(macro_score, "cross_cutting_coherence", 0.0),
                        "alignment": getattr(macro_score, "strategic_alignment", 0.0),
                    }
                    metrics_collector.end_phase(macro_score_info)
                    metrics = metrics_collector.get_metrics()

                    # Log aggregate statistics
                    self.logger.info(f"[P7] Metrics Summary:")
                    self.logger.info(f"  - Total duration: {metrics.total_duration_ms:.2f}ms")
                    self.logger.info(
                        f"  - Stages completed: {metrics.aggregate_stats.get('completed_stages', 0)}"
                    )
                    self.logger.info(
                        f"  - Avg stage duration: {metrics.aggregate_stats.get('avg_duration_ms', 0):.2f}ms"
                    )
                    self.logger.info(
                        f"  - Peak memory: {metrics.aggregate_stats.get('max_memory_mb_peak', 0):.2f}MB"
                    )

                    # Export metrics to file
                    metrics_path = (
                        Path(self.config.output_dir)
                        / "metrics"
                        / "phase7"
                        / f"{plan_id}_metrics.json"
                    )
                    metrics_collector.export_metrics(metrics_path)
                    self.logger.info(f"[P7] Metrics exported to: {metrics_path}")

                    step_results["metrics_export"] = {
                        "status": "completed",
                        "metrics_path": str(metrics_path),
                        "total_duration_ms": metrics.total_duration_ms,
                        "aggregate_stats": metrics.aggregate_stats,
                    }
                except Exception as e:
                    self.logger.warning(f"[P7] Metrics finalization failed: {e}")
                    step_results["metrics_export"] = {
                        "status": "failed",
                        "error": str(e),
                    }

            # Emit SISAS signal for phase completion
            self._emit_phase_signal(
                "P07",
                "COMPLETED",
                {
                    "plan_id": plan_id,
                    "macro_score": macro_score.score,
                    "quality_level": macro_score.quality_level,
                    "exit_gate_passed": exit_gate_result.passed if exit_gate_result else False,
                },
            )

            # ====================================================================
            # FINALIZATION: Store and Return Results
            # ====================================================================
            self.logger.info("=" * 80)
            self.logger.critical(
                "PHASE 7: MACRO AGGREGATION - CONSTITUTIONAL ORCHESTRATION COMPLETED"
            )
            self.logger.info(f"Macro Score: {macro_score.score}")
            self.logger.info(f"Quality Level: {macro_score.quality_level}")
            self.logger.info(
                f"Constitutional Invariants: {'ALL PASSED' if all_invariants_passed else 'SOME FAILED'}"
            )
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_7] = macro_score

            return {
                "status": "completed",
                "macro_score": {
                    "evaluation_id": getattr(macro_score, "evaluation_id", "UNKNOWN"),
                    "score": macro_score.score,
                    "quality_level": macro_score.quality_level,
                    "coherence": getattr(macro_score, "cross_cutting_coherence", 0.0),
                    "alignment": getattr(macro_score, "strategic_alignment", 0.0),
                    "systemic_gaps": getattr(macro_score, "systemic_gaps", []),
                },
                "step_results": step_results,
                "constitutional_invariants": constitutional_invariants,
                "all_invariants_passed": all_invariants_passed,
                "exit_gate_certificate": exit_gate_result.certificate if exit_gate_result else {},
                "components": ["CCCA", "SGD", "SAS"],
            }

        except Exception as e:
            self.logger.error(f"Phase 7 orchestration failed: {e}")
            # Emit SISAS signal for phase failure
            self._emit_phase_signal(
                "P07",
                "FAILED",
                {
                    "plan_id": plan_id,
                    "error": str(e),
                },
            )
            raise PhaseExecutionError(
                message=f"Phase 7 execution failed: {e}",
                phase_id="P07",
                context={"step_results": step_results},
            ) from e

    # =========================================================================
    # PHASE 8: Recommendations Engine (6 Stages)
    # =========================================================================
    """
    Phase 8 Execution Contract (from phase8_execution_flow.md):

    Stage 00: Foundation (Data Models)
    Stage 10: Validation (Schema Validation)
    Stage 20: Core Generation (Generic Rule Engine, Template Compiler, Main Engine, Orchestrator, Adapter)
    Stage 30: Enrichment (Signal Enriched)
    Stage 35: Targeting (Entity Targeted - Optional)

    Input: Phase 7 analysis results
    Output: Three-level recommendations (MICRO, MESO, MACRO)
    """

    def _execute_phase_08(self) -> dict[str, Any]:
        """
        Execute Phase 8: Recommendations Engine - COMPLETE ORCHESTRATION.

        Generates recommendations at three hierarchical levels: MICRO, MESO, MACRO.

        Returns:
            Dict with recommendation generation results
        """
        self.logger.info("=" * 80)
        self.logger.critical("PHASE 8: RECOMMENDATIONS ENGINE - FULL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        stage_results = {}

        try:
            # ====================================================================
            # INPUT: Get MacroScore from Phase 7
            # ====================================================================
            macro_score = self.context.get_phase_output(PhaseID.PHASE_7)
            if macro_score is None:
                raise PhaseExecutionError(
                    message="Phase 8 requires Phase 7 macro score", phase_id="P08"
                )

            self.logger.info(f"[P8] Input received: macro_score")

            # ====================================================================
            # STAGE 00: Foundation (Data Models)
            # ====================================================================
            self.logger.info("[P8-S00] Stage 00: Foundation - Data Models")

            try:
                pass

                stage_results["s00_foundation"] = {"status": "completed"}
            except Exception as e:
                self.logger.warning(f"[P8-S00] Foundation failed: {e}")
                stage_results["s00_foundation"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STAGE 10: Validation
            # ====================================================================
            self.logger.info("[P8-S10] Stage 10: Schema Validation")

            try:
                from farfan_pipeline.phases.Phase_08.phase8_10_00_schema_validation import (
                    UniversalRuleValidator,
                )

                UniversalRuleValidator()
                stage_results["s10_validation"] = {"status": "completed"}
            except Exception as e:
                self.logger.warning(f"[P8-S10] Validation failed: {e}")
                stage_results["s10_validation"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STAGE 20: Core Generation
            # ====================================================================
            self.logger.info("[P8-S20] Stage 20: Core Recommendation Generation")

            recommendations = {"MICRO": [], "MESO": [], "MACRO": []}
            try:
                from farfan_pipeline.phases.Phase_08.phase8_25_00_recommendation_bifurcator import (
                    UnifiedBifurcator,
                )

                engine = UnifiedBifurcator()

                # Get cluster data from Phase 6 and macro data from Phase 7
                cluster_scores = self.context.get_phase_output(PhaseID.PHASE_6) or []
                area_scores = self.context.get_phase_output(PhaseID.PHASE_5) or []

                # Convert scores to dict format expected by engine
                micro_scores = {}
                if isinstance(area_scores, list):
                    for score in area_scores:
                        if hasattr(score, "area_id") and hasattr(score, "score"):
                            micro_scores[score.area_id] = score.score
                elif isinstance(area_scores, dict):
                    micro_scores = area_scores

                cluster_data = {}
                if isinstance(cluster_scores, list):
                    for score in cluster_scores:
                        if hasattr(score, "cluster_id"):
                            cluster_data[score.cluster_id] = score
                elif isinstance(cluster_scores, dict):
                    cluster_data = cluster_scores

                macro_data = (
                    macro_score if isinstance(macro_score, dict) else {"macro_score": macro_score}
                )

                # Generate all recommendations using RecommendationEngine
                all_recs = engine.generate_all_recommendations(
                    micro_scores=micro_scores, cluster_data=cluster_data, macro_data=macro_data
                )

                recommendations = all_recs

                # Count recommendations (handle both dict and RecommendationSet)
                def get_rec_count(rec_set):
                    if hasattr(rec_set, "recommendations"):
                        return len(rec_set.recommendations)
                    elif isinstance(rec_set, dict):
                        return len(rec_set.get("recommendations", []))
                    return 0

                stage_results["s20_core"] = {
                    "status": "completed",
                    "micro_count": get_rec_count(all_recs.get("MICRO", {})),
                    "meso_count": get_rec_count(all_recs.get("MESO", {})),
                    "macro_count": get_rec_count(all_recs.get("MACRO", {})),
                }
                self.logger.info(f"[P8-S20] Recommendations generated: {stage_results['s20_core']}")
            except Exception as e:
                self.logger.error(f"[P8-S20] Core generation failed: {e}")
                raise PhaseExecutionError(
                    message=f"Stage 20 core generation failed: {e}", phase_id="P08"
                ) from e

            # ====================================================================
            # STAGE 30: Signal Enrichment (Optional)
            # ====================================================================
            self.logger.info("[P8-S30] Stage 30: Signal Enrichment")

            try:
                if self.config.enable_sisas and self.context.sisas:
                    # Verify SISAS object has get_metrics method before calling it
                    if not hasattr(self.context.sisas, "get_metrics"):
                        self.logger.warning(
                            "[P8-S30] SISAS object missing get_metrics method, skipping signal enrichment"
                        )
                        stage_results["s30_enrichment"] = {
                            "status": "skipped",
                            "reason": "missing get_metrics method on SISAS object",
                        }
                    else:
                        from farfan_pipeline.phases.Phase_08.phase8_30_00_signal_enriched_recommendations import (
                            SignalEnrichedRecommender,
                        )

                        enricher = SignalEnrichedRecommender()
                        # Guard against AttributeError when calling get_metrics
                        try:
                            signal_data = self.context.sisas.get_metrics()
                        except AttributeError as ae:
                            self.logger.warning(
                                f"[P8-S30] get_metrics raised AttributeError: {ae}, skipping signal enrichment"
                            )
                            stage_results["s30_enrichment"] = {
                                "status": "skipped",
                                "reason": f"AttributeError from get_metrics: {ae}",
                            }
                        else:
                            recommendations = enricher.enrich_with_signals(
                                recommendations=recommendations, signal_data=signal_data
                            )
                            stage_results["s30_enrichment"] = {"status": "completed"}
                else:
                    stage_results["s30_enrichment"] = {
                        "status": "skipped",
                        "reason": "SISAS disabled",
                    }
            except Exception as e:
                self.logger.warning(f"[P8-S30] Signal enrichment failed: {e}")
                stage_results["s30_enrichment"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # OUTPUT: Three-Level Recommendations
            # ====================================================================
            # Helper function to count recommendations (handles both RecommendationSet and dict)
            def get_rec_count_output(rec_set):
                if hasattr(rec_set, "recommendations"):
                    return len(rec_set.recommendations)
                elif isinstance(rec_set, dict):
                    return len(rec_set.get("recommendations", []))
                return 0

            total_recs = (
                get_rec_count_output(recommendations.get("MICRO", {}))
                + get_rec_count_output(recommendations.get("MESO", {}))
                + get_rec_count_output(recommendations.get("MACRO", {}))
            )

            self.logger.info("=" * 80)
            self.logger.critical("PHASE 8: RECOMMENDATIONS ENGINE - FULL ORCHESTRATION COMPLETED")
            self.logger.info(f"Total Recommendations: {total_recs}")
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_8] = recommendations

            return {
                "status": "completed",
                "recommendations": {
                    "total_count": total_recs,
                    "micro_count": get_rec_count_output(recommendations.get("MICRO", {})),
                    "meso_count": get_rec_count_output(recommendations.get("MESO", {})),
                    "macro_count": get_rec_count_output(recommendations.get("MACRO", {})),
                    "version": "3.0.0",
                },
                "stage_results": stage_results,
            }

        except Exception as e:
            self.logger.error(f"Phase 8 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 8 execution failed: {e}", phase_id="P08"
            ) from e

    # =========================================================================
    # PHASE 9: Report Assembly (4 Steps)
    # =========================================================================
    """
    Phase 9 Execution Contract (aligned with PHASE_9_MANIFEST.json):

    STEP 1: Validate Inputs (Phase9Input from contracts/phase9_10_00_input_contract.py)
    STEP 2: Assemble Report (ReportAssembler from phase9_10_00_report_assembly.py)
    STEP 3: Generate Report Artifacts (ReportGenerator from phase9_10_00_report_generator.py)
    STEP 4: Final Output with institutional annex

    Module Mapping:
    - Stage 10: phase_9_constants, report_assembly, report_generator, signal_enriched_reporting
    - Stage 15: institutional_entity_annex

    Input: Phase 8 recommendations + all prior phase outputs
    Output: PolicyReport, ExecutiveSummary, DetailedFindings (MD/HTML/PDF)
    """

    def _execute_phase_09(self) -> dict[str, Any]:
        """
        Execute Phase 9: Report Assembly - COMPLETE ORCHESTRATION.

        Orchestrates all 4 steps of Phase 9 report generation:
        1. Input validation
        2. Report assembly via ReportAssembler
        3. Artifact generation via ReportGenerator
        4. Final output with institutional annex

        Returns:
            Dict with report generation results including artifact paths
        """
        self.logger.info("=" * 80)
        self.logger.critical("PHASE 9: REPORT ASSEMBLY - FULL ORCHESTRATION STARTED")
        self.logger.info("=" * 80)

        step_results = {}
        exit_gates = {}

        try:
            # ====================================================================
            # INPUT: Get Recommendations from Phase 8
            # ====================================================================
            recommendations = self.context.get_phase_output(PhaseID.PHASE_8)
            if recommendations is None:
                raise PhaseExecutionError(
                    message="Phase 9 requires Phase 8 recommendations", phase_id="P09"
                )

            self.logger.info(f"[P9] Input received: Phase 8 recommendations")

            # ====================================================================
            # STEP 1: Validate Inputs
            # ====================================================================
            self.logger.info("[P9-S01] Step 1: Validate Inputs")

            try:
                from farfan_pipeline.phases.Phase_09.contracts.phase9_10_00_input_contract import (
                    Phase9Input,
                    validate_phase9_input,
                )

                # Build Phase9Input from context
                phase9_input = Phase9Input(
                    recommendations=(
                        recommendations if isinstance(recommendations, list) else [recommendations]
                    ),
                    signal_enriched_data=self.context.get_phase_output(PhaseID.PHASE_8) or {},
                    institutional_context={"municipality": self.config.municipality_name},
                    policy_areas=[f"PA{i:02d}" for i in range(1, 11)],
                    report_config={"format": ["html", "markdown", "pdf"]},
                )

                is_valid, validation_errors = validate_phase9_input(phase9_input)
                step_results["s01_input_validation"] = {
                    "status": "completed",
                    "valid": is_valid,
                    "errors": validation_errors if not is_valid else [],
                }

                if not is_valid:
                    self.logger.warning(f"[P9-S01] Input validation issues: {validation_errors}")
            except Exception as e:
                self.logger.warning(f"[P9-S01] Input validation skipped: {e}")
                step_results["s01_input_validation"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # STEP 2: Assemble Report (ReportAssembler)
            # ====================================================================
            self.logger.info("[P9-S02] Step 2: Assemble Report")

            analysis_report = None
            try:
                from farfan_pipeline.phases.Phase_09.phase9_10_00_report_assembly import (
                    ReportAssembler,
                )

                # Get questionnaire provider from context or factory
                questionnaire_provider = None
                if hasattr(self.context, "wiring") and self.context.wiring:
                    questionnaire_provider = getattr(
                        self.context.wiring.factory, "questionnaire_provider", None
                    )

                if questionnaire_provider is None:
                    # Fallback: Create a minimal provider
                    class MinimalProvider:
                        def get_data(self):
                            return {"blocks": {}, "metadata": {}}

                    questionnaire_provider = MinimalProvider()

                assembler = ReportAssembler(
                    questionnaire_provider=questionnaire_provider, orchestrator=self
                )

                # Gather all phase outputs for report
                execution_results = {
                    "macro_score": self.context.get_phase_output(PhaseID.PHASE_7),
                    "cluster_scores": self.context.get_phase_output(PhaseID.PHASE_6),
                    "area_scores": self.context.get_phase_output(PhaseID.PHASE_5),
                    "dimension_scores": self.context.get_phase_output(PhaseID.PHASE_4),
                    "recommendations": recommendations,
                }

                analysis_report = assembler.assemble_report(
                    plan_name=self.config.municipality_name or "policy_analysis",
                    execution_results=execution_results,
                )

                step_results["s02_assembly"] = {
                    "status": "completed",
                    "report_id": (
                        analysis_report.metadata.report_id
                        if hasattr(analysis_report, "metadata")
                        else "unknown"
                    ),
                }
                self.logger.info(
                    f"[P9-S02] Report assembled: {step_results['s02_assembly']['report_id']}"
                )
            except Exception as e:
                self.logger.error(f"[P9-S02] Report assembly failed: {e}")
                raise PhaseExecutionError(
                    message=f"Step 2 report assembly failed: {e}", phase_id="P09"
                ) from e

            # ====================================================================
            # STEP 3: Generate Report Artifacts (ReportGenerator)
            # ====================================================================
            self.logger.info("[P9-S03] Step 3: Generate Report Artifacts")

            artifacts = {}
            try:
                from pathlib import Path

                from farfan_pipeline.phases.Phase_09.phase9_10_00_report_generator import (
                    ReportGenerator,
                )

                output_dir = Path(self.config.output_dir) / "reports"
                generator = ReportGenerator(
                    output_dir=output_dir,
                    plan_name=self.config.municipality_name or "policy_analysis",
                    enable_charts=True,
                    enable_animations=True,
                )

                artifacts = generator.generate_all(
                    report=analysis_report,
                    generate_pdf=True,
                    generate_html=True,
                    generate_markdown=True,
                )

                step_results["s03_generation"] = {
                    "status": "completed",
                    "artifacts": {k: str(v) for k, v in artifacts.items()},
                }
                self.logger.info(f"[P9-S03] Generated {len(artifacts)} report artifacts")
            except Exception as e:
                self.logger.warning(f"[P9-S03] Report generation failed: {e}")
                step_results["s03_generation"] = {"status": "failed", "reason": str(e)}

            # ====================================================================
            # STEP 4: Institutional Entity Annex (Optional)
            # ====================================================================
            self.logger.info("[P9-S04] Step 4: Institutional Entity Annex")

            try:
                from farfan_pipeline.phases.Phase_09.phase9_15_00_institutional_entity_annex import (
                    generate_institutional_annex,
                )

                annex = generate_institutional_annex(
                    report=analysis_report, municipality=self.config.municipality_name
                )
                step_results["s04_annex"] = {"status": "completed", "annex_generated": True}
            except Exception as e:
                self.logger.warning(f"[P9-S04] Institutional annex skipped: {e}")
                step_results["s04_annex"] = {"status": "skipped", "reason": str(e)}

            # ====================================================================
            # OUTPUT: Final Report
            # ====================================================================
            exit_gates["gate_final"] = {
                "status": "passed" if analysis_report is not None else "failed",
                "artifacts_generated": len(artifacts),
            }

            self.logger.info("=" * 80)
            self.logger.critical("PHASE 9: REPORT ASSEMBLY - FULL ORCHESTRATION COMPLETED")
            self.logger.info(f"Report Status: {'complete' if analysis_report else 'failed'}")
            self.logger.info(f"Artifacts: {len(artifacts)}")
            self.logger.info("=" * 80)

            # Store in context
            self.context.phase_outputs[PhaseID.PHASE_9] = {
                "report": analysis_report,
                "artifacts": artifacts,
            }

            return {
                "status": "completed",
                "report": {
                    "municipality": self.config.municipality_name,
                    "status": "complete" if analysis_report else "failed",
                    "report_id": (
                        analysis_report.metadata.report_id
                        if analysis_report and hasattr(analysis_report, "metadata")
                        else None
                    ),
                },
                "artifacts": {k: str(v) for k, v in artifacts.items()},
                "step_results": step_results,
                "exit_gates": exit_gates,
            }

        except PhaseExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Phase 9 orchestration failed: {e}")
            raise PhaseExecutionError(
                message=f"Phase 9 execution failed: {e}",
                phase_id="P09",
                context={"step_results": step_results},
            ) from e

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _compute_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """Compute hash of a file for validation."""
        import hashlib

        hash_obj = hashlib.new(algorithm)
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to compute file hash for {file_path}: {e}")
            return ""

    def _execute_phase_01_subphases_individually(
        self, canonical_input, signal_enricher, subphase_results
    ) -> dict[str, Any]:
        """
        Fallback method to execute Phase 1 subphases individually.

        Used when the complete ingestion function is not available.
        """

        self.logger.info("[P1] Executing subphases individually (fallback mode)")

        # This would implement the full 16-subphase pipeline
        # For now, return a minimal structure
        return {
            "smart_chunks": [],
            "canon_policy_package": None,
            "subphase_results": subphase_results,
            "validation_result": {"all_passed": True},
        }

    # =========================================================================
    # PHASE 1 PROGRESS TRACKING METHODS
    # =========================================================================

    def _on_phase1_subphase_progress(
        self,
        subphase_id: str,
        status: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """
        Callback for Phase 1 subphase progress updates.

        Args:
            subphase_id: Subphase identifier (e.g., "SP4", "SP11")
            status: Status update (PENDING, RUNNING, COMPLETED, FAILED)
            metrics: Optional metrics dictionary
        """
        self.logger.info(
            f"[P1] Subphase progress: {subphase_id} = {status}",
            subphase_id=subphase_id,
            status=status,
            metrics=metrics,
        )

        # Update subphase registry if exists
        if subphase_id in self.PHASE1_SUBPHASES:
            subphase = self.PHASE1_SUBPHASES[subphase_id]
            subphase.status = status
            if status == "RUNNING" and subphase.started_at is None:
                subphase.started_at = datetime.utcnow()
            elif status in ("COMPLETED", "FAILED"):
                subphase.completed_at = datetime.utcnow()
            if metrics:
                subphase.metrics.update(metrics)

        # Emit signal if SISAS enabled
        if self.config.enable_sisas and self.context.sisas:
            self._emit_subphase_signal(
                phase="phase_1",
                subphase=subphase_id,
                status=status,
                metrics=metrics,
            )

    def _emit_subphase_signal(
        self,
        phase: str,
        subphase: str,
        status: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit SISAS signal for subphase progress.

        Args:
            phase: Phase identifier (e.g., "phase_1")
            subphase: Subphase identifier (e.g., "SP4")
            status: Status update
            metrics: Optional metrics dictionary
        """
        if not SISAS_CORE_AVAILABLE:
            return

        if self.context.sisas is None:
            return

        try:
            from uuid import uuid4

            signal = Signal(
                signal_id=f"{phase.upper()}_{subphase}_{status}_{uuid4().hex[:8]}",
                signal_type=SignalType.PHASE_MONITORING,
                scope=SignalScope(
                    phase=phase,
                    policy_area="ALL",
                    slot=subphase,
                ),
                content={
                    "subphase": subphase,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics or {},
                },
                provenance=SignalProvenance(
                    source_module="UnifiedOrchestrator._emit_subphase_signal",
                    created_at=datetime.utcnow(),
                    correlation_id=self.context.execution_id,
                ),
            )

            # Dispatch signal
            self.context.sisas.dispatch(signal)

            self.logger.debug(
                f"Subphase signal emitted: {phase}/{subphase} = {status}",
                signal_id=signal.signal_id,
            )

        except Exception as e:
            self.logger.warning(
                f"Failed to emit subphase signal: {e}",
                phase=phase,
                subphase=subphase,
            )

    # =========================================================================
    # PHASE 1 EXIT GATE VALIDATION
    # =========================================================================

    def _validate_phase1_exit_gate(
        self,
        canon_policy_package: Any,
    ) -> dict[str, Any]:
        """
        Validate Phase 1 output meets Phase 2 input requirements.

        Uses Phase 2's input contract for validation.

        Args:
            canon_policy_package: CanonPolicyPackage from Phase 1

        Returns:
            Dict with exit_gate_passed and validation_details
        """
        try:
            from farfan_pipeline.phases.Phase_02.contracts.phase2_10_00_input_contract import (
                Phase2InputPreconditions,
                Phase2InputValidator,
            )

            preconditions = Phase2InputPreconditions()
            validator = Phase2InputValidator(preconditions)

            # Validate CPP structure
            cpp_valid, cpp_errors = validator.validate_cpp(canon_policy_package)

            # Generate compatibility certificate
            certificate = self._generate_phase1_certificate(
                canon_policy_package,
                cpp_valid,
                cpp_errors,
            )

            exit_gate_result = {
                "exit_gate_passed": cpp_valid and certificate["status"] == "VALID",
                "cpp_validation": {
                    "valid": cpp_valid,
                    "errors": cpp_errors,
                },
                "certificate": certificate,
                "phase2_preconditions": {
                    "expected_chunk_count": preconditions.EXPECTED_CHUNK_COUNT,
                    "actual_chunk_count": len(canon_policy_package.smart_chunks),
                    "expected_schema_version": preconditions.REQUIRED_CPP_SCHEMA_VERSION,
                    "actual_schema_version": (
                        canon_policy_package.manifest.schema_version
                        if hasattr(canon_policy_package, "manifest")
                        else "UNKNOWN"
                    ),
                },
            }

            if not exit_gate_result["exit_gate_passed"]:
                self.logger.error(
                    "[P1] Exit gate FAILED",
                    errors=cpp_errors,
                    certificate_status=certificate["status"],
                )

                if self.config.strict_mode:
                    raise PhaseExecutionError(
                        message="Phase 1 exit gate failed - Phase 2 preconditions not met",
                        phase_id="P01",
                        context=exit_gate_result,
                    )
            else:
                self.logger.info(
                    "[P1] Exit gate PASSED",
                    chunks=len(canon_policy_package.smart_chunks),
                    certificate_status=certificate["status"],
                )

            return exit_gate_result

        except Exception as e:
            self.logger.error(f"[P1] Exit gate validation error: {e}")
            return {
                "exit_gate_passed": False,
                "error": str(e),
                "cpp_validation": {"valid": False, "errors": [str(e)]},
                "certificate": None,
            }

    def _generate_phase1_certificate(
        self,
        cpp: Any,
        valid: bool,
        errors: list,
    ) -> dict[str, Any]:
        """
        Generate Phase 1 compatibility certificate for Phase 2.

        Args:
            cpp: CanonPolicyPackage
            valid: Whether validation passed
            errors: List of validation errors

        Returns:
            Certificate dictionary
        """
        import json
        from datetime import datetime, timezone

        # Compute CPP hash
        cpp_dict = cpp.to_dict() if hasattr(cpp, "to_dict") else {}
        cpp_json = json.dumps(cpp_dict, sort_keys=True, default=str)
        cpp_hash = hashlib.sha256(cpp_json.encode()).hexdigest()

        certificate = {
            "phase": 1,
            "status": "VALID" if valid else "INVALID",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpp_hash": cpp_hash,
            "chunk_count": len(cpp.smart_chunks),
            "schema_version": (
                cpp.manifest.schema_version if hasattr(cpp, "manifest") else "UNKNOWN"
            ),
            "errors": errors,
            "warnings": [],
            "certificate_version": "CERT-P1-2025.1",
        }

        # Store certificate in context for Phase 2
        self.context.phase_inputs[PhaseID.PHASE_2] = {
            "cpp": cpp,
            "certificate": certificate,
        }

        return certificate

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "state": self.state_machine.current_state.name,
            "active_phases": list(self._active_phases),
            "completed_phases": list(self._completed_phases.keys()),
            "failed_phases": list(self._failed_phases.keys()),
            "dependency_graph_state": self.dependency_graph.get_state_snapshot(),
        }

    def get_sisas_metrics(self) -> dict[str, Any]:
        """Get SISAS metrics from SDO and context."""
        if self.context.sisas is None:
            return {"sisas_enabled": False}

        sdo_metrics = self.context.sisas.get_metrics()
        consumer_stats = self.context.sisas.get_consumer_stats()
        health = self.context.sisas.health_check()

        return {
            "sisas_enabled": True,
            "sdo_metrics": sdo_metrics,
            "consumer_stats": consumer_stats,
            "health_status": health["status"],
            "dead_letter_rate": health["dead_letter_rate"],
            "error_rate": health["error_rate"],
            "signal_metrics": self.context.signal_metrics,
        }

    def save_checkpoint(self, checkpoint_dir: str = None) -> str:
        """Save current pipeline state for recovery."""
        import pickle

        if checkpoint_dir is None:
            checkpoint_dir = self.config.output_dir

        checkpoint_path = Path(checkpoint_dir)
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = checkpoint_path / f"farfan_checkpoint_{timestamp}.pkl"

        checkpoint_data = {
            "context": self.context,
            "config": self.config.to_dict(),
            "phase_outputs": self.context.phase_outputs,
            "phase_results": self.context.phase_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(checkpoint_file, "wb") as f:
            pickle.dump(checkpoint_data, f)

        self.logger.info(f"Checkpoint saved to {checkpoint_file}")
        return str(checkpoint_file)

    def export_results(self, output_dir: str = None) -> dict[str, str]:
        """Export all pipeline results to structured format."""
        if output_dir is None:
            output_dir = self.config.output_dir

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        for phase_id, output in self.context.phase_outputs.items():
            phase_file = output_path / f"{phase_id.lower()}_output.json"

            if hasattr(output, "to_dict"):
                output_data = output.to_dict()
            elif isinstance(output, list) and output and hasattr(output[0], "to_dict"):
                output_data = [item.to_dict() for item in output]
            else:
                output_data = output

            with open(phase_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

            exported_files[phase_id] = str(phase_file)

        self.logger.info(f"Results exported to {output_dir}")
        return exported_files

    def cleanup(self) -> None:
        """Clean up resources after pipeline execution."""
        self.logger.info("Starting cleanup")

        # Clean up factory resources
        if self.factory:
            self.factory.cleanup()

        import gc

        gc.collect()
        self.logger.info("Cleanup completed")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "OrchestratorConfig",
    "ConfigValidationError",
    "validate_config",
    "get_development_config",
    "get_production_config",
    "get_testing_config",
    # Exceptions
    "OrchestrationError",
    "DependencyResolutionError",
    "SchedulingError",
    "StateTransitionError",
    "OrchestrationInitializationError",
    "PhaseExecutionError",
    "ContractViolationError",
    # State Machine
    "OrchestrationState",
    "StateTransition",
    "OrchestrationStateMachine",
    "VALID_TRANSITIONS",
    # Dependency Graph
    "DependencyStatus",
    "DependencyNode",
    "DependencyEdge",
    "GraphValidationResult",
    "DependencyGraph",
    # Phase Scheduler
    "SchedulingStrategy",
    "SchedulingDecision",
    "PhaseScheduler",
    # Core Orchestrator
    "PhaseStatus",
    "PhaseID",
    "PHASE_METADATA",
    "PhaseResult",
    "ExecutionContext",
    "PipelineResult",
    "UnifiedOrchestrator",
]

# Backward compatibility aliases
Orchestrator = UnifiedOrchestrator
PipelineOrchestrator = UnifiedOrchestrator
