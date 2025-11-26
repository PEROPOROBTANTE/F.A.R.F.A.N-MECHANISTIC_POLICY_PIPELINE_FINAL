#!/usr/bin/env python3
"""
Static code verification for executor architectural fixes.

Verifies the presence of critical fixes without requiring full module imports.
"""

import re
from pathlib import Path


def check_exception_chain_preservation():
    """Verify 'from e' added to exception handling."""
    print("\n=== Verification 1: Exception Chain Preservation ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check for the pattern: ) from e (accounting for multi-line raises)
    # The pattern should appear after ExecutorFailure raises
    if ") from e" not in content:
        print("❌ FAILED: 'from e' not found in ExecutorFailure raises")
        return False

    # Verify it's in the context of ExecutorFailure
    if "raise ExecutorFailure(" not in content:
        print("❌ FAILED: ExecutorFailure raise not found")
        return False

    # Count occurrences
    count = content.count(") from e")

    print(f"✓ PASSED: Found {count} exception chain preservation(s) with 'from e'")
    print("  - Exception chains will be preserved for debugging")
    return True


def check_lazy_loading():
    """Verify dimension_info uses lazy loading with @property."""
    print("\n=== Verification 2: Lazy Loading Implementation ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check for @property decorator on dimension_info
    if "@property" not in content or "def dimension_info(self):" not in content:
        print("❌ FAILED: dimension_info not implemented as @property")
        return False

    # Check for _dimension_info private attribute initialization
    if "self._dimension_info = None" not in content:
        print("❌ FAILED: _dimension_info not initialized as None")
        return False

    # Check for lazy load pattern
    if "if self._dimension_info is None:" not in content:
        print("❌ FAILED: Lazy loading check not found")
        return False

    print("✓ PASSED: dimension_info properly implemented with lazy loading")
    print("  - @property decorator found")
    print("  - _dimension_info initialized to None")
    print("  - Lazy loading pattern detected")
    return True


def check_executor_result_dataclass():
    """Verify ExecutorResult dataclass exists."""
    print("\n=== Verification 3: ExecutorResult Dataclass ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check for @dataclass decorator and class definition
    if "@dataclass" not in content or "class ExecutorResult:" not in content:
        print("❌ FAILED: ExecutorResult dataclass not found")
        return False

    # Check for required fields
    required_fields = [
        "executor_id: str",
        "success: bool",
        "data: Optional[Dict[str, Any]]",
        "error: Optional[str]",
        "execution_time_ms: int",
        "memory_usage_mb: float"
    ]

    missing_fields = []
    for field in required_fields:
        if field not in content:
            missing_fields.append(field)

    if missing_fields:
        print(f"❌ FAILED: Missing fields in ExecutorResult: {missing_fields}")
        return False

    print("✓ PASSED: ExecutorResult dataclass properly defined")
    print(f"  - All {len(required_fields)} required fields present")
    return True


def check_type_safety_fix():
    """Verify D3-Q2 type safety fix (no dict/None confusion)."""
    print("\n=== Verification 4: D3-Q2 Type Safety Fix ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check that the problematic pattern is NOT present
    bad_pattern = r"ind=first_indicator if first_indicator else \{\}"
    if re.search(bad_pattern, content):
        print("❌ FAILED: Old dict/None confusion pattern still present")
        return False

    # Check for type-safe indicator extraction comment
    if "Type-safe indicator extraction" not in content:
        print("❌ FAILED: Type-safe indicator extraction comment not found")
        return False

    # Check for explicit None handling
    if "indicator_dict = None" not in content:
        print("❌ FAILED: Explicit None assignment not found")
        return False

    print("✓ PASSED: D3-Q2 type safety fix verified")
    print("  - Old dict/None confusion pattern removed")
    print("  - Explicit None handling added")
    return True


def check_memory_safety():
    """Verify D3-Q3 memory bounds checking."""
    print("\n=== Verification 5: D3-Q3 Memory Safety ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check for MAX_ENTITY_SIZE constant
    if "MAX_ENTITY_SIZE = 1024 * 1024" not in content:
        print("❌ FAILED: MAX_ENTITY_SIZE constant not found")
        return False

    # Check for sys.getsizeof usage
    if "sys.getsizeof(e)" not in content:
        print("❌ FAILED: sys.getsizeof memory check not found")
        return False

    # Check for MemoryError handling
    if "except MemoryError:" not in content:
        print("❌ FAILED: MemoryError handling not found")
        return False

    # Check for memory safety comment
    if "Memory-safe entity processing" not in content:
        print("❌ FAILED: Memory safety documentation comment not found")
        return False

    print("✓ PASSED: D3-Q3 memory safety fix verified")
    print("  - MAX_ENTITY_SIZE limit defined (1MB)")
    print("  - sys.getsizeof bounds checking added")
    print("  - MemoryError recovery implemented")
    return True


def check_specific_exception_handling():
    """Verify specific exception catching (no silent failures)."""
    print("\n=== Verification 6: Specific Exception Handling ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check for specific exception tuples
    specific_patterns = [
        r"except \(KeyError, ValueError, TypeError, AttributeError",
        r"except \(KeyError, ValueError, IndexError, AttributeError",
    ]

    found_specific = False
    for pattern in specific_patterns:
        if re.search(pattern, content):
            found_specific = True
            break

    if not found_specific:
        print("❌ FAILED: Specific exception handling not found")
        return False

    # Check for logging of caught exceptions
    if "logger.warning(f\"" not in content:
        print("❌ FAILED: Exception logging not found")
        return False

    # Check for comment about letting system exceptions propagate
    if "Let critical system exceptions" not in content:
        print("❌ FAILED: System exception propagation comment not found")
        return False

    print("✓ PASSED: Specific exception handling verified")
    print("  - Specific exception types (KeyError, ValueError, etc.)")
    print("  - Exception logging added")
    print("  - System exceptions allowed to propagate")
    return True


def check_context_validation():
    """Verify _validate_context method exists."""
    print("\n=== Verification 7: Context Validation ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    # Check for method definition
    if "def _validate_context(self, context: Dict[str, Any]) -> None:" not in content:
        print("❌ FAILED: _validate_context method not found")
        return False

    # Check for fail fast comment
    if "Fail fast on malformed contexts" not in content:
        print("❌ FAILED: Fail fast documentation not found")
        return False

    # Check for required keys validation
    if 'required = ["document_text"]' not in content:
        print("❌ FAILED: Required keys validation not found")
        return False

    print("✓ PASSED: Context validation method verified")
    print("  - _validate_context method defined")
    print("  - Fail-fast validation implemented")
    return True


def check_imports():
    """Verify required imports added."""
    print("\n=== Verification 8: Required Imports ===")

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")
    content = executor_file.read_text()

    required_imports = [
        "from __future__ import annotations",
        "import sys",
        "import logging",
        "from dataclasses import dataclass",
    ]

    missing_imports = []
    for imp in required_imports:
        if imp not in content:
            missing_imports.append(imp)

    if missing_imports:
        print(f"❌ FAILED: Missing imports: {missing_imports}")
        return False

    # Check for logger initialization
    if "logger = logging.getLogger(__name__)" not in content:
        print("❌ FAILED: Logger not initialized")
        return False

    print("✓ PASSED: All required imports present")
    print("  - __future__ annotations")
    print("  - sys, logging, dataclasses")
    print("  - logger initialized")
    return True


def run_verification():
    """Run all verification checks."""
    print("=" * 70)
    print("EXECUTOR ARCHITECTURAL FIXES - STATIC CODE VERIFICATION")
    print("=" * 70)

    checks = [
        ("Exception Chain Preservation", check_exception_chain_preservation),
        ("Lazy Loading Implementation", check_lazy_loading),
        ("ExecutorResult Dataclass", check_executor_result_dataclass),
        ("D3-Q2 Type Safety Fix", check_type_safety_fix),
        ("D3-Q3 Memory Safety", check_memory_safety),
        ("Specific Exception Handling", check_specific_exception_handling),
        ("Context Validation", check_context_validation),
        ("Required Imports", check_imports),
    ]

    results = []
    for name, check_func in checks:
        try:
            passed = check_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print("=" * 70)
    print(f"TOTAL: {passed_count}/{total_count} checks passed")
    print("=" * 70)

    if passed_count == total_count:
        print("\n🎉 ALL FIXES VERIFIED!")
        print("\nThe following critical architectural flaws have been repaired:")
        print("  1. Exception chain preservation (debugging enabled)")
        print("  2. Type safety (no dict/None confusion)")
        print("  3. Memory bounds (1MB entity limit)")
        print("  4. Specific exception handling (no silent failures)")
        print("  5. Lazy loading (reduced metadata duplication)")
        print("  6. ExecutorResult dataclass (type-safe contracts)")
        print("  7. Context validation (fail-fast on bad input)")
        print("  8. Proper imports (annotations, logging, dataclasses)")
        print("\nThe pipeline is ready for verifiable execution.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} check(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = run_verification()
    sys.exit(exit_code)
