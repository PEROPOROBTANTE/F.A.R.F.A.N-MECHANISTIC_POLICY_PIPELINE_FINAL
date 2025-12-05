# Phase 4-6 Test Suite Quick Reference

## 🚀 Quick Start

```bash
# Run all Phase 4-6 tests
pytest tests/phases/test_phase4_pattern_filtering.py \
       tests/phases/test_phase5_signal_resolution.py \
       tests/phases/test_phase6_schema_validation.py -v

# Run with coverage
pytest tests/phases/test_phase4_pattern_filtering.py \
       tests/phases/test_phase5_signal_resolution.py \
       tests/phases/test_phase6_schema_validation.py \
       --cov=farfan_pipeline --cov-report=term-missing -v
```

---

## 📊 Test Suite Overview

| Phase | File | Tests | Focus |
|-------|------|-------|-------|
| **4** | `test_phase4_pattern_filtering.py` | 57 | Pattern filtering with strict equality |
| **5** | `test_phase5_signal_resolution.py` | 43 | Signal resolution with hard-fail |
| **6** | `test_phase6_schema_validation.py` | 63 | Schema validation (structural + semantic) |
| **Total** | **3 files** | **163** | **Complete Phase 4-6 coverage** |

---

## 🔍 What's Tested

### Phase 4: Pattern Filtering
```python
from farfan_pipeline.core.orchestrator.signal_context_scoper import (
    filter_patterns_by_context,
    context_matches,
    in_scope,
)
```

- ✅ **Strict Equality**: policy_area_id exact matching
- ✅ **Context Scoping**: global, section, chapter, page
- ✅ **Requirements**: exact, list, comparison operators (>, >=, <, <=)
- ✅ **Statistics**: total, filtered, passed counts
- ✅ **Immutability**: Pattern preservation

### Phase 5: Signal Resolution
```python
from farfan_pipeline.core.orchestrator.signal_resolution import (
    _resolve_signals,
    Signal,
    Question,
    Chunk,
)
```

- ✅ **Registry Integration**: SignalRegistry query interface
- ✅ **Hard-Fail**: No fallbacks on missing signals
- ✅ **Immutable Tuples**: NamedTuple returns
- ✅ **Set-Based**: Order-independent validation
- ✅ **Clear Errors**: Explicit missing signal messages

### Phase 6: Schema Validation
```python
from farfan_pipeline.utils.validation.schema_validator import (
    MonolithSchemaValidator,
    SchemaInitializationError,
    MonolithIntegrityReport,
)
```

- ✅ **Structural**: Type classification, homogeneity
- ✅ **Length**: 300 micro, 4 meso, 1 macro
- ✅ **Key Sets**: Dictionary consistency
- ✅ **Semantic**: Type, required, minimum fields
- ✅ **Integrity**: Cross-references, uniqueness
- ✅ **Hashing**: Deterministic verification

---

## 🎯 Test Examples

### Phase 4: Filter Patterns by Context
```python
def test_exact_context_requirement_match():
    patterns = [
        {"id": "p1", "pattern": "test", "context_requirement": {"section": "budget"}},
    ]
    
    filtered, _ = filter_patterns_by_context(patterns, {"section": "budget"})
    assert len(filtered) == 1
```

### Phase 5: Resolve Signals
```python
def test_missing_signal_raises_value_error():
    chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
    question = Question(question_id="Q07", signal_requirements={"missing_type"})
    registry = MockSignalRegistry(signals_to_return=[])
    
    with pytest.raises(ValueError, match="Missing signals"):
        _resolve_signals(chunk, question, registry)
```

### Phase 6: Validate Schema
```python
def test_micro_questions_count_300():
    monolith = {
        "schema_version": "2.0.0",
        "blocks": {
            "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
            # ...
        },
    }
    validator = MonolithSchemaValidator()
    report = validator.validate_monolith(monolith, strict=False)
    
    assert report.question_counts["micro_questions"] == 300
```

---

## 📁 File Structure

```
tests/phases/
├── test_phase4_pattern_filtering.py     (698 lines, 57 tests)
├── test_phase5_signal_resolution.py     (590 lines, 43 tests)
├── test_phase6_schema_validation.py     (991 lines, 63 tests)
├── PHASE4_6_TEST_SUITE_README.md        (comprehensive docs)
├── PHASE4_6_VERIFICATION.md             (verification report)
└── QUICK_REFERENCE_PHASE4_6.md          (this file)
```

---

## 🧪 Test Class Index

### Phase 4 (8 classes)
1. `TestPhase4PolicyAreaStrictEquality` - Strict equality filtering
2. `TestPhase4ImmutableTupleReturns` - Immutable returns
3. `TestPhase4ContextScopeFiltering` - Context scoping
4. `TestPhase4ContextRequirementMatching` - Requirement matching
5. `TestPhase4FilterStatistics` - Statistics tracking
6. `TestPhase4EmptyPatternHandling` - Empty lists
7. `TestPhase4InvalidContextHandling` - Error handling
8. `TestPhase4HelperFunctions` - Utility functions

