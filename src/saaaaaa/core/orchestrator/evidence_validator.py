from __future__ import annotations

import re
from typing import Any, Iterable


class EvidenceValidator:
    """Validate assembled evidence with configurable rules."""

    @staticmethod
    def validate(evidence: dict[str, Any], rules_object: dict[str, Any]) -> dict[str, Any]:
        """
        Validates evidence against a rules object from a V2 contract.

        Args:
            evidence: The assembled evidence dictionary.
            rules_object: The validation object from the contract, containing
                          'rules' (a list) and 'na_policy' (a string).
        """
        validation_rules = rules_object.get("rules", [])
        na_policy = rules_object.get("na_policy", "abort_on_critical")
        errors: list[str] = []
        warnings: list[str] = []

        for rule in validation_rules:
            field = rule.get("field")
            value = EvidenceValidator._resolve(field, evidence)

            # --- New Rich Rule Logic ---
            if rule.get("must_contain"):
                must_contain = rule["must_contain"]
                required_elements = set(must_contain.get("elements", []))
                present_elements = set(value) if isinstance(value, list) else set()
                missing_elements = required_elements - present_elements
                if missing_elements:
                    errors.append(f"Field '{field}' is missing required elements: {', '.join(sorted(missing_elements))}")

                required_count = must_contain.get("count")
                if required_count and len(present_elements.intersection(required_elements)) < required_count:
                    errors.append(f"Field '{field}' did not meet the required count of {required_count} for elements: {', '.join(sorted(required_elements))}")
            
            if rule.get("should_contain"):
                should_contain = rule["should_contain"]
                present_elements = set(value) if isinstance(value, list) else set()
                for requirement in should_contain:
                    elements_to_check = set(requirement.get("elements", []))
                    min_count = requirement.get("minimum", 1)
                    found_count = len(present_elements.intersection(elements_to_check))
                    if found_count < min_count:
                        warnings.append(f"Field '{field}' only has {found_count}/{min_count} of recommended elements: {', '.join(sorted(elements_to_check))}")

            # --- Original Simple Rule Logic ---
            missing = value is None
            if rule.get("required") and missing:
                errors.append(f"Missing required field '{field}'")
                continue
            if missing:
                continue

            if rule.get("type", "any") != "any" and not EvidenceValidator._check_type(value, rule["type"]):
                errors.append(f"Field '{field}' has incorrect type (expected {rule['type']})")
                continue
            
            if rule.get("min_length") is not None and EvidenceValidator._has_length(value) and len(value) < rule["min_length"]:
                errors.append(f"Field '{field}' length below min_length {rule['min_length']}")
            
            if rule.get("pattern") and isinstance(value, str) and not re.search(rule["pattern"], value):
                errors.append(f"Field '{field}' does not match pattern")


        valid = not errors
        if errors and na_policy == "abort_on_critical":
            raise ValueError(f"Evidence validation failed with critical errors: {'; '.join(errors)}")

        return {"valid": valid, "errors": errors, "warnings": warnings}

    @staticmethod
    def _resolve(path: str, evidence: dict[str, Any]) -> Any:
        if not path:
            return None
        parts = path.split(".")
        current: Any = evidence
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _check_type(value: Any, expected: str) -> bool:
        mapping = {
            "array": (list, tuple),
            "integer": (int,),
            "float": (float, int),
            "string": (str,),
            "boolean": (bool,),
            "object": (dict,),
            "any": (object,),
        }
        return isinstance(value, mapping.get(expected, (object,)))

    @staticmethod
    def _has_length(value: Any) -> bool:
        return hasattr(value, "__len__")

    @staticmethod
    def _is_number(value: Any) -> bool:
        try:
            float(value)
            return not isinstance(value, bool)
        except (TypeError, ValueError):
            return False
