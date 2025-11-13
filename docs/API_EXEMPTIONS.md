# Public API Exemptions Registry

This document tracks all public API functions that are exempt from the standard `**kwargs` prohibition.

## Exemption Categories

### 1. Backward Compatibility Wrappers

Functions that maintain compatibility with legacy APIs while transitioning to new explicit interfaces.

| Function | Module | Reason | Deprecated Version | Removal Version | Migration Path |
|----------|--------|--------|-------------------|-----------------|----------------|
| `legacy_score()` | `scoring.py` | Wrapper for old scoring API | v3.0.0 | v4.0.0 | Use `apply_scoring()` with explicit parameters |

**Requirements:**
- Must emit `DeprecationWarning`
- Must document deprecation and removal versions
- Must provide migration path in docstring

### 2. Extensible Plugin Systems

Functions that accept plugin-provided metadata or configuration.

| Function | Module | Reason | Validation | Allowed Keys |
|----------|--------|--------|------------|--------------|
| `register_validator()` | `validation_engine.py` | Plugin metadata | Logs unknown keys | author, version, description |

**Requirements:**
- Must validate or log unknown keys
- Must document allowed metadata keys
- Must use typed `**kwargs` (not `Any`)

### 3. Pass-Through Context

Framework functions that pass context to callbacks or pipeline steps.

| Function | Module | Reason | Context Type | Validation |
|----------|--------|--------|--------------|------------|
| `execute_pipeline()` | `orchestrator.py` | Pipeline execution context | Dict[str, Any] | Validated by individual steps |

**Requirements:**
- Must document that validation happens downstream
- Must specify context type explicitly
- Must not silently ignore invalid context

## Exemption Request Process

To request an exemption for a new function:

1. **Document the Rationale**
   - Explain why explicit parameters are not feasible
   - Demonstrate that the use case fits one of the three categories above
   - Show that type safety is maintained through other means

2. **Update Function Documentation**
   ```python
   def my_function(required_param: str, **plugin_metadata: str) -> Result:
       """
       Brief description.
       
       Args:
           required_param: Description of required parameter
           **plugin_metadata: Optional plugin metadata (author, version, description).
                             All values must be strings. Unknown keys are logged but
                             do not cause failures.
       
       API Exemption: Category 2 (Extensible Plugin System)
       Rationale: Plugins may provide additional metadata that the core system
                 doesn't need to validate.
       """
   ```

3. **Add to This Registry**
   - Add entry to appropriate category table
   - Include validation approach
   - Specify any constraints (allowed keys, types)

4. **Add Test Coverage**
   - Test that valid usage works correctly
   - Test that invalid usage is handled appropriately (logged/rejected)
   - Test migration path for backward compatibility exemptions

5. **Update Type Checking**
   - Ensure mypy `--strict` passes
   - Use typed `**kwargs` annotation (e.g., `**kwargs: str`)
   - Add type ignore comment only if absolutely necessary

## Review Checklist

Before approving an exemption request:

- [ ] Function fits one of the three allowed categories
- [ ] Docstring includes explicit rationale and "API Exemption" tag
- [ ] Function is added to this registry
- [ ] Type annotation uses typed `**kwargs` (not `Any`)
- [ ] Unknown/invalid kwargs are validated or logged
- [ ] Test coverage includes error cases
- [ ] Migration path documented (if backward compatibility)
- [ ] Removal timeline specified (if backward compatibility)

## Historical Exemptions (Removed)

Track exemptions that have been removed after migration:

| Function | Module | Removed Version | Reason for Removal |
|----------|--------|----------------|-------------------|
| *(None yet)* | - | - | - |

## Statistics

- Total active exemptions: 0
- Backward compatibility: 0
- Plugin systems: 0
- Pass-through context: 0
- Total removed: 0

*Last updated: 2024-10-30*
