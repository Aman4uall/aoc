import unittest

from aoc.calculators import build_energy_balance, build_reaction_system, build_stream_table
from aoc.flowsheet import build_flowsheet_graph
from aoc.models import (
    KineticAssessmentArtifact,
    ProcessNarrativeArtifact,
    ProcessTemplate,
    ProjectBasis,
    ReactionParticipant,
    RouteOption,
    ThermoAssessmentArtifact,
)
from aoc.solver_architecture import build_flowsheet_case, build_solve_result
from aoc.validators import validate_flowsheet_case, validate_solve_result


class SolverArchitectureTests(unittest.TestCase):
    def _eg_basis(self) -> ProjectBasis:
        return ProjectBasis(
            target_product="Ethylene Glycol",
            capacity_tpa=200000,
            target_purity_wt_pct=99.9,
            process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
            india_only=True,
        )

    def _eg_route(self) -> RouteOption:
        return RouteOption(
            route_id="eo_hydration",
            name="Ethylene oxide hydration",
            reaction_equation="C2H4O + H2O -> C2H6O2",
            participants=[
                ReactionParticipant(name="Ethylene oxide", formula="C2H4O", coefficient=1, role="reactant", molecular_weight_g_mol=44.05, phase="liquid"),
                ReactionParticipant(name="Water", formula="H2O", coefficient=1, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="Ethylene glycol", formula="C2H6O2", coefficient=1, role="product", molecular_weight_g_mol=62.07, phase="liquid"),
            ],
            catalysts=["none"],
            operating_temperature_c=190,
            operating_pressure_bar=14,
            residence_time_hr=0.75,
            yield_fraction=0.92,
            selectivity_fraction=0.93,
            byproducts=[],
            separations=["EO flash", "Water removal", "Vacuum distillation", "Heavy glycol split"],
            scale_up_notes="",
            route_score=9.5,
            rationale="",
            citations=["s1"],
        )

    def test_flowsheet_case_uses_solver_packets(self):
        basis = self._eg_basis()
        route = self._eg_route()
        kinetics = KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=73.0,
            pre_exponential_factor=4.8e8,
            apparent_order=1.0,
            design_residence_time_hr=0.75,
            markdown="seed",
            citations=["s1"],
        )
        thermo = ThermoAssessmentArtifact(
            feasible=True,
            estimated_reaction_enthalpy_kj_per_mol=-90.4,
            estimated_gibbs_kj_per_mol=-31.5,
            equilibrium_comment="seed",
            markdown="seed",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, kinetics, ["s1"], [])
        stream_table = build_stream_table(basis, route, reaction_system, ["s1"], [])
        graph = build_flowsheet_graph(
            route,
            stream_table,
            reaction_system,
            ProcessNarrativeArtifact(bfd_mermaid="graph TD\nA-->B", markdown="seed", citations=["s1"]),
            basis.operating_mode,
        )
        flowsheet_case = build_flowsheet_case(route.route_id, basis.operating_mode, stream_table, graph)
        energy = build_energy_balance(route, stream_table, thermo)
        solve_result = build_solve_result(flowsheet_case, stream_table, energy)

        self.assertTrue(stream_table.unit_operation_packets)
        self.assertTrue(stream_table.separation_packets)
        self.assertTrue(stream_table.recycle_packets)
        self.assertTrue(flowsheet_case.unit_operation_packets)
        self.assertTrue(flowsheet_case.separations)
        self.assertTrue(flowsheet_case.recycle_loops)
        self.assertTrue(energy.unit_thermal_packets)
        self.assertTrue(energy.network_candidates)
        self.assertIn("reactor", solve_result.unitwise_status)
        self.assertIn(solve_result.unitwise_status["reactor"], {"converged", "estimated"})
        self.assertFalse(validate_flowsheet_case(flowsheet_case))
        self.assertFalse([issue for issue in validate_solve_result(solve_result) if issue.severity.value == "blocked"])

    def test_validate_flowsheet_case_blocks_invalid_recycle_destination(self):
        basis = self._eg_basis()
        route = self._eg_route()
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
        graph = build_flowsheet_graph(
            route,
            stream_table,
            reaction_system,
            ProcessNarrativeArtifact(bfd_mermaid="graph TD\nA-->B", markdown="seed", citations=["s1"]),
            basis.operating_mode,
        )
        flowsheet_case = build_flowsheet_case(route.route_id, basis.operating_mode, stream_table, graph)
        bad_stream_id = flowsheet_case.recycle_loops[0].recycle_stream_ids[0]
        for stream in flowsheet_case.streams:
            if stream.stream_id == bad_stream_id:
                stream.destination_unit_id = "purification"
        issues = validate_flowsheet_case(flowsheet_case)
        self.assertTrue(any(issue.code == "recycle_stream_destination_invalid" for issue in issues))


if __name__ == "__main__":
    unittest.main()
