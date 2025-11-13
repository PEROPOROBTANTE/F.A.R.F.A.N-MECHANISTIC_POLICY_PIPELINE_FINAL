# Implementation Roadmap: Canonical Method Catalog with Rigorous Calibration

## Current State (After Phase 1)

✅ **Completed:**
- Catalog renamed to `complete_canonical_catalog.json`
- All references updated (5 files)
- Exhaustive search conducted and documented
- 590 methods in catalog
- 137 methods with calibration (23.2% coverage)

## Analysis Results

### Calibration Gap
- **Total methods**: 590 in catalog
- **Calibrated**: 137 (23.2%)
- **Need calibration**: 453 (76.8%)
- **Priority methods**: 123 (Bayesian, Executor, Analyzer, Extractor, Processor classes)

### Key Findings
1. **Calibration coverage is low**: Only 23% of methods calibrated
2. **29 orphaned calibrations**: Methods calibrated but not in catalog
3. **Priority gaps**: High-value methods (Bayesian, Executors) need calibration
4. **No layer assignments**: Current catalog lacks layer (Q/D/P/C/M) metadata
5. **No canonical notation**: Methods lack structured identification

## Implementation Phases

### Phase 2: Canonical Notation Integration ⏳ (Current)

**Objective**: Add canonical notation to catalog and calibration system

**Tasks:**
1. ✅ Define canonical notation specification
2. ⏳ Extend catalog JSON schema with:
   - `canonical_id` field
   - `layer` field (Q/D/P/C/M)
   - `flags` array (N/T/S/B/A/I/C)
   - `calibration_status` (CAL/REQ/OPT/DER/INS)
   - `calibration_params` object
3. ⏳ Create migration script to add canonical IDs to existing methods
4. ⏳ Update calibration_registry.py to support canonical notation

**Deliverables:**
- Canonical notation spec document ✅
- Updated catalog with canonical IDs
- Extended MethodCalibration dataclass
- Migration script

**Estimated Complexity**: HIGH (requires careful analysis of 590 methods)

### Phase 3: Calibration Registry Enhancement

**Objective**: Align calibration system with canonical catalog

**Tasks:**
1. Extend `MethodCalibration` to `CanonicalMethodCalibration`:
   - Add layer-specific parameters
   - Add congruence factors
   - Add layer weights (Q/D/P/C)
2. Implement YAML calibration loading:
   - Read from `config/calibraciones/calibration_registry.yaml`
   - Merge with Python hard-coded calibrations
   - Priority: YAML > Python (YAML overrides)
3. Update `calibration_context.py`:
   - Layer-aware calibration lookup
   - Context-based parameter adjustment
4. Update `analysis/factory.py`:
   - Add calibration file loading
   - Support multiple calibration sources

**Deliverables:**
- Extended calibration dataclass
- YAML loading mechanism
- Merged calibration registry
- Updated factory

**Estimated Complexity**: MEDIUM-HIGH

### Phase 4: Comprehensive Method Audit & Updates 🔴 (Complex)

**Objective**: Update catalog with ALL methods from system

**Sub-phases:**

#### 4a. Executor Methods
**Sources:**
- `executors/` directory
- Sophisticated methods in executor classes
- Method ensembles and chains

**Required Actions:**
- Identify all executor methods
- Assign to @C (Congruence) layer
- Determine calibration requirements
- Add to catalog

**Estimated Methods**: ~50-100

#### 4b. Pipeline Flow Methods
**Sources:**
- `aggregation.py` - Aggregation methods
- `scoring.py` - Scoring methods  
- `recommendation_engine.py` - Recommendation methods
- Concurrency/async methods

**Required Actions:**
- Identify all flow methods
- Assign to @M (Meta) or appropriate layer
- Determine calibration requirements
- Add to catalog

**Estimated Methods**: ~30-50

#### 4c. Missing Core Methods
**Sources:**
- Analysis modules
- Processing modules
- Validation modules

**Required Actions:**
- Cross-reference existing catalog with actual codebase
- Identify missing methods
- Add to catalog with proper notation

**Estimated Methods**: ~50-100

**Total Phase 4 Estimate**: 130-250 new methods

**Deliverables:**
- Comprehensive method inventory
- Updated catalog with all methods
- Layer assignments for all methods
- Gap analysis report

**Estimated Complexity**: VERY HIGH (requires codebase-wide analysis)

### Phase 5: Rigorous Calibration Development 🔴🔴 (Critical)

**Objective**: Develop academically-grounded calibrations for all required methods

**Mathematical Framework:**

#### Question Layer (@Q)
**Formula:**
```
Q_score = (E_score × w_q × ρ_base_slot) / (1 + λ_uncertainty)

Where:
- E_score: Evidence score (0-1)
- w_q: Question-specific weight
- ρ_base_slot: Base slot sensitivity (D1-Q1, D2-Q5, etc.)
- λ_uncertainty: Uncertainty penalty
```

**Academic Foundation:**
- Bayesian evidence theory (Jaynes, 2003)
- Information-theoretic scoring (Shannon, 1948)
- Evidential reasoning (Dempster-Shafer theory)

#### Dimension Layer (@D)
**Formula:**
```
D_score = (∑ᵢ₌₁ⁿ Q_scores_i × w_d_i × γ_coherence) / n

Where:
- w_d_i: Dimension-specific weights
- γ_coherence: Cross-question coherence factor (0-1)
- n: Number of questions in dimension
```

**Academic Foundation:**
- Multi-criteria decision analysis (Keeney & Raiffa, 1976)
- Aggregation theory (Grabisch et al., 2009)

