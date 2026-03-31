import unittest

from aoc.calculators import build_reaction_system, build_stream_table
from aoc.models import (
    FlowsheetBlueprintArtifact,
    FlowsheetBlueprintStep,
    KineticAssessmentArtifact,
    ProcessTemplate,
    ProjectBasis,
    ReactionParticipant,
    RouteOption,
)
from aoc.solvers.convergence import solve_multi_component_recycle_loop


class FlowsheetSequenceTests(unittest.TestCase):
    def test_multi_component_recycle_loop_solves_each_component(self):
        results = solve_multi_component_recycle_loop(
            target_total_flows={"Water": 100.0, "EO": 10.0},
            consumed_flows={"Water": 5.0, "EO": 9.0},
            recovery_fractions={"Water": 0.95, "EO": 0.60},
            purge_fractions={"Water": 0.03, "EO": 0.10},
        )
        self.assertIn("Water", results)
        self.assertIn("EO", results)
        self.assertGreater(results["Water"]["recycle_flow"], results["EO"]["recycle_flow"])
        self.assertLess(results["EO"]["fresh_flow"], 10.0)

    def test_distillation_family_sequence_builds_explicit_recycle(self):
        basis = ProjectBasis(
            target_product="Ethylene Glycol",
            capacity_tpa=200000,
            target_purity_wt_pct=99.9,
            process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
            india_only=True,
        )
        route = RouteOption(
            route_id="eo_hydration",
            name="Ethylene oxide hydration",
            reaction_equation="C2H4O + H2O -> C2H6O2",
            participants=[
                ReactionParticipant(name="Ethylene oxide", formula="C2H4O", coefficient=1, role="reactant", molecular_weight_g_mol=44.05, phase="liquid"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1, role="product", molecular_weight_g_mol=62.07, phase="liquid"),
            ],
            operating_temperature_c=190,
            operating_pressure_bar=14,
            residence_time_hr=0.75,
            yield_fraction=0.92,
            selectivity_fraction=0.93,
            byproducts=["Diethylene glycol", "Triethylene glycol"],
            catalysts=["none"],
            separations=["EO flash", "Water removal", "Vacuum distillation", "Heavy glycol split"],
            scale_up_notes="",
            route_score=9.5,
            rationale="",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        recycle_streams = [stream for stream in stream_table.streams if stream.destination_unit_id == "feed_prep" and stream.source_unit_id != "battery_limits"]
        self.assertTrue(recycle_streams)
        self.assertTrue(any(stream.stream_id == "S-301" for stream in recycle_streams))
        self.assertLess(stream_table.closure_error_pct, 2.0)
        self.assertTrue(any(trace.trace_id == "sequence_recycle_components" for trace in stream_table.calc_traces))
        self.assertTrue(any(trace.trace_id == "sequence_byproduct_closure" for trace in stream_table.calc_traces))
        self.assertGreaterEqual(len(stream_table.streams), 9)
        component_names = {component.name for stream in stream_table.streams for component in stream.components}
        self.assertTrue({"Diethylene glycol", "Triethylene glycol"} & component_names)
        self.assertNotIn("Heavy ends", component_names)
        self.assertTrue(stream_table.phase_split_specs)
        self.assertTrue(stream_table.separator_performances)
        self.assertTrue(stream_table.separation_packets[0].component_split_to_product)
        self.assertTrue(stream_table.separation_packets[0].dominant_product_phase)
        self.assertIn(stream_table.separation_packets[0].split_status, {"converged", "estimated"})
        self.assertTrue(stream_table.sections)
        self.assertTrue(any(section.section_id.startswith("purification") for section in stream_table.sections))
        self.assertTrue(any("Vacuum distillation" in section.label for section in stream_table.sections))
        self.assertTrue(any(stream.stream_role == "side_draw" for stream in stream_table.streams))
        self.assertTrue(any(packet.side_draw_stream_ids for packet in stream_table.separation_packets))
        self.assertGreaterEqual(len(stream_table.recycle_packets), 2)
        self.assertEqual(len(stream_table.convergence_summaries), len(stream_table.recycle_packets))
        self.assertTrue({"concentration_recycle_loop", "purification_recycle_loop"}.issubset({packet.loop_id for packet in stream_table.recycle_packets}))
        self.assertTrue(all(packet.purge_policy_by_family for packet in stream_table.recycle_packets))
        self.assertTrue(stream_table.recycle_packets[0].component_convergence_error_pct)
        self.assertTrue(all(error <= 95.0 for error in stream_table.recycle_packets[0].component_convergence_error_pct.values()))

    def test_solids_family_sequence_preserves_solids_path(self):
        basis = ProjectBasis(
            target_product="Sodium Bicarbonate",
            capacity_tpa=50000,
            target_purity_wt_pct=99.0,
            process_template=ProcessTemplate.GENERIC_SMALL_MOLECULE,
            india_only=True,
        )
        route = RouteOption(
            route_id="soda_ash_carboxylation",
            name="Soda ash carbonation",
            reaction_equation="Na2CO3 + CO2 + H2O -> 2 NaHCO3",
            participants=[
                ReactionParticipant(name="Soda ash", formula="Na2CO3", coefficient=1.0, role="reactant", molecular_weight_g_mol=105.99, phase="solid"),
                ReactionParticipant(name="Carbon dioxide", formula="CO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.01, phase="gas"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Sodium bicarbonate", formula="NaHCO3", coefficient=2.0, role="product", molecular_weight_g_mol=84.01, phase="solid"),
            ],
            operating_temperature_c=40.0,
            operating_pressure_bar=3.0,
            residence_time_hr=2.4,
            yield_fraction=0.93,
            selectivity_fraction=0.97,
            catalysts=[],
            separations=["crystallization", "filtration", "drying"],
            scale_up_notes="",
            route_score=9.1,
            rationale="",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=38.0,
            pre_exponential_factor=7.5e5,
            apparent_order=1.0,
            design_residence_time_hr=2.4,
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        product_stream = next(stream for stream in stream_table.streams if stream.stream_id == "S-402")
        self.assertEqual(product_stream.phase_hint, "solid")
        self.assertTrue(any(spec.mechanism == "solid_liquid_partition" for spec in stream_table.phase_split_specs))
        self.assertTrue(any(stream.stream_id == "S-301" and stream.destination_unit_id == "feed_prep" for stream in stream_table.streams))
        self.assertTrue(any(stream.stream_id == "S-351" and stream.destination_unit_id == "concentration" for stream in stream_table.streams))
        self.assertTrue(any(packet.recycle_target_unit_id == "concentration" for packet in stream_table.recycle_packets))
        self.assertLess(stream_table.closure_error_pct, 5.0)

    def test_generic_cleanup_route_expands_descriptor_driven_topology(self):
        basis = ProjectBasis(
            target_product="Ethylene Glycol",
            capacity_tpa=200000,
            target_purity_wt_pct=99.9,
            process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
            india_only=True,
        )
        route = RouteOption(
            route_id="omega_catalytic",
            name="OMEGA catalytic route",
            reaction_equation="C2H4O + H2O -> C2H6O2",
            participants=[
                ReactionParticipant(name="Ethylene oxide", formula="C2H4O", coefficient=1, role="reactant", molecular_weight_g_mol=44.05, phase="liquid"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1, role="product", molecular_weight_g_mol=62.07, phase="liquid"),
            ],
            operating_temperature_c=185,
            operating_pressure_bar=20,
            residence_time_hr=1.0,
            yield_fraction=0.96,
            selectivity_fraction=0.97,
            byproducts=["Trace heavy glycols"],
            catalysts=["CO2 catalytic loop"],
            separations=["Carbonate loop cleanup", "Hydrolysis", "Low-water purification"],
            scale_up_notes="",
            route_score=9.4,
            rationale="",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=62.0,
            pre_exponential_factor=3.5e7,
            apparent_order=1.0,
            design_residence_time_hr=1.0,
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])

        self.assertTrue(any(section.section_id.startswith("recycle_recovery") for section in stream_table.sections))
        self.assertTrue(any("Carbonate loop cleanup" in section.label for section in stream_table.sections))
        self.assertTrue(any(stream.stream_id == "S-203" and stream.destination_unit_id == "recycle_recovery" for stream in stream_table.streams))
        self.assertTrue(any(stream.stream_id == "S-301" and stream.destination_unit_id == "purification" for stream in stream_table.streams))
        purification_packet = next(packet for packet in stream_table.separation_packets if packet.unit_id == "purification")
        self.assertIn(purification_packet.split_status, {"converged", "estimated"})
        self.assertLess(purification_packet.split_closure_pct, 5.0)

    def test_blueprint_overrides_sparse_route_into_solids_sequence(self):
        basis = ProjectBasis(
            target_product="Specialty salt",
            capacity_tpa=12000,
            target_purity_wt_pct=99.0,
            process_template=ProcessTemplate.GENERIC_SMALL_MOLECULE,
            india_only=True,
        )
        route = RouteOption(
            route_id="solid_specialty_route",
            name="Solid specialty route",
            reaction_equation="A + B -> P",
            participants=[
                ReactionParticipant(name="Feed A", formula="A", coefficient=1.0, role="reactant", molecular_weight_g_mol=80.0, phase="liquid"),
                ReactionParticipant(name="Feed B", formula="B", coefficient=1.0, role="reactant", molecular_weight_g_mol=55.0, phase="liquid"),
                ReactionParticipant(name="Product P", formula="P", coefficient=1.0, role="product", molecular_weight_g_mol=120.0, phase="solid"),
            ],
            operating_temperature_c=55.0,
            operating_pressure_bar=2.0,
            residence_time_hr=3.0,
            yield_fraction=0.90,
            selectivity_fraction=0.95,
            catalysts=[],
            separations=[],
            scale_up_notes="",
            route_score=7.8,
            rationale="",
            citations=["s1"],
        )
        blueprint = FlowsheetBlueprintArtifact(
            blueprint_id="solid_specialty_bp",
            route_id=route.route_id,
            route_name=route.name,
            steps=[
                FlowsheetBlueprintStep(
                    step_id="feed_prep",
                    route_id=route.route_id,
                    section_id="feed_handling",
                    section_label="Feed handling",
                    step_role="feed_preparation",
                    unit_id="feed_prep",
                    solver_anchor_unit_id="feed_prep",
                    unit_type="feed_preparation",
                    service="Feed charging",
                ),
                FlowsheetBlueprintStep(
                    step_id="reactor",
                    route_id=route.route_id,
                    section_id="reaction",
                    section_label="Reaction",
                    step_role="reaction",
                    unit_id="reactor",
                    solver_anchor_unit_id="reactor",
                    unit_type="batch_stirred_reactor",
                    service="Main reaction",
                ),
                FlowsheetBlueprintStep(
                    step_id="concentration",
                    route_id=route.route_id,
                    section_id="concentration",
                    section_label="Crystallization",
                    step_role="primary_separation",
                    unit_id="concentration",
                    solver_anchor_unit_id="concentration",
                    unit_type="crystallizer",
                    service="Crystallization and slurry hold",
                    separation_basis_ref="crystallization",
                    phase_basis="solid-liquid split",
                ),
                FlowsheetBlueprintStep(
                    step_id="filtration",
                    route_id=route.route_id,
                    section_id="solids_finishing",
                    section_label="Solids finishing",
                    step_role="filtration",
                    unit_id="filtration",
                    solver_anchor_unit_id="filtration",
                    unit_type="filtration",
                    service="Filtration",
                    separation_basis_ref="filtration",
                    phase_basis="solid-liquid split",
                ),
                FlowsheetBlueprintStep(
                    step_id="drying",
                    route_id=route.route_id,
                    section_id="solids_finishing",
                    section_label="Solids finishing",
                    step_role="drying",
                    unit_id="drying",
                    solver_anchor_unit_id="drying",
                    unit_type="drying",
                    service="Drying",
                    phase_basis="solid finishing",
                ),
            ],
            markdown="solid blueprint",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=32.0,
            pre_exponential_factor=1.2e6,
            apparent_order=1.0,
            design_residence_time_hr=3.0,
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [], flowsheet_blueprint=blueprint)

        self.assertTrue(any("Route-derived flowsheet blueprint overrides" in item for item in stream_table.assumptions))
        self.assertIn("solids", " ".join(stream_table.assumptions).lower())
        self.assertTrue(any(section.section_id == "concentration" for section in stream_table.sections))
        self.assertTrue(any(section.section_id == "filtration" for section in stream_table.sections))
        self.assertTrue(any(section.section_id == "drying" for section in stream_table.sections))
        self.assertTrue(any(stream.destination_unit_id == "concentration" for stream in stream_table.streams))
        self.assertTrue(any(stream.source_unit_id == "drying" for stream in stream_table.streams))


if __name__ == "__main__":
    unittest.main()
