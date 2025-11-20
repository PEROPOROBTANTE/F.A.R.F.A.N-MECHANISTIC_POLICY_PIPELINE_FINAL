================================================================================
FASE 5.1: HARDCODED VALUES SCAN REPORT
================================================================================

Total hardcoded values found: 579

Type_A_Scores: 2 occurrences
Type_B_Thresholds: 81 occurrences
Type_C_Weights: 8 occurrences
Type_D_Constants: 388 occurrences
Uncategorized: 100 occurrences

================================================================================


================================================================================
Type_A_Scores: 2 occurrences
================================================================================


File: src/saaaaaa/core/calibration/unit_layer.py
--------------------------------------------------------------------------------
  Line  214: 0.000000
            Type: assignment
            Variable: score
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  265: 0.000000
            Type: assignment
            Variable: total_struct_score
            Context: UnitLayerEvaluator._compute_indicator_quality


================================================================================
Type_B_Thresholds: 81 occurrences
================================================================================


File: src/saaaaaa/core/calibration/base_layer.py
--------------------------------------------------------------------------------
  Line   60: 0.000001
            Type: comparison
            Variable: N/A
            Context: BaseLayerEvaluator.__init__
            Operator: Gt

  Line  182: 0.800000
            Type: comparison
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate
            Operator: GtE

  Line  184: 0.600000
            Type: comparison
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate
            Operator: GtE

  Line  186: 0.400000
            Type: comparison
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate
            Operator: GtE

  Line  259: 0.000000
            Type: comparison
            Variable: N/A
            Context: BaseLayerEvaluator.get_coverage_stats
            Operator: Gt


File: src/saaaaaa/core/calibration/chain_layer.py
--------------------------------------------------------------------------------
  Line  106: 0.000000
            Type: comparison
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate
            Operator: Gt

  Line  108: 0.500000
            Type: comparison
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate
            Operator: Gt


File: src/saaaaaa/core/calibration/choquet_aggregator.py
--------------------------------------------------------------------------------
  Line  170: 1.000000
            Type: comparison
            Variable: N/A
            Context: ChoquetAggregator.aggregate
            Operator: LtE


File: src/saaaaaa/core/calibration/compatibility.py
--------------------------------------------------------------------------------
  Line  264: 1.000000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_question_layer
            Operator: Eq

  Line  266: 0.700000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_question_layer
            Operator: Eq

  Line  268: 0.300000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_question_layer
            Operator: Eq

  Line  300: 1.000000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_dimension_layer
            Operator: Eq

  Line  302: 0.700000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_dimension_layer
            Operator: Eq

  Line  304: 0.300000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_dimension_layer
            Operator: Eq

  Line  336: 1.000000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_policy_layer
            Operator: Eq

  Line  338: 0.700000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_policy_layer
            Operator: Eq

  Line  340: 0.300000
            Type: comparison
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_policy_layer
            Operator: Eq


File: src/saaaaaa/core/calibration/config.py
--------------------------------------------------------------------------------
  Line  151: 0.000001
            Type: comparison
            Variable: N/A
            Context: UnitLayerConfig.__post_init__
            Operator: Gt

  Line  160: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerConfig.__post_init__
            Operator: Lt

  Line  165: 0.000001
            Type: comparison
            Variable: N/A
            Context: UnitLayerConfig.__post_init__
            Operator: Gt

  Line  172: 0.000001
            Type: comparison
            Variable: N/A
            Context: UnitLayerConfig.__post_init__
            Operator: Gt

  Line  179: 0.000001
            Type: comparison
            Variable: N/A
            Context: UnitLayerConfig.__post_init__
            Operator: Gt

  Line  187: 1.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerConfig.__post_init__
            Operator: LtE

  Line  274: 0.000001
            Type: comparison
            Variable: N/A
            Context: MetaLayerConfig.__post_init__
            Operator: Gt

  Line  346: 0.000001
            Type: comparison
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__
            Operator: Gt

  Line  357: 0.000000
            Type: comparison
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__
            Operator: Lt

  Line  361: 0.000000
            Type: comparison
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__
            Operator: Lt


