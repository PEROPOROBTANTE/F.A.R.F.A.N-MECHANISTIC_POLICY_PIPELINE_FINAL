from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from jsonschema import Draft7Validator

from saaaaaa.config.paths import PROJECT_ROOT
from saaaaaa.core.orchestrator.evidence_assembler import EvidenceAssembler
from saaaaaa.core.orchestrator.evidence_validator import EvidenceValidator
from saaaaaa.core.orchestrator.evidence_registry import get_global_registry

if TYPE_CHECKING:
    from saaaaaa.core.orchestrator.core import MethodExecutor, PreprocessedDocument
else:  # pragma: no cover - runtime avoids import to break cycles
    MethodExecutor = Any
    PreprocessedDocument = Any


class BaseExecutorWithContract(ABC):
    """Contract-driven executor that routes all calls through MethodExecutor.

    Supports both v2 and v3 contract formats:
    - v2: Legacy format with method_inputs, assembly_rules, validation_rules at top level
    - v3: New format with identity, executor_binding, method_binding, question_context,
          evidence_assembly, output_contract, validation_rules, etc.

    Contract version is auto-detected based on file name (.v3.json vs .json) and structure.
    """

    _contract_cache: dict[str, dict[str, Any]] = {}
    _schema_validators: dict[str, Draft7Validator] = {}

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
    def _get_schema_validator(cls, version: str = "v2") -> Draft7Validator:
        """Get schema validator for the specified contract version.

        Args:
            version: Contract version ("v2" or "v3")

        Returns:
            Draft7Validator for the specified version
        """
        if version not in cls._schema_validators:
            if version == "v3":
                schema_path = PROJECT_ROOT / "config" / "schemas" / "executor_contract.v3.schema.json"
            else:
                schema_path = PROJECT_ROOT / "config" / "executor_contract.schema.json"

            if not schema_path.exists():
                raise FileNotFoundError(f"Contract schema not found: {schema_path}")
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            cls._schema_validators[version] = Draft7Validator(schema)
        return cls._schema_validators[version]

    @classmethod
    def _detect_contract_version(cls, contract: dict[str, Any]) -> str:
        """Detect contract version from structure.

        v3 contracts have: identity, executor_binding, method_binding, question_context
        v2 contracts have: method_inputs, assembly_rules at top level

        Returns:
            "v3" or "v2"
        """
        v3_indicators = ["identity", "executor_binding", "method_binding", "question_context"]
        if all(key in contract for key in v3_indicators):
            return "v3"
        return "v2"

    @classmethod
    def _load_contract(cls) -> dict[str, Any]:
        base_slot = cls.get_base_slot()
        if base_slot in cls._contract_cache:
            return cls._contract_cache[base_slot]

        # Try v3 contract first, then fall back to v2
        v3_path = PROJECT_ROOT / "config" / "executor_contracts" / f"{base_slot}.v3.json"
        v2_path = PROJECT_ROOT / "config" / "executor_contracts" / f"{base_slot}.json"

        if v3_path.exists():
            contract_path = v3_path
            expected_version = "v3"
        elif v2_path.exists():
            contract_path = v2_path
            expected_version = "v2"
        else:
            raise FileNotFoundError(
                f"Contract not found for {base_slot}. "
                f"Tried: {v3_path}, {v2_path}"
            )

        contract = json.loads(contract_path.read_text(encoding="utf-8"))

        # Detect actual version from structure
        detected_version = cls._detect_contract_version(contract)
        if detected_version != expected_version:
            import logging
            logging.warning(
                f"Contract {contract_path.name} has structure of {detected_version} "
                f"but file naming suggests {expected_version}"
            )

        # Validate with appropriate schema
        validator = cls._get_schema_validator(detected_version)
        errors = sorted(validator.iter_errors(contract), key=lambda e: e.path)
        if errors:
            messages = "; ".join(err.message for err in errors)
            raise ValueError(f"Contract validation failed for {base_slot} ({detected_version}): {messages}")

        # Tag contract with version for later use
        contract["_contract_version"] = detected_version

        contract_version = contract.get("contract_version")
        if contract_version and not str(contract_version).startswith("2"):
            raise ValueError(f"Unsupported contract_version {contract_version} for {base_slot}; expected v2.x")

        identity_base_slot = contract.get("identity", {}).get("base_slot")
        if identity_base_slot and identity_base_slot != base_slot:
            raise ValueError(f"Contract base_slot mismatch: expected {base_slot}, found {identity_base_slot}")

        cls._contract_cache[base_slot] = contract
        return contract

    @staticmethod
    def _set_nested_value(target_dict: dict[str, Any], key_path: str, value: Any) -> None:
        """Set a value in a nested dict using dot-notation key path.

        Args:
            target_dict: The dictionary to modify
            key_path: Dot-separated path (e.g., "text_mining.critical_links")
            value: The value to set

        Example:
            _set_nested_value(d, "a.b.c", 123) → d["a"]["b"]["c"] = 123
        """
        keys = key_path.split(".")
        current = target_dict

        # Navigate to the parent of the final key, creating dicts as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # Key exists but is not a dict, cannot nest further
                raise ValueError(
                    f"Cannot set nested value at '{key_path}': "
                    f"intermediate key '{key}' exists but is not a dict"
                )
            current = current[key]

        # Set the final key
        current[keys[-1]] = value

    def _check_failure_contract(self, evidence: dict[str, Any], error_handling: dict[str, Any]):
        failure_contract = error_handling.get("failure_contract", {})
        abort_conditions = failure_contract.get("abort_if", [])
        if not abort_conditions:
            return

        emit_code = failure_contract.get("emit_code", "GENERIC_ABORT")

        for condition in abort_conditions:
            # Example condition check. This could be made more sophisticated.
            if condition == "missing_required_element" and evidence.get("validation", {}).get("errors"):
                # This logic assumes errors from the validator imply a missing required element,
                # which is true with our new validator.
                raise ValueError(f"Execution aborted by failure contract due to '{condition}'. Emit code: {emit_code}")
            if condition == "incomplete_text" and not evidence.get("metadata", {}).get("text_complete", True):
                raise ValueError(f"Execution aborted by failure contract due to '{condition}'. Emit code: {emit_code}")

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

        contract = self._load_contract()
        contract_version = contract.get("_contract_version", "v2")

        if contract_version == "v3":
            return self._execute_v3(document, question_context, contract)
        else:
            return self._execute_v2(document, question_context, contract)

    def _execute_v2(
        self,
        document: PreprocessedDocument,
        question_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute using v2 contract format (legacy)."""
        base_slot = self.get_base_slot()
        question_id = question_context.get("question_id")
        question_global = question_context.get("question_global")
        policy_area_id = question_context.get("policy_area_id")
        identity = question_context.get("identity", {})
        patterns = question_context.get("patterns", [])
        expected_elements = question_context.get("expected_elements", [])

        signal_pack = None
        if self.signal_registry is not None and hasattr(self.signal_registry, "get") and policy_area_id:
            signal_pack = self.signal_registry.get(policy_area_id)

        common_kwargs: dict[str, Any] = {
            "document": document,
            "base_slot": base_slot,
            "raw_text": getattr(document, "raw_text", None),
            "text": getattr(document, "raw_text", None),
            "question_id": question_id,
            "question_global": question_global,
            "policy_area_id": policy_area_id,
            "dimension_id": identity.get("dimension_id"),
            "cluster_id": identity.get("cluster_id"),
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

            if "signal_pack" in payload and payload["signal_pack"] is not None:
                if "_signal_usage" not in method_outputs:
                    method_outputs["_signal_usage"] = []
                method_outputs["_signal_usage"].append({
                    "method": f"{class_name}.{method_name}",
                    "policy_area": payload["signal_pack"].policy_area,
                    "version": payload["signal_pack"].version,
                })

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
        validation_rules_object = {"rules": validation_rules, "na_policy": na_policy}
        validation = EvidenceValidator.validate(evidence, validation_rules_object)

        error_handling = contract.get("error_handling", {})
        if error_handling:
            evidence_with_validation = {**evidence, "validation": validation}
            self._check_failure_contract(evidence_with_validation, error_handling)

        human_answer_template = contract.get("human_answer_template", "")
        human_answer = ""
        if human_answer_template:
            try:
                human_answer = human_answer_template.format(**evidence)
            except KeyError as e:
                human_answer = f"Error formatting human answer: Missing key {e}. Template: '{human_answer_template}'"
                import logging
                logging.warning(human_answer)

        result = {
            "base_slot": base_slot,
            "question_id": question_id,
            "question_global": question_global,
            "policy_area_id": policy_area_id,
            "dimension_id": identity.get("dimension_id"),
            "cluster_id": identity.get("cluster_id"),
            "evidence": evidence,
            "validation": validation,
            "trace": trace,
            "human_answer": human_answer,
        }

        return result

    def _execute_v3(
        self,
        document: PreprocessedDocument,
        question_context_external: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute using v3 contract format.

        In v3, contract contains all context, so we use contract['question_context']
        instead of question_context_external (which comes from orchestrator).
        """
        # Extract identity from contract
        identity = contract["identity"]
        base_slot = identity["base_slot"]
        question_id = identity["question_id"]
        dimension_id = identity["dimension_id"]
        policy_area_id = identity["policy_area_id"]

        # Extract question context from contract (source of truth for v3)
        question_context = contract["question_context"]
        question_global = question_context_external.get("question_global")  # May come from orchestrator
        patterns = question_context.get("patterns", [])
        expected_elements = question_context.get("expected_elements", [])

        # Signal pack
        signal_pack = None
        if self.signal_registry is not None and hasattr(self.signal_registry, "get") and policy_area_id:
            signal_pack = self.signal_registry.get(policy_area_id)

        # Extract method binding
        method_binding = contract["method_binding"]
        orchestration_mode = method_binding.get("orchestration_mode", "single_method")

        # Prepare common kwargs
        common_kwargs: dict[str, Any] = {
            "document": document,
            "base_slot": base_slot,
            "raw_text": getattr(document, "raw_text", None),
            "text": getattr(document, "raw_text", None),
            "question_id": question_id,
            "question_global": question_global,
            "policy_area_id": policy_area_id,
            "dimension_id": dimension_id,
            "cluster_id": identity.get("cluster_id"),
            "signal_pack": signal_pack,
            "question_patterns": patterns,
            "expected_elements": expected_elements,
            "question_context": question_context,
        }

        # Execute methods based on orchestration mode
        method_outputs: dict[str, Any] = {}
        signal_usage_list: list[dict[str, Any]] = []

        if orchestration_mode == "multi_method_pipeline":
            # Multi-method execution: process all methods in priority order
            methods = method_binding.get("methods", [])
            if not methods:
                raise ValueError(
                    f"orchestration_mode is 'multi_method_pipeline' but no methods array found in method_binding for {base_slot}"
                )

            # Sort by priority (lower priority number = execute first)
            sorted_methods = sorted(methods, key=lambda m: m.get("priority", 99))

            for method_spec in sorted_methods:
                class_name = method_spec["class_name"]
                method_name = method_spec["method_name"]
                provides = method_spec.get("provides", f"{class_name}.{method_name}")
                priority = method_spec.get("priority", 99)

                try:
                    result = self.method_executor.execute(
                        class_name=class_name,
                        method_name=method_name,
                        **common_kwargs,
                    )

                    # Store result using nested key structure (e.g., "text_mining.critical_links")
                    self._set_nested_value(method_outputs, provides, result)

                    # Track signal usage for this method
                    if signal_pack is not None:
                        signal_usage_list.append({
                            "method": f"{class_name}.{method_name}",
                            "policy_area": signal_pack.policy_area,
                            "version": signal_pack.version,
                            "priority": priority,
                        })

                except Exception as exc:
                    import logging
                    logging.error(
                        f"Method execution failed in multi-method pipeline: {class_name}.{method_name}",
                        exc_info=True,
                    )
                    # Store error in trace for debugging
                    self._set_nested_value(
                        method_outputs,
                        f"_errors.{provides}",
                        {"error": str(exc), "method": f"{class_name}.{method_name}"},
                    )
                    # Re-raise if error_handling policy requires it
                    error_handling = contract.get("error_handling", {})
                    on_method_failure = error_handling.get("on_method_failure", "propagate_with_trace")
                    if on_method_failure == "raise":
                        raise
                    # Otherwise continue with other methods

        else:
            # Single-method execution (backward compatible, default)
            class_name = method_binding.get("class_name")
            method_name = method_binding.get("method_name")

            if not class_name or not method_name:
                # Try primary_method if direct class_name/method_name not found
                primary_method = method_binding.get("primary_method", {})
                class_name = primary_method.get("class_name") or class_name
                method_name = primary_method.get("method_name") or method_name

            if not class_name or not method_name:
                raise ValueError(
                    f"Invalid method_binding for {base_slot}: missing class_name or method_name"
                )

            result = self.method_executor.execute(
                class_name=class_name,
                method_name=method_name,
                **common_kwargs,
            )
            method_outputs["primary_analysis"] = result

            # Track signal usage
            if signal_pack is not None:
                signal_usage_list.append({
                    "method": f"{class_name}.{method_name}",
                    "policy_area": signal_pack.policy_area,
                    "version": signal_pack.version,
                })

        # Store signal usage in method_outputs for trace
        if signal_usage_list:
            method_outputs["_signal_usage"] = signal_usage_list

        # Evidence assembly
        evidence_assembly = contract["evidence_assembly"]
        assembly_rules = evidence_assembly["assembly_rules"]
        assembled = EvidenceAssembler.assemble(method_outputs, assembly_rules)
        evidence = assembled["evidence"]
        trace = assembled["trace"]

        # Validation
        validation_rules_section = contract["validation_rules"]
        validation_rules = validation_rules_section.get("rules", [])
        na_policy = validation_rules_section.get("na_policy", "abort_on_critical")
        validation_rules_object = {"rules": validation_rules, "na_policy": na_policy}
        validation = EvidenceValidator.validate(evidence, validation_rules_object)

        # Error handling
        error_handling = contract["error_handling"]
        if error_handling:
            evidence_with_validation = {**evidence, "validation": validation}
            self._check_failure_contract(evidence_with_validation, error_handling)

        # Build result
        result_data = {
            "base_slot": base_slot,
            "question_id": question_id,
            "question_global": question_global,
            "policy_area_id": policy_area_id,
            "dimension_id": dimension_id,
            "cluster_id": identity.get("cluster_id"),
            "evidence": evidence,
            "validation": validation,
            "trace": trace,
        }

        # Validate output against output_contract schema if present
        output_contract = contract.get("output_contract", {})
        if output_contract and "schema" in output_contract:
            self._validate_output_contract(result_data, output_contract["schema"])

        # Generate human_readable_output if template exists
        human_readable_config = output_contract.get("human_readable_output", {})
        if human_readable_config:
            result_data["human_readable_output"] = self._generate_human_readable_output(
                evidence, validation, human_readable_config
            )

        return result_data

    def _validate_output_contract(self, result: dict[str, Any], schema: dict[str, Any]) -> None:
        """Validate result against output_contract schema.

        Raises:
            ValueError: If validation fails
        """
        from jsonschema import ValidationError, validate
        try:
            validate(instance=result, schema=schema)
        except ValidationError as e:
            raise ValueError(
                f"Output contract validation failed for {result.get('base_slot')}: {e.message}"
            ) from e

    def _generate_human_readable_output(
        self,
        evidence: dict[str, Any],
        validation: dict[str, Any],
        config: dict[str, Any],
    ) -> str:
        """Generate human-readable output from template.

        This is a basic implementation. A full implementation would:
        - Parse template variables like {evidence.elements_found_count}
        - Calculate derived metrics (means, counts, etc.)
        - Format in specified format (markdown, html, plain_text)

        Args:
            evidence: Evidence dict
            validation: Validation dict
            config: human_readable_output config from contract

        Returns:
            Formatted string
        """
        template_config = config.get("template", {})
        format_type = config.get("format", "markdown")

        # Basic template rendering (simplified)
        # TODO: Implement full template engine with variable substitution
        sections = []
        if "title" in template_config:
            sections.append(template_config["title"])
        if "summary" in template_config:
            sections.append(template_config["summary"])

        # Placeholder: full implementation would parse {variable} syntax
        output = "\n\n".join(sections)
        return output
