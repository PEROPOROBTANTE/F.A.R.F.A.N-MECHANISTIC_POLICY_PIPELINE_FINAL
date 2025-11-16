# Defensive Function Signatures - Implementation Report

## Problem Statement

The pipeline was experiencing frequent errors due to mismatches between how functions were called and how they were defined:

1. **PDETMunicipalPlanAnalyzer._is_likely_header()** - Called with unexpected `pdf_path` keyword argument
2. **IndustrialPolicyProcessor._analyze_causal_dimensions()** - Called without required `sentences` positional argument  
3. **BayesianMechanismInference.__init__()** - Called with unexpected `causal_hierarchy` keyword argument

## Solution Implemented

All three functions have been updated with **defensive signatures** that gracefully handle argument mismatches:

### 1. PDETMunicipalPlanAnalyzer._is_likely_header()

**Location:** `src/saaaaaa/analysis/financiero_viabilidad_tablas.py` (class PDETMunicipalPlanAnalyzer)

**Signature:**
```python
def _is_likely_header(self, row: pd.Series, **kwargs) -> bool:
```

**Changes:**
- Added `**kwargs` parameter to accept any additional keyword arguments
- Logs warning when unexpected kwargs are passed
- Continues execution gracefully, ignoring unexpected arguments

**Implementation:**
```python
def _is_likely_header(self, row: pd.Series, **kwargs) -> bool:
    """
    Determine if a DataFrame row is likely a header row based on linguistic analysis.
    
    Args:
        row: pandas Series representing a row from a DataFrame
        **kwargs: Accepts additional keyword arguments for backward compatibility.
                 These are ignored (e.g., pdf_path if mistakenly passed).
    
    Returns:
        Boolean indicating whether the row appears to be a header
    
    Note:
        This function only requires 'row' parameter. Any additional kwargs
        (like 'pdf_path') are silently ignored to maintain interface stability.
    """
    # Log warning if unexpected kwargs are passed
    if kwargs:
        logger.warning(
            f"_is_likely_header received unexpected keyword arguments: {list(kwargs.keys())}. "
            "These will be ignored. Expected signature: _is_likely_header(self, row: pd.Series)"
        )
    
    text = ' '.join(row.astype(str))
    doc = self.nlp(text)
    pos_counts = pd.Series([token.pos_ for token in doc]).value_counts()
    noun_ratio = pos_counts.get('NOUN', 0) / max(len(doc), 1)
    verb_ratio = pos_counts.get('VERB', 0) / max(len(doc), 1)
    return noun_ratio > verb_ratio and len(text) < 200
```

### 2. IndustrialPolicyProcessor._analyze_causal_dimensions()

**Location:** `src/saaaaaa/processing/policy_processor.py` (class IndustrialPolicyProcessor)

**Signature:**
```python
def _analyze_causal_dimensions(
    self, text: str, sentences: Optional[List[str]] = None
) -> Dict[str, Any]:
```

**Changes:**
- Changed `sentences` parameter from required to `Optional[List[str]] = None`
- Auto-extracts sentences from text if not provided
- Logs warning about performance impact when auto-extraction is used

**Implementation:**
```python
def _analyze_causal_dimensions(
    self, text: str, sentences: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform global analysis of causal dimensions across entire document.
    
    Args:
        text: Full document text
        sentences: Optional pre-segmented sentences. If not provided, will be 
                  automatically extracted from text using the text processor.
    
    Returns:
        Dictionary containing dimension scores and confidence metrics
    
    Note:
        This function requires 'sentences' for optimal performance. If not provided,
        sentences will be extracted from text automatically, which may impact performance.
    """
    # Defensive validation: ensure sentences parameter is provided
    if sentences is None:
        logger.warning(
            "_analyze_causal_dimensions called without 'sentences' parameter. "
            "Automatically extracting sentences from text. "
            "Expected signature: _analyze_causal_dimensions(self, text: str, sentences: List[str])"
        )
        # Auto-extract sentences if not provided
        sentences = self.text_processor.segment_into_sentences(text)
    
    # ... rest of implementation
```

