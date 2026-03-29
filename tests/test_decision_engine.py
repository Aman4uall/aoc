import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.decision_engine import (
    build_heat_integration_study,
    build_process_synthesis,
    build_rough_alternatives,
    resolve_property_gaps,
    select_route_architecture,
    selected_heat_case,
)
from aoc.route_families import build_route_family_artifact
from aoc.models import ProvenanceTag
from aoc.reasoning import MockReasoningService
from aoc.research import ResearchManager


class DecisionEngineTests(unittest.TestCase):
    def setUp(self):
        self.config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        self.reasoning = MockReasoningService()
        self.research = ResearchManager(self.reasoning)
        self.bundle = self.research.build_bundle(self.config)
        self.profile = self.reasoning.build_product_profile(self.config.basis, self.bundle.sources, self.bundle.corpus_excerpt)
        self.market = self.reasoning.build_market_assessment(self.config.basis, self.bundle.sources, self.bundle.corpus_excerpt)
        self.survey = self.reasoning.survey_routes(self.config.basis, self.bundle.sources, self.bundle.corpus_excerpt)

    def test_property_gap_blocks_estimated_high_sensitivity_values(self):
        density = next(item for item in self.profile.properties if item.name.lower() == "density")
        density.method = ProvenanceTag.ESTIMATED
        property_gap = resolve_property_gaps(self.profile, self.config)
        self.assertIn("Density", property_gap.unresolved_high_sensitivity)

    def test_density_from_specific_gravity_is_accepted_as_sourced_basis(self):
        density = next(item for item in self.profile.properties if item.name.lower() == "density")
        density.method = ProvenanceTag.CALCULATED
        density.basis = "Specific gravity reference"
        density.assumptions = ["Specific gravity value used directly as density in g/cm3"]
        property_gap = resolve_property_gaps(self.profile, self.config)
        density_value = next(item for item in property_gap.values if item.name == "Density")
        self.assertEqual(density_value.provenance_method, ProvenanceTag.SOURCED)
        self.assertNotIn("Density", property_gap.unresolved_high_sensitivity)

    def test_heat_integration_prefers_recovery_for_thermal_hydration(self):
        property_gap = resolve_property_gaps(self.profile, self.config)
        route_families = build_route_family_artifact(self.survey)
        synthesis = build_process_synthesis(self.config, self.survey, property_gap, route_families=route_families)
        rough = build_rough_alternatives(self.config, self.survey, synthesis, self.market, route_families)
        heat_study = build_heat_integration_study(self.config, rough, self.market)
        eo_route = next(item for item in heat_study.route_decisions if item.route_id == "eo_hydration")
        selected_case = selected_heat_case(eo_route)
        self.assertIsNotNone(selected_case)
        self.assertGreater(selected_case.recovered_duty_kw, 0.0)
        self.assertNotEqual(selected_case.case_id, "eo_hydration_no_recovery")

    def test_route_selection_emits_structured_decisions(self):
        property_gap = resolve_property_gaps(self.profile, self.config)
        route_families = build_route_family_artifact(self.survey)
        synthesis = build_process_synthesis(self.config, self.survey, property_gap, route_families=route_families)
        rough = build_rough_alternatives(self.config, self.survey, synthesis, self.market, route_families)
        heat_study = build_heat_integration_study(self.config, rough, self.market)
        selection, route_decision, reactor_choice, separation_choice, utility_network = select_route_architecture(
            self.config,
            self.survey,
            rough,
            heat_study,
            self.market,
            route_families,
        )
        self.assertEqual(route_decision.selected_candidate_id, selection.selected_route_id)
        self.assertTrue(route_decision.alternatives)
        self.assertTrue(reactor_choice.selected_candidate_id)
        self.assertTrue(separation_choice.selected_candidate_id)
        self.assertEqual(utility_network.route_id, selection.selected_route_id)
        self.assertIn("Family", selection.comparison_markdown)

    def test_route_family_profiles_drive_rough_cases(self):
        route_families = build_route_family_artifact(self.survey)
        self.assertTrue(route_families.profiles)
        hydration_profile = next(item for item in route_families.profiles if item.route_id == "eo_hydration")
        self.assertEqual(hydration_profile.route_family_id, "liquid_hydration_train")
        property_gap = resolve_property_gaps(self.profile, self.config)
        synthesis = build_process_synthesis(self.config, self.survey, property_gap, route_families=route_families)
        rough = build_rough_alternatives(self.config, self.survey, synthesis, self.market, route_families)
        hydration_case = next(item for item in rough.cases if item.route_id == "eo_hydration")
        self.assertEqual(hydration_case.route_family_id, "liquid_hydration_train")
        self.assertTrue(hydration_case.route_family_label)
        self.assertTrue(hydration_case.heat_recovery_style)


if __name__ == "__main__":
    unittest.main()
