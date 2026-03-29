import unittest
from pathlib import Path

from aoc.archetypes import classify_process_archetype
from aoc.config import load_project_config
from aoc.decision_engine import resolve_property_gaps
from aoc.family_adapters import build_chemistry_family_adapter
from aoc.reasoning import MockReasoningService
from aoc.research import ResearchManager
from aoc.route_families import build_route_family_artifact
from aoc.unit_operation_families import build_unit_operation_family_artifact


class UnitOperationFamilyTests(unittest.TestCase):
    def test_absorption_route_builds_absorber_led_unit_family(self):
        config = load_project_config(str(Path("examples/sulfuric_acid_india_mock.yaml").resolve()))
        reasoning = MockReasoningService()
        research = ResearchManager(reasoning)
        bundle = research.build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        archetype = classify_process_archetype(config, survey, property_gap)
        adapter = build_chemistry_family_adapter(config, survey, property_gap, archetype)
        route_families = build_route_family_artifact(survey, adapter)
        route = survey.routes[0]
        artifact = build_unit_operation_family_artifact(route, archetype, adapter, route_families)
        self.assertTrue(any(item.candidate_id == "packed_absorption_train" for item in artifact.separation_candidates))
        self.assertIn("absorber", ",".join(artifact.supporting_unit_operations))

    def test_solids_route_builds_crystallizer_led_unit_family(self):
        config = load_project_config(str(Path("examples/sodium_bicarbonate_india_mock.yaml").resolve()))
        reasoning = MockReasoningService()
        research = ResearchManager(reasoning)
        bundle = research.build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        archetype = classify_process_archetype(config, survey, property_gap)
        adapter = build_chemistry_family_adapter(config, survey, property_gap, archetype)
        route_families = build_route_family_artifact(survey, adapter)
        route = survey.routes[0]
        artifact = build_unit_operation_family_artifact(route, archetype, adapter, route_families)
        self.assertTrue(any("crystallizer" in item.candidate_id for item in artifact.separation_candidates))
        self.assertIn("dryer", artifact.supporting_unit_operations)


if __name__ == "__main__":
    unittest.main()
