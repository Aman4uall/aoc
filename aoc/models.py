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
    decision_policy: DecisionPolicy = DecisionPolicy.HYBRID
    optimization_scope: OptimizationScope = OptimizationScope.EG_FIRST
    preferred_route_id: Optional[str] = None
    preferred_site: Optional[str] = None
    preferred_site_candidates: list[str] = Field(default_factory=list)
    preferred_state_candidates: list[str] = Field(default_factory=list)
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


class AssumptionRecord(BaseModel):
    assumption_id: str
    statement: str
    reason: str
    impact_scope: str
    expiry_review_condition: str


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


class PropertyGapArtifact(ProvenancedModel):
    values: list[ValueRecord] = Field(default_factory=list)
    assumptions_log: list[AssumptionRecord] = Field(default_factory=list)
    unresolved_high_sensitivity: list[str] = Field(default_factory=list)
    markdown: str


class ProcessSynthesisArtifact(ProvenancedModel):
    operating_mode_decision: DecisionRecord
    route_candidates: list[AlternativeOption] = Field(default_factory=list)
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


class EnergyBalance(ProvenancedModel):
    duties: list[UnitDuty]
    total_heating_kw: float
    total_cooling_kw: float
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
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


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
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class HeatExchangerDesign(ProvenancedModel):
    exchanger_id: str
    service: str
    heat_load_kw: float
    lmtd_k: float
    overall_u_w_m2_k: float
    area_m2: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class StorageDesign(ProvenancedModel):
    storage_id: str
    service: str
    inventory_days: float
    working_volume_m3: float
    total_volume_m3: float
    material_of_construction: str
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


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
    utility_basis_decision_id: Optional[str] = None
    value_records: list[ValueRecord] = Field(default_factory=list)


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


class HeatIntegrationStudyArtifact(ProvenancedModel):
    route_decisions: list[UtilityNetworkDecision] = Field(default_factory=list)
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
    value_records: list[ValueRecord] = Field(default_factory=list)


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
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    scenario_results: list[ScenarioResult] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


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


class ProcessNarrativeArtifact(ProvenancedModel):
    bfd_mermaid: str
    markdown: str


class ControlPlanArtifact(ProvenancedModel):
    control_loops: list[ControlLoop]
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
