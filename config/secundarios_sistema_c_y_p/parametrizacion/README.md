# Secundarios - Parametrización

Estado: archivos NO vivos. Solo consulta histórica/migración.

Primario vigente: `config/method_parameters.json`

Reglas:
- Prefijos obligatorios: legacy_*, draft_*, migration_*, exp_*
- `_metadata`: `status`, `superseded_by`, `_live: false`, `_deprecated: true`
- No usar en runtime ni como fuente de loaders.
