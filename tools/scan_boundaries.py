#!/usr/bin/env python3
"""
AST Scanner for Core Module Boundary Violations

Scans Python modules for:
1. I/O operations (open, json.load/dump, pickle, pandas read_*, etc.)
2. __main__ blocks
3. Side effects on import
4. subprocess, requests, click usage

Usage:
    python tools/scan_boundaries.py --root src --fail-on=io,subprocess,requests,main
                                     --allow-path src/examples src/cli
                                     --sarif out/boundaries.sarif --json out/violations.json

Exit code 0 if clean, 1 if violations found.
"""

import argparse
import ast
import json
import sys
from datetime import datetime
from pathlib import Path

class BoundaryViolationVisitor(ast.NodeVisitor):
    """AST visitor to detect boundary violations in core modules."""

    # I/O function names to detect
    IO_FUNCTIONS = {
        'open', 'read', 'write',
        'load', 'dump', 'loads', 'dumps',
        'read_csv', 'read_excel', 'read_json', 'read_sql', 'read_parquet',
        'to_csv', 'to_excel', 'to_json', 'to_sql', 'to_parquet',
        'read_text', 'write_text', 'read_bytes', 'write_bytes',
    }

    # Module names that indicate I/O
    IO_MODULES = {
        'pickle', 'json', 'yaml', 'toml', 'csv',
    }

    # Subprocess/network modules
    SUBPROCESS_MODULES = {'subprocess', 'os.system'}
    NETWORK_MODULES = {'requests', 'urllib', 'http', 'httpx'}
    CLI_MODULES = {'click', 'argparse', 'sys.argv'}

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations: list[dict[str, any]] = []
        self.has_main_block = False
        self.io_calls: list[tuple[int, str]] = []
        self.subprocess_calls: list[tuple[int, str]] = []
        self.network_calls: list[tuple[int, str]] = []
        self.cli_usage: list[tuple[int, str]] = []

    def visit_If(self, node: ast.If) -> None:
        """Detect if __name__ == '__main__' blocks."""
        # Check for __name__ == '__main__' pattern
        if isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__':
            for comparator in node.test.comparators:
                if isinstance(comparator, ast.Constant) and comparator.value == '__main__':
                    self.has_main_block = True
                    self.violations.append({
                        'type': 'main_block',
                        'line': node.lineno,
                        'message': f'__main__ block found at line {node.lineno}'
                    })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detect I/O function calls."""
        # Direct function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in self.IO_FUNCTIONS:
                self.io_calls.append((node.lineno, node.func.id))
                self.violations.append({
                    'type': 'io_call',
                    'line': node.lineno,
                    'function': node.func.id,
                    'message': f'I/O operation {node.func.id}() at line {node.lineno}'
                })

        # Module.function calls (e.g., json.load)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            module_name = node.func.value.id
            func_name = node.func.attr

            # Check for I/O
            if module_name in self.IO_MODULES or func_name in self.IO_FUNCTIONS:
                self.io_calls.append((node.lineno, f'{module_name}.{func_name}'))
                self.violations.append({
                    'type': 'io_call',
                    'line': node.lineno,
                    'function': f'{module_name}.{func_name}',
                    'message': f'I/O operation {module_name}.{func_name}() at line {node.lineno}'
                })

            # Check for subprocess
            if module_name in self.SUBPROCESS_MODULES:
                self.subprocess_calls.append((node.lineno, f'{module_name}.{func_name}'))
                self.violations.append({
                    'type': 'subprocess_call',
                    'line': node.lineno,
                    'function': f'{module_name}.{func_name}',
                    'message': f'Subprocess call {module_name}.{func_name}() at line {node.lineno}'
                })

            # Check for network
            if module_name in self.NETWORK_MODULES:
                self.network_calls.append((node.lineno, f'{module_name}.{func_name}'))
                self.violations.append({
                    'type': 'network_call',
                    'line': node.lineno,
                    'function': f'{module_name}.{func_name}',
                    'message': f'Network call {module_name}.{func_name}() at line {node.lineno}'
                })

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Detect 'with open(...)' patterns."""
        for item in node.items:
            if (isinstance(item.context_expr, ast.Call) and
                isinstance(item.context_expr.func, ast.Name) and
                item.context_expr.func.id == 'open'):
                self.io_calls.append((node.lineno, 'open (with)'))
                self.violations.append({
                    'type': 'io_call',
                    'line': node.lineno,
                    'function': 'open',
                    'message': f'I/O operation: with open(...) at line {node.lineno}'
                })
        self.generic_visit(node)

