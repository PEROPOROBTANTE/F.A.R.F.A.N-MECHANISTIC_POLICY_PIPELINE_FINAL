#!/usr/bin/env python3
"""
Example script demonstrating dependency lockdown enforcement.

This script shows how the dependency lockdown system prevents magic
downloads and enforces explicit dependency management.

Run with:
    # Offline mode (default) - will fail if models not cached
    python examples/demo_dependency_lockdown.py

    # Online mode - allows model downloads
    HF_ONLINE=1 python examples/demo_dependency_lockdown.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports

from saaaaaa.core.dependency_lockdown import (
    DependencyLockdown,
    DependencyLockdownError,
    get_dependency_lockdown,
)


def demonstrate_lockdown():
    """Demonstrate dependency lockdown features."""
    
    print("=" * 80)
    print("DEPENDENCY LOCKDOWN DEMONSTRATION")
    print("=" * 80)
    
    # Get lockdown instance
    lockdown = get_dependency_lockdown()
    
    # Show current mode
    mode_info = lockdown.get_mode_description()
    print(f"\n1. Current Mode:")
    print(f"   HF_ONLINE allowed: {mode_info['hf_online_allowed']}")
    print(f"   Mode: {mode_info['mode']}")
    print(f"   HF_HUB_OFFLINE: {mode_info['hf_hub_offline']}")
    print(f"   TRANSFORMERS_OFFLINE: {mode_info['transformers_offline']}")
    
    # Check critical dependency
    print(f"\n2. Checking Critical Dependencies:")
    try:
        lockdown.check_critical_dependency(
            module_name="os",
            pip_package="builtin",
            phase="demo"
        )
        print("   ✓ os module available (builtin)")
    except DependencyLockdownError as e:
        print(f"   ✗ os module missing: {e}")
    
    # Check optional dependency
    print(f"\n3. Checking Optional Dependencies:")
    has_numpy = lockdown.check_optional_dependency(
        module_name="numpy",
        pip_package="numpy",
        feature="numerical_processing"
    )
    if has_numpy:
        print("   ✓ numpy available - full numerical processing enabled")
    else:
        print("   ⚠ numpy not available - degraded mode for numerical processing")
    
    # Check online model access
    print(f"\n4. Checking Online Model Access:")
    try:
        lockdown.check_online_model_access(
            model_name="example/model",
            operation="demonstration"
        )
        print("   ✓ Online model downloads ALLOWED (HF_ONLINE=1)")
        print("   ⚠ Models may be downloaded from HuggingFace Hub")
    except DependencyLockdownError as e:
        print("   ✓ Online model downloads BLOCKED (HF_ONLINE=0)")
        print("   Models must be pre-cached locally")
        print(f"   Error message would be: {str(e)[:100]}...")
    
    # Demonstrate embedding system integration
    print(f"\n5. Embedding System Integration:")
    try:
        from saaaaaa.processing.embedding_policy import (
            PolicyEmbeddingConfig,
            PolicyAnalysisEmbedder,
        )
        
        print("   Attempting to initialize embedding system...")
        config = PolicyEmbeddingConfig(
            embedding_model="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
        
        # This will check lockdown before attempting model load
        try:
            embedder = PolicyAnalysisEmbedder(config)
            print("   ✓ Embedding system initialized successfully")
            print("   (Model was found in cache or online downloads enabled)")
        except DependencyLockdownError as e:
            print("   ✗ Embedding system initialization blocked by lockdown:")
            print(f"   {e}")
            print("\n   To enable: HF_ONLINE=1 python examples/demo_dependency_lockdown.py")
    except ImportError as e:
        print(f"   ⚠ Cannot demo embedding system (missing dependencies): {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if mode_info['hf_online_allowed']:
        print("✓ Online mode: Model downloads allowed")
        print("  - Can download models from HuggingFace Hub")
        print("  - Models will be cached for future offline use")
    else:
        print("✓ Offline mode: Model downloads blocked")
        print("  - Only locally cached models can be used")
        print("  - To enable downloads: HF_ONLINE=1")
        print("  - No silent fallback - fails fast with clear errors")
    
    print("\nKey Principles:")
    print("  1. Explicit is better than implicit")
    print("  2. Fail fast with clear errors")
    print("  3. No magic downloads or silent degraded modes")
    print("  4. Environment-controlled behavior")
    print("=" * 80)


def demonstrate_orchestrator():
    """Demonstrate orchestrator integration."""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR INTEGRATION")
    print("=" * 80)
    
    try:
        from saaaaaa.core.orchestrator import Orchestrator
        
        print("\nInitializing orchestrator...")
        orchestrator = Orchestrator()
        
        print("✓ Orchestrator initialized")
        print(f"  Lockdown mode: {orchestrator.dependency_lockdown.get_mode_description()['mode']}")
        print(f"  HF_ONLINE: {orchestrator.dependency_lockdown.hf_allowed}")
        
    except Exception as e:
        print(f"⚠ Cannot demo orchestrator (missing dependencies): {e}")


if __name__ == "__main__":
    demonstrate_lockdown()
    demonstrate_orchestrator()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nFor more information, see DEPENDENCY_LOCKDOWN.md")
