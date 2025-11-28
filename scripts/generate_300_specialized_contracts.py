#!/usr/bin/env python3
"""
Generate 300 INDIVIDUAL, SPECIALIZED contracts - one for each question in questionnaire_monolith.json

Each contract is fully customized with:
- Unique question_id (Q001-Q300)
- Question-specific patterns
- Question-specific expected_elements
- Question-specific validations
- Question-specific text as question_text
- Method binding from method_sets
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MONOLITH_PATH = PROJECT_ROOT / "data" / "questionnaire_monolith.json"
BASE_CONTRACTS_DIR = PROJECT_ROOT / "config" / "executor_contracts"
OUTPUT_DIR = BASE_CONTRACTS_DIR / "specialized"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def get_provides_key(class_name: str, method_name: str) -> str:
    """Generate dot-notation provides key."""
    namespace_map = {
        "TextMiningEngine": "text_mining",
        "IndustrialPolicyProcessor": "industrial_policy",
        "CausalExtractor": "causal_extraction",
        "FinancialAuditor": "financial_audit",
        "PDETMunicipalPlanAnalyzer": "pdet_analysis",
        "PolicyContradictionDetector": "contradiction_detection",
        "BayesianNumericalAnalyzer": "bayesian_analysis",
        "SemanticProcessor": "semantic_processing",
        "GoalExtractor": "goal_extraction",
        "ResourceAlignmentAnalyzer": "resource_alignment",
        "BudgetAuditor": "budget_audit",
        "TemporalExtractor": "temporal_extraction",
        "EntityRecognizer": "entity_recognition",
        "RelationshipMapper": "relationship_mapping",
        "CoherenceAnalyzer": "coherence_analysis",
        "MetadataExtractor": "metadata_extraction",
        "ValidationEngine": "validation",
        "ScoringEngine": "scoring",
        "ReportGenerator": "report_generation",
        "DataQualityAnalyzer": "data_quality"
    }
    namespace = namespace_map.get(class_name, class_name.lower())
    method_key = method_name.lstrip("_").replace("__", "_")
    return f"{namespace}.{method_key}"

def get_method_role(method_name: str) -> str:
    """Generate semantic role for a method."""
    role_keywords = {
        "diagnose": "diagnosis",
        "analyze": "analysis",
        "extract": "extraction",
        "parse": "parsing",
        "process": "processing",
        "match": "matching",
        "evaluate": "evaluation",
        "compare": "comparison",
        "chunk": "chunking",
        "embed": "embedding",
        "detect": "detection",
        "calculate": "calculation",
        "validate": "validation"
    }

    method_lower = method_name.lower()
    for keyword, role in role_keywords.items():
        if keyword in method_lower:
            return f"{method_name}_{role}"

    return f"{method_name}_execution"

def load_base_contract(base_slot: str) -> dict:
    """Load the base contract for a given base_slot."""
    contract_path = BASE_CONTRACTS_DIR / f"{base_slot}.v3.json"
    if not contract_path.exists():
        raise FileNotFoundError(f"Base contract not found: {contract_path}")

    with open(contract_path) as f:
        return json.load(f)

def specialize_contract(base_contract: dict, question: dict) -> dict:
    """Specialize a base contract for a specific question."""
    # Deep copy
    contract = json.loads(json.dumps(base_contract))

    # Update identity with question-specific IDs
    contract["identity"]["question_id"] = question["question_id"]
    contract["identity"]["dimension_id"] = question.get("dimension_id", "DIM00")
    contract["identity"]["policy_area_id"] = question.get("policy_area_id", "PA00")
    contract["identity"]["cluster_id"] = question.get("cluster_id", None)
    contract["identity"]["question_global"] = question.get("question_global", None)
    contract["identity"]["created_at"] = datetime.now(timezone.utc).isoformat()

    # Update question_context with question-specific data
    contract["question_context"]["question_text"] = question.get("text", "")
    contract["question_context"]["patterns"] = question.get("patterns", [])
    contract["question_context"]["expected_elements"] = question.get("expected_elements", [])
    contract["question_context"]["validations"] = question.get("validations", {})
    contract["question_context"]["scoring_modality"] = question.get("scoring_modality", "TYPE_A")

    # Update method_binding from method_sets
    if "method_sets" in question and question["method_sets"]:
        methods_array = []
        for method_spec in question["method_sets"]:
            class_name = method_spec["class"]
            method_name = method_spec["function"]
            priority = method_spec.get("priority", 99)

            methods_array.append({
                "class_name": class_name,
                "method_name": method_name,
                "priority": priority,
                "provides": get_provides_key(class_name, method_name),
                "role": get_method_role(method_name),
                "description": method_spec.get("description", f"{class_name}.{method_name}")
            })

        contract["method_binding"]["methods"] = sorted(methods_array, key=lambda m: m["priority"])
        contract["method_binding"]["method_count"] = len(methods_array)

    # Update error_handling with question-specific failure_contract
    if "failure_contract" in question:
        contract["error_handling"]["failure_contract"] = question["failure_contract"]

    # Update traceability
    contract["traceability"]["source_question_id"] = question["question_id"]
    contract["traceability"]["specialized_from_base_slot"] = question["base_slot"]
    contract["traceability"]["contract_generation_method"] = "automated_specialization_from_monolith"
    contract["traceability"]["specialization_timestamp"] = datetime.now(timezone.utc).isoformat()

    return contract

def generate_contracts(start_index: int = 0, end_index: int = 300, batch_name: str = "all") -> dict:
    """Generate specialized contracts for a range of questions."""

    # Load monolith
    with open(MONOLITH_PATH) as f:
        monolith = json.load(f)

    questions = monolith["blocks"]["micro_questions"]

    if end_index > len(questions):
        end_index = len(questions)

    questions_batch = questions[start_index:end_index]

    stats = {
        "batch_name": batch_name,
        "start_index": start_index,
        "end_index": end_index,
        "total_in_batch": len(questions_batch),
        "generated": 0,
        "errors": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print(f"\n{'='*80}")
    print(f"Generating {batch_name}: Questions {start_index+1} to {end_index}")
    print(f"{'='*80}\n")

    for i, question in enumerate(questions_batch, start=start_index+1):
        question_id = question["question_id"]
        base_slot = question["base_slot"]

        try:
            # Load base contract
            base_contract = load_base_contract(base_slot)

            # Specialize for this question
            specialized_contract = specialize_contract(base_contract, question)

            # Save
            output_path = OUTPUT_DIR / f"{question_id}.v3.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(specialized_contract, f, indent=2, ensure_ascii=False)

            stats["generated"] += 1

            method_count = len(specialized_contract["method_binding"]["methods"])
            patterns_count = len(question.get("patterns", []))

            print(f"✅ {i:3d}/300 {question_id} | base: {base_slot:8s} | "
                  f"{method_count:2d} methods | {patterns_count:2d} patterns → {output_path.name}")

        except Exception as e:
            error_msg = f"{question_id}: {str(e)}"
            stats["errors"].append(error_msg)
            print(f"❌ {i:3d}/300 {question_id} | ERROR: {e}")

    return stats

def main():
    """Main entry point."""

    # Parse args
    if len(sys.argv) > 1:
        batch_arg = sys.argv[1]

        if batch_arg == "batch1":
            stats = generate_contracts(0, 20, "Batch 1 (Q001-Q020)")
        elif batch_arg == "batch2":
            stats = generate_contracts(20, 40, "Batch 2 (Q021-Q040)")
        elif batch_arg == "batch3":
            stats = generate_contracts(40, 60, "Batch 3 (Q041-Q060)")
        elif batch_arg == "batch4":
            stats = generate_contracts(60, 80, "Batch 4 (Q061-Q080)")
        elif batch_arg == "batch5":
            stats = generate_contracts(80, 100, "Batch 5 (Q081-Q100)")
        elif batch_arg == "batch6":
            stats = generate_contracts(100, 120, "Batch 6 (Q101-Q120)")
        elif batch_arg == "batch7":
            stats = generate_contracts(120, 140, "Batch 7 (Q121-Q140)")
        elif batch_arg == "batch8":
            stats = generate_contracts(140, 160, "Batch 8 (Q141-Q160)")
        elif batch_arg == "batch9":
            stats = generate_contracts(160, 180, "Batch 9 (Q161-Q180)")
        elif batch_arg == "batch10":
            stats = generate_contracts(180, 200, "Batch 10 (Q181-Q200)")
        elif batch_arg == "batch11":
            stats = generate_contracts(200, 220, "Batch 11 (Q201-Q220)")
        elif batch_arg == "batch12":
            stats = generate_contracts(220, 240, "Batch 12 (Q221-Q240)")
        elif batch_arg == "batch13":
            stats = generate_contracts(240, 260, "Batch 13 (Q241-Q260)")
        elif batch_arg == "batch14":
            stats = generate_contracts(260, 280, "Batch 14 (Q261-Q280)")
        elif batch_arg == "batch15":
            stats = generate_contracts(280, 300, "Batch 15 (Q281-Q300)")
        elif batch_arg == "all":
            stats = generate_contracts(0, 300, "ALL 300 CONTRACTS")
        else:
            print(f"Unknown batch: {batch_arg}")
            print("Usage: python generate_300_specialized_contracts.py [batch1|batch2|...|batch15|all]")
            sys.exit(1)
    else:
        # Default: generate all
        stats = generate_contracts(0, 300, "ALL 300 CONTRACTS")

    # Print summary
    print(f"\n{'='*80}")
    print(f"✅ {stats['batch_name']}: {stats['generated']}/{stats['total_in_batch']} contracts generated")
    if stats["errors"]:
        print(f"❌ Errors: {len(stats['errors'])}")
        for error in stats["errors"][:10]:
            print(f"   {error}")
    print(f"{'='*80}\n")

    # Save stats
    stats_path = PROJECT_ROOT / "docs" / f"contract_generation_stats_{batch_arg if len(sys.argv) > 1 else 'all'}.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"📄 Stats saved: {stats_path}")

if __name__ == "__main__":
    main()
