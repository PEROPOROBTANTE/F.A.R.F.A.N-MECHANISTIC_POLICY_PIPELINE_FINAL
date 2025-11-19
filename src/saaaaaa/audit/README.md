# FARFAN Pipeline - Audit System

## Overview

The FARFAN Audit System provides comprehensive automated auditing capabilities to verify architectural compliance, dependency injection patterns, and code quality standards.

## Quick Start

### Run Complete Audit

```bash
cd /home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE
python -m saaaaaa.audit.audit_system --repo-root . --output audit_report.json --verbose
```

### Import in Python

```python
from saaaaaa.audit import AuditSystem
from saaaaaa.config.paths import PROJECT_ROOT

# Create audit system using canonical project root
audit_system = AuditSystem(PROJECT_ROOT)

# Run specific audits
executor_results = audit_system.audit_executor_architecture()
questionnaire_results = audit_system.audit_questionnaire_access()
factory_results = audit_system.audit_factory_pattern()

# Generate comprehensive report
report = audit_system.generate_audit_report(Path("audit_report.json"))

# Print summary
audit_system.print_summary()
```

## Audit Categories

### 1. Executor Architecture
Verifies that all 30 dimension-question executors (D1Q1-D6Q5) are properly implemented.

**What it checks:**
- All 30 executor classes exist
- Each executor has required methods
- Dimension mapping is correct
- Executor hierarchy is proper

### 2. Questionnaire Access
Verifies that core scripts use dependency injection for questionnaire access.

**What it checks:**
- No direct file access to `questionnaire_monolith.json`
- No unauthorized `QuestionnaireResourceProvider` instantiation
- No direct `load_questionnaire()` calls outside factory
- Proper dependency injection patterns

### 3. Factory Pattern
Verifies the factory pattern implementation for dependency injection.

**What it checks:**
- `factory.py` exists and is complete
- `load_questionnaire()` function exists
- `QuestionnaireResourceProvider` class exists
- Proper separation of concerns

### 4. Method Signatures
Verifies that all methods have complete signatures and documentation.

**What it checks:**
- Type annotations on parameters
- Return type annotations
- Docstrings present
- Parameter documentation

### 5. Configuration System
Verifies type-safety and validation in configuration modules.

**What it checks:**
- Pydantic BaseModel usage
- Field validation
- Type safety
- Immutability (frozen models)

## Audit Findings

Each audit produces findings with the following structure:

```python
AuditFinding(
    category=AuditCategory.EXECUTOR_ARCHITECTURE,
    status=AuditStatus.VERIFIED,  # VERIFIED, WARNING, or FAILED
    component="D1Q1_Executor",
    message="Executor properly defined",
    details={...},
    timestamp="2025-11-13T..."
)
```

## Exit Codes

When run as a command-line tool:

- `0` - All audits passed
- `1` - One or more audits failed
- `2` - One or more warnings (but no failures)

## Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run FARFAN Audit
  run: |
    python -m saaaaaa.audit.audit_system \
      --repo-root . \
      --output audit_report.json

- name: Upload Audit Report
  uses: actions/upload-artifact@v3
  with:
    name: audit-report
    path: audit_report.json
```

## Verification Commands

### Quick Checks

```bash
# Count executors
grep -c "class D[1-6]Q[1-5]_Executor" src/saaaaaa/core/orchestrator/executors.py
# Expected: 30

# Check for unauthorized questionnaire access
grep -r "questionnaire_monolith.json" src/saaaaaa/processing/ src/saaaaaa/analysis/
# Expected: no results

# Verify factory exists
ls -la src/saaaaaa/core/orchestrator/factory.py
# Expected: file exists
```

## Audit Report Format

The generated JSON report contains:

```json
{
  "audit_metadata": {
    "timestamp": "2025-11-13T...",
    "repository_root": "/path/to/repo",
    "total_findings": 45
  },
  "audit_results": {
    "executor_architecture": {...},
    "questionnaire_access": {...},
    "factory_pattern": {...},
    "method_signatures": {...},
    "configuration_system": {...}
  },
  "findings": [...],
  "summary": {
    "total_findings": 45,
    "verified": 42,
    "warnings": 2,
    "failed": 1,
    "by_category": {...}
  }
}
```

## Troubleshooting

### Issue: "Executors file not found"
**Solution:** Ensure you're running from the repository root and the path to `executors.py` is correct.

### Issue: "Questionnaire access violations detected"
**Solution:** Check that core scripts don't directly access `questionnaire_monolith.json`. Use dependency injection instead.

### Issue: "Factory pattern incomplete"
**Solution:** Verify that `factory.py` and `questionnaire.py` exist and have the required functions/classes.

## Related Documentation

- [AUDIT_COMPLIANCE_REPORT.md](../../../AUDIT_COMPLIANCE_REPORT.md) - Comprehensive audit findings
- [Integration Tests](../../../tests/integration/test_30_executors.py) - Automated testing
- [Saga Pattern](../patterns/saga.py) - Compensating transactions
- [Event Tracking](../patterns/event_tracking.py) - Event system
- [RL Optimization](../optimization/rl_strategy.py) - Strategy optimization
- [OpenTelemetry](../observability/opentelemetry_integration.py) - Observability

## Support

For questions or issues with the audit system, please refer to the main project documentation or open an issue in the repository.
