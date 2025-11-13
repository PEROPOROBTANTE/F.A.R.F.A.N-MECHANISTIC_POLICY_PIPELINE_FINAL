"""
Example: Using the CPP Ingestion System

Demonstrates how to ingest a Development Plan document and work with
the resulting Canon Policy Package.
"""

from pathlib import Path
import tempfile
import json

from saaaaaa.processing.cpp_ingestion import (
    CPPIngestionPipeline,
    ChunkResolution,
    EdgeType,
)


def main():
    """Main example workflow."""
    
    print("=" * 70)
    print("CPP Ingestion System - Example Usage")
    print("=" * 70)
    print()
    
    # Step 1: Create a sample Development Plan document
    print("Step 1: Creating sample Development Plan document...")
    
    sample_content = """
    PLAN DE DESARROLLO MUNICIPAL 2024-2028
    "Hacia un Futuro Sostenible"
    
    EJE 1: DESARROLLO SOCIAL
    
    Programa 1.1: Educación de Calidad
    
    Objetivo: Mejorar la calidad educativa y aumentar la cobertura en el municipio.
    
    Proyecto 1.1.1: Mejoramiento de Infraestructura Educativa
    
    Descripción: Construcción y adecuación de instituciones educativas en zonas rurales.
    
    Meta: Aumentar la cobertura educativa del 85% al 95% para el año 2028.
    
    Indicador: Tasa de cobertura educativa
    Línea base (2023): 85%
    Meta 2028: 95%
    Unidad: Porcentaje
    
    Presupuesto Proyecto 1.1.1:
    Fuente: Transferencias SGP Educación
    Uso: Infraestructura educativa
    Monto: $5,000,000,000 COP
    Año: 2024-2026
    
    Marco Normativo:
    - Ley 715 de 2001 - Sistema General de Participaciones
    - Ley 1176 de 2007 - Artículo 16: Destinación de recursos SGP
    
    EJE 2: DESARROLLO ECONÓMICO
    
    Programa 2.1: Emprendimiento y Competitividad
    
    Objetivo: Fortalecer el ecosistema de emprendimiento local.
    
    Proyecto 2.1.1: Centro de Desarrollo Empresarial
    
    Meta: Crear 200 nuevas empresas formales entre 2024 y 2028.
    
    Indicador: Número de empresas formales creadas
    Línea base (2023): 50 empresas/año
    Meta 2028: 200 empresas (acumulado)
    
    Presupuesto Proyecto 2.1.1:
    Fuente: Recursos propios + Regalías
    Uso: Infraestructura y acompañamiento empresarial
    Monto: $3,500,000,000 COP
    Año: 2024-2028
    
    Territorio: Área urbana del municipio
    Departamento: Cundinamarca
    """
    
    # Create temporary PDF file (simplified - would be actual PDF in production)
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.txt', 
        delete=False, 
        encoding='utf-8'
    ) as f:
        # Note: In production, this would be a real PDF
        # We're using .txt for simplicity in this example
        f.write(sample_content)
        input_file = Path(f.name)
    
    print(f"✓ Sample document created: {input_file}")
    print()
    
    # Step 2: Initialize the ingestion pipeline
    print("Step 2: Initializing CPP ingestion pipeline...")
    
    pipeline = CPPIngestionPipeline(
        enable_ocr=False,  # Disable OCR for this example
        ocr_confidence_threshold=0.85,
        chunk_overlap_threshold=0.15,
    )
    
    print(f"✓ Pipeline initialized (schema: {pipeline.SCHEMA_VERSION})")
    print()
    
    # Step 3: Run ingestion
    print("Step 3: Running ingestion pipeline...")
    
    with tempfile.TemporaryDirectory() as output_dir:
        output_path = Path(output_dir)
        
        try:
            outcome = pipeline.ingest(input_file, output_path)
            
            print(f"✓ Ingestion completed with status: {outcome.status}")
            print()
            
            # Step 4: Examine results
            if outcome.status == "OK":
                print("Step 4: Examining ingestion results...")
                print()
                
                # Policy manifest
                print("Policy Manifest:")
                if outcome.policy_manifest:
                    print(f"  - Axes: {outcome.policy_manifest.axes}")
                    print(f"  - Programs: {outcome.policy_manifest.programs}")
                    print(f"  - Years: {outcome.policy_manifest.years}")
                    print(f"  - Territories: {outcome.policy_manifest.territories}")
                print()
                
                # Quality metrics
                print("Quality Metrics:")
                if outcome.metrics:
                    print(f"  - Boundary F1: {outcome.metrics.boundary_f1:.2f}")
                    print(f"  - KPI Linkage Rate: {outcome.metrics.kpi_linkage_rate:.2f}")
                    print(f"  - Budget Consistency: {outcome.metrics.budget_consistency_score:.2f}")
                    print(f"  - Provenance Completeness: {outcome.metrics.provenance_completeness:.2f}")
                print()
                
                # Fingerprints
                print("Pipeline Fingerprints:")
                for key, value in outcome.fingerprints.items():
                    print(f"  - {key}: {value}")
                print()
                
                # Output location
                print(f"CPP Output Location: {outcome.cpp_uri}")
                
                # Check what files were created
                if outcome.cpp_uri:
                    cpp_path = Path(outcome.cpp_uri)
                    if cpp_path.exists():
                        print("\nGenerated Files:")
                        for file in cpp_path.iterdir():
                            size = file.stat().st_size
                            print(f"  - {file.name} ({size:,} bytes)")
                        
                        # Show metadata
                        metadata_file = cpp_path / "metadata.json"
                        if metadata_file.exists():
                            print("\nMetadata Content:")
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                                print(json.dumps(metadata, indent=2))
                
            else:
                print("Step 4: Ingestion aborted")
                print("\nDiagnostics:")
                for diag in outcome.diagnostics:
                    print(f"  - {diag}")
            
        except Exception as e:
            print(f"✗ Error during ingestion: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            input_file.unlink()
    
    print()
    print("=" * 70)
    print("Example completed")
    print("=" * 70)


def demonstrate_chunk_queries():
    """Demonstrate querying chunks from a ChunkGraph."""
    from saaaaaa.processing.cpp_ingestion import ChunkGraph, Chunk, PolicyFacet, TimeFacet, GeoFacet, TextSpan
    
    print("\n" + "=" * 70)
    print("Chunk Query Examples")
    print("=" * 70)
    print()
    
    # Create sample chunk graph
    graph = ChunkGraph()
    
    # Add sample chunks
    for i in range(5):
        chunk = Chunk(
            id=f"chunk_{i:03d}",
            bytes_hash=f"hash_{i}",
            text_span=TextSpan(i * 100, (i + 1) * 100),
            resolution=ChunkResolution.MICRO if i < 3 else ChunkResolution.MESO,
            text=f"Sample chunk {i}",
            policy_facets=PolicyFacet(
                eje=f"Eje {(i % 2) + 1}",
                programa=f"Programa {i % 3}",
            ),
            time_facets=TimeFacet(from_year=2024, to_year=2028),
            geo_facets=GeoFacet(level="municipal"),
        )
        graph.add_chunk(chunk)
    
    # Add relationships
    graph.add_edge("chunk_000", "chunk_001", EdgeType.PRECEDES)
    graph.add_edge("chunk_001", "chunk_002", EdgeType.PRECEDES)
    graph.add_edge("chunk_003", "chunk_000", EdgeType.CONTAINS)
    
    print(f"Total chunks: {len(graph.chunks)}")
    print()
    
    # Query 1: Get all micro chunks
    print("Query 1: All MICRO resolution chunks")
    micro_chunks = [
        c for c in graph.chunks.values()
        if c.resolution == ChunkResolution.MICRO
    ]
    print(f"  Found {len(micro_chunks)} micro chunks")
    for chunk in micro_chunks[:3]:
        print(f"    - {chunk.id}: {chunk.text}")
    print()
    
    # Query 2: Get chunks by policy facet
    print("Query 2: Chunks in 'Eje 1'")
    eje1_chunks = [
        c for c in graph.chunks.values()
        if c.policy_facets.eje == "Eje 1"
    ]
    print(f"  Found {len(eje1_chunks)} chunks in Eje 1")
    for chunk in eje1_chunks:
        print(f"    - {chunk.id}: Program={chunk.policy_facets.programa}")
    print()
    
    # Query 3: Get neighbors
    print("Query 3: Navigate chunk relationships")
    chunk_id = "chunk_000"
    print(f"  Neighbors of {chunk_id}:")
    
    # Chunks that this precedes
    precedes = graph.get_neighbors(chunk_id, EdgeType.PRECEDES)
    if precedes:
        print(f"    Precedes: {precedes}")
    
    # Chunks that contain this
    containers = [
        src for src, tgt, etype in graph.edges
        if tgt == chunk_id and etype == EdgeType.CONTAINS
    ]
    if containers:
        print(f"    Contained by: {containers}")
    
    print()


if __name__ == "__main__":
    # Run main example
    main()
    
    # Run chunk query examples
    demonstrate_chunk_queries()
