"""
Guardrail script to enforce the single-source calibration/parameter architecture:
- One primary intrinsic calibration file: config/intrinsic_calibration.json
- One primary parameter file: config/method_parameters.json
- Secondary/legacy artifacts must live under config/secundarios_sistema_c_y_p/
- Singletons for orchestrator/parameter/intrinsic loaders
- Single definition of LAYER_REQUIREMENTS

Run:
    python scripts/verify_no_parallel_calibration_systems.py

Exits non-zero on violations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY_INTRINSIC = REPO_ROOT / "config" / "intrinsic_calibration.json"
PRIMARY_PARAMS = REPO_ROOT / "config" / "method_parameters.json"
SECONDARY_DIR = REPO_ROOT / "config" / "secundarios_sistema_c_y_p"


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def check_primary_files() -> None:
    if not PRIMARY_INTRINSIC.exists():
        fail(f"Missing primary intrinsic calibration file: {PRIMARY_INTRINSIC}")
    if not PRIMARY_PARAMS.exists():
        fail(f"Missing primary parameter file: {PRIMARY_PARAMS}")
    if not (REPO_ROOT / "config" / "calibration_config.py").exists():
        fail("Missing calibration_config.py in config/")
    print("✅ Primary config files present")


def check_duplicates() -> None:
    intrinsic_candidates = [p for p in REPO_ROOT.rglob("intrinsic_calibration.json")]
    param_candidates = [p for p in REPO_ROOT.rglob("method_parameters.json")]

    def allowed(p: Path) -> bool:
        try:
            p.relative_to(SECONDARY_DIR)
            return True
        except ValueError:
            return False

    bad_intrinsic = [
        p for p in intrinsic_candidates if p != PRIMARY_INTRINSIC and not allowed(p)
    ]
    bad_params = [p for p in param_candidates if p != PRIMARY_PARAMS and not allowed(p)]

    if bad_intrinsic:
        fail(f"Found stray intrinsic_calibration.json: {bad_intrinsic}")
    if bad_params:
        fail(f"Found stray method_parameters.json: {bad_params}")
    print("✅ No stray primary calibration/parameter files")


def check_singletons() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from saaaaaa import get_calibration_orchestrator, get_parameter_loader  # type: ignore
        from saaaaaa.core.calibration.intrinsic_loader import IntrinsicCalibrationLoader  # type: ignore
    except Exception as exc:  # pragma: no cover
        fail(f"Failed to import calibration singletons: {exc}")

    orch1 = get_calibration_orchestrator()
    orch2 = get_calibration_orchestrator()
    if orch1 is not orch2:
        fail("CalibrationOrchestrator is not singleton")

    params1 = get_parameter_loader()
    params2 = get_parameter_loader()
    if params1 is not params2:
        fail("ParameterLoader is not singleton")

    intr1 = IntrinsicCalibrationLoader()
    intr2 = IntrinsicCalibrationLoader()
    if intr1 is not intr2:
        fail("IntrinsicCalibrationLoader is not singleton")

    print("✅ Singleton guards passed")


def check_layer_requirements_unique() -> None:
    matches = []
    for p in REPO_ROOT.rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "LAYER_REQUIREMENTS =" in content or "LAYER_REQUIREMENTS=" in content:
            matches.append(p)

    allowed = {
        REPO_ROOT / "src" / "saaaaaa" / "core" / "calibration" / "layer_requirements.py"
    }
    extraneous = [p for p in matches if p not in allowed]
    if extraneous:
        fail(f"Duplicate LAYER_REQUIREMENTS definitions: {extraneous}")
    print("✅ LAYER_REQUIREMENTS defined only once")


def sanity_load_jsons() -> None:
    for path in (PRIMARY_INTRINSIC, PRIMARY_PARAMS):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                json.load(fh)
        except Exception as exc:
            fail(f"JSON load failed for {path}: {exc}")
    print("✅ Primary JSON files parse correctly")


def main() -> None:
    check_primary_files()
    check_duplicates()
    check_singletons()
    check_layer_requirements_unique()
    sanity_load_jsons()
    print("🎯 Calibration/parameter architecture verified.")


if __name__ == "__main__":
    main()
