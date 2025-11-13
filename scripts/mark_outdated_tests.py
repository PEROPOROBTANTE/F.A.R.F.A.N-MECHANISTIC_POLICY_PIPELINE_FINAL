#!/usr/bin/env python3
"""
Script to mark outdated tests with @pytest.mark.skip.

Reads UPDATED_TESTS_MANIFEST.json and adds pytestmark skip to outdated test files.
"""

import json
import re
from pathlib import Path


def add_skip_marker_to_file(filepath: Path, reason: str) -> bool:
    """Add pytestmark skip to a test file."""
    if not filepath.exists():
        print(f"  ⚠ File not found: {filepath}")
        return False
    
    # Read current content
    content = filepath.read_text()
    
    # Check if already marked
    if "pytestmark = pytest.mark.skip" in content:
        print(f"  ✓ Already marked: {filepath.name}")
        return True
    
    # Find the import section
    lines = content.split('\n')
    
    # Find where pytest is imported
    pytest_import_line = -1
    last_import_line = -1
    docstring_end = -1
    
    in_docstring = False
    docstring_char = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track docstring
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                docstring_char = stripped[:3]
                # Check if it's a single-line docstring (starts and ends on same line)
                if stripped.endswith(docstring_char) and len(stripped) > len(docstring_char):
                    # Single-line docstring
                    in_docstring = False
                    docstring_end = i
        else:
            if docstring_char in line:
                in_docstring = False
                docstring_end = i
        
        # Track imports
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import_line = i
            if 'pytest' in stripped:
                pytest_import_line = i
    
    # Determine where to insert
    if pytest_import_line >= 0:
        insert_line = pytest_import_line + 1
    elif last_import_line >= 0:
        insert_line = last_import_line + 1
    elif docstring_end >= 0:
        insert_line = docstring_end + 1
    else:
        insert_line = 0
    
    # Skip empty lines after insertion point
    while insert_line < len(lines) and not lines[insert_line].strip():
        insert_line += 1
    
    # Insert the pytestmark
    marker_lines = [
        "",
        "# Mark all tests in this module as outdated",
        f'pytestmark = pytest.mark.skip(reason="{reason}")',
        ""
    ]
    
    # Insert marker
    lines = lines[:insert_line] + marker_lines + lines[insert_line:]
    
    # Write back
    filepath.write_text('\n'.join(lines))
    print(f"  ✓ Marked: {filepath.name}")
    return True


def main():
    """Mark all outdated tests."""
    print("=" * 70)
    print("Marking Outdated Tests")
    print("=" * 70)
    print()
    
    # Load manifest
    manifest_path = Path(__file__).parent.parent / "tests" / "UPDATED_TESTS_MANIFEST.json"
    if not manifest_path.exists():
        print(f"✗ Manifest not found: {manifest_path}")
        return 1
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    outdated_tests = manifest.get("outdated_tests", {}).get("tests", [])
    
    if not outdated_tests:
        print("✓ No outdated tests to mark")
        return 0
    
    print(f"Found {len(outdated_tests)} outdated test files to mark\n")
    
    # Process each file
    repo_root = Path(__file__).parent.parent
    marked = 0
    skipped = 0
    
    for test_info in outdated_tests:
        filepath = repo_root / test_info["file"]
        reason = test_info["reason"]
        
        print(f"Processing: {test_info['file']}")
        if add_skip_marker_to_file(filepath, reason):
            marked += 1
        else:
            skipped += 1
    
    print()
    print("=" * 70)
    print(f"✓ Marked: {marked} files")
    if skipped > 0:
        print(f"⚠ Skipped: {skipped} files")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
