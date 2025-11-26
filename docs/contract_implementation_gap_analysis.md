# Contract v3 Implementation Gap Analysis

**Date**: 2025-11-26
**Contract Analyzed**: D1-Q1.v3.CANONICAL.json
**Python Module**: BaseExecutorWithContract._execute_v3()

## Executive Summary

**CRITICAL GAP IDENTIFIED**: The contract specifies 17 methods in `methodological_depth`, but `BaseExecutorWithContract._execute_v3()` **only executes ONE method** from `method_binding`. This is a fundamental mismatch between contract specification and implementation.

## Contract Field Analysis

| Contract Field | Backed by Python? | Usage Details | Action Required |
|----------------|-------------------|---------------|-----------------|
| **identity** | ✅ **YES** | Lines 303-307: Extracts base_slot, question_id, dimension_id, policy_area_id | None |
| **executor_binding** | ⚠️ **PARTIAL** | Not validated or enforced, just present in contract | Add validation |
| **method_binding** | ❌ **CRITICAL GAP** | Lines 321-349: Only executes **SINGLE** method (class_name, method_name). Contract has 17 methods! | **REFACTOR REQUIRED** |
| **question_context** | ✅ **YES** | Lines 310-313: Extracts patterns, expected_elements from contract | None |
| **signal_requirements** | ❌ **NO** | Not used at all - placeholder only | Document as future feature |
| **evidence_assembly** | ✅ **YES** | Lines 360-364: Uses assembly_rules with EvidenceAssembler | None |
| **output_contract** | ✅ **PARTIAL** | Lines 393-402: Validates schema, generates human_readable_output | Enhance template rendering |
| **output_contract.human_readable_output.methodological_depth** | ❌ **NO** | Documentation only, not executed | Document as metadata |
| **validation_rules** | ✅ **YES** | Lines 367-371: Validates evidence with EvidenceValidator | None |
| **traceability** | ❌ **NO** | Documentation only | Document as metadata |
| **error_handling** | ✅ **YES** | Lines 374-377: Checks failure_contract via _check_failure_contract() | None |
| **fallback_strategy** | ❌ **NO** | Not implemented | Document as future feature |
| **test_configuration** | ❌ **NO** | Documentation only | Document as metadata |
| **compatibility** | ❌ **NO** | Documentation only | Document as metadata |
| **calibration** | ❌ **NO** | Placeholder only | Document as future feature |

## Critical Issue: Multi-Method Orchestration Not Supported in v3

### The Problem

**Contract Says (method_binding section)**:
```json
{
  "method_binding": {
    "orchestration_mode": "multi_method_pipeline",
    "primary_method": {
      "class_name": "TextMiningEngine",
      "method_name": "diagnose_critical_links"
    },
    "method_count": 17
  }
}
```

**Python Does (BaseExecutorWithContract._execute_v3, lines 321-349)**:
```python
# Extract method binding
method_binding = contract["method_binding"]
class_name = method_binding["class_name"]  # ← Expects single class_name
method_name = method_binding["method_name"]  # ← Expects single method_name

# Execute primary method
result = self.method_executor.execute(
    class_name=class_name,
    method_name=method_name,
    **common_kwargs,
)
method_outputs["primary_analysis"] = result  # ← Only ONE method output
```

### v2 vs v3 Comparison

**v2 Contract (SUPPORTS MULTI-METHOD)**:
```json
{
  "method_inputs": [
    {"class": "TextMiningEngine", "method": "diagnose_critical_links", "priority": 1, "provides": "text_mining"},
    {"class": "IndustrialPolicyProcessor", "method": "process", "priority": 2, "provides": "policy_processing"},
    ...
  ]
}
```

**v2 Python Code (lines 221-252)**:
```python
method_inputs = contract.get("method_inputs", [])
sorted_inputs = sorted(method_inputs, key=lambda pair: pair.get("priority", 2))
for entry in sorted_inputs:
    class_name = entry["class"]
    method_name = entry["method"]
    provides = entry.get("provides", [])

    result = self.method_executor.execute(
        class_name=class_name,
        method_name=method_name,
        **payload,
    )
    method_outputs[provides] = result  # ← Multiple method outputs accumulated
```

## Output Structure Gap

### Phase2QuestionResult Dataclass

```python
@dataclass
class Phase2QuestionResult:
    base_slot: str
    question_id: str
    question_global: int | None
    policy_area_id: str | None = None
    dimension_id: str | None = None
    cluster_id: str | None = None
    evidence: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    trace: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    # ❌ MISSING: human_readable_output field!
```

**But _execute_v3 adds** (line 400-402):
```python
result_data["human_readable_output"] = self._generate_human_readable_output(...)
```

**Gap**: Phase2QuestionResult should include `human_readable_output: str | None = None`

## Proposed Solutions

### Option 1: Extend v3 to Support Multi-Method (RECOMMENDED)

Modify `method_binding` schema and `_execute_v3` to support:

```json
{
  "method_binding": {
    "orchestration_mode": "multi_method_pipeline",
    "methods": [
      {
        "class_name": "TextMiningEngine",
        "method_name": "diagnose_critical_links",
        "priority": 1,
        "provides": "text_mining.critical_links"
      },
      {
        "class_name": "TextMiningEngine",
        "method_name": "_analyze_link_text",
        "priority": 2,
        "provides": "text_mining.link_analysis"
      },
      ... (15 more)
    ]
  }
}
```