File: src/saaaaaa/core/calibration/congruence_layer.py
--------------------------------------------------------------------------------
  Line  181: 0.000000
            Type: comparison
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence
            Operator: Eq


File: src/saaaaaa/core/calibration/data_structures.py
--------------------------------------------------------------------------------
  Line   65: 1.000000
            Type: comparison
            Variable: N/A
            Context: LayerScore.__post_init__
            Operator: LtE

  Line  129: 1.000000
            Type: comparison
            Variable: N/A
            Context: ContextTuple.__post_init__
            Operator: LtE

  Line  374: 1.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationResult.__post_init__
            Operator: LtE

  Line  381: 0.000001
            Type: comparison
            Variable: N/A
            Context: CalibrationResult.__post_init__
            Operator: Gt

  Line  390: 1.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationResult.__post_init__
            Operator: LtE


File: src/saaaaaa/core/calibration/engine.py
--------------------------------------------------------------------------------
  Line  144: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights
            Operator: Lt

  Line  151: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights
            Operator: Lt

  Line  445: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationEngine._apply_fusion
            Operator: Lt

  Line  445: 1.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationEngine._apply_fusion
            Operator: Gt


File: src/saaaaaa/core/calibration/intrinsic_loader.py
--------------------------------------------------------------------------------
  Line  125: 0.000001
            Type: comparison
            Variable: N/A
            Context: IntrinsicScoreLoader._ensure_loaded
            Operator: Gt


File: src/saaaaaa/core/calibration/layer_computers.py
--------------------------------------------------------------------------------
  Line   44: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_base_layer
            Operator: LtE

  Line  116: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_unit_layer
            Operator: LtE

  Line  144: 0.000000
            Type: comparison
            Variable: N/A
            Context: compute_unit_layer
            Operator: Lt

  Line  144: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_unit_layer
            Operator: Gt

  Line  159: 0.000000
            Type: comparison
            Variable: N/A
            Context: compute_unit_layer
            Operator: Lt

  Line  159: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_unit_layer
            Operator: Gt

  Line  217: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_question_layer
            Operator: Eq

  Line  341: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_meta_layer
            Operator: Eq

  Line  359: 1.000000
            Type: comparison
            Variable: N/A
            Context: compute_meta_layer
            Operator: Eq


File: src/saaaaaa/core/calibration/meta_layer.py
--------------------------------------------------------------------------------
  Line  135: 1.000000
            Type: comparison
            Variable: N/A
            Context: MetaLayerEvaluator._compute_transparency
            Operator: Eq

  Line  162: 0.000000
            Type: comparison
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance
            Operator: Gt

  Line  171: 1.000000
            Type: comparison
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance
            Operator: Eq

  Line  193: 0.000000
            Type: comparison
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost
            Operator: Lt


File: src/saaaaaa/core/calibration/unit_layer.py
--------------------------------------------------------------------------------
  Line  101: 0.850000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate
            Operator: GtE

  Line  103: 0.700000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate
            Operator: GtE

  Line  105: 0.500000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate
            Operator: GtE

  Line  162: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance
            Operator: Eq

  Line  162: 1.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance
            Operator: Eq

  Line  240: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections
            Operator: Gt

  Line  246: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections
            Operator: Gt

  Line  344: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness
            Operator: Gt

  Line  386: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components
            Operator: Eq

  Line  386: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components
            Operator: Eq

  Line  386: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components
            Operator: Eq

  Line  386: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components
            Operator: Eq

  Line  409: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty
            Operator: Gt

  Line  431: 0.000000
            Type: comparison
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty
            Operator: Gt


File: src/saaaaaa/core/calibration/validator.py
--------------------------------------------------------------------------------
  Line   95: 0.000000
            Type: comparison
            Variable: N/A
            Context: ValidationReport.pass_rate
            Operator: Eq

  Line  360: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors
            Operator: Eq

  Line  363: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors
            Operator: Eq

  Line  430: 0.700000
            Type: assignment
            Variable: default_threshold
            Context: CalibrationValidator._get_threshold_for_method


