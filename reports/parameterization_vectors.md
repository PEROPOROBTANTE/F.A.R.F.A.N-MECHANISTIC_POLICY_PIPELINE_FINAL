# Parameterization Vector Inventory (Phase 1)

Goal: identify every active configuration/parameter vector that bypasses the canonical
`canonical_method_catalogue_v2.json` so we can migrate them in later phases.

This document captures the vectors detected during the first repo-wide scan.
Each section explains **where** the vector lives, **how** parameters are injected today,
and **what needs to happen** so the catalogue becomes the unique source of truth.

---

## 1. `MethodConfigLoader` JSON spec (`CANONICAL_METHOD_PARAMETERIZATION_SPEC.json`)
* **Files:** `src/saaaaaa/utils/method_config_loader.py`, consumers in
  `src/saaaaaa/analysis/Analyzer_one.py` (e.g., `SemanticAnalyzer.__init__`),
  `tests/test_method_config_loader*.py`.
* **Mechanism:** loads a separate JSON spec with `methods[].parameters[].default`.
  Methods call `config_loader.get_method_parameter(...)` to retrieve values.
* **Risk:** duplicates the catalogue; any method using this loader ignores v2 defaults.
* **Action:** enumerate all call sites (`rg "get_method_parameter"`), add the corresponding
  parameters to the catalogue (if missing), and refactor the code to read directly from
  `canonical_method_catalogue_v2.json` (or better, inject values via dependency wiring).

## 2. Derek Beach YAML `ConfigLoader`
* **Files:** `src/saaaaaa/analysis/derek_beach.py` (`ConfigLoader` class around line 433)
  loading arbitrary YAML via `analysis.factory.load_yaml`.
* **Mechanism:** reads YAML file, validates with `CDAFConfigSchema`, exposes numerous
  nested defaults (`patterns`, `lexicons`, Bayesian thresholds, etc.).
* **Risk:** entire Derek Beach analysis stack (multiple classes across the file) depends
  on this YAML instead of the canonical catalogue; defaults are duplicated in `_load_default_config`.
* **Action:** build a mapping of each `config[...]` access to canonical method entries,
  port thresholds and structures into the catalogue (possibly as structured parameters),
  and deprecate the YAML loader.

## 3. Calibration Pillar Configs (`intrinsic_calibration.json`,
   `contextual_parametrization.json`, `fusion_specification.json`)
* **Files:** `src/saaaaaa/core/calibration/engine.py`, `core/calibration/layer_computers.py`,
  `core/calibration/validators.py`, `core/calibration/orchestrator.py`.
* **Mechanism:** calibration engine constructor loads these three JSON configs directly
  and each layer computer expects dictionaries derived from them.
* **Risk:** weights, thresholds, and mappings never touch the catalogue; they live in
  standalone config JSON files.
* **Action:** classify which values represent method parameters (fusion weights, contextual
  coefficients, etc.), add them to the catalogue, and replace direct JSON reads with a
  catalogue-backed loader (or embed these configs into the canonical spec so the engine
  consumes catalogue data structures exclusively).

## 4. Flux CLI / runtime toggles (Typer options + env fallbacks)
* **Files:** `src/saaaaaa/flux/cli.py`, `src/saaaaaa/flux/configs.py`.
* **Mechanism:** CLI function `run(...)` sets ~20 parameters using `typer.Option` defaults;
  `flux/configs.py` mirrors them using `os.getenv("FLUX_*")` overrides.
* **Risk:** CLI defaults are the primary source for ingestion/chunking/scoring parameters,
  independent of the catalogue.
* **Action:** add these CLI parameters to the catalogue (with method IDs for the Flux phases),
  generate a bridge that loads defaults from the catalogue at CLI bootstrap, and retire the
  hard-coded Typer/env defaults.

## 5. Executor/Orchestrator environment overrides
* **Files:** `src/saaaaaa/core/orchestrator/executor_config.py` (Typer options + `SAAAAAA_EXEC_*`
  env overrides), `src/saaaaaa/core/orchestrator/settings.py`, `src/saaaaaa/core/orchestrator/core.py`,
  `core/wiring/feature_flags.py`.
* **Mechanism:** numerous `os.getenv` calls for max tokens, temperature, retry counts, feature flags,
  environment secrets, etc.
* **Risk:** behaviour changes with environment variables without leaving a trace in the catalogue.
* **Action:** identify which of these env knobs correspond to method-level configuration
  (e.g., executor prompts, sampling behaviours) and move them into catalogue parameters;
  keep only truly infrastructure secrets (API keys) outside.

## 6. API server operational settings
* **Files:** `src/saaaaaa/api/api_server.py` (FastAPI config class) and `src/saaaaaa/core/orchestrator/settings.py`.
* **Mechanism:** uses `os.getenv('ATROZ_*')` for rate limiting, cache TTL, directories, etc.
* **Risk:** API endpoints may rely on defaults that differ from the catalogue or never made
  it into the method inventory (e.g., caching TTLs for evidence retrieval methods).
* **Action:** audit each API entry point, tie its tunable parameters to catalogue entries,
  and only keep infra-specific environment variables (ports, secrets) outside the catalogue.

## 7. Contextual toggles within processing pipelines
* **Files:** `src/saaaaaa/processing/policy_processor.py` (`REQUIRE_CONTRADICTION_MODULE` env flag),
  `src/saaaaaa/flux/phases.py` (policy unit IDs via env), `src/saaaaaa/utils/determinism_helpers.py`
  (seed derivation from env).
* **Mechanism:** pipeline stages gate behaviour via environment variables.
* **Risk:** toggles bypass catalogue governance.
* **Action:** promote these toggles to catalogue parameters so the orchestrator explicitly
  requests the behaviour and auditing can detect deviations.

---

### Next Steps
1. For each vector above, enumerate the exact methods touched (cross-reference with
   `canonical_method_catalogue_v2.json` using the file/line metadata).
2. Prioritize vectors with the largest surface area (e.g., calibration configs, Flux CLI).
3. Migrate parameters into the catalogue (adding rigorous default derivations) and
   refactor code to consume the canonical source only.
4. Update verification tests to ensure no code path reads from deprecated configs/envs.
