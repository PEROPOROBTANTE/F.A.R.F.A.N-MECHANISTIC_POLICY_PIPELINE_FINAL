#!/usr/bin/env python3
"""
Questionnaire Architecture Enforcement Audit Tool

This tool performs comprehensive static analysis to enforce the questionnaire access architecture:
1. QuestionnaireResourceProvider is the ONLY source for pattern/validation logic
2. factory.py is the ONLY module that may read questionnaire_monolith.json
3. core.py receives QRP via dependency injection
4. arg_router_extended.py and evidence_registry.py must NOT import QRP or read questionnaire files
"""

import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Repository root
REPO_ROOT = Path(__file__).parent

# Allowed modules for questionnaire access
ALLOWED_QRP_IMPORTERS = {
    "questionnaire_resource_provider.py",  # Self
    "factory.py",  # I/O boundary
    "core.py",  # Via DI
    "__init__.py",  # Package initialization
    "core_module_factory.py",  # Factory for module DI
    "bootstrap.py",  # Wiring initialization
}

# Test files are allowed to import anything they test
def is_test_file(filepath: str) -> bool:
    """Check if file is a test file"""
    return filepath.startswith('tests/') or '/tests/' in filepath or '/test/' in filepath or Path(filepath).name.startswith('test_')

ALLOWED_MONOLITH_READERS = {
    "factory.py",  # Only factory may read
}

# Violation types
@dataclass
class Violation:
    """A detected architectural violation"""
    file_path: str
    line_number: int
    violation_type: str
    code_snippet: str
    explanation: str

@dataclass
class AnalysisReport:
    """Complete analysis report"""
    violations: list[Violation] = field(default_factory=list)
    suspicious: list[dict] = field(default_factory=list)
    compliant: list[dict] = field(default_factory=list)
    files_scanned: int = 0
    
    def is_compliant(self) -> bool:
        """Check if repository is fully compliant"""
        return len(self.violations) == 0


