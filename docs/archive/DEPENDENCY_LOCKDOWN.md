# Dependency Lockdown System

## Overview

The Dependency Lockdown system enforces strict control over network dependencies and external model downloads to prevent "magic" behavior where the system silently downloads models or falls back to degraded modes without explicit user knowledge.

## Key Principles

1. **Explicit is better than implicit**: No silent fallbacks or "best effort" behavior
2. **Fail fast with clear errors**: If a dependency is missing or not allowed, fail immediately with actionable error messages
3. **Environment-controlled**: All behavior is controlled via environment variables
4. **No magical downloads**: Models are only downloaded when explicitly allowed

## Environment Variables

### `HF_ONLINE`

Controls whether HuggingFace model downloads are allowed.

- **Default**: `0` (offline mode enforced)
- **Values**:
  - `0`: Offline mode - no model downloads allowed
  - `1`: Online mode - model downloads permitted

When `HF_ONLINE=0` (default):
- `HF_HUB_OFFLINE=1` is automatically set
- `TRANSFORMERS_OFFLINE=1` is automatically set
- Any attempt to download models raises `DependencyLockdownError`

## Usage

### In Orchestrator

The orchestrator automatically initializes dependency lockdown on construction:

```python
from saaaaaa.core.orchestrator import Orchestrator

# Lockdown is automatically initialized
orchestrator = Orchestrator()

# Check current mode
mode = orchestrator.dependency_lockdown.get_mode_description()
print(f"Dependency mode: {mode['mode']}")  # 'offline_enforced' or 'online'
```

### In Custom Code

```python
from saaaaaa.core.dependency_lockdown import get_dependency_lockdown

lockdown = get_dependency_lockdown()

# Check if online model access is allowed (raises if not)
lockdown.check_online_model_access(
    model_name="bert-base-uncased",
    operation="load transformer model"
)

# Check critical dependency (raises if missing)
lockdown.check_critical_dependency(
    module_name="numpy",
    pip_package="numpy",
    phase="data_processing"
)

# Check optional dependency (returns bool, logs warning if missing)
has_cv2 = lockdown.check_optional_dependency(
    module_name="cv2",
    pip_package="opencv-python",
    feature="image_processing"
)

if not has_cv2:
    logger.warning("DEGRADED MODE: Image processing disabled")
    # Explicitly handle degraded mode
```

### In Embedding System

The embedding system respects the lockdown automatically:

```python
from saaaaaa.processing.embedding_policy import PolicyAnalysisEmbedder, PolicyEmbeddingConfig

# With HF_ONLINE=0 (default)
config = PolicyEmbeddingConfig(embedding_model="sentence-transformers/model")

# This will raise DependencyLockdownError if model is not cached locally
try:
    embedder = PolicyAnalysisEmbedder(config)
except DependencyLockdownError as e:
    print(f"Cannot initialize embedder: {e}")
    # Error message will be:
    # "Online model download disabled in this environment. 
    #  Attempted operation: load SentenceTransformer embedding model for model 'sentence-transformers/model'.
    #  To enable online downloads, set HF_ONLINE=1 environment variable.
    #  No fallback to degraded mode - this is a hard failure."
```

## Running in Offline Mode (Default)

```bash
# Default: offline mode enforced
python my_script.py

# Explicit offline mode
HF_ONLINE=0 python my_script.py
```

**Expected behavior**:
- If models are cached locally: ✅ Works normally
- If models need download: ❌ Fails with clear error message
- No silent fallback or degraded mode

## Running in Online Mode

```bash
# Enable online model downloads
HF_ONLINE=1 python my_script.py
```

**Expected behavior**:
- Models can be downloaded from HuggingFace Hub
- Models are cached locally for future offline use
- ⚠️ Network access required

## Error Messages

### Online Model Download Disabled

```
DependencyLockdownError: Online model download disabled in this environment. 
Attempted operation: load SentenceTransformer embedding model for model 'paraphrase-multilingual-mpnet-base-v2'. 
To enable online downloads, set HF_ONLINE=1 environment variable. 
No fallback to degraded mode - this is a hard failure.
```

### Critical Dependency Missing

```
DependencyLockdownError: Critical dependency 'cv2' is missing for phase 'image_extraction'. 
Install it with: pip install opencv-python. 
No degraded mode available - this is a mandatory dependency.
```

### Optional Dependency Missing

```
WARNING: DEGRADED MODE: Optional dependency 'cv2' not available. 
Feature 'image_processing' will be disabled. 
Install with: pip install opencv-python
```

## Integration with Existing Code

### Checking Dependencies Before Phase Execution

```python
def execute_phase_with_vision(self, document):
    """Execute a phase that requires computer vision."""
    lockdown = get_dependency_lockdown()
    
    # Check critical dependency
    lockdown.check_critical_dependency(
        module_name="cv2",
        pip_package="opencv-python",
        phase="vision_processing"
    )
    
    import cv2
    # Proceed with vision processing...
```

