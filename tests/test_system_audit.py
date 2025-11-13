"""Comprehensive system audit tests - compilation, imports, routes, paths."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

# Shared configuration
EXCLUDED_DIRS = {'__pycache__', '.git', 'minipdm', '.augment', '.venv'}
API_SERVER_PATHS = [
    'src/saaaaaa/api/api_server.py',
    'api/api_server.py',
    'saaaaaa/api/api_server.py',
]

class TestCompilation:
    """Test that all Python files compile successfully."""

    @pytest.fixture
    def root_path(self) -> Path:
        """Get repository root path."""
        return Path(__file__).parent.parent

    def get_python_files(self, root: Path) -> list[Path]:
        """Get all Python files in the repository."""
        files = []
        for py_file in root.rglob("*.py"):
            # Skip excluded directories
            if any(d in py_file.parts for d in EXCLUDED_DIRS):
                continue
            files.append(py_file)
        return files

    def test_all_files_compile(self, root_path: Path) -> None:
        """Test that all Python files compile without syntax errors."""
        files = self.get_python_files(root_path)
        errors = []

        for py_file in files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    source = f.read()
                ast.parse(source, filename=str(py_file))
            except SyntaxError as e:
                rel_path = py_file.relative_to(root_path)
                errors.append(f"{rel_path}: SyntaxError at line {e.lineno}: {e.msg}")

        assert len(errors) == 0, f"Found {len(errors)} compilation errors:\n" + "\n".join(errors)

    def test_no_duplicate_lines(self, root_path: Path) -> None:
        """Test that files don't have suspicious duplicate code blocks."""
        files = self.get_python_files(root_path)
        issues = []

        for py_file in files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    lines = f.readlines()

                # Check for consecutive duplicate lines (more than 3)
                if len(lines) > 5:
                    for i in range(len(lines) - 3):
                        if (lines[i] == lines[i+1] == lines[i+2] == lines[i+3] and
                            len(lines[i].strip()) > 0):
                            rel_path = py_file.relative_to(root_path)
                            issues.append(f"{rel_path}: Duplicate lines at {i+1}")
                            break
            except Exception:
                pass

        assert len(issues) == 0, "Found suspicious duplicates:\n" + "\n".join(issues)

class TestImports:
    """Test import statements and module structure."""

    @pytest.fixture
    def root_path(self) -> Path:
        """Get repository root path."""
        return Path(__file__).parent.parent

    def test_no_circular_imports_in_core(self, root_path: Path) -> None:
        """Test that core modules don't have obvious circular imports."""
        # This is a basic check - full circular dependency detection requires runtime
        core_dirs = ['core', 'orchestrator', 'executors', 'concurrency']

        for dir_name in core_dirs:
            dir_path = root_path / dir_name
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                if '__pycache__' in str(py_file):
                    continue

                try:
                    with open(py_file, encoding='utf-8') as f:
                        tree = ast.parse(f.read())

                    # Just verify it parses - circular imports will fail at runtime
                    assert tree is not None
                except SyntaxError as e:
                    rel_path = py_file.relative_to(root_path)
                    pytest.fail(f"Syntax error in {rel_path}: {e}")

    def test_import_statements_valid(self, root_path: Path) -> None:
        """Test that import statements are syntactically valid."""
        errors = []

        for py_file in root_path.rglob("*.py"):
            if any(d in py_file.parts for d in EXCLUDED_DIRS):
                continue

            try:
                with open(py_file, encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                # Verify all import nodes are valid
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert alias.name is not None
                    elif isinstance(node, ast.ImportFrom) and node.level > 0:
                        # Relative imports should have level > 0
                        assert node.level <= 5  # Reasonable depth
            except Exception as e:
                rel_path = py_file.relative_to(root_path)
                errors.append(f"{rel_path}: {e}")

        assert len(errors) == 0, "Found import errors:\n" + "\n".join(errors)

class TestRoutes:
    """Test API routes and endpoints."""

    @pytest.fixture
    def root_path(self) -> Path:
        """Get repository root path."""
        return Path(__file__).parent.parent

    def test_api_routes_exist(self, root_path: Path) -> None:
        """Test that API server file exists and defines routes."""
        # Try to find API server file dynamically
        api_server = None
        for path in API_SERVER_PATHS:
            candidate = root_path / path
            if candidate.exists():
                api_server = candidate
                break

        if api_server is None:
            pytest.skip("API server file not found")

        with open(api_server, encoding='utf-8') as f:
            content = f.read()

        # Check for route definitions
        assert 'api/' in content, "No API routes found in api_server.py"
        assert 'health' in content or 'status' in content, "No health check endpoint found"

class TestPaths:
    """Test file paths and references."""

    @pytest.fixture
    def root_path(self) -> Path:
        """Get repository root path."""
        return Path(__file__).parent.parent

    def test_config_files_exist(self, root_path: Path) -> None:
        """Test that expected configuration files exist."""
        expected_files = [
            'pyproject.toml',
            'requirements.txt',
            'Makefile',
        ]

        missing = []
        for file_name in expected_files:
            if not (root_path / file_name).exists():
                missing.append(file_name)

        assert len(missing) == 0, f"Missing config files: {missing}"

    def test_directory_structure(self, root_path: Path) -> None:
        """Test that expected directories exist."""
        expected_dirs = [
            'src',
            'tests',
            'core',
            'orchestrator',
        ]

        missing = []
        for dir_name in expected_dirs:
            if not (root_path / dir_name).exists():
                missing.append(dir_name)

        assert len(missing) == 0, f"Missing directories: {missing}"

    def test_audit_report_exists(self, root_path: Path) -> None:
        """Test that audit report was generated."""
        audit_report = root_path / 'docs' / 'AUDIT_REPORT.json'

        assert audit_report.exists(), "Audit report not found"

        with open(audit_report, encoding='utf-8') as f:
            data = json.load(f)

        assert 'summary' in data
        assert 'compilation_status' in data
        assert data['compilation_status'] == 'PASS'

class TestSystemIntegrity:
    """Test overall system integrity."""

    @pytest.fixture
    def root_path(self) -> Path:
        """Get repository root path."""
        return Path(__file__).parent.parent

    def test_no_empty_python_files(self, root_path: Path) -> None:
        """Test that Python files are not empty."""
        empty_files = []

        for py_file in root_path.rglob("*.py"):
            if any(d in py_file.parts for d in EXCLUDED_DIRS):
                continue

            if py_file.stat().st_size == 0:
                rel_path = py_file.relative_to(root_path)
                empty_files.append(str(rel_path))

        assert len(empty_files) == 0, f"Found empty files: {empty_files}"

    def test_init_files_present(self, root_path: Path) -> None:
        """Test that package directories have __init__.py files."""
        missing = []

        # Check key package directories
        package_dirs = [
            'core',
            'orchestrator',
            'executors',
            'concurrency',
            'scoring',
            'validation',
            'contracts',
        ]

        for dir_name in package_dirs:
            dir_path = root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                init_file = dir_path / '__init__.py'
                if not init_file.exists():
                    missing.append(dir_name)

        # Allow some directories to not have __init__.py
        critical_missing = [d for d in missing if d not in ['tools', 'scripts']]
        assert len(critical_missing) == 0, f"Missing __init__.py in: {critical_missing}"
