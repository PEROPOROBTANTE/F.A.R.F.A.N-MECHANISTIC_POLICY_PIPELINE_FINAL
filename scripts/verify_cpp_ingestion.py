#!/usr/bin/env python3
"""
LEGACY SCRIPT - DO NOT USE

This script targets the deprecated CPP ingestion implementation that no longer
exists in this repository. The canonical ingestion path is:

    scripts/run_policy_pipeline_verified.py
      → saaaaaa.processing.spc_ingestion.CPPIngestionPipeline
      → saaaaaa.utils.spc_adapter.SPCAdapter
      → Orchestrator

Running this script will fail. Kept only for historical reference.

==============================================================================
DEPRECATED: Use scripts/run_policy_pipeline_verified.py instead
==============================================================================
"""

import sys
from pathlib import Path

from saaaaaa.utils.paths import data_dir
from saaaaaa.processing.cpp_ingestion import CPPIngestionPipeline


def main():
    """Test CPP ingestion pipeline."""
    
    print("=" * 80)
    print("CPP INGESTION VERIFICATION")
    print("=" * 80)
    print()
    
    # Check input file
    input_path = data_dir() / 'plans' / 'Plan_1.pdf'
    
    if not input_path.exists():
        print(f"❌ ERROR: Plan_1.pdf not found at {input_path}")
        print("   Please ensure the file exists before running.")
        return 1
    
    print(f"✓ Input file: {input_path}")
    print(f"✓ Size: {input_path.stat().st_size / 1024:.1f} KB")
    print()
    
    # Setup output directory
    cpp_output = data_dir() / 'output' / 'cpp_verify_test'
    cpp_output.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Output directory: {cpp_output}")
    print()
    
    # Initialize pipeline
    print("🔄 Initializing CPP ingestion pipeline...")
    try:
        cpp_pipeline = CPPIngestionPipeline(
            enable_ocr=True,
            ocr_confidence_threshold=0.85,
            chunk_overlap_threshold=0.15
        )
        print("✅ Pipeline initialized")
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return 1
    
    print()
    
    # Run ingestion
    print("🔄 Running CPP ingestion (may take 30-60 seconds)...")
    print()
    
    try:
        cpp_outcome = cpp_pipeline.ingest(input_path, cpp_output)
        
        if cpp_outcome.status == 'OK' and cpp_outcome.cpp_uri:
            print("=" * 80)
            print("✅ CPP INGESTION SUCCESSFUL")
            print("=" * 80)
            print()
            print(f"  Status: {cpp_outcome.status}")
            print(f"  CPP URI: {cpp_outcome.cpp_uri}")
            print(f"  Schema Version: {cpp_pipeline.SCHEMA_VERSION}")
            print()
            
            # Check output files
            cpp_dir = Path(cpp_outcome.cpp_uri)
            if cpp_dir.exists():
                print("  Generated files:")
                for file in sorted(cpp_dir.iterdir()):
                    size = file.stat().st_size
                    print(f"    - {file.name} ({size:,} bytes)")
                print()
            
            # Check policy manifest
            if cpp_outcome.policy_manifest:
                print("  Policy Manifest:")
                print(f"    Axes: {cpp_outcome.policy_manifest.axes}")
                print(f"    Programs: {cpp_outcome.policy_manifest.programs}")
                print(f"    Projects: {cpp_outcome.policy_manifest.projects}")
                print(f"    Years: {cpp_outcome.policy_manifest.years}")
                print(f"    Territories: {cpp_outcome.policy_manifest.territories}")
                print()
            
            # Check quality metrics
            if cpp_outcome.metrics:
                print("  Quality Metrics:")
                print(f"    Boundary F1: {cpp_outcome.metrics.boundary_f1:.3f}")
                print(f"    KPI Linkage Rate: {cpp_outcome.metrics.kpi_linkage_rate:.3f}")
                print(f"    Budget Consistency: {cpp_outcome.metrics.budget_consistency_score:.3f}")
                print(f"    Provenance Completeness: {cpp_outcome.metrics.provenance_completeness:.3f}")
                print()
            
            print("✅ All checks passed!")
            print()
            print("Next steps:")
            print("  1. Install full dependencies: pip install -r requirements.txt")
            print("  2. Run full orchestration: python run_complete_analysis_plan1.py")
            return 0
            
        else:
            print("=" * 80)
            print("❌ CPP INGESTION FAILED")
            print("=" * 80)
            print()
            print(f"  Status: {cpp_outcome.status}")
            print()
            
            # Show event log if available
            if hasattr(cpp_pipeline, 'event_log') and cpp_pipeline.event_log:
                print("  Event log (last 10 events):")
                for event in cpp_pipeline.event_log[-10:]:
                    print(f"    - {event}")
                print()
            
            return 1
            
    except Exception as e:
        print("=" * 80)
        print("❌ EXCEPTION DURING INGESTION")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        
        import traceback
        print("Traceback:")
        traceback.print_exc()
        print()
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
