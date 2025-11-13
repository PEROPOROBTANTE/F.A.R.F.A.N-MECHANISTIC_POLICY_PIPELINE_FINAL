#!/usr/bin/env python3
"""
Equipment script for signals subsystem.

Initializes SignalRegistry, warms up memory cache, and verifies hit rates.
"""

import argparse
import sys
from typing import Dict, Any


def warmup_memory_signals() -> Dict[str, Any]:
    """Warm up memory:// signal cache with test data."""
    from saaaaaa.core.orchestrator.signals import SignalClient, SignalPack
    
    client = SignalClient(base_url="memory://")
    
    # Register test signals for common policy areas
    policy_areas = [
        "fiscal", "education", "health", "infrastructure", "security",
        "environment", "social", "economic", "governance", "culture"
    ]
    
    registered = 0
    for area in policy_areas:
        signal_pack = SignalPack(
            version="1.0.0",
            policy_area=area,
            patterns=[f"pattern_{area}_1", f"pattern_{area}_2", f"pattern_{area}_3"],
            indicators=[f"indicator_{area}"],
            regex=[f"regex_{area}"],
            verbs=[f"verb_{area}"],
            entities=[f"entity_{area}"],
            thresholds={f"threshold_{area}": 0.85}
        )
        client.register_memory_signal(area, signal_pack)
        registered += 1
    
    return {
        "registered": registered,
        "policy_areas": policy_areas,
        "client_base_url": client.base_url
    }


def initialize_signal_registry(max_size: int = 100, ttl_s: int = 3600) -> Dict[str, Any]:
    """Initialize SignalRegistry with specified parameters."""
    from saaaaaa.core.orchestrator.signals import SignalRegistry
    
    registry = SignalRegistry(max_size=max_size, default_ttl_s=ttl_s)
    
    return {
        "max_size": registry._max_size,
        "default_ttl_s": registry._default_ttl_s,
        "store_size": len(registry._store)
    }


def verify_signal_hit_rate(threshold: float = 0.95) -> Dict[str, Any]:
    """Verify signal hit rate meets threshold."""
    from saaaaaa.core.orchestrator.signals import SignalClient
    
    client = SignalClient(base_url="memory://")
    
    # Test fetching registered signals
    test_areas = ["fiscal", "education", "health"]
    hits = 0
    total = len(test_areas)
    
    for area in test_areas:
        signal_pack = client.fetch_signal_pack(area)
        if signal_pack is not None:
            hits += 1
    
    hit_rate = hits / total if total > 0 else 0.0
    passed = hit_rate >= threshold
    
    return {
        "hits": hits,
        "total": total,
        "hit_rate": hit_rate,
        "threshold": threshold,
        "passed": passed
    }


def precompile_patterns() -> Dict[str, Any]:
    """Pre-compile common regex patterns."""
    import re
    
    patterns = [
        r"\d+\.\d+",  # Decimal numbers
        r"\$\s*\d+(?:,\d{3})*(?:\.\d{2})?",  # Currency amounts
        r"\d{4}-\d{4}",  # Year ranges
        r"(?:Ley|Decreto|Resolución)\s+\d+",  # Legal references
    ]
    
    compiled = []
    for pattern in patterns:
        try:
            re.compile(pattern)
            compiled.append(pattern)
        except re.error:
            pass
    
    return {
        "total_patterns": len(patterns),
        "compiled": len(compiled),
        "patterns": compiled
    }


def main():
    """Main equipment routine for signals."""
    parser = argparse.ArgumentParser(
        description="Equipment routine for signals subsystem"
    )
    parser.add_argument(
        "--source",
        default="memory",
        choices=["memory", "http"],
        help="Signal source (default: memory)"
    )
    parser.add_argument(
        "--preload-patterns",
        action="store_true",
        help="Pre-compile regex patterns"
    )
    parser.add_argument(
        "--warmup-cache",
        action="store_true",
        help="Warm up signal cache"
    )
    parser.add_argument(
        "--verify-registry",
        action="store_true",
        help="Verify signal registry initialization"
    )
    parser.add_argument(
        "--hit-rate-threshold",
        type=float,
        default=0.95,
        help="Minimum hit rate threshold (default: 0.95)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("EQUIP:SIGNALS - Sistema de Señales")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Initialize registry
    if args.verify_registry:
        print("Inicializando SignalRegistry...")
        try:
            result = initialize_signal_registry()
            print(f"✓ SignalRegistry: max_size={result['max_size']}, ttl={result['default_ttl_s']}s")
        except Exception as e:
            print(f"✗ SignalRegistry initialization failed: {e}")
            all_passed = False
    
    # Warm up cache
    if args.warmup_cache:
        print("\nPre-calentamiento de cache...")
        try:
            result = warmup_memory_signals()
            print(f"✓ Cache warmed: {result['registered']} policy areas registered")
            print(f"  Areas: {', '.join(result['policy_areas'][:5])}...")
        except Exception as e:
            print(f"✗ Cache warmup failed: {e}")
            all_passed = False
    
    # Pre-compile patterns
    if args.preload_patterns:
        print("\nPre-compilando patrones regex...")
        try:
            result = precompile_patterns()
            print(f"✓ Patterns compiled: {result['compiled']}/{result['total_patterns']}")
        except Exception as e:
            print(f"✗ Pattern compilation failed: {e}")
            all_passed = False
    
    # Verify hit rate
    print("\nVerificando hit rate de señales...")
    try:
        result = verify_signal_hit_rate(args.hit_rate_threshold)
        if result['passed']:
            print(f"✓ Hit rate: {result['hit_rate']:.1%} (threshold: {result['threshold']:.1%})")
        else:
            print(f"✗ Hit rate: {result['hit_rate']:.1%} < {result['threshold']:.1%}")
            all_passed = False
    except Exception as e:
        print(f"✗ Hit rate verification failed: {e}")
        all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("✓ SIGNALS EQUIPMENT COMPLETE")
    else:
        print("✗ SIGNALS EQUIPMENT FAILED")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