class QuestionnaireArchitectureAuditor(ast.NodeVisitor):
    """AST visitor to detect questionnaire access violations"""
    
    def __init__(self, file_path: Path, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.violations: list[Violation] = []
        self.suspicious: list[dict] = []
        self.file_name = file_path.name
        self.relative_path = str(file_path.relative_to(REPO_ROOT))
        
        # Track imports
        self.imports_qrp = False
        self.has_from_file_call = False
        self.has_monolith_open = False
        
    def visit_Import(self, node: ast.Import) -> None:
        """Check for 'import questionnaire_resource_provider'"""
        for alias in node.names:
            if 'questionnaire_resource_provider' in alias.name:
                # Allow test files to import what they're testing
                if not is_test_file(self.relative_path) and self.file_name not in ALLOWED_QRP_IMPORTERS:
                    self.violations.append(Violation(
                        file_path=self.relative_path,
                        line_number=node.lineno,
                        violation_type="ILLEGAL_IMPORT",
                        code_snippet=self._get_line(node.lineno),
                        explanation=f"Module {self.file_name} imports questionnaire_resource_provider, "
                                    f"but only {ALLOWED_QRP_IMPORTERS} (and test files) are allowed to import it."
                    ))
                self.imports_qrp = True
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for 'from questionnaire_resource_provider import ...'"""
        if node.module and 'questionnaire_resource_provider' in node.module:
            # Allow test files to import what they're testing
            if not is_test_file(self.relative_path) and self.file_name not in ALLOWED_QRP_IMPORTERS:
                imported_names = ', '.join(alias.name for alias in node.names)
                self.violations.append(Violation(
                    file_path=self.relative_path,
                    line_number=node.lineno,
                    violation_type="ILLEGAL_IMPORT",
                    code_snippet=self._get_line(node.lineno),
                    explanation=f"Module {self.file_name} imports {imported_names} from "
                                f"questionnaire_resource_provider, but only {ALLOWED_QRP_IMPORTERS} "
                                f"(and test files) are allowed to import from it."
                ))
            self.imports_qrp = True
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check for calls to QuestionnaireResourceProvider.from_file and file I/O"""
        # Check for QuestionnaireResourceProvider.from_file()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'from_file':
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'QuestionnaireResourceProvider':
                        # Allow test files and factory to use from_file
                        if not is_test_file(self.relative_path) and self.file_name not in ALLOWED_MONOLITH_READERS:
                            self.violations.append(Violation(
                                file_path=self.relative_path,
                                line_number=node.lineno,
                                violation_type="LEGACY_IO_PATH",
                                code_snippet=self._get_line(node.lineno),
                                explanation=f"Module {self.file_name} calls QuestionnaireResourceProvider.from_file(), "
                                            f"which is a legacy I/O path. Only factory.py (and tests) should use from_file(). "
                                            f"Core modules should receive QRP via dependency injection."
                            ))
                        self.has_from_file_call = True
        
        # Check for open() calls with questionnaire_monolith
        if isinstance(node.func, ast.Name) and node.func.id == 'open':
            if node.args:
                arg = node.args[0]
                line_text = self._get_line(node.lineno)
                if 'questionnaire_monolith' in line_text.lower():
                    if self.file_name not in ALLOWED_MONOLITH_READERS:
                        self.violations.append(Violation(
                            file_path=self.relative_path,
                            line_number=node.lineno,
                            violation_type="ILLEGAL_DATA_ACCESS",
                            code_snippet=line_text,
                            explanation=f"Module {self.file_name} directly opens questionnaire_monolith file. "
                                        f"Only factory.py is allowed to perform questionnaire I/O."
                        ))
                    self.has_monolith_open = True
        
        # Check for json.load with questionnaire_monolith context
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'load' and isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'json':
                    line_text = self._get_line(node.lineno)
                    # Check context (look at surrounding lines)
                    context = self._get_context(node.lineno, 3)
                    if 'questionnaire_monolith' in context.lower():
                        if self.file_name not in ALLOWED_MONOLITH_READERS:
                            self.violations.append(Violation(
                                file_path=self.relative_path,
                                line_number=node.lineno,
                                violation_type="ILLEGAL_DATA_ACCESS",
                                code_snippet=line_text,
                                explanation=f"Module {self.file_name} loads JSON in context of questionnaire_monolith. "
                                            f"Only factory.py is allowed to perform questionnaire I/O."
                            ))
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check for functions that look like pattern extraction or monolith loaders"""
        func_name = node.name.lower()
        
        # Check for functions that load from monolith
        if 'monolith' in func_name and ('load' in func_name or 'from' in func_name or 'read' in func_name):
            if self.file_name not in ALLOWED_MONOLITH_READERS:
                # Check if function actually reads files
                body_text = ast.get_source_segment(self.source_code, node) or ''
                if 'open(' in body_text or 'json.load' in body_text or 'read(' in body_text:
                    self.violations.append(Violation(
                        file_path=self.relative_path,
                        line_number=node.lineno,
                        violation_type="ILLEGAL_DATA_ACCESS",
                        code_snippet=f"def {node.name}(...)",
                        explanation=f"Function {node.name} loads questionnaire monolith data. "
                                    f"Only factory.py is allowed to perform questionnaire I/O. "
                                    f"Use factory.load_questionnaire_monolith() instead."
                    ))
        
        # Pattern extraction indicators
        pattern_keywords = ['extract_pattern', 'derive_pattern', 'build_pattern', 'compile_pattern',
                            'get_pattern', 'pattern_from', 'validation_from', 'extract_validation']
        
        if any(keyword in func_name for keyword in pattern_keywords):
            if self.file_name not in ['questionnaire_resource_provider.py', 'factory.py']:
                # Check if function body contains questionnaire-related logic
                body_text = ast.get_source_segment(self.source_code, node) or ''
                if any(word in body_text.lower() for word in ['questionnaire', 'monolith', 'pattern', 'validation']):
                    self.suspicious.append({
                        'file': self.relative_path,
                        'line': node.lineno,
                        'function': node.name,
                        'reason': f"Function name suggests pattern extraction logic. "
                                  f"Pattern logic should only exist in QuestionnaireResourceProvider."
                    })
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check for classes that look like pattern providers"""
        class_name = node.name.lower()
        
        if 'pattern' in class_name or 'questionnaire' in class_name or 'validation' in class_name:
            if self.file_name not in ['questionnaire_resource_provider.py', 'factory.py', 'contracts.py']:
                self.suspicious.append({
                    'file': self.relative_path,
                    'line': node.lineno,
                    'class': node.name,
                    'reason': f"Class name suggests questionnaire/pattern logic. "
                              f"Such logic should only exist in QuestionnaireResourceProvider."
                })
        
        self.generic_visit(node)
    
    def _get_line(self, line_num: int) -> str:
        """Get source line at given line number"""
        if 1 <= line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1].strip()
        return ""
    
    def _get_context(self, line_num: int, lines_before: int = 2, lines_after: int = 2) -> str:
        """Get context around a line"""
        start = max(1, line_num - lines_before)
        end = min(len(self.source_lines), line_num + lines_after)
        return '\n'.join(self.source_lines[start-1:end])


