# Method Registration Policy

## Overview

This document describes the method registration policy for the SAAAAAA (F.A.R.F.A.N) framework.

## Method Catalog Files

### Primary Catalog: `config/rules/METODOS/catalogo_completo_canonico.json`

This is the **canonical source of truth** for all method registrations at Level 3 (NIVEL3) analysis.

**Structure:**
- Total methods: 593
- Complexity levels: LOW (280), MEDIUM (282), HIGH (31)
- Priority levels: LOW (289), MEDIUM (236), HIGH (24), CRITICAL (44)
- Version: 3.0.0
- Generated: Automated NIVEL3 Analysis System

### Compatibility Alias: `metodos_completos_nivel3.json`

A symbolic link to `config/rules/METODOS/catalogo_completo_canonico.json` for backward compatibility with legacy references and guardrails validation.

**Rationale:**
- The sin-carreta guardrails check references `metodos_completos_nivel3.json`
- The custom agent documentation (`.github/agents/my-agent.md`) references this filename
- Creating a symlink maintains compatibility while keeping the canonical file in its proper location

## Related Files

- `config/COMPLETE_METHOD_CLASS_MAP.json` - Complete granular mapping for Choreographer/Orchestrator integration (416 methods across 82 classes)
- `config/canonical_method_catalog.json` - Full method catalog (7.3MB) 
- `config/method_usage_intelligence.json` - Method usage patterns and intelligence
- `config/calibration_decisions.json` - Calibration data for registered methods

## Policy

1. **Single Source of Truth**: `config/rules/METODOS/catalogo_completo_canonico.json` is the authoritative catalog
2. **No Duplication**: Other references should use symlinks or imports, not copies
3. **Version Control**: All changes to method registrations must update the version field
4. **Guardrails Compliance**: The symlink ensures CI/CD guardrails pass without code duplication
5. **Documentation**: This file serves as the canonical reference for understanding the method registration architecture

## Integration Points

### Orchestrator
The orchestrator loads method definitions from:
1. `COMPLETE_METHOD_CLASS_MAP.json` for class-level mappings
2. `catalogo_completo_canonico.json` (via symlink) for detailed method aptitude scores
3. `calibration_decisions.json` for runtime calibration

### Custom Agent (MonolithForgeAgent)
References `metodos_completos_nivel3.json` in phase 6 (MethodSetSynthesisPhase) to inject method sets by base_slot.

### Guardrails
The sin-carreta guardrails (`.github/workflows/main.yml`) validates that referenced configuration files exist in the repository.

## Maintenance

When updating method registrations:
1. Edit `config/rules/METODOS/catalogo_completo_canonico.json`
2. Increment the version number
3. Update `generated_at` timestamp
4. Regenerate `COMPLETE_METHOD_CLASS_MAP.json` if class mappings change
5. The symlink automatically reflects changes (no action needed)

## Migration from CPP to SPC

As part of the terminology migration from CPP (Canon Policy Package) to SPC (Smart Policy Chunks), method registrations continue to use the same catalog structure. The SPC adapter (`spc_adapter.py`) and orchestrator integration remain compatible with all existing method definitions.
