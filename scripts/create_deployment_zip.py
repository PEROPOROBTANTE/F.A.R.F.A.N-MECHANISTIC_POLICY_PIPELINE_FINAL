#!/usr/bin/env python3
"""
Create a deployment zip file with only the required files for maximum performance.
Excludes deprecated files, documentation, tests, and development files.
"""

import os
import zipfile
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Essential documentation files to include (all others excluded)
ESSENTIAL_DOCS = {
    'README.md',
    'QUICKSTART.md',
}

# Files and directories to exclude
EXCLUDE_PATTERNS = {
    # Deprecated files
    'ORCHESTRATOR_MONILITH.py',
    'docs/README_MONOLITH.md',

    # Documentation files (not needed for deployment)
    '*.md',
    'DOCUMENTATION_OVERVIEW.txt',

    # Development and testing
    'tests/',
    'examples/',
    '.github/',
    '.augment/',

    # IDE and dev tools
    '.vscode/',
    '.DS_Store',
    '.gitignore',
    '.importlinter',
    '.pre-commit-config.yaml',
    '.python-version',

    # Build and cache files
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.pytest_cache/',
    '.mypy_cache/',
    '.coverage',
    'htmlcov/',

    # Environment files
    '.env',
    '.env.example',
    '.env.local',

    # Git directory
    '.git/',

    # Package management
    'minipdm/',  # Separate subproject, not needed for runtime

    # Development scripts
    'scripts/verify_dependencies.py',
    'scripts/setup.sh',
    'scripts/update_imports.py',
    'atroz_quickstart.sh',

    # Tools directory (development only)
    'tools/',
}

# Essential files and directories to include
INCLUDE_PATTERNS = {
    # Main source code
    'src/',

    # Compatibility shims (needed for backward compatibility)
    'orchestrator/',
    'concurrency/',
    'core/',
    'executors/',
    'contracts/',
    'validation/',
    'scoring/',

    # Configuration files
    'config/',

    # Data files
    'data/',

    # Essential scripts
    'scripts/create_deployment_zip.py',  # This script itself

    # Root level compatibility shims
    'aggregation.py',
    'contracts.py',
    'document_ingestion.py',
    'embedding_policy.py',
    'evidence_registry.py',
    'json_contract_loader.py',
    'macro_prompts.py',
    'meso_cluster_analysis.py',
    'micro_prompts.py',
    'policy_processor.py',
    'qmcm_hooks.py',
    'recommendation_engine.py',
    'runtime_error_fixes.py',
    'schema_validator.py',
    'seed_factory.py',
    'signature_validator.py',
    'validation_engine.py',

    # Package files
    'setup.py',
    'pyproject.toml',
    'requirements.txt',
    'requirements_atroz.txt',
    'constraints.txt',
    'Makefile',

    # Symlinks
    'rules',
    'schemas',

    # Essential documentation (minimal)
    'README.md',
    'QUICKSTART.md',
}

def should_include(path: Path, base: Path) -> bool:
    """Determine if a file should be included in the deployment zip."""
    relative_path = path.relative_to(base)
    path_str = str(relative_path)

    # Check if it's the deprecated ORCHESTRATOR_MONILITH
    if 'ORCHESTRATOR_MONILITH.py' in path_str:
        return False

    # Exclude markdown files except essential ones
    if path_str.endswith('.md'):
        return path_str in ESSENTIAL_DOCS

    # Check exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith('/'):
            # Directory pattern - match at start of path components
            pattern_name = pattern.rstrip('/')
            if path_str.startswith(pattern_name + '/') or path_str == pattern_name:
                return False
        elif pattern.startswith('*.'):
            # Extension pattern
            if path_str.endswith(pattern[1:]):
                return False
        elif '/' in pattern:
            # Path pattern - exact match
            if path_str == pattern or path_str.startswith(pattern + '/'):
                return False
        else:
            # Filename pattern - match exact filename component
            parts = Path(path_str).parts
            if pattern in parts:
                return False

    # Check include patterns
    for pattern in INCLUDE_PATTERNS:
        if pattern.endswith('/'):
            # Directory pattern
            if path_str.startswith(pattern.rstrip('/')):
                return True
        elif pattern == path_str:
            # Exact match
            return True

    # If in src/ directory, include by default
    return bool(path_str.startswith('src/'))

def create_deployment_zip(output_path: Path) -> None:
    """Create a deployment zip file."""
    print(f"Creating deployment zip at {output_path}")

    included_files: list[str] = []
    excluded_files: list[str] = []

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            root_path = Path(root)

            # Skip excluded directories
            dirs_to_remove = []
            for d in dirs:
                dir_path = root_path / d
                if not should_include(dir_path, BASE_DIR):
                    dirs_to_remove.append(d)

            for d in dirs_to_remove:
                dirs.remove(d)

            # Add files
            for file in files:
                file_path = root_path / file

                if should_include(file_path, BASE_DIR):
                    arcname = file_path.relative_to(BASE_DIR)
                    zipf.write(file_path, arcname)
                    included_files.append(str(arcname))
                else:
                    excluded_files.append(str(file_path.relative_to(BASE_DIR)))

    print("\n✅ Deployment zip created successfully!")
    print(f"   Output: {output_path}")
    print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Included files: {len(included_files)}")
    print(f"   Excluded files: {len(excluded_files)}")

    # Print summary
    print("\n📦 Included components:")
    components = set()
    for f in included_files:
        component = f.split('/')[0] if '/' in f else f
        components.add(component)
    for comp in sorted(components):
        count = sum(1 for f in included_files if f.startswith(comp))
        print(f"   - {comp}: {count} files")

    print("\n🚫 Excluded deprecated/development files:")
    print(f"   - Total excluded: {len(excluded_files)}")

    # Count different types of excluded files
    deprecated_count = sum(1 for f in excluded_files if 'MONOLITH' in f)
    doc_count = sum(1 for f in excluded_files if f.endswith('.md'))
    test_count = sum(1 for f in excluded_files if f.startswith('tests/'))
    example_count = sum(1 for f in excluded_files if f.startswith('examples/'))

    print(f"   - Deprecated files: {deprecated_count}")
    print(f"   - Documentation: {doc_count}")
    print(f"   - Tests: {test_count}")
    print(f"   - Examples: {example_count}")

    # Save manifest
    manifest_path = output_path.with_suffix('.txt')
    with open(manifest_path, 'w') as f:
        f.write("SAAAAAA Deployment Package - File Manifest\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total files: {len(included_files)}\n\n")
        f.write("Included files:\n")
        f.write("-" * 60 + "\n")
        for file in sorted(included_files):
            f.write(f"{file}\n")

    print(f"\n📄 Manifest saved to: {manifest_path}")

if __name__ == "__main__":
    output_zip = BASE_DIR / "saaaaaa-deployment.zip"
    create_deployment_zip(output_zip)
    print("\n✨ Deployment package ready for production!")
