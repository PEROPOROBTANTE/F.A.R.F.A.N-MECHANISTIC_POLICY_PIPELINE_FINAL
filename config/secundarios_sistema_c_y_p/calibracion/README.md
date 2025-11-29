# Secundarios - Calibración

Estado: archivos NO vivos. Solo consulta histórica/migración.

Primarios vigentes:
- `config/intrinsic_calibration.json`
- `config/intrinsic_calibration_rubric.json`
- `config/layer_calibrations/`

Reglas:
- Prefijos obligatorios: legacy_*, draft_*, migration_*, exp_*
- `_metadata`: `status`, `superseded_by`, `_live: false`, `_deprecated: true`
- No usar en runtime ni como fuente de loaders.
