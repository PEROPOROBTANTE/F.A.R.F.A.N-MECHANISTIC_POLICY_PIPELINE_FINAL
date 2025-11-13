#!/usr/bin/env python3
"""
Example: SPC Adapter Integration with Orchestrator

Demonstrates the complete flow from SPC ingestion to orchestrator execution:
1. Create a Canon Policy Package (SPC) from ingestion
2. Convert to PreprocessedDocument using SPCAdapter
3. Pass to orchestrator for analysis
4. Show how the data flows through the system

This example shows the real-world integration between:
- SPC/CPP ingestion pipeline
- SPCAdapter (conversion layer)
- Orchestrator (analysis engine)
"""

from saaaaaa.utils.spc_adapter import SPCAdapter
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
)


def create_development_plan_spc() -> CanonPolicyPackage:
    """
    Simulate output from SPC ingestion pipeline.
    
    In production, this would come from:
    - src/saaaaaa/processing/spc_ingestion/ 
    - smart_policy_chunks_canonic_phase_one.py
    
    Returns a realistic development plan with policy hierarchy.
    """
    chunks = []
    
    # Strategic level chunks (MACRO)
    chunks.append(Chunk(
        id="eje_desarrollo_social",
        bytes_hash="hash_1",
        text_span=TextSpan(start=0, end=200),
        resolution=ChunkResolution.MACRO,
        text="EJE ESTRATÉGICO 1: DESARROLLO SOCIAL Y HUMANO. Visión 2028: Construir una sociedad equitativa con acceso universal a servicios de calidad en educación, salud y vivienda.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Educación", "Salud", "Vivienda", "Cultura"],
            projects=[]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026, 2027, 2028]),
        geo_facets=GeoFacet(territories=["Departamental"], regions=["Todo el departamento"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.96),
        provenance={"page": 12, "section": "2.1", "parser": "strategic_chunking"},
    ))
    
    # Program level chunks (MESO)
    chunks.append(Chunk(
        id="programa_salud",
        bytes_hash="hash_2",
        text_span=TextSpan(start=201, end=450),
        resolution=ChunkResolution.MESO,
        text="Programa: Salud para Todos. Objetivo: Garantizar acceso universal a servicios de salud de calidad. Estrategia: Ampliación de red hospitalaria y fortalecimiento de atención primaria.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Salud para Todos"],
            projects=["Ampliación Hospitalaria", "Atención Primaria"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026]),
        geo_facets=GeoFacet(territories=["Urbano", "Rural"], regions=["Todas las subregiones"]),
        confidence=Confidence(layout=1.0, ocr=0.97, typing=0.94),
        provenance={"page": 15, "section": "2.1.2", "parser": "strategic_chunking"},
    ))
    
    # Project level chunks (MICRO) with detailed information
    chunks.append(Chunk(
        id="proyecto_hospital_regional",
        bytes_hash="hash_3",
        text_span=TextSpan(start=451, end=700),
        resolution=ChunkResolution.MICRO,
        text="Proyecto: Construcción Hospital Regional Norte. Construcción de hospital de tercer nivel con 150 camas y servicios especializados. Ubicación: Municipio de San Pedro. Beneficiarios: 250,000 habitantes.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Salud para Todos"],
            projects=["Construcción Hospital Regional Norte"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026]),
        geo_facets=GeoFacet(territories=["San Pedro"], regions=["Subregión Norte"]),
        confidence=Confidence(layout=1.0, ocr=0.99, typing=0.97),
        budget=BudgetInfo(
            source="Sistema General de Regalías",
            use="Infraestructura hospitalaria",
            amount=45000000000.0,  # 45 billion COP
            year=2024,
            currency="COP"
        ),
        provenance={"page": 18, "section": "2.1.2.1", "parser": "strategic_chunking"},
    ))
    
    chunks.append(Chunk(
        id="proyecto_centros_salud",
        bytes_hash="hash_4",
        text_span=TextSpan(start=701, end=950),
        resolution=ChunkResolution.MICRO,
        text="Proyecto: Centros de Atención Primaria en Zonas Rurales. Construcción y dotación de 20 centros de salud en veredas y corregimientos. Equipamiento médico básico y personal capacitado.",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social"],
            programs=["Salud para Todos"],
            projects=["Centros de Atención Primaria Rurales"]
        ),
        time_facets=TimeFacet(years=[2024, 2025]),
        geo_facets=GeoFacet(territories=["Rural"], regions=["Todas las subregiones"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.95),
        budget=BudgetInfo(
            source="Presupuesto Departamental",
            use="Atención primaria rural",
            amount=8000000000.0,  # 8 billion COP
            year=2024,
            currency="COP"
        ),
        provenance={"page": 19, "section": "2.1.2.2", "parser": "strategic_chunking"},
    ))
    
    # Build chunk graph
    chunk_graph = ChunkGraph()
    for chunk in chunks:
        chunk_graph.add_chunk(chunk)
    
    # Create realistic policy manifest
    policy_manifest = PolicyManifest(
        axes=1,
        programs=1,
        projects=2,
        years=[2024, 2025, 2026, 2027, 2028],
        territories=["Departamental", "Urbano", "Rural"],
        indicators=0,
        budget_rows=2,
    )
    
    # Realistic quality metrics
    quality_metrics = QualityMetrics(
        provenance_completeness=1.0,  # All chunks have provenance
        structural_consistency=0.95,
        boundary_f1=0.88,
        kpi_linkage_rate=0.0,
        budget_consistency_score=0.92,
        temporal_robustness=0.87,
        chunk_context_coverage=0.93,
    )
    
    # Integrity index
    integrity_index = IntegrityIndex(
        blake3_root="development_plan_2024_blake3_hash",
        chunk_hashes={chunk.id: chunk.bytes_hash for chunk in chunks}
    )
    
    # Complete SPC package
    return CanonPolicyPackage(
        schema_version="SPC-2025.1",
        policy_manifest=policy_manifest,
        chunk_graph=chunk_graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=quality_metrics,
        integrity_index=integrity_index,
        metadata={
            "document_title": "Plan de Desarrollo Departamental 2024-2028",
            "entity": "Gobernación Ejemplo",
            "period": "2024-2028",
            "total_budget": 53000000000.0,
        }
    )


