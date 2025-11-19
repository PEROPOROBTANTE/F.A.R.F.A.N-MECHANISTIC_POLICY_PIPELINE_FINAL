#!/usr/bin/env python3
"""
TEST SCRIPT: Verify 60-Chunk Generation by PA×DIM Matrix
==========================================================

This script validates that the Smart Policy Chunks pipeline generates
EXACTLY 60 chunks structured by Policy Area × Dimension matrix.

NO placeholders. NO shortcuts. COMPLETE validation.
"""

import asyncio
from pathlib import Path
from collections import Counter

from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline


async def test_60_chunk_generation():
    """Test that exactly 60 chunks are generated with PA×DIM alignment."""

    print("=" * 80)
    print("HOSTILE TEST: 60-Chunk Generation Validation")
    print("=" * 80)

    # Initialize pipeline
    print("\n[1/5] Initializing CPPIngestionPipeline...")
    pipeline = CPPIngestionPipeline()
    print("✅ Pipeline initialized")

    # Load test PDF
    pdf_path = Path("data/plans/Plan_1.pdf")
    if not pdf_path.exists():
        print(f"❌ FATAL: Input PDF not found: {pdf_path}")
        return False

    print(f"\n[2/5] Processing PDF: {pdf_path}")
    print(f"  File size: {pdf_path.stat().st_size:,} bytes")

    # Process document
    try:
        cpp = await pipeline.process(
            document_path=pdf_path,
            document_id="plan1_test",
            title="Plan 1 Test"
        )
        print("✅ Document processed successfully")
    except Exception as e:
        print(f"❌ FATAL: Pipeline processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Validate chunk count
    print(f"\n[3/5] Validating chunk count...")
    chunks = cpp.chunk_graph.chunks
    chunk_count = len(chunks)

    print(f"  Total chunks generated: {chunk_count}")

    if chunk_count != 60:
        print(f"❌ CRITICAL FAILURE: Expected exactly 60 chunks, got {chunk_count}")
        print(f"   This violates the PA×DIM matrix requirement (10 PA × 6 DIM = 60)")
        return False

    print("✅ Exactly 60 chunks generated (10 PA × 6 DIM)")

    # Validate PA×DIM alignment
    print(f"\n[4/5] Validating PA×DIM alignment...")

    pa_counts = Counter()
    dim_counts = Counter()
    pa_dim_matrix = {}

    missing_pa_id = 0
    missing_dim_id = 0

    for chunk_id, chunk in chunks.items():
        pa_id = chunk.policy_area_id
        dim_id = chunk.dimension_id

        if pa_id is None:
            missing_pa_id += 1
        else:
            pa_counts[pa_id] += 1

        if dim_id is None:
            missing_dim_id += 1
        else:
            dim_counts[dim_id] += 1

        if pa_id and dim_id:
            key = (pa_id, dim_id)
            if key not in pa_dim_matrix:
                pa_dim_matrix[key] = []
            pa_dim_matrix[key].append(chunk_id)

    print(f"\n  Policy Areas found: {len(pa_counts)} unique")
    print(f"  Dimensions found: {len(dim_counts)} unique")
    print(f"  Chunks missing policy_area_id: {missing_pa_id}")
    print(f"  Chunks missing dimension_id: {missing_dim_id}")

    if missing_pa_id > 0 or missing_dim_id > 0:
        print(f"❌ CRITICAL FAILURE: Some chunks missing PA or DIM IDs")
        return False

    # Verify 10 PA × 6 DIM = 60 combinations
    expected_pa = 10
    expected_dim = 6

    if len(pa_counts) != expected_pa:
        print(f"❌ FAILURE: Expected {expected_pa} policy areas, found {len(pa_counts)}")
        print(f"   Found: {sorted(pa_counts.keys())}")
        return False

    if len(dim_counts) != expected_dim:
        print(f"❌ FAILURE: Expected {expected_dim} dimensions, found {len(dim_counts)}")
        print(f"   Found: {sorted(dim_counts.keys())}")
        return False

    print(f"\n✅ All 10 Policy Areas present: {sorted(pa_counts.keys())}")
    print(f"✅ All 6 Dimensions present: {sorted(dim_counts.keys())}")

    # Verify matrix coverage
    print(f"\n  PA×DIM Matrix coverage:")
    print(f"    Total combinations: {len(pa_dim_matrix)}")
    print(f"    Expected: {expected_pa * expected_dim} (10 × 6)")

    if len(pa_dim_matrix) != 60:
        print(f"❌ FAILURE: Matrix not fully covered")
        print(f"   Missing combinations: {60 - len(pa_dim_matrix)}")

        # Find missing combinations
        all_pa = [f"PA{i:02d}" for i in range(1, 11)]
        all_dim = [f"DIM{i:02d}" for i in range(1, 7)]
        missing = []
        for pa in all_pa:
            for dim in all_dim:
                if (pa, dim) not in pa_dim_matrix:
                    missing.append((pa, dim))

        if missing:
            print(f"   Missing: {missing[:10]}...")
        return False

    print(f"✅ Full PA×DIM matrix covered (60/60 combinations)")

    # Quality checks
    print(f"\n[5/5] Quality checks...")

    # Check chunk text length
    text_lengths = [len(chunk.text) for chunk in chunks.values()]
    avg_length = sum(text_lengths) / len(text_lengths)
    min_length = min(text_lengths)
    max_length = max(text_lengths)

    print(f"  Chunk text lengths:")
    print(f"    Average: {avg_length:.0f} chars")
    print(f"    Min: {min_length} chars")
    print(f"    Max: {max_length} chars")

    if min_length < 100:
        print(f"⚠️  WARNING: Some chunks are very short (< 100 chars)")

    if avg_length < 300:
        print(f"⚠️  WARNING: Average chunk length is low (< 300 chars)")

    # Check IntegrityIndex
    if cpp.integrity_index:
        root_hash = cpp.integrity_index.blake2b_root
        print(f"\n  IntegrityIndex:")
        print(f"    blake2b_root: {root_hash[:16]}...")

        if root_hash == "0" * 64:
            print(f"❌ FAILURE: blake2b_root is dummy value")
            return False

        print(f"✅ IntegrityIndex validated")

    # Check QualityMetrics
    if cpp.quality_metrics:
        print(f"\n  QualityMetrics:")
        print(f"    provenance_completeness: {cpp.quality_metrics.provenance_completeness:.2%}")
        print(f"    structural_consistency: {cpp.quality_metrics.structural_consistency:.2%}")
        print(f"    boundary_f1: {cpp.quality_metrics.boundary_f1:.2%}")

        if cpp.quality_metrics.provenance_completeness < 0.9:
            print(f"⚠️  WARNING: Low provenance completeness")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - 60-CHUNK GENERATION VALIDATED")
    print("=" * 80)

    # Print distribution summary
    print("\nDistribution Summary:")
    print("\nChunks per Policy Area:")
    for pa, count in sorted(pa_counts.items()):
        print(f"  {pa}: {count} chunks")

    print("\nChunks per Dimension:")
    for dim, count in sorted(dim_counts.items()):
        print(f"  {dim}: {count} chunks")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_60_chunk_generation())
    sys.exit(0 if success else 1)
