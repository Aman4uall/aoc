import unittest

from aoc.calculators import build_reaction_system, build_stream_table
from aoc.models import KineticAssessmentArtifact, ProcessTemplate, ProjectBasis, ReactionParticipant, RouteOption


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


if __name__ == "__main__":
    unittest.main()
