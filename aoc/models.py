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


class DataRealityClass(str, Enum):
    USER_PROVIDED = "user_provided"
    LIVE_FETCHED = "live_fetched"
    STRUCTURED_DATABASE = "structured_database"
    SEEDED_BENCHMARK = "seeded_benchmark"
    SOLVER_DERIVED = "solver_derived"
    MODEL_INFERRED = "model_inferred"
    UNRESOLVED = "unresolved"


class EstimationMethodTag(str, Enum):
    DIRECT = "direct"
    PSEUDO_COMPONENT = "pseudo_component"
    LIBRARY_VALUE = "library_value"
    CORRELATION = "correlation"
    ANALOGY = "analogy"
    RESOLVED_PAIR = "resolved_pair"
    REGRESSED_PAIR = "regressed_pair"
    FAMILY_ESTIMATED_PAIR = "family_estimated_pair"
    FALLBACK = "fallback"
    CITED_KINETIC_FIT = "cited_kinetic_fit"
    FAMILY_ARRHENIUS_FIT = "family_arrhenius_fit"
    RESIDENCE_TIME_HEURISTIC = "residence_time_heuristic"
    MEASURED_STREAM_BASIS = "measured_stream_basis"
    TEMPLATE_DERIVED = "template_derived"
    PLACEHOLDER_ESTIMATE = "placeholder_estimate"
    SOLVED_BALANCE = "solved_balance"
    FAMILY_PURGE_HEURISTIC = "family_purge_heuristic"
    LIVE_QUOTE = "live_quote"
    SITE_TARIFF = "site_tariff"
    MODEL_DERIVED = "model_derived"


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


class ReportParityStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


class ReportAcceptanceStatus(str, Enum):
    COMPLETE = "complete"
    CONDITIONAL = "conditional"
    BLOCKED = "blocked"


class DiagramLevel(str, Enum):
    BFD = "bfd"
    PFD = "pfd"
    CONTROL = "control"
    PID_LITE = "pid_lite"


class DiagramSymbolPolicy(str, Enum):
    BLOCK_ONLY = "block_only"
    PROCESS_ONLY = "process_only"
    CONTROL_ONLY = "control_only"
    PID_LITE_ONLY = "pid_lite_only"


class DiagramEntityKind(str, Enum):
    SECTION = "section"
    UNIT = "unit"
    STREAM_TERMINAL = "stream_terminal"
    UTILITY_NODE = "utility_node"
    CONTROL_LOOP = "control_loop"
    INSTRUMENT = "instrument"
    VALVE = "valve"
    ANNOTATION = "annotation"


class DiagramEdgeRole(str, Enum):
    PROCESS = "process"
    PRODUCT = "product"
    RECYCLE = "recycle"
    PURGE = "purge"
    VENT = "vent"
    WASTE = "waste"
    UTILITY = "utility"
    CONTROL_SIGNAL = "control_signal"
    SAFEGUARD = "safeguard"
    CONTINUATION = "continuation"


class DiagramPortSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class DiagramSymbolShape(str, Enum):
    RECT = "rect"
    ROUNDED_RECT = "rounded_rect"
    VESSEL = "vessel"
    COLUMN = "column"
    EXCHANGER = "exchanger"
    PUMP = "pump"
    TERMINAL = "terminal"
    DIAMOND = "diamond"
    INSTRUMENT_BUBBLE = "instrument_bubble"
    VALVE = "valve"
    CONNECTOR = "connector"


class DiagramLinePattern(str, Enum):
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


class RunStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"


class ClaimStatus(str, Enum):
    RESOLVED = "resolved"
    PARTIAL = "partial"
    INVALID = "invalid"
    BLOCKED = "blocked"


class ScientificClaimProvenance(str, Enum):
    SOURCED = "sourced"
    CALCULATED = "calculated"
    METHOD_DERIVED = "method_derived"
    ENVELOPE_MODEL = "envelope_model"


class ScientificGateStatus(str, Enum):
    PASS = "pass"
    SCREENING_ONLY = "screening_only"
    FAIL = "fail"


class ScientificConfidence(str, Enum):
    DETAILED = "detailed"
    METHOD_DERIVED = "method_derived"
    SCREENING = "screening"
    BLOCKED = "blocked"


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


class RealDataMode(str, Enum):
    AUDIT = "audit"
    ENFORCE_CRITICAL = "enforce_critical"
    STRICT = "strict"


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
    throughput_basis: Literal["finished_product", "active_component"] = "finished_product"
    nominal_active_wt_pct: Optional[float] = None
    product_form: str = ""
    carrier_components: list[str] = Field(default_factory=list)
    homolog_distribution: dict[str, float] = Field(default_factory=dict)
    quality_targets: list[str] = Field(default_factory=list)


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
    real_data_mode: RealDataMode = RealDataMode.AUDIT
    minimum_real_data_fraction: float = 0.75
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


class CriticFinding(ProvenancedModel):
    finding_id: str
    stage_id: str
    critic_family: str
    severity: Severity
    code: str
    message: str
    artifact_ref: Optional[str] = None
    recommended_action: str = ""
    source_issue_codes: list[str] = Field(default_factory=list)


class CriticRegistryArtifact(ProvenancedModel):
    findings: list[CriticFinding] = Field(default_factory=list)
    warning_count: int = 0
    blocked_count: int = 0
    markdown: str = ""


class PropertyGapArtifact(ProvenancedModel):
    values: list[ValueRecord] = Field(default_factory=list)
    assumptions_log: list[AssumptionRecord] = Field(default_factory=list)
    unresolved_high_sensitivity: list[str] = Field(default_factory=list)
    markdown: str


class ProcessSynthesisArtifact(ProvenancedModel):
    operating_mode_decision: DecisionRecord
    route_candidates: list[AlternativeOption] = Field(default_factory=list)
    archetype: Optional["ProcessArchetype"] = None
    family_adapter: Optional["ChemistryFamilyAdapter"] = None
    alternative_sets: list[AlternativeSet] = Field(default_factory=list)
    unit_train_candidate_ids: list[str] = Field(default_factory=list)
    markdown: str


class OperationsPlanningArtifact(ProvenancedModel):
    planning_id: str
    service_family: str
    recommended_operating_mode: str
    availability_policy_label: str
    raw_material_buffer_days: float
    finished_goods_buffer_days: float
    operating_stock_days: float
    restart_buffer_days: float
    startup_ramp_days: float
    campaign_length_days: float
    cleaning_cycle_days: float
    cleaning_downtime_days: float
    turnaround_buffer_factor: float
    throughput_loss_fraction: float
    restart_loss_fraction: float
    annual_restart_loss_kg: float = 0.0
    buffer_basis_note: str = ""
    markdown: str = ""
    calc_traces: list["CalcTrace"] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class MethodSelectionArtifact(ProvenancedModel):
    method_family: Literal["thermo", "kinetics"]
    decision: DecisionRecord
    markdown: str


class RoughAlternativeCase(ProvenancedModel):
    candidate_id: str
    route_id: str
    route_name: str
    route_family_id: str = ""
    route_family_label: str = ""
    operating_mode: str
    reactor_class: str
    separation_train: str
    heat_recovery_style: str = ""
    blueprint_step_count: int = 0
    separation_duty_count: int = 0
    recycle_intent_count: int = 0
    batch_capable: bool = False
    estimated_heating_kw: float
    estimated_cooling_kw: float
    estimated_capex_inr: float
    estimated_annual_utility_cost_inr: float
    estimated_annual_total_opex_inr: float
    critic_flags: list[str] = Field(default_factory=list)
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
    route_origin: Literal["seeded", "document", "hybrid", "generated"] = "seeded"
    route_evidence_basis: Literal["seeded_benchmark", "document_derived", "cited_technical", "cited_patent", "mixed_cited", "generated"] = "seeded_benchmark"
    source_document_id: Optional[str] = None
    evidence_score: float = 0.0
    chemistry_completeness_score: float = 0.0
    separation_complexity_score: float = 0.0
    route_rejection_reasons: list[str] = Field(default_factory=list)
    extracted_species: list[str] = Field(default_factory=list)
    reaction_family_hints: list[str] = Field(default_factory=list)
    core_species_complete: bool = True
    catalysts: list[str] = Field(default_factory=list)
    solvents: list[str] = Field(default_factory=list)
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


class RouteFamilyProfile(ProvenancedModel):
    route_id: str
    route_family_id: str
    family_label: str
    dominant_phase_pattern: str
    primary_reactor_class: str
    primary_separation_train: str
    heat_recovery_style: str
    maturity_score: float = 0.0
    india_fit_score: float = 0.0
    utility_intensity_factor: float = 1.0
    capex_intensity_factor: float = 1.0
    operability_score: float = 75.0
    data_anchor_requirements: list[str] = Field(default_factory=list)
    critic_flags: list[str] = Field(default_factory=list)
    route_descriptors: list[str] = Field(default_factory=list)
    india_deployment_blocker: str = ""
    markdown: str = ""


class RouteFamilyArtifact(ProvenancedModel):
    profiles: list[RouteFamilyProfile] = Field(default_factory=list)
    markdown: str = ""


class UnitOperationFamilyCandidate(ProvenancedModel):
    candidate_id: str
    service_group: Literal["reactor", "separation", "support"]
    family_label: str
    description: str
    applicability_score: float = 0.0
    applicability_status: Literal["preferred", "fallback", "blocked"] = "fallback"
    rationale: str = ""
    critic_flags: list[str] = Field(default_factory=list)


class UnitOperationFamilyArtifact(ProvenancedModel):
    route_id: str
    route_family_id: str
    route_family_label: str = ""
    dominant_phase_pattern: str = ""
    reactor_candidates: list[UnitOperationFamilyCandidate] = Field(default_factory=list)
    separation_candidates: list[UnitOperationFamilyCandidate] = Field(default_factory=list)
    supporting_unit_operations: list[str] = Field(default_factory=list)
    applicability_critics: list[str] = Field(default_factory=list)
    markdown: str = ""


class ReactionExtent(ProvenancedModel):
    extent_id: str
    reaction_label: str
    kind: Literal["main", "side", "byproduct"]
    representative_component: str = ""
    representative_formula: Optional[str] = None
    representative_molecular_weight_g_mol: float = 0.0
    representative_phase: str = ""
    extent_fraction_of_converted_feed: float = 0.0
    status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class ReactionExtentSet(ProvenancedModel):
    route_id: str
    extents: list[ReactionExtent] = Field(default_factory=list)
    unallocated_selectivity_fraction: float = 0.0
    closure_status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class ByproductEstimate(ProvenancedModel):
    estimate_id: str
    component_name: str
    formula: Optional[str] = None
    molecular_weight_g_mol: float
    phase: str = ""
    allocation_fraction: float = 0.0
    basis: str
    provenance: Literal["explicit_participant", "declared_trace", "family_surrogate"] = "declared_trace"
    status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class ByproductClosure(ProvenancedModel):
    route_id: str
    declared_byproducts: list[str] = Field(default_factory=list)
    explicit_byproduct_components: list[str] = Field(default_factory=list)
    estimates: list[ByproductEstimate] = Field(default_factory=list)
    unresolved_byproducts: list[str] = Field(default_factory=list)
    selectivity_gap_fraction: float = 0.0
    closure_status: Literal["converged", "estimated", "blocked"] = "estimated"
    blocking: bool = False
    notes: list[str] = Field(default_factory=list)


class BACImpurityItem(ProvenancedModel):
    impurity_id: str
    name: str
    impurity_class: str
    origin_section: str = ""
    control_section: str = ""
    fate: str = ""
    estimated_mass_flow_kg_hr: float = 0.0
    estimated_mass_fraction: float = 0.0
    severity: str = "moderate"
    status: Literal["estimated", "method_derived", "blocked"] = "estimated"


class BACImpurityModelArtifact(ProvenancedModel):
    route_id: str = ""
    selected_route_name: str = ""
    product_basis_active_fraction: float = 1.0
    items: list[BACImpurityItem] = Field(default_factory=list)
    product_quality_targets: list[str] = Field(default_factory=list)
    unresolved_impurity_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


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
    stream_role: Literal["feed", "intermediate", "recycle", "purge", "product", "waste", "side_draw", "vent"] = "intermediate"
    section_id: str = ""


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
    composition_states: list["UnitCompositionState"] = Field(default_factory=list)
    composition_closures: list["CompositionClosure"] = Field(default_factory=list)
    unit_operation_packets: list["UnitOperationPacket"] = Field(default_factory=list)
    phase_split_specs: list["PhaseSplitSpec"] = Field(default_factory=list)
    separator_performances: list["SeparatorPerformance"] = Field(default_factory=list)
    separation_packets: list["SeparationPacket"] = Field(default_factory=list)
    recycle_packets: list["RecyclePacket"] = Field(default_factory=list)
    convergence_summaries: list["ConvergenceSummary"] = Field(default_factory=list)
    sections: list["FlowsheetSection"] = Field(default_factory=list)


class StreamSpec(ProvenancedModel):
    stream_id: str
    source_unit_id: Optional[str] = None
    destination_unit_id: Optional[str] = None
    phase_hint: str = ""
    stream_role: Literal["feed", "intermediate", "recycle", "purge", "product", "waste", "side_draw", "vent"] = "intermediate"
    section_id: str = ""
    total_mass_flow_kg_hr: float = 0.0
    total_molar_flow_kmol_hr: float = 0.0
    component_names: list[str] = Field(default_factory=list)


