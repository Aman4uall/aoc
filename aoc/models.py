from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SourceKind(str, Enum):
    USER_DOCUMENT = "user_document"
    LITERATURE = "literature"
    PATENT = "patent"
    SDS = "sds"
    MARKET = "market"
    HANDBOOK = "handbook"
    WEB = "web"
    COMPANY_REPORT = "company_report"
    GOVERNMENT = "government"
    UTILITY = "utility"
    LOGISTICS = "logistics"


class ProvenanceTag(str, Enum):
    SOURCED = "sourced"
    ESTIMATED = "estimated"
    ANALOGY = "analogy"
    USER_SUPPLIED = "user_supplied"
    CALCULATED = "calculated"


class GeographicScope(str, Enum):
    INDIA = "india"
    GLOBAL = "global"
    STATE = "state"
    CITY = "city"
    UNKNOWN = "unknown"


class SourceDomain(str, Enum):
    TECHNICAL = "technical"
    SAFETY = "safety"
    MARKET = "market"
    SITE = "site"
    ECONOMICS = "economics"
    REGULATORY = "regulatory"
    UTILITIES = "utilities"
    LOGISTICS = "logistics"


class ProcessTemplate(str, Enum):
    GENERIC_SMALL_MOLECULE = "generic_small_molecule"
    ETHYLENE_GLYCOL_INDIA = "ethylene_glycol_india"


class ChapterStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETE = "complete"


class RunStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"


class GateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"


class Severity(str, Enum):
    WARNING = "warning"
    BLOCKED = "blocked"


class DecisionPolicy(str, Enum):
    HYBRID = "hybrid"
    AUTONOMOUS = "autonomous"
    ANALYST_DRIVEN = "analyst_driven"


class OptimizationScope(str, Enum):
    EG_FIRST = "eg_first"
    GENERIC = "generic"


class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScenarioStability(str, Enum):
    STABLE = "stable"
    BORDERLINE = "borderline"
    UNSTABLE = "unstable"


class ModelSettings(BaseModel):
    backend: Literal["google", "mock"] = "google"
    model_name: str = "gemini-3.1-pro-preview"
    temperature: float = 0.2


class HeatIntegrationSettings(BaseModel):
    enabled: bool = True
    min_recoverable_duty_kw: float = 5000.0
    min_approach_temp_c: float = 20.0
    allow_htm_loops: bool = True


class UncertaintyPolicy(BaseModel):
    high_sensitivity_blocks: bool = True


class ScenarioCase(BaseModel):
    name: str
    description: str
    steam_price_multiplier: float = 1.0
    power_price_multiplier: float = 1.0
    feedstock_price_multiplier: float = 1.0
    selling_price_multiplier: float = 1.0
    capex_multiplier: float = 1.0


def default_scenario_cases() -> list[ScenarioCase]:
    return [
        ScenarioCase(name="base", description="Base India tariff and market basis."),
        ScenarioCase(
            name="conservative",
            description="Higher utilities/feedstock and lower sales realization.",
            steam_price_multiplier=1.25,
            power_price_multiplier=1.15,
            feedstock_price_multiplier=1.10,
            selling_price_multiplier=0.95,
            capex_multiplier=1.10,
        ),
        ScenarioCase(
            name="upside",
            description="Milder utilities and stronger selling-price realization.",
            steam_price_multiplier=0.90,
            power_price_multiplier=0.95,
            feedstock_price_multiplier=0.97,
            selling_price_multiplier=1.04,
            capex_multiplier=0.97,
        ),
    ]


class ScenarioPolicy(BaseModel):
    cases: list[ScenarioCase] = Field(default_factory=default_scenario_cases)


class ProjectBasis(BaseModel):
    target_product: str
    capacity_tpa: float
    target_purity_wt_pct: float
    operating_mode: Literal["batch", "continuous"] = "continuous"
    annual_operating_days: int = 330
    region: str = "India"
    currency: str = "INR"
    site_assumptions: list[str] = Field(default_factory=list)
    process_template: ProcessTemplate = ProcessTemplate.GENERIC_SMALL_MOLECULE
    target_state: Optional[str] = None
    target_city: Optional[str] = None
    tariff_reference_year: int = 2025
    utility_basis_year: int = 2025
    labor_basis_year: int = 2025
    economic_reference_year: int = 2025
    india_only: bool = False


class UserDocument(BaseModel):
    label: str
    path: str
    source_kind: SourceKind = SourceKind.USER_DOCUMENT
    source_domain: SourceDomain = SourceDomain.TECHNICAL
    geographic_scope: GeographicScope = GeographicScope.UNKNOWN