def demonstrate_integration_flow():
    """
    Demonstrate the complete integration flow.
    
    Shows how data flows from:
    SPC Ingestion → SPCAdapter → PreprocessedDocument → Orchestrator
    """
    print("=" * 70)
    print("SPC ADAPTER - ORCHESTRATOR INTEGRATION")
    print("=" * 70)
    print()
    
    # PHASE 1: SPC Ingestion (Simulated)
    print("PHASE 1: SPC Ingestion")
    print("-" * 70)
    print("In production, this comes from spc_ingestion pipeline:")
    print("  - smart_policy_chunks_canonic_phase_one.py")
    print("  - StrategicChunkingSystem.process_document()")
    print()
    
    spc_package = create_development_plan_spc()
    print(f"✓ Created SPC package:")
    print(f"  - Schema version: {spc_package.schema_version}")
    print(f"  - Total chunks: {len(spc_package.chunk_graph.chunks)}")
    print(f"  - Provenance completeness: {spc_package.quality_metrics.provenance_completeness:.1%}")
    print(f"  - Budget items: {spc_package.policy_manifest.budget_rows}")
    print()
    
    # PHASE 2: Adapter Conversion
    print("PHASE 2: SPCAdapter Conversion")
    print("-" * 70)
    print("Converting SPC package to PreprocessedDocument format...")
    print()
    
    adapter = SPCAdapter()
    preprocessed_doc = adapter.to_preprocessed_document(
        spc_package,
        document_id="plan_desarrollo_departamental_2024"
    )
    
    print(f"✓ Conversion successful:")
    print(f"  - Document ID: {preprocessed_doc.document_id}")
    print(f"  - Sentences: {len(preprocessed_doc.sentences)}")
    print(f"  - Tables (budget): {len(preprocessed_doc.tables)}")
    print(f"  - Metadata keys: {list(preprocessed_doc.metadata.keys())}")
    print()
    
    # Show what the orchestrator receives
    print("PHASE 3: Orchestrator Input")
    print("-" * 70)
    print("The orchestrator receives a PreprocessedDocument with:")
    print()
    
    print("1. Structured sentences (chunks):")
    for i, sentence in enumerate(preprocessed_doc.sentences, 1):
        resolution = sentence.get('resolution', 'unknown')
        chunk_id = sentence.get('chunk_id', 'unknown')
        text_preview = sentence['text'][:50] + "..." if len(sentence['text']) > 50 else sentence['text']
        print(f"   {i}. [{resolution.upper():5}] {chunk_id}: {text_preview}")
    print()
    
    print("2. Budget tables (for financial analysis):")
    for i, table in enumerate(preprocessed_doc.tables, 1):
        print(f"   {i}. Source: {table['source']}")
        print(f"      Use: {table['use']}")
        print(f"      Amount: ${table['amount']:,.0f} {table['currency']}")
        print(f"      Year: {table['year']}")
    print()
    
    print("3. Policy metadata:")
    if "policy_manifest" in preprocessed_doc.metadata:
        manifest = preprocessed_doc.metadata["policy_manifest"]
        print(f"   - Strategic axes: {manifest['axes']}")
        print(f"   - Programs: {manifest['programs']}")
        print(f"   - Projects: {manifest['projects']}")
        print(f"   - Time period: {manifest['years'][0]}-{manifest['years'][-1]}")
        print(f"   - Territories: {', '.join(manifest['territories'])}")
    print()
    
    print("4. Quality indicators:")
    if "quality_metrics" in preprocessed_doc.metadata:
        metrics = preprocessed_doc.metadata["quality_metrics"]
        print(f"   - Provenance completeness: {metrics['provenance_completeness']:.1%}")
        print(f"   - Structural consistency: {metrics['structural_consistency']:.1%}")
        print(f"   - Budget consistency: {metrics['budget_consistency_score']:.1%}")
    print()
    
    # PHASE 4: Orchestrator Processing (Conceptual)
    print("PHASE 4: Orchestrator Processing")
    print("-" * 70)
    print("The orchestrator can now:")
    print("  1. Execute analysis phases on each chunk/sentence")
    print("  2. Apply calibration methods from calibration_registry")
    print("  3. Use resolution hierarchy (MACRO → MESO → MICRO)")
    print("  4. Link budget data to policy components")
    print("  5. Generate comprehensive analysis reports")
    print()
    
    # Show resolution-based processing example
    print("Example: Resolution-based Processing")
    print()
    
    # Group sentences by resolution
    by_resolution = {}
    for sentence in preprocessed_doc.sentences:
        res = sentence.get('resolution', 'unknown')
        if res not in by_resolution:
            by_resolution[res] = []
        by_resolution[res].append(sentence)
    
    print("  MACRO level (strategic axes):")
    if 'macro' in by_resolution:
        for s in by_resolution['macro']:
            print(f"    → Strategic analysis: {s['chunk_id']}")
    
    print()
    print("  MESO level (programs):")
    if 'meso' in by_resolution:
        for s in by_resolution['meso']:
            print(f"    → Program evaluation: {s['chunk_id']}")
    
    print()
    print("  MICRO level (projects):")
    if 'micro' in by_resolution:
        for s in by_resolution['micro']:
            print(f"    → Project assessment: {s['chunk_id']}")
            # Link to budget if available
            chunk_id = s['chunk_id']
            for table in preprocessed_doc.tables:
                if table.get('chunk_id') == chunk_id:
                    print(f"       Budget: ${table['amount']:,.0f} {table['currency']}")
    print()


