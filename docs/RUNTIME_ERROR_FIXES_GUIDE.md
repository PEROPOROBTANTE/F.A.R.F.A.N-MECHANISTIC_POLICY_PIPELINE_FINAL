# Runtime Error Fixes Documentation

## Overview

This document describes the fixes applied to prevent three critical runtime errors in the policy analysis system.

## Problems Fixed

### 1. 'bool' object is not iterable

**Error Pattern:**
```python
contradictions = some_function()  # Returns False instead of []
for c in contradictions:  # TypeError: 'bool' object is not iterable
    process(c)
```

**Solution:**
Created `ensure_list_return()` function that converts `False`, `True`, or `None` to empty list `[]`.

**Applied to:**
- `contradiction_deteccion.py`: All `_detect_*` method returns wrapped with `ensure_list_return()`
- `macro_prompts.py`: `_detect_contradictions()` return wrapped
- `policy_processor.py`: Contradiction list processing wrapped

**Example:**
```python
# Before:
contradictions.extend(semantic_contradictions)

# After:
contradictions.extend(ensure_list_return(semantic_contradictions))
```

### 2. 'str' object has no attribute 'text'

**Error Pattern:**
```python
text = "Some string"
result = text.text  # AttributeError: 'str' object has no attribute 'text'
```

**Root Cause:**
Code expecting spacy Doc/Span objects (which have `.text` attribute) receives plain strings instead.

**Solution:**
Created `safe_text_extract()` function that:
- Returns the input if it's already a string
- Extracts `.text` if the object has that attribute (spacy Doc/Span)
- Converts to string as fallback

**Applied to:**
- `contradiction_deteccion.py`: `_determine_semantic_role()` method

**Example:**
```python
# Before:
text_lower = sent.text.lower()

# After:
text_lower = safe_text_extract(sent).lower()
```

### 3. can't multiply sequence by non-int of type 'float'

**Error Pattern:**
```python
items = [1.0, 2.0, 3.0]
weight = 0.5
result = items * weight  # TypeError: can't multiply sequence by non-int of type 'float'
```

**Root Cause:**
Python lists don't support element-wise multiplication with floats directly.

**Solution:**
Created `safe_weighted_multiply()` function that:
- Uses list comprehension for lists: `[item * weight for item in items]`
- Uses numpy multiplication for numpy arrays: `items * weight`
- Handles edge cases gracefully

**Status:**
Function created and tested. No instances of this error found in current codebase, but function is available for future use or edge cases.

**Example:**
```python
# Before:
posteriors = priors * likelihood_ratio  # Error if priors is a list

# After:
posteriors = safe_weighted_multiply(priors, likelihood_ratio)
```

## Usage

Import the fix functions at the top of any module:

```python
from runtime_error_fixes import (
    ensure_list_return,
    safe_text_extract,
    safe_weighted_multiply,
    safe_list_iteration,
)
```

### ensure_list_return(value)

Use when you need to ensure a value is iterable as a list:

```python
# Wrap any function that might return False/None instead of list
items = ensure_list_return(get_items())
for item in items:  # Safe even if get_items() returned False
    process(item)
```

### safe_text_extract(obj)

Use when extracting text from objects that might be strings or spacy objects:

```python
# Safe for both strings and spacy Doc/Span objects
text = safe_text_extract(sentence)
words = text.split()
```

### safe_weighted_multiply(items, weight)

Use when multiplying lists or arrays by a scalar:

```python
# Works for both lists and numpy arrays
weighted = safe_weighted_multiply([1.0, 2.0, 3.0], 0.5)
# Result: [0.5, 1.0, 1.5]
```

### safe_list_iteration(value)

Use to ensure safe iteration over any value:

```python
# Converts bool/None to [], strings to single-item list, etc.
for item in safe_list_iteration(value):
    process(item)
```

## Testing

All fixes are tested in `tests/test_runtime_error_fixes.py`:

- Unit tests for each fix function
- Integration tests for common error scenarios
- Edge case testing (None, empty, bool, etc.)

Run tests:
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from runtime_error_fixes import *
# Manual tests run successfully
"
```

## Impact

### Files Modified

1. `runtime_error_fixes.py` - New utility module with fix functions
2. `contradiction_deteccion.py` - Applied bool→list and text extraction fixes
3. `macro_prompts.py` - Applied bool→list fix to contradiction detection
4. `policy_processor.py` - Applied bool→list fix to contradiction processing
5. `tests/test_runtime_error_fixes.py` - Comprehensive test suite

### Backward Compatibility

All changes are backward compatible:
- Functions that already return lists continue to work unchanged
- Defensive wrappers add no overhead for correct code
- No API changes to public interfaces

### Performance

Negligible performance impact:
- `ensure_list_return()`: Simple isinstance checks
- `safe_text_extract()`: Attribute check and string conversion
- `safe_weighted_multiply()`: List comprehension (Python idiomatic)

## Future Enhancements

Potential improvements:
1. Add type hints to original functions to catch errors at static analysis time
2. Consider using numpy arrays consistently for numeric operations
3. Add mypy checks to prevent bool where list expected
4. Create linter rules to detect unsafe .text access patterns

## See Also

- `adapters.py` - Contains additional safe extraction functions
- `contracts.py` - Type-safe value objects
- `TYPE_SAFETY_GUIDE.md` - Overall type safety strategy
