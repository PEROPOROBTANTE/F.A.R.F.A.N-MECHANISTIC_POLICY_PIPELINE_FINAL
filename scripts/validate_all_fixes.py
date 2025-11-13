#!/usr/bin/env python3
"""
Comprehensive validation script for all table handling and CPP ingestion fixes.

This script validates:
1. _safe_strip function handles None values correctly
2. Table extraction works with None values in cells
3. IngestionOutcome.cpp attribute is accessible
4. PreprocessedDocument uses raw_text (not content)
5. build_processor has correct signature

Note: Run this script after installing the package with: pip install -e .
"""

import sys

def validate_safe_strip():
    """Validate _safe_strip function."""
    print("=" * 70)
    print("1. Validating _safe_strip function")
    print("=" * 70)
    
    from saaaaaa.processing.cpp_ingestion.tables import _safe_strip
    
    # Test cases
    test_cases = [
        (None, "", "None → empty string"),
        ("  hello  ", "hello", "String with whitespace → stripped"),
        (42, "42", "Integer → string"),
        (3.14, "3.14", "Float → string"),
        ("", "", "Empty string → empty string"),
        ("   ", "", "Whitespace only → empty string"),
    ]
    
    all_passed = True
    for input_val, expected, description in test_cases:
        result = _safe_strip(input_val)
        if result == expected:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}: expected '{expected}', got '{result}'")
            all_passed = False
    
    if all_passed:
        print("\n✓ All _safe_strip tests passed\n")
    else:
        print("\n✗ Some _safe_strip tests failed\n")
        return False
    
    return True


def validate_table_extraction():
    """Validate table extraction with None values."""
    print("=" * 70)
    print("2. Validating table extraction with None values")
    print("=" * 70)
    
    from saaaaaa.processing.cpp_ingestion.tables import TableExtractor
    
    extractor = TableExtractor()
    
    # Test KPI extraction with None values
    kpi_table = {
        "table_id": "test_kpi",
        "page": 1,
        "headers": ["Indicador", "Línea Base", "Meta"],
        "rows": [
            ["Indicador", "Línea Base", "Meta"],
            ["Tasa A", "85", "95"],
            ["Tasa B", None, "90"],  # None in baseline
            ["Tasa C", "80", None],  # None in target
        ]
    }
    
    try:
        kpis = extractor._extract_kpis(kpi_table)
        print(f"  ✓ Extracted {len(kpis)} KPIs without errors")
        print(f"    - KPI with None baseline: {'Tasa B' in str(kpis)}")
        print(f"    - KPI with None target: {'Tasa C' in str(kpis)}")
    except Exception as e:
        print(f"  ✗ KPI extraction failed: {e}")
        return False
    
    # Test budget extraction with None values
    budget_table = {
        "table_id": "test_budget",
        "page": 1,
        "headers": ["Fuente", "Uso", "Monto"],
        "rows": [
            ["Fuente", "Uso", "Monto"],
            ["SGP", "Educación", "$1,000,000"],
            [None, "Salud", "$500,000"],  # None in source
            ["Regalías", None, "$2,000,000"],  # None in use
        ]
    }
    
    try:
        budgets = extractor._extract_budgets(budget_table)
        print(f"  ✓ Extracted {len(budgets)} budget items without errors")
    except Exception as e:
        print(f"  ✗ Budget extraction failed: {e}")
        return False
    
    print("\n✓ Table extraction tests passed\n")
    return True


