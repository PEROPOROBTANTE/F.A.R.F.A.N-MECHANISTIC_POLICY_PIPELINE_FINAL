# Signature Validation and Interface Governance System

## Overview

This system implements automated signature consistency auditing, runtime validation, and interface governance to prevent function signature mismatches in the SAAAAAA codebase.

## Problem Statement

Function signature mismatches occur when:
1. Functions are called with unexpected keyword arguments
2. Functions are called with missing required positional arguments  
3. Signatures change without corresponding updates across the dependency graph

These issues indicate a breakdown in type discipline, dependency synchronization, and integration governance.

## Solution Components

### 1. Signature Registry (`signature_validator.py`)

The signature registry maintains a versioned database of all function signatures in the project:

- **Automatic registration**: Functions can be decorated with `@validate_signature()` to automatically register their signatures
- **Version tracking**: Signature changes are detected and tracked over time
- **Hash-based detection**: Uses SHA-256 hashes of signature strings to detect changes

```python
from signature_validator import validate_signature

@validate_signature(enforce=True, track=True)
def my_function(arg1: str, arg2: int) -> bool:
    return True
```

### 2. Runtime Validation

Functions decorated with `@validate_signature()` perform runtime parameter validation:

- Validates that all required parameters are provided
- Detects unexpected keyword arguments
- Logs warnings or raises TypeError based on `enforce` flag
- Maintains backward compatibility through defensive programming

### 3. Static Signature Auditor

The `SignatureAuditor` class performs static analysis of Python code to detect signature mismatches:

```bash
python signature_validator.py audit --project-root . --output data/signature_audit_report.json
```

This generates a report of:
- Function definitions and their signatures
- Function calls and their arguments
- Detected mismatches between definitions and call sites

### 4. CI/CD Integration (`signature_ci_check.py`)

Automated signature checking for CI/CD pipelines:

```bash
python signature_ci_check.py --project-root . --fail-on-breaking
```

Features:
- Detects signature changes between commits
- Identifies breaking vs non-breaking changes
- Generates diff reports for code review
- Exits with non-zero code on policy violations

## Implementation Strategy

### Defensive Function Signatures

The following key functions have been updated with defensive signatures:

#### 1. `PDETMunicipalPlanAnalyzer._is_likely_header()`

**File**: `financiero_viabilidad_tablas.py`

**Issue**: Function was being called with unexpected `pdf_path` keyword argument

**Solution**: Added `**kwargs` to accept and ignore unexpected arguments with logging:

```python
def _is_likely_header(self, row: pd.Series, **kwargs) -> bool:
    if kwargs:
        logger.warning(f"Unexpected kwargs: {list(kwargs.keys())}")
    # ... rest of implementation
```

#### 2. `IndustrialPolicyProcessor._analyze_causal_dimensions()`

**File**: `policy_processor.py`

**Issue**: Function was being called without required `sentences` argument

**Solution**: Made `sentences` parameter optional with automatic fallback:

```python
def _analyze_causal_dimensions(
    self, text: str, sentences: Optional[List[str]] = None
) -> Dict[str, Any]:
    if sentences is None:
        logger.warning("Missing 'sentences' parameter, auto-extracting")
        sentences = self.text_processor.segment_into_sentences(text)
    # ... rest of implementation
```

#### 3. `BayesianMechanismInference.__init__()`

**File**: `derek_beach.py`

**Issue**: Function was being called with unexpected `causal_hierarchy` keyword argument

**Solution**: Added `**kwargs` to accept and ignore unexpected arguments with logging:

```python
def __init__(self, config: ConfigLoader, nlp_model: spacy.Language, **kwargs) -> None:
    if kwargs:
        logger.warning(f"Unexpected kwargs: {list(kwargs.keys())}")
    # ... rest of implementation
```

## Usage Guide

### For Developers

1. **Decorate new functions** with signature validation:
   ```python
   from signature_validator import validate_signature
   
   @validate_signature(enforce=True, track=True)
   def your_new_function(param1: str, param2: int) -> dict:
       pass
   ```