class ProjectConfig(BaseModel):
    project_id: Optional[str] = None
    basis: ProjectBasis
    strict_citation_policy: bool = True
    public_data_only: bool = True
    decision_policy: DecisionPolicy = DecisionPolicy.HYBRID
    optimization_scope: OptimizationScope = OptimizationScope.EG_FIRST
    preferred_route_id: Optional[str] = None
    preferred_site: Optional[str] = None
    preferred_site_candidates: list[str] = Field(default_factory=list)
    preferred_state_candidates: list[str] = Field(default_factory=list)
    compound_family_hint: Optional[str] = None
    phase_system_hint: Optional[str] = None
    benchmark_profile: Optional[str] = None
    evidence_lock_required: bool = True
    capacity_case_candidates: list[float] = Field(default_factory=list)
    require_india_only_data: bool = False
    user_documents: list[UserDocument] = Field(default_factory=list)
    india_market_sheets: list[str] = Field(default_factory=list)
    output_root: str = "outputs"
    model: ModelSettings = Field(default_factory=ModelSettings)
    heat_integration: HeatIntegrationSettings = Field(default_factory=HeatIntegrationSettings)
    uncertainty_policy: UncertaintyPolicy = Field(default_factory=UncertaintyPolicy)
    scenario_policy: ScenarioPolicy = Field(default_factory=ScenarioPolicy)


class SourceRecord(BaseModel):
    source_id: str
    source_kind: SourceKind
    source_domain: SourceDomain
    title: str
    url_or_doi: Optional[str] = None
    access_date: str = Field(default_factory=utc_now)
    citation_text: str
    extraction_snippet: str = ""
    confidence: float = 1.0
    provenance_tag: ProvenanceTag = ProvenanceTag.SOURCED
    local_path: Optional[str] = None
    geographic_scope: GeographicScope = GeographicScope.UNKNOWN
    geographic_label: Optional[str] = None
    reference_year: Optional[int] = None
    normalization_year: Optional[int] = None
    country: Optional[str] = None


class ProvenancedModel(BaseModel):
    citations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class PropertyRecord(ProvenancedModel):
    name: str
    value: str
    units: str
    basis: Optional[str] = None
    method: ProvenanceTag = ProvenanceTag.SOURCED
    supporting_sources: list[str] = Field(default_factory=list)


class ValueRecord(ProvenancedModel):
    value_id: str
    name: str
    value: str
    units: str
    provenance_method: ProvenanceTag
    source_ids: list[str] = Field(default_factory=list)
    uncertainty_band: str = ""
    sensitivity: SensitivityLevel = SensitivityLevel.LOW
    blocking: bool = False


class SourceCandidate(BaseModel):
    source_id: str
    authority_score: float
    recency_score: float
    geography_score: float
    domain_fit_score: float
    consistency_score: float
    total_score: float
    rationale: str = ""


class SourceCandidateSet(ProvenancedModel):
    group_id: str
    source_domain: SourceDomain
    geographic_requirement: str
    candidates: list[SourceCandidate] = Field(default_factory=list)
    selected_source_ids: list[str] = Field(default_factory=list)
    unresolved_conflict: bool = False
    markdown: str = ""


class SourceConflict(ProvenancedModel):
    conflict_id: str
    source_domain: SourceDomain
    selected_source_id: Optional[str] = None
    competing_source_ids: list[str] = Field(default_factory=list)
    score_gap: float = 0.0
    blocking: bool = False
    rationale: str = ""
    recommended_resolution: str = ""


class ResolvedSourceSet(ProvenancedModel):
    groups: list[SourceCandidateSet] = Field(default_factory=list)
    selected_source_ids: list[str] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)
    conflicts: list[SourceConflict] = Field(default_factory=list)
    markdown: str


class ResolvedValue(ValueRecord):
    resolution_level: int = 1
    selected_source_id: Optional[str] = None
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    justification: str = ""


class PropertyEstimate(ProvenancedModel):
    estimate_id: str
    property_name: str
    selected_method: ProvenanceTag
    candidate_methods: list[ProvenanceTag] = Field(default_factory=list)
    selected_source_id: Optional[str] = None
    sensitivity: SensitivityLevel = SensitivityLevel.LOW
    blocking: bool = False
    rationale: str = ""


class AssumptionRecord(BaseModel):
    assumption_id: str
    statement: str
    reason: str
    impact_scope: str
    expiry_review_condition: str


class ResolvedValueArtifact(ProvenancedModel):
    values: list[ResolvedValue] = Field(default_factory=list)
    unresolved_value_ids: list[str] = Field(default_factory=list)
    property_estimates: list[PropertyEstimate] = Field(default_factory=list)
    markdown: str


class DecisionCriterion(BaseModel):
    name: str
    weight: float
    hard_constraint: bool = False
    direction: Literal["maximize", "minimize"] = "maximize"
    justification: str


class AlternativeOption(ProvenancedModel):
    candidate_id: str
    candidate_type: str
    description: str
    inputs: dict[str, str] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)
    rejected_reasons: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    total_score: float = 0.0
    feasible: bool = True


class DecisionRecord(ProvenancedModel):
    decision_id: str
    context: str
    criteria: list[DecisionCriterion] = Field(default_factory=list)
    alternatives: list[AlternativeOption] = Field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    selected_summary: str = ""
    hard_constraint_results: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    scenario_stability: ScenarioStability = ScenarioStability.STABLE
    approval_required: bool = False
    blocked_value_ids: list[str] = Field(default_factory=list)


class AlternativeSet(ProvenancedModel):
    set_id: str
    context: str
    criteria: list[DecisionCriterion] = Field(default_factory=list)
    alternatives: list[AlternativeOption] = Field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    scenario_stability: ScenarioStability = ScenarioStability.STABLE
    markdown: str = ""


class OptionSet(ProvenancedModel):
    option_set_id: str
    specialist_role: str
    context: str
    alternatives: list[AlternativeOption] = Field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    markdown: str = ""


