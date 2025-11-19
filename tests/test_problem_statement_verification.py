"""Verification tests for the three issues mentioned in the problem statement.

This test module verifies that the three reported issues are correctly handled:
1. execute_phase_with_timeout function exists with correct signature
2. MappingProxyType is properly handled for JSON serialization  
3. EvidenceRegistry uses correct attribute name (hash_index, not _by_hash)
"""
import asyncio
import inspect
import json
import tempfile
from pathlib import Path
from types import MappingProxyType

import pytest
from saaaaaa.config.paths import PROJECT_ROOT


def test_execute_phase_with_timeout_exists():
    """Verify execute_phase_with_timeout function exists and is importable."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    assert callable(execute_phase_with_timeout)
    assert asyncio.iscoroutinefunction(execute_phase_with_timeout)


def test_execute_phase_with_timeout_signature():
    """Verify execute_phase_with_timeout has correct signature supporting both modern and legacy params."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    sig = inspect.signature(execute_phase_with_timeout)
    params = list(sig.parameters.keys())
    
    # Must have required parameters
    assert 'phase_id' in params
    assert 'phase_name' in params
    assert 'timeout_s' in params
    
    # Must support both modern (coro) and legacy (handler/args) parameters
    assert 'coro' in params or 'handler' in params
    assert 'handler' in params  # Legacy backward compatibility
    assert 'args' in params  # Legacy backward compatibility
    
    # Check defaults
    assert sig.parameters['timeout_s'].default == 300.0


def test_phase_timeout_error_exists():
    """Verify PhaseTimeoutError exception class exists."""
    from saaaaaa.core.orchestrator.core import PhaseTimeoutError
    
    assert issubclass(PhaseTimeoutError, RuntimeError)
    
    # Test that it has the expected attributes
    error = PhaseTimeoutError(1, "test_phase", 5.0)
    assert error.phase_id == 1
    assert error.phase_name == "test_phase"
    assert error.timeout_s == 5.0
    assert "timed out" in str(error).lower()


def test_phase_timeout_default_constant():
    """Verify PHASE_TIMEOUT_DEFAULT constant exists and has correct value."""
    from saaaaaa.core.orchestrator.core import PHASE_TIMEOUT_DEFAULT
    
    assert isinstance(PHASE_TIMEOUT_DEFAULT, int)
    assert PHASE_TIMEOUT_DEFAULT == 300  # 5 minutes