File: src/saaaaaa/core/calibration/validators.py
--------------------------------------------------------------------------------
  Line   96: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights
            Operator: Lt

  Line  102: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights
            Operator: Lt

  Line  120: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights
            Operator: Eq

  Line  152: 0.990000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality
            Operator: Lt

  Line  162: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality
            Operator: Eq

  Line  183: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration
            Operator: Gt

  Line  199: 1.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration
            Operator: LtE

  Line  204: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration
            Operator: Eq

  Line  254: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_config_files
            Operator: Eq

  Line  277: 1.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness
            Operator: LtE

  Line  281: 1.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness
            Operator: LtE

  Line  284: 0.000000
            Type: comparison
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness
            Operator: Eq


================================================================================
Type_C_Weights: 8 occurrences
================================================================================


File: src/saaaaaa/core/calibration/base_layer.py
--------------------------------------------------------------------------------
  Line   36: 0.400000
            Type: assignment
            Variable: THEORY_WEIGHT
            Context: BaseLayerEvaluator

  Line   37: 0.400000
            Type: assignment
            Variable: IMPL_WEIGHT
            Context: BaseLayerEvaluator

  Line   38: 0.200000
            Type: assignment
            Variable: DEPLOY_WEIGHT
            Context: BaseLayerEvaluator


File: src/saaaaaa/core/calibration/intrinsic_loader.py
--------------------------------------------------------------------------------
  Line   53: 0.400000
            Type: assignment
            Variable: DEFAULT_W_THEORY
            Context: IntrinsicScoreLoader

  Line   54: 0.350000
            Type: assignment
            Variable: DEFAULT_W_IMPL
            Context: IntrinsicScoreLoader

  Line   55: 0.250000
            Type: assignment
            Variable: DEFAULT_W_DEPLOY
            Context: IntrinsicScoreLoader


File: src/saaaaaa/core/calibration/unit_layer.py
--------------------------------------------------------------------------------
  Line  206: 0.000000
            Type: assignment
            Variable: total_weight
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  207: 0.000000
            Type: assignment
            Variable: weighted_score
            Context: UnitLayerEvaluator._compute_mandatory_sections


================================================================================
Type_D_Constants: 388 occurrences
================================================================================


File: src/saaaaaa/core/calibration/base_layer.py
--------------------------------------------------------------------------------
  Line   41: 0.100000
            Type: assignment
            Variable: UNCALIBRATED_PENALTY
            Context: BaseLayerEvaluator

  Line   60: 1.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.__init__

  Line   95: 0.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator._load

  Line   96: 0.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator._load

  Line   97: 0.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator._load

  Line  164: 1.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate

  Line  256: 0.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.get_coverage_stats

  Line  256: 1.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.get_coverage_stats

  Line  259: 0.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.get_coverage_stats

  Line  264: 0.000000
            Type: assignment
            Variable: avg_theory
            Context: BaseLayerEvaluator.get_coverage_stats

  Line  264: 0.000000
            Type: assignment
            Variable: avg_impl
            Context: BaseLayerEvaluator.get_coverage_stats

  Line  264: 0.000000
            Type: assignment
            Variable: avg_deploy
            Context: BaseLayerEvaluator.get_coverage_stats

  Line  264: 0.000000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.get_coverage_stats


File: src/saaaaaa/core/calibration/chain_layer.py
--------------------------------------------------------------------------------
  Line   52: 0.000000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line   79: 0.000000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  106: 0.000000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  108: 0.500000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  114: 1.000000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  115: 1.000000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  159: 0.000000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.compute_chain_quality


