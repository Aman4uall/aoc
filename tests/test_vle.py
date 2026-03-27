import shutil
import tempfile
import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.models import GeographicScope, ProvenanceTag, ResearchBundle, SourceDomain, SourceKind, SourceRecord
from aoc.properties import build_property_package_artifact, build_separation_thermo_artifact, component_k_value
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager


class SeparationThermoTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aoc-vle-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _eg_context(self, add_bip_source: bool = False):
        config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        config.output_root = self.temp_dir
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        if add_bip_source:
            bundle = ResearchBundle(
                sources=bundle.sources
                + [
                    SourceRecord(
                        source_id="src_bip_water_eg",
                        source_kind=SourceKind.LITERATURE,
                        source_domain=SourceDomain.TECHNICAL,
                        title="Binary interaction note",
                        citation_text="Public technical note for water / ethylene glycol NRTL parameters.",
                        extraction_snippet="BIP|NRTL|water|ethylene glycol|tau12=0.42|tau21=-0.18|alpha=0.30",
                        confidence=0.95,
                        provenance_tag=ProvenanceTag.SOURCED,
                        geographic_scope=GeographicScope.GLOBAL,
                    )
                ],
                technical_source_ids=bundle.technical_source_ids + ["src_bip_water_eg"],
                india_source_ids=bundle.india_source_ids,
                corpus_excerpt=bundle.corpus_excerpt,
                user_document_ids=bundle.user_document_ids,
            )
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        route = survey.routes[0]
        property_packages = build_property_package_artifact(config, bundle, profile, survey)
        return config, route, property_packages

    def test_component_k_value_prefers_antoine_when_available(self):
        _, _, property_packages = self._eg_context()
        water_package = next(item for item in property_packages.packages if item.identifier.canonical_name.lower() == "water")
        k_value, vapor_pressure_bar, gamma, method, status = component_k_value(water_package, 95.0, 1.5)
        self.assertGreater(k_value, 0.0)
        self.assertGreater(vapor_pressure_bar, 0.0)
        self.assertAlmostEqual(gamma, 1.0, places=6)
        self.assertEqual(method, "ideal_raoult_antoine")
        self.assertEqual(status, "resolved")

    def test_separation_thermo_builds_relative_volatility_for_eg(self):
        config, route, property_packages = self._eg_context()
        artifact = build_separation_thermo_artifact(route, property_packages, config.basis.target_product, "distillation_train")
        self.assertEqual(artifact.separation_family, "distillation")
        self.assertEqual(artifact.light_key.lower(), "water")
        self.assertEqual(artifact.heavy_key.lower(), "ethylene glycol")
        self.assertIsNotNone(artifact.relative_volatility)
        self.assertGreater(artifact.relative_volatility.average_alpha, 1.0)
        self.assertTrue(artifact.top_k_values)
        self.assertTrue(artifact.bottom_k_values)
        self.assertEqual(artifact.activity_model, "ideal_raoult_missing_bip_fallback")
        self.assertTrue(artifact.missing_binary_pairs)
        light_top = next(item for item in artifact.top_k_values if item.component_name.lower() == "water")
        heavy_top = next(item for item in artifact.top_k_values if item.component_name.lower() == "ethylene glycol")
        self.assertAlmostEqual(light_top.activity_coefficient, 1.0, places=6)
        self.assertAlmostEqual(heavy_top.activity_coefficient, 1.0, places=6)
        self.assertIn("missing_bip", artifact.relative_volatility.method)

    def test_separation_thermo_uses_nrtl_when_cited_bips_exist(self):
        config, route, property_packages = self._eg_context(add_bip_source=True)
        artifact = build_separation_thermo_artifact(route, property_packages, config.basis.target_product, "distillation_train")
        self.assertEqual(artifact.activity_model, "nrtl_modified_raoult")
        self.assertFalse(artifact.missing_binary_pairs)
        self.assertTrue(artifact.binary_interaction_parameters)
        light_top = next(item for item in artifact.top_k_values if item.component_name.lower() == "water")
        heavy_top = next(item for item in artifact.top_k_values if item.component_name.lower() == "ethylene glycol")
        self.assertNotAlmostEqual(light_top.activity_coefficient, 1.0, places=6)
        self.assertNotAlmostEqual(heavy_top.activity_coefficient, 1.0, places=6)
        self.assertIn("modified_raoult_nrtl", light_top.method)
        self.assertEqual(artifact.relative_volatility.method, "modified_raoult_nrtl")


if __name__ == "__main__":
    unittest.main()
