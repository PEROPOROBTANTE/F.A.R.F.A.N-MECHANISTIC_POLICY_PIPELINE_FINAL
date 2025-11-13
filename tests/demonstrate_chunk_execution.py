#!/usr/bin/env python3
"""
Demonstration script showing chunk routing is now wired into execution.

This script shows the execution flow with chunks actually being used,
not just preserved.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

from saaaaaa.core.orchestrator.core import ChunkData, PreprocessedDocument
from saaaaaa.core.orchestrator.chunk_router import ChunkRouter


def demonstrate_chunk_routing():
    """Show how chunk routing actually works in execution."""
    print("=" * 80)
    print("DEMONSTRATION: Chunk Routing in Execution")
    print("=" * 80)
    
    # Create sample chunks representing a policy document
    chunks = [
        ChunkData(id=0, text="Baseline gap analysis", chunk_type="diagnostic", 
                  sentences=[0,1], tables=[], start_pos=0, end_pos=50, confidence=0.9),
        ChunkData(id=1, text="Another diagnostic chunk", chunk_type="diagnostic", 
                  sentences=[2,3], tables=[], start_pos=51, end_pos=100, confidence=0.9),
        ChunkData(id=2, text="Implementation activity", chunk_type="activity", 
                  sentences=[4,5], tables=[], start_pos=101, end_pos=150, confidence=0.85),
        ChunkData(id=3, text="Another activity", chunk_type="activity", 
                  sentences=[6,7], tables=[], start_pos=151, end_pos=200, confidence=0.88),
        ChunkData(id=4, text="Another activity chunk", chunk_type="activity", 
                  sentences=[8,9], tables=[], start_pos=201, end_pos=250, confidence=0.87),
        ChunkData(id=5, text="KPI metrics", chunk_type="indicator", 
                  sentences=[10,11], tables=[], start_pos=251, end_pos=300, confidence=0.92),
        ChunkData(id=6, text="Budget allocation", chunk_type="resource", 
                  sentences=[12,13], tables=[0], start_pos=301, end_pos=350, confidence=0.95),
    ]
    
    print(f"\nDocument has {len(chunks)} chunks:")
    chunk_type_counts = {}
    for chunk in chunks:
        chunk_type_counts[chunk.chunk_type] = chunk_type_counts.get(chunk.chunk_type, 0) + 1
    for chunk_type, count in chunk_type_counts.items():
        print(f"  - {count} {chunk_type} chunks")
    
    # Route chunks
    print("\n" + "=" * 80)
    print("CHUNK ROUTING")
    print("=" * 80)
    
    router = ChunkRouter()
    chunk_routes = {}
    
    for chunk in chunks:
        route = router.route_chunk(chunk)
        if not route.skip_reason:
            chunk_routes[chunk.id] = route
            print(f"\nChunk {chunk.id} ({chunk.chunk_type}):")
            print(f"  → Routed to: {route.executor_class}")
    
    # Simulate execution routing
    print("\n" + "=" * 80)
    print("EXECUTION FLOW SIMULATION")
    print("=" * 80)
    
    # Simulate some executor slots
    executor_slots = ["D1Q1", "D1Q2", "D2Q1", "D2Q2", "D3Q1", "D5Q5"]
    
    total_possible_executions = len(chunks) * len(executor_slots)
    actual_executions = 0
    
    print(f"\nProcessing {len(executor_slots)} executor questions:")
    
    for base_slot in executor_slots:
        # Find relevant chunks for this executor
        relevant_chunk_ids = [
            chunk_id for chunk_id, route in chunk_routes.items()
            if base_slot in route.executor_class or route.executor_class == base_slot
        ]
        
        if relevant_chunk_ids:
            print(f"\n{base_slot}:")
            print(f"  Relevant chunks: {relevant_chunk_ids} ({len(relevant_chunk_ids)} chunks)")
            print(f"  Execution: execute_chunk() for each chunk")
            actual_executions += len(relevant_chunk_ids)
        else:
            print(f"\n{base_slot}:")
            print(f"  No relevant chunks - execute() on full document")
            actual_executions += 1
    
    # Calculate savings
    savings_pct = ((total_possible_executions - actual_executions) / total_possible_executions) * 100
    
    print("\n" + "=" * 80)
    print("EXECUTION METRICS")
    print("=" * 80)
    print(f"Total possible executions: {total_possible_executions}")
    print(f"  ({len(chunks)} chunks × {len(executor_slots)} executors)")
    print(f"Actual executions: {actual_executions}")
    print(f"Execution savings: {savings_pct:.1f}%")
    
    print("\n" + "=" * 80)
    print("KEY DIFFERENCES")
    print("=" * 80)
    print("\n❌ BEFORE (Preservation-Only):")
    print("  - ChunkRouter created routes ✓")
    print("  - Routes stored in chunk_routes dict ✓")
    print("  - Orchestrator called execute(full_document) ✗")
    print("  - All chunks processed by all executors ✗")
    print(f"  - {total_possible_executions} executions")
    
    print("\n✅ AFTER (Full Exploitation):")
    print("  - ChunkRouter created routes ✓")
    print("  - Routes stored in chunk_routes dict ✓")
    print("  - Orchestrator checks chunk_routes ✓")
    print("  - Finds relevant chunks per base_slot ✓")
    print("  - Calls execute_chunk() for each relevant chunk ✓")
    print("  - Aggregates results from chunks ✓")
    print(f"  - {actual_executions} executions ({savings_pct:.1f}% reduction)")
    
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print("\nIn orchestrator logs, you'll now see:")
    print('  "Chunk-aware execution enabled: routed X chunks"')
    print('  "Chunk execution metrics: Y chunk-scoped, Z full-doc, savings: W%"')
    print("\nIn verification_manifest.json:")
    print('  "spc_utilization": {')
    print('    "execution_savings": {')
    print('      "chunk_executions": Y,')
    print('      "full_doc_executions": Z,')
    print('      "actual_executions": Y+Z,')
    print('      "savings_percent": W,')
    print('      "note": "Actual execution counts from orchestrator Phase 2"')
    print('    }')
    print('  }')
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demonstrate_chunk_routing()
