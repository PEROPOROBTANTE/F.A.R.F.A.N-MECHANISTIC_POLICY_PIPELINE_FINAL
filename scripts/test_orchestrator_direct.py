#!/usr/bin/env python3
"""
Direct Orchestrator Test - Current Architecture
================================================

Tests the actual 11-phase orchestrator flow as currently implemented.
This is the REAL pipeline, not deprecated scripts.
"""

import sys
import traceback
from pathlib import Path

print("=" * 80)
print("ORCHESTRATOR DIRECT TEST - CURRENT ARCHITECTURE")
print("=" * 80)
print()

# Test 1: Import Orchestrator
print("[1/6] Importing Orchestrator from core...")
try:
    from saaaaaa.core.orchestrator import Orchestrator
    print("✓ Orchestrator imported successfully")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Import questionnaire loader
print("\n[2/6] Importing questionnaire loader...")
try:
    from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
    print("✓ questionnaire loader imported successfully")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Load questionnaire
print("\n[3/6] Loading canonical questionnaire...")
try:
    questionnaire = load_questionnaire()
    print(f"✓ Questionnaire loaded")
    print(f"  - Total questions: {questionnaire.total_question_count}")
    print(f"  - Micro questions: {questionnaire.micro_question_count}")
    print(f"  - SHA256: {questionnaire.sha256[:16]}...")
    print(f"  - Version: {questionnaire.version}")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check for PDF
print("\n[4/6] Checking for input PDF...")
pdf_path = Path("data/plans/Plan_1.pdf")
if pdf_path.exists():
    print(f"✓ Found PDF: {pdf_path} ({pdf_path.stat().st_size} bytes)")
else:
    print(f"✗ PDF not found: {pdf_path}")
    sys.exit(1)

# Test 5: Initialize Orchestrator
print("\n[5/6] Initializing Orchestrator...")
try:
    orchestrator = Orchestrator(questionnaire=questionnaire)
    print("✓ Orchestrator initialized")
    print(f"  - Phases: {len(orchestrator.FASES)}")
    print(f"  - Expected questions: {300}")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Check orchestrator methods
print("\n[6/6] Checking orchestrator execution methods...")
try:
    import inspect
    methods = [m for m in dir(orchestrator) if not m.startswith('_')]
    exec_methods = [m for m in methods if 'run' in m or 'execute' in m]
    print(f"✓ Found execution methods: {exec_methods}")

    # Check if run_async exists
    if hasattr(orchestrator, 'run_async'):
        print("✓ run_async method available")
        sig = inspect.signature(orchestrator.run_async)
        print(f"  Signature: run_async{sig}")

except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("ORCHESTRATOR INITIALIZATION SUCCESSFUL")
print("=" * 80)
print("\nNext step: Execute orchestrator.run_async(pdf_path) to test full pipeline")
print("This will run all 11 phases and reveal runtime errors")
print("=" * 80)
