#!/usr/bin/env python3
"""
Example: Using the SPC (Smart Policy Chunks) Adapter

Demonstrates how to convert a Canon Policy Package (CPP) / Smart Policy Chunks (SPC)
to PreprocessedDocument format for the orchestrator, using the new SPC terminology.

This example shows:
1. Creating a sample SPC/CPP package with real policy content
2. Converting it to PreprocessedDocument using SPCAdapter
3. Inspecting the converted document structure
4. Filtering by chunk resolution (MICRO/MESO/MACRO)
"""

from saaaaaa.utils.spc_adapter import SPCAdapter, adapt_spc_to_orchestrator
from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    Confidence,
    PolicyFacet,
    PolicyManifest,
    ProvenanceMap,
    QualityMetrics,
    TextSpan,
    TimeFacet,
    GeoFacet,
    IntegrityIndex,
    BudgetInfo,
    KPIInfo,
)


def create_sample_spc_package() -> CanonPolicyPackage:
    """
    Create a sample SPC/CPP package representing a development plan.
    
    This simulates output from the SPC ingestion pipeline with:
    - Policy chunks at different resolutions (MICRO, MESO, MACRO)
    - Budget information
    - KPI indicators
    - Policy facets (axes, programs, projects)
    - Quality metrics
    """
    print("Creating sample SPC package...")
    
    # Create chunks representing a development plan
    chunks = []
    
    # MACRO chunk: High-level development axis
    macro_chunk = Chunk(
        id="plan_eje_1",
        bytes_hash="hash_macro_1",
        text_span=TextSpan(start=0, end=150),
        resolution=ChunkResolution.MACRO,
        text="EJE 1: DESARROLLO SOCIAL. Objetivo: Mejorar la calidad de vida de la población a través de programas sociales integrales que garanticen el acceso a servicios básicos.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Educación", "Salud", "Vivienda"],
            projects=[]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026, 2027, 2028]),
        geo_facets=GeoFacet(territories=["Municipal"], regions=["Toda la región"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.95),
    )
    chunks.append(macro_chunk)
    
    # MESO chunk: Program level
    meso_chunk = Chunk(
        id="programa_1_1",
        bytes_hash="hash_meso_1",
        text_span=TextSpan(start=151, end=350),
        resolution=ChunkResolution.MESO,
        text="Programa 1.1: Educación de Calidad. Estrategia: Mejorar infraestructura educativa y capacitación docente. Meta general: Aumentar cobertura educativa del 85% al 95% para 2028.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Educación de Calidad"],
            projects=["Mejoramiento Infraestructura", "Capacitación Docente"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026, 2027, 2028]),
        geo_facets=GeoFacet(territories=["Municipal", "Rural"], regions=["Zona Norte", "Zona Sur"]),
        confidence=Confidence(layout=1.0, ocr=0.97, typing=0.93),
        kpi=KPIInfo(
            name="Tasa de cobertura educativa",
            baseline=85.0,
            target=95.0,
            unit="%"
        ),
    )
    chunks.append(meso_chunk)
    
    # MICRO chunk: Specific project with budget
    micro_chunk_1 = Chunk(
        id="proyecto_1_1_1",
        bytes_hash="hash_micro_1",
        text_span=TextSpan(start=351, end=550),
        resolution=ChunkResolution.MICRO,
        text="Proyecto 1.1.1: Mejoramiento de Infraestructura Educativa. Construcción de 3 nuevas escuelas en zonas rurales. Presupuesto asignado: $1,500,000,000 COP para el periodo 2024-2026.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Educación de Calidad"],
            projects=["Mejoramiento Infraestructura Educativa"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026]),
        geo_facets=GeoFacet(territories=["Rural"], regions=["Zona Norte"]),
        confidence=Confidence(layout=1.0, ocr=0.99, typing=0.96),
        budget=BudgetInfo(
            source="Presupuesto Municipal",
            use="Construcción escuelas",
            amount=1500000000.0,
            year=2024,
            currency="COP"
        ),
        provenance={"page": 5, "section": "1.1.1", "parser": "strategic_chunking"},
    )
    chunks.append(micro_chunk_1)
    
    # MICRO chunk: Another project
    micro_chunk_2 = Chunk(
        id="proyecto_1_1_2",
        bytes_hash="hash_micro_2",
        text_span=TextSpan(start=551, end=720),
        resolution=ChunkResolution.MICRO,
        text="Proyecto 1.1.2: Capacitación Docente. Formación continua para 200 docentes en metodologías pedagógicas innovadoras. Inversión: $300,000,000 COP.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Educación de Calidad"],
            projects=["Capacitación Docente"]
        ),
        time_facets=TimeFacet(years=[2024, 2025]),
        geo_facets=GeoFacet(territories=["Municipal"], regions=["Toda la región"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.94),
        budget=BudgetInfo(
            source="Presupuesto Municipal",
            use="Formación docente",
            amount=300000000.0,
            year=2024,
            currency="COP"
        ),
        provenance={"page": 6, "section": "1.1.2", "parser": "strategic_chunking"},
    )
    chunks.append(micro_chunk_2)
    
    # Build chunk graph
    chunk_graph = ChunkGraph()
    for chunk in chunks:
        chunk_graph.add_chunk(chunk)
    
    # Create policy manifest
    policy_manifest = PolicyManifest(
        axes=1,
        programs=1,
        projects=2,
        years=[2024, 2025, 2026, 2027, 2028],
        territories=["Municipal", "Rural"],
        indicators=1,
        budget_rows=2,
    )
    
    # Create quality metrics
    quality_metrics = QualityMetrics(
        provenance_completeness=0.5,  # 2 out of 4 chunks have provenance
        structural_consistency=0.95,
        boundary_f1=0.88,
        kpi_linkage_rate=0.25,  # 1 out of 4 chunks has KPI
        budget_consistency_score=0.92,
        temporal_robustness=0.85,
        chunk_context_coverage=0.90,
    )
    
    # Create integrity index
    integrity_index = IntegrityIndex(
        blake3_root="sample_plan_2024_blake3_root_hash",
        chunk_hashes={
            "plan_eje_1": "hash_macro_1",
            "programa_1_1": "hash_meso_1",
            "proyecto_1_1_1": "hash_micro_1",
            "proyecto_1_1_2": "hash_micro_2",
        }
    )
    
    # Build the complete package
    package = CanonPolicyPackage(
        schema_version="SPC-2025.1",
        policy_manifest=policy_manifest,
        chunk_graph=chunk_graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=quality_metrics,
        integrity_index=integrity_index,
        metadata={
            "document_title": "Plan de Desarrollo Municipal 2024-2028",
            "municipality": "Example Municipality",
            "source": "Official Development Plan",
        }
    )
    
    print(f"✓ Created SPC package with {len(chunks)} chunks")
    print(f"  - 1 MACRO chunk (development axis)")
    print(f"  - 1 MESO chunk (program)")
    print(f"  - 2 MICRO chunks (projects)")
    print()
    
    return package


