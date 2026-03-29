import shutil
import tempfile
import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.models import (
    AgentDecisionFabricArtifact,
    ChemistryFamilyAdapter,
    CostModel,
    CriticRegistryArtifact,
    DecisionRecord,
    DebtSchedule,
    EnergyBalance,
    HeatExchangerDesign,
    EquipmentListArtifact,
    FinancialSchedule,
    FlowsheetCase,
    MechanicalDesignArtifact,
    NarrativeArtifact,
    OperationsPlanningArtifact,
    PlantCostSummary,
    ReactorDesign,
    ColumnDesign,
    RouteSelectionArtifact,
    ProcessSynthesisArtifact,
    RouteFamilyArtifact,
    SolveResult,
    UtilityArchitectureDecision,
    UnitOperationFamilyArtifact,
    UtilitySummaryArtifact,
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

    def _config_from_example_file(self, filename: str):
        config = load_project_config(str(Path("examples", filename).resolve()))
        config.output_root = self.temp_dir
        return config

    def _config_from_example(self):
        return self._config_from_example_file("ethylene_glycol_india_mock.yaml")

    def _run_to_completion(self, runner: PipelineRunner):
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
        if state.awaiting_gate_id == "india_cost_basis":
            runner.approve_gate("india_cost_basis")
            state = runner.run()
        if state.awaiting_gate_id == "final_signoff":
            runner.approve_gate("final_signoff")
            state = runner.run()
        self.assertEqual(state.run_status.value, "completed")
        return state

    def test_pipeline_gate_flow_and_render(self):
        runner = PipelineRunner(self._config_from_example())
        state = self._run_to_completion(runner)
        process_description = runner.store.load_chapter(runner.config.project_id, "process_description")
        material_balance = runner.store.load_chapter(runner.config.project_id, "material_balance")
        process_selection = runner.store.load_chapter(runner.config.project_id, "process_selection")
        reactor_chapter = runner.store.load_chapter(runner.config.project_id, "reactor_design")
        process_unit_chapter = runner.store.load_chapter(runner.config.project_id, "distillation_design")
        thermo_chapter = runner.store.load_chapter(runner.config.project_id, "thermodynamic_feasibility")
        self.assertIn("### Unit Sequence", process_description.rendered_markdown)
        self.assertIn("### Section Topology", process_description.rendered_markdown)
        self.assertIn("Carbonate loop cleanup", process_description.rendered_markdown)
        self.assertIn("### Recycle Architecture", process_description.rendered_markdown)
        self.assertIn("Solver-derived process description", process_description.rendered_markdown)
        self.assertIn("### Unit Packet Balance Summary", material_balance.rendered_markdown)
        self.assertIn("### Reaction Extent Allocation", material_balance.rendered_markdown)
        self.assertIn("### Chemistry Family Adapter", process_selection.rendered_markdown)
        self.assertIn("### Route Family Profiles", process_selection.rendered_markdown)
        self.assertIn("### Unit-Operation Family Expansion", process_selection.rendered_markdown)
        self.assertIn("### Sparse-Data Policy", process_selection.rendered_markdown)
        self.assertIn("Preferred separation candidates", process_selection.rendered_markdown)
        self.assertIn("### Governing Equations", reactor_chapter.rendered_markdown)
        self.assertIn("### Solver Packet Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Kinetic Design Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Utility Coupling", reactor_chapter.rendered_markdown)
        self.assertIn("### Heat-Transfer Derivation Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Catalyst Service Basis", reactor_chapter.rendered_markdown)
        self.assertIn("Architecture family", reactor_chapter.rendered_markdown)
        self.assertIn("Allocated island target", reactor_chapter.rendered_markdown)
        self.assertIn("### Governing Equations", process_unit_chapter.rendered_markdown)
        self.assertIn("### Section and Feed Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Hydraulics Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Heat-Exchanger Thermal Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Process-Unit Calculation Traces", process_unit_chapter.rendered_markdown)
        self.assertIn("Minimum reflux ratio", process_unit_chapter.rendered_markdown)
        self.assertIn("Feed quality q-factor", process_unit_chapter.rendered_markdown)
        self.assertIn("Murphree efficiency", process_unit_chapter.rendered_markdown)
        self.assertIn("Rectifying theoretical stages", process_unit_chapter.rendered_markdown)
        self.assertIn("Reboiler package type", process_unit_chapter.rendered_markdown)
        self.assertIn("Allocated reboiler target", process_unit_chapter.rendered_markdown)
        self.assertIn("Condensing-side coefficient", process_unit_chapter.rendered_markdown)
        self.assertIn("### Separation Thermodynamics Basis", thermo_chapter.rendered_markdown)
        self.assertIn("Activity model", thermo_chapter.rendered_markdown)
        inspect_text = runner.inspect()
        self.assertIn("family_adapter:", inspect_text)
        self.assertIn("route_families:", inspect_text)
        self.assertIn("unit_operation_family:", inspect_text)
        self.assertIn("critic_registry:", inspect_text)
        self.assertIn("sparse_data_policy:", inspect_text)
        self.assertIn("continuous_liquid_organic_train", inspect_text)
        self.assertIn("route[eo_hydration]", inspect_text)
        self.assertIn("reaction_network:", inspect_text)
        self.assertIn("flowsheet_solver:", inspect_text)
        self.assertIn("composition_states:", inspect_text)
        self.assertIn("phase_split_specs:", inspect_text)
        self.assertIn("convergence_summaries:", inspect_text)
        self.assertIn("sections:", inspect_text)
        self.assertIn("section[", inspect_text)
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
        self.assertEqual(runner._load("chemistry_family_adapter", ChemistryFamilyAdapter).adapter_id, "continuous_liquid_organic_train")
        self.assertTrue(runner._load("route_family_profiles", RouteFamilyArtifact).profiles)
        self.assertTrue(runner._load("unit_operation_family", UnitOperationFamilyArtifact).reactor_candidates)
        self.assertGreaterEqual(len(runner._load("critic_registry", CriticRegistryArtifact).findings), 1)
        self.assertEqual(runner._load("process_synthesis", ProcessSynthesisArtifact).family_adapter.adapter_id, "continuous_liquid_organic_train")
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).units)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).unit_operation_packets)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).sections)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).separations)
        self.assertTrue(runner._load("flowsheet_case", FlowsheetCase).recycle_loops)
        self.assertIn(runner._load("solve_result", SolveResult).convergence_status, {"converged", "estimated"})
        self.assertTrue(runner._load("solve_result", SolveResult).unitwise_status)
        self.assertTrue(runner._load("solve_result", SolveResult).section_status)
        self.assertTrue(runner._load("utility_architecture", UtilityArchitectureDecision).architecture.selected_case_id)
        utility_architecture = runner._load("utility_architecture", UtilityArchitectureDecision)
        energy_balance = runner._load("energy_balance", EnergyBalance)
        cost_model = runner._load("cost_model", CostModel)
        operations_planning = runner._load("operations_planning", OperationsPlanningArtifact)
        reactor_design = runner._load("reactor_design", ReactorDesign)
        column_design = runner._load("column_design", ColumnDesign)
        exchanger_design = runner._load("heat_exchanger_design", HeatExchangerDesign)
        equipment_list = runner._load("equipment_list", EquipmentListArtifact)
        mechanical_design = runner._load("mechanical_design", MechanicalDesignArtifact)
        self.assertTrue(energy_balance.unit_thermal_packets)
        if "utility-only" not in utility_architecture.architecture.topology_summary.lower():
            self.assertGreaterEqual(len(utility_architecture.architecture.selected_train_steps), 1)
            self.assertGreaterEqual(len(utility_architecture.architecture.selected_package_items), len(utility_architecture.architecture.selected_train_steps) * 2)
            self.assertTrue(utility_architecture.architecture.selected_island_ids)
            self.assertTrue(
                next(
                    (
                        case.utility_islands
                        for case in utility_architecture.architecture.cases
                        if case.case_id == utility_architecture.architecture.selected_case_id
                    ),
                    [],
                )
            )
            self.assertGreater(cost_model.integration_capex_inr, 0.0)
            self.assertTrue(reactor_design.utility_topology)
            self.assertTrue(reactor_design.utility_architecture_family)
            self.assertGreaterEqual(reactor_design.allocated_recovered_duty_target_kw, 0.0)
            self.assertGreaterEqual(reactor_design.kinetic_rate_constant_1_hr, 0.0)
            self.assertGreater(reactor_design.kinetic_space_time_hr, 0.0)
            self.assertGreater(reactor_design.design_conversion_fraction, 0.0)
            self.assertGreater(reactor_design.heat_release_density_kw_m3, 0.0)
            self.assertGreater(reactor_design.adiabatic_temperature_rise_c, 0.0)
            self.assertGreater(reactor_design.heat_removal_capacity_kw, reactor_design.heat_duty_kw)
            self.assertIn(reactor_design.runaway_risk_label, {"low", "moderate", "high"})
            self.assertTrue(column_design.utility_topology)
            self.assertTrue(column_design.utility_architecture_family)
            self.assertGreaterEqual(reactor_design.integrated_exchange_area_m2, 0.0)
            self.assertGreaterEqual(column_design.integrated_reboiler_area_m2, 0.0)
            self.assertGreaterEqual(column_design.allocated_reboiler_recovery_target_kw, 0.0)
            self.assertGreaterEqual(column_design.allocated_condenser_recovery_target_kw, 0.0)
            self.assertGreater(column_design.theoretical_stages, 0.0)
            self.assertGreaterEqual(column_design.reflux_ratio, column_design.minimum_reflux_ratio)
            self.assertGreater(column_design.feed_quality_q_factor, 0.0)
            self.assertGreater(column_design.murphree_efficiency, 0.0)
            self.assertGreater(column_design.top_relative_volatility, 1.0)
            self.assertGreater(column_design.bottom_relative_volatility, 1.0)
            self.assertGreater(column_design.rectifying_theoretical_stages, 0.0)
            self.assertGreater(column_design.stripping_theoretical_stages, 0.0)
            self.assertGreater(column_design.allowable_vapor_velocity_m_s, 0.0)
            self.assertTrue(exchanger_design.selected_package_item_ids)
            self.assertTrue(exchanger_design.selected_package_roles)
            self.assertTrue(exchanger_design.utility_architecture_family)
            self.assertIn(exchanger_design.package_family, {"reboiler", "condenser", "reactor_coupling", "process_exchange", "generic"})
            if reactor_design.catalyst_name:
                self.assertGreater(reactor_design.catalyst_inventory_kg, 0.0)
                self.assertGreater(reactor_design.catalyst_cycle_days, 0.0)
                self.assertGreater(reactor_design.catalyst_weight_hourly_space_velocity_1_hr, 0.0)
            self.assertTrue(
                any(
                    item.package_role == "controls"
                    for item in utility_architecture.architecture.selected_package_items
                )
            )
            self.assertTrue(
                all(
                    step.island_id
                    for step in utility_architecture.architecture.selected_train_steps
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
                    item.package_family in {"reboiler", "condenser", "process_exchange"} and item.heat_transfer_area_m2 > 0.0 and item.lmtd_k > 0.0
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
        self.assertTrue(any(item.pressure_class for item in mechanical_design.items))
        self.assertTrue(any(item.support_load_case for item in mechanical_design.items))
        self.assertTrue(any(item.hydrotest_pressure_bar >= item.design_pressure_bar for item in mechanical_design.items))
        self.assertTrue(any(item.wind_load_kn > 0.0 for item in mechanical_design.items))
        self.assertTrue(any(item.seismic_load_kn > 0.0 for item in mechanical_design.items))
        self.assertTrue(any(item.support_variant for item in mechanical_design.items))
        self.assertTrue(any(item.anchor_group_count > 0 for item in mechanical_design.items))
        self.assertTrue(any(item.foundation_footprint_m2 > 0.0 for item in mechanical_design.items))
        self.assertTrue(any(item.nozzle_reinforcement_family for item in mechanical_design.items))
        self.assertTrue(any(item.local_shell_load_interaction_factor >= 1.0 for item in mechanical_design.items))
        self.assertTrue(
            any(
                "thermal_packet" in stream.stream_id
                for stream in utility_architecture.architecture.heat_stream_set.hot_streams + utility_architecture.architecture.heat_stream_set.cold_streams
            )
        )
        self.assertTrue(utility_architecture.architecture.heat_stream_set.composite_intervals)
        self.assertTrue(all(step.recovered_duty_kw > 0.0 for step in utility_architecture.architecture.selected_train_steps))
        if utility_architecture.architecture.selected_island_ids:
            self.assertTrue(cost_model.utility_island_costs)
            self.assertGreater(cost_model.annual_utility_island_service_cost, 0.0)
            self.assertEqual(
                {item.island_id for item in cost_model.utility_island_costs},
                set(utility_architecture.architecture.selected_island_ids),
            )
            self.assertTrue(any(item.utility_island_impacts for item in cost_model.scenario_results))
        else:
            self.assertFalse(cost_model.utility_island_costs)
            self.assertTrue(all(not item.utility_island_impacts for item in cost_model.scenario_results))
        self.assertGreater(runner._load("plant_cost_summary", PlantCostSummary).total_project_cost_inr, 0.0)
        self.assertTrue(runner._load("debt_schedule", DebtSchedule).entries)
        self.assertTrue(runner._load("financial_schedule", FinancialSchedule).lines)
        self.assertGreater(operations_planning.raw_material_buffer_days, 0.0)
        self.assertGreater(operations_planning.annual_restart_loss_kg, 0.0)
        self.assertIn("benchmark:", inspect_text)
        self.assertIn("source_resolution:", inspect_text)
        self.assertIn("archetype:", inspect_text)
        self.assertIn("operations_planning:", inspect_text)
        self.assertIn("- operating_mode: selected=", inspect_text)
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
        self.assertIn("utility_architecture:", inspect_text)
        self.assertIn("composite_intervals:", inspect_text)
        self.assertIn("utility_islands:", inspect_text)
        self.assertIn("mixture_packages:", inspect_text)
        self.assertIn("utility_architecture:", inspect_text)
        self.assertIn("train_steps:", inspect_text)
        self.assertIn("package_items:", inspect_text)
        self.assertIn("economics_v3:", inspect_text)
        self.assertIn("utility_island_costs:", inspect_text)
        self.assertIn("utility_island_service_cost_inr:", inspect_text)
        self.assertIn("utility_island_replacement_cost_inr:", inspect_text)
        self.assertIn("procurement_profile:", inspect_text)
        self.assertIn("construction_months:", inspect_text)
        self.assertIn("total_import_duty_inr:", inspect_text)
        self.assertIn("idc_inr:", inspect_text)
        self.assertIn("peak_working_capital_inr:", inspect_text)
        self.assertIn("minimum_dscr:", inspect_text)
        self.assertIn("llcr:", inspect_text)
        self.assertIn("plcr:", inspect_text)
        self.assertIn("selected_financing_candidate:", inspect_text)
        self.assertIn("downside_financing_candidate:", inspect_text)
        self.assertIn("downside_scenario_name:", inspect_text)
        self.assertIn("financing_scenario_reversal:", inspect_text)
        self.assertIn("covenant_breach_count:", inspect_text)
        equipment_chapter = runner.store.load_chapter(runner.config.project_id, "equipment_design_sizing")
        mechanical_chapter = runner.store.load_chapter(runner.config.project_id, "mechanical_design_moc")
        layout_chapter = runner.store.load_chapter(runner.config.project_id, "layout")
        working_capital_chapter = runner.store.load_chapter(runner.config.project_id, "working_capital")
        project_cost_chapter = runner.store.load_chapter(runner.config.project_id, "project_cost")
        financial_analysis_chapter = runner.store.load_chapter(runner.config.project_id, "financial_analysis")
        equipment_datasheets = runner.store.load_model(
            runner.config.project_id,
            "artifacts/equipment_datasheets.json",
            NarrativeArtifact,
        )
        self.assertIn("### Operations Planning Basis", equipment_chapter.rendered_markdown)
        self.assertIn("Dispatch buffer days", equipment_chapter.rendered_markdown)
        self.assertIn("### Mechanical Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("Foundation basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Foundation and Access Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Nozzle and Connection Schedule", mechanical_chapter.rendered_markdown)
        self.assertIn("Load Case", mechanical_chapter.rendered_markdown)
        self.assertIn("Hydrotest (bar)", mechanical_chapter.rendered_markdown)
        self.assertIn("Support Variant", mechanical_chapter.rendered_markdown)
        self.assertIn("Anchor Groups", mechanical_chapter.rendered_markdown)
        self.assertIn("Reinforcement Family", mechanical_chapter.rendered_markdown)
        self.assertIn("### Maintenance and Foundation Basis", layout_chapter.rendered_markdown)
        self.assertIn("### Operations Planning Basis", working_capital_chapter.rendered_markdown)
        self.assertIn("### Procurement-Linked Working-Capital Timing", working_capital_chapter.rendered_markdown)
        self.assertIn("Pre-commissioning inventory", working_capital_chapter.rendered_markdown)
        self.assertIn("Restart loss inventory", working_capital_chapter.rendered_markdown)
        self.assertIn("pressure_class", equipment_datasheets.markdown)
        self.assertIn("support_variant", equipment_datasheets.markdown)
        self.assertIn("foundation_footprint_m2", equipment_datasheets.markdown)
        self.assertIn("nozzle_connection_classes", equipment_datasheets.markdown)
        self.assertIn("### Procurement Timing Basis", project_cost_chapter.rendered_markdown)
        self.assertIn("### Procurement Package Timing", project_cost_chapter.rendered_markdown)
        self.assertIn("Construction months", project_cost_chapter.rendered_markdown)
        self.assertIn("Total import duty", project_cost_chapter.rendered_markdown)
        self.assertIn("Import Duty (INR)", project_cost_chapter.rendered_markdown)
        self.assertIn("### Debt Service Coverage Schedule", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Procurement-Linked Working-Capital Basis", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Lender Coverage Screening", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Financing Option Ranking", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Package Family", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Interest during construction", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Peak working capital", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Minimum DSCR", financial_analysis_chapter.rendered_markdown)
        self.assertIn("LLCR", financial_analysis_chapter.rendered_markdown)
        self.assertIn("PLCR", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Selected financing option", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Downside scenario", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Downside-preferred financing option", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Scenario reversal", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Covenant breaches", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Revenue Loss (INR)", financial_analysis_chapter.rendered_markdown)
        if cost_model.utility_island_costs:
            self.assertIn("### Utility Island Economics", project_cost_chapter.rendered_markdown)
            self.assertIn("Utility-island service", project_cost_chapter.rendered_markdown)
            self.assertIn("Utility-island replacement", project_cost_chapter.rendered_markdown)
            self.assertIn("### Scenario Utility Island Breakdown", financial_analysis_chapter.rendered_markdown)
            self.assertIn("Replacement (INR/y)", financial_analysis_chapter.rendered_markdown)
            self.assertIn("Utility-Island Burden (INR/y)", financial_analysis_chapter.rendered_markdown)
        pdf_path = runner.render()
        self.assertTrue(Path(pdf_path).exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "final_report.md").exists())

    def test_absorption_process_unit_chapter_surfaces_gle_basis(self):
        runner = PipelineRunner(self._config_from_example_file("sulfuric_acid_india_mock.yaml"))
        self._run_to_completion(runner)
        process_unit_chapter = runner.store.load_chapter(runner.config.project_id, "distillation_design")
        cost_of_production = runner.store.load_chapter(runner.config.project_id, "cost_of_production")
        project_cost = runner.store.load_chapter(runner.config.project_id, "project_cost")
        financial_analysis = runner.store.load_chapter(runner.config.project_id, "financial_analysis")
        column = runner._load("column_design", ColumnDesign)
        utilities = runner._load("utility_summary", UtilitySummaryArtifact)
        cost_model = runner._load("cost_model", CostModel)
        self.assertIn("### Gas-Liquid Equilibrium Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Absorber Capture Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Absorber Stage Screening", process_unit_chapter.rendered_markdown)
        self.assertIn("### Absorber Solvent Optimization", process_unit_chapter.rendered_markdown)
        self.assertIn("henry_law", process_unit_chapter.rendered_markdown)
        self.assertIn("Absorber Henry-law basis", process_unit_chapter.rendered_markdown)
        self.assertIn("Overall mass-transfer coefficient", process_unit_chapter.rendered_markdown)
        self.assertIn("Total pressure drop", process_unit_chapter.rendered_markdown)
        self.assertIn("Wetting ratio", process_unit_chapter.rendered_markdown)
        self.assertIn("Flooding margin fraction", process_unit_chapter.rendered_markdown)
        self.assertIn("Packing family", process_unit_chapter.rendered_markdown)
        self.assertIn("Gas-film transfer coefficient", process_unit_chapter.rendered_markdown)
        self.assertIn("Optimized solvent / gas ratio", process_unit_chapter.rendered_markdown)
        self.assertGreater(column.absorber_capture_fraction, 0.0)
        self.assertGreater(column.absorber_minimum_solvent_to_gas_ratio, 0.0)
        self.assertGreater(column.absorber_optimized_solvent_to_gas_ratio, 0.0)
        self.assertGreater(column.absorber_rich_loading_mol_mol, 0.0)
        self.assertGreaterEqual(column.absorber_lean_loading_mol_mol, 0.0)
        self.assertGreaterEqual(column.absorber_solvent_rate_case_count, 2)
        self.assertGreater(column.absorber_theoretical_stages, 0.0)
        self.assertGreater(column.absorber_packed_height_m, 0.0)
        self.assertGreater(column.absorber_gas_mass_velocity_kg_m2_s, 0.0)
        self.assertGreater(column.absorber_liquid_mass_velocity_kg_m2_s, 0.0)
        self.assertGreater(column.absorber_ntu, 0.0)
        self.assertGreater(column.absorber_htu_m, 0.0)
        self.assertTrue(column.absorber_packing_family)
        self.assertGreater(column.absorber_packing_specific_area_m2_m3, 0.0)
        self.assertGreater(column.absorber_effective_interfacial_area_m2_m3, 0.0)
        self.assertGreater(column.absorber_gas_phase_transfer_coeff_1_s, 0.0)
        self.assertGreater(column.absorber_liquid_phase_transfer_coeff_1_s, 0.0)
        self.assertGreater(column.absorber_overall_mass_transfer_coefficient_1_s, 0.0)
        self.assertGreater(column.absorber_min_wetting_rate_kg_m2_s, 0.0)
        self.assertGreater(column.absorber_wetting_ratio, 0.0)
        self.assertGreater(column.absorber_operating_velocity_m_s, 0.0)
        self.assertGreater(column.absorber_flooding_velocity_m_s, 0.0)
        self.assertGreater(column.absorber_flooding_margin_fraction, 0.0)
        self.assertGreater(column.absorber_pressure_drop_per_m_kpa_m, 0.0)
        self.assertGreater(column.absorber_total_pressure_drop_kpa, 0.0)
        self.assertTrue(any(item.utility_type == "Electricity - absorber hydraulics" for item in utilities.items))
        self.assertTrue(any(item.equipment_type == "Packing internals" for item in cost_model.equipment_cost_items))
        self.assertGreater(cost_model.annual_transport_service_cost, 0.0)
        self.assertGreater(cost_model.annual_packing_replacement_cost, 0.0)
        self.assertGreater(cost_model.packing_replacement_cycle_years, 0.0)
        self.assertGreater(cost_model.packing_replacement_event_cost, 0.0)
        self.assertGreater(cost_model.maintenance_turnaround_event_cost, 0.0)
        self.assertTrue(cost_model.availability_policy_label)
        self.assertTrue(cost_model.procurement_profile_label)
        self.assertTrue(cost_model.procurement_schedule)
        self.assertGreater(cost_model.planned_minor_outage_days_per_year, 0.0)
        self.assertGreater(cost_model.planned_major_turnaround_days, 0.0)
        self.assertGreater(cost_model.startup_loss_days_after_turnaround, 0.0)
        self.assertTrue(any(trace.trace_id == "absorber_packing_family_cost_basis" for trace in cost_model.calc_traces))
        if cost_model.utility_island_costs:
            self.assertTrue(any(trace.trace_id == "utility_island_economic_basis" for trace in cost_model.calc_traces))
        self.assertIn("Packing replacement", project_cost.rendered_markdown)
        if cost_model.utility_island_costs:
            self.assertIn("Utility Island Economics", project_cost.rendered_markdown)
        self.assertIn("Transport/service penalties", cost_of_production.rendered_markdown)
        self.assertIn("Transport/Service (INR/y)", financial_analysis.rendered_markdown)
        self.assertIn("Debt Service Coverage Schedule", financial_analysis.rendered_markdown)
        self.assertIn("Revenue Loss (INR)", financial_analysis.rendered_markdown)
        if cost_model.utility_island_costs:
            self.assertIn("Utility-Island Burden (INR/y)", financial_analysis.rendered_markdown)
        self.assertIn("Turnaround (INR)", financial_analysis.rendered_markdown)
        self.assertIn("Availability and Outage Calendar", financial_analysis.rendered_markdown)
        self.assertIn("Startup Loss (d)", financial_analysis.rendered_markdown)

    def test_solids_process_unit_chapter_surfaces_sle_basis(self):
        runner = PipelineRunner(self._config_from_example_file("sodium_bicarbonate_india_mock.yaml"))
        self._run_to_completion(runner)
        process_unit_chapter = runner.store.load_chapter(runner.config.project_id, "distillation_design")
        cost_of_production = runner.store.load_chapter(runner.config.project_id, "cost_of_production")
        project_cost = runner.store.load_chapter(runner.config.project_id, "project_cost")
        financial_analysis = runner.store.load_chapter(runner.config.project_id, "financial_analysis")
        column = runner._load("column_design", ColumnDesign)
        utilities = runner._load("utility_summary", UtilitySummaryArtifact)
        cost_model = runner._load("cost_model", CostModel)
        self.assertIn("### Solid-Liquid Equilibrium Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Crystallization Yield Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Crystallizer / Filter Design Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Filter Cycle and Dryer Endpoint Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("solubility_curve", process_unit_chapter.rendered_markdown)
        self.assertIn("Crystallizer solubility-limited basis", process_unit_chapter.rendered_markdown)
        self.assertIn("Crystal growth rate", process_unit_chapter.rendered_markdown)
        self.assertIn("Dryer product moisture fraction", process_unit_chapter.rendered_markdown)
        self.assertIn("Crystal size d50", process_unit_chapter.rendered_markdown)
        self.assertIn("Dryer heat-transfer coefficient", process_unit_chapter.rendered_markdown)
        self.assertIn("Classifier cut size", process_unit_chapter.rendered_markdown)
        self.assertIn("Dryer exhaust humidity ratio", process_unit_chapter.rendered_markdown)
        self.assertIn("Filter cycle time", process_unit_chapter.rendered_markdown)
        self.assertIn("Dryer exhaust dewpoint", process_unit_chapter.rendered_markdown)
        self.assertGreater(column.crystallizer_yield_fraction, 0.0)
        self.assertGreater(column.filter_area_m2, 0.0)
        self.assertGreater(column.filter_cycle_time_hr, 0.0)
        self.assertGreater(column.filter_cake_formation_time_hr, 0.0)
        self.assertGreater(column.filter_wash_time_hr, 0.0)
        self.assertGreater(column.filter_discharge_time_hr, 0.0)
        self.assertGreater(column.filter_cycles_per_hr, 0.0)
        self.assertGreaterEqual(column.dryer_evaporation_load_kg_hr, 0.0)
        self.assertGreater(column.crystallizer_residence_time_hr, 0.0)
        self.assertGreater(column.crystallizer_holdup_m3, 0.0)
        self.assertGreater(column.crystal_slurry_density_kg_m3, 0.0)
        self.assertGreater(column.crystal_growth_rate_mm_hr, 0.0)
        self.assertGreater(column.crystal_size_d10_mm, 0.0)
        self.assertGreater(column.crystal_size_d50_mm, 0.0)
        self.assertGreater(column.crystal_size_d90_mm, 0.0)
        self.assertGreater(column.crystal_classifier_cut_size_mm, 0.0)
        self.assertGreater(column.crystal_classified_product_fraction, 0.0)
        self.assertGreater(column.slurry_circulation_rate_m3_hr, 0.0)
        self.assertGreater(column.filter_cake_throughput_kg_m2_hr, 0.0)
        self.assertGreater(column.filter_specific_cake_resistance_m_kg, 0.0)
        self.assertGreater(column.filter_medium_resistance_1_m, 0.0)
        self.assertGreater(column.dryer_target_moisture_fraction, 0.0)
        self.assertGreater(column.dryer_product_moisture_fraction, 0.0)
        self.assertGreater(column.dryer_equilibrium_moisture_fraction, 0.0)
        self.assertGreaterEqual(column.dryer_endpoint_margin_fraction, 0.0)
        self.assertGreater(column.dryer_inlet_humidity_ratio_kg_kg, 0.0)
        self.assertGreater(column.dryer_exhaust_humidity_ratio_kg_kg, 0.0)
        self.assertGreater(column.dryer_humidity_lift_kg_kg, 0.0)
        self.assertGreater(column.dryer_exhaust_dewpoint_c, 0.0)
        self.assertGreater(column.dryer_dry_air_flow_kg_hr, 0.0)
        self.assertGreater(column.dryer_exhaust_saturation_fraction, 0.0)
        self.assertGreater(column.dryer_mass_transfer_coefficient_kg_m2_s, 0.0)
        self.assertGreater(column.dryer_heat_transfer_coefficient_w_m2_k, 0.0)
        self.assertGreater(column.dryer_heat_transfer_area_m2, 0.0)
        self.assertGreater(column.dryer_refined_duty_kw, 0.0)
        self.assertTrue(any(item.utility_type == "Electricity - solids auxiliaries" for item in utilities.items))
        self.assertTrue(any(item.utility_type == "Steam - dryer endpoint penalty" for item in utilities.items))
        self.assertTrue(any(item.equipment_type == "Crystal classifier" for item in cost_model.equipment_cost_items))
        self.assertTrue(any(item.equipment_type == "Pressure filter" for item in cost_model.equipment_cost_items))
        self.assertTrue(any(item.equipment_type == "Dryer gas handling skid" for item in cost_model.equipment_cost_items))
        self.assertGreater(cost_model.annual_transport_service_cost, 0.0)
        self.assertGreater(cost_model.annual_filter_media_replacement_cost, 0.0)
        self.assertGreater(cost_model.annual_dryer_exhaust_treatment_cost, 0.0)
        self.assertGreater(cost_model.maintenance_turnaround_event_cost, 0.0)
        self.assertTrue(cost_model.availability_policy_label)
        self.assertTrue(cost_model.procurement_profile_label)
        self.assertTrue(cost_model.procurement_schedule)
        self.assertGreater(cost_model.planned_minor_outage_days_per_year, 0.0)
        self.assertGreater(cost_model.planned_major_turnaround_days, 0.0)
        self.assertGreater(cost_model.startup_loss_days_after_turnaround, 0.0)
        self.assertTrue(any(trace.trace_id == "filter_media_replacement_basis" for trace in cost_model.calc_traces))
        self.assertTrue(any(trace.trace_id == "dryer_exhaust_treatment_basis" for trace in cost_model.calc_traces))
        if cost_model.utility_island_costs:
            self.assertTrue(any(trace.trace_id == "utility_island_economic_basis" for trace in cost_model.calc_traces))
        self.assertIn("Filter media replacement", project_cost.rendered_markdown)
        self.assertIn("Dryer exhaust treatment", project_cost.rendered_markdown)
        if cost_model.utility_island_costs:
            self.assertIn("Utility Island Economics", project_cost.rendered_markdown)
        self.assertIn("Transport/service penalties", cost_of_production.rendered_markdown)
        self.assertIn("Scenario Recurring Service Breakdown", financial_analysis.rendered_markdown)
        self.assertIn("Debt Service Coverage Schedule", financial_analysis.rendered_markdown)
        self.assertIn("Revenue Loss (INR)", financial_analysis.rendered_markdown)
        if cost_model.utility_island_costs:
            self.assertIn("Scenario Utility Island Breakdown", financial_analysis.rendered_markdown)
        self.assertIn("Turnaround (INR)", financial_analysis.rendered_markdown)
        self.assertIn("Availability and Outage Calendar", financial_analysis.rendered_markdown)
        self.assertIn("Startup Loss (d)", financial_analysis.rendered_markdown)

    def test_pipeline_blocks_on_missing_citations(self):
        runner = PipelineRunner(self._config_from_example())
        runner.reasoning = BrokenMockReasoningService()
        state = runner.run()
        self.assertEqual(state.run_status.value, "blocked")
        self.assertEqual(state.blocked_stage_id, "product_profile")
