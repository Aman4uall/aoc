import unittest

from aoc.document_facts import (
    build_document_fact_collection,
    build_document_process_options,
    extract_document_facts,
)
from aoc.models import ReactionParticipant, RouteOption, RouteSurveyArtifact
from aoc.route_chemistry import build_property_demand_plan, build_route_chemistry_artifact
from aoc.properties.models import ChemicalIdentifier, PropertyPackage, PropertyPackageArtifact, PureComponentProperty


class DocumentFactTests(unittest.TestCase):
    def test_extract_document_facts_finds_processes_and_site(self):
        text = """
        Process 1
        Isobutyl benzene and acetic anhydride are used. Yield of this process is 85%.

        Process 4
        Isobutyl benzene is raw material. Hydrogen peroxide oxidation gets Ibuprofen. Yield of the process is 88%.

        Process Selected
        On the basis of the above comparison Process 4 is selected.

        Suggested Site
        Ludhiana, Punjab

        Batch Scheduling
        Reactor R003 is a batch stirred tank reactor.

        Distillation Column-DC001
        Plug Flow Reactor-PFR
        """
        facts = extract_document_facts("user_doc_1", "Ibuprofen benchmark", text, "Ibuprofen")
        collection = build_document_fact_collection([facts])
        options = build_document_process_options([facts])

        self.assertEqual(collection.process_option_count, 2)
        self.assertIn("Process 4", collection.selected_process_labels)
        self.assertIn("Ludhiana", collection.selected_site_names)
        self.assertIn("batch", facts.operating_mode_hints)
        self.assertTrue(any(item.unit_tag == "DC001" for item in facts.equipment_mentions))
        self.assertTrue(any(item.unit_tag.startswith("PFR") for item in facts.equipment_mentions))
        self.assertEqual(len(options.options), 2)

    def test_route_chemistry_flags_generic_placeholders_and_named_species_plan(self):
        generic_route = RouteOption(
            route_id="generic_route_1",
            name="Generic primary route",
            reaction_equation="A + B -> P",
            participants=[
                ReactionParticipant(name="A", formula="CH4", coefficient=1.0, role="reactant", molecular_weight_g_mol=16.0),
                ReactionParticipant(name="B", formula="O2", coefficient=1.0, role="reactant", molecular_weight_g_mol=32.0),
                ReactionParticipant(name="P", formula="CH4O2", coefficient=1.0, role="product", molecular_weight_g_mol=48.0),
            ],
            operating_temperature_c=90.0,
            operating_pressure_bar=2.0,
            residence_time_hr=2.0,
            yield_fraction=0.85,
            selectivity_fraction=0.88,
            scale_up_notes="Generic seeded route.",
            route_score=8.0,
            rationale="Generic highest scoring route.",
            citations=["user_doc_1"],
        )
        survey = RouteSurveyArtifact(routes=[generic_route], markdown="generic", citations=["user_doc_1"])
        chemistry = build_route_chemistry_artifact(survey, [])
        self.assertIn("generic_route_1", chemistry.blocking_route_ids)
        self.assertGreaterEqual(chemistry.anonymous_species_count, 2)

        named_route = RouteOption(
            route_id="process_4",
            name="Process 4",
            reaction_equation="Isobutyl benzene + Hydrogen peroxide -> Ibuprofen",
            participants=[
                ReactionParticipant(name="Isobutyl benzene", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                ReactionParticipant(name="Hydrogen peroxide", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                ReactionParticipant(name="Ibuprofen", formula="", coefficient=1.0, role="product", molecular_weight_g_mol=0.0),
            ],
            route_origin="document",
            source_document_id="user_doc_1",
            evidence_score=0.9,
            chemistry_completeness_score=0.8,
            operating_temperature_c=80.0,
            operating_pressure_bar=3.0,
            residence_time_hr=4.0,
            yield_fraction=0.88,
            selectivity_fraction=0.9,
            scale_up_notes="Document-derived route.",
            route_score=8.8,
            rationale="Document selected process.",
            citations=["user_doc_1"],
        )
        named_chemistry = build_route_chemistry_artifact(RouteSurveyArtifact(routes=[named_route], markdown="", citations=["user_doc_1"]), [])
        self.assertEqual(named_chemistry.blocking_route_ids, [])
        self.assertEqual(named_chemistry.anonymous_species_count, 0)

        package_artifact = PropertyPackageArtifact(
            identifiers=[
                ChemicalIdentifier(identifier_id="isobutyl_benzene", canonical_name="Isobutyl benzene", source_ids=["user_doc_1"]),
                ChemicalIdentifier(identifier_id="hydrogen_peroxide", canonical_name="Hydrogen peroxide", source_ids=["user_doc_1"]),
                ChemicalIdentifier(identifier_id="ibuprofen", canonical_name="Ibuprofen", source_ids=["user_doc_1"]),
            ],
            packages=[
                PropertyPackage(
                    package_id="isobutyl_benzene_package",
                    identifier=ChemicalIdentifier(identifier_id="isobutyl_benzene", canonical_name="Isobutyl benzene", source_ids=["user_doc_1"]),
                    molecular_weight=PureComponentProperty(property_id="mw1", identifier_id="isobutyl_benzene", property_name="molecular_weight", value="134.22", units="g/mol", source_ids=["user_doc_1"]),
                    normal_boiling_point=PureComponentProperty(property_id="bp1", identifier_id="isobutyl_benzene", property_name="normal_boiling_point", value="170.0", units="C", source_ids=["user_doc_1"]),
                    melting_point=PureComponentProperty(property_id="mp1", identifier_id="isobutyl_benzene", property_name="melting_point", value="-20.0", units="C", source_ids=["user_doc_1"]),
                    liquid_density=PureComponentProperty(property_id="rho1", identifier_id="isobutyl_benzene", property_name="liquid_density", value="0.86", units="g/cm3", source_ids=["user_doc_1"]),
                    liquid_viscosity=PureComponentProperty(property_id="mu1", identifier_id="isobutyl_benzene", property_name="liquid_viscosity", value="0.001", units="Pa.s", source_ids=["user_doc_1"]),
                    liquid_heat_capacity=PureComponentProperty(property_id="cp1", identifier_id="isobutyl_benzene", property_name="liquid_heat_capacity", value="2.0", units="kJ/kg-K", source_ids=["user_doc_1"]),
                    heat_of_vaporization=PureComponentProperty(property_id="hv1", identifier_id="isobutyl_benzene", property_name="heat_of_vaporization", value="300.0", units="kJ/kg", source_ids=["user_doc_1"]),
                    thermal_conductivity=PureComponentProperty(property_id="k1", identifier_id="isobutyl_benzene", property_name="thermal_conductivity", value="0.15", units="W/m-K", source_ids=["user_doc_1"]),
                ),
                PropertyPackage(
                    package_id="hydrogen_peroxide_package",
                    identifier=ChemicalIdentifier(identifier_id="hydrogen_peroxide", canonical_name="Hydrogen peroxide", source_ids=["user_doc_1"]),
                    molecular_weight=PureComponentProperty(property_id="mw2", identifier_id="hydrogen_peroxide", property_name="molecular_weight", value="34.0", units="g/mol", source_ids=["user_doc_1"]),
                    normal_boiling_point=PureComponentProperty(property_id="bp2", identifier_id="hydrogen_peroxide", property_name="normal_boiling_point", value="150.0", units="C", source_ids=["user_doc_1"]),
                    melting_point=PureComponentProperty(property_id="mp2", identifier_id="hydrogen_peroxide", property_name="melting_point", value="-0.4", units="C", source_ids=["user_doc_1"]),
                    liquid_density=PureComponentProperty(property_id="rho2", identifier_id="hydrogen_peroxide", property_name="liquid_density", value="1.1", units="g/cm3", source_ids=["user_doc_1"]),
                    liquid_viscosity=PureComponentProperty(property_id="mu2", identifier_id="hydrogen_peroxide", property_name="liquid_viscosity", value="0.0012", units="Pa.s", source_ids=["user_doc_1"]),
                    liquid_heat_capacity=PureComponentProperty(property_id="cp2", identifier_id="hydrogen_peroxide", property_name="liquid_heat_capacity", value="2.6", units="kJ/kg-K", source_ids=["user_doc_1"]),
                    heat_of_vaporization=PureComponentProperty(property_id="hv2", identifier_id="hydrogen_peroxide", property_name="heat_of_vaporization", value="250.0", units="kJ/kg", source_ids=["user_doc_1"]),
                    thermal_conductivity=PureComponentProperty(property_id="k2", identifier_id="hydrogen_peroxide", property_name="thermal_conductivity", value="0.18", units="W/m-K", source_ids=["user_doc_1"]),
                ),
                PropertyPackage(
                    package_id="ibuprofen_package",
                    identifier=ChemicalIdentifier(identifier_id="ibuprofen", canonical_name="Ibuprofen", source_ids=["user_doc_1"]),
                    molecular_weight=PureComponentProperty(property_id="mw3", identifier_id="ibuprofen", property_name="molecular_weight", value="206.0", units="g/mol", source_ids=["user_doc_1"]),
                    normal_boiling_point=PureComponentProperty(property_id="bp3", identifier_id="ibuprofen", property_name="normal_boiling_point", value="300.0", units="C", source_ids=["user_doc_1"]),
                    melting_point=PureComponentProperty(property_id="mp3", identifier_id="ibuprofen", property_name="melting_point", value="76.0", units="C", source_ids=["user_doc_1"]),
                    liquid_density=PureComponentProperty(property_id="rho3", identifier_id="ibuprofen", property_name="liquid_density", value="1.03", units="g/cm3", source_ids=["user_doc_1"]),
                    liquid_viscosity=PureComponentProperty(property_id="mu3", identifier_id="ibuprofen", property_name="liquid_viscosity", value="0.002", units="Pa.s", source_ids=["user_doc_1"]),
                    liquid_heat_capacity=PureComponentProperty(property_id="cp3", identifier_id="ibuprofen", property_name="liquid_heat_capacity", value="2.1", units="kJ/kg-K", source_ids=["user_doc_1"]),
                    heat_of_vaporization=PureComponentProperty(property_id="hv3", identifier_id="ibuprofen", property_name="heat_of_vaporization", value="320.0", units="kJ/kg", source_ids=["user_doc_1"]),
                    thermal_conductivity=PureComponentProperty(property_id="k3", identifier_id="ibuprofen", property_name="thermal_conductivity", value="0.14", units="W/m-K", source_ids=["user_doc_1"]),
                ),
            ],
            markdown="",
            citations=["user_doc_1"],
        )
        demand = build_property_demand_plan(named_chemistry, package_artifact)
        self.assertEqual(demand.blocked_stage_ids, [])
        self.assertGreater(len(demand.items), 0)
