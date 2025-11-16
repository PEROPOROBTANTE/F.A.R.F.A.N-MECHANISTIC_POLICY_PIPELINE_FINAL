#!/usr/bin/env python3
"""
Code Inventory Generator - Exhaustive Static Analysis
Generates code_inventory.json and dependency_graph.md
"""

import ast
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass
class FunctionSignature:
    name: str
    parameters: list[str]
    return_annotation: str | None
    is_async: bool
    line_start: int
    line_end: int
    docstring: str | None

@dataclass
class ClassInfo:
    name: str
    bases: list[str]
    methods: list[FunctionSignature]
    line_start: int
    line_end: int
    docstring: str | None

@dataclass
class FileInventory:
    file_path: str
    relative_path: str
    content_hash: str
    sha256_hash: str
    lines_of_code: int
    last_modified: str
    classes: list[ClassInfo]
    functions: list[FunctionSignature]
    imports: list[str]
    dependencies: list[str]
    is_orphan: bool
    orphan_reason: str | None

class CodeInventoryGenerator:
    """Generate exhaustive code inventory with dependency analysis"""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.inventory: dict[str, FileInventory] = {}
        self.dependency_graph: dict[str, set[str]] = {}
        self.all_modules: set[str] = set()

        # Core producer files
        self.core_files = [
            "derek_beach.py",
            "policy_processor.py",
            "embedding_policy.py",
            "semantic_chunking_policy.py",
            "teoria_cambio.py",
            "contradiction_deteccion.py",
            "financiero_viabilidad_tablas.py",
            "report_assembly.py",
            "Analyzer_one.py",
            "orchestrator.py",
            "choreographer.py"
        ]

    def generate_inventory(self) -> dict[str, Any]:
        """Generate complete inventory"""
        print("Generating code inventory...")

        # Analyze all Python files
        for core_file in self.core_files:
            file_path = self.workspace_root / core_file
            if file_path.exists():
                self._analyze_file(file_path)

        # Detect orphaned code
        self._detect_orphans()

        # Build dependency graph
        self._build_dependency_graph()

        return self._export_inventory()

    def _analyze_file(self, file_path: Path):
        """Analyze single Python file"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Calculate hashes
            content_hash = hashlib.md5(content.encode()).hexdigest()
            sha256_hash = hashlib.sha256(content.encode()).hexdigest()

            # Count LOC (non-empty, non-comment)
            loc = sum(1 for line in content.split('\n')
                     if line.strip() and not line.strip().startswith('#'))

            # Extract classes and functions
            classes = self._extract_classes(tree)
            functions = self._extract_functions(tree)
            imports = self._extract_imports(tree)
            dependencies = self._extract_dependencies(imports)

            # Get file metadata
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

            relative_path = str(file_path.relative_to(self.workspace_root))

            inventory = FileInventory(
                file_path=str(file_path),
                relative_path=relative_path,
                content_hash=content_hash,
                sha256_hash=sha256_hash,
                lines_of_code=loc,
                last_modified=last_modified,
                classes=classes,
                functions=functions,
                imports=imports,
                dependencies=dependencies,
                is_orphan=False,
                orphan_reason=None
            )

            self.inventory[relative_path] = inventory
            self.all_modules.add(relative_path)

            print(f"✓ Analyzed {relative_path}: {len(classes)} classes, {len(functions)} functions, {loc} LOC")

        except Exception as e:
            print(f"✗ Failed to analyze {file_path}: {e}")

    def _extract_classes(self, tree: ast.AST) -> list[ClassInfo]:
        """Extract all class definitions"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_name(base) for base in node.bases]
                methods = []

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(self._extract_function_signature(item))

                docstring = ast.get_docstring(node)

                classes.append(ClassInfo(
                    name=node.name,
                    bases=bases,
                    methods=methods,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=docstring
                ))

        return classes

    def _extract_functions(self, tree: ast.AST) -> list[FunctionSignature]:
        """Extract module-level functions"""
        functions = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._extract_function_signature(node))

        return functions

    def _extract_function_signature(self, node) -> FunctionSignature:
        """Extract function signature details"""
        params = []
        for arg in node.args.args:
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {self._get_name(arg.annotation)}"
            params.append(param_str)

        return_annotation = None
        if node.returns:
            return_annotation = self._get_name(node.returns)

        docstring = ast.get_docstring(node)

        return FunctionSignature(
            name=node.name,
            parameters=params,
            return_annotation=return_annotation,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring
        )

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extract all import statements"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)

        return imports

    def _extract_dependencies(self, imports: list[str]) -> list[str]:
        """Extract internal file dependencies from imports"""
        dependencies = []

        for imp in imports:
            # Extract module name
            module_name = imp.split('.')[0]

            # Check if it's an internal module
            if any(core_file.replace('.py', '') == module_name for core_file in self.core_files):
                dependencies.append(f"{module_name}.py")

        return list(set(dependencies))

    def _get_name(self, node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)

    def _detect_orphans(self):
        """Detect orphaned modules and unreachable functions"""
        # Build reverse dependency map
        referenced_modules = set()

        for file_info in self.inventory.values():
            for dep in file_info.dependencies:
                referenced_modules.add(dep)

        # Check if orchestrator and choreographer reference each module
        orchestrator = self.inventory.get('orchestrator.py')
        choreographer = self.inventory.get('choreographer.py')

        entry_points = set()
        if orchestrator:
            entry_points.update(orchestrator.dependencies)
        if choreographer:
            entry_points.update(choreographer.dependencies)

        # Mark orphans
        for relative_path, file_info in self.inventory.items():
            if relative_path in ['orchestrator.py', 'choreographer.py']:
                continue  # Entry points are never orphans

            is_referenced = relative_path in referenced_modules
            is_entry_accessible = relative_path in entry_points

            if not is_referenced and not is_entry_accessible:
                file_info.is_orphan = True
                file_info.orphan_reason = "Not imported by any other module"
            elif not is_entry_accessible:
                file_info.is_orphan = True
                file_info.orphan_reason = "Not accessible from orchestrator/choreographer"

    def _build_dependency_graph(self):
        """Build dependency graph for export"""
        for relative_path, file_info in self.inventory.items():
            self.dependency_graph[relative_path] = set(file_info.dependencies)

    def _export_inventory(self) -> dict[str, Any]:
        """Export inventory to serializable format"""
        inventory_dict = {}

        for relative_path, file_info in self.inventory.items():
            inventory_dict[relative_path] = {
                "file_path": file_info.file_path,
                "relative_path": file_info.relative_path,
                "content_hash": file_info.content_hash,
                "sha256_hash": file_info.sha256_hash,
                "lines_of_code": file_info.lines_of_code,
                "last_modified": file_info.last_modified,
                "classes": [
                    {
                        "name": cls.name,
                        "bases": cls.bases,
                        "methods": [
                            {
                                "name": m.name,
                                "parameters": m.parameters,
                                "return_annotation": m.return_annotation,
                                "is_async": m.is_async,
                                "line_start": m.line_start,
                                "line_end": m.line_end,
                                "has_docstring": m.docstring is not None
                            }
                            for m in cls.methods
                        ],
                        "line_start": cls.line_start,
                        "line_end": cls.line_end,
                        "has_docstring": cls.docstring is not None
                    }
                    for cls in file_info.classes
                ],
                "functions": [
                    {
                        "name": f.name,
                        "parameters": f.parameters,
                        "return_annotation": f.return_annotation,
                        "is_async": f.is_async,
                        "line_start": f.line_start,
                        "line_end": f.line_end,
                        "has_docstring": f.docstring is not None
                    }
                    for f in file_info.functions
                ],
                "imports": file_info.imports,
                "dependencies": file_info.dependencies,
                "is_orphan": file_info.is_orphan,
                "orphan_reason": file_info.orphan_reason
            }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace_root": str(self.workspace_root),
            "total_files": len(self.inventory),
            "total_loc": sum(f.lines_of_code for f in self.inventory.values()),
            "orphaned_files": sum(1 for f in self.inventory.values() if f.is_orphan),
            "files": inventory_dict
        }

    def export_dependency_graph_md(self) -> str:
        """Export dependency graph as Mermaid markdown"""
        lines = [
            "# Dependency Graph (DAG)",
            "",
            "## System Architecture",
            "",
            "```mermaid",
            "graph TD"
        ]

        # Add metadata inputs (UPDATED: cuestionario_FIXED.json -> questionnaire_monolith.json)
        lines.append("    META1[execution_mapping.yaml]")
        lines.append("    META2[questionnaire_monolith.json]")
        lines.append("    META3[rubric_scoring.json]")
        lines.append("")

        # Add nodes
        for relative_path in self.inventory:
            node_id = relative_path.replace('.py', '').replace('_', '')
            label = relative_path.replace('.py', '')

            if self.inventory[relative_path].is_orphan:
                lines.append(f"    {node_id}[{label}]:::orphan")
            else:
                lines.append(f"    {node_id}[{label}]")

        lines.append("")

        # Add metadata → orchestrator edges
        lines.append("    META1 --> orchestrator")
        lines.append("    META2 --> orchestrator")
        lines.append("    META3 --> orchestrator")
        lines.append("    META1 --> choreographer")
        lines.append("")

        # Add dependency edges
        for source, deps in self.dependency_graph.items():
            source_id = source.replace('.py', '').replace('_', '')
            for dep in deps:
                dep_id = dep.replace('.py', '').replace('_', '')
                lines.append(f"    {source_id} --> {dep_id}")

        lines.append("")
        lines.append("    classDef orphan fill:#f99,stroke:#333,stroke-width:2px")
        lines.append("```")
        lines.append("")

        # Add orphan summary
        orphans = [f for f in self.inventory.values() if f.is_orphan]
        if orphans:
            lines.append("## ⚠️ Orphaned Modules")
            lines.append("")
            for orphan in orphans:
                lines.append(f"- **{orphan.relative_path}**: {orphan.orphan_reason}")
            lines.append("")

        # Add statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- Total files analyzed: {len(self.inventory)}")
        lines.append(f"- Total LOC: {sum(f.lines_of_code for f in self.inventory.values()):,}")
        lines.append(f"- Orphaned files: {len(orphans)}")
        lines.append(f"- Active dependencies: {sum(len(deps) for deps in self.dependency_graph.values())}")

        return '\n'.join(lines)

