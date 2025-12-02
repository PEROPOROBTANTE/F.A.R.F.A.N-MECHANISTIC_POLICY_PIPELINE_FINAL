"""
annotate_calibration_flags.py - Epistemological Flag Annotation

This script adds `requiere_calibracion` and `requiere_parametrizacion` flags
to canonical_method_catalogue_v2.json based on deterministic rules.

[Constraint 1] Flags are SOURCE OF TRUTH, not derived by rubric script.
[Constraint 4] Parametrization flags guide config externalization.

Usage:
    # Dry run
    python scripts/calibration/annotate_calibration_flags.py --dry-run
    
    # Apply
    python scripts/calibration/annotate_calibration_flags.py --apply

Rules:
1. requiere_calibracion = true if:
   - Method makes evaluative judgments (normative, quality scoring)
   - Epistemic tags include: normative, evaluative, quality_score
   - Layer is: score, analyzer (with normative component)

2. requiere_parametrizacion = true if:
   - Method has configurable_parameters count > 0
   - Method uses thresholds, weights, cutoffs (detected from param names)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


# File paths
REPO_ROOT = Path(__file__).parent.parent.parent
CATALOG_PATH = REPO_ROOT / "config" / "canonical_method_catalogue_v2.json"
EXECUTORS_PATH = REPO_ROOT / "src" / "farfan_pipeline" / "core" / "orchestrator" / "executors.py"

# Epistemological tags that indicate calibration need
CALIBRATION_TAGS = {
    "normative", 
    "evaluative_judgment",
    "quality_score",
    "bayesian",  # Often involves judgment on priors/interpretation
}

# Layers that typically require calibration
CALIBRATION_LAYERS = {
    "score",
    "analyzer",  # If combined with normative tags
}

# Parameter name patterns indicating parametrization need
PARAM_PATTERNS = [
    re.compile(r'threshold', re.I),
    re.compile(r'weight', re.I),
    re.compile(r'cutoff', re.I),
    re.compile(r'alpha', re.I),  # Bayesian priors
    re.compile(r'beta', re.I),
    re.compile(r'confidence', re.I),
    re.compile(r'tolerance', re.I),
]


def load_json(path: Path) -> Dict | List:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict | List) -> None:
    """Save JSON file with pretty formatting."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def extract_epistemic_tags_from_executors() -> Dict[str, List[str]]:
    """
    Extract EPISTEMIC_TAGS from executors.py.
    
    Returns:
        Dict mapping "ClassName.method_name" to list of tags
    """
    tags_map = {}
    
    # Read executors.py
    with open(EXECUTORS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find EPISTEMIC_TAGS dictionary
    # Pattern: ("ClassName", "method_name"): ["tag1", "tag2"]
    pattern = re.compile(
        r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)\s*:\s*\[([^\]]+)\]'
    )
    
    for match in pattern.finditer(content):
        class_name = match.group(1)
        method_name = match.group(2)
        tags_str = match.group(3)
        
        # Parse tags
        tags = [t.strip(' "') for t in tags_str.split(',')]
        
        # Create fully qualified name
        fqn = f"{class_name}.{method_name}"
        tags_map[fqn] = tags
    
    print(f"✓ Extracted {len(tags_map)} epistemology tags from executors.py")
    return tags_map


def should_require_calibration(
    method: Dict,
    epistemic_tags: Dict[str, List[str]]
) -> bool:
    """
    Determine if method requires calibration.
    
    Rules:
    1. Has normative/evaluative epistemic tags
    2. Layer is 'score' or 'analyzer' (with normative component)
    3. Explicitly tagged in known calibration methods
    
    Args:
        method: Method entry from catalog
        epistemic_tags: Map of method -> tags
        
    Returns:
        True if method requires calibration
    """
    method_id = method.get('unique_id', '')
    layer = method.get('layer', '')
    
    # Extract class.method from unique_id
    # Format: module.path.Class.method.line
    parts = method_id.split('.')
    if len(parts) >= 2:
        # Try to find Class.method
        for i in range(len(parts) - 1):
            potential_fqn = f"{parts[i]}.{parts[i+1]}"
            if potential_fqn in epistemic_tags:
                tags = epistemic_tags[potential_fqn]
                # Check if has calibration tags
                if any(tag in CALIBRATION_TAGS for tag in tags):
                    return True
    
    # Check layer-based rules
    if layer in CALIBRATION_LAYERS:
        # Analyzer layer only if has normative component
        if layer == "analyzer":
            # More conservative: require explicit tag
            return False
        return True
    
    return False


def should_require_parametrization(method: Dict) -> bool:
    """
    Determine if method requires parametrization.
    
    Rules:
    1. Has configurable_parameters count > 0
    2. Parameter names match parametrization patterns
    
    Args:
        method: Method entry from catalog
        
    Returns:
        True if method requires parametrization
    """
    config_params = method.get('configurable_parameters', {})
    param_count = config_params.get('count', 0)
    param_names = config_params.get('names', [])
    
    # Has configurable parameters
    if param_count > 0:
        return True
    
    # Check parameter name patterns
    for param_name in param_names:
        for pattern in PARAM_PATTERNS:
            if pattern.search(param_name):
                return True
    
    return False


def annotate_catalog(dry_run: bool = True) -> Tuple[int, int]:
    """
    Annotate catalog with calibration/parametrization flags.
    
    Args:
        dry_run: If True, don't modify file
        
    Returns:
        Tuple of (calibration_count, parametrization_count)
    """
    catalog = load_json(CATALOG_PATH)
    assert isinstance(catalog, list), "Catalog must be a list"
    
    # Extract epistemic tags from executors.py
    epistemic_tags = extract_epistemic_tags_from_executors()
    
    calibration_count = 0
    parametrization_count = 0
    
    for method in catalog:
        # Add flags
        method['requiere_calibracion'] = should_require_calibration(
            method, epistemic_tags
        )
        method['requiere_parametrizacion'] = should_require_parametrization(method)
        
        if method['requiere_calibracion']:
            calibration_count += 1
        if method['requiere_parametrizacion']:
            parametrization_count += 1
    
    if not dry_run:
        save_json(CATALOG_PATH, catalog)
        print(f"✓ Written: {CATALOG_PATH}")
    else:
        print(f"[DRY RUN] Would write to: {CATALOG_PATH}")
    
    return calibration_count, parametrization_count


def main():
    parser = argparse.ArgumentParser(
        description="Annotate catalog with calibration/parametrization flags"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Report changes without modifying files"
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help="Apply changes to catalog"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("ERROR: Must specify --dry-run or --apply", file=sys.stderr)
        sys.exit(1)
    
    print("="*80)
    print("CALIBRATION FLAG ANNOTATION")
    print("="*80)
    
    # Annotate catalog
    cal_count, param_count = annotate_catalog(dry_run=args.dry_run)
    
    print(f"\n📊 Results:")
    print(f"  - Methods requiring calibration: {cal_count}")
    print(f"  - Methods requiring parametrization: {param_count}")
    
    if args.dry_run:
        print("\nRun with --apply to modify catalog")
    else:
        print("\n✅ Catalog annotated successfully!")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
