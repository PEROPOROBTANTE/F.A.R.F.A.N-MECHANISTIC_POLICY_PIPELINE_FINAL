#!/usr/bin/env python3
"""
Bulk import test - verifies all modules can be imported
"""
import importlib
import sys
from pathlib import Path

def main() -> None:
    """Test importing all modules in the package."""
    errors = []
    success = []

    # Add src to path
    # Find all Python modules
    src_path = Path('src/saaaaaa')
    if not src_path.exists():
        print(f"Error: {src_path} does not exist")
        sys.exit(1)

    for py_file in src_path.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue

        # Convert path to module name
        rel_path = py_file.relative_to('src')
        module_name = str(rel_path.with_suffix('')).replace('/', '.')

        try:
            importlib.import_module(module_name)
            success.append(module_name)
            print(f'✓ {module_name}')
        except Exception as e:
            errors.append((module_name, str(e)))
            print(f'✗ {module_name}: {e}')

    print('\n=== Bulk Import Results ===')
    print(f'Success: {len(success)} modules')
    print(f'Errors: {len(errors)} modules')

    if errors:
        print('\nFailed imports:')
        for module, error in errors[:10]:  # Show first 10
            print(f'  - {module}: {error[:100]}')
        if len(errors) > 10:
            print(f'  ... and {len(errors) - 10} more')
        sys.exit(1)
    else:
        print('✅ All modules imported successfully')
        sys.exit(0)

if __name__ == '__main__':
    main()
