# Calibration Configuration Migration Summary

## Overview
Successfully migrated hardcoded calibration values from `orchestrator.py` and `layer_computers.py` to centralized configuration files, improving maintainability and configurability of the calibration system.

## Changes Made

### 1. New Configuration Files

#### `system/config/calibration/runtime_layers.json`
- **Purpose**: Stores runtime layer score computation parameters for CalibrationOrchestrator
- **Migrated values**: All hardcoded values from `_compute_*_score` methods (0.65-0.75 range)
- **Layers configured**:
  - `chain`: Chain of evidence score (@chain)
    - base_score: 0.65
    - dimension_factor: 0.15
    - dimension_max: 10.0
    - position_bonus: 0.1
    - position_threshold: 0.5
  
  - `quality`: Data quality score (@q)
    - base_score: 0.70
    - question_factor: 0.08
    - question_max: 20.0
  
  - `density`: Data density score (@d)
    - base_score: 0.68
    - position_factor: 0.15
    - optimal_position: 0.5
  
  - `provenance`: Provenance traceability score (@p)
    - base_score: 0.75
  
  - `coverage`: Coverage completeness score (@C)
    - base_score: 0.72
    - bonus_dimensions: [1, 2, 5, 10]
    - dimension_bonus: 0.1
  
  - `uncertainty`: Uncertainty quantification score (@u)
    - base_score: 0.68
  
  - `mechanism`: Mechanistic explanation score (@m)
    - base_score: 0.65
    - dimension_threshold: 7
    - dimension_bonus: 0.15

#### `system/config/calibration/unit_transforms.json`
- **Purpose**: Stores transformation formulas for layer computation functions
- **Migrated from**: `layer_computers.py` transformation logic
- **Configurations**:
  - **g_functions**: 4 transformation function types (identity, constant, piecewise_linear, sigmoidal)
  - **chain_layer**: Discrete mappings for contract validation
  - **question_layer**: Compatibility levels (primary, secondary, validator, undeclared)
  - **dimension_layer**: Alignment matrix for dimensions DIM01-DIM06
  - **policy_layer**: Policy area scores for PA01-PA10
  - **interplay_layer**: Congruence layer component scores
  - **meta_layer**: Transparency, governance, and cost aggregation

### 2. Code Changes

#### `src/farfan_pipeline/core/calibration/orchestrator.py`
- Added `_runtime_layer_config` instance variable
- Added `_load_runtime_layer_config()` method to load configuration from JSON
- Updated all `_compute_*_score` methods to load parameters from config:
  - `_compute_chain_score()`
  - `_compute_quality_score()`
  - `_compute_density_score()`
  - `_compute_provenance_score()`
  - `_compute_coverage_score()`
  - `_compute_uncertainty_score()`
  - `_compute_mechanism_score()`
- All methods now use `self._runtime_layer_config.get('layers', {}).get(layer_name, {})` pattern
- Fallback to hardcoded defaults if config not found (backward compatibility)

#### `src/farfan_pipeline/core/calibration/layer_computers.py`
- Added module-level `_unit_transforms_config` cache variable
- Added `_load_unit_transforms_config()` function to load configuration from JSON
- Updated all layer computation functions to load from config:
  - `compute_chain_layer()`: Uses config for discrete mappings
  - `compute_unit_layer()`: Uses config for g_function specifications
  - `compute_question_layer()`: Uses config for compatibility levels
  - `compute_dimension_layer()`: Uses config for alignment matrix
  - `compute_policy_layer()`: Uses config for policy area scores
  - `compute_interplay_layer()`: Uses config for interplay components
  - `compute_meta_layer()`: Uses config for meta layer aggregation
- All functions maintain backward compatibility with contextual_config parameter
- Added deprecation notes in docstrings indicating preference for unit_transforms.json

### 3. Type Updates
- Updated type hints from `Dict[str, Any]` to `dict[str, Any]` (Python 3.9+ style)
- Updated `Optional[X]` to `X | None` (Python 3.10+ style)
- Applied ruff auto-fixes for import sorting and code style

## Benefits

1. **Configurability**: Calibration parameters can now be tuned without code changes
2. **Maintainability**: Centralized configuration makes it easier to track and update values
3. **Testability**: Different configurations can be tested by swapping JSON files
4. **Auditability**: Configuration changes are tracked in version control
5. **Documentation**: JSON structure serves as self-documenting parameter catalog

## Backward Compatibility

- All functions maintain original signatures
- Fallback to hardcoded defaults if config files are missing
- Existing contextual_config parameters still supported (with deprecation notes)

## Validation

✓ Both JSON files are valid JSON
✓ Python files compile without syntax errors
✓ Configuration loader functions work correctly
✓ All required layers present in runtime_layers.json
✓ All required transforms present in unit_transforms.json
✓ Applied ruff auto-fixes for code style

## Testing Recommendations

1. Run full test suite to ensure no regressions
2. Test with missing config files to verify fallback behavior
3. Test with modified config values to verify they're being used
4. Run calibration_system tests to verify no hardcoded values remain
5. Integration test with actual CalibrationOrchestrator usage

## Migration Path for Future Use

To modify calibration parameters:
1. Edit `system/config/calibration/runtime_layers.json` for runtime layer scores
2. Edit `system/config/calibration/unit_transforms.json` for transformation formulas
3. No code changes required unless adding new layers or transforms

## Files Modified

- `src/farfan_pipeline/core/calibration/orchestrator.py`
- `src/farfan_pipeline/core/calibration/layer_computers.py`

## Files Created

- `system/config/calibration/runtime_layers.json`
- `system/config/calibration/unit_transforms.json`

## Next Steps

1. Update `.gitignore` if needed to track config files
2. Add schema validation for config files (optional)
3. Create migration script for updating old configs (optional)
4. Update documentation to reference new config files
5. Run full CI/CD pipeline to validate changes
