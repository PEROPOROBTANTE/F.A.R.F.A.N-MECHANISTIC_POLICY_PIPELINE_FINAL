#!/usr/bin/env python3
"""
NIVEL3 - Ejemplos de Uso de Métodos
Ejemplos prácticos de ejecución prioritaria de los 593 métodos del sistema

Este archivo demuestra patrones de uso para cada categoría de métodos
con énfasis en aquellos de prioridad CRITICAL y HIGH.
"""

import sys
from pathlib import Path
from typing import Any

# Añadir el directorio raíz al path
# Imports de los productores principales
try:
    from Analyzer_one import MunicipalAnalyzer
    from financiero_viabilidad_tablas import PDETMunicipalPlanAnalyzer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure all dependencies are installed and paths are correct")
    sys.exit(1)

class NIVEL3ExecutionGuide:
    """
    Guía de ejecución para métodos NIVEL3
    Proporciona patrones y ejemplos para ejecución prioritaria
    """

    def __init__(self) -> None:
        """Inicializar guía de ejecución"""
        self.execution_log = []

    # ========================================================================
    # MÉTODOS CRÍTICOS (CRITICAL PRIORITY) - Ejecución Obligatoria
    # ========================================================================

    def ejemplo_financiero_critical(self) -> PDETMunicipalPlanAnalyzer | None:
        """
        Ejemplo: PDETMunicipalPlanAnalyzer.__init__
        PRIORIDAD: CRITICAL
        APTITUD: Alta - Método fundamental de inicialización
        """
        print("\n=== EJEMPLO 1: Inicialización Análisis Financiero ===")
        print("MÉTODO: PDETMunicipalPlanAnalyzer.__init__")
        print("PRIORIDAD: CRITICAL")
        print("REQUISITOS: Configuración de contexto municipal colombiano")

        try:
            # Inicializar analizador con contexto municipal
            analyzer = PDETMunicipalPlanAnalyzer()
            print("✓ Analizador inicializado correctamente")
            print(f"  - Stopwords cargadas: {len(analyzer.stopwords) if hasattr(analyzer, 'stopwords') else 'N/A'}")
            self.execution_log.append({
                "method": "PDETMunicipalPlanAnalyzer.__init__",
                "status": "SUCCESS",
                "priority": "CRITICAL"
            })
            return analyzer
        except Exception as e:
            print(f"✗ Error: {e}")
            self.execution_log.append({
                "method": "PDETMunicipalPlanAnalyzer.__init__",
                "status": "FAILED",
                "error": str(e)
            })
            return None

    def ejemplo_municipal_analyzer_critical(self) -> MunicipalAnalyzer | None:
        """
        Ejemplo: MunicipalAnalyzer.__init__
        PRIORIDAD: CRITICAL
        APTITUD: Alta - Inicialización del analizador semántico
        """
        print("\n=== EJEMPLO 2: Inicialización Analizador Municipal ===")
        print("MÉTODO: MunicipalAnalyzer.__init__")
        print("PRIORIDAD: CRITICAL")

        try:
            analyzer = MunicipalAnalyzer()
            print("✓ MunicipalAnalyzer inicializado")
            self.execution_log.append({
                "method": "MunicipalAnalyzer.__init__",
                "status": "SUCCESS",
                "priority": "CRITICAL"
            })
            return analyzer
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def ejemplo_policy_processor_critical(self) -> dict[str, Any] | None:
        """
        Ejemplo: IndustrialPolicyProcessor.process
        PRIORIDAD: CRITICAL
        APTITUD: Media-Alta - Procesamiento principal de políticas
        """
        print("\n=== EJEMPLO 3: Procesamiento de Políticas ===")
        print("MÉTODO: IndustrialPolicyProcessor.process")
        print("PRIORIDAD: CRITICAL")
        print("REQUISITOS: Texto de política, configuración procesador")

        try:
            from policy_processor import IndustrialPolicyProcessor

            # Texto de ejemplo
            sample_text = """
            El Plan de Desarrollo contempla la inversión de 50.000 millones de pesos
            en infraestructura vial para mejorar la conectividad del municipio.
            """

            processor = IndustrialPolicyProcessor()
            result = processor.process(sample_text)

            print("✓ Política procesada exitosamente")
            print(f"  - Evidencias encontradas: {len(result.get('evidences', []))}")
            self.execution_log.append({
                "method": "IndustrialPolicyProcessor.process",
                "status": "SUCCESS",
                "priority": "CRITICAL"
            })
            return result
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # ========================================================================
    # MÉTODOS DE ALTA PRIORIDAD (HIGH PRIORITY)
    # ========================================================================

    def ejemplo_bayesian_inference_high(self) -> float | None:
        """
        Ejemplo: Métodos de inferencia bayesiana
        PRIORIDAD: HIGH
        APTITUD: Media - Requiere datos numéricos y configuración estadística
        """
        print("\n=== EJEMPLO 4: Inferencia Bayesiana ===")
        print("MÉTODOS: _bayesian_risk_inference, compute_evidence_score")
        print("PRIORIDAD: HIGH")
        print("COMPLEJIDAD: HIGH")

        try:
            from policy_processor import BayesianEvidenceScorer

            scorer = BayesianEvidenceScorer()

            # Ejemplo de evidencias
            evidences = [
                {"type": "numerical", "value": 0.85, "source": "document_1"},
                {"type": "textual", "value": 0.72, "source": "document_2"},
                {"type": "statistical", "value": 0.90, "source": "analysis_1"}
            ]

            score = scorer.compute_evidence_score(evidences)
            print(f"✓ Score de evidencia calculado: {score}")
            self.execution_log.append({
                "method": "BayesianEvidenceScorer.compute_evidence_score",
                "status": "SUCCESS",
                "priority": "HIGH"
            })
            return score
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def ejemplo_causal_dag_high(self) -> Any:  # noqa: ANN401
        """
        Ejemplo: Construcción y análisis de DAG causal
        PRIORIDAD: HIGH
        APTITUD: Media-Alta - Requiere estructura de nodos y aristas
        """
        print("\n=== EJEMPLO 5: Construcción DAG Causal ===")
        print("MÉTODO: construct_causal_dag")
        print("PRIORIDAD: HIGH")
        print("COMPLEJIDAD: HIGH")
        print("DEPENDENCIAS: networkx, análisis de grafos")

        try:
            analyzer = PDETMunicipalPlanAnalyzer()

            # Texto de ejemplo con relaciones causales
            sample_text = """
            La inversión en educación mejora los indicadores de desarrollo humano,
            lo cual a su vez incrementa la productividad económica del municipio.
            El desarrollo económico permite mayor inversión en educación.
            """

            dag = analyzer.construct_causal_dag(sample_text)
            print("✓ DAG construido exitosamente")
            if dag:
                print(f"  - Nodos identificados: {len(dag.nodes) if hasattr(dag, 'nodes') else 'N/A'}")
                print(f"  - Aristas causales: {len(dag.edges) if hasattr(dag, 'edges') else 'N/A'}")

            self.execution_log.append({
                "method": "construct_causal_dag",
                "status": "SUCCESS",
                "priority": "HIGH"
            })
            return dag
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # ========================================================================
    # MÉTODOS DE COMPLEJIDAD ALTA - Atención Especial
    # ========================================================================

    def ejemplo_monte_carlo_simulation(self) -> None:
        """
        Ejemplo: Simulaciones Monte Carlo
        COMPLEJIDAD: HIGH
        APTITUD: Media - Requiere recursos computacionales significativos
        """
        print("\n=== EJEMPLO 6: Simulación Monte Carlo ===")
        print("COMPLEJIDAD: HIGH")
        print("RECURSOS: Computación intensiva, alta memoria")
        print("NOTA: Método de ejemplo - implementación específica varía")

        print("⚠ Métodos Monte Carlo requieren:")
        print("  - Múltiples iteraciones (típicamente 1000-10000)")
        print("  - Gestión de memoria para resultados")
        print("  - Tiempo de ejecución extendido")
        print("  - Validación de convergencia")

        self.execution_log.append({
            "method": "monte_carlo_simulation",
            "status": "INFO",
            "note": "Requiere configuración específica"
        })

    # ========================================================================
    # PIPELINE DE EJECUCIÓN COMPLETO
    # ========================================================================

    def ejecutar_pipeline_completo(self, document_path: str = None) -> None:
        """
        Ejecuta un pipeline completo de análisis
        Demuestra la orquestación de múltiples métodos
        """
        print("\n" + "="*70)
        print("PIPELINE COMPLETO DE EJECUCIÓN")
        print("="*70)

        if not document_path:
            print("⚠ No se proporcionó documento. Usando datos de ejemplo.")
            document_path = "ejemplo_pdet.pdf"

        # Paso 1: Inicialización (CRITICAL)
        print("\n[1/7] Inicializando componentes...")
        self.ejemplo_financiero_critical()
        self.ejemplo_municipal_analyzer_critical()

        # Paso 2: Procesamiento de texto (CRITICAL)
        print("\n[2/7] Procesando políticas...")
        self.ejemplo_policy_processor_critical()

        # Paso 3: Análisis Bayesiano (HIGH)
        print("\n[3/7] Realizando inferencia bayesiana...")
        self.ejemplo_bayesian_inference_high()

        # Paso 4: Construcción DAG Causal (HIGH)
        print("\n[4/7] Construyendo DAG causal...")
        self.ejemplo_causal_dag_high()

        # Paso 5: Detección de contradicciones
        print("\n[5/7] Detectando contradicciones...")
        print("  (Requiere ContradictionDetector)")

        # Paso 6: Análisis de embeddings
        print("\n[6/7] Analizando embeddings semánticos...")
        print("  (Requiere PolicyEmbeddingAnalyzer)")

        # Paso 7: Ensamblaje de reporte
        print("\n[7/7] Ensamblando reporte final...")
        print("  (Requiere ReportAssembler)")

        print("\n" + "="*70)
        print("RESUMEN DE EJECUCIÓN")
        print("="*70)
        self.print_execution_summary()

    def print_execution_summary(self) -> None:
        """Imprime resumen de ejecución"""
        successful = sum(1 for log in self.execution_log if log.get('status') == 'SUCCESS')
        failed = sum(1 for log in self.execution_log if log.get('status') == 'FAILED')

        print(f"\nMétodos ejecutados: {len(self.execution_log)}")
        print(f"  ✓ Exitosos: {successful}")
        print(f"  ✗ Fallidos: {failed}")

        if failed > 0:
            print("\nMétodos fallidos:")
            for log in self.execution_log:
                if log.get('status') == 'FAILED':
                    print(f"  - {log['method']}: {log.get('error', 'Unknown error')}")

def main() -> None:
    """Función principal de demostración"""
    print("="*70)
    print("NIVEL3 - SISTEMA DE EJEMPLOS DE USO")
    print("Sistema de 593 Métodos para Análisis de Políticas Públicas")
    print("="*70)

    guide = NIVEL3ExecutionGuide()

    # Ejecutar ejemplos individuales
    print("\n### EJEMPLOS INDIVIDUALES ###\n")

    # Críticos
    guide.ejemplo_financiero_critical()
    guide.ejemplo_municipal_analyzer_critical()
    guide.ejemplo_policy_processor_critical()

    # Alta prioridad
    guide.ejemplo_bayesian_inference_high()
    guide.ejemplo_causal_dag_high()

    # Alta complejidad
    guide.ejemplo_monte_carlo_simulation()

    # Pipeline completo
    print("\n\n### PIPELINE COMPLETO ###")
    guide.ejecutar_pipeline_completo()

    print("\n" + "="*70)
    print("Para más información, consultar:")
    print("  - catalogo_completo_canonico.json (catálogo completo)")
    print("  - CHEATSHEET_NIVEL3.txt (referencia rápida)")
    print("  - README_NIVEL3.md (análisis detallado)")
    print("="*70)

if __name__ == "__main__":
    main()
