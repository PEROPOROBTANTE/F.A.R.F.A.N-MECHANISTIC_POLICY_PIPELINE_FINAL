#!/usr/bin/env python3
"""Test script to verify factory refactoring."""

import sys
from pathlib import Path

def check_no_direct_imports():
    """Check that API files don't have direct imports of processing/analysis/utils."""
    errors = []

    # Check pipeline_connector.py
    connector_path = Path('src/farfan_pipeline/api/pipeline_connector.py')
    with open(connector_path, 'r') as f:
        content = f.read()
        if 'from farfan_pipeline.processing.spc_ingestion import' in content:
            errors.append("pipeline_connector.py still has direct spc_ingestion import")
        if 'from farfan_pipeline.utils.spc_adapter import' in content:
            errors.append("pipeline_connector.py still has direct spc_adapter import")
        if 'from farfan_pipeline.utils.cpp_adapter import' in content and 'factory' not in content.split('from farfan_pipeline.utils.cpp_adapter import')[0].split('\n')[-1]:
            errors.append("pipeline_connector.py still has direct cpp_adapter import")

    # Check api_server.py
    server_path = Path('src/farfan_pipeline/api/api_server.py')
    with open(server_path, 'r') as f:
        content = f.read()
        if 'from farfan_pipeline.analysis.recommendation_engine import load_recommendation_engine' in content:
            errors.append("api_server.py still has direct recommendation_engine import")

    return errors

def check_factory_methods_used():
    """Check that factory methods are properly used."""
    errors = []

    # Check pipeline_connector.py uses factory methods
    connector_path = Path('src/farfan_pipeline/api/pipeline_connector.py')
    with open(connector_path, 'r') as f:
        content = f.read()
        if 'create_cpp_ingestion_pipeline' not in content:
            errors.append("pipeline_connector.py does not use create_cpp_ingestion_pipeline")
        if 'create_cpp_adapter' not in content:
            errors.append("pipeline_connector.py does not use create_cpp_adapter")
        if 'from ..core.orchestrator.factory import' not in content:
            errors.append("pipeline_connector.py does not import from factory")

    # Check api_server.py uses factory methods
    server_path = Path('src/farfan_pipeline/api/api_server.py')
    with open(server_path, 'r') as f:
        content = f.read()
        if 'create_recommendation_engine' not in content:
            errors.append("api_server.py does not use create_recommendation_engine")
        if 'from farfan_pipeline.core.orchestrator.factory import' not in content:
            errors.append("api_server.py does not import from factory")

    return errors

def check_factory_has_methods():
    """Check that factory.py has the new methods."""
    errors = []

    factory_path = Path('src/farfan_pipeline/core/orchestrator/factory.py')
    with open(factory_path, 'r') as f:
        content = f.read()
        if 'def create_cpp_ingestion_pipeline' not in content:
            errors.append("factory.py missing create_cpp_ingestion_pipeline")
        if 'def create_cpp_adapter' not in content:
            errors.append("factory.py missing create_cpp_adapter")
        if 'def create_recommendation_engine' not in content:
            errors.append("factory.py missing create_recommendation_engine")

    return errors

def main():
    print("Checking factory refactoring...")
    print()

    all_errors = []

    print("1. Checking for direct imports in API layer...")
    errors = check_no_direct_imports()
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ No direct imports found")

    print()
    print("2. Checking factory methods are used...")
    errors = check_factory_methods_used()
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ Factory methods properly used")

    print()
    print("3. Checking factory has new methods...")
    errors = check_factory_has_methods()
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ Factory has all new methods")

    print()
    if all_errors:
        print(f"❌ Refactoring incomplete: {len(all_errors)} errors found")
        return 1
    else:
        print("✅ All refactoring checks passed!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
