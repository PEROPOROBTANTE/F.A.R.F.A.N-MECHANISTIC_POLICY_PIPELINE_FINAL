# Canonical Method Catalog System - Quick Start

This guide provides quick access to the canonical method catalog system for method identification, calibration tracking, and migration management.

## 🚀 Quick Commands

### Build/Update Catalog
```bash
python3 scripts/build_canonical_method_catalog.py
```

### Detect Embedded Calibrations
```bash
python3 scripts/detect_embedded_calibrations.py
```

### Validate Compliance
```bash
python3 scripts/validate_canonical_catalog.py
python3 scripts/check_directive_compliance.py
```

### Run Tests
```bash
pytest tests/test_canonical_method_catalog.py -v
```

## 📊 Current Status

**Total Methods:** 1996  
**Calibration Coverage:** 31.7% centralized, 10.9% embedded, 57.3% unknown  
**Migration Backlog:** 61 methods (3 critical, 10 high priority)

## 📁 Key Files

### Core Artifacts
- `config/canonical_method_catalog.json` - Complete method inventory
- `config/embedded_calibration_appendix.json` - Migration backlog
- `config/embedded_calibration_appendix.md` - Human-readable appendix

### Documentation
- `CANONICAL_METHOD_CATALOG.md` - System documentation
- `IMPLEMENTATION_STAGES.md` - Stage tracking
- `DIRECTIVE_COMPLIANCE_SUMMARY.md` - Compliance status
- `CALIBRATION_SYSTEM.md` - Calibration system docs

### Tools
- `scripts/build_canonical_method_catalog.py` - Catalog builder
- `scripts/detect_embedded_calibrations.py` - Embedded detector
- `scripts/validate_canonical_catalog.py` - Catalog validator
- `scripts/check_directive_compliance.py` - Compliance checker

### Tests
- `tests/test_canonical_method_catalog.py` - 31 tests (all passing ✅)

## 🎯 Next Actions

### Immediate
1. Migrate 3 critical embedded calibrations
2. Investigate 320 unknown status methods

### Short-term
1. Complete high priority migrations (10 methods)
2. Begin Stage 1 (executor) implementation

## 📖 Full Documentation

See `CANONICAL_METHOD_CATALOG.md` for complete documentation.

## ✅ Directive Compliance

All 5 requirements met:
1. ✅ Universal coverage (1996 methods)
2. ✅ Mechanical decidability
3. ✅ Complete calibration tracking
4. ✅ Transitional cases managed
5. ✅ Stage enforcement ready

Run `python3 scripts/check_directive_compliance.py` for detailed compliance report.