def main():
    workspace = Path(__file__).parent.parent

    generator = CodeInventoryGenerator(str(workspace))

    # Generate inventory
    inventory_data = generator.generate_inventory()

    # Create output directories
    controls_dir = workspace / "controls"
    inventories_dir = controls_dir / "inventories"
    graphs_dir = controls_dir / "graphs"

    inventories_dir.mkdir(parents=True, exist_ok=True)
    graphs_dir.mkdir(parents=True, exist_ok=True)

    # Export inventory JSON
    inventory_path = inventories_dir / "code_inventory.json"
    with open(inventory_path, 'w', encoding='utf-8') as f:
        json.dump(inventory_data, f, indent=2, sort_keys=True)

    print(f"\n✓ Inventory exported to: {inventory_path}")

    # Export dependency graph
    graph_md = generator.export_dependency_graph_md()
    graph_path = graphs_dir / "dependency_graph.md"
    with open(graph_path, 'w', encoding='utf-8') as f:
        f.write(graph_md)

    print(f"✓ Dependency graph exported to: {graph_path}")

    # Summary
    print(f"\n{'='*60}")
    print("INVENTORY SUMMARY")
    print(f"{'='*60}")
    print(f"Total files: {inventory_data['total_files']}")
    print(f"Total LOC: {inventory_data['total_loc']:,}")
    print(f"Orphaned files: {inventory_data['orphaned_files']}")

    if inventory_data['orphaned_files'] > 0:
        print(f"\n⚠️  WARNING: {inventory_data['orphaned_files']} orphaned file(s) detected")
        print("See dependency_graph.md for details")

    return 0

if __name__ == "__main__":
    sys.exit(main())