class CriticVerdict(ProvenancedModel):
    verdict_id: str
    specialist_role: str
    status: Literal["pass", "warning", "blocked"] = "pass"
    decision_id: Optional[str] = None
    message: str
    blocking_issue_codes: list[str] = Field(default_factory=list)
    recommended_action: str = ""


class DecisionPacket(ProvenancedModel):
    packet_id: str
    specialist_role: str
    context: str
    option_set: OptionSet
    selected_decision: Optional[DecisionRecord] = None
    critic_verdicts: list[CriticVerdict] = Field(default_factory=list)
    markdown: str = ""


class AgentDecisionFabricArtifact(ProvenancedModel):
    packets: list[DecisionPacket] = Field(default_factory=list)
    markdown: str


class PropertyGapArtifact(ProvenancedModel):
    values: list[ValueRecord] = Field(default_factory=list)
    assumptions_log: list[AssumptionRecord] = Field(default_factory=list)
    unresolved_high_sensitivity: list[str] = Field(default_factory=list)
    markdown: str


class ProcessSynthesisArtifact(ProvenancedModel):
    operating_mode_decision: DecisionRecord
    route_candidates: list[AlternativeOption] = Field(default_factory=list)
    archetype: Optional["ProcessArchetype"] = None
    alternative_sets: list[AlternativeSet] = Field(default_factory=list)
    markdown: str


class MethodSelectionArtifact(ProvenancedModel):
    method_family: Literal["thermo", "kinetics"]
    decision: DecisionRecord
    markdown: str


class RoughAlternativeCase(ProvenancedModel):
    candidate_id: str
    route_id: str
    route_name: str
    operating_mode: str
    reactor_class: str
    separation_train: str
    estimated_heating_kw: float
    estimated_cooling_kw: float
    estimated_capex_inr: float
    estimated_annual_utility_cost_inr: float
    estimated_annual_total_opex_inr: float
    notes: str = ""


class RoughAlternativeSummaryArtifact(ProvenancedModel):
    cases: list[RoughAlternativeCase] = Field(default_factory=list)
    markdown: str


class ReactionParticipant(BaseModel):
    name: str
    formula: str
    coefficient: float
    role: Literal["reactant", "product", "byproduct"]
    molecular_weight_g_mol: float
    phase: Optional[str] = None


class RouteHazard(BaseModel):
    severity: Literal["low", "moderate", "high"]
    description: str
    safeguard: str


class RouteOption(ProvenancedModel):
    route_id: str
    name: str
    reaction_equation: str
    participants: list[ReactionParticipant]
    catalysts: list[str] = Field(default_factory=list)
    operating_temperature_c: float
    operating_pressure_bar: float
    residence_time_hr: float
    yield_fraction: float
    selectivity_fraction: float
    byproducts: list[str] = Field(default_factory=list)
    separations: list[str] = Field(default_factory=list)
    scale_up_notes: str
    hazards: list[RouteHazard] = Field(default_factory=list)
    route_score: float
    rationale: str


class SiteOption(ProvenancedModel):
    name: str
    state: str
    raw_material_score: int
    logistics_score: int
    utility_score: int
    business_score: int
    total_score: int
    rationale: str


class StreamComponentFlow(BaseModel):
    name: str
    formula: Optional[str] = None
    mass_flow_kg_hr: float
    molar_flow_kmol_hr: float


class StreamRecord(BaseModel):
    stream_id: str
    description: str
    temperature_c: float
    pressure_bar: float
    components: list[StreamComponentFlow]
    source_unit_id: Optional[str] = None
    destination_unit_id: Optional[str] = None
    phase_hint: str = ""


class CalcTrace(BaseModel):
    trace_id: str
    title: str
    formula: str
    substitutions: dict[str, str] = Field(default_factory=dict)
    result: str
    units: str = ""
    notes: str = ""


class StreamTable(ProvenancedModel):
    streams: list[StreamRecord]
    closure_error_pct: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)
    unit_operation_packets: list["UnitOperationPacket"] = Field(default_factory=list)
    separation_packets: list["SeparationPacket"] = Field(default_factory=list)
    recycle_packets: list["RecyclePacket"] = Field(default_factory=list)


class StreamSpec(ProvenancedModel):
    stream_id: str
    source_unit_id: Optional[str] = None
    destination_unit_id: Optional[str] = None
    phase_hint: str = ""
    total_mass_flow_kg_hr: float = 0.0
    total_molar_flow_kmol_hr: float = 0.0
    component_names: list[str] = Field(default_factory=list)


class UnitOperationPacket(ProvenancedModel):
    packet_id: str
    unit_id: str
    unit_type: str
    service: str
    inlet_stream_ids: list[str] = Field(default_factory=list)
    outlet_stream_ids: list[str] = Field(default_factory=list)
    inlet_mass_flow_kg_hr: float = 0.0
    outlet_mass_flow_kg_hr: float = 0.0
    closure_error_pct: float = 0.0
    status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class SeparationPacket(ProvenancedModel):
    packet_id: str
    unit_id: str
    separation_family: str
    driving_force: str
    inlet_stream_ids: list[str] = Field(default_factory=list)
    product_stream_ids: list[str] = Field(default_factory=list)
    waste_stream_ids: list[str] = Field(default_factory=list)
    recycle_stream_ids: list[str] = Field(default_factory=list)
    side_draw_stream_ids: list[str] = Field(default_factory=list)
    closure_error_pct: float = 0.0
    notes: list[str] = Field(default_factory=list)


