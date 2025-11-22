import sys


def test_orchestrator_imports_clean():
    # Clear cached orchestrator modules to simulate fresh import
    mods_to_clear = [m for m in list(sys.modules) if m.startswith("saaaaaa.core.orchestrator")]
    for m in mods_to_clear:
        sys.modules.pop(m, None)

    import saaaaaa.core.orchestrator  # noqa: F401
    from saaaaaa.core.orchestrator.core import (
        MethodExecutor,
        Orchestrator,
        PhaseResult,
        PreprocessedDocument,
    )
    from saaaaaa.core.orchestrator.base_executor_with_contract import BaseExecutorWithContract

    assert Orchestrator is not None
    assert PhaseResult is not None
    assert MethodExecutor is not None
    assert PreprocessedDocument is not None
    assert BaseExecutorWithContract is not None

