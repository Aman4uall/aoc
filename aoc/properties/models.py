from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from aoc.models import DecisionRecord, ProvenanceTag, ProvenancedModel, SensitivityLevel


class ChemicalIdentifier(ProvenancedModel):
    identifier_id: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    formula: Optional[str] = None
    cas_number: Optional[str] = None
    route_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    confidence: float = 1.0


class PureComponentProperty(ProvenancedModel):
    property_id: str
    identifier_id: str
    property_name: str
    value: str
    units: str
    reference_temperature_c: Optional[float] = None
    reference_pressure_bar: Optional[float] = None
    source_ids: list[str] = Field(default_factory=list)
    provenance_method: ProvenanceTag = ProvenanceTag.SOURCED
    blocking: bool = False
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    confidence: float = 1.0


class PropertyCorrelation(ProvenancedModel):
    correlation_id: str
    identifier_id: str
    property_name: str
    equation_name: str
    parameters: dict[str, float | str] = Field(default_factory=dict)
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    pressure_basis_bar: Optional[float] = None
    source_ids: list[str] = Field(default_factory=list)
    provenance_method: ProvenanceTag = ProvenanceTag.SOURCED
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    confidence: float = 1.0


class BinaryInteractionParameter(ProvenancedModel):
    bip_id: str
    component_a_id: str
    component_b_id: str
    component_a_name: str
    component_b_name: str
    model_name: str = "NRTL"
    tau12: Optional[float] = None
    tau21: Optional[float] = None
    alpha12: Optional[float] = None
    source_ids: list[str] = Field(default_factory=list)
    provenance_method: ProvenanceTag = ProvenanceTag.SOURCED
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    confidence: float = 1.0
    notes: list[str] = Field(default_factory=list)


class HenryLawConstant(ProvenancedModel):
    constant_id: str
    gas_component_id: str
    solvent_component_id: str
    gas_component_name: str
    solvent_component_name: str
    value: float
    units: str = "bar"
    reference_temperature_c: Optional[float] = None
    equation_form: str = "P=H*x"
    source_ids: list[str] = Field(default_factory=list)
    provenance_method: ProvenanceTag = ProvenanceTag.SOURCED
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    confidence: float = 1.0
    notes: list[str] = Field(default_factory=list)


class SolubilityCurve(ProvenancedModel):
    curve_id: str
    solute_component_id: str
    solvent_component_id: str
    solute_component_name: str
    solvent_component_name: str
    equation_name: str = "linear"
    parameters: dict[str, float | str] = Field(default_factory=dict)
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    units: str = "kg_solute_per_kg_solvent"
    source_ids: list[str] = Field(default_factory=list)
    provenance_method: ProvenanceTag = ProvenanceTag.SOURCED
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    confidence: float = 1.0
    notes: list[str] = Field(default_factory=list)


class PropertyPackage(ProvenancedModel):
    package_id: str
    identifier: ChemicalIdentifier
    molecular_weight: Optional[PureComponentProperty] = None
    normal_boiling_point: Optional[PureComponentProperty] = None
    melting_point: Optional[PureComponentProperty] = None
    liquid_density: Optional[PureComponentProperty] = None
    liquid_viscosity: Optional[PureComponentProperty] = None
    liquid_heat_capacity: Optional[PureComponentProperty] = None
    heat_of_vaporization: Optional[PureComponentProperty] = None
    thermal_conductivity: Optional[PureComponentProperty] = None
    vapor_pressure_correlation: Optional[PropertyCorrelation] = None
    antoine_correlation: Optional[PropertyCorrelation] = None
    resolution_status: Literal["resolved", "estimated", "blocked"] = "resolved"
    blocked_properties: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PropertyPackageArtifact(ProvenancedModel):
    identifiers: list[ChemicalIdentifier] = Field(default_factory=list)
    packages: list[PropertyPackage] = Field(default_factory=list)
    primary_route_ids: list[str] = Field(default_factory=list)
    primary_identifier_ids: list[str] = Field(default_factory=list)
    unresolved_identifier_ids: list[str] = Field(default_factory=list)
    blocked_property_ids: list[str] = Field(default_factory=list)
    correlations: list[PropertyCorrelation] = Field(default_factory=list)
    binary_interaction_parameters: list[BinaryInteractionParameter] = Field(default_factory=list)
    unresolved_binary_pairs: list[str] = Field(default_factory=list)
    henry_law_constants: list[HenryLawConstant] = Field(default_factory=list)
    unresolved_henry_pairs: list[str] = Field(default_factory=list)
    solubility_curves: list[SolubilityCurve] = Field(default_factory=list)
    unresolved_solubility_pairs: list[str] = Field(default_factory=list)
    markdown: str


