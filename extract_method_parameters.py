#!/usr/bin/env python3
"""
METHOD PARAMETER EXTRACTOR - PHASES 1 & 2
==========================================

Extrae parámetros configurables de canonical_method_catalogue_v2.json
siguiendo la guía operativa.

FASE 1: Identificación
- Filtrar métodos con required:false en input_parameters
- Excluir privados (is_private: true)
- Excluir métodos con calibration_status: "excluded"

FASE 2: Extracción
- Extraer parámetros configurables
- Inferir tipos y rangos válidos
- Generar estructura preliminar de method_parameters.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ParameterExtractor:
    """Extrae parámetros configurables del catálogo de métodos."""

    def __init__(
        self,
        catalogue_path: str = "canonical_method_catalogue_v2.json",
        calibration_path: str = "config/intrinsic_calibration.json"
    ):
        self.catalogue_path = catalogue_path
        self.calibration_path = calibration_path
        self.catalogue = {}
        self.calibration = {}
        self.stats = defaultdict(int)

    def load_data(self) -> bool:
        """Cargar catálogo y calibración."""
        try:
            logger.info(f"Loading catalogue: {self.catalogue_path}")
            with open(self.catalogue_path, 'r', encoding='utf-8') as f:
                self.catalogue = json.load(f)
            logger.info(f"✅ Loaded {len(self.catalogue)} entries")

            if Path(self.calibration_path).exists():
                logger.info(f"Loading calibration: {self.calibration_path}")
                with open(self.calibration_path, 'r', encoding='utf-8') as f:
                    self.calibration = json.load(f)
                logger.info(f"✅ Loaded calibration data")
            else:
                logger.warning(f"⚠️  Calibration file not found: {self.calibration_path}")
                self.calibration = {}

            return True

        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            return False

    def infer_param_type_and_range(
        self,
        param_name: str,
        type_hint: Optional[str],
        default_value: Any
    ) -> Tuple[str, List[Any]]:
        """
        Inferir tipo y rango válido de un parámetro.

        Returns: (type, valid_range)
        """
        # 1. Si hay type hint, usarlo
        if type_hint:
            type_hint_lower = type_hint.lower()

            # Float con rangos comunes
            if 'float' in type_hint_lower:
                # Identificar si es probabilidad, score, etc.
                if any(keyword in param_name.lower() for keyword in [
                    'prob', 'threshold', 'alpha', 'beta', 'prior', 'score',
                    'confidence', 'weight', 'ratio'
                ]):
                    return "float", [0.0, 1.0]  # Probabilidades
                elif 'learning' in param_name.lower() or 'rate' in param_name.lower():
                    return "float", [0.0001, 0.1]  # Learning rates
                else:
                    return "float", [0.0, 100.0]  # Genérico

            # Integer con rangos comunes
            elif 'int' in type_hint_lower:
                if any(keyword in param_name.lower() for keyword in [
                    'size', 'length', 'max', 'min', 'count', 'num', 'n_'
                ]):
                    return "int", [1, 10000]  # Contadores/tamaños
                elif 'iteration' in param_name.lower() or 'epoch' in param_name.lower():
                    return "int", [1, 1000]  # Iteraciones
                else:
                    return "int", [0, 1000]  # Genérico

            # Boolean
            elif 'bool' in type_hint_lower:
                return "bool", [True, False]

            # String
            elif 'str' in type_hint_lower:
                return "str", ["any"]

            # List
            elif 'list' in type_hint_lower:
                return "list", ["any"]

            # Dict
            elif 'dict' in type_hint_lower:
                return "dict", ["any"]

            # Otros tipos
            else:
                return type_hint, ["unknown"]

        # 2. Si no hay type hint, inferir del default_value
        if default_value is not None and default_value != "None":
            if isinstance(default_value, bool):
                return "bool", [True, False]
            elif isinstance(default_value, int):
                return "int", [0, 10000]
            elif isinstance(default_value, float):
                return "float", [0.0, 100.0]
            elif isinstance(default_value, str):
                return "str", ["any"]
            elif isinstance(default_value, list):
                return "list", ["any"]
            elif isinstance(default_value, dict):
                return "dict", ["any"]

        # 3. Fallback
        return "unknown", ["unknown"]

    def classify_method_type(self, method_data: Dict[str, Any]) -> str:
        """
        Clasificar tipo de método (bayesiano, ML, NLP, etc.)
        para ayudar en determinación de valores.
        """
        method_name = method_data.get('method_name', '').lower()
        file_path = method_data.get('file_path', '').lower()
        docstring = (method_data.get('docstring', '') or '').lower()

        # Bayesiano
        if any(keyword in method_name or keyword in file_path or keyword in docstring
               for keyword in ['bayesian', 'bayes', 'prior', 'posterior', 'likelihood']):
            return "bayesian"

        # Machine Learning
        if any(keyword in method_name or keyword in file_path or keyword in docstring
               for keyword in ['predict', 'train', 'classify', 'cluster', 'regression', 'model']):
            return "machine_learning"

        # NLP
        if any(keyword in method_name or keyword in file_path or keyword in docstring
               for keyword in ['text', 'token', 'embed', 'chunk', 'semantic', 'nlp', 'language']):
            return "nlp"

        # Statistical
        if any(keyword in method_name or keyword in file_path or keyword in docstring
               for keyword in ['mean', 'variance', 'distribution', 'statistical', 'correlation']):
            return "statistical"

        # Policy/Domain specific
        if any(keyword in method_name or keyword in file_path
               for keyword in ['policy', 'municipal', 'pdet', 'derek_beach']):
            return "policy_domain"

        return "general"

    def phase_1_identify_methods(self) -> List[str]:
        """
        FASE 1: Identificar métodos que requieren parametrización.

        Criterios:
        - Tiene al menos 1 parámetro con required:false
        - NO es privado (is_private: false)
        - NO está excluido (calibration_status != "excluded")
        """
        logger.info("="*80)
        logger.info("FASE 1: IDENTIFICACIÓN DE MÉTODOS")
        logger.info("="*80)

        identified_methods = []
        calibration_methods = self.calibration.get('methods', {})

        for method_id, method_data in self.catalogue.items():
            if method_id.startswith('_'):
                self.stats['skipped_metadata'] += 1
                continue

            # Criterio 1: ¿Tiene parámetros con required:false?
            params = method_data.get('input_parameters', [])
            has_configurable = any(
                not p.get('required', True) and p.get('name') != 'self'
                for p in params
            )

            if not has_configurable:
                self.stats['no_configurable_params'] += 1
                continue

            # Criterio 2: ¿Es privado?
            is_private = method_data.get('is_private', False)
            if is_private:
                self.stats['excluded_private'] += 1
                continue

            # Criterio 3: ¿Está excluido en calibración?
            cal_entry = calibration_methods.get(method_id, {})
            cal_status = cal_entry.get('calibration_status', '')
            if cal_status == 'excluded':
                self.stats['excluded_calibration'] += 1
                continue

            # ✅ Método califica para parametrización
            identified_methods.append(method_id)
            self.stats['methods_identified'] += 1

        logger.info(f"\n📊 RESULTADOS FASE 1:")
        logger.info(f"  Total entries scanned: {len(self.catalogue) - self.stats.get('skipped_metadata', 0):,}")
        logger.info(f"  ✅ Methods identified: {self.stats['methods_identified']:,}")
        logger.info(f"  ❌ No configurable params: {self.stats['no_configurable_params']:,}")
        logger.info(f"  ❌ Excluded (private): {self.stats['excluded_private']:,}")
        logger.info(f"  ❌ Excluded (calibration): {self.stats['excluded_calibration']:,}")

        return identified_methods

    def phase_2_extract_parameters(self, method_ids: List[str]) -> Dict[str, Any]:
        """
        FASE 2: Extraer parámetros configurables.

        Para cada método:
        - Extraer parámetros con required:false
        - Inferir tipos y rangos
        - Clasificar método
        - Preparar estructura para method_parameters.json
        """
        logger.info("\n" + "="*80)
        logger.info("FASE 2: EXTRACCIÓN DE PARÁMETROS")
        logger.info("="*80)

        method_parameters = {}

        for i, method_id in enumerate(method_ids, 1):
            if i % 50 == 0:
                logger.info(f"  Progress: {i}/{len(method_ids)} methods...")

            method_data = self.catalogue[method_id]
            params = method_data.get('input_parameters', [])

            # Filtrar parámetros configurables
            configurable_params = []
            for param in params:
                if param.get('required', True) or param.get('name') == 'self':
                    continue

                param_name = param['name']
                type_hint = param.get('type_hint')
                default_value = param.get('default_value')

                # Inferir tipo y rango
                inferred_type, valid_range = self.infer_param_type_and_range(
                    param_name, type_hint, default_value
                )

                configurable_params.append({
                    "name": param_name,
                    "type_hint": type_hint,
                    "inferred_type": inferred_type,
                    "current_default": default_value,
                    "valid_range": valid_range,
                    "has_default": param.get('has_default', False),
                    "default_type": param.get('default_type'),
                    "needs_validation": True,  # Todos requieren validación inicialmente
                    "source": "code_default",  # Viene del código por ahora
                    "notes": ""
                })

                self.stats['total_configurable_params'] += 1

            # Clasificar método
            method_type = self.classify_method_type(method_data)

            # Agregar a resultado
            method_parameters[method_id] = {
                "canonical_name": method_id,
                "method_name": method_data.get('method_name'),
                "class_name": method_data.get('class_name'),
                "file_path": method_data.get('file_path'),
                "line_number": method_data.get('line_number'),
                "method_type": method_type,
                "configurable_parameters": configurable_params,
                "parameter_count": len(configurable_params),
                "calibration_status": self.calibration.get('methods', {}).get(method_id, {}).get('calibration_status', 'unknown')
            }

        logger.info(f"\n📊 RESULTADOS FASE 2:")
        logger.info(f"  Methods processed: {len(method_parameters):,}")
        logger.info(f"  Total configurable parameters: {self.stats['total_configurable_params']:,}")
        logger.info(f"  Avg params per method: {self.stats['total_configurable_params'] / len(method_parameters):.2f}")

        return method_parameters

    def generate_draft_json(self, method_parameters: Dict[str, Any], output_path: str) -> bool:
        """Generar method_parameters_draft.json."""
        try:
            # Generar metadatos
            metadata = {
                "version": "0.1.0-draft",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "phase": "identification_and_extraction",
                "status": "draft",
                "total_methods": len(method_parameters),
                "total_parameters": self.stats['total_configurable_params'],
                "notes": [
                    "This is a DRAFT version generated from Phases 1-2",
                    "All parameter values are CURRENT CODE DEFAULTS",
                    "needs_validation=true for ALL parameters",
                    "Phase 3 (value determination) is REQUIRED before production use",
                    "Source hierarchy: formal_spec > reference_impl > empirical > conservative"
                ],
                "next_steps": [
                    "Phase 3: Determine correct values using hierarchy",
                    "Phase 4: Validate consistency with code",
                    "Phase 5: Implement wiring (loader + validator)"
                ]
            }

            # Generar estadísticas por tipo
            method_types = defaultdict(int)
            param_types = defaultdict(int)
            for method_data in method_parameters.values():
                method_types[method_data['method_type']] += 1
                for param in method_data['configurable_parameters']:
                    param_types[param['inferred_type']] += 1

            metadata['method_types_distribution'] = dict(method_types)
            metadata['parameter_types_distribution'] = dict(param_types)

            # Construir JSON completo
            full_output = {
                "_metadata": metadata,
                "methods": method_parameters
            }

            # Guardar
            logger.info(f"\n💾 Saving to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_output, f, indent=2, ensure_ascii=False)

            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"✅ Saved: {file_size:.2f} MB")

            return True

        except Exception as e:
            logger.error(f"❌ Error saving: {e}")
            return False

    def generate_identification_report(
        self,
        identified_methods: List[str],
        method_parameters: Dict[str, Any],
        output_path: str = "parameter_identification_report.md"
    ) -> bool:
        """Generar reporte markdown de identificación."""
        try:
            # Top 10 métodos con más parámetros
            sorted_methods = sorted(
                method_parameters.items(),
                key=lambda x: x[1]['parameter_count'],
                reverse=True
            )

            # Distribución por tipo
            method_types = defaultdict(list)
            for method_id, method_data in method_parameters.items():
                method_types[method_data['method_type']].append(method_id)

            # Generar reporte
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# PARAMETER IDENTIFICATION REPORT\n\n")
                f.write("## Phases 1-2: Identification and Extraction\n\n")
                f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n")
                f.write("---\n\n")

                # Summary
                f.write("## 📊 SUMMARY\n\n")
                f.write(f"- **Methods identified:** {len(identified_methods):,}\n")
                f.write(f"- **Total configurable parameters:** {self.stats['total_configurable_params']:,}\n")
                f.write(f"- **Avg parameters per method:** {self.stats['total_configurable_params'] / len(identified_methods):.2f}\n\n")

                # Filtering stats
                f.write("## 🔍 FILTERING STATISTICS\n\n")
                f.write(f"- Methods scanned: {len(self.catalogue) - self.stats.get('skipped_metadata', 0):,}\n")
                f.write(f"- ✅ Identified: {self.stats['methods_identified']:,}\n")
                f.write(f"- ❌ No configurable params: {self.stats['no_configurable_params']:,}\n")
                f.write(f"- ❌ Private methods: {self.stats['excluded_private']:,}\n")
                f.write(f"- ❌ Excluded by calibration: {self.stats['excluded_calibration']:,}\n\n")

                # Top 10
                f.write("## 🔝 TOP 10 METHODS (Most Configurable)\n\n")
                for i, (method_id, method_data) in enumerate(sorted_methods[:10], 1):
                    f.write(f"{i}. **{method_data['method_name']}** ")
                    f.write(f"({method_data['parameter_count']} params)\n")
                    f.write(f"   - Type: {method_data['method_type']}\n")
                    f.write(f"   - File: {method_data['file_path']}\n")
                    params_list = ", ".join(p['name'] for p in method_data['configurable_parameters'])
                    f.write(f"   - Parameters: {params_list}\n\n")

                # By type
                f.write("## 📂 METHODS BY TYPE\n\n")
                for method_type, methods in sorted(method_types.items(), key=lambda x: len(x[1]), reverse=True):
                    f.write(f"### {method_type.upper()}\n")
                    f.write(f"Count: {len(methods)}\n\n")
                    for method_id in methods[:5]:
                        method_data = method_parameters[method_id]
                        f.write(f"- {method_data['method_name']} ({method_data['parameter_count']} params)\n")
                    if len(methods) > 5:
                        f.write(f"- ... and {len(methods) - 5} more\n")
                    f.write("\n")

                # Next steps
                f.write("## 🎯 NEXT STEPS\n\n")
                f.write("### Phase 3: Value Determination\n")
                f.write("For each parameter, apply hierarchy:\n")
                f.write("1. **Formal specification** (academic papers, standards)\n")
                f.write("2. **Reference implementation** (sklearn, PyMC3, etc.)\n")
                f.write("3. **Empirical validation** (cross-validation)\n")
                f.write("4. **Conservative defaults** (last resort)\n\n")

                f.write("### Phase 4: Consistency Validation\n")
                f.write("- Compare JSON values vs code defaults\n")
                f.write("- Generate inconsistency report\n")
                f.write("- Implement CI/CD checks\n\n")

                f.write("### Phase 5: Wiring\n")
                f.write("- Implement ParameterLoader\n")
                f.write("- Implement ParameterValidator\n")
                f.write("- Add logging and auditing\n")
                f.write("- Write integration tests\n\n")

            logger.info(f"✅ Report saved: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
            return False

    def run(self, output_json: str = "method_parameters_draft.json") -> bool:
        """Ejecutar Fases 1 y 2 completas."""
        logger.info("="*80)
        logger.info("METHOD PARAMETER EXTRACTION - PHASES 1 & 2")
        logger.info("="*80)

        # Load data
        if not self.load_data():
            return False

        # Phase 1: Identify
        identified_methods = self.phase_1_identify_methods()

        if not identified_methods:
            logger.error("❌ No methods identified. Aborting.")
            return False

        # Phase 2: Extract
        method_parameters = self.phase_2_extract_parameters(identified_methods)

        # Generate outputs
        success = True
        success &= self.generate_draft_json(method_parameters, output_json)
        success &= self.generate_identification_report(identified_methods, method_parameters)

        if success:
            logger.info("\n" + "="*80)
            logger.info("✅ PHASES 1-2 COMPLETED SUCCESSFULLY")
            logger.info("="*80)
            logger.info(f"Output: {output_json}")
            logger.info(f"Report: parameter_identification_report.md")
        else:
            logger.error("\n" + "="*80)
            logger.error("❌ PHASES 1-2 FAILED")
            logger.error("="*80)

        return success


def main():
    """Entry point."""
    extractor = ParameterExtractor()
    success = extractor.run()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