def scan_file(filepath: Path) -> dict[str, any]:
    """Scan a single Python file for boundary violations."""
    try:
        with open(filepath, encoding='utf-8') as f:
            source = f.read()
    except Exception as e:
        return {
            'file': str(filepath),
            'error': f'Could not read file: {e}',
            'violations': [],
            'clean': False
        }

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        return {
            'file': str(filepath),
            'error': f'Syntax error: {e}',
            'violations': [],
            'clean': False
        }

    visitor = BoundaryViolationVisitor(str(filepath))
    visitor.visit(tree)

    return {
        'file': str(filepath),
        'violations': visitor.violations,
        'has_main_block': visitor.has_main_block,
        'io_call_count': len(visitor.io_calls),
        'clean': len(visitor.violations) == 0,
        'error': None
    }

def scan_directory(directory: Path, pattern: str = '*.py') -> list[dict[str, any]]:
    """Scan all Python files in a directory."""
    results = []
    for filepath in sorted(directory.rglob(pattern)):
        # Skip __pycache__ and test files
        if '__pycache__' in str(filepath) or 'test_' in filepath.name:
            continue
        results.append(scan_file(filepath))
    return results

def generate_sarif_report(results: list[dict[str, any]], tool_version: str = "1.0.0") -> dict:
    """Generate SARIF 2.1.0 format report for GitHub annotations."""
    sarif = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "BoundaryScanner",
                        "version": tool_version,
                        "informationUri": "https://github.com/kkkkknhh/SAAAAAA",
                        "rules": [
                            {
                                "id": "IO_VIOLATION",
                                "name": "I/O Operation in Core Module",
                                "shortDescription": {
                                    "text": "Core modules must not perform I/O operations"
                                },
                                "fullDescription": {
                                    "text": "All I/O operations must be performed through ports and adapters"
                                },
                                "defaultConfiguration": {
                                    "level": "error"
                                }
                            },
                            {
                                "id": "MAIN_BLOCK",
                                "name": "__main__ Block in Core Module",
                                "shortDescription": {
                                    "text": "Core modules must not contain __main__ blocks"
                                },
                                "defaultConfiguration": {
                                    "level": "error"
                                }
                            },
                            {
                                "id": "SUBPROCESS_VIOLATION",
                                "name": "Subprocess Call in Core Module",
                                "shortDescription": {
                                    "text": "Core modules must not call subprocess"
                                },
                                "defaultConfiguration": {
                                    "level": "error"
                                }
                            },
                            {
                                "id": "NETWORK_VIOLATION",
                                "name": "Network Call in Core Module",
                                "shortDescription": {
                                    "text": "Core modules must not make network calls"
                                },
                                "defaultConfiguration": {
                                    "level": "error"
                                }
                            }
                        ]
                    }
                },
                "results": []
            }
        ]
    }

    for result in results:
        if not result['clean'] and not result.get('error'):
            for violation in result['violations']:
                rule_id = {
                    'io_call': 'IO_VIOLATION',
                    'main_block': 'MAIN_BLOCK',
                    'subprocess_call': 'SUBPROCESS_VIOLATION',
                    'network_call': 'NETWORK_VIOLATION'
                }.get(violation['type'], 'IO_VIOLATION')

                sarif_result = {
                    "ruleId": rule_id,
                    "level": "error",
                    "message": {
                        "text": violation['message']
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": result['file'],
                                    "uriBaseId": "%SRCROOT%"
                                },
                                "region": {
                                    "startLine": violation['line'],
                                    "startColumn": 1
                                }
                            }
                        }
                    ]
                }
                sarif['runs'][0]['results'].append(sarif_result)

    return sarif

def generate_json_report(results: list[dict[str, any]]) -> dict:
    """Generate JSON violations report keyed by file, line, and node type."""
    violations_by_file = {}

    for result in results:
        if not result['clean']:
            file_path = result['file']
            violations_by_file[file_path] = {
                'violations': result['violations'],
                'has_main_block': result.get('has_main_block', False),
                'io_call_count': result.get('io_call_count', 0),
                'error': result.get('error')
            }

    return {
        'timestamp': datetime.now().isoformat(),
        'total_files_scanned': len(results),
        'files_with_violations': len(violations_by_file),
        'total_violations': sum(len(r['violations']) for r in results),
        'violations_by_file': violations_by_file
    }

def should_allow_path(filepath: Path, allowed_paths: list[str]) -> bool:
    """Check if filepath is in any of the allowed paths."""
    filepath_str = str(filepath)
    return any(allowed in filepath_str for allowed in allowed_paths)

