import unittest

from aoc.models import ProcessArchetype, ProcessTemplate, ProjectBasis
from aoc.operations import build_operating_mode_and_operations


class OperationsPlanningTests(unittest.TestCase):
    def test_build_operating_mode_and_operations_emits_continuous_liquid_basis(self):
        basis = ProjectBasis(
            target_product="Ethylene Glycol",
            capacity_tpa=200000,
            target_purity_wt_pct=99.9,
            process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
            india_only=True,
        )
        archetype = ProcessArchetype(
            archetype_id="organic_liquid_distillation_flash",
            compound_family="organic",
            dominant_product_phase="liquid",
            dominant_feed_phase="liquid",
            operating_mode_candidates=["continuous", "batch"],
            dominant_separation_family="distillation_flash",
            heat_management_profile="moderate_temperature_integrated",
            hazard_intensity="moderate",
            rationale="test",
            citations=["s1"],
        )
        decision, planning = build_operating_mode_and_operations(basis, archetype, ["s1"], ["test"])
        self.assertEqual(decision.selected_candidate_id, "continuous")
        self.assertEqual(planning.recommended_operating_mode, "continuous")
        self.assertEqual(planning.service_family, "continuous_liquid_purification")
        self.assertGreater(planning.raw_material_buffer_days, 0.0)
        self.assertGreater(planning.finished_goods_buffer_days, 0.0)
        self.assertGreater(planning.annual_restart_loss_kg, 0.0)
        self.assertGreater(len(planning.calc_traces), 0)