File: src/saaaaaa/core/calibration/choquet_aggregator.py
--------------------------------------------------------------------------------
  Line   92: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line   96: 0.000000
            Type: assignment
            Variable: linear_contribution
            Context: ChoquetAggregator.aggregate

  Line   96: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  101: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  126: 0.000000
            Type: assignment
            Variable: interaction_contribution
            Context: ChoquetAggregator.aggregate

  Line  126: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  137: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  138: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  140: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  141: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  170: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  170: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate

  Line  203: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregator.aggregate


File: src/saaaaaa/core/calibration/compatibility.py
--------------------------------------------------------------------------------
  Line  130: 0.000000
            Type: constant
            Variable: N/A
            Context: CompatibilityRegistry.validate_anti_universality

  Line  131: 0.000000
            Type: constant
            Variable: N/A
            Context: CompatibilityRegistry.validate_anti_universality

  Line  132: 0.000000
            Type: constant
            Variable: N/A
            Context: CompatibilityRegistry.validate_anti_universality

  Line  264: 1.000000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_question_layer

  Line  300: 1.000000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_dimension_layer

  Line  336: 1.000000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_policy_layer


File: src/saaaaaa/core/calibration/config.py
--------------------------------------------------------------------------------
  Line   20: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   52: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   53: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   54: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   60: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   67: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   73: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   77: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  101: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  151: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  160: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  165: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  172: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  179: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  187: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  187: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  224: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  240: 0.500000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  247: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  248: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  249: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  254: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  255: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  256: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  262: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  274: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig.__post_init__

  Line  280: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  346: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__

  Line  352: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__

  Line  357: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__

  Line  361: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__

  Line  374: 0.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.compute_hash

  Line  374: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.compute_hash

  Line  379: 1.000000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.compute_hash

  Line  383: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig

  Line  411: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig

  Line  416: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig

  Line  419: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig

  Line  420: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig

  Line  421: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig

  Line  454: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig.compute_system_hash


File: src/saaaaaa/core/calibration/congruence_layer.py
--------------------------------------------------------------------------------
  Line   58: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator.evaluate

  Line   60: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator.evaluate

  Line   61: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator.evaluate

  Line   63: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator.evaluate

  Line   64: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator.evaluate

  Line  121: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  128: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  133: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  136: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  139: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  139: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  146: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence

  Line  162: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  170: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  173: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  174: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  176: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  181: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  183: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_semantic_congruence

  Line  222: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_fusion_validity

  Line  228: 0.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_fusion_validity

  Line  241: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_fusion_validity

  Line  243: 1.000000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_fusion_validity

  Line  254: 0.500000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_fusion_validity


File: src/saaaaaa/core/calibration/data_structures.py
--------------------------------------------------------------------------------
  Line   34: 1.000000
            Type: constant
            Variable: N/A
            Context: LayerScore

  Line   65: 0.000000
            Type: constant
            Variable: N/A
            Context: LayerScore.__post_init__

  Line   65: 1.000000
            Type: constant
            Variable: N/A
            Context: LayerScore.__post_init__

  Line   81: 1.000000
            Type: constant
            Variable: N/A
            Context: ContextTuple

  Line  129: 0.000000
            Type: constant
            Variable: N/A
            Context: ContextTuple.__post_init__

  Line  129: 1.000000
            Type: constant
            Variable: N/A
            Context: ContextTuple.__post_init__

  Line  144: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationSubject

  Line  191: 1.000000
            Type: constant
            Variable: N/A
            Context: CompatibilityMapping

  Line  253: 1.000000
            Type: constant
            Variable: N/A
            Context: CompatibilityMapping.check_anti_universality

  Line  275: 1.000000
            Type: constant
            Variable: N/A
            Context: InteractionTerm

  Line  316: 0.000000
            Type: constant
            Variable: N/A
            Context: InteractionTerm.compute

  Line  317: 0.000000
            Type: constant
            Variable: N/A
            Context: InteractionTerm.compute

  Line  330: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationResult

  Line  374: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationResult.__post_init__

  Line  374: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationResult.__post_init__

  Line  390: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationResult.__post_init__

  Line  390: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationResult.__post_init__