class RecyclePacket(ProvenancedModel):
    packet_id: str
    loop_id: str
    recycle_stream_ids: list[str] = Field(default_factory=list)
    purge_stream_ids: list[str] = Field(default_factory=list)
    component_targets_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_fresh_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_recycle_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_purge_kmol_hr: dict[str, float] = Field(default_factory=dict)
    convergence_status: Literal["converged", "estimated", "blocked"] = "estimated"
    closure_error_pct: float = 0.0
    max_iterations: int = 0
    notes: list[str] = Field(default_factory=list)


class UnitSpec(ProvenancedModel):
    unit_id: str
    unit_type: str
    service: str
    upstream_stream_ids: list[str] = Field(default_factory=list)
    downstream_stream_ids: list[str] = Field(default_factory=list)
    closure_error_pct: float = 0.0
    closure_status: Literal["converged", "estimated", "blocked"] = "estimated"
    unresolved_sensitivities: list[str] = Field(default_factory=list)


class SeparationSpec(ProvenancedModel):
    separation_id: str
    separation_family: str
    driving_force: str
    inlet_stream_ids: list[str] = Field(default_factory=list)
    product_stream_ids: list[str] = Field(default_factory=list)
    waste_stream_ids: list[str] = Field(default_factory=list)
    recycle_stream_ids: list[str] = Field(default_factory=list)
    side_draw_stream_ids: list[str] = Field(default_factory=list)
    closure_error_pct: float = 0.0


class RecycleLoop(ProvenancedModel):
    loop_id: str
    recycle_stream_ids: list[str] = Field(default_factory=list)
    purge_stream_ids: list[str] = Field(default_factory=list)
    convergence_status: Literal["converged", "estimated", "blocked"] = "estimated"
    closure_error_pct: float = 0.0


class FlowsheetCase(ProvenancedModel):
    case_id: str
    route_id: str
    operating_mode: str
    units: list[UnitSpec] = Field(default_factory=list)
    streams: list[StreamSpec] = Field(default_factory=list)
    separations: list[SeparationSpec] = Field(default_factory=list)
    recycle_loops: list[RecycleLoop] = Field(default_factory=list)
    unit_operation_packets: list[UnitOperationPacket] = Field(default_factory=list)
    markdown: str = ""


class SolveResult(ProvenancedModel):
    case_id: str
    convergence_status: Literal["converged", "estimated", "blocked"] = "estimated"
    overall_closure_error_pct: float = 0.0
    unitwise_closure: dict[str, float] = Field(default_factory=dict)
    unitwise_status: dict[str, Literal["converged", "estimated", "blocked"]] = Field(default_factory=dict)
    unresolved_sensitivities: list[str] = Field(default_factory=list)
    critic_messages: list[str] = Field(default_factory=list)
    markdown: str = ""


class ReactionSystem(ProvenancedModel):
    route_id: str
    main_reaction: str
    side_reactions: list[str] = Field(default_factory=list)
    conversion_fraction: float
    selectivity_fraction: float
    excess_ratio: float
    notes: str
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class UnitDuty(BaseModel):
    unit_id: str
    heating_kw: float = 0.0
    cooling_kw: float = 0.0
    notes: str = ""
    duty_type: str = "sensible"
    hot_stream_id: Optional[str] = None
    cold_stream_id: Optional[str] = None


class UnitThermalPacket(ProvenancedModel):
    packet_id: str
    unit_id: str
    service: str
    duty_type: str = "sensible"
    heating_kw: float = 0.0
    cooling_kw: float = 0.0
    hot_stream_id: Optional[str] = None
    cold_stream_id: Optional[str] = None
    hot_supply_temp_c: float = 0.0
    hot_target_temp_c: float = 0.0
    cold_supply_temp_c: float = 0.0
    cold_target_temp_c: float = 0.0
    recoverable_duty_kw: float = 0.0
    candidate_media: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ExchangerNetworkCandidate(ProvenancedModel):
    candidate_id: str
    source_unit_id: str
    sink_unit_id: str
    hot_packet_id: str
    cold_packet_id: str
    topology: Literal["direct", "htm_loop"]
    recovered_duty_kw: float
    minimum_approach_temp_c: float
    feasible: bool = True
    notes: str = ""


