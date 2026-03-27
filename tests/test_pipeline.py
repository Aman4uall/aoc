import shutil
import tempfile
import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.models import (
    AgentDecisionFabricArtifact,
    CostModel,
    DecisionRecord,
    DebtSchedule,
    EnergyBalance,
    HeatExchangerDesign,
    EquipmentListArtifact,
    FinancialSchedule,
    FlowsheetCase,
    MechanicalDesignArtifact,
    PlantCostSummary,
    ReactorDesign,
    ColumnDesign,
    RouteSelectionArtifact,
    SolveResult,
    UtilityArchitectureDecision,
)
from aoc.pipeline import PipelineRunner
from aoc.reasoning import MockReasoningService


class BrokenMockReasoningService(MockReasoningService):
    def build_product_profile(self, basis, sources, corpus):
        artifact = super().build_product_profile(basis, sources, corpus)
        artifact.citations = []
        for item in artifact.properties:
            item.citations = []
            item.supporting_sources = []
        return artifact


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aoc-tests-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _config_from_example(self):
        config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        config.output_root = self.temp_dir
        return config

    def test_pipeline_gate_flow_and_render(self):
        runner = PipelineRunner(self._config_from_example())
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "evidence_lock")
        runner.approve_gate("evidence_lock", notes="resolved basis approved for test")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "heat_integration")
        runner.approve_gate("heat_integration", notes="approved for test")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "process_architecture")
        runner.approve_gate("process_architecture")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "design_basis")
        runner.approve_gate("design_basis")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "equipment_basis")
        runner.approve_gate("equipment_basis")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "hazop")
        runner.approve_gate("hazop")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "india_cost_basis")
        runner.approve_gate("india_cost_basis")
        state = runner.run()
        self.assertEqual(state.awaiting_gate_id, "final_signoff")
        runner.approve_gate("final_signoff")
        state = runner.run()
        self.assertEqual(state.run_status.value, "completed")
        process_description = runner.store.load_chapter(runner.config.project_id, "process_description")
        material_balance = runner.store.load_chapter(runner.config.project_id, "material_balance")
        reactor_chapter = runner.store.load_chapter(runner.config.project_id, "reactor_design")
        process_unit_chapter = runner.store.load_chapter(runner.config.project_id, "distillation_design")
        thermo_chapter = runner.store.load_chapter(runner.config.project_id, "thermodynamic_feasibility")
        self.assertIn("### Unit Sequence", process_description.rendered_markdown)
        self.assertIn("### Recycle Architecture", process_description.rendered_markdown)
        self.assertIn("Solver-derived process description", process_description.rendered_markdown)
        self.assertIn("### Unit Packet Balance Summary", material_balance.rendered_markdown)
        self.assertIn("### Reaction Extent Allocation", material_balance.rendered_markdown)
        self.assertIn("### Governing Equations", reactor_chapter.rendered_markdown)
        self.assertIn("### Solver Packet Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Utility Coupling", reactor_chapter.rendered_markdown)
        self.assertIn("### Heat-Transfer Derivation Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Governing Equations", process_unit_chapter.rendered_markdown)
        self.assertIn("### Hydraulics Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Heat-Exchanger Thermal Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Process-Unit Calculation Traces", process_unit_chapter.rendered_markdown)
        self.assertIn("Minimum reflux ratio", process_unit_chapter.rendered_markdown)
        self.assertIn("Reboiler package type", process_unit_chapter.rendered_markdown)
        self.assertIn("Condensing-side coefficient", process_unit_chapter.rendered_markdown)
        self.assertIn("### Separation Thermodynamics Basis", thermo_chapter.rendered_markdown)
        self.assertIn("Activity model", thermo_chapter.rendered_markdown)
        inspect_text = runner.inspect()
        self.assertIn("reaction_network:", inspect_text)
        self.assertIn("flowsheet_solver:", inspect_text)
        self.assertIn("composition_states:", inspect_text)
        self.assertIn("phase_split_specs:", inspect_text)
        self.assertIn("convergence_summaries:", inspect_text)
        self.assertIn("recycle_summary[", inspect_text)
        self.assertTrue(
            any(token in inspect_text for token in ["estimated_units:", "partial_coverage_units:", "blocked_units:"])
        )
        self.assertEqual(
            runner._load("route_decision", DecisionRecord).selected_candidate_id,
            runner._load("route_selection", RouteSelectionArtifact).selected_route_id,
        )
        self.assertTrue(runner._load("site_selection_decision", DecisionRecord).selected_candidate_id)
        self.assertTrue(runner._load("utility_basis_decision", DecisionRecord).selected_candidate_id)
        self.assertTrue(runner._load("economic_basis_decision", DecisionRecord).selected_candidate_id)
        self.assertTrue(runner._load("agent_decision_fabric", AgentDecisionFabricArtifact).packets)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).units)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).unit_operation_packets)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).separations)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).recycle_loops)
        self.assertIn(runner._load("solve_result", SolveResult).convergence_status, {"converged", "estimated"})
        self.assertTrue(runner._load("solve_result", SolveResult).unitwise_status)
        self.assertTrue(runner._load("utility_architecture", UtilityArchitectureDecision).architecture.selected_case_id)
        utility_architecture = runner._load("utility_architecture", UtilityArchitectureDecision)
        energy_balance = runner._load("energy_balance", EnergyBalance)
        cost_model = runner._load("cost_model", CostModel)
        reactor_design = runner._load("reactor_design", ReactorDesign)
        column_design = runner._load("column_design", ColumnDesign)
        exchanger_design = runner._load("heat_exchanger_design", HeatExchangerDesign)
        equipment_list = runner._load("equipment_list", EquipmentListArtifact)
        mechanical_design = runner._load("mechanical_design", MechanicalDesignArtifact)
        self.assertTrue(energy_balance.unit_thermal_packets)
        if "utility-only" not in utility_architecture.architecture.topology_summary.lower():
            self.assertGreaterEqual(len(utility_architecture.architecture.selected_train_steps), 1)
            self.assertGreaterEqual(len(utility_architecture.architecture.selected_package_items), len(utility_architecture.architecture.selected_train_steps) * 2)
            self.assertGreater(cost_model.integration_capex_inr, 0.0)
            self.assertTrue(reactor_design.utility_topology)
            self.assertTrue(column_design.utility_topology)
            self.assertGreaterEqual(reactor_design.integrated_exchange_area_m2, 0.0)
            self.assertGreaterEqual(column_design.integrated_reboiler_area_m2, 0.0)
            self.assertGreater(column_design.theoretical_stages, 0.0)
            self.assertGreaterEqual(column_design.reflux_ratio, column_design.minimum_reflux_ratio)
            self.assertGreater(column_design.allowable_vapor_velocity_m_s, 0.0)
            self.assertTrue(exchanger_design.selected_package_item_ids)
            self.assertTrue(exchanger_design.selected_package_roles)
            self.assertIn(exchanger_design.package_family, {"reboiler", "condenser", "reactor_coupling", "process_exchange", "generic"})
            self.assertTrue(
                any(
                    item.package_role == "controls"
                    for item in utility_architecture.architecture.selected_package_items
                )
            )
            self.assertTrue(
                any(
                    item.equipment_id.startswith("HX-")
                    or item.equipment_type in {"HTM circulation skid", "HTM expansion tank", "HTM relief package", "Utility control package"}
                    for item in cost_model.equipment_cost_items
                )
            )
            package_ids = {item.equipment_id for item in utility_architecture.architecture.selected_package_items}
            self.assertTrue(package_ids.issubset({item.equipment_id for item in equipment_list.items}))
            self.assertTrue(package_ids & {item.equipment_id for item in mechanical_design.items})
            self.assertTrue(
                any(
                    item.package_family in {"reboiler", "condenser"} and item.heat_transfer_area_m2 > 0.0 and item.lmtd_k > 0.0
                    for item in utility_architecture.architecture.selected_package_items
                    if item.package_role == "exchanger"
                )
            )
            self.assertTrue(
                all(
                    item.operating_load_kn >= 0.0 and item.nozzle_reinforcement_area_mm2 >= 0.0
                    for item in mechanical_design.items
                    if item.equipment_id in package_ids
                )
            )
        self.assertTrue(
            any(
                "thermal_packet" in stream.stream_id
                for stream in utility_architecture.architecture.heat_stream_set.hot_streams + utility_architecture.architecture.heat_stream_set.cold_streams
            )
        )
        self.assertTrue(all(step.recovered_duty_kw > 0.0 for step in utility_architecture.architecture.selected_train_steps))
        self.assertGreater(runner._load("plant_cost_summary", PlantCostSummary).total_project_cost_inr, 0.0)
        self.assertTrue(runner._load("debt_schedule", DebtSchedule).entries)
        self.assertTrue(runner._load("financial_schedule", FinancialSchedule).lines)
        self.assertIn("benchmark:", inspect_text)
        self.assertIn("source_resolution:", inspect_text)
        self.assertIn("archetype:", inspect_text)
        self.assertIn("alternative_sets:", inspect_text)
        self.assertIn("resolved_components:", inspect_text)
        self.assertIn("resolved_bip_pairs:", inspect_text)
        self.assertIn("unresolved_bip_pairs:", inspect_text)
        self.assertIn("property_requirement_stage_failures:", inspect_text)
        self.assertIn("method_decisions:", inspect_text)
        self.assertIn("property_basis:", inspect_text)
        self.assertIn("separation_thermo:", inspect_text)
        self.assertIn("byproduct_closure:", inspect_text)
        self.assertIn("agent_fabric:", inspect_text)
        self.assertIn("flowsheet_solver:", inspect_text)
        self.assertIn("mixture_packages:", inspect_text)
        self.assertIn("utility_architecture:", inspect_text)
        self.assertIn("train_steps:", inspect_text)
        self.assertIn("package_items:", inspect_text)
        self.assertIn("economics_v3:", inspect_text)
        pdf_path = runner.render()
        self.assertTrue(Path(pdf_path).exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "final_report.md").exists())

    def test_pipeline_blocks_on_missing_citations(self):
        runner = PipelineRunner(self._config_from_example())
        runner.reasoning = BrokenMockReasoningService()
        state = runner.run()
        self.assertEqual(state.run_status.value, "blocked")
        self.assertEqual(state.blocked_stage_id, "product_profile")
