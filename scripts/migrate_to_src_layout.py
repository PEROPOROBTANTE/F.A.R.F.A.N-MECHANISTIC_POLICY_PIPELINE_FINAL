#!/usr/bin/env python3
"""
Migration Script: Root-level Modules → src/saaaaaa/
======================================================

This script migrates root-level application modules into the canonical
src/saaaaaa/ structure according to the Path Management Strategy.

Author: Python Pipeline Expert
Date: 2025-11-15
"""

import ast
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json
import re

class SrcLayoutMigrator:
    """Migrates project to proper src-layout structure."""

    def __init__(self, root_dir: Path, dry_run: bool = True):
        self.root_dir = root_dir
        self.src_dir = root_dir / "src" / "saaaaaa"
        self.dry_run = dry_run
        self.migrations: List[Tuple[Path, Path]] = []
        self.import_replacements: Dict[str, str] = {}

    def analyze(self):
        """Analyze what needs to be migrated."""
        print("🔍 Analyzing migration requirements...\n")

        # Define root-level modules that should be in src/
        root_modules_to_migrate = {
            'orchestrator': self.src_dir / 'core' / 'orchestrator',
            'calibration': self.src_dir / 'core' / 'calibration',
            'validation': self.src_dir / 'utils' / 'validation',
            'scoring': self.src_dir / 'analysis' / 'scoring',
            'contracts': self.src_dir / 'core',  # contracts.py or contracts/
            'core': self.src_dir / 'core',  # Merge with existing
            'concurrency': self.src_dir / 'concurrency',  # Already exists in src
            'executors': self.src_dir / 'core' / 'orchestrator',  # Merge
        }

        for module_name, target_dir in root_modules_to_migrate.items():
            source_path = self.root_dir / module_name

            if not source_path.exists():
                print(f"   ⏭️  Skip: {module_name} (doesn't exist)")
                continue

            # Check if target already exists
            if source_path.is_dir():
                # Directory module
                target_exists = target_dir.exists()
                action = "MERGE" if target_exists else "MOVE"
                print(f"   {'📂' if action == 'MERGE' else '➡️'}  {action}: {module_name}/ → {target_dir.relative_to(self.root_dir)}/")

                # Find all Python files
                for py_file in source_path.rglob("*.py"):
                    rel_path = py_file.relative_to(source_path)
                    target_file = target_dir / rel_path
                    self.migrations.append((py_file, target_file))

                    # Define import replacement
                    old_import = f"{module_name}."
                    new_import_path = str(target_dir.relative_to(self.src_dir)).replace('/', '.')
                    new_import = f"saaaaaa.{new_import_path}."
                    if old_import not in self.import_replacements:
                        self.import_replacements[old_import] = new_import

            else:
                # Single file module (contracts.py)
                print(f"   📄 MOVE: {module_name}.py → {target_dir.relative_to(self.root_dir)}/{module_name}.py")
                target_file = target_dir / f"{module_name}.py"
                self.migrations.append((source_path, target_file))

                old_import = f"import {module_name}"
                new_import_path = str(target_dir.relative_to(self.src_dir)).replace('/', '.')
                new_import = f"from saaaaaa.{new_import_path} import {module_name}"
                self.import_replacements[old_import] = new_import

        print(f"\n📊 Summary:")
        print(f"   Files to migrate: {len(self.migrations)}")
        print(f"   Import patterns to update: {len(self.import_replacements)}")
        print()

    def execute_migration(self):
        """Execute the migration."""
        if self.dry_run:
            print("🏃 DRY RUN MODE - No files will be modified\n")
        else:
            print("🚀 EXECUTING MIGRATION\n")

        # Step 1: Move files
        print("1️⃣  Moving files...")
        for source, target in self.migrations:
            self._move_file(source, target)

        # Step 2: Update imports
        print("\n2️⃣  Updating imports...")
        self._update_all_imports()

        # Step 3: Deprecate old locations
        print("\n3️⃣  Creating deprecation markers...")
        self._create_deprecation_markers()

        print("\n✅ Migration complete!" if not self.dry_run else "\n✅ Dry run complete!")

    def _move_file(self, source: Path, target: Path):
        """Move a file to target location."""
        if not source.exists():
            print(f"   ⚠️  Skip: {source} (doesn't exist)")
            return

        # Check if target exists and is different
        if target.exists():
            if self._files_are_identical(source, target):
                print(f"   ⏭️  Skip: {source.name} (identical to target)")
                if not self.dry_run:
                    # Remove duplicate
                    source.unlink()
                return
            else:
                print(f"   ⚠️  Conflict: {source.name} exists at target with different content")
                # In real migration, would need manual resolution
                return

        print(f"   ➡️  {source.relative_to(self.root_dir)} → {target.relative_to(self.root_dir)}")

        if not self.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            # Don't delete source yet - wait until after import updates

    def _files_are_identical(self, file1: Path, file2: Path) -> bool:
        """Check if two files have identical content."""
        try:
            return file1.read_bytes() == file2.read_bytes()
        except Exception:
            return False

    def _update_all_imports(self):
        """Update imports in all Python files."""
        # Find all Python files in src/ and tests/
        python_files = []
        for pattern in [self.src_dir / "**/*.py", self.root_dir / "tests/**/*.py",
                       self.root_dir / "scripts/**/*.py", self.root_dir / "examples/**/*.py"]:
            python_files.extend(self.root_dir.glob(str(pattern.relative_to(self.root_dir))))

        for py_file in python_files:
            if '__pycache__' in str(py_file):
                continue
            self._update_imports_in_file(py_file)

    def _update_imports_in_file(self, file_path: Path):
        """Update imports in a single file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content

            # Pattern replacements
            for old_pattern, new_pattern in self.import_replacements.items():
                # Handle different import styles

                # 1. from saaaaaa.core.orchestrator.module import X
                old_from = f"from {old_pattern}"
                new_from = f"from {new_pattern}"
                content = content.replace(old_from, new_from)

                # 2. import orchestrator
                if old_pattern.endswith('.'):
                    module_name = old_pattern[:-1]
                    # import orchestrator → from saaaaaa.core.orchestrator import core as orchestrator
                    content = re.sub(
                        rf'^import {module_name}(\s|$)',
                        new_pattern.rstrip('.') + r'\1',
                        content,
                        flags=re.MULTILINE
                    )

            if content != original_content:
                print(f"   ✏️  Updated: {file_path.relative_to(self.root_dir)}")
                if not self.dry_run:
                    file_path.write_text(content, encoding='utf-8')

        except Exception as e:
            print(f"   ⚠️  Error updating {file_path.name}: {e}")

    def _create_deprecation_markers(self):
        """Create deprecation markers in old locations."""
        deprecated_modules = [
            'orchestrator', 'calibration', 'validation', 'scoring',
            'contracts', 'executors'
        ]

        for module_name in deprecated_modules:
            module_path = self.root_dir / module_name
            if not module_path.exists():
                continue

            if module_path.is_dir():
                init_file = module_path / "__init__.py"
                deprecation_content = f'''"""
