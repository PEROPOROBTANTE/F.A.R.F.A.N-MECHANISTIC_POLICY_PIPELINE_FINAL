#!/usr/bin/env python3
"""
Canonical Flux Analyzer
========================
Analyzes the project to identify files in the canonical deterministic flux
and classify files into categories:
- A: Outdated and insular
- B: Updated but insular
- C: Updated but with competition (newer replacement exists)
- D: Outdated/Updated but value hasn't been replaced

Author: Python Pipeline Expert
Date: 2025-11-15
"""

import ast
import os
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
import hashlib

@dataclass
class FileMetadata:
    """Metadata for a Python file."""
    path: Path
    imports: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    last_modified: float = 0.0
    size: int = 0
    has_tests: bool = False
    has_docstrings: bool = False
    has_type_hints: bool = False
    is_in_src: bool = False
    is_canonical: bool = False
    classification: Optional[str] = None
    reason: str = ""
    duplicates: List[Path] = field(default_factory=list)

class CanonicalFluxAnalyzer:
    """Analyzes the canonical flux of the project."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.src_dir = root_dir / "src" / "saaaaaa"
        self.files: Dict[Path, FileMetadata] = {}
        self.canonical_files: Set[Path] = set()
        self.entry_points = [
            self.src_dir / "core" / "orchestrator" / "core.py",
            self.src_dir / "core" / "orchestrator" / "__init__.py",
        ]
        self.name_to_paths: Dict[str, List[Path]] = defaultdict(list)

    def analyze(self) -> Dict[str, any]:
        """Run complete analysis."""
        print("🔍 Starting Canonical Flux Analysis...")
        print(f"📁 Root: {self.root_dir}")
        print(f"📦 Src: {self.src_dir}")
        print()

        # Step 1: Discover all Python files
        print("1️⃣  Discovering Python files...")
        self.discover_files()
        print(f"   Found {len(self.files)} Python files")
        print()

        # Step 2: Extract imports and metadata
        print("2️⃣  Extracting imports and metadata...")
        self.extract_imports()
        print(f"   Analyzed imports for all files")
        print()

        # Step 3: Identify duplicates by name
        print("3️⃣  Identifying duplicate files...")
        self.identify_duplicates()
        duplicates_count = sum(1 for f in self.files.values() if f.duplicates)
        print(f"   Found {duplicates_count} files with duplicates")
        print()

        # Step 4: Trace canonical flux from entry points
        print("4️⃣  Tracing canonical flux from entry points...")
        self.trace_canonical_flux()
        print(f"   Canonical flux: {len(self.canonical_files)} files")
        print()

        # Step 5: Classify files
        print("5️⃣  Classifying files (A/B/C/D)...")
        self.classify_files()
        print()

        # Step 6: Generate report
        print("6️⃣  Generating report...")
        report = self.generate_report()
        print()

        return report

    def discover_files(self):
        """Discover all Python files in the project."""
        for py_file in self.root_dir.rglob("*.py"):
            # Skip venv, .git, etc.
            if any(part.startswith('.') for part in py_file.parts):
                continue
            if 'venv' in py_file.parts or '__pycache__' in py_file.parts:
                continue

            metadata = FileMetadata(
                path=py_file,
                last_modified=py_file.stat().st_mtime,
                size=py_file.stat().st_size,
                is_in_src=self.src_dir in py_file.parents or py_file.is_relative_to(self.src_dir)
            )
            self.files[py_file] = metadata

            # Track by name for duplicate detection
            self.name_to_paths[py_file.name].append(py_file)

    def extract_imports(self):
        """Extract imports from all Python files."""
        for file_path, metadata in self.files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(file_path))

                    # Extract imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                metadata.imports.add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                metadata.imports.add(node.module)

                    # Check for docstrings
                    metadata.has_docstrings = ast.get_docstring(tree) is not None

                    # Check for type hints
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.returns or any(arg.annotation for arg in node.args.args):
                                metadata.has_type_hints = True
                                break

            except Exception as e:
                print(f"   ⚠️  Error parsing {file_path.name}: {e}")

    def identify_duplicates(self):
        """Identify duplicate files by name and content similarity."""
        for name, paths in self.name_to_paths.items():
            if len(paths) > 1:
                # Sort by modification time (newest first)
                paths_sorted = sorted(paths, key=lambda p: self.files[p].last_modified, reverse=True)

                # Mark all but the newest as having duplicates
                for i, path in enumerate(paths_sorted):
                    other_paths = [p for j, p in enumerate(paths_sorted) if j != i]
                    self.files[path].duplicates = other_paths

    def trace_canonical_flux(self):
        """Trace the canonical flux starting from entry points."""
        visited = set()
        to_visit = set(ep for ep in self.entry_points if ep.exists())

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)

            if current not in self.files:
                continue

            self.canonical_files.add(current)
            self.files[current].is_canonical = True

            # Find files that this imports
            metadata = self.files[current]
            for import_name in metadata.imports:
                # Convert import to file paths
                imported_files = self.resolve_import(import_name, current)
                for imported_file in imported_files:
                    if imported_file in self.files and imported_file not in visited:
                        to_visit.add(imported_file)
                        self.files[imported_file].imported_by.add(str(current))

    def resolve_import(self, import_name: str, from_file: Path) -> List[Path]:
        """Resolve an import name to file paths."""
        results = []

        # Handle saaaaaa imports
        if import_name.startswith('saaaaaa.'):
            parts = import_name.split('.')
            # Try src/saaaaaa path
            rel_path = Path(*parts[1:])  # Skip 'saaaaaa'

            # Try as package
            candidate = self.src_dir / rel_path / "__init__.py"
            if candidate.exists() and candidate in self.files:
                results.append(candidate)

            # Try as module
            candidate = self.src_dir / f"{rel_path}.py"
            if candidate.exists() and candidate in self.files:
                results.append(candidate)

        # Handle relative imports (same directory or parent)
        elif import_name.startswith('.'):
            # This requires more context - skip for now
            pass

        # Handle absolute imports from root-level directories
        else:
            parts = import_name.split('.')
            # Try root-level directory
            candidate = self.root_dir / parts[0] / "__init__.py"
            if candidate.exists() and candidate in self.files:
                results.append(candidate)

            if len(parts) > 1:
                rel_path = Path(*parts)
                candidate = self.root_dir / f"{rel_path}.py"
                if candidate.exists() and candidate in self.files:
                    results.append(candidate)

        return results

    def classify_files(self):
        """Classify files into categories A/B/C/D."""
        for file_path, metadata in self.files.items():
            if metadata.is_canonical:
                # File is in use, skip classification
                metadata.classification = "CANONICAL"
                metadata.reason = "Part of the canonical deterministic flux"
                continue

            # Not in canonical flux - needs classification
            is_outdated = self.is_outdated(file_path, metadata)
            has_replacement = self.has_replacement(file_path, metadata)
            has_value = self.has_unique_value(file_path, metadata)

            if is_outdated and not metadata.imported_by:
                # A: Outdated and insular
                metadata.classification = "A"
                metadata.reason = "Outdated and not imported by any file (DEPRECATE)"
            elif not is_outdated and not metadata.imported_by and not has_replacement:
                # B: Updated but insular
                metadata.classification = "B"
                metadata.reason = "Updated but isolated (EVALUATE for integration)"
            elif has_replacement:
                # C: Updated but with competition
                metadata.classification = "C"
                metadata.reason = f"Replaced by {metadata.duplicates[0].name if metadata.duplicates else 'newer version'} (EVALUATE)"
            elif has_value:
                # D: Has value that hasn't been replaced
                metadata.classification = "D"
                metadata.reason = "Has unique value not in canonical flux (REFACTOR/INTEGRATE)"
            else:
                metadata.classification = "B"
                metadata.reason = "Unclear status (REVIEW)"

    def is_outdated(self, file_path: Path, metadata: FileMetadata) -> bool:
        """Check if a file is outdated."""
        # Heuristics for outdated:
        # 1. Has duplicates and is older
        if metadata.duplicates:
            newest = max(metadata.duplicates + [file_path],
                        key=lambda p: self.files[p].last_modified if p in self.files else 0)
            if newest != file_path:
                return True

        # 2. No docstrings and no type hints
        if not metadata.has_docstrings and not metadata.has_type_hints:
            return True

        # 3. Very small files (< 100 bytes)
        if metadata.size < 100:
            return True

        return False

    def has_replacement(self, file_path: Path, metadata: FileMetadata) -> bool:
        """Check if file has a replacement in canonical flux."""
        if not metadata.duplicates:
            return False

        for dup in metadata.duplicates:
            if dup in self.files and self.files[dup].is_canonical:
                return True
        return False

    def has_unique_value(self, file_path: Path, metadata: FileMetadata) -> bool:
        """Check if file has unique value."""
        # Heuristics:
        # 1. Has substantial size (> 1KB)
        if metadata.size > 1000:
            # 2. Has docstrings or type hints
            if metadata.has_docstrings or metadata.has_type_hints:
                # 3. Not a duplicate or is the newest duplicate
                if not metadata.duplicates:
                    return True
                newest = max(metadata.duplicates + [file_path],
                           key=lambda p: self.files[p].last_modified if p in self.files else 0)
                if newest == file_path:
                    return True
        return False

    def generate_report(self) -> Dict:
        """Generate comprehensive report."""
        report = {
            "summary": {
                "total_files": len(self.files),
                "canonical_files": len(self.canonical_files),
                "non_canonical_files": len(self.files) - len(self.canonical_files),
            },
            "classifications": {
                "A": [],  # Outdated and insular
                "B": [],  # Updated but insular
                "C": [],  # Updated but with competition
                "D": [],  # Has value not replaced
                "CANONICAL": []
            },
            "duplicates": {},
            "recommendations": []
        }

        # Collect classifications
        for file_path, metadata in self.files.items():
            rel_path = file_path.relative_to(self.root_dir)

            file_info = {
                "path": str(rel_path),
                "size": metadata.size,
                "last_modified": metadata.last_modified,
                "imports": len(metadata.imports),
                "imported_by": len(metadata.imported_by),
                "reason": metadata.reason,
                "duplicates": [str(d.relative_to(self.root_dir)) for d in metadata.duplicates]
            }

            if metadata.classification:
                report["classifications"][metadata.classification].append(file_info)

        # Collect duplicates summary
        for name, paths in self.name_to_paths.items():
            if len(paths) > 1:
                report["duplicates"][name] = [str(p.relative_to(self.root_dir)) for p in paths]

        # Generate recommendations
        report["recommendations"] = self.generate_recommendations(report)

        # Print summary
        print("\n" + "="*80)
        print("📊 CANONICAL FLUX ANALYSIS REPORT")
        print("="*80)
        print(f"\n📦 Total Files: {report['summary']['total_files']}")
        print(f"✅ Canonical Files (in use): {report['summary']['canonical_files']}")
        print(f"❌ Non-Canonical Files: {report['summary']['non_canonical_files']}")
        print()

        print("📂 Classifications:")
        for cat, files in report["classifications"].items():
            if cat == "CANONICAL":
                continue
            print(f"   {cat}: {len(files)} files")
            if files:
                for f in files[:3]:  # Show first 3
                    print(f"      - {f['path']}")
                if len(files) > 3:
                    print(f"      ... and {len(files) - 3} more")

        print(f"\n🔄 Duplicate File Names: {len(report['duplicates'])}")
        for name, paths in list(report["duplicates"].items())[:5]:
            print(f"   {name}:")
            for p in paths:
                print(f"      - {p}")

        print(f"\n💡 Recommendations: {len(report['recommendations'])}")
        for rec in report["recommendations"][:5]:
            print(f"   - {rec}")

        return report

    def generate_recommendations(self, report: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Category A - Deprecate
        a_files = report["classifications"]["A"]
        if a_files:
            recommendations.append(
                f"DEPRECATE {len(a_files)} outdated and insular files (Category A)"
            )

        # Category C - Handle duplicates
        c_files = report["classifications"]["C"]
        if c_files:
            recommendations.append(
                f"REMOVE {len(c_files)} files that have canonical replacements (Category C)"
            )

        # Category D - Refactor
        d_files = report["classifications"]["D"]
        if d_files:
            recommendations.append(
                f"INTEGRATE {len(d_files)} files with unique value (Category D)"
            )

        # Category B - Review
        b_files = report["classifications"]["B"]
        if b_files:
            recommendations.append(
                f"REVIEW {len(b_files)} isolated updated files (Category B)"
            )

        # Root-level duplicates
        root_duplicates = [
            name for name, paths in report["duplicates"].items()
            if any(not str(p).startswith('src/') for p in paths)
        ]
        if root_duplicates:
            recommendations.append(
                f"CONSOLIDATE {len(root_duplicates)} root-level modules into src/saaaaaa/"
            )

        return recommendations

    def save_report(self, report: Dict, output_path: Path):
        """Save report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Report saved to: {output_path}")


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent
    analyzer = CanonicalFluxAnalyzer(root_dir)

    report = analyzer.analyze()

    # Save report
    output_path = root_dir / "canonical_flux_report.json"
    analyzer.save_report(report, output_path)

    print("\n✅ Analysis complete!")
    print(f"\nNext steps:")
    print(f"1. Review the report: {output_path}")
    print(f"2. Execute path management strategy")
    print(f"3. Reorganize folder structure")
    print(f"4. Deprecate/refactor based on classifications")

    return 0


if __name__ == "__main__":
    sys.exit(main())
