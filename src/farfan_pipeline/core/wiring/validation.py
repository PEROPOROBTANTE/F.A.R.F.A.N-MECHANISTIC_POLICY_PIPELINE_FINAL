"""Contract validation between wiring links.

Validates that deliverables from one module match expectations of the next.
All validations use Pydantic models for type safety and prescriptive errors.
"""

from __future__ import annotations

from typing import Any

import blake3
import structlog
from pydantic import BaseModel, ValidationError

from .contracts import (
    AdapterExpectation,
    AggregateExpectation,
    ArgRouterExpectation,
    ArgRouterPayloadDeliverable,
    CPPDeliverable,
    SPCDeliverable,
    EnrichedChunkDeliverable,
    ExecutorInputDeliverable,
    FeatureTableDeliverable,
    OrchestratorExpectation,
    PreprocessedDocumentDeliverable,
    ReportExpectation,
    ScoreExpectation,
    ScoresDeliverable,
    SignalPackDeliverable,
    SignalRegistryExpectation,
)
from .errors import WiringContractError

logger = structlog.get_logger(__name__)


class LinkValidator:
    """Validator for individual wiring links.

    Validates deliverable→expectation contracts and computes hashes for determinism.
    """

    def __init__(self, link_name: str) -> None:
        """Initialize validator for a specific link.

        Args:
            link_name: Name of the link (e.g., "cpp->adapter")
        """
        self.link_name = link_name
        self._validation_count = 0
        self._failure_count = 0

    def validate(
        self,
        deliverable_data: dict[str, Any],
        deliverable_model: type[BaseModel],
        expectation_model: type[BaseModel],
    ) -> None:
        """Validate deliverable matches expectation.

        Args:
            deliverable_data: Actual data being delivered
            deliverable_model: Pydantic model for deliverable
            expectation_model: Pydantic model for expectation

        Raises:
            WiringContractError: If validation fails
        """
        self._validation_count += 1

        # Validate deliverable schema
        try:
            deliverable = deliverable_model.model_validate(deliverable_data)
        except ValidationError as e:
            self._failure_count += 1

            errors = e.errors()
            first_error = errors[0] if errors else {}
            field = ".".join(str(loc) for loc in first_error.get("loc", []))

            raise WiringContractError(
                link=self.link_name,
                expected_schema=deliverable_model.__name__,
                received_schema=type(deliverable_data).__name__,
                field=field or None,
                fix=f"Ensure {self.link_name} produces valid {deliverable_model.__name__}. "
                    f"Error: {first_error.get('msg', 'Unknown')}",
            ) from e

        # Validate expectation schema
        # (This ensures the downstream consumer can handle the deliverable)
        try:
            expectation_model.model_validate(deliverable.model_dump())
        except ValidationError as e:
            self._failure_count += 1

            errors = e.errors()
            first_error = errors[0] if errors else {}
            field = ".".join(str(loc) for loc in first_error.get("loc", []))

            raise WiringContractError(
                link=self.link_name,
                expected_schema=expectation_model.__name__,
                received_schema=deliverable_model.__name__,
                field=field or None,
                fix=f"Deliverable from {self.link_name} does not meet expectations. "
                    f"Error: {first_error.get('msg', 'Unknown')}",
            ) from e

        logger.debug(
            "contract_validated",
            link=self.link_name,
            deliverable=deliverable_model.__name__,
            expectation=expectation_model.__name__,
        )

    def compute_hash(self, data: dict[str, Any]) -> str:
        """Compute deterministic hash of data for this link.

        Args:
            data: Data to hash

        Returns:
            BLAKE3 hash hex string
        """
        import json

        # Sort keys for deterministic hashing
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        hash_value = blake3.blake3(json_str.encode('utf-8')).hexdigest()

        logger.debug(
            "link_hash_computed",
            link=self.link_name,
            hash=hash_value[:16],
        )

        return hash_value

    def get_metrics(self) -> dict[str, Any]:
        """Get validation metrics.

        Returns:
            Dict with validation_count and failure_count
        """
        return {
            "validation_count": self._validation_count,
            "failure_count": self._failure_count,
            "success_rate": (
                (self._validation_count - self._failure_count) / self._validation_count
                if self._validation_count > 0
                else 1.0
            ),
        }


