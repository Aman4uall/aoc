import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.decision_engine import (
    build_chemistry_decision_artifact,
    build_heat_integration_study,
    build_process_synthesis,
    build_route_discovery_artifact,
    build_route_screening_artifact,
    build_rough_alternatives,
    resolve_property_gaps,
    select_route_architecture,
    selected_heat_case,
)
from aoc.flowsheet_blueprint import build_unit_train_candidate_set
from aoc.route_chemistry import build_route_chemistry_artifact
from aoc.route_families import build_route_family_artifact
from aoc.scientific_inference import build_reaction_network_v2_artifact, build_species_resolution_artifact
from aoc.scientific_inference import build_route_process_claims_artifact
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
        density.supporting_sources = []
        density.citations = []
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
        route_chemistry = build_route_chemistry_artifact(self.survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution)
        unit_train_candidates = build_unit_train_candidate_set(
            self.survey,
            route_chemistry,
            route_families,
            [],
            self.config.basis.operating_mode,
        )
        route_screening = build_route_screening_artifact(
            self.survey,
            route_chemistry,
            species_resolution,
            reaction_network_v2,
            route_families,
            unit_train_candidates,
            build_route_process_claims_artifact(self.survey, route_chemistry, unit_train_candidates),
            operating_mode=self.config.basis.operating_mode,
        )
        synthesis = build_process_synthesis(self.config, self.survey, property_gap, route_families=route_families)
        rough = build_rough_alternatives(self.config, self.survey, synthesis, self.market, route_families)
        heat_study = build_heat_integration_study(self.config, rough, self.market)
        selection, route_decision, reactor_choice, separation_choice, utility_network = select_route_architecture(
            self.config,
            self.survey,
            route_chemistry,
            rough,
            heat_study,
            self.market,
            route_families,
            route_screening=route_screening,
        )
        self.assertEqual(route_decision.selected_candidate_id, selection.selected_route_id)
        self.assertTrue(route_decision.alternatives)
        self.assertTrue(reactor_choice.selected_candidate_id)
        self.assertTrue(separation_choice.selected_candidate_id)
        self.assertEqual(utility_network.route_id, selection.selected_route_id)
        self.assertIn("Family", selection.comparison_markdown)

    def test_route_discovery_screening_and_chemistry_decision_are_separated(self):
        property_gap = resolve_property_gaps(self.profile, self.config)
        route_families = build_route_family_artifact(self.survey)
        route_chemistry = build_route_chemistry_artifact(self.survey, [])
        route_discovery = build_route_discovery_artifact(self.survey, route_chemistry, route_families)
        species_resolution = build_species_resolution_artifact(route_chemistry)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution)
        unit_train_candidates = build_unit_train_candidate_set(
            self.survey,
            route_chemistry,
            route_families,
            [],
            self.config.basis.operating_mode,
        )
        route_screening = build_route_screening_artifact(
            self.survey,
            route_chemistry,
            species_resolution,
            reaction_network_v2,
            route_families,
            unit_train_candidates,
            build_route_process_claims_artifact(self.survey, route_chemistry, unit_train_candidates),
            operating_mode=self.config.basis.operating_mode,
        )
        synthesis = build_process_synthesis(self.config, self.survey, property_gap, route_families=route_families)
        rough = build_rough_alternatives(self.config, self.survey, synthesis, self.market, route_families)
        heat_study = build_heat_integration_study(self.config, rough, self.market)
        selection, *_ = select_route_architecture(
            self.config,
            self.survey,
            route_chemistry,
            rough,
            heat_study,
            self.market,
            route_families,
            route_screening=route_screening,
            species_resolution=species_resolution,
        )
        selected_route = next(route for route in self.survey.routes if route.route_id == selection.selected_route_id)
        chemistry_decision = build_chemistry_decision_artifact(selected_route, species_resolution, reaction_network_v2)
        self.assertTrue(route_discovery.rows)
        self.assertIn(selection.selected_route_id, route_screening.retained_route_ids)
        self.assertEqual(chemistry_decision.selected_route_id, selection.selected_route_id)
        self.assertIn("Selected route", chemistry_decision.markdown)

    def test_route_screening_captures_process_burdens(self):
        acetic_config = load_project_config(str(Path("examples/acetic_acid_india_mock.yaml").resolve()))
        bundle = self.research.build_bundle(acetic_config)
        profile = self.reasoning.build_product_profile(acetic_config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = self.reasoning.survey_routes(acetic_config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, acetic_config)
        route_families = build_route_family_artifact(survey)
        route_chemistry = build_route_chemistry_artifact(survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution)
        unit_train_candidates = build_unit_train_candidate_set(
            survey,
            route_chemistry,
            route_families,
            [],
            acetic_config.basis.operating_mode,
        )
        route_screening = build_route_screening_artifact(
            survey,
            route_chemistry,
            species_resolution,
            reaction_network_v2,
            route_families,
            unit_train_candidates,
            build_route_process_claims_artifact(survey, route_chemistry, unit_train_candidates),
            operating_mode=acetic_config.basis.operating_mode,
        )
        carbonylation = next(row for row in route_screening.rows if row.route_id == "methanol_carbonylation")
        butane = next(row for row in route_screening.rows if row.route_id == "butane_oxidation")
        self.assertLess(carbonylation.waste_burden_score, butane.waste_burden_score)
        self.assertLess(carbonylation.isolation_impurity_burden_score, butane.isolation_impurity_burden_score)
        self.assertLess(carbonylation.separation_pain_score, butane.separation_pain_score)
        self.assertGreater(carbonylation.catalyst_lifecycle_burden_score, butane.catalyst_lifecycle_burden_score)

    def test_route_screening_tracks_cleanup_and_waste_treatment_details(self):
        phenol_config = load_project_config(str(Path("examples/phenol_india_mock.yaml").resolve()))
        bundle = self.research.build_bundle(phenol_config)
        profile = self.reasoning.build_product_profile(phenol_config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = self.reasoning.survey_routes(phenol_config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, phenol_config)
        route_families = build_route_family_artifact(survey)
        route_chemistry = build_route_chemistry_artifact(survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution)
        unit_train_candidates = build_unit_train_candidate_set(
            survey,
            route_chemistry,
            route_families,
            [],
            phenol_config.basis.operating_mode,
        )
        route_screening = build_route_screening_artifact(
            survey,
            route_chemistry,
            species_resolution,
            reaction_network_v2,
            route_families,
            unit_train_candidates,
            build_route_process_claims_artifact(survey, route_chemistry, unit_train_candidates),
            operating_mode=phenol_config.basis.operating_mode,
        )
        cumene = next(row for row in route_screening.rows if row.route_id == "cumene_oxidation_cleavage")
        chlorobenzene = next(row for row in route_screening.rows if row.route_id == "chlorobenzene_hydrolysis")
        direct_oxidation = next(row for row in route_screening.rows if row.route_id == "benzene_direct_hydroxylation")
        self.assertGreater(chlorobenzene.waste_treatment_load_score, cumene.waste_treatment_load_score)
        self.assertGreater(direct_oxidation.impurity_cleanup_sequence_score, cumene.impurity_cleanup_sequence_score)
        self.assertGreaterEqual(direct_oxidation.stepwise_recovery_burden_score, 0.0)

    def test_route_family_profiles_drive_rough_cases(self):
        route_families = build_route_family_artifact(self.survey)
        self.assertTrue(route_families.profiles)
        hydration_profile = next(item for item in route_families.profiles if item.route_id == "eo_hydration")
        self.assertEqual(hydration_profile.route_family_id, "liquid_hydration_train")
        property_gap = resolve_property_gaps(self.profile, self.config)
        route_chemistry = build_route_chemistry_artifact(self.survey, [])
        synthesis = build_process_synthesis(self.config, self.survey, property_gap, route_families=route_families)
        unit_train_candidates = build_unit_train_candidate_set(self.survey, route_chemistry, route_families, [], self.config.basis.operating_mode)
        rough = build_rough_alternatives(
            self.config,
            self.survey,
            synthesis,
            self.market,
            route_families,
            unit_train_candidates,
        )
        hydration_case = next(item for item in rough.cases if item.route_id == "eo_hydration")
        self.assertEqual(hydration_case.route_family_id, "liquid_hydration_train")
        self.assertTrue(hydration_case.route_family_label)
        self.assertTrue(hydration_case.heat_recovery_style)
        self.assertGreater(hydration_case.blueprint_step_count, 0)
        self.assertGreater(hydration_case.separation_duty_count, 0)
        self.assertIn("Blueprint complexity", hydration_case.notes)


if __name__ == "__main__":
    unittest.main()
