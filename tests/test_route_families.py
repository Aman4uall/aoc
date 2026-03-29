import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.reasoning import MockReasoningService
from aoc.research import ResearchManager
from aoc.route_families import build_route_family_artifact
from aoc.family_adapters import build_chemistry_family_adapter
from aoc.archetypes import classify_process_archetype
from aoc.decision_engine import resolve_property_gaps


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


if __name__ == "__main__":
    unittest.main()
