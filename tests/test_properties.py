import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aoc.calculators import build_reaction_system, build_stream_table
from aoc.config import load_project_config
from aoc.models import ProcessTemplate, ProjectConfig, ProvenanceTag, RouteOption
from aoc.pipeline import PipelineRunner
from aoc.properties import (
    build_mixture_property_artifact,
    build_property_package_artifact,
    build_property_requirement_artifact,
    property_estimates_from_packages,
    requirement_failures_for_stage,
)
from aoc.properties.models import ChemicalIdentifier, PropertyPackage, PropertyPackageArtifact, PureComponentProperty
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager


class PropertyEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aoc-properties-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _eg_config(self) -> ProjectConfig:
        config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        config.output_root = self.temp_dir
        return config

    def test_property_packages_prefer_cited_product_profile_values(self):
        config = self._eg_config()
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        artifact = build_property_package_artifact(config, bundle, profile, survey)
        eg_package = next(item for item in artifact.packages if item.identifier.canonical_name.lower() == "ethylene glycol")
        self.assertEqual(eg_package.molecular_weight.provenance_method, ProvenanceTag.SOURCED)
        self.assertEqual(eg_package.normal_boiling_point.provenance_method, ProvenanceTag.SOURCED)
        self.assertIsNotNone(eg_package.liquid_heat_capacity)
        self.assertIn("ethylene_glycol", artifact.primary_identifier_ids)
        self.assertGreaterEqual(len(artifact.identifiers), 3)

    def test_requirement_failures_surface_blocked_component_basis(self):
        config = self._eg_config()
        identifier = ChemicalIdentifier(
            identifier_id="mystery_feed",
            canonical_name="Mystery feed",
            resolution_status="estimated",
        )
        blocked_package = PropertyPackage(
            package_id="mystery_feed_package",
            identifier=identifier,
            molecular_weight=PureComponentProperty(
                property_id="mystery_feed_mw",
                identifier_id="mystery_feed",
                property_name="molecular_weight",
                value="100",
                units="g/mol",
                provenance_method=ProvenanceTag.ANALOGY,
                blocking=True,
                resolution_status="blocked",
            ),
            normal_boiling_point=PureComponentProperty(
                property_id="mystery_feed_bp",
                identifier_id="mystery_feed",
                property_name="normal_boiling_point",
                value="160",
                units="C",
                provenance_method=ProvenanceTag.ANALOGY,
                blocking=True,
                resolution_status="blocked",
            ),
            melting_point=PureComponentProperty(
                property_id="mystery_feed_mp",
                identifier_id="mystery_feed",
                property_name="melting_point",
                value="25",
                units="C",
                provenance_method=ProvenanceTag.ANALOGY,
                blocking=False,
                resolution_status="estimated",
            ),
            blocked_properties=["molecular_weight", "normal_boiling_point"],
            resolution_status="blocked",
        )
        artifact = PropertyPackageArtifact(
            identifiers=[identifier],
            packages=[blocked_package],
            primary_identifier_ids=["mystery_feed"],
            unresolved_identifier_ids=["mystery_feed"],
            blocked_property_ids=["mystery_feed_molecular_weight", "mystery_feed_normal_boiling_point"],
            markdown="blocked package",
        )
        requirement_set = build_property_requirement_artifact(config, artifact)
        failures = requirement_failures_for_stage(requirement_set, "thermodynamic_feasibility", ["mystery_feed"])
        self.assertTrue(failures)
        self.assertTrue(any(item.property_name == "molecular_weight" for item in failures))

    def test_mixture_property_artifact_uses_component_packages(self):
        config = self._eg_config()
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        route = survey.routes[0]
        kinetics = reasoning.build_kinetic_assessment(config.basis, route, bundle.sources, bundle.corpus_excerpt)
        reaction_system = build_reaction_system(config.basis, route, kinetics, route.citations, route.assumptions)
        stream_table = build_stream_table(config.basis, route, reaction_system, route.citations, route.assumptions)
        property_packages = build_property_package_artifact(config, bundle, profile, survey)
        mixture_artifact = build_mixture_property_artifact(stream_table, property_packages)
        self.assertTrue(mixture_artifact.packages)
        reactor_package = next(item for item in mixture_artifact.packages if item.unit_id == "reactor")
        self.assertIsNotNone(reactor_package.liquid_heat_capacity_kj_kg_k)
        self.assertIsNotNone(reactor_package.liquid_density_kg_m3)
        self.assertIsNotNone(reactor_package.liquid_viscosity_pa_s)

    def test_missing_binary_interaction_pairs_surface_as_property_estimates(self):
        artifact = PropertyPackageArtifact(
            unresolved_binary_pairs=["water__ethylene_glycol"],
            unresolved_henry_pairs=["sulfur_dioxide__water"],
            unresolved_solubility_pairs=["sodium_bicarbonate__water"],
            identifiers=[
                ChemicalIdentifier(identifier_id="water", canonical_name="Water"),
                ChemicalIdentifier(identifier_id="ethylene_glycol", canonical_name="Ethylene Glycol"),
                ChemicalIdentifier(identifier_id="sulfur_dioxide", canonical_name="Sulfur dioxide"),
                ChemicalIdentifier(identifier_id="sodium_bicarbonate", canonical_name="Sodium bicarbonate"),
            ],
            markdown="estimates",
        )
        estimates = property_estimates_from_packages(artifact)
        self.assertTrue(estimates)
        self.assertTrue(any("Binary interaction parameters" in item.property_name for item in estimates))
        self.assertTrue(any("Henry's law constant" in item.property_name for item in estimates))
        self.assertTrue(any("Solubility curve" in item.property_name for item in estimates))
        self.assertTrue(all(not item.blocking for item in estimates))

    def test_pipeline_blocks_when_route_component_property_basis_is_missing(self):
        config = self._eg_config()
        runner = PipelineRunner(config)
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        artifact = build_property_package_artifact(config, bundle, profile, survey)
        blocked_package = next(
            item for item in artifact.packages if item.identifier.canonical_name.lower() == "ethylene oxide"
        )
        blocked_package.molecular_weight = PureComponentProperty(
            property_id="ethylene_oxide_molecular_weight",
            identifier_id=blocked_package.identifier.identifier_id,
            property_name="molecular_weight",
            value="unknown",
            units="g/mol",
            provenance_method=ProvenanceTag.ANALOGY,
            blocking=True,
            resolution_status="blocked",
        )
        if "molecular_weight" not in blocked_package.blocked_properties:
            blocked_package.blocked_properties.append("molecular_weight")
        blocked_package.resolution_status = "blocked"
        if "ethylene_oxide_molecular_weight" not in artifact.blocked_property_ids:
            artifact.blocked_property_ids.append("ethylene_oxide_molecular_weight")

        with patch("aoc.pipeline.build_property_package_artifact", return_value=artifact):
            while True:
                state = runner.run()
                if state.awaiting_gate_id:
                    runner.approve_gate(state.awaiting_gate_id, notes="property-engine test")
                    continue
                break
        self.assertEqual(state.run_status.value, "blocked")
        self.assertEqual(state.blocked_stage_id, "property_gap_resolution")
        inspect_output = runner.inspect()
        self.assertIn("blocked_property_ids:", inspect_output)
        self.assertIn("property_requirement_stage_failures:", inspect_output)


if __name__ == "__main__":
    unittest.main()
