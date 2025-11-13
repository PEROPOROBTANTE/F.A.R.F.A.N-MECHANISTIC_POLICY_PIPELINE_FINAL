#!/usr/bin/env python3
"""
Strategic file validation helper script.
Validates syntax and provenance for strategic files listed in config/strategic_files.txt.
"""
import subprocess
import sys
from pathlib import Path

def read_strategic_files(config_path: str = "config/strategic_files.txt") -> list[str]:
    """Read strategic files from configuration."""
    files = []
    with open(config_path) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                files.append(line)
    return files

def validate_python_syntax(files: list[str]) -> int:
    """Validate Python syntax for all strategic files."""
    print("=== Validating Python syntax for all strategic files ===")

    failed = []
    for file_path in files:
        if Path(file_path).exists():
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True
            )
            if result.returncode != 0:
                failed.append(file_path)
                print(f"❌ {file_path} - syntax error")
            else:
                print(f"✓ {file_path}")
        else:
            print(f"⚠️  {file_path} - file not found (skipping)")

    if failed:
        print(f"\n❌ {len(failed)} file(s) failed syntax validation")
        return 1
    else:
        print("\n✓ All strategic files have valid Python syntax")
        return 0

def check_provenance(files: list[str], provenance_file: str = "provenance.csv") -> int:
    """Check that all strategic files are tracked in provenance.csv."""
    print(f"\n=== Verifying provenance tracking in {provenance_file} ===")

    if not Path(provenance_file).exists():
        print(f"❌ ERROR: {provenance_file} not found")
        return 1

    with open(provenance_file) as f:
        provenance_content = f.read()

    missing_files = []
    for file_path in files:
        # Extract just the filename for checking
        filename = Path(file_path).name
        if filename not in provenance_content:
            missing_files.append(file_path)

    if not missing_files:
        print(f"✓ All {len(files)} strategic files tracked in {provenance_file}")
        return 0
    else:
        print(f"❌ ERROR: {len(missing_files)} file(s) not tracked in {provenance_file}:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return 1

def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python tools/validate_strategic_files.py <command>")
        print("Commands:")
        print("  syntax      - Validate Python syntax for all strategic files")
        print("  provenance  - Check provenance tracking")
        print("  all         - Run all validations")
        sys.exit(1)

    command = sys.argv[1]

    try:
        files = read_strategic_files()
        print(f"Loaded {len(files)} strategic files from config\n")
    except FileNotFoundError:
        print("ERROR: config/strategic_files.txt not found")
        sys.exit(1)

    if command == "syntax":
        sys.exit(validate_python_syntax(files))

    elif command == "provenance":
        sys.exit(check_provenance(files))

    elif command == "all":
        exit_code = 0
        exit_code |= validate_python_syntax(files)
        exit_code |= check_provenance(files)
        sys.exit(exit_code)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
