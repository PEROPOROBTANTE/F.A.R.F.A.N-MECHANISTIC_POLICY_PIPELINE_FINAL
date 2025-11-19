#!/usr/bin/env python3
"""
Verify Signal Loading and Integration

This script verifies that:
1. Signal packs are loaded correctly from questionnaire_monolith.json
2. Each policy area has sufficient patterns (minimum 50)
3. Signal pack versions are correct
4. SignalRegistry and SignalClient are functional
5. All 10 policy areas can be retrieved

Usage:
    python scripts/verify_signals.py
    
Exit Codes:
    0: All verifications passed
    1: One or more verifications failed
"""

import json
import sys
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent.parent

from saaaaaa.core.orchestrator.signals import SignalRegistry, SignalClient, InMemorySignalSource
from saaaaaa.core.orchestrator.signal_loader import (
    build_signal_pack_from_monolith,
    build_all_signal_packs,
)
from saaaaaa.core.orchestrator.questionnaire import load_questionnaire


def verify_monolith_loading():
    """Verify questionnaire monolith can be loaded via canonical loader."""
    print("=" * 70)
    print("TEST 1: Verify Questionnaire Monolith Loading (Canonical Loader)")
    print("=" * 70)

    try:
        canonical = load_questionnaire()
        questions = canonical.data.get('blocks', {}).get('micro_questions', [])

        if len(questions) != 300:
            print(f"❌ FAIL: Expected 300 questions, got {len(questions)}")
            return False

        print(f"✓ Loaded questionnaire with {len(questions)} questions")
        print(f"✓ Hash verified: {canonical.sha256[:16]}...")
        return True

    except Exception as e:
        print(f"❌ FAIL: Could not load questionnaire: {e}")
        return False


def verify_signal_pack_building():
    """Verify signal packs can be built for all policy areas."""
    print("\n" + "=" * 70)
    print("TEST 2: Verify Signal Pack Building")
    print("=" * 70)

    errors = []
    canonical = load_questionnaire()

    # Test building all packs using canonical questionnaire
    try:
        all_packs = build_all_signal_packs(questionnaire=canonical)
        
        if len(all_packs) != 10:
            errors.append(f"Expected 10 policy areas, got {len(all_packs)}")
        
        print(f"✓ Built {len(all_packs)} signal packs")
        
        # Verify each policy area
        for pa in [f"PA{i:02d}" for i in range(1, 11)]:
            if pa not in all_packs:
                errors.append(f"Policy area {pa} not in built packs")
                continue
            
            pack = all_packs[pa]
            
            # Check version format
            if pack.version != "1.0.0":
                errors.append(f"{pa}: Version should be 1.0.0, got {pack.version}")
            
            # Check minimum patterns
            total_patterns = len(pack.patterns) + len(pack.indicators) + len(pack.regex)
            if total_patterns < 50:
                errors.append(
                    f"{pa}: Only {total_patterns} total patterns (minimum: 50)"
                )
            
            print(f"  ✓ {pa}: {len(pack.patterns)} patterns, "
                  f"{len(pack.indicators)} indicators, "
                  f"{len(pack.regex)} regex")
        
        if errors:
            for err in errors:
                print(f"  ❌ {err}")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ FAIL: Could not build signal packs: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_signal_registry():
    """Verify SignalRegistry functionality."""
    print("\n" + "=" * 70)
    print("TEST 3: Verify Signal Registry")
    print("=" * 70)
    
    try:
        monolith = load_questionnaire_monolith()
        
        # Create memory source
        memory_source = InMemorySignalSource()
        
        # Load all packs
        all_packs = build_all_signal_packs(monolith)
        for pa_code, pack in all_packs.items():
            memory_source.register(pa_code, pack)
        
        print(f"✓ Registered {len(all_packs)} signal packs in memory source")
        
        # Create client
        client = SignalClient(base_url="memory://", memory_source=memory_source)
        print("✓ Created SignalClient with memory:// transport")
        
        # Create registry
        registry = SignalRegistry(max_size=100, default_ttl_s=86400)
        
        # Pre-populate registry
        for pa in [f"PA{i:02d}" for i in range(1, 11)]:
            pack = client.fetch_signal_pack(pa)
            if not pack:
                print(f"❌ FAIL: Could not fetch signal pack for {pa}")
                return False
            registry.put(pa, pack)
        
        print(f"✓ Pre-populated registry with {len(registry._cache)} policy areas")
        
        # Test retrieval
        errors = []
        for pa in [f"PA{i:02d}" for i in range(1, 11)]:
            pack = registry.get(pa)
            if not pack:
                errors.append(f"Could not retrieve {pa} from registry")
            else:
                print(f"  ✓ Retrieved {pa}: {len(pack.patterns)} patterns")
        
        # Check metrics
        metrics = registry.get_metrics()
        print(f"\nRegistry Metrics:")
        print(f"  - Size: {metrics['size']}/{metrics['capacity']}")
        print(f"  - Hit rate: {metrics['hit_rate']:.2%}")
        print(f"  - Hits: {metrics['hits']}")
        print(f"  - Misses: {metrics['misses']}")
        
        if errors:
            for err in errors:
                print(f"❌ {err}")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ FAIL: Signal registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_pattern_counts():
    """Verify total pattern counts across all policy areas."""
    print("\n" + "=" * 70)
    print("TEST 4: Verify Pattern Counts")
    print("=" * 70)
    
    try:
        monolith = load_questionnaire_monolith()
        all_packs = build_all_signal_packs(monolith)
        
        total_patterns = sum(len(p.patterns) for p in all_packs.values())
        total_indicators = sum(len(p.indicators) for p in all_packs.values())
        total_regex = sum(len(p.regex) for p in all_packs.values())
        total_entities = sum(len(p.entities) for p in all_packs.values())
        
        print(f"Total across all policy areas:")
        print(f"  - Patterns: {total_patterns}")
        print(f"  - Indicators: {total_indicators}")
        print(f"  - Regex: {total_regex}")
        print(f"  - Entities: {total_entities}")
        print(f"  - Grand Total: {total_patterns + total_indicators + total_regex}")
        
        # Check minimums
        if total_patterns < 1000:
            print(f"❌ FAIL: Total patterns {total_patterns} < 1000")
            return False
        
        if total_indicators < 100:
            print(f"❌ FAIL: Total indicators {total_indicators} < 100")
            return False
        
        print("✓ Pattern counts meet minimum thresholds")
        return True
    
    except Exception as e:
        print(f"❌ FAIL: Pattern count verification failed: {e}")
        return False


