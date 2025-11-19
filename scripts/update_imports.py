#!/usr/bin/env python3
"""
Script to update import statements in Python files to use the new package structure.

This script will:
1. Find all Python files in specified directories
2. Update import statements to use the new saaaaaa.* package structure
3. Create backups before modifying files
"""

import re
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Core modules - ORCHESTRATOR_MONILITH is deprecated, use modular orchestrator
    # r'\bimport ORCHESTRATOR_MONILITH\b': 'from saaaaaa.core.orchestrator import',  # DEPRECATED
    # r'\bfrom ORCHESTRATOR_MONILITH import': 'from saaaaaa.core.orchestrator import',  # DEPRECATED
    r'\bimport executors_COMPLETE_FIXED\b': 'from saaaaaa.core import executors_COMPLETE_FIXED',
    r'\bfrom executors_COMPLETE_FIXED import': 'from saaaaaa.core.executors_COMPLETE_FIXED import',
    r'\bfrom orchestrator\b': 'from saaaaaa.core.orchestrator',

    # Processing modules
    r'\bimport document_ingestion\b': 'from saaaaaa.processing import document_ingestion',
    r'\bfrom document_ingestion import': 'from saaaaaa.processing.document_ingestion import',
    r'\bimport embedding_policy\b': 'from saaaaaa.processing import embedding_policy',
    r'\bfrom embedding_policy import': 'from saaaaaa.processing.embedding_policy import',
    r'\bimport semantic_chunking_policy\b': 'from saaaaaa.processing import semantic_chunking_policy',
    r'\bfrom semantic_chunking_policy import': 'from saaaaaa.processing.semantic_chunking_policy import',
    r'\bimport aggregation\b': 'from saaaaaa.processing import aggregation',
    r'\bfrom aggregation import': 'from saaaaaa.processing.aggregation import',
    r'\bimport policy_processor\b': 'from saaaaaa.processing import policy_processor',
    r'\bfrom policy_processor import': 'from saaaaaa.processing.policy_processor import',

    # Analysis modules
    r'\bimport bayesian_multilevel_system\b': 'from saaaaaa.analysis import bayesian_multilevel_system',
    r'\bfrom bayesian_multilevel_system import': 'from saaaaaa.analysis.bayesian_multilevel_system import',
    r'\bimport Analyzer_one\b': 'from saaaaaa.analysis import Analyzer_one',
    r'\bfrom Analyzer_one import': 'from saaaaaa.analysis.Analyzer_one import',
    r'\bimport contradiction_deteccion\b': 'from saaaaaa.analysis import contradiction_deteccion',
    r'\bfrom contradiction_deteccion import': 'from saaaaaa.analysis.contradiction_deteccion import',
    r'\bimport teoria_cambio\b': 'from saaaaaa.analysis import teoria_cambio',
    r'\bfrom teoria_cambio import': 'from saaaaaa.analysis.teoria_cambio import',
    r'\bimport derek_beach\b': 'from saaaaaa.analysis import derek_beach',
    r'\bfrom derek_beach import': 'from saaaaaa.analysis.derek_beach import',
    r'\bimport financiero_viabilidad_tablas\b': 'from saaaaaa.analysis import financiero_viabilidad_tablas',
    r'\bfrom financiero_viabilidad_tablas import': 'from saaaaaa.analysis.financiero_viabilidad_tablas import',
    r'\bimport meso_cluster_analysis\b': 'from saaaaaa.analysis import meso_cluster_analysis',
    r'\bfrom meso_cluster_analysis import': 'from saaaaaa.analysis.meso_cluster_analysis import',
    r'\bimport macro_prompts\b': 'from saaaaaa.analysis import macro_prompts',
    r'\bfrom macro_prompts import': 'from saaaaaa.analysis.macro_prompts import',
    r'\bimport micro_prompts\b': 'from saaaaaa.analysis import micro_prompts',
    r'\bfrom micro_prompts import': 'from saaaaaa.analysis.micro_prompts import',
    r'\bimport recommendation_engine\b': 'from saaaaaa.analysis import recommendation_engine',
    r'\bfrom recommendation_engine import': 'from saaaaaa.analysis.recommendation_engine import',
    r'\bimport enhance_recommendation_rules\b': 'from saaaaaa.analysis import enhance_recommendation_rules',
    r'\bfrom enhance_recommendation_rules import': 'from saaaaaa.analysis.enhance_recommendation_rules import',
    r'\bfrom scoring\b': 'from saaaaaa.analysis.scoring',

    # API modules
    r'\bimport api_server\b': 'from saaaaaa.api import api_server',
    r'\bfrom api_server import': 'from saaaaaa.api.api_server import',

    # Utility modules
    r'\bimport adapters\b': 'from saaaaaa.utils import adapters',
    r'\bfrom adapters import': 'from saaaaaa.utils.adapters import',
    r'\bimport contracts\b': 'from saaaaaa.utils import contracts',
    r'\bfrom contracts import': 'from saaaaaa.utils.contracts import',
    r'\bimport core_contracts\b': 'from saaaaaa.utils import core_contracts',
    r'\bfrom core_contracts import': 'from saaaaaa.utils.core_contracts import',
    r'\bimport signature_validator\b': 'from saaaaaa.utils import signature_validator',
    r'\bfrom signature_validator import': 'from saaaaaa.utils.signature_validator import',
    r'\bimport schema_monitor\b': 'from saaaaaa.utils import schema_monitor',
    r'\bfrom schema_monitor import': 'from saaaaaa.utils.schema_monitor import',
    r'\bimport validation_engine\b': 'from saaaaaa.utils import validation_engine',
    r'\bfrom validation_engine import': 'from saaaaaa.utils.validation_engine import',
    r'\bimport runtime_error_fixes\b': 'from saaaaaa.utils import runtime_error_fixes',
    r'\bfrom runtime_error_fixes import': 'from saaaaaa.utils.runtime_error_fixes import',
    r'\bimport evidence_registry\b': 'from saaaaaa.utils import evidence_registry',
    r'\bfrom evidence_registry import': 'from saaaaaa.utils.evidence_registry import',
    r'\bimport metadata_loader\b': 'from saaaaaa.utils import metadata_loader',
    r'\bfrom metadata_loader import': 'from saaaaaa.utils.metadata_loader import',
    r'\bimport json_contract_loader\b': 'from saaaaaa.utils import json_contract_loader',
    r'\bfrom json_contract_loader import': 'from saaaaaa.utils.json_contract_loader import',
    r'\bimport seed_factory\b': 'from saaaaaa.utils import seed_factory',
    r'\bfrom seed_factory import': 'from saaaaaa.utils.seed_factory import',
    r'\bimport qmcm_hooks\b': 'from saaaaaa.utils import qmcm_hooks',
    r'\bfrom qmcm_hooks import': 'from saaaaaa.utils.qmcm_hooks import',
    r'\bimport coverage_gate\b': 'from saaaaaa.utils import coverage_gate',
    r'\bfrom coverage_gate import': 'from saaaaaa.utils.coverage_gate import',
    r'\bfrom validation\b': 'from saaaaaa.utils.validation',
    r'\bfrom determinism\b': 'from saaaaaa.utils.determinism',

    # Concurrency modules
    r'\bfrom concurrency\b': 'from saaaaaa.concurrency',
}

