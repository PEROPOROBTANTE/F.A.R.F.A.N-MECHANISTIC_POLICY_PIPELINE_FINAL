# Type Safety & Contract Hardening Guide

## Overview

This guide documents the comprehensive type safety and contract validation improvements implemented to eliminate common runtime errors:
- `unexpected keyword argument 'pdf_path'/'text'`
- `missing 1 required positional argument`
- `'str' object has no attribute 'text'`
- `'bool' object is not iterable`
- `unhashable type: 'dict'`

## Architecture

### Core Components

1. **contracts.py** - Frozen data shapes and protocols
2. **adapters.py** - Centralized migration shims
3. **schema_monitor.py** - Production payload monitoring
4. **pyproject.toml** - Strict type checking configuration
5. **CI workflows** - Automated enforcement

## Quick Start

### Using Contracts

```python
from contracts import (
    TextDocument,
    AnalysisInputV1,
    validate_contract,
    ensure_iterable_not_string,
)

# Create value objects to prevent type confusion
doc = TextDocument(
    text="Policy document text",
    document_id="doc_123",
    metadata={"source": "municipal_plan"},
)

# Use TypedDict for API contracts
input_data: AnalysisInputV1 = {
    "text": doc.text,
    "document_id": doc.document_id,
}

# Runtime validation at boundaries
validate_contract(
    doc.text,
    str,
    parameter="text",
    producer="document_loader",
    consumer="analyzer",
)
```

### Keyword-Only Parameters

All public APIs now use keyword-only parameters:

```python
# Old way (error-prone)
loader.load_pdf("/path/to/file.pdf")  # ❌ Not allowed

# New way (explicit)
loader.load_pdf(pdf_path="/path/to/file.pdf")  # ✅ Clear intent
```

### Using Adapters

```python
from adapters import (
    adapt_analysis_input_kwargs,
    migrate_pdf_path_param,
    handle_renamed_param,
)

# Adapt legacy kwargs to typed contracts
def legacy_api(**kwargs):
    # Handle parameter renames with deprecation warnings
    handle_renamed_param(kwargs, "raw_text", "text")
    
    # Migrate to keyword-only
    migrate_pdf_path_param(kwargs)
    
    # Validate and convert
    typed_input = adapt_analysis_input_kwargs(kwargs)
    
    # Call new typed API
    return new_api(**typed_input)
```

### Schema Monitoring

```python
from schema_monitor import SchemaDriftDetector

# Initialize detector (samples 5% of payloads)
detector = SchemaDriftDetector(sample_rate=0.05)

# In your API/pipeline
if detector.should_sample():
    detector.record_payload(
        data,
        source="api_input",
    )

# Check for drift
alerts = detector.get_alerts()
for alert in alerts:
    if alert["type"] == "MISSING_KEYS":
        logger.critical(f"Schema drift detected: {alert}")
```

## Migration Guide

### Phase 1: Add Type Hints (Non-Breaking)

1. Add type hints to function signatures
2. Use TypedDict for dict parameters
3. Add Protocol for pluggable components

```python
# Before
def analyze(text, metadata):
    ...

# After
from contracts import AnalysisInputV1, AnalysisOutputV1

def analyze(
    *,
    text: str,
    metadata: Mapping[str, Any],
) -> AnalysisOutputV1:
    ...
```

### Phase 2: Add Runtime Validation (Semi-Breaking)

1. Add validation at ingress/egress points
2. Fail fast with structured error messages
3. Log contract mismatches

```python
from contracts import validate_contract

def analyze(*, text: str, metadata: Mapping[str, Any]):
    # Validate at ingress
    validate_contract(
        text,
        str,
        parameter="text",
        producer="caller",
        consumer="analyze",
    )
    
    # Your logic here
    ...
```

### Phase 3: Make Keyword-Only (Breaking)

1. Add `*` to force keyword-only parameters
2. Provide adapters for backwards compatibility
3. Emit deprecation warnings for old usage

```python
# Migration adapter
def load_pdf_compat(pdf_path=None, **kwargs):
    """Backwards-compatible wrapper (deprecated)."""
    warnings.warn(
        "Positional arguments deprecated, use keyword-only",
        DeprecationWarning,
    )
    return load_pdf(pdf_path=pdf_path, **kwargs)
```

