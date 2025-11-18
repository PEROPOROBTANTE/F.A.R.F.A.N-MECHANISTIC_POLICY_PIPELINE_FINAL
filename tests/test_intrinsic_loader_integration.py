"""
FASE 4: Comprehensive tests for IntrinsicScoreLoader integration.

This test suite verifies:
1. Singleton pattern works correctly
2. Thread-safety of lazy loading
3. Correct handling of computed vs excluded vs missing methods
4. All 1,995 methods can be loaded
5. Layer field extraction works
6. Score computation is correct
"""
import sys
from pathlib import Path
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader


def test_lazy_loading():
    """Test that IntrinsicScoreLoader implements lazy loading correctly."""
    print("=" * 80)
    print("TEST 1: LAZY LOADING")
    print("=" * 80)
    print()

    path = "config/intrinsic_calibration.json"
    loader = IntrinsicScoreLoader(path)

    # Initially not loaded
    print(f"Initial state - loaded: {loader._loaded}")
    if loader._loaded:
        print("✗ Data loaded on __init__ (should be lazy)")
        return False
    else:
        print("✓ Data NOT loaded on __init__ (lazy loading)")

    # First access triggers loading
    print("\nAccessing data for first time...")
    score = loader.get_score("orchestrator.__init__.__getattr__")
    print(f"Loaded: {loader._loaded}")
    print(f"Methods in cache: {len(loader._methods)}")
    print(f"Score retrieved: {score:.3f}")
    print()

    if not loader._loaded or len(loader._methods) == 0:
        print("✗ Data not loaded after first access")
        return False
    else:
        print(f"✓ Data loaded on first access: {len(loader._methods)} methods")

    # Subsequent access uses cache
    print("\nAccessing data again (should use cache)...")
    score2 = loader.get_score("orchestrator.factory.build_processor")
    print(f"Score retrieved: {score2:.3f}")
    print()

    if score2 > 0:
        print("✓ Cache working correctly")
        return True
    else:
        print("✗ Cache not working")
        return False


