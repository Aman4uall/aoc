import unittest
from pathlib import Path

from aoc.archetypes import build_alternative_sets, classify_process_archetype
from aoc.benchmarks import build_benchmark_manifest
from aoc.config import load_project_config
from aoc.decision_engine import resolve_property_gaps
from aoc.evidence import build_resolved_source_set, build_resolved_value_artifact
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager


class KernelTests(unittest.TestCase):
    def _config(self):
        return load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))

    def test_benchmark_manifest_uses_named_profile(self):
        config = self._config()
        manifest = build_benchmark_manifest(config)
        self.assertEqual(manifest.benchmark_id, "ethylene_glycol")
        self.assertIn("route_selection", manifest.expected_decisions)
        self.assertIn("financial_analysis", manifest.required_chapters)

    def test_resolved_sources_and_values_are_built_from_public_bundle(self):
        config = self._config()
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        resolved_sources = build_resolved_source_set(config, bundle)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        resolved_values = build_resolved_value_artifact(property_gap, resolved_sources, config)
        self.assertTrue(resolved_sources.selected_source_ids)
        self.assertEqual(resolved_sources.unresolved_conflicts, [])
        self.assertEqual(resolved_values.unresolved_value_ids, [])

    def test_archetype_and_alternative_sets_are_emitted(self):
        config = self._config()
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        route_survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        archetype = classify_process_archetype(config, route_survey, property_gap)
        alternative_sets = build_alternative_sets(config, archetype, route_survey)
        self.assertEqual(archetype.compound_family, "organic")
        self.assertIn("continuous", archetype.operating_mode_candidates)
        self.assertTrue(any(item.set_id == "route_screen" for item in alternative_sets))
        self.assertTrue(all(item.selected_candidate_id for item in alternative_sets))


if __name__ == "__main__":
    unittest.main()