### Phase 4: Remove Adapters (Breaking)

After one release cycle:
1. Remove deprecated parameter names
2. Remove compatibility shims
3. Update CHANGELOG.md

## Common Patterns

### Prevent `.text` on Strings

```python
from contracts import TextDocument

# ❌ Problem: passing plain str where structured object expected
def process(text):
    return text.text  # AttributeError if text is str!

# ✅ Solution: use value object
def process(doc: TextDocument):
    return doc.text  # Type system ensures doc has .text
```

### Prevent `'bool' object is not iterable`

```python
from contracts import ensure_iterable_not_string

# ❌ Problem: trying to iterate non-iterable
for item in flag:  # TypeError if flag is bool!
    ...

# ✅ Solution: validate before iteration
ensure_iterable_not_string(
    items,
    parameter="items",
    producer="caller",
    consumer="processor",
)
for item in items:
    ...
```

### Prevent `unhashable type: 'dict'`

```python
from adapters import adapt_for_set_membership

# ❌ Problem: adding unhashable to set
my_set.add({"key": "value"})  # TypeError!

# ✅ Solution: convert to hashable
hashable = adapt_for_set_membership(
    {"key": "value"},
    parameter="dict_value",
)
my_set.add(hashable)  # Works!
```

### Prevent `unexpected keyword argument`

```python
# ❌ Problem: parameter name mismatch
def old_api(raw_text):
    ...

old_api(text="hello")  # TypeError: unexpected keyword argument 'text'

# ✅ Solution: use adapter with deprecation warning
from adapters import handle_renamed_param

def new_api(**kwargs):
    handle_renamed_param(kwargs, "raw_text", "text")
    # Now kwargs["text"] exists
    ...
```

## Testing

### Contract Tests

```python
import pytest
from contracts import DocumentLoaderProtocol

@pytest.mark.contract
def test_document_loader_signature():
    """Verify load_pdf uses keyword-only params."""
    import inspect
    sig = inspect.signature(DocumentLoaderProtocol.load_pdf)
    
    # Check pdf_path is keyword-only
    pdf_path_param = sig.parameters["pdf_path"]
    assert pdf_path_param.kind == inspect.Parameter.KEYWORD_ONLY
```

### Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(
    text=st.text(min_size=1),
    metadata=st.dictionaries(st.text(), st.text()),
)
def test_text_document_roundtrip(text, metadata):
    """TextDocument preserves all input data."""
    doc = TextDocument(text=text, document_id="test", metadata=metadata)
    assert doc.text == text
    assert dict(doc.metadata) == metadata
```

## CI Integration

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        args: [--strict]
```

### GitHub Actions

```yaml
# .github/workflows/type-safety.yml
jobs:
  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      
      - name: Run MyPy
        run: mypy --strict contracts.py orchestrator.py
      
      - name: Run contract tests
        run: pytest tests/test_contracts.py -m contract
```

## Error Messages

All validation errors follow a structured format:

```
ERR_CONTRACT_MISMATCH[
  stage=FINANCIAL_ANALYSIS,
  fn=_extract_from_budget_table,
  param='tables',
  got=list,
  expected=Mapping[str, Any],
  producer=PDETMunicipalPlanAnalyzer._deduplicate_tables,
  consumer=_extract_from_budget_table
]
```

This makes debugging and monitoring easy:
- Grep logs for `ERR_CONTRACT_MISMATCH`
- Aggregate by stage/function
- Track which producer/consumer pairs fail

## Best Practices

### 1. Freeze Your Data Shapes

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Config:
    chunk_size: int
    overlap: int
```

### 2. Keyword-Only Public APIs

```python
def public_api(
    *,  # Everything after this is keyword-only
    required: str,
    optional: Optional[int] = None,
) -> Result:
    ...
```

### 3. Validate at Boundaries

```python
def api_endpoint(**kwargs):
    # Ingress validation
    validate_mapping_keys(
        kwargs,
        ["text", "document_id"],
        producer="http_client",
        consumer="api_endpoint",
    )
    
    # Process
    result = process(**kwargs)
    
    # Egress validation
    validate_contract(
        result,
        AnalysisOutputV1,
        parameter="result",
        producer="api_endpoint",
        consumer="http_response",
    )
    
    return result
