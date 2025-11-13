# Core Module: Dependency Lockdown

This module enforces strict dependency management to prevent "magic" behavior
and ensure predictable, reproducible execution.

## Key Components

### `dependency_lockdown.py`

Provides environment-based control over:
- HuggingFace model downloads (via `HF_ONLINE` env var)
- Critical vs optional dependency checks
- Explicit error messages when dependencies are missing
- No silent fallback or degraded modes

## Usage in Other Modules

When importing transformer libraries, always initialize the lockdown first:

```python
# Import lockdown before importing transformers
from saaaaaa.core.dependency_lockdown import get_dependency_lockdown
_lockdown = get_dependency_lockdown()

# Now safe to import - lockdown has set offline mode if needed
from sentence_transformers import SentenceTransformer
from transformers import AutoModel
```

This ensures:
1. `HF_HUB_OFFLINE` and `TRANSFORMERS_OFFLINE` are set if `HF_ONLINE=0`
2. Model loading respects the offline mode
3. Clear errors if models need to be downloaded but can't be

## Integration Points

The dependency lockdown is integrated at:

1. **Orchestrator initialization** (`orchestrator/core.py`)
   - Creates lockdown instance on init
   - Logs current mode
   - Available as `orchestrator.dependency_lockdown`

2. **Embedding system** (`processing/embedding_policy.py`)
   - Checks before loading SentenceTransformer
   - Checks before loading CrossEncoder
   - Validates model cache before download attempt

3. **Analysis modules** (various in `analysis/`)
   - Initialize lockdown before transformer imports
   - Ensures offline mode is set at import time

## See Also

- `/DEPENDENCY_LOCKDOWN.md` - Full documentation
- `/examples/demo_dependency_lockdown.py` - Demo script
- `/tests/test_dependency_lockdown.py` - Test suite