File: src/saaaaaa/core/calibration/engine.py
--------------------------------------------------------------------------------
  Line  136: 0.000000
            Type: assignment
            Variable: TOLERANCE
            Context: CalibrationEngine._validate_fusion_weights

  Line  144: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights

  Line  151: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights

  Line  159: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights

  Line  162: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights

  Line  176: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_config_hash

  Line  177: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_config_hash

  Line  178: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_config_hash

  Line  197: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_graph_hash

  Line  300: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._detect_interplay

  Line  358: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_layer_scores

  Line  359: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_layer_scores

  Line  360: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_layer_scores

  Line  361: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_layer_scores

  Line  362: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_layer_scores

  Line  363: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._compute_layer_scores

  Line  404: 0.000000
            Type: assignment
            Variable: linear_sum
            Context: CalibrationEngine._apply_fusion

  Line  404: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._apply_fusion

  Line  419: 0.000000
            Type: assignment
            Variable: interaction_sum
            Context: CalibrationEngine._apply_fusion

  Line  419: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._apply_fusion

  Line  445: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._apply_fusion

  Line  445: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._apply_fusion

  Line  560: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine.calibrate


File: src/saaaaaa/core/calibration/intrinsic_loader.py
--------------------------------------------------------------------------------
  Line   71: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader.__init__

  Line  125: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._ensure_loaded

  Line  168: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._ensure_loaded

  Line  174: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_statistics

  Line  175: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_statistics

  Line  176: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_statistics

  Line  182: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_statistics

  Line  184: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_statistics

  Line  186: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_statistics

  Line  197: 0.000000
            Type: assignment
            Variable: warning_count
            Context: IntrinsicScoreLoader._validate_computed_methods

  Line  197: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._validate_computed_methods

  Line  203: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._validate_computed_methods

  Line  230: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_intrinsic_score

  Line  231: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_intrinsic_score

  Line  232: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_intrinsic_score

  Line  242: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_intrinsic_score

  Line  242: 1.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_intrinsic_score

  Line  252: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._compute_intrinsic_score

  Line  254: 0.500000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader.get_score

  Line  347: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader.is_calibrated

  Line  364: 0.000000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader.is_excluded


File: src/saaaaaa/core/calibration/layer_computers.py
--------------------------------------------------------------------------------
  Line   44: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_base_layer

  Line   44: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_base_layer

  Line   81: 0.000000
            Type: assignment
            Variable: has_hard_mismatch
            Context: compute_chain_layer

  Line   81: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_chain_layer

  Line   82: 0.000000
            Type: assignment
            Variable: has_soft_violation
            Context: compute_chain_layer

  Line   82: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_chain_layer

  Line   83: 0.000000
            Type: assignment
            Variable: has_warnings
            Context: compute_chain_layer

  Line   83: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_chain_layer

  Line   86: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_chain_layer

  Line   89: 1.000000
            Type: assignment
            Variable: has_hard_mismatch
            Context: compute_chain_layer

  Line   89: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_chain_layer

  Line  116: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  116: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  124: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  133: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  140: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  144: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  144: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  155: 0.500000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  156: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  159: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  159: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  217: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_question_layer

  Line  252: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_dimension_layer

  Line  305: 1.000000
            Type: assignment
            Variable: c_sem
            Context: compute_interplay_layer

  Line  305: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_interplay_layer

  Line  330: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  331: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  332: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  341: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  348: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  349: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  350: 0.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer

  Line  359: 1.000000
            Type: constant
            Variable: N/A
            Context: compute_meta_layer


File: src/saaaaaa/core/calibration/layer_requirements.py
--------------------------------------------------------------------------------
  Line  323: 0.000000
            Type: constant
            Variable: N/A
            Context: LayerRequirementsResolver.should_skip_layer

  Line  358: 0.000000
            Type: constant
            Variable: N/A
            Context: LayerRequirementsResolver.get_layer_summary

  Line  359: 1.000000
            Type: constant
            Variable: N/A
            Context: LayerRequirementsResolver.get_layer_summary


