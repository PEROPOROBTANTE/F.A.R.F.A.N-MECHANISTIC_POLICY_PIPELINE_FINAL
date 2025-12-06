# Phase 4 Pattern Filtering Contract v2.0

## Contract Identifier
- **ID:** `PHASE4-PATTERN-FILTERING-V2.0`
- **Status:** Production
- **Effective Date:** 2024-12-05
- **Supersedes:** Phase 4 Dimension Aggregation v1.0 (deprecated)

## Purpose
Define the immutable interface contract for pattern filtering operations, establishing input/output schemas, validation rules, and semantic guarantees for context-aware pattern scoping.

## Input Contract: Pattern Catalog

### Schema: Pattern Specification
```python
PatternSpec = TypedDict('PatternSpec', {
    'id': str,                                    # Required: unique pattern identifier
    'pattern': str,                               # Required: regex or literal pattern
    'policy_area_id': NotRequired[str],           # Optional: policy area filter
    'context_scope': NotRequired[str],            # Optional: 'global' | 'section' | 'chapter' | 'page'
    'context_requirement': NotRequired[
        Union[str, Dict[str, Any]]                # Optional: context matching rules
    ],
    # Additional metadata fields preserved as-is
}, total=False)
```

### Required Fields
1. **id** (str)
   - Pattern unique identifier for logging and tracing
   - No uniqueness validation (downstream responsibility)
   - Empty string allowed (for compatibility)

2. **pattern** (str)
   - Regex pattern or literal text to match
   - Cannot be None or missing
   - Empty string allowed (matches nothing)

### Optional Fields
1. **policy_area_id** (str | None)
   - Policy area code (e.g., 'PA01', 'PA02', ...)
   - Used for cross-contamination prevention
   - Case-sensitive exact match only
   - Default: None (no policy area filtering)

2. **context_scope** (str | None)
   - Pattern applicability scope
   - Valid values: 'global', 'section', 'chapter', 'page'
   - Unknown values treated as 'global' (conservative)
   - Default: 'global'

3. **context_requirement** (str | Dict[str, Any] | None)
   - Context matching requirements
   - String: interpreted as section name `{'section': value}`
   - Dict: key-value requirements (AND logic)
   - None: no requirements (always match)
   - Default: None

### Metadata Fields
- All additional fields preserved during filtering
- No validation of extra fields
- Structure preserved (nested dicts/lists)

## Input Contract: Document Context

### Schema: Document Context
```python
DocumentContext = TypedDict('DocumentContext', {
    'section': NotRequired[str],                  # Section name
    'chapter': NotRequired[int],                  # Chapter number
    'page': NotRequired[int],                     # Page number
    'policy_area': NotRequired[str],              # Policy area code
    # Additional context fields as needed
}, total=False)
```

### Field Semantics
- All fields optional (empty context `{}` is valid)
- Missing fields treated as "not applicable"
- Additional fields preserved and available for matching
- No type coercion (strict type checking)

### Context Field Types
1. **section**: str
   - Section identifier or name
   - Case-sensitive matching
   - Examples: 'budget', 'indicators', 'introduction'

2. **chapter**: int
   - Chapter number (positive integer)
   - Used with comparison operators
   - Examples: 1, 2, 3, ...

3. **page**: int
   - Page number (positive integer)
   - Used with comparison operators
   - Examples: 1, 10, 47, ...

4. **policy_area**: str
   - Policy area code
   - Case-sensitive exact match
   - Examples: 'PA01', 'PA02', ..., 'PA10'

## Output Contract: Filtered Patterns

### Schema: Filter Result
```python
FilterResult = Tuple[
    List[PatternSpec],     # Filtered patterns (order preserved)
    FilterStatistics       # Filtering statistics
]

FilterStatistics = TypedDict('FilterStatistics', {
    'total_patterns': int,        # Input pattern count
    'context_filtered': int,      # Filtered by context_requirement
    'scope_filtered': int,        # Filtered by context_scope
    'passed': int                 # Patterns in output list
})
```

### Postconditions
1. **Arithmetic Invariant:**
   ```python
   stats['total_patterns'] == stats['context_filtered'] + stats['scope_filtered'] + stats['passed']
   ```

2. **Output Consistency:**
   ```python
   len(filtered_patterns) == stats['passed']
   ```

3. **Order Preservation:**
   - Filtered patterns maintain original input order
   - Stable sort (relative order unchanged)

4. **Structure Preservation:**
   - Pattern dictionaries not mutated
   - All fields preserved (including metadata)
   - References may be shared (shallow filtering)

5. **Empty Result Validity:**
   - Empty list `[]` is valid output
   - Statistics still computed and returned
   - No error raised for zero matches

