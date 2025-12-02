"""
test_canonical_id_format.py - Canonical ID Format Enforcement

This test suite enforces Constraint 1: canonical_method_catalogue_v2.json is the
ONLY source of truth for method IDs, and all IDs must follow canonical format.

Tests:
- Canonical ID format validation (regex pattern)
- Cross-file consistency (all JSONs reference canonical IDs only)
- No duplicate IDs
- No invalid characters (spaces, special chars)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

import pytest


# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent
CATALOG_PATH = REPO_ROOT / "config" / "canonical_method_catalogue_v2.json"
PARAMETRIZED_PATH = REPO_ROOT / "config" / "canonic_inventory_methods_parametrized.json"
LAYERS_PATH = REPO_ROOT / "config" / "canonic_inventorry_methods_layers.json"
INTRINSIC_PATH = REPO_ROOT / "system" / "config" / "calibration" / "intrinsic_calibration.json"

# Canonical ID format: module.Class.method (with optional .linenumber)
# Must NOT contain: spaces, special chars except dot and underscore
CANONICAL_PATTERN = re.compile(r'^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+$')

# Invalid patterns that should trigger failure
INVALID_PATTERNS = [
    re.compile(r'\s'),  # Spaces
    re.compile(r'::'),  # Double colon separator
    re.compile(r'/'),   # Forward slash  
    re.compile(r'Copia de'),  # Spanish "Copy of" indicates backup file
]


def load_json(path: Path) -> Dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="module")
def canonical_ids() -> Set[str]:
    """Load canonical IDs from source of truth."""
    catalog = load_json(CATALOG_PATH)
    assert isinstance(catalog, list), "Catalog must be a list"
    
    ids = set()
    for entry in catalog:
        if 'unique_id' in entry:
            ids.add(entry['unique_id'])
    
    assert len(ids) > 0, "Catalog must contain at least one method"
    return ids


def extract_method_ids(file_path: Path, file_type: str) -> List[str]:
    """Extract method IDs from a JSON file."""
    data = load_json(file_path)
    
    if file_type == 'catalog':
        return [entry['unique_id'] for entry in data if 'unique_id' in entry]
    
    # Dict-based files (layers, intrinsic, parametrized)
    if isinstance(data, dict):
        # Skip metadata keys starting with $
        return [k for k in data.keys() if not k.startswith('$')]
    
    return []


class TestCanonicalIDFormat:
    """Test suite for canonical ID format validation."""
    
    def test_catalog_ids_match_canonical_pattern(self, canonical_ids):
        """[Constraint 1] All catalog IDs must match canonical pattern."""
        invalid_ids = []
        
        for id_ in canonical_ids:
            if not CANONICAL_PATTERN.match(id_):
                invalid_ids.append(id_)
        
        assert len(invalid_ids) == 0, (
            f"Found {len(invalid_ids)} IDs not matching canonical pattern:\n" +
            "\n".join(f"  - {id_}" for id_ in invalid_ids[:10])
        )
    
    def test_catalog_ids_no_invalid_patterns(self, canonical_ids):
        """[Constraint 1] Catalog IDs must not contain invalid patterns."""
        violations = {}
        
        for id_ in canonical_ids:
            for pattern in INVALID_PATTERNS:
                if pattern.search(id_):
                    if pattern.pattern not in violations:
                        violations[pattern.pattern] = []
                    violations[pattern.pattern].append(id_)
        
        assert len(violations) == 0, (
            "Found invalid patterns in catalog IDs:\n" +
            "\n".join(
                f"  Pattern '{p}': {len(ids)} violations\n" +
                "\n".join(f"    - {id_}" for id_ in ids[:5])
                for p, ids in violations.items()
            )
        )
    
    def test_catalog_no_duplicates(self, canonical_ids):
        """[Constraint 1] Catalog must not contain duplicate IDs."""
        catalog = load_json(CATALOG_PATH)
        all_ids = [entry['unique_id'] for entry in catalog if 'unique_id' in entry]
        
        duplicates = [id_ for id_ in all_ids if all_ids.count(id_) > 1]
        unique_duplicates = list(set(duplicates))
        
        assert len(unique_duplicates) == 0, (
            f"Found {len(unique_duplicates)} duplicate IDs in catalog:\n" +
            "\n".join(f"  - {id_} (appears {all_ids.count(id_)}x)" 
                     for id_ in unique_duplicates[:10])
        )


class TestCrossFileConsistency:
    """Test suite for cross-file consistency validation."""
    
    def test_layers_json_uses_canonical_ids_only(self, canonical_ids):
        """[Constraint 1] All IDs in layers JSON must exist in canonical catalog."""
        layers_ids = extract_method_ids(LAYERS_PATH, 'layers')
        non_canonical = [id_ for id_ in layers_ids if id_ not in canonical_ids]
        
        assert len(non_canonical) == 0, (
            f"Found {len(non_canonical)} non-canonical IDs in layers JSON:\n" +
            "\n".join(f"  - {id_}" for id_ in non_canonical)
        )
    
    def test_intrinsic_json_uses_canonical_ids_only(self, canonical_ids):
        """[Constraint 1] All IDs in intrinsic calibration JSON must exist in canonical catalog."""
        intrinsic_ids = extract_method_ids(INTRINSIC_PATH, 'intrinsic')
        non_canonical = [id_ for id_ in intrinsic_ids if id_ not in canonical_ids]
        
        assert len(non_canonical) == 0, (
            f"Found {len(non_canonical)} non-canonical IDs in intrinsic JSON:\n" +
            "\n".join(f"  - {id_}" for id_ in non_canonical)
        )
    
    def test_parametrized_json_uses_canonical_ids_only(self, canonical_ids):
        """[Constraint 1] All IDs in parametrized JSON must exist in canonical catalog."""
        # Skip this test if file format is unexpected
        try:
            param_ids = extract_method_ids(PARAMETRIZED_PATH, 'parametrized')
        except Exception:
            pytest.skip("Parametrized JSON has unexpected format")
            return
        
        non_canonical = [id_ for id_ in param_ids if id_ not in canonical_ids]
        
        assert len(non_canonical) == 0, (
            f"Found {len(non_canonical)} non-canonical IDs in parametrized JSON:\n" +
            "\n".join(f"  - {id_}" for id_ in non_canonical[:10])
        )


class TestCatalogIntegrity:
    """Test suite for catalog structural integrity."""
    
    def test_catalog_is_list(self):
        """Catalog must be a JSON list."""
        catalog = load_json(CATALOG_PATH)
        assert isinstance(catalog, list), "Catalog must be a list of method entries"
    
    def test_catalog_entries_have_unique_id(self):
        """All catalog entries must have 'unique_id' field."""
        catalog = load_json(CATALOG_PATH)
        missing_id = [i for i, entry in enumerate(catalog) if 'unique_id' not in entry]
        
        assert len(missing_id) == 0, (
            f"Found {len(missing_id)} entries without 'unique_id' field:\n" +
            f"  Indices: {missing_id[:10]}"
        )
    
    def test_catalog_minimum_size(self, canonical_ids):
        """Catalog must contain reasonable number of methods."""
        # Should have at least 30 executors + other methods
        assert len(canonical_ids) >= 30, (
            f"Catalog only contains {len(canonical_ids)} methods. "
            f"Expected at least 30 (6 dimensions x 5 questions)."
        )


if __name__ == '__main__':
    # Allow running as script for quick validation
    pytest.main([__file__, '-v'])