### 3. BayesianMechanismInference.__init__()

**Location:** `src/saaaaaa/analysis/derek_beach.py` (class BayesianMechanismInference)

**Signature:**
```python
def __init__(self, config: ConfigLoader, nlp_model: spacy.Language, **kwargs) -> None:
```

**Changes:**
- Added `**kwargs` parameter to accept any additional keyword arguments
- Logs warning when unexpected kwargs are passed
- Continues initialization gracefully, ignoring unexpected arguments

**Implementation:**
```python
def __init__(self, config: ConfigLoader, nlp_model: spacy.Language, **kwargs) -> None:
    """
    Initialize Bayesian Mechanism Inference engine.
    
    Args:
        config: Configuration loader instance
        nlp_model: spaCy NLP model for text processing
        **kwargs: Accepts additional keyword arguments for backward compatibility.
                 Unexpected arguments (e.g., 'causal_hierarchy') are logged and ignored.
    
    Note:
        This function signature has been made defensive to handle unexpected
        keyword arguments that may be passed due to interface drift.
    """
    # Log warning if unexpected kwargs are passed
    if kwargs:
        logging.getLogger(__name__).warning(
            f"BayesianMechanismInference.__init__ received unexpected keyword arguments: {list(kwargs.keys())}. "
            "These will be ignored. Expected signature: __init__(self, config: ConfigLoader, nlp_model: spacy.Language)"
        )
    
    # ... rest of initialization
```

## Benefits

1. **Backward Compatibility**: Functions can still be called with old argument patterns without breaking
2. **Forward Compatibility**: New arguments can be added without breaking existing callers
3. **Graceful Degradation**: Functions log warnings but continue execution
4. **Clear Documentation**: Docstrings explain the defensive behavior
5. **No Breaking Changes**: Existing working code continues to work

## Testing

A comprehensive test suite has been created in `tests/test_defensive_signatures.py` that verifies:

1. Each function accepts the documented arguments
2. Unexpected arguments are handled gracefully
3. Docstrings accurately describe the defensive behavior
4. Warning logs are emitted when unexpected arguments are passed

## Integration with ArgRouter

The defensive signatures work seamlessly with the `ArgRouter` class used by the orchestrator:

- `ArgRouter` inspects method signatures using Python's `inspect` module
- Methods with `**kwargs` or optional parameters are correctly handled
- The router can pass available arguments while ignoring those not in the signature
- Defensive implementations provide an additional safety layer

## Recommendations

### For Future Development

1. **Always use defensive signatures** for public methods that may be called by orchestrators or external code
2. **Log warnings** when unexpected arguments are received to help identify interface drift
3. **Document the defensive behavior** clearly in docstrings
4. **Test with various argument combinations** to ensure resilience
5. **Consider using protocol classes** (PEP 544) for more flexible typing

### For Fixing Remaining Issues

The problem statement mentions these errors were "frequent" - to fully resolve:

1. Search for any remaining call sites using old argument patterns
2. Update those call sites to use the correct arguments
3. Keep the defensive implementations as safety nets
4. Monitor logs for warnings about unexpected arguments
5. Gradually migrate callers to use correct signatures

### Monitoring

To track the effectiveness of these fixes:

1. Monitor application logs for the specific warning messages
2. Count occurrences of warnings to identify problematic call sites
3. Create metrics/alerts for high frequencies of defensive warnings
4. Periodically review and update call sites based on warnings

## Conclusion

The three identified functions now have defensive signatures that gracefully handle argument mismatches:

- ✅ `_is_likely_header`: Accepts **kwargs (including unexpected `pdf_path`)
- ✅ `_analyze_causal_dimensions`: Makes `sentences` optional with auto-extraction
- ✅ `BayesianMechanismInference.__init__`: Accepts **kwargs (including unexpected `causal_hierarchy`)

These changes eliminate the "most frequent error" mentioned in the problem statement while maintaining full backward and forward compatibility.
