#!/usr/bin/env python3
"""
Real-World Scenario: Complete Policy Analysis Pipeline

This example demonstrates a complete, realistic workflow of analyzing a 
Colombian development plan using the SPC adapter and orchestrator integration.

Scenario: A policy analyst needs to:
1. Ingest a municipal development plan PDF
2. Extract and structure policy information
3. Analyze budget allocation and strategic coherence
4. Generate actionable insights and reports

This shows the real value proposition of the SPC/CPP system.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

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
    KPIInfo,
)


@dataclass
class AnalysisInsight:
    """Represents an insight from policy analysis."""
    category: str
    level: str  # MACRO, MESO, MICRO
    message: str
    severity: str  # INFO, WARNING, CRITICAL
    evidence: str


def create_realistic_development_plan() -> CanonPolicyPackage:
    """
    Create a realistic development plan based on actual Colombian PDM structure.
    
    This simulates the output from the SPC ingestion pipeline for:
    "Plan de Desarrollo Municipal: Valle Hermoso 2024-2028"
    """
    chunks = []
    
    # MACRO: Strategic Axis 1 - Social Development
    chunks.append(Chunk(
        id="eje_1_desarrollo_social",
        bytes_hash="hash_eje1",
        text_span=TextSpan(start=0, end=250),
        resolution=ChunkResolution.MACRO,
        text="""EJE ESTRATÉGICO 1: DESARROLLO SOCIAL Y CALIDAD DE VIDA