def demonstrate_resolution_filtering():
    """
    Show how resolution filtering helps orchestrator focus on specific levels.
    """
    print("=" * 70)
    print("ADVANCED: RESOLUTION-BASED ORCHESTRATOR WORKFLOWS")
    print("=" * 70)
    print()
    
    spc_package = create_development_plan_spc()
    adapter = SPCAdapter()
    
    # Strategic analysis: MACRO only
    print("Workflow 1: Strategic Analysis (MACRO only)")
    print("-" * 70)
    doc_strategic = adapter.to_preprocessed_document(
        spc_package,
        document_id="strategic_view",
        preserve_chunk_resolution=ChunkResolution.MACRO
    )
    print(f"✓ Strategic view: {len(doc_strategic.sentences)} high-level chunks")
    print("  Use case: Executive summary, strategic alignment analysis")
    for sentence in doc_strategic.sentences:
        print(f"    → {sentence['chunk_id']}: {sentence['text'][:60]}...")
    print()
    
    # Program evaluation: MESO only
    print("Workflow 2: Program Evaluation (MESO only)")
    print("-" * 70)
    doc_program = adapter.to_preprocessed_document(
        spc_package,
        document_id="program_view",
        preserve_chunk_resolution=ChunkResolution.MESO
    )
    print(f"✓ Program view: {len(doc_program.sentences)} program-level chunks")
    print("  Use case: Program coherence, resource allocation analysis")
    for sentence in doc_program.sentences:
        print(f"    → {sentence['chunk_id']}: {sentence['text'][:60]}...")
    print()
    
    # Project analysis: MICRO only
    print("Workflow 3: Project Analysis (MICRO only)")
    print("-" * 70)
    doc_project = adapter.to_preprocessed_document(
        spc_package,
        document_id="project_view",
        preserve_chunk_resolution=ChunkResolution.MICRO
    )
    print(f"✓ Project view: {len(doc_project.sentences)} detailed project chunks")
    print(f"✓ Budget tables: {len(doc_project.tables)} entries")
    print("  Use case: Detailed feasibility, budget execution tracking")
    for sentence in doc_project.sentences:
        print(f"    → {sentence['chunk_id']}: {sentence['text'][:60]}...")
    print()


def main():
    """Run integration examples."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 8 + "SPC ADAPTER - ORCHESTRATOR INTEGRATION" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Main integration flow
    demonstrate_integration_flow()
    
    # Advanced resolution filtering
    demonstrate_resolution_filtering()
    
    print("=" * 70)
    print("INTEGRATION SUMMARY")
    print("=" * 70)
    print()
    print("Key Integration Points:")
    print("  1. ✓ SPC ingestion produces CanonPolicyPackage")
    print("  2. ✓ SPCAdapter converts to PreprocessedDocument")
    print("  3. ✓ Orchestrator receives structured, validated data")
    print("  4. ✓ Resolution hierarchy enables targeted analysis")
    print("  5. ✓ Budget data and metadata flow through seamlessly")
    print()
    print("Production Workflow:")
    print("  Input → SPC Ingestion → SPCAdapter → Orchestrator → Reports")
    print()
    print("Integration complete! ✓")
    print()


if __name__ == "__main__":
    main()
