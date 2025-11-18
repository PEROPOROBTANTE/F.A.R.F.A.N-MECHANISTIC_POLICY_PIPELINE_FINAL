"""
Unit Layer (@u) - PRODUCTION IMPLEMENTATION.

Evaluates PDT quality through 4 components: S, M, I, P.
"""
import logging

from .config import UnitLayerConfig
from .data_structures import LayerID, LayerScore
from .pdt_structure import PDTStructure

logger = logging.getLogger(__name__)


class UnitLayerEvaluator:
    """
    Evaluates Unit Layer (@u) - PDT quality.

    PRODUCTION IMPLEMENTATION - All scores are data-driven.
    """

    # Mandatory blocks required for PDT compliance
    MANDATORY_BLOCKS = ["Diagnóstico", "Parte Estratégica", "PPI", "Seguimiento"]

    def __init__(self, config: UnitLayerConfig) -> None:
        self.config = config

    def evaluate(self, pdt: PDTStructure) -> LayerScore:
        """
        Production implementation - computes S, M, I, P from PDT data.

        THIS IS NOT A STUB - all scores are data-driven.
        """
        logger.info("unit_layer_evaluation_start", extra={"tokens": pdt.total_tokens})

        # Step 1: Compute S (Structural Compliance)
        S = self._compute_structural_compliance(pdt)
        logger.info("S_computed", extra={"S": S})

        # Step 2: Check hard gate for S
        if self.config.min_structural_compliance > S:
            return LayerScore(
                layer=LayerID.UNIT,
                score=0.0,
                components={"S": S, "gate_failure": "structural"},
                rationale=f"HARD GATE: S={S:.2f} < {self.config.min_structural_compliance}",
                metadata={"gate": "structural", "threshold": self.config.min_structural_compliance}
            )

        # Step 3: Compute M (Mandatory Sections)
        M = self._compute_mandatory_sections(pdt)
        logger.info("M_computed", extra={"M": M})

        # Step 4: Compute I (Indicator Quality)
        I_components = self._compute_indicator_quality(pdt)
        I = I_components["I_total"]
        logger.info("I_computed", extra={"I": I})

        # Step 5: Check hard gate for I_struct
        if I_components["I_struct"] < self.config.i_struct_hard_gate:
            return LayerScore(
                layer=LayerID.UNIT,
                score=0.0,
                components={"S": S, "M": M, "I_struct": I_components["I_struct"]},
                rationale=f"HARD GATE: I_struct={I_components['I_struct']:.2f} < {self.config.i_struct_hard_gate}",
                metadata={"gate": "indicator_structure"}
            )

        # Step 6: Compute P (PPI Completeness)
        P_components = self._compute_ppi_completeness(pdt)
        P = P_components["P_total"]
        logger.info("P_computed", extra={"P": P})

        # Step 7: Check hard gates for PPI
        if self.config.require_ppi_presence and not pdt.ppi_matrix_present:
            return LayerScore(
                layer=LayerID.UNIT,
                score=0.0,
                components={"S": S, "M": M, "I": I, "gate_failure": "ppi_presence"},
                rationale="HARD GATE: PPI required but not present",
                metadata={"gate": "ppi_presence"}
            )

        if self.config.require_indicator_matrix and not pdt.indicator_matrix_present:
            return LayerScore(
                layer=LayerID.UNIT,
                score=0.0,
                components={"S": S, "M": M, "I": I, "P": P, "gate_failure": "indicator_matrix"},
                rationale="HARD GATE: Indicator matrix required but not present",
                metadata={"gate": "indicator_matrix"}
            )

        # Step 8: Aggregate
        U_base = self._aggregate_components(S, M, I, P)
        logger.info("U_base_computed", extra={"U_base": U_base})

        # Step 9: Anti-gaming
        gaming_penalty = self._compute_gaming_penalty(pdt)
        U_final = max(0.0, U_base - gaming_penalty)

        # Step 10: Quality level
        if U_final >= 0.85:
            quality = "sobresaliente"
        elif U_final >= 0.7:
            quality = "robusto"
        elif U_final >= 0.5:
            quality = "mínimo"
        else:
            quality = "insuficiente"

        return LayerScore(
            layer=LayerID.UNIT,
            score=U_final,
            components={"S": S, "M": M, "I": I, "P": P, "U_base": U_base, "penalty": gaming_penalty},
            rationale=f"Unit quality: {quality} (S={S:.2f}, M={M:.2f}, I={I:.2f}, P={P:.2f})",
            metadata={"quality_level": quality, "aggregation": self.config.aggregation_type}
        )

    def _compute_structural_compliance(self, pdt: PDTStructure) -> float:
        """Compute S = w_block·B_cov + w_hierarchy·H + w_order·O."""
        # Block coverage
        blocks_found = sum(
            1 for block in self.MANDATORY_BLOCKS
            if block in pdt.blocks_found
            and pdt.blocks_found[block].get("tokens", 0) >= self.config.min_block_tokens
            and pdt.blocks_found[block].get("numbers_count", 0) >= self.config.min_block_numbers
        )
        B_cov = blocks_found / len(self.MANDATORY_BLOCKS)

        # Hierarchy score
        if not pdt.headers:
            H = 0.0
        else:
            valid = sum(1 for h in pdt.headers if h.get("valid_numbering"))
            ratio = valid / len(pdt.headers)
            if ratio >= self.config.hierarchy_excellent_threshold:
                H = 1.0
            elif ratio >= self.config.hierarchy_acceptable_threshold:
                H = 0.5
            else:
                H = 0.0

        # Order score - count inversions in block_sequence vs expected
        expected = ["Diagnóstico", "Parte Estratégica", "PPI", "Seguimiento"]
        inversions = 0
        if pdt.block_sequence:
            # Find positions of blocks in actual sequence
            positions = {}
            for i, block in enumerate(pdt.block_sequence):
                if block in expected:
                    positions[block] = i

            # Count inversions (pairs out of order)
            for i, block1 in enumerate(expected):
                if block1 not in positions:
                    continue
                for block2 in expected[i+1:]:
                    if block2 not in positions:
                        continue
                    if positions[block1] > positions[block2]:
                        inversions += 1

        O = 1.0 if inversions == 0 else (0.5 if inversions == 1 else 0.0)

        S = (self.config.w_block_coverage * B_cov +
             self.config.w_hierarchy * H +
             self.config.w_order * O)

        return S

    def _compute_mandatory_sections(self, pdt: PDTStructure) -> float:
        """Compute M = weighted average of section completeness."""
        # Section requirements (from config)
        requirements = {
            "Diagnóstico": {
                "min_tokens": self.config.diagnostico_min_tokens,
                "min_keywords": self.config.diagnostico_min_keywords,
                "min_numbers": self.config.diagnostico_min_numbers,
                "min_sources": self.config.diagnostico_min_sources,
                "weight": self.config.critical_sections_weight,  # Critical section
            },
            "Parte Estratégica": {
                "min_tokens": self.config.estrategica_min_tokens,
                "min_keywords": self.config.estrategica_min_keywords,
                "min_numbers": self.config.estrategica_min_numbers,
                "weight": self.config.critical_sections_weight,  # Critical section
            },
            "PPI": {
                "min_tokens": self.config.ppi_section_min_tokens,
                "min_keywords": self.config.ppi_section_min_keywords,
                "min_numbers": self.config.ppi_section_min_numbers,
                "weight": self.config.critical_sections_weight,  # Critical section
            },
            "Seguimiento": {
                "min_tokens": self.config.seguimiento_min_tokens,
                "min_keywords": self.config.seguimiento_min_keywords,
                "min_numbers": self.config.seguimiento_min_numbers,
                "weight": 1.0,
            },
            "Marco Normativo": {
                "min_tokens": self.config.marco_normativo_min_tokens,
                "min_keywords": self.config.marco_normativo_min_keywords,
                "weight": 1.0,
            }
        }

        total_weight = 0.0
        weighted_score = 0.0

        for section_name, reqs in requirements.items():
            section_data = pdt.sections_found.get(section_name, {})

            if not section_data.get("present", False):
                # Missing section gets 0
                score = 0.0
            else:
                # Check all requirements
                checks_passed = 0
                checks_total = 0

                if "min_tokens" in reqs:
                    checks_total += 1
                    if section_data.get("token_count", 0) >= reqs["min_tokens"]:
                        checks_passed += 1

                if "min_keywords" in reqs:
                    checks_total += 1
                    if section_data.get("keyword_matches", 0) >= reqs["min_keywords"]:
                        checks_passed += 1

                if "min_numbers" in reqs:
                    checks_total += 1
                    if section_data.get("number_count", 0) >= reqs["min_numbers"]:
                        checks_passed += 1

                if "min_sources" in reqs:
                    checks_total += 1
                    if section_data.get("sources_found", 0) >= reqs["min_sources"]:
                        checks_passed += 1

                score = checks_passed / checks_total if checks_total > 0 else 0.0

            weight = reqs.get("weight", 1.0)
            weighted_score += score * weight
            total_weight += weight

        M = weighted_score / total_weight if total_weight > 0 else 0.0
        return M

    def _compute_indicator_quality(self, pdt: PDTStructure) -> dict:
        """Compute I = w_struct·I_struct + w_link·I_link + w_logic·I_logic."""
        if not pdt.indicator_matrix_present or not pdt.indicator_rows:
            logger.warning("indicator_matrix_absent", extra={"I": 0.0})
            return {
                "I_struct": 0.0,
                "I_link": 0.0,
                "I_logic": 0.0,
                "I_total": 0.0
            }

        # I_struct: Field completeness
        critical_fields = ["Tipo", "Línea Estratégica", "Programa", "Línea Base",
                          "Meta Cuatrienio", "Fuente", "Unidad Medida"]
        optional_fields = ["Año LB", "Código MGA"]

        total_struct_score = 0.0
        for row in pdt.indicator_rows:
            critical_present = sum(1 for f in critical_fields if row.get(f))
            optional_present = sum(1 for f in optional_fields if row.get(f))

            # Penalize placeholders
            placeholder_count = sum(
                1 for f in critical_fields
                if row.get(f) in ["S/D", "N/A", "TBD", ""]
            )

            critical_score = critical_present / len(critical_fields)
            optional_score = optional_present / len(optional_fields)
            placeholder_penalty = (placeholder_count / len(critical_fields)) * self.config.i_placeholder_penalty_multiplier

            row_score = (critical_score * self.config.i_critical_fields_weight + optional_score) / (self.config.i_critical_fields_weight + 1)
            row_score = max(0.0, row_score - placeholder_penalty)
            total_struct_score += row_score

        I_struct = total_struct_score / len(pdt.indicator_rows)

        # I_link: Traceability (fuzzy matching between indicators and strategic lines)
        linked_count = 0
        for row in pdt.indicator_rows:
            programa = row.get("Programa", "")
            linea = row.get("Línea Estratégica", "")
            if programa and linea:
                # Simplified: check if they share significant words
                prog_words = set(programa.lower().split())
                linea_words = set(linea.lower().split())
                if len(prog_words & linea_words) >= 2:  # At least 2 words in common
                    linked_count += 1

        I_link = linked_count / len(pdt.indicator_rows)

        # I_logic: Year coherence
        logic_violations = 0
        for row in pdt.indicator_rows:
            year_lb = row.get("Año LB")

            if year_lb is not None:
                try:
                    year_lb_int = int(year_lb)
                    if not (self.config.i_valid_lb_year_min <= year_lb_int <= self.config.i_valid_lb_year_max):
                        logic_violations += 1
                except (ValueError, TypeError):
                    # Invalid year format counts as violation
                    logic_violations += 1

        I_logic = 1.0 - (logic_violations / len(pdt.indicator_rows))

        # Aggregate
        I_total = (self.config.w_i_struct * I_struct +
                  self.config.w_i_link * I_link +
                  self.config.w_i_logic * I_logic)

        return {
            "I_struct": I_struct,
            "I_link": I_link,
            "I_logic": I_logic,
            "I_total": I_total
        }

    def _compute_ppi_completeness(self, pdt: PDTStructure) -> dict:
        """Compute P = w_presence·P_presence + w_struct·P_struct + w_cons·P_consistency."""
        # P_presence
        P_presence = 1.0 if pdt.ppi_matrix_present else 0.0

        if not pdt.ppi_matrix_present or not pdt.ppi_rows:
            return {
                "P_presence": P_presence,
                "P_struct": 0.0,
                "P_consistency": 0.0,
                "P_total": P_presence * self.config.w_p_presence
            }

        # P_struct: Non-zero rows
        nonzero_rows = sum(
            1 for row in pdt.ppi_rows
            if row.get("Costo Total", 0) > 0
        )
        P_struct = nonzero_rows / len(pdt.ppi_rows)

        # P_consistency: Accounting closure
        violations = 0
        for row in pdt.ppi_rows:
            costo_total = row.get("Costo Total", 0)

            # Check temporal sum
            temporal_sum = sum(row.get(str(year), 0) for year in range(2024, 2028))
            if abs(temporal_sum - costo_total) > costo_total * self.config.p_accounting_tolerance:
                violations += 1

            # Check source sum
            source_sum = (row.get("SGP", 0) + row.get("SGR", 0) +
                         row.get("Propios", 0) + row.get("Otras", 0))
            if abs(source_sum - costo_total) > costo_total * self.config.p_accounting_tolerance:
                violations += 1

        P_consistency = 1.0 - (violations / (len(pdt.ppi_rows) * 2))  # 2 checks per row

        # Aggregate
        P_total = (self.config.w_p_presence * P_presence +
                  self.config.w_p_structure * P_struct +
                  self.config.w_p_consistency * P_consistency)

        return {
            "P_presence": P_presence,
            "P_struct": P_struct,
            "P_consistency": P_consistency,
            "P_total": P_total
        }

    def _aggregate_components(self, S: float, M: float, I: float, P: float) -> float:
        """Aggregate S, M, I, P using configured method."""
        if self.config.aggregation_type == "geometric_mean":
            # Geometric mean: (S·M·I·P)^(1/4)
            product = S * M * I * P
            return product ** 0.25
        elif self.config.aggregation_type == "harmonic_mean":
            # Harmonic mean: 4 / (1/S + 1/M + 1/I + 1/P)
            if S == 0 or M == 0 or I == 0 or P == 0:
                return 0.0
            return 4.0 / (1.0/S + 1.0/M + 1.0/I + 1.0/P)
        else:  # weighted_average
            return (self.config.w_S * S +
                   self.config.w_M * M +
                   self.config.w_I * I +
                   self.config.w_P * P)

    def _compute_gaming_penalty(self, pdt: PDTStructure) -> float:
        """Compute anti-gaming penalties."""
        penalties = []

        # Check placeholder ratio in indicators
        if pdt.indicator_matrix_present and pdt.indicator_rows:
            placeholder_count = 0
            total_fields = 0
            for row in pdt.indicator_rows:
                for _key, value in row.items():
                    total_fields += 1
                    if value in ["S/D", "N/A", "TBD", ""]:
                        placeholder_count += 1

            placeholder_ratio = placeholder_count / total_fields if total_fields > 0 else 0
            if placeholder_ratio > self.config.max_placeholder_ratio:
                penalty = (placeholder_ratio - self.config.max_placeholder_ratio) * 0.5
                penalties.append(penalty)

        # Check unique values in PPI costs
        if pdt.ppi_matrix_present and pdt.ppi_rows:
            costs = [row.get("Costo Total", 0) for row in pdt.ppi_rows]
            unique_costs = len(set(costs))
            unique_ratio = unique_costs / len(costs) if costs else 0

            if unique_ratio < self.config.min_unique_values_ratio:
                penalty = (self.config.min_unique_values_ratio - unique_ratio) * 0.3
                penalties.append(penalty)

        # Check number density in critical sections
        critical_sections = ["Diagnóstico", "Parte Estratégica", "PPI"]
        for section in critical_sections:
            section_data = pdt.sections_found.get(section, {})
            if section_data.get("present"):
                tokens = section_data.get("token_count", 0)
                numbers = section_data.get("number_count", 0)
                density = numbers / tokens if tokens > 0 else 0

                if density < self.config.min_number_density:
                    penalty = (self.config.min_number_density - density) * 0.2
                    penalties.append(penalty)

        total_penalty = sum(penalties)
        return min(total_penalty, self.config.gaming_penalty_cap)