class UnitCompositionState(ProvenancedModel):
    state_id: str
    unit_id: str
    unit_type: str
    inlet_stream_ids: list[str] = Field(default_factory=list)
    outlet_stream_ids: list[str] = Field(default_factory=list)
    inlet_component_molar_kmol_hr: dict[str, float] = Field(default_factory=dict)
    outlet_component_molar_kmol_hr: dict[str, float] = Field(default_factory=dict)
    inlet_component_mass_kg_hr: dict[str, float] = Field(default_factory=dict)
    outlet_component_mass_kg_hr: dict[str, float] = Field(default_factory=dict)
    inlet_component_mole_fraction: dict[str, float] = Field(default_factory=dict)
    outlet_component_mole_fraction: dict[str, float] = Field(default_factory=dict)
    inlet_component_mass_fraction: dict[str, float] = Field(default_factory=dict)
    outlet_component_mass_fraction: dict[str, float] = Field(default_factory=dict)
    dominant_inlet_phase: str = ""
    dominant_outlet_phase: str = ""
    status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class CompositionClosure(ProvenancedModel):
    closure_id: str
    unit_id: str
    reactive: bool = False
    inlet_fraction_sum: float = 0.0
    outlet_fraction_sum: float = 0.0
    new_outlet_components: list[str] = Field(default_factory=list)
    missing_outlet_components: list[str] = Field(default_factory=list)
    composition_error_pct: float = 0.0
    closure_status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


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
    coverage_status: Literal["complete", "partial", "blocked"] = "complete"
    missing_source_stream_ids: list[str] = Field(default_factory=list)
    missing_destination_stream_ids: list[str] = Field(default_factory=list)
    status: Literal["converged", "estimated", "blocked"] = "estimated"
    unresolved_sensitivities: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PhaseSplitSpec(ProvenancedModel):
    spec_id: str
    unit_id: str
    separation_family: str
    split_basis: str
    mechanism: str
    inlet_phases: list[str] = Field(default_factory=list)
    product_phase_target: str = ""
    waste_phase_target: str = ""
    recycle_phase_target: str = ""
    side_draw_phase_target: str = ""
    equilibrium_model: str = ""
    equilibrium_parameter_ids: list[str] = Field(default_factory=list)
    equilibrium_fallback: bool = False
    section_thermo_artifact_id: str = ""
    activity_model: str = ""
    light_key: str = ""
    heavy_key: str = ""
    top_relative_volatility: float = 0.0
    bottom_relative_volatility: float = 0.0
    average_relative_volatility: float = 0.0
    phase_split_status: Literal["complete", "partial", "blocked"] = "partial"
    notes: list[str] = Field(default_factory=list)


class SeparatorPerformance(ProvenancedModel):
    performance_id: str
    unit_id: str
    separation_family: str
    inlet_stream_ids: list[str] = Field(default_factory=list)
    product_stream_ids: list[str] = Field(default_factory=list)
    waste_stream_ids: list[str] = Field(default_factory=list)
    recycle_stream_ids: list[str] = Field(default_factory=list)
    side_draw_stream_ids: list[str] = Field(default_factory=list)
    component_split_to_product: dict[str, float] = Field(default_factory=dict)
    component_split_to_waste: dict[str, float] = Field(default_factory=dict)
    component_split_to_recycle: dict[str, float] = Field(default_factory=dict)
    component_split_to_side_draw: dict[str, float] = Field(default_factory=dict)
    dominant_product_phase: str = ""
    dominant_waste_phase: str = ""
    dominant_recycle_phase: str = ""
    product_mass_fraction: float = 0.0
    waste_mass_fraction: float = 0.0
    recycle_mass_fraction: float = 0.0
    side_draw_mass_fraction: float = 0.0
    split_closure_pct: float = 0.0
    equilibrium_model: str = ""
    equilibrium_parameter_ids: list[str] = Field(default_factory=list)
    equilibrium_fallback: bool = False
    section_thermo_artifact_id: str = ""
    activity_model: str = ""
    light_key: str = ""
    heavy_key: str = ""
    top_relative_volatility: float = 0.0
    bottom_relative_volatility: float = 0.0
    average_relative_volatility: float = 0.0
    performance_status: Literal["converged", "estimated", "blocked"] = "estimated"
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
    phase_split_spec_id: str = ""
    separator_performance_id: str = ""
    split_basis: str = ""
    component_split_to_product: dict[str, float] = Field(default_factory=dict)
    component_split_to_waste: dict[str, float] = Field(default_factory=dict)
    component_split_to_recycle: dict[str, float] = Field(default_factory=dict)
    component_split_to_side_draw: dict[str, float] = Field(default_factory=dict)
    dominant_product_phase: str = ""
    dominant_waste_phase: str = ""
    dominant_recycle_phase: str = ""
    product_mass_fraction: float = 0.0
    waste_mass_fraction: float = 0.0
    recycle_mass_fraction: float = 0.0
    side_draw_mass_fraction: float = 0.0
    split_closure_pct: float = 0.0
    equilibrium_model: str = ""
    equilibrium_parameter_ids: list[str] = Field(default_factory=list)
    equilibrium_fallback: bool = False
    section_thermo_artifact_id: str = ""
    activity_model: str = ""
    light_key: str = ""
    heavy_key: str = ""
    top_relative_volatility: float = 0.0
    bottom_relative_volatility: float = 0.0
    average_relative_volatility: float = 0.0
    split_status: Literal["converged", "estimated", "blocked"] = "estimated"
    closure_error_pct: float = 0.0
    notes: list[str] = Field(default_factory=list)


class ConvergenceSummary(ProvenancedModel):
    summary_id: str
    loop_id: str
    recycle_source_unit_id: Optional[str] = None
    recycle_target_unit_id: Optional[str] = None
    source_section_id: str = ""
    target_section_id: str = ""
    recycle_stream_ids: list[str] = Field(default_factory=list)
    purge_stream_ids: list[str] = Field(default_factory=list)
    component_count: int = 0
    converged_components: list[str] = Field(default_factory=list)
    estimated_components: list[str] = Field(default_factory=list)
    blocked_components: list[str] = Field(default_factory=list)
    max_component_error_pct: float = 0.0
    mean_component_error_pct: float = 0.0
    max_iterations: int = 0
    purge_policy_by_family: dict[str, float] = Field(default_factory=dict)
    impurity_family_components: dict[str, list[str]] = Field(default_factory=dict)
    convergence_status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class RecyclePacket(ProvenancedModel):
    packet_id: str
    loop_id: str
    recycle_source_unit_id: Optional[str] = None
    recycle_target_unit_id: Optional[str] = None
    source_section_id: str = ""
    target_section_id: str = ""
    recycle_stream_ids: list[str] = Field(default_factory=list)
    purge_stream_ids: list[str] = Field(default_factory=list)
    component_targets_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_fresh_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_recycle_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_purge_kmol_hr: dict[str, float] = Field(default_factory=dict)
    component_convergence_error_pct: dict[str, float] = Field(default_factory=dict)
    component_iterations: dict[str, int] = Field(default_factory=dict)
    purge_policy_by_family: dict[str, float] = Field(default_factory=dict)
    impurity_family_components: dict[str, list[str]] = Field(default_factory=dict)
    convergence_summary_id: str = ""
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
    coverage_status: Literal["complete", "partial", "blocked"] = "complete"
    missing_source_stream_ids: list[str] = Field(default_factory=list)
    missing_destination_stream_ids: list[str] = Field(default_factory=list)
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
    phase_split_spec_id: str = ""
    separator_performance_id: str = ""
    split_basis: str = ""
    component_split_to_product: dict[str, float] = Field(default_factory=dict)
    component_split_to_waste: dict[str, float] = Field(default_factory=dict)
    component_split_to_recycle: dict[str, float] = Field(default_factory=dict)
    component_split_to_side_draw: dict[str, float] = Field(default_factory=dict)
    dominant_product_phase: str = ""
    dominant_waste_phase: str = ""
    dominant_recycle_phase: str = ""
    product_mass_fraction: float = 0.0
    waste_mass_fraction: float = 0.0
    recycle_mass_fraction: float = 0.0
    side_draw_mass_fraction: float = 0.0
    split_closure_pct: float = 0.0
    split_status: Literal["converged", "estimated", "blocked"] = "estimated"
    closure_error_pct: float = 0.0


class RecycleLoop(ProvenancedModel):
    loop_id: str
    recycle_source_unit_id: Optional[str] = None
    recycle_target_unit_id: Optional[str] = None
    source_section_id: str = ""
    target_section_id: str = ""
    recycle_stream_ids: list[str] = Field(default_factory=list)
    purge_stream_ids: list[str] = Field(default_factory=list)
    component_convergence_error_pct: dict[str, float] = Field(default_factory=dict)
    purge_policy_by_family: dict[str, float] = Field(default_factory=dict)
    impurity_family_components: dict[str, list[str]] = Field(default_factory=dict)
    convergence_summary_id: str = ""
    convergence_status: Literal["converged", "estimated", "blocked"] = "estimated"
    closure_error_pct: float = 0.0
    max_iterations: int = 0


class FlowsheetSection(ProvenancedModel):
    section_id: str
    section_type: str
    label: str
    sequence_index: int
    unit_ids: list[str] = Field(default_factory=list)
    inlet_stream_ids: list[str] = Field(default_factory=list)
    outlet_stream_ids: list[str] = Field(default_factory=list)
    side_draw_stream_ids: list[str] = Field(default_factory=list)
    recycle_loop_ids: list[str] = Field(default_factory=list)
    status: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class FlowsheetCase(ProvenancedModel):
    case_id: str
    route_id: str
    operating_mode: str
    units: list[UnitSpec] = Field(default_factory=list)
    streams: list[StreamSpec] = Field(default_factory=list)
    composition_states: list[UnitCompositionState] = Field(default_factory=list)
    composition_closures: list[CompositionClosure] = Field(default_factory=list)
    separations: list[SeparationSpec] = Field(default_factory=list)
    recycle_loops: list[RecycleLoop] = Field(default_factory=list)
    convergence_summaries: list[ConvergenceSummary] = Field(default_factory=list)
    unit_operation_packets: list[UnitOperationPacket] = Field(default_factory=list)
    sections: list[FlowsheetSection] = Field(default_factory=list)
    markdown: str = ""


