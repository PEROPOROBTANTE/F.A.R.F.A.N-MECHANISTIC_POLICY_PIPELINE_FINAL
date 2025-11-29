Validadores del sistema de calibración/parametrización.

- `check_calibration_inventory.py`: falla si hay más de un `intrinsic_calibration*.json` o `method_parameters*.json` en `config/` (secundarios permitidos).
- Añadir aquí otros validadores (ej. verify_no_hardcoded_calibrations.py, validate_calibration_system.py) apuntando siempre a primarios en `config/`.
