Parametrización secundaria (no runtime).

- Primario vivo: `config/method_parameters.json`.
- Aquí solo derivados (`migration_*`, `legacy_*`, `exp_*`, `draft_*`) con `_metadata.status` + `_metadata.superseded_by` y `_live: false`.
- Uso permitido: migraciones o experimentación controlada; no cargar en runtime.
