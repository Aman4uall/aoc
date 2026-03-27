from __future__ import annotations

from dataclasses import dataclass, field
import json
import math

from aoc.archetypes import build_alternative_sets, classify_process_archetype
from aoc.agent_fabric import build_agent_decision_fabric
from aoc.benchmarks import build_benchmark_manifest
from aoc.calculators import (
    annual_output_kg,
    build_column_design,
    build_cost_model,
    build_energy_balance,
    build_equipment_list,
    build_financial_model,
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
    build_economic_basis_decision,
    build_heat_integration_study,
    build_process_synthesis,
    build_rough_alternatives,
    build_site_selection_decision,
    build_utility_basis_decision,
    resolve_property_gaps,
    select_route_architecture,
    selected_heat_case,
)
from aoc.economics_v2 import (
    build_debt_schedule,
    build_economic_scenario_model_v2,
    build_financing_basis_decision,
    build_financial_schedule,
    build_logistics_basis_decision,
    build_plant_cost_summary,
    build_procurement_basis_decision,
    build_tax_depreciation_basis,
)
from aoc.evidence import build_resolved_source_set, build_resolved_value_artifact, extend_resolved_value_artifact
from aoc.flowsheet import (
    build_control_architecture_decision,
    build_control_plan_from_flowsheet,
    build_flowsheet_graph,
    build_hazop_node_register,
    build_layout_decision,
)
from aoc.methods import build_capacity_decision, build_kinetics_method_decision, build_thermo_method_decision
from aoc.mechanical import build_mechanical_design_artifact, build_mechanical_design_basis, build_vessel_mechanical_designs
from aoc.models import (
    AgentDecisionFabricArtifact,
    BenchmarkManifest,
    ChapterArtifact,
    ChapterStatus,
    ColumnDesign,
    ColumnHydraulics,
    ControlArchitectureDecision,
    ControlPlanArtifact,
    CostModel,
    DebtSchedule,
    DecisionRecord,
    EquipmentDatasheet,
    EconomicScenarioModel,
    EnergyBalance,
    EquipmentListArtifact,
    FinalReport,
    FinancialModel,
    FinancialSchedule,
    FlowsheetGraph,
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
    LayoutDecisionArtifact,
    MarketAssessmentArtifact,
    MechanicalDesignArtifact,
    MechanicalDesignBasis,
    MethodSelectionArtifact,
    NarrativeArtifact,
    PlantCostSummary,
    PumpDesign,
    ProcessArchetype,
    ProcessSynthesisArtifact,
    ProcessNarrativeArtifact,
    PropertyGapArtifact,
    ProductProfileArtifact,
    ProvenanceTag,
    ProjectConfig,
    ProjectRunState,
    ReactionSystem,
    ReactorDesign,
    ReactorDesignBasis,
    ResearchBundle,
    ResolvedSourceSet,
    ResolvedValueArtifact,
    RoughAlternativeSummaryArtifact,
    RouteOption,
    RouteSelectionArtifact,
    RouteSurveyArtifact,
    RunStatus,
    SolveResult,
    SensitivityLevel,
    Severity,
    SiteSelectionArtifact,
    StorageDesign,
    StreamTable,
    TaxDepreciationBasis,
    ThermoAssessmentArtifact,
    UtilityArchitectureDecision,
    UtilitySummaryArtifact,
    UtilityNetworkDecision,
    ValidationIssue,
    VesselMechanicalDesign,
    WorkingCapitalModel,
    utc_now,
)
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
from aoc.publish import annexures_markdown, assemble_report, markdown_table, references_markdown, render_pdf
from aoc.reasoning import build_reasoning_service
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
from aoc.solver_architecture import build_flowsheet_case, build_solve_result
from aoc.store import ArtifactStore
from aoc.utility_architecture import build_utility_architecture_decision
from aoc.validators import (
    apply_state_issues,
    validate_chapter,
    validate_column_design,
    validate_cost_model,
    validate_cross_chapter_consistency,
    validate_decision_record,
    validate_energy_balance,
    validate_equipment_applicability,
    validate_financial_model,
    validate_flowsheet_case,
    validate_flowsheet_graph,
    validate_control_architecture,
    validate_hazop_node_register,
    validate_heat_integration_study,
    validate_india_location_data,
    validate_india_price_data,
    validate_kinetic_assessment,
    validate_phase_feasibility,
    validate_property_method_decision,
    validate_property_package_artifact,
    validate_process_archetype,
    validate_property_gap_artifact,
    validate_property_requirement_set,
    validate_property_requirements_for_stage,
    validate_property_records,
    validate_resolved_source_set,
    validate_resolved_value_artifact,
    validate_separation_thermo_artifact,
    validate_mixture_property_artifact,
    validate_site_selection_consistency,
    validate_solve_result,
    validate_reactor_design,
    validate_research_bundle,
    validate_route_balance,
    validate_stream_table,
    validate_thermo_assessment,
    validate_utility_architecture,
    validate_utility_network_decision,
    validate_value_records,
    validate_working_capital,
)
from aoc.value_engine import make_value_record


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
    StageSpec("project_intake", "Project intake and basis lock", (), ("project_basis", "research_bundle", "benchmark_manifest", "resolved_sources")),
    StageSpec("product_profile", "Introduction and product profile", ("research_bundle",), ("product_profile",)),
    StageSpec("market_capacity", "Market and capacity selection", ("research_bundle",), ("market_assessment", "capacity_decision")),
    StageSpec("literature_route_survey", "Literature survey", ("research_bundle",), ("route_survey",)),
    StageSpec("property_gap_resolution", "Property gap resolution", ("product_profile", "resolved_sources", "route_survey", "research_bundle"), ("property_gap", "resolved_values", "property_packages", "property_requirements", "agent_decision_fabric"), "evidence_lock", "Evidence Lock", "Approve the resolved source and value basis before process synthesis proceeds."),
    StageSpec("site_selection", "Site selection", ("research_bundle",), ("site_selection", "site_selection_decision")),
    StageSpec("process_synthesis", "Process synthesis", ("route_survey", "property_gap"), ("process_synthesis",)),
    StageSpec("rough_alternative_balances", "Rough alternative balances", ("process_synthesis", "market_assessment"), ("rough_alternatives",)),
    StageSpec("heat_integration_optimization", "Heat integration optimization", ("rough_alternatives", "market_assessment"), ("heat_integration_study",), "heat_integration", "Heat Integration Review", "Approve the selected heat-integration studies before route finalization."),
    StageSpec("route_selection", "Process selection", ("route_survey", "rough_alternatives", "heat_integration_study", "market_assessment"), ("route_selection", "route_decision", "reactor_choice_decision", "separation_choice_decision", "utility_network_decision"), "process_architecture", "Process Architecture", "Approve the selected route, reactor, separation train, and utility-integration basis before downstream design work continues."),
    StageSpec("thermodynamic_feasibility", "Thermodynamics", ("route_selection", "route_survey", "research_bundle", "property_packages", "property_requirements"), ("thermo_assessment", "thermo_method_decision", "property_method_decision", "separation_thermo")),
    StageSpec("kinetic_feasibility", "Kinetics", ("route_selection", "route_survey", "research_bundle"), ("kinetic_assessment", "kinetics_method_decision")),
    StageSpec("block_diagram", "Block diagram", ("route_selection", "route_survey", "research_bundle"), ("process_narrative",)),
    StageSpec("process_description", "Process description", ("process_narrative",), ("process_narrative",)),
    StageSpec("material_balance", "Material balance", ("route_selection", "kinetic_assessment", "process_narrative"), ("reaction_system", "stream_table", "flowsheet_graph", "flowsheet_case")),
    StageSpec("energy_balance", "Energy balance", ("stream_table", "thermo_assessment", "property_packages", "property_requirements"), ("energy_balance", "solve_result", "mixture_properties"), "design_basis", "Design Basis Lock", "Approve thermo, kinetics, process narrative, and balance basis before detailed design."),
    StageSpec("reactor_design", "Reactor design", ("reaction_system", "stream_table", "energy_balance", "mixture_properties", "property_packages", "property_requirements"), ("reactor_design", "reactor_design_basis")),
    StageSpec("distillation_design", "Distillation/process-unit design", ("stream_table", "energy_balance", "mixture_properties", "property_packages", "property_requirements", "separation_thermo"), ("column_design", "column_hydraulics", "heat_exchanger_design", "heat_exchanger_thermal_design", "exchanger_choice_decision")),
    StageSpec("equipment_sizing", "Equipment sizing", ("reactor_design", "column_design", "heat_exchanger_design"), ("storage_design", "pump_design", "equipment_list", "equipment_datasheets", "storage_choice_decision", "moc_choice_decision"), "equipment_basis", "Reactor/Column Design Basis", "Approve reactor, column, exchanger, and storage design basis before downstream detailing."),
    StageSpec("mechanical_design_moc", "Mechanical design and materials of construction", ("equipment_list", "route_selection"), ("mechanical_design", "mechanical_design_basis", "vessel_mechanical_designs")),
    StageSpec("storage_utilities", "Storage and utilities", ("storage_design", "equipment_list", "energy_balance"), ("utility_summary", "utility_basis_decision", "utility_architecture")),
    StageSpec("instrumentation_control", "Instrumentation and process control", ("equipment_list", "utility_summary", "flowsheet_graph"), ("control_plan", "control_architecture")),
    StageSpec("hazop_she", "HAZOP and SHE", ("equipment_list", "route_selection", "flowsheet_graph", "control_plan"), ("hazop_study", "hazop_node_register", "safety_environment"), "hazop", "HAZOP Gate", "Approve critical HAZOP nodes and SHE safeguards before layout and economics are released."),
    StageSpec("layout_waste", "Project and plant layout", ("equipment_list", "utility_summary", "site_selection"), ("layout_plan", "layout_decision")),
    StageSpec("project_cost", "Project cost", ("equipment_list", "utility_summary", "stream_table", "market_assessment", "site_selection"), ("cost_model", "plant_cost_summary", "procurement_basis_decision", "logistics_basis_decision")),
    StageSpec("cost_of_production", "Cost of production", ("cost_model",), ("cost_model",)),
    StageSpec("working_capital", "Working capital", ("cost_model", "market_assessment"), ("working_capital_model",)),
    StageSpec("financial_analysis", "Financial analysis", ("cost_model", "working_capital_model", "market_assessment"), ("financial_model", "economic_basis_decision", "financing_basis_decision", "economic_scenarios", "debt_schedule", "tax_depreciation_basis", "financial_schedule"), "india_cost_basis", "India Cost Basis", "Approve India site and economics basis before final assembly."),
    StageSpec("final_report", "Final report assembly", ("product_profile", "financial_model"), ("final_report",), "final_signoff", "Final Signoff", "Approve the final markdown report before PDF rendering is released."),
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
        markdown_path = self.store.project_dir(self.config.project_id) / "final_report.md"
        if not markdown_path.exists():
            raise RuntimeError("Final markdown report does not exist yet.")
        pdf_path = self.store.project_dir(self.config.project_id) / "final_report.pdf"
        render_pdf(markdown_path.read_text(encoding="utf-8"), str(pdf_path), f"{self.config.basis.target_product} Plant Design Report")
        final_report = self.store.maybe_load_model(self.config.project_id, "artifacts/final_report.json", FinalReport)
        if final_report:
            final_report.pdf_path = str(pdf_path)
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
        resolved_sources = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_sources.json", ResolvedSourceSet)
        property_gap = self.store.maybe_load_model(self.config.project_id, "artifacts/property_gap.json", PropertyGapArtifact)
        resolved_values = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_values.json", ResolvedValueArtifact)
        property_packages = self.store.maybe_load_model(self.config.project_id, "artifacts/property_packages.json", PropertyPackageArtifact)
        property_requirements = self.store.maybe_load_model(self.config.project_id, "artifacts/property_requirements.json", PropertyRequirementSet)
        separation_thermo = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_thermo.json", SeparationThermoArtifact)
        agent_fabric = self.store.maybe_load_model(self.config.project_id, "artifacts/agent_decision_fabric.json", AgentDecisionFabricArtifact)
        process_archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        process_synthesis = self.store.maybe_load_model(self.config.project_id, "artifacts/process_synthesis.json", ProcessSynthesisArtifact)
        capacity_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/capacity_decision.json", DecisionRecord)
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
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
        reaction_system = self.store.maybe_load_model(self.config.project_id, "artifacts/reaction_system.json", ReactionSystem)
        stream_table = self.store.maybe_load_model(self.config.project_id, "artifacts/stream_table.json", StreamTable)
        mixture_properties = self.store.maybe_load_model(self.config.project_id, "artifacts/mixture_properties.json", MixturePropertyArtifact)
        flowsheet_case = self.store.maybe_load_model(self.config.project_id, "artifacts/flowsheet_case.json", FlowsheetCase)
        solve_result = self.store.maybe_load_model(self.config.project_id, "artifacts/solve_result.json", SolveResult)
        utility_architecture = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_architecture.json", UtilityArchitectureDecision)
        plant_cost_summary = self.store.maybe_load_model(self.config.project_id, "artifacts/plant_cost_summary.json", PlantCostSummary)
        debt_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/debt_schedule.json", DebtSchedule)
        financial_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/financial_schedule.json", FinancialSchedule)
        if benchmark_manifest:
            lines.append("")
            lines.append("benchmark:")
            lines.append(f"- profile: {benchmark_manifest.benchmark_id}")
            lines.append(f"- archetype_family: {benchmark_manifest.archetype_family}")
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
        if property_requirements:
            lines.append(f"- property_requirement_stage_failures: {', '.join(property_requirements.blocked_stage_ids) or 'none'}")
        if process_archetype:
            lines.append("")
            lines.append("archetype:")
            lines.append(f"- id: {process_archetype.archetype_id}")
            lines.append(f"- compound_family: {process_archetype.compound_family}")
            lines.append(f"- product_phase: {process_archetype.dominant_product_phase}")
            lines.append(f"- separation_family: {process_archetype.dominant_separation_family}")
        if any([capacity_decision, site_decision, route_decision, reactor_choice, separation_choice, exchanger_choice, storage_choice, moc_choice, utility_basis_decision, procurement_basis, logistics_basis, financing_basis, economic_basis_decision]):
            lines.append("")
            lines.append("decisions:")
            for decision in [capacity_decision, site_decision, route_decision, reactor_choice, separation_choice, exchanger_choice, storage_choice, moc_choice, utility_basis_decision, procurement_basis, logistics_basis, financing_basis, economic_basis_decision]:
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
        if agent_fabric:
            lines.append("")
            lines.append("agent_fabric:")
            lines.append(f"- packets: {len(agent_fabric.packets)}")
            warning_packets = sum(1 for packet in agent_fabric.packets for verdict in packet.critic_verdicts if verdict.status == "warning")
            blocked_packets = sum(1 for packet in agent_fabric.packets for verdict in packet.critic_verdicts if verdict.status == "blocked")
            lines.append(f"- critic_warnings: {warning_packets}")
            lines.append(f"- critic_blocked: {blocked_packets}")
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
                    f"- units: {len(flowsheet_case.units)}; streams: {len(flowsheet_case.streams)}; separations: {len(flowsheet_case.separations)}; recycle_loops: {len(flowsheet_case.recycle_loops)}"
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
            if debt_schedule:
                lines.append(f"- debt_schedule_years: {len(debt_schedule.entries)}")
            if financial_schedule:
                lines.append(f"- financial_schedule_years: {len(financial_schedule.lines)}")
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

    def _refresh_agent_fabric(self) -> None:
        resolved_sources = self._maybe_load("resolved_sources", ResolvedSourceSet)
        resolved_values = self._maybe_load("resolved_values", ResolvedValueArtifact)
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
        if not any([resolved_sources, resolved_values, decisions]):
            return
        artifact = build_agent_decision_fabric(resolved_sources, resolved_values, decisions)
        self._save("agent_decision_fabric", artifact)

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

    def _existing_chapters(self, state: ProjectRunState) -> list[ChapterArtifact]:
        return [self.store.load_chapter(self.config.project_id, chapter_id) for chapter_id in state.chapter_index]

    def _gate(self, gate_id: str, title: str, description: str) -> GateDecision:
        return GateDecision(gate_id=gate_id, title=title, description=description)

    def _chapter_issues(self, chapter: ChapterArtifact) -> list[ValidationIssue]:
        return validate_chapter(chapter, self._source_ids(), self.config.strict_citation_policy)

    def _run_project_intake(self) -> StageResult:
        bundle = self.research_manager.build_bundle(self.config)
        benchmark_manifest = build_benchmark_manifest(self.config)
        resolved_sources = build_resolved_source_set(self.config, bundle)
        self._save("project_basis", self.config.basis)
        self._save("research_bundle", bundle)
        self._save("benchmark_manifest", benchmark_manifest)
        self._save("resolved_sources", resolved_sources)
        issues, missing_groups, stale_groups = validate_research_bundle(bundle, self.config)
        issues.extend(validate_resolved_source_set(resolved_sources, {source.source_id for source in bundle.sources}, self.config))
        return StageResult(issues=issues, missing_india_coverage=missing_groups, stale_source_groups=stale_groups)

    def _run_product_profile(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        artifact = self.reasoning.build_product_profile(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        self._save("product_profile", artifact)
        issues = validate_property_records(artifact.properties, self._source_ids(), self.config.strict_citation_policy)
        chapter = self._chapter(
            "introduction_product_profile",
            "Introduction and Product Profile",
            "product_profile",
            artifact.markdown,
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
        artifact = self.reasoning.build_market_assessment(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        default_price_source = next((source_id for source_id in bundle.india_source_ids if source_id.startswith("india_sheet_")), None)
        if default_price_source:
            for datum in artifact.india_price_data:
                if not datum.citations:
                    datum.citations = [default_price_source]
        capacity_decision = build_capacity_decision(self.config, artifact)
        self._save("market_assessment", artifact)
        self._save("capacity_decision", capacity_decision)
        self._refresh_agent_fabric()
        issues = validate_india_price_data(artifact.india_price_data, self._source_ids(), self.config, "market_assessment")
        chapter = self._chapter(
            "market_capacity_selection",
            "Market and Capacity Selection",
            "market_capacity",
            artifact.markdown + f"\n\n### Capacity Decision\n\n{capacity_decision.selected_summary}",
            sorted(set(artifact.citations + capacity_decision.citations)),
            artifact.assumptions + capacity_decision.assumptions,
            ["market_assessment", "capacity_decision"],
            required_inputs=["research_bundle"],
            summary=artifact.capacity_rationale,
        )
        issues.extend(validate_decision_record(capacity_decision, "capacity_decision"))
        issues.extend(self._chapter_issues(chapter))
        return StageResult(chapters=[chapter], issues=issues)

    def _run_literature_route_survey(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        artifact = self.reasoning.survey_routes(self.config.basis, bundle.sources, bundle.corpus_excerpt)
        artifact = self._normalize_route_survey(artifact)
        self._save("route_survey", artifact)
        chapter = self._chapter(
            "literature_survey",
            "Literature Survey",
            "literature_route_survey",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["route_survey"],
            required_inputs=["research_bundle"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_property_gap_resolution(self) -> StageResult:
        product_profile = self._load("product_profile", ProductProfileArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        bundle = self._load("research_bundle", ResearchBundle)
        route_survey = self._load("route_survey", RouteSurveyArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        artifact = resolve_property_gaps(product_profile, self.config)
        property_packages = build_property_package_artifact(self.config, bundle, product_profile, route_survey)
        property_requirements = build_property_requirement_artifact(self.config, property_packages)
        resolved_values = build_resolved_value_artifact(artifact, resolved_sources, self.config)
        resolved_values = extend_resolved_value_artifact(
            resolved_values,
            property_value_records(property_packages),
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
        self._refresh_agent_fabric()
        issues = validate_property_gap_artifact(artifact, self.config)
        issues.extend(validate_resolved_value_artifact(resolved_values, self._source_ids(), self.config))
        issues.extend(validate_property_package_artifact(property_packages, self._source_ids(), self.config))
        issues.extend(validate_property_requirement_set(property_requirements))
        gate = None
        if self.config.evidence_lock_required and not issues:
            gate = self._gate("evidence_lock", "Evidence Lock", "Approve the resolved source and value basis before process synthesis proceeds.")
        return StageResult(issues=issues, gate=gate)

    def _run_process_synthesis(self) -> StageResult:
        survey = self._load("route_survey", RouteSurveyArtifact)
        property_gap = self._load("property_gap", PropertyGapArtifact)
        archetype = classify_process_archetype(self.config, survey, property_gap)
        alternative_sets = build_alternative_sets(self.config, archetype, survey)
        artifact = build_process_synthesis(self.config, survey, property_gap)
        artifact.archetype = archetype
        artifact.alternative_sets = alternative_sets
        self._save("process_synthesis", artifact)
        self._save("process_archetype", archetype)
        self.config.basis.operating_mode = artifact.operating_mode_decision.selected_candidate_id or self.config.basis.operating_mode
        self.store.save_config(self.config)
        issues = validate_decision_record(artifact.operating_mode_decision, "operating_mode")
        issues.extend(validate_process_archetype(archetype))
        return StageResult(issues=issues)

    def _run_rough_alternative_balances(self) -> StageResult:
        survey = self._load("route_survey", RouteSurveyArtifact)
        synthesis = self._load("process_synthesis", ProcessSynthesisArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        artifact = build_rough_alternatives(self.config, survey, synthesis, market)
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
        rough_alternatives = self._load("rough_alternatives", RoughAlternativeSummaryArtifact)
        heat_study = self._load("heat_integration_study", HeatIntegrationStudyArtifact)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        selection, route_decision, reactor_choice, separation_choice, utility_network = select_route_architecture(
            self.config,
            survey,
            rough_alternatives,
            heat_study,
            market,
        )
        self._save("route_selection", selection)
        selected_route = self._selected_route()
        reactor_choice = select_reactor_configuration(selected_route, archetype)
        separation_choice = select_separation_configuration(selected_route, archetype)
        self._save("route_decision", route_decision)
        self._save("reactor_choice_decision", reactor_choice)
        self._save("separation_choice_decision", separation_choice)
        self._save("utility_network_decision", utility_network)
        self._refresh_agent_fabric()
        issues = (
            validate_route_balance(selected_route)
            + validate_decision_record(route_decision, "route_decision")
            + validate_decision_record(reactor_choice, "reactor_choice")
            + validate_decision_record(separation_choice, "separation_choice")
            + validate_utility_network_decision(utility_network, self.config)
        )
        selected_heat = selected_heat_case(utility_network)
        chapter = self._chapter(
            "process_selection",
            "Process Selection",
            "route_selection",
            (
                f"### Route Comparison\n\n{selection.comparison_markdown}\n\n"
                f"### Selected Route\n\n{selection.justification}\n\n"
                f"### Selected Reactor Basis\n\n{reactor_choice.selected_summary}\n\n"
                f"### Selected Separation Basis\n\n{separation_choice.selected_summary}\n\n"
                f"### Selected Heat-Integration Case\n\n"
                f"{selected_heat.title if selected_heat else 'No selected case'}: {selected_heat.summary if selected_heat else 'n/a'}"
            ),
            sorted(set(selection.citations + survey.citations)),
            survey.assumptions + selection.assumptions + route_decision.assumptions + reactor_choice.assumptions + separation_choice.assumptions,
            ["route_selection", "route_decision", "reactor_choice_decision", "separation_choice_decision", "utility_network_decision"],
            required_inputs=["route_survey", "rough_alternatives", "heat_integration_study", "market_assessment"],
        )
        issues.extend(self._chapter_issues(chapter))
        gate = self._gate("process_architecture", "Process Architecture", "Approve the selected route, reactor, separation train, and utility-integration basis.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_site_selection(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        artifact = self.reasoning.select_site(self.config.basis, bundle.sources, bundle.corpus_excerpt)
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
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        separation_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_choice_decision.json", DecisionRecord)
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
        self._save("thermo_assessment", artifact)
        self._save("thermo_method_decision", method_artifact)
        self._save("property_method_decision", property_method)
        self._save("separation_thermo", separation_thermo)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(resolved_values, artifact.value_records, resolved_sources, self.config, "thermodynamic_feasibility"),
        )
        self._refresh_agent_fabric()
        chapter = self._chapter(
            "thermodynamic_feasibility",
            "Thermodynamic Feasibility",
            "thermodynamic_feasibility",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["thermo_assessment", "thermo_method_decision"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
            summary=artifact.equilibrium_comment,
        )
        issues = (
            validate_route_balance(route)
            + validate_property_method_decision(property_method)
            + validate_separation_thermo_artifact(separation_thermo)
            + validate_decision_record(method_artifact.decision, "thermo_method_decision")
            + validate_property_requirements_for_stage(
                "thermodynamic_feasibility",
                property_requirements,
                property_packages,
                route,
                self.config.basis.target_product,
            )
            + validate_thermo_assessment(artifact)
            + self._value_issues(artifact, "thermo_assessment")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_kinetic_feasibility(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        route = self._selected_route()
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
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
        self._save("kinetic_assessment", artifact)
        self._save("kinetics_method_decision", method_artifact)
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
            validate_decision_record(method_artifact.decision, "kinetics_method_decision")
            + validate_kinetic_assessment(artifact)
            + self._value_issues(artifact, "kinetic_assessment")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _ensure_process_narrative(self) -> ProcessNarrativeArtifact:
        artifact = self.store.maybe_load_model(self.config.project_id, "artifacts/process_narrative.json", ProcessNarrativeArtifact)
        if artifact:
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
        unit_narrative = [
            f"- `{unit.unit_id}`: {unit.service}. Inlet streams `{', '.join(unit.upstream_stream_ids) or '-'}` and outlet streams `{', '.join(unit.downstream_stream_ids) or '-'}` with `{unit.closure_status}` closure and `{unit.coverage_status}` coverage."
            for unit in flowsheet_case.units
        ]
        lines = [
            f"Solver-derived process description for route `{route.route_id}` built from `{len(stream_table.unit_operation_packets)}` solved unit packets.",
            "",
            "### Unit Sequence",
            "",
            markdown_table(["Unit", "Type", "Service", "Inlet Streams", "Outlet Streams", "Closure", "Coverage"], unit_rows or [["n/a", "n/a", "n/a", "-", "-", "n/a", "n/a"]]),
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
        reaction_system: ReactionSystem,
        stream_table: StreamTable,
    ) -> str:
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
                "### Reaction Extent Allocation\n\n"
                + markdown_table(["Extent", "Kind", "Representative Component", "Fraction of Converted Feed", "Status"], reaction_rows or [["n/a", "n/a", "n/a", "0.0", "n/a"]]),
                "### Byproduct Closure\n\n"
                + markdown_table(["Component", "Basis", "Allocation Fraction", "Provenance", "Status"], byproduct_rows or [["n/a", "n/a", "0.0", "n/a", "n/a"]]),
                "### Unit Packet Balance Summary\n\n"
                + markdown_table(
                    ["Unit", "Type", "Service", "Inlet Streams", "Outlet Streams", "Inlet kg/h", "Outlet kg/h", "Closure Error (%)", "Status", "Coverage"],
                    packet_rows or [["n/a", "n/a", "n/a", "-", "-", "0.0", "0.0", "0.0", "n/a", "n/a"]],
                ),
                "### Stream Table\n\n"
                + markdown_table(["Stream", "Description", "From", "To", "Component", "kg/h", "kmol/h", "T (C)", "P (bar)"], stream_rows),
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

    def _render_reactor_design_chapter(
        self,
        reactor: ReactorDesign,
        reactor_basis: ReactorDesignBasis,
        stream_table: StreamTable,
        energy: EnergyBalance,
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
            ["Residence time (h)", f"{reactor.residence_time_hr:.3f}"],
            ["Design volume (m3)", f"{reactor.design_volume_m3:.3f}"],
            ["Design temperature (C)", f"{reactor.design_temperature_c:.1f}"],
            ["Design pressure (bar)", f"{reactor.design_pressure_bar:.2f}"],
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
            ["Heat-transfer area (m2)", f"{reactor.heat_transfer_area_m2:.3f}"],
            ["Overall U (W/m2-K)", f"{reactor.overall_u_w_m2_k:.1f}"],
            ["Reynolds number", f"{reactor.reynolds_number:,.1f}"],
            ["Prandtl number", f"{reactor.prandtl_number:.3f}"],
            ["Nusselt number", f"{reactor.nusselt_number:.2f}"],
            ["Tube count", str(reactor.number_of_tubes)],
            ["Tube length (m)", f"{reactor.tube_length_m:.3f}"],
        ]
        utility_rows = [
            ["Utility topology", reactor.utility_topology or "standalone utilities"],
            ["Cooling medium", reactor.cooling_medium],
            ["Integrated duty (kW)", f"{reactor.integrated_thermal_duty_kw:.3f}"],
            ["Residual utility duty (kW)", f"{reactor.residual_utility_duty_kw:.3f}"],
            ["Integrated LMTD (K)", f"{reactor.integrated_lmtd_k:.3f}"],
            ["Integrated exchange area (m2)", f"{reactor.integrated_exchange_area_m2:.3f}"],
            ["Coupled service basis", reactor.coupled_service_basis or "none"],
            ["Selected train steps", ", ".join(reactor.selected_train_step_ids) or "none"],
        ]
        return "\n\n".join(
            [
                reactor_basis.markdown,
                "### Governing Equations\n\n" + "\n".join(f"- `{equation}`" for equation in reactor_basis.governing_equations),
                "### Solver Packet Basis\n\n"
                + markdown_table(
                    ["Packet", "Primary Value 1", "Primary Value 2", "Closure / Recoverable", "Status / Media"],
                    packet_rows,
                ),
                "### Reactor Sizing Basis\n\n" + markdown_table(["Parameter", "Value"], basis_rows),
                "### Heat-Transfer Derivation Basis\n\n" + markdown_table(["Parameter", "Value"], heat_transfer_rows),
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
    ) -> str:
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
            ["Integrated reboiler duty (kW)", f"{column.integrated_reboiler_duty_kw:.3f}"],
            ["Residual reboiler utility (kW)", f"{column.residual_reboiler_utility_kw:.3f}"],
            ["Integrated reboiler LMTD (K)", f"{column.integrated_reboiler_lmtd_k:.3f}"],
            ["Integrated reboiler area (m2)", f"{column.integrated_reboiler_area_m2:.3f}"],
            ["Reboiler medium", column.reboiler_medium or "none"],
            ["Reboiler package type", column.reboiler_package_type or "none"],
            ["Reboiler circulation ratio", f"{column.reboiler_circulation_ratio:.3f}"],
            ["Reboiler phase-change load (kg/h)", f"{column.reboiler_phase_change_load_kg_hr:.3f}"],
            ["Reboiler package items", ", ".join(column.reboiler_package_item_ids) or "none"],
            ["Condenser recovery duty (kW)", f"{column.condenser_recovery_duty_kw:.3f}"],
            ["Condenser recovery LMTD (K)", f"{column.condenser_recovery_lmtd_k:.3f}"],
            ["Condenser recovery area (m2)", f"{column.condenser_recovery_area_m2:.3f}"],
            ["Condenser recovery medium", column.condenser_recovery_medium or "none"],
            ["Condenser package type", column.condenser_package_type or "none"],
            ["Condenser phase-change load (kg/h)", f"{column.condenser_phase_change_load_kg_hr:.3f}"],
            ["Condenser circulation flow (m3/h)", f"{column.condenser_circulation_flow_m3_hr:.3f}"],
            ["Condenser package items", ", ".join(column.condenser_package_item_ids) or "none"],
            ["Selected train steps", ", ".join(column.selected_train_step_ids) or "none"],
        ]
        exchanger_rows = [
            ["Configuration", exchanger_thermal.selected_configuration],
            ["Heat load (kW)", f"{exchanger.heat_load_kw:.3f}"],
            ["LMTD (K)", f"{exchanger.lmtd_k:.1f}"],
            ["Overall U (W/m2-K)", f"{exchanger.overall_u_w_m2_k:.1f}"],
            ["Area (m2)", f"{exchanger.area_m2:.3f}"],
            ["Package family", exchanger.package_family or "generic"],
            ["Selected train step", exchanger.selected_train_step_id or "none"],
            ["Package roles", ", ".join(exchanger.selected_package_roles) or "none"],
            ["Selected package items", ", ".join(exchanger.selected_package_item_ids) or "none"],
            ["Boiling-side coefficient (W/m2-K)", f"{exchanger.boiling_side_coefficient_w_m2_k:.3f}"],
            ["Condensing-side coefficient (W/m2-K)", f"{exchanger.condensing_side_coefficient_w_m2_k:.3f}"],
        ]
        return "\n\n".join(
            [
                column_hydraulics.markdown,
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
                "### Process-Unit Sizing Basis\n\n" + markdown_table(["Parameter", "Value"], column_rows),
                "### Hydraulics Basis\n\n" + markdown_table(["Parameter", "Value"], hydraulics_rows),
                "### Utility Coupling\n\n" + markdown_table(["Parameter", "Value"], utility_rows),
                "### Heat-Exchanger Thermal Basis\n\n" + markdown_table(["Parameter", "Value"], exchanger_rows),
                self._render_trace_section("Process-Unit Calculation Traces", column.calc_traces + exchanger.calc_traces),
            ]
        )

    def _run_block_diagram(self) -> StageResult:
        artifact = self._ensure_process_narrative()
        markdown = f"```mermaid\n{artifact.bfd_mermaid}\n```"
        chapter = self._chapter(
            "block_flow_diagram",
            "Block Flow Diagram",
            "block_diagram",
            markdown,
            artifact.citations,
            artifact.assumptions,
            ["process_narrative"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_process_description(self) -> StageResult:
        artifact = self._ensure_process_narrative()
        chapter = self._chapter(
            "process_description",
            "Process Description",
            "process_description",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["process_narrative"],
            required_inputs=["process_narrative"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_material_balance(self) -> StageResult:
        route = self._selected_route()
        kinetics = self._load("kinetic_assessment", KineticAssessmentArtifact)
        process_narrative = self._ensure_process_narrative()
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        reaction_system = build_reaction_system(self.config.basis, route, kinetics, route.citations + kinetics.citations, route.assumptions + kinetics.assumptions)
        stream_table = build_stream_table(
            self.config.basis,
            route,
            reaction_system,
            reaction_system.citations,
            reaction_system.assumptions,
            property_packages,
        )
        flowsheet_graph = build_flowsheet_graph(
            route,
            stream_table,
            reaction_system,
            process_narrative,
            self.config.basis.operating_mode,
        )
        flowsheet_case = build_flowsheet_case(route.route_id, self.config.basis.operating_mode, stream_table, flowsheet_graph)
        self._save("reaction_system", reaction_system)
        self._save("stream_table", stream_table)
        self._save("flowsheet_graph", flowsheet_graph)
        self._save("flowsheet_case", flowsheet_case)
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        resolved_values = extend_resolved_value_artifact(resolved_values, reaction_system.value_records, resolved_sources, self.config, "material_balance_reaction_system")
        resolved_values = extend_resolved_value_artifact(resolved_values, stream_table.value_records, resolved_sources, self.config, "material_balance_stream_table")
        self._save("resolved_values", resolved_values)
        material_markdown = self._render_solver_material_balance(reaction_system, stream_table)
        chapter = self._chapter(
            "material_balance",
            "Material Balance",
            "material_balance",
            material_markdown,
            sorted(set(stream_table.citations + reaction_system.citations)),
            reaction_system.assumptions + stream_table.assumptions,
            ["reaction_system", "stream_table", "flowsheet_graph", "flowsheet_case"],
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
        issues = (
            validate_reaction_system(reaction_system)
            + validate_stream_table(stream_table)
            + validate_flowsheet_graph(flowsheet_graph)
            + validate_flowsheet_case(flowsheet_case)
            + self._value_issues(reaction_system, "reaction_system")
            + self._value_issues(stream_table, "stream_table")
            + self._chapter_issues(chapter)
            + self._chapter_issues(process_description_chapter)
        )
        return StageResult(chapters=[process_description_chapter, chapter], issues=issues)

    def _run_energy_balance(self) -> StageResult:
        route = self._selected_route()
        stream_table = self._load("stream_table", StreamTable)
        thermo = self._load("thermo_assessment", ThermoAssessmentArtifact)
        kinetics = self._load("kinetic_assessment", KineticAssessmentArtifact)
        reaction_system = self._load("reaction_system", ReactionSystem)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
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
        duty_rows = [[duty.unit_id, f"{duty.heating_kw:.3f}", f"{duty.cooling_kw:.3f}", duty.notes] for duty in energy.duties]
        markdown = markdown_table(["Unit", "Heating (kW)", "Cooling (kW)", "Notes"], duty_rows)
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
            + validate_energy_balance(energy)
            + validate_phase_feasibility(route, thermo, kinetics, reaction_system, energy)
            + validate_solve_result(solve_result)
            + self._chapter_issues(chapter)
        )
        gate = self._gate("design_basis", "Design Basis Lock", "Approve thermo, kinetics, process narrative, and balance basis before detailed design.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_reactor_design(self) -> StageResult:
        route = self._selected_route()
        reaction_system = self._load("reaction_system", ReactionSystem)
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        mixture_properties = self._load("mixture_properties", MixturePropertyArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        reactor_choice = self._load("reactor_choice_decision", DecisionRecord)
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(self._selected_utility_network(), energy)
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
        )
        reactor_basis = build_reactor_design_basis(reactor)
        self._save("reactor_design", reactor)
        self._save("reactor_design_basis", reactor_basis)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), reactor.value_records, resolved_sources, self.config, "reactor_design"),
        )
        markdown = self._render_reactor_design_chapter(reactor, reactor_basis, stream_table, energy)
        chapter = self._chapter(
            "reactor_design",
            "Reactor Design",
            "reactor_design",
            markdown,
            reactor.citations,
            reactor.assumptions,
            ["reactor_design", "reactor_design_basis"],
            required_inputs=["reaction_system", "stream_table", "energy_balance"],
        )
        issues = (
            validate_decision_record(reactor_choice, "reactor_choice_decision")
            + validate_property_requirements_for_stage(
                "reactor_design",
                property_requirements,
                property_packages,
                route,
                self.config.basis.target_product,
                mixture_properties,
                relevant_unit_ids=["reactor"],
            )
            + validate_reactor_design(reactor)
            + self._value_issues(reactor, "reactor_design")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_distillation_design(self) -> StageResult:
        route = self._selected_route()
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        mixture_properties = self._load("mixture_properties", MixturePropertyArtifact)
        property_packages = self._load("property_packages", PropertyPackageArtifact)
        property_requirements = self._load("property_requirements", PropertyRequirementSet)
        separation_thermo = self._load("separation_thermo", SeparationThermoArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        separation_choice = self._load("separation_choice_decision", DecisionRecord)
        exchanger_choice = select_exchanger_configuration(route, energy)
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(self._selected_utility_network(), energy)
        column = build_column_design(
            self.config.basis,
            route,
            stream_table,
            energy,
            mixture_properties,
            separation_choice,
            utility_architecture,
            separation_thermo,
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
        markdown = self._render_process_unit_design_chapter(column, column_hydraulics, exchanger, exchanger_thermal, stream_table)
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
            + validate_column_design(column)
            + self._value_issues(column, "column_design")
            + self._value_issues(exchanger, "heat_exchanger_design")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_equipment_sizing(self) -> StageResult:
        product_profile = self._load("product_profile", ProductProfileArtifact)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        density_record = next((item for item in product_profile.properties if item.name == "Density"), None)
        density_kg_m3 = 1100.0
        if density_record:
            density_kg_m3 = float(density_record.value) * 1000.0 if density_record.units == "g/cm3" else float(density_record.value)
        route = self._selected_route()
        reactor = self._load("reactor_design", ReactorDesign)
        column = self._load("column_design", ColumnDesign)
        exchanger = self._load("heat_exchanger_design", HeatExchangerDesign)
        reactor_choice = self._load("reactor_choice_decision", DecisionRecord)
        separation_choice = self._load("separation_choice_decision", DecisionRecord)
        energy = self._load("energy_balance", EnergyBalance)
        utility_network = self._selected_utility_network()
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision) or build_utility_architecture_decision(utility_network, energy)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        storage_choice = select_storage_configuration(self.config.basis, archetype)
        moc_choice = select_moc_configuration(route, archetype)
        storage = build_storage_design(self.config.basis, density_kg_m3, product_profile.citations, product_profile.assumptions, storage_choice)
        pump_design = build_pump_design(storage)
        self._save("storage_design", storage)
        equipment_items = build_equipment_list(route, reactor, column, exchanger, storage, energy, moc_choice, utility_architecture)
        artifact = EquipmentListArtifact(
            items=equipment_items,
            citations=sorted(set(reactor.citations + column.citations + exchanger.citations + storage.citations + utility_architecture.citations)),
            assumptions=reactor.assumptions + column.assumptions + exchanger.assumptions + storage.assumptions + utility_architecture.assumptions,
        )
        datasheets = build_equipment_datasheets(artifact, reactor, column, exchanger, storage)
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
        rows = [[item.equipment_id, item.equipment_type, item.service, f"{item.volume_m3:.3f}", item.material_of_construction] for item in equipment_items]
        markdown = markdown_table(["ID", "Type", "Service", "Volume (m3)", "MoC"], rows)
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
                    ["Working volume (m3)", f"{storage.working_volume_m3:.3f}"],
                    ["Total volume (m3)", f"{storage.total_volume_m3:.3f}"],
                    ["Tank diameter (m)", f"{storage.diameter_m:.3f}"],
                    ["Straight-side height (m)", f"{storage.straight_side_height_m:.3f}"],
                ],
            )
            + "\n\n"
            f"{markdown}",
            artifact.citations,
            artifact.assumptions,
            ["storage_design", "pump_design", "equipment_list", "equipment_datasheets", "storage_choice_decision", "moc_choice_decision"],
            required_inputs=["reactor_design", "column_design", "heat_exchanger_design"],
        )
        issues = (
            validate_decision_record(storage_choice, "storage_choice_decision")
            + validate_decision_record(moc_choice, "moc_choice_decision")
            + self._value_issues(storage, "storage_design")
            + validate_equipment_applicability(route, reactor_choice, separation_choice, reactor, column, exchanger, utility_network)
            + self._chapter_issues(chapter)
        )
        gate = self._gate("equipment_basis", "Reactor/Column Design Basis", "Approve reactor, column, exchanger, and storage design basis before downstream detailing.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_mechanical_design_moc(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        artifact = build_mechanical_design_artifact(equipment)
        basis = build_mechanical_design_basis(artifact)
        vessel_designs = build_vessel_mechanical_designs(artifact)
        self._save("mechanical_design", artifact)
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
        chapter = self._chapter(
            "mechanical_design_moc",
            "Mechanical Design and MoC",
            "mechanical_design_moc",
            artifact.markdown
            + "\n\n"
            + markdown_table(
                ["Equipment", "Support Load (kN)", "Anchor Bolt (mm)", "Base Plate (mm)", "Thermal Growth (mm)"],
                [
                    [
                        item.equipment_id,
                        f"{item.support_design.support_load_basis_kn:.3f}",
                        f"{item.support_design.anchor_bolt_diameter_mm:.3f}",
                        f"{item.support_design.base_plate_thickness_mm:.3f}",
                        f"{item.support_design.thermal_growth_mm:.3f}",
                    ]
                    for item in vessel_designs
                    if item.support_design is not None
                ]
                or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
            ),
            artifact.citations or equipment.citations,
            artifact.assumptions + ["Mechanical chapter now uses deterministic screening calculations for shell thickness, nozzles, and supports."],
            ["mechanical_design", "mechanical_design_basis", "vessel_mechanical_designs"],
            required_inputs=["equipment_list", "route_selection"],
            summary="Mechanical design chapter includes screening shell thickness, nozzle, and support calculations for major equipment.",
        )
        issues = self._value_issues(artifact, "mechanical_design") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_storage_utilities(self) -> StageResult:
        storage = self._load("storage_design", StorageDesign)
        equipment = self._load("equipment_list", EquipmentListArtifact)
        energy = self._load("energy_balance", EnergyBalance)
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
            + "\n\n### Utilities\n\n"
            + markdown_table(["Utility", "Load", "Units", "Basis"], rows)
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
            required_inputs=["storage_design", "equipment_list", "energy_balance", "utility_network_decision"],
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
        route = self._selected_route()
        artifact = build_control_plan_from_flowsheet(route, equipment, utilities, flowsheet_graph)
        control_architecture = build_control_architecture_decision(
            route,
            equipment,
            utilities.model_dump_json(indent=2),
            artifact,
            flowsheet_graph,
        )
        self._save("control_plan", artifact)
        self._save("control_architecture", control_architecture)
        self._refresh_agent_fabric()
        rows = [[loop.control_id, loop.controlled_variable, loop.manipulated_variable, loop.sensor, loop.actuator] for loop in artifact.control_loops]
        markdown = (
            artifact.markdown
            + "\n\n### Control Architecture Decision\n\n"
            + control_architecture.markdown
            + "\n\n### Control Loops\n\n"
            + markdown_table(["Loop", "Controlled variable", "Manipulated variable", "Sensor", "Actuator"], rows)
        )
        chapter = self._chapter(
            "instrumentation_control",
            "Instrumentation and Process Control",
            "instrumentation_control",
            markdown,
            artifact.citations or control_architecture.citations or equipment.citations or utilities.citations,
            artifact.assumptions + control_architecture.assumptions,
            ["control_plan", "control_architecture"],
            required_inputs=["equipment_list", "utility_summary", "flowsheet_graph"],
        )
        issues = validate_control_architecture(control_architecture) + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_hazop_she(self) -> StageResult:
        route = self._selected_route()
        equipment = self._load("equipment_list", EquipmentListArtifact)
        flowsheet_graph = self._load("flowsheet_graph", FlowsheetGraph)
        control_plan = self._load("control_plan", ControlPlanArtifact)
        register = build_hazop_node_register(route, equipment, flowsheet_graph, control_plan)
        hazop = HazopStudyArtifact(nodes=register.nodes, markdown=register.markdown, citations=register.citations, assumptions=register.assumptions)
        self._save("hazop_study", hazop)
        self._save("hazop_node_register", register)
        she = self.reasoning.build_safety_environment(self.config.basis, route.model_dump_json(indent=2), hazop.model_dump_json(indent=2))
        self._save("safety_environment", she)
        hazop_chapter = self._chapter("hazop", "HAZOP", "hazop_she", hazop.markdown, hazop.citations, hazop.assumptions, ["hazop_study", "hazop_node_register"], required_inputs=["equipment_list", "route_selection", "flowsheet_graph", "control_plan"])
        she_chapter = self._chapter("safety_health_environment_waste", "Safety, Health, Environment, and Waste Management", "hazop_she", she.markdown, she.citations or route.citations or equipment.citations, she.assumptions + register.assumptions, ["safety_environment"], required_inputs=["equipment_list", "route_selection", "flowsheet_graph", "control_plan"], summary=she.summary)
        issues = validate_hazop_node_register(register) + self._chapter_issues(hazop_chapter) + self._chapter_issues(she_chapter)
        gate = self._gate("hazop", "HAZOP Gate", "Approve critical HAZOP nodes and SHE safeguards.")
        return StageResult(chapters=[hazop_chapter, she_chapter], issues=issues, gate=gate)

    def _run_layout_waste(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        flowsheet_graph = self._load("flowsheet_graph", FlowsheetGraph)
        archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        layout_choice = select_layout_configuration(site, equipment, utilities, flowsheet_graph, archetype)
        layout_decision = build_layout_decision(site.selected_site, equipment, utilities, flowsheet_graph, layout_choice)
        artifact = NarrativeArtifact(
            artifact_id="layout_plan",
            title="Layout",
            markdown=layout_decision.markdown,
            summary=layout_choice.selected_summary,
            citations=layout_decision.citations,
            assumptions=layout_decision.assumptions,
        )
        self._save("layout_plan", artifact)
        self._save("layout_decision", layout_decision)
        self._refresh_agent_fabric()
        chapter = self._chapter(
            "layout",
            "Project and Plant Layout",
            "layout_waste",
            artifact.markdown,
            artifact.citations or site.citations or equipment.citations or utilities.citations,
            artifact.assumptions,
            ["layout_plan", "layout_decision"],
            required_inputs=["equipment_list", "utility_summary", "site_selection"],
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
        utility_network = self._selected_utility_network()
        utility_architecture = self._maybe_load("utility_architecture", UtilityArchitectureDecision)
        citations = sorted(set(equipment.citations + utilities.citations + market.citations + site.citations + utility_network.citations))
        assumptions = equipment.assumptions + utilities.assumptions + market.assumptions + site.assumptions + utility_network.assumptions
        procurement_basis = build_procurement_basis_decision(site, equipment.items)
        logistics_basis = build_logistics_basis_decision(site, market)
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
        )
        plant_cost_summary = build_plant_cost_summary(cost_model)
        self._save("cost_model", cost_model)
        self._save("plant_cost_summary", plant_cost_summary)
        self._save("procurement_basis_decision", procurement_basis)
        self._save("logistics_basis_decision", logistics_basis)
        self._refresh_agent_fabric()
        resolved_values = self._load("resolved_values", ResolvedValueArtifact)
        resolved_sources = self._load("resolved_sources", ResolvedSourceSet)
        self._save("resolved_values", extend_resolved_value_artifact(resolved_values, cost_model.value_records, resolved_sources, self.config, "project_cost"))
        scenario_markdown = ""
        if cost_model.scenario_results:
            scenario_markdown = "\n\n### Scenario Cost Snapshot\n\n" + markdown_table(
                ["Scenario", "Utility Cost (INR/y)", "Operating Cost (INR/y)", "Revenue (INR/y)", "Gross Margin (INR/y)"],
                [
                    [
                        item.scenario_name,
                        f"{item.annual_utility_cost_inr:,.2f}",
                        f"{item.annual_operating_cost_inr:,.2f}",
                        f"{item.annual_revenue_inr:,.2f}",
                        f"{item.gross_margin_inr:,.2f}",
                    ]
                    for item in cost_model.scenario_results
                ],
            )
        equipment_cost_markdown = "\n\n### Equipment-wise Costing\n\n" + markdown_table(
            ["Equipment", "Type", "Bare Cost (INR)", "Installed Cost (INR)", "Spares (INR)", "Basis"],
            [
                [
                    item.equipment_id,
                    item.equipment_type,
                    f"{item.bare_cost_inr:,.2f}",
                    f"{item.installed_cost_inr:,.2f}",
                    f"{item.spares_cost_inr:,.2f}",
                    item.basis,
                ]
                for item in cost_model.equipment_cost_items
            ] or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        )
        markdown = markdown_table(
            ["Cost bucket", f"Value ({cost_model.currency})"],
            [
                ["Equipment purchase", f"{cost_model.equipment_purchase_cost:,.2f}"],
                ["Installed cost", f"{cost_model.installed_cost:,.2f}"],
                ["Direct cost", f"{cost_model.direct_cost:,.2f}"],
                ["Indirect cost", f"{cost_model.indirect_cost:,.2f}"],
                ["Contingency", f"{cost_model.contingency:,.2f}"],
                ["Heat integration CAPEX", f"{cost_model.integration_capex_inr:,.2f}"],
                ["Total CAPEX", f"{cost_model.total_capex:,.2f}"],
            ],
        )
        markdown += equipment_cost_markdown + scenario_markdown
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
            ["cost_model", "plant_cost_summary", "procurement_basis_decision", "logistics_basis_decision"],
            required_inputs=["equipment_list", "utility_summary", "stream_table", "market_assessment", "site_selection"],
        )
        issues = (
            validate_decision_record(procurement_basis, "procurement_basis_decision")
            + validate_decision_record(logistics_basis, "logistics_basis_decision")
            + validate_cost_model(cost_model, self._source_ids(), self.config)
            + self._value_issues(cost_model, "cost_model")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_cost_of_production(self) -> StageResult:
        cost_model = self._load("cost_model", CostModel)
        unit_cost = cost_model.annual_opex / max(annual_output_kg(self.config.basis), 1.0)
        markdown = markdown_table(
            ["Opex bucket", f"Value ({cost_model.currency}/y)"],
            [
                ["Raw materials", f"{cost_model.annual_raw_material_cost:,.2f}"],
                ["Utilities", f"{cost_model.annual_utility_cost:,.2f}"],
                ["Labor", f"{cost_model.annual_labor_cost:,.2f}"],
                ["Maintenance", f"{cost_model.annual_maintenance_cost:,.2f}"],
                ["Overheads", f"{cost_model.annual_overheads:,.2f}"],
                ["Total OPEX", f"{cost_model.annual_opex:,.2f}"],
                ["Unit cost", f"{unit_cost:,.2f} {cost_model.currency}/kg"],
            ],
        )
        chapter = self._chapter(
            "cost_of_production",
            "Cost of Production",
            "cost_of_production",
            markdown,
            cost_model.citations,
            cost_model.assumptions,
            ["cost_model"],
            required_inputs=["cost_model"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_working_capital(self) -> StageResult:
        cost_model = self._load("cost_model", CostModel)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        citations = sorted(set(cost_model.citations + market.citations))
        assumptions = cost_model.assumptions + market.assumptions
        model = build_working_capital_model(self.config.basis, cost_model, market.estimated_price_per_kg, citations, assumptions)
        self._save("working_capital_model", model)
        self._save(
            "resolved_values",
            extend_resolved_value_artifact(self._load("resolved_values", ResolvedValueArtifact), model.value_records, self._load("resolved_sources", ResolvedSourceSet), self.config, "working_capital"),
        )
        markdown = markdown_table(
            ["Parameter", "Value"],
            [
                ["Raw-material inventory days", f"{model.raw_material_days:.1f}"],
                ["Product inventory days", f"{model.product_inventory_days:.1f}"],
                ["Receivable days", f"{model.receivable_days:.1f}"],
                ["Payable days", f"{model.payable_days:.1f}"],
                ["Working capital", f"INR {model.working_capital_inr:,.2f}"],
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
        cost_model = self._load("cost_model", CostModel)
        working_capital = self._load("working_capital_model", WorkingCapitalModel)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        utility_network = self._selected_utility_network()
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
        utility_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_basis_decision.json", DecisionRecord)
        financing_basis = build_financing_basis_decision(self.config.basis, site)
        citations = sorted(set(cost_model.citations + working_capital.citations + market.citations))
        assumptions = cost_model.assumptions + working_capital.assumptions + market.assumptions
        financial_model = build_financial_model(self.config.basis, market.estimated_price_per_kg, cost_model, working_capital, citations, assumptions, financing_basis=financing_basis)
        economic_basis_decision = build_economic_basis_decision(self.config, site, utility_network, cost_model, financial_model, utility_basis_decision)
        economic_scenarios = build_economic_scenario_model_v2(cost_model, financial_model, economic_basis_decision)
        debt_schedule = build_debt_schedule(cost_model, financing_basis)
        tax_depreciation_basis = build_tax_depreciation_basis(cost_model)
        financial_schedule = build_financial_schedule(financial_model)
        plant_cost_summary = build_plant_cost_summary(cost_model, working_capital)
        cost_model.economic_basis_decision_id = economic_basis_decision.decision_id
        self._save("cost_model", cost_model)
        self._save("plant_cost_summary", plant_cost_summary)
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
        markdown = markdown_table(
            ["Metric", "Value"],
            [
                ["Annual revenue", f"{financial_model.currency} {financial_model.annual_revenue:,.2f}"],
                ["Annual operating cost", f"{financial_model.currency} {financial_model.annual_operating_cost:,.2f}"],
                ["Gross profit", f"{financial_model.currency} {financial_model.gross_profit:,.2f}"],
                ["Working capital", f"{financial_model.currency} {financial_model.working_capital:,.2f}"],
                ["Payback", f"{financial_model.payback_years:.3f} y"],
                ["NPV", f"{financial_model.currency} {financial_model.npv:,.2f}"],
                ["IRR", f"{financial_model.irr:.2f}%"],
                ["Profitability index", f"{financial_model.profitability_index:.3f}"],
                ["Break-even fraction", f"{financial_model.break_even_fraction:.3f}"],
            ],
        )
        if financial_model.scenario_results:
            markdown += "\n\n### Scenario Margin Snapshot\n\n" + markdown_table(
                ["Scenario", "Revenue (INR/y)", "Operating Cost (INR/y)", "Gross Margin (INR/y)"],
                [
                    [
                        item.scenario_name,
                        f"{item.annual_revenue_inr:,.2f}",
                        f"{item.annual_operating_cost_inr:,.2f}",
                        f"{item.gross_margin_inr:,.2f}",
                    ]
                    for item in financial_model.scenario_results
                ],
            )
        if financial_model.annual_schedule:
            markdown += "\n\n### Multi-Year Financial Schedule\n\n" + markdown_table(
                ["Year", "Capacity Utilization (%)", "Revenue (INR)", "Operating Cost (INR)", "Interest (INR)", "Depreciation (INR)", "PBT (INR)", "Tax (INR)", "PAT (INR)", "Cash Accrual (INR)"],
                [
                    [
                        str(item["year"]),
                        f'{item["capacity_utilization_pct"]:.2f}',
                        f'{item["revenue_inr"]:,.2f}',
                        f'{item["operating_cost_inr"]:,.2f}',
                        f'{item["interest_inr"]:,.2f}',
                        f'{item["depreciation_inr"]:,.2f}',
                        f'{item["profit_before_tax_inr"]:,.2f}',
                        f'{item["tax_inr"]:,.2f}',
                        f'{item["profit_after_tax_inr"]:,.2f}',
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
            + validate_decision_record(financing_basis, "financing_basis_decision")
            + validate_decision_record(economic_basis_decision, "economic_basis_decision")
            + self._value_issues(financial_model, "financial_model")
            + validate_cross_chapter_consistency(
                self.config,
                self._load("route_selection", RouteSelectionArtifact),
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
        resolved_sources = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_sources.json", ResolvedSourceSet)
        product_profile = self._load("product_profile", ProductProfileArtifact)
        property_gap = self.store.maybe_load_model(self.config.project_id, "artifacts/property_gap.json", PropertyGapArtifact)
        resolved_values = self.store.maybe_load_model(self.config.project_id, "artifacts/resolved_values.json", ResolvedValueArtifact)
        property_packages = self.store.maybe_load_model(self.config.project_id, "artifacts/property_packages.json", PropertyPackageArtifact)
        property_requirements = self.store.maybe_load_model(self.config.project_id, "artifacts/property_requirements.json", PropertyRequirementSet)
        separation_thermo = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_thermo.json", SeparationThermoArtifact)
        agent_fabric = self.store.maybe_load_model(self.config.project_id, "artifacts/agent_decision_fabric.json", AgentDecisionFabricArtifact)
        process_archetype = self.store.maybe_load_model(self.config.project_id, "artifacts/process_archetype.json", ProcessArchetype)
        process_synthesis = self.store.maybe_load_model(self.config.project_id, "artifacts/process_synthesis.json", ProcessSynthesisArtifact)
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
        debt_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/debt_schedule.json", DebtSchedule)
        tax_depreciation_basis = self.store.maybe_load_model(self.config.project_id, "artifacts/tax_depreciation_basis.json", TaxDepreciationBasis)
        financial_schedule = self.store.maybe_load_model(self.config.project_id, "artifacts/financial_schedule.json", FinancialSchedule)
        route_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/route_decision.json", DecisionRecord)
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
        existing_chapters = self._existing_chapters(state)
        report_excerpt = "\n\n".join(chapter.rendered_markdown for chapter in existing_chapters if chapter.chapter_id not in {"executive_summary", "conclusion"})
        executive = self.reasoning.build_executive_summary(self.config.basis, report_excerpt)
        conclusion = self.reasoning.build_conclusion(self.config.basis, financial.model_dump_json(indent=2))
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
            reaction_system,
            property_gap,
            resolved_values,
            property_packages,
            property_requirements,
            separation_thermo,
            process_archetype,
            process_synthesis,
            agent_fabric,
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
        full_chapters = [chapter for chapter in existing_chapters if chapter.chapter_id not in {"executive_summary", "conclusion"}] + [executive_chapter, conclusion_chapter]
        report_markdown = assemble_report(self.config.basis, full_chapters, references_md, annexures_md)
        markdown_path = self.store.save_text(self.config.project_id, "final_report.md", report_markdown)
        final_report = FinalReport(project_id=self.config.project_id, markdown_path=str(markdown_path), references=list(source_index.keys()), annexure_paths=[str(self.store.project_dir(self.config.project_id) / "annexures")])
        self._save("final_report", final_report)
        issues = self._chapter_issues(executive_chapter) + self._chapter_issues(conclusion_chapter)
        gate = self._gate("final_signoff", "Final Signoff", "Approve the final markdown report before PDF rendering is released.")
        return StageResult(chapters=[executive_chapter, conclusion_chapter], issues=issues, missing_india_coverage=[], stale_source_groups=[], gate=gate)
