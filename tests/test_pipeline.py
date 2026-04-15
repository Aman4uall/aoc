import shutil
import tempfile
import unittest
from pathlib import Path

import fitz

from aoc.benchmarks import build_benchmark_manifest
from aoc.config import load_project_config
from aoc.models import (
    AgentDecisionFabricArtifact,
    BACDiagramBenchmarkArtifact,
    BACImpurityLedgerArtifact,
    BACImpurityModelArtifact,
    BACPurificationSectionArtifact,
    BACPseudoComponentBasisArtifact,
    BACDrawingPackageArtifact,
    BACRenderingAuditArtifact,
    BenchmarkVoiceProfile,
    BinaryPairCoverageArtifact,
    ChemistryFamilyAdapter,
    CommercialProductBasisArtifact,
    CostModel,
    CriticRegistryArtifact,
    DataGapRegistryArtifact,
    DataRealityAuditArtifact,
    DecisionRecord,
    DebtSchedule,
    DiagramDeliveryManifestArtifact,
    EnergyBalance,
    HeatExchangerDesign,
    EquipmentListArtifact,
    FinalReport,
    FormattedReportArtifact,
    FormatterAcceptanceArtifact,
    FormatterParityArtifact,
    FinancialSchedule,
    FlowsheetBlueprintArtifact,
    FlowsheetCase,
    MechanicalDesignArtifact,
    ModelSettings,
    NarrativeRewriteArtifact,
    NarrativeArtifact,
    OperationsPlanningArtifact,
    DocumentFactCollectionArtifact,
    DocumentProcessOptionsArtifact,
    GeographicScope,
    PlantCostSummary,
    ProcessSelectionComparisonArtifact,
    ProductProfileArtifact,
    ProjectBasis,
    ProjectConfig,
    ProjectRunState,
    RealDataMode,
    ReactorDesign,
    ResearchBundle,
    RunStatus,
    IndianLocationDatum,
    ColumnDesign,
    MissingDataAcceptanceArtifact,
    RecycleBasisArtifact,
    RouteChemistryArtifact,
    RouteEconomicBasisArtifact,
    RouteOption,
    RouteSelectionComparisonArtifact,
    RouteSelectionComparisonRow,
    RouteProcessClaimsArtifact,
    RouteSelectionArtifact,
    RouteSiteFitArtifact,
    RouteSurveyArtifact,
    SentencePatternLibrary,
    SiteSelectionArtifact,
    SiteOption,
    ToneStyleRules,
    SourceDomain,
    SourceKind,
    SourceRecord,
    ProcessSynthesisArtifact,
    ReportParityArtifact,
    ReportParityFrameworkArtifact,
    ReportAcceptanceArtifact,
    RouteFamilyArtifact,
    SolveResult,
    UnitTrainConsistencyArtifact,
    UnitTrainCandidateSet,
    UserDocument,
    UtilityArchitectureDecision,
    UnitOperationFamilyArtifact,
    UtilitySummaryArtifact,
)
from aoc.pipeline import PipelineRunner
from aoc.properties.sources import match_benchmark_entry
from aoc.reasoning import MockReasoningService
from aoc.validators import validate_site_selection_consistency


class BrokenMockReasoningService(MockReasoningService):
    def build_product_profile(self, basis, sources, corpus):
        artifact = super().build_product_profile(basis, sources, corpus)
        artifact.citations = []
        for item in artifact.properties:
            item.citations = []
            item.supporting_sources = []
        return artifact


class BrokenSiteCitationReasoningService(MockReasoningService):
    def select_site(self, basis, sources, corpus):
        artifact = super().select_site(basis, sources, corpus)
        artifact.citations = artifact.citations or [source.source_id for source in sources[:2]]
        for datum in artifact.india_location_data:
            datum.citations = []
        return artifact


class MissingPropertyRowCitationReasoningService(MockReasoningService):
    def build_product_profile(self, basis, sources, corpus):
        artifact = super().build_product_profile(basis, sources, corpus)
        artifact.citations = artifact.citations or [source.source_id for source in sources[:2]]
        for item in artifact.properties:
            item.citations = []
            item.supporting_sources = []
        return artifact


