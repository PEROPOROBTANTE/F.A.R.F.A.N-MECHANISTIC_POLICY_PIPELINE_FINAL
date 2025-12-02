"""
normalize_method_ids.py - Canonical ID Normalization Script

This script detects and corrects ID format divergences across all calibration
JSON files, enforcing Constraint 1: canonical_method_catalogue_v2.json is the
ONLY source of truth for method IDs.

Usage:
    # Dry run (report only)
    python scripts/calibration/normalize_method_ids.py --dry-run
    
    # Apply changes
    python scripts/calibration/normalize_method_ids.py --apply
    
    # Specific files only
    python scripts/calibration/normalize_method_ids.py --files intrinsic --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


# File paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent
CATALOG_PATH = REPO_ROOT / "config" / "canonical_method_catalogue_v2.json"
PARAMETRIZED_PATH = REPO_ROOT / "config" / "canonic_inventory_methods_parametrized.json"
LAYERS_PATH = REPO_ROOT / "config" / "canonic_inventorry_methods_layers.json"
INTRINSIC_PATH = REPO_ROOT / "system" / "config" / "calibration" / "intrinsic_calibration.json"

# Canonical ID format: module.Class.method
CANONICAL_PATTERN = re.compile(r'^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+$')


def load_json(path: Path) -> Dict:
    """Load JSON file with error handling."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def save_json(path: Path, data: Dict, dry_run: bool = True) -> None:
    """Save JSON file with pretty formatting."""
    if dry_run:
        print(f"[DRY RUN] Would write to: {path}")
        return
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Trailing newline
    
    print(f"✓ Written: {path}")


def load_canonical_ids() -> Set[str]:
    """
    Load canonical method IDs from the source of truth.
    
    [Constraint 1] canonical_method_catalogue_v2.json is the ONLY valid registry.
    
    Returns:
        Set of canonical IDs extracted from 'unique_id' field
    """
    catalog = load_json(CATALOG_PATH)
    
    if not isinstance(catalog, list):
        print("ERROR: Catalog should be a list of method entries", file=sys.stderr)
        sys.exit(1)
    
    canonical_ids = set()
    for entry in catalog:
        if 'unique_id' in entry:
            canonical_ids.add(entry['unique_id'])
    
    print(f"✓ Loaded {len(canonical_ids)} canonical IDs from catalog")
    return canonical_ids


def normalize_id(raw_id: str) -> str:
    """
    Normalize an ID to canonical format.
    
    Transformations:
    - Replace '::' with '.'
    - Replace '/' with '.'
    - Strip leading/trailing dots
    - Remove file path prefixes (keep only module.Class.method)
    - REJECT IDs with spaces (indicating backup files like "Copia de")
    
    Args:
        raw_id: Raw ID from JSON file
        
    Returns:
        Normalized ID or None if ID should be removed
    """
    normalized = raw_id
    
    # Check for spaces (indicates backup/invalid files)
    if ' ' in normalized:
        return None  # Mark for removal
    
    # Replace separators
    normalized = normalized.replace('::', '.')
    normalized = normalized.replace('/', '.')
    
    # Strip whitespace
    normalized = normalized.strip()
    
    # Remove leading/trailing dots
    normalized = normalized.strip('.')
    
    return normalized


def extract_ids_from_file(path: Path, file_type: str) -> List[str]:
    """
    Extract all method IDs from a JSON file.
    
    Args:
        path: Path to JSON file
        file_type: One of 'catalog', 'parametrized', 'layers', 'intrinsic'
        
    Returns:
        List of method IDs found in file
    """
    data = load_json(path)
    ids = []
    
    if file_type == 'catalog':
        # List of method entries
        for entry in data:
            if 'unique_id' in entry:
                ids.append(entry['unique_id'])
    
    elif file_type in ('parametrized', 'layers', 'intrinsic'):
        # Dict with method IDs as keys
        if isinstance(data, dict):
            # Skip metadata keys (starting with $)
            ids = [k for k in data.keys() if not k.startswith('$')]
        else:
            print(f"WARNING: Unexpected format in {path}", file=sys.stderr)
    
    return ids


