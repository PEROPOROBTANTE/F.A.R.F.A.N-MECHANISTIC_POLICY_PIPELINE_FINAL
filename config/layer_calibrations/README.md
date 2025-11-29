# Layer Calibrations

Productos de calibración por capa (Sistema 2). Cada archivo refleja calibraciones finales por rol/método.

Primarios:
- Directorio completo `config/layer_calibrations/` es la única fuente de calibraciones por capa.
- No contiene parámetros de método (Sistema 1).

Reglas:
- Formato: `config/layer_calibrations/<ROLE>/<method>.json`
- No mezclar parámetros ni thresholds aquí; esos viven en `config/method_parameters.json`.
- Secundarios/legacy deben ir a `config/secundarios_sistema_c_y_p/calibracion/` con prefijo y metadatos.
