"""
Calibration system protocols and abstract interfaces.

This module defines the contracts that all layer evaluators must satisfy.
Using Protocol instead of ABC allows for structural subtyping (duck typing)
while still enabling static type checking with mypy.

Design Philosophy:
- All evaluators return LayerScore (not raw float)
- Evaluation methods must be pure (no side effects beyond logging)
- All parameters must be explicitly typed
- Protocols enable static verification without inheritance
"""
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .data_structures import LayerScore

if TYPE_CHECKING:
    from .pdt_structure import PDTStructure


@runtime_checkable
class LayerEvaluator(Protocol):
    """
    Protocol that all layer evaluators must implement.

    This ensures consistent signature across all evaluation layers:
    - BASE (@b)
    - UNIT (@u)
    - QUESTION (@q)
    - DIMENSION (@d)
    - POLICY (@p)
    - CONGRUENCE (@C)
    - CHAIN (@chain)
    - META (@m)

    By using Protocol, we enable static type checking without requiring
    explicit inheritance. Any class with an `evaluate()` method that
    returns LayerScore will satisfy this protocol.

    Example:
        def process_layer(evaluator: LayerEvaluator, **kwargs):
            score = evaluator.evaluate(**kwargs)
            assert isinstance(score, LayerScore)  # Always true
    """

    def evaluate(self, **kwargs) -> LayerScore:
        """
        Evaluate layer and return LayerScore.

        Each evaluator can accept different keyword arguments depending
        on what it needs, but MUST return LayerScore.

        Returns:
            LayerScore with score ∈ [0.0, 1.0], components, and rationale

        Example implementations:
            # BASE layer
            def evaluate(self, method_id: str) -> LayerScore: ...

            # UNIT layer
            def evaluate(self, pdt: PDTStructure) -> LayerScore: ...

            # QUESTION layer
            def evaluate(self, method_id: str, question_id: str) -> LayerScore: ...
        """
        ...


@runtime_checkable
class BaseLayerEvaluatorProtocol(Protocol):
    """
    Specific protocol for BASE layer evaluation.

    BASE layer evaluates intrinsic method quality from pre-computed
    calibration scores (b_theory, b_impl, b_deploy).
    """

    def evaluate(self, method_id: str) -> LayerScore:
        """
        Evaluate BASE layer for a method.

        Args:
            method_id: Canonical method identifier

        Returns:
            LayerScore with @b score and component breakdown
        """
        ...


@runtime_checkable
class UnitLayerEvaluatorProtocol(Protocol):
    """
    Specific protocol for UNIT layer evaluation.

    UNIT layer evaluates PDT quality through 4 components: S, M, I, P.
    """

    def evaluate(self, pdt: "PDTStructure") -> LayerScore:  # type: ignore
        """
        Evaluate UNIT layer from PDT structure.

        Args:
            pdt: Parsed PDT structure

        Returns:
            LayerScore with U score and SMIP components
        """
        ...


@runtime_checkable
class ContextualLayerEvaluatorProtocol(Protocol):
    """
    Protocol for contextual layers (@q, @d, @p).

    These layers evaluate method-context compatibility.
    """

    def evaluate_question(self, method_id: str, question_id: str) -> float:
        """Evaluate @q (question compatibility)."""
        ...

    def evaluate_dimension(self, method_id: str, dimension: str) -> float:
        """Evaluate @d (dimension compatibility)."""
        ...

    def evaluate_policy(self, method_id: str, policy_area: str) -> float:
        """Evaluate @p (policy compatibility)."""
        ...


@runtime_checkable
class CongruenceLayerEvaluatorProtocol(Protocol):
    """
    Protocol for CONGRUENCE layer (@C).

    Evaluates ensemble validity when multiple methods work together.
    """

    def evaluate(
        self,
        method_ids: list[str],
        subgraph_id: str,
        fusion_rule: str,
        available_inputs: list[str]
    ) -> float:
        """
        Evaluate congruence for a method ensemble.

        Args:
            method_ids: List of methods in the ensemble
            subgraph_id: Identifier for the interaction subgraph
            fusion_rule: How outputs are combined (e.g., "weighted_average")
            available_inputs: Inputs available to the ensemble

        Returns:
            Congruence score ∈ [0.0, 1.0]
        """
        ...


@runtime_checkable
class ChainLayerEvaluatorProtocol(Protocol):
    """
    Protocol for CHAIN layer (@chain).

    Evaluates data flow integrity between method inputs and outputs.
    """

    def evaluate(
        self,
        method_id: str,
        provided_inputs: list[str]
    ) -> float:
        """
        Evaluate chain integrity for a method.

        Args:
            method_id: Method identifier
            provided_inputs: Inputs provided to the method

        Returns:
            Chain score ∈ [0.0, 1.0]
        """
        ...


@runtime_checkable
class MetaLayerEvaluatorProtocol(Protocol):
    """
    Protocol for META layer (@m).

    Evaluates governance, transparency, and computational cost.
    """

    def evaluate(
        self,
        method_id: str,
        method_version: str,
        config_hash: str,
        formula_exported: bool,
        full_trace: bool,
        logs_conform: bool,
        signature_valid: bool,
        execution_time_s: float | None
    ) -> float:
        """
        Evaluate meta/governance layer.

        Args:
            method_id: Method identifier
            method_version: Semantic version
            config_hash: Configuration hash for reproducibility
            formula_exported: Whether computation formula is exported
            full_trace: Whether full execution trace is available
            logs_conform: Whether logs conform to schema
            signature_valid: Whether cryptographic signature is valid
            execution_time_s: Execution time in seconds (None if not measured)

        Returns:
            Meta score ∈ [0.0, 1.0]
        """
        ...


def validate_evaluator_protocol(evaluator: object, protocol_type: type) -> bool:
    """
    Validate that an evaluator satisfies a protocol.

    This is useful for runtime validation before using an evaluator.

    Args:
        evaluator: The evaluator instance to check
        protocol_type: The protocol type to check against (e.g., LayerEvaluator)

    Returns:
        True if evaluator satisfies protocol, False otherwise

    Example:
        evaluator = BaseLayerEvaluator("config/intrinsic_calibration.json")
        assert validate_evaluator_protocol(evaluator, LayerEvaluator)
    """
    return isinstance(evaluator, protocol_type)