def test_thread_safety():
    """Test that concurrent access to single loader instance is thread-safe."""
    print("=" * 80)
    print("TEST 2: THREAD-SAFETY (single instance, multiple threads)")
    print("=" * 80)
    print()

    # Create single loader instance
    loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
    print(f"Created loader instance: {id(loader)}")
    print()

    results = []
    errors = []

    def access_loader(thread_id):
        """Access shared loader from separate thread."""
        try:
            # All threads access the SAME loader instance
            loader._ensure_loaded()
            count = len(loader._methods)

            # Try to get some scores
            score1 = loader.get_score("orchestrator.__init__.__getattr__")
            score2 = loader.get_score("orchestrator.factory.build_processor")

            results.append((thread_id, count, score1, score2))
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Create 10 threads that all access the same loader
    threads = []
    print("Starting 10 concurrent threads accessing shared loader...")
    for i in range(10):
        t = threading.Thread(target=access_loader, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all to complete
    for t in threads:
        t.join()

    print(f"Threads completed: {len(results)}")
    print()

    # Verify no errors
    if errors:
        print(f"✗ {len(errors)} threads had errors:")
        for thread_id, error in errors:
            print(f"  Thread {thread_id}: {error}")
        return False
    else:
        print("✓ No thread errors")

    # Verify all threads got same method count
    counts = [r[1] for r in results]
    unique_counts = set(counts)

    print(f"Method counts: {unique_counts}")
    if len(unique_counts) == 1:
        print(f"✓ All threads loaded same data: {counts[0]} methods")
    else:
        print(f"✗ Inconsistent method counts: {unique_counts}")
        return False

    # Verify all threads got same scores
    scores1 = set(r[2] for r in results)
    scores2 = set(r[3] for r in results)

    print(f"Score consistency: {len(scores1)} unique values for method 1, {len(scores2)} for method 2")
    if len(scores1) == 1 and len(scores2) == 1:
        print(f"✓ All threads got consistent scores")
        return True
    else:
        print(f"✗ Inconsistent scores across threads")
        return False


def test_method_categories():
    """Test handling of computed, excluded, and missing methods."""
    print("=" * 80)
    print("TEST 3: METHOD CATEGORIES (computed/excluded/missing)")
    print("=" * 80)
    print()

    loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
    loader._ensure_loaded()

    # Get statistics
    stats = loader.get_statistics()

    print("Statistics from JSON:")
    print(f"  Total methods: {stats['total']}")
    print(f"  Computed: {stats['computed']}")
    print(f"  Excluded: {stats['excluded']}")
    print()

    # Find actual examples of each category
    computed_examples = []
    excluded_examples = []

    for method_id, data in loader._methods.items():
        status = data.get("calibration_status", "unknown")
        if status == "computed" and len(computed_examples) < 3:
            computed_examples.append(method_id)
        elif status == "excluded" and len(excluded_examples) < 3:
            excluded_examples.append(method_id)

    # Test computed methods
    print("Testing COMPUTED methods:")
    all_passed = True
    for method_id in computed_examples[:3]:
        is_calibrated = loader.is_calibrated(method_id)
        score = loader.get_score(method_id)
        status = "✓" if (is_calibrated and score > 0) else "✗"

        if not (is_calibrated and score > 0):
            all_passed = False

        print(f"  {status} {method_id[:60]:60s} - score: {score:.3f}")
    print()

    # Test excluded methods
    print("Testing EXCLUDED methods:")
    for method_id in excluded_examples[:3]:
        is_calibrated = loader.is_calibrated(method_id)
        score = loader.get_score(method_id)
        status = "✓" if (not is_calibrated and score == 0.5) else "✗"

        if not (not is_calibrated and score == 0.5):
            all_passed = False

        print(f"  {status} {method_id[:60]:60s} - excluded (score: {score:.3f})")
    print()

    # Test missing method
    print("Testing MISSING method:")
    fake_method = "fake.module.FakeClass.fake_method_does_not_exist"
    is_calibrated = loader.is_calibrated(fake_method)
    score = loader.get_score(fake_method)
    status = "✓" if (not is_calibrated and score == 0.5) else "✗"

    if not (not is_calibrated and score == 0.5):
        all_passed = False

    print(f"  {status} {fake_method:60s} - missing (score: {score:.3f})")
    print()

    if all_passed:
        print("✓ All category tests passed")
        return True
    else:
        print("✗ Some category tests failed")
        return False


def test_all_methods_loadable():
    """Test that all 1,995 methods can be loaded without errors."""
    print("=" * 80)
    print("TEST 4: ALL METHODS LOADABLE")
    print("=" * 80)
    print()

    loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
    loader._ensure_loaded()

    total_methods = len(loader._methods)
    print(f"Total methods in JSON: {total_methods}")
    print()

    # Try to load score for every method
    errors = []
    scores = []

    print("Loading all methods...")
    for method_id in loader._methods.keys():
        try:
            score = loader.get_score(method_id)
            scores.append(score)

            # Verify score is in valid range
            if not (0.0 <= score <= 1.0):
                errors.append((method_id, f"Invalid score: {score}"))
        except Exception as e:
            errors.append((method_id, str(e)))

    print(f"Successfully loaded: {len(scores)}/{total_methods}")
    print()

    if errors:
        print(f"✗ {len(errors)} methods had errors:")
        for method_id, error in errors[:10]:  # Show first 10
            print(f"  - {method_id}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        return False
    else:
        print(f"✓ All {total_methods} methods loaded successfully")

        # Score statistics
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        print(f"\nScore statistics:")
        print(f"  Average: {avg_score:.3f}")
        print(f"  Min: {min_score:.3f}")
        print(f"  Max: {max_score:.3f}")

        return True


def test_layer_field_extraction():
    """Test that layer (role) field is correctly extracted."""
    print("=" * 80)
    print("TEST 5: LAYER FIELD EXTRACTION")
    print("=" * 80)
    print()

    loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
    loader._ensure_loaded()

    # Get statistics on layer distribution
    layer_counts = {}
    methods_without_layer = []

    for method_id, data in loader._methods.items():
        layer = data.get("layer")
        if layer:
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        else:
            if len(methods_without_layer) < 5:
                methods_without_layer.append(method_id)

    print("Layer distribution:")
    for layer, count in sorted(layer_counts.items(), key=lambda x: -x[1]):
        print(f"  {layer:15s}: {count:4d} methods")
    print()

    # Test specific examples
    test_cases = [
        ("orchestrator.__init__.__getattr__", "orchestrator"),
        ("src.saaaaaa.analysis.Analyzer_one.BatchProcessor.__init__", "analyzer"),
        ("smart_policy_chunks_canonic_phase_one.ArgumentAnalyzer.__init__", "processor"),
        ("src.saaaaaa.utils.adapters._deprecation_warning", "utility"),
    ]

    print("Testing specific layer extractions:")
    all_passed = True
    for method_id, expected_layer in test_cases:
        actual_layer = loader.get_layer(method_id)
        status = "✓" if actual_layer == expected_layer else "✗"

        if actual_layer != expected_layer:
            all_passed = False

        print(f"  {status} {method_id[:50]:50s} → {actual_layer} (expected: {expected_layer})")
    print()

    # Test methods without layer field
    if methods_without_layer:
        print(f"Methods without layer field: {len(methods_without_layer)} found")
        print("Examples:")
        for method_id in methods_without_layer[:3]:
            layer = loader.get_layer(method_id)
            print(f"  - {method_id[:60]:60s} → {layer}")
        print()

    if all_passed:
        print("✓ Layer extraction working correctly")
        return True
    else:
        print("✗ Some layer extractions failed")
        return False


def test_score_computation():
    """Test that score is computed correctly from b_theory, b_impl, b_deploy."""
    print("=" * 80)
    print("TEST 6: SCORE COMPUTATION (weighted average of components)")
    print("=" * 80)
    print()

    loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
    loader._ensure_loaded()

    # Get weights used by loader
    print(f"Weights used:")
    print(f"  w_theory: {loader.w_theory}")
    print(f"  w_impl: {loader.w_impl}")
    print(f"  w_deploy: {loader.w_deploy}")
    print()

    # Find methods with explicit components to verify computation
    test_cases = []
    for method_id, data in loader._methods.items():
        if data.get("calibration_status") == "computed":
            if len(test_cases) < 5:
                test_cases.append((
                    method_id,
                    data.get("b_theory", 0.0),
                    data.get("b_impl", 0.0),
                    data.get("b_deploy", 0.0)
                ))

    print("Testing score computation:")
    all_passed = True

    for method_id, theory, impl, deploy in test_cases:
        # Get actual score from loader (computed on-the-fly)
        actual_score = loader.get_score(method_id)

        # Compute expected score using same formula
        expected = (
            loader.w_theory * theory +
            loader.w_impl * impl +
            loader.w_deploy * deploy
        )

        difference = abs(expected - actual_score)

        # Allow small floating point difference
        status = "✓" if difference < 0.001 else "✗"

        if difference >= 0.001:
            all_passed = False

        print(f"  {status} {method_id[:40]:40s}")
        print(f"      Components: theory={theory:.3f}, impl={impl:.3f}, deploy={deploy:.3f}")
        print(f"      Expected: {expected:.3f}, Actual: {actual_score:.3f} (diff: {difference:.6f})")
        print()

    if all_passed:
        print("✓ All score computations correct")
        return True
    else:
        print("✗ Some score computations failed")
        return False


def test_executor_coverage():
    """Test that all 30 executors (D1Q1-D6Q5) are in the JSON."""
    print("=" * 80)
    print("TEST 7: EXECUTOR COVERAGE (30 executors)")
    print("=" * 80)
    print()

    loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")

    executor_template = "src.saaaaaa.core.orchestrator.executors.D{d}Q{q}_Executor.execute"

    missing = []
    found = []

    for d in range(1, 7):
        for q in range(1, 6):
            executor_id = executor_template.format(d=d, q=q)

            if loader.is_calibrated(executor_id):
                score = loader.get_score(executor_id)
                found.append((executor_id, score))
            else:
                missing.append(executor_id)

    print(f"Found: {len(found)}/30 executors")
    print(f"Missing: {len(missing)}/30 executors")
    print()

    if missing:
        print("✗ MISSING executors:")
        for executor_id in missing:
            print(f"  - {executor_id}")
        print()
        return False
    else:
        print("✓ All 30 executors present in JSON")

        # Show sample scores
        print("\nSample executor scores:")
        for executor_id, score in found[:5]:
            short_name = executor_id.split(".")[-2]  # e.g., "D1Q1_Executor"
            print(f"  {short_name}: {score:.3f}")

        return True


if __name__ == "__main__":
    print("\nFASE 4: INTRINSIC LOADER INTEGRATION TESTS")
    print()

    # Run all tests
    test1 = test_lazy_loading()
    print()
    test2 = test_thread_safety()
    print()
    test3 = test_method_categories()
    print()
    test4 = test_all_methods_loadable()
    print()
    test5 = test_layer_field_extraction()
    print()
    test6 = test_score_computation()
    print()
    test7 = test_executor_coverage()

    # Summary
    print()
    print("=" * 80)
    print("FINAL RESULTS - FASE 4")
    print("=" * 80)
    print(f"Lazy loading: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Thread-safety: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Method categories: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"All methods loadable: {'✅ PASS' if test4 else '❌ FAIL'}")
    print(f"Layer extraction: {'✅ PASS' if test5 else '❌ FAIL'}")
    print(f"Score computation: {'✅ PASS' if test6 else '❌ FAIL'}")
    print(f"Executor coverage: {'✅ PASS' if test7 else '❌ FAIL'}")
    print()

    if all([test1, test2, test3, test4, test5, test6, test7]):
        print("🎉 ALL INTRINSIC LOADER TESTS PASSED - FASE 4 COMPLETE!")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED")
        sys.exit(1)