File: src/saaaaaa/core/calibration/meta_layer.py
--------------------------------------------------------------------------------
  Line   44: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator.evaluate

  Line   45: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator.evaluate

  Line   46: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator.evaluate

  Line   47: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator.evaluate

  Line  132: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_transparency

  Line  135: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_transparency

  Line  138: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_transparency

  Line  162: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance

  Line  168: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance

  Line  171: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance

  Line  174: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance

  Line  191: 0.500000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost

  Line  193: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost

  Line  195: 0.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost

  Line  198: 1.000000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost

  Line  209: 0.500000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost


File: src/saaaaaa/core/calibration/orchestrator.py
--------------------------------------------------------------------------------
  Line  217: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate

  Line  223: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate

  Line  342: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate

  Line  343: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate

  Line  344: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate

  Line  345: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate


File: src/saaaaaa/core/calibration/parameter_loader.py
--------------------------------------------------------------------------------
  Line   60: 0.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.__init__

  Line  121: 1.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader._ensure_loaded

  Line  142: 1.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  148: 0.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  155: 0.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  268: 1.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.executor_requires_all_layers

  Line  270: 1.000000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.executor_requires_all_layers


File: src/saaaaaa/core/calibration/pdt_structure.py
--------------------------------------------------------------------------------
  Line   71: 0.000000
            Type: constant
            Variable: N/A
            Context: PDTStructure

  Line   88: 0.000000
            Type: constant
            Variable: N/A
            Context: PDTStructure


File: src/saaaaaa/core/calibration/unit_layer.py
--------------------------------------------------------------------------------
  Line   43: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line   62: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line   77: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line   86: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line   98: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line  105: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line  122: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  124: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  125: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  131: 0.000000
            Type: assignment
            Variable: H
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  131: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  133: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  136: 1.000000
            Type: assignment
            Variable: H
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  136: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  138: 0.500000
            Type: assignment
            Variable: H
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  138: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  140: 0.000000
            Type: assignment
            Variable: H
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  140: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  144: 0.000000
            Type: assignment
            Variable: inversions
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  144: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  156: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  160: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  162: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  162: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  162: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  162: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  162: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_structural_compliance

  Line  197: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  202: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  206: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  207: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  212: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  214: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  217: 0.000000
            Type: assignment
            Variable: checks_passed
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  217: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  218: 0.000000
            Type: assignment
            Variable: checks_total
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  218: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  221: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  222: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  223: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  226: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  227: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  228: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  231: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  232: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  233: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  236: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  237: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  238: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  240: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  240: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  242: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  246: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  246: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_mandatory_sections

  Line  252: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  254: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  255: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  256: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  257: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  265: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  267: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  268: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  272: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  280: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  281: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  287: 0.000000
            Type: assignment
            Variable: linked_count
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  287: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  296: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  301: 0.000000
            Type: assignment
            Variable: logic_violations
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  301: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  309: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  312: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  314: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_indicator_quality

  Line  331: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  331: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  336: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  337: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  343: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  344: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  344: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  349: 0.000000
            Type: assignment
            Variable: violations
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  349: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  351: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  354: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  356: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  359: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  359: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  360: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  360: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  362: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  364: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_ppi_completeness

  Line  386: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  386: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  386: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  386: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  387: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  388: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  388: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  388: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  388: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  401: 0.000000
            Type: assignment
            Variable: placeholder_count
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  401: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  402: 0.000000
            Type: assignment
            Variable: total_fields
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  402: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  405: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  407: 1.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  409: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  409: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  411: 0.500000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  416: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  418: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  429: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  430: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  431: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  431: 0.000000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty


File: src/saaaaaa/core/calibration/validator.py
--------------------------------------------------------------------------------
  Line   95: 0.000000
            Type: constant
            Variable: N/A
            Context: ValidationReport.pass_rate

  Line   96: 0.000000
            Type: constant
            Variable: N/A
            Context: ValidationReport.pass_rate

  Line  206: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_method

  Line  207: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_method

  Line  289: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_method

  Line  295: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_method

  Line  328: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  329: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  353: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  354: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  355: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  356: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  360: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  363: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors


