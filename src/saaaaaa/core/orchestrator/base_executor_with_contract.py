from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from jsonschema import Draft7Validator

from saaaaaa.config.paths import PROJECT_ROOT
from saaaaaa.core.orchestrator.evidence_assembler import EvidenceAssembler
from saaaaaa.core.orchestrator.evidence_validator import EvidenceValidator

if TYPE_CHECKING:
    from saaaaaa.core.orchestrator.core import MethodExecutor, PreprocessedDocument
else:  # pragma: no cover - runtime avoids import to break cycles
    MethodExecutor = Any
    PreprocessedDocument = Any


class BaseExecutorWithContract(ABC):
    """Contract-driven executor that routes all calls through MethodExecutor."""

    _contract_cache: dict[str, dict[str, Any]] = {}
    _schema_validator: Draft7Validator | None = None

    def __init__(
        self,
        method_executor: MethodExecutor,
        signal_registry: Any,
        config: Any,
        questionnaire_provider: Any,
        calibration_orchestrator: Any | None = None,
    ) -> None:
        try:
            from saaaaaa.core.orchestrator.core import MethodExecutor as _MethodExecutor
        except Exception as exc:  # pragma: no cover - defensive guard
            raise RuntimeError(
                "Failed to import MethodExecutor for BaseExecutorWithContract invariants. "
                "Ensure saaaaaa.core.orchestrator.core is importable before constructing contract executors."
            ) from exc
        if not isinstance(method_executor, _MethodExecutor):
            raise RuntimeError("A valid MethodExecutor instance is required for contract executors.")
        self.method_executor = method_executor
        self.signal_registry = signal_registry
        self.config = config
        self.questionnaire_provider = questionnaire_provider
        self.calibration_orchestrator = calibration_orchestrator

    @classmethod
    @abstractmethod
    def get_base_slot(cls) -> str:
        raise NotImplementedError

    @classmethod
    def _get_schema_validator(cls) -> Draft7Validator:
        if cls._schema_validator is None:
            schema_path = PROJECT_ROOT / "config" / "executor_contract.schema.json"
            if not schema_path.exists():
                raise FileNotFoundError(f"Contract schema not found: {schema_path}")
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            cls._schema_validator = Draft7Validator(schema)
        return cls._schema_validator

    @classmethod
    def _load_contract(cls) -> dict[str, Any]:
        base_slot = cls.get_base_slot()
        if base_slot in cls._contract_cache:
            return cls._contract_cache[base_slot]

        contract_path = PROJECT_ROOT / "config" / "executor_contracts" / f"{base_slot}.json"
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract not found: {contract_path}")

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        validator = cls._get_schema_validator()
        errors = sorted(validator.iter_errors(contract), key=lambda e: e.path)
        if errors:
            messages = "; ".join(err.message for err in errors)
            raise ValueError(f"Contract validation failed for {base_slot}: {messages}")

        cls._contract_cache[base_slot] = contract
        return contract

    def execute(
        self,
        document: PreprocessedDocument,
        method_executor: MethodExecutor,
        *,
        question_context: dict[str, Any],
    ) -> dict[str, Any]:
        if method_executor is not self.method_executor:
            raise RuntimeError("Mismatched MethodExecutor instance for contract executor")

        base_slot = self.get_base_slot()
        if question_context.get("base_slot") != base_slot:
            raise ValueError(
                f"Question base_slot {question_context.get('base_slot')} does not match executor {base_slot}"
            )

        question_id = question_context.get("question_id")
        question_global = question_context.get("question_global")
        policy_area_id = question_context.get("policy_area_id")
        dimension_id = question_context.get("dimension_id")
        cluster_id = question_context.get("cluster_id")
        patterns = question_context.get("patterns", [])
        expected_elements = question_context.get("expected_elements", [])

        signal_pack = None
        if self.signal_registry is not None and hasattr(self.signal_registry, "get") and policy_area_id:
            signal_pack = self.signal_registry.get(policy_area_id)

        contract = self._load_contract()

        common_kwargs: dict[str, Any] = {
            "document": document,
            "base_slot": base_slot,
            "raw_text": getattr(document, "raw_text", None),
            "text": getattr(document, "raw_text", None),
            "question_id": question_id,
            "question_global": question_global,
            "policy_area_id": policy_area_id,
            "dimension_id": dimension_id,
            "cluster_id": cluster_id,
            "signal_pack": signal_pack,
            "question_patterns": patterns,
            "expected_elements": expected_elements,
        }

        method_outputs: dict[str, Any] = {}
        method_inputs = contract.get("method_inputs", [])
        indexed = list(enumerate(method_inputs))
        sorted_inputs = sorted(indexed, key=lambda pair: (pair[1].get("priority", 2), pair[0]))
        for _, entry in sorted_inputs:
            class_name = entry["class"]
            method_name = entry["method"]
            provides = entry.get("provides", [])
            extra_args = entry.get("args", {})

            payload = {**common_kwargs, **extra_args}

            result = self.method_executor.execute(
                class_name=class_name,
                method_name=method_name,
                **payload,
            )

            if isinstance(provides, str):
                method_outputs[provides] = result
            else:
                for key in provides:
                    method_outputs[key] = result

        assembly_rules = contract.get("assembly_rules", [])
        assembled = EvidenceAssembler.assemble(method_outputs, assembly_rules)
        evidence = assembled["evidence"]
        trace = assembled["trace"]

        validation_rules = contract.get("validation_rules", [])
        na_policy = contract.get("na_policy", "abort")
        validation = EvidenceValidator.validate(evidence, validation_rules, na_policy=na_policy)

        return {
            "base_slot": base_slot,
            "question_id": question_id,
            "question_global": question_global,
            "policy_area_id": policy_area_id,
            "dimension_id": dimension_id,
            "cluster_id": cluster_id,
            "evidence": evidence,
            "validation": validation,
            "trace": trace,
        }
