from __future__ import annotations

from dataclasses import dataclass, field
import json
import math

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
from aoc.models import (
    ChapterArtifact,
    ChapterStatus,
    ColumnDesign,
    ControlPlanArtifact,
    CostModel,
    DecisionRecord,
    EnergyBalance,
    EquipmentListArtifact,
    FinalReport,
    FinancialModel,
    GateDecision,
    GateStatus,
    HazopNode,
    HazopStudyArtifact,
    HeatExchangerDesign,
    HeatIntegrationStudyArtifact,
    KineticAssessmentArtifact,
    MarketAssessmentArtifact,
    NarrativeArtifact,
    ProcessSynthesisArtifact,
    ProcessNarrativeArtifact,
    PropertyGapArtifact,
    ProductProfileArtifact,
    ProvenanceTag,
    ProjectConfig,
    ProjectRunState,
    ReactionSystem,
    ReactorDesign,
    ResearchBundle,
    RoughAlternativeSummaryArtifact,
    RouteOption,
    RouteSelectionArtifact,
    RouteSurveyArtifact,
    RunStatus,
    SensitivityLevel,
    Severity,
    SiteSelectionArtifact,
    StorageDesign,
    StreamTable,
    ThermoAssessmentArtifact,
    UtilitySummaryArtifact,
    UtilityNetworkDecision,
    ValidationIssue,
    WorkingCapitalModel,
    utc_now,
)
from aoc.publish import annexures_markdown, assemble_report, markdown_table, references_markdown, render_pdf
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager
from aoc.store import ArtifactStore
from aoc.validators import (
    apply_state_issues,
    validate_chapter,
    validate_column_design,
    validate_cost_model,
    validate_cross_chapter_consistency,
    validate_decision_record,
    validate_equipment_applicability,
    validate_financial_model,
    validate_heat_integration_study,
    validate_india_location_data,
    validate_india_price_data,
    validate_kinetic_assessment,
    validate_phase_feasibility,
    validate_property_gap_artifact,
    validate_property_records,
    validate_site_selection_consistency,
    validate_reactor_design,
    validate_research_bundle,
    validate_route_balance,
    validate_stream_table,
    validate_thermo_assessment,
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
    StageSpec("project_intake", "Project intake and basis lock", (), ("project_basis", "research_bundle")),
    StageSpec("product_profile", "Introduction and product profile", ("research_bundle",), ("product_profile",)),
    StageSpec("market_capacity", "Market and capacity selection", ("research_bundle",), ("market_assessment",)),
    StageSpec("literature_route_survey", "Literature survey", ("research_bundle",), ("route_survey",)),
    StageSpec("property_gap_resolution", "Property gap resolution", ("product_profile",), ("property_gap",)),
    StageSpec("site_selection", "Site selection", ("research_bundle",), ("site_selection", "site_selection_decision")),
    StageSpec("process_synthesis", "Process synthesis", ("route_survey", "property_gap"), ("process_synthesis",)),
    StageSpec("rough_alternative_balances", "Rough alternative balances", ("process_synthesis", "market_assessment"), ("rough_alternatives",)),
    StageSpec("heat_integration_optimization", "Heat integration optimization", ("rough_alternatives", "market_assessment"), ("heat_integration_study",), "heat_integration", "Heat Integration Review", "Approve the selected heat-integration studies before route finalization."),
    StageSpec("route_selection", "Process selection", ("route_survey", "rough_alternatives", "heat_integration_study", "market_assessment"), ("route_selection", "route_decision", "reactor_choice_decision", "separation_choice_decision", "utility_network_decision"), "process_architecture", "Process Architecture", "Approve the selected route, reactor, separation train, and utility-integration basis before downstream design work continues."),
    StageSpec("thermodynamic_feasibility", "Thermodynamics", ("route_selection", "route_survey", "research_bundle"), ("thermo_assessment",)),
    StageSpec("kinetic_feasibility", "Kinetics", ("route_selection", "route_survey", "research_bundle"), ("kinetic_assessment",)),
    StageSpec("block_diagram", "Block diagram", ("route_selection", "route_survey", "research_bundle"), ("process_narrative",)),
    StageSpec("process_description", "Process description", ("process_narrative",), ("process_narrative",)),
    StageSpec("material_balance", "Material balance", ("route_selection", "kinetic_assessment"), ("reaction_system", "stream_table")),
    StageSpec("energy_balance", "Energy balance", ("stream_table", "thermo_assessment"), ("energy_balance",), "design_basis", "Design Basis Lock", "Approve thermo, kinetics, process narrative, and balance basis before detailed design."),
    StageSpec("reactor_design", "Reactor design", ("reaction_system", "stream_table", "energy_balance"), ("reactor_design",)),
    StageSpec("distillation_design", "Distillation/process-unit design", ("stream_table", "energy_balance"), ("column_design", "heat_exchanger_design")),
    StageSpec("equipment_sizing", "Equipment sizing", ("reactor_design", "column_design", "heat_exchanger_design"), ("storage_design", "equipment_list"), "equipment_basis", "Reactor/Column Design Basis", "Approve reactor, column, exchanger, and storage design basis before downstream detailing."),
    StageSpec("mechanical_design_moc", "Mechanical design and materials of construction", ("equipment_list", "route_selection"), ("mechanical_design",)),
    StageSpec("storage_utilities", "Storage and utilities", ("storage_design", "equipment_list", "energy_balance"), ("utility_summary", "utility_basis_decision")),
    StageSpec("instrumentation_control", "Instrumentation and process control", ("equipment_list", "utility_summary"), ("control_plan",)),
    StageSpec("hazop_she", "HAZOP and SHE", ("equipment_list", "route_selection"), ("hazop_study", "safety_environment"), "hazop", "HAZOP Gate", "Approve critical HAZOP nodes and SHE safeguards before layout and economics are released."),
    StageSpec("layout_waste", "Project and plant layout", ("equipment_list", "utility_summary", "site_selection"), ("layout_plan",)),
    StageSpec("project_cost", "Project cost", ("equipment_list", "utility_summary", "stream_table", "market_assessment", "site_selection"), ("cost_model",)),
    StageSpec("cost_of_production", "Cost of production", ("cost_model",), ("cost_model",)),
    StageSpec("working_capital", "Working capital", ("cost_model", "market_assessment"), ("working_capital_model",)),
    StageSpec("financial_analysis", "Financial analysis", ("cost_model", "working_capital_model", "market_assessment"), ("financial_model", "economic_basis_decision"), "india_cost_basis", "India Cost Basis", "Approve India site and economics basis before final assembly."),
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
            if result.issues:
                state.run_status = RunStatus.BLOCKED
                state.blocked_stage_id = stage.id
                apply_state_issues(state, result.issues, result.missing_india_coverage, result.stale_source_groups)
                for chapter in result.chapters:
                    chapter.status = ChapterStatus.BLOCKED
                    chapter.blockers.extend(result.issues)
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
        property_gap = self.store.maybe_load_model(self.config.project_id, "artifacts/property_gap.json", PropertyGapArtifact)
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
        route_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/route_decision.json", DecisionRecord)
        reactor_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/reactor_choice_decision.json", DecisionRecord)
        separation_choice = self.store.maybe_load_model(self.config.project_id, "artifacts/separation_choice_decision.json", DecisionRecord)
        utility_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_basis_decision.json", DecisionRecord)
        economic_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_basis_decision.json", DecisionRecord)
        heat_study = self.store.maybe_load_model(self.config.project_id, "artifacts/heat_integration_study.json", HeatIntegrationStudyArtifact)
        if property_gap:
            lines.append("")
            lines.append("value_resolution:")
            unresolved = ", ".join(property_gap.unresolved_high_sensitivity) or "none"
            lines.append(f"- unresolved_high_sensitivity: {unresolved}")
        if site_decision or route_decision or reactor_choice or separation_choice or utility_basis_decision or economic_basis_decision:
            lines.append("")
            lines.append("decisions:")
            for decision in [site_decision, route_decision, reactor_choice, separation_choice, utility_basis_decision, economic_basis_decision]:
                if decision:
                    lines.append(
                        f"- {decision.decision_id}: selected={decision.selected_candidate_id or 'n/a'}; stability={decision.scenario_stability.value}; approval_required={'yes' if decision.approval_required else 'no'}"
                    )
        if heat_study:
            lines.append("")
            lines.append("heat_integration:")
            for route_case in heat_study.route_decisions:
                selected_case = selected_heat_case(route_case)
                lines.append(
                    f"- {route_case.route_id}: case={selected_case.case_id if selected_case else 'n/a'}; recovered_kw={selected_case.recovered_duty_kw if selected_case else 0.0:.1f}; savings_inr={selected_case.annual_savings_inr if selected_case else 0.0:.2f}"
                )
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
        self._save("project_basis", self.config.basis)
        self._save("research_bundle", bundle)
        issues, missing_groups, stale_groups = validate_research_bundle(bundle, self.config)
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
        self._save("market_assessment", artifact)
        issues = validate_india_price_data(artifact.india_price_data, self._source_ids(), self.config, "market_assessment")
        chapter = self._chapter(
            "market_capacity_selection",
            "Market and Capacity Selection",
            "market_capacity",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["market_assessment"],
            required_inputs=["research_bundle"],
            summary=artifact.capacity_rationale,
        )
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
        artifact = resolve_property_gaps(product_profile, self.config)
        self._save("property_gap", artifact)
        issues = validate_property_gap_artifact(artifact, self.config)
        return StageResult(issues=issues)

    def _run_process_synthesis(self) -> StageResult:
        survey = self._load("route_survey", RouteSurveyArtifact)
        property_gap = self._load("property_gap", PropertyGapArtifact)
        artifact = build_process_synthesis(self.config, survey, property_gap)
        self._save("process_synthesis", artifact)
        self.config.basis.operating_mode = artifact.operating_mode_decision.selected_candidate_id or self.config.basis.operating_mode
        self.store.save_config(self.config)
        issues = validate_decision_record(artifact.operating_mode_decision, "operating_mode")
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
        selection, route_decision, reactor_choice, separation_choice, utility_network = select_route_architecture(
            self.config,
            survey,
            rough_alternatives,
            heat_study,
            market,
        )
        self._save("route_selection", selection)
        self._save("route_decision", route_decision)
        self._save("reactor_choice_decision", reactor_choice)
        self._save("separation_choice_decision", separation_choice)
        self._save("utility_network_decision", utility_network)
        selected_route = self._selected_route()
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
        artifact = self.reasoning.build_thermo_assessment(self.config.basis, route, bundle.sources, bundle.corpus_excerpt)
        artifact.value_records = [
            make_value_record(
                "thermo_reaction_enthalpy",
                "Reaction enthalpy",
                artifact.estimated_reaction_enthalpy_kj_per_mol,
                "kJ/mol",
                provenance_method=ProvenanceTag.SOURCED,
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "thermo_reaction_gibbs",
                "Reaction Gibbs free energy",
                artifact.estimated_gibbs_kj_per_mol,
                "kJ/mol",
                provenance_method=ProvenanceTag.SOURCED,
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
        ]
        self._save("thermo_assessment", artifact)
        chapter = self._chapter(
            "thermodynamic_feasibility",
            "Thermodynamic Feasibility",
            "thermodynamic_feasibility",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["thermo_assessment"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
            summary=artifact.equilibrium_comment,
        )
        issues = validate_route_balance(route) + validate_thermo_assessment(artifact) + self._value_issues(artifact, "thermo_assessment") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_kinetic_feasibility(self) -> StageResult:
        bundle = self._load("research_bundle", ResearchBundle)
        route = self._selected_route()
        artifact = self.reasoning.build_kinetic_assessment(self.config.basis, route, bundle.sources, bundle.corpus_excerpt)
        artifact.value_records = [
            make_value_record(
                "kinetic_activation_energy",
                "Activation energy",
                artifact.activation_energy_kj_per_mol,
                "kJ/mol",
                provenance_method=ProvenanceTag.SOURCED,
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "kinetic_pre_exponential",
                "Pre-exponential factor",
                artifact.pre_exponential_factor,
                "1/h",
                provenance_method=ProvenanceTag.SOURCED,
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.MEDIUM,
            ),
            make_value_record(
                "kinetic_residence_time",
                "Design residence time",
                artifact.design_residence_time_hr,
                "h",
                provenance_method=ProvenanceTag.SOURCED,
                citations=artifact.citations,
                assumptions=artifact.assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
        ]
        self._save("kinetic_assessment", artifact)
        chapter = self._chapter(
            "reaction_kinetics",
            "Reaction Kinetics",
            "kinetic_feasibility",
            artifact.markdown,
            artifact.citations,
            artifact.assumptions,
            ["kinetic_assessment"],
            required_inputs=["route_selection", "route_survey", "research_bundle"],
        )
        issues = validate_kinetic_assessment(artifact) + self._value_issues(artifact, "kinetic_assessment") + self._chapter_issues(chapter)
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
        reaction_system = build_reaction_system(self.config.basis, route, kinetics, route.citations + kinetics.citations, route.assumptions + kinetics.assumptions)
        stream_table = build_stream_table(self.config.basis, route, reaction_system, reaction_system.citations, reaction_system.assumptions)
        self._save("reaction_system", reaction_system)
        self._save("stream_table", stream_table)
        stream_rows: list[list[str]] = []
        for stream in stream_table.streams:
            for component in stream.components:
                stream_rows.append([stream.stream_id, component.name, f"{component.mass_flow_kg_hr:.3f}", f"{component.molar_flow_kmol_hr:.6f}"])
        markdown = markdown_table(["Stream", "Component", "kg/h", "kmol/h"], stream_rows)
        chapter = self._chapter(
            "material_balance",
            "Material Balance",
            "material_balance",
            markdown,
            sorted(set(stream_table.citations + reaction_system.citations)),
            reaction_system.assumptions + stream_table.assumptions,
            ["reaction_system", "stream_table"],
            required_inputs=["route_selection", "kinetic_assessment"],
        )
        issues = (
            validate_reaction_system(reaction_system)
            + validate_stream_table(stream_table)
            + self._value_issues(reaction_system, "reaction_system")
            + self._value_issues(stream_table, "stream_table")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_energy_balance(self) -> StageResult:
        route = self._selected_route()
        stream_table = self._load("stream_table", StreamTable)
        thermo = self._load("thermo_assessment", ThermoAssessmentArtifact)
        kinetics = self._load("kinetic_assessment", KineticAssessmentArtifact)
        reaction_system = self._load("reaction_system", ReactionSystem)
        energy = build_energy_balance(route, stream_table, thermo)
        self._save("energy_balance", energy)
        duty_rows = [[duty.unit_id, f"{duty.heating_kw:.3f}", f"{duty.cooling_kw:.3f}", duty.notes] for duty in energy.duties]
        markdown = markdown_table(["Unit", "Heating (kW)", "Cooling (kW)", "Notes"], duty_rows)
        chapter = self._chapter(
            "energy_balance",
            "Energy Balance",
            "energy_balance",
            markdown,
            sorted(set(stream_table.citations + energy.citations)),
            stream_table.assumptions + energy.assumptions,
            ["energy_balance"],
            required_inputs=["stream_table", "thermo_assessment"],
        )
        issues = (
            self._value_issues(energy, "energy_balance")
            + validate_phase_feasibility(route, thermo, kinetics, reaction_system, energy)
            + self._chapter_issues(chapter)
        )
        gate = self._gate("design_basis", "Design Basis Lock", "Approve thermo, kinetics, process narrative, and balance basis before detailed design.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_reactor_design(self) -> StageResult:
        route = self._selected_route()
        reaction_system = self._load("reaction_system", ReactionSystem)
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        reactor = build_reactor_design(self.config.basis, route, reaction_system, stream_table, energy)
        self._save("reactor_design", reactor)
        markdown = markdown_table(
            ["Parameter", "Value"],
            [
                ["Reactor type", reactor.reactor_type],
                ["Residence time (h)", f"{reactor.residence_time_hr:.3f}"],
                ["Liquid holdup (m3)", f"{reactor.liquid_holdup_m3:.3f}"],
                ["Design volume (m3)", f"{reactor.design_volume_m3:.3f}"],
                ["Design temperature (C)", f"{reactor.design_temperature_c:.1f}"],
                ["Design pressure (bar)", f"{reactor.design_pressure_bar:.2f}"],
                ["Heat duty (kW)", f"{reactor.heat_duty_kw:.3f}"],
                ["Heat-transfer area (m2)", f"{reactor.heat_transfer_area_m2:.3f}"],
            ],
        )
        chapter = self._chapter(
            "reactor_design",
            "Reactor Design",
            "reactor_design",
            markdown,
            reactor.citations,
            reactor.assumptions,
            ["reactor_design"],
            required_inputs=["reaction_system", "stream_table", "energy_balance"],
        )
        issues = validate_reactor_design(reactor) + self._value_issues(reactor, "reactor_design") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_distillation_design(self) -> StageResult:
        route = self._selected_route()
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        column = build_column_design(self.config.basis, route, stream_table, energy)
        exchanger = build_heat_exchanger_design(route, energy)
        self._save("column_design", column)
        self._save("heat_exchanger_design", exchanger)
        markdown = (
            "### D-101 Distillation Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Light key", column.light_key],
                    ["Heavy key", column.heavy_key],
                    ["Relative volatility", f"{column.relative_volatility:.3f}"],
                    ["Minimum stages", f"{column.min_stages:.3f}"],
                    ["Design stages", str(column.design_stages)],
                    ["Reflux ratio", f"{column.reflux_ratio:.3f}"],
                    ["Diameter (m)", f"{column.column_diameter_m:.3f}"],
                    ["Height (m)", f"{column.column_height_m:.3f}"],
                    ["Condenser duty (kW)", f"{column.condenser_duty_kw:.3f}"],
                    ["Reboiler duty (kW)", f"{column.reboiler_duty_kw:.3f}"],
                ],
            )
            + "\n\n### E-101 Heat Exchanger Basis\n\n"
            + markdown_table(
                ["Parameter", "Value"],
                [
                    ["Service", exchanger.service],
                    ["Heat load (kW)", f"{exchanger.heat_load_kw:.3f}"],
                    ["LMTD (K)", f"{exchanger.lmtd_k:.1f}"],
                    ["Overall U (W/m2-K)", f"{exchanger.overall_u_w_m2_k:.1f}"],
                    ["Area (m2)", f"{exchanger.area_m2:.3f}"],
                ],
            )
        )
        chapter = self._chapter(
            "distillation_design",
            "Distillation / Process-Unit Design",
            "distillation_design",
            markdown,
            sorted(set(column.citations + exchanger.citations)),
            column.assumptions + exchanger.assumptions,
            ["column_design", "heat_exchanger_design"],
            required_inputs=["stream_table", "energy_balance"],
        )
        issues = validate_column_design(column) + self._value_issues(column, "column_design") + self._value_issues(exchanger, "heat_exchanger_design") + self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_equipment_sizing(self) -> StageResult:
        product_profile = self._load("product_profile", ProductProfileArtifact)
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
        utility_network = self._selected_utility_network()
        storage = build_storage_design(self.config.basis, density_kg_m3, product_profile.citations, product_profile.assumptions)
        self._save("storage_design", storage)
        energy = self._load("energy_balance", EnergyBalance)
        equipment_items = build_equipment_list(route, reactor, column, exchanger, storage, energy)
        artifact = EquipmentListArtifact(items=equipment_items, citations=sorted(set(reactor.citations + column.citations + exchanger.citations + storage.citations)), assumptions=reactor.assumptions + column.assumptions + exchanger.assumptions + storage.assumptions)
        self._save("equipment_list", artifact)
        rows = [[item.equipment_id, item.equipment_type, item.service, f"{item.volume_m3:.3f}", item.material_of_construction] for item in equipment_items]
        markdown = markdown_table(["ID", "Type", "Service", "Volume (m3)", "MoC"], rows)
        chapter = self._chapter(
            "equipment_design_sizing",
            "Equipment Design and Sizing",
            "equipment_sizing",
            markdown,
            artifact.citations,
            artifact.assumptions,
            ["storage_design", "equipment_list"],
            required_inputs=["reactor_design", "column_design", "heat_exchanger_design"],
        )
        issues = (
            self._value_issues(storage, "storage_design")
            + validate_equipment_applicability(route, reactor_choice, separation_choice, reactor, column, exchanger, utility_network)
            + self._chapter_issues(chapter)
        )
        gate = self._gate("equipment_basis", "Reactor/Column Design Basis", "Approve reactor, column, exchanger, and storage design basis before downstream detailing.")
        return StageResult(chapters=[chapter], issues=issues, gate=gate)

    def _run_mechanical_design_moc(self) -> StageResult:
        route = self._selected_route()
        equipment = self._load("equipment_list", EquipmentListArtifact)
        artifact = self.reasoning.build_mechanical_design(self.config.basis, route, equipment.model_dump_json(indent=2))
        self._save("mechanical_design", artifact)
        chapter = self._chapter(
            "mechanical_design_moc",
            "Mechanical Design and MoC",
            "mechanical_design_moc",
            artifact.markdown,
            artifact.citations or route.citations or equipment.citations,
            artifact.assumptions,
            ["mechanical_design"],
            required_inputs=["equipment_list", "route_selection"],
            summary=artifact.summary,
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_storage_utilities(self) -> StageResult:
        storage = self._load("storage_design", StorageDesign)
        equipment = self._load("equipment_list", EquipmentListArtifact)
        energy = self._load("energy_balance", EnergyBalance)
        site = self._load("site_selection", SiteSelectionArtifact)
        utility_network = self._selected_utility_network()
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
        )
        artifact.utility_basis_decision_id = utility_basis_decision.decision_id
        self._save("utility_basis_decision", utility_basis_decision)
        self._save("utility_summary", artifact)
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
        )
        chapter = self._chapter(
            "storage_utilities",
            "Storage and Utilities",
            "storage_utilities",
            markdown,
            sorted(set(storage.citations + artifact.citations + utility_network.citations + utility_basis_decision.citations)),
            storage.assumptions + artifact.assumptions + utility_network.assumptions + utility_basis_decision.assumptions,
            ["utility_summary", "utility_basis_decision"],
            required_inputs=["storage_design", "equipment_list", "energy_balance", "utility_network_decision"],
        )
        issues = (
            validate_decision_record(utility_basis_decision, "utility_basis_decision")
            + self._value_issues(utility_basis, "utility_basis")
            + self._value_issues(artifact, "utility_summary")
            + self._chapter_issues(chapter)
        )
        return StageResult(chapters=[chapter], issues=issues)

    def _run_instrumentation_control(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        artifact = self.reasoning.build_control_strategy(self.config.basis, equipment.model_dump_json(indent=2), utilities.model_dump_json(indent=2))
        self._save("control_plan", artifact)
        rows = [[loop.control_id, loop.controlled_variable, loop.manipulated_variable, loop.sensor, loop.actuator] for loop in artifact.control_loops]
        markdown = artifact.markdown + "\n\n### Control Loops\n\n" + markdown_table(["Loop", "Controlled variable", "Manipulated variable", "Sensor", "Actuator"], rows)
        chapter = self._chapter(
            "instrumentation_control",
            "Instrumentation and Process Control",
            "instrumentation_control",
            markdown,
            artifact.citations or equipment.citations or utilities.citations,
            artifact.assumptions,
            ["control_plan"],
            required_inputs=["equipment_list", "utility_summary"],
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_hazop_she(self) -> StageResult:
        route = self._selected_route()
        equipment = self._load("equipment_list", EquipmentListArtifact)
        nodes = [
            HazopNode(node_id="R-102", parameter="Temperature", guide_word="More", causes=["Loss of cooling", "High EO feed"], consequences=["Runaway tendency", "Selectivity loss"], safeguards=["Temperature alarm", "Emergency feed isolation"], recommendation="Trip EO feed and open emergency cooling on high-high reactor temperature.", citations=route.citations),
            HazopNode(node_id="R-102", parameter="Pressure", guide_word="More", causes=["Blocked outlet", "Rapid vapor generation"], consequences=["Hydrator overpressure"], safeguards=["PSV", "Pressure alarm"], recommendation="Confirm relief load case and vent routing to safe containment.", citations=route.citations),
            HazopNode(node_id="V-101", parameter="Level", guide_word="Less", causes=["Excess withdrawal", "Flash instability"], consequences=["Pump cavitation", "Poor downstream feed control"], safeguards=["Low-level alarm", "Pump trip"], recommendation="Interlock transfer pump on low-low level.", citations=route.citations),
            HazopNode(node_id="D-101", parameter="Pressure", guide_word="Less", causes=["Vacuum overshoot"], consequences=["Air ingress", "Column instability"], safeguards=["Vacuum control loop", "Pressure alarm"], recommendation="Provide low-pressure permissive and oxygen ingress monitoring.", citations=route.citations),
        ]
        hazop_markdown = "### HAZOP Summary\n\n" + markdown_table(
            ["Node", "Parameter", "Guide word", "Causes", "Consequences", "Safeguards", "Recommendation"],
            [[node.node_id, node.parameter, node.guide_word, "; ".join(node.causes), "; ".join(node.consequences), "; ".join(node.safeguards), node.recommendation] for node in nodes],
        )
        hazop = HazopStudyArtifact(nodes=nodes, markdown=hazop_markdown, citations=route.citations, assumptions=route.assumptions)
        self._save("hazop_study", hazop)
        she = self.reasoning.build_safety_environment(self.config.basis, route.model_dump_json(indent=2), hazop.model_dump_json(indent=2))
        self._save("safety_environment", she)
        hazop_chapter = self._chapter("hazop", "HAZOP", "hazop_she", hazop.markdown, hazop.citations, hazop.assumptions, ["hazop_study"], required_inputs=["equipment_list", "route_selection"])
        she_chapter = self._chapter("safety_health_environment_waste", "Safety, Health, Environment, and Waste Management", "hazop_she", she.markdown, she.citations or route.citations or equipment.citations, she.assumptions, ["safety_environment"], required_inputs=["equipment_list", "route_selection"], summary=she.summary)
        issues = self._chapter_issues(hazop_chapter) + self._chapter_issues(she_chapter)
        gate = self._gate("hazop", "HAZOP Gate", "Approve critical HAZOP nodes and SHE safeguards.")
        return StageResult(chapters=[hazop_chapter, she_chapter], issues=issues, gate=gate)

    def _run_layout_waste(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        artifact = self.reasoning.build_layout_plan(self.config.basis, equipment.model_dump_json(indent=2), utilities.model_dump_json(indent=2), site.model_dump_json(indent=2))
        self._save("layout_plan", artifact)
        chapter = self._chapter(
            "layout",
            "Project and Plant Layout",
            "layout_waste",
            artifact.markdown,
            artifact.citations or site.citations or equipment.citations or utilities.citations,
            artifact.assumptions,
            ["layout_plan"],
            required_inputs=["equipment_list", "utility_summary", "site_selection"],
            summary=artifact.summary,
        )
        issues = self._chapter_issues(chapter)
        return StageResult(chapters=[chapter], issues=issues)

    def _run_project_cost(self) -> StageResult:
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        stream_table = self._load("stream_table", StreamTable)
        market = self._load("market_assessment", MarketAssessmentArtifact)
        site = self._load("site_selection", SiteSelectionArtifact)
        utility_network = self._selected_utility_network()
        citations = sorted(set(equipment.citations + utilities.citations + market.citations + site.citations + utility_network.citations))
        assumptions = equipment.assumptions + utilities.assumptions + market.assumptions + site.assumptions + utility_network.assumptions
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
            scenario_policy=self.config.scenario_policy,
        )
        self._save("cost_model", cost_model)
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
        markdown += scenario_markdown
        chapter = self._chapter(
            "project_cost",
            "Project Cost",
            "project_cost",
            markdown,
            cost_model.citations,
            cost_model.assumptions,
            ["cost_model"],
            required_inputs=["equipment_list", "utility_summary", "stream_table", "market_assessment", "site_selection"],
        )
        issues = validate_cost_model(cost_model, self._source_ids(), self.config) + self._value_issues(cost_model, "cost_model") + self._chapter_issues(chapter)
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
        citations = sorted(set(cost_model.citations + working_capital.citations + market.citations))
        assumptions = cost_model.assumptions + working_capital.assumptions + market.assumptions
        financial_model = build_financial_model(self.config.basis, market.estimated_price_per_kg, cost_model, working_capital, citations, assumptions)
        economic_basis_decision = build_economic_basis_decision(self.config, site, utility_network, cost_model, financial_model, utility_basis_decision)
        cost_model.economic_basis_decision_id = economic_basis_decision.decision_id
        self._save("cost_model", cost_model)
        self._save("financial_model", financial_model)
        self._save("economic_basis_decision", economic_basis_decision)
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
        chapter = self._chapter(
            "financial_analysis",
            "Financial Analysis",
            "financial_analysis",
            markdown,
            financial_model.citations,
            financial_model.assumptions + economic_basis_decision.assumptions,
            ["financial_model", "economic_basis_decision"],
            required_inputs=["cost_model", "working_capital_model", "market_assessment"],
        )
        issues = (
            validate_financial_model(financial_model, self.config)
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
        product_profile = self._load("product_profile", ProductProfileArtifact)
        property_gap = self.store.maybe_load_model(self.config.project_id, "artifacts/property_gap.json", PropertyGapArtifact)
        process_synthesis = self.store.maybe_load_model(self.config.project_id, "artifacts/process_synthesis.json", ProcessSynthesisArtifact)
        stream_table = self._load("stream_table", StreamTable)
        energy = self._load("energy_balance", EnergyBalance)
        heat_integration_study = self.store.maybe_load_model(self.config.project_id, "artifacts/heat_integration_study.json", HeatIntegrationStudyArtifact)
        utility_network = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_network_decision.json", UtilityNetworkDecision)
        site_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/site_selection_decision.json", DecisionRecord)
        utility_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/utility_basis_decision.json", DecisionRecord)
        economic_basis_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/economic_basis_decision.json", DecisionRecord)
        equipment = self._load("equipment_list", EquipmentListArtifact)
        utilities = self._load("utility_summary", UtilitySummaryArtifact)
        cost_model = self._load("cost_model", CostModel)
        working_capital = self._load("working_capital_model", WorkingCapitalModel)
        financial = self._load("financial_model", FinancialModel)
        route_decision = self.store.maybe_load_model(self.config.project_id, "artifacts/route_decision.json", DecisionRecord)
        reaction_system = self._load("reaction_system", ReactionSystem)
        reactor = self._load("reactor_design", ReactorDesign)
        column = self._load("column_design", ColumnDesign)
        exchanger = self._load("heat_exchanger_design", HeatExchangerDesign)
        storage = self._load("storage_design", StorageDesign)
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
            ("Utility Basis Traces", utilities.utility_basis.calc_traces if utilities.utility_basis else []),
            ("Project-Cost Traces", cost_model.calc_traces),
            ("Working-Capital Traces", working_capital.calc_traces),
            ("Financial Traces", financial.calc_traces),
        ]
        annexures_md = annexures_markdown(
            product_profile,
            property_gap,
            process_synthesis,
            stream_table,
            equipment.items,
            energy,
            heat_integration_study,
            utility_network,
            utilities,
            cost_model,
            working_capital,
            financial,
            route_decision,
            site_decision,
            utility_basis_decision,
            economic_basis_decision,
            source_index,
            assumptions,
            calc_sections,
            site.india_location_data,
            [
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
