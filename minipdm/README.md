# MiniPDM Bootstrap

This directory contains an isolated prototype environment with a virtualenv and the minimal folder structure requested for contract-driven municipal policy analysis experiments.

## Layout
- `controls/`, `artifacts/`, `core/`, `mods/`, `tests/`, `config/`: Skeleton modules and storage points for future code and data.
- `.github/workflows/`: Placeholder for CI workflows.
- `.venv/`: Local Python virtual environment (ignored by git).

## Environment
Dependencies are pinned in `requirements.txt` and installed into `.venv`. Activate the environment via:

```bash
source .venv/bin/activate
```

To verify the bootstrap succeeded, run:

```bash
python -c "import yaml,pytest,jsonschema,networkx; print('OK_DEPS')"
```

The command should print `OK_DEPS` once the environment is healthy.