## Semantic Contracts

### Contract 1: Strict Policy Area Equality
- **Requirement:** `policy_area` matching uses exact string equality
- **Case Sensitivity:** YES (PA01 ≠ pa01)
- **No Partial Match:** PA01 ≠ PA0 ≠ PA
- **No Wildcards:** PA* not expanded
- **No Ranges:** PA01-PA05 not expanded
- **No Fuzzy Match:** No similarity algorithms

### Contract 2: Context Scope Hierarchy
- **global:** Always applicable (no context required)
- **section:** Requires 'section' in document_context
- **chapter:** Requires 'chapter' in document_context
- **page:** Requires 'page' in document_context
- **unknown:** Treated as 'global' (conservative)

### Contract 3: Context Requirement Matching
- **AND Logic:** All requirements must be satisfied
- **Match Types:**
  1. **Exact:** `context[key] == required_value` (strict equality)
  2. **List:** `context[key] in required_value` (membership)
  3. **Comparison:** Operators >, <, >=, <= with numeric conversion
- **Missing Field:** Requirement fails (pattern rejected)
- **Type Mismatch:** Requirement fails (pattern rejected)

### Contract 4: Comparison Operators
- **Supported:** `>`, `<`, `>=`, `<=`
- **Format:** Operator immediately followed by number (e.g., '>2', '>=10')
- **Type Conversion:** Both values converted to float
- **Parse Error:** Requirement fails (pattern rejected)
- **Type Error:** Requirement fails (pattern rejected)

### Contract 5: Pattern Immutability
- **Input patterns:** Not modified during filtering
- **Output patterns:** Same dictionary objects as input (references preserved)
- **Metadata:** All extra fields preserved
- **Nested structures:** Preserved by reference (shallow copy)

### Contract 6: Statistics Accuracy
- **total_patterns:** Exact count of input patterns
- **context_filtered:** Patterns rejected by context_requirement mismatch
- **scope_filtered:** Patterns rejected by context_scope incompatibility
- **passed:** Patterns included in output (no double-counting)

## Error Handling Contract

### Validation Errors (Non-Fatal)
- **Missing 'pattern' field:** Skip pattern, log warning, continue
- **Invalid context type:** Treat as empty context, continue
- **Invalid comparison:** Reject pattern, continue

### Fatal Errors (Raise Exception)
- None (all error conditions handled gracefully)

### Logging Requirements
- **WARNING:** Zero patterns after filtering
- **DEBUG:** Individual pattern filter decisions
- **INFO:** Filter operation completion with statistics

## Function Signature

```python
def filter_patterns_by_context(
    patterns: List[Dict[str, Any]],
    document_context: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter patterns based on document context.
    
    Args:
        patterns: List of pattern specifications
        document_context: Current document context
    
    Returns:
        Tuple of (filtered_patterns, statistics)
    
    Raises:
        No exceptions (graceful error handling)
    
    Postconditions:
        - len(result[0]) == result[1]['passed']
        - result[1]['total_patterns'] == len(patterns)
        - All filtered patterns match document_context
        - Pattern order preserved
        - Pattern structures not mutated
    """
```

## Helper Function Contracts

### context_matches
```python
def context_matches(
    document_context: Dict[str, Any],
    context_requirement: Union[Dict[str, Any], str, None]
) -> bool:
    """
    Check if document context satisfies pattern requirements.
    
    Args:
        document_context: Current context
        context_requirement: Pattern requirements
    
    Returns:
        True if all requirements satisfied, False otherwise
    
    Semantics:
        - None requirement → True (no requirements)
        - str requirement → {'section': str} (section match)
        - dict requirement → AND logic for all key-value pairs
        - Invalid types → True (permissive)
    """
```

### evaluate_comparison
```python
def evaluate_comparison(
    value: Any,
    expression: str
) -> bool:
    """
    Evaluate comparison expression (e.g., '>2', '>=5').
    
    Args:
        value: Value from document context
        expression: Comparison string (operator + number)
    
    Returns:
        True if comparison holds, False otherwise
    
    Supported:
        >, <, >=, <=
    
    Error Handling:
        - Parse error → False
        - Type conversion error → False
    """
```

### in_scope
```python
def in_scope(
    document_context: Dict[str, Any],
    scope: str
) -> bool:
    """
    Check if pattern scope applies to current context.
    
    Args:
        document_context: Current context
        scope: Pattern scope string
    
    Returns:
        True if pattern should be applied, False otherwise
    
    Semantics:
        - 'global' → True (always applicable)
        - 'section' → 'section' in document_context
        - 'chapter' → 'chapter' in document_context
        - 'page' → 'page' in document_context
        - unknown → True (conservative)
    """
```

