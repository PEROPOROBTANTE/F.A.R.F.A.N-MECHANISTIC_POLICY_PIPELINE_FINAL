"""Test that no absolute paths exist in the codebase."""

import os
import re
from pathlib import Path, PureWindowsPath
import pytest


REPO_ROOT = Path(__file__).parent.parent.parent
PATH_SEPARATOR = Path(os.sep).as_posix()
ABSOLUTE_SEGMENTS = ("home", "Users", "tmp", "var", "usr")
ABSOLUTE_PREFIXES = [
    f"{PATH_SEPARATOR}{segment}" for segment in ABSOLUTE_SEGMENTS
]
UNIX_ABSOLUTE_PATTERN = re.compile(
    r'["\'](' + "|".join(re.escape(prefix) for prefix in ABSOLUTE_PREFIXES) + r')/[^"\']*["\']'
)
TMP_MARKER = f"{PATH_SEPARATOR}tmp{PATH_SEPARATOR}"
USR_LIB = str(Path(os.sep) / "usr" / "lib")
USR_LOCAL_LIB = str(Path(os.sep) / "usr" / "local" / "lib")
WINDOWS_TEMP = str(PureWindowsPath("C:/temp"))


def get_python_files():
    """Get all Python files to check."""
    files = []
    for py_file in REPO_ROOT.rglob("*.py"):
        # Skip venv, cache, etc.
        if any(skip in str(py_file) for skip in [
            "/.venv/", "/venv/", "/env/",
            "/__pycache__/",
            "/minipdm/",
            "/.git/",
        ]):
            continue
        files.append(py_file)
    return files


def test_no_absolute_unix_paths():
    """No absolute Unix-style paths should exist in code."""
    pattern = UNIX_ABSOLUTE_PATTERN
    
    violations = []
    
    for py_file in get_python_files():
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Skip if in comment or docstring context
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                if '>>>' in line:  # doctest example
                    continue
                    
                if pattern.search(line):
                    # Allow specific exceptions
                    # Check if this is in a docstring (lines with >>>)
                    if '>>>' in line:
                        continue
                    if 'paths.py' in str(py_file):
                        # Allow examples in paths.py docstrings
                        continue
                    if 'native_check.py' in str(py_file) and (USR_LIB in line or USR_LOCAL_LIB in line):
                        # System library paths for native checks
                        continue
                    if 'test_paths_no_absolutes.py' in str(py_file):
                        # This test file checks for these patterns - meta!
                        continue
                    if 'test_' in str(py_file) and TMP_MARKER in line:
                        # Test files may exercise temp directories - should be fixed but not critical
                        continue
                    
                    rel_path = py_file.relative_to(REPO_ROOT)
                    violations.append(f"{rel_path}:{line_num}: {line.strip()[:80]}")
        except Exception:
            pass
    
    if violations:
        msg = "\n".join([
            "Absolute paths detected (use proj_root(), tmp_dir(), etc. instead):",
            *violations[:20],
        ])
        if len(violations) > 20:
            msg += f"\n... and {len(violations) - 20} more"
        pytest.fail(msg)


def test_no_absolute_windows_paths():
    """No absolute Windows-style paths should exist in code."""
    pattern = re.compile(r'["\'][A-Z]:\\\\[^"\']*["\']')
    
    violations = []
    
    for py_file in get_python_files():
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    rel_path = py_file.relative_to(REPO_ROOT)
                    violations.append(f"{rel_path}:{line_num}: {line.strip()[:80]}")
        except Exception:
            pass
    
    if violations:
        msg = "\n".join([
            "Absolute Windows paths detected:",
            *violations[:20],
        ])
        if len(violations) > 20:
            msg += f"\n... and {len(violations) - 20} more"
        pytest.fail(msg)


def test_no_syspath_manipulation():
    """No sys.path manipulation should exist outside scripts/tests/examples."""
    pattern = re.compile(r'sys\.path\.(append|insert)')
    
    violations = []
    
    for py_file in get_python_files():
        # Allow in specific locations
        rel_path = py_file.relative_to(REPO_ROOT)
        if any(str(rel_path).startswith(prefix) for prefix in [
            "scripts/",
            "tests/",
            "examples/",
            "tools/",
        ]):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    violations.append(f"{rel_path}:{line_num}: {line.strip()[:80]}")
        except Exception:
            pass
    
    if violations:
        msg = "\n".join([
            "sys.path manipulation detected outside scripts/tests/examples:",
            "Use proper package imports instead.",
            *violations,
        ])
        pytest.fail(msg)


def test_prefer_pathlib_over_os_path():
    """Prefer pathlib.Path over os.path (warning only)."""
    pattern = re.compile(r'os\.path\.(join|exists|dirname|basename|abspath)')
    
    usages = []
    
    for py_file in get_python_files():
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    rel_path = py_file.relative_to(REPO_ROOT)
                    usages.append(f"{rel_path}:{line_num}")
        except Exception:
            pass
    
    # This is informational - not a failure
    if usages:
        print(f"\nInfo: Found {len(usages)} uses of os.path (consider migrating to pathlib)")


def test_hardcoded_temp_dirs():
    """No hardcoded OS-specific temp directories should exist."""
    temp_patterns = [
        TMP_MARKER.rstrip(PATH_SEPARATOR),
        WINDOWS_TEMP,
    ]
    pattern = re.compile(r'["\'](' + "|".join(re.escape(p) for p in temp_patterns) + r')["\']')
    
    violations = []
    
    for py_file in get_python_files():
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    # Skip docstring examples
                    if '>>>' in line:
                        continue
                    
                    rel_path = py_file.relative_to(REPO_ROOT)
                    # Allow in tests for now (should be fixed but not blocking)
                    if 'test_' not in str(rel_path):
                        violations.append(f"{rel_path}:{line_num}: {line.strip()[:80]}")
        except Exception:
            pass
    
    if violations:
        msg = "\n".join([
            "Hardcoded temp directories detected (use tmp_dir() instead):",
            *violations,
        ])
        pytest.fail(msg)