class EnergyBalance(ProvenancedModel):
    duties: list[UnitDuty]
    total_heating_kw: float
    total_cooling_kw: float
    unit_thermal_packets: list[UnitThermalPacket] = Field(default_factory=list)
    network_candidates: list[ExchangerNetworkCandidate] = Field(default_factory=list)
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class ReactorDesign(ProvenancedModel):
    reactor_id: str
    reactor_type: str
    design_basis: str
    residence_time_hr: float
    liquid_holdup_m3: float
    design_volume_m3: float
    design_temperature_c: float
    design_pressure_bar: float
    heat_duty_kw: float
    heat_transfer_area_m2: float
    shell_diameter_m: float = 0.0
    shell_length_m: float = 0.0
    overall_u_w_m2_k: float = 0.0
    reynolds_number: float = 0.0
    prandtl_number: float = 0.0
    nusselt_number: float = 0.0
    number_of_tubes: int = 0
    tube_length_m: float = 0.0
    cooling_medium: str = ""
    utility_topology: str = ""
    integrated_thermal_duty_kw: float = 0.0
    residual_utility_duty_kw: float = 0.0
    selected_train_step_ids: list[str] = Field(default_factory=list)
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class ReactorDesignBasis(ProvenancedModel):
    reactor_id: str
    selected_reactor_type: str
    governing_equations: list[str] = Field(default_factory=list)
    design_inputs: dict[str, str] = Field(default_factory=dict)
    operating_envelope: dict[str, str] = Field(default_factory=dict)
    markdown: str = ""


class ColumnDesign(ProvenancedModel):
    column_id: str
    service: str
    light_key: str
    heavy_key: str
    relative_volatility: float
    min_stages: float
    design_stages: int
    reflux_ratio: float
    column_diameter_m: float
    column_height_m: float
    condenser_duty_kw: float
    reboiler_duty_kw: float
    feed_stage: int = 0
    tray_spacing_m: float = 0.0
    flooding_fraction: float = 0.0
    downcomer_area_fraction: float = 0.0
    top_temperature_c: float = 0.0
    bottom_temperature_c: float = 0.0
    utility_topology: str = ""
    integrated_reboiler_duty_kw: float = 0.0
    residual_reboiler_utility_kw: float = 0.0
    condenser_recovery_duty_kw: float = 0.0
    selected_train_step_ids: list[str] = Field(default_factory=list)
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class ColumnHydraulics(ProvenancedModel):
    column_id: str
    flooding_fraction: float
    tray_spacing_m: float
    downcomer_area_fraction: float
    vapor_velocity_m_s: float = 0.0
    liquid_load_m3_hr: float = 0.0
    markdown: str = ""


class HeatExchangerDesign(ProvenancedModel):
    exchanger_id: str
    service: str
    heat_load_kw: float
    lmtd_k: float
    overall_u_w_m2_k: float
    area_m2: float
    exchanger_type: str = ""
    shell_diameter_m: float = 0.0
    tube_count: int = 0
    tube_length_m: float = 0.0
    shell_passes: int = 1
    tube_passes: int = 1
    utility_topology: str = ""
    selected_train_step_id: Optional[str] = None
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class HeatExchangerThermalDesign(ProvenancedModel):
    exchanger_id: str
    selected_configuration: str
    governing_equations: list[str] = Field(default_factory=list)
    thermal_inputs: dict[str, str] = Field(default_factory=dict)
    markdown: str = ""


class StorageDesign(ProvenancedModel):
    storage_id: str
    service: str
    inventory_days: float
    working_volume_m3: float
    total_volume_m3: float
    material_of_construction: str
    diameter_m: float = 0.0
    straight_side_height_m: float = 0.0
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class PumpDesign(ProvenancedModel):
    pump_id: str
    service: str
    flow_m3_hr: float
    differential_head_m: float
    power_kw: float
    npsh_margin_m: float
    markdown: str = ""


class EquipmentDatasheet(ProvenancedModel):
    datasheet_id: str
    equipment_id: str
    equipment_type: str
    service: str
    design_data: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class EquipmentSpec(ProvenancedModel):
    equipment_id: str
    equipment_type: str
    service: str
    design_basis: str
    volume_m3: float
    design_temperature_c: float
    design_pressure_bar: float
    material_of_construction: str
    duty_kw: float = 0.0
    notes: str = ""


class MechanicalComponentDesign(ProvenancedModel):
    equipment_id: str
    equipment_type: str
    design_pressure_bar: float
    design_temperature_c: float
    corrosion_allowance_mm: float
    shell_thickness_mm: float
    head_thickness_mm: float = 0.0
    nozzle_diameter_mm: float = 0.0
    support_type: str = ""
    support_thickness_mm: float = 0.0
    notes: str = ""
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class MechanicalDesignBasis(ProvenancedModel):
    basis_id: str
    code_basis: str
    design_pressure_basis: str
    design_temperature_basis: str
    corrosion_allowance_mm: float
    markdown: str = ""


class SupportDesign(ProvenancedModel):
    equipment_id: str
    support_type: str
    support_load_basis_kn: float
    support_thickness_mm: float
    anchor_bolt_diameter_mm: float = 0.0
    base_plate_thickness_mm: float = 0.0
    markdown: str = ""


class NozzleSchedule(ProvenancedModel):
    equipment_id: str
    nozzle_count: int
    nozzle_diameters_mm: list[float] = Field(default_factory=list)
    nozzle_services: list[str] = Field(default_factory=list)
    markdown: str = ""


class VesselMechanicalDesign(ProvenancedModel):
    equipment_id: str
    shell_thickness_mm: float
    head_thickness_mm: float
    corrosion_allowance_mm: float
    support_design: Optional[SupportDesign] = None
    nozzle_schedule: Optional[NozzleSchedule] = None
    markdown: str = ""


class MechanicalDesignArtifact(ProvenancedModel):
    items: list[MechanicalComponentDesign] = Field(default_factory=list)
    markdown: str
    value_records: list[ValueRecord] = Field(default_factory=list)