Objetivo General: Garantizar el bienestar integral de la población mediante el acceso equitativo a servicios de educación, salud, cultura y deporte, con enfoque diferencial y territorial.
Presupuesto: $85,000,000,000 COP (38% del presupuesto total)""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social y Calidad de Vida"],
            programs=["Educación", "Salud", "Cultura", "Deporte"],
            projects=[]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026, 2027, 2028]),
        geo_facets=GeoFacet(territories=["Municipal"], regions=["Urbano y Rural"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.96),
        provenance={"page": 25, "section": "3.1", "parser": "strategic_chunking"},
    ))
    
    # MACRO: Strategic Axis 2 - Economic Development
    chunks.append(Chunk(
        id="eje_2_desarrollo_economico",
        bytes_hash="hash_eje2",
        text_span=TextSpan(start=251, end=450),
        resolution=ChunkResolution.MACRO,
        text="""EJE ESTRATÉGICO 2: DESARROLLO ECONÓMICO SOSTENIBLE
Objetivo General: Fortalecer las cadenas productivas locales y promover el emprendimiento, con énfasis en agricultura sostenible y turismo rural.
Presupuesto: $45,000,000,000 COP (20% del presupuesto total)""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Económico Sostenible"],
            programs=["Agricultura", "Turismo", "Emprendimiento"],
            projects=[]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026, 2027, 2028]),
        geo_facets=GeoFacet(territories=["Municipal"], regions=["Rural principalmente"]),
        confidence=Confidence(layout=1.0, ocr=0.97, typing=0.95),
        provenance={"page": 42, "section": "3.2", "parser": "strategic_chunking"},
    ))
    
    # MESO: Education Program
    chunks.append(Chunk(
        id="programa_educacion_calidad",
        bytes_hash="hash_prog1",
        text_span=TextSpan(start=451, end=700),
        resolution=ChunkResolution.MESO,
        text="""Programa 1.1: Educación de Calidad para Todos
Meta: Aumentar cobertura educativa del 82% al 95% y mejorar resultados en Pruebas Saber.
Estrategia: Infraestructura educativa, capacitación docente, alimentación escolar y transporte.
Presupuesto: $35,000,000,000 COP""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social y Calidad de Vida"],
            programs=["Educación de Calidad para Todos"],
            projects=["Infraestructura Educativa", "Capacitación Docente", "PAE"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026, 2027, 2028]),
        geo_facets=GeoFacet(territories=["Municipal", "Rural"], regions=["Todas"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.94),
        kpi=KPIInfo(
            name="Cobertura educativa",
            baseline=82.0,
            target=95.0,
            unit="%"
        ),
        provenance={"page": 28, "section": "3.1.1", "parser": "strategic_chunking"},
    ))
    
    # MESO: Health Program
    chunks.append(Chunk(
        id="programa_salud_todos",
        bytes_hash="hash_prog2",
        text_span=TextSpan(start=701, end=950),
        resolution=ChunkResolution.MESO,
        text="""Programa 1.2: Salud Para Todos
Meta: Reducir mortalidad infantil de 15 a 8 por cada 1,000 nacidos vivos.
Estrategia: Ampliación red hospitalaria, programas de prevención y vacunación.
Presupuesto: $28,000,000,000 COP""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social y Calidad de Vida"],
            programs=["Salud Para Todos"],
            projects=["Hospital Rural", "Centros de Salud", "Vacunación"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026]),
        geo_facets=GeoFacet(territories=["Municipal", "Rural"], regions=["Todas"]),
        confidence=Confidence(layout=1.0, ocr=0.97, typing=0.93),
        kpi=KPIInfo(
            name="Mortalidad infantil",
            baseline=15.0,
            target=8.0,
            unit="por 1000"
        ),
        provenance={"page": 32, "section": "3.1.2", "parser": "strategic_chunking"},
    ))
    
    # MICRO: School Infrastructure Project
    chunks.append(Chunk(
        id="proyecto_escuelas_rurales",
        bytes_hash="hash_proy1",
        text_span=TextSpan(start=951, end=1200),
        resolution=ChunkResolution.MICRO,
        text="""Proyecto 1.1.1: Construcción y Mejoramiento de Escuelas Rurales
Descripción: Construcción de 2 nuevas escuelas y mejoramiento de 8 existentes en veredas.
Beneficiarios: 1,200 estudiantes en zona rural.
Ubicación: Veredas El Bosque, La Esperanza, San Isidro y otras.
Monto: $15,000,000,000 COP
Fuente: Sistema General de Participaciones (70%) y Recursos Propios (30%)""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social y Calidad de Vida"],
            programs=["Educación de Calidad para Todos"],
            projects=["Infraestructura Educativa Rural"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026]),
        geo_facets=GeoFacet(
            territories=["Rural"],
            regions=["El Bosque", "La Esperanza", "San Isidro"]
        ),
        confidence=Confidence(layout=1.0, ocr=0.99, typing=0.97),
        budget=BudgetInfo(
            source="SGP 70% + Recursos Propios 30%",
            use="Construcción y mejoramiento escuelas rurales",
            amount=15000000000.0,
            year=2024,
            currency="COP"
        ),
        provenance={"page": 29, "section": "3.1.1.1", "parser": "strategic_chunking"},
    ))
    
    # MICRO: Teacher Training Project
    chunks.append(Chunk(
        id="proyecto_capacitacion_docente",
        bytes_hash="hash_proy2",
        text_span=TextSpan(start=1201, end=1450),
        resolution=ChunkResolution.MICRO,
        text="""Proyecto 1.1.2: Formación Continua para Docentes
Descripción: Programa de capacitación en metodologías activas y TIC para 150 docentes.
Modalidad: Diplomados presenciales y virtuales.
Alianza: Universidad Regional y Ministerio de Educación.
Monto: $800,000,000 COP""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social y Calidad de Vida"],
            programs=["Educación de Calidad para Todos"],
            projects=["Capacitación Docente en Metodologías Activas"]
        ),
        time_facets=TimeFacet(years=[2024, 2025]),
        geo_facets=GeoFacet(territories=["Municipal"], regions=["Todas"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.96),
        budget=BudgetInfo(
            source="Recursos Propios",
            use="Formación docente",
            amount=800000000.0,
            year=2024,
            currency="COP"
        ),
        provenance={"page": 30, "section": "3.1.1.2", "parser": "strategic_chunking"},
    ))
    
    # MICRO: Rural Hospital Project
    chunks.append(Chunk(
        id="proyecto_hospital_rural",
        bytes_hash="hash_proy3",
        text_span=TextSpan(start=1451, end=1700),
        resolution=ChunkResolution.MICRO,
        text="""Proyecto 1.2.1: Hospital Rural Integrado
Descripción: Construcción hospital de primer nivel con servicios de urgencias, consulta externa y hospitalización.
Capacidad: 30 camas, atención 24/7.
Beneficiarios: 45,000 habitantes zona rural.
Monto: $12,000,000,000 COP
Fuente: Sistema General de Regalías""",
        policy_facets=PolicyFacet(
            axes=["Desarrollo Social y Calidad de Vida"],
            programs=["Salud Para Todos"],
            projects=["Hospital Rural Integrado"]
        ),
        time_facets=TimeFacet(years=[2024, 2025, 2026]),
        geo_facets=GeoFacet(territories=["Rural"], regions=["Zona Norte Rural"]),
        confidence=Confidence(layout=1.0, ocr=0.99, typing=0.97),
        budget=BudgetInfo(
            source="Sistema General de Regalías",
            use="Construcción hospital rural",
            amount=12000000000.0,
            year=2024,
            currency="COP"
        ),
        provenance={"page": 33, "section": "3.1.2.1", "parser": "strategic_chunking"},
    ))
    
    # Build complete SPC package
    chunk_graph = ChunkGraph()
    for chunk in chunks:
        chunk_graph.add_chunk(chunk)
    
    policy_manifest = PolicyManifest(
        axes=2,
        programs=2,
        projects=4,
        years=[2024, 2025, 2026, 2027, 2028],
        territories=["Municipal", "Rural", "Urbano"],
        indicators=2,
        budget_rows=4,
    )
    
    quality_metrics = QualityMetrics(
        provenance_completeness=1.0,
        structural_consistency=0.96,
        boundary_f1=0.89,
        kpi_linkage_rate=0.29,  # 2 out of 7 chunks have KPIs
        budget_consistency_score=0.94,
        temporal_robustness=0.88,
        chunk_context_coverage=0.92,
    )
    
    integrity_index = IntegrityIndex(
        blake3_root="valle_hermoso_2024_blake3",
        chunk_hashes={chunk.id: chunk.bytes_hash for chunk in chunks}
    )
    
    return CanonPolicyPackage(
        schema_version="SPC-2025.1",
        policy_manifest=policy_manifest,
        chunk_graph=chunk_graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=quality_metrics,
        integrity_index=integrity_index,
        metadata={
            "document_title": "Plan de Desarrollo Municipal: Valle Hermoso 2024-2028",
            "municipality": "Valle Hermoso",
            "department": "Ejemplo",
            "period": "2024-2028",
            "total_budget": 225000000000.0,  # 225 billion COP
            "mayor": "Alcaldía Municipal",
            "approval_date": "2024-06-15",
        }
    )


def analyze_budget_distribution(doc) -> List[AnalysisInsight]:
    """Analyze budget distribution across policy hierarchy."""
    insights = []
    
    # Calculate total budget
    total_budget = sum(table['amount'] for table in doc.tables)
    
    # Analyze distribution
    if len(doc.tables) > 0:
        insights.append(AnalysisInsight(
            category="Budget",
            level="MICRO",
            message=f"Total allocated budget: ${total_budget:,.0f} COP across {len(doc.tables)} projects",
            severity="INFO",
            evidence=f"{len(doc.tables)} budget entries identified"
        ))
        
        # Check for concentration
        max_amount = max(table['amount'] for table in doc.tables)
        if max_amount / total_budget > 0.5:
            insights.append(AnalysisInsight(
                category="Budget",
                level="MICRO",
                message="High budget concentration detected: Single project receives >50% of funds",
                severity="WARNING",
                evidence=f"Largest project: ${max_amount:,.0f} COP ({max_amount/total_budget:.1%})"
            ))
    
    return insights


def analyze_strategic_coherence(doc) -> List[AnalysisInsight]:
    """Analyze strategic coherence across resolution levels."""
    insights = []
    
    # Count chunks by resolution
    by_resolution = {}
    for sentence in doc.sentences:
        res = sentence.get('resolution', 'unknown')
        by_resolution[res] = by_resolution.get(res, 0) + 1
    
    macro_count = by_resolution.get('macro', 0)
    meso_count = by_resolution.get('meso', 0)
    micro_count = by_resolution.get('micro', 0)
    
    # Check pyramid structure
    if macro_count > 0 and meso_count > 0 and micro_count > 0:
        insights.append(AnalysisInsight(
            category="Structure",
            level="MACRO",
            message=f"Complete policy hierarchy detected: {macro_count} axes → {meso_count} programs → {micro_count} projects",
            severity="INFO",
            evidence="All three resolution levels present"
        ))
        
        # Check ratios
        if micro_count / meso_count < 1.5:
            insights.append(AnalysisInsight(
                category="Structure",
                level="MESO",
                message="Low project density: Each program has <2 projects on average",
                severity="WARNING",
                evidence=f"Ratio: {micro_count} projects / {meso_count} programs = {micro_count/meso_count:.1f}"
            ))
    
    return insights


def analyze_kpi_coverage(doc) -> List[AnalysisInsight]:
    """Analyze KPI and indicator coverage."""
    insights = []
    
    # Count chunks with KPIs
    chunks_with_kpi = 0
    for chunk_meta in doc.metadata.get("chunks", []):
        if chunk_meta.get("has_kpi", False):
            chunks_with_kpi += 1
    
    total_chunks = len(doc.metadata.get("chunks", []))
    kpi_rate = chunks_with_kpi / total_chunks if total_chunks > 0 else 0
    
    if kpi_rate < 0.3:
        insights.append(AnalysisInsight(
            category="Measurement",
            level="MESO",
            message=f"Low KPI coverage: Only {kpi_rate:.1%} of chunks have measurable indicators",
            severity="CRITICAL",
            evidence=f"{chunks_with_kpi} out of {total_chunks} chunks have KPIs"
        ))
    else:
        insights.append(AnalysisInsight(
            category="Measurement",
            level="MESO",
            message=f"Adequate KPI coverage: {kpi_rate:.1%} of chunks have indicators",
            severity="INFO",
            evidence=f"{chunks_with_kpi} KPIs identified"
        ))
    
    return insights


def generate_analysis_report(insights: List[AnalysisInsight]) -> None:
    """Generate a formatted analysis report."""
    print("=" * 70)
    print("POLICY ANALYSIS REPORT")
    print("=" * 70)
    print()
    
    # Group by severity
    critical = [i for i in insights if i.severity == "CRITICAL"]
    warnings = [i for i in insights if i.severity == "WARNING"]
    info = [i for i in insights if i.severity == "INFO"]
    
    if critical:
        print("🔴 CRITICAL FINDINGS:")
        for insight in critical:
            print(f"   [{insight.category}] {insight.message}")
            print(f"      Evidence: {insight.evidence}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for insight in warnings:
            print(f"   [{insight.category}] {insight.message}")
            print(f"      Evidence: {insight.evidence}")
        print()
    
    if info:
        print("ℹ️  INFORMATION:")
        for insight in info:
            print(f"   [{insight.category}] {insight.message}")
        print()


def main():
    """Execute complete real-world scenario."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "REAL-WORLD SCENARIO: POLICY ANALYSIS" + " " * 20 + "║")
    print("║" + " " * 10 + "Plan de Desarrollo Municipal Valle Hermoso" + " " * 16 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # STEP 1: Ingestion (simulated)
    print("STEP 1: Policy Document Ingestion")
    print("-" * 70)
    print("Input: 'Plan_Valle_Hermoso_2024-2028.pdf' (150 pages)")
    print("Processing: SPC ingestion pipeline...")
    print()
    
    spc_package = create_realistic_development_plan()
    print(f"✓ Ingestion complete:")
    print(f"  - Document: {spc_package.metadata['document_title']}")
    print(f"  - Municipality: {spc_package.metadata['municipality']}")
    print(f"  - Period: {spc_package.metadata['period']}")
    print(f"  - Total budget: ${spc_package.metadata['total_budget']:,.0f} COP")
    print(f"  - Chunks extracted: {len(spc_package.chunk_graph.chunks)}")
    print(f"  - Quality score: {spc_package.quality_metrics.structural_consistency:.1%}")
    print()
    
    # STEP 2: Conversion
    print("STEP 2: Conversion to Analysis Format")
    print("-" * 70)
    print("Using SPCAdapter to prepare for orchestrator...")
    print()
    
    adapter = SPCAdapter()
    doc = adapter.to_preprocessed_document(
        spc_package,
        document_id="valle_hermoso_2024"
    )
    
    print(f"✓ Conversion successful:")
    print(f"  - Document ID: {doc.document_id}")
    print(f"  - Structured chunks: {len(doc.sentences)}")
    print(f"  - Budget tables: {len(doc.tables)}")
    print()
    
    # STEP 3: Multi-dimensional Analysis
    print("STEP 3: Automated Policy Analysis")
    print("-" * 70)
    print()
    
    all_insights = []
    
    print("Analyzing budget distribution...")
    all_insights.extend(analyze_budget_distribution(doc))
    
    print("Analyzing strategic coherence...")
    all_insights.extend(analyze_strategic_coherence(doc))
    
    print("Analyzing KPI coverage...")
    all_insights.extend(analyze_kpi_coverage(doc))
    
    print("✓ Analysis complete")
    print()
    
    # STEP 4: Generate Report
    generate_analysis_report(all_insights)
    
    # STEP 5: Detailed Breakdown
    print("=" * 70)
    print("DETAILED POLICY STRUCTURE")
    print("=" * 70)
    print()
    
    # Strategic level
    print("STRATEGIC AXES (MACRO):")
    for sentence in doc.sentences:
        if sentence.get('resolution') == 'macro':
            print(f"  • {sentence['chunk_id']}")
            print(f"    {sentence['text'][:100]}...")
    print()
    
    # Program level
    print("PROGRAMS (MESO):")
    for sentence in doc.sentences:
        if sentence.get('resolution') == 'meso':
            print(f"  • {sentence['chunk_id']}")
            print(f"    {sentence['text'][:100]}...")
    print()
    
    # Project level with budget
    print("PROJECTS (MICRO) WITH BUDGET:")
    for sentence in doc.sentences:
        if sentence.get('resolution') == 'micro':
            chunk_id = sentence['chunk_id']
            print(f"  • {chunk_id}")
            print(f"    {sentence['text'][:80]}...")
            
            # Find associated budget
            for table in doc.tables:
                if table.get('chunk_id') == chunk_id:
                    print(f"    💰 Budget: ${table['amount']:,.0f} {table['currency']}")
                    print(f"    📊 Source: {table['source']}")
    print()
    
    # Summary
    print("=" * 70)
    print("SCENARIO SUMMARY")
    print("=" * 70)
    print()
    print("What was demonstrated:")
    print("  ✓ Real-world development plan structure")
    print("  ✓ Complete SPC ingestion → adapter → orchestrator flow")
    print("  ✓ Multi-level analysis (strategic, programmatic, operational)")
    print("  ✓ Budget tracking and financial analysis")
    print("  ✓ KPI and indicator coverage assessment")
    print("  ✓ Automated insight generation")
    print()
    print("Value proposition:")
    print("  • Automated extraction of policy structure from PDFs")
    print("  • Multi-resolution analysis (MACRO/MESO/MICRO)")
    print("  • Budget accountability and tracking")
    print("  • Quality metrics and validation")
    print("  • Actionable insights for decision-makers")
    print()
    print("✓ Complete policy analysis pipeline demonstrated!")
    print()


if __name__ == "__main__":
    main()