def analyze_divergences(
    canonical_ids: Set[str],
    file_ids: Dict[str, List[str]]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Analyze ID format divergences and non-canonical IDs.
    
    Args:
        canonical_ids: Set of valid IDs from catalog
        file_ids: Dict mapping file name to list of IDs
        
    Returns:
        Tuple of (format_errors, non_canonical_errors)
        - format_errors: IDs that don't match canonical pattern
        - non_canonical_errors: IDs not present in catalog
    """
    format_errors = {}
    non_canonical_errors = {}
    
    for file_name, ids in file_ids.items():
        format_errs = []
        non_canon_errs = []
        
        for id_ in ids:
            # Check format
            if not CANONICAL_PATTERN.match(id_):
                format_errs.append(id_)
            
            # Check against catalog (skip catalog itself)
            if file_name != 'catalog' and id_ not in canonical_ids:
                non_canon_errs.append(id_)
        
        if format_errs:
            format_errors[file_name] = format_errs
        if non_canon_errs:
            non_canonical_errors[file_name] = non_canon_errs
    
    return format_errors, non_canonical_errors


def generate_report(
    format_errors: Dict[str, List[str]],
    non_canonical_errors: Dict[str, List[str]]
) -> None:
    """Print analysis report."""
    print("\n" + "="*80)
    print("CANONICAL ID NORMALIZATION REPORT")
    print("="*80)
    
    # Format errors
    if format_errors:
        print("\n❌ FORMAT ERRORS (IDs not matching canonical pattern):")
        for file_name, ids in format_errors.items():
            print(f"\n  {file_name}: {len(ids)} IDs")
            for id_ in ids[:10]:  # Show first 10
                normalized = normalize_id(id_)
                print(f"    - {id_}")
                print(f"      → {normalized}")
            if len(ids) > 10:
                print(f"    ... and {len(ids) - 10} more")
    else:
        print("\n✓ No format errors found")
    
    # Non-canonical errors
    if non_canonical_errors:
        print("\n❌ NON-CANONICAL IDs (not found in catalog):")
        for file_name, ids in non_canonical_errors.items():
            print(f"\n  {file_name}: {len(ids)} IDs")
            for id_ in ids[:5]:  # Show first 5
                print(f"    - {id_}")
            if len(ids) > 5:
                print(f"    ... and {len(ids) - 5} more")
    else:
        print("\n✓ All IDs are canonical")
    
    print("\n" + "="*80)


def apply_catalog_normalization(dry_run: bool = True) -> Set[str]:
    """
    Normalize IDs in the canonical catalog itself.
    
    Returns:
        Updated set of canonical IDs
    """
    print("\n🔧 Normalizing canonical_method_catalogue_v2.json...")
    
    catalog = load_json(CATALOG_PATH)
    updated_count = 0
    removed_count = 0
    new_canonical_ids = set()
    new_catalog = []
    
    for entry in catalog:
        if 'unique_id' in entry:
            original_id = entry['unique_id']
            normalized_id = normalize_id(original_id)
            
            # Skip entries with invalid IDs (spaces, backup files)
            if normalized_id is None:
                removed_count += 1
                continue
            
            if original_id != normalized_id:
                entry['unique_id'] = normalized_id
                updated_count += 1
            
            new_canonical_ids.add(normalized_id)
            new_catalog.append(entry)
        else:
            new_catalog.append(entry)
    
    if updated_count > 0 or removed_count > 0:
        save_json(CATALOG_PATH, new_catalog, dry_run=dry_run)
        print(f"  ✓ Normalized {updated_count} IDs, removed {removed_count} invalid IDs")
    else:
        print("  ✓ Catalog already normalized")
    
    return new_canonical_ids


def remove_non_canonical_ids(
    file_path: Path,
    file_type: str,
    canonical_ids: Set[str],
    dry_run: bool = True
) -> None:
    """
    Remove non-canonical IDs from a JSON file.
    
    Args:
        file_path: Path to JSON file
        file_type: File type identifier
        canonical_ids: Set of valid canonical IDs
        dry_run: If True, don't modify files
    """
    data = load_json(file_path)
    
    if file_type in ('layers', 'intrinsic', 'parametrized'):
        if not isinstance(data, dict):
            return
        
        # Separate metadata from methods
        metadata = {k: v for k, v in data.items() if k.startswith('$')}
        methods = {k: v for k, v in data.items() if not k.startswith('$')}
        
        # Filter to canonical IDs only
        canonical_methods = {k: v for k, v in methods.items() if k in canonical_ids}
        removed_count = len(methods) - len(canonical_methods)
        
        if removed_count > 0:
            # Reconstruct with metadata + canonical methods
            new_data = {**metadata, **canonical_methods}
            save_json(file_path, new_data, dry_run=dry_run)
            print(f"  ✓ Removed {removed_count} non-canonical IDs from {file_path.name}")
        else:
            print(f"  ✓ {file_path.name} already uses canonical IDs only")


def main():
    parser = argparse.ArgumentParser(
        description="Normalize method IDs across calibration JSON files"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Report errors without modifying files"
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help="Apply normalization changes to files"
    )
    parser.add_argument(
        '--files',
        nargs='+',
        choices=['catalog', 'parametrized', 'layers', 'intrinsic', 'all'],
        default=['all'],
        help="Specific files to check"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("ERROR: Must specify --dry-run or --apply", file=sys.stderr)
        sys.exit(1)
    
    # Load canonical IDs (source of truth)
    canonical_ids = load_canonical_ids()
    
    # Extract IDs from all files
    file_ids = {}
    
    if 'all' in args.files or 'catalog' in args.files:
        file_ids['catalog'] = extract_ids_from_file(CATALOG_PATH, 'catalog')
    
    if 'all' in args.files or 'parametrized' in args.files:
        file_ids['parametrized'] = extract_ids_from_file(PARAMETRIZED_PATH, 'parametrized')
    
    if 'all' in args.files or 'layers' in args.files:
        file_ids['layers'] = extract_ids_from_file(LAYERS_PATH, 'layers')
    
    if 'all' in args.files or 'intrinsic' in args.files:
        file_ids['intrinsic'] = extract_ids_from_file(INTRINSIC_PATH, 'intrinsic')
    
    # Analyze divergences
    format_errors, non_canonical_errors = analyze_divergences(canonical_ids, file_ids)
    
    # Generate report
    generate_report(format_errors, non_canonical_errors)
    
    # Apply fixes if requested
    if args.apply:
        print("\n🔧 APPLYING NORMALIZATION...")
        
        # Step 1: Normalize catalog (source of truth)
        if format_errors.get('catalog'):
            canonical_ids = apply_catalog_normalization(dry_run=False)
        
        # Step 2: Remove non-canonical IDs from other files
        if non_canonical_errors.get('parametrized'):
            remove_non_canonical_ids(PARAMETRIZED_PATH, 'parametrized', canonical_ids, dry_run=False)
        
        if non_canonical_errors.get('layers'):
            remove_non_canonical_ids(LAYERS_PATH, 'layers', canonical_ids, dry_run=False)
        
        if non_canonical_errors.get('intrinsic'):
            remove_non_canonical_ids(INTRINSIC_PATH, 'intrinsic', canonical_ids, dry_run=False)
        
        print("\n✅ Normalization complete! Re-run with --dry-run to verify.")
        sys.exit(0)
    
    # Exit with error if issues found in dry-run mode
    if format_errors or non_canonical_errors:
        if args.dry_run:
            print("\nRun with --apply to fix these issues (WARNING: will modify files)")
        sys.exit(1)
    else:
        print("\n✓ All IDs are canonical and properly formatted!")
        sys.exit(0)


if __name__ == '__main__':
    main()