DEPRECATED: This module has been moved to src/saaaaaa/

Please update your imports:
    OLD: from {module_name} import X
    NEW: from saaaaaa.core.{module_name} import X  (or appropriate location)

This module will be removed in a future version.
"""
import warnings
warnings.warn(
    f"Module '{module_name}' has been moved to src/saaaaaa/. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)
'''
                print(f"   📝 Deprecation: {module_name}/__init__.py")
                if not self.dry_run:
                    init_file.write_text(deprecation_content, encoding='utf-8')

    def cleanup_old_locations(self):
        """Remove old root-level directories after verification."""
        print("\n4️⃣  Cleaning up old locations...")

        old_dirs = [
            'orchestrator', 'calibration', 'validation', 'scoring',
            'contracts', 'executors', 'core', 'concurrency'
        ]

        for dir_name in old_dirs:
            dir_path = self.root_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"   🗑️  Remove: {dir_name}/")
                if not self.dry_run:
                    shutil.rmtree(dir_path)

    def verify_migration(self):
        """Verify the migration was successful."""
        print("\n5️⃣  Verifying migration...")

        issues = []

        # Check no root-level modules exist
        for item in self.root_dir.iterdir():
            if item.is_dir() and item.name not in ['src', 'tests', 'scripts', 'tools',
                                                     'docs', 'data', 'examples', '.git',
                                                     '.github', 'minipdm', 'metricas_y_seguimiento_canonico',
                                                     '__pycache__', '.pytest_cache', 'venv', '.venv']:
                if any((item / f).suffix == '.py' for f in item.iterdir() if f.is_file()):
                    issues.append(f"Root-level module still exists: {item.name}/")

        # Check all expected modules in src/
        required_modules = [
            self.src_dir / 'core' / 'orchestrator',
            self.src_dir / 'core' / 'calibration',
            self.src_dir / 'utils' / 'validation',
        ]

        for module_path in required_modules:
            if not module_path.exists():
                issues.append(f"Missing expected module: {module_path.relative_to(self.root_dir)}")

        if issues:
            print(f"   ⚠️  Found {len(issues)} issues:")
            for issue in issues:
                print(f"      - {issue}")
            return False
        else:
            print("   ✅ All checks passed!")
            return True


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent

    import argparse
    parser = argparse.ArgumentParser(description="Migrate to src-layout structure")
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without executing (default)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually execute the migration')
    parser.add_argument('--cleanup', action='store_true',
                       help='Cleanup old directories after migration')

    args = parser.parse_args()

    dry_run = not args.execute

    if args.execute:
        response = input("⚠️  This will modify files. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return 1

    migrator = SrcLayoutMigrator(root_dir, dry_run=dry_run)

    migrator.analyze()
    migrator.execute_migration()

    if args.cleanup and not dry_run:
        migrator.cleanup_old_locations()

    if not dry_run:
        migrator.verify_migration()

    print("\n📚 Next steps:")
    print("1. Run tests: pytest tests/")
    print("2. Check imports: python scripts/verify_imports.py")
    print("3. Verify install: pip install -e .")
    print("4. Review and commit changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
