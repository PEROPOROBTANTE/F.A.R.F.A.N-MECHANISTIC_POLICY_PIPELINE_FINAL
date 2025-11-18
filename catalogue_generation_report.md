================================================================
CATÁLOGO V2 - REPORTE DE GENERACIÓN
================================================================

ESTADÍSTICAS:
  Total methods scanned: 2301
  Methods successfully parsed: 2301 (100%)
  Methods with parsing errors: 0

  Methods with configurable params: 602 (26.2%)
  Total parameters: 4293
  Configurable parameters: 1361 (31.7%)

DISTRIBUCIÓN DE DEFAULTS:
  Literal values: 1163 (85.5%)
  Evaluated expressions: 0 (0.0%)
  Complex expressions: 198 (14.5%)

VERIFICACIONES:
  ✅ Test 1 (Consistency): PASS (0 errors)
  ✅ Test 2 (Source Match): PASS (0 mismatches in 50 samples)
  ✅ Test 3 (Coverage): PASS (26.2% methods, 31.7% params)
  ✅ Test 4 (Known Methods): PASS (12/12 known methods correct)

ARCHIVO GENERADO:
  Path: canonical_method_catalogue_v2.json
  Size: 3.9 MB
  Methods: 2301
  Valid JSON: ✅

CAMBIOS vs CATÁLOGO VIEJO:
  Methods added: 564
  Methods removed: 258
  Parameters updated: 1361
  Fields added per method: 4 (has_default, default_value, default_type, default_source)

TOP 10 METHODS WITH MOST CONFIGURABLES:
  1. src.saaaaaa.core.calibration.config.UnitLayerConfig.__init__: 54 configurable params
  2. src.saaaaaa.flux.cli.run: 22 configurable params
  3. src.saaaaaa.analysis.scoring.ScoringConfig.__init__: 18 configurable params
  4. src.saaaaaa.processing.policy_processor.ProcessorConfig.__init__: 17 configurable params
  5. src.saaaaaa.analysis.derek_beach.MetaNode.__init__: 14 configurable params
  6. src.saaaaaa.core.calibration.config.MetaLayerConfig.__init__: 13 configurable params
  7. src.saaaaaa.core.orchestrator.core.Orchestrator.__init__: 11 configurable params
  8. src.saaaaaa.optimization.rl_strategy.BanditArm.__init__: 11 configurable params
  9. src.saaaaaa.core.calibration.config.CalibrationSystemConfig.__init__: 10 configurable params
  10. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.__init__: 10 configurable params

MÉTODOS CON DEFAULTS COMPLEJOS (revisar):
  - src.saaaaaa.analysis.bayesian_multilevel_system.MacroLevelAnalysis.__init__: param="metadata" default="factory:dict"
  - src.saaaaaa.analysis.bayesian_multilevel_system.MesoLevelAnalysis.__init__: param="metadata" default="factory:dict"
  - src.saaaaaa.analysis.bayesian_multilevel_system.MicroLevelAnalysis.__init__: param="metadata" default="factory:dict"
  - src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.__init__: param="output_dir" default="Path('data/bayesian_outputs')"
  - src.saaaaaa.analysis.bayesian_multilevel_system.PeerContext.__init__: param="metadata" default="factory:dict"
  - src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.__init__: param="device" default="'cuda' if torch.cuda.is_available() else 'cpu'"
  - src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect: param="dimension" default="PolicyDimension.ESTRATEGICO"
  - src.saaaaaa.analysis.contradiction_deteccion.PolicyStatement.__init__: param="dependencies" default="factory:set"
  - src.saaaaaa.analysis.contradiction_deteccion.PolicyStatement.__init__: param="entities" default="factory:list"
  - src.saaaaaa.analysis.contradiction_deteccion.PolicyStatement.__init__: param="quantitative_claims" default="factory:list"
  - src.saaaaaa.analysis.contradiction_deteccion.PolicyStatement.__init__: param="temporal_markers" default="factory:list"
  - src.saaaaaa.analysis.derek_beach.MetaNode.__init__: param="audit_flags" default="factory:list"
  - src.saaaaaa.analysis.derek_beach.MetaNode.__init__: param="causal_justification" default="factory:list"
  - src.saaaaaa.analysis.derek_beach.MetaNode.__init__: param="contextual_risks" default="factory:list"
  - src.saaaaaa.analysis.financiero_viabilidad_tablas.CausalEdge.__init__: param="evidence_quotes" default="factory:list"
  - src.saaaaaa.analysis.financiero_viabilidad_tablas.CausalEffect.__init__: param="confounders_adjusted" default="factory:list"
  - src.saaaaaa.analysis.financiero_viabilidad_tablas.CausalEffect.__init__: param="mediating_paths" default="factory:list"
  - src.saaaaaa.analysis.macro_prompts.BayesianPortfolio.__init__: param="metadata" default="factory:dict"
  - src.saaaaaa.analysis.macro_prompts.ContradictionReport.__init__: param="metadata" default="factory:dict"
  - src.saaaaaa.analysis.macro_prompts.CoverageAnalysis.__init__: param="metadata" default="factory:dict"

================================================================
RESULTADO: ✅ CATÁLOGO GENERADO CON ÉXITO
================================================================