```

### 4. Version Your DTOs

```python
class DocumentMetadataV1(TypedDict):
    """Version 1 of document metadata contract."""
    file_path: str
    file_name: str

class DocumentMetadataV2(TypedDict):
    """Version 2 - added hash field."""
    file_path: str
    file_name: str
    file_hash: str  # New field

# Adapter for migration period
def adapt_v1_to_v2(v1: DocumentMetadataV1) -> DocumentMetadataV2:
    return {
        **v1,
        "file_hash": compute_hash(v1["file_path"]),
    }
```

### 5. Use Sentinels for Optional Params

```python
from contracts import MISSING

def api(
    required: str,
    optional: str | _MissingSentinel = MISSING,
) -> None:
    if optional is MISSING:
        # Truly not provided (different from None)
        optional = get_default()
```

## Metrics & Monitoring

### Key Metrics to Track

1. **Contract Mismatch Rate**: `grep ERR_CONTRACT_MISMATCH logs | wc -l`
2. **Schema Drift Events**: `detector.get_alerts() | length`
3. **Type Check Failures**: CI builds failing on type checks
4. **Deprecation Warning Count**: `grep DeprecationWarning logs`

### Dashboards

```python
from schema_monitor import get_detector

# Get metrics for monitoring
metrics = get_detector().get_metrics()
# {
#   "sources": ["api_input", "document_loader"],
#   "total_samples": 1234,
#   "sources_with_drift": 1,
# }
```

## Rollout Plan

### Week 1: Foundation
- ✅ Add `contracts.py`, `adapters.py`, `schema_monitor.py`
- ✅ Configure `pyproject.toml` with strict settings
- ✅ Add CI workflows

### Week 2: Core Modules
- ✅ Update `orchestrator.py` to keyword-only
- ✅ Update `document_ingestion.py` to keyword-only
- ✅ Update `embedding_policy.py` with validation
- ✅ Add adapter functions for backwards compatibility

### Week 3: Tests & Documentation
- ✅ Add contract tests
- ✅ Add property-based tests
- ✅ Document migration guide
- ⏳ Run full test suite

### Week 4: Expand Coverage
- ⏳ Update `policy_processor.py`
- ⏳ Update remaining modules
- ⏳ Enable strict mode in CI (blocking)

### Week 5: Cleanup
- ⏳ Remove old adapters (after deprecation period)
- ⏳ Update CHANGELOG.md
- ⏳ Final validation

## Troubleshooting

### Q: Type checker complains about `Any` usage

**A:** Replace `Any` with specific types or use Protocol:

```python
# Instead of
def process(data: Any) -> Any:
    ...

# Use
from contracts import TextProcessorProtocol

def process(data: TextProcessorProtocol) -> ProcessedText:
    ...
```

### Q: Getting "unexpected keyword argument" in tests

**A:** Update test calls to use keyword arguments:

```python
# Old
result = loader.load_pdf("/path/to/file.pdf")

# New
result = loader.load_pdf(pdf_path="/path/to/file.pdf")
```

### Q: Schema drift alerts firing constantly

**A:** Check if baseline schema is outdated:

```python
# Update baseline
detector.save_baseline(Path("baseline_schema.json"))
```

### Q: Type checks too slow in CI

**A:** Use incremental type checking and cache:

```yaml
- name: Cache mypy
  uses: actions/cache@v3
  with:
    path: .mypy_cache
    key: mypy-${{ hashFiles('**/*.py') }}
```

## References

- **Problem Statement**: Original requirements document
- **contracts.py**: TypedDict and Protocol definitions
- **adapters.py**: Migration utilities
- **schema_monitor.py**: Runtime monitoring
- **pyproject.toml**: Type checker configuration
- **tests/test_contracts.py**: Contract test examples
- **tests/test_property_based.py**: Property-based test examples

## Support

For questions or issues:
1. Check this guide first
2. Review contract test examples
3. Consult type checker documentation
4. File an issue with ERR_CONTRACT_MISMATCH message

---

**Last Updated**: 2025-10-30  
**Version**: 1.0.0  
**Status**: Active Development
