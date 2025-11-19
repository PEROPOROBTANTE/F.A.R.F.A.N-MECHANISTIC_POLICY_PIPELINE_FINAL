#!/usr/bin/env python3
"""
Comprehensive path audit script for SAAAAAA.

Scans the entire repository for path-related patterns and generates
a detailed audit report identifying risks and violations.
"""

from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from saaaaaa.config.paths import PROJECT_ROOT as REPO_ROOT
except Exception:  # pragma: no cover - fallback when package not installed
    REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PathFinding:
    """A single path-related finding."""
    file: Path
    line_number: int
    line_content: str
    category: str
    severity: str  # "critical", "high", "medium", "low"
    message: str
    fix_suggestion: str = ""


@dataclass
class PathAuditReport:
    """Complete path audit report."""
    findings: list[PathFinding] = field(default_factory=list)
    file_count: int = 0
    scanned_files: list[Path] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    
    def add_finding(self, finding: PathFinding) -> None:
        """Add a finding to the report."""
        self.findings.append(finding)
    
    def by_severity(self, severity: str) -> list[PathFinding]:
        """Get findings by severity level."""
        return [f for f in self.findings if f.severity == severity]
    
    def by_category(self, category: str) -> list[PathFinding]:
        """Get findings by category."""
        return [f for f in self.findings if f.category == category]
    
    def summary_stats(self) -> dict[str, int]:
        """Generate summary statistics."""
        return {
            "total_findings": len(self.findings),
            "critical": len(self.by_severity("critical")),
            "high": len(self.by_severity("high")),
            "medium": len(self.by_severity("medium")),
            "low": len(self.by_severity("low")),
            "files_scanned": self.file_count,
        }


