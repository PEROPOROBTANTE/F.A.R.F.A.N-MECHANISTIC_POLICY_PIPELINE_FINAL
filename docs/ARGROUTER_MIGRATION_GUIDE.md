# ArgRouter to ExtendedArgRouter Migration Guide

## Overview

This document provides guidance for the transition from the legacy `ArgRouter` to the new `ExtendedArgRouter` implementation. The migration improves the codebase through:

- **Strict validation** to prevent silent parameter drops
- **30+ special routes** for commonly-called methods
- **Comprehensive metrics** for monitoring and debugging
- **Forward compatibility** with **kwargs support

## Current Status

✅ **All Phases Complete**
- Phase 1: ExtendedArgRouter integrated into MethodExecutor
- Phase 2: Metrics collection and CI integration
- Phase 3: Deprecation warnings (completed)
- Phase 4: Final consolidation into single arg_router.py module

**What Changed in Phase 4:**
- Consolidated all routing code into `src/saaaaaa/core/orchestrator/arg_router.py`
- Removed `arg_router_extended.py` (merged into main module)
- Removed compatibility shim at `orchestrator/arg_router.py`
- Both `ArgRouter` and `ExtendedArgRouter` now available from single import

## For Application Developers

### No Action Required

If you're using the orchestrator through standard APIs, **no changes are needed**. The `MethodExecutor` automatically uses `ExtendedArgRouter` as of Phase 1.

### Using the Router (Post Phase 4)

All routing functionality is now in a single module:

```python
# Import from consolidated module
from saaaaaa.core.orchestrator.arg_router import ArgRouter, ExtendedArgRouter

# Both classes available from same import
# ExtendedArgRouter is recommended for new code
router = ExtendedArgRouter(class_registry)

# ArgRouter base class still available for compatibility
base_router = ArgRouter(class_registry)
```

### Handling Validation Errors

If you encounter `ArgumentValidationError` after the migration, this indicates your code was passing unexpected parameters that were previously silently dropped.

**Action**: Fix the calling code to match the method signature:

```python
# Before: Passing unexpected parameter
executor.execute("MyClass", "my_method", content="data", unexpected_param="value")
# Error: ArgumentValidationError: unexpected=['unexpected_param']

# After: Remove unexpected parameter
executor.execute("MyClass", "my_method", content="data")
# Success: Parameter contract enforced correctly
```

## For Library Developers

### Using ExtendedArgRouter Directly

```python
from saaaaaa.core.orchestrator.arg_router_extended import ExtendedArgRouter

# Create router with class registry
router = ExtendedArgRouter(class_registry)

# Route method calls
args, kwargs = router.route("ClassName", "method_name", payload)

# Access metrics
metrics = router.get_metrics()
print(f"Total routes: {metrics['total_routes']}")
print(f"Silent drops prevented: {metrics['silent_drops_prevented']}")
```

### Accessing Metrics from MethodExecutor

```python
from saaaaaa.core.orchestrator.core import MethodExecutor

executor = MethodExecutor()

# Execute some methods...
executor.execute("MyClass", "my_method", arg1="value")

# Get routing metrics
metrics = executor.get_routing_metrics()
print(f"Special route hit rate: {metrics['special_route_hit_rate']:.2%}")
```

## Monitoring and CI Integration

### Running Metrics Report

The repository includes a metrics reporting script:

```bash
# Generate metrics report (informational)
python scripts/report_routing_metrics.py metrics.json

# Fail CI if silent drops detected (strict mode)
python scripts/report_routing_metrics.py metrics.json --fail-on-silent-drops
```

### CI Workflow

A GitHub Actions workflow is available at `.github/workflows/routing-metrics.yml`:

- Runs on every PR and push to main/develop
- Reports routing metrics to GitHub Actions summary
- Can be configured for strict validation (fails on silent drops)

### Interpreting Metrics

| Metric | Description | Good Target |
|--------|-------------|-------------|
| `total_routes` | Total method calls routed | N/A (informational) |
| `special_routes_hit` | Calls using special routes | Increases over time |
| `special_route_hit_rate` | % of calls using special routes | > 20% |
| `validation_errors` | Failed validations | 0 |
| `silent_drops_prevented` | Contract violations caught | 0 |
| `error_rate` | % of failed validations | < 1% |

## Special Routes

ExtendedArgRouter includes 30+ pre-defined special routes for high-traffic methods:

### Text Analysis Methods
- `_extract_quantitative_claims`
- `_parse_number`
- `_determine_semantic_role`
- `_extract_indicators`
- `_extract_entities`
- `_parse_citation`

### Pattern Compilation Methods
- `_compile_pattern_registry`
- `_compile_regex_patterns`
- `_compile_indicator_patterns`
- `_compile_validation_rules`

### Analysis Methods
- `_analyze_temporal_coherence`
- `_analyze_source_reliability`
- `_analyze_coherence_score`
- `_analyze_stakeholder_impact`

### Validation Methods
- `_validate_evidence_chain`
- `_validate_numerical_consistency`
- `_validate_threshold_compliance`
- `_validate_governance_structure`

### Calculation Methods
- `_calculate_confidence_score`
- `_calculate_bayesian_update`
- `_calculate_evidence_weight`
- `_calculate_alignment_score`

And more! See `src/saaaaaa/core/orchestrator/arg_router_extended.py` for the complete list.

## Adding New Special Routes

To add a new special route to ExtendedArgRouter:

1. Open `src/saaaaaa/core/orchestrator/arg_router_extended.py`
2. Add entry to `_build_special_routes()` method:

```python
"_your_method_name": {
    "required_args": ["param1", "param2"],
    "optional_args": ["optional_param"],
    "accepts_kwargs": True,  # or False
    "description": "Human-readable description",
}
```

3. Add test case in `tests/test_arg_router_extended.py`

## Troubleshooting

### Issue: Tests fail with ArgumentValidationError

**Cause**: Code is passing unexpected parameters that were previously silently dropped.

**Solution**: Review the error message to identify unexpected parameters, then update calling code to match the method signature.

### Issue: DeprecationWarning in tests

**Cause**: Code is still using deprecated `ArgRouter` class.

**Solution**: Update imports to use `ExtendedArgRouter` instead.

### Issue: Metrics show high error rate

**Cause**: Multiple contract violations throughout the codebase.

**Solution**: 
1. Review `silent_drops_prevented` metric to identify problem areas
2. Fix calling code to match method signatures
3. Add tests to prevent regression

## Timeline

### Current (Phases 1-3): Deprecation Period
- Duration: 1 sprint (2-4 weeks)
- ExtendedArgRouter active in MethodExecutor
- Deprecation warnings guide developers
- Metrics collected for analysis

### Next (Phase 4): Final Removal
- After deprecation period completes
- Delete `arg_router.py`
- Rename `arg_router_extended.py` to `arg_router.py`
- Update documentation

## Support

For questions or issues with the migration:

1. Check this guide first
2. Review the roadmap in the PR description
3. Check metrics to understand routing behavior
4. Open an issue with:
   - Error message or deprecation warning
   - Code snippet showing the problem
   - Routing metrics if available

## Additional Resources

- **ExtendedArgRouter source**: `src/saaaaaa/core/orchestrator/arg_router_extended.py`
- **Tests**: `tests/test_arg_router_extended.py`
- **Metrics script**: `scripts/report_routing_metrics.py`
- **CI workflow**: `.github/workflows/routing-metrics.yml`
- **Original roadmap**: See PR description