class SolveResult(ProvenancedModel):
    case_id: str
    convergence_status: Literal["converged", "estimated", "blocked"] = "estimated"
    overall_closure_error_pct: float = 0.0
    unitwise_closure: dict[str, float] = Field(default_factory=dict)
    unitwise_status: dict[str, Literal["converged", "estimated", "blocked"]] = Field(default_factory=dict)
    unitwise_coverage_status: dict[str, Literal["complete", "partial", "blocked"]] = Field(default_factory=dict)
    unitwise_blockers: dict[str, list[str]] = Field(default_factory=dict)
    unitwise_unresolved_sensitivities: dict[str, list[str]] = Field(default_factory=dict)
    section_status: dict[str, Literal["converged", "estimated", "blocked"]] = Field(default_factory=dict)
    composition_status: dict[str, Literal["converged", "estimated", "blocked"]] = Field(default_factory=dict)
    separation_status: dict[str, Literal["converged", "estimated", "blocked"]] = Field(default_factory=dict)
    recycle_status: dict[str, Literal["converged", "estimated", "blocked"]] = Field(default_factory=dict)
    convergence_summaries: list[ConvergenceSummary] = Field(default_factory=list)
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
    reaction_extent_set: Optional[ReactionExtentSet] = None
    byproduct_closure: Optional[ByproductClosure] = None
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
    phase_regime: str = ""
    residence_time_hr: float
    liquid_holdup_m3: float
    design_volume_m3: float
    design_temperature_c: float
    design_pressure_bar: float
    design_conversion_fraction: float = 0.0
    kinetic_rate_constant_1_hr: float = 0.0
    kinetic_space_time_hr: float = 0.0
    kinetic_damkohler_number: float = 0.0
    heat_duty_kw: float
    heat_release_density_kw_m3: float = 0.0
    adiabatic_temperature_rise_c: float = 0.0
    heat_removal_capacity_kw: float = 0.0
    heat_removal_margin_fraction: float = 0.0
    thermal_stability_score: float = 0.0
    runaway_risk_label: str = ""
    heat_transfer_area_m2: float
    shell_diameter_m: float = 0.0
    shell_length_m: float = 0.0
    overall_u_w_m2_k: float = 0.0
    reynolds_number: float = 0.0
    prandtl_number: float = 0.0
    nusselt_number: float = 0.0
    catalyst_name: str = ""
    catalyst_inventory_kg: float = 0.0
    catalyst_cycle_days: float = 0.0
    catalyst_regeneration_days: float = 0.0
    catalyst_void_fraction: float = 0.0
    catalyst_weight_hourly_space_velocity_1_hr: float = 0.0
    number_of_tubes: int = 0
    tube_length_m: float = 0.0
    cooling_medium: str = ""
    utility_topology: str = ""
    utility_architecture_family: str = ""
    integrated_thermal_duty_kw: float = 0.0
    residual_utility_duty_kw: float = 0.0
    integrated_lmtd_k: float = 0.0
    integrated_exchange_area_m2: float = 0.0
    allocated_recovered_duty_target_kw: float = 0.0
    coupled_service_basis: str = ""
    selected_utility_island_ids: list[str] = Field(default_factory=list)
    selected_utility_header_levels: list[int] = Field(default_factory=list)
    selected_utility_cluster_ids: list[str] = Field(default_factory=list)
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
    theoretical_stages: float = 0.0
    design_stages: int
    tray_efficiency: float = 0.0
    minimum_reflux_ratio: float = 0.0
    reflux_ratio: float
    reflux_ratio_multiple_of_min: float = 0.0
    column_diameter_m: float
    column_height_m: float
    condenser_duty_kw: float
    reboiler_duty_kw: float
    vapor_load_kg_hr: float = 0.0
    liquid_load_m3_hr: float = 0.0
    vapor_density_kg_m3: float = 0.0
    liquid_density_kg_m3: float = 0.0
    feed_stage: int = 0
    tray_spacing_m: float = 0.0
    flooding_fraction: float = 0.0
    downcomer_area_fraction: float = 0.0
    allowable_vapor_velocity_m_s: float = 0.0
    superficial_vapor_velocity_m_s: float = 0.0
    pressure_drop_per_stage_kpa: float = 0.0
    top_temperature_c: float = 0.0
    bottom_temperature_c: float = 0.0
    feed_quality_q_factor: float = 0.0
    murphree_efficiency: float = 0.0
    top_relative_volatility: float = 0.0
    bottom_relative_volatility: float = 0.0
    rectifying_theoretical_stages: float = 0.0
    stripping_theoretical_stages: float = 0.0
    rectifying_vapor_load_kg_hr: float = 0.0
    stripping_vapor_load_kg_hr: float = 0.0
    rectifying_liquid_load_m3_hr: float = 0.0
    stripping_liquid_load_m3_hr: float = 0.0
    utility_topology: str = ""
    utility_architecture_family: str = ""
    integrated_reboiler_duty_kw: float = 0.0
    residual_reboiler_utility_kw: float = 0.0
    integrated_reboiler_lmtd_k: float = 0.0
    integrated_reboiler_area_m2: float = 0.0
    allocated_reboiler_recovery_target_kw: float = 0.0
    reboiler_medium: str = ""
    reboiler_package_type: str = ""
    reboiler_circulation_ratio: float = 0.0
    reboiler_phase_change_load_kg_hr: float = 0.0
    reboiler_package_item_ids: list[str] = Field(default_factory=list)
    condenser_recovery_duty_kw: float = 0.0
    condenser_recovery_lmtd_k: float = 0.0
    condenser_recovery_area_m2: float = 0.0
    allocated_condenser_recovery_target_kw: float = 0.0
    condenser_recovery_medium: str = ""
    condenser_package_type: str = ""
    condenser_phase_change_load_kg_hr: float = 0.0
    condenser_circulation_flow_m3_hr: float = 0.0
    condenser_package_item_ids: list[str] = Field(default_factory=list)
    selected_utility_island_ids: list[str] = Field(default_factory=list)
    selected_utility_header_levels: list[int] = Field(default_factory=list)
    selected_utility_cluster_ids: list[str] = Field(default_factory=list)
    equilibrium_model: str = ""
    equilibrium_parameter_ids: list[str] = Field(default_factory=list)
    equilibrium_fallback: bool = False
    absorber_key_component: str = ""
    absorber_henry_constant_bar: float = 0.0
    absorber_equilibrium_slope: float = 0.0
    absorber_solvent_to_gas_ratio: float = 0.0
    absorber_minimum_solvent_to_gas_ratio: float = 0.0
    absorber_optimized_solvent_to_gas_ratio: float = 0.0
    absorber_lean_loading_mol_mol: float = 0.0
    absorber_rich_loading_mol_mol: float = 0.0
    absorber_solvent_rate_case_count: int = 0
    absorber_capture_fraction: float = 0.0
    absorber_stage_efficiency: float = 0.0
    absorber_theoretical_stages: float = 0.0
    absorber_packed_height_m: float = 0.0
    absorber_gas_mass_velocity_kg_m2_s: float = 0.0
    absorber_liquid_mass_velocity_kg_m2_s: float = 0.0
    absorber_ntu: float = 0.0
    absorber_htu_m: float = 0.0
    absorber_overall_mass_transfer_coefficient_1_s: float = 0.0
    absorber_packing_family: str = ""
    absorber_packing_specific_area_m2_m3: float = 0.0
    absorber_effective_interfacial_area_m2_m3: float = 0.0
    absorber_gas_phase_transfer_coeff_1_s: float = 0.0
    absorber_liquid_phase_transfer_coeff_1_s: float = 0.0
    absorber_min_wetting_rate_kg_m2_s: float = 0.0
    absorber_wetting_ratio: float = 0.0
    absorber_operating_velocity_m_s: float = 0.0
    absorber_flooding_velocity_m_s: float = 0.0
    absorber_flooding_margin_fraction: float = 0.0
    absorber_pressure_drop_per_m_kpa_m: float = 0.0
    absorber_total_pressure_drop_kpa: float = 0.0
    crystallizer_key_component: str = ""
    crystallizer_solubility_limit_kg_per_kg: float = 0.0
    crystallizer_feed_loading_kg_per_kg: float = 0.0
    crystallizer_supersaturation_ratio: float = 0.0
    crystallizer_precipitated_mass_kg_hr: float = 0.0
    crystallizer_dissolved_mass_kg_hr: float = 0.0
    crystallizer_yield_fraction: float = 0.0
    crystallizer_residence_time_hr: float = 0.0
    crystallizer_holdup_m3: float = 0.0
    crystal_slurry_density_kg_m3: float = 0.0
    crystal_growth_rate_mm_hr: float = 0.0
    crystal_size_d10_mm: float = 0.0
    crystal_size_d50_mm: float = 0.0
    crystal_size_d90_mm: float = 0.0
    crystal_classifier_cut_size_mm: float = 0.0
    crystal_classified_product_fraction: float = 0.0
    slurry_circulation_rate_m3_hr: float = 0.0
    filter_cake_moisture_fraction: float = 0.0
    filter_area_m2: float = 0.0
    filter_cake_throughput_kg_m2_hr: float = 0.0
    filter_specific_cake_resistance_m_kg: float = 0.0
    filter_medium_resistance_1_m: float = 0.0
    filter_cycle_time_hr: float = 0.0
    filter_cake_formation_time_hr: float = 0.0
    filter_wash_time_hr: float = 0.0
    filter_discharge_time_hr: float = 0.0
    filter_cycles_per_hr: float = 0.0
    dryer_evaporation_load_kg_hr: float = 0.0
    dryer_residence_time_hr: float = 0.0
    dryer_target_moisture_fraction: float = 0.0
    dryer_product_moisture_fraction: float = 0.0
    dryer_equilibrium_moisture_fraction: float = 0.0
    dryer_endpoint_margin_fraction: float = 0.0
    dryer_inlet_humidity_ratio_kg_kg: float = 0.0
    dryer_exhaust_humidity_ratio_kg_kg: float = 0.0
    dryer_humidity_lift_kg_kg: float = 0.0
    dryer_exhaust_dewpoint_c: float = 0.0
    dryer_dry_air_flow_kg_hr: float = 0.0
    dryer_exhaust_saturation_fraction: float = 0.0
    dryer_mass_transfer_coefficient_kg_m2_s: float = 0.0
    dryer_heat_transfer_coefficient_w_m2_k: float = 0.0
    dryer_heat_transfer_area_m2: float = 0.0
    dryer_refined_duty_kw: float = 0.0
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
    capacity_factor_m_s: float = 0.0
    allowable_vapor_velocity_m_s: float = 0.0
    active_area_m2: float = 0.0
    pressure_drop_per_stage_kpa: float = 0.0
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
    package_family: str = ""
    circulation_flow_m3_hr: float = 0.0
    phase_change_load_kg_hr: float = 0.0
    package_holdup_m3: float = 0.0
    boiling_side_coefficient_w_m2_k: float = 0.0
    condensing_side_coefficient_w_m2_k: float = 0.0
    utility_topology: str = ""
    utility_architecture_family: str = ""
    selected_island_id: Optional[str] = None
    selected_header_level: int = 0
    selected_cluster_id: Optional[str] = None
    allocated_recovered_duty_target_kw: float = 0.0
    selected_train_step_id: Optional[str] = None
    selected_package_item_ids: list[str] = Field(default_factory=list)
    selected_package_roles: list[str] = Field(default_factory=list)
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class HeatExchangerThermalDesign(ProvenancedModel):
    exchanger_id: str
    selected_configuration: str
    governing_equations: list[str] = Field(default_factory=list)
    thermal_inputs: dict[str, str] = Field(default_factory=dict)
    package_basis: dict[str, str] = Field(default_factory=dict)
    markdown: str = ""


class StorageDesign(ProvenancedModel):
    storage_id: str
    service: str
    inventory_days: float
    working_volume_m3: float
    total_volume_m3: float
    material_of_construction: str
    operating_stock_days: float = 0.0
    dispatch_buffer_days: float = 0.0
    restart_buffer_days: float = 0.0
    turnaround_buffer_factor: float = 1.0
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
    allowable_stress_mpa: float = 0.0
    joint_efficiency: float = 0.0
    corrosion_allowance_mm: float
    shell_thickness_mm: float
    head_thickness_mm: float = 0.0
    nozzle_diameter_mm: float = 0.0
    support_type: str = ""
    support_variant: str = ""
    support_thickness_mm: float = 0.0
    operating_load_kn: float = 0.0
    thermal_growth_mm: float = 0.0
    nozzle_reinforcement_area_mm2: float = 0.0
    support_load_case: str = ""
    pressure_class: str = ""
    hydrotest_pressure_bar: float = 0.0
    design_vertical_load_kn: float = 0.0
    piping_load_kn: float = 0.0
    wind_load_kn: float = 0.0
    seismic_load_kn: float = 0.0
    maintenance_platform_required: bool = False
    platform_area_m2: float = 0.0
    pipe_rack_tie_in_required: bool = False
    anchor_group_count: int = 0
    foundation_footprint_m2: float = 0.0
    maintenance_clearance_m: float = 0.0
    access_ladder_required: bool = False
    lifting_lug_required: bool = False
    nozzle_reinforcement_family: str = ""
    local_shell_load_interaction_factor: float = 0.0
    notes: str = ""
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class MechanicalDesignBasis(ProvenancedModel):
    basis_id: str
    code_basis: str
    design_pressure_basis: str
    design_temperature_basis: str
    corrosion_allowance_mm: float
    support_design_basis: str = ""
    load_case_basis: str = ""
    connection_rating_basis: str = ""
    access_platform_basis: str = ""
    foundation_basis: str = ""
    nozzle_load_basis: str = ""
    markdown: str = ""


class SupportDesign(ProvenancedModel):
    equipment_id: str
    support_type: str
    support_variant: str = ""
    support_load_basis_kn: float
    support_load_case: str = ""
    support_thickness_mm: float
    operating_load_kn: float = 0.0
    design_vertical_load_kn: float = 0.0
    piping_load_kn: float = 0.0
    wind_load_kn: float = 0.0
    seismic_load_kn: float = 0.0
    overturning_moment_kn_m: float = 0.0
    thermal_growth_mm: float = 0.0
    anchor_bolt_diameter_mm: float = 0.0
    base_plate_thickness_mm: float = 0.0
    maintenance_platform_required: bool = False
    platform_area_m2: float = 0.0
    pipe_rack_tie_in_required: bool = False
    anchor_group_count: int = 0
    foundation_footprint_m2: float = 0.0
    maintenance_clearance_m: float = 0.0
    access_ladder_required: bool = False
    lifting_lug_required: bool = False
    foundation_note: str = ""
    markdown: str = ""


class NozzleSchedule(ProvenancedModel):
    equipment_id: str
    nozzle_count: int
    nozzle_diameters_mm: list[float] = Field(default_factory=list)
    nozzle_services: list[str] = Field(default_factory=list)
    reinforcement_area_mm2: list[float] = Field(default_factory=list)
    nozzle_pressure_class: str = ""
    nozzle_orientations_deg: list[float] = Field(default_factory=list)
    nozzle_connection_classes: list[str] = Field(default_factory=list)
    nozzle_load_cases_kn: list[float] = Field(default_factory=list)
    nozzle_reinforcement_family: str = ""
    nozzle_projection_mm: list[float] = Field(default_factory=list)
    local_shell_load_factors: list[float] = Field(default_factory=list)
    markdown: str = ""


class VesselMechanicalDesign(ProvenancedModel):
    equipment_id: str
    shell_thickness_mm: float
    head_thickness_mm: float
    corrosion_allowance_mm: float
    hydrotest_pressure_bar: float = 0.0
    pressure_class: str = ""
    access_platform_required: bool = False
    support_variant: str = ""
    anchor_group_count: int = 0
    foundation_footprint_m2: float = 0.0
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
    procurement_package_family: str = ""
    procurement_lead_time_months: float = 0.0
    procurement_award_month: float = 0.0
    procurement_delivery_month: float = 0.0
    import_content_fraction: float = 0.0
    import_duty_fraction: float = 0.0
    import_duty_inr: float = 0.0
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


class HeatCompositeInterval(ProvenancedModel):
    interval_id: str
    upper_temp_c: float
    lower_temp_c: float
    shifted_upper_temp_c: float
    shifted_lower_temp_c: float
    hot_duty_kw: float
    cold_duty_kw: float
    net_duty_kw: float
    notes: str = ""


class HeatUtilityIsland(ProvenancedModel):
    island_id: str
    topology: str
    architecture_role: str = "generic"
    header_level: int = 0
    cluster_id: Optional[str] = None
    hot_stream_ids: list[str] = Field(default_factory=list)
    cold_stream_ids: list[str] = Field(default_factory=list)
    unit_ids: list[str] = Field(default_factory=list)
    match_ids: list[str] = Field(default_factory=list)
    train_step_ids: list[str] = Field(default_factory=list)
    candidate_match_count: int = 0
    recoverable_potential_kw: float = 0.0
    target_recovered_duty_kw: float = 0.0
    selection_priority: float = 0.0
    shared_htm_inventory_m3: float = 0.0
    header_design_pressure_bar: float = 0.0
    condenser_reboiler_pair_score: float = 0.0
    control_complexity_factor: float = 0.0
    recovered_duty_kw: float
    residual_hot_utility_kw: float
    residual_cold_utility_kw: float
    direct_match_count: int = 0
    indirect_match_count: int = 0
    cross_service: bool = False
    notes: str = ""


class HeatStreamSet(ProvenancedModel):
    route_id: str
    hot_streams: list[HeatStream] = Field(default_factory=list)
    cold_streams: list[HeatStream] = Field(default_factory=list)
    composite_intervals: list[HeatCompositeInterval] = Field(default_factory=list)
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
    base_case_id: Optional[str] = None
    topology: str
    architecture_family: str = "base"
    recovered_duty_kw: float
    residual_hot_utility_kw: float
    residual_cold_utility_kw: float
    exchanger_count: int
    header_count: int = 0
    shared_htm_island_count: int = 0
    condenser_reboiler_cluster_count: int = 0
    selection_score: float = 0.0
    match_candidates: list[HeatMatchCandidate] = Field(default_factory=list)
    selected_matches: list[HeatMatch] = Field(default_factory=list)
    utility_islands: list[HeatUtilityIsland] = Field(default_factory=list)
    selected_train_steps: list["HeatExchangerTrainStep"] = Field(default_factory=list)
    markdown: str = ""


class UtilityTrainPackageItem(ProvenancedModel):
    package_item_id: str
    parent_step_id: str
    island_id: Optional[str] = None
    cluster_id: Optional[str] = None
    header_level: int = 0
    package_role: Literal["exchanger", "circulation", "expansion", "relief", "controls", "header"]
    equipment_id: str
    equipment_type: str
    service: str
    package_family: str = ""
    design_temperature_c: float
    design_pressure_bar: float
    volume_m3: float = 0.0
    duty_kw: float = 0.0
    power_kw: float = 0.0
    flow_m3_hr: float = 0.0
    lmtd_k: float = 0.0
    heat_transfer_area_m2: float = 0.0
    phase_change_load_kg_hr: float = 0.0
    circulation_ratio: float = 0.0
    material_of_construction: str = ""
    notes: str = ""


class HeatExchangerTrainStep(ProvenancedModel):
    step_id: str
    exchanger_id: str
    island_id: Optional[str] = None
    cluster_id: Optional[str] = None
    header_level: int = 0
    topology: str
    service: str
    hot_stream_id: str
    cold_stream_id: str
    source_unit_id: str
    sink_unit_id: str
    recovered_duty_kw: float
    medium: str
    package_items: list[UtilityTrainPackageItem] = Field(default_factory=list)
    notes: str = ""


