#!/usr/bin/env python3
"""
Direct Pipeline Test - Runtime Error Discovery
===============================================

This script attempts to run the pipeline directly using correct imports
to discover all runtime errors.
"""

import sys
import traceback
from pathlib import Path

print("=" * 80)
print("DIRECT PIPELINE EXECUTION - ERROR DISCOVERY")
print("=" * 80)
print()

# Test 1: Import CPPIngestionPipeline from correct location
print("[1/5] Importing CPPIngestionPipeline from spc_ingestion...")
try:
    from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline
    print("✓ CPPIngestionPipeline imported successfully")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Import Orchestrator
print("\n[2/5] Importing Orchestrator...")
try:
    from saaaaaa.core.orchestrator import Orchestrator
    print("✓ Orchestrator imported successfully")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check for input PDF
print("\n[3/5] Checking for input PDF...")
pdf_path = Path("data/plans/Plan_1.pdf")
if pdf_path.exists():
    print(f"✓ Found PDF: {pdf_path} ({pdf_path.stat().st_size} bytes)")
else:
    print(f"✗ PDF not found: {pdf_path}")
    sys.exit(1)

# Test 4: Initialize CPPIngestionPipeline
print("\n[4/5] Initializing CPPIngestionPipeline...")
try:
    pipeline = CPPIngestionPipeline()
    print("✓ Pipeline initialized")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Try to ingest the PDF
print("\n[5/5] Attempting to ingest PDF...")
try:
    output_dir = Path("artifacts/test_run")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Input: {pdf_path}")
    print(f"  Output: {output_dir}")
    print(f"  Starting ingestion...")

    import asyncio
    result = asyncio.run(pipeline.process(pdf_path, document_id="test_doc", title="Test Plan"))

    print(f"✓ Ingestion completed!")
    print(f"  Result type: {type(result)}")
    print(f"  Result: {result}")

except Exception as e:
    print(f"✗ FAILED during ingestion: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("ERROR COLLECTED - This is the structural obstacle")
    print("=" * 80)
    sys.exit(1)

print("\n" + "=" * 80)
print("SUCCESS! Pipeline executed without structural errors")
print("=" * 80)
