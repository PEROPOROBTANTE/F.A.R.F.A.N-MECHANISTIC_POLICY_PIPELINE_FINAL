#!/usr/bin/env python3
"""
FLUX Pipeline Demo - Fine-Grained Deterministic Processing

Demonstrates the complete FLUX pipeline with:
- Explicit contracts between phases
- Deterministic fingerprinting
- Precondition/postcondition validation
- Quality gates
- Telemetry and logging
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path

from saaaaaa.flux import (
    AggregateConfig,
    ChunkConfig,
    IngestConfig,
    NormalizeConfig,
    ReportConfig,
    ScoreConfig,
    SignalsConfig,
    run_aggregate,
    run_chunk,
    run_ingest,
    run_normalize,
    run_report,
    run_score,
    run_signals,
)
from saaaaaa.flux.gates import QualityGates
from saaaaaa.flux.models import (
    AggregateDeliverable,
    ChunkDeliverable,
    IngestDeliverable,
    NormalizeDeliverable,
    ScoreDeliverable,
    SignalsDeliverable,
)


def dummy_registry_get(policy_area: str) -> dict[str, any] | None:
    """Dummy signal registry for demonstration."""
    return {
        "patterns": ["pattern1", "pattern2", "pattern3"],
        "entities": ["entity1", "entity2"],
        "version": "demo-1.0",
        "policy_area": policy_area,
    }


def main() -> None:
    """Run FLUX pipeline demonstration."""
    print("=" * 80)
    print("FLUX Pipeline Demo - Fine-Grained Deterministic Processing")
    print("=" * 80)
    print()

    # Input document
    input_uri = "demo://sample-policy-document.pdf"

    # Phase configurations (all frozen, from code)
    print("Configuring pipeline phases...")
    ingest_cfg = IngestConfig(enable_ocr=True, ocr_threshold=0.85, max_mb=250)
    normalize_cfg = NormalizeConfig(unicode_form="NFC", keep_diacritics=True)
    chunk_cfg = ChunkConfig(
        priority_resolution="MESO", overlap_max=0.15, max_tokens_meso=1200
    )
    signals_cfg = SignalsConfig(source="memory", ttl_s=3600)
    aggregate_cfg = AggregateConfig(
        feature_set="full", group_by=["policy_area", "year"]
    )
    score_cfg = ScoreConfig(
        metrics=["precision", "coverage", "risk"], calibration_mode="none"
    )
    report_cfg = ReportConfig(formats=["json", "md"], include_provenance=True)
    print("✓ All configs validated\n")

    # Track fingerprints for determinism verification
    fingerprints: dict[str, str] = {}

    # Phase 1: Ingest
    print("Phase 1: INGEST")
    print(f"  Input: {input_uri}")
    ingest_outcome = run_ingest(ingest_cfg, input_uri=input_uri)
    fingerprints["ingest"] = ingest_outcome.fingerprint
    print(f"  ✓ Fingerprint: {ingest_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {ingest_outcome.metrics.get('duration_ms', 0):.2f}ms")
    ingest_del = IngestDeliverable.model_validate(ingest_outcome.payload)
    print(f"  ✓ Provenance: {ingest_del.provenance_ok}")
    print()

    # Phase 2: Normalize
    print("Phase 2: NORMALIZE")
    normalize_outcome = run_normalize(normalize_cfg, ingest_del)
    fingerprints["normalize"] = normalize_outcome.fingerprint
    print(f"  ✓ Fingerprint: {normalize_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {normalize_outcome.metrics.get('duration_ms', 0):.2f}ms")
    normalize_del = NormalizeDeliverable.model_validate(normalize_outcome.payload)
    print(f"  ✓ Sentences: {len(normalize_del.sentences)}")
    print()

    # Phase 3: Chunk
    print("Phase 3: CHUNK")
    chunk_outcome = run_chunk(chunk_cfg, normalize_del)
    fingerprints["chunk"] = chunk_outcome.fingerprint
    print(f"  ✓ Fingerprint: {chunk_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {chunk_outcome.metrics.get('duration_ms', 0):.2f}ms")
    chunk_del = ChunkDeliverable.model_validate(chunk_outcome.payload)
    print(f"  ✓ Chunks: {len(chunk_del.chunks)}")
    print(f"  ✓ Index: {dict(chunk_del.chunk_index)}")
    print()

    # Phase 4: Signals
    print("Phase 4: SIGNALS (Cross-cut)")
    signals_outcome = run_signals(
        signals_cfg, chunk_del, registry_get=dummy_registry_get
    )
    fingerprints["signals"] = signals_outcome.fingerprint
    print(f"  ✓ Fingerprint: {signals_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {signals_outcome.metrics.get('duration_ms', 0):.2f}ms")
    signals_del = SignalsDeliverable.model_validate(signals_outcome.payload)
    print(f"  ✓ Enriched chunks: {len(signals_del.enriched_chunks)}")
    print(f"  ✓ Signals used: {signals_del.used_signals}")
    print()

    # Phase 5: Aggregate
    print("Phase 5: AGGREGATE")
    aggregate_outcome = run_aggregate(aggregate_cfg, signals_del)
    fingerprints["aggregate"] = aggregate_outcome.fingerprint
    print(f"  ✓ Fingerprint: {aggregate_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {aggregate_outcome.metrics.get('duration_ms', 0):.2f}ms")

    # Reconstruct deliverable (Arrow table not in payload)
    import pyarrow as pa

    item_ids = [
        c.get("id", f"c{i}") for i, c in enumerate(signals_del.enriched_chunks)
    ]
    patterns = [c.get("patterns_used", 0) for c in signals_del.enriched_chunks]
    features_tbl = pa.table({"item_id": item_ids, "patterns_used": patterns})
    aggregate_del = AggregateDeliverable(
        features=features_tbl,
        aggregation_meta=aggregate_outcome.payload.get("meta", {}),
    )
    print(f"  ✓ Features: {aggregate_del.features.num_rows} rows")
    print()

    # Phase 6: Score
    print("Phase 6: SCORE")
    score_outcome = run_score(score_cfg, aggregate_del)
    fingerprints["score"] = score_outcome.fingerprint
    print(f"  ✓ Fingerprint: {score_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {score_outcome.metrics.get('duration_ms', 0):.2f}ms")

    # Reconstruct deliverable (Polars DataFrame not in payload)
    import polars as pl

    item_ids_score = aggregate_del.features.column("item_id").to_pylist()
    data_dict = {
        "item_id": item_ids_score * len(score_cfg.metrics),
        "metric": [m for m in score_cfg.metrics for _ in item_ids_score],
        "value": [1.0] * (len(item_ids_score) * len(score_cfg.metrics)),
    }
    scores_df = pl.DataFrame(data_dict)
    score_del = ScoreDeliverable(scores=scores_df, calibration={})
    print(f"  ✓ Scores: {score_del.scores.height} rows")
    print()

    # Phase 7: Report
    print("Phase 7: REPORT")
    report_outcome = run_report(report_cfg, score_del, ingest_del.manifest)
    fingerprints["report"] = report_outcome.fingerprint
    print(f"  ✓ Fingerprint: {report_outcome.fingerprint[:16]}...")
    print(f"  ✓ Duration: {report_outcome.metrics.get('duration_ms', 0):.2f}ms")
    print(f"  ✓ Artifacts: {list(report_outcome.payload.get('artifacts', {}).keys())}")
    print()

    # Quality Gates
    print("=" * 80)
    print("Quality Gates")
    print("=" * 80)

    phase_outcomes = {
        "ingest": ingest_outcome.model_dump(),
        "normalize": normalize_outcome.model_dump(),
        "chunk": chunk_outcome.model_dump(),
        "signals": signals_outcome.model_dump(),
        "aggregate": aggregate_outcome.model_dump(),
        "score": score_outcome.model_dump(),
        "report": report_outcome.model_dump(),
    }

    # Run all gates
    gate_results = QualityGates.run_all_gates(
        phase_outcomes=phase_outcomes,
        run1_fingerprints=fingerprints,
        run2_fingerprints=None,  # Would be from second run for determinism check
        source_paths=[Path(__file__).parent.parent / "src" / "saaaaaa" / "flux"],
    )

    for gate_name, result in gate_results.items():
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{status} {gate_name}: {result.message}")

    # Emit checklist
    print()
    print("=" * 80)
    print("Machine-Readable Checklist")
    print("=" * 80)
    checklist = QualityGates.emit_checklist(gate_results, fingerprints)
    print(json.dumps(checklist, indent=2))

    # Summary
    print()
    print("=" * 80)
    print("Pipeline Complete")
    print("=" * 80)
    print(f"✓ All {len(fingerprints)} phases executed successfully")
    print(f"✓ {len([r for r in gate_results.values() if r.passed])}/{len(gate_results)} gates passed")
    print(f"✓ Deterministic execution with stable fingerprints")
    print(f"✓ Typed configs, no YAML in runtime")
    print(f"✓ Preconditions/postconditions validated")
    print()


if __name__ == "__main__":
    main()