class PathAuditor:
    """Main path auditor class."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.report = PathAuditReport()
        
        # Patterns to detect various path issues
        self.patterns = {
            "sys_path_append": re.compile(r'sys\.path\.(append|insert)'),
            "absolute_unix": re.compile(r'["\'](?:/home|/Users|/tmp|/var|/usr)/[^"\']*["\']'),
            "absolute_windows": re.compile(r'["\'][A-Z]:\\\\[^"\']*["\']'),
            "file_usage": re.compile(r'Path\s*\(\s*__file__\s*\)'),
            "file_parent": re.compile(r'__file__.*\.parent'),
            "open_builtin": re.compile(r'\bopen\s*\([^)]*\)'),
            "os_path_join": re.compile(r'os\.path\.join'),
            "os_path_exists": re.compile(r'os\.path\.exists'),
            "os_path_dirname": re.compile(r'os\.path\.dirname'),
            "os_path_abspath": re.compile(r'os\.path\.abspath'),
            "glob_usage": re.compile(r'\bglob\.(?:glob|iglob)'),
            "hardcoded_separator": re.compile(r'["\'][^"\']*[/\\]{2,}[^"\']*["\']'),
            "cwd_usage": re.compile(r'os\.getcwd\(\)|Path\.cwd\(\)'),
            "home_env": re.compile(r'os\.getenv\(["\']HOME["\']'),
            "temp_hardcode": re.compile(r'["\'](?:/tmp|C:\\\\temp)["\']'),
        }
        
    def should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "/.venv/", "/venv/", "/env/",
            "/__pycache__/",
            "/minipdm/",
            "/.git/",
            "/node_modules/",
            ".pyc",
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def scan_file(self, file_path: Path) -> None:
        """Scan a single Python file for path issues."""
        if self.should_skip(file_path):
            return
            
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            rel_path = file_path.relative_to(self.repo_root)
            
            for line_num, line in enumerate(lines, 1):
                self._check_line(rel_path, line_num, line)
                
            # AST-based checks
            try:
                tree = ast.parse(content, str(file_path))
                self._check_ast(rel_path, tree, lines)
            except SyntaxError:
                pass  # Skip files with syntax errors
                
        except Exception as e:
            # Don't fail the whole scan on one bad file
            pass
    
    def _check_line(self, rel_path: Path, line_num: int, line: str) -> None:
        """Check a single line for path issues."""
        
        # sys.path manipulation
        if self.patterns["sys_path_append"].search(line):
            # Allow in scripts/ and tests/, but warn elsewhere
            if not (str(rel_path).startswith("scripts/") or 
                    str(rel_path).startswith("tests/") or
                    str(rel_path).startswith("examples/")):
                self.report.add_finding(PathFinding(
                    file=rel_path,
                    line_number=line_num,
                    line_content=line.strip(),
                    category="sys_path_manipulation",
                    severity="critical",
                    message="sys.path manipulation detected outside scripts/tests/examples",
                    fix_suggestion="Use proper package imports instead of sys.path"
                ))
        
        # Absolute paths (Unix-style)
        if self.patterns["absolute_unix"].search(line):
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="absolute_path",
                severity="high",
                message="Absolute Unix path detected",
                fix_suggestion="Use proj_root() or data_dir() from saaaaaa.utils.paths"
            ))
        
        # Absolute paths (Windows-style)
        if self.patterns["absolute_windows"].search(line):
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="absolute_path",
                severity="high",
                message="Absolute Windows path detected",
                fix_suggestion="Use proj_root() or data_dir() from saaaaaa.utils.paths"
            ))
        
        # __file__ usage for paths
        if self.patterns["file_usage"].search(line) or self.patterns["file_parent"].search(line):
            # This is OK in scripts/ and specific places, but should be reviewed
            if not str(rel_path).startswith("scripts/"):
                self.report.add_finding(PathFinding(
                    file=rel_path,
                    line_number=line_num,
                    line_content=line.strip(),
                    category="file_usage",
                    severity="medium",
                    message="__file__ usage detected - may break in packaged distributions",
                    fix_suggestion="Use resources() for packaged data or proj_root() for workspace-relative paths"
                ))
        
        # os.path usage
        if (self.patterns["os_path_join"].search(line) or 
            self.patterns["os_path_dirname"].search(line) or
            self.patterns["os_path_abspath"].search(line)):
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="os_path_usage",
                severity="medium",
                message="os.path usage detected",
                fix_suggestion="Use pathlib.Path instead of os.path"
            ))
        
        # hardcoded path separators
        if self.patterns["hardcoded_separator"].search(line):
            stripped = line.strip().lower()
            if "http://" in stripped or "https://" in stripped or ":// " in stripped:
                return
            if stripped.startswith("#"):
                return
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="hardcoded_separator",
                severity="medium",
                message="Potential hardcoded path separator detected",
                fix_suggestion="Use Path.joinpath() or / operator"
            ))
        
        # os.getcwd / current path usage
        if self.patterns["cwd_usage"].search(line):
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="cwd_usage",
                severity="medium",
                message="Current working directory usage - fragile in different execution contexts",
                fix_suggestion="Use proj_root() or explicit paths from saaaaaa.utils.paths"
            ))
        
        # HOME environment variable
        if self.patterns["home_env"].search(line):
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="home_env",
                severity="low",
                message="HOME environment variable usage",
                fix_suggestion="Use Path.home() from pathlib"
            ))
        
        # Hardcoded temp directories
        if self.patterns["temp_hardcode"].search(line):
            self.report.add_finding(PathFinding(
                file=rel_path,
                line_number=line_num,
                line_content=line.strip(),
                category="temp_hardcode",
                severity="high",
                message="Hardcoded temp directory path",
                fix_suggestion="Use tmp_dir() from saaaaaa.utils.paths or tempfile module"
            ))
    
    def _check_ast(self, rel_path: Path, tree: ast.AST, lines: list[str]) -> None:
        """Perform AST-based checks."""
        # Check for open() calls without proper context managers
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    # Check if it's inside a 'with' statement
                    # This is a simplified check - full check would need parent tracking
                    if hasattr(node, "lineno"):
                        line_content = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        if "with" not in line_content:
                            # This is just informational - not all open() needs 'with'
                            self.report.add_finding(PathFinding(
                                file=rel_path,
                                line_number=node.lineno,
                                line_content=line_content.strip(),
                                category="open_without_context",
                                severity="low",
                                message="open() call - verify proper resource cleanup",
                                fix_suggestion="Consider using 'with open(...)' for automatic cleanup"
                            ))
    
    def scan_repository(self) -> None:
        """Scan the entire repository."""
        print(f"Scanning repository: {self.repo_root}")
        
        # Find all Python files
        python_files = list(self.repo_root.rglob("*.py"))
        python_files = [f for f in python_files if not self.should_skip(f)]
        
        self.report.file_count = len(python_files)
        self.report.scanned_files = python_files
        
        print(f"Found {len(python_files)} Python files to scan")
        
        for i, py_file in enumerate(python_files, 1):
            if i % 50 == 0:
                print(f"  Scanned {i}/{len(python_files)} files...")
            self.scan_file(py_file)
        
        print(f"Scan complete. Found {len(self.report.findings)} issues.")
    
    def generate_markdown_report(self, output_path: Path) -> None:
        """Generate a detailed Markdown report."""
        stats = self.report.summary_stats()
        
        lines = [
            "# Path Audit Report",
            "",
            "**Generated by:** `scripts/audit_paths.py`",
            f"**Repository:** {self.repo_root}",
            "",
            "## Executive Summary",
            "",
            f"- **Files Scanned:** {stats['files_scanned']}",
            f"- **Total Findings:** {stats['total_findings']}",
            f"- **Critical:** {stats['critical']}",
            f"- **High:** {stats['high']}",
            f"- **Medium:** {stats['medium']}",
            f"- **Low:** {stats['low']}",
            "",
            "## Findings by Severity",
            "",
        ]
        
        # Group by severity
        for severity in ["critical", "high", "medium", "low"]:
            findings = self.report.by_severity(severity)
            if findings:
                lines.append(f"### {severity.upper()} ({len(findings)})")
                lines.append("")
                
                # Group by category
                by_category = defaultdict(list)
                for finding in findings:
                    by_category[finding.category].append(finding)
                
                for category, cat_findings in sorted(by_category.items()):
                    lines.append(f"#### {category} ({len(cat_findings)} occurrences)")
                    lines.append("")
                    
                    # Show first 10 examples
                    for finding in cat_findings[:10]:
                        lines.append(f"- **{finding.file}:{finding.line_number}**")
                        lines.append(f"  - {finding.message}")
                        lines.append(f"  - Code: `{finding.line_content[:100]}`")
                        if finding.fix_suggestion:
                            lines.append(f"  - Fix: {finding.fix_suggestion}")
                        lines.append("")
                    
                    if len(cat_findings) > 10:
                        lines.append(f"  ... and {len(cat_findings) - 10} more occurrences")
                        lines.append("")
        
        # Category breakdown
        lines.extend([
            "## Findings by Category",
            "",
        ])
        
        by_category = defaultdict(list)
        for finding in self.report.findings:
            by_category[finding.category].append(finding)
        
        for category, findings in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
            lines.append(f"### {category}: {len(findings)} occurrences")
            lines.append("")
        
        # Recommendations
        lines.extend([
            "",
            "## Recommendations",
            "",
            "1. **Eliminate sys.path manipulation**: Use proper package imports",
            "2. **Remove absolute paths**: Use `proj_root()`, `data_dir()`, etc. from `saaaaaa.utils.paths`",
            "3. **Replace os.path with pathlib.Path**: More portable and Pythonic",
            "4. **Use resources() for packaged data**: Ensures compatibility with wheels/sdist",
            "5. **Validate all path operations**: Use `validate_read_path()` and `validate_write_path()`",
            "6. **Add path traversal protection**: Use `safe_join()` for user-provided paths",
            "7. **Use temp_dir() instead of hardcoded /tmp**: Ensures controlled cleanup",
            "",
            "## Next Steps",
            "",
            "1. Create tests under `tests/paths/` to enforce these rules",
            "2. Fix critical and high severity issues first",
            "3. Add pre-commit hooks to prevent regressions",
            "4. Update CI to test on Windows, macOS, and Linux",
            "5. Document path handling guidelines in README",
            "",
        ])
        
        # Write report
        output_path.write_text("\n".join(lines), encoding='utf-8')
        print(f"\nReport written to: {output_path}")


def main() -> int:
    """Main entry point."""
    auditor = PathAuditor(REPO_ROOT)
    auditor.scan_repository()
    
    # Generate report
    output_path = REPO_ROOT / "PATHS_AUDIT.md"
    auditor.generate_markdown_report(output_path)
    
    # Print summary
    stats = auditor.report.summary_stats()
    print("\n" + "=" * 60)
    print("PATH AUDIT SUMMARY")
    print("=" * 60)
    print(f"Files scanned:     {stats['files_scanned']}")
    print(f"Total findings:    {stats['total_findings']}")
    print(f"  Critical:        {stats['critical']}")
    print(f"  High:            {stats['high']}")
    print(f"  Medium:          {stats['medium']}")
    print(f"  Low:             {stats['low']}")
    print("=" * 60)
    
    # Return non-zero if critical issues found
    return 1 if stats['critical'] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
