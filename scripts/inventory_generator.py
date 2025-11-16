#!/usr/bin/env python3
"""
Inventory Generator for Policy Analysis Codebase
Generates machine-readable inventory.json and provenance.csv
"""

import ast
import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

@dataclass
class FunctionInfo:
    """Function/method metadata"""
    name: str
    owner_file: str
    loc: list[int]  # [start_line, end_line]
    signature: str
    is_public: bool
    docstring: str | None
    return_type: str | None
    input_types: list[str]
    side_effects: list[str]
    cyclomatic_complexity: int
    dependencies: list[str]

@dataclass
class ClassInfo:
    """Class metadata"""
    name: str
    owner_file: str
    loc: list[int]
    is_public: bool
    docstring: str | None
    methods: list[FunctionInfo]
    base_classes: list[str]
    dependencies: list[str]

@dataclass
class FileInfo:
    """File-level metadata"""
    file_path: str
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
    imports: list[str]
    last_modified: str
    git_commit: str | None
    git_author: str | None
    lines_of_code: int

class InventoryGenerator:
    """Generate complete codebase inventory"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.inventory: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "root_directory": str(self.root_dir),
            "files": []
        }
        self.provenance: list[dict[str, str]] = []

    def analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze a single Python file"""
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        # Get git metadata
        git_info = self._get_git_info(file_path)

        # Extract imports
        imports = self._extract_imports(tree)

        # Extract classes
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node, file_path, content)
                classes.append(class_info)

        # Extract module-level functions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not self._is_class_method(node, tree):
                func_info = self._analyze_function(node, file_path, content)
                functions.append(func_info)

        return FileInfo(
            file_path=str(file_path.relative_to(self.root_dir)),
            classes=classes,
            functions=functions,
            imports=imports,
            last_modified=git_info.get('date', ''),
            git_commit=git_info.get('commit', ''),
            git_author=git_info.get('author', ''),
            lines_of_code=len(content.splitlines())
        )

    def _analyze_class(self, node: ast.ClassDef, file_path: Path, content: str) -> ClassInfo:
        """Analyze a class definition"""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._analyze_function(item, file_path, content, is_method=True)
                methods.append(method_info)

        base_classes = [self._get_name(base) for base in node.bases]

        return ClassInfo(
            name=node.name,
            owner_file=str(file_path.relative_to(self.root_dir)),
            loc=[node.lineno, node.end_lineno or node.lineno],
            is_public=not node.name.startswith('_'),
            docstring=ast.get_docstring(node),
            methods=methods,
            base_classes=base_classes,
            dependencies=self._extract_class_dependencies(node)
        )

    def _analyze_function(self, node: ast.FunctionDef, file_path: Path,
                          content: str, is_method: bool = False) -> FunctionInfo:
        """Analyze a function/method definition"""
        # Extract signature
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        signature = f"{node.name}({', '.join(args)})"

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Detect side effects
        side_effects = self._detect_side_effects(node)

        # Calculate complexity
        complexity = self._calculate_complexity(node)

        # Extract dependencies
        dependencies = self._extract_function_dependencies(node)

        return FunctionInfo(
            name=node.name,
            owner_file=str(file_path.relative_to(self.root_dir)),
            loc=[node.lineno, node.end_lineno or node.lineno],
            signature=signature,
            is_public=not node.name.startswith('_'),
            docstring=ast.get_docstring(node),
            return_type=return_type,
            input_types=args,
            side_effects=side_effects,
            cyclomatic_complexity=complexity,
            dependencies=dependencies
        )

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extract all imports from AST"""
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

    def _detect_side_effects(self, node: ast.FunctionDef) -> list[str]:
        """Detect potential side effects in function"""
        effects = []

        for child in ast.walk(node):
            # File I/O
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in ['open', 'write', 'print']:
                    effects.append('file_io')

            # Global modifications
            if isinstance(child, ast.Global):
                effects.append('global_modification')

            # Database operations
            if isinstance(child, ast.Attribute):
                if any(db in ast.unparse(child) for db in ['execute', 'commit', 'insert', 'update']):
                    effects.append('database_operation')

        return list(set(effects))

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _extract_function_dependencies(self, node: ast.FunctionDef) -> list[str]:
        """Extract function call dependencies"""
        dependencies = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies.append(ast.unparse(child.func))

        return list(set(dependencies))

    def _extract_class_dependencies(self, node: ast.ClassDef) -> list[str]:
        """Extract class-level dependencies"""
        dependencies = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        dependencies.append(target.id)

        return dependencies

    def _get_git_info(self, file_path: Path) -> dict[str, str]:
        """Get git metadata for file"""
        try:
            # Get last commit info
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%H|%an|%ai', '--', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                commit, author, date = result.stdout.strip().split('|')
                return {
                    'commit': commit,
                    'author': author,
                    'date': date
                }
        except Exception:
            pass

        return {}

    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return str(node)

    def _is_class_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is a class method"""
        for item in ast.walk(tree):
            if isinstance(item, ast.ClassDef):
                for body_item in item.body:
                    if body_item is node:
                        return True
        return False

    def generate(self, target_files: list[str]) -> None:
        """Generate inventory for specified files"""
        print("Generating inventory...")

        for file_pattern in target_files:
            file_path = self.root_dir / file_pattern

            if not file_path.exists():
                print(f"Warning: {file_path} not found")
                continue

            print(f"Analyzing {file_path.name}...")
            file_info = self.analyze_file(file_path)

            # Add to inventory
            self.inventory["files"].append(asdict(file_info))

            # Add to provenance
            if file_info.git_commit:
                self.provenance.append({
                    'file': file_info.file_path,
                    'commit_hash': file_info.git_commit,
                    'author': file_info.git_author,
                    'timestamp': file_info.last_modified
                })

        # Save inventory
        inventory_path = self.root_dir / 'inventory.json'
        with open(inventory_path, 'w', encoding='utf-8') as f:
            json.dump(self.inventory, f, indent=2, ensure_ascii=False)

        print(f"✓ Inventory saved to {inventory_path}")

        # Save provenance
        provenance_path = self.root_dir / 'provenance.csv'
        if self.provenance:
            with open(provenance_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['file', 'commit_hash', 'author', 'timestamp'])
                writer.writeheader()
                writer.writerows(self.provenance)

            print(f"✓ Provenance saved to {provenance_path}")

        # Generate README
        self._generate_readme()

    def _generate_readme(self) -> None:
        """Generate README.inventory.md"""
        readme_content = f"""# Codebase Inventory

**Generated:** {self.inventory['generated_at']}

## Statistics

- **Total Files:** {len(self.inventory['files'])}
- **Total Classes:** {sum(len(f['classes']) for f in self.inventory['files'])}
- **Total Functions:** {sum(len(f['functions']) for f in self.inventory['files']) + sum(sum(len(c['methods']) for c in f['classes']) for f in self.inventory['files'])}
- **Total LOC:** {sum(f['lines_of_code'] for f in self.inventory['files'])}

## Files

"""

        for file_info in self.inventory['files']:
            readme_content += f"\n### {file_info['file_path']}\n\n"
            readme_content += f"- **Lines of Code:** {file_info['lines_of_code']}\n"
            readme_content += f"- **Classes:** {len(file_info['classes'])}\n"
            readme_content += f"- **Functions:** {len(file_info['functions'])}\n"
            readme_content += f"- **Last Modified:** {file_info['last_modified']}\n"

            if file_info['classes']:
                readme_content += "\n**Classes:**\n"
                for cls in file_info['classes']:
                    readme_content += f"- `{cls['name']}` ({len(cls['methods'])} methods)\n"

        readme_path = self.root_dir / 'README.inventory.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"✓ README saved to {readme_path}")

def main():
    """Main entry point"""
    root_dir = Path(__file__).parent

    target_files = [
        'financiero_viabilidad_tablas.py',
        'Analyzer_one.py',
        'report_assembly.py',
        'policy_processor.py',
        'contradiction_deteccion.py',
        'derek_beach.py',
        'embedding_policy.py',
        'teoria_cambio.py'
    ]

    generator = InventoryGenerator(str(root_dir))
    generator.generate(target_files)

    print("\n✓ Inventory generation complete!")
    print("  - inventory.json")
    print("  - provenance.csv")
    print("  - README.inventory.md")

if __name__ == '__main__':
    main()