File: src/saaaaaa/core/calibration/validators.py
--------------------------------------------------------------------------------
  Line   59: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_layer_completeness

  Line   65: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_layer_completeness

  Line   96: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights

  Line  102: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights

  Line  112: 0.000000
            Type: assignment
            Variable: tolerance
            Context: CalibrationValidator.validate_fusion_weights

  Line  113: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights

  Line  120: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights

  Line  149: 1.000000
            Type: assignment
            Variable: all_policies_maximal
            Context: CalibrationValidator.validate_anti_universality

  Line  149: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality

  Line  152: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality

  Line  153: 0.000000
            Type: assignment
            Variable: all_policies_maximal
            Context: CalibrationValidator.validate_anti_universality

  Line  153: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality

  Line  162: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality

  Line  181: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  181: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  181: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  183: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  199: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  199: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  204: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration

  Line  254: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_config_files

  Line  277: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness

  Line  277: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness

  Line  281: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness

  Line  281: 1.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness

  Line  284: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_boundedness


================================================================================
Uncategorized: 100 occurrences
================================================================================


File: src/saaaaaa/core/calibration/base_layer.py
--------------------------------------------------------------------------------
  Line   36: 0.400000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator

  Line   37: 0.400000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator

  Line   38: 0.200000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator

  Line   41: 0.100000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator

  Line   60: 0.000001
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.__init__

  Line  182: 0.800000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate

  Line  184: 0.600000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate

  Line  186: 0.400000
            Type: constant
            Variable: N/A
            Context: BaseLayerEvaluator.evaluate


File: src/saaaaaa/core/calibration/chain_layer.py
--------------------------------------------------------------------------------
  Line   91: 0.300000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  109: 0.600000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate

  Line  111: 0.800000
            Type: constant
            Variable: N/A
            Context: ChainLayerEvaluator.evaluate


File: src/saaaaaa/core/calibration/compatibility.py
--------------------------------------------------------------------------------
  Line   94: 0.100000
            Type: constant
            Variable: N/A
            Context: CompatibilityRegistry.get

  Line  107: 0.900000
            Type: constant
            Variable: N/A
            Context: CompatibilityRegistry.validate_anti_universality

  Line  266: 0.700000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_question_layer

  Line  268: 0.300000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_question_layer

  Line  302: 0.700000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_dimension_layer

  Line  304: 0.300000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_dimension_layer

  Line  338: 0.700000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_policy_layer

  Line  340: 0.300000
            Type: constant
            Variable: N/A
            Context: ContextualLayerEvaluator.evaluate_policy_layer


File: src/saaaaaa/core/calibration/config.py
--------------------------------------------------------------------------------
  Line   39: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   40: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   41: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   42: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   59: 0.100000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   61: 0.020000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   62: 0.300000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   68: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   69: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line   76: 0.800000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  109: 0.400000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  110: 0.300000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  111: 0.300000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  114: 0.700000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  121: 0.850000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  133: 0.200000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  134: 0.400000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  135: 0.400000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  138: 0.700000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  141: 0.800000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  144: 0.010000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  145: 0.800000
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig

  Line  151: 0.000001
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  165: 0.000001
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  172: 0.000001
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  179: 0.000001
            Type: constant
            Variable: N/A
            Context: UnitLayerConfig.__post_init__

  Line  241: 0.400000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  242: 0.100000
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig

  Line  274: 0.000001
            Type: constant
            Variable: N/A
            Context: MetaLayerConfig.__post_init__

  Line  307: 0.122951
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  308: 0.098361
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  309: 0.081967
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  310: 0.065574
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  311: 0.049180
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  312: 0.081967
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  313: 0.065574
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  314: 0.034426
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  322: 0.150000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  323: 0.120000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  324: 0.080000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  325: 0.050000
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig

  Line  346: 0.000001
            Type: constant
            Variable: N/A
            Context: ChoquetAggregationConfig.__post_init__

  Line  412: 0.900000
            Type: constant
            Variable: N/A
            Context: CalibrationSystemConfig


