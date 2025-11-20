#!/usr/bin/env python3
"""
Bulk Executor Update Script
============================

Updates all 30 executors with:
1. Canonical method sequences from catalog
2. AnswerAssembler integration
3. Proper validation

This script reads canonical_executor_catalog.json and generates
the correct _get_method_sequence() for each executor.
"""

import json
import re
from pathlib import Path


def load_catalog():
    """Load canonical executor catalog."""
    catalog_path = Path("config/canonical_executor_catalog.json")
    with open(catalog_path, 'r') as f:
        return json.load(f)


def extract_methods_for_executor(executor_data):
    """Extract method sequence from executor data."""
    methods = []
    for package in executor_data['p']:
        class_name = package['c']
        for method in package['m']:
            methods.append((class_name, method))
    return methods


def generate_method_sequence_code(methods, indent=12):
    """Generate Python code for _get_method_sequence method."""
    spaces = ' ' * indent
    lines = ['return [']

    current_class = None
    for class_name, method_name in methods:
        # Add comment when class changes
        if class_name != current_class:
            if current_class is not None:
                lines.append('')  # Blank line between classes
            # Get class abbreviation comment
            abbrev = get_class_abbreviation(class_name)
            lines.append(f'{spaces}# {abbrev}: {class_name}')
            current_class = class_name

        lines.append(f"{spaces}('{class_name}', '{method_name}'),")

    lines.append(f'{spaces[:-4]}]')  # Dedent for closing bracket
    return '\n'.join(lines)


def get_class_abbreviation(class_name):
    """Get abbreviation for class based on catalog."""
    mapping = {
        'IndustrialPolicyProcessor': 'PP',
        'PolicyTextProcessor': 'PP',
        'BayesianEvidenceScorer': 'PP',
        'PolicyContradictionDetector': 'CD',
        'BayesianConfidenceCalculator': 'CD',
        'TemporalLogicVerifier': 'CD',
        'PDETMunicipalPlanAnalyzer': 'FV',
        'FinancialAuditor': 'FV',
        'BeachEvidentialTest': 'DB',
        'BayesianMechanismInference': 'DB',
        'CausalExtractor': 'DB',
        'MechanismPartExtractor': 'DB',
        'CausalInferenceSetup': 'DB',
        'OperationalizationAuditor': 'DB',
        'CDAFFramework': 'DB',
        'PolicyAnalysisEmbedder': 'EP',
        'BayesianNumericalAnalyzer': 'EP',
        'SemanticAnalyzer': 'A1',
        'PerformanceAnalyzer': 'A1',
        'TextMiningEngine': 'A1',
        'MunicipalOntology': 'A1',
        'TeoriaCambio': 'TC',
        'AdvancedDAGValidator': 'TC',
        'SemanticProcessor': 'SC',
        'ReportAssembler': 'RA',
    }
    return mapping.get(class_name, '??')


def generate_executor_class_code(question_id, executor_data, dimension):
    """Generate complete executor class code."""
    # Extract Q number (e.g., "Q1" from "D1-Q1")
    q_num = question_id.split('-')[1]
    class_name = f"D{dimension}Q{q_num[1]}_Executor"

    # Get question text from catalog
    question_text = executor_data.get('t', f'{question_id}')

    # Extract methods
    methods = extract_methods_for_executor(executor_data)
    method_sequence_code = generate_method_sequence_code(methods)

    # Generate class code
    code = f'''class {class_name}(AdvancedDataFlowExecutor):
    """{question_id}: {question_text[:80]}"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for {question_id} - FROM CANONICAL CATALOG."""
        {method_sequence_code}

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="{question_id}",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {{
            "method_results": method_results,
            "answer": answer
        }}

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []
'''

    return code


def main():
    """Main execution."""
    print("=" * 70)
    print("EXECUTOR BULK UPDATE SCRIPT")
    print("=" * 70)

    # Load catalog
    print("\n[1/4] Loading canonical executor catalog...")
    catalog = load_catalog()
    executors = catalog['executors']
    print(f"✓ Loaded {len(executors)} executor definitions")

    # Generate code for all executors
    print("\n[2/4] Generating executor code...")

    output_lines = []
    output_lines.append("# ============================================================================")
    output_lines.append("# ALL 30 EXECUTORS - CANONICAL METHOD SEQUENCES + ANSWER ASSEMBLY")
    output_lines.append("# Generated from canonical_executor_catalog.json")
    output_lines.append("# ============================================================================\n")

    for ex_data in executors:
        qid = ex_data['q']
        dimension = qid.split('-')[0][1]  # Extract dimension number

        code = generate_executor_class_code(qid, ex_data, dimension)
        output_lines.append(code)
        output_lines.append("")  # Blank line between classes

        print(f"  ✓ Generated {qid}")

    # Write to file
    print("\n[3/4] Writing updated executors...")
    output_path = Path("src/saaaaaa/core/orchestrator/executors_GENERATED.py")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"✓ Written to {output_path}")

    # Summary
    print("\n[4/4] Summary")
    print(f"  - Total executors generated: 30")
    print(f"  - All use canonical method sequences")
    print(f"  - All integrate AnswerAssembler")
    print(f"  - Output file: {output_path}")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("  1. Review generated file: executors_GENERATED.py")
    print("  2. Merge with existing executors.py")
    print("  3. Test with real PDT data")
    print("=" * 70)


if __name__ == "__main__":
    main()