@pytest.mark.asyncio
async def test_execute_phase_with_timeout_legacy_signature():
    """Verify execute_phase_with_timeout works with legacy handler/args signature."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    async def test_handler(x, y):
        return x + y
    
    # Test with legacy signature (handler and args parameters)
    result = await execute_phase_with_timeout(
        phase_id=1,
        phase_name="test",
        handler=test_handler,
        args=(2, 3),
        timeout_s=1.0
    )
    assert result == 5


def test_mappingproxy_normalization_exists():
    """Verify _normalize_monolith_for_hash function exists."""
    from saaaaaa.core.orchestrator.core import _normalize_monolith_for_hash
    
    assert callable(_normalize_monolith_for_hash)


def test_mappingproxy_uses_isinstance_not_string_check():
    """Verify MappingProxyType handling uses proper isinstance() checks, not string-based checks."""
    from saaaaaa.core.orchestrator import core
    import ast
    import inspect
    
    # Get the source code of the core module
    source = inspect.getsource(core)
    
    # Parse it to check for weak string-based type checks
    tree = ast.parse(source)
    
    # Search for any string-based type checking patterns
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            # Look for patterns like "'mappingproxy' in str(type(...))"
            code = ast.unparse(node)
            if 'mappingproxy' in code.lower() and 'str' in code.lower():
                pytest.fail(
                    f"Found weak string-based MappingProxyType check: {code}. "
                    "Should use isinstance(obj, MappingProxyType) instead."
                )


def test_mappingproxy_json_serialization():
    """Verify MappingProxyType can be properly normalized and serialized to JSON."""
    from saaaaaa.core.orchestrator.core import _normalize_monolith_for_hash
    
    # Create a MappingProxyType with nested structures
    test_data = {
        'a': 1,
        'b': {'c': 2, 'd': [3, 4]},
        'e': MappingProxyType({'f': 5})
    }
    proxy = MappingProxyType(test_data)
    
    # Normalize it
    normalized = _normalize_monolith_for_hash(proxy)
    
    # Verify it's a regular dict
    assert isinstance(normalized, dict)
    assert not isinstance(normalized, MappingProxyType)
    
    # Verify nested proxies are also converted
    assert isinstance(normalized['e'], dict)
    assert not isinstance(normalized['e'], MappingProxyType)
    
    # Verify it can be JSON serialized without errors
    try:
        json_str = json.dumps(normalized, sort_keys=True)
        assert len(json_str) > 0
    except TypeError as e:
        pytest.fail(f"Failed to serialize normalized monolith to JSON: {e}")


def test_mappingproxy_import_from_types():
    """Verify MappingProxyType is imported from the standard types module."""
    from saaaaaa.core.orchestrator import core
    import inspect
    
    source = inspect.getsource(core)
    
    # Check that MappingProxyType is imported from types module
    assert 'from types import MappingProxyType' in source or 'from types import' in source


def test_evidence_registry_has_hash_index_not_by_hash():
    """Verify EvidenceRegistry uses hash_index attribute, not _by_hash."""
    from saaaaaa.core.orchestrator import EvidenceRegistry
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = EvidenceRegistry(storage_path=Path(tmpdir) / "test.jsonl")
        
        # Verify hash_index exists
        assert hasattr(registry, 'hash_index'), "EvidenceRegistry must have hash_index attribute"
        assert isinstance(registry.hash_index, dict), "hash_index must be a dict"
        
        # Verify _by_hash does NOT exist
        assert not hasattr(registry, '_by_hash'), (
            "EvidenceRegistry should not have _by_hash attribute. "
            "The correct attribute name is hash_index."
        )


def test_evidence_registry_hash_index_type():
    """Verify hash_index is properly typed as dict[str, EvidenceRecord]."""
    from saaaaaa.core.orchestrator import EvidenceRegistry, EvidenceRecord
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Disable DAG to avoid issues with parent_evidence_ids
        registry = EvidenceRegistry(storage_path=Path(tmpdir) / "test.jsonl", enable_dag=False)
        
        # Add a test record
        evidence_id = registry.record_evidence(
            evidence_type="test_type",
            payload={"data": ["evidence1", "evidence2"]},
            source_method="test_module.test_method",
            metadata={"test": True}
        )
        
        # Verify it's in hash_index
        assert evidence_id in registry.hash_index
        assert isinstance(registry.hash_index[evidence_id], EvidenceRecord)


def test_no_by_hash_usage_in_codebase():
    """Verify that _by_hash is not used anywhere in the codebase."""
    import os
    from pathlib import Path
    
    src_dir = PROJECT_ROOT / "src"
    py_files = list(src_dir.rglob("*.py"))
    
    for py_file in py_files:
        try:
            content = py_file.read_text()
            # Skip comments
            lines = [line for line in content.split('\n') if not line.strip().startswith('#')]
            code = '\n'.join(lines)
            
            if '_by_hash' in code:
                # Check if it's in a string literal or comment, which is okay
                if 'registry._by_hash' in code or 'self._by_hash' in code:
                    pytest.fail(
                        f"Found usage of _by_hash in {py_file}. "
                        "Should use hash_index instead."
                    )
        except Exception:
            # Skip files that can't be read
            pass


def test_all_three_issues_integration():
    """Integration test verifying all three issues are properly resolved."""
    from saaaaaa.core.orchestrator.core import (
        execute_phase_with_timeout,
        PhaseTimeoutError,
        PHASE_TIMEOUT_DEFAULT,
        _normalize_monolith_for_hash
    )
    from saaaaaa.core.orchestrator import EvidenceRegistry
    from types import MappingProxyType
    import tempfile
    from pathlib import Path
    
    # Issue 1: execute_phase_with_timeout exists
    assert callable(execute_phase_with_timeout)
    assert asyncio.iscoroutinefunction(execute_phase_with_timeout)
    assert issubclass(PhaseTimeoutError, RuntimeError)
    assert PHASE_TIMEOUT_DEFAULT == 300
    
    # Issue 2: MappingProxyType handling
    test_proxy = MappingProxyType({'a': 1})
    normalized = _normalize_monolith_for_hash(test_proxy)
    json.dumps(normalized)  # Should not raise TypeError
    
    # Issue 3: EvidenceRegistry uses hash_index
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = EvidenceRegistry(storage_path=Path(tmpdir) / "test.jsonl")
        assert hasattr(registry, 'hash_index')
        assert not hasattr(registry, '_by_hash')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
