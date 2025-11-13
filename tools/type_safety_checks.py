#!/usr/bin/env python3
"""
Type safety validation scripts for CI/CD workflows.
This script consolidates inline Python scripts from type-safety.yml.
"""
import ast
import re
import sys

def check_kwargs_in_public_apis(files: list[str]) -> int:
    """Check for **kwargs in public APIs."""
    print("=== Checking for **kwargs in public APIs ===")

    issues = []
    for file in files:
        try:
            with open(file) as f:
                content = f.read()
                # Look for public functions with **kwargs
                matches = re.findall(
                    r'^\s*def\s+([a-z_][a-z0-9_]*)\s*\([^)]*\*\*kwargs',
                    content,
                    re.MULTILINE
                )
                if matches:
                    issues.append(f'{file}: Found **kwargs in public functions: {matches}')
        except FileNotFoundError:
            pass

    if issues:
        print('WARNING: Found **kwargs in public APIs (should be deprecated):')
        for issue in issues:
            print(f'  - {issue}')
        print('Note: **kwargs is discouraged in public APIs per design guidelines')
        return 1
    else:
        print('✓ No **kwargs found in core public APIs')
        return 0

def check_contract_test_coverage() -> int:
    """Check contract test coverage."""
    print("=== Verifying contract test coverage ===")

    # Check that contract tests exist
    try:
        with open('tests/test_contracts.py') as f:
            content = f.read()
            contract_count = content.count('def test_')
            print(f'✓ Found {contract_count} contract tests')
            if contract_count < 5:
                print('WARNING: Fewer than 5 contract tests found')
    except FileNotFoundError:
        print('ERROR: Contract test file not found')
        return 1

    # Check for public interfaces without tests
    print('=== Checking public interface coverage ===')
    files_to_check = [
        'contracts.py',
        'orchestrator.py',
        'document_ingestion.py',
        'embedding_policy.py',
        'semantic_chunking_policy.py'
    ]

    missing_tests = []
    for file in files_to_check:
        try:
            with open(file) as f:
                tree = ast.parse(f.read())

            public_functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_') or isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                    public_functions.append(node.name)

            # Check if tests exist for public functions
            with open('tests/test_contracts.py') as f:
                test_content = f.read()

            for func in public_functions:
                test_name = f'def test_{func.lower()}'
                if test_name not in test_content:
                    missing_tests.append(f'{file}:{func}')

        except Exception as e:
            print(f'Warning: Could not analyze {file}: {e}')

    if missing_tests:
        print('WARNING: Missing contract tests for public interfaces:')
        for item in missing_tests:
            print(f'  - {item}')
        print('Consider adding contract tests for these interfaces')
    else:
        print('✓ All public interfaces appear to have contract test coverage')

    return 0

def check_typing_any_usage(files: list[str]) -> int:
    """Check for typing.Any usage."""
    print("=== Checking for typing.Any usage (should be minimal) ===")

    for file in files:
        try:
            with open(file) as f:
                lines = f.readlines()
                any_lines = [
                    (i+1, line.strip())
                    for i, line in enumerate(lines)
                    if ': Any' in line or '-> Any' in line
                ]
                if any_lines:
                    print(f'\n{file} - Found Any usage:')
                    for lineno, line in any_lines[:5]:  # Show first 5
                        print(f'  Line {lineno}: {line[:80]}')
                else:
                    print(f'✓ {file} - No Any usage found')
        except FileNotFoundError:
            pass

    return 0

def check_frozen_dataclasses(files: list[str]) -> int:
    """Check for frozen dataclasses."""
    print("=== Checking for frozen dataclasses ===")

    for file in files:
        try:
            with open(file) as f:
                content = f.read()
                dataclasses = re.findall(r'@dataclass\([^)]*\)', content)
                frozen_count = sum(1 for dc in dataclasses if 'frozen=True' in dc)
                total_count = len(dataclasses)
                print(f'{file}: {frozen_count}/{total_count} dataclasses are frozen')
        except FileNotFoundError:
            pass

    return 0

def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python tools/type_safety_checks.py <command>")
        print("Commands: kwargs, coverage, any, frozen")
        sys.exit(1)

    command = sys.argv[1]

    if command == "kwargs":
        files = [
            'contracts.py',
            'orchestrator.py',
            'document_ingestion.py',
            'embedding_policy.py',
        ]
        sys.exit(check_kwargs_in_public_apis(files))

    elif command == "coverage":
        sys.exit(check_contract_test_coverage())

    elif command == "any":
        files = [
            'contracts.py',
            'orchestrator.py',
            'document_ingestion.py',
            'embedding_policy.py',
        ]
        sys.exit(check_typing_any_usage(files))

    elif command == "frozen":
        files = [
            'contracts.py',
            'document_ingestion.py',
        ]
        sys.exit(check_frozen_dataclasses(files))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