**Python Changes**:
```python
def _execute_v3(...):
    # ...
    method_binding = contract["method_binding"]
    orchestration_mode = method_binding.get("orchestration_mode", "single_method")

    method_outputs: dict[str, Any] = {}

    if orchestration_mode == "multi_method_pipeline":
        methods = method_binding["methods"]
        sorted_methods = sorted(methods, key=lambda m: m.get("priority", 99))

        for method_spec in sorted_methods:
            class_name = method_spec["class_name"]
            method_name = method_spec["method_name"]
            provides = method_spec.get("provides", f"{class_name}.{method_name}")

            result = self.method_executor.execute(
                class_name=class_name,
                method_name=method_name,
                **common_kwargs,
            )

            # Store in nested structure: text_mining.critical_links
            _set_nested_value(method_outputs, provides, result)
    else:
        # Single method mode (backward compatible)
        class_name = method_binding["class_name"]
        method_name = method_binding["method_name"]
        result = self.method_executor.execute(...)
        method_outputs["primary_analysis"] = result

    # Rest of evidence assembly...
```

### Option 2: Use v2 for Multi-Method Executors

Keep v3 as single-method only, use v2 contracts for multi-method executors like D1-Q1.

**Drawback**: Loses benefits of v3 structure (better organization, validation, documentation)

### Option 3: Hybrid Approach

Treat `methodological_depth` methods as **documentation only**, execute only the `primary_method`. Evidence from all 17 methods comes from the single primary method call (which internally calls the other 16).

**Drawback**: Violates the promise of the contract - methods listed should be executed

## Recommended Action Plan

1. ✅ **Document current gaps** (this document)
2. ⬜ **Update executor_contract.v3.schema.json** to support multi-method orchestration
3. ⬜ **Refactor BaseExecutorWithContract._execute_v3()** to execute multiple methods
4. ⬜ **Update Phase2QuestionResult** dataclass to include `human_readable_output`
5. ⬜ **Add human_answer_structure** to contract showing expected evidence structure
6. ⬜ **Regenerate D1-Q1.v3.CANONICAL.json** with corrected method_binding structure
7. ⬜ **Write integration tests** to validate 17-method execution

## Fields That Are Documentation-Only (OK)

These fields serve as metadata/documentation and are NOT expected to be executed:

- ✅ **traceability**: Provenance information for auditing
- ✅ **test_configuration**: Testing metadata
- ✅ **compatibility**: Version compatibility notes
- ✅ **output_contract.human_readable_output.methodological_depth**: Epistemological documentation
- ✅ **calibration** (for now): Placeholder for future calibration system

These should be marked as `"_meta"` or `"_documentation"` sections in future schema versions.

## Human Answer Structure Requirements

The user requested `human_answer_structure` showing the **actual output structure** from the 17 methods. This should be a concrete example:

```json
{
  "human_answer_structure": {
    "description": "Expected structure of evidence dict after 17 methods execute and evidence is assembled",
    "example": {
      "elements_found": [
        {"type": "fuentes_oficiales", "value": "DANE", "confidence": 0.95, "source_sentence": "..."},
        {"type": "indicadores_cuantitativos", "value": "tasa de VBG: 12.3%", "confidence": 0.89, "source_sentence": "..."}
      ],
      "critical_links": [
        {"cause": "alta tasa de VBG", "effect": "baja autonomía económica", "confidence": 0.78}
      ],
      "financial_amounts": [
        {"amount": 15000000, "currency": "COP", "category": "SGR", "confidence": 0.92}
      ],
      "goals_extracted": [
        {"goal_verb": "reducir", "target": "VBG", "quantifier": "20%", "timeframe": "2024-2027"}
      ],
      "quantitative_claims": [
        {"subject": "tasa de VBG", "value": 12.3, "unit": "%", "sentence_id": 45}
      ],
      "bayesian_metrics": {
        "vbg_rate_posterior": {"mean": 0.123, "ci_95": [0.11, 0.14]},
        "comparison_vs_national": {"prob_higher": 0.87}
      },
      "semantic_chunks": [
        {"chunk_id": 1, "text": "...", "embedding": [...], "relevance": 0.91}
      ]
    },
    "schema": {
      "type": "object",
      "properties": {
        "elements_found": {"type": "array", "items": {...}},
        "critical_links": {"type": "array", "items": {...}},
        "financial_amounts": {"type": "array", "items": {...}},
        "goals_extracted": {"type": "array", "items": {...}},
        "quantitative_claims": {"type": "array", "items": {...}},
        "bayesian_metrics": {"type": "object", "properties": {...}},
        "semantic_chunks": {"type": "array", "items": {...}}
      }
    }
  }
}
```

This makes the contract **actionable** - developers know exactly what data structure to expect.

---

## Conclusion

The D1-Q1.v3.CANONICAL.json contract is **structurally excellent** but has a **critical implementation gap**: the Python code cannot execute the 17 methods specified. We must either:

1. **Refactor Python** to support multi-method v3 execution (recommended)
2. **Revise contract** to match current single-method v3 implementation
3. **Use v2 format** for multi-method executors

The user's request to add `human_answer_structure` is essential and should be done **after** resolving the multi-method orchestration issue.
