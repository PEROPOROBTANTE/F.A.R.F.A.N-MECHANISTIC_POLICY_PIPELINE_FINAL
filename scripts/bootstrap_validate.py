#!/usr/bin/env python3
"""Bootstrap and validation utility for the ATROZ analytical stack.

This script provisions an isolated Python environment, installs the
``requirements_atroz.txt`` dependencies, performs a dry-run import of the
:class:`PolicyAnalysisOrchestrator`, executes a CHESS strategy run against a
provided plan document, and finally validates the dashboard interface either by
launching the Flask API server or by running the integration test suite.

The goal is to give operators a single command that both warms up the canonical
registry (surfacing any missing wheels before the heavy orchestration run) and
confirms that the analytical and presentation layers are healthy once the
dependencies are available.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

# Define repository root
repo_root = Path(__file__).parent.parent

def create_virtualenv(venv_path: Path, python_executable: str) -> Path:
    """Create the virtual environment if it does not yet exist."""
    if venv_path.exists():
        print(f"[bootstrap] Using existing virtual environment at {venv_path}")
    else:
        print(f"[bootstrap] Creating virtual environment at {venv_path}")
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
        )

    if os.name == "nt":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    if not python_path.exists():
        raise RuntimeError(
            f"Python executable not found inside virtualenv: {python_path}"
        )

    return python_path

def install_dependencies(venv_python: Path, requirements_file: Path) -> None:
    """Install project requirements into the virtual environment."""
    print(f"[bootstrap] Installing dependencies from {requirements_file}")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
        ],
        check=True,
    )

def dry_run_import(venv_python: Path, repo_root: Path) -> None:
    """Trigger a dry-run import to surface missing wheels early."""
    print("[bootstrap] Performing dry-run import of PolicyAnalysisOrchestrator")
    subprocess.run(
        [
            str(venv_python),
            "-c",
            "from orchestrator import PolicyAnalysisOrchestrator; print('import-ok')",
        ],
        cwd=str(repo_root),
        check=True,
    )

def load_plan_metadata(metadata_path: Path | None, plan_path: Path) -> dict:
    """Load plan metadata from JSON or synthesize a default payload."""
    if metadata_path:
        print(f"[bootstrap] Loading plan metadata from {metadata_path}")
        with metadata_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # Default metadata payload derived from the plan file itself.
    print("[bootstrap] No metadata file provided; generating default metadata")
    return {
        "source_path": str(plan_path.resolve()),
        "plan_name": plan_path.stem,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

def execute_chess_strategy(
    venv_python: Path,
    repo_root: Path,
    plan_path: Path,
    metadata: dict,
    output_dir: Path,
) -> None:
    """Run the CHESS strategy end to end using the orchestrator."""
    print("[bootstrap] Executing CHESS strategy against provided plan document")

    helper_code = dedent(
        f"""
        import json
        from pathlib import Path
        from saaaaaa.core.orchestrator import PolicyAnalysisOrchestrator, OrchestratorConfig

        repo_root = Path({json.dumps(str(repo_root))})
        plan_path = Path({json.dumps(str(plan_path))})
        plan_document = plan_path.read_text(encoding='utf-8')
        metadata = json.loads({json.dumps(metadata)})

        config = OrchestratorConfig(
            questionnaire_path=str(repo_root / 'questionnaire_monolith.json'),
            plan_document_path=str(plan_path),
            execution_mapping_path=str(repo_root / 'execution_mapping.yaml'),
            method_class_map_path=str(repo_root / 'COMPLETE_METHOD_CLASS_MAP.json'),
            output_directory=str({json.dumps(str(output_dir))}),
        )

        orchestrator = PolicyAnalysisOrchestrator(config)
        result = orchestrator.execute_chess_strategy(plan_document, metadata)
        orchestrator.save_results(result)

        print('execution-id:', result.execution_id)
        print('overall-score:', getattr(result.macro_result, 'overall_score', 'n/a'))
        print('micro-answers:', len(result.micro_results))
        print('meso-clusters:', len(result.meso_results))
        print('chess-execution-complete')
        """
    )

    subprocess.run(
        [str(venv_python), "-c", helper_code],
        cwd=str(repo_root),
        check=True,
    )

def run_validation(venv_python: Path, repo_root: Path, mode: str) -> None:
    """Validate either via integration tests or by launching the API."""
    if mode == "tests":
        print("[bootstrap] Running integration tests with pytest")
        subprocess.run(
            [str(venv_python), "-m", "pytest", "tests"],
            cwd=str(repo_root),
            check=True,
        )
    else:
        print("[bootstrap] Launching Flask API server (press Ctrl+C to stop)")
        subprocess.run(
            [str(venv_python), "api_server.py"],
            cwd=str(repo_root),
            check=True,
        )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision dependencies, execute CHESS, and validate the dashboard",
    )
    parser.add_argument(
        "plan",
        type=Path,
        help="Path to the plan document that will be analyzed",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Optional JSON file containing plan metadata for the orchestrator",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        default=Path(".venv_atroz"),
        help="Location of the virtual environment to create/use",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="System Python executable used to bootstrap the virtualenv",
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        default=Path("requirements_atroz.txt"),
        help="Requirements file to install inside the virtual environment",
    )
    parser.add_argument(
        "--validate",
        choices=["tests", "api"],
        default="tests",
        help="Final validation step to perform after CHESS execution",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory where orchestrator outputs will be stored",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_arguments()
    plan_path = args.plan.resolve()

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan document not found: {plan_path}")

    requirements_path = (repo_root / args.requirements).resolve()
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

    venv_path = (repo_root / args.venv).resolve()
    output_dir = (repo_root / args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    venv_python = create_virtualenv(venv_path, args.python)
    install_dependencies(venv_python, requirements_path)
    dry_run_import(venv_python, repo_root)

    metadata = load_plan_metadata(args.metadata, plan_path)
    execute_chess_strategy(venv_python, repo_root, plan_path, metadata, output_dir)
    run_validation(venv_python, repo_root, args.validate)

    print("[bootstrap] All steps completed successfully")

if __name__ == "__main__":
    main()