def example_1_basic_conversion():
    """Example 1: Basic conversion with SPCAdapter."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Conversion with SPCAdapter")
    print("=" * 70)
    print()
    
    # Create sample package
    spc_package = create_sample_spc_package()
    
    # Create adapter
    adapter = SPCAdapter()
    print("Creating SPCAdapter instance...")
    
    # Convert to PreprocessedDocument
    print("Converting SPC package to PreprocessedDocument...")
    doc = adapter.to_preprocessed_document(
        spc_package,
        document_id="plan_desarrollo_2024"
    )
    
    print(f"✓ Conversion successful!")
    print()
    print(f"PreprocessedDocument details:")
    print(f"  - Document ID: {doc.document_id}")
    print(f"  - Sentences/chunks: {len(doc.sentences)}")
    print(f"  - Tables (budget data): {len(doc.tables)}")
    print(f"  - Raw text length: {len(doc.raw_text)} characters")
    print()
    
    # Inspect metadata
    print("Metadata:")
    print(f"  - Schema version: {doc.metadata['schema_version']}")
    print(f"  - Total chunks: {doc.metadata['total_chunks']}")
    print(f"  - Provenance completeness: {doc.metadata['provenance_completeness']:.1%}")
    print()
    
    # Show policy manifest
    if "policy_manifest" in doc.metadata:
        manifest = doc.metadata["policy_manifest"]
        print("Policy Manifest:")
        print(f"  - Axes: {manifest['axes']}")
        print(f"  - Programs: {manifest['programs']}")
        print(f"  - Projects: {manifest['projects']}")
        print(f"  - Years: {manifest['years']}")
        print(f"  - Budget rows: {manifest['budget_rows']}")
    print()
    
    # Show quality metrics
    if "quality_metrics" in doc.metadata:
        metrics = doc.metadata["quality_metrics"]
        print("Quality Metrics:")
        print(f"  - Structural consistency: {metrics['structural_consistency']:.2%}")
        print(f"  - Boundary F1: {metrics['boundary_f1']:.2%}")
        print(f"  - Budget consistency: {metrics['budget_consistency_score']:.2%}")
    print()
    
    return doc


def example_2_resolution_filtering():
    """Example 2: Filtering by chunk resolution."""
    print("=" * 70)
    print("EXAMPLE 2: Filtering by Chunk Resolution")
    print("=" * 70)
    print()
    
    spc_package = create_sample_spc_package()
    adapter = SPCAdapter()
    
    # Convert with MICRO resolution only
    print("Converting with MICRO resolution filter (projects only)...")
    doc_micro = adapter.to_preprocessed_document(
        spc_package,
        document_id="plan_micro_only",
        preserve_chunk_resolution=ChunkResolution.MICRO
    )
    
    print(f"✓ MICRO chunks: {len(doc_micro.sentences)} chunks")
    for i, sentence in enumerate(doc_micro.sentences, 1):
        print(f"  {i}. {sentence['chunk_id']}: {sentence['text'][:60]}...")
    print()
    
    # Convert with MESO resolution only
    print("Converting with MESO resolution filter (programs only)...")
    doc_meso = adapter.to_preprocessed_document(
        spc_package,
        document_id="plan_meso_only",
        preserve_chunk_resolution=ChunkResolution.MESO
    )
    
    print(f"✓ MESO chunks: {len(doc_meso.sentences)} chunks")
    for i, sentence in enumerate(doc_meso.sentences, 1):
        print(f"  {i}. {sentence['chunk_id']}: {sentence['text'][:60]}...")
    print()
    
    # Convert with MACRO resolution only
    print("Converting with MACRO resolution filter (axes only)...")
    doc_macro = adapter.to_preprocessed_document(
        spc_package,
        document_id="plan_macro_only",
        preserve_chunk_resolution=ChunkResolution.MACRO
    )
    
    print(f"✓ MACRO chunks: {len(doc_macro.sentences)} chunks")
    for i, sentence in enumerate(doc_macro.sentences, 1):
        print(f"  {i}. {sentence['chunk_id']}: {sentence['text'][:60]}...")
    print()


def example_3_convenience_function():
    """Example 3: Using convenience function."""
    print("=" * 70)
    print("EXAMPLE 3: Using Convenience Function")
    print("=" * 70)
    print()
    
    spc_package = create_sample_spc_package()
    
    print("Using adapt_spc_to_orchestrator() convenience function...")
    doc = adapt_spc_to_orchestrator(
        spc_package,
        document_id="plan_convenience"
    )
    
    print(f"✓ Conversion successful!")
    print(f"  - Document ID: {doc.document_id}")
    print(f"  - Chunks: {len(doc.sentences)}")
    print()
    
    # Show chunk details
    print("Chunk details:")
    for chunk_meta in doc.metadata["chunks"]:
        print(f"  - {chunk_meta['id']}: resolution={chunk_meta['resolution']}, "
              f"has_budget={chunk_meta['has_budget']}, has_kpi={chunk_meta['has_kpi']}")
    print()


def main():
    """Run all examples."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SPC ADAPTER - USAGE EXAMPLES" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Example 1: Basic conversion
    example_1_basic_conversion()
    
    # Example 2: Resolution filtering
    example_2_resolution_filtering()
    
    # Example 3: Convenience function
    example_3_convenience_function()
    
    print("=" * 70)
    print("All examples completed successfully! ✓")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. SPCAdapter converts SPC/CPP packages to PreprocessedDocument")
    print("  2. Can filter by resolution (MICRO/MESO/MACRO) for different views")
    print("  3. Preserves all metadata: policy manifest, quality metrics, etc.")
    print("  4. Extracts budget data and KPIs automatically")
    print("  5. Convenience function available for simple use cases")
    print()


if __name__ == "__main__":
    main()
