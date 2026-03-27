import unittest

from aoc.calculators import build_reaction_system, build_stream_table
from aoc.models import KineticAssessmentArtifact, ProcessTemplate, ProjectBasis, ReactionParticipant, RouteOption
from aoc.properties.models import HenryLawConstant, PropertyPackageArtifact, SolubilityCurve


class SeparatorModelTests(unittest.TestCase):
    def test_absorption_family_emits_gas_liquid_separator_models(self):
        basis = ProjectBasis(
            target_product="Sulfuric Acid",
            capacity_tpa=200000,
            target_purity_wt_pct=98.0,
            process_template=ProcessTemplate.GENERIC_SMALL_MOLECULE,
            india_only=True,
        )
        route = RouteOption(
            route_id="contact_double_absorption",
            name="Contact double absorption",
            reaction_equation="SO2 + 0.5 O2 + H2O -> H2SO4",
            participants=[
                ReactionParticipant(name="Sulfur dioxide", formula="SO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=64.07, phase="gas"),
                ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Sulfuric acid", formula="H2SO4", coefficient=1.0, role="product", molecular_weight_g_mol=98.079, phase="liquid"),
            ],
            operating_temperature_c=430.0,
            operating_pressure_bar=2.0,
            residence_time_hr=0.4,
            yield_fraction=0.97,
            selectivity_fraction=0.99,
            catalysts=["V2O5"],
            separations=["drying tower", "absorption tower", "gas scrubbing"],
            scale_up_notes="",
            route_score=9.6,
            rationale="",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=52.0,
            pre_exponential_factor=8.8e6,
            apparent_order=1.0,
            design_residence_time_hr=0.4,
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        self.assertTrue(any(spec.mechanism == "gas_liquid_partition" for spec in stream_table.phase_split_specs))
        self.assertTrue(all(perf.performance_status in {"converged", "estimated"} for perf in stream_table.separator_performances))

    def test_absorption_family_uses_henry_basis_when_available(self):
        basis = ProjectBasis(
            target_product="Sulfuric Acid",
            capacity_tpa=200000,
            target_purity_wt_pct=98.0,
            process_template=ProcessTemplate.GENERIC_SMALL_MOLECULE,
            india_only=True,
        )
        route = RouteOption(
            route_id="contact_double_absorption",
            name="Contact double absorption",
            reaction_equation="SO2 + 0.5 O2 + H2O -> H2SO4",
            participants=[
                ReactionParticipant(name="Sulfur dioxide", formula="SO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=64.07, phase="gas"),
                ReactionParticipant(name="Oxygen", formula="O2", coefficient=0.5, role="reactant", molecular_weight_g_mol=32.0, phase="gas"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Sulfuric acid", formula="H2SO4", coefficient=1.0, role="product", molecular_weight_g_mol=98.079, phase="liquid"),
            ],
            operating_temperature_c=430.0,
            operating_pressure_bar=2.0,
            residence_time_hr=0.4,
            yield_fraction=0.97,
            selectivity_fraction=0.99,
            catalysts=["V2O5"],
            separations=["drying tower", "absorption tower", "gas scrubbing"],
            scale_up_notes="",
            route_score=9.6,
            rationale="",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=52.0,
            pre_exponential_factor=8.8e6,
            apparent_order=1.0,
            design_residence_time_hr=0.4,
            markdown="seed",
            citations=["s1"],
        )
        property_packages = PropertyPackageArtifact(
            henry_law_constants=[
                HenryLawConstant(
                    constant_id="sulfur_dioxide__sulfuric_acid",
                    gas_component_id="sulfur_dioxide",
                    solvent_component_id="sulfuric_acid",
                    gas_component_name="Sulfur dioxide",
                    solvent_component_name="Sulfuric acid",
                    value=0.9,
                    units="bar",
                    reference_temperature_c=25.0,
                    source_ids=["s1"],
                )
            ],
            markdown="henry",
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [], property_packages)
        self.assertTrue(any(spec.equilibrium_model == "henry_law" for spec in stream_table.phase_split_specs))
        self.assertTrue(any(packet.equilibrium_model == "henry_law" for packet in stream_table.separation_packets))

    def test_separator_packets_reference_phase_split_and_performance(self):
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
        spec_ids = {spec.spec_id for spec in stream_table.phase_split_specs}
        perf_ids = {perf.performance_id for perf in stream_table.separator_performances}
        self.assertTrue(stream_table.separation_packets)
        self.assertTrue(all(packet.phase_split_spec_id in spec_ids for packet in stream_table.separation_packets))
        self.assertTrue(all(packet.separator_performance_id in perf_ids for packet in stream_table.separation_packets))
        self.assertTrue(all(packet.split_basis for packet in stream_table.separation_packets))

    def test_solids_family_uses_solubility_curve_when_available(self):
        basis = ProjectBasis(
            target_product="Sodium Bicarbonate",
            capacity_tpa=150000,
            target_purity_wt_pct=99.0,
            process_template=ProcessTemplate.GENERIC_SMALL_MOLECULE,
            india_only=True,
        )
        route = RouteOption(
            route_id="solvay_bicarbonate",
            name="Bicarbonate crystallization",
            reaction_equation="Na2CO3 + CO2 + H2O -> 2 NaHCO3",
            participants=[
                ReactionParticipant(name="Soda ash", formula="Na2CO3", coefficient=1.0, role="reactant", molecular_weight_g_mol=105.99, phase="liquid"),
                ReactionParticipant(name="Carbon dioxide", formula="CO2", coefficient=1.0, role="reactant", molecular_weight_g_mol=44.01, phase="gas"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Sodium bicarbonate", formula="NaHCO3", coefficient=2.0, role="product", molecular_weight_g_mol=84.01, phase="solid"),
            ],
            operating_temperature_c=40.0,
            operating_pressure_bar=2.0,
            residence_time_hr=1.0,
            yield_fraction=0.95,
            selectivity_fraction=0.98,
            catalysts=["none"],
            separations=["crystallization", "filtration", "drying"],
            scale_up_notes="",
            route_score=9.1,
            rationale="",
            citations=["s1"],
        )
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=18.0,
            pre_exponential_factor=1.1e5,
            apparent_order=1.0,
            design_residence_time_hr=1.0,
            markdown="seed",
            citations=["s1"],
        )
        property_packages = PropertyPackageArtifact(
            solubility_curves=[
                SolubilityCurve(
                    curve_id="sodium_bicarbonate__water",
                    solute_component_id="sodium_bicarbonate",
                    solvent_component_id="water",
                    solute_component_name="Sodium bicarbonate",
                    solvent_component_name="Water",
                    equation_name="linear",
                    parameters={"a": 0.062, "b": 0.00110},
                    temperature_min_c=0.0,
                    temperature_max_c=80.0,
                    units="kg_solute_per_kg_solvent",
                    source_ids=["s1"],
                )
            ],
            markdown="solubility",
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [], property_packages)
        self.assertTrue(any(spec.equilibrium_model == "solubility_curve" for spec in stream_table.phase_split_specs))
        self.assertTrue(any(packet.equilibrium_model == "solubility_curve" for packet in stream_table.separation_packets))


if __name__ == "__main__":
    unittest.main()
