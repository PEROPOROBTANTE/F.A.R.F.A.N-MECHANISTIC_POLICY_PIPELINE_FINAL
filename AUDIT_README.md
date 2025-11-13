# Runtime Code Audit Tool

## Overview

This directory contains a comprehensive audit tool for identifying files and directories that are **not strictly required for runtime execution** of a Python codebase. The tool performs a **dry-run analysis only** and never modifies the working tree.

## Files

- **`runtime_audit.py`** - The audit tool implementation
- **`AUDIT_DRY_RUN_REPORT.json`** - Machine-readable complete audit report
- **`AUDIT_SUMMARY.md`** - Human-readable executive summary

## Quick Start

### Run the Audit

```bash
# Generate a fresh audit report
python runtime_audit.py > my_audit.json 2> audit.log

# Or use the pre-generated report
cat AUDIT_DRY_RUN_REPORT.json | jq '.evidence.summary'
```

### Read the Summary

```bash
# View the human-readable summary
cat AUDIT_SUMMARY.md
```

## How It Works

The audit tool implements a comprehensive 9-step analysis:

### Step 1: Parse Packaging Configuration
- Reads `setup.py`, `pyproject.toml`, `setup.cfg`
- Extracts entry points (console_scripts, etc.)
- Identifies the package structure

### Step 2: Build Import Graph
- Parses all Python files using AST
- Traces `import` and `from ... import` statements
- Resolves module paths to file locations
- Builds a dependency graph

### Step 3: Scan for Dynamic Imports
- Detects `importlib.import_module()`
- Detects `__import__()`
- Finds plugin registries and factory patterns
- Matches string literals that look like module names
- Scans for `pkg_resources` and `entry_points()` usage

### Step 4: Scan for Runtime File I/O
- Detects `open()`, `Path().read_text()`, `Path().read_bytes()`
- Finds `json.load()`, `json.loads()`
- Finds `yaml.safe_load()`, `yaml.load()`
- Resolves file paths to actual files in the repository

### Step 5: Identify Package Structure
- Finds all `__init__.py` files
- Maps package directories
- Preserves package hierarchy

### Step 6: Trace Reachability
- Performs DFS from entry points through import graph
- Marks all reachable modules
- Preserves parent `__init__.py` files for package integrity

### Step 7: Classify Files
- **Keep**: Files required for runtime
- **Delete**: Files safe to remove (with rule citations)
- **Unsure**: Files needing human review

### Step 8: Simulate Smoke Test
- Verifies main package can be imported
- Checks package structure integrity

### Step 9: Generate Report
- Outputs structured JSON report
- Includes complete evidence trail
- Provides rule citations for all decisions

## Classification Rules

### Files are KEPT if:
- ✅ Reachable in import graph from entry points
- ✅ Referenced by runtime file I/O operations
- ✅ Required for package structure (`__init__.py` in kept packages)
- ✅ Packaging files (setup.py, pyproject.toml, requirements.txt)
- ✅ Compatibility shims for backward-compatible imports

### Files are marked for DELETION if ALL these hold:
- ❌ Not reachable in import graph
- ❌ Not matched by dynamic import patterns
- ❌ Not referenced by runtime file I/O
- ❌ Not required for package structure
- ❌ Match deletion patterns (tests, docs, examples, dev tools, etc.)

### Files are UNSURE if:
- ⚠️ Python files not in import graph (might be CLI entry points)
- ⚠️ Files with `main()` function not in packaging config
- ⚠️ Legacy/deprecated/experimental code
- ⚠️ Ambiguous purpose requiring human judgment

## Report Structure

### JSON Report Format

```json
{
  "keep": [
    {
      "path": "src/saaaaaa/core/orchestrator/core.py",
      "reason": "Reachable in import graph from entry points"
    }
  ],
  "delete": [
    {
      "path": "tests/test_core.py",
      "reason": "Test file; not required for runtime",
      "rules": ["unreachable-import-graph", "no-runtime-io"]
    }
  ],
  "unsure": [
    {
      "path": "scripts/utility.py",
      "ambiguity": "Has main() function; might be CLI entry point"
    }
  ],
  "evidence": {
    "entry_points": ["saaaaaa.core.orchestrator:main"],
    "import_graph_nodes": 115,
    "dynamic_strings_matched": ["'factory'", "'registry'"],
    "runtime_io_refs": ["core.py -> 'config/settings.json'"],
    "smoke_test": "simulated-pass",
    "summary": {
      "total_kept": 142,
      "total_deleted": 258,
      "total_unsure": 84,
      "entry_points_analyzed": 4
    }
  }
}
```

## Query Examples

### Using jq to Query the Report

