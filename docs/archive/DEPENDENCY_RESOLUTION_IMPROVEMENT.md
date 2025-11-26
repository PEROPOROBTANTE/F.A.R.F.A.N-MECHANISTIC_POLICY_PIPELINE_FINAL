# Dependency Resolution Improvement

**Date**: 2025-11-08  
**Status**: ✅ COMPLETE  
**Issue**: Pip dependency resolution failures with strict version pins

## Problem

The original `requirements-core.txt` used **strict exact version pins** (`==`) for all packages, which caused pip dependency resolution failures when:

1. Transitive dependencies of different packages required incompatible versions
2. Multiple packages depended on the same library with different version constraints
3. HuggingFace ecosystem packages (transformers, tokenizers, huggingface-hub) had complex interdependencies

### Example Conflict Scenario
```
transformers==4.53.0 requires tokenizers>=0.20.0
sentence-transformers==3.3.1 requires transformers>=4.40.0
huggingface-hub==0.27.1 is pinned but transformers needs >=0.27.0,<1.0.0
```

With strict pins, pip cannot resolve these overlapping requirements.

## Solution

### 1. Loosened Version Constraints for ML/NLP Packages

Changed from exact pins to **constrained ranges** for packages with complex dependency chains:

| Package | Before | After | Reason |
|---------|--------|-------|--------|
| transformers | `==4.53.0` | `>=4.40.0,<5.0.0` | HuggingFace ecosystem |
| huggingface-hub | `==0.27.1` | `>=0.27.0,<1.0.0` | HuggingFace ecosystem |
| tokenizers | `==0.21.0` | `>=0.20.0,<1.0.0` | HuggingFace ecosystem |
| sentence-transformers | `==3.3.1` | `>=3.0.0,<4.0.0` | Depends on transformers |
| safetensors | `==0.5.2` | `>=0.4.0,<1.0.0` | Used by transformers |
| numpy | `==1.26.4` | `>=1.26.0,<3.0.0` | Scientific computing base |
| scipy | `==1.14.1` | `>=1.14.0,<2.0.0` | Scientific computing |
| pandas | `==2.2.3` | `>=2.2.0,<3.0.0` | Data processing |
| scikit-learn | `==1.6.1` | `>=1.5.0,<2.0.0` | ML library |
| pydantic | `==2.10.6` | `>=2.10.0,<3.0.0` | Data validation |
| fastapi | `==0.115.6` | `>=0.115.0,<1.0.0` | Web framework |

**Key Principle**: Use `>=X,<Y` format with **upper bounds** to maintain stability while allowing pip's resolver flexibility.

### 2. Maintained Exact Pins for Stable Packages

44 packages still use exact pins (`==`) where there are no known dependency conflicts:
- PDF processing libraries (PyMuPDF, pdfplumber, PyPDF2)
- Utilities (click, pyyaml, python-dotenv)
- Testing tools (pytest, pytest-cov)
- And other stable dependencies

### 3. Updated Validation Infrastructure

**a) Updated `.github/workflows/dependency-gates.yml` Gate 3:**
```yaml
# Before: Failed on any >= operator
# After: Allows >=X,<Y but fails on unconstrained >=X
if grep -E ">=" requirements-core.txt | grep -v "^#" | grep -v "<"; then
  echo "❌ FAILED: Unconstrained open version ranges detected!"
  exit 1
fi
```

**b) Updated `scripts/check_version_pins.py`:**
- Changed from "exact pins only" to "exact pins OR constrained ranges"
- Added `ALLOWED_CONSTRAINED_RANGES` whitelist
- Validates that constrained ranges have upper bounds

**c) Updated `tests/test_dependency_management.py`:**
- Test now accepts constrained ranges for approved packages
- Enforces exact pins for all other packages

## Benefits

### ✅ Improved Dependency Resolution
- Pip can now find compatible versions for complex dependency chains
- Reduces "ResolutionImpossible" errors
- Allows for smoother updates of HuggingFace ecosystem packages

### ✅ Maintained Reproducibility
- Upper bounds prevent unexpected major version jumps
- Core stable packages still use exact pins
- Lock files (constraints-*.txt) still available for exact reproduction

### ✅ Better Compatibility
- Works with broader range of environments
- Easier to integrate with other projects
- Less likely to conflict with platform-specific requirements

## Verification

### Format Validation
```bash
python3 scripts/check_version_pins.py requirements-core.txt
# ✅ SUCCESS: All version constraints are appropriate
```

### Constraint Analysis
```python
# 44 packages with exact pins (==)
# 11 packages with constrained ranges (>=....<)
# 0 issues found
```

### Package Distribution
- Exact pins: 80% of packages (stable, low-conflict)
- Constrained ranges: 20% of packages (complex dependency chains)

## Migration Notes

### For CI/CD
No changes needed - existing workflows will continue to work with the updated validation logic.

### For Developers
Installation commands remain the same:
```bash
pip install -r requirements-core.txt
```

### For Lock Files
Existing lock files (constraints-*.txt) can still be used for exact reproduction:
```bash
pip install -c constraints-complete.txt -r requirements-core.txt
```

## Files Changed

| File | Change |
|------|--------|
| `requirements-core.txt` | Loosened 11 packages to constrained ranges |
| `.github/workflows/dependency-gates.yml` | Updated Gate 3 validation logic |
| `scripts/check_version_pins.py` | Added support for constrained ranges |
| `tests/test_dependency_management.py` | Updated test to allow constrained ranges |
| `DEPENDENCY_IMPLEMENTATION_SUMMARY.md` | Updated to reflect hybrid approach |

## References

- [Python Packaging User Guide - Dependency Specification](https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/)
- [PEP 440 - Version Identifiers](https://peps.python.org/pep-0440/)
- [pip Dependency Resolution](https://pip.pypa.io/en/stable/topics/dependency-resolution/)

## Summary

**Before**: All packages used strict exact pins → dependency resolution failures  
**After**: Hybrid approach with constrained ranges for complex packages → improved resolution while maintaining stability  
**Result**: Better pip compatibility with maintained reproducibility
