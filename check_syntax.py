import os
import py_compile
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass
import traceback


@dataclass
class SyntaxErrorRecord:
    file_path: str
    error_type: str
    line_number: int
    message: str
    full_traceback: str


class ComprehensiveSyntaxValidator:
    def __init__(self):
        self.errors: List[SyntaxErrorRecord] = []
        self.checked_files = 0
        self.directories_to_scan = [
            "src/farfan_pipeline",
            "farfan_core",
            "tests",
            "scripts",
            "tools",
        ]
    
    def validate_file(self, file_path: str) -> None:
        """Validate a single Python file for syntax errors."""
        self.checked_files += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                error_msg = str(e)
                line_num = e.lineno if e.lineno else 0
                
                error_detail = self._classify_error(e, content)
                
                self.errors.append(SyntaxErrorRecord(
                    file_path=file_path,
                    error_type=error_detail,
                    line_number=line_num,
                    message=error_msg,
                    full_traceback=traceback.format_exc()
                ))
                return
            
            try:
                ast.parse(content, filename=file_path)
            except SyntaxError as e:
                error_msg = str(e)
                line_num = e.lineno if e.lineno else 0
                error_detail = self._classify_error(e, content)
                
                self.errors.append(SyntaxErrorRecord(
                    file_path=file_path,
                    error_type=error_detail,
                    line_number=line_num,
                    message=error_msg,
                    full_traceback=traceback.format_exc()
                ))
                return
            
            try:
                py_compile.compile(file_path, doraise=True)
            except py_compile.PyCompileError as e:
                self.errors.append(SyntaxErrorRecord(
                    file_path=file_path,
                    error_type="PyCompileError",
                    line_number=0,
                    message=str(e),
                    full_traceback=traceback.format_exc()
                ))
                
        except UnicodeDecodeError as e:
            self.errors.append(SyntaxErrorRecord(
                file_path=file_path,
                error_type="UnicodeDecodeError",
                line_number=0,
                message=f"Invalid encoding: {str(e)}",
                full_traceback=traceback.format_exc()
            ))
        except Exception as e:
            self.errors.append(SyntaxErrorRecord(
                file_path=file_path,
                error_type=type(e).__name__,
                line_number=0,
                message=str(e),
                full_traceback=traceback.format_exc()
            ))
    
    def _classify_error(self, error: Exception, content: str) -> str:
        """Classify the type of syntax error."""
        error_msg = str(error).lower()
        
        if "missing parentheses" in error_msg or "unclosed" in error_msg:
            return "Unclosed brackets/parentheses"
        elif "invalid character" in error_msg or "non-ascii" in error_msg:
            return "Illegal characters"
        elif "unexpected indent" in error_msg or "expected an indented block" in error_msg:
            return "Invalid indentation"
        elif "invalid syntax" in error_msg and "f-string" in error_msg:
            return "Malformed f-strings"
        elif ":" in error_msg and "expected" in error_msg:
            return "Missing colons"
        elif "positional" in error_msg or "keyword" in error_msg:
            return "Python 3.10+ syntax violations"
        elif "invalid decimal literal" in error_msg:
            return "Invalid decimal literal"
        elif "from __future__" in error_msg:
            return "Invalid __future__ import placement"
        else:
            return "Syntax error"
    
    def scan_directory(self, directory: str) -> None:
        """Recursively scan a directory for Python files."""
        if not os.path.exists(directory):
            print(f"Warning: Directory {directory} does not exist")
            return
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'farfan-env', '.venv', 'venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.validate_file(file_path)
    
    def generate_report(self) -> str:
        """Generate a markdown report of all syntax errors."""
        report = []
        report.append("# Python Syntax Validation Report\n")
        report.append(f"**Total files checked:** {self.checked_files}\n")
        report.append(f"**Files with errors:** {len(self.errors)}\n")
        report.append(f"**Success rate:** {((self.checked_files - len(self.errors)) / self.checked_files * 100):.2f}%\n\n")
        
        if not self.errors:
            report.append("✅ **All Python files passed syntax validation!**\n")
            return ''.join(report)
        
        report.append("## Error Summary by Type\n\n")
        error_types: Dict[str, int] = {}
        for error in self.errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{error_type}**: {count} file(s)\n")
        
        report.append("\n## Detailed Error List\n\n")
        
        for idx, error in enumerate(self.errors, 1):
            report.append(f"### Error {idx}: {error.file_path}\n\n")
            report.append(f"- **Type:** {error.error_type}\n")
            report.append(f"- **Line:** {error.line_number}\n")
            report.append(f"- **Message:** {error.message}\n\n")
            report.append("```python\n")
            report.append(error.full_traceback)
            report.append("\n```\n\n")
        
        return ''.join(report)
    
    def run(self) -> int:
        """Run the validation process."""
        print("=" * 80)
        print("COMPREHENSIVE PYTHON SYNTAX VALIDATION")
        print("=" * 80)
        print()
        
        for directory in self.directories_to_scan:
            print(f"Scanning directory: {directory}")
            self.scan_directory(directory)
        
        print(f"\nValidation complete!")
        print(f"Total files checked: {self.checked_files}")
        print(f"Files with errors: {len(self.errors)}")
        
        report_content = self.generate_report()
        
        with open("SYNTAX_VALIDATION_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"\nReport saved to: SYNTAX_VALIDATION_REPORT.md")
        
        if self.errors:
            print("\n❌ VALIDATION FAILED - Syntax errors found")
            return 1
        else:
            print("\n✅ VALIDATION PASSED - No syntax errors found")
            return 0


if __name__ == "__main__":
    validator = ComprehensiveSyntaxValidator()
    sys.exit(validator.run())