class MissingCriticalBACPropertyReasoningService(MockReasoningService):
    def build_product_profile(self, basis, sources, corpus):
        artifact = super().build_product_profile(basis, sources, corpus)
        artifact.citations = artifact.citations or [source.source_id for source in sources[:3]]
        artifact.properties = [item for item in artifact.properties if item.name.strip().lower() == "molecular weight"]
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

    def _bac_benchmark_config(self):
        return ProjectConfig(
            project_id="bac-benchmark-pipeline-test",
            benchmark_profile="benzalkonium_chloride",
            basis=ProjectBasis(
                target_product="Benzalkonium chloride",
                capacity_tpa=50000,
                target_purity_wt_pct=50.0,
                operating_mode="continuous",
                throughput_basis="finished_product",
                nominal_active_wt_pct=50.0,
                product_form="50_wt_pct_solution",
                carrier_components=["water", "ethanol"],
                homolog_distribution={"c12": 0.4, "c14": 0.5, "c16": 0.1},
                quality_targets=[
                    "50 wt% active",
                    "Residual free benzyl chloride below finished-goods limit",
                    "Residual free tertiary amine below finished-goods limit",
                ],
            ),
            model=ModelSettings(backend="mock", model_name="gemini-3.1-pro-preview", temperature=0.2),
            output_root=self.temp_dir,
        )

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

    def test_document_driven_route_extraction_replaces_generic_fallback_for_unseen_chemistry(self):
        document_path = Path(self.temp_dir, "ibuprofen_route.md")
        document_path.write_text(
            "\n".join(
                [
                    "Process 1",
                    "Isobutyl benzene and acetic anhydride are used.",
                    "",
                    "Process 4",
                    "Isobutyl benzene is raw material. Hydrogen peroxide oxidation gets Ibuprofen. Yield of the process is 88%.",
                    "",
                    "Process Selected",
                    "On the basis of the above comparison Process 4 is selected.",
                    "",
                    "Suggested Site",
                    "Ludhiana, Punjab",
                    "",
                    "Batch Scheduling",
                    "Reactor R003 is a batch stirred tank reactor.",
                    "Distillation Column-DC001",
                    "Plug Flow Reactor-PFR",
                ]
            ),
            encoding="utf-8",
        )
        config = self._config_from_example()
        config.project_id = "ibuprofen-doc-driven-test"
        config.require_india_only_data = False
        config.basis.india_only = False
        config.basis.target_product = "Ibuprofen"
        config.user_documents = [UserDocument(label="Ibuprofen benchmark", path=str(document_path))]
        runner = PipelineRunner(config)

        intake_result = runner._run_project_intake()
        literature_result = runner._run_literature_route_survey()

        self.assertEqual(intake_result.issues, [])
        self.assertEqual(literature_result.issues, [])

        document_facts = runner._load("user_document_facts", DocumentFactCollectionArtifact)
        document_process_options = runner._load("document_process_options", DocumentProcessOptionsArtifact)
        route_survey = runner._load("route_survey", RouteSurveyArtifact)
        route_chemistry = runner._load("route_chemistry", RouteChemistryArtifact)

        self.assertEqual(document_facts.process_option_count, 2)
        self.assertIn("Process 4", document_facts.selected_process_labels)
        self.assertIn("Ludhiana", document_facts.selected_site_names)
        self.assertEqual(len(document_process_options.options), 2)
        self.assertNotIn("generic_route_1", [route.route_id for route in route_survey.routes])
        self.assertIn("user_doc_1_process_4", [route.route_id for route in route_survey.routes])
        self.assertGreaterEqual(route_chemistry.resolved_species_count, 1)
        self.assertEqual(route_chemistry.blocking_route_ids, [])
        selected_route = next(route for route in route_survey.routes if route.route_id == "user_doc_1_process_4")
        reactants = [participant.name for participant in selected_route.participants if participant.role == "reactant"]
        self.assertIn("Isobutyl benzene", reactants)
        self.assertNotIn("88%", reactants)

    def test_pipeline_gate_flow_and_render(self):
        runner = PipelineRunner(self._config_from_example())
        state = self._run_to_completion(runner)
        process_description = runner.store.load_chapter(runner.config.project_id, "process_description")
        process_flow_diagram = runner.store.load_chapter(runner.config.project_id, "process_flow_diagram")
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
        self.assertIn("### Diagram Basis", process_flow_diagram.rendered_markdown)
        self.assertIn("### Diagram Acceptance", process_flow_diagram.rendered_markdown)
        self.assertIn("```diagram-svg", process_flow_diagram.rendered_markdown)
        self.assertIn("### Unit Packet Balance Summary", material_balance.rendered_markdown)
        self.assertIn("### Reaction Extent Allocation", material_balance.rendered_markdown)
        self.assertIn("### Overall Plant Balance Summary", material_balance.rendered_markdown)
        self.assertIn("### Section Balance Summary", material_balance.rendered_markdown)
        self.assertIn("### Recycle and Purge Summary", material_balance.rendered_markdown)
        self.assertIn("### Composition Closure Summary", material_balance.rendered_markdown)
        self.assertIn("### Long Stream Ledger", material_balance.rendered_markdown)
        self.assertIn("### Route-Family Stream Focus", material_balance.rendered_markdown)
        self.assertIn("### Overall Energy Summary", runner.store.load_chapter(runner.config.project_id, "energy_balance").rendered_markdown)
        self.assertIn("### Section Duty Summary", runner.store.load_chapter(runner.config.project_id, "energy_balance").rendered_markdown)
        self.assertIn("### Unit Thermal Packet Summary", runner.store.load_chapter(runner.config.project_id, "energy_balance").rendered_markdown)
        self.assertIn("### Recovery Candidate Summary", runner.store.load_chapter(runner.config.project_id, "energy_balance").rendered_markdown)
        self.assertIn("### Route-Family Duty Focus", runner.store.load_chapter(runner.config.project_id, "energy_balance").rendered_markdown)
        self.assertIn("### Energy-Balance Calculation Traces", runner.store.load_chapter(runner.config.project_id, "energy_balance").rendered_markdown)
        self.assertIn("### Chemistry Family Adapter", process_selection.rendered_markdown)
        self.assertIn("### Route Discovery", process_selection.rendered_markdown)
        self.assertIn("### Route Screening", process_selection.rendered_markdown)
        self.assertIn("### Route Selection Comparison", process_selection.rendered_markdown)
        self.assertIn("### Chemistry Decision", process_selection.rendered_markdown)
        self.assertIn("### Route-Derived Flowsheet Blueprint", process_selection.rendered_markdown)
        self.assertIn("### Route Family Profiles", process_selection.rendered_markdown)
        self.assertIn("### Unit-Operation Family Expansion", process_selection.rendered_markdown)
        self.assertIn("### Sparse-Data Policy", process_selection.rendered_markdown)
        self.assertIn("Preferred separation candidates", process_selection.rendered_markdown)
        self.assertIn("### Governing Equations", reactor_chapter.rendered_markdown)
        self.assertIn("### Route-Family Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Solver Packet Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Balance Reference Snapshot", reactor_chapter.rendered_markdown)
        self.assertIn("### Reactor Feed / Product / Recycle Summary", reactor_chapter.rendered_markdown)
        self.assertIn("### Reactor Local Stream Split Summary", reactor_chapter.rendered_markdown)
        self.assertIn("### Key Reactor Component Balance", reactor_chapter.rendered_markdown)
        self.assertIn("### Reactor Design Inputs", reactor_chapter.rendered_markdown)
        self.assertIn("### Reactor Operating Envelope", reactor_chapter.rendered_markdown)
        self.assertIn("### Reaction and Sizing Derivation Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Reactor Equation-Substitution Sheet", reactor_chapter.rendered_markdown)
        self.assertIn("### Kinetic Design Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Reactor Geometry and Internals", reactor_chapter.rendered_markdown)
        self.assertIn("### Utility Coupling", reactor_chapter.rendered_markdown)
        self.assertIn("### Heat-Transfer Derivation Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Thermal Stability and Hazard Envelope", reactor_chapter.rendered_markdown)
        self.assertIn("### Catalyst Service Basis", reactor_chapter.rendered_markdown)
        self.assertIn("### Integrated Utility Package Basis", reactor_chapter.rendered_markdown)
        self.assertIn("Architecture family", reactor_chapter.rendered_markdown)
        self.assertIn("Allocated island target", reactor_chapter.rendered_markdown)
        self.assertIn("### Governing Equations", process_unit_chapter.rendered_markdown)
        self.assertIn("### Route-Family Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Balance Reference Snapshot", process_unit_chapter.rendered_markdown)
        self.assertIn("### Unit-by-Unit Feed / Product / Recycle Summary", process_unit_chapter.rendered_markdown)
        self.assertIn("### Process-Unit Local Stream Split Summary", process_unit_chapter.rendered_markdown)
        self.assertIn("### Key Process-Unit Component Balance", process_unit_chapter.rendered_markdown)
        self.assertIn("### Separation Design Inputs", process_unit_chapter.rendered_markdown)
        self.assertIn("### Section and Feed Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Distillation Equation-Substitution Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Feed and Internal Flow Derivation", process_unit_chapter.rendered_markdown)
        self.assertIn("### Feed Condition and Internal Flow Substitution Sheet", process_unit_chapter.rendered_markdown)
        self.assertIn("### Column Operating Envelope", process_unit_chapter.rendered_markdown)
        self.assertIn("### Hydraulics Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Reboiler and Condenser Package Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Reboiler and Condenser Thermal Substitution Sheet", process_unit_chapter.rendered_markdown)
        self.assertIn("### Heat-Transfer Package Inputs", process_unit_chapter.rendered_markdown)
        self.assertIn("### Exchanger Package Selection Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Heat-Exchanger Thermal Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("### Process-Unit Calculation Traces", process_unit_chapter.rendered_markdown)
        self.assertIn("Nmin = Fenske(alpha, LK/HK split)", process_unit_chapter.rendered_markdown)
        self.assertIn("Rmin = Underwood(alpha, q, keys)", process_unit_chapter.rendered_markdown)
        self.assertIn("N = Gilliland(Nmin, R/Rmin)", process_unit_chapter.rendered_markdown)
        self.assertIn("R/Rmin = R / Rmin", process_unit_chapter.rendered_markdown)
        self.assertIn("A = Q / (U * LMTD)", process_unit_chapter.rendered_markdown)
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
        report_parity_framework = runner._load("report_parity_framework", ReportParityFrameworkArtifact)
        report_parity = runner._load("report_parity", ReportParityArtifact)
        report_acceptance = runner._load("report_acceptance", ReportAcceptanceArtifact)
        self.assertIn("family_adapter:", inspect_text)
        self.assertIn("report_parity:", inspect_text)
        self.assertIn("report_acceptance:", inspect_text)
        self.assertIn("diagram_acceptance:", inspect_text)
        self.assertIn("pfd_cleanliness_score:", inspect_text)
        self.assertIn("pfd_node_overlaps:", inspect_text)
        self.assertIn("pfd_node_label_overlaps:", inspect_text)
        self.assertIn("pfd_crowded_sheets:", inspect_text)
        self.assertIn("pfd_max_sheet_utilization:", inspect_text)
        self.assertIn("pfd_blocking_issues:", inspect_text)
        self.assertIn("diagram_exports:", inspect_text)
        self.assertIn("bfd_svg_sheets:", inspect_text)
        self.assertIn("pfd_svg_sheets:", inspect_text)
        self.assertIn("pid_lite_svg_sheets:", inspect_text)
        self.assertIn("drawio_files:", inspect_text)
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "process_flow_diagram_routing.json").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "diagram_domain_packs.json").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "pid_lite_routing.json").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "control_system_routing.json").exists())
        self.assertIn("diagram_architecture:", inspect_text)
        self.assertIn("status: modular_default", inspect_text)
        self.assertIn("svg_source_of_truth: yes", inspect_text)
        self.assertIn("drawio_export_enabled: yes", inspect_text)
        self.assertIn("control_review:", inspect_text)
        self.assertIn("cause_effect_rows:", inspect_text)
        self.assertIn("scientific_basis:", inspect_text)
        self.assertIn("scientific_inference:", inspect_text)
        self.assertIn("overall_status: partial", inspect_text)
        self.assertIn("pipeline_status: awaiting_approval", inspect_text)
        self.assertIn("route_families:", inspect_text)
        self.assertIn("route_selection_comparison:", inspect_text)
        self.assertIn("unit_operation_family:", inspect_text)
        self.assertIn("critic_registry:", inspect_text)
        self.assertIn("sparse_data_policy:", inspect_text)
        self.assertIn("flowsheet_blueprint:", inspect_text)
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
        self.assertTrue(runner._load("route_selection_comparison", RouteSelectionComparisonArtifact).rows)
        self.assertTrue(runner._load("unit_train_candidates", UnitTrainCandidateSet).blueprints)
        self.assertTrue(runner._load("route_process_claims", RouteProcessClaimsArtifact).claims)
        self.assertTrue(runner._load("flowsheet_blueprint", FlowsheetBlueprintArtifact).steps)
        self.assertTrue(runner._load("unit_operation_family", UnitOperationFamilyArtifact).reactor_candidates)
        self.assertGreaterEqual(len(runner._load("critic_registry", CriticRegistryArtifact).findings), 1)
        self.assertEqual(runner._load("process_synthesis", ProcessSynthesisArtifact).family_adapter.adapter_id, "continuous_liquid_organic_train")
        self.assertTrue(report_parity_framework.chapter_contracts)
        self.assertTrue(report_parity_framework.support_contracts)
        self.assertGreaterEqual(report_parity.complete_chapter_count, 1)
        self.assertIn(report_acceptance.overall_status.value, {"conditional", "complete"})
        self.assertEqual(report_acceptance.pipeline_status.value, "awaiting_approval")
        self.assertNotIn("appendix_msds", report_parity.missing_support_ids)
        self.assertNotIn("appendix_code_backup", report_parity.missing_support_ids)
        self.assertNotIn("appendix_process_design_datasheets", report_parity.missing_support_ids)
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
        route_site_fit = runner._load("route_site_fit", RouteSiteFitArtifact)
        route_economic_basis = runner._load("route_economic_basis", RouteEconomicBasisArtifact)
        operations_planning = runner._load("operations_planning", OperationsPlanningArtifact)
        reactor_design = runner._load("reactor_design", ReactorDesign)
        column_design = runner._load("column_design", ColumnDesign)
        exchanger_design = runner._load("heat_exchanger_design", HeatExchangerDesign)
        equipment_list = runner._load("equipment_list", EquipmentListArtifact)
        mechanical_design = runner._load("mechanical_design", MechanicalDesignArtifact)
        self.assertTrue(energy_balance.unit_thermal_packets)
        self.assertEqual(route_site_fit.route_id, runner._load("route_selection", RouteSelectionArtifact).selected_route_id)
        self.assertEqual(route_economic_basis.route_id, route_site_fit.route_id)
        self.assertEqual(route_economic_basis.selected_site, route_site_fit.selected_site)
        self.assertGreater(route_site_fit.overall_fit_score, 0.0)
        self.assertGreaterEqual(route_economic_basis.raw_material_complexity_factor, 1.0)
        self.assertGreaterEqual(route_economic_basis.site_input_cost_factor, 1.0)
        self.assertGreaterEqual(route_economic_basis.logistics_intensity_factor, 1.0)
        self.assertEqual(runner._load("economic_basis_decision", DecisionRecord).selected_candidate_id, "selected_integrated_base")
        self.assertGreaterEqual(cost_model.route_site_fit_score, route_site_fit.overall_fit_score - 0.01)
        self.assertGreaterEqual(cost_model.route_feedstock_cluster_factor, 1.0)
        self.assertGreaterEqual(cost_model.route_logistics_penalty_factor, 1.0)
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
        self.assertIn("route_site_fit_score:", inspect_text)
        self.assertIn("route_economic_coverage:", inspect_text)
        self.assertIn("route_solvent_recovery_service_inr:", inspect_text)
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
        storage_utilities_chapter = runner.store.load_chapter(runner.config.project_id, "storage_utilities")
        instrumentation_chapter = runner.store.load_chapter(runner.config.project_id, "instrumentation_control")
        hazop_chapter = runner.store.load_chapter(runner.config.project_id, "hazop")
        she_chapter = runner.store.load_chapter(runner.config.project_id, "safety_health_environment_waste")
        cost_of_production_chapter = runner.store.load_chapter(runner.config.project_id, "cost_of_production")
        working_capital_chapter = runner.store.load_chapter(runner.config.project_id, "working_capital")
        project_cost_chapter = runner.store.load_chapter(runner.config.project_id, "project_cost")
        financial_analysis_chapter = runner.store.load_chapter(runner.config.project_id, "financial_analysis")
        equipment_datasheets = runner.store.load_model(
            runner.config.project_id,
            "artifacts/equipment_datasheets.json",
            NarrativeArtifact,
        )
        self.assertIn("### Operations Planning Basis", equipment_chapter.rendered_markdown)
        self.assertIn("### Storage Transfer Pump Basis", equipment_chapter.rendered_markdown)
        self.assertIn("### Storage and Inventory Vessel Basis", equipment_chapter.rendered_markdown)
        self.assertIn("### Major Process Equipment Basis", equipment_chapter.rendered_markdown)
        self.assertIn("### Heat Exchanger and Thermal-Service Basis", equipment_chapter.rendered_markdown)
        self.assertIn("### Rotating and Auxiliary Package Basis", equipment_chapter.rendered_markdown)
        self.assertIn("### Utility-Coupled Package Inventory", equipment_chapter.rendered_markdown)
        self.assertIn("### Datasheet Coverage Matrix", equipment_chapter.rendered_markdown)
        self.assertIn("### Equipment-by-Equipment Sizing Summary", equipment_chapter.rendered_markdown)
        self.assertIn("Dispatch buffer days", equipment_chapter.rendered_markdown)
        self.assertIn("### Mechanical Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Mechanical Design Input Matrix", mechanical_chapter.rendered_markdown)
        self.assertIn("Allowable Stress (MPa)", mechanical_chapter.rendered_markdown)
        self.assertIn("Joint Efficiency", mechanical_chapter.rendered_markdown)
        self.assertIn("### Shell and Head Thickness Derivation", mechanical_chapter.rendered_markdown)
        self.assertIn("t = P*D / (2*S*J - 1.2*P) + CA", mechanical_chapter.rendered_markdown)
        self.assertIn("### Support and Overturning Derivation", mechanical_chapter.rendered_markdown)
        self.assertIn("Wsupport = Wvertical + Wpiping + Wwind + Wseismic", mechanical_chapter.rendered_markdown)
        self.assertIn("### Nozzle Reinforcement and Connection Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("Areinf = f(dnozzle, Pdesign, equipment family)", mechanical_chapter.rendered_markdown)
        self.assertIn("### Connection and Piping Class Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("Piping Class Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Material of Construction Matrix", mechanical_chapter.rendered_markdown)
        self.assertIn("### MoC Option Screening", mechanical_chapter.rendered_markdown)
        self.assertIn("### Equipment-Wise MoC Justification Matrix", mechanical_chapter.rendered_markdown)
        self.assertIn("### Inspection and Maintainability Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Corrosion and Service Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Utility and Storage MoC Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("Foundation basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Foundation and Access Basis", mechanical_chapter.rendered_markdown)
        self.assertIn("### Nozzle and Connection Schedule", mechanical_chapter.rendered_markdown)
        self.assertIn("Load Case", mechanical_chapter.rendered_markdown)
        self.assertIn("Hydrotest (bar)", mechanical_chapter.rendered_markdown)
        self.assertIn("Support Variant", mechanical_chapter.rendered_markdown)
        self.assertIn("Anchor Groups", mechanical_chapter.rendered_markdown)
        self.assertIn("Reinforcement Family", mechanical_chapter.rendered_markdown)
        self.assertIn("### Storage Service Matrix", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Storage Inventory and Buffer Basis", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Utility Consumption Summary", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Utility Service System Matrix", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Utility Peak and Annualized Demand", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Utility Demand by Major Unit", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Utility Island Service Basis", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Header and Thermal-Loop Basis", storage_utilities_chapter.rendered_markdown)
        self.assertIn("Recommended operating mode", storage_utilities_chapter.rendered_markdown)
        self.assertIn("Cost Proxy", storage_utilities_chapter.rendered_markdown)
        self.assertIn("### Control Philosophy", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Control System Diagram", instrumentation_chapter.rendered_markdown)
        self.assertIn("### P&ID-lite Clusters", instrumentation_chapter.rendered_markdown)
        self.assertIn("```diagram-svg", instrumentation_chapter.rendered_markdown)
        self.assertIn("Instrumented Process Flow Overlay", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Loop Objective Matrix", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Cause And Effect Review", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Controlled and Manipulated Variable Register", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Startup, Shutdown, and Override Basis", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Alarm and Interlock Basis", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Utility-Integrated Control Basis", instrumentation_chapter.rendered_markdown)
        self.assertIn("### Control Loop Sheets", instrumentation_chapter.rendered_markdown)
        self.assertIn("Disturbance Basis", instrumentation_chapter.rendered_markdown)
        self.assertIn("Override / Permissive Basis", instrumentation_chapter.rendered_markdown)
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "diagrams" / "control_system_sheet_1.svg").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "diagrams" / "control_system_sheet_2.svg").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "diagrams" / "control_system.drawio").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "control_cause_effect.json").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "diagrams" / "pid_lite_sheet_1.svg").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "diagrams" / "pid_lite.drawio").exists())
        self.assertIn("### HAZOP Coverage Summary", hazop_chapter.rendered_markdown)
        self.assertIn("### HAZOP Node Basis", hazop_chapter.rendered_markdown)
        self.assertIn("### Critical Node Summary", hazop_chapter.rendered_markdown)
        self.assertIn("### Deviation Cause-Consequence Matrix", hazop_chapter.rendered_markdown)
        self.assertIn("### Recommendation Register", hazop_chapter.rendered_markdown)
        self.assertIn("Design Intent", hazop_chapter.rendered_markdown)
        self.assertIn("Priority", hazop_chapter.rendered_markdown)
        self.assertIn("Status", hazop_chapter.rendered_markdown)
        self.assertIn("### Safety Basis", she_chapter.rendered_markdown)
        self.assertIn("### Hazard and Emergency Response Basis", she_chapter.rendered_markdown)
        self.assertIn("### Health and Exposure Basis", she_chapter.rendered_markdown)
        self.assertIn("### Environmental and Waste Basis", she_chapter.rendered_markdown)
        self.assertIn("### Environmental Control and Monitoring Basis", she_chapter.rendered_markdown)
        self.assertIn("### Waste Handling and Disposal Basis", she_chapter.rendered_markdown)
        self.assertIn("### Safeguard Linkage", she_chapter.rendered_markdown)
        self.assertIn("Emergency Trigger", she_chapter.rendered_markdown)
        self.assertIn("PPE / Controls", she_chapter.rendered_markdown)
        self.assertIn("Waste Class", she_chapter.rendered_markdown)
        self.assertIn("### Plot Plan Basis", layout_chapter.rendered_markdown)
        self.assertIn("### Plot Layout Schematic", layout_chapter.rendered_markdown)
        self.assertIn("```mermaid", layout_chapter.rendered_markdown)
        self.assertIn("### Area Zoning and Separation Basis", layout_chapter.rendered_markdown)
        self.assertIn("### Equipment Placement Matrix", layout_chapter.rendered_markdown)
        self.assertIn("### Utility Corridor Matrix", layout_chapter.rendered_markdown)
        self.assertIn("### Utility Routing and Access Basis", layout_chapter.rendered_markdown)
        self.assertIn("### Dispatch and Emergency Access Basis", layout_chapter.rendered_markdown)
        self.assertIn("### Maintenance and Foundation Basis", layout_chapter.rendered_markdown)
        self.assertIn("Operating mode", layout_chapter.rendered_markdown)
        self.assertIn("### Operations Planning Basis", working_capital_chapter.rendered_markdown)
        self.assertIn("### Working-Capital Parameter Basis", working_capital_chapter.rendered_markdown)
        self.assertIn("### Inventory, Receivable, and Payable Basis", working_capital_chapter.rendered_markdown)
        self.assertIn("### Procurement-Linked Working-Capital Timing", working_capital_chapter.rendered_markdown)
        self.assertIn("Pre-commissioning inventory", working_capital_chapter.rendered_markdown)
        self.assertIn("Restart loss inventory", working_capital_chapter.rendered_markdown)
        self.assertIn("Cash-cycle component", working_capital_chapter.rendered_markdown)
        self.assertIn("Operating stock", working_capital_chapter.rendered_markdown)
        self.assertIn("### Cost of Production Summary", cost_of_production_chapter.rendered_markdown)
        self.assertIn("### Manufacturing Cost Build-Up", cost_of_production_chapter.rendered_markdown)
        self.assertIn("### Utility and Raw-Material Cost Basis", cost_of_production_chapter.rendered_markdown)
        self.assertIn("### Unit Cost and Selling Basis", cost_of_production_chapter.rendered_markdown)
        self.assertIn("Gross margin basis", cost_of_production_chapter.rendered_markdown)
        self.assertIn("pressure_class", equipment_datasheets.markdown)
        self.assertIn("support_variant", equipment_datasheets.markdown)
        self.assertIn("foundation_footprint_m2", equipment_datasheets.markdown)
        self.assertIn("nozzle_connection_classes", equipment_datasheets.markdown)
        self.assertIn("### Package Derivation Basis", equipment_datasheets.markdown)
        self.assertIn("### Mechanical Basis", equipment_datasheets.markdown)
        self.assertIn("allowable_stress_mpa", equipment_datasheets.markdown)
        self.assertIn("joint_efficiency", equipment_datasheets.markdown)
        self.assertIn("corrosion_allowance_mm", equipment_datasheets.markdown)
        self.assertIn("shell_thickness_mm", equipment_datasheets.markdown)
        self.assertIn("pipe_rack_tie_in_required", equipment_datasheets.markdown)
        self.assertIn("anchor_group_count", equipment_datasheets.markdown)
        self.assertIn("Pump datasheet emitted separately", equipment_datasheets.markdown)
        self.assertIn("dispatch_turnover_basis", equipment_datasheets.markdown)
        self.assertIn("working_to_total_volume_ratio", equipment_datasheets.markdown)
        self.assertIn("### Procurement Timing Basis", project_cost_chapter.rendered_markdown)
        self.assertIn("### Route Site Fit", project_cost_chapter.rendered_markdown)
        self.assertIn("### Route-Derived Economic Basis", project_cost_chapter.rendered_markdown)
        self.assertIn("### Route-Derived Recurring Burden Register", project_cost_chapter.rendered_markdown)
        self.assertIn("### Procurement Package Timing", project_cost_chapter.rendered_markdown)
        self.assertIn("### Project Cost Build-Up Summary", project_cost_chapter.rendered_markdown)
        self.assertIn("### Direct Plant Cost Head Allocation", project_cost_chapter.rendered_markdown)
        self.assertIn("### Indirect and Contingency Basis", project_cost_chapter.rendered_markdown)
        self.assertIn("### Equipment Family Cost Allocation", project_cost_chapter.rendered_markdown)
        self.assertIn("### Installed Equipment Cost Matrix", project_cost_chapter.rendered_markdown)
        self.assertIn("Construction months", project_cost_chapter.rendered_markdown)
        self.assertIn("Overall site-fit score", project_cost_chapter.rendered_markdown)
        self.assertIn("Raw-material complexity factor", project_cost_chapter.rendered_markdown)
        self.assertIn("Solvent recovery service", project_cost_chapter.rendered_markdown)
        self.assertIn("Total import duty", project_cost_chapter.rendered_markdown)
        self.assertIn("Import Duty (INR)", project_cost_chapter.rendered_markdown)
        self.assertIn("Instrumentation and control", project_cost_chapter.rendered_markdown)
        self.assertIn("Civil and structural", project_cost_chapter.rendered_markdown)
        self.assertIn("Direct-cost uplift above installed basis", project_cost_chapter.rendered_markdown)
        self.assertIn("Purchased equipment", project_cost_chapter.rendered_markdown)
        self.assertIn("### Debt Service Coverage Schedule", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Financial Performance Summary", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Profitability and Return Summary", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Funding and Capital Structure Basis", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Procurement-Linked Working-Capital Basis", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Lender Coverage Screening", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Financing Option Ranking", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Profit and Loss Schedule", financial_analysis_chapter.rendered_markdown)
        self.assertIn("### Cash Accrual and Funding Schedule", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Package Family", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Interest during construction", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Peak working capital", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Minimum DSCR", financial_analysis_chapter.rendered_markdown)
        self.assertIn("LLCR", financial_analysis_chapter.rendered_markdown)
        self.assertIn("PLCR", financial_analysis_chapter.rendered_markdown)
        self.assertIn("Cash Accrual (INR)", financial_analysis_chapter.rendered_markdown)
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
        final_report = runner._load("final_report", FinalReport)
        final_report_path = Path(self.temp_dir) / runner.config.project_id / "final_report.md"
        final_report_raw_path = Path(self.temp_dir) / runner.config.project_id / "final_report_raw.md"
        final_report_formatted_path = Path(self.temp_dir) / runner.config.project_id / "final_report_formatted.md"
        final_report_formatted_html_path = Path(self.temp_dir) / runner.config.project_id / "final_report_formatted.html"
        self.assertTrue(final_report_path.exists())
        self.assertTrue(final_report_raw_path.exists())
        self.assertTrue(final_report_formatted_path.exists())
        self.assertTrue(final_report_formatted_html_path.exists())
        self.assertEqual(Path(final_report.raw_markdown_path).resolve(), final_report_raw_path.resolve())
        self.assertEqual(Path(final_report.formatted_markdown_path).resolve(), final_report_formatted_path.resolve())
        self.assertTrue(any(path.endswith("bfd_sheet_1.svg") for path in final_report.diagram_svg_paths))
        self.assertTrue(any(path.endswith("pfd_sheet_1.svg") for path in final_report.diagram_svg_paths))
        self.assertTrue(any(path.endswith("bfd.drawio") for path in final_report.diagram_drawio_paths))
        self.assertTrue(any(path.endswith("pfd.drawio") for path in final_report.diagram_drawio_paths))
        self.assertTrue(any(path.endswith("pid_lite_sheet_1.svg") for path in final_report.diagram_svg_paths))
        self.assertTrue(any(path.endswith("pid_lite.drawio") for path in final_report.diagram_drawio_paths))
        delivery_manifest = runner._load("diagram_delivery_manifest", DiagramDeliveryManifestArtifact)
        self.assertEqual(delivery_manifest.architecture_status, "modular_default")
        self.assertTrue(delivery_manifest.svg_source_of_truth)
        self.assertTrue(delivery_manifest.drawio_export_enabled)
        self.assertTrue(any(path.endswith("pfd.drawio") for path in delivery_manifest.drawio_paths))
        self.assertTrue(any(path.endswith("pid_lite_sheet_1.svg") for path in delivery_manifest.pid_lite_svg_paths))
        self.assertEqual(runner._load("benchmark_voice_profile", BenchmarkVoiceProfile).voice_id, "ict_home_paper_voice_v1")
        self.assertEqual(runner._load("sentence_pattern_library", SentencePatternLibrary).voice_id, "ict_home_paper_voice_v1")
        self.assertEqual(runner._load("tone_style_rules", ToneStyleRules).voice_id, "ict_home_paper_voice_v1")
        rewrite_plan = runner._load("narrative_rewrite_plan", NarrativeRewriteArtifact)
        self.assertGreater(rewrite_plan.aggressive_block_count, 0)
        self.assertGreater(rewrite_plan.protected_block_count, 0)
        final_report_markdown = final_report_path.read_text()
        formatted_report_markdown = final_report_formatted_path.read_text()
        self.assertIn("## Report Basis", final_report_markdown)
        self.assertIn("## Document Control", final_report_markdown)
        self.assertIn("## Preliminary Techno-Economic Feasibility Report", final_report_markdown)
        self.assertIn("## List of Tables", final_report_markdown)
        self.assertIn("## List of Figures", final_report_markdown)
        self.assertIn("## Index", final_report_markdown)
        self.assertIn("## Appendix Index", final_report_markdown)
        self.assertIn("# 1. Executive Summary", final_report_markdown)
        self.assertIn("# 29. References", final_report_markdown)
        self.assertIn("# 30. Appendices and Annexures", final_report_markdown)
        self.assertIn("**Table 1.", final_report_markdown)
        self.assertIn("Figure 9.1.", final_report_markdown)
        self.assertIn("## Appendix Navigation", final_report_markdown)
        self.assertIn("## Appendix A: Material Safety Data Sheet", final_report_markdown)
        self.assertIn("## Appendix B: Python Code and Reproducibility Bundle", final_report_markdown)
        self.assertIn("## Appendix C: Process Design Data Sheet", final_report_markdown)
        self.assertIn("# Executive Summary", formatted_report_markdown)
        self.assertIn("# Chapter 1: Introduction", formatted_report_markdown)
        self.assertIn("# Chapter 2: Literature Survey", formatted_report_markdown)
        self.assertIn("# Chapter 8: Process Flow Diagram", formatted_report_markdown)
        self.assertIn("## List of Tables", formatted_report_markdown)
        self.assertIn("## List of Figures", formatted_report_markdown)
        self.assertIn("- Table 1.", formatted_report_markdown)
        self.assertIn("# Appendices", formatted_report_markdown)
        self.assertIn("Appendix A:", formatted_report_markdown)
        self.assertIn("Prepared for the proposed Ethylene Glycol plant design case in India.", formatted_report_markdown)
        self.assertIn("The route-wise comparison retained for process selection is given below.", formatted_report_markdown)
        self.assertIn("The adopted commercial basis of the project is summarized below.", formatted_report_markdown)
        self.assertIn("The principal financial indicators are summarized below.", formatted_report_markdown)
        self.assertIn("The process-selection chapter uses comparative tables to support the engineering judgment leading to the final route choice.", formatted_report_markdown)
        self.assertIn("Particular emphasis is placed on the commercial basis of the product, since it governs the subsequent process design.", formatted_report_markdown)
        self.assertIn("The comparison shows that the preferred route must satisfy not only chemistry feasibility but also operability and purification practicality.", formatted_report_markdown)
        self.assertIn("The relative strengths and limitations of the candidate routes can be read directly from this comparison.", formatted_report_markdown)
        self.assertIn("The tabulated literature review is used to compare the practical routes before narrowing the discussion to those retained for detailed design.", formatted_report_markdown)
        self.assertIn("This chapter presents the key project-finance metrics and the resulting economic viability of the selected plant configuration.", formatted_report_markdown)
        self.assertIn("The material-balance chapter records the solved stream results in tabulated form so that the plant-wide basis and the unit-wise material movement remain transparent.", formatted_report_markdown)
        self.assertIn("The financial chapter presents the principal indicators in tabulated form and then interprets them from the standpoint of engineering feasibility.", formatted_report_markdown)
        self.assertIn("Table 3.4. Route Selection Comparison", formatted_report_markdown)
        self.assertIn("Appendix", formatted_report_markdown)
        self.assertIn("Detailed calculation traces and supporting technical tables for this chapter are presented in the appendices.", formatted_report_markdown)
        self.assertIn("The relative strengths and limitations of the candidate routes can be read directly from this comparison.", formatted_report_markdown)
        self.assertTrue(runner._load("formatted_report", FormattedReportArtifact).formatted_html)
        formatted_report_html = final_report_formatted_html_path.read_text()
        self.assertNotIn("<li>*Recommendation:**", formatted_report_html)
        self.assertNotIn("<li>*1. Analysis Summary:**", formatted_report_html)
        self.assertIn("<diagram-sheet class='landscape full-page'>", formatted_report_html)
        self.assertIn("<div class='diagram-sheet-figure'><svg", formatted_report_html)
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "diagrams" / "bfd_sheet_1.svg").exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "diagrams" / "pfd_sheet_1.svg").exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "diagrams" / "bfd.drawio").exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "diagrams" / "pfd.drawio").exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "diagrams" / "pid_lite_sheet_1.svg").exists())
        self.assertTrue((Path(self.temp_dir) / runner.config.project_id / "diagrams" / "pid_lite.drawio").exists())
        self.assertIn(
            runner._load("formatter_acceptance", FormatterAcceptanceArtifact).overall_status.value,
            {"conditional", "complete"},
        )
        parity = runner._load("formatter_parity", FormatterParityArtifact)
        acceptance = runner._load("formatter_acceptance", FormatterAcceptanceArtifact)
        self.assertGreaterEqual(parity.numeric_preservation_ratio, 0.95)
        self.assertGreater(parity.overall_parity_score, 0.6)
        self.assertGreaterEqual(parity.table_figure_parity_score, 0.6)
        self.assertGreater(parity.typography_layout_score, 0.6)
        self.assertIn(acceptance.benchmark_parity_status.value, {"conditional", "complete"})
        pdf_doc = fitz.open(pdf_path)
        pdf_fonts = {
            span["font"]
            for page in pdf_doc
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        }
        pdf_doc.close()
        self.assertTrue(any("Roman" in font for font in pdf_fonts))
        self.assertIn("## Annexure I: Evidence and Source Basis", final_report_markdown)
        self.assertIn("## Annexure II: Property and Thermodynamic Registers", final_report_markdown)
        self.assertIn("## Annexure V: Equipment, Utility, and Financial Registers", final_report_markdown)
        self.assertIn("### Mechanical Design Summary View", final_report_markdown)
        self.assertIn("### Utility Island Summary View", final_report_markdown)
        self.assertIn("### Utility Train Package Summary View", final_report_markdown)
        self.assertIn("### Financial Schedule Summary View", final_report_markdown)
        self.assertIn("\n---\n\n# 2. Introduction and Product Profile", final_report_markdown)

    def test_absorption_process_unit_chapter_surfaces_gle_basis(self):
        runner = PipelineRunner(self._config_from_example_file("sulfuric_acid_india_mock.yaml"))
        self._run_to_completion(runner)
        process_unit_chapter = runner.store.load_chapter(runner.config.project_id, "distillation_design")
        equipment_chapter = runner.store.load_chapter(runner.config.project_id, "equipment_design_sizing")
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
        self.assertIn("### Absorber Equation-Substitution Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("A = L / (m * G)", process_unit_chapter.rendered_markdown)
        self.assertIn("Z = NTU * HTU", process_unit_chapter.rendered_markdown)
        self.assertIn("### Absorber Package Sizing Derivation", equipment_chapter.rendered_markdown)
        self.assertIn("Vpack = (pi / 4) * D^2 * Z", equipment_chapter.rendered_markdown)
        self.assertIn("Aeff,total = aeff * Vpack", equipment_chapter.rendered_markdown)
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
        equipment_chapter = runner.store.load_chapter(runner.config.project_id, "equipment_design_sizing")
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
        self.assertIn("### Crystallizer / Filter / Dryer Equation-Substitution Basis", process_unit_chapter.rendered_markdown)
        self.assertIn("S = Cfeed / C*", process_unit_chapter.rendered_markdown)
        self.assertIn("DeltaY = Yout - Yin", process_unit_chapter.rendered_markdown)
        self.assertIn("### Solids Package Sizing Derivation", equipment_chapter.rendered_markdown)
        self.assertIn("mfilter = A * flux", equipment_chapter.rendered_markdown)
        self.assertIn("qA = Q / A", equipment_chapter.rendered_markdown)
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

    def test_bac_benchmark_artifacts_are_emitted_and_consistent(self):
        config = self._bac_benchmark_config()
        runner = PipelineRunner(config)
        state = ProjectRunState(
            project_id=config.project_id,
            model_name=config.model.model_name,
            strict_citation_policy=config.strict_citation_policy,
        )
        runner.store.save_run_state(state)

        runner._run_project_intake()
        runner._run_product_profile()
        runner._run_market_capacity()
        runner._run_literature_route_survey()
        runner._run_property_gap_resolution()
        runner._run_site_selection()
        runner._run_process_synthesis()
        runner._run_rough_alternative_balances()
        runner._run_heat_integration_optimization()
        runner._run_route_selection()
        runner._refresh_scientific_inference("route_selection", state)
        thermo_result = runner._run_thermodynamic_feasibility()
        runner._refresh_scientific_inference("thermodynamic_feasibility", state)
        runner._run_kinetic_feasibility()
        runner._run_block_diagram()
        runner._run_process_description()
        material_result = runner._run_material_balance()
        runner._refresh_scientific_inference("material_balance", state)
        runner._save_report_acceptance(RunStatus.READY)

        commercial_basis = runner._load("commercial_product_basis", CommercialProductBasisArtifact)
        process_selection = runner._load("process_selection_comparison", ProcessSelectionComparisonArtifact)
        purification_sections = runner._load("bac_purification_sections", BACPurificationSectionArtifact)
        impurity_model = runner._load("bac_impurity_model", BACImpurityModelArtifact)
        consistency = runner._load("unit_train_consistency", UnitTrainConsistencyArtifact)
        data_reality = runner._load("data_reality_audit", DataRealityAuditArtifact)
        data_gap_registry = runner._load("data_gap_registry", DataGapRegistryArtifact)
        pseudo_component_basis = runner._load("bac_pseudo_component_basis", BACPseudoComponentBasisArtifact)
        pair_coverage = runner._load("binary_pair_coverage", BinaryPairCoverageArtifact)
        impurity_ledger = runner._load("bac_impurity_ledger", BACImpurityLedgerArtifact)
        recycle_basis = runner._load("recycle_basis", RecycleBasisArtifact)
        missing_data_acceptance = runner._load("missing_data_acceptance", MissingDataAcceptanceArtifact)
        report_acceptance = runner._load("report_acceptance", ReportAcceptanceArtifact)
        thermo_chapter = next(chapter for chapter in thermo_result.chapters if chapter.chapter_id == "thermodynamic_feasibility")
        material_chapter = next(chapter for chapter in material_result.chapters if chapter.chapter_id == "material_balance")
        inspect_text = runner.inspect()

        self.assertAlmostEqual(commercial_basis.active_fraction, 0.5, places=6)
        self.assertGreater(commercial_basis.sold_solution_basis_kg_hr, commercial_basis.active_basis_kg_hr)
        self.assertGreater(process_selection.route_discovery_count, 0)
        self.assertEqual(process_selection.selected_route_id, runner._load("route_selection", RouteSelectionArtifact).selected_route_id)
        self.assertTrue(any(section.section_id == "concentration" for section in purification_sections.sections))
        self.assertTrue(impurity_model.items)
        self.assertIn(consistency.overall_status, {"pass", "warning"})
        self.assertGreater(len(data_reality.rows), 0)
        self.assertGreaterEqual(len(data_gap_registry.items), 5)
        self.assertTrue(pseudo_component_basis.active_nonvolatile)
        self.assertTrue(pair_coverage.rows)
        self.assertTrue(impurity_ledger.items)
        self.assertTrue(recycle_basis.loops)
        self.assertIn(missing_data_acceptance.overall_status.value, {"conditional", "blocked", "complete"})
        self.assertNotIn("product_profile", data_reality.critical_seeded_artifact_refs)
        self.assertNotIn("commercial_product_basis", data_reality.critical_seeded_artifact_refs)
        self.assertNotIn("property_packages", data_reality.critical_seeded_artifact_refs)
        self.assertIn("process_selection_comparison", data_reality.critical_seeded_artifact_refs)
        self.assertEqual(report_acceptance.real_data_status, "conditional")
        self.assertGreater(report_acceptance.real_data_coverage_fraction, 0.0)
        self.assertNotIn("CRYS-201", material_chapter.rendered_markdown)
        self.assertNotIn("FILT-201", material_chapter.rendered_markdown)
        self.assertNotIn("DRY-301", material_chapter.rendered_markdown)
        self.assertIn("### BAC Purification Sections", thermo_chapter.rendered_markdown)
        self.assertIn("### BAC Impurity Model", material_chapter.rendered_markdown)
        self.assertIn("commercial_product_basis:", inspect_text)
        self.assertIn("bac_benchmark_basis:", inspect_text)
        self.assertIn("route_evidence_status:", inspect_text)
        self.assertIn("data_reality:", inspect_text)

    def test_bac_pipeline_emits_rendering_audit_benchmark_and_package_after_instrumentation(self):
        config = self._bac_benchmark_config()
        runner = PipelineRunner(config)
        state = ProjectRunState(
            project_id=config.project_id,
            model_name=config.model.model_name,
            strict_citation_policy=config.strict_citation_policy,
        )
        runner.store.save_run_state(state)

        runner._run_project_intake()
        runner._run_product_profile()
        runner._run_market_capacity()
        runner._run_literature_route_survey()
        runner._run_property_gap_resolution()
        runner._run_site_selection()
        runner._run_process_synthesis()
        runner._run_rough_alternative_balances()
        runner._run_heat_integration_optimization()
        runner._run_route_selection()
        runner._refresh_scientific_inference("route_selection", state)
        runner._run_thermodynamic_feasibility()
        runner._refresh_scientific_inference("thermodynamic_feasibility", state)
        runner._run_kinetic_feasibility()
        runner._run_block_diagram()
        runner._run_process_description()
        runner._run_material_balance()
        runner._refresh_scientific_inference("material_balance", state)
        runner._run_energy_balance()
        runner._run_reactor_design()
        runner._run_distillation_design()
        runner._run_equipment_sizing()
        runner._run_mechanical_design_moc()
        runner._run_storage_utilities()
        runner._run_instrumentation_control()

        rendering_audit = runner._load("bac_rendering_audit", BACRenderingAuditArtifact)
        benchmark = runner._load("bac_diagram_benchmark", BACDiagramBenchmarkArtifact)
        drawing_package = runner._load("bac_drawing_package", BACDrawingPackageArtifact)
        inspect_text = runner.inspect()

        self.assertIn(rendering_audit.overall_status, {"complete", "conditional", "blocked"})
        self.assertIn(benchmark.overall_status, {"complete", "conditional", "blocked"})
        self.assertIn(drawing_package.overall_status, {"complete", "conditional", "blocked"})
        self.assertGreaterEqual(len(rendering_audit.rows), 3)
        self.assertGreaterEqual(len(benchmark.rows), 4)
        self.assertGreaterEqual(len(drawing_package.register_rows), 5)
        self.assertIn("bac_diagrams:", inspect_text)
        self.assertIn("rendering_audit:", inspect_text)
        self.assertIn("benchmark:", inspect_text)
        self.assertIn("package_workflow:", inspect_text)
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "bac_rendering_audit.json").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "bac_diagram_benchmark.json").exists())
        self.assertTrue((runner.store.project_dir(runner.config.project_id) / "artifacts" / "bac_drawing_package.json").exists())

    def test_bac_strict_real_data_mode_blocks_acceptance_when_seeded_dependencies_remain(self):
        config = self._bac_benchmark_config()
        config.real_data_mode = RealDataMode.STRICT
        config.minimum_real_data_fraction = 0.75
        runner = PipelineRunner(config)
        state = ProjectRunState(
            project_id=config.project_id,
            model_name=config.model.model_name,
            strict_citation_policy=config.strict_citation_policy,
        )
        runner.store.save_run_state(state)

        runner._run_project_intake()
        runner._run_product_profile()
        runner._run_market_capacity()
        runner._run_literature_route_survey()
        runner._run_property_gap_resolution()
        runner._run_site_selection()
        runner._run_process_synthesis()
        runner._run_rough_alternative_balances()
        runner._run_heat_integration_optimization()
        runner._run_route_selection()
        runner._run_thermodynamic_feasibility()
        runner._run_kinetic_feasibility()
        runner._run_block_diagram()
        runner._run_process_description()
        runner._run_material_balance()
        runner._save_report_acceptance(RunStatus.READY)

        acceptance = runner._load("report_acceptance", ReportAcceptanceArtifact)
        self.assertEqual(acceptance.overall_status.value, "blocked")
        self.assertIn("real_data_policy_blocked", acceptance.blocking_issue_codes)
        self.assertGreater(acceptance.real_data_coverage_fraction, 0.0)
        self.assertTrue(acceptance.critical_seeded_dependencies)

    def test_route_evidence_basis_reclassifies_external_cited_routes(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        survey = RouteSurveyArtifact(
            routes=[
                RouteOption(
                    route_id="bac_live_route",
                    name="BAC live cited route",
                    reaction_equation="A + B -> P",
                    participants=[],
                    evidence_score=0.86,
                    operating_temperature_c=85.0,
                    operating_pressure_bar=2.0,
                    residence_time_hr=2.0,
                    yield_fraction=0.95,
                    selectivity_fraction=0.96,
                    scale_up_notes="test",
                    route_score=8.5,
                    rationale="test",
                    citations=["src_lit_01"],
                )
            ],
            markdown="test",
            citations=["src_lit_01"],
            assumptions=[],
        )
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="src_lit_01",
                    source_kind=SourceKind.LITERATURE,
                    source_domain=SourceDomain.TECHNICAL,
                    title="BAC process paper",
                    citation_text="BAC process paper",
                    geographic_scope=GeographicScope.GLOBAL,
                )
            ],
            technical_source_ids=["src_lit_01"],
            corpus_excerpt="BAC process paper excerpt",
        )

        updated = runner._apply_route_evidence_basis(survey, bundle)

        self.assertEqual(updated.routes[0].route_origin, "hybrid")
        self.assertEqual(updated.routes[0].route_evidence_basis, "cited_technical")

    def test_report_acceptance_uses_route_evidence_basis_for_bac_process_selection(self):
        config = self._bac_benchmark_config()
        runner = PipelineRunner(config)
        state = ProjectRunState(
            project_id=config.project_id,
            model_name=config.model.model_name,
            strict_citation_policy=config.strict_citation_policy,
        )
        runner.store.save_run_state(state)
        runner._run_project_intake()
        runner._save(
            "route_selection",
            RouteSelectionArtifact(
                selected_route_id="bac_live_route",
                justification="Selected from cited live evidence.",
                comparison_markdown="test",
                citations=["src_lit_01"],
                assumptions=[],
            ),
        )
        runner._save(
            "process_selection_comparison",
            ProcessSelectionComparisonArtifact(
                selected_route_id="bac_live_route",
                selected_route_name="BAC live cited route",
                route_discovery_count=1,
                retained_route_count=1,
                eliminated_route_count=0,
                rows=[
                    RouteSelectionComparisonRow(
                        route_id="bac_live_route",
                        route_name="BAC live cited route",
                        route_origin="hybrid",
                        route_evidence_basis="cited_technical",
                        evidence_score=0.86,
                        scientific_status="design_feasible",
                        selected=True,
                        citations=["src_lit_01"],
                        assumptions=[],
                    )
                ],
                citations=["src_lit_01"],
                assumptions=[],
            ),
        )

        runner._save_report_acceptance(RunStatus.READY)
        acceptance = runner._load("report_acceptance", ReportAcceptanceArtifact)

        self.assertEqual(acceptance.route_evidence_status, "complete")

    def test_bac_route_survey_rebinds_to_external_technical_sources_when_available(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        survey = runner.reasoning.survey_routes(runner.config.basis, [], "")
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="src_bac_route_01",
                    source_kind=SourceKind.LITERATURE,
                    source_domain=SourceDomain.TECHNICAL,
                    title="BAC process note",
                    citation_text="BAC process note",
                    geographic_scope=GeographicScope.GLOBAL,
                )
            ],
            technical_source_ids=["src_bac_route_01"],
            corpus_excerpt="BAC process note",
        )

        updated = runner._replace_bac_route_survey_with_external_candidates(survey, bundle)

        self.assertEqual(updated.citations, ["src_bac_route_01"])
        self.assertTrue(all(route.route_origin == "hybrid" for route in updated.routes))
        self.assertTrue(all(route.route_evidence_basis in {"cited_technical", "mixed_cited"} for route in updated.routes))
        self.assertTrue(all(route.citations == ["src_bac_route_01"] for route in updated.routes))

    def test_bac_site_selection_rebinds_to_external_site_sources_when_available(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        artifact = runner.reasoning.select_site(runner.config.basis, [], "")
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="src_bac_site_01",
                    source_kind=SourceKind.COMPANY_REPORT,
                    source_domain=SourceDomain.SITE,
                    title="BAC site note",
                    citation_text="BAC site note",
                    geographic_scope=GeographicScope.INDIA,
                )
            ],
            india_source_ids=["src_bac_site_01"],
            corpus_excerpt="BAC site note",
        )

        updated = runner._replace_bac_site_selection_with_external_candidates(artifact, bundle)

        self.assertEqual(updated.citations, ["src_bac_site_01"])
        self.assertTrue(all(candidate.citations == ["src_bac_site_01"] for candidate in updated.candidates))
        self.assertTrue(all(location.citations == ["src_bac_site_01"] for location in updated.india_location_data))
        self.assertIn("externally sourced", updated.markdown.lower())

    def test_site_selection_audit_credits_selected_external_site_evidence(self):
        config = self._bac_benchmark_config()
        config.model.backend = "google"
        runner = PipelineRunner(config)
        state = ProjectRunState(
            project_id=config.project_id,
            model_name=config.model.model_name,
            strict_citation_policy=config.strict_citation_policy,
        )
        runner.store.save_run_state(state)
        runner._save("benchmark_manifest", build_benchmark_manifest(config))
        runner._save(
            "site_selection",
            SiteSelectionArtifact(
                candidates=[
                    SiteOption(
                        name="Dahej",
                        state="Gujarat",
                        raw_material_score=9,
                        logistics_score=9,
                        utility_score=9,
                        business_score=8,
                        total_score=35,
                        rationale="test",
                        citations=["src_site_01"],
                    )
                ],
                selected_site="Dahej",
                india_location_data=[
                    IndianLocationDatum(
                        location_id="site_dahej",
                        site_name="Dahej",
                        state="Gujarat",
                        port_access="test",
                        utility_note="test",
                        logistics_note="test",
                        regulatory_note="test",
                        reference_year=2025,
                        citations=["src_site_01"],
                    )
                ],
                markdown="test",
                citations=["src_site_01"],
                assumptions=[],
            ),
        )

        runner._save_report_acceptance(RunStatus.READY)
        audit = runner._load("data_reality_audit", DataRealityAuditArtifact)
        site_row = next(row for row in audit.rows if row.artifact_ref == "site_selection")

        self.assertEqual(site_row.dominant_class.value, "live_fetched")
        self.assertGreater(site_row.real_data_fraction, 0.5)
        self.assertNotIn("site_selection", audit.critical_seeded_artifact_refs)

    def test_pipeline_blocks_on_missing_citations(self):
        runner = PipelineRunner(self._config_from_example())
        runner.reasoning = BrokenMockReasoningService()
        state = runner.run()
        self.assertEqual(state.run_status.value, "blocked")
        self.assertEqual(state.blocked_stage_id, "product_profile")

    def test_repair_artifact_citations_filters_internal_ids(self):
        runner = PipelineRunner(self._config_from_example())
        runner._run_project_intake()
        bundle = runner._load("research_bundle", ResearchBundle)
        artifact = NarrativeArtifact(
            artifact_id="safety_environment",
            title="SHE",
            markdown="test",
            summary="test",
            citations=["route_2", "R-101", bundle.sources[0].source_id],
            assumptions=[],
        )

        fallback_citations = [source.source_id for source in bundle.sources[:2]]
        runner._repair_artifact_citations(artifact, fallback_citations, "normalized")

        self.assertEqual(artifact.citations, [bundle.sources[0].source_id])
        self.assertIn("normalized", artifact.assumptions)

    def test_site_selection_inherits_location_citations_when_row_ids_are_missing(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        runner.reasoning = BrokenSiteCitationReasoningService()
        runner._run_project_intake()
        result = runner._run_site_selection()

        self.assertFalse(any(issue.code == "uncited_india_location" for issue in result.issues))
        artifact = runner._load("site_selection", SiteSelectionArtifact)
        self.assertTrue(artifact.india_location_data)
        self.assertTrue(all(item.citations for item in artifact.india_location_data))

    def test_site_selection_allows_specific_location_label_to_match_selected_cluster_label(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        runner.reasoning = BrokenSiteCitationReasoningService()
        runner._run_project_intake()
        runner._run_site_selection()
        artifact = runner._load("site_selection", SiteSelectionArtifact)
        artifact.selected_site = "Dahej PCPIR"
        artifact.india_location_data[0].site_name = "Payal Industrial Park, Dahej PCPIR"

        issues = validate_site_selection_consistency(artifact)
        self.assertFalse(any(issue.code == "selected_site_missing_location_evidence" for issue in issues))

    def test_product_profile_inherits_property_row_citations_when_row_ids_are_missing(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        runner.reasoning = MissingPropertyRowCitationReasoningService()
        runner._run_project_intake()
        result = runner._run_product_profile()

        self.assertFalse(any(issue.code == "missing_property_sources" for issue in result.issues))
        artifact = runner._load("product_profile", ProductProfileArtifact)
        self.assertTrue(artifact.properties)
        self.assertTrue(all(item.supporting_sources or item.citations for item in artifact.properties))

    def test_bac_product_profile_synthesizes_required_unavailability_rows_when_live_model_omits_them(self):
        runner = PipelineRunner(self._bac_benchmark_config())
        runner.reasoning = MissingCriticalBACPropertyReasoningService()
        runner._run_project_intake()
        result = runner._run_product_profile()

        self.assertFalse(any(issue.code == "missing_critical_properties" for issue in result.issues))
        artifact = runner._load("product_profile", ProductProfileArtifact)
        property_names = {item.name.strip().lower() for item in artifact.properties}
        self.assertIn("melting point", property_names)
        self.assertIn("boiling point", property_names)
        self.assertIn("density", property_names)
        synthesized = {item.name: item for item in artifact.properties if item.name in {"Melting Point", "Boiling Point", "Density"}}
        self.assertTrue(all(item.value == "Not Available" for item in synthesized.values()))
        self.assertTrue(all(item.supporting_sources or item.citations for item in synthesized.values()))

    def test_property_library_matches_common_solvents_and_formulation_water_aliases(self):
        for name in ("Acetonitrile", "Butanone", "Water (for final formulation)"):
            key, entry = match_benchmark_entry(name)
            self.assertIsNotNone(key)
            self.assertIsNotNone(entry)
            self.assertIn("properties", entry)
            self.assertIn("molecular_weight", entry["properties"])
            self.assertIn("normal_boiling_point", entry["properties"])
            self.assertIn("liquid_density", entry["properties"])