class HeatNetworkArchitecture(ProvenancedModel):
    route_id: str
    selected_case_id: Optional[str] = None
    heat_stream_set: Optional[HeatStreamSet] = None
    cases: list[HeatNetworkCase] = Field(default_factory=list)
    selected_island_ids: list[str] = Field(default_factory=list)
    selected_train_steps: list[HeatExchangerTrainStep] = Field(default_factory=list)
    selected_package_items: list[UtilityTrainPackageItem] = Field(default_factory=list)
    topology_summary: str = ""
    markdown: str = ""


class ControlLoop(ProvenancedModel):
    control_id: str
    unit_id: str = ""
    loop_family: str = ""
    controlled_variable: str
    manipulated_variable: str
    sensor: str
    actuator: str
    objective: str = ""
    disturbance_basis: str = ""
    startup_logic: str = ""
    shutdown_logic: str = ""
    override_logic: str = ""
    safeguard_linkage: str = ""
    criticality: str = ""
    notes: str


class HazopNode(ProvenancedModel):
    node_id: str
    node_family: str = ""
    design_intent: str = ""
    parameter: str
    guide_word: str
    deviation: str = ""
    causes: list[str]
    consequences: list[str]
    safeguards: list[str]
    linked_control_loops: list[str] = Field(default_factory=list)
    consequence_severity: str = ""
    recommendation_priority: str = ""
    recommendation_status: str = "open"
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
    annual_transport_service_cost_inr: float = 0.0
    annual_utility_island_service_cost_inr: float = 0.0
    annual_utility_island_replacement_cost_inr: float = 0.0
    annual_utility_island_operating_burden_inr: float = 0.0
    annual_packing_replacement_cost_inr: float = 0.0
    annual_classifier_service_cost_inr: float = 0.0
    annual_filter_media_replacement_cost_inr: float = 0.0
    annual_dryer_exhaust_treatment_cost_inr: float = 0.0
    annual_operating_cost_inr: float
    annual_revenue_inr: float
    gross_margin_inr: float
    utility_island_impacts: list["UtilityIslandScenarioImpact"] = Field(default_factory=list)
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


class UtilityIslandEconomicImpact(ProvenancedModel):
    island_id: str
    topology: str
    train_step_count: int = 0
    package_item_count: int = 0
    shared_htm_inventory_m3: float = 0.0
    header_design_pressure_bar: float = 0.0
    condenser_reboiler_pair_score: float = 0.0
    control_complexity_factor: float = 0.0
    recovered_duty_kw: float = 0.0
    recovered_duty_share_fraction: float = 0.0
    utility_cost_share_fraction: float = 0.0
    capex_share_fraction: float = 0.0
    bare_cost_inr: float = 0.0
    installed_cost_inr: float = 0.0
    project_capex_burden_inr: float = 0.0
    annual_allocated_utility_cost_inr: float = 0.0
    annual_service_cost_inr: float = 0.0
    annualized_replacement_cost_inr: float = 0.0
    annual_operating_burden_inr: float = 0.0
    maintenance_cycle_years: float = 0.0
    replacement_event_cost_inr: float = 0.0
    planned_turnaround_days: float = 0.0
    steam_sensitivity_weight: float = 0.0
    power_sensitivity_weight: float = 0.0
    capex_sensitivity_weight: float = 0.0
    notes: str = ""


class UtilityIslandScenarioImpact(ProvenancedModel):
    island_id: str
    scenario_name: str
    project_capex_burden_inr: float = 0.0
    annual_allocated_utility_cost_inr: float = 0.0
    annual_service_cost_inr: float = 0.0
    annual_replacement_cost_inr: float = 0.0
    annual_operating_burden_inr: float = 0.0
    notes: str = ""


class EconomicScenarioModel(ProvenancedModel):
    selected_basis_decision_id: Optional[str] = None
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    markdown: str


class ProcurementPackageImpact(ProvenancedModel):
    package_id: str
    equipment_type: str
    package_family: str
    lead_time_months: float = 0.0
    award_month: float = 0.0
    delivery_month: float = 0.0
    erection_month: float = 0.0
    import_content_fraction: float = 0.0
    import_duty_fraction: float = 0.0
    import_duty_inr: float = 0.0
    capex_burden_inr: float = 0.0
    long_lead: bool = False
    notes: str = ""


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
    annual_transport_service_cost: float = 0.0
    annual_utility_island_service_cost: float = 0.0
    annual_utility_island_replacement_cost: float = 0.0
    annual_packing_replacement_cost: float = 0.0
    annual_classifier_service_cost: float = 0.0
    annual_filter_media_replacement_cost: float = 0.0
    annual_dryer_exhaust_treatment_cost: float = 0.0
    packing_replacement_cycle_years: float = 0.0
    packing_replacement_event_cost: float = 0.0
    availability_policy_label: str = ""
    planned_minor_outage_days_per_year: float = 0.0
    planned_major_turnaround_days: float = 0.0
    startup_loss_days_after_turnaround: float = 0.0
    minor_outage_window_note: str = ""
    major_turnaround_window_note: str = ""
    maintenance_turnaround_cycle_years: int = 0
    maintenance_turnaround_event_cost: float = 0.0
    procurement_profile_label: str = ""
    imported_equipment_fraction: float = 0.0
    long_lead_equipment_fraction: float = 0.0
    construction_months: int = 0
    procurement_advance_fraction: float = 0.0
    procurement_progress_fraction: float = 0.0
    procurement_retention_fraction: float = 0.0
    total_import_duty_inr: float = 0.0
    procurement_schedule: list[dict[str, float | str]] = Field(default_factory=list)
    procurement_package_impacts: list[ProcurementPackageImpact] = Field(default_factory=list)
    annual_overheads: float
    route_site_fit_score: float = 0.0
    route_feedstock_cluster_factor: float = 1.0
    route_logistics_penalty_factor: float = 1.0
    route_batch_penalty_fraction: float = 0.0
    route_solvent_recovery_service_cost_inr: float = 0.0
    route_catalyst_service_cost_inr: float = 0.0
    route_waste_treatment_burden_inr: float = 0.0
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    india_price_data: list[IndianPriceDatum] = Field(default_factory=list)
    selected_route_id: Optional[str] = None
    selected_heat_integration_case_id: Optional[str] = None
    integration_capex_inr: float = 0.0
    utility_island_costs: list[UtilityIslandEconomicImpact] = Field(default_factory=list)
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
    cash_buffer_days: float = 0.0
    operating_stock_days: float = 0.0
    procurement_timing_factor: float = 0.0
    precommissioning_inventory_days: float = 0.0
    precommissioning_inventory_month: float = 0.0
    restart_loss_inventory_inr: float = 0.0
    outage_buffer_inventory_inr: float = 0.0
    precommissioning_inventory_inr: float = 0.0
    raw_material_inventory_inr: float = 0.0
    product_inventory_inr: float = 0.0
    receivables_inr: float = 0.0
    payables_inr: float = 0.0
    cash_buffer_inr: float = 0.0
    peak_working_capital_month: float = 0.0
    peak_working_capital_inr: float = 0.0
    buffer_basis_note: str = ""
    working_capital_inr: float
    calc_traces: list[CalcTrace] = Field(default_factory=list)
    value_records: list[ValueRecord] = Field(default_factory=list)


class FinancialModel(ProvenancedModel):
    currency: str
    annual_revenue: float
    annual_operating_cost: float
    gross_profit: float
    working_capital: float
    peak_working_capital_inr: float = 0.0
    peak_working_capital_month: float = 0.0
    payback_years: float
    npv: float
    irr: float
    profitability_index: float
    break_even_fraction: float
    total_project_funding_inr: float = 0.0
    construction_interest_during_construction_inr: float = 0.0
    minimum_dscr: float = 0.0
    average_dscr: float = 0.0
    llcr: float = 0.0
    plcr: float = 0.0
    selected_financing_candidate_id: str = ""
    selected_financing_description: str = ""
    downside_scenario_name: str = ""
    downside_financing_candidate_id: str = ""
    financing_scenario_reversal: bool = False
    covenant_breach_codes: list[str] = Field(default_factory=list)
    covenant_warnings: list[str] = Field(default_factory=list)
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
    availability_pct: float = 0.0
    minor_outage_days: float = 0.0
    major_turnaround_days: float = 0.0
    startup_loss_days: float = 0.0
    available_operating_days: float = 0.0
    outage_calendar_note: str = ""
    revenue_loss_from_outages_inr: float = 0.0
    capex_draw_inr: float = 0.0
    debt_draw_inr: float = 0.0
    equity_draw_inr: float = 0.0
    idc_inr: float = 0.0
    revenue_inr: float
    operating_cost_inr: float
    raw_material_cost_inr: float = 0.0
    utility_cost_inr: float = 0.0
    labor_cost_inr: float = 0.0
    base_maintenance_inr: float = 0.0
    transport_service_cost_inr: float = 0.0
    utility_island_service_cost_inr: float = 0.0
    utility_island_replacement_cost_inr: float = 0.0
    packing_replacement_cost_inr: float = 0.0
    classifier_service_cost_inr: float = 0.0
    filter_media_replacement_cost_inr: float = 0.0
    dryer_exhaust_treatment_cost_inr: float = 0.0
    turnaround_cost_inr: float = 0.0
    utility_island_turnaround_cost_inr: float = 0.0
    turnaround_flag: bool = False
    principal_repayment_inr: float = 0.0
    debt_service_inr: float = 0.0
    dscr: float = 0.0
    cfads_inr: float = 0.0
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
    stage_revision_counts: dict[str, int] = Field(default_factory=dict)
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


class ReportChapterContract(BaseModel):
    chapter_id: str
    benchmark_title: str
    required_outputs: list[str] = Field(default_factory=list)
    required_markers: list[str] = Field(default_factory=list)
    requires_citations: bool = True
    notes: str = ""


class ReportSupportContract(BaseModel):
    support_id: str
    benchmark_title: str
    required_markers: list[str] = Field(default_factory=list)
    notes: str = ""


class ReportParityFrameworkArtifact(ProvenancedModel):
    framework_id: str
    benchmark_id: str
    chapter_contracts: list[ReportChapterContract] = Field(default_factory=list)
    support_contracts: list[ReportSupportContract] = Field(default_factory=list)
    markdown: str = ""


class ChapterParityResult(BaseModel):
    chapter_id: str
    benchmark_title: str
    status: ReportParityStatus
    present: bool
    citation_count: int = 0
    missing_outputs: list[str] = Field(default_factory=list)
    missing_markers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SupportParityResult(BaseModel):
    support_id: str
    benchmark_title: str
    status: ReportParityStatus
    present: bool
    missing_markers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReportParityArtifact(ProvenancedModel):
    framework_id: str
    benchmark_id: str
    overall_status: ReportParityStatus
    complete_chapter_count: int = 0
    partial_chapter_count: int = 0
    missing_chapter_count: int = 0
    complete_support_count: int = 0
    partial_support_count: int = 0
    missing_support_count: int = 0
    missing_chapter_ids: list[str] = Field(default_factory=list)
    missing_support_ids: list[str] = Field(default_factory=list)
    chapter_results: list[ChapterParityResult] = Field(default_factory=list)
    support_results: list[SupportParityResult] = Field(default_factory=list)
    markdown: str = ""


class DecisionAcceptanceResult(BaseModel):
    decision_id: str
    present: bool
    notes: list[str] = Field(default_factory=list)


class ReportAcceptanceArtifact(ProvenancedModel):
    benchmark_id: str
    overall_status: ReportAcceptanceStatus
    pipeline_status: RunStatus
    report_parity_status: Optional[ReportParityStatus] = None
    blocked_stage_id: Optional[str] = None
    satisfied_expected_decision_count: int = 0
    missing_expected_decision_count: int = 0
    missing_expected_decisions: list[str] = Field(default_factory=list)
    blocking_issue_codes: list[str] = Field(default_factory=list)
    decision_results: list[DecisionAcceptanceResult] = Field(default_factory=list)
    conditional_notes: list[str] = Field(default_factory=list)
    route_evidence_status: str = "not_evaluated"
    product_basis_status: str = "not_evaluated"
    unit_train_consistency_status: str = "not_evaluated"
    purification_rigor_status: str = "not_evaluated"
    economic_realism_status: str = "not_evaluated"
    real_data_status: str = "not_evaluated"
    real_data_coverage_fraction: float = 0.0
    critical_seeded_dependencies: list[str] = Field(default_factory=list)
    summary: str = ""
    markdown: str = ""


class DataRealityAuditRow(ProvenancedModel):
    artifact_ref: str
    artifact_label: str
    domain: str
    critical: bool = False
    dominant_class: DataRealityClass = DataRealityClass.MODEL_INFERRED
    counts_by_class: dict[str, int] = Field(default_factory=dict)
    real_data_fraction: float = 0.0
    seeded_fraction: float = 0.0
    solver_fraction: float = 0.0
    inferred_fraction: float = 0.0
    notes: list[str] = Field(default_factory=list)


class DataRealityAuditArtifact(ProvenancedModel):
    benchmark_profile: str = ""
    project_id: str = ""
    rows: list[DataRealityAuditRow] = Field(default_factory=list)
    overall_real_data_fraction: float = 0.0
    critical_seeded_artifact_refs: list[str] = Field(default_factory=list)
    critical_inferred_artifact_refs: list[str] = Field(default_factory=list)
    summary: str = ""
    markdown: str = ""


class MethodBasisRecord(ProvenancedModel):
    method_name: str
    method_tag: EstimationMethodTag = EstimationMethodTag.FALLBACK
    method_basis: str = ""
    source_refs: list[str] = Field(default_factory=list)
    fallback_reason: str = ""


class DatumRequirementRule(ProvenancedModel):
    datum_id: str
    engineering_category: str
    allowed_methods: list[EstimationMethodTag] = Field(default_factory=list)
    forbidden_methods: list[EstimationMethodTag] = Field(default_factory=list)
    minimum_confidence: float = 0.0
    critical: bool = False


class EstimationPolicy(ProvenancedModel):
    policy_id: str
    benchmark_profile: str = ""
    rules: list[DatumRequirementRule] = Field(default_factory=list)
    markdown: str = ""