def scan_file(file_path: Path) -> tuple[list[Violation], list[dict]]:
    """Scan a single Python file for violations"""
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(file_path))
        
        auditor = QuestionnaireArchitectureAuditor(file_path, source)
        auditor.visit(tree)
        
        return auditor.violations, auditor.suspicious
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"Error scanning {file_path}: {e}", file=sys.stderr)
        return [], []


def scan_repository() -> AnalysisReport:
    """Scan entire repository for violations"""
    report = AnalysisReport()
    
    # Find all Python files
    python_files = list(REPO_ROOT.rglob('*.py'))
    
    # Exclude test files, migrations, and virtual environments
    python_files = [
        f for f in python_files
        if not any(part.startswith('.') or part in ['venv', 'env', '__pycache__', 'migrations']
                   for part in f.parts)
    ]
    
    print(f"Scanning {len(python_files)} Python files...")
    
    for file_path in python_files:
        violations, suspicious = scan_file(file_path)
        report.violations.extend(violations)
        report.suspicious.extend(suspicious)
        report.files_scanned += 1
        
        # Track compliant files that correctly use the architecture
        if not violations and not suspicious:
            # Check if file uses QRP correctly (via factory)
            try:
                source = file_path.read_text(encoding='utf-8')
                if 'QuestionnaireResourceProvider' in source or 'questionnaire_resource_provider' in source:
                    relative_path = str(file_path.relative_to(REPO_ROOT))
                    if file_path.name in ALLOWED_QRP_IMPORTERS:
                        report.compliant.append({
                            'file': relative_path,
                            'reason': 'Correctly imports/uses QuestionnaireResourceProvider per architecture'
                        })
            except:
                pass
    
    return report