### create_document_context
```python
def create_document_context(
    section: Optional[str] = None,
    chapter: Optional[int] = None,
    page: Optional[int] = None,
    policy_area: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Helper to create document context dictionary.
    
    Args:
        section: Section name
        chapter: Chapter number
        page: Page number
        policy_area: Policy area code
        **kwargs: Additional context fields
    
    Returns:
        Dictionary with non-None values only
    
    Postcondition:
        - Only non-None values included
        - Additional kwargs merged
    """
```

## Test Coverage Requirements

### Functional Tests (Minimum 50 test cases)
1. **Policy Area Strict Equality** (7 tests)
   - Exact match
   - Case sensitivity
   - No partial match
   - No prefix match
   - No wildcard expansion
   - No range expansion
   - Cross-contamination prevention

2. **Immutable Returns** (6 tests)
   - List type (not tuple in current impl)
   - Order preservation
   - Pattern structure preservation
   - No mutation
   - Empty result as list
   - No reference sharing violations

3. **Context Scope Filtering** (7 tests)
   - Global scope always passes
   - Section scope requires section
   - Chapter scope requires chapter
   - Page scope requires page
   - Unknown scope defaults to allow
   - Missing scope defaults to global
   - Mixed scopes filtered correctly

4. **Context Requirement Matching** (8 tests)
   - Exact match
   - List membership
   - Comparison operators (>, <, >=, <=)
   - Multiple requirements AND logic
   - String requirement as section
   - Missing fields reject match

5. **Filter Statistics** (5 tests)
   - Total patterns tracked
   - Context filtered count
   - Scope filtered count
   - Passed count
   - Statistics consistency invariant

6. **Edge Cases** (17 tests)
   - Empty pattern list
   - Empty context
   - Invalid context
   - Missing pattern fields
   - Zero results
   - Large pattern catalogs
   - Unicode handling

### Property-Based Tests
- No cross-contamination (different policy areas never mix)
- Filtering rate within bounds (0.0 to 1.0)
- Arithmetic invariants always hold
- Order preservation verified
- Deterministic results (same input → same output)

## Performance Contract

### Time Complexity
- **O(n)** where n = number of patterns (typical case)
- **O(n × m)** worst case where m = average requirement fields

### Space Complexity
- **O(n)** for input and output lists
- **O(1)** for statistics

### Scalability
- Must handle 10,000+ patterns without degradation
- Parallel iteration within stages (where applicable)

## Observability Contract

### Structured Logging
```python
{
    "event": str,              # Event type
    "pattern_id": str,         # Pattern identifier
    "scope": str,              # Context scope
    "requirement": dict,       # Context requirement
    "context": dict,           # Document context
    "passed": bool,            # Filter result
    "stats": dict,             # Filter statistics
    "filtering_rate": float,   # Efficiency metric
    "timestamp": str           # ISO 8601
}
```

### Metrics
- `N4_PF.patterns_total`: Input pattern count
- `N4_PF.patterns_filtered`: Total filtered out
- `N4_PF.filtering_rate`: Percentage filtered
- `N4_PF.latency_ms`: Operation duration

### Alerts
- Zero patterns after filtering (potential config issue)

## Version History

### v2.0 (2024-12-05) - Current
- Complete rewrite for Pattern Filtering functionality
- Established three-tier hierarchical specification
- Aligned with Phases 6-8 documentation pattern
- Added comprehensive test coverage requirements
- Defined immutability and observability contracts

### v1.0 (Deprecated)
- Dimension Aggregation specification
- Superseded by new Pattern Filtering contract

## Contract Enforcement

### Pre-deployment Checklist
- [ ] All 50+ test cases passing
- [ ] Property-based tests passing
- [ ] Performance benchmarks met
- [ ] Structured logging implemented
- [ ] Metrics instrumented
- [ ] Documentation updated (EN + ES)

### Runtime Validation
- Input pattern schema validation (optional)
- Output statistics invariant checking (assertion)
- Logging of all filter decisions (debug level)

## Contract Violations

### Violation Severity
- **Critical:** Arithmetic invariant broken (sum mismatch)
- **Major:** Pattern mutation detected
- **Minor:** Statistics incomplete or inconsistent

### Remediation
- Critical: Abort operation, raise exception
- Major: Log error, continue with warning
- Minor: Log warning, proceed

---

**Contract Authority:** F.A.R.F.A.N. Architecture Board  
**Review Cycle:** Quarterly or on breaking changes  
**Next Review:** 2025-03-05  
**Contact:** architecture@farfan-pipeline.org