#### Policy Area Layer (@P)
**Formula:**
```
P_score = (∑ⱼ₌₁ᵐ D_scores_j × w_p_j × ψ_integration) / m

Where:
- w_p_j: Policy area weights
- ψ_integration: Cross-area integration factor
- m: Number of dimensions in policy area
```

**Academic Foundation:**
- Policy coherence frameworks (Nilsson et al., 2012)
- Integrated assessment models (Rotmans & van Asselt, 1996)

#### Congruence Layer (@C) - MOST COMPLEX
**Formula:**
```
C_score = (M_score × w_ensemble × κ_congruence) + 
          (∑ₖ Mₖ_predecessor × αₖ) - 
          (∑ₗ Dₗ_disruption × βₗ)

Where:
- M_score: Individual method score
- w_ensemble: Ensemble weight for this method
- κ_congruence: Congruence factor (derived from compatibility matrix)
- αₖ: Influence coefficients from predecessor methods
- βₗ: Disruption penalties from incompatibilities
```

**Congruence Factor Calculation:**
```
κ_congruence = exp(-∑ᵢ (σᵢ² / τᵢ²))

Where:
- σᵢ: Standard deviation of method outputs
- τᵢ: Tolerance thresholds
```

**Academic Foundation:**
- Ensemble methods (Dietterich, 2000)
- Method stacking (Wolpert, 1992)
- Bayesian model averaging (Hoeting et al., 1999)
- Compatibility theory (Pearl, 2009)

#### Meta Layer (@M)
**Formula:**
```
M_score = f_agg(
    Q_layer × w_Q,
    D_layer × w_D,
    P_layer × w_P,
    C_layer × w_C
)

Where f_agg ∈ {WEIGHTED_AVG, GEOMETRIC_MEAN, HARMONIC_MEAN, OWA}
```

**Academic Foundation:**
- Aggregation operators (Beliakov et al., 2007)
- OWA operators (Yager, 1988)
- Fuzzy integrals (Grabisch, 1996)

**Tasks:**
1. **Literature Review** (Per Method Category):
   - Identify academic foundations
   - Extract parameter ranges
   - Validate against policy analysis best practices
   
2. **Parameter Derivation**:
   - Calculate evidence thresholds from domain expertise
   - Derive weights from importance analysis
   - Compute sensitivity factors from variance analysis
   
3. **Calibration Implementation**:
   - For each method requiring calibration (453 methods)
   - Define all layer-specific parameters
   - Implement mathematical formulas
   - Document academic justification

4. **Congruence Matrix Development**:
   - Identify all executor method ensembles
   - Build compatibility matrix
   - Calculate congruence factors
   - Implement disruption detection

**Deliverables:**
- Calibration specifications for 453 methods
- Academic reference document (50+ papers)
- Mathematical validation tests
- Congruence matrices for executor ensembles
- Python/YAML calibration implementations

**Estimated Complexity**: EXTREMELY HIGH
**Estimated Time**: 40-80 hours (assuming domain expertise)

**CRITICAL REQUIREMENTS:**
- NO default values without justification
- NO heuristic approximations
- NO simplifications without validation
- EVERY parameter must have academic backing
- ALL formulas must be mathematically rigorous

### Phase 6: Validation & Testing

**Objective**: Ensure calibration system works correctly

**Tasks:**
1. Unit tests for calibration loading
2. Integration tests for layer calculations
3. Validation against known test cases
4. Performance benchmarking
5. Documentation

**Deliverables:**
- Test suite (100+ tests)
- Validation report
- Performance analysis
- User documentation

**Estimated Complexity**: MEDIUM

## Implementation Strategy

### Immediate Actions (This Session)
1. ✅ Create canonical notation specification
2. ✅ Conduct gap analysis
3. ⏳ Create implementation roadmap
4. ⏳ Begin Phase 2: Add canonical IDs to sample methods

### Short-term (Next Sessions)
1. Complete Phase 2: Canonical notation integration
2. Begin Phase 3: Calibration registry enhancement
3. Start Phase 4a: Executor method audit

### Medium-term (Multi-session)
1. Complete Phase 3 and 4
2. Begin Phase 5: Rigorous calibration development
   - Start with priority methods
   - Work in batches of 20-30 methods
   - Validate each batch

### Long-term (Ongoing)
1. Complete Phase 5 calibration work
2. Phase 6 validation
3. Continuous refinement based on usage

## Risk Mitigation

### Risk 1: Incomplete Academic Foundation
**Mitigation**: 
- Work with domain experts
- Use established frameworks (Bayesian, MCDA)
- Document assumptions clearly

### Risk 2: Computational Complexity
**Mitigation**:
- Implement caching
- Use efficient algorithms
- Profile and optimize

### Risk 3: Parameter Tuning Difficulty
**Mitigation**:
- Start with conservative values
- Implement sensitivity analysis
- Use empirical validation

### Risk 4: Integration Challenges
**Mitigation**:
- Maintain backward compatibility
- Gradual rollout
- Comprehensive testing

## Success Criteria

1. **Coverage**: 100% of active methods have calibration (or explicit OPT status)
2. **Academic Rigor**: Every calibration parameter has documented justification
3. **Mathematical Validity**: All formulas are mathematically sound
4. **System Integration**: Calibration system integrates seamlessly
5. **Performance**: No significant performance degradation
6. **Documentation**: Complete specification and user guide

## Timeline Estimate

- **Phase 2**: 4-6 hours
- **Phase 3**: 6-8 hours
- **Phase 4**: 12-16 hours
- **Phase 5**: 40-80 hours (depends on expertise)
- **Phase 6**: 8-12 hours

**Total**: 70-122 hours

This is a **major refactoring** requiring sustained, focused effort across multiple sessions.