# File path mappings for configuration/data files
FILE_PATH_MAPPINGS = {
    r'\bquestionnaire_monolith\.json\b': 'data/questionnaire_monolith.json',
    r'\binteraction_matrix\.csv\b': 'data/interaction_matrix.csv',
    r'\bprovenance\.csv\b': 'data/provenance.csv',
    r'\binventory\.json\b': 'config/inventory.json',
    r'\bexecution_mapping\.yaml\b': 'config/execution_mapping.yaml',
    r'\bmethod_counts\.json\b': 'config/method_counts.json',
    r'\bforge_manifest\.json\b': 'config/forge_manifest.json',
}

def update_file_imports(file_path: Path, dry_run: bool = True) -> tuple[bool, list[str]]:
    """
    Update import statements in a Python file.

    Args:
        file_path: Path to the Python file
        dry_run: If True, only report changes without modifying the file

    Returns:
        Tuple of (was_modified, list_of_changes)
    """
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False, []

    original_content = content
    changes = []

    # Update import statements
    for pattern, replacement in IMPORT_MAPPINGS.items():
        matches = re.finditer(pattern, content)
        for match in matches:
            old_import = match.group(0)
            # Replace the matched pattern
            if old_import.startswith('import '):
                new_line = re.sub(pattern, replacement, old_import)
            else:
                new_line = re.sub(pattern, replacement, old_import)

            content = content.replace(old_import, new_line)
            changes.append(f"  {old_import} -> {new_line}")

    # Update file path references
    for pattern, replacement in FILE_PATH_MAPPINGS.items():
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"  Path updated: {pattern} -> {replacement}")

    if content != original_content:
        if not dry_run:
            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return True, changes

    return False, []

def main():
    """Main function to update imports in all Python files."""
    import argparse

    parser = argparse.ArgumentParser(description='Update import statements to new package structure')
    parser.add_argument('directories', nargs='+', help='Directories to process (e.g., tests examples scripts)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--no-backup', action='store_true', help='Do not create .bak backup files')

    args = parser.parse_args()

    total_files = 0
    modified_files = 0

    for directory in args.directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Warning: Directory {directory} does not exist")
            continue

        print(f"\nProcessing directory: {directory}")
        print("=" * 80)

        for py_file in dir_path.rglob('*.py'):
            total_files += 1
            was_modified, changes = update_file_imports(py_file, dry_run=args.dry_run)

            if was_modified:
                modified_files += 1
                print(f"\n{py_file}:")
                for change in changes:
                    print(change)

    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Files {'that would be ' if args.dry_run else ''}modified: {modified_files}")

    if args.dry_run:
        print("\nThis was a dry run. Use without --dry-run to actually modify files.")
    else:
        print("\nFiles have been updated. Backup files created with .bak extension.")

if __name__ == '__main__':
    main()