def validate_ingestion_outcome():
    """Validate IngestionOutcome.cpp attribute."""
    print("=" * 70)
    print("3. Validating IngestionOutcome.cpp attribute")
    print("=" * 70)
    
    from saaaaaa.processing.cpp_ingestion.models import (
        IngestionOutcome,
        CanonPolicyPackage,
        PolicyManifest,
        ChunkGraph,
    )
    from saaaaaa.utils.paths import tmp_dir
    
    # Create minimal CPP
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(
            axes=2,
            programs=5,
        ),
        chunk_graph=ChunkGraph(),
    )
    
    # Create outcome with cpp
    outcome = IngestionOutcome(
        status="OK",
        cpp_uri=str(tmp_dir() / "test"),
        cpp=cpp,
    )
    
    # Validate
    if not hasattr(outcome, "cpp"):
        print("  ✗ IngestionOutcome missing cpp attribute")
        return False
    print("  ✓ IngestionOutcome has cpp attribute")
    
    if outcome.cpp is None:
        print("  ✗ cpp attribute is None")
        return False
    print("  ✓ cpp attribute is not None")
    
    if outcome.cpp.schema_version != "CPP-2025.1":
        print("  ✗ Cannot access cpp.schema_version")
        return False
    print("  ✓ Can access cpp.schema_version")
    
    # Test without cpp
    outcome_no_cpp = IngestionOutcome(status="ABORT")
    if outcome_no_cpp.cpp is not None:
        print("  ✗ cpp should be None when not provided")
        return False
    print("  ✓ cpp is None when not provided")
    
    print("\n✓ IngestionOutcome.cpp tests passed\n")
    return True


def validate_preprocessed_document():
    """Validate PreprocessedDocument attributes."""
    print("=" * 70)
    print("4. Validating PreprocessedDocument.raw_text attribute")
    print("=" * 70)
    
    from saaaaaa.core.orchestrator.core import PreprocessedDocument
    
    doc = PreprocessedDocument(
        document_id="test",
        raw_text="Test content",
        sentences=["Test content."],
        tables=[],
        metadata={},
    )
    
    if not hasattr(doc, "raw_text"):
        print("  ✗ PreprocessedDocument missing raw_text attribute")
        return False
    print("  ✓ PreprocessedDocument has raw_text attribute")
    
    if doc.raw_text != "Test content":
        print("  ✗ raw_text value incorrect")
        return False
    print("  ✓ raw_text value is correct")
    
    if hasattr(doc, "content"):
        print("  ℹ PreprocessedDocument has 'content' attribute (unexpected)")
        print("    Note: Code should use 'raw_text', not 'content'")
    else:
        print("  ✓ PreprocessedDocument does not have 'content' attribute")
    
    # Test accessing raw_text length
    try:
        length = len(doc.raw_text)
        print(f"  ✓ Can access len(doc.raw_text): {length} characters")
    except Exception as e:
        print(f"  ✗ Cannot access len(doc.raw_text): {e}")
        return False
    
    print("\n✓ PreprocessedDocument tests passed\n")
    return True


def validate_build_processor():
    """Validate build_processor signature."""
    print("=" * 70)
    print("5. Validating build_processor signature")
    print("=" * 70)
    
    import inspect
    from saaaaaa.core.orchestrator.factory import build_processor
    
    sig = inspect.signature(build_processor)
    params = sig.parameters
    
    print(f"  Signature: {sig}")
    print(f"  Parameters: {list(params.keys())}")
    
    # Check that all parameters are keyword-only or have defaults
    has_required_positional = False
    for param_name, param in params.items():
        is_keyword_only = param.kind == inspect.Parameter.KEYWORD_ONLY
        has_default = param.default != inspect.Parameter.empty
        
        if not (is_keyword_only or has_default):
            print(f"  ✗ Parameter '{param_name}' requires a value (not keyword-only and no default)")
            has_required_positional = True
        else:
            status = "keyword-only" if is_keyword_only else f"default={param.default}"
            print(f"  ✓ {param_name}: {status}")
    
    if has_required_positional:
        print("\n✗ build_processor has required positional arguments")
        return False
    
    print("  ✓ No required positional arguments")
    print("\n✓ build_processor signature is correct\n")
    return True


def main():
    """Run all validations."""
    print("\n")
    print("=" * 70)
    print("COMPREHENSIVE VALIDATION OF TABLE HANDLING FIXES")
    print("=" * 70)
    print()
    
    results = []
    
    try:
        results.append(("_safe_strip", validate_safe_strip()))
        results.append(("Table extraction", validate_table_extraction()))
        results.append(("IngestionOutcome.cpp", validate_ingestion_outcome()))
        results.append(("PreprocessedDocument", validate_preprocessed_document()))
        results.append(("build_processor", validate_build_processor()))
    except Exception as e:
        print(f"\n✗ Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("=" * 70)
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 70)
        print()
        print("The system is ready for end-to-end execution.")
        print()
        return True
    else:
        print("=" * 70)
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
