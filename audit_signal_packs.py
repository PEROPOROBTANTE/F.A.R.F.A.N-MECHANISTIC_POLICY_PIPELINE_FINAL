
import json
from pathlib import Path

from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
from saaaaaa.core.orchestrator.signal_registry import create_signal_registry

def audit_chunking_signals(registry, monolith):
    print("Auditing ChunkingSignalPack...")
    signals = registry.get_chunking_signals()

    assert signals.section_detection_patterns, "section_detection_patterns should not be empty"

    expected_embedding_config = monolith['blocks']['semantic_layers']['embedding_strategy']
    assert signals.embedding_config == expected_embedding_config, "embedding_config does not match monolith"

    print("ChunkingSignalPack audit PASSED.")

def audit_micro_answering_signals(registry, monolith):
    print("\nAuditing MicroAnsweringSignalPack for Q001...")
    question_id = "Q001"
    signals = registry.get_micro_answering_signals(question_id)

    monolith_question = next(q for q in monolith['blocks']['micro_questions'] if q['question_id'] == question_id)

    expected_patterns_count = len(monolith_question['patterns'])
    actual_patterns_count = len(signals.question_patterns[question_id])
    assert actual_patterns_count == expected_patterns_count, f"Expected {expected_patterns_count} patterns, but got {actual_patterns_count}"

    expected_elements_count = len(monolith_question['expected_elements'])
    actual_elements_count = len(signals.expected_elements[question_id])
    assert actual_elements_count == expected_elements_count, f"Expected {expected_elements_count} elements, but got {actual_elements_count}"

    print("MicroAnsweringSignalPack audit PASSED.")

def audit_validation_signals(registry, monolith):
    print("\nAuditing ValidationSignalPack for Q001...")
    question_id = "Q001"
    signals = registry.get_validation_signals(question_id)

    monolith_question = next(q for q in monolith['blocks']['micro_questions'] if q['question_id'] == question_id)

    expected_rules_count = len(monolith_question['validations'])
    actual_rules_count = len(signals.validation_rules[question_id])
    assert actual_rules_count == expected_rules_count, f"Expected {expected_rules_count} validation rules, but got {actual_rules_count}"

    expected_emit_code = monolith_question['failure_contract']['emit_code']
    actual_emit_code = signals.failure_contracts[question_id].emit_code
    assert actual_emit_code == expected_emit_code, f"Expected emit_code {expected_emit_code}, but got {actual_emit_code}"

    print("ValidationSignalPack audit PASSED.")

def audit_assembly_signals(registry, monolith):
    print("\nAuditing AssemblySignalPack for MESO_1...")
    level = "MESO_1"
    signals = registry.get_assembly_signals(level)

    assert "MESO_1" in signals.aggregation_methods, "MESO_1 should be in aggregation_methods"

    expected_cluster = next(c for c in monolith['blocks']['niveles_abstraccion']['clusters'] if c['cluster_id'] == 'CL01')
    expected_policy_areas = expected_cluster['policy_area_ids']
    assert signals.cluster_policy_areas['CL01'] == expected_policy_areas, "cluster_policy_areas do not match"

    print("AssemblySignalPack audit PASSED.")

def audit_scoring_signals(registry, monolith):
    print("\nAuditing ScoringSignalPack for Q001...")
    question_id = "Q001"
    signals = registry.get_scoring_signals(question_id)

    monolith_question = next(q for q in monolith['blocks']['micro_questions'] if q['question_id'] == question_id)
    expected_modality = monolith_question['scoring_modality']

    assert signals.question_modalities[question_id] == expected_modality, f"Expected modality {expected_modality}, but got {signals.question_modalities[question_id]}"
    assert expected_modality in signals.modality_configs, f"{expected_modality} config not found in modality_configs"

    print("ScoringSignalPack audit PASSED.")

def main():
    try:
        # Load monolith data directly for comparison
        monolith_path = Path("data/questionnaire_monolith.json")
        monolith_data = json.loads(monolith_path.read_text(encoding='utf-8'))

        # Load questionnaire and create registry
        questionnaire = load_questionnaire()
        registry = create_signal_registry(questionnaire)

        # Run audits
        audit_chunking_signals(registry, monolith_data)
        audit_micro_answering_signals(registry, monolith_data)
        audit_validation_signals(registry, monolith_data)
        audit_assembly_signals(registry, monolith_data)
        audit_scoring_signals(registry, monolith_data)

        print("\nAll signal pack audits completed successfully.")

    except Exception as e:
        print(f"\nAn error occurred during the audit: {e}")

if __name__ == "__main__":
    main()