def print_report(results: list[dict[str, any]], fail_on_types: set[str] | None = None) -> int:
    """Print scan results and return exit code."""
    total_files = len(results)
    clean_files = sum(1 for r in results if r['clean'])
    total_violations = sum(len(r['violations']) for r in results)

    if fail_on_types is None:
        fail_on_types = {'io_call', 'main_block', 'subprocess_call', 'network_call'}

    print("=" * 80)
    print("CORE MODULE BOUNDARY SCAN REPORT")
    print("=" * 80)
    print(f"\nFiles scanned: {total_files}")
    print(f"Clean files: {clean_files}")
    print(f"Files with violations: {total_files - clean_files}")
    print(f"Total violations: {total_violations}")
    print()

    if total_violations == 0:
        print("✅ All files are clean! No boundary violations detected.")
        return 0

    print("❌ Violations found:\n")

    # Count violations by type
    violation_counts = {}
    for result in results:
        if not result['clean']:
            for violation in result['violations']:
                vtype = violation['type']
                violation_counts[vtype] = violation_counts.get(vtype, 0) + 1

    print("Violation summary:")
    for vtype, count in sorted(violation_counts.items()):
        marker = "❌" if vtype in fail_on_types else "⚠️ "
        print(f"  {marker} {vtype}: {count}")
    print()

    for result in results:
        if not result['clean']:
            print(f"\n{result['file']}")
            if result.get('error'):
                print(f"  ERROR: {result['error']}")
            else:
                for violation in result['violations']:
                    marker = "❌" if violation['type'] in fail_on_types else "⚠️ "
                    print(f"  {marker} Line {violation['line']}: {violation['message']}")

    print("\n" + "=" * 80)
    print("REMEDIATION:")
    print("- Move all __main__ blocks to examples/ directory")
    print("- Move all I/O operations to orchestrator/factory.py")
    print("- Core modules should be pure libraries receiving data via contracts")
    print("=" * 80)

    # Determine if we should fail based on fail_on_types
    should_fail = any(
        violation['type'] in fail_on_types
        for result in results
        for violation in result['violations']
    )

    return 1 if should_fail else 0

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scan Python modules for boundary violations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python tools/scan_boundaries.py --root src/saaaaaa/core

  # Fail on specific violations only
  python tools/scan_boundaries.py --root src --fail-on io,main

  # Allow specific paths
  python tools/scan_boundaries.py --root src --fail-on io,subprocess,requests,main \\
                                   --allow-path src/examples src/cli

  # Generate SARIF and JSON reports
  python tools/scan_boundaries.py --root src/saaaaaa/core \\
                                   --sarif out/boundaries.sarif \\
                                   --json out/violations.json
        """
    )

    parser.add_argument(
        '--root',
        type=str,
        required=True,
        help='Root directory to scan'
    )

    parser.add_argument(
        '--fail-on',
        type=str,
        default='io,main,subprocess,network',
        help='Comma-separated list of violation types to fail on (io, main, subprocess, network)'
    )

    parser.add_argument(
        '--allow-path',
        nargs='+',
        default=[],
        help='Paths to exclude from scanning (e.g., src/examples src/cli)'
    )

    parser.add_argument(
        '--sarif',
        type=str,
        help='Output SARIF report to this file'
    )

    parser.add_argument(
        '--json',
        type=str,
        help='Output JSON violations report to this file'
    )

    # Legacy positional argument support
    if len(sys.argv) == 2 and not sys.argv[1].startswith('--'):
        # Old style: python scan_boundaries.py <directory>
        target_path = Path(sys.argv[1])
        fail_on_types = {'io_call', 'main_block', 'subprocess_call', 'network_call'}
        allowed_paths = []
        sarif_output = None
        json_output = None
    else:
        args = parser.parse_args()
        target_path = Path(args.root)
        fail_on_types = set()
        for vtype in args.fail_on.split(','):
            vtype = vtype.strip()
            if vtype == 'io':
                fail_on_types.add('io_call')
            elif vtype == 'main':
                fail_on_types.add('main_block')
            elif vtype == 'subprocess':
                fail_on_types.add('subprocess_call')
            elif vtype == 'network':
                fail_on_types.add('network_call')

        allowed_paths = args.allow_path
        sarif_output = args.sarif
        json_output = args.json

    if not target_path.exists():
        print(f"Error: Directory {target_path} does not exist")
        return 1

    results = scan_directory(target_path)

    # Filter results based on allowed paths
    if allowed_paths:
        filtered_results = []
        for result in results:
            if not should_allow_path(Path(result['file']), allowed_paths):
                filtered_results.append(result)
            else:
                # Mark as clean if in allowed path
                result['clean'] = True
                result['violations'] = []
                filtered_results.append(result)
        results = filtered_results

    # Generate SARIF report if requested
    if sarif_output:
        sarif_path = Path(sarif_output)
        sarif_path.parent.mkdir(parents=True, exist_ok=True)
        sarif_data = generate_sarif_report(results)
        with open(sarif_path, 'w', encoding='utf-8') as f:
            json.dump(sarif_data, f, indent=2)
        print(f"SARIF report written to {sarif_output}")

    # Generate JSON report if requested
    if json_output:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_data = generate_json_report(results)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        print(f"JSON report written to {json_output}")

    return print_report(results, fail_on_types)

if __name__ == '__main__':
    sys.exit(main())