class DataGapItem(ProvenancedModel):
    datum_id: str
    engineering_category: str
    current_value: str = ""
    units: str = ""
    provenance_class: DataRealityClass = DataRealityClass.MODEL_INFERRED
    method_name: str = ""
    method_tag: EstimationMethodTag = EstimationMethodTag.FALLBACK
    method_basis: str = ""
    confidence: float = 0.0
    downstream_consumers: list[str] = Field(default_factory=list)
    upgrade_priority: Literal["low", "medium", "high", "critical"] = "medium"
    direct_data: bool = False
    source_refs: list[str] = Field(default_factory=list)
    fallback_reason: str = ""
    status: Literal["direct", "estimated", "inferred", "solver_derived", "unresolved"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class DataGapRegistryArtifact(ProvenancedModel):
    benchmark_profile: str = ""
    project_id: str = ""
    items: list[DataGapItem] = Field(default_factory=list)
    summary: str = ""
    markdown: str = ""


class BACPseudoComponentBasisArtifact(ProvenancedModel):
    artifact_id: str
    active_basis_name: str = "BAC active pseudo-component"
    amine_basis_name: str = "Alkyldimethylamine pseudo-component"
    carrier_basis_name: str = "Carrier phase"
    sold_solution_basis_name: str = "Sold-solution pseudo-mixture"
    active_representative_mw_g_mol: float = 0.0
    active_density_kg_m3: float = 0.0
    active_viscosity_pa_s: float = 0.0
    active_cp_kj_kg_k: float = 0.0
    active_thermal_conductivity_w_m_k: float = 0.0
    active_nonvolatile: bool = True
    sold_solution_density_kg_m3: float = 0.0
    sold_solution_viscosity_pa_s: float = 0.0
    sold_solution_cp_kj_kg_k: float = 0.0
    homolog_distribution: dict[str, float] = Field(default_factory=dict)
    carrier_components: list[str] = Field(default_factory=list)
    markdown: str = ""


class BinaryPairCoverageRow(ProvenancedModel):
    pair_id: str
    component_a: str
    component_b: str
    status: Literal["resolved_from_data", "regressed_from_data", "family_estimated", "fallback"] = "fallback"
    model_name: str = "NRTL"
    source_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BinaryPairCoverageArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str = ""
    rows: list[BinaryPairCoverageRow] = Field(default_factory=list)
    critical_fallback_pairs: list[str] = Field(default_factory=list)
    markdown: str = ""


class SectionThermoAssignmentRow(ProvenancedModel):
    section_id: str
    section_label: str = ""
    thermo_method: str = ""
    activity_model: str = ""
    key_pairs: list[str] = Field(default_factory=list)
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    notes: list[str] = Field(default_factory=list)


class SectionThermoAssignmentArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str = ""
    rows: list[SectionThermoAssignmentRow] = Field(default_factory=list)
    markdown: str = ""


class KineticBasisArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str = ""
    reaction_family: str = ""
    assumed_mechanism_class: str = ""
    activation_energy_kj_per_mol: float = 0.0
    pre_exponential_factor: float = 0.0
    apparent_order: float = 0.0
    design_residence_time_hr: float = 0.0
    method_tag: EstimationMethodTag = EstimationMethodTag.FAMILY_ARRHENIUS_FIT
    cap_logic_summary: str = ""
    markdown: str = ""


class ReactorBasisConfidenceArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str = ""
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    basis_summary: str = ""
    hidden_cap_logic: bool = False
    markdown: str = ""


class BACImpurityLedgerItem(ProvenancedModel):
    impurity_id: str
    impurity_class: str
    origin: str = ""
    expected_location: str = ""
    control_section: str = ""
    purge_mechanism: str = ""
    mass_estimate_kg_hr: float = 0.0
    status: Literal["measured_or_observed", "template_derived", "placeholder_estimate", "unresolved"] = "template_derived"
    notes: list[str] = Field(default_factory=list)


class BACImpurityLedgerArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str = ""
    items: list[BACImpurityLedgerItem] = Field(default_factory=list)
    markdown: str = ""


class RecycleBasisLoop(ProvenancedModel):
    loop_id: str
    source_section_id: str = ""
    target_section_id: str = ""
    actual_recycle_stream_ids: list[str] = Field(default_factory=list)
    actual_purge_stream_ids: list[str] = Field(default_factory=list)
    purge_policy_by_family: dict[str, float] = Field(default_factory=dict)
    purge_basis_by_family: dict[str, str] = Field(default_factory=dict)
    closure_confidence: Literal["converged", "estimated", "blocked"] = "estimated"
    notes: list[str] = Field(default_factory=list)


class RecycleBasisArtifact(ProvenancedModel):
    artifact_id: str
    loops: list[RecycleBasisLoop] = Field(default_factory=list)
    markdown: str = ""


class EconomicGapItem(ProvenancedModel):
    item_id: str
    label: str
    source_type: Literal["real_external_quote", "benchmark_anchor", "route_complexity_estimate", "solver_derived_burden"] = "solver_derived_burden"
    normalization_basis: str = ""
    site_dependence: str = ""
    estimate_method: str = ""
    gap_flag: str = ""
    notes: list[str] = Field(default_factory=list)


class EconomicInputRealityArtifact(ProvenancedModel):
    artifact_id: str
    rows: list[EconomicGapItem] = Field(default_factory=list)
    markdown: str = ""


class MissingDataValidationIssue(ProvenancedModel):
    datum_id: str
    code: str
    severity: Literal["warning", "blocked"] = "warning"
    message: str


class MissingDataAcceptanceArtifact(ProvenancedModel):
    artifact_id: str
    overall_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    coverage_fraction: float = 0.0
    named_estimate_fraction: float = 0.0
    hidden_placeholder_count: int = 0
    critical_unresolved_count: int = 0
    issues: list[MissingDataValidationIssue] = Field(default_factory=list)
    summary: str = ""
    markdown: str = ""


class ProcessOptionFact(ProvenancedModel):
    option_id: str
    label: str
    source_document_id: str
    selected_in_document: bool = False
    yield_fraction: Optional[float] = None
    reaction_family_hints: list[str] = Field(default_factory=list)
    extracted_species: list[str] = Field(default_factory=list)
    raw_materials: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    solvents: list[str] = Field(default_factory=list)
    hazards: list[str] = Field(default_factory=list)
    summary: str = ""
    source_excerpt: str = ""


class ReactionMentionArtifact(ProvenancedModel):
    mention_id: str
    route_option_id: str = ""
    step_label: str = ""
    reaction_family_hint: str = ""
    reactants: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    byproducts: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    solvents: list[str] = Field(default_factory=list)
    source_document_id: str
    source_excerpt: str = ""


class EquipmentMentionArtifact(ProvenancedModel):
    mention_id: str
    unit_tag: str
    unit_type: str = ""
    service_hint: str = ""
    route_option_id: str = ""
    source_document_id: str
    source_excerpt: str = ""


class SiteComparisonArtifact(ProvenancedModel):
    site_id: str
    site_name: str
    state: str = ""
    selected_in_document: bool = False
    score_text: str = ""
    rationale: str = ""
    source_document_id: str
    source_excerpt: str = ""


class EconomicFactArtifact(ProvenancedModel):
    fact_id: str
    label: str
    value_text: str
    units: str = ""
    category: str = ""
    source_document_id: str
    source_excerpt: str = ""


class ProcessComparisonArtifact(ProvenancedModel):
    comparison_id: str
    source_document_id: str
    options: list[ProcessOptionFact] = Field(default_factory=list)
    selected_option_id: Optional[str] = None
    comparison_notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class DocumentFactArtifact(ProvenancedModel):
    document_id: str
    source_id: str
    title: str
    process_comparisons: list[ProcessComparisonArtifact] = Field(default_factory=list)
    reaction_mentions: list[ReactionMentionArtifact] = Field(default_factory=list)
    equipment_mentions: list[EquipmentMentionArtifact] = Field(default_factory=list)
    site_comparisons: list[SiteComparisonArtifact] = Field(default_factory=list)
    economic_facts: list[EconomicFactArtifact] = Field(default_factory=list)
    operating_mode_hints: list[str] = Field(default_factory=list)
    utility_mentions: list[str] = Field(default_factory=list)
    alias_map: dict[str, list[str]] = Field(default_factory=dict)
    markdown: str = ""


class DocumentFactCollectionArtifact(ProvenancedModel):
    documents: list[DocumentFactArtifact] = Field(default_factory=list)
    process_option_count: int = 0
    reaction_mention_count: int = 0
    equipment_mention_count: int = 0
    selected_process_labels: list[str] = Field(default_factory=list)
    selected_site_names: list[str] = Field(default_factory=list)
    markdown: str = ""


class DocumentProcessOptionsArtifact(ProvenancedModel):
    options: list[ProcessOptionFact] = Field(default_factory=list)
    selected_option_ids: list[str] = Field(default_factory=list)
    source_document_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class ResearchBundle(BaseModel):
    sources: list[SourceRecord]
    technical_source_ids: list[str] = Field(default_factory=list)
    india_source_ids: list[str] = Field(default_factory=list)
    corpus_excerpt: str
    user_document_ids: list[str] = Field(default_factory=list)
    user_document_facts: list[DocumentFactArtifact] = Field(default_factory=list)
    document_process_options: list[ProcessOptionFact] = Field(default_factory=list)


class SourceDiscoveryArtifact(BaseModel):
    sources: list[SourceRecord]
    summary: str


class ProductProfileArtifact(ProvenancedModel):
    product_name: str
    properties: list[PropertyRecord]
    uses: list[str]
    industrial_relevance: str
    safety_notes: list[str]
    commercial_basis_summary: str = ""
    nominal_active_wt_pct: Optional[float] = None
    product_form: str = ""
    carrier_components: list[str] = Field(default_factory=list)
    homolog_distribution: dict[str, float] = Field(default_factory=dict)
    quality_targets: list[str] = Field(default_factory=list)
    markdown: str


class CommercialProductBasisArtifact(ProvenancedModel):
    product_name: str
    throughput_basis: Literal["finished_product", "active_component"] = "finished_product"
    sold_solution_basis_kg_hr: float = 0.0
    active_basis_kg_hr: float = 0.0
    active_fraction: float = 1.0
    sold_concentration_wt_pct: float = 100.0
    sold_solution_price_inr_per_kg: float = 0.0
    active_price_inr_per_kg: float = 0.0
    packaging_mode: str = ""
    dispatch_mode: str = ""
    product_form: str = ""
    carrier_components: list[str] = Field(default_factory=list)
    homolog_distribution: dict[str, float] = Field(default_factory=dict)
    quality_targets: list[str] = Field(default_factory=list)
    capacity_basis_note: str = ""
    markdown: str = ""


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


class RouteDiscoveryRow(ProvenancedModel):
    route_id: str
    route_name: str
    route_origin: Literal["seeded", "document", "hybrid", "generated"] = "seeded"
    route_family_id: str = ""
    evidence_score: float = 0.0
    chemistry_completeness_score: float = 0.0
    step_count: int = 0
    batch_capable: bool = False
    source_document_id: str = ""
    discovery_status: Literal["discovered", "weak_evidence", "incomplete_chemistry"] = "discovered"


class RouteDiscoveryArtifact(ProvenancedModel):
    rows: list[RouteDiscoveryRow] = Field(default_factory=list)
    markdown: str = ""


class SpeciesResolutionIssue(ProvenancedModel):
    issue_id: str
    route_id: str
    species_name: str
    issue_code: str
    blocking: bool = False
    message: str = ""


class SpeciesNode(ProvenancedModel):
    species_id: str
    canonical_name: str
    formula: Optional[str] = None
    aliases: list[str] = Field(default_factory=list)
    role_tags: list[str] = Field(default_factory=list)
    route_ids: list[str] = Field(default_factory=list)
    phase_hint: str = ""
    source_document_ids: list[str] = Field(default_factory=list)
    resolution_status: Literal["resolved", "partial", "anonymous"] = "resolved"
    species_kind: Literal["discrete", "bundle", "impurity_class", "carrier"] = "discrete"
    commercial_role: str = ""
    volatility_class: Literal["volatile", "semivolatile", "nonvolatile", "carrier", "unknown"] = "unknown"


class ReactionStep(ProvenancedModel):
    step_id: str
    route_id: str
    step_label: str = ""
    reaction_family: str = ""
    reactant_species_ids: list[str] = Field(default_factory=list)
    product_species_ids: list[str] = Field(default_factory=list)
    byproduct_species_ids: list[str] = Field(default_factory=list)
    catalyst_names: list[str] = Field(default_factory=list)
    solvent_names: list[str] = Field(default_factory=list)
    source_document_id: str = ""
    source_excerpt: str = ""
    confidence: float = 0.0


class RouteCandidateGraph(ProvenancedModel):
    route_id: str
    route_name: str
    route_origin: Literal["seeded", "document", "hybrid", "generated"] = "seeded"
    source_document_id: Optional[str] = None
    species_nodes: list[SpeciesNode] = Field(default_factory=list)
    reaction_steps: list[ReactionStep] = Field(default_factory=list)
    major_separation_hints: list[str] = Field(default_factory=list)
    anonymous_core_species: list[str] = Field(default_factory=list)
    unresolved_issues: list[SpeciesResolutionIssue] = Field(default_factory=list)
    chemistry_completeness_score: float = 0.0
    batch_capable: bool = False
    markdown: str = ""


class RouteChemistryArtifact(ProvenancedModel):
    route_graphs: list[RouteCandidateGraph] = Field(default_factory=list)
    resolved_species_count: int = 0
    anonymous_species_count: int = 0
    blocking_route_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class PropertyDemandItem(ProvenancedModel):
    demand_id: str
    species_id: str
    species_name: str
    stage_id: str
    property_name: str
    sensitivity: SensitivityLevel = SensitivityLevel.LOW
    blocking: bool = False
    rationale: str = ""


class SpeciesPropertyCoverage(ProvenancedModel):
    coverage_id: str
    species_id: str
    species_name: str
    stage_id: str
    property_name: str
    coverage_status: Literal["covered", "estimated", "missing", "blocked"] = "missing"
    source_ids: list[str] = Field(default_factory=list)
    blocking: bool = False
    rationale: str = ""


class PropertyDemandPlan(ProvenancedModel):
    route_ids: list[str] = Field(default_factory=list)
    items: list[PropertyDemandItem] = Field(default_factory=list)
    coverage: list[SpeciesPropertyCoverage] = Field(default_factory=list)
    blocking_species_ids: list[str] = Field(default_factory=list)
    blocked_stage_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class MethodCoverageDecision(ProvenancedModel):
    decision_id: str
    context: str
    status: Literal["covered", "partial", "blocked"] = "partial"
    blocking_species_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class SpeciesResolutionRecord(ProvenancedModel):
    route_id: str
    route_name: str
    core_species_ids: list[str] = Field(default_factory=list)
    valid_core_species_ids: list[str] = Field(default_factory=list)
    invalid_core_species_names: list[str] = Field(default_factory=list)
    unresolved_core_species_names: list[str] = Field(default_factory=list)
    unresolved_intermediate_names: list[str] = Field(default_factory=list)
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    markdown: str = ""


class SpeciesResolutionArtifact(ProvenancedModel):
    selected_route_id: str = ""
    routes: list[SpeciesResolutionRecord] = Field(default_factory=list)
    blocking_route_ids: list[str] = Field(default_factory=list)
    invalid_species_names: list[str] = Field(default_factory=list)
    markdown: str = ""


class ReactionNetworkRoute(ProvenancedModel):
    route_id: str
    route_name: str
    core_species_complete: bool = False
    step_count: int = 0
    reaction_steps: list[ReactionStep] = Field(default_factory=list)
    blocking_issue_codes: list[str] = Field(default_factory=list)
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    markdown: str = ""


class ReactionNetworkV2Artifact(ProvenancedModel):
    selected_route_id: str = ""
    routes: list[ReactionNetworkRoute] = Field(default_factory=list)
    blocking_route_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class RouteScreeningRow(ProvenancedModel):
    route_id: str
    route_name: str
    route_family_id: str = ""
    screening_status: Literal["retained", "review", "eliminated"] = "review"
    chemistry_readiness: Literal["design_ready", "screening_only", "blocked"] = "screening_only"
    core_species_complete: bool = False
    reaction_step_count: int = 0
    major_separation_defined: bool = False
    hazard_review_required: bool = False
    reagent_catalyst_burden_score: float = 0.0
    stepwise_recovery_burden_score: float = 0.0
    catalyst_lifecycle_burden_score: float = 0.0
    isolation_impurity_burden_score: float = 0.0
    impurity_cleanup_sequence_score: float = 0.0
    separation_pain_score: float = 0.0
    operability_burden_score: float = 0.0
    waste_burden_score: float = 0.0
    waste_treatment_load_score: float = 0.0
    elimination_stage: str = ""
    reasons: list[str] = Field(default_factory=list)


class RouteScreeningArtifact(ProvenancedModel):
    rows: list[RouteScreeningRow] = Field(default_factory=list)
    retained_route_ids: list[str] = Field(default_factory=list)
    eliminated_route_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class RouteProcessClaimRecord(ProvenancedModel):
    route_id: str
    route_name: str
    claim_type: Literal["reagent_recycle", "impurity_classes", "cleanup_sequence", "waste_modes"]
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    items: list[str] = Field(default_factory=list)
    item_count: int = 0
    metrics: dict[str, float] = Field(default_factory=dict)
    rationale: str = ""


class RouteProcessClaimsArtifact(ProvenancedModel):
    claims: list[RouteProcessClaimRecord] = Field(default_factory=list)
    markdown: str = ""


class ChemistryDecisionArtifact(ProvenancedModel):
    selected_route_id: str = ""
    selected_route_name: str = ""
    chemistry_basis_status: Literal["design_ready", "screening_only", "blocked"] = "screening_only"
    core_species_ids: list[str] = Field(default_factory=list)
    unresolved_species_names: list[str] = Field(default_factory=list)
    reaction_step_count: int = 0
    dominant_reaction_families: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    solvents: list[str] = Field(default_factory=list)
    rationale: str = ""
    markdown: str = ""


class ThermoSectionAdmissibility(ProvenancedModel):
    route_id: str
    section_id: str
    separation_family: str
    method_family: str
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    required_inputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    rationale: str = ""


class ThermoAdmissibilityArtifact(ProvenancedModel):
    selected_route_id: str = ""
    selected_route_status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    selected_route_confidence: ScientificConfidence = ScientificConfidence.SCREENING
    route_status: dict[str, ScientificGateStatus] = Field(default_factory=dict)
    route_confidence: dict[str, ScientificConfidence] = Field(default_factory=dict)
    sections: list[ThermoSectionAdmissibility] = Field(default_factory=list)
    blocking_route_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class BACPurificationSection(ProvenancedModel):
    section_id: str
    step_id: str = ""
    label: str
    service: str
    separation_family: str
    key_species: list[str] = Field(default_factory=list)
    recovery_targets: list[str] = Field(default_factory=list)
    purge_targets: list[str] = Field(default_factory=list)
    thermo_method: str = ""
    activity_model: str = ""
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    notes: list[str] = Field(default_factory=list)


class BACPurificationSectionArtifact(ProvenancedModel):
    route_id: str = ""
    blueprint_id: str = ""
    sections: list[BACPurificationSection] = Field(default_factory=list)
    unresolved_section_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class KineticsStepAdmissibility(ProvenancedModel):
    route_id: str
    step_id: str
    reaction_family: str = ""
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    kinetics_required: bool = True
    rationale: str = ""


class KineticsAdmissibilityArtifact(ProvenancedModel):
    selected_route_id: str = ""
    selected_route_status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    selected_route_confidence: ScientificConfidence = ScientificConfidence.SCREENING
    route_status: dict[str, ScientificGateStatus] = Field(default_factory=dict)
    route_confidence: dict[str, ScientificConfidence] = Field(default_factory=dict)
    steps: list[KineticsStepAdmissibility] = Field(default_factory=list)
    blocking_route_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class FlowsheetIntentItem(ProvenancedModel):
    route_id: str
    step_id: str
    intent_type: str
    unit_id: str
    service: str
    phase_basis: str = ""
    upstream_intent_ids: list[str] = Field(default_factory=list)
    basis: str = ""


class FlowsheetIntentArtifact(ProvenancedModel):
    route_id: str
    blueprint_id: str = ""
    batch_capable: bool = False
    intents: list[FlowsheetIntentItem] = Field(default_factory=list)
    markdown: str = ""


class TopologyCandidateRecord(ProvenancedModel):
    blueprint_id: str
    route_id: str
    route_name: str
    step_count: int = 0
    tagged_unit_count: int = 0
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    screening_balance_allowed: bool = False
    reasons: list[str] = Field(default_factory=list)


class TopologyCandidateArtifact(ProvenancedModel):
    selected_route_id: str = ""
    selected_blueprint_id: str = ""
    screening_balance_allowed: bool = False
    candidates: list[TopologyCandidateRecord] = Field(default_factory=list)
    route_to_unit_map: list[str] = Field(default_factory=list)
    markdown: str = ""


class UnitTrainConsistencyRow(ProvenancedModel):
    artifact_ref: str
    expected_unit_aliases: list[str] = Field(default_factory=list)
    observed_unit_ids: list[str] = Field(default_factory=list)
    missing_expected_units: list[str] = Field(default_factory=list)
    unexpected_units: list[str] = Field(default_factory=list)
    status: Literal["pass", "warning", "blocked"] = "warning"
    notes: list[str] = Field(default_factory=list)


class UnitTrainConsistencyArtifact(ProvenancedModel):
    route_id: str = ""
    blueprint_id: str = ""
    canonical_unit_ids: list[str] = Field(default_factory=list)
    canonical_sections: list[str] = Field(default_factory=list)
    alias_map: dict[str, list[str]] = Field(default_factory=dict)
    rows: list[UnitTrainConsistencyRow] = Field(default_factory=list)
    overall_status: Literal["pass", "warning", "blocked"] = "warning"
    blocking_artifact_refs: list[str] = Field(default_factory=list)
    markdown: str = ""


class UnitDesignConfidence(BaseModel):
    unit_id: str
    unit_type: str
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    rationale: str = ""
    blocking_reasons: list[str] = Field(default_factory=list)


class DesignConfidenceArtifact(ProvenancedModel):
    selected_route_id: str = ""
    overall_confidence: ScientificConfidence = ScientificConfidence.SCREENING
    blocked_unit_ids: list[str] = Field(default_factory=list)
    units: list[UnitDesignConfidence] = Field(default_factory=list)
    markdown: str = ""


class EconomicCoverageDecision(ProvenancedModel):
    route_id: str = ""
    status: Literal["detailed", "screening", "blocked"] = "screening"
    missing_basis: list[str] = Field(default_factory=list)
    rationale: str = ""
    markdown: str = ""


class ScientificClaim(ProvenancedModel):
    claim_id: str
    stage_id: str
    domain: str
    subject: str
    value_text: str
    units: str = ""
    status: ClaimStatus = ClaimStatus.PARTIAL
    provenance: ScientificClaimProvenance = ScientificClaimProvenance.ENVELOPE_MODEL
    uncertainty_class: str = "review"
    dependency_ids: list[str] = Field(default_factory=list)
    revision_count: int = 0
    frozen: bool = False
    blocking: bool = False


class ClaimGraphArtifact(ProvenancedModel):
    claims: list[ScientificClaim] = Field(default_factory=list)
    changed_claim_ids: list[str] = Field(default_factory=list)
    frozen_claim_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class InferenceQuestion(ProvenancedModel):
    question_id: str
    domain: str
    prompt: str
    why_it_matters: str
    dependent_claim_ids: list[str] = Field(default_factory=list)
    evidence_targets: list[str] = Field(default_factory=list)
    unanswered_effect: Literal["downgrade", "block"] = "block"
    priority_score: float = 0.0
    active: bool = True


class QuestionAnswer(ProvenancedModel):
    question_id: str
    answer_text: str
    resolved_claim_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class InferenceQuestionQueueArtifact(ProvenancedModel):
    active_questions: list[InferenceQuestion] = Field(default_factory=list)
    resolved_answers: list[QuestionAnswer] = Field(default_factory=list)
    markdown: str = ""


class RevisionTicket(ProvenancedModel):
    ticket_id: str
    target_stage_id: str
    triggered_by_stage_id: str
    reason: str
    dependent_claim_ids: list[str] = Field(default_factory=list)
    status: Literal["open", "applied", "closed", "skipped"] = "open"
    material_change: bool = True
    revision_limit: int = 0


class RevisionLedgerArtifact(ProvenancedModel):
    tickets: list[RevisionTicket] = Field(default_factory=list)
    active_ticket_ids: list[str] = Field(default_factory=list)
    revision_counts_by_stage: dict[str, int] = Field(default_factory=dict)
    markdown: str = ""


class ScientificGateEntry(ProvenancedModel):
    gate_id: str
    domain: str
    status: ScientificGateStatus = ScientificGateStatus.SCREENING_ONLY
    confidence: ScientificConfidence = ScientificConfidence.SCREENING
    rationale: str = ""
    blocking_claim_ids: list[str] = Field(default_factory=list)
    blocking_question_ids: list[str] = Field(default_factory=list)


class ScientificGateMatrixArtifact(ProvenancedModel):
    entries: list[ScientificGateEntry] = Field(default_factory=list)
    markdown: str = ""


class RouteSelectionComparisonRow(ProvenancedModel):
    route_id: str
    route_name: str
    route_origin: Literal["seeded", "document", "hybrid", "generated"] = "seeded"
    route_evidence_basis: Literal["seeded_benchmark", "document_derived", "cited_technical", "cited_patent", "mixed_cited", "generated"] = "seeded_benchmark"
    route_family_id: str = ""
    total_score: float = 0.0
    evidence_score: float = 0.0
    chemistry_completeness_score: float = 0.0
    separation_complexity_score: float = 0.0
    selected_heat_case_id: str = ""
    feasible: bool = True
    scientific_status: Literal["design_feasible", "screening_feasible", "blocked"] = "design_feasible"
    blocking_scientific_gate: str = ""
    selected: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)
    why_not_chosen: str = ""