class EquipmentListArtifact(ProvenancedModel):
    items: list[EquipmentSpec]


class UtilityLoad(ProvenancedModel):
    utility_id: str
    utility_type: str
    load: float
    units: str
    basis: str
    notes: str = ""


class UtilityBasis(ProvenancedModel):
    steam_pressure_bar: float
    steam_cost_inr_per_kg: float
    cooling_water_cost_inr_per_m3: float
    power_cost_inr_per_kwh: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class UtilitySummaryArtifact(ProvenancedModel):
    items: list[UtilityLoad]
    utility_basis: Optional[UtilityBasis] = None
    selected_heat_integration_case_id: Optional[str] = None
    recovered_duty_kw: float = 0.0
    selected_train_step_count: int = 0
    selected_train_recovered_duty_kw: float = 0.0
    utility_basis_decision_id: Optional[str] = None
    value_records: list[ValueRecord] = Field(default_factory=list)


class EquipmentCostItem(ProvenancedModel):
    equipment_id: str
    equipment_type: str
    service: str
    basis: str
    bare_cost_inr: float
    installed_cost_inr: float
    spares_cost_inr: float = 0.0
    notes: str = ""


class HeatStream(ProvenancedModel):
    stream_id: str
    name: str
    kind: Literal["hot", "cold"]
    source_unit_id: str
    supply_temp_c: float
    target_temp_c: float
    duty_kw: float
    phase_change: bool = False
    notes: str = ""


class UtilityTarget(ProvenancedModel):
    base_hot_utility_kw: float
    base_cold_utility_kw: float
    minimum_hot_utility_kw: float
    minimum_cold_utility_kw: float
    recoverable_duty_kw: float
    pinch_temp_c: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)


class HeatMatch(ProvenancedModel):
    match_id: str
    hot_stream_id: str
    cold_stream_id: str
    recovered_duty_kw: float
    direct: bool
    medium: str
    min_approach_temp_c: float
    notes: str = ""


class HeatStreamSet(ProvenancedModel):
    route_id: str
    hot_streams: list[HeatStream] = Field(default_factory=list)
    cold_streams: list[HeatStream] = Field(default_factory=list)
    pinch_temp_c: float = 0.0
    markdown: str = ""


class HeatMatchCandidate(ProvenancedModel):
    candidate_id: str
    hot_stream_id: str
    cold_stream_id: str
    topology: str
    recovered_duty_kw: float
    feasible: bool = True
    notes: str = ""


class HeatIntegrationCase(ProvenancedModel):
    case_id: str
    title: str
    recovered_duty_kw: float
    residual_hot_utility_kw: float
    residual_cold_utility_kw: float
    added_capex_inr: float
    annual_savings_inr: float
    payback_years: float
    operability_penalty: float
    safety_penalty: float
    feasible: bool = True
    heat_matches: list[HeatMatch] = Field(default_factory=list)
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    summary: str = ""


class HeatNetworkCase(ProvenancedModel):
    case_id: str
    topology: str
    recovered_duty_kw: float
    residual_hot_utility_kw: float
    residual_cold_utility_kw: float
    exchanger_count: int
    match_candidates: list[HeatMatchCandidate] = Field(default_factory=list)
    selected_matches: list[HeatMatch] = Field(default_factory=list)
    selected_train_steps: list["HeatExchangerTrainStep"] = Field(default_factory=list)
    markdown: str = ""


class HeatExchangerTrainStep(ProvenancedModel):
    step_id: str
    exchanger_id: str
    topology: str
    service: str
    hot_stream_id: str
    cold_stream_id: str
    source_unit_id: str
    sink_unit_id: str
    recovered_duty_kw: float
    medium: str
    notes: str = ""


class HeatNetworkArchitecture(ProvenancedModel):
    route_id: str
    selected_case_id: Optional[str] = None
    heat_stream_set: Optional[HeatStreamSet] = None
    cases: list[HeatNetworkCase] = Field(default_factory=list)
    selected_train_steps: list[HeatExchangerTrainStep] = Field(default_factory=list)
    topology_summary: str = ""
    markdown: str = ""


class ControlLoop(ProvenancedModel):
    control_id: str
    controlled_variable: str
    manipulated_variable: str
    sensor: str
    actuator: str
    notes: str


class HazopNode(ProvenancedModel):
    node_id: str
    parameter: str
    guide_word: str
    causes: list[str]
    consequences: list[str]
    safeguards: list[str]
    recommendation: str


class HazopStudyArtifact(ProvenancedModel):
    nodes: list[HazopNode]
    markdown: str


class HazopNodeRegister(ProvenancedModel):
    nodes: list[HazopNode] = Field(default_factory=list)
    coverage_summary: str
    markdown: str


class IndianPriceDatum(ProvenancedModel):
    datum_id: str
    category: str
    item_name: str
    region: str
    units: str
    value_inr: float
    reference_year: int
    normalization_year: int


class IndianLocationDatum(ProvenancedModel):
    location_id: str
    site_name: str
    state: str
    country: str = "India"
    port_access: str
    utility_note: str
    logistics_note: str
    regulatory_note: str
    reference_year: int


