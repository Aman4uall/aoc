import unittest

from aoc.flowsheet_blueprint import build_unit_train_candidate_set, select_flowsheet_blueprint
from aoc.models import (
    CommercialProductBasisArtifact,
    EquipmentListArtifact,
    EquipmentSpec,
    DesignConfidenceArtifact,
    FlowsheetBlueprintArtifact,
    FlowsheetBlueprintStep,
    MarketAssessmentArtifact,
    ProductProfileArtifact,
    ProjectBasis,
    ReactionParticipant,
    RouteSelectionArtifact,
    RouteOption,
    RouteSurveyArtifact,
    SolveResult,
)
from aoc.properties.models import ChemicalIdentifier, PropertyPackage, PropertyPackageArtifact, PureComponentProperty
from aoc.properties import build_separation_thermo_artifact
from aoc.route_chemistry import build_property_demand_plan, build_route_chemistry_artifact
from aoc.route_families import build_route_family_artifact
from aoc.scientific_inference import (
    build_bac_purification_section_artifact,
    build_commercial_product_basis_artifact,
    build_design_confidence_artifact,
    build_economic_coverage_decision,
    build_kinetics_admissibility_artifact,
    build_reaction_network_v2_artifact,
    build_route_process_claims_artifact,
    build_species_resolution_artifact,
    build_thermo_admissibility_artifact,
    build_topology_candidate_artifact,
    build_unit_train_consistency_artifact,
)


def _route(
    route_id: str,
    name: str,
    *,
    participants: list[ReactionParticipant],
    separations: list[str],
    origin: str = "seeded",
    evidence_score: float = 0.85,
    family_hints: list[str] | None = None,
) -> RouteOption:
    return RouteOption(
        route_id=route_id,
        name=name,
        reaction_equation=" + ".join(item.name for item in participants if item.role == "reactant") + " -> " + next(item.name for item in participants if item.role == "product"),
        participants=participants,
        route_origin=origin,
        evidence_score=evidence_score,
        chemistry_completeness_score=0.90,
        separation_complexity_score=0.55,
        extracted_species=[item.name for item in participants],
        reaction_family_hints=family_hints or [],
        catalysts=[],
        operating_temperature_c=80.0,
        operating_pressure_bar=3.0,
        residence_time_hr=2.0,
        yield_fraction=0.90,
        selectivity_fraction=0.92,
        byproducts=[],
        separations=separations,
        scale_up_notes="test route",
        hazards=[],
        route_score=8.0,
        rationale="test",
        citations=["test_source"],
    )


def _package(identifier_id: str, canonical_name: str) -> PropertyPackage:
    identifier = ChemicalIdentifier(
        identifier_id=identifier_id,
        canonical_name=canonical_name,
        aliases=[canonical_name],
        formula="C2H6O2" if "glycol" in canonical_name.lower() else "H2O",
        source_ids=["test_source"],
    )
    return PropertyPackage(
        package_id=f"{identifier_id}_pkg",
        identifier=identifier,
        molecular_weight=PureComponentProperty(property_id=f"{identifier_id}_mw", identifier_id=identifier_id, property_name="molecular_weight", value="62.07", units="g/mol", source_ids=["test_source"]),
        normal_boiling_point=PureComponentProperty(property_id=f"{identifier_id}_bp", identifier_id=identifier_id, property_name="normal_boiling_point", value="197.3", units="C", source_ids=["test_source"]),
        melting_point=PureComponentProperty(property_id=f"{identifier_id}_mp", identifier_id=identifier_id, property_name="melting_point", value="-12.0", units="C", source_ids=["test_source"]),
        liquid_density=PureComponentProperty(property_id=f"{identifier_id}_rho", identifier_id=identifier_id, property_name="liquid_density", value="1110", units="kg/m3", source_ids=["test_source"]),
        liquid_heat_capacity=PureComponentProperty(property_id=f"{identifier_id}_cp", identifier_id=identifier_id, property_name="liquid_heat_capacity", value="2.4", units="kJ/kg-K", source_ids=["test_source"]),
        heat_of_vaporization=PureComponentProperty(property_id=f"{identifier_id}_hvap", identifier_id=identifier_id, property_name="heat_of_vaporization", value="800", units="kJ/kg", source_ids=["test_source"]),
    )