### Handling Optional Dependencies

```python
def execute_phase_with_optional_nlp(self, document):
    """Execute a phase with optional NLP enhancements."""
    lockdown = get_dependency_lockdown()
    
    # Check optional dependency
    has_spacy = lockdown.check_optional_dependency(
        module_name="spacy",
        pip_package="spacy",
        feature="advanced_nlp"
    )
    
    if has_spacy:
        import spacy
        # Use spacy for enhanced processing
        logger.info("Using advanced NLP with spacy")
    else:
        # Use basic processing without spacy
        logger.warning("DEGRADED MODE: Using basic NLP (spacy not available)")
        # Must explicitly log degraded mode, no silent fallback
```

## Testing

Tests verify the lockdown behavior:

```python
import os
import pytest
from saaaaaa.core.dependency_lockdown import DependencyLockdownError, reset_dependency_lockdown

def test_offline_mode_enforced():
    """Verify offline mode is enforced by default."""
    reset_dependency_lockdown()
    
    from saaaaaa.core.dependency_lockdown import get_dependency_lockdown
    
    lockdown = get_dependency_lockdown()
    
    assert lockdown.hf_allowed is False
    assert os.getenv("HF_HUB_OFFLINE") == "1"
    assert os.getenv("TRANSFORMERS_OFFLINE") == "1"

def test_online_access_blocked_in_offline_mode():
    """Verify that online model access raises error in offline mode."""
    os.environ["HF_ONLINE"] = "0"
    reset_dependency_lockdown()
    
    from saaaaaa.core.dependency_lockdown import get_dependency_lockdown
    
    lockdown = get_dependency_lockdown()
    
    with pytest.raises(DependencyLockdownError) as exc:
        lockdown.check_online_model_access("test-model", "test operation")
    
    assert "Online model download disabled" in str(exc.value)
    assert "No fallback" in str(exc.value)
```

## Design Rationale

### Why Fail Fast?

Silent fallbacks create unpredictable behavior:
- Users don't know when they're in degraded mode
- Results may be silently lower quality
- Debugging is harder when failures are hidden
- Production deployments need predictable behavior

### Why Environment Variables?

- Simple, standard mechanism for configuration
- Works in all deployment environments (local, CI, containers)
- No code changes needed to switch modes
- Easy to set in deployment configurations

### Why No Default Online Mode?

- Prevents accidental network dependencies
- Forces explicit opt-in for downloads
- Prevents surprise downloads in production
- Aligns with principle of explicit configuration

## Migration Guide

If you have existing code that relied on automatic model downloads:

1. **Local development**: Set `HF_ONLINE=1` in your environment or `.env` file
2. **CI/CD**: Pre-download models and cache them, or set `HF_ONLINE=1` in CI
3. **Production**: Use cached models (recommended) or set `HF_ONLINE=1` if needed

Example CI configuration:

```yaml
# .github/workflows/test.yml
env:
  HF_ONLINE: 1  # Allow downloads in CI

jobs:
  test:
    steps:
      - name: Cache models
        uses: actions/cache@v3
        with:
          path: ~/.cache/huggingface
          key: hf-models-${{ hashFiles('requirements.txt') }}
      
      - name: Run tests
        env:
          HF_ONLINE: 0  # Use cached models, no downloads
        run: pytest
```

## Troubleshooting

### Error: "Online model download disabled"

**Solution 1**: Enable online mode
```bash
HF_ONLINE=1 python your_script.py
```

**Solution 2**: Pre-download models
```bash
# Download models once with online mode
HF_ONLINE=1 python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('model-name')"

# Then use offline mode
HF_ONLINE=0 python your_script.py
```

### Models Not Found Even When Cached

Check cache locations:
```bash
echo $HF_HOME
echo $TRANSFORMERS_CACHE
ls -la ~/.cache/huggingface/hub
```

Verify model is actually cached:
```bash
ls -la ~/.cache/huggingface/hub/ | grep "model-name"
```

## API Reference

### `DependencyLockdown`

Main class for dependency enforcement.

#### Methods

- `check_online_model_access(model_name: str, operation: str) -> None`
  - Raises `DependencyLockdownError` if HF_ONLINE=0
  
- `check_critical_dependency(module_name: str, pip_package: str, phase: str | None) -> None`
  - Raises `DependencyLockdownError` if dependency missing
  
- `check_optional_dependency(module_name: str, pip_package: str, feature: str) -> bool`
  - Returns `True` if available, `False` if missing (logs warning)
  
- `get_mode_description() -> dict`
  - Returns current lockdown configuration

### `get_dependency_lockdown()`

Returns the global singleton `DependencyLockdown` instance.

### `reset_dependency_lockdown()`

Resets the global instance (mainly for testing).

## See Also

- [HuggingFace Offline Mode Documentation](https://huggingface.co/docs/transformers/installation#offline-mode)
- [sentence-transformers Caching](https://www.sbert.net/docs/pretrained_models.html#offline-usage)