2. **Check for signature changes** before committing:
   ```bash
   python signature_ci_check.py --fail-on-changes
   ```

3. **Review audit reports** for existing code:
   ```bash
   python signature_validator.py audit --project-root .
   ```

### For CI/CD Pipelines

Add to your CI workflow (`.github/workflows/ci.yml`):

```yaml
- name: Check Function Signatures
  run: |
    python signature_ci_check.py \
      --project-root . \
      --fail-on-breaking \
      --output artifacts/signature_diff.json
  
- name: Upload Signature Report
  uses: actions/upload-artifact@v2
  with:
    name: signature-report
    path: artifacts/signature_diff.json
```

### For Code Reviews

When reviewing PRs that modify function signatures:

1. Check the signature diff report in CI artifacts
2. Verify that all call sites have been updated
3. Ensure backward compatibility is maintained or breaking changes are documented
4. Review the impact on dependent modules

## Preventative Measures

### 1. Type Hints

All functions should use comprehensive type hints:

```python
from typing import List, Dict, Optional, Any

def process_data(
    text: str,
    options: Optional[Dict[str, Any]] = None
) -> List[str]:
    pass
```

### 2. Mypy Integration

Run static type checking:

```bash
mypy --strict src/
```

### 3. Signature Tests

Add signature regression tests:

```python
import inspect

def test_function_signature_unchanged():
    sig = inspect.signature(my_function)
    expected = "(arg1: str, arg2: int) -> bool"
    assert str(sig) == expected
```

### 4. Documentation

Document signature changes in:
- Commit messages
- CHANGELOG.md
- Function docstrings
- Migration guides (for breaking changes)

## Monitoring and Alerts

### Signature Change Metrics

The system tracks:
- Total number of registered signatures
- Number of signature changes per commit
- Ratio of breaking to non-breaking changes
- Frequency of signature violations

### Alert Thresholds

Configure alerts for:
- More than 5 breaking changes in a single commit
- Signature mismatches detected in production code
- Functions called with wrong signatures (runtime)

## Best Practices

1. **Always use type hints** for function parameters and return types
2. **Use `**kwargs` defensively** only when backward compatibility is critical
3. **Log warnings** when unexpected arguments are received
4. **Run signature checks** before committing code
5. **Review signature reports** in code reviews
6. **Document breaking changes** in release notes
7. **Maintain backward compatibility** when possible
8. **Use adapter pattern** for major signature changes

## Integration with Existing Tools

### Mypy

Signature validation complements mypy:
- Mypy: Static type checking at build time
- Signature validator: Runtime checking and CI integration

### Pytest

Add signature validation to test fixtures:

```python
@pytest.fixture(autouse=True)
def validate_all_signatures():
    from signature_validator import _signature_registry
    _signature_registry.save()
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: signature-check
        name: Validate Function Signatures
        entry: python signature_ci_check.py --fail-on-breaking
        language: python
        pass_filenames: false
```

## Troubleshooting

### Common Issues

**Issue**: Function signature changed but CI didn't detect it
- **Solution**: Ensure function is decorated with `@validate_signature(track=True)`

**Issue**: Too many false positives in audit
- **Solution**: Tune the static analyzer or add exceptions for generated code

**Issue**: Breaking change not detected
- **Solution**: Review the `_is_breaking_change()` logic and add more cases

## Future Enhancements

1. **LLM-assisted semantic diffing** to predict downstream breakages
2. **Dependency graph visualization** showing affected call sites
3. **Automatic migration scripts** for common signature changes
4. **Integration with IDE** for real-time validation
5. **Machine learning** to predict risky signature changes

## References

- Problem Statement: Function Signature Mismatch Analysis
- Strategic Mitigation Plan: Interface Governance Framework
- Liskov Substitution Principle: https://en.wikipedia.org/wiki/Liskov_substitution_principle
- Python Signature Object: https://docs.python.org/3/library/inspect.html#inspect.Signature

## Support

For questions or issues:
- File an issue in the repository
- Contact the Signature Governance Team
- Review the test suite in `tests/test_signature_validator.py`