class ScenarioResult(BaseModel):
    scenario_name: str
    annual_utility_cost_inr: float
    annual_operating_cost_inr: float
    annual_revenue_inr: float
    gross_margin_inr: float
    selected: bool = False


class UtilityNetworkDecision(ProvenancedModel):
    route_id: str
    utility_target: UtilityTarget
    heat_streams: list[HeatStream] = Field(default_factory=list)
    cases: list[HeatIntegrationCase] = Field(default_factory=list)
    decision: DecisionRecord
    selected_case_id: Optional[str] = None
    base_annual_utility_cost_inr: float = 0.0
    selected_annual_utility_cost_inr: float = 0.0
    scenario_results: list[ScenarioResult] = Field(default_factory=list)
    markdown: str


class UtilityArchitectureDecision(ProvenancedModel):
    route_id: str
    architecture: HeatNetworkArchitecture
    decision: DecisionRecord
    markdown: str


class HeatIntegrationStudyArtifact(ProvenancedModel):
    route_decisions: list[UtilityNetworkDecision] = Field(default_factory=list)
    markdown: str


class EconomicScenarioModel(ProvenancedModel):
    selected_basis_decision_id: Optional[str] = None
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    markdown: str


class CostModel(ProvenancedModel):
    currency: str
    equipment_purchase_cost: float
    installed_cost: float
    direct_cost: float
    indirect_cost: float
    contingency: float
    total_capex: float
    annual_opex: float
    annual_raw_material_cost: float
    annual_utility_cost: float
    annual_labor_cost: float
    annual_maintenance_cost: float
    annual_overheads: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    india_price_data: list[IndianPriceDatum] = Field(default_factory=list)
    selected_route_id: Optional[str] = None
    selected_heat_integration_case_id: Optional[str] = None
    integration_capex_inr: float = 0.0
    scenario_results: list[ScenarioResult] = Field(default_factory=list)
    economic_basis_decision_id: Optional[str] = None
    equipment_cost_items: list[EquipmentCostItem] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class EquipmentCostBreakdown(ProvenancedModel):
    equipment_id: str
    bare_cost_inr: float
    installation_inr: float
    piping_inr: float
    instrumentation_inr: float
    electrical_inr: float
    civil_structural_inr: float
    insulation_painting_inr: float
    contingency_inr: float
    total_installed_inr: float


class PlantCostSummary(ProvenancedModel):
    currency: str
    equipment_breakdowns: list[EquipmentCostBreakdown] = Field(default_factory=list)
    direct_plant_cost_inr: float
    indirect_cost_inr: float
    contingency_inr: float
    working_capital_inr: float = 0.0
    total_project_cost_inr: float
    markdown: str = ""


class WorkingCapitalModel(ProvenancedModel):
    raw_material_days: float
    product_inventory_days: float
    receivable_days: float
    payable_days: float
    working_capital_inr: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class FinancialModel(ProvenancedModel):
    currency: str
    annual_revenue: float
    annual_operating_cost: float
    gross_profit: float
    working_capital: float
    payback_years: float
    npv: float
    irr: float
    profitability_index: float
    break_even_fraction: float
    annual_schedule: list[dict[str, float | str]] = Field(default_factory=list)
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    scenario_results: list[ScenarioResult] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class DebtScheduleEntry(ProvenancedModel):
    year: int
    opening_debt_inr: float
    principal_repayment_inr: float
    interest_inr: float
    closing_debt_inr: float


class DebtSchedule(ProvenancedModel):
    debt_fraction: float
    interest_rate: float
    entries: list[DebtScheduleEntry] = Field(default_factory=list)
    markdown: str = ""


class TaxDepreciationBasis(ProvenancedModel):
    depreciation_method: str
    depreciation_years: int
    tax_rate_fraction: float
    markdown: str = ""


class FinancialScheduleLine(ProvenancedModel):
    year: int
    capacity_utilization_pct: float
    revenue_inr: float
    operating_cost_inr: float
    depreciation_inr: float
    interest_inr: float
    profit_before_tax_inr: float
    tax_inr: float
    profit_after_tax_inr: float
    cash_accrual_inr: float


class FinancialSchedule(ProvenancedModel):
    currency: str
    lines: list[FinancialScheduleLine] = Field(default_factory=list)
    markdown: str = ""


class ValidationIssue(BaseModel):
    code: str
    severity: Severity
    message: str
    artifact_ref: Optional[str] = None
    source_refs: list[str] = Field(default_factory=list)


class ChapterArtifact(BaseModel):
    chapter_id: str
    title: str
    stage_id: str
    status: ChapterStatus
    required_inputs: list[str] = Field(default_factory=list)
    produced_outputs: list[str] = Field(default_factory=list)
    blockers: list[ValidationIssue] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    summary: str = ""
    rendered_markdown: str


class GateDecision(BaseModel):
    gate_id: str
    title: str
    description: str
    status: GateStatus = GateStatus.PENDING
    notes: str = ""
    created_at: str = Field(default_factory=utc_now)
    approved_at: Optional[str] = None