class RouteSelectionComparisonArtifact(ProvenancedModel):
    selected_route_id: str = ""
    rows: list[RouteSelectionComparisonRow] = Field(default_factory=list)
    blocked_route_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class ProcessSelectionComparisonArtifact(RouteSelectionComparisonArtifact):
    route_discovery_count: int = 0
    retained_route_count: int = 0
    eliminated_route_count: int = 0
    selected_route_name: str = ""


class RouteSelectionArtifact(ProvenancedModel):
    selected_route_id: str
    justification: str
    comparison_markdown: str


class SeparationDutyItem(ProvenancedModel):
    duty_id: str
    route_id: str
    step_id: str
    separation_family: str
    driving_force: str = ""
    key_species: list[str] = Field(default_factory=list)
    basis: str = ""


class RecycleIntentArtifact(ProvenancedModel):
    intent_id: str
    route_id: str
    source_step_id: str
    target_step_id: str
    stream_family: str = ""
    basis: str = ""
    closing_species: list[str] = Field(default_factory=list)


class FlowsheetBlueprintStep(ProvenancedModel):
    step_id: str
    route_id: str
    section_id: str
    section_label: str
    step_role: str
    unit_id: str
    solver_anchor_unit_id: str = ""
    unit_tag: str = ""
    unit_type: str
    service: str
    reaction_step_ref: str = ""
    separation_basis_ref: str = ""
    batch_campaign_ref: str = ""
    phase_basis: str = ""
    upstream_step_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class FlowsheetBlueprintArtifact(ProvenancedModel):
    blueprint_id: str
    route_id: str
    route_name: str
    route_origin: Literal["seeded", "document", "hybrid", "generated"] = "seeded"
    steps: list[FlowsheetBlueprintStep] = Field(default_factory=list)
    separation_duties: list[SeparationDutyItem] = Field(default_factory=list)
    recycle_intents: list[RecycleIntentArtifact] = Field(default_factory=list)
    batch_capable: bool = False
    selected_unit_tags: list[str] = Field(default_factory=list)
    markdown: str = ""


class UnitTrainCandidateSet(ProvenancedModel):
    blueprints: list[FlowsheetBlueprintArtifact] = Field(default_factory=list)
    markdown: str = ""


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
    chemistry_family_adapter_id: str = ""


class ChemistryFamilyAdapter(ProvenancedModel):
    adapter_id: str
    family_label: str
    compound_family: Literal["organic", "inorganic", "mixed"]
    dominant_phase_system: Literal["gas", "liquid", "solid", "mixed"]
    route_generation_hints: list[str] = Field(default_factory=list)
    property_priority_order: list[str] = Field(default_factory=list)
    preferred_reactor_candidates: list[str] = Field(default_factory=list)
    preferred_separation_candidates: list[str] = Field(default_factory=list)
    preferred_storage_candidates: list[str] = Field(default_factory=list)
    moc_bias_candidates: list[str] = Field(default_factory=list)
    common_unit_operations: list[str] = Field(default_factory=list)
    corrosion_cues: list[str] = Field(default_factory=list)
    heat_integration_patterns: list[str] = Field(default_factory=list)
    critic_focus: list[str] = Field(default_factory=list)
    sparse_data_blockers: list[str] = Field(default_factory=list)
    benchmark_profiles: list[str] = Field(default_factory=list)
    rationale: str
    markdown: str = ""


