import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.models import ProjectBasis, ProjectConfig
from aoc.reasoning import MockReasoningService
from aoc.research import ResearchManager
from aoc.flowsheet_blueprint import build_unit_train_candidate_set, select_flowsheet_blueprint
from aoc.route_families import build_route_family_artifact
from aoc.route_chemistry import build_route_chemistry_artifact
from aoc.family_adapters import build_chemistry_family_adapter
from aoc.archetypes import build_alternative_sets
from aoc.archetypes import classify_process_archetype
from aoc.decision_engine import resolve_property_gaps
from aoc.selectors import select_reactor_configuration
from aoc.unit_operation_families import build_unit_operation_family_artifact


class RouteFamilyTests(unittest.TestCase):
    def test_route_family_artifact_covers_mock_route_survey(self):
        config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        reasoning = MockReasoningService()
        research = ResearchManager(reasoning)
        bundle = research.build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        archetype = classify_process_archetype(config, survey, property_gap)
        adapter = build_chemistry_family_adapter(config, survey, property_gap, archetype)
        artifact = build_route_family_artifact(survey, adapter)
        self.assertEqual(len(artifact.profiles), len(survey.routes))
        self.assertIn("Route", artifact.markdown)
        eo_profile = next(item for item in artifact.profiles if item.route_id == "eo_hydration")
        self.assertEqual(eo_profile.route_family_id, "liquid_hydration_train")
        self.assertTrue(eo_profile.primary_reactor_class)
        self.assertTrue(eo_profile.primary_separation_train)

    def test_benzalkonium_chloride_routes_map_to_quaternization_family(self):
        config = ProjectConfig(
            basis=ProjectBasis(
                target_product="Benzalkonium chloride",
                capacity_tpa=50000,
                target_purity_wt_pct=80.0,
                operating_mode="continuous",
                throughput_basis="finished_product",
                nominal_active_wt_pct=80.0,
                product_form="aqueous_or_alcohol_solution",
                carrier_components=["water", "ethanol"],
                homolog_distribution={"c12": 0.4, "c14": 0.5, "c16": 0.1},
                quality_targets=[
                    "Residual free benzyl chloride below finished-goods limit",
                    "Residual free tertiary amine below finished-goods limit",
                ],
            )
        )
        reasoning = MockReasoningService()
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        self.assertIn("80 wt% active", profile.commercial_basis_summary)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        self.assertNotIn("generic_route_1", {route.route_id for route in survey.routes})
        route_chemistry = build_route_chemistry_artifact(survey, [])
        self.assertEqual(route_chemistry.blocking_route_ids, [])
        bac_graph = next(item for item in route_chemistry.route_graphs if item.route_id == "benzyl_chloride_quaternization_ethanol")
        active_node = next(node for node in bac_graph.species_nodes if node.species_id == "benzalkonium_chloride")
        ethanol_node = next(node for node in bac_graph.species_nodes if node.species_id == "ethanol")
        self.assertEqual(active_node.species_kind, "bundle")
        self.assertEqual(active_node.commercial_role, "active_bundle")
        self.assertEqual(active_node.volatility_class, "nonvolatile")
        self.assertEqual(ethanol_node.species_kind, "carrier")
        self.assertIn("solvent", ethanol_node.role_tags)
        property_gap = resolve_property_gaps(profile, config)
        archetype = classify_process_archetype(config, survey, property_gap)
        self.assertEqual(archetype.dominant_product_phase, "liquid")
        self.assertEqual(archetype.dominant_separation_family, "mixed_purification")
        adapter = build_chemistry_family_adapter(config, survey, property_gap, archetype)
        artifact = build_route_family_artifact(survey, adapter)
        profile = next(item for item in artifact.profiles if item.route_id == "benzyl_chloride_quaternization_ethanol")
        self.assertEqual(profile.route_family_id, "quaternization_liquid_train")
        self.assertIn("recovery", profile.primary_separation_train.lower())

        alternative_sets = build_alternative_sets(config, archetype, survey, artifact)
        reactor_family = next(item for item in alternative_sets if item.set_id == "reactor_family")
        self.assertEqual(reactor_family.selected_candidate_id, "cstr_train")

        selected_route = next(route for route in survey.routes if route.route_id == "benzyl_chloride_quaternization_ethanol")
        unit_family = build_unit_operation_family_artifact(selected_route, archetype, adapter, artifact)
        reactor_choice = select_reactor_configuration(selected_route, archetype, adapter, unit_family, artifact)
        self.assertEqual(reactor_choice.selected_candidate_id, "jacketed_cstr_train")

        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, artifact, [], config.basis.operating_mode)
        blueprint = select_flowsheet_blueprint(candidate_set, selected_route.route_id)
        reactor_step = next(step for step in blueprint.steps if step.step_role == "reaction")
        primary_separation = next(step for step in blueprint.steps if step.step_role == "primary_separation")
        self.assertEqual(reactor_step.unit_type, "cstr")
        self.assertEqual(primary_separation.unit_type, "distillation")


if __name__ == "__main__":
    unittest.main()
