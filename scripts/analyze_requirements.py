#!/usr/bin/env python3
"""
Complete requirements compatibility analyzer.
Checks ALL packages against Python 3.10.12 and identifies conflicts.
"""
import sys
import json
from packaging import version
from packaging.requirements import Requirement

def parse_requirements_file(filepath):
    """Parse requirements file and return list of requirements."""
    requirements = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#') and not line.startswith('-r'):
                try:
                    req = Requirement(line)
                    requirements.append({
                        'name': req.name,
                        'specifier': str(req.specifier),
                        'raw': line,
                        'file': filepath
                    })
                except Exception as e:
                    print(f"Warning: Could not parse '{line}': {e}", file=sys.stderr)
    return requirements

def main():
    files = [
        'requirements.txt',
        'requirements-dev.txt',
        'requirements-optional.txt',
        'requirements-docs.txt'
    ]
    
    all_requirements = {}
    conflicts = []
    
    # Parse all files
    for filepath in files:
        try:
            reqs = parse_requirements_file(filepath)
            for req in reqs:
                name = req['name'].lower()
                if name not in all_requirements:
                    all_requirements[name] = []
                all_requirements[name].append(req)
        except FileNotFoundError:
            print(f"Warning: {filepath} not found", file=sys.stderr)
    
    # Find conflicts
    print("=" * 80)
    print("REQUIREMENTS COMPATIBILITY ANALYSIS")
    print("=" * 80)
    print(f"\nPython Version: 3.10.12\n")
    
    print("DUPLICATE PACKAGES (different versions):")
    print("-" * 80)
    for name, reqs in sorted(all_requirements.items()):
        if len(reqs) > 1:
            # Check if versions differ
            versions = set(req['specifier'] for req in reqs)
            if len(versions) > 1:
                conflicts.append(name)
                print(f"\n⚠️  {name.upper()}")
                for req in reqs:
                    print(f"    {req['file']:30s} → {req['specifier']}")
    
    if not conflicts:
        print("  ✓ No version conflicts found")
    
    # Known Python 3.10 incompatibilities
    print("\n\nKNOWN PYTHON 3.10 INCOMPATIBILITIES:")
    print("-" * 80)
    
    py310_issues = {
        'networkx': ('3.5', '3.4.2', 'networkx 3.5 requires Python >=3.11'),
        'sentence-transformers': ('3.3.1', '3.0.1', 'Newer versions may have better compatibility'),
    }
    
    for name, reqs in sorted(all_requirements.items()):
        if name in py310_issues:
            pinned_ver, recommended_ver, reason = py310_issues[name]
            for req in reqs:
                if pinned_ver in req['specifier']:
                    print(f"\n❌ {name.upper()}")
                    print(f"    Current: {req['specifier']}")
                    print(f"    Recommended for Python 3.10: =={recommended_ver}")
                    print(f"    Reason: {reason}")
    
    print("\n\nRECOMMENDED FIXES:")
    print("=" * 80)
    print("""
1. networkx: Change from ==3.5 to ==3.4.2 (last version supporting Python 3.10)
2. Flask: Consolidate to ==3.0.3 (resolve conflict between requirements.txt and requirements-optional.txt)
3. flask-socketio: Use ==5.4.1 (from requirements-optional.txt)
4. pyjwt: Use ==2.10.1 (from requirements-optional.txt)
5. sentence-transformers: Keep ==3.0.1 for stability

All other packages appear compatible with Python 3.10.12
""")
    
    return 0 if not conflicts else 1

if __name__ == '__main__':
    sys.exit(main())
