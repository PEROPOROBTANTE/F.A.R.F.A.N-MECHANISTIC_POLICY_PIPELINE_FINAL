# Orchestrator Compatibility Layer

⚠️ **This directory contains ONLY compatibility shims for backward compatibility.**

## Real Implementation

The actual orchestrator implementation is located at:
```
src/saaaaaa/core/orchestrator/
```

All orchestration-related code is consolidated in that ONE location.

## What's in This Directory?

This directory contains thin compatibility shims that redirect imports to the real implementation:

| File | Purpose | Redirects To |
|------|---------|-------------|
| `__init__.py` | Main orchestrator API | `src/saaaaaa/core/orchestrator/` |
| `choreographer_dispatch.py` | Dispatcher component | `src/saaaaaa/core/orchestrator/choreographer.py` |
| `executors.py` | Executor utilities | `src/saaaaaa/core/orchestrator/executors.py` |
| `arg_router.py` | Argument routing | `src/saaaaaa/core/orchestrator/arg_router.py` |
| `factory.py` | Component factories | `src/saaaaaa/core/orchestrator/factory.py` |
| `provider.py` | Configuration providers | Local implementation (to be migrated) |
| `settings.py` | Settings | Local implementation (to be migrated) |

## For New Code

**DO NOT** import from this directory. Instead, import from:
```python
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.choreographer import Choreographer, ChoreographerDispatcher
from saaaaaa.core.orchestrator.executors import MethodExecutor
```

## Migration Path

Old code (still works):
```python
from orchestrator import Orchestrator
from orchestrator.choreographer_dispatch import ChoreographerDispatcher
```

New code (preferred):
```python
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.choreographer import Choreographer, ChoreographerDispatcher
```

## See Also

- `PROJECT_STRUCTURE.md` - Complete repository structure documentation
- `src/saaaaaa/core/orchestrator/` - Real orchestrator implementation
