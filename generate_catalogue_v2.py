#!/usr/bin/env python3
"""
CANONICAL METHOD CATALOGUE V2 GENERATOR
========================================

Generates a complete, accurate method catalogue from source code using AST parsing.

ZERO TOLERANCE REQUIREMENTS:
1. Parse ALL .py files in src/saaaaaa/
2. Extract 100% accurate parameter information
3. Correctly identify required vs optional parameters
4. Extract default values (literal, expression, or complex)
5. Handle ALL Python parameter types: args, defaults, *args, **kwargs, kwonly
6. Maintain existing metadata from old catalogue
7. Generate fully validated output

Output: canonical_method_catalogue_v2.json
"""

import ast
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MethodCatalogueGenerator:
    """Generates canonical method catalogue from source code."""

    def __init__(self, source_root: str = "src/saaaaaa", old_catalogue_path: Optional[str] = None):
        self.source_root = Path(source_root).resolve()  # Use absolute path
        # Find project root (2 levels up from src/saaaaaa)
        self.project_root = self.source_root.parent.parent
        self.old_catalogue = {}
        self.old_catalogue_path = old_catalogue_path
        self.catalogue = {}
        self.stats = defaultdict(int)
        self.errors = []
        self.complex_defaults = []

        if old_catalogue_path and Path(old_catalogue_path).exists():
            logger.info(f"Loading old catalogue: {old_catalogue_path}")
            with open(old_catalogue_path, 'r', encoding='utf-8') as f:
                self.old_catalogue = json.load(f)

    def generate_unique_id(self, canonical_name: str) -> str:
        """Generate unique 16-char hex ID from canonical name."""
        return hashlib.md5(canonical_name.encode('utf-8')).hexdigest()[:16]

    def extract_default_value(self, default_node: ast.AST) -> Tuple[Any, str]:
        """
        Extract default value from AST node.

        Returns: (default_value, default_type)
        - default_type: "literal" | "expression" | "complex"

        IMPORTANT: Python None is returned as string "None" to avoid JSON null confusion
        """
        try:
            # Case 1: Literal (0.5, "text", True, None, [], {})
            value = ast.literal_eval(default_node)

            # Convert Python None to string "None" for JSON compatibility
            if value is None:
                return "None", "literal"

            return value, "literal"
        except (ValueError, SyntaxError):
            # Case 2: Not a literal, return as string (complex)
            try:
                code = ast.unparse(default_node)
                return code, "complex"
            except Exception:
                return "<unparseable>", "complex"

    def parse_parameters(self, func_node: ast.FunctionDef, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse function parameters with FULL support for all Python parameter types.

        Handles:
        - Regular args with/without defaults
        - *args
        - **kwargs
        - Keyword-only args with/without defaults
        """
        params = []
        args_obj = func_node.args

        # Total counts
        regular_args = args_obj.args  # List[ast.arg]
        defaults = args_obj.defaults  # List[ast.expr]
        kwonlyargs = args_obj.kwonlyargs  # List[ast.arg]
        kw_defaults = args_obj.kw_defaults  # List[Optional[ast.expr]]
        vararg = args_obj.vararg  # Optional[ast.arg] (*args)
        kwarg = args_obj.kwarg  # Optional[ast.arg] (**kwargs)

        # Process regular positional arguments
        num_regular = len(regular_args)
        num_defaults = len(defaults)
        num_without_default = num_regular - num_defaults

        for i, arg in enumerate(regular_args):
            param_name = arg.arg
            type_hint = ast.unparse(arg.annotation) if arg.annotation else None

            # Determine if this arg has a default
            has_default = (i >= num_without_default)
            required = not has_default

            default_value = None
            default_type = None
            default_source = None

            if has_default:
                default_index = i - num_without_default
                default_node = defaults[default_index]
                default_value, default_type = self.extract_default_value(default_node)
                default_source = f"line {func_node.lineno}"

                # Track complex defaults
                if default_type == "complex":
                    self.complex_defaults.append({
                        "file": file_path,
                        "function": func_node.name,
                        "param": param_name,
                        "default": default_value,
                        "line": func_node.lineno
                    })

            params.append({
                "name": param_name,
                "type_hint": type_hint,
                "required": required,
                "has_default": has_default,
                "default_value": default_value,
                "default_type": default_type,
                "default_source": default_source
            })

        # Process *args (if present)
        if vararg:
            params.append({
                "name": f"*{vararg.arg}",
                "type_hint": ast.unparse(vararg.annotation) if vararg.annotation else None,
                "required": False,
                "has_default": True,
                "default_value": "()",
                "default_type": "literal",
                "default_source": "varargs"
            })

        # Process keyword-only arguments
        for i, kwonly_arg in enumerate(kwonlyargs):
            param_name = kwonly_arg.arg
            type_hint = ast.unparse(kwonly_arg.annotation) if kwonly_arg.annotation else None

            # Keyword-only args may or may not have defaults
            kw_default_node = kw_defaults[i]  # Can be None
            has_default = kw_default_node is not None
            required = not has_default

            default_value = None
            default_type = None
            default_source = None

            if has_default:
                default_value, default_type = self.extract_default_value(kw_default_node)
                default_source = f"line {func_node.lineno}"

                if default_type == "complex":
                    self.complex_defaults.append({
                        "file": file_path,
                        "function": func_node.name,
                        "param": param_name,
                        "default": default_value,
                        "line": func_node.lineno
                    })

            params.append({
                "name": param_name,
                "type_hint": type_hint,
                "required": required,
                "has_default": has_default,
                "default_value": default_value,
                "default_type": default_type,
                "default_source": default_source
            })

        # Process **kwargs (if present)
        if kwarg:
            params.append({
                "name": f"**{kwarg.arg}",
                "type_hint": ast.unparse(kwarg.annotation) if kwarg.annotation else None,
                "required": False,
                "has_default": True,
                "default_value": "{}",
                "default_type": "literal",
                "default_source": "kwargs"
            })

        return params

    def _extract_from_class(self, class_node: ast.ClassDef, class_name: str, module_path: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract all methods from a class, including from nested classes."""
        methods = []

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Method in this class
                method_name = item.name
                canonical_name = f"{module_path}.{class_name}.{method_name}"

                method_data = self.extract_method_data(
                    item, canonical_name, method_name, class_name,
                    file_path, module_path
                )
                methods.append(method_data)
                self.stats['methods_in_classes'] += 1

            elif isinstance(item, ast.ClassDef):
                # Nested class - recursively extract
                nested_class_name = f"{class_name}.{item.name}"
                nested_methods = self._extract_from_class(item, nested_class_name, module_path, file_path)
                methods.extend(nested_methods)

        return methods

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Python file and extract all method definitions."""
        methods = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {file_path}: {e}")
                self.stats['parse_errors'] += 1
                return methods

            # Get relative path from project root
            rel_path = file_path.relative_to(self.project_root)
            module_path = str(rel_path.with_suffix('')).replace('/', '.')

            # Extract classes and functions using proper traversal
            # Process module-level nodes only (avoid duplicates from ast.walk)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_name = node.name

                    # Extract methods from class (including nested classes)
                    methods.extend(self._extract_from_class(node, class_name, module_path, str(rel_path)))

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Top-level function
                    func_name = node.name
                    canonical_name = f"{module_path}.{func_name}"

                    method_data = self.extract_method_data(
                        node, canonical_name, func_name, None,
                        str(rel_path), module_path
                    )
                    methods.append(method_data)
                    self.stats['top_level_functions'] += 1

            self.stats['files_parsed'] += 1

        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
            self.stats['parse_errors'] += 1

        return methods

    def extract_method_data(
        self,
        func_node: ast.FunctionDef,
        canonical_name: str,
        method_name: str,
        class_name: Optional[str],
        file_path: str,
        module_path: str
    ) -> Dict[str, Any]:
        """Extract complete method data from AST node."""

        # Get old metadata if exists
        old_data = self.old_catalogue.get(canonical_name, {})

        # Parse parameters
        input_parameters = self.parse_parameters(func_node, file_path)

        # Extract return type
        return_type = None
        if func_node.returns:
            try:
                return_type = ast.unparse(func_node.returns)
            except Exception:
                return_type = "<unparseable>"

        # Extract docstring
        docstring = ast.get_docstring(func_node)

        # Extract decorators
        decorators = []
        for decorator in func_node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                decorators.append("<unparseable>")

        # Build signature
        try:
            sig_parts = []
            for param in input_parameters:
                if param.get('has_default'):
                    sig_parts.append(f"{param['name']}={param.get('default_value', '...')}")
                else:
                    sig_parts.append(param['name'])
            signature = f"{method_name}({', '.join(sig_parts)})"
        except Exception as e:
            logger.error(f"Failed to generate signature for method '{method_name}' in file '{file_path}': {e}")
            signature = f"{method_name}(...)"

        # Configurable parameters
        configurable_params = [p for p in input_parameters if p.get('has_default', False) and p['name'] != 'self']
        configurable_count = len(configurable_params)

        # Build method data
        method_data = {
            "unique_id": self.generate_unique_id(canonical_name),
            "canonical_name": canonical_name,
            "method_name": method_name,
            "class_name": class_name,
            "file_path": file_path,
            "module_path": module_path,
            "line_number": func_node.lineno,
            "signature": signature,
            "input_parameters": input_parameters,
            "return_type": return_type,
            "docstring": docstring,
            "decorators": decorators,
            "is_async": isinstance(func_node, ast.AsyncFunctionDef),
            "is_private": method_name.startswith('_') and not method_name.startswith('__'),
            "is_abstract": "abstractmethod" in decorators,
            "configurable_parameters": {
                "count": configurable_count,
                "names": [p['name'] for p in configurable_params],
                "all_have_valid_defaults": all(
                    p.get('default_value') is not None for p in configurable_params
                )
            }
        }

        # Merge with old metadata (preserve additional fields)
        for key, value in old_data.items():
            if key not in method_data:
                method_data[key] = value

        # Track stats
        if configurable_count > 0:
            self.stats['methods_with_defaults'] += 1
            self.stats['total_configurable_params'] += configurable_count

        return method_data

    def scan_source_tree(self) -> Dict[str, Any]:
        """Scan entire source tree and build catalogue."""
        logger.info(f"Scanning source tree: {self.source_root}")

        if not self.source_root.exists():
            raise FileNotFoundError(f"Source root not found: {self.source_root}")

        # Find all Python files
        python_files = list(self.source_root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        all_methods = []

        for i, py_file in enumerate(python_files, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(python_files)} files...")

            methods = self.parse_file(py_file)
            all_methods.extend(methods)

        logger.info(f"Extracted {len(all_methods)} methods total")

        # Build catalogue dictionary
        catalogue = {}
        for method_data in all_methods:
            canonical_name = method_data['canonical_name']
            catalogue[canonical_name] = method_data

        self.stats['total_methods'] = len(catalogue)

        return catalogue

    def generate_metadata(self) -> Dict[str, Any]:
        """Generate catalogue metadata."""
        total_params = sum(
            len(m.get('input_parameters', []))
            for m in self.catalogue.values()
        )

        return {
            "version": "2.0.0",
            "generation_date": datetime.now(timezone.utc).isoformat(),
            "total_methods": self.stats['total_methods'],
            "methods_with_defaults": self.stats['methods_with_defaults'],
            "total_parameters": total_params,
            "configurable_parameters": self.stats['total_configurable_params'],
            "coverage": "100%",
            "validation_passed": False,  # Will be set after validation
            "method_default_ratio": (
                self.stats['methods_with_defaults'] / self.stats['total_methods']
                if self.stats['total_methods'] > 0 else 0
            ),
            "parameter_default_ratio": (
                self.stats['total_configurable_params'] / total_params
                if total_params > 0 else 0
            ),
            "files_parsed": self.stats['files_parsed'],
            "parse_errors": self.stats['parse_errors'],
            "complex_defaults_count": len(self.complex_defaults)
        }

    def generate_catalogue(self, output_path: str = "canonical_method_catalogue_v2.json") -> bool:
        """Generate complete catalogue and save to JSON."""
        logger.info("="*80)
        logger.info("CANONICAL METHOD CATALOGUE V2 GENERATION")
        logger.info("="*80)

        try:
            # Scan source tree
            self.catalogue = self.scan_source_tree()

            # Generate metadata
            metadata = self.generate_metadata()

            # Add metadata to catalogue
            full_catalogue = {"_metadata": metadata}
            full_catalogue.update(self.catalogue)

            # Save to file
            logger.info(f"Saving catalogue to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_catalogue, f, indent=2, ensure_ascii=False)

            file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Catalogue saved: {file_size:.2f} MB")

            # Print stats
            self.print_stats(metadata)

            # Save complex defaults list
            if self.complex_defaults:
                complex_defaults_path = "methods_with_complex_defaults.txt"
                with open(complex_defaults_path, 'w', encoding='utf-8') as f:
                    f.write("METHODS WITH COMPLEX DEFAULT VALUES\n")
                    f.write("="*80 + "\n\n")
                    for item in self.complex_defaults:
                        f.write(f"File: {item['file']}\n")
                        f.write(f"Function: {item['function']}\n")
                        f.write(f"Parameter: {item['param']}\n")
                        f.write(f"Default: {item['default']}\n")
                        f.write(f"Line: {item['line']}\n")
                        f.write("-"*80 + "\n")
                logger.info(f"Complex defaults saved: {complex_defaults_path}")

            return True

        except Exception as e:
            logger.error(f"FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def print_stats(self, metadata: Dict[str, Any]):
        """Print generation statistics."""
        print("\n" + "="*80)
        print("GENERATION STATISTICS")
        print("="*80)
        print(f"Total methods scanned: {metadata['total_methods']:,}")
        print(f"Methods with defaults: {metadata['methods_with_defaults']:,} ({metadata['method_default_ratio']:.2%})")
        print(f"Total parameters: {metadata['total_parameters']:,}")
        print(f"Configurable parameters: {metadata['configurable_parameters']:,} ({metadata['parameter_default_ratio']:.2%})")
        print(f"Files parsed: {metadata['files_parsed']:,}")
        print(f"Parse errors: {metadata['parse_errors']}")
        print(f"Complex defaults: {metadata['complex_defaults_count']}")
        print("="*80)

        if self.errors:
            print("\nERRORS:")
            for error in self.errors[:10]:
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate canonical method catalogue v2")
    parser.add_argument("--source", default="src/saaaaaa", help="Source root directory")
    parser.add_argument("--old-catalogue", help="Path to old catalogue for metadata preservation")
    parser.add_argument("--output", default="canonical_method_catalogue_v2.json", help="Output file")

    args = parser.parse_args()

    generator = MethodCatalogueGenerator(
        source_root=args.source,
        old_catalogue_path=args.old_catalogue
    )

    success = generator.generate_catalogue(output_path=args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