```bash
# Get summary statistics
jq '.evidence.summary' AUDIT_DRY_RUN_REPORT.json

# List all files to keep
jq '.keep[].path' AUDIT_DRY_RUN_REPORT.json -r

# List all test files marked for deletion
jq '.delete[] | select(.path | contains("test")) | .path' AUDIT_DRY_RUN_REPORT.json -r

# Find files kept due to runtime I/O
jq '.keep[] | select(.reason | contains("runtime file I/O"))' AUDIT_DRY_RUN_REPORT.json

# List all unsure items with main() function
jq '.unsure[] | select(.ambiguity | contains("main()"))' AUDIT_DRY_RUN_REPORT.json

# Count deletion categories
jq '.delete | group_by(.reason) | map({reason: .[0].reason, count: length})' AUDIT_DRY_RUN_REPORT.json
```

### Using Python to Query the Report

```python
import json

with open('AUDIT_DRY_RUN_REPORT.json') as f:
    report = json.load(f)

# Get all Python files in src/ that should be kept
kept_src_files = [
    item['path'] for item in report['keep']
    if item['path'].startswith('src/') and item['path'].endswith('.py')
]

# Get all test files marked for deletion
test_deletions = [
    item for item in report['delete']
    if 'test' in item['path'].lower()
]

# Get files needing human review
unsure = report['unsure']
print(f"Files needing review: {len(unsure)}")
```

## Interpreting Results

### Keep Category
These files are **required for runtime execution**. Do not delete these files as they are:
- Imported by the application
- Loaded at runtime via file I/O
- Required for package imports to work
- Part of the packaging infrastructure

### Delete Category
These files are **safe to remove** as they are:
- Not reachable from entry points
- Not used at runtime
- Development, testing, or documentation files

Each deletion includes specific **rule citations** explaining why it's safe to delete.

### Unsure Category
These files require **human review** because:
- They might be CLI entry points not declared in packaging config
- They might be compatibility shims
- Their purpose is ambiguous
- They use patterns the tool cannot analyze

**Action Required:** Review each unsure item manually before making a decision.

## Safety Features

### ⚠️ This Tool is DRY-RUN ONLY
- **Never modifies files**
- **Never deletes anything**
- Only produces a report
- All changes must be made manually after human review

### Safety Checks Performed
✅ Import graph tracing from all entry points  
✅ Dynamic import pattern detection  
✅ Runtime file I/O scanning  
✅ Package structure verification  
✅ Smoke test simulation  

### Caveats and Limitations

1. **Static Analysis Only**: Cannot detect runtime-computed imports like `importlib.import_module(variable)`
2. **False Negatives**: May miss some dynamic patterns
3. **Conservative**: Prefers "unsure" over incorrect deletion
4. **No Execution**: Does not run the code, only analyzes it statically

## Recommended Workflow

### Phase 1: Human Review (YOU ARE HERE)
1. Read `AUDIT_SUMMARY.md` for overview
2. Review unsure items manually
3. Verify deletion candidates make sense
4. Check for any obvious misclassifications

### Phase 2: Validation
1. Create a git branch for the deletion
2. Start with low-risk deletions (docs, examples)
3. Run tests after each batch deletion
4. Verify package still installs: `pip install -e .`

### Phase 3: Cleanup
1. Delete files in batches by category
2. Update `.gitignore` if needed
3. Update documentation
4. Commit with clear messages

### Phase 4: Verification
1. Full test suite run
2. Package installation test
3. CLI entry point tests
4. Import smoke tests

## Customization

### Modify Keep Rules

Edit `_should_keep()` method in `runtime_audit.py`:

```python
def _should_keep(self, item: Path) -> bool:
    # Add your custom keep logic here
    if item.name == "my_special_file.txt":
        return True
    # ... existing logic ...
```

### Modify Delete Patterns

Edit `_should_delete()` method:

```python
delete_patterns = [
    'test_*.py', 
    '*_test.py',
    # Add more patterns here
    'my_pattern/',
]
```

### Add Dynamic Import Patterns

Edit `_scan_dynamic_imports()` method:

```python
patterns = [
    r'importlib\.import_module',
    r'__import__\(',
    # Add more patterns here
    r'my_custom_loader',
]
```

## Troubleshooting

### "Too many files in unsure category"

This is expected for a complex repository. Review these manually:
- Check if Python files are compatibility shims
- Verify if files with main() should be entry points
- Document intentional standalone scripts

### "Entry points not found"

The tool looks for entry points in:
- `setup.py` (entry_points section)
- `pyproject.toml` ([project.scripts] section)

If your project uses a different format, you may need to update `_parse_packaging_files()`.

### "Import resolution failing"

The tool tries multiple strategies to resolve imports:
1. From `src/` directory
2. From repository root
3. Relative imports

If you have a custom package structure, update `_resolve_import()` method.

## Contributing

To improve the audit tool:

1. Add more dynamic import patterns
2. Improve import resolution logic
3. Add more file I/O patterns
4. Enhance classification rules
5. Add custom checks for your domain

## License

Same as the parent project.

## Contact

For questions or issues, please refer to the parent project's issue tracker.
