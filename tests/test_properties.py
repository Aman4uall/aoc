import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aoc.calculators import build_reaction_system, build_stream_table
from aoc.config import load_project_config
from aoc.models import (
    ColumnDesign,
    ModelSettings,
    ProductProfileArtifact,
    ProjectBasis,
    ProjectConfig,
    ProvenanceTag,
    ReactionParticipant,
    ReactorDesign,
    RouteOption,
    RouteSurveyArtifact,
)
from aoc.pipeline import PipelineRunner
from aoc.properties import (
    build_mixture_property_artifact,
    build_property_method_decision,
    build_property_package_artifact,
    build_property_requirement_artifact,
    build_section_separation_thermo_artifact,
    build_separation_thermo_artifact,
    property_value_records,
    property_estimates_from_packages,
    requirement_failures_for_stage,
)
from aoc.properties.models import ChemicalIdentifier, MixturePropertyArtifact, PropertyPackage, PropertyPackageArtifact, PureComponentProperty
from aoc.properties.sources import collect_identifier_specs
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager
from aoc.route_chemistry import build_route_chemistry_artifact
from aoc.route_families import build_route_family_artifact
from aoc.scientific_inference import build_thermo_admissibility_artifact


class PropertyEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aoc-properties-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _eg_config(self) -> ProjectConfig:
        config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        config.output_root = self.temp_dir
        return config

    def _bac_config(self) -> ProjectConfig:
        return ProjectConfig(
            project_id="benzalkonium-chloride-property-test",
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
            ),
            model=ModelSettings(backend="mock", model_name="gemini-3.1-pro-preview", temperature=0.2),
        )

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

    def test_collect_identifier_specs_filters_noise_fragments(self):
        profile = ProductProfileArtifact(
            product_name="Ibuprofen",
            properties=[],
            uses=[],
            industrial_relevance="test",
            safety_notes=[],
            markdown="",
        )
        survey = RouteSurveyArtifact(
            routes=[
                RouteOption(
                    route_id="doc_route",
                    name="Document route",
                    reaction_equation="Isobutyl benzene + Hydrogen peroxide -> Ibuprofen",
                    participants=[
                        ReactionParticipant(name="Isobutyl benzene", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="11 | P a g e", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="3100psig", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="and acetic anhydride", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="as Boots-Hoechst-Celanese ibuprofen", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="make ibuprofen", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="such as water", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="Ibuprofen", formula="", coefficient=1.0, role="product", molecular_weight_g_mol=0.0),
                    ],
                    route_score=1.0,
                    operating_temperature_c=25.0,
                    operating_pressure_bar=1.0,
                    residence_time_hr=1.0,
                    yield_fraction=0.8,
                    selectivity_fraction=0.8,
                    scale_up_notes="test",
                    rationale="test",
                    citations=["user_doc_1"],
                )
            ],
            markdown="",
            citations=["user_doc_1"],
        )
        specs = collect_identifier_specs(profile, survey)
        names = [item["canonical_name"] for item in specs]
        self.assertIn("Ibuprofen", names)
        self.assertIn("Isobutyl benzene", names)
        self.assertNotIn("11 | P a g e", names)
        self.assertNotIn("3100psig", names)
        self.assertNotIn("and acetic anhydride", names)
        self.assertNotIn("as Boots-Hoechst-Celanese ibuprofen", names)
        self.assertNotIn("make ibuprofen", names)
        self.assertNotIn("such as water", names)

    def test_collect_identifier_specs_include_bac_carriers_solvents_and_known_byproducts(self):
        profile = ProductProfileArtifact(
            product_name="Benzalkonium chloride",
            properties=[],
            uses=[],
            industrial_relevance="test",
            safety_notes=[],
            carrier_components=["water", "ethanol"],
            markdown="",
        )
        survey = RouteSurveyArtifact(
            routes=[
                RouteOption(
                    route_id="bac_route",
                    name="BAC route",
                    reaction_equation="Alkyldimethylamine + Benzyl chloride -> Benzalkonium chloride",
                    participants=[
                        ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46),
                        ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58),
                        ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04),
                    ],
                    solvents=["Ethanol", "Water"],
                    byproducts=["trace benzyl alcohol from hydrolysis", "residual free amine"],
                    route_score=9.0,
                    operating_temperature_c=80.0,
                    operating_pressure_bar=2.0,
                    residence_time_hr=2.0,
                    yield_fraction=0.95,
                    selectivity_fraction=0.96,
                    scale_up_notes="test",
                    rationale="test",
                    citations=["seed_1"],
                )
            ],
            markdown="",
            citations=["seed_1"],
        )
        specs = collect_identifier_specs(profile, survey)
        names = {item["canonical_name"].lower() for item in specs}
        self.assertIn("benzalkonium chloride", names)
        self.assertIn("water", names)
        self.assertIn("ethanol", names)
        self.assertIn("benzyl alcohol", names)

    def test_bac_formulated_product_profile_does_not_override_active_nonvolatile_basis(self):
        config = self._bac_config()
        config.output_root = self.temp_dir
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_packages = build_property_package_artifact(config, bundle, profile, survey)

        bac_package = next(item for item in property_packages.packages if item.identifier.identifier_id == "benzalkonium_chloride")

        self.assertGreater(float(bac_package.normal_boiling_point.value), 900.0)
        self.assertEqual(float(bac_package.heat_of_vaporization.value), 0.0)

    def test_bac_selected_cleanup_pair_uses_volatile_cleanup_not_active_distillation(self):
        config = self._bac_config()
        config.output_root = self.temp_dir
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        route = next(item for item in survey.routes if item.route_id == "benzyl_chloride_quaternization_high_strength")
        property_packages = build_property_package_artifact(config, bundle, profile, survey)
        separation_thermo = build_separation_thermo_artifact(
            route,
            property_packages,
            config.basis.target_product,
            "extractive_distillation_train",
        )
        route_chemistry = build_route_chemistry_artifact(survey, [])
        thermo_admissibility = build_thermo_admissibility_artifact(
            survey,
            route_chemistry,
            property_packages,
            build_route_family_artifact(survey),
            selected_route_id=route.route_id,
            separation_thermo=separation_thermo,
            property_method=build_property_method_decision(route, property_packages),
        )

        self.assertEqual(separation_thermo.light_key, "Benzyl chloride")
        self.assertEqual(separation_thermo.heavy_key, "Alkyldimethylamine")
        self.assertTrue(separation_thermo.relative_volatility.feasible)
        self.assertEqual(separation_thermo.activity_model, "nrtl_family_estimated_modified_raoult")
        self.assertEqual(separation_thermo.missing_binary_pairs, [])
        bac_top = next(item for item in separation_thermo.top_k_values if item.identifier_id == "benzalkonium_chloride")
        self.assertLess(bac_top.k_value, 1e-6)
        self.assertIn("nonvolatile", bac_top.method)
        self.assertEqual(thermo_admissibility.selected_route_status.value, "pass")

    def test_bac_section_specific_cleanup_pair_tracks_purification_feed(self):
        config = self._bac_config()
        config.output_root = self.temp_dir
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        route = next(item for item in survey.routes if item.route_id == "benzyl_chloride_quaternization_high_strength")
        property_packages = build_property_package_artifact(config, bundle, profile, survey)

        section_thermo = build_section_separation_thermo_artifact(
            route,
            property_packages,
            config.basis.target_product,
            ["Benzalkonium chloride", "Benzyl chloride", "Alkyldimethylamine", "Ethanol"],
            "distillation_train",
            section_id="purification",
        )

        self.assertEqual(section_thermo.light_key, "Benzyl chloride")
        self.assertEqual(section_thermo.heavy_key, "Alkyldimethylamine")
        self.assertEqual(section_thermo.activity_model, "nrtl_family_estimated_modified_raoult")
        self.assertGreater(section_thermo.relative_volatility.average_alpha, 1.0)

    def test_bac_distillation_design_stays_liquid_purification_when_distillation_is_selected(self):
        config = self._bac_config()
        config.output_root = self.temp_dir
        runner = PipelineRunner(config)

        for _ in range(24):
            state = runner.run()
            if state.awaiting_gate_id == "equipment_basis":
                break
            if state.awaiting_gate_id:
                runner.approve_gate(state.awaiting_gate_id, notes="BAC separation-basis test")
                continue
            break

        self.assertIsNone(state.blocked_stage_id, f"BAC run blocked early at {state.blocked_stage_id}")
        self.assertEqual(state.awaiting_gate_id, "equipment_basis")
        column = runner._load("column_design", ColumnDesign)
        self.assertIn("distillation", column.service.lower())
        self.assertNotIn("crystallizer", column.service.lower())

    def test_bac_reactor_design_uses_liquid_density_basis_and_bounded_residence(self):
        config = self._bac_config()
        config.output_root = self.temp_dir
        runner = PipelineRunner(config)

        for _ in range(24):
            state = runner.run()
            if state.awaiting_gate_id == "equipment_basis":
                break
            if state.awaiting_gate_id:
                runner.approve_gate(state.awaiting_gate_id, notes="BAC reactor-basis test")
                continue
            break

        self.assertIsNone(state.blocked_stage_id, f"BAC run blocked early at {state.blocked_stage_id}")
        self.assertEqual(state.awaiting_gate_id, "equipment_basis")
        reactor = runner._load("reactor_design", ReactorDesign)
        mixture_artifact = runner._load("mixture_properties", MixturePropertyArtifact)
        reactor_package = next(item for item in mixture_artifact.packages if item.unit_id == "reactor")

        self.assertGreater(reactor_package.liquid_density_kg_m3, 900.0)
        self.assertLessEqual(reactor.residence_time_hr, 4.1)
        self.assertLess(reactor.design_volume_m3, 100.0)

    def test_property_value_records_can_be_filtered_by_property_demand(self):
        artifact = PropertyPackageArtifact(
            identifiers=[
                ChemicalIdentifier(identifier_id="ibuprofen", canonical_name="Ibuprofen", source_ids=["user_doc_1"]),
            ],
            packages=[
                PropertyPackage(
                    package_id="ibuprofen_package",
                    identifier=ChemicalIdentifier(identifier_id="ibuprofen", canonical_name="Ibuprofen", source_ids=["user_doc_1"]),
                    molecular_weight=PureComponentProperty(property_id="mw", identifier_id="ibuprofen", property_name="molecular_weight", value="206", units="g/mol", source_ids=["user_doc_1"]),
                    normal_boiling_point=PureComponentProperty(property_id="bp", identifier_id="ibuprofen", property_name="normal_boiling_point", value="300", units="C", source_ids=["user_doc_1"]),
                    melting_point=PureComponentProperty(property_id="mp", identifier_id="ibuprofen", property_name="melting_point", value="76", units="C", source_ids=["user_doc_1"]),
                    liquid_density=PureComponentProperty(property_id="rho", identifier_id="ibuprofen", property_name="liquid_density", value="1.03", units="g/cm3", source_ids=["user_doc_1"]),
                    liquid_viscosity=PureComponentProperty(property_id="mu", identifier_id="ibuprofen", property_name="liquid_viscosity", value="0.002", units="Pa.s", source_ids=[]),
                    liquid_heat_capacity=PureComponentProperty(property_id="cp", identifier_id="ibuprofen", property_name="liquid_heat_capacity", value="2.1", units="kJ/kg-K", source_ids=[]),
                    heat_of_vaporization=PureComponentProperty(property_id="hv", identifier_id="ibuprofen", property_name="heat_of_vaporization", value="320", units="kJ/kg", source_ids=[]),
                    thermal_conductivity=PureComponentProperty(property_id="k", identifier_id="ibuprofen", property_name="thermal_conductivity", value="0.14", units="W/m-K", source_ids=[]),
                )
            ],
            markdown="",
        )
        demand = type("Demand", (), {"items": [type("Item", (), {"species_id": "ibuprofen", "property_name": "molecular_weight"})(), type("Item", (), {"species_id": "ibuprofen", "property_name": "normal_boiling_point"})()]})()
        records = property_value_records(artifact, demand)
        self.assertEqual({record.name for record in records}, {"Ibuprofen Molecular weight", "Ibuprofen Normal boiling point"})

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
