#!/usr/bin/env python3
"""
Update questionnaire_monolith.json with correct method_sets from executors.py.

This script:
1. Reads executor_methods_mapping.json
2. Updates each micro_question's method_sets in questionnaire_monolith.json
3. Preserves all other fields unchanged
"""

import json
from pathlib import Path

def main():
    # Paths
    project_root = Path(__file__).parent
    mapping_path = project_root / "executor_methods_mapping.json"
    monolith_path = project_root / "data" / "questionnaire_monolith.json"
    backup_path = project_root / "data" / "questionnaire_monolith.json.backup"

    print("Loading executor methods mapping...")
    with open(mapping_path, 'r', encoding='utf-8') as f:
        methods_mapping = json.load(f)

    print(f"Loaded {len(methods_mapping)} executor method sets")

    print("Loading questionnaire monolith...")
    with open(monolith_path, 'r', encoding='utf-8') as f:
        monolith = json.load(f)

    # Create backup
    print("Creating backup...")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(monolith, f, indent=2, ensure_ascii=False)
    print(f"Backup created: {backup_path}")

    # Update method_sets for each micro_question
    updated_count = 0
    skipped_count = 0

    micro_questions = monolith.get("blocks", {}).get("micro_questions", [])
    print(f"Found {len(micro_questions)} micro-questions in monolith")

    for question in micro_questions:
        base_slot = question.get("base_slot")
        if not base_slot:
            print(f"  Warning: Question {question.get('question_id', 'UNKNOWN')} has no base_slot")
            skipped_count += 1
            continue

        # Look up methods for this base_slot
        if base_slot not in methods_mapping:
            print(f"  Warning: No methods found for {base_slot}")
            skipped_count += 1
            continue

        methods = methods_mapping[base_slot]

        # Build method_sets array
        method_sets = []
        for i, method_info in enumerate(methods, start=1):
            class_name = method_info["class"]
            method_name = method_info["method"]

            # Determine method_type based on heuristics
            if "validate" in method_name.lower() or "audit" in method_name.lower():
                method_type = "validation"
            elif "extract" in method_name.lower() or "parse" in method_name.lower():
                method_type = "extraction"
            elif "score" in method_name.lower() or "calculate" in method_name.lower():
                method_type = "scoring"
            elif "analyze" in method_name.lower() or "evaluate" in method_name.lower():
                method_type = "analysis"
            else:
                method_type = "analysis"  # default

            # Create description
            description = f"{class_name}.{method_name}"

            method_sets.append({
                "class": class_name,
                "function": method_name,  # Note: using "function" not "method"
                "method_type": method_type,
                "priority": i,
                "description": description
            })

        # Update the question's method_sets
        question["method_sets"] = method_sets
        updated_count += 1

        if updated_count % 50 == 0:
            print(f"  Updated {updated_count} questions...")

    print(f"\nUpdate complete:")
    print(f"  - Updated: {updated_count} questions")
    print(f"  - Skipped: {skipped_count} questions")

    # Write updated monolith
    print("Writing updated monolith...")
    with open(monolith_path, 'w', encoding='utf-8') as f:
        json.dump(monolith, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully updated {monolith_path}")
    print(f"   Backup available at: {backup_path}")

if __name__ == "__main__":
    main()
