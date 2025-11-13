#!/usr/bin/env python3
"""
Validate questionnaire_monolith.json against its JSON Schema.

This script validates the structure, integrity, and quality constraints
of the questionnaire monolith file.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("Error: jsonschema package not installed. Install with: pip install jsonschema")
    sys.exit(1)


def load_json_file(path: Path) -> Dict:
    """Load a JSON file and return its contents."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}")
        sys.exit(1)


def validate_schema(data: Dict, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validate data against schema.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validator = Draft7Validator(schema)
    errors = []
    
    for error in sorted(validator.iter_errors(data), key=lambda e: e.path):
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"  [{path}] {error.message}")
    
    return len(errors) == 0, errors


def validate_base_slot_distribution(data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that base slots are properly distributed.
    Each of 30 base slots (D1-Q1 through D6-Q5) should appear exactly 10 times.
    """
    errors = []
    micro_questions = data.get('blocks', {}).get('micro_questions', [])
    
    base_slot_counts = {}
    for q in micro_questions:
        slot = q.get('base_slot', '')
        base_slot_counts[slot] = base_slot_counts.get(slot, 0) + 1
    
    # Check that we have exactly 30 unique base slots
    if len(base_slot_counts) != 30:
        errors.append(f"  Expected 30 unique base slots, found {len(base_slot_counts)}")
    
    # Check that each base slot appears exactly 10 times
    for slot, count in sorted(base_slot_counts.items()):
        if count != 10:
            errors.append(f"  Base slot {slot} appears {count} times (expected 10)")
    
    return len(errors) == 0, errors


def validate_question_id_uniqueness(data: Dict) -> Tuple[bool, List[str]]:
    """Validate that all question IDs are unique."""
    errors = []
    all_question_ids = []
    
    # Collect all question IDs
    micro_questions = data.get('blocks', {}).get('micro_questions', [])
    for q in micro_questions:
        all_question_ids.append(q.get('question_id', ''))
    
    meso_questions = data.get('blocks', {}).get('meso_questions', [])
    for q in meso_questions:
        all_question_ids.append(q.get('question_id', ''))
    
    macro_question = data.get('blocks', {}).get('macro_question', {})
    all_question_ids.append(macro_question.get('question_id', ''))
    
    # Check for duplicates
    seen = set()
    duplicates = set()
    for qid in all_question_ids:
        if qid in seen:
            duplicates.add(qid)
        seen.add(qid)
    
    if duplicates:
        errors.append(f"  Duplicate question IDs found: {', '.join(sorted(duplicates))}")
    
    return len(errors) == 0, errors


def validate_cluster_hermeticity(data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate cluster definitions are hermetic and consistent.
    Each cluster should have correct policy areas and all policy areas must be assigned.
    """
    errors = []
    
    niveles = data.get('blocks', {}).get('niveles_abstraccion', {})
    clusters = niveles.get('clusters', [])
    policy_areas = niveles.get('policy_areas', [])
    
    # Expected cluster to policy area mappings
    expected_mappings = {
        'CL01': {'PA02', 'PA03', 'PA07'},
        'CL02': {'PA01', 'PA05', 'PA06'},
        'CL03': {'PA04', 'PA08'},
        'CL04': {'PA09', 'PA10'}
    }
    
    # Validate cluster definitions
    all_assigned_pas = set()
    for cluster in clusters:
        cluster_id = cluster.get('cluster_id', '')
        pas = set(cluster.get('policy_area_ids', []))
        all_assigned_pas.update(pas)
        
        if cluster_id in expected_mappings:
            expected = expected_mappings[cluster_id]
            if pas != expected:
                errors.append(
                    f"  Cluster {cluster_id} has policy areas {pas}, expected {expected}"
                )
    
    # Validate all policy areas are assigned to a cluster
    defined_pas = {pa['policy_area_id'] for pa in policy_areas}
    if all_assigned_pas != defined_pas:
        missing = defined_pas - all_assigned_pas
        extra = all_assigned_pas - defined_pas
        if missing:
            errors.append(f"  Policy areas not assigned to any cluster: {missing}")
        if extra:
            errors.append(f"  Policy areas in clusters but not defined: {extra}")
    
    return len(errors) == 0, errors


def validate_referential_integrity(data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate referential integrity between different sections.
    E.g., policy_area_ids in questions must exist in niveles_abstraccion.
    """
    errors = []
    
    niveles = data.get('blocks', {}).get('niveles_abstraccion', {})
    
    # Collect valid IDs
    valid_policy_areas = {pa['policy_area_id'] for pa in niveles.get('policy_areas', [])}
    valid_dimensions = {d['dimension_id'] for d in niveles.get('dimensions', [])}
    valid_clusters = {c['cluster_id'] for c in niveles.get('clusters', [])}
    
    # Check micro questions
    micro_questions = data.get('blocks', {}).get('micro_questions', [])
    for i, q in enumerate(micro_questions):
        pa_id = q.get('policy_area_id', '')
        dim_id = q.get('dimension_id', '')
        cluster_id = q.get('cluster_id', '')
        
        if pa_id not in valid_policy_areas:
            errors.append(f"  Question {i+1} references invalid policy_area_id: {pa_id}")
        if dim_id not in valid_dimensions:
            errors.append(f"  Question {i+1} references invalid dimension_id: {dim_id}")
        if cluster_id not in valid_clusters:
            errors.append(f"  Question {i+1} references invalid cluster_id: {cluster_id}")
    
    return len(errors) == 0, errors


def main():
    """Main validation function."""
    # Find repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # File paths
    monolith_path = repo_root / "data" / "questionnaire_monolith.json"
    schema_path = repo_root / "config" / "schemas" / "questionnaire_monolith.schema.json"
    
    print("=" * 80)
    print("Questionnaire Monolith Schema Validation")
    print("=" * 80)
    print()
    
    # Load files
    print(f"Loading monolith from: {monolith_path}")
    monolith = load_json_file(monolith_path)
    
    print(f"Loading schema from: {schema_path}")
    schema = load_json_file(schema_path)
    print()
    
    # Track validation results
    all_valid = True
    
    # Validation 1: JSON Schema validation
    print("1. JSON Schema Validation")
    print("-" * 80)
    is_valid, errors = validate_schema(monolith, schema)
    if is_valid:
        print("✓ Schema validation passed")
    else:
        print(f"✗ Schema validation failed with {len(errors)} errors:")
        for error in errors[:20]:  # Limit output
            print(error)
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
        all_valid = False
    print()
    
    # Validation 2: Base slot distribution
    print("2. Base Slot Distribution")
    print("-" * 80)
    is_valid, errors = validate_base_slot_distribution(monolith)
    if is_valid:
        print("✓ Base slot distribution is correct (30 slots × 10 questions each)")
    else:
        print(f"✗ Base slot distribution validation failed:")
        for error in errors:
            print(error)
        all_valid = False
    print()
    
    # Validation 3: Question ID uniqueness
    print("3. Question ID Uniqueness")
    print("-" * 80)
    is_valid, errors = validate_question_id_uniqueness(monolith)
    if is_valid:
        print("✓ All question IDs are unique (305 questions)")
    else:
        print(f"✗ Question ID uniqueness validation failed:")
        for error in errors:
            print(error)
        all_valid = False
    print()
    
    # Validation 4: Cluster hermeticity
    print("4. Cluster Hermeticity")
    print("-" * 80)
    is_valid, errors = validate_cluster_hermeticity(monolith)
    if is_valid:
        print("✓ Cluster definitions are hermetic and correct")
    else:
        print(f"✗ Cluster hermeticity validation failed:")
        for error in errors:
            print(error)
        all_valid = False
    print()
    
    # Validation 5: Referential integrity
    print("5. Referential Integrity")
    print("-" * 80)
    is_valid, errors = validate_referential_integrity(monolith)
    if is_valid:
        print("✓ Referential integrity checks passed")
    else:
        print(f"✗ Referential integrity validation failed:")
        for error in errors:
            print(error)
        all_valid = False
    print()
    
    # Summary
    print("=" * 80)
    if all_valid:
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 80)
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