class ProjectRunState(BaseModel):
    project_id: str
    model_name: str
    strict_citation_policy: bool
    current_stage_index: int = 0
    current_stage_id: str = ""
    run_status: RunStatus = RunStatus.READY
    completed_stages: list[str] = Field(default_factory=list)
    blocked_stage_id: Optional[str] = None
    awaiting_gate_id: Optional[str] = None
    gates: dict[str, GateDecision] = Field(default_factory=dict)
    chapter_index: dict[str, ChapterStatus] = Field(default_factory=dict)
    blocking_issues: list[ValidationIssue] = Field(default_factory=list)
    missing_india_coverage: list[str] = Field(default_factory=list)
    stale_source_groups: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    last_updated: str = Field(default_factory=utc_now)


class BenchmarkManifest(BaseModel):
    benchmark_id: str
    target_product: str
    archetype_family: str
    required_chapters: list[str] = Field(default_factory=list)
    expected_decisions: list[str] = Field(default_factory=list)
    required_public_source_domains: list[SourceDomain] = Field(default_factory=list)
    notes: str = ""


class ResearchBundle(BaseModel):
    sources: list[SourceRecord]
    technical_source_ids: list[str] = Field(default_factory=list)
    india_source_ids: list[str] = Field(default_factory=list)
    corpus_excerpt: str
    user_document_ids: list[str] = Field(default_factory=list)


class SourceDiscoveryArtifact(BaseModel):
    sources: list[SourceRecord]
    summary: str


class ProductProfileArtifact(ProvenancedModel):
    product_name: str
    properties: list[PropertyRecord]
    uses: list[str]
    industrial_relevance: str
    safety_notes: list[str]
    markdown: str


class MarketAssessmentArtifact(ProvenancedModel):
    estimated_price_per_kg: float
    price_range: str
    competitor_notes: list[str]
    demand_drivers: list[str]
    capacity_rationale: str
    india_price_data: list[IndianPriceDatum] = Field(default_factory=list)
    markdown: str


class RouteSurveyArtifact(ProvenancedModel):
    routes: list[RouteOption]
    markdown: str


class RouteSelectionArtifact(ProvenancedModel):
    selected_route_id: str
    justification: str
    comparison_markdown: str


class ProcessArchetype(ProvenancedModel):
    archetype_id: str
    compound_family: Literal["organic", "inorganic", "mixed"]
    dominant_product_phase: Literal["gas", "liquid", "solid", "mixed"]
    dominant_feed_phase: Literal["gas", "liquid", "solid", "mixed"]
    operating_mode_candidates: list[str] = Field(default_factory=list)
    dominant_separation_family: str
    heat_management_profile: str
    hazard_intensity: Literal["low", "moderate", "high"]
    rationale: str
    benchmark_profile: Optional[str] = None


class SiteSelectionArtifact(ProvenancedModel):
    candidates: list[SiteOption]
    selected_site: str
    india_location_data: list[IndianLocationDatum] = Field(default_factory=list)
    markdown: str


class ThermoAssessmentArtifact(ProvenancedModel):
    feasible: bool
    estimated_reaction_enthalpy_kj_per_mol: float
    estimated_gibbs_kj_per_mol: float
    equilibrium_comment: str
    markdown: str
    value_records: list[ValueRecord] = Field(default_factory=list)


class KineticAssessmentArtifact(ProvenancedModel):
    feasible: bool
    activation_energy_kj_per_mol: float
    pre_exponential_factor: float
    apparent_order: float
    design_residence_time_hr: float
    markdown: str
    value_records: list[ValueRecord] = Field(default_factory=list)


class FlowsheetNode(BaseModel):
    node_id: str
    unit_type: str
    label: str
    upstream_nodes: list[str] = Field(default_factory=list)
    downstream_nodes: list[str] = Field(default_factory=list)
    representative_stream_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class UnitOperationModel(ProvenancedModel):
    unit_id: str
    unit_type: str
    service: str
    formula_traces: list[CalcTrace] = Field(default_factory=list)
    convergence_status: Literal["seeded", "converged", "estimated", "blocked"] = "seeded"
    unresolved_sensitivities: list[str] = Field(default_factory=list)


class FlowsheetGraph(ProvenancedModel):
    graph_id: str
    route_id: str
    operating_mode: str
    nodes: list[FlowsheetNode] = Field(default_factory=list)
    unit_models: list[UnitOperationModel] = Field(default_factory=list)
    stream_ids: list[str] = Field(default_factory=list)
    convergence_status: Literal["seeded", "converged", "estimated", "blocked"] = "seeded"
    unresolved_sensitivities: list[str] = Field(default_factory=list)
    markdown: str


class ProcessNarrativeArtifact(ProvenancedModel):
    bfd_mermaid: str
    markdown: str


class ControlPlanArtifact(ProvenancedModel):
    control_loops: list[ControlLoop]
    markdown: str


class ControlArchitectureDecision(ProvenancedModel):
    decision: DecisionRecord
    critical_units: list[str] = Field(default_factory=list)
    markdown: str


class LayoutDecisionArtifact(ProvenancedModel):
    decision: DecisionRecord
    winning_layout_basis: str
    markdown: str


class NarrativeArtifact(ProvenancedModel):
    artifact_id: str
    title: str
    markdown: str
    summary: str


class FinalReport(BaseModel):
    project_id: str
    markdown_path: str
    pdf_path: Optional[str] = None
    references: list[str] = Field(default_factory=list)
    annexure_paths: list[str] = Field(default_factory=list)