class MixturePropertyPackage(ProvenancedModel):
    mixture_id: str
    unit_id: str
    state_id: str
    dominant_phase: str = ""
    component_mass_fraction: dict[str, float] = Field(default_factory=dict)
    component_package_ids: dict[str, str] = Field(default_factory=dict)
    liquid_heat_capacity_kj_kg_k: Optional[float] = None
    liquid_density_kg_m3: Optional[float] = None
    liquid_viscosity_pa_s: Optional[float] = None
    heat_of_vaporization_kj_kg: Optional[float] = None
    thermal_conductivity_w_m_k: Optional[float] = None
    resolution_status: Literal["resolved", "estimated", "blocked"] = "estimated"
    estimated_properties: list[str] = Field(default_factory=list)
    blocking_properties: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class MixturePropertyArtifact(ProvenancedModel):
    packages: list[MixturePropertyPackage] = Field(default_factory=list)
    blocked_unit_ids: list[str] = Field(default_factory=list)
    markdown: str


class PropertyRequirement(ProvenancedModel):
    requirement_id: str
    stage_id: str
    unit_family: str
    property_name: str
    allow_estimated: bool = False
    optional: bool = False
    sensitivity: SensitivityLevel = SensitivityLevel.HIGH
    blocking: bool = True
    notes: str = ""


class PropertyRequirementCoverage(ProvenancedModel):
    coverage_id: str
    stage_id: str
    identifier_id: str
    property_name: str
    status: Literal["covered", "estimated", "blocked", "missing"] = "covered"
    allow_estimated: bool = False
    blocking: bool = True
    source_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class PropertyRequirementSet(ProvenancedModel):
    requirements: list[PropertyRequirement] = Field(default_factory=list)
    coverage: list[PropertyRequirementCoverage] = Field(default_factory=list)
    blocked_requirement_ids: list[str] = Field(default_factory=list)
    blocked_stage_ids: list[str] = Field(default_factory=list)
    markdown: str


class PropertyMethodDecision(ProvenancedModel):
    decision: DecisionRecord
    selected_property_package_ids: list[str] = Field(default_factory=list)
    blocked_requirement_ids: list[str] = Field(default_factory=list)
    markdown: str


class PropertyEstimateSummary(BaseModel):
    identifier_id: str
    property_name: str
    rationale: str


class ComponentKValue(ProvenancedModel):
    estimate_id: str
    identifier_id: str
    component_name: str
    temperature_c: float
    pressure_bar: float
    vapor_pressure_bar: float = 0.0
    activity_coefficient: float = 1.0
    k_value: float = 0.0
    method: str = ""
    activity_model: str = "ideal_raoult"
    binary_pair_id: Optional[str] = None
    resolution_status: Literal["resolved", "estimated", "blocked"] = "estimated"


class RelativeVolatilityEstimate(ProvenancedModel):
    estimate_id: str
    light_key_identifier_id: str
    heavy_key_identifier_id: str
    light_key: str
    heavy_key: str
    top_alpha: float = 0.0
    bottom_alpha: float = 0.0
    average_alpha: float = 0.0
    method: str = ""
    feasible: bool = True
    notes: list[str] = Field(default_factory=list)


class SeparationThermoArtifact(ProvenancedModel):
    artifact_id: str
    route_id: str
    separation_family: str
    system_pressure_bar: float
    nominal_top_temp_c: float
    nominal_bottom_temp_c: float
    light_key: str
    heavy_key: str
    activity_model: str = "ideal_raoult"
    top_k_values: list[ComponentKValue] = Field(default_factory=list)
    bottom_k_values: list[ComponentKValue] = Field(default_factory=list)
    binary_interaction_parameters: list[BinaryInteractionParameter] = Field(default_factory=list)
    missing_binary_pairs: list[str] = Field(default_factory=list)
    fallback_notes: list[str] = Field(default_factory=list)
    relative_volatility: Optional[RelativeVolatilityEstimate] = None
    blocked_component_ids: list[str] = Field(default_factory=list)
    markdown: str = ""
