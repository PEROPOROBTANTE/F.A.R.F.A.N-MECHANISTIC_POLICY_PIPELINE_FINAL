#!/usr/bin/env python3
"""
Dependency Verification Script

Verifies that all required dependencies are installed and that the class registry
can successfully load all 22 classes mentioned in the import resolution documentation.

This script validates the fixes described in the import resolution problem statement:
1. All class paths use absolute imports with saaaaaa. prefix
2. All required external dependencies are available
3. SpaCy models are installed
"""

import sys
from importlib import import_module
from pathlib import Path

def check_class_registry_paths():
    """Verify all class paths have saaaaaa. prefix."""
    print("=" * 70)
    print("1. Checking Class Registry Paths")
    print("=" * 70)

    try:
        from saaaaaa.core.orchestrator.class_registry import get_class_paths

        paths = get_class_paths()
        print(f"✓ Found {len(paths)} registered classes")

        # Verify all paths start with saaaaaa.
        invalid_paths = []
        for class_name, import_path in paths.items():
            if not import_path.startswith("saaaaaa."):
                invalid_paths.append((class_name, import_path))

        if invalid_paths:
            print(f"✗ ERROR: {len(invalid_paths)} classes have invalid paths:")
            for name, path in invalid_paths:
                print(f"  - {name}: {path}")
            return False

        print("✓ All paths use absolute imports with saaaaaa. prefix")

        # Verify count matches expected (22 classes)
        if len(paths) != 22:
            print(f"⚠ WARNING: Expected 22 classes, found {len(paths)}")
        else:
            print("✓ All 22 expected classes are registered")

        return True

    except Exception as e:
        print(f"✗ ERROR: Failed to check class registry: {e}")
        return False

def check_core_dependencies():
    """Check that core Python dependencies are installed."""
    print("\n" + "=" * 70)
    print("2. Checking Core Dependencies")
    print("=" * 70)

    required_packages = {
        "numpy": "Scientific computing",
        "pandas": "Data manipulation",
        "scipy": "Scientific algorithms",
        "networkx": "Graph analysis",
        "sklearn": "Machine learning",
        "transformers": "NLP transformers",
        "sentence_transformers": "Semantic embeddings",
        "spacy": "NLP framework",
    }

    missing = []
    for package, description in required_packages.items():
        try:
            import_module(package)
            print(f"✓ {package}: {description}")
        except ImportError:
            print(f"✗ {package}: {description} - NOT INSTALLED")
            missing.append(package)

    return len(missing) == 0

def check_pdf_dependencies():
    """Check PDF processing dependencies."""
    print("\n" + "=" * 70)
    print("3. Checking PDF Processing Dependencies")
    print("=" * 70)

    pdf_packages = {
        "fitz": ("PyMuPDF", "PDF document processing"),
        "tabula": ("tabula-py", "Table extraction from PDFs"),
        "camelot": ("camelot-py", "Complex table extraction"),
        "pdfplumber": ("pdfplumber", "PDF text and layout"),
    }

    missing = []
    for module_name, (package_name, description) in pdf_packages.items():
        try:
            import_module(module_name)
            print(f"✓ {package_name}: {description}")
        except ImportError:
            print(f"✗ {package_name}: {description} - NOT INSTALLED")
            missing.append(package_name)

    return len(missing) == 0

def check_nlp_dependencies():
    """Check NLP-specific dependencies."""
    print("\n" + "=" * 70)
    print("4. Checking NLP Dependencies")
    print("=" * 70)

    nlp_packages = {
        "sentencepiece": "Tokenization for transformers (PolicyContradictionDetector)",
        "tiktoken": "OpenAI tokenizer",
        "fuzzywuzzy": "Fuzzy string matching",
        "Levenshtein": "String similarity metrics",
    }

    missing = []
    for package, description in nlp_packages.items():
        try:
            import_module(package)
            print(f"✓ {package}: {description}")
        except ImportError:
            print(f"✗ {package}: {description} - NOT INSTALLED")
            missing.append(package)

    return len(missing) == 0

def check_spacy_models():
    """Check SpaCy language models."""
    print("\n" + "=" * 70)
    print("5. Checking SpaCy Language Models")
    print("=" * 70)

    try:
        import spacy

        # Check for Spanish models
        models = {
            "es_core_news_lg": "Large Spanish model (required for CDAF and Financial)",
            "es_dep_news_trf": "Transformer Spanish model (recommended)",
        }

        all_installed = True
        for model_name, description in models.items():
            try:
                spacy.load(model_name)
                print(f"✓ {model_name}: {description}")
            except OSError:
                print(f"✗ {model_name}: {description} - NOT INSTALLED")
                print(f"  Install with: python -m spacy download {model_name}")
                all_installed = False

        return all_installed

    except ImportError:
        print("✗ ERROR: spacy not installed")
        return False

def check_class_registry_loading():
    """Attempt to actually load the class registry."""
    print("\n" + "=" * 70)
    print("6. Loading Class Registry")
    print("=" * 70)

    try:
        from saaaaaa.core.orchestrator.class_registry import (
            ClassRegistryError,
            build_class_registry,
        )

        print("Attempting to load all 22 classes...")
        registry = build_class_registry()

        print(f"✓ Successfully loaded {len(registry)} classes:")
        for name in sorted(registry.keys()):
            print(f"  ✓ {name}")

        return True

    except ClassRegistryError as e:
        print(f"✗ ClassRegistryError: {e}")
        print("\nSome classes failed to load. Check that all dependencies are installed.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("SAAAAAA Dependency Verification")
    print("=" * 70)
    print("\nVerifying import resolution fixes and dependencies...")
    print("This validates the fixes described in IMPORT_RESOLUTION_SUMMARY.md\n")

    checks = [
        check_class_registry_paths,
        check_core_dependencies,
        check_pdf_dependencies,
        check_nlp_dependencies,
        check_spacy_models,
        check_class_registry_loading,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Check failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total} checks")

    if all(results):
        print("\n✓ All checks passed! The system is properly configured.")
        print("\nThe import resolution fixes are in place:")
        print("  ✓ All 22 classes use absolute imports with saaaaaa. prefix")
        print("  ✓ All required dependencies are installed")
        print("  ✓ Class registry can load all modules successfully")
        return 0
    else:
        print("\n✗ Some checks failed. Please install missing dependencies.")
        print("\nTo install all dependencies:")
        print("  pip install -r requirements.txt")
        print("\nTo install SpaCy models:")
        print("  python -m spacy download es_core_news_lg")
        print("  python -m spacy download es_dep_news_trf")
        return 1

if __name__ == "__main__":
    sys.exit(main())