def verify_consumption_infrastructure():
    """Verify consumption tracking infrastructure exists."""
    print("\n" + "=" * 70)
    print("TEST 5: Verify Consumption Infrastructure")
    print("=" * 70)
    
    try:
        # Check signal_consumption module exists and works
        from saaaaaa.core.orchestrator.signal_consumption import (
            SignalConsumptionProof,
            SignalManifest,
            build_merkle_tree,
        )
        
        print("✓ signal_consumption module imported")
        
        # Test proof creation
        proof = SignalConsumptionProof(
            executor_id="TestExecutor",
            question_id="Q001",
            policy_area="PA01",
        )
        proof.record_pattern_match("test.*pattern", "test text")
        
        if len(proof.consumed_patterns) != 1:
            print("❌ FAIL: Proof did not record pattern match")
            return False
        
        if not proof.proof_chain:
            print("❌ FAIL: Proof chain not generated")
            return False
        
        print(f"✓ SignalConsumptionProof working: 1 match, chain length {len(proof.proof_chain)}")
        
        # Test Merkle tree
        merkle_root = build_merkle_tree(["p1", "p2", "p3"])
        if not merkle_root or len(merkle_root) != 64:  # SHA256 hex length
            print("❌ FAIL: Invalid Merkle root")
            return False
        
        print(f"✓ Merkle tree builder working: root {merkle_root[:16]}...")
        
        # Check verification script exists
        verify_script = REPO_ROOT / "scripts" / "verify_signal_consumption.py"
        if not verify_script.exists():
            print(f"❌ FAIL: Verification script not found at {verify_script}")
            return False
        
        print(f"✓ Consumption verification script exists")
        
        return True
    
    except Exception as e:
        print(f"❌ FAIL: Consumption infrastructure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("SIGNAL INTEGRATION VERIFICATION")
    print("=" * 70)
    
    tests = [
        verify_monolith_loading,
        verify_signal_pack_building,
        verify_signal_registry,
        verify_pattern_counts,
        verify_consumption_infrastructure,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ FATAL ERROR in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ ALL VERIFICATIONS PASSED")
        print("SIGNALS_VERIFIED=1")
        print("\nNote: To verify signal CONSUMPTION during execution:")
        print("  python scripts/verify_signal_consumption.py")
        return 0
    else:
        print("\n❌ SOME VERIFICATIONS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
