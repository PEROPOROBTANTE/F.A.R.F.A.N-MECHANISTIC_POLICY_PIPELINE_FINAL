#!/usr/bin/env python3
"""
Ejemplos de Uso del Catálogo Canónico de Executors
F.A.R.F.A.N Mechanistic Policy Pipeline

Este script demuestra cómo utilizar el catálogo canónico de executors
para orquestación inteligente, análisis de cobertura y optimización.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter, defaultdict


class CanonicalCatalogManager:
    """Gestor para interactuar con el catálogo canónico de executors."""

    def __init__(self, catalog_path: str = "config/canonical_executor_catalog.json"):
        """Inicializa el gestor cargando el catálogo."""
        self.catalog_path = Path(catalog_path)
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        """Carga el catálogo desde el archivo JSON."""
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ========================================================================
    # CASO DE USO 1: ORQUESTADOR INTELIGENTE
    # ========================================================================

    def orquestar_pregunta(self, question_id: str, priority_level: int = 2) -> Dict[str, Any]:
        """
        Orquesta la ejecución de una pregunta específica.

        Args:
            question_id: ID de la pregunta (e.g., "D1-Q1")
            priority_level: Nivel mínimo de prioridad (1-3)

        Returns:
            Diccionario con la secuencia de ejecución optimizada
        """
        # Buscar la pregunta en el catálogo
        question = self._find_question(question_id)
        if not question:
            raise ValueError(f"Pregunta {question_id} no encontrada en el catálogo")

        execution_plan = {
            "question_id": question_id,
            "text": question['t'],
            "total_methods": question['m'],
            "flow": question['flow'],
            "packages": []
        }

        # Filtrar métodos por prioridad
        for package in question['p']:
            filtered_methods = []
            for i, method in enumerate(package['m']):
                if package['pr'][i] >= priority_level:
                    filtered_methods.append({
                        "class": package['c'],
                        "method": method,
                        "type": package['t'][i],
                        "priority": package['pr'][i]
                    })

            if filtered_methods:
                execution_plan["packages"].append({
                    "file": package['f'],
                    "class": package['c'],
                    "methods": filtered_methods,
                    "note": package.get('note', '')
                })

        return execution_plan

    def ejecutar_metodos(self, file_code: str, class_name: str, methods: List[str]):
        """
        Simula la ejecución de métodos de una clase específica.

        Args:
            file_code: Código del archivo (PP, CD, etc.)
            class_name: Nombre de la clase
            methods: Lista de nombres de métodos a ejecutar
        """
        print(f"\n🔧 Ejecutando {len(methods)} métodos de {file_code}:{class_name}")
        for method in methods:
            print(f"   ✓ {method}()")

    # ========================================================================
    # CASO DE USO 2: ANÁLISIS DE COBERTURA
    # ========================================================================

    def analizar_metodos_reutilizados(self) -> Dict[str, Any]:
        """
        Analiza qué métodos son más reutilizados en diferentes preguntas.

        Returns:
            Diccionario con estadísticas de reutilización
        """
        method_usage = Counter()
        method_by_file = defaultdict(Counter)

        for executor in self.catalog['executors']:
            for package in executor['p']:
                file_code = package['f']
                class_name = package['c']
                for method in package['m']:
                    full_method = f"{class_name}.{method}"
                    method_usage[full_method] += 1
                    method_by_file[file_code][full_method] += 1

        # Top 10 métodos más usados
        top_methods = method_usage.most_common(10)

        return {
            "total_unique_methods": len(method_usage),
            "total_method_calls": sum(method_usage.values()),
            "top_10_methods": [
                {"method": method, "uses": count, "percentage": f"{(count/30)*100:.1f}%"}
                for method, count in top_methods
            ],
            "usage_by_file": {
                file: dict(counter)
                for file, counter in method_by_file.items()
            }
        }

    def analizar_cobertura_por_dimension(self) -> Dict[str, Any]:
        """
        Analiza la distribución de métodos por dimensión.

        Returns:
            Diccionario con estadísticas por dimensión
        """
        coverage = {}

        for dim_id, dim_info in self.catalog['dimensions'].items():
            dim_methods = set()
            dim_executors = []

            # Obtener todos los executors de esta dimensión
            for executor in self.catalog['executors']:
                if executor['q'].startswith(dim_id):
                    dim_executors.append(executor)
                    for package in executor['p']:
                        for method in package['m']:
                            dim_methods.add(f"{package['c']}.{method}")

            coverage[dim_id] = {
                "name": dim_info['name'],
                "label": dim_info['label'],
                "total_executors": len(dim_executors),
                "unique_methods": len(dim_methods),
                "avg_methods_per_executor": sum(e['m'] for e in dim_executors) / len(dim_executors) if dim_executors else 0
            }

        return coverage

    # ========================================================================
    # CASO DE USO 3: OPTIMIZACIÓN DE EJECUCIÓN
    # ========================================================================

    def obtener_metodos_priorizados(self, question_id: str, min_priority: int = 2) -> List[Dict[str, Any]]:
        """
        Obtiene solo los métodos críticos e importantes de una pregunta.

        Args:
            question_id: ID de la pregunta
            min_priority: Prioridad mínima (1-3)

        Returns:
            Lista de métodos priorizados
        """
        question = self._find_question(question_id)
        if not question:
            return []

        prioritized = []
        for package in question['p']:
            for i, method in enumerate(package['m']):
                if package['pr'][i] >= min_priority:
                    prioritized.append({
                        "file": package['f'],
                        "class": package['c'],
                        "method": method,
                        "type": package['t'][i],
                        "priority": package['pr'][i],
                        "priority_label": self.catalog['metadata']['priority'][str(package['pr'][i])]
                    })

        return sorted(prioritized, key=lambda x: x['priority'], reverse=True)

    def generar_plan_ejecucion_batch(self, dimension_id: str, priority_level: int = 3) -> Dict[str, Any]:
        """
        Genera un plan de ejecución en batch para una dimensión completa.

        Args:
            dimension_id: ID de la dimensión (D1-D6)
            priority_level: Nivel de prioridad mínimo

        Returns:
            Plan de ejecución optimizado
        """
        dimension = self.catalog['dimensions'].get(dimension_id)
        if not dimension:
            raise ValueError(f"Dimensión {dimension_id} no encontrada")

        batch_plan = {
            "dimension": dimension_id,
            "name": dimension['name'],
            "label": dimension['label'],
            "questions": []
        }

        for q_num in range(1, 6):
            question_id = f"{dimension_id}-Q{q_num}"
            plan = self.orquestar_pregunta(question_id, priority_level)
            batch_plan["questions"].append(plan)

        return batch_plan

    # ========================================================================
    # CASO DE USO 4: ANÁLISIS DE CARACTERÍSTICAS ESPECIALES
    # ========================================================================

    def analizar_sistema_bicameral(self) -> Dict[str, Any]:
        """
        Analiza las características del sistema bicameral de validación.

        Returns:
            Información del sistema bicameral
        """
        bicameral = self.catalog['special_features']['bicameral_system']

        ruta1_executor = self._find_question(bicameral['ruta_1']['executor'])
        ruta2_executor = self._find_question(bicameral['ruta_2']['executor'])

        return {
            "description": bicameral['description'],
            "ruta_1": {
                **bicameral['ruta_1'],
                "total_methods": ruta1_executor['m'] if ruta1_executor else 0
            },
            "ruta_2": {
                **bicameral['ruta_2'],
                "total_methods": ruta2_executor['m'] if ruta2_executor else 0
            }
        }

    def analizar_validacion_anti_milagro(self) -> Dict[str, Any]:
        """
        Analiza los métodos de validación anti-milagro.

        Returns:
            Información de validación anti-milagro
        """
        anti_milagro = self.catalog['special_features']['anti_milagro']
        executor = self._find_question(anti_milagro['executor'])

        return {
            "description": anti_milagro['description'],
            "executor": anti_milagro['executor'],
            "patrones": anti_milagro['patrones'],
            "umbrales": anti_milagro['umbrales'],
            "key_methods": anti_milagro['key_methods'],
            "total_methods_in_executor": executor['m'] if executor else 0
        }

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    def _find_question(self, question_id: str) -> Dict[str, Any] | None:
        """Busca una pregunta por su ID en el catálogo."""
        for executor in self.catalog['executors']:
            if executor['q'] == question_id:
                return executor
        return None

    def print_statistics(self):
        """Imprime estadísticas generales del catálogo."""
        metadata = self.catalog['metadata']
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DEL CATÁLOGO CANÓNICO")
        print("="*70)
        print(f"Versión: {metadata['version']}")
        print(f"Fecha: {metadata['created']}")
        print(f"\n📋 Cobertura:")
        print(f"  • Executors: {metadata['total_executors']}")
        print(f"  • Base Slots: {metadata['total_base_slots']}")
        print(f"  • Preguntas totales: {metadata['total_questions']}")
        print(f"  • Policy Areas: {metadata['total_policy_areas']}")
        print(f"  • Dimensiones: {metadata['dimensions']}")
        print(f"\n📦 Archivos Core: {len(metadata['files'])}")
        for code, info in metadata['files'].items():
            print(f"  • {code}: {info['name']}")
        print("="*70 + "\n")


# ============================================================================
# EJEMPLOS DE USO
# ============================================================================

def ejemplo_1_orquestador_inteligente():
    """Ejemplo 1: Usar el orquestador inteligente."""
    print("\n" + "="*70)
    print("EJEMPLO 1: ORQUESTADOR INTELIGENTE")
    print("="*70)

    manager = CanonicalCatalogManager()

    # Orquestar D1-Q1 con solo métodos críticos (prioridad 3)
    plan = manager.orquestar_pregunta("D1-Q1", priority_level=3)

    print(f"\n📋 Pregunta: {plan['question_id']}")
    print(f"📝 Texto: {plan['text'][:100]}...")
    print(f"🔄 Flow: {plan['flow']}")
    print(f"🎯 Métodos críticos: {sum(len(p['methods']) for p in plan['packages'])}")

    print("\n🚀 Plan de ejecución:")
    for package in plan['packages']:
        print(f"\n  📦 {package['file']}:{package['class']}")
        print(f"     {package['note']}")
        for method in package['methods'][:3]:  # Mostrar solo primeros 3
            priority_icon = "★" if method['priority'] == 3 else "◆"
            print(f"     {priority_icon} {method['method']} ({method['type']})")


def ejemplo_2_analisis_cobertura():
    """Ejemplo 2: Análisis de cobertura de métodos."""
    print("\n" + "="*70)
    print("EJEMPLO 2: ANÁLISIS DE COBERTURA")
    print("="*70)

    manager = CanonicalCatalogManager()

    # Analizar métodos reutilizados
    reuse = manager.analizar_metodos_reutilizados()

    print(f"\n📊 Métodos únicos: {reuse['total_unique_methods']}")
    print(f"🔢 Total invocaciones: {reuse['total_method_calls']}")
    print(f"\n🏆 Top 5 métodos más usados:")
    for i, method_info in enumerate(reuse['top_10_methods'][:5], 1):
        print(f"  {i}. {method_info['method']}")
        print(f"     Usado en {method_info['uses']} executors ({method_info['percentage']})")

    # Analizar cobertura por dimensión
    coverage = manager.analizar_cobertura_por_dimension()

    print(f"\n📐 Cobertura por Dimensión:")
    for dim_id, info in coverage.items():
        print(f"\n  {dim_id} - {info['name']} ({info['label']})")
        print(f"     Executors: {info['total_executors']}")
        print(f"     Métodos únicos: {info['unique_methods']}")
        print(f"     Promedio métodos/executor: {info['avg_methods_per_executor']:.1f}")


def ejemplo_3_optimizacion_ejecucion():
    """Ejemplo 3: Optimización de ejecución."""
    print("\n" + "="*70)
    print("EJEMPLO 3: OPTIMIZACIÓN DE EJECUCIÓN")
    print("="*70)

    manager = CanonicalCatalogManager()

    # Obtener solo métodos críticos e importantes de D6-Q1
    prioritized = manager.obtener_metodos_priorizados("D6-Q1", min_priority=2)

    print(f"\n🎯 Métodos priorizados para D6-Q1 (Integridad de Teoría de Cambio)")
    print(f"Total: {len(prioritized)} métodos")

    critical = [m for m in prioritized if m['priority'] == 3]
    important = [m for m in prioritized if m['priority'] == 2]

    print(f"\n★ Críticos: {len(critical)}")
    for method in critical[:5]:
        print(f"  • {method['class']}.{method['method']} ({method['type']})")

    print(f"\n◆ Importantes: {len(important)}")
    for method in important[:5]:
        print(f"  • {method['class']}.{method['method']} ({method['type']})")


def ejemplo_4_caracteristicas_especiales():
    """Ejemplo 4: Analizar características especiales."""
    print("\n" + "="*70)
    print("EJEMPLO 4: CARACTERÍSTICAS ESPECIALES")
    print("="*70)

    manager = CanonicalCatalogManager()

    # Sistema bicameral
    bicameral = manager.analizar_sistema_bicameral()
    print("\n🏛️  Sistema Bicameral")
    print(f"Descripción: {bicameral['description']}")
    print(f"\nRuta 1: {bicameral['ruta_1']['executor']}")
    print(f"  {bicameral['ruta_1']['description']}")
    print(f"  Método principal: {bicameral['ruta_1']['primary_method']}")
    print(f"  Total métodos: {bicameral['ruta_1']['total_methods']}")

    print(f"\nRuta 2: {bicameral['ruta_2']['executor']}")
    print(f"  {bicameral['ruta_2']['description']}")
    print(f"  Método principal: {bicameral['ruta_2']['primary_method']}")
    print(f"  Total métodos: {bicameral['ruta_2']['total_methods']}")

    # Validación anti-milagro
    anti_milagro = manager.analizar_validacion_anti_milagro()
    print("\n\n🚫 Validación Anti-Milagro")
    print(f"Descripción: {anti_milagro['description']}")
    print(f"Executor: {anti_milagro['executor']}")
    print(f"Patrones: {', '.join(anti_milagro['patrones'])}")
    print(f"Umbrales: {', '.join(anti_milagro['umbrales'])}")
    print(f"\nMétodos clave:")
    for method in anti_milagro['key_methods'][:3]:
        print(f"  • {method}")


def main():
    """Función principal que ejecuta todos los ejemplos."""
    manager = CanonicalCatalogManager()
    manager.print_statistics()

    ejemplo_1_orquestador_inteligente()
    ejemplo_2_analisis_cobertura()
    ejemplo_3_optimizacion_ejecucion()
    ejemplo_4_caracteristicas_especiales()

    print("\n" + "="*70)
    print("✅ Todos los ejemplos ejecutados exitosamente")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
