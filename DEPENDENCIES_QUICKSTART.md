# Dependency Management Quick Start

This guide helps you quickly get started with the SAAAAAA dependency management system.

## Installation Scenarios

### Scenario 1: Minimal Production Environment

Install only core runtime dependencies:

```bash
pip install -r requirements-core.txt
```

**When to use**: Docker containers, production servers, minimal installs

### Scenario 2: Development Environment

Install core + development tools:

```bash
pip install -r requirements-dev.txt
```

**When to use**: Local development, CI/CD pipelines

### Scenario 3: Full Installation

Install everything including optional features:

```bash
pip install -r requirements-all.txt
```

**When to use**: Complete development environment, testing all features

## Quick Verification

After installation, verify everything works:

```bash
# Quick import check
python3 scripts/verify_importability.py

# Full dependency audit
python3 scripts/audit_dependencies.py

# Or use Make targets
make deps:verify
make deps:audit
```

## Common Tasks

### Check What's Installed

```bash
pip freeze
```

### Compare with Expected Versions

```bash
pip freeze > freeze-current.txt
python3 scripts/compare_freeze_lock.py freeze-current.txt constraints-new.txt
```

### Find Missing Dependencies

```bash
python3 scripts/audit_dependencies.py
# Check dependency_audit_report.json for details
```

### Lock Current Environment

```bash
make deps:lock
# Creates constraints-frozen.txt
```

## Troubleshooting

### Issue: Import errors after installation

**Solution 1**: Reinstall with constraints
```bash
pip install --force-reinstall -c constraints-new.txt -r requirements-core.txt
```

**Solution 2**: Check for missing packages
```bash
python3 scripts/verify_importability.py
```

### Issue: Version conflicts

**Solution**: Use constraints file
```bash
pip install -c constraints-new.txt -r requirements-core.txt
```

### Issue: tensorflow won't install (Python 3.12)

**Solution**: Install compatible version
```bash
pip install tensorflow>=2.16.0
```

⚠️ Downgrading Python is no longer supported. Stay on 3.12.x and upgrade TensorFlow to 2.16+.

### Issue: torch installation fails

**Solution**: Install from PyTorch index
```bash
# CPU only
pip install torch --index-url https://download.pytorch.org/whl/cpu

# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

## Python Version Compatibility

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.10 | ❌ Not Supported | Legacy configuration |
| 3.11 | ❌ Not Supported | Legacy configuration |
| 3.12 | ✅ Required | Upgrade TensorFlow to 2.16+ |

## File Reference

| File | Purpose |
|------|---------|
| `requirements-core.txt` | Core runtime dependencies (production) |
| `requirements-optional.txt` | Optional runtime features |
| `requirements-dev.txt` | Development & testing tools |
| `requirements-docs.txt` | Documentation generation |
| `requirements-all.txt` | All dependencies combined |
| `constraints-new.txt` | Version constraints for reproducibility |

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/audit_dependencies.py` | Scan code for imports, detect missing packages |
| `scripts/verify_importability.py` | Test that packages can be imported |
| `scripts/generate_dependency_files.py` | Generate all requirements files |
| `scripts/compare_freeze_lock.py` | Compare installed vs expected versions |
| `scripts/check_version_pins.py` | Verify all versions are exactly pinned |

## Make Targets

| Target | Command | Purpose |
|--------|---------|---------|
| Verify | `make deps:verify` | Full verification (imports + audit) |
| Lock | `make deps:lock` | Generate lock file from current env |
| Audit | `make deps:audit` | Scan for imports and missing packages |
| Clean | `make deps:clean` | Remove audit artifacts |

## CI/CD Integration

The system includes automated gates in `.github/workflows/dependency-gates.yml`:

1. **Missing Import Detection** - Fails if any imports can't be satisfied
2. **Importability Verification** - Fails if critical packages can't be imported
3. **Open Range Detection** - Fails if core dependencies use open ranges
4. **Freeze vs Lock** - Warns if installed versions differ from lock
5. **Security Scan** - Warns on known vulnerabilities

## Further Reading

- **Complete Documentation**: See `DEPENDENCIES_AUDIT.md`
- **Adding Dependencies**: See "Adding New Dependencies" section in `DEPENDENCIES_AUDIT.md`
- **CI/CD Gates**: See "CI/CD Gates" section in `DEPENDENCIES_AUDIT.md`

## Getting Help

1. Check `DEPENDENCIES_AUDIT.md` for detailed documentation
2. Run verification scripts to diagnose issues
3. Check GitHub issues for known problems
4. Create new issue with `dependencies` label

## Best Practices

✅ **DO**:
- Always use exact version pins (==) in requirements-core.txt
- Run `make deps:verify` before committing dependency changes
- Update `DEPENDENCIES_AUDIT.md` when adding new dependencies
- Test in clean virtual environment before committing
- Use constraints file for reproducible builds

❌ **DON'T**:
- Don't use open ranges (>=, ~=) in core dependencies
- Don't commit without running verification
- Don't skip security scans when updating packages
- Don't add dependencies without justification
- Don't modify generated files manually (use generator script)