File: src/saaaaaa/core/calibration/congruence_layer.py
--------------------------------------------------------------------------------
  Line  142: 0.800000
            Type: constant
            Variable: N/A
            Context: CongruenceLayerEvaluator._compute_scale_congruence


File: src/saaaaaa/core/calibration/data_structures.py
--------------------------------------------------------------------------------
  Line  223: 0.100000
            Type: constant
            Variable: N/A
            Context: CompatibilityMapping.get_question_score

  Line  231: 0.100000
            Type: constant
            Variable: N/A
            Context: CompatibilityMapping.get_dimension_score

  Line  239: 0.100000
            Type: constant
            Variable: N/A
            Context: CompatibilityMapping.get_policy_score

  Line  241: 0.900000
            Type: constant
            Variable: N/A
            Context: CompatibilityMapping.check_anti_universality

  Line  381: 0.000001
            Type: constant
            Variable: N/A
            Context: CalibrationResult.__post_init__


File: src/saaaaaa/core/calibration/engine.py
--------------------------------------------------------------------------------
  Line  136: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationEngine._validate_fusion_weights


File: src/saaaaaa/core/calibration/intrinsic_loader.py
--------------------------------------------------------------------------------
  Line   53: 0.400000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader

  Line   54: 0.350000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader

  Line   55: 0.250000
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader

  Line  125: 0.000001
            Type: constant
            Variable: N/A
            Context: IntrinsicScoreLoader._ensure_loaded


File: src/saaaaaa/core/calibration/layer_computers.py
--------------------------------------------------------------------------------
  Line  138: 0.300000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  141: 0.600000
            Type: constant
            Variable: N/A
            Context: compute_unit_layer

  Line  279: 0.900000
            Type: constant
            Variable: N/A
            Context: compute_policy_layer


File: src/saaaaaa/core/calibration/meta_layer.py
--------------------------------------------------------------------------------
  Line  134: 0.700000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_transparency

  Line  136: 0.400000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_transparency

  Line  170: 0.660000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance

  Line  172: 0.330000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_governance

  Line  200: 0.800000
            Type: constant
            Variable: N/A
            Context: MetaLayerEvaluator._compute_cost


File: src/saaaaaa/core/calibration/orchestrator.py
--------------------------------------------------------------------------------
  Line  291: 0.100000
            Type: constant
            Variable: N/A
            Context: CalibrationOrchestrator.calibrate


File: src/saaaaaa/core/calibration/parameter_loader.py
--------------------------------------------------------------------------------
  Line  145: 0.850000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  146: 0.700000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  147: 0.550000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  152: 0.850000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  153: 0.700000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  154: 0.550000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_quality_thresholds

  Line  158: 0.700000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_validation_threshold_for_role

  Line  199: 0.700000
            Type: constant
            Variable: N/A
            Context: MethodParameterLoader.get_executor_threshold


File: src/saaaaaa/core/calibration/unit_layer.py
--------------------------------------------------------------------------------
  Line  101: 0.850000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line  103: 0.700000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator.evaluate

  Line  383: 0.250000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._aggregate_components

  Line  421: 0.300000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty

  Line  434: 0.200000
            Type: constant
            Variable: N/A
            Context: UnitLayerEvaluator._compute_gaming_penalty


File: src/saaaaaa/core/calibration/validator.py
--------------------------------------------------------------------------------
  Line  366: 0.800000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_plan_executors

  Line  430: 0.700000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator._get_threshold_for_method


File: src/saaaaaa/core/calibration/validators.py
--------------------------------------------------------------------------------
  Line  112: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_fusion_weights

  Line  152: 0.990000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_anti_universality

  Line  183: 0.000000
            Type: constant
            Variable: N/A
            Context: CalibrationValidator.validate_intrinsic_calibration