class ScientificInferenceTests(unittest.TestCase):
    def test_commercial_product_basis_normalizes_bac_sold_solution_vs_active_basis(self):
        basis = ProjectBasis(
            target_product="Benzalkonium chloride",
            capacity_tpa=50000,
            target_purity_wt_pct=50.0,
            operating_mode="continuous",
            throughput_basis="finished_product",
            nominal_active_wt_pct=50.0,
            product_form="50_wt_pct_solution",
            carrier_components=["water", "ethanol"],
            homolog_distribution={"c12": 0.4, "c14": 0.5, "c16": 0.1},
            quality_targets=["50 wt% active", "low residual benzyl chloride"],
        )
        product_profile = ProductProfileArtifact(
            product_name="Benzalkonium chloride",
            properties=[],
            uses=["disinfectant"],
            industrial_relevance="Commercial BAC solution sold on active-content basis.",
            safety_notes=["Corrosive and irritant"],
            commercial_basis_summary="50 wt% active BAC solution",
            nominal_active_wt_pct=50.0,
            product_form="50 wt% aqueous or alcohol solution",
            carrier_components=["water", "ethanol"],
            homolog_distribution={"c12": 0.4, "c14": 0.5, "c16": 0.1},
            quality_targets=["50 wt% active", "low residual benzyl chloride"],
            markdown="",
            citations=["test_source"],
            assumptions=[],
        )
        market = MarketAssessmentArtifact(
            estimated_price_per_kg=185.0,
            price_range="INR 170-200/kg",
            competitor_notes=[],
            demand_drivers=["institutional hygiene demand"],
            capacity_rationale="Benchmark BAC case on sold solution basis.",
            markdown="",
            citations=["test_source"],
            assumptions=[],
        )

        artifact = build_commercial_product_basis_artifact(basis, product_profile, market)

        self.assertAlmostEqual(artifact.active_fraction, 0.5, places=6)
        self.assertGreater(artifact.sold_solution_basis_kg_hr, artifact.active_basis_kg_hr)
        self.assertAlmostEqual(artifact.active_price_inr_per_kg, 370.0, places=2)
        self.assertIn("finished-solution dispatch", artifact.dispatch_mode)

    def test_species_resolution_filters_invalid_core_species(self):
        survey = RouteSurveyArtifact(
            routes=[
                _route(
                    "bad_route",
                    "Bad Route",
                    participants=[
                        ReactionParticipant(name="11 | Page", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                        ReactionParticipant(name="Ibuprofen", formula="", coefficient=1.0, role="product", molecular_weight_g_mol=206.0),
                    ],
                    separations=["distillation"],
                    origin="document",
                )
            ],
            markdown="",
            citations=["test_source"],
        )
        route_chemistry = build_route_chemistry_artifact(survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry, "bad_route")
        reaction_network = build_reaction_network_v2_artifact(route_chemistry, species_resolution, "bad_route")

        self.assertIn("bad_route", species_resolution.blocking_route_ids)
        self.assertIn("11 | Page", species_resolution.invalid_species_names)
        self.assertIn("bad_route", reaction_network.blocking_route_ids)

    def test_thermo_admissibility_passes_for_resolved_distillation_basis(self):
        route = _route(
            "good_route",
            "Good Route",
            participants=[
                ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.0),
                ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1.0, role="product", molecular_weight_g_mol=62.07),
            ],
            separations=["distillation purification"],
        )
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        property_packages = PropertyPackageArtifact(
            packages=[
                _package("water", "Water"),
                _package("ethylene_glycol", "Ethylene glycol"),
            ],
            markdown="",
            citations=["test_source"],
        )

        artifact = build_thermo_admissibility_artifact(
            survey,
            route_chemistry,
            property_packages,
            build_route_family_artifact(survey),
            selected_route_id="good_route",
        )

        self.assertEqual(artifact.selected_route_status.value, "pass")

    def test_kinetics_admissibility_blocks_unseen_high_criticality_route(self):
        route = _route(
            "oxidation_route",
            "Oxidation Route",
            participants=[
                ReactionParticipant(name="Isobutyl benzene", formula="C10H14", coefficient=1.0, role="reactant", molecular_weight_g_mol=134.2),
                ReactionParticipant(name="Ibuprofen", formula="C13H18O2", coefficient=1.0, role="product", molecular_weight_g_mol=206.0),
            ],
            separations=["distillation"],
            origin="document",
            evidence_score=0.55,
            family_hints=["oxidation"],
        )
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])

        artifact = build_kinetics_admissibility_artifact(
            survey,
            route_chemistry,
            selected_route_id="oxidation_route",
        )

        self.assertEqual(artifact.selected_route_status.value, "fail")

    def test_bac_property_demand_and_thermo_treat_active_as_nonvolatile_solution(self):
        route = _route(
            "bac_route",
            "BAC route",
            participants=[
                ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
            ],
            separations=["ethanol recovery", "light-ends stripping", "active dilution and polishing"],
            family_hints=["quaternization"],
        )
        route.solvents = ["Ethanol", "Water"]
        route.byproducts = ["trace benzyl alcohol from hydrolysis", "residual free amine", "residual benzyl chloride"]
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        packages = PropertyPackageArtifact(
            packages=[
                _package("alkyldimethylamine", "Alkyldimethylamine"),
                _package("benzyl_chloride", "Benzyl chloride"),
                _package("benzalkonium_chloride", "Benzalkonium chloride"),
                _package("ethanol", "Ethanol"),
                _package("water", "Water"),
                _package("benzyl_alcohol", "Benzyl alcohol"),
            ],
            markdown="",
            citations=["test_source"],
        )

        property_demand = build_property_demand_plan(route_chemistry, packages)
        thermo = build_thermo_admissibility_artifact(
            survey,
            route_chemistry,
            packages,
            build_route_family_artifact(survey),
            selected_route_id="bac_route",
        )

        distillation_demands = [
            item
            for item in property_demand.items
            if item.species_id == "benzalkonium_chloride" and item.stage_id == "distillation_design"
        ]
        self.assertEqual(distillation_demands, [])
        self.assertEqual(thermo.selected_route_status.value, "pass")
        self.assertTrue(any(section.separation_family in {"flash", "distillation"} for section in thermo.sections))
        self.assertTrue(any("solution-phase product" in section.rationale for section in thermo.sections))

    def test_bac_impurity_class_does_not_keep_species_and_topology_at_screening_only(self):
        route = _route(
            "bac_route",
            "BAC route",
            participants=[
                ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
            ],
            separations=["light-ends flashing", "vacuum polishing"],
            family_hints=["quaternization"],
        )
        route.solvents = ["Ethanol", "Water"]
        route.byproducts = ["residual free amine", "residual benzyl chloride", "color bodies"]
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry, "bac_route")
        reaction_network = build_reaction_network_v2_artifact(route_chemistry, species_resolution, "bac_route")
        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, build_route_family_artifact(survey), [], "continuous")
        topology = build_topology_candidate_artifact(candidate_set, species_resolution, reaction_network, selected_route_id="bac_route")

        self.assertEqual(species_resolution.routes[0].status.value, "pass")
        self.assertEqual(reaction_network.routes[0].status.value, "pass")
        self.assertEqual(topology.candidates[0].status.value, "pass")

    def test_bac_purification_sections_capture_concentration_and_recovery_basis(self):
        route = _route(
            "bac_route",
            "BAC route",
            participants=[
                ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
            ],
            separations=["ethanol recovery", "volatile cleanup", "product polishing"],
            family_hints=["quaternization"],
        )
        route.solvents = ["Ethanol", "Water"]
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        route_families = build_route_family_artifact(survey)
        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, route_families, [], "continuous")
        blueprint = select_flowsheet_blueprint(candidate_set, "bac_route")
        packages = PropertyPackageArtifact(
            packages=[
                _package("alkyldimethylamine", "Alkyldimethylamine"),
                _package("benzyl_chloride", "Benzyl chloride"),
                _package("benzalkonium_chloride", "Benzalkonium chloride"),
                _package("ethanol", "Ethanol"),
                _package("water", "Water"),
            ],
            markdown="",
            citations=["test_source"],
        )
        separation_thermo = build_separation_thermo_artifact(route, packages, "Benzalkonium chloride", "extractive_distillation_train")
        route_selection = RouteSelectionArtifact(
            selected_route_id="bac_route",
            justification="selected for test",
            comparison_markdown="",
            citations=["test_source"],
            assumptions=[],
        )

        artifact = build_bac_purification_section_artifact(route_selection, blueprint, separation_thermo)

        self.assertIsNotNone(artifact)
        section_ids = {section.section_id for section in artifact.sections}
        self.assertIn("concentration", section_ids)
        self.assertIn("purification", section_ids)
        concentration = next(section for section in artifact.sections if section.section_id == "concentration")
        self.assertIn("Ethanol", concentration.key_species)

    def test_unit_train_consistency_blocks_legacy_solids_units_for_bac(self):
        route = _route(
            "bac_route",
            "BAC route",
            participants=[
                ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
            ],
            separations=["volatile cleanup", "product polishing"],
            family_hints=["quaternization"],
        )
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        blueprint = select_flowsheet_blueprint(
            build_unit_train_candidate_set(survey, route_chemistry, build_route_family_artifact(survey), [], "continuous"),
            "bac_route",
        )
        equipment_list = EquipmentListArtifact(
            items=[
                EquipmentSpec(
                    equipment_id="R-101",
                    equipment_type="reactor",
                    service="Quaternization reactor",
                    design_basis="test",
                    volume_m3=10.0,
                    design_temperature_c=90.0,
                    design_pressure_bar=4.0,
                    material_of_construction="SS316",
                ),
                EquipmentSpec(
                    equipment_id="CRYS-201",
                    equipment_type="crystallizer",
                    service="Legacy solids train artifact",
                    design_basis="test",
                    volume_m3=4.0,
                    design_temperature_c=40.0,
                    design_pressure_bar=1.5,
                    material_of_construction="SS316",
                ),
            ],
            citations=["test_source"],
            assumptions=[],
        )

        artifact = build_unit_train_consistency_artifact(blueprint, equipment_list=equipment_list)

        self.assertEqual(artifact.overall_status, "blocked")
        self.assertIn("equipment_list", artifact.blocking_artifact_refs)

    def test_bac_design_confidence_upgrades_to_method_derived_with_solver_supported_major_units(self):
        route = _route(
            "bac_route",
            "BAC route",
            participants=[
                ReactionParticipant(name="Alkyldimethylamine", formula="C16H35N", coefficient=1.0, role="reactant", molecular_weight_g_mol=241.46, phase="liquid"),
                ReactionParticipant(name="Benzyl chloride", formula="C7H7Cl", coefficient=1.0, role="reactant", molecular_weight_g_mol=126.58, phase="liquid"),
                ReactionParticipant(name="Benzalkonium chloride", formula="C23H42ClN", coefficient=1.0, role="product", molecular_weight_g_mol=368.04, phase="liquid"),
            ],
            separations=["light-ends flashing", "vacuum polishing"],
            family_hints=["quaternization"],
        )
        route.solvents = ["Ethanol", "Water"]
        route.byproducts = ["residual free amine", "residual benzyl chloride", "color bodies"]
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry, "bac_route")
        reaction_network = build_reaction_network_v2_artifact(route_chemistry, species_resolution, "bac_route")
        route_families = build_route_family_artifact(survey)
        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, route_families, [], "continuous")
        topology = build_topology_candidate_artifact(candidate_set, species_resolution, reaction_network, selected_route_id="bac_route")
        blueprint = next(item for item in candidate_set.blueprints if item.route_id == "bac_route")
        packages = PropertyPackageArtifact(
            packages=[
                _package("alkyldimethylamine", "Alkyldimethylamine"),
                _package("benzyl_chloride", "Benzyl chloride"),
                _package("benzalkonium_chloride", "Benzalkonium chloride"),
                _package("ethanol", "Ethanol"),
                _package("water", "Water"),
            ],
            markdown="",
            citations=["test_source"],
        )
        thermo = build_thermo_admissibility_artifact(
            survey,
            route_chemistry,
            packages,
            route_families,
            selected_route_id="bac_route",
        )
        kinetics = build_kinetics_admissibility_artifact(
            survey,
            route_chemistry,
            selected_route_id="bac_route",
            kinetic_assessment=type("KineticAssessment", (), {"activation_energy_kj_mol": 58.0})(),
        )
        unit_ids = [step.solver_anchor_unit_id or step.unit_id for step in blueprint.steps]
        solve_result = SolveResult(
            case_id="bac_case",
            convergence_status="converged",
            unitwise_status={unit_id: "converged" for unit_id in unit_ids},
            unitwise_coverage_status={unit_id: "complete" for unit_id in unit_ids},
            unitwise_blockers={},
            unitwise_unresolved_sensitivities={},
            markdown="",
        )

        design_confidence = build_design_confidence_artifact(
            selected_route_id="bac_route",
            topology_candidates=topology,
            thermo_admissibility=thermo,
            kinetics_admissibility=kinetics,
            flowsheet_blueprint=blueprint,
            solve_result=solve_result,
        )

        reactor_unit = next(unit for unit in design_confidence.units if unit.unit_id == "reactor")
        separation_unit = next(unit for unit in design_confidence.units if unit.unit_id == "primary_separation")
        self.assertEqual(design_confidence.overall_confidence.value, "method_derived")
        self.assertEqual(reactor_unit.confidence.value, "method_derived")
        self.assertEqual(separation_unit.confidence.value, "method_derived")

    def test_topology_and_economic_coverage_respect_screening_vs_blocked(self):
        route = _route(
            "good_route",
            "Good Route",
            participants=[
                ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.0),
                ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1.0, role="product", molecular_weight_g_mol=62.07),
            ],
            separations=["distillation purification"],
        )
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        species_resolution = build_species_resolution_artifact(route_chemistry, "good_route")
        reaction_network = build_reaction_network_v2_artifact(route_chemistry, species_resolution, "good_route")
        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, build_route_family_artifact(survey), [], "continuous")
        topology = build_topology_candidate_artifact(candidate_set, species_resolution, reaction_network, selected_route_id="good_route")
        design_confidence = DesignConfidenceArtifact(selected_route_id="good_route", overall_confidence="blocked", blocked_unit_ids=["reactor"], units=[], markdown="")

        economic_coverage = build_economic_coverage_decision(
            route_id="good_route",
            route_economic_basis=type("RouteEconomicBasis", (), {"coverage_status": "grounded"})(),
            route_site_fit=object(),
            design_confidence=design_confidence,
        )

        self.assertTrue(topology.screening_balance_allowed)
        self.assertEqual(economic_coverage.status, "blocked")

    def test_route_process_claims_emit_recycle_impurity_and_waste_facts(self):
        route = _route(
            "cleanup_route",
            "Cleanup Route",
            participants=[
                ReactionParticipant(name="Phenol", formula="C6H6O", coefficient=1.0, role="product", molecular_weight_g_mol=94.11),
                ReactionParticipant(name="Benzene", formula="C6H6", coefficient=1.0, role="reactant", molecular_weight_g_mol=78.11),
            ],
            separations=["caustic wash", "solvent recovery", "phenol distillation"],
            family_hints=["oxidation"],
        )
        route.byproducts = ["saline purge", "catechol", "tar"]
        route.catalysts = ["Oxidation catalyst"]
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["test_source"])
        route_chemistry = build_route_chemistry_artifact(survey, [])
        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, build_route_family_artifact(survey), [], "continuous")

        claims = build_route_process_claims_artifact(survey, route_chemistry, candidate_set)

        self.assertTrue(claims.claims)
        claim_types = {claim.claim_type for claim in claims.claims}
        self.assertEqual(claim_types, {"reagent_recycle", "impurity_classes", "cleanup_sequence", "waste_modes"})
        waste_claim = next(claim for claim in claims.claims if claim.claim_type == "waste_modes")
        impurity_claim = next(claim for claim in claims.claims if claim.claim_type == "impurity_classes")
        self.assertIn("aqueous_treatment", waste_claim.items)
        self.assertIn("heavy_organics", impurity_claim.items)


if __name__ == "__main__":
    unittest.main()