class SparseDataPolicyRule(ProvenancedModel):
    rule_id: str
    stage_id: str
    subject: str
    artifact_family: str
    preferred_resolution_order: list[ProvenanceTag] = Field(default_factory=list)
    allow_calculated: bool = True
    allow_estimated: bool = True
    allow_analogy: bool = False
    allow_heuristic_fallback: bool = False
    minimum_confidence: float = 0.0
    block_when_missing: bool = True
    current_status: Literal["covered", "warning", "blocked"] = "covered"
    triggered_items: list[str] = Field(default_factory=list)
    rationale: str = ""


class SparseDataPolicyArtifact(ProvenancedModel):
    policy_id: str
    adapter_id: str
    family_label: str
    rules: list[SparseDataPolicyRule] = Field(default_factory=list)
    blocked_stage_ids: list[str] = Field(default_factory=list)
    warning_stage_ids: list[str] = Field(default_factory=list)
    markdown: str = ""


class SiteSelectionArtifact(ProvenancedModel):
    candidates: list[SiteOption]
    selected_site: str
    india_location_data: list[IndianLocationDatum] = Field(default_factory=list)
    markdown: str


class RouteSiteFitArtifact(ProvenancedModel):
    route_id: str
    selected_site: str
    blueprint_id: str = ""
    blueprint_step_count: int = 0
    separation_duty_count: int = 0
    recycle_intent_count: int = 0
    batch_capable: bool = False
    port_dependency_factor: float = 0.0
    feedstock_cluster_factor: float = 1.0
    logistics_penalty_factor: float = 1.0
    utility_reliability_factor: float = 1.0
    batch_site_factor: float = 1.0
    overall_fit_score: float = 0.0
    notes: str = ""
    markdown: str = ""


class RouteEconomicItem(ProvenancedModel):
    component_name: str
    role: str
    annualized_burden_inr: float = 0.0
    recovery_fraction: float = 0.0
    notes: str = ""


class RouteEconomicBasisArtifact(ProvenancedModel):
    route_id: str
    selected_site: str
    blueprint_id: str = ""
    operating_mode: str
    blueprint_step_count: int = 0
    separation_duty_count: int = 0
    recycle_intent_count: int = 0
    batch_capable: bool = False
    major_feed_components: list[str] = Field(default_factory=list)
    recycle_component_count: int = 0
    raw_material_complexity_factor: float = 1.0
    site_input_cost_factor: float = 1.0
    logistics_intensity_factor: float = 1.0
    batch_occupancy_penalty_fraction: float = 0.0
    solvent_recovery_service_cost_inr: float = 0.0
    catalyst_service_cost_inr: float = 0.0
    waste_treatment_burden_inr: float = 0.0
    coverage_status: Literal["screening", "hybrid", "grounded"] = "screening"
    items: list[RouteEconomicItem] = Field(default_factory=list)
    notes: str = ""
    markdown: str = ""


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
    section_id: str = ""
    section_type: str = ""
    upstream_nodes: list[str] = Field(default_factory=list)
    downstream_nodes: list[str] = Field(default_factory=list)
    representative_stream_ids: list[str] = Field(default_factory=list)
    stream_roles: list[str] = Field(default_factory=list)
    recycle_loop_ids: list[str] = Field(default_factory=list)
    side_draw_stream_ids: list[str] = Field(default_factory=list)
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
    section_ids: list[str] = Field(default_factory=list)
    stream_ids: list[str] = Field(default_factory=list)
    convergence_status: Literal["seeded", "converged", "estimated", "blocked"] = "seeded"
    unresolved_sensitivities: list[str] = Field(default_factory=list)
    markdown: str


class ProcessNarrativeArtifact(ProvenancedModel):
    bfd_mermaid: str
    markdown: str


class DiagramStyleProfile(ProvenancedModel):
    style_id: str
    style_name: str
    canvas_width_px: int = 1800
    canvas_height_px: int = 920
    body_font_family: str = "Calibri"
    heading_font_family: str = "Calibri"
    mono_font_family: str = "Courier New"
    node_fill: str = "#f7f7f7"
    node_stroke: str = "#222222"
    recycle_stroke: str = "#5d6d7e"
    utility_stroke: str = "#4a6fa5"
    stream_stroke: str = "#111111"
    markdown: str = ""


class DiagramSymbolDefinition(BaseModel):
    symbol_key: str
    label: str
    diagram_level: DiagramLevel
    entity_kind: DiagramEntityKind
    pid_family: str = ""
    shape: DiagramSymbolShape
    width_px: int
    height_px: int
    stroke_color: str = "#222222"
    fill_color: str = "#f7f7f7"
    stroke_width_px: float = 1.5
    line_pattern: DiagramLinePattern = DiagramLinePattern.SOLID
    label_position: Literal["inside", "above", "below", "right"] = "inside"
    equipment_tag_position: Literal["hidden", "above", "header"] = "above"
    notes: list[str] = Field(default_factory=list)


class DiagramEdgeStyleRule(BaseModel):
    role: DiagramEdgeRole
    diagram_level: DiagramLevel
    stroke_color: str
    stroke_width_px: float = 2.0
    line_pattern: DiagramLinePattern = DiagramLinePattern.SOLID
    arrow_marker: Literal["none", "forward", "bidirectional"] = "forward"
    label_box_fill: str = "#ffffff"


class DiagramLevelStylePolicy(BaseModel):
    diagram_level: DiagramLevel
    symbol_policy: DiagramSymbolPolicy
    allowed_symbol_keys: list[str] = Field(default_factory=list)
    forbidden_entity_kinds: list[DiagramEntityKind] = Field(default_factory=list)
    allowed_edge_roles: list[DiagramEdgeRole] = Field(default_factory=list)
    body_font_family: str = "Calibri"
    heading_font_family: str = "Calibri"
    mono_font_family: str = "Courier New"
    title_font_size_px: int = 22
    primary_label_font_size_px: int = 13
    secondary_label_font_size_px: int = 10
    minimum_text_size_px: int = 9
    minimum_node_spacing_px: int = 44
    minimum_label_clearance_px: int = 16
    orthogonal_routing_only: bool = True
    allow_diagonal_connectors: bool = False
    notes: list[str] = Field(default_factory=list)


class DiagramSymbolLibraryArtifact(ProvenancedModel):
    library_id: str
    library_name: str
    symbols: list[DiagramSymbolDefinition] = Field(default_factory=list)
    edge_styles: list[DiagramEdgeStyleRule] = Field(default_factory=list)
    level_policies: list[DiagramLevelStylePolicy] = Field(default_factory=list)
    markdown: str = ""


class DiagramTargetProfile(ProvenancedModel):
    target_id: str
    target_product: str
    domain_pack_id: str = "specialty_chemicals"
    required_bfd_sections: list[str] = Field(default_factory=list)
    required_pfd_unit_families: list[str] = Field(default_factory=list)
    major_stream_roles: list[str] = Field(default_factory=list)
    preferred_template_families: list[str] = Field(default_factory=list)
    allowed_pfd_symbol_keys: list[str] = Field(default_factory=list)
    recycle_notation: str = "Recycle"
    purge_notation: str = "Purge"
    vent_notation: str = "Vent"
    waste_notation: str = "Waste"
    main_body_max_pfd_nodes: int = 8
    module_row_width_fraction: float = 0.72
    connector_mid_x_spacing_px: int = 28
    connector_lane_y_spacing_px: int = 18
    markdown: str = ""


class DiagramDomainPack(BaseModel):
    pack_id: str
    label: str
    match_tokens: list[str] = Field(default_factory=list)
    required_bfd_sections: list[str] = Field(default_factory=list)
    required_pfd_unit_families: list[str] = Field(default_factory=list)
    major_stream_roles: list[str] = Field(default_factory=list)
    preferred_template_families: list[str] = Field(default_factory=list)
    main_body_max_pfd_nodes: int = 8
    module_row_width_fraction: float = 0.72
    connector_mid_x_spacing_px: int = 28
    connector_lane_y_spacing_px: int = 18
    template_overrides: dict[str, DiagramEquipmentTemplate] = Field(default_factory=dict)
    allowed_pfd_symbol_keys: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DiagramDomainPackArtifact(ProvenancedModel):
    artifact_id: str
    packs: list[DiagramDomainPack] = Field(default_factory=list)
    markdown: str = ""


class DiagramLabel(BaseModel):
    text: str
    kind: Literal["primary", "secondary", "stream", "condition", "utility"] = "primary"


class DiagramLayoutHints(BaseModel):
    orientation: Literal["LR", "TB"] = "LR"
    rank: int = 0
    branch_level: int = 0
    sheet_id: str = "sheet_1"
    lane: str = "main"


class DiagramNode(BaseModel):
    node_id: str
    label: str
    node_family: str
    section_id: str = ""
    equipment_tag: str = ""
    labels: list[DiagramLabel] = Field(default_factory=list)
    layout: DiagramLayoutHints = Field(default_factory=DiagramLayoutHints)
    x: float = 0.0
    y: float = 0.0
    width: float = 180.0
    height: float = 72.0
    notes: str = ""


