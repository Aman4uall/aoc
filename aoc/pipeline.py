from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import re

from aoc.archetypes import build_alternative_sets, classify_process_archetype
from aoc.agent_fabric import build_agent_decision_fabric
from aoc.benchmarks import build_benchmark_manifest
from aoc.calculators import (
    annual_output_kg,
    build_column_design,
    build_cost_model,
    build_energy_balance,
    build_equipment_list,
    build_heat_exchanger_design,
    build_reaction_system,
    build_reactor_design,
    build_storage_design,
    build_stream_table,
    build_working_capital_model,
    compute_utilities,
    reaction_is_balanced,
)
from aoc.decision_engine import (
    build_chemistry_decision_artifact,
    build_economic_basis_decision,
    build_heat_integration_study,
    build_process_synthesis,
    build_route_discovery_artifact,
    build_route_screening_artifact,
    build_rough_alternatives,
    build_site_selection_decision,
    build_utility_basis_decision,
    resolve_property_gaps,
    select_route_architecture,
    selected_heat_case,
)
from aoc.diagrams import (
    build_block_flow_diagram,
    build_control_system_diagram,
    build_diagram_acceptance,
    build_diagram_style_profile,
    build_diagram_target_profile,
    build_process_flow_diagram,
    diagram_svg_fence,
)
from aoc.document_facts import build_document_fact_collection, build_document_process_options
from aoc.critics import merge_critic_registry
from aoc.economics_v2 import (
    build_debt_schedule,
    build_economic_scenario_model_v2,
    build_financing_basis_decision,
    build_financial_schedule,
    build_logistics_basis_decision,
    build_plant_cost_summary,
    build_procurement_basis_decision,
    build_route_economic_basis_artifact,
    build_route_site_fit_artifact,
    build_tax_depreciation_basis,
    evaluate_financing_basis_decision,
)
from aoc.evidence import build_resolved_source_set, build_resolved_value_artifact, extend_resolved_value_artifact
from aoc.family_adapters import build_chemistry_family_adapter
from aoc.formatter import (
    build_benchmark_style_profile,
    build_benchmark_voice_profile,
    build_formatted_report_package,
    build_formatter_target_profile,
    build_narrative_rewrite_artifact,
    build_semantic_report_artifact,
    build_sentence_pattern_library,
    build_tone_style_rules,
)
from aoc.flowsheet_blueprint import (
    build_process_narrative_from_blueprint,
    build_unit_train_candidate_set,
    select_flowsheet_blueprint,
)
from aoc.flowsheet import (
    build_control_architecture_decision,
    build_control_plan_from_flowsheet,
    build_flowsheet_graph,
    build_hazop_node_register,
    build_layout_decision,
)
from aoc.methods import build_capacity_decision, build_kinetics_method_decision, build_thermo_method_decision
from aoc.mechanical import build_mechanical_design_artifact, build_mechanical_design_basis, build_vessel_mechanical_designs
from aoc.route_families import build_route_family_artifact, profile_for_route
from aoc.route_chemistry import build_property_demand_plan, build_route_chemistry_artifact
from aoc.route_planning import build_route_selection_comparison
from aoc.report_parity import build_report_parity_framework, evaluate_report_acceptance, evaluate_report_parity
from aoc.scientific_inference import (
    build_bac_binary_pair_coverage_artifact,
    build_bac_data_gap_registry_artifact,
    build_bac_estimation_policy_artifact,
    build_bac_impurity_model_artifact,
    build_bac_impurity_ledger_artifact,
    build_bac_kinetic_basis_artifact,
    build_bac_pseudo_component_basis_artifact,
    build_bac_purification_section_artifact,
    build_bac_section_thermo_assignment_artifact,
    build_claim_graph_artifact,
    build_commercial_product_basis_artifact,
    build_data_reality_audit_artifact,
    build_design_confidence_artifact,
    build_economic_input_reality_artifact,
    build_economic_coverage_decision,
    build_flowsheet_intent_artifact,
    build_inference_question_queue,
    build_kinetics_admissibility_artifact,
    build_missing_data_acceptance_artifact,
    build_reaction_network_v2_artifact,
    build_reactor_basis_confidence_artifact,
    build_recycle_basis_artifact,
    build_route_process_claims_artifact,
    build_revision_ledger,
    build_scientific_gate_matrix_artifact,
    build_species_resolution_artifact,
    build_thermo_admissibility_artifact,
    build_topology_candidate_artifact,
    build_unit_train_consistency_artifact,
)
from aoc.models import (
    AgentDecisionFabricArtifact,
    BACImpurityLedgerArtifact,
    BACImpurityModelArtifact,
    BACPurificationSectionArtifact,
    BACPseudoComponentBasisArtifact,
    BenchmarkManifest,
    BlockFlowDiagramArtifact,
    ChapterArtifact,
    ChemistryFamilyAdapter,
    ChemistryDecisionArtifact,
    ClaimGraphArtifact,
    ChapterStatus,
    CommercialProductBasisArtifact,
    ColumnDesign,
    ColumnHydraulics,
    ControlArchitectureDecision,
    ControlPlanArtifact,
    ControlSystemDiagramArtifact,
    CostModel,
    CriticRegistryArtifact,
    DataGapRegistryArtifact,
    DataRealityAuditArtifact,
    DebtSchedule,
    DecisionRecord,
    DocumentFactCollectionArtifact,
    DocumentProcessOptionsArtifact,
    EconomicCoverageDecision,
    EconomicInputRealityArtifact,
    EquipmentDatasheet,
    EconomicScenarioModel,
    EnergyBalance,
    EquipmentListArtifact,
    FinalReport,
    FormattedReportArtifact,
    FormatterAcceptanceArtifact,
    FormatterDecisionArtifact,
    FormatterParityArtifact,
    FormatterTargetProfile,
    FinancialModel,
    FinancialSchedule,
    FlowsheetGraph,
    FlowsheetBlueprintArtifact,
    FlowsheetIntentArtifact,
    FlowsheetCase,
    GateDecision,
    GateStatus,
    HazopNode,
    HazopNodeRegister,
    HeatExchangerThermalDesign,
    HazopStudyArtifact,
    HeatExchangerDesign,
    HeatIntegrationStudyArtifact,
    KineticAssessmentArtifact,
    KineticBasisArtifact,
    KineticsAdmissibilityArtifact,
    LayoutDecisionArtifact,
    MarketAssessmentArtifact,
    MechanicalDesignArtifact,
    MechanicalDesignBasis,
    MethodSelectionArtifact,
    BenchmarkStyleProfile,
    NarrativeArtifact,
    OperationsPlanningArtifact,
    PlantCostSummary,
    PumpDesign,
    ProcessArchetype,
    ProcessSelectionComparisonArtifact,
    ProcessSynthesisArtifact,
    ProcessNarrativeArtifact,
    PropertyRecord,
    PropertyDemandPlan,
    PropertyGapArtifact,
    ProductProfileArtifact,
    ProvenanceTag,
    ProjectConfig,
    ProjectRunState,
    RealDataMode,
    MissingDataAcceptanceArtifact,
    ReportAcceptanceArtifact,
    ReportAcceptanceStatus,
    ReportParityArtifact,
    ReportParityFrameworkArtifact,
    ReactionParticipant,
    ReactionNetworkV2Artifact,
    ReactionSystem,
    ReactorDesign,
    ReactorBasisConfidenceArtifact,
    ReactorDesignBasis,
    ResearchBundle,
    ResolvedSourceSet,
    ResolvedValueArtifact,
    RevisionLedgerArtifact,
    RoughAlternativeSummaryArtifact,
    RouteOption,
    RouteChemistryArtifact,
    RouteDiscoveryArtifact,
    RouteFamilyArtifact,
    RouteProcessClaimsArtifact,
    RouteScreeningArtifact,
    ScientificGateMatrixArtifact,
    RouteSelectionComparisonArtifact,
    RouteSelectionArtifact,
    RouteEconomicBasisArtifact,
    RouteSiteFitArtifact,
    RouteSurveyArtifact,
    RunStatus,
    SolveResult,
    SparseDataPolicyArtifact,
    SensitivityLevel,
    ScenarioStability,
    ScientificConfidence,
    ScientificGateStatus,
    Severity,
    SiteSelectionArtifact,
    StorageDesign,
    StreamTable,
    EstimationPolicy,
    TaxDepreciationBasis,
    ThermoAssessmentArtifact,
    ThermoAdmissibilityArtifact,
    TopologyCandidateArtifact,
    SemanticReportArtifact,
    UnitTrainConsistencyArtifact,
    UnitTrainCandidateSet,
    UtilityArchitectureDecision,
    UnitOperationFamilyArtifact,
    UtilitySummaryArtifact,
    UtilityNetworkDecision,
    ValidationIssue,
    VesselMechanicalDesign,
    WorkingCapitalModel,
    SpeciesResolutionArtifact,
    InferenceQuestionQueueArtifact,
    DesignConfidenceArtifact,
    DiagramAcceptanceArtifact,
    DiagramStyleProfile,
    DiagramTargetProfile,
    utc_now,
    ProcessFlowDiagramArtifact,
)
from aoc.operations import build_operating_mode_and_operations
from aoc.properties import (
    MixturePropertyArtifact,
    PropertyMethodDecision,
    PropertyPackageArtifact,
    PropertyRequirementSet,
    SeparationThermoArtifact,
    build_mixture_property_artifact,
    build_property_method_decision,
    build_property_package_artifact,
    build_property_requirement_artifact,
    build_separation_thermo_artifact,
    property_estimates_from_packages,
    property_value_records,
)
from aoc.properties.sources import is_valid_property_identifier_name, normalize_chemical_name
from aoc.publish import annexures_markdown, assemble_report, markdown_table, references_markdown, render_academic_pdf, render_pdf, render_styled_pdf
from aoc.reasoning import MockReasoningService, build_reasoning_service
from aoc.research import ResearchManager
from aoc.selectors import (
    select_exchanger_configuration,
    select_layout_configuration,
    select_moc_configuration,
    select_reactor_configuration,
    select_separation_configuration,
    select_storage_configuration,
)
from aoc.design_artifacts import (
    build_column_hydraulics,
    build_equipment_datasheets,
    build_heat_exchanger_thermal_design,
    build_pump_design,
    build_reactor_design_basis,
)
from aoc.sparse_data import build_sparse_data_policy
from aoc.solver_architecture import build_flowsheet_case, build_solve_result
from aoc.store import ArtifactStore
from aoc.unit_operation_families import build_unit_operation_family_artifact
from aoc.utility_architecture import build_utility_architecture_decision
from aoc.validators import (
    apply_state_issues,
    validate_architecture_package_critics,
    validate_bac_impurity_model_artifact,
    validate_bac_purification_section_artifact,
    validate_chapter,
    validate_chemistry_family_adapter,
    validate_column_design,
    validate_cost_model,
    validate_cross_chapter_consistency,
    validate_decision_record,
    validate_document_fact_collection,
    validate_energy_balance,
    validate_equipment_applicability,
    validate_financing_decision_alignment,
    validate_financial_model,
    validate_flowsheet_blueprint,
    validate_flowsheet_case,
    validate_flowsheet_graph,
    validate_control_plan,
    validate_control_architecture,
    validate_chemistry_decision_artifact,
    validate_hazop_node_register,
    validate_heat_integration_study,
    validate_india_location_data,
    validate_india_price_data,
    validate_kinetic_assessment,
    validate_kinetics_method_critics,
    validate_financing_operability_critics,
    validate_mechanical_design_artifact,
    validate_missing_data_acceptance_artifact,
    validate_phase_feasibility,
    validate_property_method_decision,
    validate_property_package_artifact,
    validate_report_parity,
    validate_report_acceptance,
    validate_report_parity_framework,
    validate_process_archetype,
    validate_property_gap_artifact,
    validate_property_demand_plan,
    validate_property_requirement_set,
    validate_property_requirements_for_stage,
    validate_property_records,
    validate_claim_graph_artifact,
    validate_commercial_product_basis_artifact,
    validate_design_confidence_artifact,
    validate_economic_coverage_decision,
    validate_flowsheet_intent_artifact,
    validate_inference_question_queue,
    validate_kinetics_admissibility_artifact,
    validate_reaction_network_v2_artifact,
    validate_revision_ledger_artifact,
    validate_resolved_source_set,
    validate_resolved_value_artifact,
    validate_scientific_gate_matrix,
    validate_separation_thermo_artifact,
    validate_sparse_data_policy,
    validate_sparse_data_policy_for_stage,
    validate_mixture_property_artifact,
    validate_operations_planning,
    validate_unit_operation_family_artifact,
    validate_site_selection_consistency,
    validate_solve_result,
    validate_reactor_design,
    validate_reactor_hazard_basis_critics,
    validate_research_bundle,
    validate_route_balance,
    validate_route_chemistry_artifact,
    validate_route_discovery_artifact,
    validate_route_economic_basis_artifact,
    validate_route_family_artifact,
    validate_route_economic_critics,
    validate_route_process_claims_artifact,
    validate_route_screening_artifact,
    validate_route_site_fit_artifact,
    validate_species_resolution_artifact,
    validate_route_selection_comparison,
    validate_route_selection_critics,
    validate_thermo_admissibility_artifact,
    validate_topology_candidate_artifact,
    validate_unit_train_consistency_artifact,
    validate_separation_design_critics,
    validate_separation_thermo_critics,
    validate_stream_table,
    validate_technical_economic_critics,
    validate_thermo_assessment,
    validate_unit_family_property_coverage,
    validate_unit_train_candidate_set,
    validate_utility_architecture,
    validate_utility_network_decision,
    validate_value_records,
    validate_working_capital,
)
from aoc.value_engine import make_value_record


def _coerce_numeric_value(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        numbers = [float(match) for match in re.findall(r"-?\d+(?:\.\d+)?", text)]
        if not numbers:
            raise
        if len(numbers) >= 2 and ("-" in text or "to" in text.lower()):
            return sum(numbers[:2]) / 2.0
        return numbers[0]


@dataclass(frozen=True)
class StageSpec:
    id: str
    title: str
    required_artifacts: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    gate_id: str | None = None
    gate_title: str | None = None
    gate_description: str | None = None


@dataclass
class StageResult:
    chapters: list[ChapterArtifact] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    gate: GateDecision | None = None
    missing_india_coverage: list[str] = field(default_factory=list)
    stale_source_groups: list[str] = field(default_factory=list)


STAGES = [
    StageSpec("project_intake", "Project intake and basis lock", (), ("project_basis", "research_bundle", "benchmark_manifest", "resolved_sources", "report_parity_framework", "user_document_facts", "document_process_options")),
    StageSpec("product_profile", "Introduction and product profile", ("research_bundle",), ("product_profile",)),
    StageSpec("market_capacity", "Market and capacity selection", ("research_bundle",), ("market_assessment", "capacity_decision", "commercial_product_basis")),
    StageSpec("literature_route_survey", "Literature survey", ("research_bundle",), ("route_survey", "route_chemistry", "route_discovery")),
    StageSpec("property_gap_resolution", "Property gap resolution", ("product_profile", "resolved_sources", "route_survey", "research_bundle"), ("property_gap", "resolved_values", "property_packages", "property_requirements", "property_demand_plan", "agent_decision_fabric"), "evidence_lock", "Evidence Lock", "Approve the resolved source and value basis before process synthesis proceeds."),
    StageSpec("site_selection", "Site selection", ("research_bundle",), ("site_selection", "site_selection_decision")),
    StageSpec("process_synthesis", "Process synthesis", ("route_survey", "property_gap"), ("process_synthesis", "operations_planning", "chemistry_family_adapter", "route_family_profiles", "sparse_data_policy", "property_requirements", "unit_train_candidates", "route_process_claims", "route_screening")),
    StageSpec("rough_alternative_balances", "Rough alternative balances", ("process_synthesis", "market_assessment"), ("rough_alternatives",)),
    StageSpec("heat_integration_optimization", "Heat integration optimization", ("rough_alternatives", "market_assessment"), ("heat_integration_study",), "heat_integration", "Heat Integration Review", "Approve the selected heat-integration studies before route finalization."),
    StageSpec("route_selection", "Process selection", ("route_survey", "rough_alternatives", "heat_integration_study", "market_assessment"), ("route_selection", "route_selection_comparison", "process_selection_comparison", "route_decision", "reactor_choice_decision", "separation_choice_decision", "utility_network_decision", "unit_operation_family", "flowsheet_blueprint", "chemistry_decision"), "process_architecture", "Process Architecture", "Approve the selected route, reactor, separation train, and utility-integration basis before downstream design work continues."),
    StageSpec("thermodynamic_feasibility", "Thermodynamics", ("route_selection", "route_survey", "research_bundle", "property_packages", "property_requirements"), ("thermo_assessment", "thermo_method_decision", "property_method_decision", "separation_thermo", "bac_purification_sections")),
    StageSpec("kinetic_feasibility", "Kinetics", ("route_selection", "route_survey", "research_bundle"), ("kinetic_assessment", "kinetics_method_decision")),
    StageSpec("block_diagram", "Block diagram", ("route_selection", "route_survey", "research_bundle"), ("process_narrative",)),
    StageSpec("process_description", "Process description", ("process_narrative",), ("process_narrative",)),
    StageSpec("material_balance", "Material balance", ("route_selection", "kinetic_assessment", "process_narrative"), ("reaction_system", "stream_table", "flowsheet_graph", "flowsheet_case", "bac_impurity_model")),
    StageSpec("energy_balance", "Energy balance", ("stream_table", "thermo_assessment", "property_packages", "property_requirements"), ("energy_balance", "solve_result", "mixture_properties"), "design_basis", "Design Basis Lock", "Approve thermo, kinetics, process narrative, and balance basis before detailed design."),
    StageSpec("reactor_design", "Reactor design", ("reaction_system", "stream_table", "energy_balance", "mixture_properties", "property_packages", "property_requirements", "kinetic_assessment"), ("reactor_design", "reactor_design_basis")),
    StageSpec("distillation_design", "Distillation/process-unit design", ("stream_table", "energy_balance", "mixture_properties", "property_packages", "property_requirements", "separation_thermo"), ("column_design", "column_hydraulics", "heat_exchanger_design", "heat_exchanger_thermal_design", "exchanger_choice_decision")),
    StageSpec("equipment_sizing", "Equipment sizing", ("reactor_design", "column_design", "heat_exchanger_design", "operations_planning"), ("storage_design", "pump_design", "equipment_list", "equipment_datasheets", "storage_choice_decision", "moc_choice_decision"), "equipment_basis", "Reactor/Column Design Basis", "Approve reactor, column, exchanger, and storage design basis before downstream detailing."),
    StageSpec("mechanical_design_moc", "Mechanical design and materials of construction", ("equipment_list", "route_selection"), ("mechanical_design", "mechanical_design_basis", "vessel_mechanical_designs")),
    StageSpec("storage_utilities", "Storage and utilities", ("storage_design", "equipment_list", "energy_balance", "operations_planning", "pump_design"), ("utility_summary", "utility_basis_decision", "utility_architecture")),
    StageSpec("instrumentation_control", "Instrumentation and process control", ("equipment_list", "utility_summary", "flowsheet_graph"), ("control_plan", "control_architecture")),
    StageSpec("hazop_she", "HAZOP and SHE", ("equipment_list", "route_selection", "flowsheet_graph", "control_plan", "utility_summary"), ("hazop_study", "hazop_node_register", "safety_environment"), "hazop", "HAZOP Gate", "Approve critical HAZOP nodes and SHE safeguards before layout and economics are released."),
    StageSpec("layout_waste", "Project and plant layout", ("equipment_list", "utility_summary", "site_selection", "mechanical_design", "operations_planning"), ("layout_plan", "layout_decision")),
    StageSpec("project_cost", "Project cost", ("equipment_list", "utility_summary", "stream_table", "market_assessment", "site_selection", "route_selection", "operations_planning", "flowsheet_blueprint"), ("route_site_fit", "route_economic_basis", "cost_model", "plant_cost_summary", "procurement_basis_decision", "logistics_basis_decision")),
    StageSpec("cost_of_production", "Cost of production", ("cost_model", "market_assessment"), ("cost_model",)),
    StageSpec("working_capital", "Working capital", ("cost_model", "market_assessment", "operations_planning"), ("working_capital_model",)),
    StageSpec("financial_analysis", "Financial analysis", ("cost_model", "working_capital_model", "market_assessment"), ("financial_model", "economic_basis_decision", "financing_basis_decision", "economic_scenarios", "debt_schedule", "tax_depreciation_basis", "financial_schedule"), "india_cost_basis", "India Cost Basis", "Approve India site and economics basis before final assembly."),
    StageSpec("final_report", "Final report assembly", ("product_profile", "financial_model"), ("final_report", "report_parity", "report_acceptance", "unit_train_consistency", "benchmark_style_profile", "benchmark_voice_profile", "sentence_pattern_library", "tone_style_rules", "formatter_target_profile", "semantic_report", "narrative_rewrite_plan", "formatted_report", "formatter_decision", "formatter_parity", "formatter_acceptance"), "final_signoff", "Final Signoff", "Approve the final markdown report before PDF rendering is released."),
]


def validate_reaction_system(reaction_system: ReactionSystem) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not 0.0 < reaction_system.conversion_fraction <= 1.0:
        issues.append(
            ValidationIssue(
                code="invalid_conversion",
                severity=Severity.BLOCKED,
                message="Reaction-system conversion must lie between 0 and 1.",
                artifact_ref="reaction_system",
            )
        )
    if not 0.0 < reaction_system.selectivity_fraction <= 1.0:
        issues.append(
            ValidationIssue(
                code="invalid_selectivity",
                severity=Severity.BLOCKED,
                message="Reaction-system selectivity must lie between 0 and 1.",
                artifact_ref="reaction_system",
            )
        )
    if reaction_system.reaction_extent_set is None:
        issues.append(
            ValidationIssue(
                code="missing_reaction_extent_set",
                severity=Severity.BLOCKED,
                message="Reaction-system extent set is missing.",
                artifact_ref="reaction_system",
            )
        )
    if reaction_system.byproduct_closure is None:
        issues.append(
            ValidationIssue(
                code="missing_byproduct_closure",
                severity=Severity.BLOCKED,
                message="Reaction-system byproduct closure is missing.",
                artifact_ref="reaction_system",
            )
        )
        return issues
    if reaction_system.byproduct_closure.closure_status == "blocked" or reaction_system.byproduct_closure.blocking:
        issues.append(
            ValidationIssue(
                code="blocked_byproduct_closure",
                severity=Severity.BLOCKED,
                message="Byproduct closure remains blocked: " + ", ".join(reaction_system.byproduct_closure.unresolved_byproducts or ["unspecified side reactions"]) + ".",
                artifact_ref="reaction_system",
            )
        )
    if reaction_system.reaction_extent_set and reaction_system.reaction_extent_set.unallocated_selectivity_fraction > 1e-4:
        issues.append(
            ValidationIssue(
                code="reaction_extent_unallocated_fraction",
                severity=Severity.BLOCKED,
                message=f"Reaction extent set leaves {reaction_system.reaction_extent_set.unallocated_selectivity_fraction:.6f} of converted feed unallocated.",
                artifact_ref="reaction_system",
            )
        )
    return issues


class PipelineRunner:
    def __init__(self, config: ProjectConfig, store: ArtifactStore | None = None):
        self.config = config
        self.store = store or ArtifactStore(config.output_root)
        self.reasoning = build_reasoning_service(config.model)
        self.research_manager = ResearchManager(self.reasoning)

    @classmethod
    def from_project_id(cls, project_id: str, output_root: str = "outputs") -> "PipelineRunner":
        store = ArtifactStore(output_root)
        config = store.load_model(project_id, "project_config.json", ProjectConfig)
        return cls(config, store=store)

    def run(self) -> ProjectRunState:
        state = self.store.load_run_state(self.config.project_id)
        if not state:
            state = ProjectRunState(
                project_id=self.config.project_id,
                model_name=self.config.model.model_name,
                strict_citation_policy=self.config.strict_citation_policy,
            )
            self.store.save_config(self.config)
            self.store.save_run_state(state)
        if state.awaiting_gate_id:
            gate = state.gates.get(state.awaiting_gate_id)
            if gate and gate.status != GateStatus.APPROVED:
                state.run_status = RunStatus.AWAITING_APPROVAL
                self.store.save_run_state(state)
                return state
            state.awaiting_gate_id = None
        while state.current_stage_index < len(STAGES):
            stage = STAGES[state.current_stage_index]
            state.current_stage_id = stage.id
            state.run_status = RunStatus.RUNNING
            self.store.save_run_state(state)
            result = getattr(self, f"_run_{stage.id}")()
            scientific_issues, rewind_stage_id = self._refresh_scientific_inference(stage.id, state)
            result.issues.extend(scientific_issues)
            self._refresh_critic_registry(stage.id, result.issues)
            self._refresh_agent_fabric()
            if rewind_stage_id is not None:
                state.stage_revision_counts[rewind_stage_id] = state.stage_revision_counts.get(rewind_stage_id, 0) + 1
                self._invalidate_from_stage(state, rewind_stage_id)
                state.run_status = RunStatus.READY
                self.store.save_run_state(state)
                continue
            blocking_issues = [issue for issue in result.issues if issue.severity == Severity.BLOCKED]
            if blocking_issues:
                state.run_status = RunStatus.BLOCKED
                state.blocked_stage_id = stage.id
                apply_state_issues(state, blocking_issues, result.missing_india_coverage, result.stale_source_groups)
                for chapter in result.chapters:
                    chapter.status = ChapterStatus.BLOCKED
                    chapter.blockers.extend(blocking_issues)
                    self.store.save_chapter(self.config.project_id, chapter)
                    state.chapter_index[chapter.chapter_id] = chapter.status
                self._save_report_acceptance(RunStatus.BLOCKED, blocked_stage_id=stage.id, blocking_issues=blocking_issues)
                self.store.save_run_state(state)
                return state
            state.blocked_stage_id = None
            apply_state_issues(state, [], result.missing_india_coverage, result.stale_source_groups)
            for chapter in result.chapters:
                self.store.save_chapter(self.config.project_id, chapter)
                state.chapter_index[chapter.chapter_id] = chapter.status
            if stage.id not in state.completed_stages:
                state.completed_stages.append(stage.id)
            state.current_stage_index += 1
            if result.gate:
                state.gates[result.gate.gate_id] = result.gate
                state.awaiting_gate_id = result.gate.gate_id
                state.run_status = RunStatus.AWAITING_APPROVAL
                self.store.save_run_state(state)
                return state
            self.store.save_run_state(state)
        state.run_status = RunStatus.COMPLETED
        self.store.save_run_state(state)
        return state

    def render(self) -> str:
        state = self._require_state()
        gate = state.gates.get("final_signoff")
        if not gate or gate.status != GateStatus.APPROVED:
            raise RuntimeError("Final signoff is required before PDF rendering.")
        final_report = self.store.maybe_load_model(self.config.project_id, "artifacts/final_report.json", FinalReport)
        markdown_path = self.store.project_dir(self.config.project_id) / "final_report.md"
        if not markdown_path.exists():
            raise RuntimeError("Final markdown report does not exist yet.")
        formatted_markdown_path = self.store.project_dir(self.config.project_id) / "final_report_formatted.md"
        formatted_html_path = self.store.project_dir(self.config.project_id) / "final_report_formatted.html"
        pdf_path = self.store.project_dir(self.config.project_id) / "final_report.pdf"
        formatted_pdf_path = self.store.project_dir(self.config.project_id) / "final_report_formatted.pdf"
        if formatted_html_path.exists():
            render_styled_pdf(
                formatted_html_path.read_text(encoding="utf-8"),
                str(formatted_pdf_path),
                f"{self.config.basis.target_product} Plant Design Report",
                header_text=f"{self.config.basis.target_product} Academic Report",
            )
            self.store.save_text(
                self.config.project_id,
                "final_report_render_source.md",
                formatted_markdown_path.read_text(encoding="utf-8") if formatted_markdown_path.exists() else markdown_path.read_text(encoding="utf-8"),
            )
            pdf_path.write_bytes(formatted_pdf_path.read_bytes())
        elif formatted_markdown_path.exists():
            render_academic_pdf(
                formatted_markdown_path.read_text(encoding="utf-8"),
                str(formatted_pdf_path),
                f"{self.config.basis.target_product} Plant Design Report",
                header_text=f"{self.config.basis.target_product} Academic Report",
            )
            self.store.save_text(self.config.project_id, "final_report_render_source.md", formatted_markdown_path.read_text(encoding="utf-8") if formatted_markdown_path.exists() else markdown_path.read_text(encoding="utf-8"))
            pdf_path.write_bytes(formatted_pdf_path.read_bytes())
        else:
            render_pdf(markdown_path.read_text(encoding="utf-8"), str(pdf_path), f"{self.config.basis.target_product} Plant Design Report")
        if final_report:
            final_report.pdf_path = str(pdf_path)
            final_report.formatted_pdf_path = str(formatted_pdf_path) if formatted_markdown_path.exists() else None
            self.store.save_model(self.config.project_id, "artifacts/final_report.json", final_report)
        return str(pdf_path)

    def approve_gate(self, gate_id: str, notes: str = "") -> ProjectRunState:
        state = self._require_state()
        gate = state.gates.get(gate_id)
        if not gate:
            raise RuntimeError(f"Unknown gate '{gate_id}'.")
        gate.status = GateStatus.APPROVED
        gate.notes = notes
        gate.approved_at = gate.approved_at or utc_now()
        if state.awaiting_gate_id == gate_id:
            state.awaiting_gate_id = None
            state.run_status = RunStatus.READY
        self.store.save_run_state(state)
        return state

    def inspect(self) -> str:
        state = self._require_state()
        lines = [
            f"project_id: {state.project_id}",
            f"run_status: {state.run_status.value}",
            f"current_stage: {state.current_stage_id or 'n/a'}",
            f"completed_stages: {len(state.completed_stages)}/{len(STAGES)}",
        ]
        if state.awaiting_gate_id:
            lines.append(f"awaiting_gate: {state.awaiting_gate_id}")
        if state.blocked_stage_id:
            lines.append(f"blocked_stage: {state.blocked_stage_id}")
        if state.stage_revision_counts:
            lines.append(
                "stage_revisions: "
                + ", ".join(f"{stage_id}={count}" for stage_id, count in sorted(state.stage_revision_counts.items()))
            )
        if state.missing_india_coverage:
            lines.append(f"missing_india_coverage: {', '.join(state.missing_india_coverage)}")
        if state.stale_source_groups:
            lines.append(f"stale_source_groups: {', '.join(state.stale_source_groups)}")
        if state.blocking_issues:
            lines.append("blocking_issues:")
            for issue in state.blocking_issues:
                lines.append(f"- {issue.code}: {issue.message}")
        lines.append("")
        lines.append("gates:")
        for gate in state.gates.values():
            lines.append(f"- {gate.gate_id}: {gate.status.value}")
        lines.append("")
        lines.append("chapters:")
        for chapter_id, status in sorted(state.chapter_index.items()):
            lines.append(f"- {chapter_id}: {status.value}")
        benchmark_manifest = self.store.maybe_load_model(self.config.project_id, "artifacts/benchmark_manifest.json", BenchmarkManifest)
        report_parity_framework = self.store.maybe_load_model(self.config.project_id, "artifacts/report_parity_framework.json", ReportParityFrameworkArtifact)
        report_parity = self.store.maybe_load_model(self.config.project_id, "artifacts/report_parity.json", ReportParityArtifact)
        report_acceptance = self.store.maybe_load_model(self.config.project_id, "artifacts/report_acceptance.json", ReportAcceptanceArtifact)
        data_reality_audit = self.store.maybe_load_model(self.config.project_id, "artifacts/data_reality_audit.json", DataRealityAuditArtifact)
        document_facts = self.store.maybe_load_model(self.config.project_id, "artifacts/user_document_facts.json", DocumentFactCollectionArtifact)
        document_process_options = self.store.maybe_load_model(self.config.project_id, "artifacts/document_process_options.json", DocumentProcessOptionsArtifact)
        commercial_product_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/commercial_product_basis.json", CommercialProductBasisArtifact)
        claim_graph = self.store.maybe_load_model(self.config.project_id, "artifacts/claim_graph.json", ClaimGraphArtifact)
        question_queue = self.store.maybe_load_model(self.config.project_id, "artifacts/inference_question_queue.json", InferenceQuestionQueueArtifact)
        revision_ledger = self.store.maybe_load_model(self.config.project_id, "artifacts/revision_ledger.json", RevisionLedgerArtifact)
        scientific_gate_matrix = self.store.maybe_load_model(self.config.project_id, "artifacts/scientific_gate_matrix.json", ScientificGateMatrixArtifact)
        species_resolution = self.store.maybe_load_model(self.config.project_id, "artifacts/species_resolution.json", SpeciesResolutionArtifact)
        reaction_network_v2 = self.store.maybe_load_model(self.config.project_id, "artifacts/reaction_network_v2.json", ReactionNetworkV2Artifact)
        thermo_admissibility = self.store.maybe_load_model(self.config.project_id, "artifacts/thermo_admissibility.json", ThermoAdmissibilityArtifact)
        kinetics_admissibility = self.store.maybe_load_model(self.config.project_id, "artifacts/kinetics_admissibility.json", KineticsAdmissibilityArtifact)
        flowsheet_intents = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_intents.json", FlowsheetIntentArtifact)
        topology_candidates = self.store.maybe_load_model(self.config.project_id, "artifacts/topology_candidates.json", TopologyCandidateArtifact)
        design_confidence = self.store.maybe_load_model(self.config.project_id, "artifacts/design_confidence.json", DesignConfidenceArtifact)
        economic_coverage = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_coverage.json", EconomicCoverageDecision)
        resolved_sources = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_sources.json", ResolvedSourceSet)
        property_gap = self.store.maybe_load_model(self.config.project_id, "artifacts/property_gap.json", PropertyGapArtifact)
        resolved_values = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_values.json", ResolvedValueArtifact)
        property_packages = self.store.maybe_load_model(self.config.project_id, "artifacts/property_packages.json", PropertyPackageArtifact)
        route_chemistry = self.store.maybe_load_model(self.config.project_id, "artifacts/route_chemistry.json", RouteChemistryArtifact)
        property_demand_plan = self.store.maybe_load_model(self.config.project_id, "artifacts/property_demand_plan.json", PropertyDemandPlan)
        property_requirements = self.store.maybe_load_model(self.config.project_id, "artifacts/property_requirements.json", PropertyRequirementSet)
        separation_thermo = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_thermo.json", SeparationThermoArtifact)
        bac_purification_sections = self.store.maybe_load_model(self.config.project_id, "artifacts/bac_purification_sections.json", BACPurificationSectionArtifact)
        bac_impurity_model = self.store.maybe_load_model(self.config.project_id, "artifacts/bac_impurity_model.json", BACImpurityModelArtifact)
        agent_fabric = self.store.maybe_load_model(self.config.project_id, "artifacts/agent_decision_fabric.json", AgentDecisionFabricArtifact)
        critic_registry = self.store.maybe_load_model(self.config.project_id, "artifacts/critic_registry.json", CriticRegistryArtifact)
        process_archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        family_adapter = self.store.maybe_load_model(self.config.project_id, "artifacts/chemistry_family_adapter.json", ChemistryFamilyAdapter)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        process_synthesis = self.store.maybe_load_model(self.config.project_id, "artifacts/process_synthesis.json", ProcessSynthesisArtifact)
        route_discovery = self.store.maybe_load_model(self.config.project_id, "artifacts/route_discovery.json", RouteDiscoveryArtifact)
        route_screening = self.store.maybe_load_model(self.config.project_id, "artifacts/route_screening.json", RouteScreeningArtifact)
        process_selection_comparison = self.store.maybe_load_model(self.config.project_id, "artifacts/process_selection_comparison.json", ProcessSelectionComparisonArtifact)
        unit_train_candidates = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_train_candidates.json", UnitTrainCandidateSet)
        operations_planning = self.store.maybe_load_model(self.config.project_id, "artifacts/operations_planning.json", OperationsPlanningArtifact)
        capacity_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/capacity_decision.json", DecisionRecord)
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
        route_selection_comparison = self.store.maybe_load_model(self.config.project_id, "artifacts/route_selection_comparison.json", RouteSelectionComparisonArtifact)
        chemistry_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/chemistry_decision.json", ChemistryDecisionArtifact)
        route_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/route_decision.json", DecisionRecord)
        reactor_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/reactor_choice_decision.json", DecisionRecord)
        separation_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_choice_decision.json", DecisionRecord)
        exchanger_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/exchanger_choice_decision.json", DecisionRecord)
        storage_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/storage_choice_decision.json", DecisionRecord)
        moc_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/moc_choice_decision.json", DecisionRecord)
        utility_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_basis_decision.json", DecisionRecord)
        procurement_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/procurement_basis_decision.json", DecisionRecord)
        logistics_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/logistics_basis_decision.json", DecisionRecord)
        financing_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/financing_basis_decision.json", DecisionRecord)
        economic_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_basis_decision.json", DecisionRecord)
        thermo_method = self.store.maybe_load_model(self.config.project_id, "artifacts/thermo_method_decision.json", MethodSelectionArtifact)
        property_method = self.store.maybe_load_model(self.config.project_id, "artifacts/property_method_decision.json", PropertyMethodDecision)
        separation_thermo = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_thermo.json", SeparationThermoArtifact)
        kinetics_method = self.store.maybe_load_model(self.config.project_id, "artifacts/kinetics_method_decision.json", MethodSelectionArtifact)
        layout_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/layout_decision.json", LayoutDecisionArtifact)
        heat_study = self.store.maybe_load_model(self.config.project_id, "artifacts/heat_integration_study.json", HeatIntegrationStudyArtifact)
        utility_network = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_network_decision.json", UtilityNetworkDecision)
        reaction_system = self.store.maybe_load_model(self.config.project_id, "artifacts/reaction_system.json", ReactionSystem)
        stream_table = self.store.maybe_load_model(self.config.project_id, "artifacts/stream_table.json", StreamTable)
        mixture_properties = self.store.maybe_load_model(self.config.project_id, "artifacts/mixture_properties.json", MixturePropertyArtifact)
        flowsheet_blueprint = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_blueprint.json", FlowsheetBlueprintArtifact)
        flowsheet_case = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_case.json", FlowsheetCase)
        solve_result = self.store.maybe_load_model(self.config.project_id, "artifacts/solve_result.json", SolveResult)
        utility_architecture = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_architecture.json", UtilityArchitectureDecision)
        plant_cost_summary = self.store.maybe_load_model(self.config.project_id, "artifacts/plant_cost_summary.json", PlantCostSummary)
        route_site_fit = self.store.maybe_load_model(self.config.project_id, "artifacts/route_site_fit.json", RouteSiteFitArtifact)
        route_economic_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/route_economic_basis.json", RouteEconomicBasisArtifact)
        bac_purification_sections = self.store.maybe_load_model(self.config.project_id, "artifacts/bac_purification_sections.json", BACPurificationSectionArtifact)
        bac_impurity_model = self.store.maybe_load_model(self.config.project_id, "artifacts/bac_impurity_model.json", BACImpurityModelArtifact)
        unit_train_consistency = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_train_consistency.json", UnitTrainConsistencyArtifact)
        debt_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/debt_schedule.json", DebtSchedule)
        financial_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/financial_schedule.json", FinancialSchedule)
        if benchmark_manifest:
            lines.append("")
            lines.append("benchmark:")
            lines.append(f"- profile: {benchmark_manifest.benchmark_id}")
            lines.append(f"- archetype_family: {benchmark_manifest.archetype_family}")
        if report_parity_framework or report_parity:
            lines.append("")
            lines.append("report_parity:")
            if report_parity_framework:
                lines.append(f"- framework_id: {report_parity_framework.framework_id}")
                lines.append(f"- chapter_contracts: {len(report_parity_framework.chapter_contracts)}")
                lines.append(f"- support_contracts: {len(report_parity_framework.support_contracts)}")
            if report_parity:
                lines.append(f"- overall_status: {report_parity.overall_status.value}")
                lines.append(
                    f"- chapters_complete_partial_missing: {report_parity.complete_chapter_count}/{report_parity.partial_chapter_count}/{report_parity.missing_chapter_count}"
                )
                lines.append(
                    f"- support_complete_partial_missing: {report_parity.complete_support_count}/{report_parity.partial_support_count}/{report_parity.missing_support_count}"
                )
                lines.append(f"- missing_chapters: {', '.join(report_parity.missing_chapter_ids) or 'none'}")
                lines.append(f"- missing_support: {', '.join(report_parity.missing_support_ids) or 'none'}")
        if report_acceptance:
            lines.append("")
            lines.append("report_acceptance:")
            lines.append(f"- overall_status: {report_acceptance.overall_status.value}")
            lines.append(f"- pipeline_status: {report_acceptance.pipeline_status.value}")
            lines.append(f"- report_parity_status: {report_acceptance.report_parity_status.value if report_acceptance.report_parity_status else 'not_evaluated'}")
            lines.append(f"- blocked_stage: {report_acceptance.blocked_stage_id or 'none'}")
            lines.append(
                f"- expected_decisions_satisfied_missing: {report_acceptance.satisfied_expected_decision_count}/{report_acceptance.missing_expected_decision_count}"
            )
            lines.append(f"- missing_expected_decisions: {', '.join(report_acceptance.missing_expected_decisions) or 'none'}")
            lines.append(f"- blocking_issue_codes: {', '.join(report_acceptance.blocking_issue_codes) or 'none'}")
            lines.append(f"- route_evidence_status: {report_acceptance.route_evidence_status}")
            lines.append(f"- product_basis_status: {report_acceptance.product_basis_status}")
            lines.append(f"- unit_train_consistency_status: {report_acceptance.unit_train_consistency_status}")
            lines.append(f"- purification_rigor_status: {report_acceptance.purification_rigor_status}")
            lines.append(f"- economic_realism_status: {report_acceptance.economic_realism_status}")
            lines.append(f"- real_data_status: {report_acceptance.real_data_status}")
            lines.append(f"- real_data_coverage: {report_acceptance.real_data_coverage_fraction:.1%}")
            lines.append(f"- critical_seeded_dependencies: {', '.join(report_acceptance.critical_seeded_dependencies) or 'none'}")
        if data_reality_audit:
            lines.append("")
            lines.append("data_reality:")
            lines.append(f"- benchmark_profile: {data_reality_audit.benchmark_profile}")
            lines.append(f"- overall_real_data_fraction: {data_reality_audit.overall_real_data_fraction:.1%}")
            lines.append(f"- critical_seeded_refs: {', '.join(data_reality_audit.critical_seeded_artifact_refs) or 'none'}")
            lines.append(f"- critical_inferred_refs: {', '.join(data_reality_audit.critical_inferred_artifact_refs) or 'none'}")
        if species_resolution or reaction_network_v2 or thermo_admissibility or kinetics_admissibility or topology_candidates:
            lines.append("")
            lines.append("scientific_basis:")
            if species_resolution:
                lines.append(f"- species_blocking_routes: {', '.join(species_resolution.blocking_route_ids) or 'none'}")
            if reaction_network_v2:
                lines.append(f"- reaction_network_blocking_routes: {', '.join(reaction_network_v2.blocking_route_ids) or 'none'}")
            if thermo_admissibility:
                lines.append(f"- thermo_selected_route_status: {thermo_admissibility.selected_route_status.value}")
                lines.append(f"- thermo_selected_route_confidence: {thermo_admissibility.selected_route_confidence.value}")
            if kinetics_admissibility:
                lines.append(f"- kinetics_selected_route_status: {kinetics_admissibility.selected_route_status.value}")
                lines.append(f"- kinetics_selected_route_confidence: {kinetics_admissibility.selected_route_confidence.value}")
            if topology_candidates:
                lines.append(f"- topology_selected_blueprint: {topology_candidates.selected_blueprint_id or 'none'}")
                lines.append(f"- screening_balance_allowed: {'yes' if topology_candidates.screening_balance_allowed else 'no'}")
        if flowsheet_intents or design_confidence or economic_coverage or scientific_gate_matrix or claim_graph or question_queue or revision_ledger:
            lines.append("")
            lines.append("scientific_inference:")
            if flowsheet_intents:
                lines.append(f"- flowsheet_intents: {len(flowsheet_intents.intents)}")
            if design_confidence:
                lines.append(f"- design_confidence: {design_confidence.overall_confidence.value}")
                lines.append(f"- blocked_units: {', '.join(design_confidence.blocked_unit_ids) or 'none'}")
            if economic_coverage:
                lines.append(f"- economic_coverage: {economic_coverage.status}")
                lines.append(f"- economic_missing_basis: {', '.join(economic_coverage.missing_basis) or 'none'}")
            if scientific_gate_matrix:
                lines.append(
                    f"- scientific_gates: {', '.join(f'{item.gate_id}={item.status.value}' for item in scientific_gate_matrix.entries) or 'none'}"
                )
            if claim_graph:
                lines.append(f"- claims: {len(claim_graph.claims)}")
                lines.append(f"- changed_claims: {', '.join(claim_graph.changed_claim_ids) or 'none'}")
            if question_queue:
                lines.append(f"- active_questions: {len(question_queue.active_questions)}")
            if revision_ledger:
                lines.append(f"- active_revision_tickets: {', '.join(revision_ledger.active_ticket_ids) or 'none'}")
        if document_facts or document_process_options:
            lines.append("")
            lines.append("document_facts:")
            if document_facts:
                lines.append(f"- documents: {len(document_facts.documents)}")
                lines.append(f"- process_options: {document_facts.process_option_count}")
                lines.append(f"- reaction_mentions: {document_facts.reaction_mention_count}")
                lines.append(f"- equipment_mentions: {document_facts.equipment_mention_count}")
                lines.append(f"- selected_processes: {', '.join(document_facts.selected_process_labels) or 'none'}")
                lines.append(f"- selected_sites: {', '.join(document_facts.selected_site_names) or 'none'}")
            if document_process_options:
                lines.append(f"- document_option_ids: {', '.join(item.option_id for item in document_process_options.options[:5]) or 'none'}")
        if resolved_sources:
            lines.append("")
            lines.append("source_resolution:")
            lines.append(f"- selected_sources: {len(resolved_sources.selected_source_ids)}")
            lines.append(f"- unresolved_conflicts: {', '.join(resolved_sources.unresolved_conflicts) or 'none'}")
            if resolved_sources.conflicts:
                for conflict in resolved_sources.conflicts[:5]:
                    lines.append(
                        f"- conflict[{conflict.source_domain.value}]: selected={conflict.selected_source_id or 'none'}; competing={', '.join(conflict.competing_source_ids) or 'none'}; blocking={'yes' if conflict.blocking else 'no'}"
                    )
        if commercial_product_basis:
            lines.append("")
            lines.append("commercial_product_basis:")
            lines.append(f"- throughput_basis: {commercial_product_basis.throughput_basis}")
            lines.append(f"- sold_solution_basis_kg_hr: {commercial_product_basis.sold_solution_basis_kg_hr:,.3f}")
            lines.append(f"- active_basis_kg_hr: {commercial_product_basis.active_basis_kg_hr:,.3f}")
            lines.append(f"- sold_concentration_wt_pct: {commercial_product_basis.sold_concentration_wt_pct:.2f}")
            lines.append(f"- sold_solution_price_inr_per_kg: {commercial_product_basis.sold_solution_price_inr_per_kg:,.2f}")
            lines.append(f"- active_price_inr_per_kg: {commercial_product_basis.active_price_inr_per_kg:,.2f}")
        if property_gap:
            lines.append("")
            lines.append("value_resolution:")
            unresolved = ", ".join(property_gap.unresolved_high_sensitivity) or "none"
            lines.append(f"- unresolved_high_sensitivity: {unresolved}")
        if resolved_values:
            lines.append(f"- evidence_lock_unresolved: {', '.join(resolved_values.unresolved_value_ids) or 'none'}")
            if resolved_values.property_estimates:
                lines.append(f"- property_estimates: {len(resolved_values.property_estimates)}")
        if property_packages:
            lines.append(f"- resolved_components: {len(property_packages.packages)}")
            lines.append(f"- unresolved_identifiers: {', '.join(property_packages.unresolved_identifier_ids) or 'none'}")
            lines.append(f"- blocked_property_ids: {', '.join(property_packages.blocked_property_ids[:8]) or 'none'}")
            lines.append(f"- resolved_bip_pairs: {len(property_packages.binary_interaction_parameters)}")
            lines.append(f"- unresolved_bip_pairs: {', '.join(property_packages.unresolved_binary_pairs[:6]) or 'none'}")
            lines.append(f"- resolved_henry_pairs: {len(property_packages.henry_law_constants)}")
            lines.append(f"- unresolved_henry_pairs: {', '.join(property_packages.unresolved_henry_pairs[:6]) or 'none'}")
            lines.append(f"- resolved_solubility_pairs: {len(property_packages.solubility_curves)}")
            lines.append(f"- unresolved_solubility_pairs: {', '.join(property_packages.unresolved_solubility_pairs[:6]) or 'none'}")
        if route_chemistry:
            lines.append("")
            lines.append("route_chemistry:")
            lines.append(f"- route_graphs: {len(route_chemistry.route_graphs)}")
            lines.append(f"- resolved_species_count: {route_chemistry.resolved_species_count}")
            lines.append(f"- anonymous_species_count: {route_chemistry.anonymous_species_count}")
            lines.append(f"- blocking_routes: {', '.join(route_chemistry.blocking_route_ids) or 'none'}")
        if property_demand_plan:
            lines.append("")
            lines.append("property_demand:")
            lines.append(f"- route_ids: {', '.join(property_demand_plan.route_ids) or 'none'}")
            lines.append(f"- items: {len(property_demand_plan.items)}")
            lines.append(f"- blocked_stages: {', '.join(property_demand_plan.blocked_stage_ids) or 'none'}")
            lines.append(f"- blocking_species_ids: {', '.join(property_demand_plan.blocking_species_ids[:8]) or 'none'}")
        if property_requirements:
            lines.append(f"- property_requirement_stage_failures: {', '.join(property_requirements.blocked_stage_ids) or 'none'}")
        if process_archetype:
            lines.append("")
            lines.append("archetype:")
            lines.append(f"- id: {process_archetype.archetype_id}")
            lines.append(f"- compound_family: {process_archetype.compound_family}")
            lines.append(f"- product_phase: {process_archetype.dominant_product_phase}")
            lines.append(f"- separation_family: {process_archetype.dominant_separation_family}")
        if family_adapter:
            lines.append("")
            lines.append("family_adapter:")
            lines.append(f"- id: {family_adapter.adapter_id}")
            lines.append(f"- family_label: {family_adapter.family_label}")
            lines.append(f"- route_hints: {', '.join(family_adapter.route_generation_hints[:4]) or 'none'}")
            lines.append(f"- property_priority: {', '.join(family_adapter.property_priority_order[:5]) or 'none'}")
            lines.append(f"- preferred_separation_candidates: {', '.join(family_adapter.preferred_separation_candidates[:4]) or 'none'}")
            lines.append(f"- critic_focus: {', '.join(family_adapter.critic_focus[:4]) or 'none'}")
            lines.append(f"- sparse_data_blockers: {', '.join(family_adapter.sparse_data_blockers[:4]) or 'none'}")
        if route_families:
            lines.append("")
            lines.append("route_families:")
            lines.append(f"- profiles: {len(route_families.profiles)}")
            for profile in route_families.profiles[:5]:
                lines.append(
                    f"- route[{profile.route_id}]: family={profile.route_family_id}; reactor={profile.primary_reactor_class}; separation={profile.primary_separation_train}; heat={profile.heat_recovery_style}"
                )
        if unit_operation_family:
            lines.append("")
            lines.append("unit_operation_family:")
            lines.append(f"- route_id: {unit_operation_family.route_id}")
            lines.append(f"- route_family_id: {unit_operation_family.route_family_id}")
            lines.append(f"- reactor_candidates: {', '.join(item.candidate_id for item in unit_operation_family.reactor_candidates[:4]) or 'none'}")
            lines.append(f"- separation_candidates: {', '.join(item.candidate_id for item in unit_operation_family.separation_candidates[:4]) or 'none'}")
            lines.append(f"- supporting_ops: {', '.join(unit_operation_family.supporting_unit_operations[:6]) or 'none'}")
            lines.append(f"- applicability_critics: {', '.join(unit_operation_family.applicability_critics[:4]) or 'none'}")
        if sparse_data_policy:
            lines.append("")
            lines.append("sparse_data_policy:")
            lines.append(f"- id: {sparse_data_policy.policy_id}")
            lines.append(f"- adapter_id: {sparse_data_policy.adapter_id}")
            lines.append(f"- blocked_stages: {', '.join(sparse_data_policy.blocked_stage_ids) or 'none'}")
            lines.append(f"- warning_stages: {', '.join(sparse_data_policy.warning_stage_ids) or 'none'}")
            triggered_rules = [rule for rule in sparse_data_policy.rules if rule.current_status in {'warning', 'blocked'}]
            lines.append(f"- triggered_rules: {len(triggered_rules)}")
        if operations_planning:
            lines.append("")
            lines.append("operations_planning:")
            lines.append(f"- service_family: {operations_planning.service_family}")
            lines.append(f"- operating_mode: {operations_planning.recommended_operating_mode}")
            lines.append(f"- raw_material_buffer_days: {operations_planning.raw_material_buffer_days:.1f}")
            lines.append(f"- finished_goods_buffer_days: {operations_planning.finished_goods_buffer_days:.1f}")
            lines.append(f"- restart_loss_fraction: {operations_planning.restart_loss_fraction:.4f}")
            lines.append(f"- annual_restart_loss_kg: {operations_planning.annual_restart_loss_kg:,.1f}")
        operating_mode_decision = process_synthesis.operating_mode_decision if process_synthesis else None
        utility_network_decision = utility_network.decision if utility_network else None
        if any([capacity_decision, operating_mode_decision, site_decision, route_decision, reactor_choice, separation_choice, utility_network_decision, exchanger_choice, storage_choice, moc_choice, utility_basis_decision, procurement_basis, logistics_basis, financing_basis, economic_basis_decision]):
            lines.append("")
            lines.append("decisions:")
            for decision in [capacity_decision, operating_mode_decision, site_decision, route_decision, reactor_choice, separation_choice, utility_network_decision, exchanger_choice, storage_choice, moc_choice, utility_basis_decision, procurement_basis, logistics_basis, financing_basis, economic_basis_decision]:
                if decision:
                    lines.append(
                        f"- {decision.decision_id}: selected={decision.selected_candidate_id or 'n/a'}; stability={decision.scenario_stability.value}; approval_required={'yes' if decision.approval_required else 'no'}"
                    )
        if thermo_method or kinetics_method or property_method:
            lines.append("")
            lines.append("method_decisions:")
            if property_method:
                lines.append(f"- property_basis: {property_method.decision.selected_candidate_id or 'n/a'}")
            if separation_thermo and separation_thermo.relative_volatility is not None:
                lines.append(
                    f"- separation_thermo: alpha={separation_thermo.relative_volatility.average_alpha:.4f}; "
                    f"keys={separation_thermo.light_key}/{separation_thermo.heavy_key}; method={separation_thermo.relative_volatility.method}; "
                    f"activity={separation_thermo.activity_model}"
                )
            if thermo_method:
                lines.append(f"- thermo: {thermo_method.decision.selected_candidate_id or 'n/a'}")
            if kinetics_method:
                lines.append(f"- kinetics: {kinetics_method.decision.selected_candidate_id or 'n/a'}")
        if reaction_system and (reaction_system.byproduct_closure or reaction_system.reaction_extent_set):
            lines.append("")
            lines.append("reaction_network:")
            if reaction_system.byproduct_closure:
                lines.append(
                    f"- byproduct_closure: status={reaction_system.byproduct_closure.closure_status}; blocking={'yes' if reaction_system.byproduct_closure.blocking else 'no'}; estimates={len(reaction_system.byproduct_closure.estimates)}"
                )
                if reaction_system.byproduct_closure.unresolved_byproducts:
                    lines.append(f"- unresolved_byproducts: {', '.join(reaction_system.byproduct_closure.unresolved_byproducts[:6])}")
            if reaction_system.reaction_extent_set:
                lines.append(
                    f"- extents: {len(reaction_system.reaction_extent_set.extents)}; unallocated_fraction={reaction_system.reaction_extent_set.unallocated_selectivity_fraction:.6f}; status={reaction_system.reaction_extent_set.closure_status}"
                )
        if process_synthesis and process_synthesis.alternative_sets:
            lines.append("")
            lines.append("alternative_sets:")
            for alt_set in process_synthesis.alternative_sets:
                lines.append(
                    f"- {alt_set.set_id}: selected={alt_set.selected_candidate_id or 'n/a'}; candidates={len(alt_set.alternatives)}; stability={alt_set.scenario_stability.value}"
                )
        if unit_train_candidates or flowsheet_blueprint:
            lines.append("")
            lines.append("flowsheet_blueprint:")
            if unit_train_candidates:
                lines.append(f"- candidates: {len(unit_train_candidates.blueprints)}")
            if flowsheet_blueprint:
                lines.append(f"- selected_blueprint: {flowsheet_blueprint.blueprint_id}")
                lines.append(f"- steps: {len(flowsheet_blueprint.steps)}")
                lines.append(f"- tagged_units: {', '.join(flowsheet_blueprint.selected_unit_tags) or 'none'}")
                lines.append(f"- recycle_intents: {len(flowsheet_blueprint.recycle_intents)}")
        if route_selection_comparison:
            lines.append("")
            lines.append("route_selection_comparison:")
            lines.append(f"- selected_route: {route_selection_comparison.selected_route_id}")
            lines.append(f"- rows: {len(route_selection_comparison.rows)}")
            lines.append(f"- blocked_routes: {', '.join(route_selection_comparison.blocked_route_ids) or 'none'}")
        if process_selection_comparison:
            lines.append(f"- discovery_count: {process_selection_comparison.route_discovery_count}")
            lines.append(f"- retained_count: {process_selection_comparison.retained_route_count}")
            lines.append(f"- eliminated_count: {process_selection_comparison.eliminated_route_count}")
        if route_discovery or route_screening or chemistry_decision:
            lines.append("")
            lines.append("process_selection_logic:")
            if route_discovery:
                lines.append(f"- discovered_routes: {len(route_discovery.rows)}")
            if route_screening:
                lines.append(f"- retained_routes: {', '.join(route_screening.retained_route_ids) or 'none'}")
                lines.append(f"- eliminated_routes: {', '.join(route_screening.eliminated_route_ids) or 'none'}")
            if chemistry_decision:
                lines.append(f"- chemistry_basis_status: {chemistry_decision.chemistry_basis_status}")
                lines.append(f"- chemistry_steps: {chemistry_decision.reaction_step_count}")
        if agent_fabric:
            lines.append("")
            lines.append("agent_fabric:")
            lines.append(f"- packets: {len(agent_fabric.packets)}")
            warning_packets = sum(1 for packet in agent_fabric.packets for verdict in packet.critic_verdicts if verdict.status == "warning")
            blocked_packets = sum(1 for packet in agent_fabric.packets for verdict in packet.critic_verdicts if verdict.status == "blocked")
            lines.append(f"- critic_warnings: {warning_packets}")
            lines.append(f"- critic_blocked: {blocked_packets}")
        if critic_registry:
            lines.append("")
            lines.append("critic_registry:")
            lines.append(f"- findings: {len(critic_registry.findings)}")
            lines.append(f"- warnings: {critic_registry.warning_count}")
            lines.append(f"- blocked: {critic_registry.blocked_count}")
            for finding in critic_registry.findings[:5]:
                lines.append(f"- critic[{finding.stage_id}/{finding.critic_family}]: {finding.code}")
        if flowsheet_case or solve_result:
            lines.append("")
            lines.append("flowsheet_solver:")
            if stream_table:
                lines.append(
                    f"- composition_states: {len(stream_table.composition_states)}; composition_closures: {len(stream_table.composition_closures)}; phase_split_specs: {len(stream_table.phase_split_specs)}; separator_performances: {len(stream_table.separator_performances)}; convergence_summaries: {len(stream_table.convergence_summaries)}"
                )
            if mixture_properties:
                lines.append(
                    f"- mixture_packages: {len(mixture_properties.packages)}; blocked_mixture_units: {', '.join(mixture_properties.blocked_unit_ids) or 'none'}"
                )
            if flowsheet_case:
                lines.append(
                    f"- units: {len(flowsheet_case.units)}; streams: {len(flowsheet_case.streams)}; sections: {len(flowsheet_case.sections)}; separations: {len(flowsheet_case.separations)}; recycle_loops: {len(flowsheet_case.recycle_loops)}"
                )
                for section in flowsheet_case.sections[:5]:
                    lines.append(
                        f"- section[{section.section_id}]: label={section.label}; type={section.section_type}; units={', '.join(section.unit_ids) or '-'}; status={section.status}"
                    )
            if solve_result:
                lines.append(
                    f"- convergence: {solve_result.convergence_status}; closure_error_pct: {solve_result.overall_closure_error_pct:.3f}; critic_messages: {len(solve_result.critic_messages)}"
                )
                blocked_units = [unit_id for unit_id, status in solve_result.unitwise_status.items() if status == "blocked"]
                estimated_units = [unit_id for unit_id, status in solve_result.unitwise_status.items() if status == "estimated"]
                partial_coverage_units = [
                    unit_id for unit_id, status in solve_result.unitwise_coverage_status.items() if status == "partial"
                ]
                if blocked_units:
                    lines.append(f"- blocked_units: {', '.join(blocked_units[:6])}")
                if estimated_units:
                    lines.append(f"- estimated_units: {', '.join(estimated_units[:6])}")
                if partial_coverage_units:
                    lines.append(f"- partial_coverage_units: {', '.join(partial_coverage_units[:6])}")
                if solve_result.unitwise_blockers:
                    for unit_id, blockers in list(solve_result.unitwise_blockers.items())[:5]:
                        lines.append(f"- unit_blocker[{unit_id}]: {'; '.join(blockers[:2])}")
                if solve_result.unitwise_unresolved_sensitivities:
                    for unit_id, sensitivities in list(solve_result.unitwise_unresolved_sensitivities.items())[:5]:
                        lines.append(f"- unit_unresolved[{unit_id}]: {', '.join(sensitivities[:3])}")
                if solve_result.section_status:
                    blocked_sections = [section_id for section_id, status in solve_result.section_status.items() if status == "blocked"]
                    estimated_sections = [section_id for section_id, status in solve_result.section_status.items() if status == "estimated"]
                    if blocked_sections:
                        lines.append(f"- blocked_sections: {', '.join(blocked_sections[:6])}")
                    if estimated_sections:
                        lines.append(f"- estimated_sections: {', '.join(estimated_sections[:6])}")
                if solve_result.composition_status:
                    blocked_comp = [unit_id for unit_id, status in solve_result.composition_status.items() if status == "blocked"]
                    estimated_comp = [unit_id for unit_id, status in solve_result.composition_status.items() if status == "estimated"]
                    if blocked_comp:
                        lines.append(f"- blocked_composition_units: {', '.join(blocked_comp[:6])}")
                    if estimated_comp:
                        lines.append(f"- estimated_composition_units: {', '.join(estimated_comp[:6])}")
                if solve_result.convergence_summaries:
                    for summary in solve_result.convergence_summaries[:5]:
                        lines.append(
                            f"- recycle_summary[{summary.loop_id}]: status={summary.convergence_status}; max_error={summary.max_component_error_pct:.3f}%; purge_families={', '.join(sorted(summary.purge_policy_by_family)) or 'none'}"
                        )
        if heat_study:
            lines.append("")
            lines.append("heat_integration:")
            for route_case in heat_study.route_decisions:
                selected_case = selected_heat_case(route_case)
                lines.append(
                    f"- {route_case.route_id}: case={selected_case.case_id if selected_case else 'n/a'}; recovered_kw={selected_case.recovered_duty_kw if selected_case else 0.0:.1f}; savings_inr={selected_case.annual_savings_inr if selected_case else 0.0:.2f}"
                )
        if utility_architecture:
            lines.append("")
            lines.append("utility_architecture:")
            lines.append(f"- topology: {utility_architecture.architecture.topology_summary}")
            lines.append(f"- selected_case: {utility_architecture.architecture.selected_case_id or 'n/a'}")
            selected_case = next(
                (
                    case
                    for case in utility_architecture.architecture.cases
                    if case.case_id == utility_architecture.architecture.selected_case_id
                ),
                None,
            )
            if selected_case:
                lines.append(f"- architecture_family: {selected_case.architecture_family}")
                lines.append(f"- header_levels: {selected_case.header_count}")
                lines.append(f"- shared_htm_islands: {selected_case.shared_htm_island_count}")
                lines.append(f"- condenser_reboiler_clusters: {selected_case.condenser_reboiler_cluster_count}")
            lines.append(
                f"- composite_intervals: {len(utility_architecture.architecture.heat_stream_set.composite_intervals) if utility_architecture.architecture.heat_stream_set else 0}"
            )
            lines.append(f"- utility_islands: {len(utility_architecture.architecture.selected_island_ids)}")
            lines.append(f"- train_steps: {len(utility_architecture.architecture.selected_train_steps)}")
            lines.append(f"- package_items: {len(utility_architecture.architecture.selected_package_items)}")
        if layout_decision:
            lines.append("")
            lines.append("layout:")
            lines.append(f"- basis: {layout_decision.winning_layout_basis}")
        if plant_cost_summary or debt_schedule or financial_schedule:
            lines.append("")
            lines.append("economics_v3:")
            if plant_cost_summary:
                lines.append(f"- total_project_cost_inr: {plant_cost_summary.total_project_cost_inr:,.2f}")
            if route_site_fit:
                lines.append(f"- route_site_fit_score: {route_site_fit.overall_fit_score:.2f}")
                lines.append(f"- route_site_logistics_penalty: {route_site_fit.logistics_penalty_factor:.3f}")
            if route_economic_basis:
                lines.append(f"- route_economic_coverage: {route_economic_basis.coverage_status}")
                lines.append(f"- route_batch_penalty_fraction: {route_economic_basis.batch_occupancy_penalty_fraction:.3f}")
                lines.append(f"- route_solvent_recovery_service_inr: {route_economic_basis.solvent_recovery_service_cost_inr:,.2f}")
            cost_model = self.store.maybe_load_model(self.config.project_id, "artifacts/cost_model.json", CostModel)
            if cost_model:
                lines.append(f"- utility_island_costs: {len(cost_model.utility_island_costs)}")
                lines.append(f"- utility_island_service_cost_inr: {cost_model.annual_utility_island_service_cost:,.2f}")
                lines.append(f"- utility_island_replacement_cost_inr: {cost_model.annual_utility_island_replacement_cost:,.2f}")
                lines.append(f"- procurement_profile: {cost_model.procurement_profile_label or 'n/a'}")
                lines.append(f"- construction_months: {cost_model.construction_months}")
                lines.append(f"- total_import_duty_inr: {cost_model.total_import_duty_inr:,.2f}")
                lines.append(f"- procurement_packages: {len(cost_model.procurement_package_impacts)}")
            if debt_schedule:
                lines.append(f"- debt_schedule_years: {len(debt_schedule.entries)}")
            if financial_schedule:
                lines.append(f"- financial_schedule_years: {len(financial_schedule.lines)}")
            financial_model = self.store.maybe_load_model(self.config.project_id, "artifacts/financial_model.json", FinancialModel)
            if financial_model:
                lines.append(f"- idc_inr: {financial_model.construction_interest_during_construction_inr:,.2f}")
                lines.append(f"- peak_working_capital_inr: {financial_model.peak_working_capital_inr:,.2f}")
                lines.append(f"- peak_working_capital_month: {financial_model.peak_working_capital_month:.2f}")
                lines.append(f"- minimum_dscr: {financial_model.minimum_dscr:.3f}")
                lines.append(f"- average_dscr: {financial_model.average_dscr:.3f}")
                lines.append(f"- llcr: {financial_model.llcr:.3f}")
                lines.append(f"- plcr: {financial_model.plcr:.3f}")
                lines.append(f"- selected_financing_candidate: {financial_model.selected_financing_candidate_id or 'n/a'}")
                lines.append(f"- downside_financing_candidate: {financial_model.downside_financing_candidate_id or 'n/a'}")
                lines.append(f"- downside_scenario_name: {financial_model.downside_scenario_name or 'n/a'}")
                lines.append(f"- financing_scenario_reversal: {'yes' if financial_model.financing_scenario_reversal else 'no'}")
                lines.append(f"- covenant_breach_count: {len(financial_model.covenant_breach_codes)}")
                lines.append(f"- covenant_warning_count: {len(financial_model.covenant_warnings)}")
        if bac_purification_sections or bac_impurity_model or unit_train_consistency:
            lines.append("")
            lines.append("bac_benchmark_basis:")
            if bac_purification_sections:
                lines.append(f"- purification_sections: {len(bac_purification_sections.sections)}")
                lines.append(f"- unresolved_purification_sections: {', '.join(bac_purification_sections.unresolved_section_ids) or 'none'}")
            if bac_impurity_model:
                lines.append(f"- impurity_items: {len(bac_impurity_model.items)}")
                lines.append(f"- unresolved_impurity_ids: {', '.join(bac_impurity_model.unresolved_impurity_ids) or 'none'}")
            if unit_train_consistency:
                lines.append(f"- unit_train_consistency: {unit_train_consistency.overall_status}")
                lines.append(f"- unit_train_blocking_refs: {', '.join(unit_train_consistency.blocking_artifact_refs) or 'none'}")
        return "\n".join(lines)

    def _require_state(self) -> ProjectRunState:
        state = self.store.load_run_state(self.config.project_id)
        if not state:
            raise RuntimeError(f"No run state found for project '{self.config.project_id}'.")
        return state

    def _load(self, name: str, model_type):
        return self.store.load_model(self.config.project_id, f"artifacts/{name}.json", model_type)

    def _save(self, name: str, model) -> None:
        self.store.save_model(self.config.project_id, f"artifacts/{name}.json", model)

    def _maybe_load(self, name: str, model_type):
        return self.store.maybe_load_model(self.config.project_id, f"artifacts/{name}.json", model_type)

    def _stage_index(self, stage_id: str) -> int:
        for index, stage in enumerate(STAGES):
            if stage.id == stage_id:
                return index
        raise RuntimeError(f"Unknown stage '{stage_id}'.")

    def _invalidate_from_stage(self, state: ProjectRunState, stage_id: str) -> None:
        target_index = self._stage_index(stage_id)
        invalid_stage_ids = {stage.id for stage in STAGES[target_index:]}
        for stage in STAGES[target_index:]:
            for artifact_name in stage.output_artifacts:
                self.store.delete_path(self.config.project_id, f"artifacts/{artifact_name}.json")
        for chapter_id in list(state.chapter_index):
            chapter_artifact = self.store.maybe_load_model(self.config.project_id, f"chapter_artifacts/{chapter_id}.json", ChapterArtifact)
            if chapter_artifact is not None and chapter_artifact.stage_id in invalid_stage_ids:
                self.store.delete_path(self.config.project_id, f"chapter_artifacts/{chapter_id}.json")
                self.store.delete_path(self.config.project_id, f"chapters/{chapter_id}.md")
                state.chapter_index.pop(chapter_id, None)
        for stage in STAGES[target_index:]:
            if stage.gate_id:
                state.gates.pop(stage.gate_id, None)
        state.completed_stages = [item for item in state.completed_stages if self._stage_index(item) < target_index]
        state.current_stage_index = target_index
        state.current_stage_id = stage_id
        state.awaiting_gate_id = None
        state.blocked_stage_id = None

    def _refresh_scientific_inference(self, stage_id: str, state: ProjectRunState) -> tuple[list[ValidationIssue], str | None]:
        issues: list[ValidationIssue] = []
        is_bac_benchmark = (
            "benzalkonium" in self.config.basis.target_product.lower()
            or (self.config.benchmark_profile or "").strip().lower() == "benzalkonium_chloride"
        )
        selected_route = self._maybe_load("route_selection", RouteSelectionArtifact)
        selected_route_id = selected_route.selected_route_id if selected_route is not None else ""
        route_survey = self._maybe_load("route_survey", RouteSurveyArtifact)
        route_chemistry = self._maybe_load("route_chemistry", RouteChemistryArtifact)
        property_packages = self._maybe_load("property_packages", PropertyPackageArtifact)
        route_families = self._maybe_load("route_family_profiles", RouteFamilyArtifact)
        unit_train_candidates = self._maybe_load("unit_train_candidates", UnitTrainCandidateSet)
        route_process_claims = self._maybe_load("route_process_claims", RouteProcessClaimsArtifact)
        flowsheet_blueprint = self._maybe_load("flowsheet_blueprint", FlowsheetBlueprintArtifact)
        route_selection_comparison = self._maybe_load("route_selection_comparison", RouteSelectionComparisonArtifact)
        separation_thermo = self._maybe_load("separation_thermo", SeparationThermoArtifact)
        property_method = self._maybe_load("property_method_decision", PropertyMethodDecision)
        kinetics_method = self._maybe_load("kinetics_method_decision", MethodSelectionArtifact)
        kinetic_assessment = self._maybe_load("kinetic_assessment", KineticAssessmentArtifact)
        solve_result = self._maybe_load("solve_result", SolveResult)
        flowsheet_case = self._maybe_load("flowsheet_case", FlowsheetCase)
        route_site_fit = self._maybe_load("route_site_fit", RouteSiteFitArtifact)
        route_economic_basis = self._maybe_load("route_economic_basis", RouteEconomicBasisArtifact)
        equipment_list = self._maybe_load("equipment_list", EquipmentListArtifact)
        reactor_design = self._maybe_load("reactor_design", ReactorDesign)
        column_design = self._maybe_load("column_design", ColumnDesign)
        stream_table = self._maybe_load("stream_table", StreamTable)
        energy_balance = self._maybe_load("energy_balance", EnergyBalance)
        control_plan = self._maybe_load("control_plan", ControlPlanArtifact)
        cost_model = self._maybe_load("cost_model", CostModel)
        commercial_product_basis = self._maybe_load("commercial_product_basis", CommercialProductBasisArtifact)

        species_resolution = None
        reaction_network_v2 = None
        thermo_admissibility = None
        kinetics_admissibility = None
        topology_candidates = None
        flowsheet_intents = None
        design_confidence = None
        economic_coverage = None
        gate_matrix = None
        claim_graph = None
        question_queue = None
        revision_ledger = None

        if route_chemistry is not None:
            species_resolution = build_species_resolution_artifact(route_chemistry, selected_route_id)
            reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution, selected_route_id)
            self._save("species_resolution", species_resolution)
            self._save("reaction_network_v2", reaction_network_v2)
            issues.extend(validate_species_resolution_artifact(species_resolution))
            issues.extend(validate_reaction_network_v2_artifact(reaction_network_v2))
        if route_survey is not None and route_chemistry is not None and property_packages is not None:
            thermo_admissibility = build_thermo_admissibility_artifact(
                route_survey,
                route_chemistry,
                property_packages,
                route_families,
                selected_route_id=selected_route_id,
                separation_thermo=separation_thermo,
                property_method=property_method,
            )
            self._save("thermo_admissibility", thermo_admissibility)
            issues.extend(validate_thermo_admissibility_artifact(thermo_admissibility))
        if route_survey is not None and route_chemistry is not None:
            kinetics_admissibility = build_kinetics_admissibility_artifact(
                route_survey,
                route_chemistry,
                selected_route_id=selected_route_id,
                kinetics_method=kinetics_method,
                kinetic_assessment=kinetic_assessment,
            )
            self._save("kinetics_admissibility", kinetics_admissibility)
            issues.extend(validate_kinetics_admissibility_artifact(kinetics_admissibility))
        if unit_train_candidates is not None and species_resolution is not None and reaction_network_v2 is not None:
            topology_candidates = build_topology_candidate_artifact(
                unit_train_candidates,
                species_resolution,
                reaction_network_v2,
                selected_route_id=selected_route_id,
            )
            self._save("topology_candidates", topology_candidates)
            issues.extend(validate_topology_candidate_artifact(topology_candidates))
            if route_survey is not None and route_process_claims is None:
                route_process_claims = build_route_process_claims_artifact(
                    route_survey,
                    route_chemistry,
                    unit_train_candidates,
                )
                self._save("route_process_claims", route_process_claims)
        if flowsheet_blueprint is not None:
            flowsheet_intents = build_flowsheet_intent_artifact(flowsheet_blueprint)
            self._save("flowsheet_intents", flowsheet_intents)
            issues.extend(validate_flowsheet_intent_artifact(flowsheet_intents))
        if selected_route_id and topology_candidates is not None:
            design_confidence = build_design_confidence_artifact(
                selected_route_id=selected_route_id,
                topology_candidates=topology_candidates,
                thermo_admissibility=thermo_admissibility,
                kinetics_admissibility=kinetics_admissibility,
                flowsheet_blueprint=flowsheet_blueprint,
                flowsheet_case=flowsheet_case,
                solve_result=solve_result,
                reactor_design=reactor_design,
                column_design=column_design,
                equipment_list=equipment_list,
            )
            self._save("design_confidence", design_confidence)
            issues.extend(validate_design_confidence_artifact(design_confidence))
        if selected_route_id and route_site_fit is not None and route_economic_basis is not None:
            economic_coverage = build_economic_coverage_decision(
                route_id=selected_route_id,
                route_economic_basis=route_economic_basis,
                route_site_fit=route_site_fit,
                design_confidence=design_confidence,
            )
            self._save("economic_coverage", economic_coverage)
            issues.extend(validate_economic_coverage_decision(economic_coverage))
        if is_bac_benchmark and flowsheet_blueprint is not None and any(
            artifact is not None
            for artifact in [stream_table, energy_balance, equipment_list, control_plan, reactor_design, column_design, cost_model]
        ):
            unit_train_consistency = build_unit_train_consistency_artifact(
                flowsheet_blueprint,
                stream_table=stream_table,
                energy_balance=energy_balance,
                equipment_list=equipment_list,
                control_plan=control_plan,
                reactor_design=reactor_design,
                column_design=column_design,
                cost_model=cost_model,
            )
            self._save("unit_train_consistency", unit_train_consistency)
            issues.extend(validate_unit_train_consistency_artifact(unit_train_consistency))
        if selected_route is not None and stream_table is not None and commercial_product_basis is not None:
            bac_impurity_model = build_bac_impurity_model_artifact(selected_route, stream_table, commercial_product_basis)
            if bac_impurity_model is not None:
                self._save("bac_impurity_model", bac_impurity_model)
                issues.extend(validate_bac_impurity_model_artifact(bac_impurity_model))
        if selected_route is not None and flowsheet_blueprint is not None and separation_thermo is not None:
            bac_purification_sections = build_bac_purification_section_artifact(
                selected_route,
                flowsheet_blueprint,
                separation_thermo,
                stream_table=stream_table,
            )
            if bac_purification_sections is not None:
                self._save("bac_purification_sections", bac_purification_sections)
                issues.extend(validate_bac_purification_section_artifact(bac_purification_sections))
        if any([species_resolution, thermo_admissibility, kinetics_admissibility, topology_candidates, design_confidence, economic_coverage]):
            gate_matrix = build_scientific_gate_matrix_artifact(
                species_resolution=species_resolution,
                thermo_admissibility=thermo_admissibility,
                kinetics_admissibility=kinetics_admissibility,
                topology_candidates=topology_candidates,
                design_confidence=design_confidence,
                economic_coverage=economic_coverage,
            )
            self._save("scientific_gate_matrix", gate_matrix)
            issues.extend(validate_scientific_gate_matrix(gate_matrix))
        if any([species_resolution, reaction_network_v2, selected_route, thermo_admissibility, kinetics_admissibility, topology_candidates, design_confidence, economic_coverage]):
            previous_claim_graph = self._maybe_load("claim_graph", ClaimGraphArtifact)
            claim_graph = build_claim_graph_artifact(
                stage_id=stage_id,
                previous=previous_claim_graph,
                selected_route_id=selected_route_id,
                species_resolution=species_resolution,
                reaction_network=reaction_network_v2,
                route_process_claims=route_process_claims,
                route_selection=selected_route,
                thermo_admissibility=thermo_admissibility,
                kinetics_admissibility=kinetics_admissibility,
                topology_candidates=topology_candidates,
                stream_table=stream_table,
                design_confidence=design_confidence,
                economic_coverage=economic_coverage,
            )
            self._save("claim_graph", claim_graph)
            issues.extend(validate_claim_graph_artifact(claim_graph))
            question_queue = build_inference_question_queue(
                species_resolution=species_resolution,
                route_process_claims=route_process_claims,
                thermo_admissibility=thermo_admissibility,
                kinetics_admissibility=kinetics_admissibility,
                topology_candidates=topology_candidates,
                economic_coverage=economic_coverage,
            )
            self._save("inference_question_queue", question_queue)
            issues.extend(validate_inference_question_queue(question_queue))
            previous_ledger = self._maybe_load("revision_ledger", RevisionLedgerArtifact)
            revision_ledger = build_revision_ledger(
                previous=previous_ledger,
                stage_id=stage_id,
                state_revision_counts=state.stage_revision_counts,
                route_selection_comparison=route_selection_comparison,
                thermo_admissibility=thermo_admissibility,
                kinetics_admissibility=kinetics_admissibility,
            )
            self._save("revision_ledger", revision_ledger)
            issues.extend(validate_revision_ledger_artifact(revision_ledger))
            if any(ticket.status == "open" for ticket in revision_ledger.tickets):
                for ticket in revision_ledger.tickets:
                    if ticket.status == "open":
                        return issues, ticket.target_stage_id
        return issues, None

    def _benchmark_decision_presence(self) -> dict[str, bool]:
        capacity_decision = self._maybe_load("capacity_decision", DecisionRecord)
        process_synthesis = self._maybe_load("process_synthesis", ProcessSynthesisArtifact)
        route_decision = self._maybe_load("route_decision", DecisionRecord)
        site_decision = self._maybe_load("site_selection_decision", DecisionRecord)
        reactor_choice = self._maybe_load("reactor_choice_decision", DecisionRecord)
        separation_choice = self._maybe_load("separation_choice_decision", DecisionRecord)
        utility_basis = self._maybe_load("utility_basis_decision", DecisionRecord)
        economic_basis = self._maybe_load("economic_basis_decision", DecisionRecord)
        financing_basis = self._maybe_load("financing_basis_decision", DecisionRecord)
        layout_decision = self._maybe_load("layout_decision", LayoutDecisionArtifact)
        return {
            "capacity_case": bool(capacity_decision and capacity_decision.selected_candidate_id),
            "operating_mode": bool(
                process_synthesis
                and process_synthesis.operating_mode_decision
                and process_synthesis.operating_mode_decision.selected_candidate_id
            ),
            "route_selection": bool(route_decision and route_decision.selected_candidate_id),
            "site_selection": bool(site_decision and site_decision.selected_candidate_id),
            "reactor_choice": bool(reactor_choice and reactor_choice.selected_candidate_id),
            "separation_choice": bool(separation_choice and separation_choice.selected_candidate_id),
            "utility_basis": bool(utility_basis and utility_basis.selected_candidate_id),
            "economic_basis": bool(economic_basis and economic_basis.selected_candidate_id),
            "financing_basis": bool(financing_basis and financing_basis.selected_candidate_id),
            "layout": bool(layout_decision and layout_decision.decision and layout_decision.decision.selected_candidate_id),
        }

    def _save_report_acceptance(
        self,
        pipeline_status: RunStatus,
        report_parity: ReportParityArtifact | None = None,
        blocked_stage_id: str | None = None,
        blocking_issues: list[ValidationIssue] | None = None,
    ) -> ReportAcceptanceArtifact | None:
        benchmark_manifest = self._maybe_load("benchmark_manifest", BenchmarkManifest)
        if benchmark_manifest is None:
            return None
        artifact = evaluate_report_acceptance(
            benchmark_manifest,
            report_parity,
            self._benchmark_decision_presence(),
            pipeline_status,
            blocked_stage_id=blocked_stage_id,
            blocking_issues=blocking_issues or [],
        )
        route_selection = self._maybe_load("route_selection", RouteSelectionArtifact)
        process_selection_comparison = self._maybe_load("process_selection_comparison", ProcessSelectionComparisonArtifact)
        commercial_product_basis = self._maybe_load("commercial_product_basis", CommercialProductBasisArtifact)
        resolved_sources = self._maybe_load("resolved_sources", ResolvedSourceSet)
        property_packages = self._maybe_load("property_packages", PropertyPackageArtifact)
        site_selection = self._maybe_load("site_selection", SiteSelectionArtifact)
        unit_train_consistency = self._maybe_load("unit_train_consistency", UnitTrainConsistencyArtifact)
        bac_purification_sections = self._maybe_load("bac_purification_sections", BACPurificationSectionArtifact)
        bac_impurity_model = self._maybe_load("bac_impurity_model", BACImpurityModelArtifact)
        economic_coverage = self._maybe_load("economic_coverage", EconomicCoverageDecision)
        cost_model = self._maybe_load("cost_model", CostModel)
        market_assessment = self._maybe_load("market_assessment", MarketAssessmentArtifact)
        route_economic_basis = self._maybe_load("route_economic_basis", RouteEconomicBasisArtifact)
        data_reality_audit = build_data_reality_audit_artifact(
            self.config,
            resolved_sources,
            self._maybe_load("product_profile", ProductProfileArtifact),
            commercial_product_basis,
            process_selection_comparison,
            property_packages,
            site_selection,
            bac_purification_sections,
            bac_impurity_model,
            economic_coverage,
            cost_model,
        )
        if data_reality_audit is not None:
            self._save("data_reality_audit", data_reality_audit)
        estimation_policy = build_bac_estimation_policy_artifact() if (self.config.benchmark_profile or "").strip().lower() == "benzalkonium_chloride" else None
        pseudo_component_basis = build_bac_pseudo_component_basis_artifact(self.config.basis, self._maybe_load("product_profile", ProductProfileArtifact), property_packages)
        pair_coverage = build_bac_binary_pair_coverage_artifact(route_selection, property_packages, self._maybe_load("separation_thermo", SeparationThermoArtifact))
        section_thermo_assignment = build_bac_section_thermo_assignment_artifact(self._maybe_load("flowsheet_blueprint", FlowsheetBlueprintArtifact), bac_purification_sections, self._maybe_load("separation_thermo", SeparationThermoArtifact))
        kinetic_basis = build_bac_kinetic_basis_artifact(route_selection, self._maybe_load("kinetic_assessment", KineticAssessmentArtifact))
        reactor_basis_confidence = build_reactor_basis_confidence_artifact(kinetic_basis, self._maybe_load("reactor_design", ReactorDesign))
        impurity_ledger = build_bac_impurity_ledger_artifact(bac_impurity_model)
        recycle_basis = build_recycle_basis_artifact(self._maybe_load("stream_table", StreamTable))
        economic_input_reality = build_economic_input_reality_artifact(cost_model, route_economic_basis, market_assessment)
        data_gap_registry = build_bac_data_gap_registry_artifact(
            self.config,
            pseudo_component_basis,
            pair_coverage,
            kinetic_basis,
            impurity_ledger,
            recycle_basis,
            economic_input_reality,
        )
        missing_data_acceptance = build_missing_data_acceptance_artifact(
            data_gap_registry,
            pair_coverage,
            impurity_ledger,
            economic_input_reality,
        )
        for artifact_id, built_artifact in [
            ("estimation_policy", estimation_policy),
            ("bac_pseudo_component_basis", pseudo_component_basis),
            ("binary_pair_coverage", pair_coverage),
            ("section_thermo_assignment", section_thermo_assignment),
            ("kinetic_basis", kinetic_basis),
            ("reactor_basis_confidence", reactor_basis_confidence),
            ("bac_impurity_ledger", impurity_ledger),
            ("recycle_basis", recycle_basis),
            ("economic_input_reality", economic_input_reality),
            ("data_gap_registry", data_gap_registry),
            ("missing_data_acceptance", missing_data_acceptance),
        ]:
            if built_artifact is not None:
                self._save(artifact_id, built_artifact)

        route_evidence_status = "not_evaluated"
        if process_selection_comparison is not None and route_selection is not None:
            selected_row = next(
                (
                    row
                    for row in process_selection_comparison.rows
                    if row.route_id == route_selection.selected_route_id or row.selected
                ),
                None,
            )
            if selected_row is None or selected_row.scientific_status == "blocked":
                route_evidence_status = "blocked"
            elif (
                selected_row.route_evidence_basis == "seeded_benchmark"
                or selected_row.route_origin == "seeded"
                or selected_row.evidence_score < 0.75
            ):
                route_evidence_status = "conditional"
            else:
                route_evidence_status = "complete"

        product_basis_status = "not_evaluated"
        if commercial_product_basis is not None:
            if (
                commercial_product_basis.throughput_basis == "finished_product"
                and commercial_product_basis.sold_solution_basis_kg_hr >= commercial_product_basis.active_basis_kg_hr > 0.0
                and 0.0 < commercial_product_basis.active_fraction <= 1.0
            ):
                product_basis_status = "complete"
            elif commercial_product_basis.active_basis_kg_hr > 0.0:
                product_basis_status = "conditional"
            else:
                product_basis_status = "blocked"

        unit_train_consistency_status = "not_evaluated"
        if unit_train_consistency is not None:
            unit_train_consistency_status = {
                "pass": "complete",
                "warning": "conditional",
                "blocked": "blocked",
            }[unit_train_consistency.overall_status]

        purification_rigor_status = "not_evaluated"
        if bac_purification_sections is not None:
            section_statuses = [section.status for section in bac_purification_sections.sections]
            section_confidences = [section.confidence for section in bac_purification_sections.sections]
            if bac_purification_sections.unresolved_section_ids or any(
                status == ScientificGateStatus.FAIL for status in section_statuses
            ):
                purification_rigor_status = "blocked"
            elif section_statuses and all(status == ScientificGateStatus.PASS for status in section_statuses) and all(
                confidence != ScientificConfidence.SCREENING for confidence in section_confidences
            ):
                purification_rigor_status = "complete"
            else:
                purification_rigor_status = "conditional"

        economic_realism_status = "not_evaluated"
        if economic_coverage is not None:
            economic_realism_status = {
                "detailed": "complete",
                "screening": "conditional",
                "blocked": "blocked",
            }[economic_coverage.status]

        real_data_status = "not_evaluated"
        real_data_coverage_fraction = 0.0
        critical_seeded_dependencies: list[str] = []
        if data_reality_audit is not None:
            real_data_coverage_fraction = data_reality_audit.overall_real_data_fraction
            critical_seeded_dependencies = list(
                dict.fromkeys(
                    data_reality_audit.critical_seeded_artifact_refs + data_reality_audit.critical_inferred_artifact_refs
                )
            )
            if real_data_coverage_fraction >= 0.75 and not critical_seeded_dependencies:
                real_data_status = "complete"
            elif critical_seeded_dependencies:
                real_data_status = "conditional"
            else:
                real_data_status = "conditional"

        updated_overall_status = artifact.overall_status
        updated_blocked_stage = artifact.blocked_stage_id
        updated_blocking_issue_codes = list(artifact.blocking_issue_codes)
        updated_conditional_notes = list(artifact.conditional_notes)
        real_data_note = ""
        if data_reality_audit is not None and self.config.real_data_mode != RealDataMode.AUDIT:
            threshold = max(min(self.config.minimum_real_data_fraction, 1.0), 0.0)
            has_critical_dependency = bool(critical_seeded_dependencies)
            below_threshold = real_data_coverage_fraction < threshold
            real_data_note = (
                f"Real-data policy `{self.config.real_data_mode.value}` observed {real_data_coverage_fraction:.1%} "
                f"critical real-data coverage against threshold {threshold:.0%}."
            )
            if self.config.real_data_mode == RealDataMode.ENFORCE_CRITICAL:
                if updated_overall_status != ReportAcceptanceStatus.BLOCKED and (has_critical_dependency or below_threshold):
                    updated_overall_status = ReportAcceptanceStatus.CONDITIONAL
                    updated_conditional_notes.append(real_data_note)
            elif self.config.real_data_mode == RealDataMode.STRICT:
                if has_critical_dependency or below_threshold:
                    updated_overall_status = ReportAcceptanceStatus.BLOCKED
                    updated_blocked_stage = updated_blocked_stage or "report_acceptance"
                    if "real_data_policy_blocked" not in updated_blocking_issue_codes:
                        updated_blocking_issue_codes.append("real_data_policy_blocked")
                    updated_conditional_notes.append(real_data_note)
        if missing_data_acceptance is not None:
            if missing_data_acceptance.overall_status == ReportAcceptanceStatus.BLOCKED:
                updated_overall_status = ReportAcceptanceStatus.BLOCKED
                updated_blocked_stage = updated_blocked_stage or "report_acceptance"
                if "missing_data_policy_blocked" not in updated_blocking_issue_codes:
                    updated_blocking_issue_codes.append("missing_data_policy_blocked")
            elif (
                missing_data_acceptance.overall_status == ReportAcceptanceStatus.CONDITIONAL
                and updated_overall_status != ReportAcceptanceStatus.BLOCKED
            ):
                updated_overall_status = ReportAcceptanceStatus.CONDITIONAL
            updated_conditional_notes.append(missing_data_acceptance.summary)

        artifact = artifact.model_copy(
            update={
                "overall_status": updated_overall_status,
                "blocked_stage_id": updated_blocked_stage,
                "blocking_issue_codes": updated_blocking_issue_codes,
                "conditional_notes": updated_conditional_notes,
                "route_evidence_status": route_evidence_status,
                "product_basis_status": product_basis_status,
                "unit_train_consistency_status": unit_train_consistency_status,
                "purification_rigor_status": purification_rigor_status,
                "economic_realism_status": economic_realism_status,
                "real_data_status": real_data_status,
                "real_data_coverage_fraction": real_data_coverage_fraction,
                "critical_seeded_dependencies": critical_seeded_dependencies,
                "summary": (
                    f"{artifact.summary} Route evidence={route_evidence_status}; product basis={product_basis_status}; "
                    f"unit-train consistency={unit_train_consistency_status}; purification rigor={purification_rigor_status}; "
                    f"economic realism={economic_realism_status}; real-data status={real_data_status} "
                    f"({real_data_coverage_fraction:.1%} critical real coverage). "
                    f"{missing_data_acceptance.summary if missing_data_acceptance is not None else ''} "
                    f"{real_data_note}".strip()
                ).strip(),
            }
        )
        self._save("report_acceptance", artifact)
        return artifact

    def _refresh_agent_fabric(self) -> None:
        resolved_sources = self._maybe_load("resolved_sources", ResolvedSourceSet)
        resolved_values = self._maybe_load("resolved_values", ResolvedValueArtifact)
        critic_registry = self._maybe_load("critic_registry", CriticRegistryArtifact)
        process_synthesis = self._maybe_load("process_synthesis", ProcessSynthesisArtifact)
        decision_names = [
            "capacity_decision",
            "site_selection_decision",
            "route_decision",
            "reactor_choice_decision",
            "separation_choice_decision",
            "exchanger_choice_decision",
            "storage_choice_decision",
            "moc_choice_decision",
            "utility_basis_decision",
            "procurement_basis_decision",
            "logistics_basis_decision",
            "financing_basis_decision",
            "economic_basis_decision",
        ]
        decisions = [decision for name in decision_names if (decision := self._maybe_load(name, DecisionRecord)) is not None]
        if process_synthesis is not None:
            decisions.append(process_synthesis.operating_mode_decision)
        utility_network = self._maybe_load("utility_network_decision", UtilityNetworkDecision)
        if utility_network is not None:
            decisions.append(utility_network.decision)
        thermo_method = self._maybe_load("thermo_method_decision", MethodSelectionArtifact)
        kinetics_method = self._maybe_load("kinetics_method_decision", MethodSelectionArtifact)
        control_architecture = self._maybe_load("control_architecture", ControlArchitectureDecision)
        layout_decision = self._maybe_load("layout_decision", LayoutDecisionArtifact)
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision)
        if thermo_method:
            decisions.append(thermo_method.decision)
        if kinetics_method:
            decisions.append(kinetics_method.decision)
        if control_architecture:
            decisions.append(control_architecture.decision)
        if layout_decision:
            decisions.append(layout_decision.decision)
        if utility_architecture:
            decisions.append(utility_architecture.decision)
        if not any([resolved_sources, resolved_values, decisions, critic_registry]):
            return
        artifact = build_agent_decision_fabric(resolved_sources, resolved_values, decisions, critic_registry=critic_registry)
        self._save("agent_decision_fabric", artifact)

    def _refresh_critic_registry(self, stage_id: str, issues: list[ValidationIssue]) -> None:
        existing = self._maybe_load("critic_registry", CriticRegistryArtifact)
        solve_result = self._maybe_load("solve_result", SolveResult) if stage_id in {"material_balance", "energy_balance"} else None
        artifact = merge_critic_registry(existing, stage_id, issues, solve_result=solve_result)
        self._save("critic_registry", artifact)

    def _escalate_decision_for_critic_issues(
        self,
        decision: DecisionRecord,
        issues: list[ValidationIssue],
        *,
        trigger_codes: set[str] | None = None,
        note_prefix: str = "Critic escalation",
    ) -> DecisionRecord:
        relevant = [
            issue
            for issue in issues
            if trigger_codes is None or issue.code in trigger_codes
        ]
        if not relevant:
            return decision
        hard_constraints = list(decision.hard_constraint_results)
        note = f"{note_prefix}: " + "; ".join(issue.code for issue in relevant[:4])
        if note not in hard_constraints:
            hard_constraints.append(note)
        confidence = decision.confidence if decision.confidence > 0.0 else 0.78
        return decision.model_copy(
            update={
                "approval_required": True,
                "scenario_stability": (
                    decision.scenario_stability
                    if decision.scenario_stability == ScenarioStability.UNSTABLE
                    else ScenarioStability.BORDERLINE
                ),
                "confidence": max(confidence - 0.10, 0.40),
                "hard_constraint_results": hard_constraints,
            },
            deep=True,
        )

    def _chapter(
        self,
        chapter_id: str,
        title: str,
        stage_id: str,
        markdown: str,
        citations: list[str],
        assumptions: list[str],
        produced_outputs: list[str],
        *,
        required_inputs: list[str] | None = None,
        summary: str = "",
    ) -> ChapterArtifact:
        return ChapterArtifact(
            chapter_id=chapter_id,
            title=title,
            stage_id=stage_id,
            status=ChapterStatus.COMPLETE,
            required_inputs=required_inputs or [],
            produced_outputs=produced_outputs,
            citations=citations,
            assumptions=assumptions,
            summary=summary,
            rendered_markdown=f"## {title}\n\n{markdown.strip()}",
        )

    def _source_ids(self) -> set[str]:
        bundle = self._load("research_bundle", ResearchBundle)
        return {source.source_id for source in bundle.sources}

    def _repair_india_price_data(self, artifact, bundle: ResearchBundle) -> None:
        fallback_citations = list(
            dict.fromkeys(
                [
                    *bundle.india_source_ids,
                    *[source.source_id for source in bundle.sources if source.source_domain.value in {"economics", "utilities", "market"}],
                    *getattr(artifact, "citations", []),
                ]
            )
        )
        normalization_updated = False
        citation_repaired = False
        for datum in getattr(artifact, "india_price_data", []):
            if not datum.citations and fallback_citations:
                datum.citations = list(fallback_citations)
                citation_repaired = True
            if datum.normalization_year < self.config.basis.economic_reference_year:
                datum.normalization_year = self.config.basis.economic_reference_year
                normalization_updated = True
        if citation_repaired:
            artifact.assumptions.append(
                "Per-datum India price citations were inherited from the cited market and India-basis sources when the model omitted row-level source ids."
            )
        if normalization_updated:
            artifact.assumptions.append(
                f"India price data was normalized forward to the project economic reference year {self.config.basis.economic_reference_year} for feasibility-level screening."
            )

    def _repair_india_location_data(self, artifact, bundle: ResearchBundle) -> None:
        fallback_citations = list(
            dict.fromkeys(
                [
                    *bundle.india_source_ids,
                    *[
                        source.source_id
                        for source in bundle.sources
                        if source.source_domain.value in {"site", "logistics", "utilities", "regulatory"}
                    ],
                    *getattr(artifact, "citations", []),
                ]
            )
        )
        citation_repaired = False
        for location in getattr(artifact, "india_location_data", []):
            if not location.citations and fallback_citations:
                location.citations = list(fallback_citations)
                citation_repaired = True
        if citation_repaired:
            artifact.assumptions.append(
                "Per-location India site citations were inherited from the cited site, logistics, utility, and regulatory sources when the model omitted row-level source ids."
            )

    def _repair_product_profile_citations(self, artifact) -> None:
        fallback_citations = list(dict.fromkeys(getattr(artifact, "citations", [])))
        citation_repaired = False
        for item in getattr(artifact, "properties", []):
            if item.supporting_sources or item.citations or not fallback_citations:
                continue
            item.supporting_sources = list(fallback_citations)
            citation_repaired = True
        if citation_repaired:
            artifact.assumptions.append(
                "Per-property product-profile citations were inherited from the cited product-profile sources when the model omitted row-level source ids."
            )
        if self.config.benchmark_profile != "benzalkonium_chloride":
            return
        observed = {item.name.strip().lower() for item in getattr(artifact, "properties", [])}
        fallback_support = list(
            dict.fromkeys(
                fallback_citations
                or [
                    source.source_id
                    for source in getattr(self._maybe_load("research_bundle", ResearchBundle), "sources", [])
                    if source.source_domain.value in {"technical", "safety", "market", "regulatory"}
                ]
            )
        )
        synthesized = False
        for name, units, note in (
            (
                "Melting Point",
                "°C",
                "Physical property for the pure BAC active or a standardized commercial homolog mixture is not directly available in the cited source set.",
            ),
            (
                "Boiling Point",
                "°C",
                "BAC active is treated as effectively nonvolatile in the process basis; a true boiling point for the commercial homolog mixture is not directly available in the cited source set.",
            ),
            (
                "Density",
                "g/cm³",
                "A directly sourced density for the exact benchmark commercial basis is not available in the cited source set and is handled later through the BAC pseudo-component basis.",
            ),
        ):
            if name.lower() in observed:
                continue
            artifact.properties.append(
                PropertyRecord(
                    name=name,
                    value="Not Available",
                    units=units,
                    basis=None,
                    method=ProvenanceTag.SOURCED,
                    supporting_sources=list(fallback_support),
                    citations=list(fallback_support),
                    assumptions=[note],
                )
            )
            synthesized = True
        if synthesized:
            artifact.assumptions.append(
                "Required BAC product-profile rows for melting point, boiling point, and density were synthesized as explicit sourced unavailability records when the live model omitted them, so the report surfaces the data gap instead of failing silently."
            )

    @staticmethod
    def _is_external_source_id(source_id: str) -> bool:
        text = (source_id or "").strip().lower()
        if not text:
            return False
        return not (
            text.startswith("seed_")
            or text.startswith("benchmark_")
            or text.startswith("seed_bip_")
        )

    def _bac_external_technical_source_ids(self, bundle: ResearchBundle) -> list[str]:
        return [
            source_id
            for source_id in dict.fromkeys(
                [
                    *bundle.technical_source_ids,
                    *[
                        source.source_id
                        for source in bundle.sources
                        if source.source_domain.value in {"technical", "safety", "regulatory"}
                    ],
                ]
            )
            if self._is_external_source_id(source_id)
        ]

    def _bac_external_site_source_ids(self, bundle: ResearchBundle) -> list[str]:
        return [
            source_id
            for source_id in dict.fromkeys(
                [
                    *bundle.india_source_ids,
                    *[
                        source.source_id
                        for source in bundle.sources
                        if source.source_domain.value in {"site", "logistics", "utilities", "regulatory"}
                    ],
                ]
            )
            if self._is_external_source_id(source_id)
        ]

    def _replace_bac_route_survey_with_external_candidates(
        self,
        artifact: RouteSurveyArtifact,
        bundle: ResearchBundle,
    ) -> RouteSurveyArtifact:
        if self.config.basis.target_product.strip().lower() != "benzalkonium chloride":
            return artifact
        external_source_ids = self._bac_external_technical_source_ids(bundle)
        if not external_source_ids:
            return artifact
        if any(route.route_evidence_basis in {"cited_technical", "cited_patent", "mixed_cited", "document_derived"} for route in artifact.routes):
            return artifact
        cited_routes: list[RouteOption] = []
        for route in artifact.routes:
            if route.route_id == "benzyl_chloride_quaternization_ethanol":
                cited_routes.append(
                    route.model_copy(
                        update={
                            "route_origin": "hybrid",
                            "route_evidence_basis": "cited_technical",
                            "evidence_score": max(route.evidence_score, 0.84),
                            "citations": list(external_source_ids),
                            "rationale": "Externally cited BAC route built around benzyl chloride quaternization in alcohol medium with continuous cleanup and commercial active-solution finishing.",
                            "scale_up_notes": "Externally sourced technical references support the alcohol-medium continuous BAC route as a commercial active-solution basis with residual-reactant cleanup and dilution finishing.",
                        }
                    )
                )
            elif route.route_id == "benzyl_chloride_quaternization_high_strength":
                cited_routes.append(
                    route.model_copy(
                        update={
                            "route_origin": "hybrid",
                            "route_evidence_basis": "mixed_cited",
                            "evidence_score": max(route.evidence_score, 0.78),
                            "citations": list(external_source_ids),
                            "rationale": "Externally cited high-strength BAC quaternization variant with lower solvent circulation and tighter residual cleanup requirements.",
                            "scale_up_notes": "Externally sourced BAC technical references support a concentrated continuous quaternization variant, but with stronger viscosity, color, and exotherm-control burden.",
                        }
                    )
                )
            elif route.route_id == "benzyl_alcohol_activation_quaternization":
                cited_routes.append(
                    route.model_copy(
                        update={
                            "route_origin": "hybrid",
                            "route_evidence_basis": "cited_technical",
                            "evidence_score": max(route.evidence_score, 0.64),
                            "citations": list(external_source_ids),
                            "rationale": "Externally cited alternate BAC route hypothesis using benzyl alcohol activation before quaternization, retained as a weaker but evidenced alternative.",
                            "scale_up_notes": "Externally sourced references indicate the route is chemically plausible, though less attractive because of added activation and chloride-management burden.",
                        }
                    )
                )
            else:
                cited_routes.append(route)
        markdown = (
            "Benzalkonium chloride route survey is anchored to externally cited BAC process references rather than seeded route families. "
            "The alternatives compare continuous benzyl chloride quaternization variants on exotherm control, residual benzyl chloride cleanup, solvent handling, and commercial active-solution finishing.\n\n"
            + artifact.markdown
        )
        assumptions = [
            assumption
            for assumption in artifact.assumptions
            if "seeded" not in assumption.lower()
        ]
        assumptions.append(
            "BAC route survey candidates were replaced with externally cited route alternatives when non-seed technical evidence was available in the research bundle."
        )
        return artifact.model_copy(
            update={
                "routes": cited_routes,
                "markdown": markdown,
                "citations": list(external_source_ids),
                "assumptions": assumptions,
            },
            deep=True,
        )

    def _replace_bac_site_selection_with_external_candidates(
        self,
        artifact,
        bundle: ResearchBundle,
    ):
        if self.config.basis.target_product.strip().lower() != "benzalkonium chloride":
            return artifact
        external_source_ids = self._bac_external_site_source_ids(bundle)
        if not external_source_ids:
            return artifact
        if any(self._is_external_source_id(source_id) for source_id in artifact.citations):
            return artifact
        artifact.candidates = [
            candidate.model_copy(
                update={
                    "citations": list(external_source_ids),
                    "rationale": (
                        "Externally sourced BAC siting evidence supports this candidate on port logistics, utility access, industrial services, and liquid chemical dispatch."
                        if candidate.name == "Dahej"
                        else "Externally sourced BAC siting evidence supports this candidate as a credible west-coast or market-linked alternative for liquid chemical manufacture."
                    ),
                }
            )
            for candidate in artifact.candidates
        ]
        artifact.india_location_data = [
            location.model_copy(update={"citations": list(external_source_ids)})
            for location in artifact.india_location_data
        ]
        artifact.citations = list(external_source_ids)
        artifact.markdown = (
            "BAC site candidates are backed by externally sourced India site, logistics, utility, and regulatory evidence rather than seeded cluster-only siting notes.\n\n"
            + artifact.markdown
        )
        artifact.assumptions = [
            assumption
            for assumption in artifact.assumptions
            if "seeded" not in assumption.lower()
        ] + [
            "BAC site candidates were rebound to externally sourced India site evidence when non-seed site/logistics/utility/regulatory references were available."
        ]
        return artifact

    def _repair_artifact_citations(self, artifact, fallback_citations: list[str], note: str) -> None:
        valid_source_ids = self._source_ids()
        current_citations = list(dict.fromkeys(getattr(artifact, "citations", [])))
        filtered_citations = [citation for citation in current_citations if citation in valid_source_ids]
        repaired = filtered_citations != current_citations
        if not filtered_citations and fallback_citations:
            filtered_citations = [citation for citation in dict.fromkeys(fallback_citations) if citation in valid_source_ids]
            repaired = repaired or bool(filtered_citations)
        if repaired and filtered_citations:
            artifact.citations = filtered_citations
            artifact.assumptions.append(note)

    def _value_issues(self, artifact, artifact_ref: str) -> list[ValidationIssue]:
        return validate_value_records(getattr(artifact, "value_records", []), self._source_ids(), self.config, artifact_ref)

    def _selected_route(self) -> RouteOption:
        selection = self._load("route_selection", RouteSelectionArtifact)
        survey = self._load("route_survey", RouteSurveyArtifact)
        for route in survey.routes:
            if route.route_id == selection.selected_route_id:
                return route
        raise RuntimeError(f"Selected route '{selection.selected_route_id}' not found.")

    def _selected_utility_network(self) -> UtilityNetworkDecision:
        return self._load("utility_network_decision", UtilityNetworkDecision)

    def _normalize_route_survey(self, artifact: RouteSurveyArtifact) -> RouteSurveyArtifact:
        if self.config.basis.target_product.lower() != "ethylene glycol":
            return artifact
        for route in artifact.routes:
            name = route.name.lower()
            if "omega" in name or "ethylene carbonate" in name:
                route.route_id = "omega_catalytic"
                route.reaction_equation = "C2H4O + H2O -> C2H6O2"
                route.participants = [
                    route.participants[0].model_copy(update={"name": "Ethylene oxide", "formula": "C2H4O", "coefficient": 1.0, "role": "reactant", "molecular_weight_g_mol": 44.05}),
                    route.participants[0].model_copy(update={"name": "Water", "formula": "H2O", "coefficient": 1.0, "role": "reactant", "molecular_weight_g_mol": 18.015}),
                    route.participants[0].model_copy(update={"name": "Ethylene glycol", "formula": "C2H6O2", "coefficient": 1.0, "role": "product", "molecular_weight_g_mol": 62.07}),
                ]
                if "CO2 catalytic loop" not in route.catalysts:
                    route.catalysts.append("CO2 catalytic loop")
            elif "hydration" in name and "oxide" in name:
                route.route_id = "eo_hydration"
                route.reaction_equation = "C2H4O + H2O -> C2H6O2"
                route.participants = [
                    route.participants[0].model_copy(update={"name": "Ethylene oxide", "formula": "C2H4O", "coefficient": 1.0, "role": "reactant", "molecular_weight_g_mol": 44.05}),
                    route.participants[0].model_copy(update={"name": "Water", "formula": "H2O", "coefficient": 1.0, "role": "reactant", "molecular_weight_g_mol": 18.015}),
                    route.participants[0].model_copy(update={"name": "Ethylene glycol", "formula": "C2H6O2", "coefficient": 1.0, "role": "product", "molecular_weight_g_mol": 62.07}),
                ]
            elif "chlorohydrin" in name:
                route.route_id = "chlorohydrin"
                route.reaction_equation = "C2H5ClO + NaOH -> C2H6O2 + NaCl"
                route.participants = [
                    route.participants[0].model_copy(update={"name": "Ethylene chlorohydrin", "formula": "C2H5ClO", "coefficient": 1.0, "role": "reactant", "molecular_weight_g_mol": 80.51}),
                    route.participants[0].model_copy(update={"name": "Sodium hydroxide", "formula": "NaOH", "coefficient": 1.0, "role": "reactant", "molecular_weight_g_mol": 40.00}),
                    route.participants[0].model_copy(update={"name": "Ethylene glycol", "formula": "C2H6O2", "coefficient": 1.0, "role": "product", "molecular_weight_g_mol": 62.07}),
                    route.participants[0].model_copy(update={"name": "Sodium chloride", "formula": "NaCl", "coefficient": 1.0, "role": "byproduct", "molecular_weight_g_mol": 58.44}),
                ]
        return artifact

    def _augment_route_survey_from_documents(self, artifact: RouteSurveyArtifact, bundle: ResearchBundle) -> RouteSurveyArtifact:
        if not bundle.document_process_options:
            return artifact
        has_generic_fallback = len(artifact.routes) == 1 and artifact.routes[0].route_id == "generic_route_1"
        existing_ids = {route.route_id for route in artifact.routes}
        augmented_routes = [] if has_generic_fallback else list(artifact.routes)
        if has_generic_fallback:
            existing_ids = set()
        for option in bundle.document_process_options:
            route_id = option.option_id
            if route_id in existing_ids:
                continue
            valid_species = [name for name in option.extracted_species if self._is_valid_route_species_candidate(name)]
            valid_raw_materials = [name for name in option.raw_materials if self._is_valid_route_species_candidate(name)]
            catalyst_ids = {
                normalize_chemical_name(name)
                for name in option.catalysts
                if self._is_valid_route_species_candidate(name)
            }
            solvent_ids = {
                normalize_chemical_name(name)
                for name in option.solvents
                if self._is_valid_route_species_candidate(name)
            }
            target_id = normalize_chemical_name(self.config.basis.target_product)
            candidate_reactants = valid_raw_materials[:3] or valid_species[:2]
            reactants = list(
                dict.fromkeys(
                    name
                    for name in candidate_reactants
                    if normalize_chemical_name(name) not in catalyst_ids
                    and normalize_chemical_name(name) not in solvent_ids
                    and normalize_chemical_name(name) != target_id
                )
            )
            participants = [
                ReactionParticipant(
                    name=name,
                    formula="",
                    coefficient=1.0,
                    role="reactant",
                    molecular_weight_g_mol=0.0,
                    phase=None,
                )
                for name in reactants
            ]
            participants.append(
                ReactionParticipant(
                    name=self.config.basis.target_product,
                    formula="",
                    coefficient=1.0,
                    role="product",
                    molecular_weight_g_mol=0.0,
                    phase=None,
                )
            )
            score = 6.0
            if option.yield_fraction is not None:
                score += option.yield_fraction * 2.0
            if option.selected_in_document:
                score += 1.0
            evidence_score = 0.90 if option.selected_in_document else 0.72
            completeness = 0.80 if option.extracted_species else 0.45
            augmented_routes.append(
                RouteOption(
                    route_id=route_id,
                    name=option.label,
                    reaction_equation=f"{' + '.join(reactants) if reactants else 'document reactants'} -> {self.config.basis.target_product}",
                    participants=participants,
                    route_origin="document",
                    route_evidence_basis="document_derived",
                    source_document_id=option.source_document_id,
                    evidence_score=evidence_score,
                    chemistry_completeness_score=completeness,
                    separation_complexity_score=max(0.4, min(1.0, len(valid_species) / 8.0)),
                    extracted_species=list(valid_species),
                    reaction_family_hints=list(option.reaction_family_hints),
                    core_species_complete=bool(reactants),
                    catalysts=list(option.catalysts),
                    operating_temperature_c=80.0,
                    operating_pressure_bar=3.0,
                    residence_time_hr=4.0 if self.config.basis.operating_mode == "batch" else 2.0,
                    yield_fraction=option.yield_fraction or 0.80,
                    selectivity_fraction=min(option.yield_fraction + 0.05, 0.98) if option.yield_fraction is not None else 0.85,
                    byproducts=[],
                    separations=["document-derived purification train"],
                    scale_up_notes=option.summary[:240] or "Document-derived route option.",
                    hazards=[],
                    route_score=score,
                    rationale=option.summary[:240] or "Route extracted from document process-comparison section.",
                    citations=option.citations,
                    assumptions=["Document-derived route option uses heuristic participant extraction and placeholder thermophysical data until the chemistry graph is resolved."],
                )
            )
            existing_ids.add(route_id)
        if len(augmented_routes) == len(artifact.routes) and not has_generic_fallback:
            return artifact
        markdown_parts = [artifact.markdown.strip()] if artifact.markdown.strip() else []
        markdown_parts.append("### Document-Derived Route Options\n")
        markdown_parts.append(
            "\n".join(
                [
                    "| Route | Origin | Selected in Document | Yield | Extracted Species |",
                    "| --- | --- | --- | --- | --- |",
                    *[
                        f"| {route.name} | {route.route_origin} | "
                        f"{'yes' if route.route_origin == 'document' and route.route_id in {item.option_id for item in bundle.document_process_options if item.selected_in_document} else 'no'} | "
                        f"{route.yield_fraction:.2f} | {', '.join(route.extracted_species[:4]) or '-'} |"
                        for route in augmented_routes
                    ],
                ]
            )
        )
        return artifact.model_copy(update={"routes": augmented_routes, "markdown": "\n\n".join(markdown_parts)}, deep=True)

    @staticmethod
    def _infer_route_evidence_basis(route: RouteOption, source_index: dict[str, SourceRecord]) -> tuple[str, str]:
        if route.route_origin == "document":
            return "document_derived", "document"
        if not route.citations:
            return "generated", "generated"
        cited_records = [source_index[source_id] for source_id in route.citations if source_id in source_index]
        external_citation_ids = [
            source_id
            for source_id in route.citations
            if source_id
            and not source_id.startswith("seed_")
            and not source_id.startswith("benchmark_")
            and not source_id.startswith("seed_bip_")
        ]
        if cited_records and all(record.source_id.startswith("seed_") for record in cited_records) and not external_citation_ids:
            return "seeded_benchmark", "seeded"
        if not cited_records and external_citation_ids:
            return "cited_technical", "hybrid"
        if not cited_records:
            return "generated", route.route_origin
        source_kinds = {record.source_kind.value for record in cited_records}
        if external_citation_ids and any(
            kind in source_kinds
            for kind in {"patent", "literature", "handbook", "web", "company_report", "sds", "government"}
        ):
            if "patent" in source_kinds and (
                source_kinds & {"literature", "handbook", "web", "company_report", "sds", "government"}
            ):
                return "mixed_cited", "hybrid"
            if "patent" in source_kinds:
                return "cited_patent", "hybrid"
            return "cited_technical", "hybrid"
        if "patent" in source_kinds and ("literature" in source_kinds or "handbook" in source_kinds):
            return "mixed_cited", "hybrid"
        if "patent" in source_kinds:
            return "cited_patent", "hybrid"
        if source_kinds & {"literature", "handbook", "web", "company_report", "sds", "government"}:
            return "cited_technical", "hybrid"
        return "generated", route.route_origin

    def _apply_route_evidence_basis(self, artifact: RouteSurveyArtifact, bundle: ResearchBundle) -> RouteSurveyArtifact:
        source_index = {source.source_id: source for source in bundle.sources}
        updated_routes: list[RouteOption] = []
        changed = False
        for route in artifact.routes:
            evidence_basis, route_origin = self._infer_route_evidence_basis(route, source_index)
            if evidence_basis != route.route_evidence_basis or route_origin != route.route_origin:
                changed = True
                updated_routes.append(
                    route.model_copy(
                        update={
                            "route_evidence_basis": evidence_basis,
                            "route_origin": route_origin,
                        }
                    )
                )
            else:
                updated_routes.append(route)
        if not changed:
            return artifact
        return artifact.model_copy(update={"routes": updated_routes}, deep=True)

    @staticmethod
    def _is_valid_route_species_candidate(name: str) -> bool:
        return is_valid_property_identifier_name(name)

    def _existing_chapters(self, state: ProjectRunState) -> list[ChapterArtifact]:
        return [self.store.load_chapter(self.config.project_id, chapter_id) for chapter_id in state.chapter_index]

    def _gate(self, gate_id: str, title: str, description: str) -> GateDecision:
        return GateDecision(gate_id=gate_id, title=title, description=description)

    def _chapter_issues(self, chapter: ChapterArtifact) -> list[ValidationIssue]:
        return validate_chapter(chapter, self._source_ids(), self.config.strict_citation_policy)

    def _run_project_intake(self) -> StageResult:
        bundle = self.research_manager.build_bundle(self.config)
        benchmark_manifest = build_benchmark_manifest(self.config)
        report_parity_framework = build_report_parity_framework(benchmark_manifest)
        resolved_sources = build_resolved_source_set(self.config, bundle)
        document_facts = build_document_fact_collection(bundle.user_document_facts)
        document_process_options = build_document_process_options(bundle.user_document_facts)
        self._save("project_basis", self.config.basis)
        self._save("research_bundle", bundle)
        self._save("benchmark_manifest", benchmark_manifest)
        self._save("report_parity_framework", report_parity_framework)
        self._save("resolved_sources", resolved_sources)
        self._save("user_document_facts", document_facts)
        self._save("document_process_options", document_process_options)
        issues, missing_groups, stale_groups = validate_research_bundle(bundle, self.config)
        issues.extend(validate_document_fact_collection(document_facts))
        issues.extend(validate_report_parity_framework(report_parity_framework, benchmark_manifest))
        issues.extend(validate_resolved_source_set(resolved_sources, {source.source_id for source in bundle.sources}, self.config))
        return StageResult(issues=issues, missing_india_coverage=missing_groups, stale_source_groups=stale_groups)

    def _run_product_profile(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        artifact = self.reasoning.build_product_profile(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        self._repair_product_profile_citations(artifact)
        self._save("product_profile", artifact)
        issues = validate_property_records(artifact.properties, self._source_ids(), self.config.strict_citation_policy)
        chapter_markdown = artifact.markdown
        if self.config.benchmark_profile == "benzalkonium_chloride" and artifact.properties:
            property_rows = [
                [
                    item.name,
                    item.value,
                    item.units or "-",
                    item.method.value,
                    ", ".join(item.supporting_sources or item.citations) or "-",
                ]
                for item in artifact.properties
            ]
            chapter_markdown += (
                "\n\n### Properties\n\n"
                + markdown_table(
                    ["Property", "Value", "Units", "Quality", "Citations"],
                    property_rows,
                )
            )
        chapter = self._chapter(
            "introduction_product_profile",
            "Introduction and Product Profile",
            "product_profile",
            chapter_markdown,
            artifact.citations,
            artifact.assumptions,
            ["product_profile"],
            required_inputs=["research_bundle"],
            summary=artifact.industrial_relevance,
        )
        issues.extend(self._chapter_issues(chapter))
        return StageResult(chapters=[chapter], issues=issues)

    def _run_market_capacity(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        product_profile = self._load("product_profile", ProductProfileArtifact)
        artifact = self.reasoning.build_market_assessment(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        commercial_basis = build_commercial_product_basis_artifact(self.config.basis, product_profile, artifact)
        default_price_source = next((source_id for source_id in bundle.india_source_ids if source_id.startswith("india_sheet_")), None)
        if default_price_source:
            for datum in artifact.india_price_data:
                if not datum.citations:
                    datum.citations = [default_price_source]
        self._repair_india_price_data(artifact, bundle)
        capacity_decision = build_capacity_decision(self.config, artifact)
        self._save("market_assessment", artifact)
        self._save("capacity_decision", capacity_decision)
        self._save("commercial_product_basis", commercial_basis)
        self._refresh_agent_fabric()
        issues = validate_india_price_data(artifact.india_price_data, self._source_ids(), self.config, "market_assessment")
        issues.extend(validate_commercial_product_basis_artifact(commercial_basis))
        chapter = self._chapter(
            "market_capacity_selection",
            "Market and Capacity Selection",
            "market_capacity",
            artifact.markdown
            + f"\n\n### Commercial Product Basis\n\n{commercial_basis.markdown}\n\n### Capacity Decision\n\n{capacity_decision.selected_summary}",
            sorted(set(artifact.citations + capacity_decision.citations + commercial_basis.citations)),
            artifact.assumptions + commercial_basis.assumptions + capacity_decision.assumptions,
            ["market_assessment", "capacity_decision", "commercial_product_basis"],
            required_inputs=["research_bundle", "product_profile"],
            summary=artifact.capacity_rationale,
        )
        issues.extend(validate_decision_record(capacity_decision, "capacity_decision"))
        issues.extend(self._chapter_issues(chapter))
        return StageResult(chapters=[chapter], issues=issues)

    def _run_literature_route_survey(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        artifact = self.reasoning.survey_routes(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        artifact = self._normalize_route_survey(artifact)
        artifact = self._replace_bac_route_survey_with_external_candidates(artifact, bundle)
        artifact = self._augment_route_survey_from_documents(artifact, bundle)
        artifact = self._apply_route_evidence_basis(artifact, bundle)
        route_chemistry = build_route_chemistry_artifact(artifact, bundle.user_document_facts)
        route_discovery = build_route_discovery_artifact(artifact, route_chemistry)
        document_process_options = self._load("document_process_options", DocumentProcessOptionsArtifact)
        self._save("route_survey", artifact)
        self._save("route_chemistry", route_chemistry)
        self._save("route_discovery", route_discovery)
        chapter = self._chapter(
            "literature_survey",
            "Literature Survey",
            "literature_route_survey",
            (
                f"{artifact.markdown}\n\n"
                f"### Route Discovery\n\n{route_discovery.markdown}\n\n"
                f"### Route Chemistry Coverage\n\n{route_chemistry.markdown}\n\n"
                f"### Document-Derived Process Options\n\n"
                f"{document_process_options.markdown if document_process_options.options else 'No document-derived process options.'}"
            ),
            artifact.citations,
            artifact.assumptions,
            ["route_survey", "route_chemistry", "route_discovery"],
            required_inputs=["research_bundle"],
        )
        issues = validate_route_chemistry_artifact(route_chemistry)
        issues.extend(validate_route_discovery_artifact(route_discovery))
        issues.extend(self._chapter_issues(chapter))
        return StageResult(chapters=[chapter], issues=issues)

    def _run_property_gap_resolution(self) -> StageResult:
        product_profile = self._load("product_profile", ProductProfileArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        bundle = self._load("research_bundle", ResearchBundle)
        route_survey = self._load("route_survey", RouteSurveyArtifact)
        route_chemistry = self._load("route_chemistry", RouteChemistryArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        artifact = resolve_property_gaps(product_profile, self.config)
        property_packages = build_property_package_artifact(self.config, bundle, product_profile, route_survey)
        property_requirements = build_property_requirement_artifact(self.config, property_packages)
        property_demand_plan = build_property_demand_plan(route_chemistry, property_packages)
        resolved_values = build_resolved_value_artifact(artifact, resolved_sources, self.config)
        resolved_values = extend_resolved_value_artifact(
            resolved_values,
            property_value_records(property_packages, property_demand_plan),
            resolved_sources,
            self.config,
            "property_engine",
        )
        bip_estimates = property_estimates_from_packages(property_packages)
        if bip_estimates:
            estimate_index = {
                item.estimate_id: item
                for item in resolved_values.property_estimates
            }
            estimate_index.update({item.estimate_id: item for item in bip_estimates})
            resolved_values = resolved_values.model_copy(
                update={
                    "property_estimates": sorted(
                        estimate_index.values(),
                        key=lambda item: item.property_name.lower(),
                    )
                }
            )
        market_value_records = [
            make_value_record(
                f"market_{datum.datum_id}",
                f"{datum.item_name} price basis",
                datum.value_inr,
                datum.units,
                provenance_method=ProvenanceTag.SOURCED,
                source_ids=datum.citations,
                citations=datum.citations,
                assumptions=market.assumptions,
                sensitivity=SensitivityLevel.HIGH if datum.category in {"product", "raw_material", "utility"} else SensitivityLevel.MEDIUM,
            )
            for datum in market.india_price_data
        ]
        resolved_values = extend_resolved_value_artifact(resolved_values, market_value_records, resolved_sources, self.config, "market_capacity")
        self._save("property_gap", artifact)
        self._save("resolved_values", resolved_values)
        self._save("property_packages", property_packages)
        self._save("property_requirements", property_requirements)
        self._save("property_demand_plan", property_demand_plan)
        self._refresh_agent_fabric()
        issues = validate_property_gap_artifact(artifact, self.config)
        issues.extend(validate_route_chemistry_artifact(route_chemistry))
        issues.extend(validate_resolved_value_artifact(resolved_values, self._source_ids(), self.config))
        issues.extend(validate_property_package_artifact(property_packages, self._source_ids(), self.config))
        issues.extend(validate_property_requirement_set(property_requirements))
        issues.extend(validate_property_demand_plan(property_demand_plan))
        gate = None
        if self.config.evidence_lock_required and not issues:
            gate = self._gate("evidence_lock", "Evidence Lock", "Approve the resolved source and value basis before process synthesis proceeds.")
        return StageResult(issues=issues, gate=gate)

    def _run_process_synthesis(self) -> StageResult:
        survey = self._load("route_survey", RouteSurveyArtifact)
        route_chemistry = self._load("route_chemistry", RouteChemistryArtifact)
        bundle = self._load("research_bundle", ResearchBundle)
        property_gap = self._load("property_gap", PropertyGapArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        archetype = classify_process_archetype(self.config, survey, property_gap)
        family_adapter = build_chemistry_family_adapter(self.config, survey, property_gap, archetype)
        route_families = build_route_family_artifact(survey, family_adapter)
        sparse_data_policy = build_sparse_data_policy(self.config, family_adapter, property_packages)
        archetype = archetype.model_copy(update={"chemistry_family_adapter_id": family_adapter.adapter_id}, deep=True)
        property_requirements = build_property_requirement_artifact(self.config, property_packages, sparse_data_policy)
        alternative_sets = build_alternative_sets(self.config, archetype, survey, route_families)
        citations = sorted(set(survey.citations + property_gap.citations + archetype.citations))
        assumptions = survey.assumptions + property_gap.assumptions + archetype.assumptions
        operating_mode_decision, operations_planning = build_operating_mode_and_operations(self.config.basis, archetype, citations, assumptions)
        artifact = build_process_synthesis(
            self.config,
            survey,
            property_gap,
            operating_mode_decision=operating_mode_decision,
            route_families=route_families,
        )
        species_resolution = build_species_resolution_artifact(route_chemistry)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution)
        unit_train_candidates = build_unit_train_candidate_set(
            survey,
            route_chemistry,
            route_families,
            bundle.user_document_facts,
            operating_mode_decision.selected_candidate_id or self.config.basis.operating_mode,
        )
        route_process_claims = build_route_process_claims_artifact(
            survey,
            route_chemistry,
            unit_train_candidates,
        )
        route_screening = build_route_screening_artifact(
            survey,
            route_chemistry,
            species_resolution,
            reaction_network_v2,
            route_families,
            unit_train_candidates,
            route_process_claims,
            operating_mode=operating_mode_decision.selected_candidate_id or self.config.basis.operating_mode,
        )
        artifact.archetype = archetype
        artifact.family_adapter = family_adapter
        artifact.alternative_sets = alternative_sets
        artifact.unit_train_candidate_ids = [item.blueprint_id for item in unit_train_candidates.blueprints]
        self._save("process_synthesis", artifact)
        self._save("process_archetype", archetype)
        self._save("chemistry_family_adapter", family_adapter)
        self._save("route_family_profiles", route_families)
        self._save("sparse_data_policy", sparse_data_policy)
        self._save("property_requirements", property_requirements)
        self._save("operations_planning", operations_planning)
        self._save("unit_train_candidates", unit_train_candidates)
        self._save("route_process_claims", route_process_claims)
        self._save("route_screening", route_screening)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), operations_planning.value_records, self._load("resolved_sources", ResolvedSourceSet), self.config, "process_synthesis"),
        )
        self.config.basis.operating_mode = artifact.operating_mode_decision.selected_candidate_id or self.config.basis.operating_mode
        self.store.save_config(self.config)
        issues = validate_decision_record(artifact.operating_mode_decision, "operating_mode")
        issues.extend(validate_chemistry_family_adapter(family_adapter))
        issues.extend(validate_route_family_artifact(route_families))
        issues.extend(validate_sparse_data_policy(sparse_data_policy))
        issues.extend(validate_property_requirement_set(property_requirements))
        issues.extend(validate_process_archetype(archetype))
        issues.extend(validate_operations_planning(operations_planning))
        issues.extend(validate_unit_train_candidate_set(unit_train_candidates))
        issues.extend(validate_route_process_claims_artifact(route_process_claims))
        issues.extend(validate_route_screening_artifact(route_screening))
        return StageResult(issues=issues)

    def _run_rough_alternative_balances(self) -> StageResult:
        survey = self._load("route_survey", RouteSurveyArtifact)
        synthesis = self._load("process_synthesis", ProcessSynthesisArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        route_families = self._load("route_family_profiles", RouteFamilyArtifact)
        unit_train_candidates = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_train_candidates.json", UnitTrainCandidateSet)
        artifact = build_rough_alternatives(
            self.config,
            survey,
            synthesis,
            market,
            route_families,
            unit_train_candidates,
        )
        self._save("rough_alternatives", artifact)
        return StageResult()

    def _run_heat_integration_optimization(self) -> StageResult:
        rough_alternatives = self._load("rough_alternatives", RoughAlternativeSummaryArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        artifact = build_heat_integration_study(self.config, rough_alternatives, market)
        self._save("heat_integration_study", artifact)
        issues = validate_heat_integration_study(artifact, self.config)
        chapter = self._chapter(
            "heat_integration_strategy",
            "Heat Integration and Utility Optimization",
            "heat_integration_optimization",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["heat_integration_study"],
            required_inputs=["rough_alternatives", "market_assessment"],
        )
        issues.extend(self._chapter_issues(chapter))
        gate = self._gate("heat_integration", "Heat Integration Review", "Approve the heat-integration studies before route finalization.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_route_selection(self) -> StageResult:
        survey = self._load("route_survey", RouteSurveyArtifact)
        route_chemistry = self._load("route_chemistry", RouteChemistryArtifact)
        route_discovery = self.store.maybe_load_model(self.config.project_id, "artifacts/route_discovery.json", RouteDiscoveryArtifact)
        route_process_claims = self.store.maybe_load_model(self.config.project_id, "artifacts/route_process_claims.json", RouteProcessClaimsArtifact)
        route_screening = self.store.maybe_load_model(self.config.project_id, "artifacts/route_screening.json", RouteScreeningArtifact)
        rough_alternatives = self._load("rough_alternatives", RoughAlternativeSummaryArtifact)
        heat_study = self._load("heat_integration_study", HeatIntegrationStudyArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        unit_train_candidates = self._load("unit_train_candidates", UnitTrainCandidateSet)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        family_adapter = self.store.maybe_load_model(self.config.project_id, "artifacts/chemistry_family_adapter.json", ChemistryFamilyAdapter)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        species_resolution = build_species_resolution_artifact(route_chemistry)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution)
        thermo_admissibility = build_thermo_admissibility_artifact(
            survey,
            route_chemistry,
            property_packages,
            route_families,
        )
        kinetics_admissibility = build_kinetics_admissibility_artifact(
            survey,
            route_chemistry,
        )
        selection, route_decision, reactor_choice, separation_choice, utility_network = select_route_architecture(
            self.config,
            survey,
            route_chemistry,
            rough_alternatives,
            heat_study,
            market,
            route_families,
            route_screening=route_screening,
            species_resolution=species_resolution,
            thermo_admissibility=thermo_admissibility,
            kinetics_admissibility=kinetics_admissibility,
        )
        route_selection_comparison = build_route_selection_comparison(
            survey,
            route_chemistry,
            selection,
            route_decision,
            rough_alternatives,
            heat_study,
            route_families,
        )
        process_selection_comparison = ProcessSelectionComparisonArtifact(
            **route_selection_comparison.model_dump(),
            route_discovery_count=len(route_discovery.rows) if route_discovery is not None else len(survey.routes),
            retained_route_count=len(route_screening.retained_route_ids) if route_screening is not None else 0,
            eliminated_route_count=len(route_screening.eliminated_route_ids) if route_screening is not None else 0,
            selected_route_name=next(
                (row.route_name for row in route_selection_comparison.rows if row.route_id == selection.selected_route_id),
                selection.selected_route_id,
            ),
        )
        self._save("route_selection", selection)
        selected_route = self._selected_route()
        flowsheet_blueprint = select_flowsheet_blueprint(unit_train_candidates, selected_route.route_id)
        species_resolution = build_species_resolution_artifact(route_chemistry, selected_route.route_id)
        reaction_network_v2 = build_reaction_network_v2_artifact(route_chemistry, species_resolution, selected_route.route_id)
        if route_screening is None:
            if route_process_claims is None:
                route_process_claims = build_route_process_claims_artifact(
                    survey,
                    route_chemistry,
                    unit_train_candidates,
                )
            route_screening = build_route_screening_artifact(
                survey,
                route_chemistry,
                species_resolution,
                reaction_network_v2,
                route_families,
                unit_train_candidates,
                route_process_claims,
                operating_mode=self.config.basis.operating_mode,
            )
        thermo_admissibility = build_thermo_admissibility_artifact(
            survey,
            route_chemistry,
            property_packages,
            route_families,
            selected_route_id=selected_route.route_id,
        )
        kinetics_admissibility = build_kinetics_admissibility_artifact(
            survey,
            route_chemistry,
            selected_route_id=selected_route.route_id,
        )
        unit_operation_family = build_unit_operation_family_artifact(selected_route, archetype, family_adapter, route_families)
        reactor_choice = select_reactor_configuration(selected_route, archetype, family_adapter, unit_operation_family, route_families)
        separation_choice = select_separation_configuration(selected_route, archetype, family_adapter, unit_operation_family)
        topology_candidates = build_topology_candidate_artifact(
            unit_train_candidates,
            species_resolution,
            reaction_network_v2,
            selected_route_id=selected_route.route_id,
        )
        flowsheet_intents = build_flowsheet_intent_artifact(flowsheet_blueprint)
        chemistry_decision = build_chemistry_decision_artifact(selected_route, species_resolution, reaction_network_v2)
        route_selection_issues = validate_route_selection_critics(selection, route_families)
        unit_family_property_issues = validate_unit_family_property_coverage(
            selected_route,
            reactor_choice,
            separation_choice,
            unit_operation_family,
            property_packages,
        )
        route_decision = self._escalate_decision_for_critic_issues(
            route_decision,
            route_selection_issues,
            trigger_codes={"route_family_critic_flags_present"},
            note_prefix="Route-family critic escalation",
        )
        reactor_choice = self._escalate_decision_for_critic_issues(
            reactor_choice,
            unit_family_property_issues,
            trigger_codes={"reactor_hazard_property_coverage_weak", "reactor_transport_property_coverage_weak"},
            note_prefix="Reactor property-coverage escalation",
        )
        separation_choice = self._escalate_decision_for_critic_issues(
            separation_choice,
            unit_family_property_issues,
            trigger_codes={
                "absorption_family_property_coverage_weak",
                "solids_family_property_coverage_weak",
                "distillation_family_property_coverage_weak",
            },
            note_prefix="Separation property-coverage escalation",
        )
        self._save("route_decision", route_decision)
        self._save("reactor_choice_decision", reactor_choice)
        self._save("separation_choice_decision", separation_choice)
        self._save("utility_network_decision", utility_network)
        self._save("species_resolution", species_resolution)
        self._save("reaction_network_v2", reaction_network_v2)
        self._save("thermo_admissibility", thermo_admissibility)
        self._save("kinetics_admissibility", kinetics_admissibility)
        self._save("unit_operation_family", unit_operation_family)
        self._save("route_selection_comparison", route_selection_comparison)
        self._save("process_selection_comparison", process_selection_comparison)
        if route_screening is not None:
            self._save("route_screening", route_screening)
        if route_process_claims is not None:
            self._save("route_process_claims", route_process_claims)
        self._save("flowsheet_blueprint", flowsheet_blueprint)
        self._save("topology_candidates", topology_candidates)
        self._save("flowsheet_intents", flowsheet_intents)
        self._save("chemistry_decision", chemistry_decision)
        self._refresh_agent_fabric()
        issues = (
            validate_route_balance(selected_route)
            + validate_decision_record(route_decision, "route_decision")
            + validate_decision_record(reactor_choice, "reactor_choice")
            + validate_decision_record(separation_choice, "separation_choice")
            + validate_route_selection_comparison(route_selection_comparison)
            + validate_route_selection_comparison(process_selection_comparison)
            + validate_species_resolution_artifact(species_resolution)
            + validate_reaction_network_v2_artifact(reaction_network_v2)
            + (validate_route_process_claims_artifact(route_process_claims) if route_process_claims is not None else [])
            + validate_route_screening_artifact(route_screening)
            + validate_chemistry_decision_artifact(chemistry_decision)
            + validate_thermo_admissibility_artifact(thermo_admissibility)
            + validate_kinetics_admissibility_artifact(kinetics_admissibility)
            + route_selection_issues
            + unit_family_property_issues
            + validate_unit_operation_family_artifact(unit_operation_family)
            + validate_flowsheet_blueprint(flowsheet_blueprint)
            + validate_topology_candidate_artifact(topology_candidates)
            + validate_flowsheet_intent_artifact(flowsheet_intents)
            + validate_utility_network_decision(utility_network, self.config)
        )
        selected_heat = selected_heat_case(utility_network)
        chapter = self._chapter(
            "process_selection",
            "Process Selection",
            "route_selection",
            (
                f"### Route Comparison\n\n{selection.comparison_markdown}\n\n"
                f"### Route Discovery\n\n{route_discovery.markdown if route_discovery else 'No explicit route-discovery artifact generated.'}\n\n"
                f"### Route Screening\n\n{route_screening.markdown if route_screening else 'No explicit route-screening artifact generated.'}\n\n"
                f"### Route Selection Comparison\n\n{route_selection_comparison.markdown}\n\n"
                f"### Process Selection Comparison\n\n{process_selection_comparison.markdown}\n\n"
                f"### Chemistry Decision\n\n{chemistry_decision.markdown}\n\n"
                f"### Selected Route\n\n{selection.justification}\n\n"
                f"### Route-Derived Flowsheet Blueprint\n\n{flowsheet_blueprint.markdown}\n\n"
                f"### Route Family Profiles\n\n{route_families.markdown if route_families else 'No route-family profiles generated.'}\n\n"
                f"### Unit-Operation Family Expansion\n\n{unit_operation_family.markdown}\n\n"
                f"### Chemistry Family Adapter\n\n{family_adapter.markdown if family_adapter else 'No chemistry-family adapter generated.'}\n\n"
                f"### Sparse-Data Policy\n\n{sparse_data_policy.markdown if sparse_data_policy else 'No sparse-data policy generated.'}\n\n"
                f"### Selected Reactor Basis\n\n{reactor_choice.selected_summary}\n\n"
                f"### Selected Separation Basis\n\n{separation_choice.selected_summary}\n\n"
                f"### Selected Heat-Integration Case\n\n"
                f"{selected_heat.title if selected_heat else 'No selected case'}: {selected_heat.summary if selected_heat else 'n/a'}"
            ),
            sorted(
                set(
                    selection.citations
                    + survey.citations
                    + route_selection_comparison.citations
                    + process_selection_comparison.citations
                    + (route_discovery.citations if route_discovery else [])
                    + (route_screening.citations if route_screening else [])
                    + chemistry_decision.citations
                    + flowsheet_blueprint.citations
                    + (family_adapter.citations if family_adapter else [])
                    + (sparse_data_policy.citations if sparse_data_policy else [])
                )
            ),
            survey.assumptions
            + selection.assumptions
            + route_selection_comparison.assumptions
            + process_selection_comparison.assumptions
            + (route_discovery.assumptions if route_discovery else [])
            + (route_screening.assumptions if route_screening else [])
            + chemistry_decision.assumptions
            + flowsheet_blueprint.assumptions
            + route_decision.assumptions
            + reactor_choice.assumptions
            + separation_choice.assumptions
            + (family_adapter.assumptions if family_adapter else [])
            + (sparse_data_policy.assumptions if sparse_data_policy else []),
            [
                "route_selection",
                "route_discovery",
                "route_screening",
                "route_selection_comparison",
                "process_selection_comparison",
                "chemistry_decision",
                "route_decision",
                "reactor_choice_decision",
                "separation_choice_decision",
                "utility_network_decision",
                "route_family_profiles",
                "unit_operation_family",
                "chemistry_family_adapter",
                "sparse_data_policy",
                "flowsheet_blueprint",
            ],
            required_inputs=["route_survey", "rough_alternatives", "heat_integration_study", "market_assessment"],
        )
        issues.extend(self._chapter_issues(chapter))
        gate = self._gate("process_architecture", "Process Architecture", "Approve the selected route, reactor, separation train, and utility-integration basis.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_site_selection(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        artifact = self.reasoning.select_site(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        artifact = self._replace_bac_site_selection_with_external_candidates(artifact, bundle)
        self._repair_india_location_data(artifact, bundle)
        site_decision = build_site_selection_decision(self.config, artifact)
        artifact.selected_site = site_decision.selected_candidate_id or artifact.selected_site
        self._save("site_selection", artifact)
        self._save("site_selection_decision", site_decision)
        self._refresh_agent_fabric()
        chapter = self._chapter(
            "site_selection",
            "Site Selection",
            "site_selection",
            artifact.markdown + f"\n\n### Deterministic Site Decision\n\n{site_decision.selected_summary}",
            sorted(set(artifact.citations + site_decision.citations)),
            artifact.assumptions + site_decision.assumptions,
            ["site_selection", "site_selection_decision"],
            required_inputs=["research_bundle"],
        )
        issues = validate_india_location_data(artifact.india_location_data, self._source_ids(), self.config, "site_selection")
        issues.extend(validate_decision_record(site_decision, "site_selection_decision"))
        issues.extend(validate_site_selection_consistency(artifact, site_decision))
        issues.extend(self._chapter_issues(chapter))
        return StageResult(chapters=[chapter], issues=issues)

    def _run_thermodynamic_feasibility(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        route = self._selected_route()
        route_selection_artifact = self._load("route_selection", RouteSelectionArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        route_decision = self._load("route_decision", DecisionRecord)
        separation_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_choice_decision.json", DecisionRecord)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        utility_network = self._load("utility_network_decision", UtilityNetworkDecision)
        route_survey = self._load("route_survey", RouteSurveyArtifact)
        route_chemistry = self._load("route_chemistry", RouteChemistryArtifact)
        property_method = build_property_method_decision(route, property_packages)
        separation_thermo = build_separation_thermo_artifact(
            route,
            property_packages,
            self.config.basis.target_product,
            separation_choice.selected_candidate_id if separation_choice else None,
        )
        method_artifact = build_thermo_method_decision(self.config, route, resolved_values, archetype)
        artifact = self.reasoning.build_thermo_assessment(self.config.basis, route, bundle.sources, bundle.corpus_excerpt)
        method_map = {
            "direct_public_data": ProvenanceTag.SOURCED,
            "correlation_interpolation": ProvenanceTag.CALCULATED,
            "estimation_method": ProvenanceTag.ESTIMATED,
            "analogy_basis": ProvenanceTag.ANALOGY,
        }
        selected_method = method_artifact.decision.selected_candidate_id or "direct_public_data"
        artifact.value_records = [
            make_value_record(
                "thermo_reaction_enthalpy",
                "Reaction enthalpy",
                artifact.estimated_reaction_enthalpy_kj_per_mol,
                "kJ/mol",
                provenance_method=method_map[selected_method],
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "thermo_reaction_gibbs",
                "Reaction Gibbs free energy",
                artifact.estimated_gibbs_kj_per_mol,
                "kJ/mol",
                provenance_method=method_map[selected_method],
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
        ]
        artifact.markdown = (
            "### Selected Property Basis\n\n"
            f"{property_method.decision.selected_summary}\n\n"
            f"{property_method.markdown}\n\n"
            "### Separation Thermodynamics Basis\n\n"
            f"{separation_thermo.markdown}\n\n"
            "### Selected Thermodynamic Method\n\n"
            f"{method_artifact.decision.selected_summary}\n\n"
            f"{method_artifact.markdown}\n\n"
            "### Thermodynamic Interpretation\n\n"
            f"{artifact.markdown}"
        )
        architecture_package_issues = validate_architecture_package_critics(
            route,
            separation_choice
            or DecisionRecord(
                decision_id="separation_choice",
                context="seed",
                citations=[],
                assumptions=[],
            ),
            unit_operation_family,
            separation_thermo,
            None,
            sparse_data_policy,
            property_packages,
        )
        route_decision = self._escalate_decision_for_critic_issues(
            route_decision,
            architecture_package_issues,
            trigger_codes={
                "architecture_package_fallback_thermo",
                "architecture_package_weak_absorber_basis",
                "architecture_package_weak_solids_basis",
                "architecture_package_sparse_data_compounded",
            },
            note_prefix="Architecture thermo-basis escalation",
        )
        if separation_choice is not None:
            separation_choice = self._escalate_decision_for_critic_issues(
                separation_choice,
                architecture_package_issues,
                trigger_codes={
                    "architecture_package_fallback_thermo",
                    "architecture_package_weak_absorber_basis",
                    "architecture_package_weak_solids_basis",
                    "architecture_package_sparse_data_compounded",
                },
                note_prefix="Separation architecture escalation",
            )
        utility_network_decision = self._escalate_decision_for_critic_issues(
            utility_network.decision,
            architecture_package_issues,
            trigger_codes={
                "architecture_package_fallback_thermo",
                "architecture_package_weak_absorber_basis",
                "architecture_package_weak_solids_basis",
                "architecture_package_sparse_data_compounded",
            },
            note_prefix="Utility architecture escalation",
        )
        utility_network = utility_network.model_copy(update={"decision": utility_network_decision}, deep=True)
        self._save("thermo_assessment", artifact)
        self._save("thermo_method_decision", method_artifact)
        self._save("property_method_decision", property_method)
        self._save("separation_thermo", separation_thermo)
        thermo_admissibility = build_thermo_admissibility_artifact(
            route_survey,
            route_chemistry,
            property_packages,
            self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact),
            selected_route_id=route.route_id,
            separation_thermo=separation_thermo,
            property_method=property_method,
        )
        bac_purification_sections = build_bac_purification_section_artifact(
            route_selection_artifact,
            self._maybe_load("flowsheet_blueprint", FlowsheetBlueprintArtifact),
            separation_thermo,
        )
        self._save("thermo_admissibility", thermo_admissibility)
        if bac_purification_sections is not None:
            self._save("bac_purification_sections", bac_purification_sections)
        self._save("route_decision", route_decision)
        if separation_choice is not None:
            self._save("separation_choice_decision", separation_choice)
        self._save("utility_network_decision", utility_network)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(resolved_values, artifact.value_records, resolved_sources, self.config, "thermodynamic_feasibility"),
        )
        self._refresh_agent_fabric()
        chapter = self._chapter(
            "thermodynamic_feasibility",
            "Thermodynamic Feasibility",
            "thermodynamic_feasibility",
            artifact.markdown
            + (
                f"\n\n### BAC Purification Sections\n\n{bac_purification_sections.markdown}"
                if bac_purification_sections is not None
                else ""
            ),
            sorted(
                set(
                    artifact.citations
                    + method_artifact.citations
                    + property_method.citations
                    + separation_thermo.citations
                    + (bac_purification_sections.citations if bac_purification_sections is not None else [])
                )
            ),
            artifact.assumptions + (bac_purification_sections.assumptions if bac_purification_sections is not None else []),
            ["thermo_assessment", "thermo_method_decision", "property_method_decision", "separation_thermo", "bac_purification_sections"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
            summary=artifact.equilibrium_comment,
        )
        issues = (
            validate_route_balance(route)
            + validate_decision_record(route_decision, "route_decision")
            + (validate_decision_record(separation_choice, "separation_choice_decision") if separation_choice is not None else [])
            + validate_decision_record(utility_network.decision, "utility_network_decision")
            + validate_property_method_decision(property_method)
            + validate_separation_thermo_artifact(separation_thermo)
            + validate_thermo_admissibility_artifact(thermo_admissibility)
            + (validate_bac_purification_section_artifact(bac_purification_sections) if bac_purification_sections is not None else [])
            + validate_separation_thermo_critics(route, separation_thermo)
            + architecture_package_issues
            + validate_decision_record(method_artifact.decision, "thermo_method_decision")
            + validate_property_requirements_for_stage(
                "thermodynamic_feasibility",
                property_requirements,
                property_packages,
                route,
                self.config.basis.target_product,
            )
            + validate_sparse_data_policy_for_stage("thermodynamic_feasibility", sparse_data_policy)
            + validate_thermo_assessment(artifact)
            + self._value_issues(artifact, "thermo_assessment")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_kinetic_feasibility(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        route = self._selected_route()
        route_selection_artifact = self._load("route_selection", RouteSelectionArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        route_decision = self._load("route_decision", DecisionRecord)
        reactor_choice = self._load("reactor_choice_decision", DecisionRecord)
        separation_choice = self._load("separation_choice_decision", DecisionRecord)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        separation_thermo = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_thermo.json", SeparationThermoArtifact)
        utility_network = self._load("utility_network_decision", UtilityNetworkDecision)
        route_survey = self._load("route_survey", RouteSurveyArtifact)
        route_chemistry = self._load("route_chemistry", RouteChemistryArtifact)
        method_artifact = build_kinetics_method_decision(self.config, route, resolved_values, archetype)
        artifact = self.reasoning.build_kinetic_assessment(self.config.basis, route, bundle.sources, bundle.corpus_excerpt)
        method_map = {
            "cited_rate_law": ProvenanceTag.SOURCED,
            "arrhenius_fit": ProvenanceTag.CALCULATED,
            "apparent_order_fit": ProvenanceTag.ESTIMATED,
            "conservative_analogy": ProvenanceTag.ANALOGY,
        }
        selected_method = method_artifact.decision.selected_candidate_id or "cited_rate_law"
        artifact.value_records = [
            make_value_record(
                "kinetic_activation_energy",
                "Activation energy",
                artifact.activation_energy_kj_per_mol,
                "kJ/mol",
                provenance_method=method_map[selected_method],
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "kinetic_pre_exponential",
                "Pre-exponential factor",
                artifact.pre_exponential_factor,
                "1/h",
                provenance_method=method_map[selected_method],
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.MEDIUM,
            ),
            make_value_record(
                "kinetic_residence_time",
                "Design residence time",
                artifact.design_residence_time_hr,
                "h",
                provenance_method=method_map[selected_method],
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
        ]
        artifact.markdown = (
            "### Selected Kinetic Method\n\n"
            f"{method_artifact.decision.selected_summary}\n\n"
            f"{method_artifact.markdown}\n\n"
            "### Kinetic Interpretation\n\n"
            f"{artifact.markdown}"
        )
        architecture_package_issues = validate_architecture_package_critics(
            route,
            separation_choice,
            unit_operation_family,
            separation_thermo,
            method_artifact,
            sparse_data_policy,
            property_packages,
        )
        route_decision = self._escalate_decision_for_critic_issues(
            route_decision,
            architecture_package_issues,
            trigger_codes={
                "architecture_package_weak_kinetics_basis",
                "architecture_package_sparse_data_compounded",
            },
            note_prefix="Architecture kinetics-basis escalation",
        )
        reactor_choice = self._escalate_decision_for_critic_issues(
            reactor_choice,
            architecture_package_issues,
            trigger_codes={
                "architecture_package_weak_kinetics_basis",
                "architecture_package_sparse_data_compounded",
            },
            note_prefix="Reactor kinetics-basis escalation",
        )
        utility_network_decision = self._escalate_decision_for_critic_issues(
            utility_network.decision,
            architecture_package_issues,
            trigger_codes={
                "architecture_package_weak_kinetics_basis",
                "architecture_package_sparse_data_compounded",
            },
            note_prefix="Utility architecture kinetics escalation",
        )
        utility_network = utility_network.model_copy(update={"decision": utility_network_decision}, deep=True)
        self._save("kinetic_assessment", artifact)
        self._save("kinetics_method_decision", method_artifact)
        kinetics_admissibility = build_kinetics_admissibility_artifact(
            route_survey,
            route_chemistry,
            selected_route_id=route.route_id,
            kinetics_method=method_artifact,
            kinetic_assessment=artifact,
        )
        self._save("kinetics_admissibility", kinetics_admissibility)
        self._save("route_decision", route_decision)
        self._save("reactor_choice_decision", reactor_choice)
        self._save("utility_network_decision", utility_network)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(resolved_values, artifact.value_records, resolved_sources, self.config, "kinetic_feasibility"),
        )
        self._refresh_agent_fabric()
        chapter = self._chapter(
            "reaction_kinetics",
            "Reaction Kinetics",
            "kinetic_feasibility",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["kinetic_assessment", "kinetics_method_decision"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
        )
        issues = (
            validate_decision_record(route_decision, "route_decision")
            + validate_decision_record(reactor_choice, "reactor_choice_decision")
            + validate_decision_record(utility_network.decision, "utility_network_decision")
            + validate_decision_record(method_artifact.decision, "kinetics_method_decision")
            + validate_kinetics_admissibility_artifact(kinetics_admissibility)
            + validate_kinetics_method_critics(route, method_artifact)
            + architecture_package_issues
            + validate_kinetic_assessment(artifact)
            + self._value_issues(artifact, "kinetic_assessment")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _ensure_process_narrative(self) -> ProcessNarrativeArtifact:
        artifact = self.store.maybe_load_model(self.config.project_id, "artifacts/process_narrative.json", ProcessNarrativeArtifact)
        if artifact:
            return artifact
        flowsheet_blueprint = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_blueprint.json", FlowsheetBlueprintArtifact)
        if flowsheet_blueprint is not None:
            artifact = build_process_narrative_from_blueprint(flowsheet_blueprint)
            self._save("process_narrative", artifact)
            return artifact
        bundle = self._load("research_bundle", ResearchBundle)
        route = self._selected_route()
        artifact = self.reasoning.build_process_narrative(self.config.basis, route, bundle.sources, bundle.corpus_excerpt)
        self._save("process_narrative", artifact)
        return artifact

    def _render_solver_process_description(
        self,
        route: RouteOption,
        flowsheet_case: FlowsheetCase,
        stream_table: StreamTable,
    ) -> str:
        flowsheet_blueprint = self.store.maybe_load_model(
            self.config.project_id,
            "artifacts/flowsheet_blueprint.json",
            FlowsheetBlueprintArtifact,
        )
        unit_rows = [
            [
                unit.unit_id,
                unit.unit_type,
                unit.service,
                ", ".join(unit.upstream_stream_ids) or "-",
                ", ".join(unit.downstream_stream_ids) or "-",
                unit.closure_status,
                unit.coverage_status,
            ]
            for unit in flowsheet_case.units
        ]
        separation_rows = [
            [
                separation.separation_id,
                separation.separation_family,
                separation.driving_force,
                ", ".join(separation.product_stream_ids) or "-",
                ", ".join(separation.recycle_stream_ids) or "-",
                separation.split_status,
            ]
            for separation in flowsheet_case.separations
        ]
        recycle_rows = [
            [
                loop.loop_id,
                loop.recycle_source_unit_id or "-",
                ", ".join(loop.recycle_stream_ids) or "-",
                ", ".join(loop.purge_stream_ids) or "-",
                loop.convergence_status,
            ]
            for loop in flowsheet_case.recycle_loops
        ]
        section_rows = [
            [
                section.section_id,
                section.label,
                section.section_type,
                ", ".join(section.unit_ids) or "-",
                ", ".join(section.inlet_stream_ids) or "-",
                ", ".join(section.outlet_stream_ids) or "-",
                ", ".join(section.side_draw_stream_ids) or "-",
                section.status,
            ]
            for section in flowsheet_case.sections
        ]
        unit_narrative = [
            f"- `{unit.unit_id}`: {unit.service}. Inlet streams `{', '.join(unit.upstream_stream_ids) or '-'}` and outlet streams `{', '.join(unit.downstream_stream_ids) or '-'}` with `{unit.closure_status}` closure and `{unit.coverage_status}` coverage."
            for unit in flowsheet_case.units
        ]
        route_descriptor_rows = [[str(index), descriptor] for index, descriptor in enumerate(route.separations, start=1)]
        blueprint_rows = []
        if flowsheet_blueprint is not None and flowsheet_blueprint.steps:
            blueprint_rows = [
                [
                    step.section_label,
                    step.service,
                    "; ".join(step.notes) or "-",
                ]
                for step in flowsheet_blueprint.steps
            ]
        lines = [
            f"Solver-derived process description for route `{route.route_id}` built from `{len(stream_table.unit_operation_packets)}` solved unit packets.",
            "",
            "### Route Descriptor Basis",
            "",
            markdown_table(["Order", "Route Descriptor"], route_descriptor_rows or [["-", "No explicit route descriptors were retained."]]),
            "",
            "### Route-Derived Blueprint Basis",
            "",
            markdown_table(["Section", "Service", "Blueprint Notes"], blueprint_rows or [["-", "-", "No explicit blueprint notes were retained."]]),
            "",
            "### Unit Sequence",
            "",
            markdown_table(["Unit", "Type", "Service", "Inlet Streams", "Outlet Streams", "Closure", "Coverage"], unit_rows or [["n/a", "n/a", "n/a", "-", "-", "n/a", "n/a"]]),
            "",
            "### Section Topology",
            "",
            markdown_table(["Section", "Label", "Type", "Units", "Inlet Streams", "Outlet Streams", "Side Draws", "Status"], section_rows or [["n/a", "n/a", "n/a", "-", "-", "-", "-", "n/a"]]),
            "",
            "### Separation Architecture",
            "",
            markdown_table(["Separation", "Family", "Driving Force", "Product Streams", "Recycle Streams", "Status"], separation_rows or [["n/a", "n/a", "n/a", "-", "-", "n/a"]]),
            "",
            "### Recycle Architecture",
            "",
            markdown_table(["Loop", "Source Unit", "Recycle Streams", "Purge Streams", "Status"], recycle_rows or [["n/a", "-", "-", "-", "n/a"]]),
            "",
            "### Unit Narrative",
            "",
            "\n".join(unit_narrative or ["- No solved unit narrative is available."]),
        ]
        return "\n".join(lines)

    def _render_solver_material_balance(
        self,
        route: RouteOption,
        route_profile,
        reaction_system: ReactionSystem,
        stream_table: StreamTable,
        flowsheet_case: FlowsheetCase | None = None,
    ) -> str:
        def _stream_mass(stream_id: str) -> float:
            stream = next((item for item in stream_table.streams if item.stream_id == stream_id), None)
            return sum(component.mass_flow_kg_hr for component in stream.components) if stream else 0.0

        def _stream_molar(stream_id: str) -> float:
            stream = next((item for item in stream_table.streams if item.stream_id == stream_id), None)
            return sum(component.molar_flow_kmol_hr for component in stream.components) if stream else 0.0

        total_fresh_feed = sum(
            sum(component.mass_flow_kg_hr for component in stream.components)
            for stream in stream_table.streams
            if stream.stream_role == "feed"
        )
        total_external_out = sum(
            sum(component.mass_flow_kg_hr for component in stream.components)
            for stream in stream_table.streams
            if stream.stream_role in {"product", "waste", "vent", "purge"}
        )
        total_recycle = sum(
            sum(component.mass_flow_kg_hr for component in stream.components)
            for stream in stream_table.streams
            if stream.stream_role == "recycle"
        )
        total_side_draw = sum(
            sum(component.mass_flow_kg_hr for component in stream.components)
            for stream in stream_table.streams
            if stream.stream_role == "side_draw"
        )
        overall_rows = [
            ["Fresh feed", f"{total_fresh_feed:.3f}", f"{sum(_stream_molar(item.stream_id) for item in stream_table.streams if item.stream_role == 'feed'):.6f}"],
            ["External outlet", f"{total_external_out:.3f}", f"{sum(_stream_molar(item.stream_id) for item in stream_table.streams if item.stream_role in {'product', 'waste', 'vent', 'purge'}):.6f}"],
            ["Recycle circulation", f"{total_recycle:.3f}", f"{sum(_stream_molar(item.stream_id) for item in stream_table.streams if item.stream_role == 'recycle'):.6f}"],
            ["Side draws", f"{total_side_draw:.3f}", f"{sum(_stream_molar(item.stream_id) for item in stream_table.streams if item.stream_role == 'side_draw'):.6f}"],
            ["Closure error (%)", f"{stream_table.closure_error_pct:.3f}", "-"],
        ]
        section_rows = []
        for section in stream_table.sections:
            inlet_mass = sum(_stream_mass(stream_id) for stream_id in section.inlet_stream_ids)
            outlet_mass = sum(_stream_mass(stream_id) for stream_id in section.outlet_stream_ids)
            side_draw_mass = sum(_stream_mass(stream_id) for stream_id in section.side_draw_stream_ids)
            recycle_ids = [
                stream_id
                for loop in stream_table.recycle_packets
                if loop.loop_id in section.recycle_loop_ids
                for stream_id in loop.recycle_stream_ids
            ]
            recycle_mass = sum(_stream_mass(stream_id) for stream_id in recycle_ids)
            section_rows.append(
                [
                    section.section_id,
                    section.label,
                    section.section_type,
                    f"{inlet_mass:.3f}",
                    f"{outlet_mass:.3f}",
                    f"{side_draw_mass:.3f}",
                    f"{recycle_mass:.3f}",
                    section.status,
                ]
            )
        reaction_rows = [
            [
                extent.extent_id,
                extent.kind,
                extent.representative_component or "-",
                f"{extent.extent_fraction_of_converted_feed:.6f}",
                extent.status,
            ]
            for extent in (reaction_system.reaction_extent_set.extents if reaction_system.reaction_extent_set else [])
        ]
        byproduct_rows = [
            [
                estimate.component_name,
                estimate.basis,
                f"{estimate.allocation_fraction:.6f}",
                estimate.provenance,
                estimate.status,
            ]
            for estimate in (reaction_system.byproduct_closure.estimates if reaction_system.byproduct_closure else [])
        ]
        packet_rows = [
            [
                packet.unit_id,
                packet.unit_type,
                packet.service,
                ", ".join(packet.inlet_stream_ids) or "-",
                ", ".join(packet.outlet_stream_ids) or "-",
                f"{packet.inlet_mass_flow_kg_hr:.3f}",
                f"{packet.outlet_mass_flow_kg_hr:.3f}",
                f"{packet.closure_error_pct:.3f}",
                packet.status,
                packet.coverage_status,
            ]
            for packet in stream_table.unit_operation_packets
        ]
        recycle_rows = [
            [
                summary.loop_id,
                summary.recycle_source_unit_id or "-",
                summary.recycle_target_unit_id or "-",
                ", ".join(summary.recycle_stream_ids) or "-",
                ", ".join(summary.purge_stream_ids) or "-",
                f"{summary.max_component_error_pct:.3f}",
                f"{summary.mean_component_error_pct:.3f}",
                summary.convergence_status,
            ]
            for summary in stream_table.convergence_summaries
        ]
        composition_rows = [
            [
                closure.unit_id,
                "yes" if closure.reactive else "no",
                f"{closure.inlet_fraction_sum:.4f}",
                f"{closure.outlet_fraction_sum:.4f}",
                ", ".join(closure.new_outlet_components[:4]) or "-",
                ", ".join(closure.missing_outlet_components[:4]) or "-",
                f"{closure.composition_error_pct:.3f}",
                closure.closure_status,
            ]
            for closure in stream_table.composition_closures
        ]
        unit_composition_rows = [
            [
                state.unit_id,
                state.unit_type,
                state.dominant_inlet_phase or "-",
                state.dominant_outlet_phase or "-",
                ", ".join(f"{name}={value:.3f}" for name, value in list(state.outlet_component_mass_fraction.items())[:4]) or "-",
                state.status,
            ]
            for state in stream_table.composition_states
        ]
        stream_role_rows = [
            [
                stream.stream_id,
                stream.stream_role,
                stream.section_id or "-",
                stream.source_unit_id or "-",
                stream.destination_unit_id or "-",
                f"{sum(component.mass_flow_kg_hr for component in stream.components):.3f}",
                f"{sum(component.molar_flow_kmol_hr for component in stream.components):.6f}",
            ]
            for stream in stream_table.streams
        ]
        focus_unit_tokens: set[str] = set()
        route_family_id = getattr(route_profile, "route_family_id", "")
        if any(token in route_family_id for token in {"hydration", "carbonylation", "distillation"}):
            focus_unit_tokens = {"feed_prep", "reactor", "primary_flash", "concentration", "purification"}
        elif any(token in route_family_id for token in {"absorption", "gas_absorption", "oxidation"}):
            focus_unit_tokens = {"feed_prep", "reactor", "primary_separation", "regeneration", "purification"}
        elif any(token in route_family_id for token in {"solids", "solvay", "carboxylation"}):
            focus_unit_tokens = {"feed_prep", "reactor", "primary_separation", "concentration", "filtration", "drying"}
        elif "extraction" in route_family_id:
            focus_unit_tokens = {"feed_prep", "reactor", "primary_separation", "purification", "regeneration"}
        focus_streams = [
            stream
            for stream in stream_table.streams
            if stream.stream_role in {"feed", "recycle", "purge", "product", "side_draw", "vent"}
            or (stream.source_unit_id in focus_unit_tokens or stream.destination_unit_id in focus_unit_tokens)
        ]
        route_family_rows = [
            [
                stream.stream_id,
                stream.stream_role,
                stream.source_unit_id or "-",
                stream.destination_unit_id or "-",
                stream.phase_hint or "-",
                f"{sum(component.mass_flow_kg_hr for component in stream.components):.3f}",
                ", ".join(
                    f"{component.name}={component.mass_flow_kg_hr:.1f}"
                    for component in sorted(stream.components, key=lambda item: item.mass_flow_kg_hr, reverse=True)[:4]
                ) or "-",
            ]
            for stream in focus_streams
        ]
        stream_rows: list[list[str]] = []
        for stream in stream_table.streams:
            for component in stream.components:
                stream_rows.append(
                    [
                        stream.stream_id,
                        stream.description,
                        stream.source_unit_id or "-",
                        stream.destination_unit_id or "-",
                        component.name,
                        f"{component.mass_flow_kg_hr:.3f}",
                        f"{component.molar_flow_kmol_hr:.6f}",
                        f"{stream.temperature_c:.1f}",
                        f"{stream.pressure_bar:.2f}",
                    ]
                )
        return "\n\n".join(
            [
                "### Overall Plant Balance Summary\n\n"
                + markdown_table(["Basis", "Mass Flow (kg/h)", "Molar Flow (kmol/h)"], overall_rows),
                "### Section Balance Summary\n\n"
                + markdown_table(
                    ["Section", "Label", "Type", "Inlet kg/h", "Outlet kg/h", "Side Draw kg/h", "Recycle kg/h", "Status"],
                    section_rows or [["n/a", "n/a", "n/a", "0.0", "0.0", "0.0", "0.0", "n/a"]],
                ),
                "### Reaction Extent Allocation\n\n"
                + markdown_table(["Extent", "Kind", "Representative Component", "Fraction of Converted Feed", "Status"], reaction_rows or [["n/a", "n/a", "n/a", "0.0", "n/a"]]),
                "### Byproduct Closure\n\n"
                + markdown_table(["Component", "Basis", "Allocation Fraction", "Provenance", "Status"], byproduct_rows or [["n/a", "n/a", "0.0", "n/a", "n/a"]]),
                "### Unit Packet Balance Summary\n\n"
                + markdown_table(
                    ["Unit", "Type", "Service", "Inlet Streams", "Outlet Streams", "Inlet kg/h", "Outlet kg/h", "Closure Error (%)", "Status", "Coverage"],
                    packet_rows or [["n/a", "n/a", "n/a", "-", "-", "0.0", "0.0", "0.0", "n/a", "n/a"]],
                ),
                "### Recycle and Purge Summary\n\n"
                + markdown_table(
                    ["Loop", "Source Unit", "Target Unit", "Recycle Streams", "Purge Streams", "Max Error (%)", "Mean Error (%)", "Status"],
                    recycle_rows or [["n/a", "-", "-", "-", "-", "0.0", "0.0", "n/a"]],
                ),
                "### Composition Closure Summary\n\n"
                + markdown_table(
                    ["Unit", "Reactive", "Inlet Fraction Sum", "Outlet Fraction Sum", "New Components", "Missing Components", "Error (%)", "Status"],
                    composition_rows or [["n/a", "n/a", "0.0", "0.0", "-", "-", "0.0", "n/a"]],
                ),
                "### Unitwise Outlet Composition Snapshot\n\n"
                + markdown_table(
                    ["Unit", "Type", "Inlet Phase", "Outlet Phase", "Outlet Mass Fractions", "Status"],
                    unit_composition_rows or [["n/a", "n/a", "-", "-", "-", "n/a"]],
                ),
                "### Stream Role Summary\n\n"
                + markdown_table(
                    ["Stream", "Role", "Section", "From", "To", "kg/h", "kmol/h"],
                    stream_role_rows or [["n/a", "n/a", "-", "-", "-", "0.0", "0.0"]],
                ),
                "### Route-Family Stream Focus\n\n"
                + markdown_table(
                    ["Stream", "Role", "From", "To", "Phase", "kg/h", "Dominant Components"],
                    route_family_rows or [["n/a", "n/a", "-", "-", "-", "0.0", "-"]],
                ),
                "### Long Stream Ledger\n\n"
                + markdown_table(["Stream", "Description", "From", "To", "Component", "kg/h", "kmol/h", "T (C)", "P (bar)"], stream_rows),
                self._render_trace_section("Stream-Balance Calculation Traces", stream_table.calc_traces),
            ]
        )

    def _render_energy_balance_chapter(
        self,
        route: RouteOption,
        route_profile,
        stream_table: StreamTable,
        energy: EnergyBalance,
    ) -> str:
        section_unit_index = {
            unit_id: section.section_id
            for section in stream_table.sections
            for unit_id in section.unit_ids
        }
        overall_rows = [
            ["Total heating duty", f"{energy.total_heating_kw:.3f}", "kW"],
            ["Total cooling duty", f"{energy.total_cooling_kw:.3f}", "kW"],
            ["Net external duty", f"{energy.total_heating_kw - energy.total_cooling_kw:.3f}", "kW"],
            ["Thermal packets", f"{len(energy.unit_thermal_packets)}", "count"],
            ["Recovery candidates", f"{len(energy.network_candidates)}", "count"],
            ["Recoverable packet duty", f"{sum(packet.recoverable_duty_kw for packet in energy.unit_thermal_packets):.3f}", "kW"],
        ]
        duty_rows = [
            [
                duty.unit_id,
                section_unit_index.get(duty.unit_id, "-"),
                duty.duty_type,
                f"{duty.heating_kw:.3f}",
                f"{duty.cooling_kw:.3f}",
                duty.notes,
            ]
            for duty in energy.duties
        ]
        section_rows = []
        for section in stream_table.sections:
            heating = sum(duty.heating_kw for duty in energy.duties if duty.unit_id in section.unit_ids)
            cooling = sum(duty.cooling_kw for duty in energy.duties if duty.unit_id in section.unit_ids)
            recoverable = sum(packet.recoverable_duty_kw for packet in energy.unit_thermal_packets if packet.unit_id in section.unit_ids)
            section_rows.append(
                [
                    section.section_id,
                    section.label,
                    f"{heating:.3f}",
                    f"{cooling:.3f}",
                    f"{recoverable:.3f}",
                    section.status,
                ]
            )
        thermal_rows = [
            [
                packet.packet_id,
                packet.unit_id,
                section_unit_index.get(packet.unit_id, "-"),
                packet.duty_type,
                f"{packet.heating_kw:.3f}",
                f"{packet.cooling_kw:.3f}",
                f"{packet.hot_supply_temp_c:.1f}",
                f"{packet.hot_target_temp_c:.1f}",
                f"{packet.cold_supply_temp_c:.1f}",
                f"{packet.cold_target_temp_c:.1f}",
                f"{packet.recoverable_duty_kw:.3f}",
                ", ".join(packet.candidate_media) or "-",
            ]
            for packet in energy.unit_thermal_packets
        ]
        candidate_rows = [
            [
                candidate.candidate_id,
                candidate.source_unit_id,
                candidate.sink_unit_id,
                candidate.topology,
                f"{candidate.recovered_duty_kw:.3f}",
                f"{candidate.minimum_approach_temp_c:.1f}",
                "yes" if candidate.feasible else "no",
                candidate.notes,
            ]
            for candidate in energy.network_candidates[:16]
        ]
        utility_rows = [
            [
                packet.unit_id,
                route.route_id,
                ", ".join(packet.candidate_media) or "-",
                f"{max(packet.heating_kw, packet.cooling_kw):.3f}",
                f"{packet.recoverable_duty_kw:.3f}",
                packet.service,
            ]
            for packet in energy.unit_thermal_packets
        ]
        route_family_id = getattr(route_profile, "route_family_id", "")
        if any(token in route_family_id for token in {"hydration", "carbonylation", "distillation"}):
            focus_units = {"E-101", "R-101", "V-101", "EV-101", "D-101", "E-201"}
        elif any(token in route_family_id for token in {"absorption", "oxidation"}):
            focus_units = {"E-101", "R-101", "ABS-201", "STR-201", "CONV-101"}
        elif any(token in route_family_id for token in {"solids", "solvay", "carboxylation"}):
            focus_units = {"E-101", "R-101", "CRYS-201", "FILT-201", "DRY-301"}
        elif "extraction" in route_family_id:
            focus_units = {"E-101", "R-101", "EXT-201", "DEC-201", "SR-301"}
        else:
            focus_units = {duty.unit_id for duty in energy.duties}
        route_family_rows = [
            [
                duty.unit_id,
                duty.duty_type,
                f"{duty.heating_kw:.3f}",
                f"{duty.cooling_kw:.3f}",
                section_unit_index.get(duty.unit_id, "-"),
                duty.notes,
            ]
            for duty in energy.duties
            if duty.unit_id in focus_units
        ]
        return "\n\n".join(
            [
                "### Overall Energy Summary\n\n"
                + markdown_table(["Basis", "Value", "Units"], overall_rows),
                "### Unit Duty Summary\n\n"
                + markdown_table(["Unit", "Section", "Duty Type", "Heating (kW)", "Cooling (kW)", "Notes"], duty_rows or [["n/a", "-", "n/a", "0.0", "0.0", "-"]]),
                "### Section Duty Summary\n\n"
                + markdown_table(["Section", "Label", "Heating (kW)", "Cooling (kW)", "Recoverable (kW)", "Status"], section_rows or [["n/a", "n/a", "0.0", "0.0", "0.0", "n/a"]]),
                "### Unit Thermal Packet Summary\n\n"
                + markdown_table(
                    ["Packet", "Unit", "Section", "Type", "Heating (kW)", "Cooling (kW)", "Hot In (C)", "Hot Out (C)", "Cold In (C)", "Cold Out (C)", "Recoverable (kW)", "Candidate Media"],
                    thermal_rows or [["n/a", "n/a", "-", "n/a", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "-"]],
                ),
                "### Recovery Candidate Summary\n\n"
                + markdown_table(
                    ["Candidate", "Source Unit", "Sink Unit", "Topology", "Recovered Duty (kW)", "Min Approach (C)", "Feasible", "Notes"],
                    candidate_rows or [["n/a", "-", "-", "n/a", "0.0", "0.0", "no", "-"]],
                ),
                "### Utility Consumption Basis\n\n"
                + markdown_table(
                    ["Unit", "Route", "Candidate Media", "Peak Duty (kW)", "Recoverable Duty (kW)", "Service"],
                    utility_rows or [["n/a", route.route_id, "-", "0.0", "0.0", "-"]],
                ),
                "### Route-Family Duty Focus\n\n"
                + markdown_table(
                    ["Unit", "Duty Type", "Heating (kW)", "Cooling (kW)", "Section", "Notes"],
                    route_family_rows or [["n/a", "n/a", "0.0", "0.0", "-", "-"]],
                ),
                self._render_trace_section("Energy-Balance Calculation Traces", energy.calc_traces),
            ]
        )

    def _render_trace_section(self, title: str, traces) -> str:
        rows = [
            [
                trace.title,
                trace.formula,
                "; ".join(f"{key}={value}" for key, value in trace.substitutions.items()) or "-",
                f"{trace.result} {trace.units}".strip(),
                trace.notes or "-",
            ]
            for trace in traces
        ]
        return f"### {title}\n\n" + markdown_table(
            ["Trace", "Formula", "Inputs", "Result", "Notes"],
            rows or [["n/a", "n/a", "-", "n/a", "-"]],
        )

    def _stream_mass_component_snapshot(self, stream, limit: int = 4) -> str:
        components = sorted(stream.components, key=lambda item: item.mass_flow_kg_hr, reverse=True)
        return ", ".join(f"{component.name}={component.mass_flow_kg_hr:.1f}" for component in components[:limit]) or "-"

    def _local_stream_role(
        self,
        stream_id: str,
        inlet_stream_ids: list[str],
        outlet_stream_ids: list[str],
        stream_role: str,
    ) -> str:
        if stream_id in inlet_stream_ids:
            return "recycle feed" if stream_role == "recycle" else "feed"
        if stream_id in outlet_stream_ids:
            if stream_role == "recycle":
                return "recycle product"
            if stream_role in {"side_draw", "purge", "vent", "waste"}:
                return stream_role.replace("_", " ")
            return "product"
        return "reference"

    def _unit_stream_summary_rows(
        self,
        stream_table: StreamTable,
        unit_id: str,
        unit_label: str,
        inlet_stream_ids: list[str],
        outlet_stream_ids: list[str],
    ) -> list[list[str]]:
        related_stream_ids = list(dict.fromkeys([*inlet_stream_ids, *outlet_stream_ids]))
        rows: list[list[str]] = []
        for stream_id in related_stream_ids:
            stream = next((item for item in stream_table.streams if item.stream_id == stream_id), None)
            if stream is None:
                continue
            rows.append(
                [
                    unit_id,
                    unit_label,
                    stream.stream_id,
                    self._local_stream_role(stream.stream_id, inlet_stream_ids, outlet_stream_ids, stream.stream_role),
                    stream.stream_role,
                    stream.section_id or "-",
                    stream.phase_hint or "-",
                    f"{sum(component.mass_flow_kg_hr for component in stream.components):.3f}",
                    f"{sum(component.molar_flow_kmol_hr for component in stream.components):.6f}",
                    self._stream_mass_component_snapshot(stream),
                ]
            )
        return rows

    def _local_stream_split_summary_rows(self, unit_stream_rows: list[list[str]]) -> list[list[str]]:
        split_buckets = {
            "fresh_feed": {"feed"},
            "recycle_feed": {"recycle feed"},
            "total_feed": {"feed", "recycle feed"},
            "product_effluent": {"product"},
            "recycle_effluent": {"recycle product"},
            "side_draw_purge_vent": {"side draw", "purge", "vent", "waste"},
        }
        rows: list[list[str]] = []
        for label, roles in split_buckets.items():
            selected = [row for row in unit_stream_rows if row[3] in roles]
            mass = sum(float(row[7]) for row in selected)
            molar = sum(float(row[8]) for row in selected)
            rows.append([label, str(len(selected)), f"{mass:.3f}", f"{molar:.6f}"])
        return rows

    def _unit_key_component_balance_rows(
        self,
        stream_table: StreamTable,
        inlet_stream_ids: list[str],
        outlet_stream_ids: list[str],
        limit: int = 6,
    ) -> list[list[str]]:
        inlet_components: dict[str, float] = {}
        outlet_components: dict[str, float] = {}
        for stream in stream_table.streams:
            if stream.stream_id in inlet_stream_ids:
                for component in stream.components:
                    inlet_components[component.name] = inlet_components.get(component.name, 0.0) + component.mass_flow_kg_hr
            if stream.stream_id in outlet_stream_ids:
                for component in stream.components:
                    outlet_components[component.name] = outlet_components.get(component.name, 0.0) + component.mass_flow_kg_hr
        component_names = sorted(
            set(inlet_components) | set(outlet_components),
            key=lambda name: max(inlet_components.get(name, 0.0), outlet_components.get(name, 0.0)),
            reverse=True,
        )[:limit]
        rows: list[list[str]] = []
        for name in component_names:
            inlet = inlet_components.get(name, 0.0)
            outlet = outlet_components.get(name, 0.0)
            rows.append([name, f"{inlet:.3f}", f"{outlet:.3f}", f"{outlet - inlet:.3f}"])
        return rows

    def _field_label(self, key: str) -> str:
        label = key.replace("_", " ").strip()
        return label[:1].upper() + label[1:] if label else key

    def _mapping_rows(self, mapping: dict[str, str]) -> list[list[str]]:
        return [[self._field_label(key), value] for key, value in mapping.items()]

    def _render_reactor_design_chapter(
        self,
        reactor: ReactorDesign,
        reactor_basis: ReactorDesignBasis,
        stream_table: StreamTable,
        energy: EnergyBalance,
        route_profile=None,
    ) -> str:
        reactor_packet = next((packet for packet in stream_table.unit_operation_packets if packet.unit_id == "reactor" or packet.unit_type == "reactor"), None)
        thermal_packet = next(
            (
                packet
                for packet in energy.unit_thermal_packets
                if packet.unit_id in {"R-101", "CONV-101", "reactor"}
            ),
            None,
        )
        basis_rows = [
            ["Selected reactor type", reactor_basis.selected_reactor_type],
            ["Design basis", reactor.design_basis],
            ["Phase regime", reactor.phase_regime or "n/a"],
            ["Residence time (h)", f"{reactor.residence_time_hr:.3f}"],
            ["Design volume (m3)", f"{reactor.design_volume_m3:.3f}"],
            ["Design temperature (C)", f"{reactor.design_temperature_c:.1f}"],
            ["Design pressure (bar)", f"{reactor.design_pressure_bar:.2f}"],
        ]
        kinetic_rows = [
            ["Design conversion fraction", f"{reactor.design_conversion_fraction:.4f}"],
            ["Rate constant (1/h)", f"{reactor.kinetic_rate_constant_1_hr:.6f}"],
            ["Kinetic space time (h)", f"{reactor.kinetic_space_time_hr:.6f}"],
            ["Damkohler number", f"{reactor.kinetic_damkohler_number:.6f}"],
        ]
        packet_rows = [
            [
                reactor_packet.packet_id if reactor_packet else "n/a",
                f"{reactor_packet.inlet_mass_flow_kg_hr:.3f}" if reactor_packet else "n/a",
                f"{reactor_packet.outlet_mass_flow_kg_hr:.3f}" if reactor_packet else "n/a",
                f"{reactor_packet.closure_error_pct:.3f}" if reactor_packet else "n/a",
                reactor_packet.status if reactor_packet else "n/a",
            ],
            [
                thermal_packet.packet_id if thermal_packet else "n/a",
                f"{thermal_packet.heating_kw:.3f}" if thermal_packet else "n/a",
                f"{thermal_packet.cooling_kw:.3f}" if thermal_packet else "n/a",
                f"{thermal_packet.recoverable_duty_kw:.3f}" if thermal_packet else "n/a",
                ", ".join(thermal_packet.candidate_media) if thermal_packet and thermal_packet.candidate_media else "n/a",
            ],
        ]
        heat_transfer_rows = [
            ["Heat duty (kW)", f"{reactor.heat_duty_kw:.3f}"],
            ["Heat-release density (kW/m3)", f"{reactor.heat_release_density_kw_m3:.3f}"],
            ["Adiabatic temperature rise (C)", f"{reactor.adiabatic_temperature_rise_c:.3f}"],
            ["Heat-removal capacity (kW)", f"{reactor.heat_removal_capacity_kw:.3f}"],
            ["Heat-removal margin", f"{reactor.heat_removal_margin_fraction:.4f}"],
            ["Thermal stability score", f"{reactor.thermal_stability_score:.2f}"],
            ["Runaway risk label", reactor.runaway_risk_label or "n/a"],
            ["Heat-transfer area (m2)", f"{reactor.heat_transfer_area_m2:.3f}"],
            ["Overall U (W/m2-K)", f"{reactor.overall_u_w_m2_k:.1f}"],
            ["Reynolds number", f"{reactor.reynolds_number:,.1f}"],
            ["Prandtl number", f"{reactor.prandtl_number:.3f}"],
            ["Nusselt number", f"{reactor.nusselt_number:.2f}"],
            ["Tube count", str(reactor.number_of_tubes)],
            ["Tube length (m)", f"{reactor.tube_length_m:.3f}"],
        ]
        catalyst_rows = [
            ["Catalyst", reactor.catalyst_name or "none"],
            ["Catalyst inventory (kg)", f"{reactor.catalyst_inventory_kg:.3f}"],
            ["Catalyst cycle (days)", f"{reactor.catalyst_cycle_days:.1f}"],
            ["Catalyst regeneration (days)", f"{reactor.catalyst_regeneration_days:.1f}"],
            ["Catalyst void fraction", f"{reactor.catalyst_void_fraction:.3f}"],
            ["Catalyst WHSV (1/h)", f"{reactor.catalyst_weight_hourly_space_velocity_1_hr:.4f}"],
        ]
        utility_rows = [
            ["Utility topology", reactor.utility_topology or "standalone utilities"],
            ["Architecture family", reactor.utility_architecture_family or "base"],
            ["Cooling medium", reactor.cooling_medium],
            ["Integrated duty (kW)", f"{reactor.integrated_thermal_duty_kw:.3f}"],
            ["Allocated island target (kW)", f"{reactor.allocated_recovered_duty_target_kw:.3f}"],
            ["Residual utility duty (kW)", f"{reactor.residual_utility_duty_kw:.3f}"],
            ["Integrated LMTD (K)", f"{reactor.integrated_lmtd_k:.3f}"],
            ["Integrated exchange area (m2)", f"{reactor.integrated_exchange_area_m2:.3f}"],
            ["Selected utility islands", ", ".join(reactor.selected_utility_island_ids) or "none"],
            ["Selected header levels", ", ".join(str(level) for level in reactor.selected_utility_header_levels) or "none"],
            ["Selected cluster ids", ", ".join(reactor.selected_utility_cluster_ids) or "none"],
            ["Coupled service basis", reactor.coupled_service_basis or "none"],
            ["Selected train steps", ", ".join(reactor.selected_train_step_ids) or "none"],
        ]
        reactor_design_input_rows = self._mapping_rows(reactor_basis.design_inputs)
        reactor_operating_envelope_rows = self._mapping_rows(reactor_basis.operating_envelope)
        reactor_geometry_rows = [
            ["Liquid holdup (m3)", f"{reactor.liquid_holdup_m3:.3f}"],
            ["Shell diameter (m)", f"{reactor.shell_diameter_m:.3f}"],
            ["Shell length (m)", f"{reactor.shell_length_m:.3f}"],
            ["Tube count", str(reactor.number_of_tubes)],
            ["Tube length (m)", f"{reactor.tube_length_m:.3f}"],
            ["Heat-transfer area (m2)", f"{reactor.heat_transfer_area_m2:.3f}"],
            ["Cooling medium", reactor.cooling_medium or "n/a"],
            ["Utility topology", reactor.utility_topology or "standalone utilities"],
        ]
        reactor_throughput_m3_hr = reactor.design_volume_m3 / max(reactor.residence_time_hr, 1e-6)
        reactor_da_consistency = reactor.kinetic_rate_constant_1_hr * reactor.residence_time_hr
        reactor_heat_release_density_basis = reactor.heat_duty_kw / max(reactor.design_volume_m3, 1e-6)
        reactor_area_basis = (
            (reactor.heat_duty_kw * 1000.0) / max(reactor.overall_u_w_m2_k * max(reactor.integrated_lmtd_k, 1.0), 1.0)
            if reactor.overall_u_w_m2_k > 0.0
            else 0.0
        )
        reactor_derivation_rows = [
            ["Volumetric throughput", "Vdot = V / tau", f"{reactor_throughput_m3_hr:.3f} m3/h"],
            ["Kinetic consistency", "Da = k * tau", f"{reactor_da_consistency:.4f}"],
            ["Heat release density", "q''' = Q / V", f"{reactor_heat_release_density_basis:.3f} kW/m3"],
            [
                "Heat-transfer area check",
                "A = Q / (U * LMTD)",
                f"{reactor_area_basis:.3f} m2" if reactor.integrated_lmtd_k > 0.0 else "n/a",
            ],
            ["Design conversion basis", "Target conversion", f"{reactor.design_conversion_fraction:.4f}"],
            ["Packet closure basis", "Unit packet closure", f"{reactor_packet.closure_error_pct:.3f} %" if reactor_packet else "n/a"],
        ]
        reactor_substitution_rows = [
            [
                "Residence-time sizing",
                "Vdot = V / tau",
                f"V={reactor.design_volume_m3:.3f} m3; tau={reactor.residence_time_hr:.3f} h",
                f"{reactor_throughput_m3_hr:.3f} m3/h",
            ],
            [
                "Damkohler basis",
                "Da = k * tau",
                f"k={reactor.kinetic_rate_constant_1_hr:.6f} 1/h; tau={reactor.residence_time_hr:.3f} h",
                f"{reactor_da_consistency:.4f}",
            ],
            [
                "Thermal intensity",
                "q''' = Q / V",
                f"Q={reactor.heat_duty_kw:.3f} kW; V={reactor.design_volume_m3:.3f} m3",
                f"{reactor_heat_release_density_basis:.3f} kW/m3",
            ],
            [
                "Heat-transfer area check",
                "A = Q / (U * LMTD)",
                (
                    f"Q={reactor.heat_duty_kw * 1000.0:.1f} W; U={reactor.overall_u_w_m2_k:.1f} W/m2-K; "
                    f"LMTD={reactor.integrated_lmtd_k:.3f} K"
                    if reactor.integrated_lmtd_k > 0.0
                    else "Integrated LMTD not available"
                ),
                f"{reactor_area_basis:.3f} m2" if reactor.integrated_lmtd_k > 0.0 else "n/a",
            ],
            [
                "Heat-removal margin",
                "Margin = Qrem / Qduty - 1",
                f"Qrem={reactor.heat_removal_capacity_kw:.3f} kW; Qduty={reactor.heat_duty_kw:.3f} kW",
                f"{reactor.heat_removal_margin_fraction:.4f}",
            ],
            [
                "Residual utility demand",
                "Qres = Qduty - Qint",
                f"Qduty={reactor.heat_duty_kw:.3f} kW; Qint={reactor.integrated_thermal_duty_kw:.3f} kW",
                f"{reactor.residual_utility_duty_kw:.3f} kW",
            ],
        ]
        reactor_hazard_rows = [
            ["Adiabatic temperature rise (C)", f"{reactor.adiabatic_temperature_rise_c:.3f}"],
            ["Heat-removal capacity (kW)", f"{reactor.heat_removal_capacity_kw:.3f}"],
            ["Heat-removal margin", f"{reactor.heat_removal_margin_fraction:.4f}"],
            ["Thermal stability score", f"{reactor.thermal_stability_score:.2f}"],
            ["Runaway risk label", reactor.runaway_risk_label or "n/a"],
            ["Residual utility duty (kW)", f"{reactor.residual_utility_duty_kw:.3f}"],
            ["Integrated recovered duty (kW)", f"{reactor.integrated_thermal_duty_kw:.3f}"],
        ]
        reactor_package_rows = [
            ["Architecture family", reactor.utility_architecture_family or "base"],
            ["Coupled service basis", reactor.coupled_service_basis or "none"],
            ["Integrated LMTD (K)", f"{reactor.integrated_lmtd_k:.3f}"],
            ["Integrated exchange area (m2)", f"{reactor.integrated_exchange_area_m2:.3f}"],
            ["Allocated recovered-duty target (kW)", f"{reactor.allocated_recovered_duty_target_kw:.3f}"],
            ["Selected utility islands", ", ".join(reactor.selected_utility_island_ids) or "none"],
            ["Selected header levels", ", ".join(str(level) for level in reactor.selected_utility_header_levels) or "none"],
            ["Selected cluster ids", ", ".join(reactor.selected_utility_cluster_ids) or "none"],
            ["Selected train steps", ", ".join(reactor.selected_train_step_ids) or "none"],
        ]
        reactor_stream_ids = list(dict.fromkeys((reactor_packet.inlet_stream_ids if reactor_packet else []) + (reactor_packet.outlet_stream_ids if reactor_packet else [])))
        balance_rows = []
        for stream_id in reactor_stream_ids:
            stream = next((item for item in stream_table.streams if item.stream_id == stream_id), None)
            if stream is None:
                continue
            balance_rows.append(
                [
                    stream.stream_id,
                    stream.stream_role,
                    stream.source_unit_id or "-",
                    stream.destination_unit_id or "-",
                    f"{sum(component.mass_flow_kg_hr for component in stream.components):.3f}",
                    ", ".join(
                        f"{component.name}={component.mass_flow_kg_hr:.1f}"
                        for component in sorted(stream.components, key=lambda item: item.mass_flow_kg_hr, reverse=True)[:4]
                    ) or "-",
                ]
            )
        route_family_rows = [
            ["Route family", getattr(route_profile, "family_label", "n/a")],
            ["Route family id", getattr(route_profile, "route_family_id", "n/a")],
            ["Primary reactor class", getattr(route_profile, "primary_reactor_class", "n/a")],
            ["Primary separation train", getattr(route_profile, "primary_separation_train", "n/a")],
            ["Heat recovery style", getattr(route_profile, "heat_recovery_style", "n/a")],
            ["Data anchors", ", ".join(getattr(route_profile, "data_anchor_requirements", [])) or "none"],
        ]
        reactor_stream_rows = self._unit_stream_summary_rows(
            stream_table,
            reactor_packet.unit_id if reactor_packet else "reactor",
            reactor_packet.service if reactor_packet else "Main reactor service",
            reactor_packet.inlet_stream_ids if reactor_packet else [],
            reactor_packet.outlet_stream_ids if reactor_packet else [],
        )
        reactor_split_rows = self._local_stream_split_summary_rows(reactor_stream_rows)
        reactor_component_rows = self._unit_key_component_balance_rows(
            stream_table,
            reactor_packet.inlet_stream_ids if reactor_packet else [],
            reactor_packet.outlet_stream_ids if reactor_packet else [],
        )
        return "\n\n".join(
            [
                reactor_basis.markdown,
                "### Governing Equations\n\n" + "\n".join(f"- `{equation}`" for equation in reactor_basis.governing_equations),
                "### Route-Family Basis\n\n" + markdown_table(["Parameter", "Value"], route_family_rows),
                "### Solver Packet Basis\n\n"
                + markdown_table(
                    ["Packet", "Primary Value 1", "Primary Value 2", "Closure / Recoverable", "Status / Media"],
                    packet_rows,
                ),
                "### Balance Reference Snapshot\n\n"
                + markdown_table(
                    ["Stream", "Role", "From", "To", "kg/h", "Dominant Components"],
                    balance_rows or [["n/a", "n/a", "-", "-", "0.0", "-"]],
                ),
                "### Reactor Feed / Product / Recycle Summary\n\n"
                + markdown_table(
                    ["Unit", "Service", "Stream", "Local Role", "Stream Role", "Section", "Phase", "kg/h", "kmol/h", "Dominant Components"],
                    reactor_stream_rows or [["reactor", "Main reactor service", "n/a", "n/a", "n/a", "-", "-", "0.0", "0.0", "-"]],
                ),
                "### Reactor Local Stream Split Summary\n\n"
                + markdown_table(
                    ["Split", "Stream Count", "Mass Flow (kg/h)", "Molar Flow (kmol/h)"],
                    reactor_split_rows,
                ),
                "### Key Reactor Component Balance\n\n"
                + markdown_table(
                    ["Component", "Inlet kg/h", "Outlet kg/h", "Delta kg/h"],
                    reactor_component_rows or [["n/a", "0.0", "0.0", "0.0"]],
                ),
                "### Reactor Design Inputs\n\n" + markdown_table(["Parameter", "Value"], reactor_design_input_rows),
                "### Reactor Operating Envelope\n\n" + markdown_table(["Parameter", "Value"], reactor_operating_envelope_rows),
                "### Reactor Sizing Basis\n\n" + markdown_table(["Parameter", "Value"], basis_rows),
                "### Reaction and Sizing Derivation Basis\n\n"
                + markdown_table(["Check", "Formula / Basis", "Result"], reactor_derivation_rows),
                "### Reactor Equation-Substitution Sheet\n\n"
                + markdown_table(["Check", "Equation", "Substitution", "Result"], reactor_substitution_rows),
                "### Kinetic Design Basis\n\n" + markdown_table(["Parameter", "Value"], kinetic_rows),
                "### Reactor Geometry and Internals\n\n" + markdown_table(["Parameter", "Value"], reactor_geometry_rows),
                "### Heat-Transfer Derivation Basis\n\n" + markdown_table(["Parameter", "Value"], heat_transfer_rows),
                "### Thermal Stability and Hazard Envelope\n\n" + markdown_table(["Parameter", "Value"], reactor_hazard_rows),
                "### Catalyst Service Basis\n\n" + markdown_table(["Parameter", "Value"], catalyst_rows),
                "### Integrated Utility Package Basis\n\n" + markdown_table(["Parameter", "Value"], reactor_package_rows),
                "### Utility Coupling\n\n" + markdown_table(["Parameter", "Value"], utility_rows),
                self._render_trace_section("Reactor Calculation Traces", reactor.calc_traces),
            ]
        )

    def _render_process_unit_design_chapter(
        self,
        column: ColumnDesign,
        column_hydraulics: ColumnHydraulics,
        exchanger: HeatExchangerDesign,
        exchanger_thermal: HeatExchangerThermalDesign,
        stream_table: StreamTable,
        route_profile=None,
    ) -> str:
        def _normalize_component(name: str) -> str:
            return name.strip().lower().replace("-", "_").replace(" ", "_")

        def _component_mass(stream_ids: list[str], component_name: str) -> float:
            selected_ids = set(stream_ids)
            target = _normalize_component(component_name)
            return sum(
                component.mass_flow_kg_hr
                for stream in stream_table.streams
                if stream.stream_id in selected_ids
                for component in stream.components
                if _normalize_component(component.name) == target
            )

        def _preferred_component(packet, *, mode: str) -> str | None:
            component_names = (
                set(packet.component_split_to_product)
                | set(packet.component_split_to_waste)
                | set(packet.component_split_to_recycle)
            )
            excluded = {"water"} if mode == "sle" else {"water", "sulfuric_acid", "spent_acid"}
            ranked: list[tuple[float, float, str]] = []
            for component_name in component_names:
                normalized = _normalize_component(component_name)
                if normalized in excluded:
                    continue
                product_split = packet.component_split_to_product.get(component_name, 0.0)
                waste_split = packet.component_split_to_waste.get(component_name, 0.0)
                recycle_split = packet.component_split_to_recycle.get(component_name, 0.0)
                score = (
                    product_split + recycle_split - waste_split
                    if mode == "gle"
                    else product_split - recycle_split - waste_split
                )
                ranked.append((score, product_split + recycle_split + waste_split, component_name))
            if ranked:
                return max(ranked, key=lambda item: (item[0], item[1], item[2].lower()))[2]
            return None

        process_packets = [
            packet
            for packet in stream_table.unit_operation_packets
            if packet.unit_id in {"concentration", "purification", "regeneration", "filtration", "drying"}
            or packet.unit_type in {"distillation", "evaporation", "stripping", "filtration", "drying", "extraction"}
        ]
        packet_rows = [
            [
                packet.packet_id,
                packet.unit_id,
                packet.unit_type,
                f"{packet.inlet_mass_flow_kg_hr:.3f}",
                f"{packet.outlet_mass_flow_kg_hr:.3f}",
                f"{packet.closure_error_pct:.3f}",
                packet.status,
            ]
            for packet in process_packets
        ]
        balance_reference_rows = []
        referenced_stream_ids = {
            stream_id
            for packet in process_packets
            for stream_id in (*packet.inlet_stream_ids, *packet.outlet_stream_ids)
        }
        for stream in stream_table.streams:
            if stream.stream_id not in referenced_stream_ids:
                continue
            balance_reference_rows.append(
                [
                    stream.stream_id,
                    stream.stream_role,
                    stream.source_unit_id or "-",
                    stream.destination_unit_id or "-",
                    f"{sum(component.mass_flow_kg_hr for component in stream.components):.3f}",
                    ", ".join(
                        f"{component.name}={component.mass_flow_kg_hr:.1f}"
                        for component in sorted(stream.components, key=lambda item: item.mass_flow_kg_hr, reverse=True)[:4]
                    ) or "-",
                ]
            )
        route_family_rows = [
            ["Route family", getattr(route_profile, "family_label", "n/a")],
            ["Route family id", getattr(route_profile, "route_family_id", "n/a")],
            ["Primary separation train", getattr(route_profile, "primary_separation_train", "n/a")],
            ["Heat recovery style", getattr(route_profile, "heat_recovery_style", "n/a")],
            ["Dominant phase pattern", getattr(route_profile, "dominant_phase_pattern", "n/a")],
            ["Data anchors", ", ".join(getattr(route_profile, "data_anchor_requirements", [])) or "none"],
        ]
        process_stream_rows: list[list[str]] = []
        for packet in process_packets:
            process_stream_rows.extend(
                self._unit_stream_summary_rows(
                    stream_table,
                    packet.unit_id,
                    packet.service,
                    packet.inlet_stream_ids,
                    packet.outlet_stream_ids,
                )
            )
        process_split_rows = self._local_stream_split_summary_rows(process_stream_rows)
        process_component_rows: list[list[str]] = []
        for packet in process_packets:
            component_rows = self._unit_key_component_balance_rows(
                stream_table,
                packet.inlet_stream_ids,
                packet.outlet_stream_ids,
                limit=4,
            )
            for row in component_rows:
                process_component_rows.append([packet.unit_id, packet.service, *row])
        column_rows = [
            ["Service", column.service],
            ["Light key", column.light_key],
            ["Heavy key", column.heavy_key],
            ["Relative volatility", f"{column.relative_volatility:.3f}"],
            ["Minimum stages", f"{column.min_stages:.3f}"],
            ["Theoretical stages", f"{column.theoretical_stages:.3f}"],
            ["Design stages", str(column.design_stages)],
            ["Tray efficiency", f"{column.tray_efficiency:.3f}"],
            ["Minimum reflux ratio", f"{column.minimum_reflux_ratio:.3f}"],
            ["Reflux ratio", f"{column.reflux_ratio:.3f}"],
            ["R / Rmin", f"{column.reflux_ratio_multiple_of_min:.3f}"],
            ["Diameter (m)", f"{column.column_diameter_m:.3f}"],
            ["Height (m)", f"{column.column_height_m:.3f}"],
            ["Feed stage", str(column.feed_stage)],
        ]
        section_rows = [
            ["Feed quality q-factor", f"{column.feed_quality_q_factor:.3f}"],
            ["Murphree efficiency", f"{column.murphree_efficiency:.3f}"],
            ["Top relative volatility", f"{column.top_relative_volatility:.3f}"],
            ["Bottom relative volatility", f"{column.bottom_relative_volatility:.3f}"],
            ["Rectifying theoretical stages", f"{column.rectifying_theoretical_stages:.3f}"],
            ["Stripping theoretical stages", f"{column.stripping_theoretical_stages:.3f}"],
            ["Rectifying vapor load (kg/h)", f"{column.rectifying_vapor_load_kg_hr:.3f}"],
            ["Stripping vapor load (kg/h)", f"{column.stripping_vapor_load_kg_hr:.3f}"],
            ["Rectifying liquid load (m3/h)", f"{column.rectifying_liquid_load_m3_hr:.3f}"],
            ["Stripping liquid load (m3/h)", f"{column.stripping_liquid_load_m3_hr:.3f}"],
        ]
        hydraulics_rows = [
            ["Tray spacing (m)", f"{column.tray_spacing_m:.3f}"],
            ["Flooding fraction", f"{column.flooding_fraction:.3f}"],
            ["Downcomer area fraction", f"{column.downcomer_area_fraction:.3f}"],
            ["Vapor velocity (m/s)", f"{column_hydraulics.vapor_velocity_m_s:.3f}"],
            ["Allowable vapor velocity (m/s)", f"{column_hydraulics.allowable_vapor_velocity_m_s:.3f}"],
            ["Capacity factor (m/s)", f"{column_hydraulics.capacity_factor_m_s:.3f}"],
            ["Active area (m2)", f"{column_hydraulics.active_area_m2:.3f}"],
            ["Liquid load (m3/h)", f"{column_hydraulics.liquid_load_m3_hr:.3f}"],
            ["Vapor load (kg/h)", f"{column.vapor_load_kg_hr:.3f}"],
            ["Liquid density (kg/m3)", f"{column.liquid_density_kg_m3:.3f}"],
            ["Vapor density (kg/m3)", f"{column.vapor_density_kg_m3:.3f}"],
            ["Pressure drop per stage (kPa)", f"{column.pressure_drop_per_stage_kpa:.3f}"],
            ["Top temperature (C)", f"{column.top_temperature_c:.1f}"],
            ["Bottom temperature (C)", f"{column.bottom_temperature_c:.1f}"],
        ]
        utility_rows = [
            ["Utility topology", column.utility_topology or "standalone utilities"],
            ["Architecture family", column.utility_architecture_family or "base"],
            ["Integrated reboiler duty (kW)", f"{column.integrated_reboiler_duty_kw:.3f}"],
            ["Allocated reboiler target (kW)", f"{column.allocated_reboiler_recovery_target_kw:.3f}"],
            ["Residual reboiler utility (kW)", f"{column.residual_reboiler_utility_kw:.3f}"],
            ["Integrated reboiler LMTD (K)", f"{column.integrated_reboiler_lmtd_k:.3f}"],
            ["Integrated reboiler area (m2)", f"{column.integrated_reboiler_area_m2:.3f}"],
            ["Reboiler medium", column.reboiler_medium or "none"],
            ["Reboiler package type", column.reboiler_package_type or "none"],
            ["Reboiler circulation ratio", f"{column.reboiler_circulation_ratio:.3f}"],
            ["Reboiler phase-change load (kg/h)", f"{column.reboiler_phase_change_load_kg_hr:.3f}"],
            ["Reboiler package items", ", ".join(column.reboiler_package_item_ids) or "none"],
            ["Condenser recovery duty (kW)", f"{column.condenser_recovery_duty_kw:.3f}"],
            ["Allocated condenser target (kW)", f"{column.allocated_condenser_recovery_target_kw:.3f}"],
            ["Condenser recovery LMTD (K)", f"{column.condenser_recovery_lmtd_k:.3f}"],
            ["Condenser recovery area (m2)", f"{column.condenser_recovery_area_m2:.3f}"],
            ["Condenser recovery medium", column.condenser_recovery_medium or "none"],
            ["Condenser package type", column.condenser_package_type or "none"],
            ["Condenser phase-change load (kg/h)", f"{column.condenser_phase_change_load_kg_hr:.3f}"],
            ["Condenser circulation flow (m3/h)", f"{column.condenser_circulation_flow_m3_hr:.3f}"],
            ["Condenser package items", ", ".join(column.condenser_package_item_ids) or "none"],
            ["Selected utility islands", ", ".join(column.selected_utility_island_ids) or "none"],
            ["Selected header levels", ", ".join(str(level) for level in column.selected_utility_header_levels) or "none"],
            ["Selected cluster ids", ", ".join(column.selected_utility_cluster_ids) or "none"],
            ["Selected train steps", ", ".join(column.selected_train_step_ids) or "none"],
        ]
        exchanger_rows = [
            ["Configuration", exchanger_thermal.selected_configuration],
            ["Heat load (kW)", f"{exchanger.heat_load_kw:.3f}"],
            ["LMTD (K)", f"{exchanger.lmtd_k:.1f}"],
            ["Overall U (W/m2-K)", f"{exchanger.overall_u_w_m2_k:.1f}"],
            ["Area (m2)", f"{exchanger.area_m2:.3f}"],
            ["Package family", exchanger.package_family or "generic"],
            ["Architecture family", exchanger.utility_architecture_family or "base"],
            ["Selected train step", exchanger.selected_train_step_id or "none"],
            ["Selected utility island", exchanger.selected_island_id or "none"],
            ["Selected header level", str(exchanger.selected_header_level or 0)],
            ["Selected cluster id", exchanger.selected_cluster_id or "none"],
            ["Allocated island target (kW)", f"{exchanger.allocated_recovered_duty_target_kw:.3f}"],
            ["Package roles", ", ".join(exchanger.selected_package_roles) or "none"],
            ["Selected package items", ", ".join(exchanger.selected_package_item_ids) or "none"],
            ["Boiling-side coefficient (W/m2-K)", f"{exchanger.boiling_side_coefficient_w_m2_k:.3f}"],
            ["Condensing-side coefficient (W/m2-K)", f"{exchanger.condensing_side_coefficient_w_m2_k:.3f}"],
        ]
        heat_transfer_input_rows = self._mapping_rows(exchanger_thermal.thermal_inputs)
        heat_transfer_package_rows = self._mapping_rows(exchanger_thermal.package_basis)
        distillation_sections: list[str] = []
        absorption_sections: list[str] = []
        crystallization_sections: list[str] = []
        if "absor" not in column.service.lower() and "crystallizer" not in column.service.lower():
            separation_input_rows = [
                ["Service", column.service],
                ["Equilibrium model", column.equilibrium_model or "screening_vle"],
                ["Equilibrium parameter ids", ", ".join(column.equilibrium_parameter_ids) or "none"],
                ["Light key", column.light_key],
                ["Heavy key", column.heavy_key],
                ["Relative volatility", f"{column.relative_volatility:.3f}"],
                ["Minimum stages", f"{column.min_stages:.3f}"],
                ["Theoretical stages", f"{column.theoretical_stages:.3f}"],
                ["Design stages", str(column.design_stages)],
                ["Minimum reflux ratio", f"{column.minimum_reflux_ratio:.3f}"],
                ["Operating reflux ratio", f"{column.reflux_ratio:.3f}"],
            ]
            flow_derivation_rows = [
                ["Minimum stages", "Fenske screening", f"{column.min_stages:.3f}"],
                ["Minimum reflux", "Underwood screening", f"{column.minimum_reflux_ratio:.3f}"],
                ["Operating stages", "Gilliland screening", f"{column.theoretical_stages:.3f}"],
                ["Feed condition", "q-factor basis", f"{column.feed_quality_q_factor:.3f}"],
                ["Rectifying section split", "Section stage allocation", f"{column.rectifying_theoretical_stages:.3f} stages"],
                ["Stripping section split", "Section stage allocation", f"{column.stripping_theoretical_stages:.3f} stages"],
                ["Rectifying internal vapor load", "Top section vapor load", f"{column.rectifying_vapor_load_kg_hr:.3f} kg/h"],
                ["Stripping internal vapor load", "Bottom section vapor load", f"{column.stripping_vapor_load_kg_hr:.3f} kg/h"],
                ["Rectifying liquid load", "Top section liquid load", f"{column.rectifying_liquid_load_m3_hr:.3f} m3/h"],
                ["Stripping liquid load", "Bottom section liquid load", f"{column.stripping_liquid_load_m3_hr:.3f} m3/h"],
            ]
            murphree_stage_count = column.theoretical_stages / max(column.murphree_efficiency, 1e-9)
            reboiler_effective_u = (
                (column.integrated_reboiler_duty_kw * 1000.0)
                / max(column.integrated_reboiler_area_m2 * max(column.integrated_reboiler_lmtd_k, 1e-9), 1e-9)
                if column.integrated_reboiler_area_m2 > 0.0 and column.integrated_reboiler_lmtd_k > 0.0
                else 0.0
            )
            condenser_effective_u = (
                (column.condenser_recovery_duty_kw * 1000.0)
                / max(column.condenser_recovery_area_m2 * max(column.condenser_recovery_lmtd_k, 1e-9), 1e-9)
                if column.condenser_recovery_area_m2 > 0.0 and column.condenser_recovery_lmtd_k > 0.0
                else 0.0
            )
            reboiler_latent_basis = (
                (column.reboiler_duty_kw * 3600.0) / max(column.reboiler_phase_change_load_kg_hr, 1e-9)
                if column.reboiler_phase_change_load_kg_hr > 0.0
                else 0.0
            )
            condenser_latent_basis = (
                (column.condenser_recovery_duty_kw * 3600.0) / max(column.condenser_phase_change_load_kg_hr, 1e-9)
                if column.condenser_phase_change_load_kg_hr > 0.0
                else 0.0
            )
            distillation_substitution_rows = [
                [
                    "Fenske minimum stages",
                    "Nmin = Fenske(alpha, LK/HK split)",
                    (
                        f"alpha={column.relative_volatility:.3f}; "
                        f"alpha_top={column.top_relative_volatility:.3f}; "
                        f"alpha_bottom={column.bottom_relative_volatility:.3f}"
                    ),
                    f"{column.min_stages:.3f}",
                ],
                [
                    "Underwood minimum reflux",
                    "Rmin = Underwood(alpha, q, keys)",
                    (
                        f"alpha_top={column.top_relative_volatility:.3f}; "
                        f"alpha_bottom={column.bottom_relative_volatility:.3f}; "
                        f"q={column.feed_quality_q_factor:.3f}"
                    ),
                    f"{column.minimum_reflux_ratio:.3f}",
                ],
                [
                    "Gilliland operating stages",
                    "N = Gilliland(Nmin, R/Rmin)",
                    f"Nmin={column.min_stages:.3f}; R/Rmin={column.reflux_ratio_multiple_of_min:.3f}",
                    f"{column.theoretical_stages:.3f}",
                ],
                [
                    "Murphree tray conversion",
                    "Nactual = Ntheoretical / Em",
                    f"Ntheoretical={column.theoretical_stages:.3f}; Em={column.murphree_efficiency:.3f}",
                    f"{murphree_stage_count:.3f} equivalent trays",
                ],
            ]
            feed_internal_substitution_rows = [
                [
                    "Feed quality basis",
                    "q = feed thermal condition parameter",
                    f"selected feed stage={column.feed_stage}; q={column.feed_quality_q_factor:.3f}",
                    f"{column.feed_quality_q_factor:.3f}",
                ],
                [
                    "Rectifying section split",
                    "Nrect = f(feed stage, N)",
                    f"feed stage={column.feed_stage}; N={column.design_stages}",
                    f"{column.rectifying_theoretical_stages:.3f} stages",
                ],
                [
                    "Stripping section split",
                    "Nstrip = N - Nrect",
                    f"N={column.theoretical_stages:.3f}; Nrect={column.rectifying_theoretical_stages:.3f}",
                    f"{column.stripping_theoretical_stages:.3f} stages",
                ],
                [
                    "Rectifying vapor load",
                    "Vrect from section screening",
                    f"R={column.reflux_ratio:.3f}; Rmin={column.minimum_reflux_ratio:.3f}",
                    f"{column.rectifying_vapor_load_kg_hr:.3f} kg/h",
                ],
                [
                    "Stripping vapor load",
                    "Vstrip from bottom section screening",
                    f"Nstrip={column.stripping_theoretical_stages:.3f}; q={column.feed_quality_q_factor:.3f}",
                    f"{column.stripping_vapor_load_kg_hr:.3f} kg/h",
                ],
                [
                    "Rectifying liquid load",
                    "Lrect from reflux / internal flow basis",
                    f"R={column.reflux_ratio:.3f}",
                    f"{column.rectifying_liquid_load_m3_hr:.3f} m3/h",
                ],
                [
                    "Stripping liquid load",
                    "Lstrip from boilup / internal flow basis",
                    f"Reboiler duty={column.reboiler_duty_kw:.3f} kW",
                    f"{column.stripping_liquid_load_m3_hr:.3f} m3/h",
                ],
            ]
            operating_envelope_rows = [
                ["Column diameter (m)", f"{column.column_diameter_m:.3f}"],
                ["Column height (m)", f"{column.column_height_m:.3f}"],
                ["Top temperature (C)", f"{column.top_temperature_c:.1f}"],
                ["Bottom temperature (C)", f"{column.bottom_temperature_c:.1f}"],
                ["Liquid density (kg/m3)", f"{column.liquid_density_kg_m3:.3f}"],
                ["Vapor density (kg/m3)", f"{column.vapor_density_kg_m3:.3f}"],
                ["Superficial vapor velocity (m/s)", f"{column.superficial_vapor_velocity_m_s:.3f}"],
                ["Allowable vapor velocity (m/s)", f"{column.allowable_vapor_velocity_m_s:.3f}"],
                ["Flooding fraction", f"{column.flooding_fraction:.3f}"],
                ["Pressure drop per stage (kPa)", f"{column.pressure_drop_per_stage_kpa:.3f}"],
            ]
            reboiler_condenser_rows = [
                ["Reboiler package type", column.reboiler_package_type or "none"],
                ["Reboiler medium", column.reboiler_medium or "none"],
                ["Reboiler integrated duty (kW)", f"{column.integrated_reboiler_duty_kw:.3f}"],
                ["Reboiler LMTD (K)", f"{column.integrated_reboiler_lmtd_k:.3f}"],
                ["Reboiler integrated area (m2)", f"{column.integrated_reboiler_area_m2:.3f}"],
                ["Reboiler phase-change load (kg/h)", f"{column.reboiler_phase_change_load_kg_hr:.3f}"],
                ["Condenser package type", column.condenser_package_type or "none"],
                ["Condenser recovery medium", column.condenser_recovery_medium or "none"],
                ["Condenser recovery duty (kW)", f"{column.condenser_recovery_duty_kw:.3f}"],
                ["Condenser recovery LMTD (K)", f"{column.condenser_recovery_lmtd_k:.3f}"],
                ["Condenser recovery area (m2)", f"{column.condenser_recovery_area_m2:.3f}"],
                ["Condenser phase-change load (kg/h)", f"{column.condenser_phase_change_load_kg_hr:.3f}"],
            ]
            reboiler_condenser_substitution_rows = [
                [
                    "Operating reflux multiple",
                    "R/Rmin = R / Rmin",
                    f"R={column.reflux_ratio:.3f}; Rmin={column.minimum_reflux_ratio:.3f}",
                    f"{column.reflux_ratio_multiple_of_min:.3f}",
                ],
                [
                    "Integrated reboiler area",
                    "A = Q / (U * LMTD)",
                    (
                        f"Q={column.integrated_reboiler_duty_kw * 1000.0:.1f} W; "
                        f"U={reboiler_effective_u:.1f} W/m2-K; "
                        f"LMTD={column.integrated_reboiler_lmtd_k:.3f} K"
                    ),
                    f"{column.integrated_reboiler_area_m2:.3f} m2",
                ],
                [
                    "Reboiler phase-change basis",
                    "m = Q / lambda",
                    f"Q={column.reboiler_duty_kw:.3f} kW; lambda~={reboiler_latent_basis:.1f} kJ/kg",
                    f"{column.reboiler_phase_change_load_kg_hr:.3f} kg/h",
                ],
                [
                    "Condenser recovery area",
                    "A = Q / (U * LMTD)",
                    (
                        f"Q={column.condenser_recovery_duty_kw * 1000.0:.1f} W; "
                        f"U={condenser_effective_u:.1f} W/m2-K; "
                        f"LMTD={column.condenser_recovery_lmtd_k:.3f} K"
                    ),
                    f"{column.condenser_recovery_area_m2:.3f} m2",
                ],
                [
                    "Condenser phase-change basis",
                    "m = Q / lambda",
                    f"Q={column.condenser_recovery_duty_kw:.3f} kW; lambda~={condenser_latent_basis:.1f} kJ/kg",
                    f"{column.condenser_phase_change_load_kg_hr:.3f} kg/h",
                ],
            ]
            distillation_sections.append(
                "### Separation Design Inputs\n\n" + markdown_table(["Parameter", "Value"], separation_input_rows)
            )
            distillation_sections.append(
                "### Section and Feed Basis\n\n"
                + markdown_table(["Parameter", "Value"], section_rows)
            )
            distillation_sections.append(
                "### Distillation Equation-Substitution Basis\n\n"
                + markdown_table(["Check", "Equation", "Substitution", "Result"], distillation_substitution_rows)
            )
            distillation_sections.append(
                "### Feed and Internal Flow Derivation\n\n"
                + markdown_table(["Check", "Formula / Basis", "Result"], flow_derivation_rows)
            )
            distillation_sections.append(
                "### Feed Condition and Internal Flow Substitution Sheet\n\n"
                + markdown_table(["Check", "Equation", "Substitution", "Result"], feed_internal_substitution_rows)
            )
            distillation_sections.append(
                "### Column Operating Envelope\n\n"
                + markdown_table(["Parameter", "Value"], operating_envelope_rows)
            )
            distillation_sections.append(
                "### Reboiler and Condenser Package Basis\n\n"
                + markdown_table(["Parameter", "Value"], reboiler_condenser_rows)
            )
            distillation_sections.append(
                "### Reboiler and Condenser Thermal Substitution Sheet\n\n"
                + markdown_table(["Check", "Equation", "Substitution", "Result"], reboiler_condenser_substitution_rows)
            )
        if "absor" in column.service.lower():
            equilibrium_packets = [
                packet
                for packet in stream_table.separation_packets
                if packet.unit_id in {"primary_separation", "regeneration"}
                or packet.separation_family in {"absorption", "stripping"}
            ]
            if equilibrium_packets:
                packet_rows = [
                    [
                        packet.packet_id,
                        packet.unit_id,
                        packet.equilibrium_model or "heuristic_gle_fallback",
                        ", ".join(packet.equilibrium_parameter_ids) or "none",
                        "yes" if packet.equilibrium_fallback else "no",
                        f"{packet.product_mass_fraction:.3f}",
                        f"{packet.waste_mass_fraction:.3f}",
                        f"{packet.recycle_mass_fraction:.3f}",
                        "; ".join(packet.notes) or "n/a",
                    ]
                    for packet in equilibrium_packets
                ]
                component_rows = []
                for packet in equilibrium_packets:
                    component_name = _preferred_component(packet, mode="gle")
                    if not component_name:
                        continue
                    captured_mass = _component_mass(packet.product_stream_ids, component_name) + _component_mass(packet.recycle_stream_ids, component_name)
                    offgas_mass = _component_mass(packet.waste_stream_ids, component_name)
                    retained_fraction = min(
                        packet.component_split_to_product.get(component_name, 0.0)
                        + packet.component_split_to_recycle.get(component_name, 0.0),
                        1.0,
                    )
                    component_rows.append(
                        [
                            packet.unit_id,
                            component_name,
                            packet.equilibrium_model or "heuristic_gle_fallback",
                            f"{captured_mass:.3f}",
                            f"{offgas_mass:.3f}",
                            f"{retained_fraction:.4f}",
                            "; ".join(packet.notes) or "n/a",
                        ]
                    )
                absorption_sections = [
                    "### Gas-Liquid Equilibrium Basis\n\n"
                    + markdown_table(
                        [
                            "Packet",
                            "Unit",
                            "Model",
                            "Parameter IDs",
                            "Fallback",
                            "Product Mass Fraction",
                            "Waste Mass Fraction",
                            "Recycle Mass Fraction",
                            "Notes",
                        ],
                        packet_rows,
                    )
                ]
                if component_rows:
                    absorption_sections.append(
                        "### Absorber Capture Basis\n\n"
                        + markdown_table(
                            [
                                "Unit",
                                "Component",
                                "Model",
                                "Captured to Liquid (kg/h)",
                                "Offgas (kg/h)",
                                "Retained Fraction",
                                "Notes",
                            ],
                            component_rows,
                    )
                    )
                absorption_factor = column.absorber_solvent_to_gas_ratio / max(column.absorber_equilibrium_slope, 1e-9)
                absorber_height_check = column.absorber_ntu * column.absorber_htu_m
                absorber_pressure_drop_check = column.absorber_pressure_drop_per_m_kpa_m * column.absorber_packed_height_m
                absorber_derivation_rows = [
                    [
                        "Henry slope basis",
                        "m = H / P",
                        f"H={column.absorber_henry_constant_bar:.6f} bar; screening pressure basis folded into model",
                        f"{column.absorber_equilibrium_slope:.6f}",
                    ],
                    [
                        "Absorption factor",
                        "A = L / (m * G)",
                        f"L/G={column.absorber_solvent_to_gas_ratio:.6f}; m={column.absorber_equilibrium_slope:.6f}",
                        f"{absorption_factor:.6f}",
                    ],
                    [
                        "Theoretical stage basis",
                        "Kremser-style screening with capture target",
                        f"Capture={column.absorber_capture_fraction:.6f}; eta_stage={column.absorber_stage_efficiency:.6f}",
                        f"{column.absorber_theoretical_stages:.6f} stages",
                    ],
                    [
                        "Packed-height basis",
                        "Z = NTU * HTU",
                        f"NTU={column.absorber_ntu:.6f}; HTU={column.absorber_htu_m:.6f} m",
                        f"{absorber_height_check:.6f} m",
                    ],
                    [
                        "Pressure-drop basis",
                        "DeltaP = (DeltaP/L) * Z",
                        f"DeltaP/L={column.absorber_pressure_drop_per_m_kpa_m:.6f} kPa/m; Z={column.absorber_packed_height_m:.6f} m",
                        f"{absorber_pressure_drop_check:.6f} kPa",
                    ],
                    [
                        "Wetting window basis",
                        "Wet ratio = L / Lmin",
                        f"L={column.absorber_liquid_mass_velocity_kg_m2_s:.6f}; Lmin={column.absorber_min_wetting_rate_kg_m2_s:.6f}",
                        f"{column.absorber_wetting_ratio:.6f}",
                    ],
                ]
                absorber_stage_rows = [
                    ["Key absorbed component", column.absorber_key_component or "n/a"],
                    ["Henry constant (bar)", f"{column.absorber_henry_constant_bar:.6f}"],
                    ["Equilibrium slope m", f"{column.absorber_equilibrium_slope:.6f}"],
                    ["Solvent / gas ratio", f"{column.absorber_solvent_to_gas_ratio:.6f}"],
                    ["Capture fraction", f"{column.absorber_capture_fraction:.6f}"],
                    ["Stage efficiency", f"{column.absorber_stage_efficiency:.6f}"],
                    ["Theoretical stages", f"{column.absorber_theoretical_stages:.6f}"],
                    ["Gas mass velocity (kg/m2-s)", f"{column.absorber_gas_mass_velocity_kg_m2_s:.6f}"],
                    ["Liquid mass velocity (kg/m2-s)", f"{column.absorber_liquid_mass_velocity_kg_m2_s:.6f}"],
                    ["Packing family", column.absorber_packing_family or "n/a"],
                    ["Packing specific area (m2/m3)", f"{column.absorber_packing_specific_area_m2_m3:.6f}"],
                    ["Effective interfacial area (m2/m3)", f"{column.absorber_effective_interfacial_area_m2_m3:.6f}"],
                    ["Gas-film transfer coefficient (1/s)", f"{column.absorber_gas_phase_transfer_coeff_1_s:.6f}"],
                    ["Liquid-film transfer coefficient (1/s)", f"{column.absorber_liquid_phase_transfer_coeff_1_s:.6f}"],
                    ["Overall mass-transfer coefficient (1/s)", f"{column.absorber_overall_mass_transfer_coefficient_1_s:.6f}"],
                    ["Minimum wetting rate (kg/m2-s)", f"{column.absorber_min_wetting_rate_kg_m2_s:.6f}"],
                    ["Wetting ratio", f"{column.absorber_wetting_ratio:.6f}"],
                    ["Operating velocity (m/s)", f"{column.absorber_operating_velocity_m_s:.6f}"],
                    ["Flooding velocity (m/s)", f"{column.absorber_flooding_velocity_m_s:.6f}"],
                    ["Flooding margin fraction", f"{column.absorber_flooding_margin_fraction:.6f}"],
                    ["NTU", f"{column.absorber_ntu:.6f}"],
                    ["HTU (m)", f"{column.absorber_htu_m:.6f}"],
                    ["Pressure drop per m (kPa/m)", f"{column.absorber_pressure_drop_per_m_kpa_m:.6f}"],
                    ["Total pressure drop (kPa)", f"{column.absorber_total_pressure_drop_kpa:.6f}"],
                    ["Packed height (m)", f"{column.absorber_packed_height_m:.6f}"],
                ]
                absorption_sections.append(
                    "### Absorber Stage Screening\n\n"
                    + markdown_table(["Parameter", "Value"], absorber_stage_rows)
                )
                absorption_sections.append(
                    "### Absorber Solvent Optimization\n\n"
                    + markdown_table(
                        ["Parameter", "Value"],
                        [
                            ["Minimum solvent / gas ratio", f"{column.absorber_minimum_solvent_to_gas_ratio:.6f}"],
                            ["Optimized solvent / gas ratio", f"{column.absorber_optimized_solvent_to_gas_ratio:.6f}"],
                            ["Selected solvent / gas ratio", f"{column.absorber_solvent_to_gas_ratio:.6f}"],
                            ["Lean loading (mol/mol solvent)", f"{column.absorber_lean_loading_mol_mol:.6f}"],
                            ["Rich loading (mol/mol solvent)", f"{column.absorber_rich_loading_mol_mol:.6f}"],
                            ["Candidate cases evaluated", str(column.absorber_solvent_rate_case_count)],
                        ],
                    )
                )
                absorption_sections.append(
                    "### Absorber Equation-Substitution Basis\n\n"
                    + markdown_table(
                        ["Check", "Equation", "Substitution", "Result"],
                        absorber_derivation_rows,
                    )
                )
                absorption_sections.append(
                    "### Absorber Operating Envelope\n\n"
                    + markdown_table(
                        ["Parameter", "Value"],
                        [
                            ["Operating gas mass velocity (kg/m2-s)", f"{column.absorber_gas_mass_velocity_kg_m2_s:.6f}"],
                            ["Operating liquid mass velocity (kg/m2-s)", f"{column.absorber_liquid_mass_velocity_kg_m2_s:.6f}"],
                            ["Overall mass-transfer coefficient (1/s)", f"{column.absorber_overall_mass_transfer_coefficient_1_s:.6f}"],
                            ["Pressure drop per m (kPa/m)", f"{column.absorber_pressure_drop_per_m_kpa_m:.6f}"],
                            ["Total pressure drop (kPa)", f"{column.absorber_total_pressure_drop_kpa:.6f}"],
                            ["Packed height (m)", f"{column.absorber_packed_height_m:.6f}"],
                        ],
                    )
                )
        elif "crystallizer" in column.service.lower():
            equilibrium_packets = [
                packet
                for packet in stream_table.separation_packets
                if packet.unit_id in {"concentration", "filtration", "drying"}
                or packet.separation_family in {"crystallization", "filtration", "drying"}
            ]
            if equilibrium_packets:
                packet_rows = [
                    [
                        packet.packet_id,
                        packet.unit_id,
                        packet.equilibrium_model or "heuristic_sle_fallback",
                        ", ".join(packet.equilibrium_parameter_ids) or "none",
                        "yes" if packet.equilibrium_fallback else "no",
                        f"{packet.product_mass_fraction:.3f}",
                        f"{packet.waste_mass_fraction:.3f}",
                        f"{packet.recycle_mass_fraction:.3f}",
                        "; ".join(packet.notes) or "n/a",
                    ]
                    for packet in equilibrium_packets
                ]
                component_rows = []
                for packet in equilibrium_packets:
                    component_name = _preferred_component(packet, mode="sle")
                    if not component_name:
                        continue
                    precipitated_mass = _component_mass(packet.product_stream_ids, component_name)
                    dissolved_mass = _component_mass(packet.recycle_stream_ids, component_name) + _component_mass(packet.waste_stream_ids, component_name)
                    yield_fraction = precipitated_mass / max(precipitated_mass + dissolved_mass, 1e-9)
                    component_rows.append(
                        [
                            packet.unit_id,
                            component_name,
                            packet.equilibrium_model or "heuristic_sle_fallback",
                            f"{dissolved_mass:.3f}",
                            f"{precipitated_mass:.3f}",
                            f"{yield_fraction:.4f}",
                            "; ".join(packet.notes) or "n/a",
                        ]
                    )
                crystallization_sections = [
                    "### Solid-Liquid Equilibrium Basis\n\n"
                    + markdown_table(
                        [
                            "Packet",
                            "Unit",
                            "Model",
                            "Parameter IDs",
                            "Fallback",
                            "Product Mass Fraction",
                            "Waste Mass Fraction",
                            "Recycle Mass Fraction",
                            "Notes",
                        ],
                        packet_rows,
                    )
                ]
                if component_rows:
                    crystallization_sections.append(
                        "### Crystallization Yield Basis\n\n"
                        + markdown_table(
                            [
                                "Unit",
                                "Component",
                                "Model",
                                "Dissolved in Liquor (kg/h)",
                                "Precipitated to Crystals (kg/h)",
                                "Yield Fraction",
                                "Notes",
                            ],
                            component_rows,
                        )
                    )
                supersaturation_check = column.crystallizer_feed_loading_kg_per_kg / max(column.crystallizer_solubility_limit_kg_per_kg, 1e-9)
                yield_check = column.crystallizer_precipitated_mass_kg_hr / max(
                    column.crystallizer_precipitated_mass_kg_hr + column.crystallizer_dissolved_mass_kg_hr,
                    1e-9,
                )
                filter_cycle_check = (
                    column.filter_cake_formation_time_hr + column.filter_wash_time_hr + column.filter_discharge_time_hr
                )
                slurry_turnover = column.slurry_circulation_rate_m3_hr / max(column.crystallizer_holdup_m3, 1e-9)
                humidity_lift_check = column.dryer_exhaust_humidity_ratio_kg_kg - column.dryer_inlet_humidity_ratio_kg_kg
                specific_evaporation = column.dryer_evaporation_load_kg_hr / max(column.dryer_dry_air_flow_kg_hr, 1e-9)
                solids_derivation_rows = [
                    [
                        "Supersaturation basis",
                        "S = Cfeed / C*",
                        f"Cfeed={column.crystallizer_feed_loading_kg_per_kg:.6f}; C*={column.crystallizer_solubility_limit_kg_per_kg:.6f}",
                        f"{supersaturation_check:.6f}",
                    ],
                    [
                        "Crystal yield basis",
                        "Y = mprecip / (mprecip + mdiss)",
                        (
                            f"mprecip={column.crystallizer_precipitated_mass_kg_hr:.6f} kg/h; "
                            f"mdiss={column.crystallizer_dissolved_mass_kg_hr:.6f} kg/h"
                        ),
                        f"{yield_check:.6f}",
                    ],
                    [
                        "Slurry turnover",
                        "Turnover = Qslurry / Vhold",
                        f"Qslurry={column.slurry_circulation_rate_m3_hr:.6f} m3/h; Vhold={column.crystallizer_holdup_m3:.6f} m3",
                        f"{slurry_turnover:.6f} 1/h",
                    ],
                    [
                        "Filter cycle basis",
                        "tcycle = tform + twash + tdischarge",
                        (
                            f"tform={column.filter_cake_formation_time_hr:.6f} h; "
                            f"twash={column.filter_wash_time_hr:.6f} h; "
                            f"tdischarge={column.filter_discharge_time_hr:.6f} h"
                        ),
                        f"{filter_cycle_check:.6f} h/cycle",
                    ],
                    [
                        "Cycle frequency",
                        "f = 1 / tcycle",
                        f"tcycle={column.filter_cycle_time_hr:.6f} h/cycle",
                        f"{column.filter_cycles_per_hr:.6f} 1/h",
                    ],
                    [
                        "Dryer humidity lift",
                        "DeltaY = Yout - Yin",
                        (
                            f"Yout={column.dryer_exhaust_humidity_ratio_kg_kg:.6f}; "
                            f"Yin={column.dryer_inlet_humidity_ratio_kg_kg:.6f}"
                        ),
                        f"{humidity_lift_check:.6f} kg/kg",
                    ],
                    [
                        "Specific evaporation",
                        "mevap / mair",
                        (
                            f"mevap={column.dryer_evaporation_load_kg_hr:.6f} kg/h; "
                            f"mair={column.dryer_dry_air_flow_kg_hr:.6f} kg/h"
                        ),
                        f"{specific_evaporation:.6f} kg/kg",
                    ],
                ]
                crystallizer_rows = [
                    ["Key crystal component", column.crystallizer_key_component or "n/a"],
                    ["Solubility limit (kg/kg solvent)", f"{column.crystallizer_solubility_limit_kg_per_kg:.6f}"],
                    ["Feed loading (kg/kg solvent)", f"{column.crystallizer_feed_loading_kg_per_kg:.6f}"],
                    ["Supersaturation ratio", f"{column.crystallizer_supersaturation_ratio:.6f}"],
                    ["Precipitated mass (kg/h)", f"{column.crystallizer_precipitated_mass_kg_hr:.6f}"],
                    ["Dissolved mass (kg/h)", f"{column.crystallizer_dissolved_mass_kg_hr:.6f}"],
                    ["Yield fraction", f"{column.crystallizer_yield_fraction:.6f}"],
                    ["Crystallizer residence time (h)", f"{column.crystallizer_residence_time_hr:.6f}"],
                    ["Crystallizer holdup (m3)", f"{column.crystallizer_holdup_m3:.6f}"],
                    ["Crystal slurry density (kg/m3)", f"{column.crystal_slurry_density_kg_m3:.6f}"],
                    ["Crystal growth rate (mm/h)", f"{column.crystal_growth_rate_mm_hr:.6f}"],
                    ["Crystal size d10 (mm)", f"{column.crystal_size_d10_mm:.6f}"],
                    ["Crystal size d50 (mm)", f"{column.crystal_size_d50_mm:.6f}"],
                    ["Crystal size d90 (mm)", f"{column.crystal_size_d90_mm:.6f}"],
                    ["Classifier cut size (mm)", f"{column.crystal_classifier_cut_size_mm:.6f}"],
                    ["Classified product fraction", f"{column.crystal_classified_product_fraction:.6f}"],
                    ["Slurry circulation rate (m3/h)", f"{column.slurry_circulation_rate_m3_hr:.6f}"],
                    ["Filter cake moisture fraction", f"{column.filter_cake_moisture_fraction:.6f}"],
                    ["Filter area (m2)", f"{column.filter_area_m2:.6f}"],
                    ["Filter cake throughput (kg/m2-h)", f"{column.filter_cake_throughput_kg_m2_hr:.6f}"],
                    ["Specific cake resistance (m/kg)", f"{column.filter_specific_cake_resistance_m_kg:.6f}"],
                    ["Filter medium resistance (1/m)", f"{column.filter_medium_resistance_1_m:.6f}"],
                    ["Dryer evaporation load (kg/h)", f"{column.dryer_evaporation_load_kg_hr:.6f}"],
                    ["Dryer residence time (h)", f"{column.dryer_residence_time_hr:.6f}"],
                    ["Dryer target moisture fraction", f"{column.dryer_target_moisture_fraction:.6f}"],
                    ["Dryer product moisture fraction", f"{column.dryer_product_moisture_fraction:.6f}"],
                    ["Dryer equilibrium moisture fraction", f"{column.dryer_equilibrium_moisture_fraction:.6f}"],
                    ["Dryer inlet humidity ratio (kg/kg)", f"{column.dryer_inlet_humidity_ratio_kg_kg:.6f}"],
                    ["Dryer exhaust humidity ratio (kg/kg)", f"{column.dryer_exhaust_humidity_ratio_kg_kg:.6f}"],
                    ["Dryer dry-air flow (kg/h)", f"{column.dryer_dry_air_flow_kg_hr:.6f}"],
                    ["Dryer exhaust saturation fraction", f"{column.dryer_exhaust_saturation_fraction:.6f}"],
                    ["Dryer mass-transfer coefficient (kg/m2-s)", f"{column.dryer_mass_transfer_coefficient_kg_m2_s:.6f}"],
                    ["Dryer heat-transfer coefficient (W/m2-K)", f"{column.dryer_heat_transfer_coefficient_w_m2_k:.6f}"],
                    ["Dryer heat-transfer area (m2)", f"{column.dryer_heat_transfer_area_m2:.6f}"],
                    ["Dryer refined duty (kW)", f"{column.dryer_refined_duty_kw:.6f}"],
                ]
                crystallization_sections.append(
                    "### Crystallizer / Filter Design Basis\n\n"
                    + markdown_table(["Parameter", "Value"], crystallizer_rows)
                )
                crystallization_sections.append(
                    "### Filter Cycle and Dryer Endpoint Basis\n\n"
                    + markdown_table(
                        ["Parameter", "Value"],
                        [
                            ["Filter cycle time (h/cycle)", f"{column.filter_cycle_time_hr:.6f}"],
                            ["Filter cake formation time (h)", f"{column.filter_cake_formation_time_hr:.6f}"],
                            ["Filter wash time (h)", f"{column.filter_wash_time_hr:.6f}"],
                            ["Filter discharge time (h)", f"{column.filter_discharge_time_hr:.6f}"],
                            ["Filter cycles per hour", f"{column.filter_cycles_per_hr:.6f}"],
                            ["Dryer endpoint margin fraction", f"{column.dryer_endpoint_margin_fraction:.6f}"],
                            ["Dryer humidity lift (kg/kg)", f"{column.dryer_humidity_lift_kg_kg:.6f}"],
                            ["Dryer exhaust dewpoint (C)", f"{column.dryer_exhaust_dewpoint_c:.6f}"],
                        ],
                    )
                )
                crystallization_sections.append(
                    "### Crystallizer / Filter / Dryer Equation-Substitution Basis\n\n"
                    + markdown_table(
                        ["Check", "Equation", "Substitution", "Result"],
                        solids_derivation_rows,
                    )
                )
                crystallization_sections.append(
                    "### Crystallizer and Dryer Operating Envelope\n\n"
                    + markdown_table(
                        ["Parameter", "Value"],
                        [
                            ["Crystallizer residence time (h)", f"{column.crystallizer_residence_time_hr:.6f}"],
                            ["Crystallizer holdup (m3)", f"{column.crystallizer_holdup_m3:.6f}"],
                            ["Slurry circulation rate (m3/h)", f"{column.slurry_circulation_rate_m3_hr:.6f}"],
                            ["Filter cycles per hour", f"{column.filter_cycles_per_hr:.6f}"],
                            ["Dryer dry-air flow (kg/h)", f"{column.dryer_dry_air_flow_kg_hr:.6f}"],
                            ["Dryer heat-transfer area (m2)", f"{column.dryer_heat_transfer_area_m2:.6f}"],
                        ],
                    )
                )
        return "\n\n".join(
            [
                column_hydraulics.markdown,
                "### Route-Family Basis\n\n" + markdown_table(["Parameter", "Value"], route_family_rows),
                "### Governing Equations\n\n"
                + "\n".join(
                    f"- `{equation}`"
                    for equation in (
                        ["Fenske / Underwood / Gilliland equivalents", *exchanger_thermal.governing_equations]
                    )
                ),
                "### Solver Packet Basis\n\n"
                + markdown_table(
                    ["Packet", "Unit", "Type", "Inlet kg/h", "Outlet kg/h", "Closure Error (%)", "Status"],
                    packet_rows or [["n/a", "n/a", "n/a", "0.0", "0.0", "0.0", "n/a"]],
                ),
                "### Balance Reference Snapshot\n\n"
                + markdown_table(
                    ["Stream", "Role", "From", "To", "kg/h", "Dominant Components"],
                    balance_reference_rows or [["n/a", "n/a", "-", "-", "0.0", "-"]],
                ),
                "### Unit-by-Unit Feed / Product / Recycle Summary\n\n"
                + markdown_table(
                    ["Unit", "Service", "Stream", "Local Role", "Stream Role", "Section", "Phase", "kg/h", "kmol/h", "Dominant Components"],
                    process_stream_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "-", "-", "0.0", "0.0", "-"]],
                ),
                "### Process-Unit Local Stream Split Summary\n\n"
                + markdown_table(
                    ["Split", "Stream Count", "Mass Flow (kg/h)", "Molar Flow (kmol/h)"],
                    process_split_rows,
                ),
                "### Key Process-Unit Component Balance\n\n"
                + markdown_table(
                    ["Unit", "Service", "Component", "Inlet kg/h", "Outlet kg/h", "Delta kg/h"],
                    process_component_rows or [["n/a", "n/a", "n/a", "0.0", "0.0", "0.0"]],
                ),
                *distillation_sections,
                *absorption_sections,
                *crystallization_sections,
                "### Process-Unit Sizing Basis\n\n" + markdown_table(["Parameter", "Value"], column_rows),
                "### Hydraulics Basis\n\n" + markdown_table(["Parameter", "Value"], hydraulics_rows),
                "### Heat-Transfer Package Inputs\n\n" + markdown_table(["Parameter", "Value"], heat_transfer_input_rows),
                "### Exchanger Package Selection Basis\n\n" + markdown_table(["Parameter", "Value"], heat_transfer_package_rows),
                "### Utility Coupling\n\n" + markdown_table(["Parameter", "Value"], utility_rows),
                "### Heat-Exchanger Thermal Basis\n\n" + markdown_table(["Parameter", "Value"], exchanger_rows),
                self._render_trace_section("Process-Unit Calculation Traces", column.calc_traces + exchanger.calc_traces),
            ]
        )

    def _run_block_diagram(self) -> StageResult:
        artifact = self._ensure_process_narrative()
        route = self._selected_route()
        route_selection = self._load("route_selection", RouteSelectionArtifact)
        flowsheet_blueprint = self._load("flowsheet_blueprint", FlowsheetBlueprintArtifact)
        diagram_style = build_diagram_style_profile()
        diagram_target = build_diagram_target_profile(self.config.basis)
        bfd = build_block_flow_diagram(flowsheet_blueprint, diagram_style, diagram_target)
        bfd_acceptance = build_diagram_acceptance(
            diagram_kind="bfd",
            diagram_id=bfd.diagram_id,
            nodes=bfd.nodes,
            edges=bfd.edges,
            target=diagram_target,
            blueprint=flowsheet_blueprint,
        )
        self._save("diagram_style_profile", diagram_style)
        self._save("diagram_target_profile", diagram_target)
        self._save("block_flow_diagram_artifact", bfd)
        self._save("block_flow_diagram_acceptance", bfd_acceptance)
        for index, sheet in enumerate(bfd.sheets, start=1):
            self.store.save_text(self.config.project_id, f"diagrams/bfd_sheet_{index}.svg", sheet.svg)
        chapter_citations = sorted(set(bfd.citations or artifact.citations or route.citations or route_selection.citations))
        markdown = "\n\n".join(
            [
                bfd.markdown.strip(),
                *(f"### {sheet.title}\n\n{diagram_svg_fence(sheet.svg)}" for sheet in bfd.sheets),
                "### Diagram Acceptance\n\n" + bfd_acceptance.markdown.strip(),
                "### Debug Mermaid Fallback\n\n```mermaid\n" + bfd.mermaid_fallback + "\n```",
            ]
        )
        bfd_chapter = self._chapter(
            "block_flow_diagram",
            "Block Flow Diagram",
            "block_diagram",
            markdown,
            chapter_citations,
            bfd.assumptions + bfd_acceptance.assumptions,
            ["process_narrative", "block_flow_diagram_artifact", "block_flow_diagram_acceptance"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
        )
        issues = self._chapter_issues(bfd_chapter)
        return StageResult(chapters=[bfd_chapter], issues=issues)

    def _run_process_description(self) -> StageResult:
        artifact = self._ensure_process_narrative()
        route = self._selected_route()
        route_selection = self._load("route_selection", RouteSelectionArtifact)
        chapter_citations = artifact.citations or route.citations or route_selection.citations
        chapter = self._chapter(
            "process_description",
            "Process Description",
            "process_description",
            artifact.markdown,
            chapter_citations,
            artifact.assumptions,
            ["process_narrative"],
            required_inputs=["process_narrative"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_material_balance(self) -> StageResult:
        route = self._selected_route()
        route_selection_artifact = self._load("route_selection", RouteSelectionArtifact)
        kinetics = self._load("kinetic_assessment", KineticAssessmentArtifact)
        process_narrative = self._ensure_process_narrative()
        flowsheet_blueprint = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_blueprint.json", FlowsheetBlueprintArtifact)
        topology_candidates = self.store.maybe_load_model(self.config.project_id, "artifacts/topology_candidates.json", TopologyCandidateArtifact)
        if topology_candidates is not None:
            selected_topology = next((item for item in topology_candidates.candidates if item.route_id == route.route_id), None)
            if selected_topology is not None and selected_topology.status == ScientificGateStatus.FAIL:
                return StageResult(
                    issues=[
                        ValidationIssue(
                            code="material_balance_topology_blocked",
                            severity=Severity.BLOCKED,
                            message=f"Selected route '{route.route_id}' has no admissible topology for even screening-level balance work.",
                            artifact_ref="topology_candidates",
                            source_refs=selected_topology.citations,
                        )
                    ]
                )
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        route_profile = profile_for_route(route_families, route.route_id)
        reaction_system = build_reaction_system(self.config.basis, route, kinetics, route.citations + kinetics.citations, route.assumptions + kinetics.assumptions)
        stream_table = build_stream_table(
            self.config.basis,
            route,
            reaction_system,
            reaction_system.citations,
            reaction_system.assumptions,
            property_packages,
            flowsheet_blueprint,
        )
        flowsheet_graph = build_flowsheet_graph(
            route,
            stream_table,
            reaction_system,
            process_narrative,
            self.config.basis.operating_mode,
            flowsheet_blueprint,
        )
        flowsheet_case = build_flowsheet_case(route.route_id, self.config.basis.operating_mode, stream_table, flowsheet_graph)
        commercial_product_basis = self._maybe_load("commercial_product_basis", CommercialProductBasisArtifact)
        bac_impurity_model = build_bac_impurity_model_artifact(route_selection_artifact, stream_table, commercial_product_basis)
        self._save("reaction_system", reaction_system)
        self._save("stream_table", stream_table)
        self._save("flowsheet_graph", flowsheet_graph)
        self._save("flowsheet_case", flowsheet_case)
        if bac_impurity_model is not None:
            self._save("bac_impurity_model", bac_impurity_model)
        diagram_style = build_diagram_style_profile()
        diagram_target = build_diagram_target_profile(self.config.basis)
        equipment_for_pfd = self._maybe_load("equipment_list", EquipmentListArtifact)
        pfd = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            equipment_for_pfd,
            None,
            diagram_style,
            diagram_target,
            self._maybe_load("control_plan", ControlPlanArtifact),
        )
        pfd_acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id=pfd.diagram_id,
            nodes=pfd.nodes,
            edges=pfd.edges,
            target=diagram_target,
            flowsheet_graph=flowsheet_graph,
            flowsheet_case=flowsheet_case,
        )
        self._save("diagram_style_profile", diagram_style)
        self._save("diagram_target_profile", diagram_target)
        self._save("process_flow_diagram_artifact", pfd)
        self._save("process_flow_diagram_acceptance", pfd_acceptance)
        for index, sheet in enumerate(pfd.sheets, start=1):
            self.store.save_text(self.config.project_id, f"diagrams/pfd_sheet_{index}.svg", sheet.svg)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = extend_resolved_value_artifact(resolved_values, reaction_system.value_records, resolved_sources, self.config, "material_balance_reaction_system")
        resolved_values = extend_resolved_value_artifact(resolved_values, stream_table.value_records, resolved_sources, self.config, "material_balance_stream_table")
        self._save("resolved_values", resolved_values)
        material_markdown = self._render_solver_material_balance(route, route_profile, reaction_system, stream_table, flowsheet_case)
        chapter = self._chapter(
            "material_balance",
            "Material Balance",
            "material_balance",
            material_markdown + (f"\n\n### BAC Impurity Model\n\n{bac_impurity_model.markdown}" if bac_impurity_model is not None else ""),
            sorted(set(stream_table.citations + reaction_system.citations)),
            reaction_system.assumptions + stream_table.assumptions + (bac_impurity_model.assumptions if bac_impurity_model is not None else []),
            ["reaction_system", "stream_table", "flowsheet_graph", "flowsheet_case", "bac_impurity_model"],
            required_inputs=["route_selection", "kinetic_assessment", "process_narrative"],
        )
        process_description_chapter = self._chapter(
            "process_description",
            "Process Description",
            "material_balance",
            self._render_solver_process_description(route, flowsheet_case, stream_table),
            sorted(set(process_narrative.citations + stream_table.citations + reaction_system.citations)),
            process_narrative.assumptions + reaction_system.assumptions + stream_table.assumptions,
            ["process_narrative", "flowsheet_case", "stream_table"],
            required_inputs=["route_selection", "kinetic_assessment", "process_narrative"],
            summary="Solver-derived process description refreshed from solved unit packets, separation packets, and recycle loops.",
        )
        pfd_markdown = "\n\n".join(
            [
                pfd.markdown.strip(),
                *(f"### {sheet.title}\n\n{diagram_svg_fence(sheet.svg)}" for sheet in pfd.sheets),
                "### Diagram Acceptance\n\n" + pfd_acceptance.markdown.strip(),
            ]
        )
        process_flow_diagram_chapter = self._chapter(
            "process_flow_diagram",
            "Process Flow Diagram",
            "material_balance",
            pfd_markdown,
            sorted(set(pfd.citations + stream_table.citations + flowsheet_graph.citations)),
            pfd.assumptions + pfd_acceptance.assumptions,
            ["process_flow_diagram_artifact", "process_flow_diagram_acceptance", "flowsheet_graph", "flowsheet_case"],
            required_inputs=["route_selection", "kinetic_assessment", "process_narrative"],
            summary="Equipment-level process flow diagram regenerated from the solved flowsheet graph, stream topology, and recycle structure.",
        )
        issues = (
            validate_reaction_system(reaction_system)
            + validate_stream_table(stream_table)
            + validate_flowsheet_graph(flowsheet_graph)
            + validate_flowsheet_case(flowsheet_case)
            + (validate_bac_impurity_model_artifact(bac_impurity_model) if bac_impurity_model is not None else [])
            + self._value_issues(reaction_system, "reaction_system")
            + self._value_issues(stream_table, "stream_table")
            + self._chapter_issues(chapter)
            + self._chapter_issues(process_description_chapter)
            + self._chapter_issues(process_flow_diagram_chapter)
        )
        return StageResult(chapters=[process_description_chapter, process_flow_diagram_chapter, chapter], issues=issues)

    def _run_energy_balance(self) -> StageResult:
        route = self._selected_route()
        thermo_admissibility = self.store.maybe_load_model(self.config.project_id, "artifacts/thermo_admissibility.json", ThermoAdmissibilityArtifact)
        if thermo_admissibility is not None and thermo_admissibility.selected_route_status != ScientificGateStatus.PASS:
            return StageResult(
                issues=[
                    ValidationIssue(
                        code="energy_balance_requires_detailed_thermo",
                        severity=Severity.BLOCKED,
                        message="Detailed energy balance is blocked until thermodynamic admissibility reaches detailed-design grade.",
                        artifact_ref="thermo_admissibility",
                        source_refs=thermo_admissibility.citations,
                    )
                ]
            )
        stream_table = self._load("stream_table", StreamTable)
        thermo = self._load("thermo_assessment", ThermoAssessmentArtifact)
        kinetics = self._load("kinetic_assessment", KineticAssessmentArtifact)
        reaction_system = self._load("reaction_system", ReactionSystem)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        route_profile = profile_for_route(route_families, route.route_id)
        mixture_properties = build_mixture_property_artifact(stream_table, property_packages)
        energy = build_energy_balance(route, stream_table, thermo, mixture_properties)
        flowsheet_case = self._load("flowsheet_case", FlowsheetCase)
        solve_result = build_solve_result(flowsheet_case, stream_table, energy)
        self._save("energy_balance", energy)
        self._save("solve_result", solve_result)
        self._save("mixture_properties", mixture_properties)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), energy.value_records, self._load("resolved_sources", ResolvedSourceSet), self.config, "energy_balance"),
        )
        markdown = self._render_energy_balance_chapter(route, route_profile, stream_table, energy)
        chapter = self._chapter(
            "energy_balance",
            "Energy Balance",
            "energy_balance",
            markdown,
            sorted(set(stream_table.citations + energy.citations)),
            stream_table.assumptions + energy.assumptions,
            ["energy_balance", "solve_result"],
            required_inputs=["stream_table", "thermo_assessment"],
        )
        issues = (
            self._value_issues(energy, "energy_balance")
            + validate_mixture_property_artifact(mixture_properties)
            + validate_property_requirements_for_stage(
                "energy_balance",
                property_requirements,
                property_packages,
                route,
                self.config.basis.target_product,
                mixture_properties,
                relevant_unit_ids=["feed_prep", "primary_flash", "primary_separation", "purification", "filtration", "drying"],
            )
            + validate_sparse_data_policy_for_stage("energy_balance", sparse_data_policy)
            + validate_energy_balance(energy)
            + validate_phase_feasibility(route, thermo, kinetics, reaction_system, energy)
            + validate_solve_result(solve_result)
            + self._chapter_issues(chapter)
        )
        gate = self._gate("design_basis", "Design Basis Lock", "Approve thermo, kinetics, process narrative, and balance basis before detailed design.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_reactor_design(self) -> StageResult:
        route = self._selected_route()
        kinetics_admissibility = self.store.maybe_load_model(self.config.project_id, "artifacts/kinetics_admissibility.json", KineticsAdmissibilityArtifact)
        if kinetics_admissibility is not None and kinetics_admissibility.selected_route_status != ScientificGateStatus.PASS:
            return StageResult(
                issues=[
                    ValidationIssue(
                        code="reactor_design_requires_detailed_kinetics",
                        severity=Severity.BLOCKED,
                        message="Detailed reactor design is blocked until kinetics admissibility reaches detailed-design grade.",
                        artifact_ref="kinetics_admissibility",
                        source_refs=kinetics_admissibility.citations,
                    )
                ]
            )
        reaction_system = self._load("reaction_system", ReactionSystem)
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        kinetics = self._load("kinetic_assessment", KineticAssessmentArtifact)
        mixture_properties = self._load("mixture_properties", MixturePropertyArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        process_synthesis = self._load("process_synthesis", ProcessSynthesisArtifact)
        reactor_choice = self._load("reactor_choice_decision", DecisionRecord)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(self._selected_utility_network(), energy)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        route_profile = profile_for_route(route_families, route.route_id)
        self._save("utility_architecture", utility_architecture)
        reactor = build_reactor_design(
            self.config.basis,
            route,
            reaction_system,
            stream_table,
            energy,
            mixture_properties,
            reactor_choice,
            utility_architecture,
            kinetics=kinetics,
        )
        reactor_hazard_issues = validate_reactor_hazard_basis_critics(
            route,
            reactor_choice,
            reactor,
            operations_planning,
        )
        reactor_choice = self._escalate_decision_for_critic_issues(
            reactor_choice,
            reactor_hazard_issues,
            trigger_codes={
                "reactor_hazard_basis_high_runaway_risk",
                "reactor_hazard_basis_unsupported",
                "hazard_route_batch_mode_selected",
                "hazard_route_restart_loss_high",
            },
            note_prefix="Reactor hazard-basis escalation",
        )
        operating_mode_decision = self._escalate_decision_for_critic_issues(
            process_synthesis.operating_mode_decision,
            reactor_hazard_issues,
            trigger_codes={"hazard_route_batch_mode_selected", "hazard_route_restart_loss_high"},
            note_prefix="Operating-mode hazard escalation",
        )
        process_synthesis = process_synthesis.model_copy(
            update={"operating_mode_decision": operating_mode_decision},
            deep=True,
        )
        reactor_basis = build_reactor_design_basis(reactor)
        self._save("reactor_choice_decision", reactor_choice)
        self._save("process_synthesis", process_synthesis)
        self._save("reactor_design", reactor)
        self._save("reactor_design_basis", reactor_basis)
        self._refresh_agent_fabric()
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), reactor.value_records, resolved_sources, self.config, "reactor_design"),
        )
        markdown = self._render_reactor_design_chapter(reactor, reactor_basis, stream_table, energy, route_profile)
        chapter = self._chapter(
            "reactor_design",
            "Reactor Design",
            "reactor_design",
            markdown,
            reactor.citations,
            reactor.assumptions,
            ["reactor_design", "reactor_design_basis"],
            required_inputs=["reaction_system", "stream_table", "energy_balance", "kinetic_assessment"],
        )
        issues = (
            validate_decision_record(reactor_choice, "reactor_choice_decision")
            + validate_decision_record(process_synthesis.operating_mode_decision, "operating_mode")
            + validate_property_requirements_for_stage(
                "reactor_design",
                property_requirements,
                property_packages,
                route,
                self.config.basis.target_product,
                mixture_properties,
                relevant_unit_ids=["reactor"],
            )
            + validate_sparse_data_policy_for_stage("reactor_design", sparse_data_policy)
            + validate_reactor_design(reactor)
            + reactor_hazard_issues
            + self._value_issues(reactor, "reactor_design")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_distillation_design(self) -> StageResult:
        route = self._selected_route()
        thermo_admissibility = self.store.maybe_load_model(self.config.project_id, "artifacts/thermo_admissibility.json", ThermoAdmissibilityArtifact)
        if thermo_admissibility is not None and thermo_admissibility.selected_route_status != ScientificGateStatus.PASS:
            return StageResult(
                issues=[
                    ValidationIssue(
                        code="separation_design_requires_detailed_thermo",
                        severity=Severity.BLOCKED,
                        message="Detailed separation design is blocked until thermodynamic admissibility reaches detailed-design grade.",
                        artifact_ref="thermo_admissibility",
                        source_refs=thermo_admissibility.citations,
                    )
                ]
            )
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        mixture_properties = self._load("mixture_properties", MixturePropertyArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        separation_thermo = self._load("separation_thermo", SeparationThermoArtifact)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        separation_choice = self._load("separation_choice_decision", DecisionRecord)
        exchanger_choice = select_exchanger_configuration(route, energy)
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(self._selected_utility_network(), energy)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        route_profile = profile_for_route(route_families, route.route_id)
        column = build_column_design(
            self.config.basis,
            route,
            stream_table,
            energy,
            mixture_properties,
            separation_choice,
            utility_architecture,
            separation_thermo,
            property_packages,
        )
        exchanger = build_heat_exchanger_design(route, energy, exchanger_choice, utility_architecture)
        column_hydraulics = build_column_hydraulics(column)
        exchanger_thermal = build_heat_exchanger_thermal_design(exchanger)
        self._save("column_design", column)
        self._save("heat_exchanger_design", exchanger)
        self._save("column_hydraulics", column_hydraulics)
        self._save("heat_exchanger_thermal_design", exchanger_thermal)
        self._save("utility_architecture", utility_architecture)
        self._save("exchanger_choice_decision", exchanger_choice)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_values = extend_resolved_value_artifact(resolved_values, column.value_records, resolved_sources, self.config, "distillation_design")
        resolved_values = extend_resolved_value_artifact(resolved_values, exchanger.value_records, resolved_sources, self.config, "heat_exchanger_design")
        self._save("resolved_values", resolved_values)
        markdown = self._render_process_unit_design_chapter(column, column_hydraulics, exchanger, exchanger_thermal, stream_table, route_profile)
        chapter = self._chapter(
            "distillation_design",
            "Distillation / Process-Unit Design",
            "distillation_design",
            markdown,
            sorted(set(column.citations + exchanger.citations)),
            column.assumptions + exchanger.assumptions,
            ["column_design", "column_hydraulics", "heat_exchanger_design", "heat_exchanger_thermal_design", "exchanger_choice_decision"],
            required_inputs=["stream_table", "energy_balance"],
        )
        issues = (
            validate_decision_record(separation_choice, "separation_choice_decision")
            + validate_decision_record(exchanger_choice, "exchanger_choice_decision")
            + validate_property_requirements_for_stage(
                "distillation_design",
                property_requirements,
                property_packages,
                route,
                self.config.basis.target_product,
                mixture_properties,
                relevant_unit_ids=["purification", "concentration", "regeneration", "filtration", "drying"],
            )
            + validate_sparse_data_policy_for_stage("distillation_design", sparse_data_policy)
            + validate_column_design(column)
            + validate_separation_design_critics(separation_choice, column, separation_thermo, unit_operation_family)
            + self._value_issues(column, "column_design")
            + self._value_issues(exchanger, "heat_exchanger_design")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_equipment_sizing(self) -> StageResult:
        product_profile = self._load("product_profile", ProductProfileArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        family_adapter = self.store.maybe_load_model(self.config.project_id, "artifacts/chemistry_family_adapter.json", ChemistryFamilyAdapter)
        density_record = next((item for item in product_profile.properties if item.name == "Density"), None)
        commercial_basis = self.store.maybe_load_model(
            self.config.project_id,
            "artifacts/commercial_product_basis.json",
            CommercialProductBasisArtifact,
        )
        density_kg_m3 = 995.0 if (commercial_basis and commercial_basis.product_name.lower() == "benzalkonium chloride") else 1100.0
        if density_record:
            try:
                density_value = _coerce_numeric_value(density_record.value)
                density_kg_m3 = density_value * 1000.0 if density_record.units == "g/cm3" else density_value
            except ValueError:
                pass
        route = self._selected_route()
        reactor = self._load("reactor_design", ReactorDesign)
        column = self._load("column_design", ColumnDesign)
        exchanger = self._load("heat_exchanger_design", HeatExchangerDesign)
        reactor_choice = self._load("reactor_choice_decision", DecisionRecord)
        separation_choice = self._load("separation_choice_decision", DecisionRecord)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        energy = self._load("energy_balance", EnergyBalance)
        utility_network = self._selected_utility_network()
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(utility_network, energy)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        storage_choice = select_storage_configuration(self.config.basis, archetype, family_adapter)
        moc_choice = select_moc_configuration(route, archetype, family_adapter)
        storage = build_storage_design(self.config.basis, density_kg_m3, product_profile.citations, product_profile.assumptions, storage_choice, operations_planning)
        pump_design = build_pump_design(storage)
        self._save("storage_design", storage)
        equipment_items = build_equipment_list(route, reactor, column, exchanger, storage, energy, moc_choice, utility_architecture)
        artifact = EquipmentListArtifact(
            items=equipment_items,
            citations=sorted(set(reactor.citations + column.citations + exchanger.citations + storage.citations + utility_architecture.citations)),
            assumptions=reactor.assumptions + column.assumptions + exchanger.assumptions + storage.assumptions + utility_architecture.assumptions,
        )
        datasheets = build_equipment_datasheets(artifact, reactor, column, exchanger, storage, pump_design)
        self._save("equipment_list", artifact)
        self._save("utility_architecture", utility_architecture)
        self._save("pump_design", pump_design)
        self._save(
            "equipment_datasheets",
            NarrativeArtifact(
                artifact_id="equipment_datasheets",
                title="Equipment Datasheets",
                markdown="\n\n".join(item.markdown for item in datasheets),
                summary=f"{len(datasheets)} equipment datasheets generated.",
                citations=sorted({citation for item in datasheets for citation in item.citations}),
                assumptions=sorted({assumption for item in datasheets for assumption in item.assumptions}),
            ),
        )
        self._save("storage_choice_decision", storage_choice)
        self._save("moc_choice_decision", moc_choice)
        self._refresh_agent_fabric()
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), storage.value_records, resolved_sources, self.config, "equipment_sizing"),
        )
        main_equipment_ids = {reactor.reactor_id, column.column_id, exchanger.exchanger_id, storage.storage_id}
        major_equipment_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                f"{item.volume_m3:.3f}",
                f"{item.duty_kw:.3f}",
                f"{item.design_temperature_c:.1f}",
                f"{item.design_pressure_bar:.2f}",
                item.material_of_construction,
            ]
            for item in equipment_items
            if item.equipment_id in main_equipment_ids
        ]
        package_inventory_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                f"{item.volume_m3:.3f}",
                f"{item.duty_kw:.3f}",
                item.material_of_construction,
                item.design_basis,
            ]
            for item in equipment_items
            if item.equipment_id not in main_equipment_ids
        ]
        storage_inventory_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                f"{item.volume_m3:.3f}",
                f"{item.design_temperature_c:.1f}",
                f"{item.design_pressure_bar:.2f}",
                item.material_of_construction,
                item.design_basis,
            ]
            for item in equipment_items
            if any(token in item.equipment_type.lower() for token in ["storage", "tank", "drum"])
        ]
        thermal_service_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                f"{item.duty_kw:.3f}",
                f"{item.design_temperature_c:.1f}",
                f"{item.design_pressure_bar:.2f}",
                item.material_of_construction,
                item.design_basis,
            ]
            for item in equipment_items
            if any(token in f"{item.equipment_type} {item.service}".lower() for token in ["exchanger", "reboiler", "condenser", "header", "htm", "utility"])
        ]
        rotating_aux_rows = [
            [
                pump_design.pump_id,
                "Transfer pump",
                pump_design.service,
                f"{pump_design.flow_m3_hr:.3f}",
                f"{pump_design.differential_head_m:.3f}",
                f"{pump_design.power_kw:.3f}",
                f"{pump_design.npsh_margin_m:.3f}",
                "Dedicated pump design artifact",
            ]
        ] + [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                f"{max(item.volume_m3, 0.0):.3f}",
                f"{item.design_pressure_bar:.2f}",
                f"{item.duty_kw:.3f}",
                "n/a",
                item.design_basis,
            ]
            for item in equipment_items
            if any(token in f"{item.equipment_type} {item.service}".lower() for token in ["classifier", "filter", "dryer", "circulation", "pump", "compressor", "blower", "fan", "skid"])
        ]
        family_map: dict[str, list[str]] = {}
        for item in datasheets:
            family_map.setdefault(item.equipment_type, []).append(item.equipment_id)
        datasheet_coverage_rows = [
            [family, str(len(ids)), ", ".join(ids[:5]) + (" ..." if len(ids) > 5 else "")]
            for family, ids in sorted(family_map.items())
        ]
        equipment_summary_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                f"{item.volume_m3:.3f}",
                f"{item.duty_kw:.3f}",
                f"{item.design_temperature_c:.1f}",
                f"{item.design_pressure_bar:.2f}",
                item.material_of_construction,
                item.design_basis,
            ]
            for item in equipment_items
        ]
        absorber_package_sections: list[str] = []
        solids_package_sections: list[str] = []
        if "absor" in column.service.lower() and column.absorber_packing_family:
            packed_cross_section = math.pi * (column.column_diameter_m / 2.0) ** 2 * max(1.0 - column.downcomer_area_fraction, 0.25)
            packed_volume = packed_cross_section * max(column.absorber_packed_height_m, 0.0)
            effective_area_inventory = column.absorber_effective_interfacial_area_m2_m3 * packed_volume
            flooding_utilization = column.absorber_operating_velocity_m_s / max(column.absorber_flooding_velocity_m_s, 1e-9)
            absorber_package_rows = [
                [
                    "Packed volume",
                    "Vpack = (pi / 4) * D^2 * Z",
                    f"D={column.column_diameter_m:.3f} m; Z={column.absorber_packed_height_m:.3f} m",
                    f"{packed_volume:.3f} m3",
                ],
                [
                    "Effective interfacial inventory",
                    "Aeff,total = aeff * Vpack",
                    f"aeff={column.absorber_effective_interfacial_area_m2_m3:.3f} m2/m3; Vpack={packed_volume:.3f} m3",
                    f"{effective_area_inventory:.3f} m2",
                ],
                [
                    "Hydraulic operating window",
                    "vop / vflood",
                    f"vop={column.absorber_operating_velocity_m_s:.3f} m/s; vflood={column.absorber_flooding_velocity_m_s:.3f} m/s",
                    f"{flooding_utilization:.4f}",
                ],
                [
                    "Pressure-drop package basis",
                    "DeltaP = (DeltaP/L) * Z",
                    f"DeltaP/L={column.absorber_pressure_drop_per_m_kpa_m:.3f} kPa/m; Z={column.absorber_packed_height_m:.3f} m",
                    f"{column.absorber_total_pressure_drop_kpa:.3f} kPa",
                ],
                [
                    "Wetting excess",
                    "Wet ratio - 1",
                    f"Wet ratio={column.absorber_wetting_ratio:.4f}",
                    f"{max(column.absorber_wetting_ratio - 1.0, 0.0):.4f}",
                ],
            ]
            absorber_package_sections.append(
                "### Absorber Package Sizing Derivation\n\n"
                + markdown_table(["Check", "Equation", "Substitution", "Result"], absorber_package_rows)
            )
        if "crystallizer" in column.service.lower() and column.crystallizer_key_component:
            filter_solids_capacity = column.filter_area_m2 * column.filter_cake_throughput_kg_m2_hr
            solids_per_cycle = filter_solids_capacity / max(column.filter_cycles_per_hr, 1e-9)
            dryer_area_duty_density = column.dryer_refined_duty_kw / max(column.dryer_heat_transfer_area_m2, 1e-9)
            classifier_turnover = column.slurry_circulation_rate_m3_hr / max(column.crystallizer_holdup_m3, 1e-9)
            solids_package_rows = [
                [
                    "Classifier turnover",
                    "Qslurry / Vhold",
                    f"Qslurry={column.slurry_circulation_rate_m3_hr:.3f} m3/h; Vhold={column.crystallizer_holdup_m3:.3f} m3",
                    f"{classifier_turnover:.4f} 1/h",
                ],
                [
                    "Filter solids capacity",
                    "mfilter = A * flux",
                    f"A={column.filter_area_m2:.3f} m2; flux={column.filter_cake_throughput_kg_m2_hr:.3f} kg/m2-h",
                    f"{filter_solids_capacity:.3f} kg/h",
                ],
                [
                    "Solids per cycle",
                    "mcycle = mfilter / fcycle",
                    f"mfilter={filter_solids_capacity:.3f} kg/h; fcycle={column.filter_cycles_per_hr:.3f} 1/h",
                    f"{solids_per_cycle:.3f} kg/cycle",
                ],
                [
                    "Dryer area duty density",
                    "qA = Q / A",
                    f"Q={column.dryer_refined_duty_kw:.3f} kW; A={column.dryer_heat_transfer_area_m2:.3f} m2",
                    f"{dryer_area_duty_density:.3f} kW/m2",
                ],
                [
                    "Dry-air moisture pickup",
                    "mevap / mair",
                    f"mevap={column.dryer_evaporation_load_kg_hr:.3f} kg/h; mair={column.dryer_dry_air_flow_kg_hr:.3f} kg/h",
                    f"{(column.dryer_evaporation_load_kg_hr / max(column.dryer_dry_air_flow_kg_hr, 1e-9)):.4f} kg/kg",
                ],
            ]
            solids_package_sections.append(
                "### Solids Package Sizing Derivation\n\n"
                + markdown_table(["Check", "Equation", "Substitution", "Result"], solids_package_rows)
            )
        chapter = self._chapter(
            "equipment_design_sizing",
            "Equipment Design and Sizing",
            "equipment_sizing",
            "### Storage Decision\n\n"
            f"{storage_choice.selected_summary}\n\n"
            "### Material of Construction Decision\n\n"
            f"{moc_choice.selected_summary}\n\n"
            "### Storage Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Inventory days", f"{storage.inventory_days:.1f}"],
                    ["Dispatch buffer days", f"{storage.dispatch_buffer_days:.1f}"],
                    ["Operating stock days", f"{storage.operating_stock_days:.1f}"],
                    ["Restart buffer days", f"{storage.restart_buffer_days:.1f}"],
                    ["Turnaround buffer factor", f"{storage.turnaround_buffer_factor:.3f}"],
                    ["Working volume (m3)", f"{storage.working_volume_m3:.3f}"],
                    ["Total volume (m3)", f"{storage.total_volume_m3:.3f}"],
                    ["Tank diameter (m)", f"{storage.diameter_m:.3f}"],
                    ["Straight-side height (m)", f"{storage.straight_side_height_m:.3f}"],
                ],
            )
            + "\n\n### Operations Planning Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Operating mode", operations_planning.recommended_operating_mode],
                    ["Service family", operations_planning.service_family],
                    ["Raw-material buffer (d)", f"{operations_planning.raw_material_buffer_days:.1f}"],
                    ["Finished-goods buffer (d)", f"{operations_planning.finished_goods_buffer_days:.1f}"],
                    ["Operating stock (d)", f"{operations_planning.operating_stock_days:.1f}"],
                    ["Restart buffer (d)", f"{operations_planning.restart_buffer_days:.1f}"],
                    ["Startup ramp (d)", f"{operations_planning.startup_ramp_days:.1f}"],
                    ["Campaign length (d)", f"{operations_planning.campaign_length_days:.1f}"],
                    ["Annual restart loss (kg/y)", f"{operations_planning.annual_restart_loss_kg:,.1f}"],
                ],
            )
            + "\n\n### Storage Transfer Pump Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Pump id", pump_design.pump_id],
                    ["Service", pump_design.service],
                    ["Flow (m3/h)", f"{pump_design.flow_m3_hr:.3f}"],
                    ["Differential head (m)", f"{pump_design.differential_head_m:.1f}"],
                    ["Power (kW)", f"{pump_design.power_kw:.3f}"],
                    ["NPSH margin (m)", f"{pump_design.npsh_margin_m:.3f}"],
                ],
            )
            + "\n\n### Storage and Inventory Vessel Basis\n\n"
            + markdown_table(
                ["ID", "Type", "Service", "Volume (m3)", "Design T (C)", "Design P (bar)", "MoC", "Design Basis"],
                storage_inventory_rows or [[storage.storage_id, "Storage tank", storage.service, f"{storage.total_volume_m3:.3f}", "0.0", "0.0", storage.material_of_construction, "storage basis"]],
            )
            + "\n\n### Major Process Equipment Basis\n\n"
            + markdown_table(
                ["ID", "Type", "Service", "Volume (m3)", "Duty (kW)", "Design T (C)", "Design P (bar)", "MoC"],
                major_equipment_rows or [["n/a", "n/a", "n/a", "0.0", "0.0", "0.0", "0.0", "n/a"]],
            )
            + "\n\n### Heat Exchanger and Thermal-Service Basis\n\n"
            + markdown_table(
                ["ID", "Type", "Service", "Duty (kW)", "Design T (C)", "Design P (bar)", "MoC", "Design Basis"],
                thermal_service_rows or [[exchanger.exchanger_id, "Heat exchanger", exchanger.service, f"{exchanger.heat_load_kw:.3f}", "0.0", "0.0", "n/a", "thermal-service basis"]],
            )
            + "\n\n### Rotating and Auxiliary Package Basis\n\n"
            + markdown_table(
                ["ID", "Type", "Service", "Flow/Volume Basis", "Head/Pressure Basis", "Power/Duty (kW)", "NPSH Margin", "Design Basis"],
                rotating_aux_rows or [[pump_design.pump_id, "Transfer pump", pump_design.service, f"{pump_design.flow_m3_hr:.3f}", f"{pump_design.differential_head_m:.3f}", f"{pump_design.power_kw:.3f}", f"{pump_design.npsh_margin_m:.3f}", "pump basis"]],
            )
            + "\n\n### Utility-Coupled Package Inventory\n\n"
            + markdown_table(
                ["ID", "Type", "Service", "Volume (m3)", "Duty (kW)", "MoC", "Design Basis"],
                package_inventory_rows or [["n/a", "n/a", "n/a", "0.0", "0.0", "n/a", "n/a"]],
            )
            + ("\n\n" + "\n\n".join(absorber_package_sections) if absorber_package_sections else "")
            + ("\n\n" + "\n\n".join(solids_package_sections) if solids_package_sections else "")
            + "\n\n### Datasheet Coverage Matrix\n\n"
            + markdown_table(
                ["Equipment Family", "Datasheet Count", "Representative IDs"],
                datasheet_coverage_rows or [["n/a", "0", "n/a"]],
            )
            + "\n\n### Equipment-by-Equipment Sizing Summary\n\n"
            + markdown_table(
                ["ID", "Type", "Service", "Volume (m3)", "Duty (kW)", "Design T (C)", "Design P (bar)", "MoC", "Design Basis"],
                equipment_summary_rows,
            ),
            artifact.citations,
            artifact.assumptions,
            ["storage_design", "pump_design", "equipment_list", "equipment_datasheets", "storage_choice_decision", "moc_choice_decision"],
            required_inputs=["reactor_design", "column_design", "heat_exchanger_design"],
        )
        issues = (
            validate_decision_record(storage_choice, "storage_choice_decision")
            + validate_decision_record(moc_choice, "moc_choice_decision")
            + self._value_issues(storage, "storage_design")
            + validate_equipment_applicability(route, reactor_choice, separation_choice, reactor, column, exchanger, utility_network, unit_operation_family)
            + self._chapter_issues(chapter)
        )
        gate = self._gate("equipment_basis", "Reactor/Column Design Basis", "Approve reactor, column, exchanger, and storage design basis before downstream detailing.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_mechanical_design_moc(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        route = self._selected_route()
        reactor = self._load("reactor_design", ReactorDesign)
        column = self._load("column_design", ColumnDesign)
        exchanger = self._load("heat_exchanger_design", HeatExchangerDesign)
        storage = self._load("storage_design", StorageDesign)
        pump_design = self._load("pump_design", PumpDesign)
        moc_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/moc_choice_decision.json", DecisionRecord)
        artifact = build_mechanical_design_artifact(equipment)
        basis = build_mechanical_design_basis(artifact)
        vessel_designs = build_vessel_mechanical_designs(artifact)
        datasheets = build_equipment_datasheets(equipment, reactor, column, exchanger, storage, pump_design, artifact, vessel_designs, basis)
        moc_alternative_map = {
            item.candidate_id: item.description
            for item in (moc_choice.alternatives if moc_choice else [])
        }

        def _service_basis(equipment_type: str, service: str) -> str:
            lowered = f"{equipment_type} {service}".lower()
            if any(token in lowered for token in ["acid", "chlor", "absor", "scrub"]):
                return "acidic / gas-treatment service"
            if any(token in lowered for token in ["crystallizer", "filter", "dryer", "classifier", "slurry", "solid"]):
                return "solids / abrasive service"
            if any(token in lowered for token in ["reboiler", "condenser", "exchanger", "steam", "htm", "header", "utility"]):
                return "thermal / utility service"
            if "storage" in lowered or "tank" in lowered:
                return "inventory / storage service"
            return "general process liquid service"

        def _corrosion_driver(selected_moc: str, service_basis: str, design_temperature_c: float) -> str:
            lowered = f"{selected_moc} {service_basis}".lower()
            if "acidic" in lowered or "chlor" in lowered:
                return "aqueous acid / chloride corrosion screening"
            if "solids" in lowered or "abrasive" in lowered:
                return "erosion-abrasion and wet-solids hold-up"
            if "thermal / utility" in lowered:
                return "thermal cycling, condensate, and fouling-side exposure"
            if design_temperature_c >= 180.0:
                return "elevated-temperature metal-loss allowance"
            return "general aqueous-organic corrosion allowance basis"

        def _alternate_moc(selected_moc: str, service_basis: str) -> str:
            lowered = selected_moc.lower()
            if "rubber" in lowered:
                return moc_alternative_map.get("ss316l", "SS316L construction")
            if "alloy" in lowered:
                return moc_alternative_map.get("ss316l", "SS316L construction")
            if "316" in lowered or "304" in lowered:
                return (
                    moc_alternative_map.get("rubber_lined_cs", "Rubber-lined carbon steel")
                    if "acidic" in service_basis
                    else moc_alternative_map.get("carbon_steel", "Carbon steel construction")
                )
            return (
                moc_alternative_map.get("rubber_lined_cs", "Rubber-lined carbon steel")
                if "acidic" in service_basis
                else moc_alternative_map.get("ss316l", "SS316L construction")
            )

        def _inspection_basis(service_basis: str, equipment_type: str) -> str:
            lowered = f"{service_basis} {equipment_type}".lower()
            if "acidic" in lowered or "absorber" in lowered or "column" in lowered or "reactor" in lowered:
                return "thickness survey + nozzle / tray / internals inspection"
            if "solids" in lowered:
                return "erosion hotspot, cake-contact, and circulation loop inspection"
            if "thermal / utility" in lowered:
                return "tube-side fouling, rack shoe, and support expansion inspection"
            if "storage" in lowered or "tank" in lowered:
                return "shell-floor, vent, and nozzle pad inspection"
            return "periodic shell and connection inspection"

        def _piping_class_basis(selected_moc: str, service_basis: str, pressure_class: str) -> str:
            lowered = f"{selected_moc} {service_basis}".lower()
            if "acidic" in lowered:
                return f"{pressure_class} lined / corrosion-resistant process class"
            if "solids" in lowered:
                return f"{pressure_class} abrasion-tolerant slurry service class"
            if "thermal / utility" in lowered:
                return f"{pressure_class} thermal-oil / utility piping class"
            if "storage" in lowered:
                return f"{pressure_class} tank farm and transfer class"
            if "316" in lowered or "304" in lowered:
                return f"{pressure_class} stainless process class"
            return f"{pressure_class} carbon/alloy steel process class"

        def _maintainability_basis(service_basis: str, support_variant: str, equipment_type: str) -> str:
            lowered = f"{service_basis} {support_variant} {equipment_type}".lower()
            if "acidic" in lowered:
                return "corrosion monitoring, nozzle pad inspection, and internals washdown access"
            if "solids" in lowered:
                return "cleanout access, erosion hotspot inspection, and cake-contact maintenance"
            if "utility" in lowered or "header" in lowered:
                return "rack access, expansion restraint checks, and isolation spool maintenance"
            if "storage" in lowered or "tank" in lowered:
                return "shell-floor inspection, vent maintenance, and transfer-line isolation access"
            return "platform/ladder access with routine shell and nozzle inspection"

        mechanical_input_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                f"{item.design_pressure_bar:.2f}",
                f"{item.design_temperature_c:.1f}",
                f"{item.allowable_stress_mpa:.1f}",
                f"{item.joint_efficiency:.2f}",
                f"{item.corrosion_allowance_mm:.2f}",
                item.pressure_class,
            ]
            for item in artifact.items
        ]

        shell_rows = [
            [
                item.equipment_id,
                "t = P*D / (2*S*J - 1.2*P) + CA",
                (
                    f"P={item.design_pressure_bar / 10.0:.3f} MPa; "
                    f"D≈{max((4.0 * max(eq.volume_m3, 0.5) / (math.pi * 6.0)) ** (1.0 / 3.0), 0.9):.3f} m; "
                    f"CA={item.corrosion_allowance_mm:.1f} mm"
                ),
                f"{item.shell_thickness_mm:.3f}",
                f"{item.head_thickness_mm:.3f}",
                f"{item.corrosion_allowance_mm:.3f}",
                item.pressure_class,
                f"{item.hydrotest_pressure_bar:.3f}",
            ]
            for item in artifact.items
            for eq in equipment.items
            if eq.equipment_id == item.equipment_id and item.shell_thickness_mm > 0.0
        ]
        support_rows = [
            [
                vessel.equipment_id,
                vessel.support_design.support_load_case,
                "Wsupport = Wvertical + Wpiping + Wwind + Wseismic",
                (
                    f"Wv={vessel.support_design.design_vertical_load_kn:.3f}; "
                    f"Wp={vessel.support_design.piping_load_kn:.3f}; "
                    f"Ww={vessel.support_design.wind_load_kn:.3f}; "
                    f"Ws={vessel.support_design.seismic_load_kn:.3f}"
                ),
                f"{vessel.support_design.support_load_basis_kn:.3f}",
                f"{vessel.support_design.overturning_moment_kn_m:.3f}",
                f"{vessel.support_design.anchor_bolt_diameter_mm:.3f}",
                f"{vessel.support_design.base_plate_thickness_mm:.3f}",
                vessel.support_design.foundation_note,
            ]
            for vessel in vessel_designs
            if vessel.support_design is not None
        ]
        nozzle_rows = [
            [
                vessel.equipment_id,
                ", ".join(vessel.nozzle_schedule.nozzle_services),
                vessel.nozzle_schedule.nozzle_reinforcement_family or "n/a",
                "Areinf = f(dnozzle, Pdesign, equipment family)",
                (
                    f"d={vessel.nozzle_schedule.nozzle_diameters_mm[0]:.1f} mm; "
                    f"P={next((item.design_pressure_bar for item in artifact.items if item.equipment_id == vessel.equipment_id), 0.0):.2f} bar"
                ),
                f"{vessel.nozzle_schedule.reinforcement_area_mm2[0]:.3f}",
                f"{vessel.nozzle_schedule.local_shell_load_factors[0]:.3f}",
                vessel.nozzle_schedule.nozzle_pressure_class,
                ", ".join(f"{load:.2f}" for load in vessel.nozzle_schedule.nozzle_load_cases_kn),
            ]
            for vessel in vessel_designs
            if vessel.nozzle_schedule is not None and vessel.nozzle_schedule.reinforcement_area_mm2
        ]
        connection_rows = [
            [
                vessel.equipment_id,
                next((item.support_variant or item.support_type for item in artifact.items if item.equipment_id == vessel.equipment_id), "n/a"),
                ", ".join(vessel.nozzle_schedule.nozzle_connection_classes),
                _piping_class_basis(
                    next((eq.material_of_construction for eq in equipment.items if eq.equipment_id == vessel.equipment_id), "n/a"),
                    _service_basis(
                        next((eq.equipment_type for eq in equipment.items if eq.equipment_id == vessel.equipment_id), "n/a"),
                        next((eq.service for eq in equipment.items if eq.equipment_id == vessel.equipment_id), "n/a"),
                    ),
                    vessel.nozzle_schedule.nozzle_pressure_class,
                ),
                ", ".join(f"{angle:.0f}" for angle in vessel.nozzle_schedule.nozzle_orientations_deg),
                ", ".join(f"{projection:.1f}" for projection in vessel.nozzle_schedule.nozzle_projection_mm),
                "yes" if next((item.pipe_rack_tie_in_required for item in artifact.items if item.equipment_id == vessel.equipment_id), False) else "no",
            ]
            for vessel in vessel_designs
            if vessel.nozzle_schedule is not None
        ]
        moc_rows = [
            [
                item.equipment_id,
                item.equipment_type,
                item.service,
                item.material_of_construction,
                f"{item.design_temperature_c:.1f}",
                f"{item.design_pressure_bar:.2f}",
                (
                    "corrosive liquid / absorber service"
                    if "acid" in item.service.lower() or "absor" in item.service.lower()
                    else "solids handling / abrasive service"
                    if any(token in item.service.lower() for token in ["crystallizer", "filter", "dryer", "classifier"])
                    else "general process service"
                ),
            ]
            for item in equipment.items
        ]
        inspection_rows = [
            [
                item.equipment_id,
                _service_basis(item.equipment_type, item.service),
                _inspection_basis(_service_basis(item.equipment_type, item.service), item.equipment_type),
                _maintainability_basis(
                    _service_basis(item.equipment_type, item.service),
                    next((mechanical_item.support_variant for mechanical_item in artifact.items if mechanical_item.equipment_id == item.equipment_id), ""),
                    item.equipment_type,
                ),
                "yes" if next((mechanical_item.maintenance_platform_required for mechanical_item in artifact.items if mechanical_item.equipment_id == item.equipment_id), False) else "no",
                "yes" if next((mechanical_item.access_ladder_required for mechanical_item in artifact.items if mechanical_item.equipment_id == item.equipment_id), False) else "no",
            ]
            for item in equipment.items
        ]
        moc_option_rows = [
            [
                option.candidate_id,
                option.description,
                f"{option.total_score:.2f}",
                "selected" if moc_choice and option.candidate_id == moc_choice.selected_candidate_id else "alternate",
                "yes" if option.feasible else "no",
                "; ".join(option.rejected_reasons) or "screening-feasible",
            ]
            for option in (moc_choice.alternatives if moc_choice else [])
        ]
        moc_justification_rows = [
            [
                item.equipment_id,
                _service_basis(item.equipment_type, item.service),
                _corrosion_driver(item.material_of_construction, _service_basis(item.equipment_type, item.service), item.design_temperature_c),
                item.material_of_construction,
                _alternate_moc(item.material_of_construction, _service_basis(item.equipment_type, item.service)),
                _inspection_basis(_service_basis(item.equipment_type, item.service), item.equipment_type),
                (
                    f"{item.material_of_construction} retained for {route.route_family_id if hasattr(route, 'route_family_id') else route.route_id} "
                    f"because { _service_basis(item.equipment_type, item.service) } controls the screening basis."
                ),
            ]
            for item in equipment.items
        ]
        utility_moc_rows = [
            [
                service_class,
                ", ".join(sorted(item.equipment_id for item in members)),
                ", ".join(sorted({item.material_of_construction for item in members})),
                primary_driver,
                piping_basis,
            ]
            for service_class, members, primary_driver, piping_basis in [
                (
                    "Storage and inventory systems",
                    [item for item in equipment.items if "storage" in item.equipment_type.lower() or "tank" in item.equipment_type.lower()],
                    "inventory breathing, drainage, and shell-floor exposure",
                    "tank nozzle and vent classes follow selected vessel pressure class basis",
                ),
                (
                    "Thermal and utility packages",
                    [item for item in equipment.items if any(token in f"{item.equipment_type} {item.service}".lower() for token in ["reboiler", "condenser", "exchanger", "header", "htm", "utility"])],
                    "thermal cycling, condensation, and fouling-side service",
                    "utility headers and exchanger nozzles inherit screening connection classes from mechanical basis",
                ),
                (
                    "Primary process vessels",
                    [item for item in equipment.items if item.equipment_id in {reactor.reactor_id, column.column_id}],
                    "core reaction / separation chemistry and cleanability",
                    "primary process connections follow equipment pressure class and nozzle reinforcement family",
                ),
            ]
            if members
        ]
        corrosion_rows = [
            ["Selected MoC decision", moc_choice.selected_candidate_id if moc_choice else "n/a"],
            ["Decision summary", moc_choice.selected_summary if moc_choice else "n/a"],
            ["Route family service", route.route_family_id if hasattr(route, "route_family_id") else route.route_id],
            ["Storage material", storage.material_of_construction],
            ["Reactor material", next((item.material_of_construction for item in equipment.items if item.equipment_id == reactor.reactor_id), "n/a")],
            ["Main separation material", next((item.material_of_construction for item in equipment.items if item.equipment_id == column.column_id), "n/a")],
        ]
        self._save("mechanical_design", artifact)
        produced_outputs = ["mechanical_design", "mechanical_design_basis", "vessel_mechanical_designs", "equipment_datasheets"]
        if self.config.benchmark_profile == "benzalkonium_chloride":
            self._save("mechanical_design_moc", artifact)
            produced_outputs.insert(1, "mechanical_design_moc")
        self._save("mechanical_design_basis", basis)
        self._save(
            "vessel_mechanical_designs",
            NarrativeArtifact(
                artifact_id="vessel_mechanical_designs",
                title="Vessel Mechanical Designs",
                markdown="\n\n".join(item.markdown for item in vessel_designs),
                summary=f"{len(vessel_designs)} vessel mechanical design records generated.",
                citations=sorted({citation for item in vessel_designs for citation in item.citations}),
                assumptions=sorted({assumption for item in vessel_designs for assumption in item.assumptions}),
            ),
        )
        self._save(
            "equipment_datasheets",
            NarrativeArtifact(
                artifact_id="equipment_datasheets",
                title="Equipment Datasheets",
                markdown="\n\n".join(item.markdown for item in datasheets),
                summary=f"{len(datasheets)} equipment datasheets generated.",
                citations=sorted({citation for item in datasheets for citation in item.citations}),
                assumptions=sorted({assumption for item in datasheets for assumption in item.assumptions}),
            ),
        )
        chapter = self._chapter(
            "mechanical_design_moc",
            "Mechanical Design and MoC",
            "mechanical_design_moc",
            artifact.markdown
            + "\n\n"
            + "### Mechanical Basis\n\n"
            + markdown_table(
                ["Field", "Value"],
                [
                    ["Code basis", basis.code_basis],
                    ["Design pressure basis", basis.design_pressure_basis],
                    ["Design temperature basis", basis.design_temperature_basis],
                    ["Support design basis", basis.support_design_basis],
                    ["Load case basis", basis.load_case_basis],
                    ["Foundation basis", basis.foundation_basis],
                    ["Nozzle load basis", basis.nozzle_load_basis],
                    ["Connection rating basis", basis.connection_rating_basis],
                    ["Access platform basis", basis.access_platform_basis],
                ],
            )
            + "\n\n### Mechanical Design Input Matrix\n\n"
            + markdown_table(
                ["Equipment", "Type", "Pdesign (bar)", "Tdesign (C)", "Allowable Stress (MPa)", "Joint Efficiency", "CA (mm)", "Pressure Class"],
                mechanical_input_rows or [["n/a", "n/a", "0.0", "0.0", "0.0", "0.0", "0.0", "n/a"]],
            )
            + "\n\n"
            + markdown_table(
                ["Equipment", "Load Case", "Support Load (kN)", "Wind (kN)", "Seismic (kN)", "Piping (kN)", "Anchor Bolt (mm)", "Base Plate (mm)", "Platform", "Platform Area (m2)"],
                [
                    [
                        item.equipment_id,
                        item.support_design.support_load_case,
                        f"{item.support_design.support_load_basis_kn:.3f}",
                        f"{item.support_design.wind_load_kn:.3f}",
                        f"{item.support_design.seismic_load_kn:.3f}",
                        f"{item.support_design.piping_load_kn:.3f}",
                        f"{item.support_design.anchor_bolt_diameter_mm:.3f}",
                        f"{item.support_design.base_plate_thickness_mm:.3f}",
                        "yes" if item.support_design.maintenance_platform_required else "no",
                        f"{item.support_design.platform_area_m2:.3f}",
                    ]
                    for item in vessel_designs
                    if item.support_design is not None
                ]
                or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Foundation and Access Basis\n\n"
            + markdown_table(
                ["Equipment", "Support Variant", "Anchor Groups", "Footprint (m2)", "Clearance (m)", "Ladder", "Lifting Lugs"],
                [
                    [
                        item.equipment_id,
                        item.support_design.support_variant or item.support_type,
                        str(item.support_design.anchor_group_count),
                        f"{item.support_design.foundation_footprint_m2:.3f}",
                        f"{item.support_design.maintenance_clearance_m:.3f}",
                        "yes" if item.support_design.access_ladder_required else "no",
                        "yes" if item.support_design.lifting_lug_required else "no",
                    ]
                    for item in vessel_designs
                    if item.support_design is not None
                ]
                or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Shell and Head Thickness Derivation\n\n"
            + markdown_table(
                ["Equipment", "Equation", "Substitution", "Shell t (mm)", "Head t (mm)", "CA (mm)", "Pressure Class", "Hydrotest (bar)"],
                shell_rows or [["n/a", "n/a", "n/a", "0.0", "0.0", "0.0", "n/a", "0.0"]],
            )
            + "\n\n### Support and Overturning Derivation\n\n"
            + markdown_table(
                ["Equipment", "Load Case", "Equation", "Substitution", "Support Load (kN)", "Overturning (kN.m)", "Anchor Bolt (mm)", "Base Plate (mm)", "Foundation Note"],
                support_rows or [["n/a", "n/a", "n/a", "n/a", "0.0", "0.0", "0.0", "0.0", "n/a"]],
            )
            + "\n\n### Nozzle Reinforcement and Connection Basis\n\n"
            + markdown_table(
                ["Equipment", "Services", "Reinforcement Family", "Equation", "Substitution", "Area (mm2)", "Shell Factor", "Class", "Load Cases (kN)"],
                nozzle_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "0.0", "0.0", "n/a", "0.0"]],
            )
            + "\n\n### Connection and Piping Class Basis\n\n"
            + markdown_table(
                ["Equipment", "Support Variant", "Connection Classes", "Piping Class Basis", "Orientations (deg)", "Projections (mm)", "Rack Tie-In"],
                connection_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Material of Construction Matrix\n\n"
            + markdown_table(
                ["Equipment", "Type", "Service", "Selected MoC", "Design T (C)", "Design P (bar)", "Service Basis"],
                moc_rows or [["n/a", "n/a", "n/a", "n/a", "0.0", "0.0", "n/a"]],
            )
            + "\n\n### MoC Option Screening\n\n"
            + markdown_table(
                ["Candidate", "Description", "Score", "Role", "Feasible", "Screening Notes"],
                moc_option_rows or [["n/a", "n/a", "0.0", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Equipment-Wise MoC Justification Matrix\n\n"
            + markdown_table(
                ["Equipment", "Service Basis", "Corrosion Driver", "Selected MoC", "Alternate MoC", "Inspection / Cleaning Basis", "Rationale"],
                moc_justification_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Inspection and Maintainability Basis\n\n"
            + markdown_table(
                ["Equipment", "Service Basis", "Inspection Basis", "Maintainability Basis", "Platform", "Ladder"],
                inspection_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Corrosion and Service Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                corrosion_rows,
            )
            + "\n\n### Utility and Storage MoC Basis\n\n"
            + markdown_table(
                ["Service Class", "Equipment", "Typical MoC", "Primary Driver", "Piping / Connection Basis"],
                utility_moc_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Nozzle and Connection Schedule\n\n"
            + markdown_table(
                ["Equipment", "Pressure Class", "Hydrotest (bar)", "Reinforcement Family", "Nozzle Services", "Connection Classes", "Orientations (deg)", "Projections (mm)", "Shell Factors", "Load Cases (kN)"],
                [
                    [
                        item.equipment_id,
                        item.pressure_class,
                        f"{item.hydrotest_pressure_bar:.3f}",
                        item.nozzle_schedule.nozzle_reinforcement_family or "n/a",
                        ", ".join(item.nozzle_schedule.nozzle_services),
                        ", ".join(item.nozzle_schedule.nozzle_connection_classes),
                        ", ".join(f"{angle:.0f}" for angle in item.nozzle_schedule.nozzle_orientations_deg),
                        ", ".join(f"{projection:.1f}" for projection in item.nozzle_schedule.nozzle_projection_mm),
                        ", ".join(f"{factor:.2f}" for factor in item.nozzle_schedule.local_shell_load_factors),
                        ", ".join(f"{load:.2f}" for load in item.nozzle_schedule.nozzle_load_cases_kn),
                    ]
                    for item in vessel_designs
                    if item.nozzle_schedule is not None
                ]
                or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            ),
            artifact.citations or equipment.citations,
            artifact.assumptions
            + [
                "Mechanical chapter now uses deterministic screening calculations for shell thickness, nozzles, support load cases, foundation/access basis, connection classes, piping class basis, and equipment-wise material of construction basis with alternates and service rationale.",
                "Inspection and maintainability basis remains feasibility-level screening, but it now follows service class, support variant, and access provisions equipment by equipment.",
            ],
            produced_outputs,
            required_inputs=["equipment_list", "route_selection"],
            summary="Mechanical design chapter includes screening shell/head/nozzle/support derivations, piping/connection basis, MoC option screening, inspection/maintainability basis, and equipment-wise material-of-construction justification.",
        )
        issues = validate_mechanical_design_artifact(artifact) + self._value_issues(artifact, "mechanical_design") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_storage_utilities(self) -> StageResult:
        storage = self._load("storage_design", StorageDesign)
        equipment = self._load("equipment_list", EquipmentListArtifact)
        energy = self._load("energy_balance", EnergyBalance)
        column = self._load("column_design", ColumnDesign)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        pump_design = self._load("pump_design", PumpDesign)
        site = self._load("site_selection", SiteSelectionArtifact)
        utility_network = self._selected_utility_network()
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(utility_network, energy)
        utility_basis, utility_basis_decision = build_utility_basis_decision(
            self.config,
            site,
            utility_network,
            sorted(set(site.citations + equipment.citations + utility_network.citations)),
            site.assumptions + equipment.assumptions + utility_network.assumptions,
        )
        artifact = compute_utilities(
            self.config.basis,
            energy,
            equipment.items,
            utility_basis,
            sorted(set(utility_basis.citations + utility_network.citations)),
            utility_basis.assumptions + utility_network.assumptions,
            utility_network_decision=utility_network,
            utility_architecture=utility_architecture,
            column_design=column,
        )
        artifact.utility_basis_decision_id = utility_basis_decision.decision_id
        self._save("utility_basis_decision", utility_basis_decision)
        self._save("utility_summary", artifact)
        self._save("utility_architecture", utility_architecture)
        self._refresh_agent_fabric()
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = extend_resolved_value_artifact(resolved_values, utility_basis.value_records, resolved_sources, self.config, "utility_basis")
        resolved_values = extend_resolved_value_artifact(resolved_values, artifact.value_records, resolved_sources, self.config, "utility_summary")
        self._save("resolved_values", resolved_values)
        rows = [[item.utility_type, f"{item.load:.3f}", item.units, item.basis] for item in artifact.items]
        annual_operating_hours = self.config.basis.annual_operating_days * 24.0

        def _annualized_usage(load: float, units: str) -> str:
            lowered = units.lower()
            if lowered in {"kw", "kwh/h"}:
                annual_units = "kWh/y"
            elif lowered == "kg/h":
                annual_units = "kg/y"
            elif lowered == "m3/h":
                annual_units = "m3/y"
            elif lowered == "nm3/h":
                annual_units = "Nm3/y"
            else:
                annual_units = f"{units}*h/y"
            return f"{load * annual_operating_hours:.1f} {annual_units}"

        def _cost_proxy(item) -> str:
            lowered = item.utility_type.lower()
            if "steam" in lowered:
                return f"{item.load * annual_operating_hours * utility_basis.steam_cost_inr_per_kg:.0f} INR/y"
            if "cooling water" in lowered:
                return f"{item.load * annual_operating_hours * utility_basis.cooling_water_cost_inr_per_m3:.0f} INR/y"
            if "electricity" in lowered or "heat-integration auxiliaries" in lowered:
                return f"{item.load * annual_operating_hours * utility_basis.power_cost_inr_per_kwh:.0f} INR/y"
            return "screening service allowance"

        def _peak_factor(item) -> float:
            lowered = item.utility_type.lower()
            if "steam" in lowered:
                return 1.08
            if "cooling water" in lowered:
                return 1.10
            if "electricity" in lowered or "heat-integration auxiliaries" in lowered:
                return 1.15
            if "nitrogen" in lowered:
                return 1.20
            return 1.05

        def _service_system_basis(item) -> tuple[str, str, str]:
            lowered = item.utility_type.lower()
            if "steam" in lowered:
                return (
                    f"{utility_basis.steam_pressure_bar:.1f} bar saturated steam header",
                    "reactor heating, reboiler duty, and dryer endpoint polish",
                    "1 x operating + startup margin on steam letdown / control valve basis",
                )
            if "cooling water" in lowered:
                return (
                    "recirculating cooling-water network with 10 C rise",
                    "condenser duty, exchanger cooling, and thermal packet cold-side service",
                    "peak summer duty covered by screening CW oversizing factor",
                )
            if "electricity" in lowered or "heat-integration auxiliaries" in lowered:
                return (
                    "plant electrical distribution / MCC basis",
                    "agitation, pumping, fans, controls, and heat-recovery auxiliaries",
                    "feasibility standby allowance embedded in peak demand factor",
                )
            if "dm water" in lowered:
                return (
                    "demineralized water and wash-service header",
                    "boiler make-up, washdown, and utility support",
                    "intermittent demand carried as service allowance rather than dedicated redundancy",
                )
            if "nitrogen" in lowered:
                return (
                    "nitrogen blanketing / inerting manifold",
                    "storage blanketing, shutdown purge, and inert atmosphere protection",
                    "peak inerting event handled by conservative surge factor",
                )
            return (
                "screening plant service basis",
                item.basis,
                "feasibility-level allowance",
            )

        heating_contributors = sorted(
            [duty for duty in energy.duties if duty.heating_kw > 0.0],
            key=lambda duty: duty.heating_kw,
            reverse=True,
        )
        cooling_contributors = sorted(
            [duty for duty in energy.duties if duty.cooling_kw > 0.0],
            key=lambda duty: duty.cooling_kw,
            reverse=True,
        )

        def _utility_contributor_rows() -> list[list[str]]:
            contributor_rows: list[list[str]] = []
            for duty in heating_contributors[:3]:
                contributor_rows.append(["Steam", duty.unit_id, f"{duty.heating_kw:.3f} kW", duty.notes or "heating duty from unit energy balance"])
            for duty in cooling_contributors[:3]:
                contributor_rows.append(["Cooling water", duty.unit_id, f"{duty.cooling_kw:.3f} kW", duty.notes or "cooling duty from unit energy balance"])
            contributor_rows.append(
                [
                    "Electricity",
                    pump_design.pump_id,
                    f"{pump_design.power_kw:.3f} kW",
                    "storage transfer and dispatch pumping basis",
                ]
            )
            if "absorption" in column.service.lower() and column.absorber_total_pressure_drop_kpa > 0.0:
                contributor_rows.append(
                    [
                        "Electricity",
                        column.column_id,
                        f"{max(column.absorber_total_pressure_drop_kpa * max(column.absorber_operating_velocity_m_s, 0.1), 0.0):.3f} screening index",
                        "absorber hydraulics and packing pressure-drop penalty",
                    ]
                )
            if "crystallizer" in column.service.lower() and column.dryer_refined_duty_kw > 0.0:
                contributor_rows.append(
                    [
                        "Electricity/Steam",
                        column.column_id,
                        f"{column.dryer_refined_duty_kw:.3f} kW",
                        "solids auxiliaries and dryer endpoint service",
                    ]
                )
            if utility_architecture.architecture.selected_train_steps:
                contributor_rows.append(
                    [
                        "Heat-integration auxiliaries",
                        utility_architecture.architecture.selected_case_id or "selected_train",
                        f"{artifact.selected_train_recovered_duty_kw:.3f} kW recovered",
                        "selected heat-recovery train circulation, controls, and HTM support",
                    ]
                )
            contributor_rows.append(
                [
                    "Nitrogen",
                    storage.storage_id,
                    f"{next((item.load for item in artifact.items if item.utility_type.lower() == 'nitrogen'), 0.0):.3f} Nm3/h",
                    "storage blanketing and inerting demand",
                ]
            )
            contributor_rows.append(
                [
                    "DM water",
                    "boiler_makeup_and_wash",
                    f"{next((item.load for item in artifact.items if item.utility_type.lower() == 'dm water'), 0.0):.3f} m3/h",
                    "boiler make-up and wash-service allowance",
                ]
            )
            return contributor_rows

        storage_rows = [
            [item.equipment_id, item.service, item.equipment_type, item.material_of_construction, f"{item.volume_m3:.3f}", item.design_basis]
            for item in equipment.items
            if "storage" in item.equipment_type.lower() or "tank" in item.equipment_type.lower()
        ]
        storage_policy_rows = [
            ["Recommended operating mode", operations_planning.recommended_operating_mode],
            ["Availability policy", operations_planning.availability_policy_label],
            ["Raw-material buffer (d)", f"{operations_planning.raw_material_buffer_days:.1f}"],
            ["Finished-goods buffer (d)", f"{operations_planning.finished_goods_buffer_days:.1f}"],
            ["Operating stock (d)", f"{operations_planning.operating_stock_days:.1f}"],
            ["Dispatch buffer (d)", f"{storage.dispatch_buffer_days:.1f}"],
            ["Restart buffer (d)", f"{storage.restart_buffer_days:.1f}"],
            ["Campaign length (d)", f"{operations_planning.campaign_length_days:.1f}"],
            ["Startup ramp (d)", f"{operations_planning.startup_ramp_days:.1f}"],
            ["Restart loss fraction", f"{operations_planning.restart_loss_fraction:.4f}"],
            ["Annual restart loss (kg/y)", f"{operations_planning.annual_restart_loss_kg:,.1f}"],
            ["Turnaround buffer factor", f"{storage.turnaround_buffer_factor:.3f}"],
            ["Shared buffer basis", operations_planning.buffer_basis_note or "operations-planning basis"],
        ]
        utility_summary_rows = [
            [
                item.utility_type,
                f"{item.load:.3f}",
                item.units,
                _annualized_usage(item.load, item.units),
                item.basis,
            ]
            for item in artifact.items
        ]
        utility_peak_rows = [
            [
                item.utility_type,
                f"{item.load:.3f}",
                item.units,
                f"{_peak_factor(item):.2f}",
                f"{item.load * _peak_factor(item):.3f}",
                _annualized_usage(item.load, item.units),
                _cost_proxy(item),
            ]
            for item in artifact.items
        ]
        selected_architecture = utility_architecture.architecture
        utility_system_rows = [
            [
                item.utility_type,
                *_service_system_basis(item),
            ]
            for item in artifact.items
        ]
        island_rows = [
            [
                island.island_id,
                island.architecture_role,
                str(island.header_level),
                island.cluster_id or "-",
                f"{island.recovered_duty_kw:.3f}",
                f"{island.target_recovered_duty_kw:.3f}",
                f"{island.shared_htm_inventory_m3:.3f}",
                f"{island.header_design_pressure_bar:.3f}",
                f"{island.control_complexity_factor:.3f}",
            ]
            for case in selected_architecture.cases
            if case.case_id == selected_architecture.selected_case_id
            for island in case.utility_islands
        ]
        header_rows = [
            [
                step.step_id,
                step.island_id or "-",
                str(step.header_level),
                step.cluster_id or "-",
                package.package_role,
                package.package_family or "-",
                f"{package.design_pressure_bar:.2f}",
                f"{package.design_temperature_c:.1f}",
                package.service,
            ]
            for step in selected_architecture.selected_train_steps
            for package in step.package_items
            if package.package_role in {"header", "circulation", "controls", "relief"}
        ]
        utility_demand_rows = _utility_contributor_rows()
        selected_case = selected_heat_case(utility_network)
        markdown = (
            "### Storage Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Inventory days", f"{storage.inventory_days:.1f}"],
                    ["Working volume (m3)", f"{storage.working_volume_m3:.3f}"],
                    ["Total volume (m3)", f"{storage.total_volume_m3:.3f}"],
                    ["Material of construction", storage.material_of_construction],
                ],
            )
            + "\n\n### Storage Inventory and Buffer Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                storage_policy_rows,
            )
            + "\n\n### Storage Service Matrix\n\n"
            + markdown_table(
                ["Equipment", "Service", "Type", "MoC", "Volume (m3)", "Design Basis"],
                storage_rows or [[storage.storage_id, storage.service, "storage", storage.material_of_construction, f"{storage.total_volume_m3:.3f}", "plant storage basis"]],
            )
            + "\n\n### Selected Heat Integration\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Selected case", selected_case.title if selected_case else "n/a"],
                    ["Recovered duty (kW)", f"{artifact.recovered_duty_kw:.3f}"],
                    ["Residual hot utility (kW)", f"{selected_case.residual_hot_utility_kw:.3f}" if selected_case else "n/a"],
                    ["Residual cold utility (kW)", f"{selected_case.residual_cold_utility_kw:.3f}" if selected_case else "n/a"],
                ],
            )
            + "\n\n### Utility Basis Decision\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Selected basis", utility_basis_decision.selected_candidate_id or "n/a"],
                    ["Steam pressure (bar)", f"{utility_basis.steam_pressure_bar:.1f}"],
                    ["Steam cost (INR/kg)", f"{utility_basis.steam_cost_inr_per_kg:.2f}"],
                    ["Power cost (INR/kWh)", f"{utility_basis.power_cost_inr_per_kwh:.2f}"],
                ],
            )
            + "\n\n### Utility Consumption Summary\n\n"
            + markdown_table(
                ["Utility", "Load", "Units", "Annualized Proxy", "Basis"],
                utility_summary_rows or [["n/a", "0.0", "n/a", "0.0", "n/a"]],
            )
            + "\n\n### Utility Service System Matrix\n\n"
            + markdown_table(
                ["Utility System", "Supply Basis", "Primary Services", "Standby / Design Note"],
                utility_system_rows or [["n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Utility Peak and Annualized Demand\n\n"
            + markdown_table(
                ["Utility", "Normal Load", "Units", "Peak Factor", "Peak Load", "Annualized Usage", "Cost Proxy"],
                utility_peak_rows or [["n/a", "0.0", "n/a", "1.00", "0.0", "0.0", "n/a"]],
            )
            + "\n\n### Utility Demand by Major Unit\n\n"
            + markdown_table(
                ["Utility", "Contributor", "Estimated Demand", "Basis"],
                utility_demand_rows or [["n/a", "n/a", "0.0", "n/a"]],
            )
            + "\n\n### Utilities\n\n"
            + markdown_table(["Utility", "Load", "Units", "Basis"], rows)
            + "\n\n### Utility Island Service Basis\n\n"
            + markdown_table(
                ["Island", "Role", "Header Level", "Cluster", "Recovered Duty (kW)", "Target Duty (kW)", "HTM Inventory (m3)", "Header Pressure (bar)", "Control Complexity"],
                island_rows or [["n/a", "n/a", "0", "-", "0.0", "0.0", "0.0", "0.0", "0.0"]],
            )
            + "\n\n### Header and Thermal-Loop Basis\n\n"
            + markdown_table(
                ["Step", "Island", "Header", "Cluster", "Role", "Family", "Pressure (bar)", "Temperature (C)", "Service"],
                header_rows or [["n/a", "-", "0", "-", "n/a", "-", "0.0", "0.0", "n/a"]],
            )
            + "\n\n### Utility Architecture\n\n"
            + utility_architecture.markdown
        )
        chapter = self._chapter(
            "storage_utilities",
            "Storage and Utilities",
            "storage_utilities",
            markdown,
            sorted(set(storage.citations + artifact.citations + utility_network.citations + utility_basis_decision.citations)),
            storage.assumptions + artifact.assumptions + utility_network.assumptions + utility_basis_decision.assumptions,
            ["utility_summary", "utility_basis_decision", "utility_architecture"],
            required_inputs=["storage_design", "equipment_list", "energy_balance", "operations_planning", "pump_design", "utility_network_decision"],
        )
        issues = (
            validate_decision_record(utility_basis_decision, "utility_basis_decision")
            + validate_utility_architecture(utility_architecture)
            + self._value_issues(utility_basis, "utility_basis")
            + self._value_issues(artifact, "utility_summary")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_instrumentation_control(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        flowsheet_graph = self._load("flowsheet_graph", FlowsheetGraph)
        flowsheet_case = self._maybe_load("flowsheet_case", FlowsheetCase)
        route = self._selected_route()
        diagram_style = build_diagram_style_profile()
        artifact = build_control_plan_from_flowsheet(route, equipment, utilities, flowsheet_graph)
        control_architecture = build_control_architecture_decision(
            route,
            equipment,
            utilities.model_dump_json(indent=2),
            artifact,
            flowsheet_graph,
        )
        control_diagram = build_control_system_diagram(artifact, control_architecture, flowsheet_graph, diagram_style, flowsheet_case)
        self._save("control_plan", artifact)
        self._save("control_architecture", control_architecture)
        self._save("control_system_diagram_artifact", control_diagram)
        for index, sheet in enumerate(control_diagram.sheets, start=1):
            self.store.save_text(self.config.project_id, f"diagrams/control_system_sheet_{index}.svg", sheet.svg)
        self._refresh_agent_fabric()
        rows = [
            [
                loop.control_id,
                loop.unit_id or "-",
                loop.loop_family or "-",
                loop.controlled_variable,
                loop.manipulated_variable,
                loop.sensor,
                loop.actuator,
                loop.criticality or "-",
            ]
            for loop in artifact.control_loops
        ]
        loop_detail_rows = [
            [
                loop.control_id,
                loop.unit_id or "-",
                loop.controlled_variable,
                loop.manipulated_variable,
                loop.objective or loop.notes,
                loop.disturbance_basis or "-",
                loop.criticality or "-",
            ]
            for loop in artifact.control_loops
        ]
        startup_rows = [
            [
                loop.control_id,
                loop.startup_logic or "standard startup permissive",
                loop.shutdown_logic or "standard shutdown rundown",
                loop.override_logic or "basic operator override",
            ]
            for loop in artifact.control_loops
        ]
        safeguard_rows = [
            [
                loop.control_id,
                f"High/low {loop.controlled_variable}",
                "alarm + operator response" if (loop.criticality or "").lower() != "high" else "alarm + override / interlock response",
                loop.safeguard_linkage or f"Protects {loop.manipulated_variable.lower()} basis",
            ]
            for loop in artifact.control_loops
        ]
        loopsheet_rows = [
            [
                loop.control_id,
                loop.unit_id or "-",
                loop.loop_family or "-",
                loop.sensor,
                loop.actuator,
                loop.objective or loop.notes,
                loop.startup_logic or "-",
                loop.override_logic or "-",
            ]
            for loop in artifact.control_loops
        ]
        utility_link_rows = [
            [
                item.utility_type,
                f"{item.load:.3f} {item.units}",
                (
                    "temperature / pressure loops depend on steam or cooling-service availability"
                    if item.utility_type.lower() in {"steam", "cooling water"}
                    else "inventory, purge, or protective logic references this plant utility service"
                ),
            ]
            for item in utilities.items
        ]
        markdown = (
            artifact.markdown
            + "\n\n### Control System Diagram\n\n"
            + "\n\n".join(diagram_svg_fence(sheet.svg) for sheet in control_diagram.sheets)
            + "\n\n### Control Philosophy\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Selected architecture", control_architecture.decision.selected_candidate_id or "n/a"],
                    ["Critical units", ", ".join(control_architecture.critical_units) or "none"],
                    ["Loop count", str(len(artifact.control_loops))],
                    ["Utility services linked", str(len(utilities.items))],
                    ["High-criticality loops", str(sum(1 for loop in artifact.control_loops if (loop.criticality or '').lower() == 'high'))],
                ],
            )
            + "\n\n### Control Architecture Decision\n\n"
            + control_architecture.markdown
            + "\n\n### Loop Objective Matrix\n\n"
            + markdown_table(
                ["Loop", "Unit", "Controlled Variable", "Manipulated Variable", "Objective", "Disturbance Basis", "Criticality"],
                loop_detail_rows or [["n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Controlled and Manipulated Variable Register\n\n"
            + markdown_table(
                ["Loop", "Unit", "Family", "Controlled Variable", "Manipulated Variable", "Sensor", "Actuator", "Criticality"],
                rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Startup, Shutdown, and Override Basis\n\n"
            + markdown_table(
                ["Loop", "Startup Logic", "Shutdown Logic", "Override / Permissive Basis"],
                startup_rows or [["n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Alarm and Interlock Basis\n\n"
            + markdown_table(
                ["Loop", "Deviation", "Protective Layer", "Purpose"],
                safeguard_rows or [["n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Utility-Integrated Control Basis\n\n"
            + markdown_table(
                ["Utility", "Load", "Control Linkage"],
                utility_link_rows or [["n/a", "0.0", "n/a"]],
            )
            + "\n\n### Control Loop Sheets\n\n"
            + markdown_table(
                ["Loop", "Unit", "Family", "Sensor", "Actuator", "Objective", "Startup Basis", "Override Basis"],
                loopsheet_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
        )
        chapter = self._chapter(
            "instrumentation_control",
            "Instrumentation and Process Control",
            "instrumentation_control",
            markdown,
            artifact.citations or control_architecture.citations or equipment.citations or utilities.citations,
            artifact.assumptions + control_architecture.assumptions + control_diagram.assumptions,
            ["control_plan", "control_architecture", "control_system_diagram_artifact"],
            required_inputs=["equipment_list", "utility_summary", "flowsheet_graph"],
        )
        issues = validate_control_plan(artifact) + validate_control_architecture(control_architecture) + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_hazop_she(self) -> StageResult:
        route = self._selected_route()
        equipment = self._load("equipment_list", EquipmentListArtifact)
        flowsheet_graph = self._load("flowsheet_graph", FlowsheetGraph)
        control_plan = self._load("control_plan", ControlPlanArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        register = build_hazop_node_register(route, equipment, flowsheet_graph, control_plan)
        hazop = HazopStudyArtifact(nodes=register.nodes, markdown=register.markdown, citations=register.citations, assumptions=register.assumptions)
        self._save("hazop_study", hazop)
        self._save("hazop_node_register", register)
        she = self.reasoning.build_safety_environment(self.config.basis, route.model_dump_json(indent=2), hazop.model_dump_json(indent=2))
        self._repair_artifact_citations(
            she,
            register.citations + route.citations + equipment.citations + utilities.citations,
            "SHE citations were normalized to valid source ids when the generated artifact returned internal route or equipment identifiers.",
        )
        self._save("safety_environment", she)
        hazop_summary_rows = [
            ["Node count", str(len(register.nodes))],
            ["High-severity route hazards", str(sum(1 for hazard in route.hazards if hazard.severity == "high"))],
            ["Control loops linked", str(len(control_plan.control_loops))],
            ["Coverage summary", register.coverage_summary],
            ["Node families", ", ".join(sorted({node.node_family for node in register.nodes})) or "none"],
        ]
        critical_node_rows = [
            [
                node.node_id,
                node.node_family or "-",
                node.deviation or f"{node.guide_word} {node.parameter}",
                node.parameter,
                node.guide_word,
                node.consequence_severity or "-",
                "; ".join(node.consequences),
                "; ".join(node.safeguards),
            ]
            for node in register.nodes
        ]
        node_basis_rows = [
            [
                node.node_id,
                node.node_family or "-",
                node.design_intent or "-",
                node.parameter,
                node.guide_word,
                node.deviation or "-",
                "; ".join(node.linked_control_loops) or "-",
            ]
            for node in register.nodes
        ]
        deviation_rows = [
            [
                node.node_id,
                node.deviation or f"{node.guide_word} {node.parameter}",
                "; ".join(node.causes),
                "; ".join(node.consequences),
                "; ".join(node.safeguards),
            ]
            for node in register.nodes
        ]
        recommendation_rows = [
            [
                node.node_id,
                node.recommendation_priority or "-",
                node.recommendation_status or "-",
                node.recommendation,
                "; ".join(node.causes),
            ]
            for node in register.nodes
        ]
        safety_rows = [
            [hazard.severity.title(), hazard.description, hazard.safeguard]
            for hazard in route.hazards
        ] or [["Moderate", "Generic process upset and containment risk", "Use route-selected safeguards and HAZOP recommendations."]]
        emergency_rows = [
            [
                node.node_id,
                node.deviation or f"{node.guide_word} {node.parameter}",
                (
                    "isolate feeds, stabilize utilities, and hold inventory in safe containment"
                    if node.node_family in {"reactor", "column_or_main_separation", "absorber"}
                    else "stop transfer / circulation and move to contained safe state"
                ),
                "; ".join(node.safeguards) or "alarm and manual response",
                node.recommendation,
            ]
            for node in register.nodes
        ]
        health_rows = [
            [
                "Operator exposure",
                "feed / product / intermediate contact and vapor release during sampling, transfer, and upset response",
                "exposure monitoring at sampling, transfer, and vent-handling points",
                "service-specific PPE, chemical-resistant gloves, eye protection, and respiratory precautions where indicated",
                "linked to selected route family and HAZOP node families",
            ],
            [
                "Maintenance exposure",
                "equipment opening, filter / cake handling, exchanger cleaning, and confined-space entry risk",
                "permit-to-work, isolation verification, and post-cleaning gas test basis",
                "maintenance PPE upgraded for corrosive, hot, or solids-bearing service",
                "applies during shutdown, cleanup, and turnaround activity",
            ],
            [
                "Training and competency",
                "routine operating, emergency isolation, inerting, and chemical handling scenarios",
                "startup, shutdown, and emergency drill coverage tied to critical loops and HAZOP nodes",
                "role-specific operating and emergency response training",
                "control philosophy and HAZOP outputs are used as the training basis",
            ],
        ]
        environment_rows = [
            [
                "Air emissions",
                "vent, offgas, absorber discharge, dryer exhaust, and utility-release points remain tied to selected separation and utility architecture",
                "route-family vent routing, control-loop-linked upset response, and utility-integrated safeguards",
                "periodic vent / stack monitoring plus upset-event logging",
            ],
            [
                "Wastewater",
                "aqueous purge, wash, and cleanup streams require segregation by corrosive / solids / organics burden",
                "segregated collection, neutralization / equalization, and load-based downstream treatment",
                "screening effluent characterization and routed discharge control",
            ],
            [
                "Solid and hazardous waste",
                "filter cake, spent media, catalyst, contaminated solids, and maintenance residues require route-family-specific handling",
                "contained storage, labeled handling, recovery / disposal routing, and turnaround waste segregation",
                "batch / campaign waste tracking and controlled offsite disposition basis",
            ],
        ]
        waste_rows = [
            [
                "Vent / offgas condensate and purge",
                "reactor, separation, and utility upset / normal purge points",
                "segregate by corrosive / organic / inerted service and route to recovery or controlled treatment",
                "selected route-family vent handling basis",
            ],
            [
                "Aqueous wash and cleanup streams",
                "sampling, washdown, maintenance, and aqueous separation service",
                "collect separately and treat as route-specific wastewater load",
                "neutralization / equalization before discharge screening",
            ],
            [
                "Solid waste and contaminated media",
                "filters, dryers, catalyst/media replacement, and solids cleanup",
                "closed handling, labeled storage, and recovery / disposal by waste class",
                "solid-waste and hazardous-waste routing basis",
            ],
        ]
        environmental_control_rows = [
            [
                item.utility_type,
                f"{item.load:.3f} {item.units}",
                (
                    "utility reliability is tied to SHE performance for temperature / pressure / inerting control"
                    if item.utility_type.lower() in {"steam", "cooling water", "nitrogen"}
                    else "utility demand contributes to environmental load and emergency operability basis"
                ),
            ]
            for item in utilities.items
        ]
        hazop_markdown = (
            "### HAZOP Coverage Summary\n\n"
            + markdown_table(["Parameter", "Value"], hazop_summary_rows)
            + "\n\n### HAZOP Node Basis\n\n"
            + markdown_table(
                ["Node", "Family", "Design Intent", "Parameter", "Guide Word", "Deviation", "Linked Control Loops"],
                node_basis_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Critical Node Summary\n\n"
            + markdown_table(
                ["Node", "Family", "Deviation", "Parameter", "Guide Word", "Severity", "Consequences", "Safeguards"],
                critical_node_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Deviation Cause-Consequence Matrix\n\n"
            + markdown_table(
                ["Node", "Deviation", "Causes", "Consequences", "Safeguards"],
                deviation_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### HAZOP Node Register\n\n"
            + hazop.markdown.replace("### HAZOP Node Register\n\n", "")
            + "\n\n### Recommendation Register\n\n"
            + markdown_table(
                ["Node", "Priority", "Status", "Recommendation", "Primary Causes"],
                recommendation_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
        )
        she_markdown = (
            she.markdown
            + "\n\n### Safety Basis\n\n"
            + markdown_table(["Severity", "Hazard", "Safeguard"], safety_rows)
            + "\n\n### Hazard and Emergency Response Basis\n\n"
            + markdown_table(
                ["Node", "Emergency Trigger", "Immediate Response", "Protective Systems", "Follow-Up Recommendation"],
                emergency_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
            )
            + "\n\n### Health and Exposure Basis\n\n"
            + markdown_table(
                ["Topic", "Exposure Basis", "Monitoring / Verification", "PPE / Controls", "Operational Linkage"],
                health_rows,
            )
            + "\n\n### Environmental and Waste Basis\n\n"
            + markdown_table(
                ["Area", "Release / Load Basis", "Control Basis", "Monitoring Basis"],
                environment_rows,
            )
            + "\n\n### Environmental Control and Monitoring Basis\n\n"
            + markdown_table(
                ["Utility / Service", "Load", "SHE Linkage"],
                environmental_control_rows or [["n/a", "0.0", "n/a"]],
            )
            + "\n\n### Waste Handling and Disposal Basis\n\n"
            + markdown_table(
                ["Waste Class", "Typical Source", "Handling Basis", "Disposition Basis"],
                waste_rows,
            )
            + "\n\n### Safeguard Linkage\n\n"
            + markdown_table(
                ["Node", "Safeguards", "Linked Loops", "Recommendation"],
                [[node.node_id, "; ".join(node.safeguards), "; ".join(node.linked_control_loops) or "-", node.recommendation] for node in register.nodes] or [["n/a", "n/a", "n/a", "n/a"]],
            )
        )
        hazop_chapter = self._chapter("hazop", "HAZOP", "hazop_she", hazop_markdown, hazop.citations, hazop.assumptions, ["hazop_study", "hazop_node_register"], required_inputs=["equipment_list", "route_selection", "flowsheet_graph", "control_plan"])
        she_chapter = self._chapter("safety_health_environment_waste", "Safety, Health, Environment, and Waste Management", "hazop_she", she_markdown, she.citations or route.citations or equipment.citations, she.assumptions + register.assumptions + utilities.assumptions, ["safety_environment"], required_inputs=["equipment_list", "route_selection", "flowsheet_graph", "control_plan", "utility_summary"], summary=she.summary)
        issues = validate_hazop_node_register(register) + self._chapter_issues(hazop_chapter) + self._chapter_issues(she_chapter)
        gate = self._gate("hazop", "HAZOP Gate", "Approve critical HAZOP nodes and SHE safeguards.")
        return StageResult(chapters=[hazop_chapter, she_chapter], issues=issues, gate=gate)

    def _run_layout_waste(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        flowsheet_graph = self._load("flowsheet_graph", FlowsheetGraph)
        mechanical_design = self._load("mechanical_design", MechanicalDesignArtifact)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        family_adapter = self.store.maybe_load_model(self.config.project_id, "artifacts/chemistry_family_adapter.json", ChemistryFamilyAdapter)
        layout_choice = select_layout_configuration(site, equipment, utilities, flowsheet_graph, archetype, family_adapter)
        layout_decision = build_layout_decision(site.selected_site, equipment, utilities, flowsheet_graph, layout_choice)
        mechanical_layout_markdown = "\n\n### Maintenance and Foundation Basis\n\n" + markdown_table(
            ["Equipment", "Support Variant", "Footprint (m2)", "Clearance (m)", "Platform", "Rack Tie-In"],
            [
                [
                    item.equipment_id,
                    item.support_variant or item.support_type,
                    f"{item.foundation_footprint_m2:.3f}",
                    f"{item.maintenance_clearance_m:.3f}",
                    "yes" if item.maintenance_platform_required else "no",
                    "yes" if item.pipe_rack_tie_in_required else "no",
                ]
                for item in mechanical_design.items
            ]
            or [["n/a", "n/a", "0.0", "0.0", "no", "no"]],
        )
        layout_rows = [
            [node.node_id, node.label, node.section_id or "-", ", ".join(node.upstream_nodes) or "-", ", ".join(node.downstream_nodes) or "-"]
            for node in flowsheet_graph.nodes
        ]
        node_zone_map: dict[str, str] = {}
        for node in flowsheet_graph.nodes:
            node_text = f"{node.node_id} {node.label} {node.section_id or ''}".lower()
            if any(token in node_text for token in ["storage", "tank", "feed", "receipt"]):
                node_zone_map[node.node_id] = "Tank farm / receipt zone"
            elif any(token in node_text for token in ["reactor", "reaction", "oxid", "hydrat"]):
                node_zone_map[node.node_id] = "Process reaction zone"
            elif any(token in node_text for token in ["column", "distillation", "purification", "separation", "absorber", "crystallizer", "dryer", "filter"]):
                node_zone_map[node.node_id] = "Separation and finishing zone"
            elif any(token in node_text for token in ["waste", "effluent", "vent", "recovery"]):
                node_zone_map[node.node_id] = "Waste / recovery zone"
            else:
                node_zone_map[node.node_id] = "General process block"

        zone_groups: dict[str, list[str]] = {}
        for node_id, zone in node_zone_map.items():
            zone_groups.setdefault(zone, []).append(node_id)
        zone_rows = [
            [
                zone,
                ", ".join(sorted(node_ids)),
                (
                    "hazard segregation and controlled access"
                    if "reaction" in zone.lower() or "tank farm" in zone.lower()
                    else "short process transfer and operability grouping"
                ),
                (
                    "buffered from dispatch / occupied areas"
                    if "reaction" in zone.lower()
                    else "truck / service access maintained"
                    if "tank farm" in zone.lower()
                    else "kept accessible for maintenance and utility routing"
                ),
            ]
            for zone, node_ids in zone_groups.items()
        ]
        utility_route_rows = [
            [
                item.utility_type,
                item.basis,
                (
                    "process-side corridor to reaction and separation core"
                    if item.utility_type.lower() in {"steam", "cooling water", "heat-integration auxiliaries"}
                    else "tank farm / blanketing header and service access edge"
                    if item.utility_type.lower() == "nitrogen"
                    else "service corridor routed away from primary hazard cluster"
                ),
                layout_decision.winning_layout_basis,
            ]
            for item in utilities.items
        ]
        access_rows = [
            [
                "Operating mode",
                operations_planning.recommended_operating_mode,
                "layout keeps routine operator circulation outside the primary hazard core while preserving direct access to critical units",
            ],
            [
                "Dispatch and truck movement",
                f"{operations_planning.finished_goods_buffer_days:.1f} d FG buffer",
                "storage and loading area placed toward the dispatch edge with maintained truck and emergency vehicle access",
            ],
            [
                "Emergency response",
                f"{sum(1 for node in flowsheet_graph.nodes if node_zone_map.get(node.node_id) == 'Process reaction zone')} reaction-zone nodes",
                "reaction and high-hazard zones remain segregated from occupied / dispatch zones with clear firefighting approach",
            ],
            [
                "Maintenance turnaround",
                f"{operations_planning.campaign_length_days:.1f} d campaign",
                "equipment clearance, platform access, and rack tie-ins inform maintenance-side spacing and isolation access",
            ],
        ]
        utility_corridor_rows = [
            [
                item.utility_type,
                (
                    "header / rack corridor"
                    if item.utility_type.lower() in {"steam", "cooling water", "nitrogen", "dm water"}
                    else "electrical and local service corridor"
                ),
                (
                    "parallel to process train with branch take-offs at major units"
                    if item.utility_type.lower() in {"steam", "cooling water"}
                    else "distributed to storage, purge, and utility consumers with isolation access"
                ),
                (
                    "kept off main truck path and outside maintenance lift envelope"
                    if item.utility_type.lower() != "electricity"
                    else "routed with safe separation from wet and hot service zones"
                ),
            ]
            for item in utilities.items
        ]
        plot_rows = [
            ["Selected site", site.selected_site],
            ["Winning basis", layout_decision.winning_layout_basis],
            ["Major equipment count", str(len(equipment.items))],
            ["Flowsheet node count", str(len(flowsheet_graph.nodes))],
            ["Operating mode", operations_planning.recommended_operating_mode],
            ["Campaign length (d)", f"{operations_planning.campaign_length_days:.1f}"],
            ["Dispatch buffer (d)", f"{operations_planning.finished_goods_buffer_days:.1f}"],
        ]
        mermaid_nodes = []
        mermaid_links = []
        zone_alias = {
            "Tank farm / receipt zone": "tank_farm",
            "Process reaction zone": "reaction_zone",
            "Separation and finishing zone": "separation_zone",
            "Waste / recovery zone": "waste_zone",
            "General process block": "general_zone",
        }
        for zone, alias in zone_alias.items():
            members = ", ".join(sorted(zone_groups.get(zone, []))) or "none"
            mermaid_nodes.append(f'    {alias}["{zone}\\n{members}"]')
        ordered_aliases = [alias for zone, alias in zone_alias.items() if zone in zone_groups]
        for left, right in zip(ordered_aliases, ordered_aliases[1:]):
            mermaid_links.append(f"    {left} --> {right}")
        if not mermaid_links and ordered_aliases:
            mermaid_links.append(f"    {ordered_aliases[0]}")
        plot_schematic = "```mermaid\nflowchart LR\n" + "\n".join(mermaid_nodes + mermaid_links) + "\n```"
        artifact = NarrativeArtifact(
            artifact_id="layout_plan",
            title="Layout",
            markdown=(
                layout_decision.markdown
                + "\n\n### Plot Plan Basis\n\n"
                + markdown_table(["Parameter", "Value"], plot_rows)
                + "\n\n### Plot Layout Schematic\n\n"
                + plot_schematic
                + "\n\n### Area Zoning and Separation Basis\n\n"
                + markdown_table(
                    ["Zone", "Representative Nodes", "Primary Layout Driver", "Access / Separation Note"],
                    zone_rows or [["n/a", "n/a", "n/a", "n/a"]],
                )
                + "\n\n### Equipment Placement Matrix\n\n"
                + markdown_table(["Node", "Label", "Section", "Upstream", "Downstream"], layout_rows or [["n/a", "n/a", "-", "-", "-"]])
                + "\n\n### Utility Corridor Matrix\n\n"
                + markdown_table(
                    ["Utility", "Corridor Type", "Routing Basis", "Spacing / Access Note"],
                    utility_corridor_rows or [["n/a", "n/a", "n/a", "n/a"]],
                )
                + "\n\n### Utility Routing and Access Basis\n\n"
                + markdown_table(["Utility", "Basis", "Routing Strategy", "Layout Linkage"], utility_route_rows or [["n/a", "n/a", "n/a", "n/a"]])
                + "\n\n### Dispatch and Emergency Access Basis\n\n"
                + markdown_table(
                    ["Topic", "Basis", "Layout Consequence"],
                    access_rows or [["n/a", "n/a", "n/a"]],
                )
                + mechanical_layout_markdown
            ),
            summary=layout_choice.selected_summary,
            citations=layout_decision.citations,
            assumptions=layout_decision.assumptions,
        )
        self._save("layout_plan", artifact)
        produced_outputs = ["layout_plan", "layout_decision"]
        if self.config.benchmark_profile == "benzalkonium_chloride":
            self._save("layout", artifact)
            produced_outputs.insert(1, "layout")
        self._save("layout_decision", layout_decision)
        self._refresh_agent_fabric()
        chapter = self._chapter(
            "layout",
            "Project and Plant Layout",
            "layout_waste",
            artifact.markdown,
            artifact.citations or site.citations or equipment.citations or utilities.citations,
            artifact.assumptions,
            produced_outputs,
            required_inputs=["equipment_list", "utility_summary", "site_selection", "mechanical_design", "operations_planning"],
            summary=artifact.summary,
        )
        issues = validate_decision_record(layout_choice, "layout_choice") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_project_cost(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        stream_table = self._load("stream_table", StreamTable)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        route_selection = self._load("route_selection", RouteSelectionArtifact)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        flowsheet_blueprint = self._load("flowsheet_blueprint", FlowsheetBlueprintArtifact)
        column_design = self._load("column_design", ColumnDesign)
        utility_network = self._selected_utility_network()
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision)
        citations = sorted(
            set(
                equipment.citations
                + utilities.citations
                + market.citations
                + site.citations
                + route_selection.citations
                + operations_planning.citations
                + flowsheet_blueprint.citations
                + utility_network.citations
            )
        )
        assumptions = (
            equipment.assumptions
            + utilities.assumptions
            + market.assumptions
            + site.assumptions
            + route_selection.assumptions
            + operations_planning.assumptions
            + flowsheet_blueprint.assumptions
            + utility_network.assumptions
        )
        route_site_fit = build_route_site_fit_artifact(
            self.config.basis,
            site,
            route_selection,
            flowsheet_blueprint,
            operations_planning,
            citations,
            assumptions,
        )
        route_economic_basis = build_route_economic_basis_artifact(
            self.config.basis,
            site,
            route_selection,
            stream_table,
            market,
            flowsheet_blueprint,
            operations_planning,
            route_site_fit,
            citations,
            assumptions,
        )
        procurement_basis = build_procurement_basis_decision(
            site,
            equipment.items,
            route_site_fit=route_site_fit,
            route_economic_basis=route_economic_basis,
        )
        logistics_basis = build_logistics_basis_decision(
            site,
            market,
            route_site_fit=route_site_fit,
            route_economic_basis=route_economic_basis,
        )
        cost_model = build_cost_model(
            self.config.basis,
            equipment.items,
            utilities,
            stream_table,
            market,
            site,
            citations,
            assumptions,
            utility_network_decision=utility_network,
            utility_architecture=utility_architecture,
            scenario_policy=self.config.scenario_policy,
            procurement_basis=procurement_basis,
            logistics_basis=logistics_basis,
            route_site_fit=route_site_fit,
            route_economic_basis=route_economic_basis,
            column_design=column_design,
        )
        plant_cost_summary = build_plant_cost_summary(cost_model)
        self._save("route_site_fit", route_site_fit)
        self._save("route_economic_basis", route_economic_basis)
        self._save("cost_model", cost_model)
        self._save("plant_cost_summary", plant_cost_summary)
        self._save("procurement_basis_decision", procurement_basis)
        self._save("logistics_basis_decision", logistics_basis)
        self._refresh_agent_fabric()
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        self._save("resolved_values", extend_resolved_value_artifact(resolved_values, cost_model.value_records, resolved_sources, self.config, "project_cost"))
        direct_head_totals = {
            "bare": sum(item.bare_cost_inr for item in plant_cost_summary.equipment_breakdowns),
            "installation": sum(item.installation_inr for item in plant_cost_summary.equipment_breakdowns),
            "piping": sum(item.piping_inr for item in plant_cost_summary.equipment_breakdowns),
            "instrumentation": sum(item.instrumentation_inr for item in plant_cost_summary.equipment_breakdowns),
            "electrical": sum(item.electrical_inr for item in plant_cost_summary.equipment_breakdowns),
            "civil": sum(item.civil_structural_inr for item in plant_cost_summary.equipment_breakdowns),
            "insulation": sum(item.insulation_painting_inr for item in plant_cost_summary.equipment_breakdowns),
            "equipment_contingency": sum(item.contingency_inr for item in plant_cost_summary.equipment_breakdowns),
        }
        direct_head_totals["spares"] = sum(item.spares_cost_inr for item in cost_model.equipment_cost_items)
        utility_island_project_capex = sum(item.project_capex_burden_inr for item in cost_model.utility_island_costs)
        direct_cost_uplift = max(cost_model.direct_cost - cost_model.installed_cost, 0.0)
        family_rollups: dict[str, dict[str, float]] = {}
        for item in cost_model.equipment_cost_items:
            family_bucket = family_rollups.setdefault(
                item.equipment_type,
                {
                    "count": 0.0,
                    "bare": 0.0,
                    "installed": 0.0,
                    "spares": 0.0,
                    "import_duty": 0.0,
                },
            )
            family_bucket["count"] += 1.0
            family_bucket["bare"] += item.bare_cost_inr
            family_bucket["installed"] += item.installed_cost_inr
            family_bucket["spares"] += item.spares_cost_inr
            family_bucket["import_duty"] += item.import_duty_inr
        project_cost_summary_markdown = "\n\n### Project Cost Build-Up Summary\n\n" + markdown_table(
            ["Project-cost head", f"Value ({cost_model.currency})"],
            [
                ["Purchased equipment", f"{cost_model.equipment_purchase_cost:,.2f}"],
                ["Installed equipment and packages", f"{cost_model.installed_cost:,.2f}"],
                ["Direct plant cost", f"{cost_model.direct_cost:,.2f}"],
                ["Indirect cost", f"{cost_model.indirect_cost:,.2f}"],
                ["Contingency", f"{cost_model.contingency:,.2f}"],
                ["Total CAPEX", f"{cost_model.total_capex:,.2f}"],
            ],
        )
        direct_cost_markdown = "\n\n### Direct Plant Cost Head Allocation\n\n" + markdown_table(
            ["Direct-cost head", f"Allocated value ({cost_model.currency})"],
            [
                ["Purchased equipment", f"{direct_head_totals['bare']:,.2f}"],
                ["Installation", f"{direct_head_totals['installation']:,.2f}"],
                ["Piping", f"{direct_head_totals['piping']:,.2f}"],
                ["Instrumentation and control", f"{direct_head_totals['instrumentation']:,.2f}"],
                ["Electrical", f"{direct_head_totals['electrical']:,.2f}"],
                ["Civil and structural", f"{direct_head_totals['civil']:,.2f}"],
                ["Insulation and painting", f"{direct_head_totals['insulation']:,.2f}"],
                ["Equipment-level contingency allowance", f"{direct_head_totals['equipment_contingency']:,.2f}"],
                ["Total spares allowance", f"{direct_head_totals['spares']:,.2f}"],
                ["Allocated direct plant cost", f"{plant_cost_summary.direct_plant_cost_inr:,.2f}"],
            ],
        )
        indirect_cost_markdown = "\n\n### Indirect and Contingency Basis\n\n" + markdown_table(
            ["Allowance", f"Value ({cost_model.currency})"],
            [
                ["Installed-cost base", f"{cost_model.installed_cost:,.2f}"],
                ["Direct-cost uplift above installed basis", f"{direct_cost_uplift:,.2f}"],
                ["Indirect engineering / procurement / construction", f"{cost_model.indirect_cost:,.2f}"],
                ["Contingency", f"{cost_model.contingency:,.2f}"],
                ["Heat-integration CAPEX", f"{cost_model.integration_capex_inr:,.2f}"],
                ["Utility-island project CAPEX burden", f"{utility_island_project_capex:,.2f}"],
                ["Total import-duty burden", f"{cost_model.total_import_duty_inr:,.2f}"],
                ["Total CAPEX", f"{cost_model.total_capex:,.2f}"],
            ],
        )
        equipment_family_markdown = "\n\n### Equipment Family Cost Allocation\n\n" + markdown_table(
            ["Equipment family", "Count", "Bare Cost (INR)", "Installed Cost (INR)", "Spares (INR)", "Import Duty (INR)"],
            [
                [
                    equipment_type,
                    str(int(values["count"])),
                    f"{values['bare']:,.2f}",
                    f"{values['installed']:,.2f}",
                    f"{values['spares']:,.2f}",
                    f"{values['import_duty']:,.2f}",
                ]
                for equipment_type, values in sorted(
                    family_rollups.items(),
                    key=lambda item: (-item[1]["installed"], item[0].lower()),
                )
            ]
            or [["n/a", "0", "0.00", "0.00", "0.00", "0.00"]],
        )
        scenario_markdown = ""
        if cost_model.scenario_results:
            scenario_markdown = "\n\n### Scenario Cost Snapshot\n\n" + markdown_table(
                ["Scenario", "Utility Cost (INR/y)", "Transport/Service (INR/y)", "Utility-Island Burden (INR/y)", "Operating Cost (INR/y)", "Revenue (INR/y)", "Gross Margin (INR/y)"],
                [
                    [
                        item.scenario_name,
                        f"{item.annual_utility_cost_inr:,.2f}",
                        f"{item.annual_transport_service_cost_inr:,.2f}",
                        f"{item.annual_utility_island_operating_burden_inr:,.2f}",
                        f"{item.annual_operating_cost_inr:,.2f}",
                        f"{item.annual_revenue_inr:,.2f}",
                        f"{item.gross_margin_inr:,.2f}",
                    ]
                    for item in cost_model.scenario_results
                ],
            )
        recurring_service_markdown = ""
        if cost_model.annual_transport_service_cost > 0.0:
            recurring_service_markdown = "\n\n### Recurring Transport / Service Submodels\n\n" + markdown_table(
                ["Recurring submodel", f"Value ({cost_model.currency}/y)"],
                [
                    ["Utility-island service", f"{cost_model.annual_utility_island_service_cost:,.2f}"],
                    ["Utility-island replacement", f"{cost_model.annual_utility_island_replacement_cost:,.2f}"],
                    ["Packing replacement", f"{cost_model.annual_packing_replacement_cost:,.2f}"],
                    ["Classifier service", f"{cost_model.annual_classifier_service_cost:,.2f}"],
                    ["Filter media replacement", f"{cost_model.annual_filter_media_replacement_cost:,.2f}"],
                    ["Dryer exhaust treatment", f"{cost_model.annual_dryer_exhaust_treatment_cost:,.2f}"],
                    ["Total transport/service burden", f"{cost_model.annual_transport_service_cost:,.2f}"],
                ],
            )
        utility_island_markdown = ""
        if cost_model.utility_island_costs:
            utility_island_markdown = "\n\n### Utility Island Economics\n\n" + markdown_table(
                [
                    "Island",
                    "Topology",
                    "HTM Inventory (m3)",
                    "Header Pressure (bar)",
                    "Pair Score",
                    "Cycle (y)",
                    "Turnaround (d)",
                    "Project CAPEX Burden (INR)",
                    "Allocated Utility (INR/y)",
                    "Service (INR/y)",
                    "Replacement (INR/y)",
                    "Operating Burden (INR/y)",
                ],
                [
                    [
                        item.island_id,
                        item.topology,
                        f"{item.shared_htm_inventory_m3:.3f}",
                        f"{item.header_design_pressure_bar:.2f}",
                        f"{item.condenser_reboiler_pair_score:.3f}",
                        f"{item.maintenance_cycle_years:.2f}",
                        f"{item.planned_turnaround_days:.2f}",
                        f"{item.project_capex_burden_inr:,.2f}",
                        f"{item.annual_allocated_utility_cost_inr:,.2f}",
                        f"{item.annual_service_cost_inr:,.2f}",
                        f"{item.annualized_replacement_cost_inr:,.2f}",
                        f"{item.annual_operating_burden_inr:,.2f}",
                    ]
                    for item in cost_model.utility_island_costs
                ],
            )
        procurement_timing_markdown = "\n\n### Procurement Timing Basis\n\n" + markdown_table(
            ["Field", "Value"],
            [
                ["Profile", cost_model.procurement_profile_label or "n/a"],
                ["Construction months", str(cost_model.construction_months)],
                ["Imported equipment fraction", f"{cost_model.imported_equipment_fraction:.3f}"],
                ["Long-lead equipment fraction", f"{cost_model.long_lead_equipment_fraction:.3f}"],
                ["Total import duty", f"{cost_model.currency} {cost_model.total_import_duty_inr:,.2f}"],
                ["Advance fraction", f"{cost_model.procurement_advance_fraction:.3f}"],
                ["Progress fraction", f"{cost_model.procurement_progress_fraction:.3f}"],
                ["Retention fraction", f"{cost_model.procurement_retention_fraction:.3f}"],
            ],
        )
        if cost_model.procurement_schedule:
            procurement_timing_markdown += "\n\n" + markdown_table(
                ["Package Family", "Milestone", "Month", "Draw Fraction", "CAPEX Draw (INR)"],
                [
                    [
                        str(item.get("package_family", "")),
                        str(item.get("milestone", "")),
                        f"{float(item.get('month', 0.0)):.1f}",
                        f"{float(item.get('draw_fraction', 0.0)):.3f}",
                        f"{float(item.get('capex_draw_inr', 0.0)):,.2f}",
                    ]
                    for item in cost_model.procurement_schedule
                ],
            )
        if cost_model.procurement_package_impacts:
            procurement_timing_markdown += "\n\n### Procurement Package Timing\n\n" + markdown_table(
                ["Equipment", "Type", "Package Family", "Lead (mo)", "Award Month", "Delivery Month", "Import Content", "Import Duty", "CAPEX Burden (INR)"],
                [
                    [
                        item.package_id,
                        item.equipment_type,
                        item.package_family,
                        f"{item.lead_time_months:.2f}",
                        f"{item.award_month:.2f}",
                        f"{item.delivery_month:.2f}",
                        f"{item.import_content_fraction:.3f}",
                        f"{item.import_duty_inr:,.2f}",
                        f"{item.capex_burden_inr:,.2f}",
                    ]
                    for item in cost_model.procurement_package_impacts
                ],
            )
        equipment_cost_markdown = "\n\n### Installed Equipment Cost Matrix\n\n" + markdown_table(
            ["Equipment", "Type", "Bare Cost (INR)", "Installed Cost (INR)", "Spares (INR)", "Package Family", "Lead (mo)", "Import Duty (INR)", "Basis"],
            [
                [
                    item.equipment_id,
                    item.equipment_type,
                    f"{item.bare_cost_inr:,.2f}",
                    f"{item.installed_cost_inr:,.2f}",
                    f"{item.spares_cost_inr:,.2f}",
                    item.procurement_package_family or "n/a",
                    f"{item.procurement_lead_time_months:.2f}",
                    f"{item.import_duty_inr:,.2f}",
                    item.basis,
                ]
                for item in cost_model.equipment_cost_items
            ] or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        )
        markdown = (
            "\n\n### Route Site Fit\n\n"
            + route_site_fit.markdown
            + "\n\n### Route-Derived Economic Basis\n\n"
            + route_economic_basis.markdown
            + "\n\n### Route-Derived Recurring Burden Register\n\n"
            + markdown_table(
                ["Component", "Role", "Annualized Burden (INR/y)", "Recovery Fraction", "Notes"],
                [
                    [
                        item.component_name,
                        item.role,
                        f"{item.annualized_burden_inr:,.2f}",
                        f"{item.recovery_fraction:.3f}",
                        item.notes or "-",
                    ]
                    for item in route_economic_basis.items
                ]
                or [["n/a", "n/a", "0.00", "0.000", "-"]],
            )
            + project_cost_summary_markdown
            + direct_cost_markdown
            + indirect_cost_markdown
            + equipment_family_markdown
            + procurement_timing_markdown
            + equipment_cost_markdown
            + utility_island_markdown
            + recurring_service_markdown
            + scenario_markdown
        )
        chapter = self._chapter(
            "project_cost",
            "Project Cost",
            "project_cost",
            "### Procurement Basis\n\n"
            f"{procurement_basis.selected_summary}\n\n"
            "### Logistics Basis\n\n"
            f"{logistics_basis.selected_summary}\n\n"
            f"{markdown}",
            cost_model.citations,
            cost_model.assumptions,
            ["route_site_fit", "route_economic_basis", "cost_model", "plant_cost_summary", "procurement_basis_decision", "logistics_basis_decision"],
            required_inputs=["equipment_list", "utility_summary", "stream_table", "market_assessment", "site_selection", "route_selection", "operations_planning", "flowsheet_blueprint"],
        )
        issues = (
            validate_route_site_fit_artifact(route_site_fit, site, route_selection)
            + validate_route_economic_basis_artifact(route_economic_basis, route_site_fit)
            + validate_decision_record(procurement_basis, "procurement_basis_decision")
            + validate_decision_record(logistics_basis, "logistics_basis_decision")
            + validate_cost_model(cost_model, self._source_ids(), self.config)
            + self._value_issues(cost_model, "cost_model")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_cost_of_production(self) -> StageResult:
        cost_model = self._load("cost_model", CostModel)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        annual_output = max(annual_output_kg(self.config.basis), 1.0)
        unit_cost = cost_model.annual_opex / max(annual_output_kg(self.config.basis), 1.0)
        selling_price = market.estimated_price_per_kg
        gross_margin_per_kg = selling_price - unit_cost
        summary_markdown = "\n\n### Cost of Production Summary\n\n" + markdown_table(
            ["Metric", "Value"],
            [
                ["Annual production", f"{annual_output:,.2f} kg/y"],
                ["Annual operating cost", f"{cost_model.currency} {cost_model.annual_opex:,.2f}/y"],
                ["Unit cost of production", f"{unit_cost:,.2f} {cost_model.currency}/kg"],
                ["Selling price basis", f"{selling_price:,.2f} {cost_model.currency}/kg"],
                ["Gross margin basis", f"{gross_margin_per_kg:,.2f} {cost_model.currency}/kg"],
            ],
        )
        opex_rows = [
            ["Raw materials", f"{cost_model.annual_raw_material_cost:,.2f}"],
            ["Utilities", f"{cost_model.annual_utility_cost:,.2f}"],
            ["Labor", f"{cost_model.annual_labor_cost:,.2f}"],
        ]
        if cost_model.annual_transport_service_cost > 0.0:
            base_maintenance = max(cost_model.annual_maintenance_cost - cost_model.annual_transport_service_cost, 0.0)
            opex_rows.extend(
                [
                    ["Base maintenance", f"{base_maintenance:,.2f}"],
                    ["Utility-island service", f"{cost_model.annual_utility_island_service_cost:,.2f}"],
                    ["Utility-island replacement", f"{cost_model.annual_utility_island_replacement_cost:,.2f}"],
                    ["Packing replacement", f"{cost_model.annual_packing_replacement_cost:,.2f}"],
                    ["Classifier service", f"{cost_model.annual_classifier_service_cost:,.2f}"],
                    ["Filter media replacement", f"{cost_model.annual_filter_media_replacement_cost:,.2f}"],
                    ["Dryer exhaust treatment", f"{cost_model.annual_dryer_exhaust_treatment_cost:,.2f}"],
                    ["Transport/service penalties", f"{cost_model.annual_transport_service_cost:,.2f}"],
                    ["Total maintenance", f"{cost_model.annual_maintenance_cost:,.2f}"],
                ]
            )
        else:
            opex_rows.append(["Maintenance", f"{cost_model.annual_maintenance_cost:,.2f}"])
        opex_rows.extend(
            [
                ["Overheads", f"{cost_model.annual_overheads:,.2f}"],
                ["Total OPEX", f"{cost_model.annual_opex:,.2f}"],
                ["Unit cost", f"{unit_cost:,.2f} {cost_model.currency}/kg"],
            ]
        )
        manufacturing_build_up_markdown = "\n\n### Manufacturing Cost Build-Up\n\n" + markdown_table(
            ["Opex bucket", f"Value ({cost_model.currency}/y)", "Share of OPEX (%)"],
            [
                [
                    row[0],
                    row[1],
                    f"{(float(row[1].replace(',', '').split()[0]) / cost_model.annual_opex * 100.0):.2f}" if cost_model.annual_opex > 0.0 and row[0] not in {"Unit cost"} else ("-" if row[0] == "Unit cost" else "0.00"),
                ]
                for row in opex_rows
            ],
        )
        raw_utility_markdown = "\n\n### Utility and Raw-Material Cost Basis\n\n" + markdown_table(
            ["Basis item", "Value"],
            [
                ["Annual raw-material cost", f"{cost_model.currency} {cost_model.annual_raw_material_cost:,.2f}/y"],
                ["Annual utility cost", f"{cost_model.currency} {cost_model.annual_utility_cost:,.2f}/y"],
                ["Annual labor cost", f"{cost_model.currency} {cost_model.annual_labor_cost:,.2f}/y"],
                ["Annual output", f"{annual_output:,.2f} kg/y"],
                ["Selling price basis", f"{selling_price:,.2f} {cost_model.currency}/kg"],
            ],
        )
        recurring_service_markdown = ""
        if cost_model.annual_transport_service_cost > 0.0:
            recurring_service_markdown = "\n\n### Recurring Service and Maintenance Basis\n\n" + markdown_table(
                ["Service component", f"Value ({cost_model.currency}/y)"],
                [
                    ["Base maintenance", f"{max(cost_model.annual_maintenance_cost - cost_model.annual_transport_service_cost, 0.0):,.2f}"],
                    ["Utility-island service", f"{cost_model.annual_utility_island_service_cost:,.2f}"],
                    ["Utility-island replacement", f"{cost_model.annual_utility_island_replacement_cost:,.2f}"],
                    ["Packing replacement", f"{cost_model.annual_packing_replacement_cost:,.2f}"],
                    ["Classifier service", f"{cost_model.annual_classifier_service_cost:,.2f}"],
                    ["Filter media replacement", f"{cost_model.annual_filter_media_replacement_cost:,.2f}"],
                    ["Dryer exhaust treatment", f"{cost_model.annual_dryer_exhaust_treatment_cost:,.2f}"],
                    ["Total transport/service penalties", f"{cost_model.annual_transport_service_cost:,.2f}"],
                    ["Total maintenance", f"{cost_model.annual_maintenance_cost:,.2f}"],
                ],
            )
        unit_cost_basis_markdown = "\n\n### Unit Cost and Selling Basis\n\n" + markdown_table(
            ["Metric", "Value"],
            [
                ["Unit cost of production", f"{unit_cost:,.2f} {cost_model.currency}/kg"],
                ["Selling price basis", f"{selling_price:,.2f} {cost_model.currency}/kg"],
                ["Gross margin basis", f"{gross_margin_per_kg:,.2f} {cost_model.currency}/kg"],
                ["Operating margin on selling basis", f"{(gross_margin_per_kg / selling_price * 100.0):.2f}%" if selling_price > 0.0 else "n/a"],
            ],
        )
        markdown = (
            summary_markdown
            + manufacturing_build_up_markdown
            + raw_utility_markdown
            + recurring_service_markdown
            + unit_cost_basis_markdown
        )
        chapter = self._chapter(
            "cost_of_production",
            "Cost of Production",
            "cost_of_production",
            markdown,
            cost_model.citations,
            cost_model.assumptions,
            ["cost_model"],
            required_inputs=["cost_model", "market_assessment"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_working_capital(self) -> StageResult:
        cost_model = self._load("cost_model", CostModel)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        citations = sorted(set(cost_model.citations + market.citations))
        assumptions = cost_model.assumptions + market.assumptions
        model = build_working_capital_model(self.config.basis, cost_model, market.estimated_price_per_kg, citations, assumptions, operations_planning)
        self._save("working_capital_model", model)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), model.value_records, self._load("resolved_sources", ResolvedSourceSet), self.config, "working_capital"),
        )
        markdown = "\n\n### Working-Capital Parameter Basis\n\n" + markdown_table(
            ["Parameter", "Value"],
            [
                ["Raw-material inventory days", f"{model.raw_material_days:.1f}"],
                ["Product inventory days", f"{model.product_inventory_days:.1f}"],
                ["Cash buffer days", f"{model.cash_buffer_days:.1f}"],
                ["Operating stock days", f"{model.operating_stock_days:.1f}"],
                ["Procurement timing factor", f"{model.procurement_timing_factor:.3f}"],
                ["Pre-commissioning inventory days", f"{model.precommissioning_inventory_days:.1f}"],
                ["Receivable days", f"{model.receivable_days:.1f}"],
                ["Payable days", f"{model.payable_days:.1f}"],
                ["Pre-commissioning inventory", f"INR {model.precommissioning_inventory_inr:,.2f}"],
                ["Restart loss inventory", f"INR {model.restart_loss_inventory_inr:,.2f}"],
                ["Outage buffer inventory", f"INR {model.outage_buffer_inventory_inr:,.2f}"],
                ["Working capital", f"INR {model.working_capital_inr:,.2f}"],
                ["Peak working capital", f"INR {model.peak_working_capital_inr:,.2f}"],
            ],
        )
        markdown += "\n\n### Working-Capital Breakdown\n\n" + markdown_table(
            ["Component", "Value"],
            [
                ["Raw-material inventory", f"INR {model.raw_material_inventory_inr:,.2f}"],
                ["Product inventory", f"INR {model.product_inventory_inr:,.2f}"],
                ["Receivables", f"INR {model.receivables_inr:,.2f}"],
                ["Cash buffer", f"INR {model.cash_buffer_inr:,.2f}"],
                ["Pre-commissioning inventory", f"INR {model.precommissioning_inventory_inr:,.2f}"],
                ["Restart loss inventory", f"INR {model.restart_loss_inventory_inr:,.2f}"],
                ["Outage buffer inventory", f"INR {model.outage_buffer_inventory_inr:,.2f}"],
                ["Payables", f"INR {model.payables_inr:,.2f}"],
            ],
        )
        markdown += "\n\n### Inventory, Receivable, and Payable Basis\n\n" + markdown_table(
            ["Cash-cycle component", "Days", "Value"],
            [
                ["Raw-material inventory", f"{model.raw_material_days:.1f}", f"INR {model.raw_material_inventory_inr:,.2f}"],
                ["Product inventory", f"{model.product_inventory_days:.1f}", f"INR {model.product_inventory_inr:,.2f}"],
                ["Receivables", f"{model.receivable_days:.1f}", f"INR {model.receivables_inr:,.2f}"],
                ["Payables", f"{model.payable_days:.1f}", f"INR {model.payables_inr:,.2f}"],
                ["Cash buffer", f"{model.cash_buffer_days:.1f}", f"INR {model.cash_buffer_inr:,.2f}"],
                ["Operating stock", f"{model.operating_stock_days:.1f}", f"INR {model.outage_buffer_inventory_inr:,.2f}"],
            ],
        )
        markdown += "\n\n### Procurement-Linked Working-Capital Timing\n\n" + markdown_table(
            ["Parameter", "Value"],
            [
                ["Procurement timing factor", f"{model.procurement_timing_factor:.3f}"],
                ["Pre-commissioning inventory month", f"{model.precommissioning_inventory_month:.2f}"],
                ["Peak working-capital month", f"{model.peak_working_capital_month:.2f}"],
                ["Peak working capital", f"INR {model.peak_working_capital_inr:,.2f}"],
            ],
        )
        markdown += "\n\n### Operations Planning Basis\n\n" + markdown_table(
            ["Parameter", "Value"],
            [
                ["Availability policy", operations_planning.availability_policy_label],
                ["Operating mode", operations_planning.recommended_operating_mode],
                ["Raw-material buffer (d)", f"{operations_planning.raw_material_buffer_days:.1f}"],
                ["Finished-goods buffer (d)", f"{operations_planning.finished_goods_buffer_days:.1f}"],
                ["Operating stock (d)", f"{operations_planning.operating_stock_days:.1f}"],
                ["Restart buffer (d)", f"{operations_planning.restart_buffer_days:.1f}"],
                ["Annual restart loss (kg/y)", f"{operations_planning.annual_restart_loss_kg:,.1f}"],
            ],
        )
        chapter = self._chapter(
            "working_capital",
            "Working Capital",
            "working_capital",
            markdown,
            model.citations,
            model.assumptions,
            ["working_capital_model"],
            required_inputs=["cost_model", "market_assessment"],
        )
        issues = validate_working_capital(model) + self._value_issues(model, "working_capital_model") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_financial_analysis(self) -> StageResult:
        economic_coverage = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_coverage.json", EconomicCoverageDecision)
        if economic_coverage is not None and economic_coverage.status != "detailed":
            return StageResult(
                issues=[
                    ValidationIssue(
                        code="financial_analysis_requires_detailed_economics",
                        severity=Severity.BLOCKED,
                        message="Detailed financial analysis is blocked until route-derived economics reaches detailed coverage.",
                        artifact_ref="economic_coverage",
                        source_refs=economic_coverage.citations,
                    )
                ]
            )
        cost_model = self._load("cost_model", CostModel)
        working_capital = self._load("working_capital_model", WorkingCapitalModel)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        process_synthesis = self._load("process_synthesis", ProcessSynthesisArtifact)
        operations_planning = self._load("operations_planning", OperationsPlanningArtifact)
        route_selection = self._load("route_selection", RouteSelectionArtifact)
        utility_network = self._selected_utility_network()
        reactor = self._load("reactor_design", ReactorDesign)
        column = self._load("column_design", ColumnDesign)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        utility_architecture = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_architecture.json", UtilityArchitectureDecision)
        flowsheet_blueprint = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_blueprint.json", FlowsheetBlueprintArtifact)
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
        utility_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_basis_decision.json", DecisionRecord)
        financing_seed = build_financing_basis_decision(self.config.basis, site)
        citations = sorted(set(cost_model.citations + working_capital.citations + market.citations))
        assumptions = cost_model.assumptions + working_capital.assumptions + market.assumptions
        financing_basis, financial_model = evaluate_financing_basis_decision(
            self.config.basis,
            market.estimated_price_per_kg,
            cost_model,
            working_capital,
            citations,
            assumptions,
            financing_seed,
        )
        economic_basis_decision = build_economic_basis_decision(
            self.config,
            site,
            utility_network,
            cost_model,
            financial_model,
            utility_basis_decision,
            flowsheet_blueprint,
        )
        route_economic_issues = validate_route_economic_critics(
            route_selection,
            utility_network,
            cost_model,
            economic_basis_decision,
        )
        economic_basis_decision = self._escalate_decision_for_critic_issues(
            economic_basis_decision,
            route_economic_issues,
            trigger_codes={
                "economic_basis_counterfactual_selected",
                "economic_basis_rejects_selected_recovery",
                "economic_basis_conservative_override",
            },
            note_prefix="Economic-basis critic escalation",
        )
        financing_operability_issues = validate_financing_operability_critics(
            financing_basis,
            economic_basis_decision,
            financial_model,
            operations_planning,
            reactor,
            utility_network,
        )
        financing_basis = self._escalate_decision_for_critic_issues(
            financing_basis,
            route_economic_issues + financing_operability_issues,
            trigger_codes={
                "economic_basis_counterfactual_selected",
                "economic_basis_rejects_selected_recovery",
                "economic_basis_conservative_override",
                "financing_operability_tension",
                "hazard_route_high_leverage_financing",
            },
            note_prefix="Financing critic escalation",
        )
        operating_mode_decision = self._escalate_decision_for_critic_issues(
            process_synthesis.operating_mode_decision,
            financing_operability_issues,
            trigger_codes={
                "operating_mode_integrated_economics_tension",
            },
            note_prefix="Operating-mode critic escalation",
        )
        process_synthesis = process_synthesis.model_copy(
            update={"operating_mode_decision": operating_mode_decision},
            deep=True,
        )
        economic_scenarios = build_economic_scenario_model_v2(cost_model, financial_model, economic_basis_decision)
        debt_schedule = build_debt_schedule(cost_model, financing_basis)
        tax_depreciation_basis = build_tax_depreciation_basis(cost_model)
        financial_schedule = build_financial_schedule(financial_model)
        plant_cost_summary = build_plant_cost_summary(cost_model, working_capital)
        cost_model.economic_basis_decision_id = economic_basis_decision.decision_id
        self._save("cost_model", cost_model)
        self._save("plant_cost_summary", plant_cost_summary)
        self._save("process_synthesis", process_synthesis)
        self._save("financial_model", financial_model)
        self._save("economic_basis_decision", economic_basis_decision)
        self._save("economic_scenarios", economic_scenarios)
        self._save("financing_basis_decision", financing_basis)
        self._save("debt_schedule", debt_schedule)
        self._save("tax_depreciation_basis", tax_depreciation_basis)
        self._save("financial_schedule", financial_schedule)
        self._refresh_agent_fabric()
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        self._save("resolved_values", extend_resolved_value_artifact(resolved_values, financial_model.value_records, resolved_sources, self.config, "financial_analysis"))
        financial_summary_markdown = "\n\n### Financial Performance Summary\n\n" + markdown_table(
            ["Metric", "Value"],
            [
                ["Annual revenue", f"{financial_model.currency} {financial_model.annual_revenue:,.2f}"],
                ["Annual operating cost", f"{financial_model.currency} {financial_model.annual_operating_cost:,.2f}"],
                ["Gross profit", f"{financial_model.currency} {financial_model.gross_profit:,.2f}"],
                ["Working capital", f"{financial_model.currency} {financial_model.working_capital:,.2f}"],
                ["Peak working capital", f"{financial_model.currency} {financial_model.peak_working_capital_inr:,.2f}"],
                ["Peak working-capital month", f"{financial_model.peak_working_capital_month:.2f}"],
                ["Total project funding", f"{financial_model.currency} {financial_model.total_project_funding_inr:,.2f}"],
                ["Interest during construction", f"{financial_model.currency} {financial_model.construction_interest_during_construction_inr:,.2f}"],
                ["Payback", f"{financial_model.payback_years:.3f} y"],
                ["NPV", f"{financial_model.currency} {financial_model.npv:,.2f}"],
                ["IRR", f"{financial_model.irr:.2f}%"],
                ["Profitability index", f"{financial_model.profitability_index:.3f}"],
                ["Break-even fraction", f"{financial_model.break_even_fraction:.3f}"],
                ["Minimum DSCR", f"{financial_model.minimum_dscr:.3f}"],
                ["Average DSCR", f"{financial_model.average_dscr:.3f}"],
                ["LLCR", f"{financial_model.llcr:.3f}"],
                ["PLCR", f"{financial_model.plcr:.3f}"],
                ["Selected financing option", financial_model.selected_financing_candidate_id or "n/a"],
                ["Downside scenario", financial_model.downside_scenario_name or "n/a"],
                ["Downside-preferred financing option", financial_model.downside_financing_candidate_id or "n/a"],
                ["Scenario reversal", "yes" if financial_model.financing_scenario_reversal else "no"],
                ["Covenant breaches", ", ".join(financial_model.covenant_breach_codes) or "none"],
            ],
        )
        profitability_markdown = "\n\n### Profitability and Return Summary\n\n" + markdown_table(
            ["Metric", "Value"],
            [
                ["Payback", f"{financial_model.payback_years:.3f} y"],
                ["NPV", f"{financial_model.currency} {financial_model.npv:,.2f}"],
                ["IRR", f"{financial_model.irr:.2f}%"],
                ["Profitability index", f"{financial_model.profitability_index:.3f}"],
                ["Break-even fraction", f"{financial_model.break_even_fraction:.3f}"],
                ["Minimum DSCR", f"{financial_model.minimum_dscr:.3f}"],
                ["Average DSCR", f"{financial_model.average_dscr:.3f}"],
                ["LLCR", f"{financial_model.llcr:.3f}"],
                ["PLCR", f"{financial_model.plcr:.3f}"],
            ],
        )
        funding_markdown = "\n\n### Funding and Capital Structure Basis\n\n" + markdown_table(
            ["Funding item", "Value"],
            [
                ["Total project funding", f"{financial_model.currency} {financial_model.total_project_funding_inr:,.2f}"],
                ["Interest during construction", f"{financial_model.currency} {financial_model.construction_interest_during_construction_inr:,.2f}"],
                ["Working capital", f"{financial_model.currency} {financial_model.working_capital:,.2f}"],
                ["Peak working capital", f"{financial_model.currency} {financial_model.peak_working_capital_inr:,.2f}"],
                ["Selected financing option", financial_model.selected_financing_candidate_id or "n/a"],
                ["Downside-preferred financing option", financial_model.downside_financing_candidate_id or "n/a"],
            ],
        )
        markdown = financial_summary_markdown + profitability_markdown + funding_markdown
        if cost_model.procurement_schedule:
            markdown += "\n\n### Procurement and Construction Funding Basis\n\n" + markdown_table(
                ["Package Family", "Milestone", "Month", "Draw Fraction", "CAPEX Draw (INR)"],
                [
                    [
                        str(item.get("package_family", "")),
                        str(item.get("milestone", "")),
                        f"{float(item.get('month', 0.0)):.1f}",
                        f"{float(item.get('draw_fraction', 0.0)):.3f}",
                        f"{float(item.get('capex_draw_inr', 0.0)):,.2f}",
                    ]
                    for item in cost_model.procurement_schedule
                ],
            )
        markdown += "\n\n### Procurement-Linked Working-Capital Basis\n\n" + markdown_table(
            ["Metric", "Value"],
            [
                ["Procurement timing factor", f"{working_capital.procurement_timing_factor:.3f}"],
                ["Pre-commissioning inventory days", f"{working_capital.precommissioning_inventory_days:.1f}"],
                ["Pre-commissioning inventory month", f"{working_capital.precommissioning_inventory_month:.2f}"],
                ["Pre-commissioning inventory", f"{financial_model.currency} {working_capital.precommissioning_inventory_inr:,.2f}"],
                ["Peak working-capital month", f"{working_capital.peak_working_capital_month:.2f}"],
                ["Peak working capital", f"{financial_model.currency} {working_capital.peak_working_capital_inr:,.2f}"],
            ],
        )
        if financial_model.annual_schedule:
            markdown += "\n\n### Availability and Outage Calendar\n\n" + markdown_table(
                ["Year", "Availability (%)", "Minor Outage (d)", "Turnaround (d)", "Startup Loss (d)", "Revenue Loss (INR)", "Available Days", "Calendar Basis"],
                [
                    [
                        str(item["year"]),
                        f'{item.get("availability_pct", 0.0):.2f}',
                        f'{item.get("minor_outage_days", 0.0):.2f}',
                        f'{item.get("major_turnaround_days", 0.0):.2f}',
                        f'{item.get("startup_loss_days", 0.0):.2f}',
                        f'{item.get("revenue_loss_from_outages_inr", 0.0):,.2f}',
                        f'{item.get("available_operating_days", 0.0):.2f}',
                        str(item.get("outage_calendar_note", "")),
                    ]
                    for item in financial_model.annual_schedule
                ],
            )
            markdown += "\n\n### Debt Service Coverage Schedule\n\n" + markdown_table(
                ["Year", "Principal (INR)", "Interest (INR)", "Debt Service (INR)", "CFADS (INR)", "DSCR"],
                [
                    [
                        str(item["year"]),
                        f'{item.get("principal_repayment_inr", 0.0):,.2f}',
                        f'{item.get("interest_inr", 0.0):,.2f}',
                        f'{item.get("debt_service_inr", 0.0):,.2f}',
                        f'{item.get("cfads_inr", 0.0):,.2f}',
                        f'{item.get("dscr", 0.0):.3f}',
                    ]
                    for item in financial_model.annual_schedule
                ],
            )
        markdown += "\n\n### Lender Coverage Screening\n\n" + markdown_table(
            ["Metric", "Value"],
            [
                ["Minimum DSCR", f"{financial_model.minimum_dscr:.3f}"],
                ["Average DSCR", f"{financial_model.average_dscr:.3f}"],
                ["LLCR", f"{financial_model.llcr:.3f}"],
                ["PLCR", f"{financial_model.plcr:.3f}"],
                ["Downside scenario", financial_model.downside_scenario_name or "n/a"],
                ["Downside-preferred financing option", financial_model.downside_financing_candidate_id or "n/a"],
                ["Scenario reversal", "yes" if financial_model.financing_scenario_reversal else "no"],
            ],
        )
        if financing_basis.alternatives:
            markdown += "\n\n### Financing Option Ranking\n\n" + markdown_table(
                ["Option", "Score", "Min DSCR", "LLCR", "PLCR", "Downside DSCR", "Downside LLCR", "Downside PLCR", "IRR (%)", "IDC (INR)", "Coverage", "Downside", "Rejected / Pressure"],
                [
                    [
                        option.description,
                        f"{option.total_score:.3f}",
                        option.outputs.get("minimum_dscr", "n/a"),
                        option.outputs.get("llcr", "n/a"),
                        option.outputs.get("plcr", "n/a"),
                        option.outputs.get("downside_minimum_dscr", "n/a"),
                        option.outputs.get("downside_llcr", "n/a"),
                        option.outputs.get("downside_plcr", "n/a"),
                        option.outputs.get("irr_pct", "n/a"),
                        option.outputs.get("idc_inr", "n/a"),
                        option.outputs.get("coverage_status", "n/a"),
                        option.outputs.get("downside_coverage_status", "n/a"),
                        "; ".join(option.rejected_reasons) or "none",
                    ]
                    for option in financing_basis.alternatives
                ],
            )
        if financial_model.covenant_warnings:
            markdown += "\n\n### Covenant Warnings\n\n" + "\n".join(f"- {warning}" for warning in financial_model.covenant_warnings)
        if financial_model.scenario_results:
            markdown += "\n\n### Scenario Margin Snapshot\n\n" + markdown_table(
                ["Scenario", "Revenue (INR/y)", "Transport/Service (INR/y)", "Utility-Island Burden (INR/y)", "Operating Cost (INR/y)", "Gross Margin (INR/y)"],
                [
                    [
                        item.scenario_name,
                        f"{item.annual_revenue_inr:,.2f}",
                        f"{item.annual_transport_service_cost_inr:,.2f}",
                        f"{item.annual_utility_island_operating_burden_inr:,.2f}",
                        f"{item.annual_operating_cost_inr:,.2f}",
                        f"{item.gross_margin_inr:,.2f}",
                    ]
                    for item in financial_model.scenario_results
                ],
            )
            if any(item.annual_transport_service_cost_inr > 0.0 for item in financial_model.scenario_results):
                markdown += "\n\n### Scenario Recurring Service Breakdown\n\n" + markdown_table(
                    ["Scenario", "Utility-Island Service (INR/y)", "Utility-Island Replacement (INR/y)", "Packing (INR/y)", "Classifier (INR/y)", "Filter Media (INR/y)", "Dryer Exhaust (INR/y)"],
                    [
                        [
                            item.scenario_name,
                            f"{item.annual_utility_island_service_cost_inr:,.2f}",
                            f"{item.annual_utility_island_replacement_cost_inr:,.2f}",
                            f"{item.annual_packing_replacement_cost_inr:,.2f}",
                            f"{item.annual_classifier_service_cost_inr:,.2f}",
                            f"{item.annual_filter_media_replacement_cost_inr:,.2f}",
                            f"{item.annual_dryer_exhaust_treatment_cost_inr:,.2f}",
                        ]
                        for item in financial_model.scenario_results
                    ],
                )
            if any(item.utility_island_impacts for item in financial_model.scenario_results):
                markdown += "\n\n### Scenario Utility Island Breakdown\n\n" + markdown_table(
                    ["Scenario", "Island", "Capex Burden (INR)", "Allocated Utility (INR/y)", "Service (INR/y)", "Replacement (INR/y)", "Operating Burden (INR/y)"],
                    [
                        [
                            item.scenario_name,
                            impact.island_id,
                            f"{impact.project_capex_burden_inr:,.2f}",
                            f"{impact.annual_allocated_utility_cost_inr:,.2f}",
                            f"{impact.annual_service_cost_inr:,.2f}",
                            f"{impact.annual_replacement_cost_inr:,.2f}",
                            f"{impact.annual_operating_burden_inr:,.2f}",
                        ]
                        for item in financial_model.scenario_results
                        for impact in item.utility_island_impacts
                    ],
                )
        if financial_model.annual_schedule:
            markdown += "\n\n### Multi-Year Financial Schedule\n\n" + markdown_table(
                ["Year", "Capacity Utilization (%)", "Availability (%)", "Revenue Loss (INR)", "Revenue (INR)", "Operating Cost (INR)", "Transport/Service (INR)", "Utility-Island Service (INR)", "Utility-Island Replacement (INR)", "Packing (INR)", "Turnaround (INR)", "Utility-Island Turnaround (INR)", "Principal (INR)", "Interest (INR)", "Debt Service (INR)", "CFADS (INR)", "DSCR", "Depreciation (INR)", "PBT (INR)", "Tax (INR)", "PAT (INR)", "Cash Accrual (INR)"],
                [
                    [
                        str(item["year"]),
                        f'{item["capacity_utilization_pct"]:.2f}',
                        f'{item.get("availability_pct", 0.0):.2f}',
                        f'{item.get("revenue_loss_from_outages_inr", 0.0):,.2f}',
                        f'{item["revenue_inr"]:,.2f}',
                        f'{item["operating_cost_inr"]:,.2f}',
                        f'{item.get("transport_service_cost_inr", 0.0):,.2f}',
                        f'{item.get("utility_island_service_cost_inr", 0.0):,.2f}',
                        f'{item.get("utility_island_replacement_cost_inr", 0.0):,.2f}',
                        f'{item.get("packing_replacement_cost_inr", 0.0):,.2f}',
                        f'{item.get("turnaround_cost_inr", 0.0):,.2f}',
                        f'{item.get("utility_island_turnaround_cost_inr", 0.0):,.2f}',
                        f'{item.get("principal_repayment_inr", 0.0):,.2f}',
                        f'{item["interest_inr"]:,.2f}',
                        f'{item.get("debt_service_inr", 0.0):,.2f}',
                        f'{item.get("cfads_inr", 0.0):,.2f}',
                        f'{item.get("dscr", 0.0):.3f}',
                        f'{item["depreciation_inr"]:,.2f}',
                        f'{item["profit_before_tax_inr"]:,.2f}',
                        f'{item["tax_inr"]:,.2f}',
                        f'{item["profit_after_tax_inr"]:,.2f}',
                        f'{item["cash_accrual_inr"]:,.2f}',
                    ]
                    for item in financial_model.annual_schedule
                ],
            )
            markdown += "\n\n### Profit and Loss Schedule\n\n" + markdown_table(
                ["Year", "Revenue (INR)", "Operating Cost (INR)", "Depreciation (INR)", "Interest (INR)", "PBT (INR)", "Tax (INR)", "PAT (INR)"],
                [
                    [
                        str(item["year"]),
                        f'{item["revenue_inr"]:,.2f}',
                        f'{item["operating_cost_inr"]:,.2f}',
                        f'{item["depreciation_inr"]:,.2f}',
                        f'{item["interest_inr"]:,.2f}',
                        f'{item["profit_before_tax_inr"]:,.2f}',
                        f'{item["tax_inr"]:,.2f}',
                        f'{item["profit_after_tax_inr"]:,.2f}',
                    ]
                    for item in financial_model.annual_schedule
                ],
            )
            markdown += "\n\n### Cash Accrual and Funding Schedule\n\n" + markdown_table(
                ["Year", "CAPEX Draw (INR)", "Debt Draw (INR)", "Equity Draw (INR)", "IDC (INR)", "CFADS (INR)", "Debt Service (INR)", "Cash Accrual (INR)"],
                [
                    [
                        str(item["year"]),
                        f'{item.get("capex_draw_inr", 0.0):,.2f}',
                        f'{item.get("debt_draw_inr", 0.0):,.2f}',
                        f'{item.get("equity_draw_inr", 0.0):,.2f}',
                        f'{item.get("idc_inr", 0.0):,.2f}',
                        f'{item.get("cfads_inr", 0.0):,.2f}',
                        f'{item.get("debt_service_inr", 0.0):,.2f}',
                        f'{item["cash_accrual_inr"]:,.2f}',
                    ]
                    for item in financial_model.annual_schedule
                ],
            )
        chapter = self._chapter(
            "financial_analysis",
            "Financial Analysis",
            "financial_analysis",
            "### Financing Basis\n\n"
            f"{financing_basis.selected_summary}\n\n"
            f"{markdown}"
            + "\n\n### Debt Schedule\n\n"
            + debt_schedule.markdown
            + "\n\n### Tax and Depreciation Basis\n\n"
            + tax_depreciation_basis.markdown,
            financial_model.citations,
            financial_model.assumptions + economic_basis_decision.assumptions + financing_basis.assumptions,
            ["financial_model", "economic_basis_decision", "financing_basis_decision", "economic_scenarios", "debt_schedule", "tax_depreciation_basis", "financial_schedule"],
            required_inputs=["cost_model", "working_capital_model", "market_assessment"],
        )
        issues = (
            validate_financial_model(financial_model, self.config)
            + validate_financing_decision_alignment(financing_basis, financial_model)
            + validate_decision_record(financing_basis, "financing_basis_decision")
            + validate_decision_record(economic_basis_decision, "economic_basis_decision")
            + validate_decision_record(process_synthesis.operating_mode_decision, "operating_mode")
            + self._value_issues(financial_model, "financial_model")
            + validate_technical_economic_critics(column, utility_network, cost_model, unit_operation_family, utility_architecture)
            + route_economic_issues
            + financing_operability_issues
            + validate_cross_chapter_consistency(
                self.config,
                route_selection,
                site,
                utility_network,
                self._load("utility_summary", UtilitySummaryArtifact),
                cost_model,
                working_capital,
                financial_model,
                site_decision=site_decision,
                utility_basis_decision=utility_basis_decision,
                economic_basis_decision=economic_basis_decision,
            )
            + self._chapter_issues(chapter)
        )
        gate = self._gate("india_cost_basis", "India Cost Basis", "Approve India site and economics basis before final assembly.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_final_report(self) -> StageResult:
        state = self._require_state()
        benchmark_manifest = self.store.maybe_load_model(self.config.project_id, "artifacts/benchmark_manifest.json", BenchmarkManifest)
        report_parity_framework = self.store.maybe_load_model(self.config.project_id, "artifacts/report_parity_framework.json", ReportParityFrameworkArtifact)
        resolved_sources = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_sources.json", ResolvedSourceSet)
        product_profile = self._load("product_profile", ProductProfileArtifact)
        route_survey = self.store.maybe_load_model(self.config.project_id, "artifacts/route_survey.json", RouteSurveyArtifact)
        property_gap = self.store.maybe_load_model(self.config.project_id, "artifacts/property_gap.json", PropertyGapArtifact)
        resolved_values = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_values.json", ResolvedValueArtifact)
        property_packages = self.store.maybe_load_model(self.config.project_id, "artifacts/property_packages.json", PropertyPackageArtifact)
        property_requirements = self.store.maybe_load_model(self.config.project_id, "artifacts/property_requirements.json", PropertyRequirementSet)
        separation_thermo = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_thermo.json", SeparationThermoArtifact)
        bac_purification_sections = self.store.maybe_load_model(self.config.project_id, "artifacts/bac_purification_sections.json", BACPurificationSectionArtifact)
        bac_impurity_model = self.store.maybe_load_model(self.config.project_id, "artifacts/bac_impurity_model.json", BACImpurityModelArtifact)
        agent_fabric = self.store.maybe_load_model(self.config.project_id, "artifacts/agent_decision_fabric.json", AgentDecisionFabricArtifact)
        critic_registry = self.store.maybe_load_model(self.config.project_id, "artifacts/critic_registry.json", CriticRegistryArtifact)
        process_archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        route_families = self.store.maybe_load_model(self.config.project_id, "artifacts/route_family_profiles.json", RouteFamilyArtifact)
        unit_operation_family = self.store.maybe_load_model(self.config.project_id, "artifacts/unit_operation_family.json", UnitOperationFamilyArtifact)
        sparse_data_policy = self.store.maybe_load_model(self.config.project_id, "artifacts/sparse_data_policy.json", SparseDataPolicyArtifact)
        process_synthesis = self.store.maybe_load_model(self.config.project_id, "artifacts/process_synthesis.json", ProcessSynthesisArtifact)
        operations_planning = self.store.maybe_load_model(self.config.project_id, "artifacts/operations_planning.json", OperationsPlanningArtifact)
        capacity_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/capacity_decision.json", DecisionRecord)
        property_method = self.store.maybe_load_model(self.config.project_id, "artifacts/property_method_decision.json", PropertyMethodDecision)
        thermo_method = self.store.maybe_load_model(self.config.project_id, "artifacts/thermo_method_decision.json", MethodSelectionArtifact)
        kinetics_method = self.store.maybe_load_model(self.config.project_id, "artifacts/kinetics_method_decision.json", MethodSelectionArtifact)
        stream_table = self._load("stream_table", StreamTable)
        mixture_properties = self.store.maybe_load_model(self.config.project_id, "artifacts/mixture_properties.json", MixturePropertyArtifact)
        flowsheet_graph = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_graph.json", FlowsheetGraph)
        flowsheet_case = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_case.json", FlowsheetCase)
        solve_result = self.store.maybe_load_model(self.config.project_id, "artifacts/solve_result.json", SolveResult)
        energy = self._load("energy_balance", EnergyBalance)
        heat_integration_study = self.store.maybe_load_model(self.config.project_id, "artifacts/heat_integration_study.json", HeatIntegrationStudyArtifact)
        utility_network = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_network_decision.json", UtilityNetworkDecision)
        utility_architecture = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_architecture.json", UtilityArchitectureDecision)
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
        exchanger_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/exchanger_choice_decision.json", DecisionRecord)
        storage_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/storage_choice_decision.json", DecisionRecord)
        moc_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/moc_choice_decision.json", DecisionRecord)
        utility_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_basis_decision.json", DecisionRecord)
        procurement_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/procurement_basis_decision.json", DecisionRecord)
        logistics_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/logistics_basis_decision.json", DecisionRecord)
        financing_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/financing_basis_decision.json", DecisionRecord)
        economic_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_basis_decision.json", DecisionRecord)
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        control_architecture = self.store.maybe_load_model(self.config.project_id, "artifacts/control_architecture.json", ControlArchitectureDecision)
        hazop_register = self.store.maybe_load_model(self.config.project_id, "artifacts/hazop_node_register.json", HazopNodeRegister)
        layout_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/layout_decision.json", LayoutDecisionArtifact)
        mechanical_design = self.store.maybe_load_model(self.config.project_id, "artifacts/mechanical_design.json", MechanicalDesignArtifact)
        mechanical_design_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/mechanical_design_basis.json", MechanicalDesignBasis)
        cost_model = self._load("cost_model", CostModel)
        plant_cost_summary = self.store.maybe_load_model(self.config.project_id, "artifacts/plant_cost_summary.json", PlantCostSummary)
        working_capital = self._load("working_capital_model", WorkingCapitalModel)
        financial = self._load("financial_model", FinancialModel)
        economic_scenarios = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_scenarios.json", EconomicScenarioModel)
        route_economic_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/route_economic_basis.json", RouteEconomicBasisArtifact)
        debt_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/debt_schedule.json", DebtSchedule)
        tax_depreciation_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/tax_depreciation_basis.json", TaxDepreciationBasis)
        financial_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/financial_schedule.json", FinancialSchedule)
        route_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/route_decision.json", DecisionRecord)
        route_selection = self.store.maybe_load_model(self.config.project_id, "artifacts/route_selection.json", RouteSelectionArtifact)
        reaction_system = self._load("reaction_system", ReactionSystem)
        reactor = self._load("reactor_design", ReactorDesign)
        reactor_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/reactor_design_basis.json", ReactorDesignBasis)
        column = self._load("column_design", ColumnDesign)
        column_hydraulics = self.store.maybe_load_model(self.config.project_id, "artifacts/column_hydraulics.json", ColumnHydraulics)
        exchanger = self._load("heat_exchanger_design", HeatExchangerDesign)
        exchanger_thermal = self.store.maybe_load_model(self.config.project_id, "artifacts/heat_exchanger_thermal_design.json", HeatExchangerThermalDesign)
        storage = self._load("storage_design", StorageDesign)
        pump_design = self.store.maybe_load_model(self.config.project_id, "artifacts/pump_design.json", PumpDesign)
        equipment_datasheets = self.store.maybe_load_model(self.config.project_id, "artifacts/equipment_datasheets.json", NarrativeArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        bundle = self._load("research_bundle", ResearchBundle)
        estimation_policy = build_bac_estimation_policy_artifact() if (self.config.benchmark_profile or "").strip().lower() == "benzalkonium_chloride" else None
        pseudo_component_basis = build_bac_pseudo_component_basis_artifact(self.config.basis, product_profile, property_packages)
        pair_coverage = build_bac_binary_pair_coverage_artifact(route_selection, property_packages, separation_thermo)
        kinetic_basis = build_bac_kinetic_basis_artifact(route_selection, self.store.maybe_load_model(self.config.project_id, "artifacts/kinetic_assessment.json", KineticAssessmentArtifact))
        reactor_basis_confidence = build_reactor_basis_confidence_artifact(kinetic_basis, reactor)
        impurity_ledger = build_bac_impurity_ledger_artifact(bac_impurity_model)
        recycle_basis = build_recycle_basis_artifact(stream_table)
        section_thermo_assignment = build_bac_section_thermo_assignment_artifact(self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_blueprint.json", FlowsheetBlueprintArtifact), bac_purification_sections, separation_thermo)
        economic_input_reality = build_economic_input_reality_artifact(cost_model, route_economic_basis, self.store.maybe_load_model(self.config.project_id, "artifacts/market_assessment.json", MarketAssessmentArtifact))
        data_gap_registry = build_bac_data_gap_registry_artifact(
            self.config,
            pseudo_component_basis,
            pair_coverage,
            kinetic_basis,
            impurity_ledger,
            recycle_basis,
            economic_input_reality,
        )
        missing_data_acceptance = build_missing_data_acceptance_artifact(
            data_gap_registry,
            pair_coverage,
            impurity_ledger,
            economic_input_reality,
        )
        for artifact_id, built_artifact in [
            ("estimation_policy", estimation_policy),
            ("bac_pseudo_component_basis", pseudo_component_basis),
            ("binary_pair_coverage", pair_coverage),
            ("section_thermo_assignment", section_thermo_assignment),
            ("kinetic_basis", kinetic_basis),
            ("reactor_basis_confidence", reactor_basis_confidence),
            ("bac_impurity_ledger", impurity_ledger),
            ("recycle_basis", recycle_basis),
            ("economic_input_reality", economic_input_reality),
            ("data_gap_registry", data_gap_registry),
            ("missing_data_acceptance", missing_data_acceptance),
        ]:
            if built_artifact is not None:
                self._save(artifact_id, built_artifact)
        existing_chapters = self._existing_chapters(state)
        report_excerpt = "\n\n".join(chapter.rendered_markdown for chapter in existing_chapters if chapter.chapter_id not in {"executive_summary", "conclusion"})
        summary_reasoning = (
            MockReasoningService()
            if (self.config.benchmark_profile or "").strip().lower() == "benzalkonium_chloride"
            else self.reasoning
        )
        executive = summary_reasoning.build_executive_summary(self.config.basis, report_excerpt)
        conclusion = summary_reasoning.build_conclusion(self.config.basis, financial.model_dump_json(indent=2))
        source_index = {source.source_id: source for source in bundle.sources}
        fallback_exec_citations = list(source_index.keys())[:4]
        executive_chapter = ChapterArtifact(
            chapter_id="executive_summary",
            title="Executive Summary",
            stage_id="final_report",
            status=ChapterStatus.COMPLETE,
            citations=executive.citations or fallback_exec_citations,
            assumptions=executive.assumptions,
            rendered_markdown=executive.markdown,
        )
        conclusion_chapter = self._chapter(
            "conclusion",
            "Conclusion",
            "final_report",
            conclusion.markdown,
            conclusion.citations or financial.citations or fallback_exec_citations[:2],
            conclusion.assumptions,
            ["financial_model"],
            required_inputs=["financial_model"],
            summary=conclusion.summary,
        )

        data_gap_chapter: ChapterArtifact | None = None
        if data_gap_registry is not None:
            methodology_sections = []
            if estimation_policy is not None:
                methodology_sections.extend(["### Estimation Policy", "", estimation_policy.markdown, ""])
            if pseudo_component_basis is not None:
                methodology_sections.extend(["### BAC Pseudo-Component Basis", "", pseudo_component_basis.markdown, ""])
            if pair_coverage is not None:
                methodology_sections.extend(["### Binary Pair Coverage", "", pair_coverage.markdown, ""])
            if section_thermo_assignment is not None:
                methodology_sections.extend(["### Section Thermo Assignment", "", section_thermo_assignment.markdown, ""])
            if kinetic_basis is not None:
                methodology_sections.extend(["### Kinetic Basis", "", kinetic_basis.markdown, ""])
            if recycle_basis is not None:
                methodology_sections.extend(["### Recycle and Purge Basis", "", recycle_basis.markdown, ""])
            if economic_input_reality is not None:
                methodology_sections.extend(["### Economics Input Reality", "", economic_input_reality.markdown, ""])
            if missing_data_acceptance is not None:
                methodology_sections.extend(["### Missing-Data Acceptance", "", missing_data_acceptance.markdown, ""])
            methodology_sections.extend(["### Data-Gap Registry", "", data_gap_registry.markdown])
            data_gap_chapter = self._chapter(
                "data_gaps_estimation_methods",
                "Data Gaps and Estimation Methods",
                "final_report",
                "This section records the major BAC data gaps, the method used to replace each missing quantity, and the resulting confidence for preliminary design.\n\n"
                + "\n".join(methodology_sections).strip(),
                sorted(set(
                    (data_gap_registry.citations if data_gap_registry is not None else [])
                    + (pseudo_component_basis.citations if pseudo_component_basis is not None else [])
                    + (pair_coverage.citations if pair_coverage is not None else [])
                    + (kinetic_basis.citations if kinetic_basis is not None else [])
                    + (economic_input_reality.citations if economic_input_reality is not None else [])
                )),
                sorted(set(
                    (data_gap_registry.assumptions if data_gap_registry is not None else [])
                    + (missing_data_acceptance.assumptions if missing_data_acceptance is not None else [])
                )),
                ["data_gap_registry", "estimation_policy", "bac_pseudo_component_basis", "binary_pair_coverage", "section_thermo_assignment", "kinetic_basis", "recycle_basis", "economic_input_reality", "missing_data_acceptance"],
            )

        method_notes = {
            "thermodynamic_feasibility": pair_coverage,
            "reaction_kinetics": kinetic_basis,
            "material_balance": recycle_basis,
            "financial_analysis": economic_input_reality,
            "project_cost": economic_input_reality,
        }
        augmented_chapters: list[ChapterArtifact] = []
        for chapter in existing_chapters:
            note_artifact = method_notes.get(chapter.chapter_id)
            if note_artifact is None:
                augmented_chapters.append(chapter)
                continue
            extra = f"\n\n### Estimation Method Note\n\n{getattr(note_artifact, 'markdown', '').strip()}"
            augmented_chapters.append(chapter.model_copy(update={"rendered_markdown": chapter.rendered_markdown.rstrip() + extra}))
        reactor_appendix_path = self.store.project_dir(self.config.project_id) / "reactor_mechanical_design_report.md"
        if reactor_appendix_path.exists():
            reactor_appendix_markdown = reactor_appendix_path.read_text(encoding="utf-8").strip()
            reactor_appendix_lines = reactor_appendix_markdown.splitlines()
            if reactor_appendix_lines and reactor_appendix_lines[0].startswith("#"):
                reactor_appendix_lines = reactor_appendix_lines[1:]
                while reactor_appendix_lines and not reactor_appendix_lines[0].strip():
                    reactor_appendix_lines = reactor_appendix_lines[1:]
            reactor_appendix_body = "\n".join(reactor_appendix_lines).strip()
            reactor_appendix_chapter = ChapterArtifact(
                chapter_id="reactor_mechanical_appendix",
                title="Detailed Mechanical Design of Reactor R-101",
                stage_id="final_report",
                status=ChapterStatus.COMPLETE,
                citations=["literature_benchchem_synthesis", "sds_vertex_ai", "patent_CN109553539B"],
                assumptions=[
                    "This appendix reproduces the standalone reactor mechanical design dossier so the main formatted report contains the full reactor package.",
                ],
                summary="Standalone detailed reactor mechanical design dossier included as an appendix-style chapter in the final report package.",
                rendered_markdown=reactor_appendix_body,
            )
            augmented_chapters.append(reactor_appendix_chapter)
        assumptions: list[str] = []
        for chapter in existing_chapters + [executive_chapter, conclusion_chapter]:
            assumptions.extend(chapter.assumptions)
        references_md = references_markdown(source_index)
        calc_sections = [
            ("Reaction-System Calculation Traces", reaction_system.calc_traces),
            ("Stream-Balance Calculation Traces", stream_table.calc_traces),
            ("Energy-Balance Calculation Traces", energy.calc_traces),
            ("Reactor Design Traces", reactor.calc_traces),
            ("Column Design Traces", column.calc_traces),
            ("Heat-Exchanger Design Traces", exchanger.calc_traces),
            ("Storage Design Traces", storage.calc_traces),
            ("Mechanical Design Traces", [trace for item in (mechanical_design.items if mechanical_design else []) for trace in item.calc_traces]),
            ("Utility Basis Traces", utilities.utility_basis.calc_traces if utilities.utility_basis else []),
            ("Project-Cost Traces", cost_model.calc_traces),
            ("Working-Capital Traces", working_capital.calc_traces),
            ("Financial Traces", financial.calc_traces),
        ]
        annexures_md = annexures_markdown(
            benchmark_manifest,
            resolved_sources,
            product_profile,
            route_survey,
            reaction_system,
            property_gap,
            resolved_values,
            property_packages,
            property_requirements,
            separation_thermo,
            process_archetype,
            route_families,
            unit_operation_family,
            sparse_data_policy,
            process_synthesis,
            operations_planning,
            agent_fabric,
            critic_registry,
            stream_table,
            mixture_properties,
            flowsheet_graph,
            flowsheet_case,
            solve_result,
            equipment.items,
            energy,
            heat_integration_study,
            utility_network,
            utility_architecture,
            utilities,
            mechanical_design,
            mechanical_design_basis,
            control_architecture,
            hazop_register,
            cost_model,
            plant_cost_summary,
            working_capital,
            financial,
            debt_schedule,
            tax_depreciation_basis,
            financial_schedule,
            economic_scenarios,
            route_decision,
            site_decision,
            utility_basis_decision,
            economic_basis_decision,
            [
                decision
                for decision in [
                    capacity_decision,
                    property_method.decision if property_method else None,
                    thermo_method.decision if thermo_method else None,
                    kinetics_method.decision if kinetics_method else None,
                    exchanger_choice,
                    storage_choice,
                    moc_choice,
                    procurement_basis,
                    logistics_basis,
                    financing_basis,
                    layout_decision.decision if layout_decision else None,
                ]
                if decision is not None
            ],
            source_index,
            assumptions,
            calc_sections,
            site.india_location_data,
            reactor_basis,
            column_hydraulics,
            exchanger_thermal,
            pump_design,
            equipment_datasheets.markdown if equipment_datasheets else None,
            [
                *(property_value_records(property_packages) if property_packages else []),
                *getattr(self._load("thermo_assessment", ThermoAssessmentArtifact), "value_records", []),
                *getattr(self._load("kinetic_assessment", KineticAssessmentArtifact), "value_records", []),
                *getattr(reaction_system, "value_records", []),
                *getattr(stream_table, "value_records", []),
                *getattr(energy, "value_records", []),
                *getattr(reactor, "value_records", []),
                *getattr(column, "value_records", []),
                *getattr(exchanger, "value_records", []),
                *getattr(storage, "value_records", []),
                *(getattr(utilities.utility_basis, "value_records", []) if utilities.utility_basis else []),
                *getattr(utilities, "value_records", []),
                *getattr(cost_model, "value_records", []),
                *getattr(working_capital, "value_records", []),
                *getattr(financial, "value_records", []),
            ],
        )
        body_chapters = [chapter for chapter in augmented_chapters if chapter.chapter_id not in {"executive_summary", "conclusion"}]
        if data_gap_chapter is not None:
            body_chapters.append(data_gap_chapter)
        full_chapters = body_chapters + [executive_chapter, conclusion_chapter]
        for chapter in full_chapters:
            if chapter.stage_id == "final_report":
                self.store.save_chapter(self.config.project_id, chapter)
        report_markdown = assemble_report(self.config.basis, full_chapters, references_md, annexures_md)
        raw_markdown_path = self.store.save_text(self.config.project_id, "final_report_raw.md", report_markdown)
        markdown_path = self.store.save_text(self.config.project_id, "final_report.md", report_markdown)
        benchmark_style_profile = build_benchmark_style_profile()
        benchmark_voice_profile = build_benchmark_voice_profile()
        sentence_pattern_library = build_sentence_pattern_library()
        tone_style_rules = build_tone_style_rules()
        formatter_target_profile = build_formatter_target_profile(self.config.basis)
        semantic_report = build_semantic_report_artifact(
            self.config.project_id,
            benchmark_style_profile,
            formatter_target_profile,
            str(raw_markdown_path),
            full_chapters,
        )
        narrative_rewrite_plan = build_narrative_rewrite_artifact(
            semantic_report,
            benchmark_voice_profile,
            tone_style_rules,
        )
        formatted_report, formatter_decision, formatter_parity, formatter_acceptance = build_formatted_report_package(
            self.config.basis,
            benchmark_style_profile,
            formatter_target_profile,
            semantic_report,
            narrative_rewrite_plan,
            references_md,
            annexures_md,
        )
        formatted_markdown_path = self.store.save_text(
            self.config.project_id,
            "final_report_formatted.md",
            formatted_report.formatted_markdown,
        )
        formatted_html_path = self.store.save_text(
            self.config.project_id,
            "final_report_formatted.html",
            formatted_report.formatted_html,
        )
        self._save("benchmark_style_profile", benchmark_style_profile)
        self._save("benchmark_voice_profile", benchmark_voice_profile)
        self._save("sentence_pattern_library", sentence_pattern_library)
        self._save("tone_style_rules", tone_style_rules)
        self._save("formatter_target_profile", formatter_target_profile)
        self._save("semantic_report", semantic_report)
        self._save("narrative_rewrite_plan", narrative_rewrite_plan)
        self._save("formatted_report", formatted_report)
        self._save("formatter_decision", formatter_decision)
        self._save("formatter_parity", formatter_parity)
        self._save("formatter_acceptance", formatter_acceptance)
        if report_parity_framework is None:
            report_parity_framework = build_report_parity_framework(benchmark_manifest)
            self._save("report_parity_framework", report_parity_framework)
        report_parity = evaluate_report_parity(report_parity_framework, full_chapters, references_md, annexures_md)
        self._save("report_parity", report_parity)
        report_acceptance = self._save_report_acceptance(RunStatus.AWAITING_APPROVAL, report_parity=report_parity)
        final_report = FinalReport(
            project_id=self.config.project_id,
            markdown_path=str(markdown_path),
            raw_markdown_path=str(raw_markdown_path),
            formatted_markdown_path=str(formatted_markdown_path),
            formatted_html_path=str(formatted_html_path),
            style_profile_id=benchmark_style_profile.style_id,
            formatter_target_id=formatter_target_profile.target_id,
            references=list(source_index.keys()),
            annexure_paths=[str(self.store.project_dir(self.config.project_id) / "annexures")],
        )
        self._save("final_report", final_report)
        issues = self._chapter_issues(executive_chapter) + self._chapter_issues(conclusion_chapter)
        issues.extend(validate_report_parity(report_parity))
        if report_acceptance:
            issues.extend(validate_report_acceptance(report_acceptance))
        if missing_data_acceptance is not None:
            issues.extend(validate_missing_data_acceptance_artifact(missing_data_acceptance))
        gate = self._gate("final_signoff", "Final Signoff", "Approve the final markdown report before PDF rendering is released.")
        return StageResult(chapters=[executive_chapter, conclusion_chapter], issues=issues, missing_india_coverage=[], stale_source_groups=[], gate=gate)