def generate_report(report: AnalysisReport) -> str:
    """Generate comprehensive compliance report"""
    lines = []
    
    # Compliance Summary
    lines.append("=" * 80)
    lines.append("QUESTIONNAIRE ARCHITECTURE COMPLIANCE REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("COMPLIANCE SUMMARY")
    lines.append("-" * 80)
    
    if report.is_compliant():
        lines.append("✓ COMPLIANT: The repository fully adheres to the Questionnaire Access Architecture.")
        lines.append(f"  Scanned {report.files_scanned} files with NO violations detected.")
    else:
        lines.append(f"✗ NON-COMPLIANT: {len(report.violations)} architectural violations detected.")
        lines.append(f"  The repository violates the Questionnaire Access Architecture specification.")
        lines.append(f"  Scanned {report.files_scanned} files.")
    
    lines.append("")
    
    # Violations
    if report.violations:
        lines.append("VIOLATIONS")
        lines.append("-" * 80)
        lines.append("")
        
        # Group by type
        by_type: dict[str, list[Violation]] = {}
        for v in report.violations:
            by_type.setdefault(v.violation_type, []).append(v)
        
        for vtype, violations in sorted(by_type.items()):
            lines.append(f"[{vtype}] ({len(violations)} occurrence(s))")
            lines.append("")
            
            for i, v in enumerate(violations, 1):
                lines.append(f"  {i}. File: {v.file_path}")
                lines.append(f"     Line: {v.line_number}")
                lines.append(f"     Code: {v.code_snippet}")
                lines.append(f"     Explanation: {v.explanation}")
                lines.append("")
        
        lines.append("")
    
    # Suspicious Constructs
    if report.suspicious:
        lines.append("SUSPICIOUS CONSTRUCTS")
        lines.append("-" * 80)
        lines.append("")
        
        for i, sus in enumerate(report.suspicious, 1):
            lines.append(f"  {i}. File: {sus['file']}")
            lines.append(f"     Line: {sus['line']}")
            if 'function' in sus:
                lines.append(f"     Function: {sus['function']}")
            if 'class' in sus:
                lines.append(f"     Class: {sus['class']}")
            lines.append(f"     Reason: {sus['reason']}")
            lines.append("")
        
        lines.append("")
    
    # Compliant Access Points
    if report.compliant:
        lines.append("CONFIRMED COMPLIANT ACCESS POINTS")
        lines.append("-" * 80)
        lines.append("")
        
        for comp in report.compliant:
            lines.append(f"  ✓ {comp['file']}")
            lines.append(f"    {comp['reason']}")
            lines.append("")
        
        lines.append("")
    
    # Remediation Guidance
    if report.violations:
        lines.append("REMEDIATION GUIDANCE")
        lines.append("-" * 80)
        lines.append("")
        
        violation_types = set(v.violation_type for v in report.violations)
        
        if 'ILLEGAL_IMPORT' in violation_types:
            lines.append("ILLEGAL_IMPORT:")
            lines.append("  - Remove all imports of questionnaire_resource_provider from modules outside")
            lines.append("    the allowed set: {factory.py, core.py, questionnaire_resource_provider.py}")
            lines.append("  - Instead, receive QuestionnaireResourceProvider via dependency injection")
            lines.append("  - Use factory.build_processor() to get a properly wired ProcessorBundle")
            lines.append("")
        
        if 'ILLEGAL_DATA_ACCESS' in violation_types:
            lines.append("ILLEGAL_DATA_ACCESS:")
            lines.append("  - Remove all direct file I/O to questionnaire_monolith.json")
            lines.append("  - Use factory.load_questionnaire_monolith() for I/O-based initialization")
            lines.append("  - Use factory.build_processor() to get pre-loaded questionnaire data")
            lines.append("  - Pass questionnaire data via contracts/parameters, not by reading files")
            lines.append("")
        
        if 'LEGACY_IO_PATH' in violation_types:
            lines.append("LEGACY_IO_PATH:")
            lines.append("  - Replace QuestionnaireResourceProvider.from_file() calls with factory-based initialization")
            lines.append("  - In factory.py: use load_questionnaire_monolith() then construct QRP with that data")
            lines.append("  - In core modules: receive QRP via dependency injection, don't construct it")
            lines.append("  - Mark from_file() as @deprecated with migration guidance")
            lines.append("")
        
        if 'REIMPLEMENTED_QUESTIONNAIRE_LOGIC' in violation_types:
            lines.append("REIMPLEMENTED_QUESTIONNAIRE_LOGIC:")
            lines.append("  - Move all pattern extraction logic into questionnaire_resource_provider.py")
            lines.append("  - Expose pattern catalogs via QuestionnaireResourceProvider methods")
            lines.append("  - Remove duplicate pattern definitions from other modules")
            lines.append("  - Use provider.get_temporal_patterns(), provider.get_indicator_patterns(), etc.")
            lines.append("")
    
    return '\n'.join(lines)


def main():
    """Run the audit and generate report"""
    print("Starting Questionnaire Architecture Enforcement Audit...")
    print()
    
    report = scan_repository()
    
    # Generate text report
    text_report = generate_report(report)
    print(text_report)
    
    # Save to file
    output_file = REPO_ROOT / 'ARCHITECTURE_AUDIT_REPORT.txt'
    output_file.write_text(text_report, encoding='utf-8')
    print(f"\nReport saved to: {output_file}")
    
    # Save JSON report for programmatic processing
    json_report = {
        'compliant': report.is_compliant(),
        'files_scanned': report.files_scanned,
        'violations': [
            {
                'file': v.file_path,
                'line': v.line_number,
                'type': v.violation_type,
                'code': v.code_snippet,
                'explanation': v.explanation
            }
            for v in report.violations
        ],
        'suspicious': report.suspicious,
        'compliant_files': report.compliant
    }
    
    json_file = REPO_ROOT / 'ARCHITECTURE_AUDIT_REPORT.json'
    json_file.write_text(json.dumps(json_report, indent=2), encoding='utf-8')
    print(f"JSON report saved to: {json_file}")
    
    # Exit with appropriate code
    sys.exit(0 if report.is_compliant() else 1)


if __name__ == '__main__':
    main()