class DiagramEdge(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: Literal[
        "main",
        "product",
        "recycle",
        "purge",
        "vent",
        "waste",
        "side_draw",
        "utility",
        "control_signal",
        "safeguard",
        "continuation",
    ] = "main"
    stream_id: str = ""
    label: str = ""
    condition_label: str = ""
    sheet_id: str = "sheet_1"
    notes: str = ""


class DiagramSheet(BaseModel):
    sheet_id: str
    title: str
    width_px: int = 1400
    height_px: int = 520
    stitch_panel_id: str = ""
    stitch_panel_title: str = ""
    stitch_prev_sheet_id: str = ""
    stitch_next_sheet_id: str = ""
    drawing_number: str = ""
    sheet_number: str = ""
    revision: str = "A"
    revision_date: str = ""
    issue_status: str = "For Review"
    prepared_by: str = "AoC"
    checked_by: str = ""
    reviewed_by: str = ""
    approved_by: str = ""
    approved_date: str = ""
    orientation: Literal["portrait", "landscape"] = "landscape"
    presentation_mode: Literal["inline", "sheet"] = "sheet"
    preferred_scale: float = 1.0
    full_page: bool = True
    legend_mode: Literal["embedded", "suppressed"] = "embedded"
    suppress_inline_wrapping: bool = True
    node_ids: list[str] = Field(default_factory=list)
    edge_ids: list[str] = Field(default_factory=list)
    svg: str = ""


class PlantDiagramEntity(BaseModel):
    entity_id: str
    kind: DiagramEntityKind
    label: str
    diagram_level: DiagramLevel
    section_id: str = ""
    unit_id: str = ""
    stream_id: str = ""
    utility_id: str = ""
    control_id: str = ""
    instrument_id: str = ""
    equipment_tag: str = ""
    service: str = ""
    symbol_key: str = ""
    must_be_isolated: bool = False
    preferred_module_id: str = ""
    attached_to_entity_id: str = ""
    attachment_role: str = ""
    pid_function: str = ""
    pid_loop_id: str = ""
    line_class: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class PlantDiagramConnection(BaseModel):
    connection_id: str
    role: DiagramEdgeRole
    diagram_level: DiagramLevel
    source_entity_id: str
    target_entity_id: str
    stream_id: str = ""
    control_id: str = ""
    label: str = ""
    condition_label: str = ""
    must_route_externally: bool = False
    preferred_lane: str = "main"
    line_class: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class PlantDiagramSemanticsArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    entities: list[PlantDiagramEntity] = Field(default_factory=list)
    connections: list[PlantDiagramConnection] = Field(default_factory=list)
    section_order: list[str] = Field(default_factory=list)
    markdown: str = ""


class DiagramModulePort(BaseModel):
    port_id: str
    entity_id: str = ""
    connection_role: DiagramEdgeRole = DiagramEdgeRole.PROCESS
    template_port_role: str = ""
    side: DiagramPortSide
    order_index: int = 0
    lane: str = "main"
    label: str = ""


class DiagramEquipmentPortTemplate(BaseModel):
    port_role: str
    side: DiagramPortSide
    lane: str = "main"
    order_index: int = 0


class DiagramEquipmentTemplate(BaseModel):
    template_id: str
    family: str
    match_tokens: list[str] = Field(default_factory=list)
    node_family: str
    pfd_symbol_key: str
    pid_symbol_key: str = "pid_unit"
    default_width_px: int = 180
    default_height_px: int = 120
    ports: list[DiagramEquipmentPortTemplate] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DiagramEquipmentTemplateArtifact(ProvenancedModel):
    artifact_id: str
    templates: list[DiagramEquipmentTemplate] = Field(default_factory=list)
    markdown: str = ""


class DiagramModuleConstraint(BaseModel):
    key: Literal[
        "min_node_spacing_px",
        "min_label_clearance_px",
        "max_nodes",
        "max_edges",
        "max_crossings",
        "sheet_break_allowed",
        "orthogonal_only",
    ]
    value: str


class DiagramModuleSpec(BaseModel):
    module_id: str
    module_kind: DiagramLevel
    title: str
    symbol_policy: DiagramSymbolPolicy
    section_id: str = ""
    unit_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    connection_ids: list[str] = Field(default_factory=list)
    boundary_ports: list[DiagramModulePort] = Field(default_factory=list)
    allowed_edge_roles: list[DiagramEdgeRole] = Field(default_factory=list)
    forbidden_entity_kinds: list[DiagramEntityKind] = Field(default_factory=list)
    preferred_orientation: Literal["LR", "TB"] = "LR"
    sheet_break_allowed: bool = True
    must_be_isolated: bool = False
    constraints: list[DiagramModuleConstraint] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DiagramModuleArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    module_kind: DiagramLevel
    modules: list[DiagramModuleSpec] = Field(default_factory=list)
    markdown: str = ""


class DiagramModulePlacement(BaseModel):
    module_id: str
    sheet_id: str
    x: float
    y: float
    width: float
    height: float
    z_index: int = 0


class DiagramInterModuleConnector(BaseModel):
    connector_id: str
    role: DiagramEdgeRole
    source_module_id: str
    source_port_id: str
    target_module_id: str
    target_port_id: str
    label: str = ""
    continuation_marker: str = ""


class DiagramSheetComposition(BaseModel):
    sheet_id: str
    title: str
    diagram_level: DiagramLevel
    width_px: int = 1600
    height_px: int = 900
    stitch_panel_id: str = ""
    stitch_panel_title: str = ""
    stitch_prev_sheet_id: str = ""
    stitch_next_sheet_id: str = ""
    module_placements: list[DiagramModulePlacement] = Field(default_factory=list)
    connectors: list[DiagramInterModuleConnector] = Field(default_factory=list)
    legend_mode: Literal["embedded", "suppressed"] = "suppressed"
    title_block_mode: Literal["embedded", "suppressed"] = "embedded"


class DiagramSheetCompositionArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    diagram_level: DiagramLevel
    sheets: list[DiagramSheetComposition] = Field(default_factory=list)
    markdown: str = ""


class BlockFlowDiagramArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    nodes: list[DiagramNode] = Field(default_factory=list)
    edges: list[DiagramEdge] = Field(default_factory=list)
    sheets: list[DiagramSheet] = Field(default_factory=list)
    mermaid_fallback: str = ""
    markdown: str = ""


class ProcessFlowDiagramArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    nodes: list[DiagramNode] = Field(default_factory=list)
    edges: list[DiagramEdge] = Field(default_factory=list)
    sheets: list[DiagramSheet] = Field(default_factory=list)
    markdown: str = ""


class ControlSystemDiagramArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    sheets: list[DiagramSheet] = Field(default_factory=list)
    markdown: str = ""


class ControlCauseEffectRow(ProvenancedModel):
    control_id: str
    unit_id: str = ""
    controlled_variable: str = ""
    cause_permissive: str = ""
    action_shutdown: str = ""
    override_logic: str = ""
    safeguard_trip: str = ""
    protected_final_action: str = ""
    criticality: str = ""
    safety_critical: bool = False


class ControlCauseEffectArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str
    rows: list[ControlCauseEffectRow] = Field(default_factory=list)
    markdown: str = ""


class DiagramRoutePoint(BaseModel):
    x: float
    y: float


class DiagramRouteHint(BaseModel):
    edge_id: str
    points: list[DiagramRoutePoint] = Field(default_factory=list)
    label_x: float = 0.0
    label_y: float = 0.0
    condition_x: float = 0.0
    condition_y: float = 0.0


class DiagramContinuationMarker(BaseModel):
    x: float
    y: float
    side: Literal["left", "right"] = "right"
    label: str = ""
    target_sheet: str = ""


class DiagramRoutingSheet(BaseModel):
    sheet_id: str
    route_hints: list[DiagramRouteHint] = Field(default_factory=list)
    continuation_markers: list[DiagramContinuationMarker] = Field(default_factory=list)
    crossing_count: int = 0
    congested_connector_count: int = 0
    max_channel_load: int = 0


class DiagramRoutingArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    diagram_level: DiagramLevel
    sheets: list[DiagramRoutingSheet] = Field(default_factory=list)
    markdown: str = ""


class PidLiteDiagramArtifact(ProvenancedModel):
    diagram_id: str
    route_id: str
    nodes: list[DiagramNode] = Field(default_factory=list)
    edges: list[DiagramEdge] = Field(default_factory=list)
    sheets: list[DiagramSheet] = Field(default_factory=list)
    markdown: str = ""


class DiagramAcceptanceArtifact(ProvenancedModel):
    diagram_id: str
    diagram_kind: Literal["bfd", "pfd"]
    overall_status: Literal["complete", "conditional", "blocked"] = "conditional"
    missing_required_nodes: list[str] = Field(default_factory=list)
    missing_required_edges: list[str] = Field(default_factory=list)
    mismatched_labels: list[str] = Field(default_factory=list)
    benchmark_cleanliness_score: float = 1.0
    node_overlap_count: int = 0
    node_label_overlap_count: int = 0
    crowded_sheet_count: int = 0
    max_sheet_utilization_fraction: float = 0.0
    missing_drafting_field_count: int = 0
    duplicate_drawing_number_count: int = 0
    duplicate_sheet_number_count: int = 0
    missing_title_block_count: int = 0
    title_block_overlap_count: int = 0
    warning_issue_codes: list[str] = Field(default_factory=list)
    blocking_issue_codes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class BACDiagramBenchmarkRow(ProvenancedModel):
    diagram_kind: Literal["bfd", "pfd", "pid", "drawio"]
    status: Literal["pass", "warning", "fail"] = "warning"
    checks_passed: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    blocking_codes: list[str] = Field(default_factory=list)
    summary: str = ""


class BACDiagramBenchmarkArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str
    benchmark_profile: str = "benzalkonium_chloride"
    overall_status: Literal["complete", "conditional", "blocked"] = "conditional"
    rows: list[BACDiagramBenchmarkRow] = Field(default_factory=list)
    benchmark_labels: list[str] = Field(default_factory=list)
    markdown: str = ""


class BACRenderingAuditRow(ProvenancedModel):
    diagram_kind: Literal["bfd", "pfd", "pid"]
    status: Literal["pass", "warning", "fail"] = "warning"
    sheet_count: int = 0
    benchmark_cleanliness_score: float = 1.0
    route_crossings: int = 0
    route_congestion: int = 0
    max_channel_load: int = 0
    continuation_marker_count: int = 0
    missing_title_block_count: int = 0
    title_block_overlap_count: int = 0
    findings: list[str] = Field(default_factory=list)
    summary: str = ""


class BACRenderingAuditArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str
    overall_status: Literal["complete", "conditional", "blocked"] = "conditional"
    rows: list[BACRenderingAuditRow] = Field(default_factory=list)
    audit_scope: list[str] = Field(default_factory=list)
    markdown: str = ""


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


class FormatterChapterGroup(BaseModel):
    group_id: str
    target_title: str
    source_chapter_ids: list[str] = Field(default_factory=list)
    numbered: bool = True


class BenchmarkStyleProfile(ProvenancedModel):
    style_id: str
    style_name: str
    benchmark_labels: list[str] = Field(default_factory=list)
    body_font_family: str
    heading_font_family: str
    cover_font_family: str
    chapter_title_pattern: str
    front_matter_sections: list[str] = Field(default_factory=list)
    preferred_margin_pt: float = 48.0
    preferred_body_font_size_pt: float = 12.0
    preferred_heading_sizes_pt: list[float] = Field(default_factory=list)
    markdown: str = ""


class BenchmarkVoiceProfile(ProvenancedModel):
    voice_id: str
    voice_name: str
    benchmark_labels: list[str] = Field(default_factory=list)
    tone_summary: str = ""
    preferred_sentence_patterns: list[str] = Field(default_factory=list)
    preferred_transition_patterns: list[str] = Field(default_factory=list)
    preferred_paragraph_traits: list[str] = Field(default_factory=list)
    discouraged_phrases: list[str] = Field(default_factory=list)
    discouraged_styles: list[str] = Field(default_factory=list)
    chapter_voice_notes: dict[str, str] = Field(default_factory=dict)
    markdown: str = ""


class SentencePatternLibrary(ProvenancedModel):
    library_id: str
    voice_id: str
    chapter_sentence_patterns: dict[str, list[str]] = Field(default_factory=dict)
    transition_patterns: list[str] = Field(default_factory=list)
    anti_pattern_replacements: dict[str, str] = Field(default_factory=dict)
    markdown: str = ""


class ToneStyleRules(ProvenancedModel):
    rules_id: str
    voice_id: str
    rewrite_safe_block_roles: list[str] = Field(default_factory=list)
    protected_content_types: list[str] = Field(default_factory=list)
    chapter_template_expectations: dict[str, list[str]] = Field(default_factory=dict)
    chapter_transition_templates: dict[str, list[str]] = Field(default_factory=dict)
    chapter_table_discussion_templates: dict[str, list[str]] = Field(default_factory=dict)
    anti_pattern_replacements: dict[str, str] = Field(default_factory=dict)
    cadence_rules: list[str] = Field(default_factory=list)
    markdown: str = ""


class FormatterTargetProfile(ProvenancedModel):
    target_id: str
    style_id: str
    benchmark_id: str
    chapter_groups: list[FormatterChapterGroup] = Field(default_factory=list)
    appendix_heading_style: str = "Appendix {label}: {title}"
    markdown: str = ""


class SemanticBlock(BaseModel):
    block_id: str
    kind: Literal["heading", "paragraph", "table", "list", "figure", "code", "note"]
    role: Literal[
        "front_matter",
        "narrative",
        "summary_table",
        "evidence_table",
        "appendix_only",
        "reference",
        "annexure",
        "equation_like",
        "list",
    ] = "narrative"
    title: str = ""
    heading_level: int = 0
    markdown: str
    citations: list[str] = Field(default_factory=list)


class SemanticSection(BaseModel):
    section_id: str
    source_chapter_id: str
    title: str
    citations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    blocks: list[SemanticBlock] = Field(default_factory=list)


class SemanticReportArtifact(ProvenancedModel):
    report_id: str
    style_id: str
    target_id: str
    raw_markdown_path: str
    sections: list[SemanticSection] = Field(default_factory=list)
    appendix_sections: list[SemanticSection] = Field(default_factory=list)
    markdown: str = ""


class NarrativeRewriteBlock(BaseModel):
    block_id: str
    source_chapter_id: str
    chapter_title: str
    block_kind: str
    block_role: str
    rewrite_mode: Literal["aggressive", "light", "protect"] = "light"
    protection_reasons: list[str] = Field(default_factory=list)
    preserved_tokens: list[str] = Field(default_factory=list)
    recommended_focus: list[str] = Field(default_factory=list)
    original_markdown: str = ""


class NarrativeRewriteArtifact(ProvenancedModel):
    rewrite_id: str
    voice_id: str
    rules_id: str
    block_plans: list[NarrativeRewriteBlock] = Field(default_factory=list)
    aggressive_block_count: int = 0
    light_block_count: int = 0
    protected_block_count: int = 0
    protected_content_summary: list[str] = Field(default_factory=list)
    markdown: str = ""


class FormattedReportArtifact(ProvenancedModel):
    formatter_id: str
    target_id: str
    formatted_markdown: str
    formatted_html: str
    chapter_titles: list[str] = Field(default_factory=list)
    appendix_titles: list[str] = Field(default_factory=list)
    markdown: str = ""


class FormatterDecisionArtifact(ProvenancedModel):
    formatter_id: str
    decisions: list[str] = Field(default_factory=list)
    preserved_artifact_refs: list[str] = Field(default_factory=list)
    moved_appendix_sections: list[str] = Field(default_factory=list)
    markdown: str = ""


class FormatterParityArtifact(ProvenancedModel):
    style_id: str
    target_id: str
    structure_status: ReportParityStatus = ReportParityStatus.PARTIAL
    tone_status: ReportParityStatus = ReportParityStatus.PARTIAL
    citation_status: ReportParityStatus = ReportParityStatus.PARTIAL
    numeric_status: ReportParityStatus = ReportParityStatus.PARTIAL
    chapter_coverage_status: ReportParityStatus = ReportParityStatus.PARTIAL
    appendix_placement_status: ReportParityStatus = ReportParityStatus.PARTIAL
    table_figure_status: ReportParityStatus = ReportParityStatus.PARTIAL
    chapter_specificity_status: ReportParityStatus = ReportParityStatus.PARTIAL
    typography_layout_status: ReportParityStatus = ReportParityStatus.PARTIAL
    numeric_preservation_ratio: float = 0.0
    citation_preservation_ratio: float = 0.0
    structure_parity_score: float = 0.0
    table_figure_parity_score: float = 0.0
    chapter_specificity_score: float = 0.0
    typography_layout_score: float = 0.0
    overall_parity_score: float = 0.0
    moved_appendix_block_count: int = 0
    missing_chapter_ids: list[str] = Field(default_factory=list)
    parity_notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class FormatterAcceptanceArtifact(ProvenancedModel):
    overall_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    structure_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    citation_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    numeric_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    appendix_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    benchmark_parity_status: ReportAcceptanceStatus = ReportAcceptanceStatus.CONDITIONAL
    overall_parity_score: float = 0.0
    notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class FinalReport(BaseModel):
    project_id: str
    markdown_path: str
    raw_markdown_path: Optional[str] = None
    formatted_markdown_path: Optional[str] = None
    formatted_html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    formatted_pdf_path: Optional[str] = None
    style_profile_id: Optional[str] = None
    formatter_target_id: Optional[str] = None
    references: list[str] = Field(default_factory=list)
    annexure_paths: list[str] = Field(default_factory=list)
    diagram_svg_paths: list[str] = Field(default_factory=list)
    diagram_drawio_paths: list[str] = Field(default_factory=list)


class DiagramDeliveryManifestArtifact(ProvenancedModel):
    manifest_id: str
    project_id: str
    architecture_status: Literal["modular_default"] = "modular_default"
    svg_source_of_truth: bool = True
    drawio_export_enabled: bool = True
    bfd_svg_paths: list[str] = Field(default_factory=list)
    pfd_svg_paths: list[str] = Field(default_factory=list)
    control_svg_paths: list[str] = Field(default_factory=list)
    pid_lite_svg_paths: list[str] = Field(default_factory=list)
    drawio_paths: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    markdown: str = ""


class BACDrawingRegisterRow(ProvenancedModel):
    diagram_kind: Literal["bfd", "pfd", "pid", "control"]
    sheet_id: str
    title: str
    drawing_number: str = ""
    sheet_number: str = ""
    issue_status: str = ""
    checked_by: str = ""
    reviewed_by: str = ""
    approved_by: str = ""
    approved_date: str = ""
    svg_path: str = ""
    drawio_path: str = ""


class BACDrawingPackageArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str
    package_profile: str = "benzalkonium_chloride"
    overall_status: Literal["complete", "conditional", "blocked"] = "conditional"
    benchmark_status: str = ""
    review_workflow_status: Literal["draft", "for_review", "approved", "as_built"] = "draft"
    revision_history: list[str] = Field(default_factory=list)
    checker: str = ""
    reviewer: str = ""
    approver: str = ""
    svg_paths: list[str] = Field(default_factory=list)
    drawio_paths: list[str] = Field(default_factory=list)
    register_rows: list[BACDrawingRegisterRow] = Field(default_factory=list)
    package_notes: list[str] = Field(default_factory=list)
    markdown: str = ""
