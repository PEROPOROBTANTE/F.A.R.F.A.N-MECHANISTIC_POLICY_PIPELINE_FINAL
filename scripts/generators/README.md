Generadores de calibración/parametrización (outputs primarios).

- `determine_parameter_values.py`, `determine_parameter_values_v3.py`: producen `config/method_parameters.json`.
- `rigorous_calibration_triage.py`: produce `config/intrinsic_calibration.json` y `config/layer_calibrations/<ROLE>/...` según rol.

Reglas:
- Siempre escribir a `config/` (no root, no secundarios).
- Etiquetar derivados como `migration_*`/`draft_*` si se guardan en secundarios.