class WiringValidator:
    """Central validator for all wiring links.

    Provides validation methods for each i→i+1 link in the system.
    """

    def __init__(self) -> None:
        """Initialize wiring validator."""
        self._validators = {
            "cpp->adapter": LinkValidator("cpp->adapter"),
            "spc->adapter": LinkValidator("spc->adapter"),
            "adapter->orchestrator": LinkValidator("adapter->orchestrator"),
            "orchestrator->argrouter": LinkValidator("orchestrator->argrouter"),
            "argrouter->executors": LinkValidator("argrouter->executors"),
            "signals->registry": LinkValidator("signals->registry"),
            "executors->aggregate": LinkValidator("executors->aggregate"),
            "aggregate->score": LinkValidator("aggregate->score"),
            "score->report": LinkValidator("score->report"),
        }

        logger.info("wiring_validator_initialized", links=len(self._validators))

    def validate_spc_to_adapter(self, spc_data: dict[str, Any]) -> None:
        """Validate SPC → Adapter link.

        Args:
            spc_data: SPC deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        from .contracts import SPCDeliverable

        validator = self._validators["spc->adapter"]
        validator.validate(
            deliverable_data=spc_data,
            deliverable_model=SPCDeliverable,
            expectation_model=AdapterExpectation,
        )

    def validate_cpp_to_adapter(self, cpp_data: dict[str, Any]) -> None:
        """Validate CPP → Adapter link.

        DEPRECATED: Use validate_spc_to_adapter instead.

        Args:
            cpp_data: CPP deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        # Forward to new validator if possible, but keep legacy link name for now
        # to avoid breaking existing hashes if they depend on link name.
        # However, we should warn.
        import warnings
        warnings.warn(
            "validate_cpp_to_adapter is deprecated. Use validate_spc_to_adapter instead.",
            DeprecationWarning,
            stacklevel=2
        )

        validator = self._validators["cpp->adapter"]
        validator.validate(
            deliverable_data=cpp_data,
            deliverable_model=CPPDeliverable,
            expectation_model=AdapterExpectation,
        )

    def validate_adapter_to_orchestrator(
        self,
        preprocessed_doc_data: dict[str, Any],
    ) -> None:
        """Validate Adapter → Orchestrator link.

        Args:
            preprocessed_doc_data: PreprocessedDocument deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        validator = self._validators["adapter->orchestrator"]
        validator.validate(
            deliverable_data=preprocessed_doc_data,
            deliverable_model=PreprocessedDocumentDeliverable,
            expectation_model=OrchestratorExpectation,
        )

    def validate_orchestrator_to_argrouter(
        self,
        payload_data: dict[str, Any],
    ) -> None:
        """Validate Orchestrator → ArgRouter link.

        Args:
            payload_data: ArgRouter payload deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        validator = self._validators["orchestrator->argrouter"]
        validator.validate(
            deliverable_data=payload_data,
            deliverable_model=ArgRouterPayloadDeliverable,
            expectation_model=ArgRouterExpectation,
        )

    def validate_argrouter_to_executors(
        self,
        executor_input_data: dict[str, Any],
    ) -> None:
        """Validate ArgRouter → Executors link.

        Args:
            executor_input_data: Executor input deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        self._validators["argrouter->executors"]
        # Note: ExecutorInput doesn't have a matching expectation model yet
        # For now, just validate the deliverable
        from pydantic import ValidationError

        try:
            ExecutorInputDeliverable.model_validate(executor_input_data)
        except ValidationError as e:
            raise WiringContractError(
                link="argrouter->executors",
                expected_schema=ExecutorInputDeliverable.__name__,
                received_schema=type(executor_input_data).__name__,
                field=str(e.errors()[0].get("loc", [])) if e.errors() else None,
                fix="Ensure ArgRouter produces valid ExecutorInputDeliverable",
            ) from e

    def validate_signals_to_registry(
        self,
        signal_pack_data: dict[str, Any],
    ) -> None:
        """Validate Signals → Registry link.

        Args:
            signal_pack_data: SignalPack deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        validator = self._validators["signals->registry"]
        validator.validate(
            deliverable_data=signal_pack_data,
            deliverable_model=SignalPackDeliverable,
            expectation_model=SignalRegistryExpectation,
        )

    def validate_executors_to_aggregate(
        self,
        enriched_chunks_data: list[dict[str, Any]],
    ) -> None:
        """Validate Executors → Aggregate link.

        Args:
            enriched_chunks_data: List of enriched chunk deliverables

        Raises:
            WiringContractError: If validation fails
        """
        validator = self._validators["executors->aggregate"]

        # Validate each chunk
        for i, chunk_data in enumerate(enriched_chunks_data):
            try:
                EnrichedChunkDeliverable.model_validate(chunk_data)
            except ValidationError as e:
                raise WiringContractError(
                    link="executors->aggregate",
                    expected_schema=EnrichedChunkDeliverable.__name__,
                    received_schema=type(chunk_data).__name__,
                    field=f"chunk[{i}]",
                    fix=f"Ensure all enriched chunks are valid. Chunk {i} failed validation.",
                ) from e

        # Validate aggregate expectation
        validator.validate(
            deliverable_data={"enriched_chunks": enriched_chunks_data},
            deliverable_model=AggregateExpectation,
            expectation_model=AggregateExpectation,  # Same for now
        )

    def validate_aggregate_to_score(
        self,
        feature_table_data: dict[str, Any],
    ) -> None:
        """Validate Aggregate → Score link.

        Args:
            feature_table_data: Feature table deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        validator = self._validators["aggregate->score"]
        validator.validate(
            deliverable_data=feature_table_data,
            deliverable_model=FeatureTableDeliverable,
            expectation_model=ScoreExpectation,
        )

    def validate_score_to_report(
        self,
        scores_data: dict[str, Any],
    ) -> None:
        """Validate Score → Report link.

        Args:
            scores_data: Scores deliverable data

        Raises:
            WiringContractError: If validation fails
        """
        validator = self._validators["score->report"]
        validator.validate(
            deliverable_data=scores_data,
            deliverable_model=ScoresDeliverable,
            expectation_model=ReportExpectation,
        )

    def compute_link_hash(self, link_name: str, data: dict[str, Any]) -> str:
        """Compute hash for a specific link.

        Args:
            link_name: Name of the link
            data: Data to hash

        Returns:
            BLAKE3 hash hex string

        Raises:
            KeyError: If link_name is not recognized
        """
        validator = self._validators[link_name]
        return validator.compute_hash(data)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all links.

        Returns:
            Dict mapping link names to their metrics
        """
        return {
            link_name: validator.get_metrics()
            for link_name, validator in self._validators.items()
        }

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all validation activity.

        Returns:
            Summary dict with total counts and success rate
        """
        all_metrics = self.get_all_metrics()

        total_validations = sum(m["validation_count"] for m in all_metrics.values())
        total_failures = sum(m["failure_count"] for m in all_metrics.values())

        return {
            "total_validations": total_validations,
            "total_failures": total_failures,
            "overall_success_rate": (
                (total_validations - total_failures) / total_validations
                if total_validations > 0
                else 1.0
            ),
            "links": all_metrics,
        }


__all__ = [
    'LinkValidator',
    'WiringValidator',
]
