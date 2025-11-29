Calibración secundaria (no runtime).

- Primario vivo: `config/intrinsic_calibration.json` y `config/layer_calibrations/`.
- Aquí solo van derivados (`migration_*`, `legacy_*`, `exp_*`, `draft_*`) con `_metadata.status` + `_metadata.superseded_by` y siempre `_live: false`.
- Uso permitido: migraciones, auditorías o regeneración; no consumir en carga de producción.
