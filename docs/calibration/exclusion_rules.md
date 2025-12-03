# Exclusion Rules for Intrinsic Calibration

**Version**: 1.0.0  
**Last Updated**: 2025-12-03  
**Source**: `intrinsic_calibration_rubric.json` § exclusion_criteria

---

## Purpose

This document defines **exclusion patterns** for methods that should NOT be calibrated by the intrinsic calibration system. These methods are non-analytical, non-semantic, or pure utility functions that do not affect the quality or correctness of analytical results.

---

## Exclusion Categories

### 1. Magic Methods

Methods that implement Python's data model protocols but perform no analytical computation.

| Pattern | Reason | Example |
|:--------|:-------|:--------|
| `__init__` | Constructor - non-analytical | `class Analyzer: def __init__(self, config): ...` |
| `__str__` | String representation - non-analytical | `def __str__(self): return f"Method({self.id})"` |
| `__repr__` | String representation - non-analytical | `def __repr__(self): return f"<Analyzer at {hex(id(self))}>"` |
| `__eq__` | Equality comparison - non-analytical | `def __eq__(self, other): return self.id == other.id` |
| `__hash__` | Hash function - non-analytical | `def __hash__(self): return hash(self.id)` |
| `__len__` | Length accessor - non-analytical | `def __len__(self): return len(self.results)` |

**Rationale**: These methods are protocol implementations required by Python's object model. They do not perform domain-specific analysis or computation.

---

### 2. Private Utility Functions

Private helper methods that perform formatting, logging, or printing operations.

| Pattern | Reason | Example |
|:--------|:-------|:--------|
| `_format_*` | Formatting utility - non-semantic | `def _format_output(self, data): return json.dumps(data)` |
| `_log_*` | Logging utility - non-semantic | `def _log_progress(self, msg): logger.info(msg)` |
| `_print_*` | Print utility - non-semantic | `def _print_summary(self, results): print(results)` |

**Rationale**: These are pure I/O or presentation methods with no impact on analytical correctness.

---

### 3. Serialization Methods

Methods that convert data structures to/from standard formats.

| Pattern | Reason | Example |
|:--------|:-------|:--------|
| `to_string` | Serialization - non-semantic | `def to_string(self): return str(self.data)` |
| `to_json` | Serialization - non-semantic | `def to_json(self): return json.dumps(self.__dict__)` |
| `to_dict` | Serialization - non-semantic | `def to_dict(self): return {"id": self.id, "name": self.name}` |

**Rationale**: Serialization is a mechanical transformation without analytical logic.

---

### 4. AST Visitor Patterns

Methods following the visitor pattern for AST traversal.

| Pattern | Reason | Example |
|:--------|:-------|:--------|
| `visit_*` | AST visitor - non-analytical | `def visit_FunctionDef(self, node): self.functions.append(node)` |

**Rationale**: AST visitors are structural traversal methods. The analytical logic resides in what they *do* with visited nodes, not the visiting itself.

---

## Dynamic Exclusion Rules

Beyond pattern matching, the following **dynamic rules** apply:

### Rule 1: Private Utilities in Utility Layer

```python
condition: method_name.startswith('_') and layer == 'utility' and not analytically_active
reason: Private utility function - non-analytical
```

**Example**:
```python
# In src/farfan_pipeline/utils/helpers.py
def _sanitize_filename(name: str) -> str:  # EXCLUDED
    """Remove invalid characters from filename."""
    return re.sub(r'[^\w\s-]', '', name)
```

---

### Rule 2: Pure Getters

```python
condition: method_name.startswith('get_') and return_type in ['str', 'Path', 'bool'] and not analytically_active
reason: Simple getter with no analytical logic
```

**Example**:
```python
def get_config_path(self) -> Path:  # EXCLUDED
    """Return configuration file path."""
    return self._config_path
```

**Counter-example** (NOT excluded):
```python
def get_normalized_score(self) -> float:  # NOT EXCLUDED
    """Compute and return normalized score."""
    return self.raw_score / self.max_possible_score  # Analytical computation
```

---

## Verification Examples

### Should Be EXCLUDED ✅

```python
def __eq__(self, other):
    return self.id == other.id

def _format_report(self, data):
    return f"Report: {data}"

def to_json(self):
    return json.dumps(self.__dict__)

def visit_ClassDef(self, node):
    self.classes.append(node.name)

def get_method_name(self) -> str:
    return self._name
```

### Should Be CALIBRATED ❌

```python
def compute_score(self, text: str) -> float:
    """Analytical computation."""
    return len(text) / 1000.0

def calculate_threshold(self, distribution: List[float]) -> float:
    """Parametric decision."""
    return np.percentile(distribution, 75)

def filter_relevant_documents(self, docs: List[Doc]) -> List[Doc]:
    """Analytical filtering."""
    return [d for d in docs if d.score > self.threshold]
```

---

## Enforcement

The exclusion rules are enforced by:

1. **`rigorous_calibration_triage.py`**: Pre-filters methods before calibration
2. **`intrinsic_calibration_rubric.json`**: Machine-readable exclusion patterns
3. **Decision Automaton** (see [`decision_automaton.md`](file:///Users/recovered/Applications/F.A.R.F.A.N%20-MECHANISTIC-PIPELINE/docs/calibration/decision_automaton.md)): 3-question flow to determine calibration requirement

---

## References

- **Rubric Source**: [`intrinsic_calibration_rubric.json`](file:///Users/recovered/Applications/F.A.R.F.A.N%20-MECHANISTIC-PIPELINE/src/farfan_pipeline/core/calibration/intrinsic_calibration_rubric.json) § exclusion_criteria
- **Canonical Specification**: [`CALIBRATION_CANONICAL_COHERENCE_ANALYSIS.md`](file:///Users/recovered/Applications/F.A.R.F.A.N%20-MECHANISTIC-PIPELINE/CALIBRATION_CANONICAL_COHERENCE_ANALYSIS.md)
- **Decision Flow**: [`decision_automaton.md`](file:///Users/recovered/Applications/F.A.R.F.A.N%20-MECHANISTIC-PIPELINE/docs/calibration/decision_automaton.md)