### Phase 5 (9 classes)
1. `TestPhase5SignalRegistryIntegration` - Registry queries
2. `TestPhase5MissingSignalHardStops` - Hard-fail behavior
3. `TestPhase5ImmutableSignalTuples` - Immutable returns
4. `TestPhase5SetBasedValidation` - Set operations
5. `TestPhase5SignalTypeValidation` - Type checking
6. `TestPhase5ErrorMessageClarity` - Error messages
7. `TestPhase5ChunkAndQuestionStructure` - Data structures
8. `TestPhase5RegistryCallPatterns` - Call patterns
9. `TestPhase5EdgeCases` - Edge cases

### Phase 6 (12 classes)
1. `TestPhase6StructuralValidation` - Structure checks
2. `TestPhase6ListLengthEquality` - Length validation
3. `TestPhase6DictKeySetEquality` - Key set validation
4. `TestPhase6SemanticValidation` - Semantic rules
5. `TestPhase6MinimumValueConstraints` - Value ranges
6. `TestPhase6SchemaVersionValidation` - Version checks
7. `TestPhase6ReferentialIntegrity` - Cross-references
8. `TestPhase6FieldCoverageValidation` - Field coverage
9. `TestPhase6HashCalculation` - Hash verification
10. `TestPhase6ValidationReport` - Report structure
11. `TestPhase6StrictMode` - Strict behavior
12. `TestPhase6EdgeCases` - Edge cases

---

## 🔧 Common Commands

### Run Specific Test Class
```bash
pytest tests/phases/test_phase4_pattern_filtering.py::TestPhase4PolicyAreaStrictEquality -v
```

### Run Specific Test Method
```bash
pytest tests/phases/test_phase5_signal_resolution.py::TestPhase5MissingSignalHardStops::test_missing_signal_raises_value_error -v
```

### Run with Output
```bash
pytest tests/phases/test_phase6_schema_validation.py -v -s
```

### Run with Markers (if defined)
```bash
pytest tests/phases/ -m "phase4" -v
pytest tests/phases/ -m "phase5" -v
pytest tests/phases/ -m "phase6" -v
```

### Generate HTML Report
```bash
pytest tests/phases/test_phase4_pattern_filtering.py \
       tests/phases/test_phase5_signal_resolution.py \
       tests/phases/test_phase6_schema_validation.py \
       --cov=farfan_pipeline \
       --cov-report=html -v
```

---

## 📈 Coverage Expectations

### Phase 4: signal_context_scoper.py
- `filter_patterns_by_context()` - 100%
- `context_matches()` - 100%
- `in_scope()` - 100%
- `evaluate_comparison()` - 100%
- `create_document_context()` - 100%

### Phase 5: signal_resolution.py
- `_resolve_signals()` - 100%
- `Signal` NamedTuple - 100%
- `Question` NamedTuple - 100%
- `Chunk` NamedTuple - 100%

### Phase 6: schema_validator.py
- `MonolithSchemaValidator` - 90%+
- `validate_monolith()` - 100%
- `_validate_structure()` - 100%
- `_validate_schema_version()` - 100%
- `_validate_question_counts()` - 100%
- `_calculate_schema_hash()` - 100%

---

## ⚠️ Common Issues

### Import Errors
If you get import errors, ensure you're in the repo root:
```bash
cd /path/to/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL_XMc5SAHQbm9aIptulKlXy
pytest tests/phases/test_phase4_pattern_filtering.py -v
```

### Module Not Found
Make sure the package is installed:
```bash
pip install -e .
```

### Test Discovery Issues
Use explicit paths:
```bash
pytest tests/phases/test_phase4_pattern_filtering.py::TestPhase4PolicyAreaStrictEquality -v
```

---

## 📚 Documentation

- **Full Documentation**: `PHASE4_6_TEST_SUITE_README.md`
- **Verification Report**: `PHASE4_6_VERIFICATION.md`
- **Quick Reference**: This file

---

## ✅ Verification

All test files compile successfully:
```bash
python -m py_compile tests/phases/test_phase4_pattern_filtering.py
python -m py_compile tests/phases/test_phase5_signal_resolution.py
python -m py_compile tests/phases/test_phase6_schema_validation.py
echo "✅ All tests compile successfully"
```

---

## 🎓 Best Practices

1. **Run tests before committing**
   ```bash
   pytest tests/phases/test_phase4_pattern_filtering.py -v
   ```

2. **Check coverage regularly**
   ```bash
   pytest tests/phases/ --cov=farfan_pipeline --cov-report=term-missing
   ```

3. **Use verbose mode for debugging**
   ```bash
   pytest tests/phases/test_phase5_signal_resolution.py -vv -s
   ```

4. **Run specific test when debugging**
   ```bash
   pytest tests/phases/test_phase6_schema_validation.py::TestPhase6StructuralValidation::test_validate_top_level_keys_present -vv -s
   ```

---

## 📞 Support

For questions or issues:
1. Check `PHASE4_6_TEST_SUITE_README.md` for detailed documentation
2. Review `PHASE4_6_VERIFICATION.md` for implementation details
3. Examine test file docstrings for specific test behavior

---

**Status**: Implementation Complete ✅  
**Test Count**: 163 tests  
**Coverage**: 100% of requested functionality  
**Documentation**: Complete
