from __future__ import annotations

import re

from aoc.calculators import operating_hours_per_year, reaction_balance_delta, reaction_is_balanced
from aoc.models import (
    BACDrawingPackageArtifact,
    BACDiagramBenchmarkArtifact,
    BACImpurityLedgerArtifact,
    BACImpurityModelArtifact,
    BACPurificationSectionArtifact,
    BACRenderingAuditArtifact,
    BenchmarkManifest,
    ChemistryFamilyAdapter,
    ChemistryDecisionArtifact,
    ChapterArtifact,
    ClaimGraphArtifact,
    ClaimStatus,
    DesignConfidenceArtifact,
    DocumentFactCollectionArtifact,
    EconomicCoverageDecision,
    FlowsheetIntentArtifact,
    ReportAcceptanceArtifact,
    ReportAcceptanceStatus,
    ReportParityArtifact,
    ReportParityFrameworkArtifact,
    ColumnDesign,
    ControlPlanArtifact,
    ControlArchitectureDecision,
    CostModel,
    DecisionRecord,
    DiagramEdgeRole,
    DiagramEntityKind,
    DiagramLevel,
    DiagramDomainPackArtifact,
    DiagramModuleArtifact,
    DiagramLabel,
    DiagramNode,
    DiagramSheet,
    DiagramSheetCompositionArtifact,
    DiagramSymbolLibraryArtifact,
    DiagramSymbolPolicy,
    DiagramTargetProfile,
    EnergyBalance,
    FinancialModel,
    FlowsheetBlueprintArtifact,
    FlowsheetCase,
    FlowsheetGraph,
    GeographicScope,
    HazopNodeRegister,
    HeatExchangerDesign,
    HeatIntegrationStudyArtifact,
    IndianLocationDatum,
    IndianPriceDatum,
    KineticAssessmentArtifact,
    KineticsAdmissibilityArtifact,
    MechanicalDesignArtifact,
    MethodSelectionArtifact,
    OperationsPlanningArtifact,
    MissingDataAcceptanceArtifact,
    ProcessArchetype,
    PlantDiagramSemanticsArtifact,
    PropertyGapArtifact,
    PropertyDemandPlan,
    ProvenanceTag,
    ProjectConfig,
    ProjectRunState,
    PropertyRecord,
    ReactionNetworkV2Artifact,
    ReactionSystem,
    ReactorDesign,
    ResearchBundle,
    ResolvedSourceSet,
    ResolvedValueArtifact,
    RevisionLedgerArtifact,
    CommercialProductBasisArtifact,
    RouteDiscoveryArtifact,
    RouteFamilyArtifact,
    RouteChemistryArtifact,
    RouteEconomicBasisArtifact,
    RouteProcessClaimsArtifact,
    RouteScreeningArtifact,
    RouteSiteFitArtifact,
    RouteSelectionComparisonArtifact,
    RouteSelectionArtifact,
    ScientificGateMatrixArtifact,
    ScientificGateStatus,
    SiteSelectionArtifact,
    ScenarioStability,
    Severity,
    SparseDataPolicyArtifact,
    SpeciesResolutionArtifact,
    SourceDomain,
    SourceRecord,
    StreamTable,
    ThermoAssessmentArtifact,
    ThermoAdmissibilityArtifact,
    TopologyCandidateArtifact,
    UnitTrainConsistencyArtifact,
    UnitTrainCandidateSet,
    UnitOperationFamilyArtifact,
    UtilitySummaryArtifact,
    UtilityArchitectureDecision,
    UtilityNetworkDecision,
    ValidationIssue,
    WorkingCapitalModel,
    SensitivityLevel,
    InferenceQuestionQueueArtifact,
)
from aoc.properties.sources import normalize_chemical_name
from aoc.properties import active_identifier_ids_for_route, requirement_failures_for_stage
from aoc.properties.models import MixturePropertyArtifact, PropertyMethodDecision, PropertyPackageArtifact, PropertyRequirementSet, SeparationThermoArtifact


def _normalize_site_label(value: str) -> str:
    normalized = normalize_chemical_name(value)
    replacements = {
        "petroleum_chemicals_and_petrochemicals_investment_region": "pcpir",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def require_source_ids(citation_ids: list[str], available_source_ids: set[str], artifact_ref: str, code: str) -> list[ValidationIssue]:
    missing = sorted({citation_id for citation_id in citation_ids if citation_id not in available_source_ids})
    if not missing:
        return []
    return [
        ValidationIssue(
            code=code,
            severity=Severity.BLOCKED,
            message=f"Missing source records for citations: {', '.join(missing)}.",
            artifact_ref=artifact_ref,
            source_refs=missing,
        )
    ]


def validate_property_records(properties: list[PropertyRecord], available_source_ids: set[str], strict: bool) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    critical = {"molecular weight", "melting point", "boiling point", "density"}
    observed = {item.name.strip().lower() for item in properties}
    missing = sorted(critical - observed)
    if strict and missing:
        issues.append(
            ValidationIssue(
                code="missing_critical_properties",
                severity=Severity.BLOCKED,
                message=f"Missing critical product properties: {', '.join(item.title() for item in missing)}.",
                artifact_ref="product_profile",
            )
        )
    for item in properties:
        issues.extend(require_source_ids(item.supporting_sources or item.citations, available_source_ids, "product_profile", "missing_property_sources"))
    return issues


def validate_property_gap_artifact(property_gap: PropertyGapArtifact, config: ProjectConfig) -> list[ValidationIssue]:
    if not config.uncertainty_policy.high_sensitivity_blocks:
        return []
    if not property_gap.unresolved_high_sensitivity:
        return []
    return [
        ValidationIssue(
            code="unresolved_high_sensitivity_values",
            severity=Severity.BLOCKED,
            message="High-sensitivity values remain unresolved: " + ", ".join(property_gap.unresolved_high_sensitivity) + ".",
            artifact_ref="property_gap",
        )
    ]


def validate_value_records(
    value_records,
    available_source_ids: set[str],
    config: ProjectConfig,
    artifact_ref: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for value in value_records:
        if value.source_ids:
            issues.extend(require_source_ids(value.source_ids, available_source_ids, artifact_ref, "missing_value_sources"))
        elif config.strict_citation_policy and value.provenance_method in {
            ProvenanceTag.SOURCED,
            ProvenanceTag.ESTIMATED,
            ProvenanceTag.ANALOGY,
            ProvenanceTag.USER_SUPPLIED,
        } and value.sensitivity in {SensitivityLevel.HIGH, SensitivityLevel.MEDIUM}:
            issues.append(
                ValidationIssue(
                    code="uncited_value_record",
                    severity=Severity.BLOCKED,
                    message=f"Value '{value.name}' in '{artifact_ref}' has no source ids.",
                    artifact_ref=artifact_ref,
                )
            )
        if config.uncertainty_policy.high_sensitivity_blocks and value.sensitivity == SensitivityLevel.HIGH and value.blocking:
            issues.append(
                ValidationIssue(
                    code="blocking_high_sensitivity_value",
                    severity=Severity.BLOCKED,
                    message=f"High-sensitivity value '{value.name}' remains blocked in '{artifact_ref}'.",
                    artifact_ref=artifact_ref,
                    source_refs=value.source_ids,
                )
            )
    return issues


def validate_resolved_source_set(
    resolved_sources: ResolvedSourceSet,
    available_source_ids: set[str],
    config: ProjectConfig,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(require_source_ids(resolved_sources.selected_source_ids, available_source_ids, "resolved_sources", "missing_resolved_sources"))
    if config.require_india_only_data and resolved_sources.unresolved_conflicts:
        issues.append(
            ValidationIssue(
                code="unresolved_source_conflicts",
                severity=Severity.BLOCKED,
                message="Source conflicts remain for: " + ", ".join(resolved_sources.unresolved_conflicts) + ".",
                artifact_ref="resolved_sources",
                source_refs=resolved_sources.selected_source_ids,
            )
        )
    return issues


def validate_resolved_value_artifact(
    resolved_values: ResolvedValueArtifact,
    available_source_ids: set[str],
    config: ProjectConfig,
) -> list[ValidationIssue]:
    issues = validate_value_records(resolved_values.values, available_source_ids, config, "resolved_values")
    if config.evidence_lock_required and resolved_values.unresolved_value_ids:
        issues.append(
            ValidationIssue(
                code="evidence_lock_unresolved_values",
                severity=Severity.BLOCKED,
                message="Evidence lock cannot pass while unresolved values remain: " + ", ".join(resolved_values.unresolved_value_ids) + ".",
                artifact_ref="resolved_values",
            )
        )
    return issues


def validate_property_package_artifact(
    property_packages: PropertyPackageArtifact,
    available_source_ids: set[str],
    config: ProjectConfig,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not property_packages.packages:
        issues.append(
            ValidationIssue(
                code="missing_property_packages",
                severity=Severity.BLOCKED,
                message="Property Engine did not build any component packages.",
                artifact_ref="property_packages",
            )
        )
        return issues
    for package in property_packages.packages:
        for prop in (
            package.molecular_weight,
            package.normal_boiling_point,
            package.melting_point,
            package.liquid_density,
            package.liquid_viscosity,
            package.liquid_heat_capacity,
            package.heat_of_vaporization,
            package.thermal_conductivity,
        ):
            if prop is None:
                continue
            if prop.source_ids:
                issues.extend(require_source_ids(prop.source_ids, available_source_ids, "property_packages", "missing_property_package_sources"))
            elif prop.provenance_method in {
                ProvenanceTag.SOURCED,
                ProvenanceTag.CALCULATED,
                ProvenanceTag.ESTIMATED,
            } and config.strict_citation_policy and not prop.blocking:
                issues.append(
                    ValidationIssue(
                        code="uncited_property_package_value",
                        severity=Severity.BLOCKED,
                        message=f"Property package value '{package.identifier.canonical_name} {prop.property_name}' has no source ids.",
                        artifact_ref="property_packages",
                    )
                )
    for bip in property_packages.binary_interaction_parameters:
        if bip.source_ids:
            issues.extend(require_source_ids(bip.source_ids, available_source_ids, "property_packages", "missing_binary_interaction_sources"))
        elif bip.resolution_status == "resolved" and config.strict_citation_policy:
            issues.append(
                ValidationIssue(
                    code="uncited_binary_interaction_parameter",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Binary interaction parameter '{bip.component_a_name} / {bip.component_b_name}' is marked resolved without source ids."
                    ),
                    artifact_ref="property_packages",
                )
            )
    for constant in property_packages.henry_law_constants:
        if constant.source_ids:
            issues.extend(require_source_ids(constant.source_ids, available_source_ids, "property_packages", "missing_henry_sources"))
        elif constant.resolution_status == "resolved" and config.strict_citation_policy:
            issues.append(
                ValidationIssue(
                    code="uncited_henry_constant",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Henry-law constant '{constant.gas_component_name} in {constant.solvent_component_name}' is marked resolved without source ids."
                    ),
                    artifact_ref="property_packages",
                )
            )
    for curve in property_packages.solubility_curves:
        if curve.source_ids:
            issues.extend(require_source_ids(curve.source_ids, available_source_ids, "property_packages", "missing_solubility_sources"))
        elif curve.resolution_status == "resolved" and config.strict_citation_policy:
            issues.append(
                ValidationIssue(
                    code="uncited_solubility_curve",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Solubility curve '{curve.solute_component_name} in {curve.solvent_component_name}' is marked resolved without source ids."
                    ),
                    artifact_ref="property_packages",
                )
            )
    return issues


def validate_property_requirement_set(requirement_set: PropertyRequirementSet) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not requirement_set.requirements:
        issues.append(
            ValidationIssue(
                code="missing_property_requirements",
                severity=Severity.BLOCKED,
                message="No property requirement set was generated for downstream stages.",
                artifact_ref="property_requirements",
            )
        )
    return issues


def validate_sparse_data_policy(policy: SparseDataPolicyArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not policy.policy_id:
        issues.append(
            ValidationIssue(
                code="missing_sparse_data_policy_id",
                severity=Severity.BLOCKED,
                message="Sparse-data policy must include a policy id.",
                artifact_ref="sparse_data_policy",
            )
        )
    if not policy.adapter_id:
        issues.append(
            ValidationIssue(
                code="missing_sparse_data_policy_adapter",
                severity=Severity.BLOCKED,
                message="Sparse-data policy must reference the chemistry-family adapter.",
                artifact_ref="sparse_data_policy",
            )
        )
    if not policy.rules:
        issues.append(
            ValidationIssue(
                code="missing_sparse_data_policy_rules",
                severity=Severity.BLOCKED,
                message="Sparse-data policy must define at least one fallback rule.",
                artifact_ref="sparse_data_policy",
            )
        )
    return issues


def validate_sparse_data_policy_for_stage(
    stage_id: str,
    policy: SparseDataPolicyArtifact | None,
) -> list[ValidationIssue]:
    if policy is None:
        return []
    issues: list[ValidationIssue] = []
    for rule in policy.rules:
        if rule.stage_id != stage_id:
            continue
        if rule.current_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="sparse_data_policy_blocked",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Stage '{stage_id}' violates sparse-data rule '{rule.subject}' for "
                        f"'{policy.family_label}': {', '.join(rule.triggered_items[:3]) or rule.rationale}."
                    ),
                    artifact_ref="sparse_data_policy",
                )
            )
        elif rule.current_status == "warning":
            issues.append(
                ValidationIssue(
                    code="sparse_data_policy_warning",
                    severity=Severity.WARNING,
                    message=(
                        f"Stage '{stage_id}' is proceeding under sparse-data warning '{rule.subject}' for "
                        f"'{policy.family_label}': {', '.join(rule.triggered_items[:3]) or rule.rationale}."
                    ),
                    artifact_ref="sparse_data_policy",
                )
            )
    return issues


def validate_property_method_decision(property_method: PropertyMethodDecision) -> list[ValidationIssue]:
    return validate_decision_record(property_method.decision, "property_method_decision")


def validate_property_requirements_for_stage(
    stage_id: str,
    requirement_set: PropertyRequirementSet,
    property_packages: PropertyPackageArtifact,
    route,
    product_name: str | None = None,
    mixture_properties: MixturePropertyArtifact | None = None,
    relevant_unit_ids: list[str] | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    active_ids = active_identifier_ids_for_route(property_packages, route, product_name)
    failures = requirement_failures_for_stage(requirement_set, stage_id, active_ids)
    for failure in failures:
        issues.append(
            ValidationIssue(
                code="property_requirement_failure",
                severity=Severity.BLOCKED,
                message=(
                    f"Stage '{stage_id}' is missing a usable '{failure.property_name}' basis for identifier "
                    f"'{failure.identifier_id}' ({failure.status})."
                ),
                artifact_ref=stage_id,
                source_refs=failure.source_ids,
            )
        )
    blocked_unit_ids = set(mixture_properties.blocked_unit_ids) if mixture_properties is not None else set()
    if relevant_unit_ids:
        blocked_unit_ids &= set(relevant_unit_ids)
    if blocked_unit_ids:
        blocked_units = ", ".join(sorted(blocked_unit_ids))
        issues.append(
            ValidationIssue(
                code="blocked_mixture_properties",
                severity=Severity.BLOCKED,
                message=f"Stage '{stage_id}' has blocked mixture-property packages for units: {blocked_units}.",
                artifact_ref=stage_id,
            )
        )
    return issues


def validate_mixture_property_artifact(mixture_properties: MixturePropertyArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not mixture_properties.packages:
        issues.append(
            ValidationIssue(
                code="missing_mixture_properties",
                severity=Severity.BLOCKED,
                message="No mixture-property packages were generated from the solved composition states.",
                artifact_ref="mixture_properties",
            )
        )
    return issues


def validate_separation_thermo_artifact(separation_thermo: SeparationThermoArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if separation_thermo.relative_volatility is None:
        issues.append(
            ValidationIssue(
                code="missing_separation_thermo",
                severity=Severity.BLOCKED,
                message="No separation-thermodynamics artifact was generated.",
                artifact_ref="separation_thermo",
            )
        )
        return issues
    key_names = {separation_thermo.light_key.lower(), separation_thermo.heavy_key.lower()}
    blocked_key_components = [
        item for item in separation_thermo.blocked_component_ids if item.replace("_", " ").lower() in key_names
    ]
    if blocked_key_components and separation_thermo.separation_family in {"distillation", "absorption", "extraction"}:
        issues.append(
            ValidationIssue(
                code="blocked_separation_thermo_components",
                severity=Severity.BLOCKED,
                message="Separation thermodynamics is blocked for key components: " + ", ".join(blocked_key_components) + ".",
                artifact_ref="separation_thermo",
                source_refs=separation_thermo.citations,
            )
        )
    if separation_thermo.relative_volatility.average_alpha <= 1.0 and separation_thermo.separation_family in {"distillation", "absorption"}:
        issues.append(
            ValidationIssue(
                code="invalid_relative_volatility",
                severity=Severity.BLOCKED,
                message="Relative volatility / partition basis is not usable for the selected separation family.",
                artifact_ref="separation_thermo",
                source_refs=separation_thermo.citations,
            )
        )
    elif separation_thermo.relative_volatility.average_alpha <= 1.0 and separation_thermo.separation_family == "extraction":
        issues.append(
            ValidationIssue(
                code="weak_extraction_partition_basis",
                severity=Severity.WARNING,
                message="Relative volatility is weak for the extraction screening pair, so extraction performance must rely on explicit solvent/distribution basis rather than VLE alone.",
                artifact_ref="separation_thermo",
                source_refs=separation_thermo.citations,
            )
        )
    return issues


def validate_decision_record(decision: DecisionRecord, artifact_ref: str | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not decision.selected_candidate_id:
        issues.append(
            ValidationIssue(
                code="decision_missing_selection",
                severity=Severity.BLOCKED,
                message=f"Decision '{decision.decision_id}' has no selected candidate.",
                artifact_ref=artifact_ref or decision.decision_id,
            )
        )
        return issues
    selected = next((item for item in decision.alternatives if item.candidate_id == decision.selected_candidate_id), None)
    if selected is None:
        issues.append(
            ValidationIssue(
                code="decision_selected_candidate_missing",
                severity=Severity.BLOCKED,
                message=f"Decision '{decision.decision_id}' selected candidate '{decision.selected_candidate_id}' is not present.",
                artifact_ref=artifact_ref or decision.decision_id,
            )
        )
    elif not selected.feasible:
        issues.append(
            ValidationIssue(
                code="decision_selected_candidate_infeasible",
                severity=Severity.BLOCKED,
                message=f"Decision '{decision.decision_id}' selected infeasible candidate '{decision.selected_candidate_id}'.",
                artifact_ref=artifact_ref or decision.decision_id,
            )
        )
    if decision.scenario_stability == ScenarioStability.UNSTABLE and not decision.approval_required:
        issues.append(
            ValidationIssue(
                code="decision_unstable",
                severity=Severity.BLOCKED,
                message=f"Decision '{decision.decision_id}' is unstable under conservative scenarios.",
                artifact_ref=artifact_ref or decision.decision_id,
            )
        )
    return issues


def validate_chemistry_family_adapter(adapter: ChemistryFamilyAdapter) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not adapter.adapter_id:
        issues.append(
            ValidationIssue(
                code="missing_family_adapter_id",
                severity=Severity.BLOCKED,
                message="Chemistry-family adapter must include an adapter id.",
                artifact_ref="chemistry_family_adapter",
            )
        )
    if not adapter.route_generation_hints:
        issues.append(
            ValidationIssue(
                code="missing_family_adapter_route_hints",
                severity=Severity.BLOCKED,
                message="Chemistry-family adapter must define route-generation hints.",
                artifact_ref="chemistry_family_adapter",
            )
        )
    if not adapter.property_priority_order:
        issues.append(
            ValidationIssue(
                code="missing_family_adapter_property_priority",
                severity=Severity.BLOCKED,
                message="Chemistry-family adapter must define property-priority order.",
                artifact_ref="chemistry_family_adapter",
            )
        )
    if not adapter.common_unit_operations:
        issues.append(
            ValidationIssue(
                code="missing_family_adapter_unit_ops",
                severity=Severity.BLOCKED,
                message="Chemistry-family adapter must define common unit operations.",
                artifact_ref="chemistry_family_adapter",
            )
        )
    if not adapter.critic_focus:
        issues.append(
            ValidationIssue(
                code="missing_family_adapter_critic_focus",
                severity=Severity.BLOCKED,
                message="Chemistry-family adapter must define critic focus areas.",
                artifact_ref="chemistry_family_adapter",
            )
        )
    return issues


def validate_route_family_artifact(route_families: RouteFamilyArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not route_families.profiles:
        issues.append(
            ValidationIssue(
                code="missing_route_family_profiles",
                severity=Severity.BLOCKED,
                message="Route-family expansion requires at least one classified route-family profile.",
                artifact_ref="route_family_profiles",
            )
        )
        return issues
    for profile in route_families.profiles:
        if not profile.route_family_id:
            issues.append(
                ValidationIssue(
                    code="missing_route_family_id",
                    severity=Severity.BLOCKED,
                    message=f"Route '{profile.route_id}' is missing a route-family id.",
                    artifact_ref="route_family_profiles",
                )
            )
        if not profile.primary_reactor_class:
            issues.append(
                ValidationIssue(
                    code="missing_route_family_reactor_basis",
                    severity=Severity.BLOCKED,
                    message=f"Route-family profile '{profile.route_id}' is missing a reactor basis.",
                    artifact_ref="route_family_profiles",
                )
            )
        if not profile.primary_separation_train:
            issues.append(
                ValidationIssue(
                    code="missing_route_family_separation_basis",
                    severity=Severity.BLOCKED,
                    message=f"Route-family profile '{profile.route_id}' is missing a separation-train basis.",
                    artifact_ref="route_family_profiles",
                )
            )
    return issues


def validate_route_selection_critics(
    route_selection: RouteSelectionArtifact,
    route_families: RouteFamilyArtifact | None,
) -> list[ValidationIssue]:
    if route_families is None or not route_selection.selected_route_id:
        return []
    profile = next((item for item in route_families.profiles if item.route_id == route_selection.selected_route_id), None)
    if profile is None or not profile.critic_flags:
        return []
    return [
        ValidationIssue(
            code="route_family_critic_flags_present",
            severity=Severity.WARNING,
            message=f"Selected route family '{profile.family_label}' still carries critic flags: {', '.join(profile.critic_flags[:3])}.",
            artifact_ref="route_selection",
        )
    ]


def validate_separation_thermo_critics(route, separation_thermo: SeparationThermoArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if separation_thermo.separation_family in {"distillation", "extraction"} and separation_thermo.activity_model == "ideal_raoult":
        issues.append(
            ValidationIssue(
                code="weak_nonideal_thermo_basis",
                severity=Severity.WARNING,
                message=f"Route '{route.route_id}' is still using ideal Raoult screening for a nontrivial {separation_thermo.separation_family} service.",
                artifact_ref="separation_thermo",
            )
        )
    if separation_thermo.missing_binary_pairs:
        issues.append(
            ValidationIssue(
                code="missing_binary_interaction_coverage",
                severity=Severity.WARNING,
                message="Binary interaction coverage remains incomplete for the selected separation thermo basis: "
                + ", ".join(separation_thermo.missing_binary_pairs[:4])
                + ".",
                artifact_ref="separation_thermo",
            )
        )
    if separation_thermo.fallback_notes:
        issues.append(
            ValidationIssue(
                code="separation_thermo_fallback_active",
                severity=Severity.WARNING,
                message="Separation thermodynamics is relying on fallback assumptions: " + "; ".join(separation_thermo.fallback_notes[:2]) + ".",
                artifact_ref="separation_thermo",
            )
        )
    return issues


def validate_separation_design_critics(
    separation_choice: DecisionRecord,
    column: ColumnDesign,
    separation_thermo: SeparationThermoArtifact | None = None,
    unit_operation_family: UnitOperationFamilyArtifact | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_sep = (separation_choice.selected_candidate_id or "").lower()
    service = column.service.lower()
    family_id = (unit_operation_family.route_family_id if unit_operation_family is not None else "").lower()
    distillation_selected = any(token in selected_sep for token in ("distill", "fraction", "column", "rectif", "strip")) or any(
        token in service for token in ("distillation", "fractionation", "column")
    )
    absorption_selected = "absorption" in selected_sep or "absorb" in service
    solids_selected = any(token in selected_sep for token in ("crystall", "dry", "filter")) or any(
        token in service for token in ("crystall", "dryer", "filter")
    )

    if distillation_selected:
        if column.relative_volatility < 1.05:
            issues.append(
                ValidationIssue(
                    code="distillation_relative_volatility_too_low",
                    severity=Severity.BLOCKED,
                    message="Selected distillation service has relative volatility below 1.05 and should not be treated as a viable primary split without a stronger separation basis.",
                    artifact_ref=column.column_id,
                )
            )
        if separation_thermo is not None and separation_thermo.relative_volatility is not None and not separation_thermo.relative_volatility.feasible:
            issues.append(
                ValidationIssue(
                    code="separation_thermo_infeasible",
                    severity=Severity.BLOCKED,
                    message="The selected separation thermo artifact marks the key split as infeasible under the current distillation basis.",
                    artifact_ref="separation_thermo",
                )
            )
        if column.reflux_ratio_multiple_of_min > 5.0 or column.minimum_reflux_ratio > 25.0:
            issues.append(
                ValidationIssue(
                    code="distillation_reflux_extreme",
                    severity=Severity.WARNING,
                    message="Selected distillation basis requires extreme reflux severity and should remain under critic scrutiny.",
                    artifact_ref=column.column_id,
                )
            )

    if absorption_selected or family_id in {"gas_absorption_converter_train", "regeneration_loop_train"}:
        if column.absorber_capture_fraction > 0.90 and (column.absorber_henry_constant_bar <= 0.0 or column.equilibrium_fallback):
            issues.append(
                ValidationIssue(
                    code="absorber_capture_without_equilibrium_basis",
                    severity=Severity.BLOCKED,
                    message="High absorber capture is being claimed without a resolved Henry-law basis.",
                    artifact_ref=column.column_id,
                )
            )
        if 0.0 < column.absorber_flooding_margin_fraction < 0.10:
            issues.append(
                ValidationIssue(
                    code="absorber_operating_window_too_narrow",
                    severity=Severity.BLOCKED,
                    message="Absorber flooding margin is below 10%, leaving no credible operating window.",
                    artifact_ref=column.column_id,
                )
            )
        elif 0.10 <= column.absorber_flooding_margin_fraction < 0.15:
            issues.append(
                ValidationIssue(
                    code="absorber_operating_window_weak",
                    severity=Severity.WARNING,
                    message="Absorber flooding margin is narrow and should be treated as a weak screening basis.",
                    artifact_ref=column.column_id,
                )
            )

    if solids_selected or family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"}:
        if column.crystallizer_yield_fraction > 0.10 and column.crystallizer_supersaturation_ratio <= 1.0:
            issues.append(
                ValidationIssue(
                    code="crystallizer_yield_without_supersaturation",
                    severity=Severity.BLOCKED,
                    message="Crystallizer yield is positive even though the current basis shows no supersaturation driving force.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.dryer_product_moisture_fraction > 0.0
            and column.dryer_equilibrium_moisture_fraction > 0.0
            and column.dryer_product_moisture_fraction < column.dryer_equilibrium_moisture_fraction * 0.95
        ):
            issues.append(
                ValidationIssue(
                    code="dryer_endpoint_below_equilibrium",
                    severity=Severity.BLOCKED,
                    message="Dryer endpoint moisture is below the equilibrium moisture basis and is not physically credible.",
                    artifact_ref=column.column_id,
                )
            )
        if column.filter_area_m2 > 0.0 and column.filter_cycles_per_hr <= 0.0:
            issues.append(
                ValidationIssue(
                    code="filter_cycle_basis_missing",
                    severity=Severity.BLOCKED,
                    message="Filter area is nonzero but no credible filter cycling basis was produced.",
                    artifact_ref=column.column_id,
                )
            )
    return issues


def _resolved_property_count(property_packages: PropertyPackageArtifact, active_ids: set[str], property_name: str) -> int:
    count = 0
    for package in property_packages.packages:
        if package.identifier.identifier_id not in active_ids:
            continue
        prop = getattr(package, property_name, None)
        if prop is not None and getattr(prop, "resolution_status", "") == "resolved":
            count += 1
    return count


def validate_unit_family_property_coverage(
    route,
    reactor_choice: DecisionRecord,
    separation_choice: DecisionRecord,
    unit_operation_family: UnitOperationFamilyArtifact | None,
    property_packages: PropertyPackageArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    active_ids = set(active_identifier_ids_for_route(property_packages, route, None))
    if not active_ids:
        return issues
    family_id = (unit_operation_family.route_family_id if unit_operation_family is not None else "").lower()
    selected_reactor = (reactor_choice.selected_candidate_id or "").lower()
    selected_sep = (separation_choice.selected_candidate_id or "").lower()
    high_hazard = any((hazard.severity or "").lower() == "high" for hazard in route.hazards)
    hazard_sensitive_reactor = high_hazard or any(token in selected_reactor for token in ("oxidizer", "converter", "carbonylation", "fixed_bed", "trickle"))

    if hazard_sensitive_reactor:
        resolved_tc = _resolved_property_count(property_packages, active_ids, "thermal_conductivity")
        resolved_cp = _resolved_property_count(property_packages, active_ids, "liquid_heat_capacity")
        resolved_density = _resolved_property_count(property_packages, active_ids, "liquid_density")
        if resolved_tc == 0:
            issues.append(
                ValidationIssue(
                    code="reactor_hazard_property_coverage_weak",
                    severity=Severity.WARNING,
                    message="Selected reactor family is hazard-sensitive, but no active component has resolved thermal-conductivity coverage.",
                    artifact_ref="property_packages",
                )
            )
        if resolved_cp == 0 or resolved_density == 0:
            issues.append(
                ValidationIssue(
                    code="reactor_transport_property_coverage_weak",
                    severity=Severity.WARNING,
                    message="Selected reactor family is proceeding with weak resolved heat-capacity or density coverage for the active route components.",
                    artifact_ref="property_packages",
                )
            )

    absorption_family = family_id in {"gas_absorption_converter_train", "regeneration_loop_train"} or any(
        token in selected_sep for token in ("absorption", "packed_absorption", "gas_drying")
    )
    if absorption_family and property_packages.unresolved_henry_pairs:
        severity = Severity.BLOCKED if not property_packages.henry_law_constants else Severity.WARNING
        issues.append(
            ValidationIssue(
                code="absorption_family_property_coverage_weak",
                severity=severity,
                message="Absorption-led unit families still have unresolved Henry-law coverage: " + ", ".join(property_packages.unresolved_henry_pairs[:4]) + ".",
                artifact_ref="property_packages",
            )
        )

    solids_family = family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"} or any(
        token in selected_sep for token in ("crystall", "dryer", "filter")
    )
    if solids_family and property_packages.unresolved_solubility_pairs:
        severity = Severity.BLOCKED if not property_packages.solubility_curves else Severity.WARNING
        issues.append(
            ValidationIssue(
                code="solids_family_property_coverage_weak",
                severity=severity,
                message="Solids-handling unit families still have unresolved solubility coverage: " + ", ".join(property_packages.unresolved_solubility_pairs[:4]) + ".",
                artifact_ref="property_packages",
            )
        )

    distillation_family = any(token in selected_sep for token in ("distillation", "extractive", "extraction"))
    if distillation_family and property_packages.unresolved_binary_pairs:
        issues.append(
            ValidationIssue(
                code="distillation_family_property_coverage_weak",
                severity=Severity.WARNING,
                message="Selected separation family still has unresolved binary-interaction coverage: " + ", ".join(property_packages.unresolved_binary_pairs[:4]) + ".",
                artifact_ref="property_packages",
            )
        )
    return issues


def validate_reactor_hazard_basis_critics(
    route,
    reactor_choice: DecisionRecord,
    reactor: ReactorDesign,
    operations_planning: OperationsPlanningArtifact | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_reactor = (reactor_choice.selected_candidate_id or "").lower()
    high_hazard = any((hazard.severity or "").lower() == "high" for hazard in route.hazards)
    hazard_sensitive_reactor = high_hazard or any(token in selected_reactor for token in ("oxidizer", "converter", "carbonylation", "fixed_bed", "trickle"))
    if not hazard_sensitive_reactor:
        return issues

    if reactor.runaway_risk_label == "high":
        issues.append(
            ValidationIssue(
                code="reactor_hazard_basis_high_runaway_risk",
                severity=Severity.WARNING,
                message="Selected reactor remains in a high runaway-risk regime and should stay approval-gated.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if reactor.heat_removal_margin_fraction < 0.10 or reactor.thermal_stability_score < 55.0:
        issues.append(
            ValidationIssue(
                code="reactor_hazard_basis_unsupported",
                severity=Severity.WARNING,
                message="Hazard-sensitive reactor family still has a weak thermal-severity or heat-removal basis for a confident autonomous selection.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if operations_planning is not None and high_hazard and operations_planning.recommended_operating_mode == "batch":
        issues.append(
            ValidationIssue(
                code="hazard_route_batch_mode_selected",
                severity=Severity.WARNING,
                message="High-hazard route is paired with batch operation, so restart and reheat exposure should remain analyst-approved.",
                artifact_ref="operations_planning",
            )
        )
    if operations_planning is not None and high_hazard and operations_planning.restart_loss_fraction > 0.008:
        issues.append(
            ValidationIssue(
                code="hazard_route_restart_loss_high",
                severity=Severity.WARNING,
                message="High-hazard route still carries elevated restart-loss burden, which weakens the hazard-operability basis.",
                artifact_ref="operations_planning",
            )
        )
    return issues


def validate_route_economic_critics(
    route_selection: RouteSelectionArtifact,
    utility_network: UtilityNetworkDecision,
    cost_model: CostModel,
    economic_basis_decision: DecisionRecord,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_case = next((item for item in utility_network.cases if item.case_id == utility_network.selected_case_id), None)
    selected_economic_basis = economic_basis_decision.selected_candidate_id or ""

    if selected_economic_basis != "selected_integrated_base":
        issues.append(
            ValidationIssue(
                code="economic_basis_counterfactual_selected",
                severity=Severity.WARNING,
                message=(
                    f"Economic basis selected '{selected_economic_basis}' instead of the integrated base case for route "
                    f"'{route_selection.selected_route_id or cost_model.selected_route_id or utility_network.route_id}'."
                ),
                artifact_ref="economic_basis_decision",
            )
        )

    if (
        selected_economic_basis == "no_recovery_counterfactual"
        and selected_case is not None
        and selected_case.recovered_duty_kw > 0.0
        and utility_network.selected_annual_utility_cost_inr < utility_network.base_annual_utility_cost_inr
    ):
        issues.append(
            ValidationIssue(
                code="economic_basis_rejects_selected_recovery",
                severity=Severity.WARNING,
                message=(
                    f"Economic basis rejected the selected recovery case '{selected_case.case_id}' even though it recovers "
                    f"{selected_case.recovered_duty_kw:.1f} kW and reduces annual utility cost."
                ),
                artifact_ref="economic_basis_decision",
            )
        )

    if (
        selected_economic_basis == "conservative_case"
        and cost_model.selected_heat_integration_case_id
        and utility_network.selected_case_id == cost_model.selected_heat_integration_case_id
        and cost_model.integration_capex_inr > 0.0
    ):
        issues.append(
            ValidationIssue(
                code="economic_basis_conservative_override",
                severity=Severity.WARNING,
                message=(
                    "Economic basis stayed on the conservative counterfactual despite a fully costed selected heat-integration "
                    "architecture, so the basis should remain approval-gated."
                ),
                artifact_ref="economic_basis_decision",
            )
        )
    return issues


def validate_financing_operability_critics(
    financing_basis: DecisionRecord,
    economic_basis_decision: DecisionRecord,
    financial_model: FinancialModel,
    operations_planning: OperationsPlanningArtifact,
    reactor: ReactorDesign | None = None,
    utility_network: UtilityNetworkDecision | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_financing = (financing_basis.selected_candidate_id or "").lower()
    high_leverage = "70_30" in selected_financing or "70:30" in financing_basis.selected_summary
    selected_case = None
    if utility_network is not None and utility_network.selected_case_id:
        selected_case = next((item for item in utility_network.cases if item.case_id == utility_network.selected_case_id), None)

    if (
        high_leverage
        and (financial_model.covenant_breach_codes or financial_model.minimum_dscr < 1.12)
        and (operations_planning.throughput_loss_fraction > 0.02 or operations_planning.restart_loss_fraction > 0.005)
    ):
        issues.append(
            ValidationIssue(
                code="financing_operability_tension",
                severity=Severity.WARNING,
                message="Higher-leverage financing is being held against an operating mode with meaningful outage or restart-loss burden.",
                artifact_ref="financing_basis_decision",
            )
        )
    if high_leverage and reactor is not None and reactor.runaway_risk_label == "high":
        issues.append(
            ValidationIssue(
                code="hazard_route_high_leverage_financing",
                severity=Severity.WARNING,
                message="High-leverage financing remains selected even though the reactor hazard basis still carries high runaway risk.",
                artifact_ref="financing_basis_decision",
            )
        )
    if (
        economic_basis_decision.selected_candidate_id != "selected_integrated_base"
        and operations_planning.recommended_operating_mode == "continuous"
        and selected_case is not None
        and selected_case.recovered_duty_kw > 0.0
    ):
        issues.append(
            ValidationIssue(
                code="operating_mode_integrated_economics_tension",
                severity=Severity.WARNING,
                message="Operating mode remains tuned for continuous integrated service while the selected economic basis has moved to a counterfactual case.",
                artifact_ref="operating_mode",
            )
        )
    return issues


def validate_architecture_package_critics(
    route,
    separation_choice: DecisionRecord,
    unit_operation_family: UnitOperationFamilyArtifact | None,
    separation_thermo: SeparationThermoArtifact | None,
    kinetics_method: MethodSelectionArtifact | None,
    sparse_data_policy: SparseDataPolicyArtifact | None,
    property_packages: PropertyPackageArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    family_id = (unit_operation_family.route_family_id if unit_operation_family is not None else "").lower()
    selected_sep = (separation_choice.selected_candidate_id or "").lower()
    route_text = " ".join(
        [
            route.route_id,
            route.name,
            route.reaction_equation,
            " ".join(route.catalysts),
            " ".join(route.byproducts),
        ]
    ).lower()
    high_hazard = any((hazard.severity or "").lower() == "high" for hazard in route.hazards)
    distillation_family = any(token in selected_sep for token in ("distillation", "extractive", "extraction")) or family_id in {
        "continuous_liquid_organic_train",
        "mixed_separation_specialty_train",
    }
    absorption_family = family_id in {"gas_absorption_converter_train", "regeneration_loop_train"} or any(
        token in selected_sep for token in ("absorption", "packed_absorption", "gas_drying")
    )
    solids_family = family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"} or any(
        token in selected_sep for token in ("crystall", "dryer", "filter")
    )
    architecture_weak = False

    if (
        distillation_family
        and separation_thermo is not None
        and (
            separation_thermo.activity_model == "ideal_raoult"
            or bool(separation_thermo.missing_binary_pairs)
            or bool(separation_thermo.fallback_notes)
        )
    ):
        architecture_weak = True
        issues.append(
            ValidationIssue(
                code="architecture_package_fallback_thermo",
                severity=Severity.WARNING,
                message="Selected architecture is still relying on fallback or idealized thermodynamics for the chosen liquid separation family.",
                artifact_ref="separation_thermo",
            )
        )

    if absorption_family and property_packages.unresolved_henry_pairs:
        architecture_weak = True
        issues.append(
            ValidationIssue(
                code="architecture_package_weak_absorber_basis",
                severity=Severity.WARNING,
                message="Selected absorber-led architecture still depends on unresolved Henry-law coverage.",
                artifact_ref="property_packages",
            )
        )

    if solids_family and property_packages.unresolved_solubility_pairs:
        architecture_weak = True
        issues.append(
            ValidationIssue(
                code="architecture_package_weak_solids_basis",
                severity=Severity.WARNING,
                message="Selected solids-handling architecture still depends on unresolved solubility coverage.",
                artifact_ref="property_packages",
            )
        )

    selected_kinetics = (kinetics_method.decision.selected_candidate_id if kinetics_method is not None else "") or ""
    complex_route = any(token in route_text for token in ("carbonylation", "converter", "oxidation", "catal"))
    if kinetics_method is not None and selected_kinetics in {"conservative_analogy", "apparent_order_fit"} and (complex_route or high_hazard):
        architecture_weak = True
        issues.append(
            ValidationIssue(
                code="architecture_package_weak_kinetics_basis",
                severity=Severity.WARNING,
                message="Selected architecture is still resting on analogy or coarse fitted kinetics for a complex or high-hazard route.",
                artifact_ref="kinetics_method_decision",
            )
        )

    if architecture_weak and sparse_data_policy is not None:
        triggered = [
            rule
            for rule in sparse_data_policy.rules
            if rule.current_status in {"warning", "blocked"}
            and rule.stage_id in {"thermodynamic_feasibility", "kinetic_feasibility", "reactor_design", "distillation_design"}
        ]
        if triggered:
            issues.append(
                ValidationIssue(
                    code="architecture_package_sparse_data_compounded",
                    severity=Severity.WARNING,
                    message=(
                        "Selected architecture has compounded sparse-data pressure across thermo/kinetics/design stages: "
                        + ", ".join(rule.subject for rule in triggered[:4])
                        + "."
                    ),
                    artifact_ref="sparse_data_policy",
                )
            )
    return issues


def validate_kinetics_method_critics(route, method_artifact: MethodSelectionArtifact) -> list[ValidationIssue]:
    selected = method_artifact.decision.selected_candidate_id or ""
    route_text = " ".join(
        [
            route.route_id,
            route.name,
            route.reaction_equation,
            " ".join(route.catalysts),
            " ".join(route.byproducts),
        ]
    ).lower()
    high_hazard = any((hazard.severity or "").lower() == "high" for hazard in route.hazards)
    complex_route = any(token in route_text for token in ("carbonylation", "converter", "oxidation", "catal"))
    issues: list[ValidationIssue] = []
    if complex_route and selected in {"apparent_order_fit", "conservative_analogy"}:
        issues.append(
            ValidationIssue(
                code="weak_kinetics_basis_for_complex_route",
                severity=Severity.WARNING,
                message=f"Selected kinetics method '{selected}' is weak for a complex catalytic/pressure-sensitive route.",
                artifact_ref="kinetics_method_decision",
            )
        )
    if high_hazard and selected == "conservative_analogy":
        issues.append(
            ValidationIssue(
                code="hazard_route_using_analogy_kinetics",
                severity=Severity.WARNING,
                message="High-hazard route is relying on conservative analogy kinetics and should remain under analyst scrutiny.",
                artifact_ref="kinetics_method_decision",
            )
        )
    return issues


def validate_unit_operation_family_artifact(unit_family: UnitOperationFamilyArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not unit_family.route_id:
        issues.append(
            ValidationIssue(
                code="missing_unit_family_route_id",
                severity=Severity.BLOCKED,
                message="Unit-operation family artifact must reference a route id.",
                artifact_ref="unit_operation_family",
            )
        )
    if not unit_family.reactor_candidates:
        issues.append(
            ValidationIssue(
                code="missing_unit_family_reactor_candidates",
                severity=Severity.BLOCKED,
                message="Unit-operation family artifact must include reactor candidates.",
                artifact_ref="unit_operation_family",
            )
        )
    if not unit_family.separation_candidates:
        issues.append(
            ValidationIssue(
                code="missing_unit_family_separation_candidates",
                severity=Severity.BLOCKED,
                message="Unit-operation family artifact must include separation candidates.",
                artifact_ref="unit_operation_family",
            )
        )
    if not unit_family.supporting_unit_operations:
        issues.append(
            ValidationIssue(
                code="missing_unit_family_supporting_ops",
                severity=Severity.BLOCKED,
                message="Unit-operation family artifact must include supporting unit-operation expectations.",
                artifact_ref="unit_operation_family",
            )
        )
    return issues


def validate_process_archetype(archetype: ProcessArchetype) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not archetype.operating_mode_candidates:
        issues.append(
            ValidationIssue(
                code="archetype_missing_operating_modes",
                severity=Severity.BLOCKED,
                message="Process archetype has no operating-mode candidates.",
                artifact_ref="process_archetype",
            )
        )
    if not archetype.dominant_separation_family:
        issues.append(
            ValidationIssue(
                code="archetype_missing_separation_family",
                severity=Severity.BLOCKED,
                message="Process archetype has no dominant separation family.",
                artifact_ref="process_archetype",
            )
        )
    return issues


def validate_site_selection_consistency(site_selection: SiteSelectionArtifact, site_decision: DecisionRecord | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    candidate_names = {candidate.name for candidate in site_selection.candidates}
    location_names = {location.site_name for location in site_selection.india_location_data}
    normalized_location_names = {
        _normalize_site_label(location.site_name)
        for location in site_selection.india_location_data
    }
    if site_selection.selected_site and site_selection.selected_site not in candidate_names:
        issues.append(
            ValidationIssue(
                code="selected_site_missing_candidate",
                severity=Severity.BLOCKED,
                message=f"Selected site '{site_selection.selected_site}' is not present in scored candidates.",
                artifact_ref="site_selection",
            )
        )
    selected_site_normalized = _normalize_site_label(site_selection.selected_site) if site_selection.selected_site else ""
    location_match = (
        not selected_site_normalized
        or not normalized_location_names
        or any(
            selected_site_normalized == location_name
            or selected_site_normalized in location_name
            or location_name in selected_site_normalized
            for location_name in normalized_location_names
        )
    )
    if site_selection.selected_site and location_names and not location_match:
        issues.append(
            ValidationIssue(
                code="selected_site_missing_location_evidence",
                severity=Severity.BLOCKED,
                message=f"Selected site '{site_selection.selected_site}' has no matching India location evidence entry.",
                artifact_ref="site_selection",
            )
        )
    if site_decision and site_decision.selected_candidate_id and site_decision.selected_candidate_id != site_selection.selected_site:
        issues.append(
            ValidationIssue(
                code="site_decision_mismatch",
                severity=Severity.BLOCKED,
                message=f"Site decision selected '{site_decision.selected_candidate_id}' but site artifact selected '{site_selection.selected_site}'.",
                artifact_ref="site_selection",
            )
        )
    return issues


def validate_route_site_fit_artifact(
    route_site_fit: RouteSiteFitArtifact,
    site_selection: SiteSelectionArtifact | None = None,
    route_selection: RouteSelectionArtifact | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not route_site_fit.route_id:
        issues.append(
            ValidationIssue(
                code="missing_route_site_fit_route",
                severity=Severity.BLOCKED,
                message="Route site-fit artifact is missing a route id.",
                artifact_ref="route_site_fit",
            )
        )
    if not route_site_fit.selected_site:
        issues.append(
            ValidationIssue(
                code="missing_route_site_fit_site",
                severity=Severity.BLOCKED,
                message="Route site-fit artifact is missing a selected site.",
                artifact_ref="route_site_fit",
            )
        )
    if route_site_fit.feedstock_cluster_factor <= 0.0 or route_site_fit.logistics_penalty_factor <= 0.0 or route_site_fit.utility_reliability_factor <= 0.0:
        issues.append(
            ValidationIssue(
                code="invalid_route_site_fit_factors",
                severity=Severity.BLOCKED,
                message="Route site-fit factors must all be positive.",
                artifact_ref="route_site_fit",
            )
        )
    if not 0.0 <= route_site_fit.overall_fit_score <= 100.0:
        issues.append(
            ValidationIssue(
                code="invalid_route_site_fit_score",
                severity=Severity.BLOCKED,
                message="Route site-fit score must lie between 0 and 100.",
                artifact_ref="route_site_fit",
            )
        )
    if site_selection is not None and site_selection.selected_site and route_site_fit.selected_site != site_selection.selected_site:
        issues.append(
            ValidationIssue(
                code="route_site_fit_site_mismatch",
                severity=Severity.BLOCKED,
                message=f"Route site-fit site '{route_site_fit.selected_site}' does not match selected site '{site_selection.selected_site}'.",
                artifact_ref="route_site_fit",
            )
        )
    if route_selection is not None and route_selection.selected_route_id and route_site_fit.route_id != route_selection.selected_route_id:
        issues.append(
            ValidationIssue(
                code="route_site_fit_route_mismatch",
                severity=Severity.BLOCKED,
                message=f"Route site-fit route '{route_site_fit.route_id}' does not match selected route '{route_selection.selected_route_id}'.",
                artifact_ref="route_site_fit",
            )
        )
    return issues


def validate_route_economic_basis_artifact(
    route_economic_basis: RouteEconomicBasisArtifact,
    route_site_fit: RouteSiteFitArtifact | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not route_economic_basis.route_id:
        issues.append(
            ValidationIssue(
                code="missing_route_economic_basis_route",
                severity=Severity.BLOCKED,
                message="Route-derived economic basis is missing a route id.",
                artifact_ref="route_economic_basis",
            )
        )
    if route_economic_basis.raw_material_complexity_factor <= 0.0 or route_economic_basis.site_input_cost_factor <= 0.0 or route_economic_basis.logistics_intensity_factor <= 0.0:
        issues.append(
            ValidationIssue(
                code="invalid_route_economic_basis_factors",
                severity=Severity.BLOCKED,
                message="Route-derived economic basis multipliers must all be positive.",
                artifact_ref="route_economic_basis",
            )
        )
    if route_economic_basis.batch_occupancy_penalty_fraction < 0.0:
        issues.append(
            ValidationIssue(
                code="invalid_route_batch_penalty",
                severity=Severity.BLOCKED,
                message="Route-derived batch occupancy penalty cannot be negative.",
                artifact_ref="route_economic_basis",
            )
        )
    if any(
        burden < 0.0
        for burden in (
            route_economic_basis.solvent_recovery_service_cost_inr,
            route_economic_basis.catalyst_service_cost_inr,
            route_economic_basis.waste_treatment_burden_inr,
        )
    ):
        issues.append(
            ValidationIssue(
                code="negative_route_economic_burden",
                severity=Severity.BLOCKED,
                message="Route-derived economic service burdens cannot be negative.",
                artifact_ref="route_economic_basis",
            )
        )
    if route_site_fit is not None:
        if route_economic_basis.route_id != route_site_fit.route_id:
            issues.append(
                ValidationIssue(
                    code="route_economic_route_mismatch",
                    severity=Severity.BLOCKED,
                    message="Route-derived economic basis route id does not match the route site-fit artifact.",
                    artifact_ref="route_economic_basis",
                )
            )
        if route_economic_basis.selected_site != route_site_fit.selected_site:
            issues.append(
                ValidationIssue(
                    code="route_economic_site_mismatch",
                    severity=Severity.BLOCKED,
                    message="Route-derived economic basis site does not match the route site-fit artifact.",
                    artifact_ref="route_economic_basis",
                )
            )
    return issues


def validate_route_balance(route) -> list[ValidationIssue]:
    if reaction_is_balanced(route):
        return []
    delta = reaction_balance_delta(route)
    return [
        ValidationIssue(
            code="unbalanced_route",
            severity=Severity.BLOCKED,
            message=f"Selected route is not atom-balanced: {delta}.",
            artifact_ref=route.route_id,
        )
    ]


def validate_stream_table(stream_table: StreamTable, tolerance_pct: float = 2.0) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if stream_table.closure_error_pct > tolerance_pct:
        issues.append(
            ValidationIssue(
                code="stream_closure",
                severity=Severity.BLOCKED,
                message=f"Stream table closure error {stream_table.closure_error_pct:.3f}% exceeds tolerance {tolerance_pct:.3f}%.",
                artifact_ref="stream_table",
            )
        )
    if stream_table.unit_operation_packets and not stream_table.composition_states:
        issues.append(
            ValidationIssue(
                code="missing_composition_states",
                severity=Severity.BLOCKED,
                message="Stream table exposes unit packets but no unitwise composition states.",
                artifact_ref="stream_table",
            )
        )
    if stream_table.unit_operation_packets and not stream_table.composition_closures:
        issues.append(
            ValidationIssue(
                code="missing_composition_closures",
                severity=Severity.BLOCKED,
                message="Stream table exposes unit packets but no composition-closure summaries.",
                artifact_ref="stream_table",
            )
        )
    if stream_table.separation_packets and not stream_table.phase_split_specs:
        issues.append(
            ValidationIssue(
                code="missing_phase_split_specs",
                severity=Severity.BLOCKED,
                message="Stream table exposes separator packets but no phase-split specs.",
                artifact_ref="stream_table",
            )
        )
    if stream_table.separation_packets and not stream_table.separator_performances:
        issues.append(
            ValidationIssue(
                code="missing_separator_performances",
                severity=Severity.BLOCKED,
                message="Stream table exposes separator packets but no separator performance records.",
                artifact_ref="stream_table",
            )
        )
    if stream_table.recycle_packets and not stream_table.convergence_summaries:
        issues.append(
            ValidationIssue(
                code="missing_convergence_summaries",
                severity=Severity.BLOCKED,
                message="Stream table exposes recycle packets but no recycle convergence summaries.",
                artifact_ref="stream_table",
            )
        )
    for spec in stream_table.phase_split_specs:
        if spec.phase_split_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="phase_split_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Separator '{spec.unit_id}' has a blocked phase-split spec.",
                    artifact_ref="stream_table",
                )
            )
        elif spec.phase_split_status == "partial":
            issues.append(
                ValidationIssue(
                    code="phase_split_partial",
                    severity=Severity.WARNING,
                    message=f"Separator '{spec.unit_id}' retains partial phase-split coverage.",
                    artifact_ref="stream_table",
                )
            )
    for performance in stream_table.separator_performances:
        if performance.performance_status == "blocked" or performance.split_closure_pct > 25.0:
            issues.append(
                ValidationIssue(
                    code="separator_performance_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Separator '{performance.unit_id}' has blocked performance with split closure {performance.split_closure_pct:.3f}%.",
                    artifact_ref="stream_table",
                )
            )
        elif performance.performance_status == "estimated":
            issues.append(
                ValidationIssue(
                    code="separator_performance_estimated",
                    severity=Severity.WARNING,
                    message=f"Separator '{performance.unit_id}' remains estimated with split closure {performance.split_closure_pct:.3f}%.",
                    artifact_ref="stream_table",
                )
            )
    for summary in stream_table.convergence_summaries:
        if not summary.purge_policy_by_family:
            issues.append(
                ValidationIssue(
                    code="convergence_summary_missing_purge_policy",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{summary.loop_id}' has no explicit purge policy by impurity family.",
                    artifact_ref="stream_table",
                )
            )
        if summary.convergence_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="convergence_summary_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{summary.loop_id}' has a blocked convergence summary.",
                    artifact_ref="stream_table",
                )
            )
    for state in stream_table.composition_states:
        if state.status == "blocked":
            issues.append(
                ValidationIssue(
                    code="composition_state_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{state.unit_id}' has blocked composition propagation state.",
                    artifact_ref="stream_table",
                )
            )
    for closure in stream_table.composition_closures:
        if closure.closure_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="composition_closure_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{closure.unit_id}' has blocked composition closure.",
                    artifact_ref="stream_table",
                )
            )
        elif closure.closure_status == "estimated":
            issues.append(
                ValidationIssue(
                    code="composition_closure_estimated",
                    severity=Severity.WARNING,
                    message=f"Unit '{closure.unit_id}' retains estimated composition closure.",
                    artifact_ref="stream_table",
                )
            )
    waste_sink_streams = [
        stream
        for stream in stream_table.streams
        if stream.destination_unit_id == "waste_treatment"
        or stream.stream_role in {"waste", "vent", "purge"}
    ]
    if waste_sink_streams:
        generic_sink_ids = sorted({stream.stream_id for stream in waste_sink_streams if stream.destination_unit_id == "waste_treatment"})
        if generic_sink_ids:
            issues.append(
                ValidationIssue(
                    code="generic_waste_sink_active",
                    severity=Severity.WARNING,
                    message=(
                        "Waste-routing still terminates in a generic 'waste_treatment' sink for streams "
                        + ", ".join(generic_sink_ids[:6])
                        + ". Explicit downstream closure should name the final handling path such as scrubber, ETP, hazardous-organic tank, incineration, or offsite disposal."
                    ),
                    artifact_ref="stream_table",
                )
            )
        waste_roles = {stream.stream_role for stream in waste_sink_streams if stream.destination_unit_id == "waste_treatment"}
        if len(waste_roles) > 1:
            issues.append(
                ValidationIssue(
                    code="mixed_waste_sink_requires_segregation",
                    severity=Severity.WARNING,
                    message=(
                        "Multiple waste roles share the same generic waste sink ("
                        + ", ".join(sorted(waste_roles))
                        + "). The design should segregate vent handling, aqueous effluent, and hazardous-organic waste explicitly."
                    ),
                    artifact_ref="stream_table",
                )
            )
    return issues


def validate_flowsheet_case(flowsheet_case: FlowsheetCase) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    stream_ids = {stream.stream_id for stream in flowsheet_case.streams}
    summary_index = {summary.loop_id: summary for summary in flowsheet_case.convergence_summaries}
    composition_state_index = {state.unit_id: state for state in flowsheet_case.composition_states}
    composition_closure_index = {closure.unit_id: closure for closure in flowsheet_case.composition_closures}
    if not flowsheet_case.units:
        issues.append(
            ValidationIssue(
                code="flowsheet_case_missing_units",
                severity=Severity.BLOCKED,
                message="Flowsheet case has no unit specifications.",
                artifact_ref="flowsheet_case",
            )
        )
        return issues
    for unit in flowsheet_case.units:
        if unit.closure_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="flowsheet_unit_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{unit.unit_id}' is blocked in the flowsheet case with closure error {unit.closure_error_pct:.3f}%.",
                    artifact_ref="flowsheet_case",
                )
            )
        if unit.missing_source_stream_ids:
            issues.append(
                ValidationIssue(
                    code="flowsheet_unit_missing_source",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Unit '{unit.unit_id}' has inlet streams without upstream source references: "
                        f"{', '.join(unit.missing_source_stream_ids)}."
                    ),
                    artifact_ref="flowsheet_case",
                )
            )
        if unit.missing_destination_stream_ids:
            issues.append(
                ValidationIssue(
                    code="flowsheet_unit_missing_destination",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Unit '{unit.unit_id}' has outlet streams without downstream destination references: "
                        f"{', '.join(unit.missing_destination_stream_ids)}."
                    ),
                    artifact_ref="flowsheet_case",
                )
            )
        if unit.unresolved_sensitivities and unit.closure_status != "blocked":
            issues.append(
                ValidationIssue(
                    code="flowsheet_unit_unresolved_basis",
                    severity=Severity.WARNING,
                    message=(
                        f"Unit '{unit.unit_id}' still carries unresolved basis items: "
                        f"{', '.join(unit.unresolved_sensitivities[:3])}."
                    ),
                    artifact_ref="flowsheet_case",
                )
            )
        if unit.unit_type in {"storage", "waste_handling", "recycle"}:
            continue
        if unit.unit_id not in composition_state_index:
            issues.append(
                ValidationIssue(
                    code="flowsheet_unit_missing_composition_state",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{unit.unit_id}' has no composition state in the flowsheet case.",
                    artifact_ref="flowsheet_case",
                )
            )
        if unit.unit_id not in composition_closure_index:
            issues.append(
                ValidationIssue(
                    code="flowsheet_unit_missing_composition_closure",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{unit.unit_id}' has no composition closure in the flowsheet case.",
                    artifact_ref="flowsheet_case",
                )
            )
    for separation in flowsheet_case.separations:
        if not separation.inlet_stream_ids:
            issues.append(
                ValidationIssue(
                    code="separation_missing_inlet",
                    severity=Severity.BLOCKED,
                    message=f"Separation '{separation.separation_id}' has no inlet streams.",
                    artifact_ref="flowsheet_case",
                )
            )
        for stream_id in separation.inlet_stream_ids + separation.product_stream_ids + separation.waste_stream_ids + separation.recycle_stream_ids + separation.side_draw_stream_ids:
            if stream_id not in stream_ids:
                issues.append(
                    ValidationIssue(
                        code="separation_missing_stream_ref",
                        severity=Severity.BLOCKED,
                        message=f"Separation '{separation.separation_id}' references unknown stream '{stream_id}'.",
                        artifact_ref="flowsheet_case",
                    )
                )
        if not (separation.product_stream_ids or separation.waste_stream_ids or separation.recycle_stream_ids or separation.side_draw_stream_ids):
            issues.append(
                ValidationIssue(
                    code="separation_missing_outlets",
                    severity=Severity.BLOCKED,
                    message=f"Separation '{separation.separation_id}' has no outlet split streams.",
                    artifact_ref="flowsheet_case",
                )
            )
        if separation.closure_error_pct > 5.0:
            issues.append(
                ValidationIssue(
                    code="separation_closure_high",
                    severity=Severity.BLOCKED,
                    message=f"Separation '{separation.separation_id}' closure error {separation.closure_error_pct:.3f}% exceeds tolerance.",
                    artifact_ref="flowsheet_case",
                )
            )
        if separation.split_status == "blocked" or separation.split_closure_pct > 25.0:
            issues.append(
                ValidationIssue(
                    code="separation_split_blocked",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Separation '{separation.separation_id}' has blocked split performance with "
                        f"split closure {separation.split_closure_pct:.3f}%."
                    ),
                    artifact_ref="flowsheet_case",
                )
            )
        for component_name in (
            set(separation.component_split_to_product)
            | set(separation.component_split_to_waste)
            | set(separation.component_split_to_recycle)
            | set(separation.component_split_to_side_draw)
        ):
            split_total = (
                separation.component_split_to_product.get(component_name, 0.0)
                + separation.component_split_to_waste.get(component_name, 0.0)
                + separation.component_split_to_recycle.get(component_name, 0.0)
                + separation.component_split_to_side_draw.get(component_name, 0.0)
            )
            if split_total > 1.10 or split_total < 0.75:
                issues.append(
                    ValidationIssue(
                        code="separation_component_split_unbalanced",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Separation '{separation.separation_id}' has weak component split closure for "
                            f"'{component_name}' with total split {split_total:.3f}."
                        ),
                        artifact_ref="flowsheet_case",
                    )
                )
    for section in flowsheet_case.sections:
        if not section.unit_ids:
            issues.append(
                ValidationIssue(
                    code="flowsheet_section_missing_units",
                    severity=Severity.BLOCKED,
                    message=f"Section '{section.section_id}' has no active unit ids.",
                    artifact_ref="flowsheet_case",
                )
            )
        if not section.inlet_stream_ids:
            issues.append(
                ValidationIssue(
                    code="flowsheet_section_missing_inlets",
                    severity=Severity.BLOCKED,
                    message=f"Section '{section.section_id}' has no inlet stream ids.",
                    artifact_ref="flowsheet_case",
                )
            )
        if not section.outlet_stream_ids:
            issues.append(
                ValidationIssue(
                    code="flowsheet_section_missing_outlets",
                    severity=Severity.BLOCKED,
                    message=f"Section '{section.section_id}' has no outlet stream ids.",
                    artifact_ref="flowsheet_case",
                )
            )
        if section.status == "blocked":
            issues.append(
                ValidationIssue(
                    code="flowsheet_section_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Section '{section.section_id}' is blocked in the flowsheet case.",
                    artifact_ref="flowsheet_case",
                )
            )
    for loop in flowsheet_case.recycle_loops:
        if not loop.recycle_stream_ids:
            issues.append(
                ValidationIssue(
                    code="recycle_loop_missing_recycle",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop.loop_id}' has no recycle stream ids.",
                    artifact_ref="flowsheet_case",
                )
            )
        for stream_id in loop.recycle_stream_ids + loop.purge_stream_ids:
            if stream_id not in stream_ids:
                issues.append(
                    ValidationIssue(
                        code="recycle_loop_missing_stream_ref",
                        severity=Severity.BLOCKED,
                        message=f"Recycle loop '{loop.loop_id}' references unknown stream '{stream_id}'.",
                        artifact_ref="flowsheet_case",
                    )
                )
        for stream_id in loop.recycle_stream_ids:
            stream = next((item for item in flowsheet_case.streams if item.stream_id == stream_id), None)
            if stream is not None and loop.recycle_target_unit_id and stream.destination_unit_id != loop.recycle_target_unit_id:
                issues.append(
                    ValidationIssue(
                        code="recycle_stream_destination_invalid",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Recycle stream '{stream_id}' in loop '{loop.loop_id}' returns to "
                            f"'{stream.destination_unit_id or 'unknown'}' instead of '{loop.recycle_target_unit_id}'."
                        ),
                        artifact_ref="flowsheet_case",
                    )
                )
        if not loop.recycle_target_unit_id:
            issues.append(
                ValidationIssue(
                    code="recycle_loop_missing_target",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop.loop_id}' has no resolved recycle target unit.",
                    artifact_ref="flowsheet_case",
                )
            )
        if max(loop.component_convergence_error_pct.values(), default=0.0) > 95.0:
            issues.append(
                ValidationIssue(
                    code="recycle_component_convergence_high",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop.loop_id}' has component convergence error above 95.0%.",
                    artifact_ref="flowsheet_case",
                )
            )
        summary = summary_index.get(loop.loop_id)
        if summary is None:
            issues.append(
                ValidationIssue(
                    code="recycle_loop_missing_summary",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop.loop_id}' has no convergence summary.",
                    artifact_ref="flowsheet_case",
                )
            )
            continue
        if not summary.purge_policy_by_family:
            issues.append(
                ValidationIssue(
                    code="recycle_loop_missing_purge_policy",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop.loop_id}' has no explicit purge policy by impurity family.",
                    artifact_ref="flowsheet_case",
                )
            )
        if summary.convergence_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="recycle_loop_summary_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop.loop_id}' has a blocked convergence summary.",
                    artifact_ref="flowsheet_case",
                )
            )
    return issues


def validate_solve_result(solve_result: SolveResult) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if solve_result.convergence_status == "blocked":
        issues.append(
            ValidationIssue(
                code="solve_result_blocked",
                severity=Severity.BLOCKED,
                message="Flowsheet solve result is blocked.",
                artifact_ref="solve_result",
            )
        )
    for unit_id, status in solve_result.unitwise_status.items():
        if status == "blocked":
            issues.append(
                ValidationIssue(
                    code="unitwise_convergence_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{unit_id}' is blocked in the solve result.",
                    artifact_ref="solve_result",
                )
            )
    for section_id, status in solve_result.section_status.items():
        if status == "blocked":
            issues.append(
                ValidationIssue(
                    code="section_convergence_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Section '{section_id}' is blocked in the solve result.",
                    artifact_ref="solve_result",
                )
            )
    for unit_id, blockers in solve_result.unitwise_blockers.items():
        for blocker in blockers:
            issues.append(
                ValidationIssue(
                    code="unitwise_packet_coverage_blocked",
                    severity=Severity.BLOCKED,
                    message=blocker,
                    artifact_ref="solve_result",
                )
            )
    for unit_id, status in solve_result.composition_status.items():
        if status == "blocked":
            issues.append(
                ValidationIssue(
                    code="composition_convergence_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Unit '{unit_id}' is blocked in composition propagation.",
                    artifact_ref="solve_result",
                )
            )
    for separation_id, status in solve_result.separation_status.items():
        if status == "blocked":
            issues.append(
                ValidationIssue(
                    code="separation_convergence_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Separation '{separation_id}' is blocked in the solve result.",
                    artifact_ref="solve_result",
                )
            )
    for loop_id, status in solve_result.recycle_status.items():
        if status == "blocked":
            issues.append(
                ValidationIssue(
                    code="recycle_convergence_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{loop_id}' is blocked in the solve result.",
                artifact_ref="solve_result",
            )
        )
    for summary in solve_result.convergence_summaries:
        if summary.convergence_status == "blocked":
            issues.append(
                ValidationIssue(
                    code="recycle_summary_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Recycle loop '{summary.loop_id}' is blocked in the convergence summary.",
                    artifact_ref="solve_result",
                )
            )
    for message in solve_result.critic_messages:
        lowered = message.lower()
        if (
            "blocked" not in lowered
            and "too high" not in lowered
            and "no usable" not in lowered
            and "no unit thermal packet" not in lowered
            and "weak component split closure" not in lowered
        ):
            continue
        issues.append(
            ValidationIssue(
                code="flowsheet_critic",
                severity=Severity.BLOCKED,
                message=message,
                artifact_ref="solve_result",
            )
        )
    return issues


def validate_energy_balance(energy_balance: EnergyBalance) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not energy_balance.unit_thermal_packets:
        issues.append(
            ValidationIssue(
                code="missing_unit_thermal_packets",
                severity=Severity.BLOCKED,
                message="Energy balance does not expose any unit thermal packets.",
                artifact_ref="energy_balance",
            )
        )
        return issues
    total_packet_heating = round(sum(packet.heating_kw for packet in energy_balance.unit_thermal_packets), 3)
    total_packet_cooling = round(sum(packet.cooling_kw for packet in energy_balance.unit_thermal_packets), 3)
    if abs(total_packet_heating - energy_balance.total_heating_kw) > max(5.0, energy_balance.total_heating_kw * 0.05):
        issues.append(
            ValidationIssue(
                code="thermal_packet_heating_mismatch",
                severity=Severity.BLOCKED,
                message="Summed thermal-packet heating duty does not reconcile with total heating duty.",
                artifact_ref="energy_balance",
            )
        )
    if abs(total_packet_cooling - energy_balance.total_cooling_kw) > max(5.0, energy_balance.total_cooling_kw * 0.05):
        issues.append(
            ValidationIssue(
                code="thermal_packet_cooling_mismatch",
                severity=Severity.BLOCKED,
                message="Summed thermal-packet cooling duty does not reconcile with total cooling duty.",
                artifact_ref="energy_balance",
            )
        )
    hot_packets = [packet for packet in energy_balance.unit_thermal_packets if packet.cooling_kw > 0.0]
    cold_packets = [packet for packet in energy_balance.unit_thermal_packets if packet.heating_kw > 0.0]
    feasible_recovery_window = any(
        hot_packet.hot_supply_temp_c - cold_packet.cold_supply_temp_c >= 20.0
        for hot_packet in hot_packets
        for cold_packet in cold_packets
        if hot_packet.unit_id != cold_packet.unit_id
    )
    if hot_packets and cold_packets and feasible_recovery_window and not energy_balance.network_candidates:
        issues.append(
            ValidationIssue(
                code="missing_network_candidates",
                severity=Severity.BLOCKED,
                message="Energy balance has both hot and cold packets but no exchanger-network candidates.",
                artifact_ref="energy_balance",
            )
        )
    for packet in energy_balance.unit_thermal_packets:
        if packet.heating_kw > 0.0 and packet.cold_target_temp_c <= packet.cold_supply_temp_c:
            issues.append(
                ValidationIssue(
                    code="invalid_cold_side_temperature_rise",
                    severity=Severity.BLOCKED,
                    message=f"Thermal packet '{packet.packet_id}' does not show a usable cold-side temperature rise.",
                    artifact_ref="energy_balance",
                )
            )
        if packet.cooling_kw > 0.0 and packet.hot_supply_temp_c <= packet.hot_target_temp_c:
            issues.append(
                ValidationIssue(
                    code="invalid_hot_side_temperature_drop",
                    severity=Severity.BLOCKED,
                    message=f"Thermal packet '{packet.packet_id}' does not show a usable hot-side temperature drop.",
                    artifact_ref="energy_balance",
                )
            )
    for candidate in energy_balance.network_candidates:
        if not candidate.feasible:
            continue
        if candidate.recovered_duty_kw <= 0.0:
            issues.append(
                ValidationIssue(
                    code="invalid_network_candidate_duty",
                    severity=Severity.BLOCKED,
                    message=f"Network candidate '{candidate.candidate_id}' has non-positive recovered duty.",
                    artifact_ref="energy_balance",
                )
            )
    return issues


def validate_thermo_assessment(thermo: ThermoAssessmentArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not thermo.feasible:
        issues.append(
            ValidationIssue(
                code="thermo_infeasible",
                severity=Severity.BLOCKED,
                message="Thermodynamic assessment marks the selected route as infeasible.",
                artifact_ref="thermo_assessment",
            )
        )
    if abs(thermo.estimated_reaction_enthalpy_kj_per_mol) < 1e-6:
        issues.append(
            ValidationIssue(
                code="thermo_zero_enthalpy",
                severity=Severity.BLOCKED,
                message="Thermodynamic assessment produced a near-zero reaction enthalpy, which is not credible for the selected basis.",
                artifact_ref="thermo_assessment",
            )
        )
    return issues


def validate_kinetic_assessment(kinetics: KineticAssessmentArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing_arrhenius_basis = (
        kinetics.activation_energy_kj_per_mol <= 0.0
        and kinetics.pre_exponential_factor <= 0.0
        and any(
            phrase in " ".join(kinetics.assumptions).lower()
            for phrase in (
                "could not be determined",
                "critical data gap",
                "no experimental data",
            )
        )
    )
    if not kinetics.feasible:
        issues.append(
            ValidationIssue(
                code="kinetics_infeasible",
                severity=Severity.BLOCKED,
                message="Kinetic assessment marks the selected route as infeasible.",
                artifact_ref="kinetic_assessment",
            )
        )
    if kinetics.design_residence_time_hr <= 0.0:
        issues.append(
            ValidationIssue(
                code="invalid_residence_time",
                severity=Severity.BLOCKED,
                message="Design residence time must be positive.",
                artifact_ref="kinetic_assessment",
            )
        )
    if kinetics.activation_energy_kj_per_mol <= 0.0:
        if not missing_arrhenius_basis:
            issues.append(
                ValidationIssue(
                    code="invalid_activation_energy",
                    severity=Severity.BLOCKED,
                    message="Activation energy must be positive for the selected kinetic basis.",
                    artifact_ref="kinetic_assessment",
                )
            )
    return issues


def validate_phase_feasibility(
    route,
    thermo: ThermoAssessmentArtifact,
    kinetics: KineticAssessmentArtifact,
    reaction_system: ReactionSystem,
    energy_balance: EnergyBalance,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if route.residence_time_hr > 0:
        mismatch = abs(kinetics.design_residence_time_hr - route.residence_time_hr) / route.residence_time_hr
        if mismatch > 0.50:
            issues.append(
                ValidationIssue(
                    code="residence_time_basis_mismatch",
                    severity=Severity.BLOCKED,
                    message="Kinetic residence-time basis diverges materially from the selected route basis.",
                    artifact_ref="design_basis",
                )
            )
    if thermo.estimated_reaction_enthalpy_kj_per_mol < 0.0 and energy_balance.total_cooling_kw <= 0.0:
        issues.append(
            ValidationIssue(
                code="missing_exotherm_cooling",
                severity=Severity.BLOCKED,
                message="Selected route is exothermic, but the energy balance does not provide cooling duty.",
                artifact_ref="energy_balance",
            )
        )
    if thermo.estimated_reaction_enthalpy_kj_per_mol > 0.0 and energy_balance.total_heating_kw <= 0.0:
        issues.append(
            ValidationIssue(
                code="missing_endotherm_heating",
                severity=Severity.BLOCKED,
                message="Selected route is endothermic, but the energy balance does not provide heating duty.",
                artifact_ref="energy_balance",
            )
        )
    if reaction_system.conversion_fraction < 0.50:
        issues.append(
            ValidationIssue(
                code="low_conversion_basis",
                severity=Severity.BLOCKED,
                message="Reaction conversion basis is too low for downstream preliminary equipment sizing.",
                artifact_ref="reaction_system",
            )
        )
    return issues


def validate_chapter(chapter: ChapterArtifact, available_source_ids: set[str], strict: bool) -> list[ValidationIssue]:
    issues = require_source_ids(chapter.citations, available_source_ids, chapter.chapter_id, "missing_chapter_sources")
    if strict and not chapter.citations:
        issues.append(
            ValidationIssue(
                code="chapter_without_citations",
                severity=Severity.BLOCKED,
                message=f"Chapter '{chapter.title}' has no citations under strict mode.",
                artifact_ref=chapter.chapter_id,
            )
        )
    return issues


def validate_report_parity_framework(
    framework: ReportParityFrameworkArtifact,
    benchmark_manifest: BenchmarkManifest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    contract_ids = {contract.chapter_id for contract in framework.chapter_contracts}
    missing_contracts = [chapter_id for chapter_id in benchmark_manifest.required_chapters if chapter_id not in contract_ids]
    if missing_contracts:
        issues.append(
            ValidationIssue(
                code="missing_report_parity_contracts",
                severity=Severity.BLOCKED,
                message="Report parity framework is missing required chapter contracts: " + ", ".join(missing_contracts) + ".",
                artifact_ref="report_parity_framework",
            )
        )
    if not framework.support_contracts:
        issues.append(
            ValidationIssue(
                code="missing_report_support_contracts",
                severity=Severity.BLOCKED,
                message="Report parity framework did not define benchmark support-section contracts.",
                artifact_ref="report_parity_framework",
            )
        )
    return issues


def validate_report_parity(parity: ReportParityArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if parity.missing_chapter_ids:
        issues.append(
            ValidationIssue(
                code="missing_benchmark_report_chapters",
                severity=Severity.BLOCKED,
                message="Benchmark-required report chapters are missing: " + ", ".join(parity.missing_chapter_ids) + ".",
                artifact_ref="report_parity",
            )
        )
    if parity.partial_chapter_count or parity.partial_support_count or parity.missing_support_count:
        issues.append(
            ValidationIssue(
                code="report_parity_gap_remaining",
                severity=Severity.WARNING,
                message=(
                    "Report parity is not complete yet: "
                    f"{parity.partial_chapter_count} partial chapters, "
                    f"{parity.partial_support_count} partial support sections, "
                    f"{parity.missing_support_count} missing support sections."
                ),
                artifact_ref="report_parity",
            )
        )
    return issues


def validate_report_acceptance(acceptance: ReportAcceptanceArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if acceptance.overall_status == ReportAcceptanceStatus.BLOCKED:
        issues.append(
            ValidationIssue(
                code="benchmark_acceptance_blocked",
                severity=Severity.BLOCKED,
                message=acceptance.summary,
                artifact_ref="report_acceptance",
            )
        )
    elif acceptance.overall_status == ReportAcceptanceStatus.CONDITIONAL:
        issues.append(
            ValidationIssue(
                code="benchmark_acceptance_conditional",
                severity=Severity.WARNING,
                message=acceptance.summary,
                artifact_ref="report_acceptance",
            )
        )
    return issues


def validate_missing_data_acceptance_artifact(artifact: MissingDataAcceptanceArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    severity = Severity.BLOCKED if artifact.overall_status == ReportAcceptanceStatus.BLOCKED else Severity.WARNING
    if artifact.overall_status != ReportAcceptanceStatus.COMPLETE:
        issues.append(
            ValidationIssue(
                code="missing_data_acceptance_not_complete",
                severity=severity,
                message=artifact.summary,
                artifact_ref="missing_data_acceptance",
            )
        )
    for item in artifact.issues:
        issues.append(
            ValidationIssue(
                code=item.code,
                severity=Severity.BLOCKED if item.severity == "blocked" else Severity.WARNING,
                message=item.message,
                artifact_ref="missing_data_acceptance",
            )
        )
    return issues


def validate_utility_network_decision(utility_network_decision: UtilityNetworkDecision, config: ProjectConfig) -> list[ValidationIssue]:
    issues = validate_decision_record(utility_network_decision.decision, "utility_network_decision")
    selected_case = next((item for item in utility_network_decision.cases if item.case_id == utility_network_decision.selected_case_id), None)
    if selected_case is None:
        issues.append(
            ValidationIssue(
                code="missing_selected_heat_case",
                severity=Severity.BLOCKED,
                message=f"Route '{utility_network_decision.route_id}' has no selected heat-integration case.",
                artifact_ref="utility_network_decision",
            )
        )
        return issues
    better_case = next(
        (
            item
            for item in utility_network_decision.cases
            if item.feasible
            and item.case_id != selected_case.case_id
            and item.annual_savings_inr > selected_case.annual_savings_inr * 1.05
        ),
        None,
    )
    if selected_case.case_id.endswith("no_recovery") and better_case and config.heat_integration.enabled:
        issues.append(
            ValidationIssue(
                code="missed_heat_recovery_case",
                severity=Severity.BLOCKED,
                message=(
                    f"Selected case '{selected_case.case_id}' leaves purchased utility unreduced even though "
                    f"'{better_case.case_id}' provides materially higher savings."
                ),
                artifact_ref="utility_network_decision",
            )
        )
    if utility_network_decision.utility_target.recoverable_duty_kw >= config.heat_integration.min_recoverable_duty_kw and not utility_network_decision.cases:
        issues.append(
            ValidationIssue(
                code="missing_heat_cases",
                severity=Severity.BLOCKED,
                message="Recoverable duty trigger was met, but no heat-integration cases were generated.",
                artifact_ref="utility_network_decision",
            )
        )
    stream_index = {stream.stream_id: stream for stream in utility_network_decision.heat_streams}
    for case in utility_network_decision.cases:
        if not case.feasible:
            continue
        for match in case.heat_matches:
            hot_stream = stream_index.get(match.hot_stream_id)
            cold_stream = stream_index.get(match.cold_stream_id)
            if hot_stream is None or cold_stream is None:
                issues.append(
                    ValidationIssue(
                        code="heat_match_missing_stream",
                        severity=Severity.BLOCKED,
                        message=f"Heat match '{match.match_id}' references missing hot/cold streams.",
                        artifact_ref="utility_network_decision",
                    )
                )
                continue
            if match.direct and hot_stream.supply_temp_c - cold_stream.target_temp_c < match.min_approach_temp_c:
                issues.append(
                    ValidationIssue(
                        code="insufficient_direct_heat_driving_force",
                        severity=Severity.BLOCKED,
                        message=f"Direct heat match '{match.match_id}' does not satisfy the minimum approach temperature.",
                        artifact_ref="utility_network_decision",
                    )
                )
            if not match.direct and hot_stream.supply_temp_c <= cold_stream.supply_temp_c:
                issues.append(
                    ValidationIssue(
                        code="invalid_indirect_heat_match",
                        severity=Severity.BLOCKED,
                        message=f"Indirect heat match '{match.match_id}' has no usable thermal lift from the selected hot stream.",
                        artifact_ref="utility_network_decision",
                    )
                )
    return issues


def validate_utility_architecture(utility_architecture: UtilityArchitectureDecision) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_steps = utility_architecture.architecture.selected_train_steps
    selected_package_items = utility_architecture.architecture.selected_package_items
    heat_stream_set = utility_architecture.architecture.heat_stream_set
    if heat_stream_set and heat_stream_set.hot_streams and heat_stream_set.cold_streams and not heat_stream_set.composite_intervals:
        issues.append(
            ValidationIssue(
                code="missing_composite_intervals",
                severity=Severity.BLOCKED,
                message="Utility architecture has hot and cold heat streams but no composite thermal intervals.",
                artifact_ref="utility_architecture",
            )
        )
    if not selected_steps:
        return issues
    selected_islands = utility_architecture.architecture.selected_island_ids
    case_index = {case.case_id: case for case in utility_architecture.architecture.cases}
    selected_case = case_index.get(utility_architecture.architecture.selected_case_id or "")
    if not selected_islands or not selected_case or not selected_case.utility_islands:
        issues.append(
            ValidationIssue(
                code="missing_utility_islands",
                severity=Severity.BLOCKED,
                message="Selected utility architecture exposes train steps but no utility-island architecture.",
                artifact_ref="utility_architecture",
            )
        )
    else:
        island_by_id = {island.island_id: island for island in selected_case.utility_islands}
        for step in selected_steps:
            if not step.island_id or step.island_id not in island_by_id:
                issues.append(
                    ValidationIssue(
                        code="train_step_missing_island",
                        severity=Severity.BLOCKED,
                        message=f"Selected train step '{step.step_id}' is not assigned to a valid utility island.",
                        artifact_ref="utility_architecture",
                    )
                )
            if selected_case.header_count > 0 and step.header_level <= 0:
                issues.append(
                    ValidationIssue(
                        code="train_step_missing_header_level",
                        severity=Severity.BLOCKED,
                        message=f"Selected train step '{step.step_id}' is missing staged-header level metadata.",
                        artifact_ref="utility_architecture",
                    )
                )
            if selected_case.condenser_reboiler_cluster_count > 0 and not step.cluster_id:
                issues.append(
                    ValidationIssue(
                        code="train_step_missing_cluster_id",
                        severity=Severity.BLOCKED,
                        message=f"Selected train step '{step.step_id}' is missing condenser-reboiler cluster metadata.",
                        artifact_ref="utility_architecture",
                    )
                )
        for island in selected_case.utility_islands:
            if not island.train_step_ids:
                issues.append(
                    ValidationIssue(
                        code="empty_utility_island",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' has no selected train steps.",
                        artifact_ref="utility_architecture",
                    )
                )
            if selected_case.header_count > 0 and island.header_level <= 0:
                issues.append(
                    ValidationIssue(
                        code="utility_island_missing_header_level",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' is missing staged-header level metadata.",
                        artifact_ref="utility_architecture",
                    )
                )
            if selected_case.condenser_reboiler_cluster_count > 0 and not island.cluster_id:
                issues.append(
                    ValidationIssue(
                        code="utility_island_missing_cluster_id",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' is missing condenser-reboiler cluster metadata.",
                        artifact_ref="utility_architecture",
                    )
                )
            if island.target_recovered_duty_kw > island.recoverable_potential_kw + 1e-6:
                issues.append(
                    ValidationIssue(
                        code="utility_island_target_exceeds_potential",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' has a target duty above its recoverable potential.",
                        artifact_ref="utility_architecture",
                    )
                )
            if island.recovered_duty_kw > island.target_recovered_duty_kw + 1.0:
                issues.append(
                    ValidationIssue(
                        code="utility_island_recovery_exceeds_target",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' recovers more duty than its allocated target.",
                        artifact_ref="utility_architecture",
                    )
                )
            if island.candidate_match_count <= 0:
                issues.append(
                    ValidationIssue(
                        code="utility_island_missing_candidate_basis",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' has no candidate-match basis.",
                        artifact_ref="utility_architecture",
                    )
                )
    package_index: dict[str, set[str]] = {}
    for package_item in selected_package_items:
        package_index.setdefault(package_item.parent_step_id, set()).add(package_item.package_role)
        if not package_item.island_id:
            issues.append(
                ValidationIssue(
                    code="package_item_missing_island",
                    severity=Severity.BLOCKED,
                    message=f"Utility package item '{package_item.package_item_id}' is missing an island id.",
                    artifact_ref="utility_architecture",
                )
            )
    for step in selected_steps:
        roles = package_index.get(step.step_id, set())
        if "exchanger" not in roles or "controls" not in roles:
            issues.append(
                ValidationIssue(
                    code="incomplete_utility_train_package",
                    severity=Severity.BLOCKED,
                    message=f"Selected train step '{step.step_id}' is missing mandatory exchanger/control package items.",
                    artifact_ref="utility_architecture",
                )
            )
        if step.medium.lower() != "direct":
            missing_roles = {"circulation", "expansion", "relief"} - roles
            if missing_roles:
                issues.append(
                    ValidationIssue(
                        code="incomplete_htm_package",
                        severity=Severity.BLOCKED,
                        message=f"Selected HTM train step '{step.step_id}' is missing package roles: {', '.join(sorted(missing_roles))}.",
                        artifact_ref="utility_architecture",
                    )
                )
    if selected_case and selected_case.header_count > 0:
        header_islands = {
            package_item.island_id
            for package_item in selected_package_items
            if package_item.package_role == "header" and package_item.island_id
        }
        for island in selected_case.utility_islands:
            if island.header_level > 0 and island.island_id not in header_islands:
                issues.append(
                    ValidationIssue(
                        code="missing_header_package_item",
                        severity=Severity.BLOCKED,
                        message=f"Utility island '{island.island_id}' is missing the staged-header/network package item required by the selected topology.",
                        artifact_ref="utility_architecture",
                    )
                )
    for package_item in selected_package_items:
        if package_item.package_role == "exchanger" and package_item.package_family in {"reboiler", "condenser"}:
            if package_item.heat_transfer_area_m2 <= 0.0 or package_item.lmtd_k <= 0.0:
                issues.append(
                    ValidationIssue(
                        code="underspecified_reboiler_condenser_package",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Utility package '{package_item.package_item_id}' must include positive area and LMTD "
                            f"for {package_item.package_family} sizing."
                        ),
                        artifact_ref="utility_architecture",
                    )
                )
    return issues


def validate_heat_integration_study(study: HeatIntegrationStudyArtifact, config: ProjectConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for route_decision in study.route_decisions:
        issues.extend(validate_utility_network_decision(route_decision, config))
    if config.heat_integration.enabled and not study.route_decisions:
        issues.append(
            ValidationIssue(
                code="missing_heat_integration_study",
                severity=Severity.BLOCKED,
                message="Heat integration is enabled, but no route heat studies were generated.",
                artifact_ref="heat_integration_study",
            )
        )
    return issues


def _is_india_source(source: SourceRecord) -> bool:
    if source.country and source.country.lower() == "india":
        return True
    if source.geographic_scope in {GeographicScope.INDIA, GeographicScope.STATE, GeographicScope.CITY}:
        return True
    return "india" in (source.geographic_label or "").lower()


def validate_research_bundle(bundle: ResearchBundle, config: ProjectConfig) -> tuple[list[ValidationIssue], list[str], list[str]]:
    issues: list[ValidationIssue] = []
    missing_groups: list[str] = []
    stale_groups: list[str] = []

    source_ids = {source.source_id for source in bundle.sources}
    if not source_ids:
        issues.append(
            ValidationIssue(
                code="no_sources",
                severity=Severity.BLOCKED,
                message="No sources were discovered or supplied for the run.",
                artifact_ref="research_bundle",
            )
        )
        return issues, ["all"], stale_groups

    if config.require_india_only_data:
        india_sources = [source for source in bundle.sources if _is_india_source(source)]
        if not india_sources:
            issues.append(
                ValidationIssue(
                    code="missing_india_sources",
                    severity=Severity.BLOCKED,
                    message="India-only mode is enabled, but no India-grounded sources were found.",
                    artifact_ref="research_bundle",
                )
            )
            missing_groups.append("india_sources")
        domain_checks = {
            "india_market": {SourceDomain.MARKET, SourceDomain.ECONOMICS},
            "india_site": {SourceDomain.SITE, SourceDomain.LOGISTICS, SourceDomain.REGULATORY},
            "india_utilities": {SourceDomain.UTILITIES},
        }
        for group, accepted_domains in domain_checks.items():
            matched = [source for source in india_sources if source.source_domain in accepted_domains]
            if not matched:
                missing_groups.append(group)
        reference_year = config.basis.economic_reference_year
        for group, accepted_domains in {
            "india_market": {SourceDomain.MARKET, SourceDomain.ECONOMICS},
            "india_utilities": {SourceDomain.UTILITIES},
        }.items():
            matched = [source for source in india_sources if source.source_domain in accepted_domains]
            if not matched:
                continue
            if any(source.reference_year and reference_year - source.reference_year > 5 and source.normalization_year is None for source in matched):
                stale_groups.append(group)
        if stale_groups:
            issues.append(
                ValidationIssue(
                    code="stale_india_sources",
                    severity=Severity.BLOCKED,
                    message=f"India source groups need normalization or refresh: {', '.join(sorted(stale_groups))}.",
                    artifact_ref="research_bundle",
                )
            )
        if missing_groups:
            issues.append(
                ValidationIssue(
                    code="missing_india_coverage",
                    severity=Severity.BLOCKED,
                    message=f"Missing India evidence groups: {', '.join(sorted(missing_groups))}.",
                    artifact_ref="research_bundle",
                )
            )
    return issues, sorted(set(missing_groups)), sorted(set(stale_groups))


def validate_document_fact_collection(collection: DocumentFactCollectionArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if collection.documents and collection.process_option_count <= 0:
        issues.append(
            ValidationIssue(
                code="missing_document_process_options",
                severity=Severity.WARNING,
                message="User documents were ingested, but no structured process options were extracted.",
                artifact_ref="user_document_facts",
            )
        )
    for document in collection.documents:
        seen_ids: set[str] = set()
        for comparison in document.process_comparisons:
            for option in comparison.options:
                if option.option_id in seen_ids:
                    issues.append(
                        ValidationIssue(
                            code="duplicate_document_option_id",
                            severity=Severity.BLOCKED,
                            message=f"Document option id '{option.option_id}' is duplicated within extracted document facts.",
                            artifact_ref="user_document_facts",
                        )
                    )
                seen_ids.add(option.option_id)
    return issues


def validate_route_chemistry_artifact(artifact: RouteChemistryArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for graph in artifact.route_graphs:
        for issue in graph.unresolved_issues:
            severity = Severity.WARNING
            issues.append(
                ValidationIssue(
                    code=issue.issue_code,
                    severity=severity,
                    message=issue.message,
                    artifact_ref="route_chemistry",
                    source_refs=issue.citations,
                )
            )
        if not graph.species_nodes:
            issues.append(
                ValidationIssue(
                    code="missing_route_species_graph",
                    severity=Severity.BLOCKED,
                    message=f"Route '{graph.route_id}' has no species nodes in the route chemistry graph.",
                    artifact_ref="route_chemistry",
                )
            )
    return issues


def validate_route_discovery_artifact(artifact: RouteDiscoveryArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    route_ids = [row.route_id for row in artifact.rows]
    if len(route_ids) != len(set(route_ids)):
        issues.append(
            ValidationIssue(
                code="duplicate_route_discovery_rows",
                severity=Severity.BLOCKED,
                message="Route discovery artifact contains duplicate route ids.",
                artifact_ref="route_discovery",
            )
        )
    if not artifact.rows:
        issues.append(
            ValidationIssue(
                code="missing_route_discovery_rows",
                severity=Severity.BLOCKED,
                message="Route discovery artifact is empty.",
                artifact_ref="route_discovery",
            )
        )
    return issues


def validate_route_screening_artifact(artifact: RouteScreeningArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    route_ids = [row.route_id for row in artifact.rows]
    if len(route_ids) != len(set(route_ids)):
        issues.append(
            ValidationIssue(
                code="duplicate_route_screening_rows",
                severity=Severity.BLOCKED,
                message="Route screening artifact contains duplicate route ids.",
                artifact_ref="route_screening",
            )
        )
    retained = set(artifact.retained_route_ids)
    eliminated = set(artifact.eliminated_route_ids)
    if retained & eliminated:
        issues.append(
            ValidationIssue(
                code="route_screening_conflicting_status",
                severity=Severity.BLOCKED,
                message="A route cannot be both retained and eliminated in route screening.",
                artifact_ref="route_screening",
            )
        )
    if not retained:
        issues.append(
            ValidationIssue(
                code="route_screening_no_retained_routes",
                severity=Severity.BLOCKED,
                message="Route screening eliminated every route before final selection.",
                artifact_ref="route_screening",
            )
        )
    return issues


def validate_route_process_claims_artifact(artifact: RouteProcessClaimsArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.claims:
        issues.append(
            ValidationIssue(
                code="missing_route_process_claims",
                severity=Severity.BLOCKED,
                message="No route process claims were generated for process screening.",
                artifact_ref="route_process_claims",
            )
        )
        return issues
    keys = [(claim.route_id, claim.claim_type) for claim in artifact.claims]
    if len(keys) != len(set(keys)):
        issues.append(
            ValidationIssue(
                code="duplicate_route_process_claims",
                severity=Severity.BLOCKED,
                message="Route process claims contain duplicate route/claim-type pairs.",
                artifact_ref="route_process_claims",
            )
        )
    return issues


def validate_chemistry_decision_artifact(artifact: ChemistryDecisionArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.selected_route_id:
        issues.append(
            ValidationIssue(
                code="missing_chemistry_decision_route",
                severity=Severity.BLOCKED,
                message="Chemistry decision artifact must identify the selected route.",
                artifact_ref="chemistry_decision",
            )
        )
    if artifact.chemistry_basis_status == "blocked":
        issues.append(
            ValidationIssue(
                code="chemistry_decision_blocked",
                severity=Severity.BLOCKED,
                message="Selected route chemistry is still blocked.",
                artifact_ref="chemistry_decision",
            )
        )
    return issues


def validate_property_demand_plan(plan: PropertyDemandPlan) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not plan.items:
        issues.append(
            ValidationIssue(
                code="missing_property_demand_items",
                severity=Severity.BLOCKED,
                message="Property demand plan is empty.",
                artifact_ref="property_demand_plan",
            )
        )
        return issues
    if plan.blocking_species_ids:
        issues.append(
            ValidationIssue(
                code="species_property_coverage_blocked",
                severity=Severity.BLOCKED,
                message=f"Species-aware property coverage remains blocked for: {', '.join(plan.blocking_species_ids[:8])}.",
                artifact_ref="property_demand_plan",
            )
        )
    return issues


def validate_species_resolution_artifact(artifact: SpeciesResolutionArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.routes:
        issues.append(
            ValidationIssue(
                code="missing_species_resolution_routes",
                severity=Severity.BLOCKED,
                message="Species-resolution artifact is empty.",
                artifact_ref="species_resolution",
            )
        )
        return issues
    for route in artifact.routes:
        if route.invalid_core_species_names:
            issues.append(
                ValidationIssue(
                    code="invalid_core_species_detected",
                    severity=Severity.BLOCKED,
                    message=f"Route '{route.route_id}' has invalid core species: {', '.join(route.invalid_core_species_names[:6])}.",
                    artifact_ref="species_resolution",
                    source_refs=route.citations,
                )
            )
    return issues


def validate_reaction_network_v2_artifact(artifact: ReactionNetworkV2Artifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.routes:
        issues.append(
            ValidationIssue(
                code="missing_reaction_network_routes",
                severity=Severity.BLOCKED,
                message="Reaction-network v2 artifact is empty.",
                artifact_ref="reaction_network_v2",
            )
        )
        return issues
    for route in artifact.routes:
        if route.step_count <= 0:
            issues.append(
                ValidationIssue(
                    code="missing_reaction_steps_v2",
                    severity=Severity.BLOCKED,
                    message=f"Route '{route.route_id}' has no reaction steps in reaction-network v2.",
                    artifact_ref="reaction_network_v2",
                    source_refs=route.citations,
                )
            )
    return issues


def validate_thermo_admissibility_artifact(artifact: ThermoAdmissibilityArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.sections:
        issues.append(
            ValidationIssue(
                code="missing_thermo_admissibility_sections",
                severity=Severity.BLOCKED,
                message="Thermo-admissibility artifact contains no section evaluations.",
                artifact_ref="thermo_admissibility",
            )
        )
        return issues
    if artifact.selected_route_id and artifact.selected_route_status == ScientificGateStatus.FAIL:
        issues.append(
            ValidationIssue(
                code="selected_route_thermo_inadmissible",
                severity=Severity.BLOCKED,
                message=f"Selected route '{artifact.selected_route_id}' failed thermodynamic admissibility.",
                artifact_ref="thermo_admissibility",
                source_refs=artifact.citations,
            )
        )
    return issues


def validate_kinetics_admissibility_artifact(artifact: KineticsAdmissibilityArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.steps:
        issues.append(
            ValidationIssue(
                code="missing_kinetics_admissibility_steps",
                severity=Severity.BLOCKED,
                message="Kinetics-admissibility artifact contains no reaction-step evaluations.",
                artifact_ref="kinetics_admissibility",
            )
        )
        return issues
    if artifact.selected_route_id and artifact.selected_route_status == ScientificGateStatus.FAIL:
        issues.append(
            ValidationIssue(
                code="selected_route_kinetics_inadmissible",
                severity=Severity.BLOCKED,
                message=f"Selected route '{artifact.selected_route_id}' failed kinetics admissibility.",
                artifact_ref="kinetics_admissibility",
                source_refs=artifact.citations,
            )
        )
    return issues


def validate_flowsheet_intent_artifact(artifact: FlowsheetIntentArtifact) -> list[ValidationIssue]:
    if artifact.intents:
        return []
    return [
        ValidationIssue(
            code="missing_flowsheet_intents",
            severity=Severity.BLOCKED,
            message="Flowsheet-intent artifact has no synthesized intents.",
            artifact_ref="flowsheet_intents",
            source_refs=artifact.citations,
        )
    ]


def validate_topology_candidate_artifact(artifact: TopologyCandidateArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.candidates:
        issues.append(
            ValidationIssue(
                code="missing_topology_candidates",
                severity=Severity.BLOCKED,
                message="Topology-candidate artifact is empty.",
                artifact_ref="topology_candidates",
            )
        )
        return issues
    if artifact.selected_route_id:
        selected = next((item for item in artifact.candidates if item.route_id == artifact.selected_route_id), None)
        if selected is None:
            issues.append(
                ValidationIssue(
                    code="selected_topology_candidate_missing",
                    severity=Severity.BLOCKED,
                    message=f"Selected route '{artifact.selected_route_id}' has no topology candidate row.",
                    artifact_ref="topology_candidates",
                )
            )
        elif selected.status == ScientificGateStatus.FAIL:
            issues.append(
                ValidationIssue(
                    code="selected_topology_inadmissible",
                    severity=Severity.BLOCKED,
                    message=f"Selected route '{artifact.selected_route_id}' has no admissible topology candidate.",
                    artifact_ref="topology_candidates",
                    source_refs=selected.citations,
                )
            )
    return issues


def validate_commercial_product_basis_artifact(artifact: CommercialProductBasisArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if artifact.sold_solution_basis_kg_hr <= 0.0 or artifact.active_basis_kg_hr <= 0.0:
        issues.append(
            ValidationIssue(
                code="invalid_commercial_product_basis_flow",
                severity=Severity.BLOCKED,
                message="Commercial product basis must carry positive sold-solution and active-basis throughput.",
                artifact_ref="commercial_product_basis",
            )
        )
    if not 0.0 < artifact.active_fraction <= 1.0:
        issues.append(
            ValidationIssue(
                code="invalid_commercial_active_fraction",
                severity=Severity.BLOCKED,
                message="Commercial product basis active fraction must lie between zero and one.",
                artifact_ref="commercial_product_basis",
            )
        )
    if artifact.sold_solution_price_inr_per_kg <= 0.0 or artifact.active_price_inr_per_kg <= 0.0:
        issues.append(
            ValidationIssue(
                code="invalid_commercial_price_basis",
                severity=Severity.BLOCKED,
                message="Commercial product basis must include positive sold-solution and active-normalized prices.",
                artifact_ref="commercial_product_basis",
            )
        )
    return issues


def validate_bac_impurity_model_artifact(artifact: BACImpurityModelArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.items:
        issues.append(
            ValidationIssue(
                code="missing_bac_impurity_model",
                severity=Severity.WARNING,
                message="BAC impurity model was not generated.",
                artifact_ref="bac_impurity_model",
            )
        )
        return issues
    if artifact.unresolved_impurity_ids:
        issues.append(
            ValidationIssue(
                code="unresolved_bac_impurity_classes",
                severity=Severity.WARNING,
                message="BAC impurity model still has unresolved impurity classes: " + ", ".join(artifact.unresolved_impurity_ids) + ".",
                artifact_ref="bac_impurity_model",
            )
        )
    return issues


def validate_bac_purification_section_artifact(artifact: BACPurificationSectionArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.sections:
        issues.append(
            ValidationIssue(
                code="missing_bac_purification_sections",
                severity=Severity.WARNING,
                message="BAC purification-section artifact was not generated.",
                artifact_ref="bac_purification_sections",
            )
        )
        return issues
    if artifact.unresolved_section_ids:
        issues.append(
            ValidationIssue(
                code="unresolved_bac_purification_sections",
                severity=Severity.WARNING,
                message="BAC purification sections remain unresolved: " + ", ".join(artifact.unresolved_section_ids) + ".",
                artifact_ref="bac_purification_sections",
            )
        )
    return issues


def validate_unit_train_consistency_artifact(artifact: UnitTrainConsistencyArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.rows:
        issues.append(
            ValidationIssue(
                code="missing_unit_train_consistency_rows",
                severity=Severity.WARNING,
                message="Unit-train consistency artifact has no comparison rows.",
                artifact_ref="unit_train_consistency",
            )
        )
        return issues
    for row in artifact.rows:
        if row.status == "blocked":
            issues.append(
                ValidationIssue(
                    code="unit_train_consistency_blocked",
                    severity=Severity.BLOCKED,
                    message=f"Artifact '{row.artifact_ref}' diverges from the selected unit train.",
                    artifact_ref="unit_train_consistency",
                    source_refs=[row.artifact_ref],
                )
            )
    return issues


def validate_design_confidence_artifact(artifact: DesignConfidenceArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if artifact.blocked_unit_ids:
        issues.append(
            ValidationIssue(
                code="blocked_unit_design_confidence",
                severity=Severity.BLOCKED,
                message="Major unit design remains blocked for: " + ", ".join(artifact.blocked_unit_ids[:8]) + ".",
                artifact_ref="design_confidence",
            )
        )
    return issues


def validate_economic_coverage_decision(artifact: EconomicCoverageDecision) -> list[ValidationIssue]:
    if artifact.status != "blocked":
        return []
    return [
        ValidationIssue(
            code="economic_coverage_blocked",
            severity=Severity.BLOCKED,
            message="Economic coverage is blocked: " + (", ".join(artifact.missing_basis) or artifact.rationale),
            artifact_ref="economic_coverage",
            source_refs=artifact.citations,
        )
    ]


def validate_claim_graph_artifact(artifact: ClaimGraphArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.claims:
        issues.append(
            ValidationIssue(
                code="missing_scientific_claims",
                severity=Severity.WARNING,
                message="Claim graph is empty.",
                artifact_ref="claim_graph",
            )
        )
        return issues
    for claim in artifact.claims:
        if claim.status == ClaimStatus.BLOCKED and claim.blocking:
            issues.append(
                ValidationIssue(
                    code="blocked_scientific_claim",
                    severity=Severity.BLOCKED,
                    message=f"Scientific claim '{claim.claim_id}' is blocked.",
                    artifact_ref="claim_graph",
                    source_refs=claim.citations,
                )
            )
    return issues


def validate_inference_question_queue(artifact: InferenceQuestionQueueArtifact) -> list[ValidationIssue]:
    if artifact.active_questions:
        return []
    return [
        ValidationIssue(
            code="missing_inference_questions",
            severity=Severity.WARNING,
            message="No active inference questions were generated.",
            artifact_ref="inference_question_queue",
        )
    ]


def validate_revision_ledger_artifact(artifact: RevisionLedgerArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for ticket in artifact.tickets:
        if ticket.status == "skipped":
            issues.append(
                ValidationIssue(
                    code="revision_budget_exhausted",
                    severity=Severity.BLOCKED,
                    message=f"Revision budget exhausted for target stage '{ticket.target_stage_id}'.",
                    artifact_ref="revision_ledger",
                    source_refs=ticket.citations,
                )
            )
    return issues


def validate_scientific_gate_matrix(artifact: ScientificGateMatrixArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for entry in artifact.entries:
        if entry.status == ScientificGateStatus.FAIL:
            issues.append(
                ValidationIssue(
                    code=f"{entry.gate_id}_failed",
                    severity=Severity.BLOCKED,
                    message=f"Scientific gate '{entry.gate_id}' failed.",
                    artifact_ref="scientific_gate_matrix",
                    source_refs=entry.citations,
                )
            )
    return issues


def validate_route_selection_comparison(artifact: RouteSelectionComparisonArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not artifact.rows:
        issues.append(
            ValidationIssue(
                code="missing_route_selection_comparison_rows",
                severity=Severity.BLOCKED,
                message="Route-selection comparison artifact is empty.",
                artifact_ref="route_selection_comparison",
            )
        )
        return issues
    selected_rows = [row for row in artifact.rows if row.selected]
    if len(selected_rows) != 1:
        issues.append(
            ValidationIssue(
                code="invalid_route_selection_comparison_selection",
                severity=Severity.BLOCKED,
                message="Route-selection comparison must contain exactly one selected route row.",
                artifact_ref="route_selection_comparison",
            )
        )
    return issues


def validate_unit_train_candidate_set(candidate_set: UnitTrainCandidateSet) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not candidate_set.blueprints:
        issues.append(
            ValidationIssue(
                code="missing_unit_train_candidates",
                severity=Severity.BLOCKED,
                message="No unit-train candidates were synthesized from route chemistry.",
                artifact_ref="unit_train_candidates",
            )
        )
        return issues
    for blueprint in candidate_set.blueprints:
        if not blueprint.steps:
            issues.append(
                ValidationIssue(
                    code="empty_flowsheet_blueprint",
                    severity=Severity.BLOCKED,
                    message=f"Flowsheet blueprint '{blueprint.blueprint_id}' has no steps.",
                    artifact_ref="unit_train_candidates",
                )
            )
    return issues


def validate_flowsheet_blueprint(blueprint: FlowsheetBlueprintArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not blueprint.steps:
        issues.append(
            ValidationIssue(
                code="missing_flowsheet_blueprint_steps",
                severity=Severity.BLOCKED,
                message="Selected flowsheet blueprint has no steps.",
                artifact_ref="flowsheet_blueprint",
            )
        )
        return issues
    if not any(step.step_role == "reaction" for step in blueprint.steps):
        issues.append(
            ValidationIssue(
                code="missing_flowsheet_blueprint_reaction_step",
                severity=Severity.BLOCKED,
                message="Selected flowsheet blueprint has no reaction step.",
                artifact_ref="flowsheet_blueprint",
            )
        )
    if not any(step.step_role in {"primary_separation", "purification", "filtration", "drying"} for step in blueprint.steps):
        issues.append(
            ValidationIssue(
                code="missing_flowsheet_blueprint_separation_step",
                severity=Severity.WARNING,
                message="Selected flowsheet blueprint has no explicit downstream separation or finishing step.",
                artifact_ref="flowsheet_blueprint",
            )
        )
    return issues


def validate_india_price_data(
    price_data: list[IndianPriceDatum],
    available_source_ids: set[str],
    config: ProjectConfig,
    artifact_ref: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.require_india_only_data and not price_data:
        issues.append(
            ValidationIssue(
                code="missing_india_price_data",
                severity=Severity.BLOCKED,
                message="India-only economics requires cited Indian price data.",
                artifact_ref=artifact_ref,
            )
        )
        return issues
    for datum in price_data:
        if datum.value_inr <= 0:
            issues.append(
                ValidationIssue(
                    code="nonpositive_price",
                    severity=Severity.BLOCKED,
                    message=f"Indian price datum '{datum.datum_id}' is non-positive.",
                    artifact_ref=artifact_ref,
                )
            )
        if datum.reference_year != datum.normalization_year and datum.normalization_year < config.basis.economic_reference_year:
            issues.append(
                ValidationIssue(
                    code="stale_price_normalization",
                    severity=Severity.BLOCKED,
                    message=f"Indian price datum '{datum.datum_id}' is normalized only to {datum.normalization_year}.",
                    artifact_ref=artifact_ref,
                )
            )
        if datum.citations:
            issues.extend(require_source_ids(datum.citations, available_source_ids, artifact_ref, "missing_india_price_sources"))
        elif config.strict_citation_policy:
            issues.append(
                ValidationIssue(
                    code="uncited_india_price_data",
                    severity=Severity.BLOCKED,
                    message=f"Indian price datum '{datum.datum_id}' has no citations.",
                    artifact_ref=artifact_ref,
                )
            )
    return issues


def validate_india_location_data(
    locations: list[IndianLocationDatum],
    available_source_ids: set[str],
    config: ProjectConfig,
    artifact_ref: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.require_india_only_data and not locations:
        issues.append(
            ValidationIssue(
                code="missing_india_location_data",
                severity=Severity.BLOCKED,
                message="India-only siting requires cited Indian location data.",
                artifact_ref=artifact_ref,
            )
        )
        return issues
    for location in locations:
        if location.country.lower() != "india":
            issues.append(
                ValidationIssue(
                    code="non_india_site",
                    severity=Severity.BLOCKED,
                    message=f"Site candidate '{location.site_name}' is not marked as Indian.",
                    artifact_ref=artifact_ref,
                )
            )
        if location.citations:
            issues.extend(require_source_ids(location.citations, available_source_ids, artifact_ref, "missing_india_location_sources"))
        elif config.strict_citation_policy:
            issues.append(
                ValidationIssue(
                    code="uncited_india_location",
                    severity=Severity.BLOCKED,
                    message=f"Indian location datum '{location.location_id}' has no citations.",
                    artifact_ref=artifact_ref,
                )
            )
    return issues


def validate_reactor_design(reactor: ReactorDesign) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if reactor.design_volume_m3 <= 0 or reactor.liquid_holdup_m3 <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_reactor_volume",
                severity=Severity.BLOCKED,
                message="Reactor design volume must be positive.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if reactor.heat_transfer_area_m2 <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_heat_transfer_area",
                severity=Severity.BLOCKED,
                message="Reactor heat transfer area must be positive.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if reactor.kinetic_space_time_hr <= 0.0 or reactor.design_conversion_fraction <= 0.0:
        issues.append(
            ValidationIssue(
                code="missing_reactor_kinetic_basis",
                severity=Severity.BLOCKED,
                message="Reactor design requires kinetics-coupled residence-time and conversion basis outputs.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if (
        reactor.heat_release_density_kw_m3 <= 0.0
        or reactor.adiabatic_temperature_rise_c <= 0.0
        or reactor.heat_removal_capacity_kw <= 0.0
        or not reactor.runaway_risk_label
    ):
        issues.append(
            ValidationIssue(
                code="missing_reactor_stability_basis",
                severity=Severity.BLOCKED,
                message="Reactor design requires thermal-severity, heat-removal, and runaway-screening outputs.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if reactor.catalyst_name and (
        reactor.catalyst_inventory_kg <= 0.0
        or reactor.catalyst_cycle_days <= 0.0
        or reactor.catalyst_weight_hourly_space_velocity_1_hr <= 0.0
    ):
        issues.append(
            ValidationIssue(
                code="missing_catalyst_service_basis",
                severity=Severity.BLOCKED,
                message="Catalytic reactor service requires catalyst inventory, cycle, and WHSV outputs.",
                artifact_ref=reactor.reactor_id,
            )
        )
    return issues


def validate_column_design(column: ColumnDesign) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if column.design_stages < 2:
        issues.append(
            ValidationIssue(
                code="invalid_column_stages",
                severity=Severity.BLOCKED,
                message="Column design must contain at least two stages.",
                artifact_ref=column.column_id,
            )
        )
    if column.column_diameter_m <= 0 or column.column_height_m <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_column_geometry",
                severity=Severity.BLOCKED,
                message="Column diameter and height must be positive.",
                artifact_ref=column.column_id,
            )
        )
    if "absorption" not in column.service.lower() and "crystallizer" not in column.service.lower():
        if (
            column.feed_quality_q_factor <= 0.0
            or column.murphree_efficiency <= 0.0
            or column.top_relative_volatility <= 1.0
            or column.bottom_relative_volatility <= 1.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_distillation_feed_basis",
                    severity=Severity.BLOCKED,
                    message="Distillation-style service requires feed-quality, Murphree-efficiency, and section-volatility outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.rectifying_theoretical_stages <= 0.0
            or column.stripping_theoretical_stages <= 0.0
            or column.rectifying_vapor_load_kg_hr <= 0.0
            or column.stripping_liquid_load_m3_hr <= 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_distillation_section_basis",
                    severity=Severity.BLOCKED,
                    message="Distillation-style service requires explicit rectifying/stripping section stage and load outputs.",
                    artifact_ref=column.column_id,
                )
            )
    if "absorption" in column.service.lower():
        if column.absorber_capture_fraction <= 0.0 or column.absorber_packed_height_m <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_absorber_screening_basis",
                    severity=Severity.BLOCKED,
                    message="Absorber service requires capture and packed-height screening outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if column.absorber_ntu <= 0.0 or column.absorber_htu_m <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_absorber_mass_transfer_basis",
                    severity=Severity.BLOCKED,
                    message="Absorber service requires packed-tower mass-transfer screening metrics.",
                    artifact_ref=column.column_id,
                )
            )
        if column.absorber_overall_mass_transfer_coefficient_1_s <= 0.0 or column.absorber_total_pressure_drop_kpa <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_absorber_hydraulic_refinement",
                    severity=Severity.BLOCKED,
                    message="Absorber service requires packed-tower coefficient and pressure-drop screening outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.absorber_min_wetting_rate_kg_m2_s <= 0.0
            or column.absorber_wetting_ratio <= 0.0
            or column.absorber_flooding_velocity_m_s <= 0.0
            or column.absorber_flooding_margin_fraction <= 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_absorber_operating_window_basis",
                    severity=Severity.BLOCKED,
                    message="Absorber service requires packed-bed wetting and flooding window outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            not column.absorber_packing_family
            or column.absorber_packing_specific_area_m2_m3 <= 0.0
            or column.absorber_effective_interfacial_area_m2_m3 <= 0.0
            or column.absorber_gas_phase_transfer_coeff_1_s <= 0.0
            or column.absorber_liquid_phase_transfer_coeff_1_s <= 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_absorber_packing_family_basis",
                    severity=Severity.BLOCKED,
                    message="Absorber service requires packing-family transfer-unit outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.absorber_minimum_solvent_to_gas_ratio <= 0.0
            or column.absorber_optimized_solvent_to_gas_ratio <= 0.0
            or column.absorber_rich_loading_mol_mol <= 0.0
            or column.absorber_solvent_rate_case_count < 2
        ):
            issues.append(
                ValidationIssue(
                    code="missing_absorber_solvent_optimization_basis",
                    severity=Severity.BLOCKED,
                    message="Absorber service requires solvent-rate optimization outputs and lean/rich loading screening.",
                    artifact_ref=column.column_id,
                )
            )
    if "crystallizer" in column.service.lower():
        if column.crystallizer_yield_fraction <= 0.0 or column.filter_area_m2 <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_crystallizer_screening_basis",
                    severity=Severity.BLOCKED,
                    message="Crystallizer service requires crystal-yield and filter-area screening outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.filter_cycle_time_hr <= 0.0
            or column.filter_cake_formation_time_hr <= 0.0
            or column.filter_wash_time_hr <= 0.0
            or column.filter_discharge_time_hr <= 0.0
            or column.filter_cycles_per_hr <= 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_filter_cycle_basis",
                    severity=Severity.BLOCKED,
                    message="Crystallizer/filtration service requires explicit filter cycle-timing outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if column.crystallizer_residence_time_hr <= 0.0 or column.dryer_refined_duty_kw <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_solids_unit_refinement",
                    severity=Severity.BLOCKED,
                    message="Crystallizer/dryer service requires residence-time, holdup, and refined dryer-duty outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if column.crystal_growth_rate_mm_hr <= 0.0 or column.slurry_circulation_rate_m3_hr <= 0.0 or column.dryer_product_moisture_fraction <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_solids_growth_or_endpoint_basis",
                    severity=Severity.BLOCKED,
                    message="Crystallizer/dryer service requires crystal-growth, slurry-circulation, and dryer-endpoint screening outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.crystal_size_d10_mm <= 0.0
            or column.crystal_size_d50_mm <= 0.0
            or column.crystal_size_d90_mm <= 0.0
            or column.dryer_equilibrium_moisture_fraction <= 0.0
            or column.dryer_mass_transfer_coefficient_kg_m2_s <= 0.0
            or column.dryer_heat_transfer_area_m2 <= 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_solids_distribution_or_transfer_basis",
                    severity=Severity.BLOCKED,
                    message="Crystallizer/dryer service requires PSD and dryer heat/mass-transfer endpoint outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.crystal_classifier_cut_size_mm <= 0.0
            or column.crystal_classified_product_fraction <= 0.0
            or column.filter_specific_cake_resistance_m_kg <= 0.0
            or column.filter_medium_resistance_1_m <= 0.0
            or column.dryer_exhaust_humidity_ratio_kg_kg <= 0.0
            or column.dryer_dry_air_flow_kg_hr <= 0.0
            or column.dryer_exhaust_saturation_fraction <= 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_solids_transport_limited_basis",
                    severity=Severity.BLOCKED,
                    message="Crystallizer/dryer service requires classification, filter-resistance, and dryer exhaust-humidity outputs.",
                    artifact_ref=column.column_id,
                )
            )
        if (
            column.dryer_humidity_lift_kg_kg <= 0.0
            or column.dryer_exhaust_dewpoint_c <= 0.0
            or column.dryer_endpoint_margin_fraction < 0.0
        ):
            issues.append(
                ValidationIssue(
                    code="missing_dryer_endpoint_margin_basis",
                    severity=Severity.BLOCKED,
                    message="Crystallizer/dryer service requires humidity-lift, dewpoint, and endpoint-margin outputs.",
                    artifact_ref=column.column_id,
                )
            )
    return issues


def validate_mechanical_design_artifact(artifact: MechanicalDesignArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for item in artifact.items:
        if item.design_pressure_bar > 0.0 and not item.pressure_class:
            issues.append(
                ValidationIssue(
                    code="missing_mechanical_pressure_class",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' is missing a pressure class.",
                    artifact_ref="mechanical_design",
                )
            )
        if item.hydrotest_pressure_bar < item.design_pressure_bar:
            issues.append(
                ValidationIssue(
                    code="invalid_hydrotest_pressure",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' has hydrotest pressure below design pressure.",
                    artifact_ref="mechanical_design",
                )
            )
        if not item.support_load_case:
            issues.append(
                ValidationIssue(
                    code="missing_support_load_case",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' is missing a support load case.",
                    artifact_ref="mechanical_design",
                )
            )
        if item.support_type == "pipe rack support" and not item.pipe_rack_tie_in_required:
            issues.append(
                ValidationIssue(
                    code="missing_pipe_rack_tie_in",
                    severity=Severity.BLOCKED,
                    message=f"Pipe-rack-supported equipment '{item.equipment_id}' must flag rack tie-in requirements.",
                    artifact_ref="mechanical_design",
                )
            )
        if item.maintenance_platform_required and item.platform_area_m2 <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_platform_area",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' requires a platform area when a maintenance platform is selected.",
                    artifact_ref="mechanical_design",
                )
            )
        if item.equipment_type.lower() not in {"utility control package", "instrument panel"} and item.foundation_footprint_m2 <= 0.0:
            issues.append(
                ValidationIssue(
                    code="missing_foundation_footprint",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' requires a positive foundation footprint.",
                    artifact_ref="mechanical_design",
                )
            )
        if item.anchor_group_count <= 0 and item.support_type != "pipe rack support":
            issues.append(
                ValidationIssue(
                    code="missing_anchor_group_basis",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' requires anchor-group screening outputs.",
                    artifact_ref="mechanical_design",
                )
            )
        if item.local_shell_load_interaction_factor < 1.0:
            issues.append(
                ValidationIssue(
                    code="invalid_local_shell_interaction",
                    severity=Severity.BLOCKED,
                    message=f"Mechanical design for '{item.equipment_id}' has an invalid local shell/load interaction factor.",
                    artifact_ref="mechanical_design",
                )
            )
    return issues


def validate_equipment_applicability(
    route,
    reactor_choice: DecisionRecord,
    separation_choice: DecisionRecord,
    reactor: ReactorDesign,
    column: ColumnDesign,
    exchanger: HeatExchangerDesign,
    utility_network_decision: UtilityNetworkDecision,
    unit_operation_family: UnitOperationFamilyArtifact | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_case = next((item for item in utility_network_decision.cases if item.case_id == utility_network_decision.selected_case_id), None)
    selected_sep = (separation_choice.selected_candidate_id or "").lower()
    selected_reactor = (reactor_choice.selected_candidate_id or "").lower()
    column_service = column.service.lower()
    reactor_type = reactor.reactor_type.lower()
    absorption_design_present = (
        "absorb" in column_service
        or column.absorber_capture_fraction > 0.0
        or column.absorber_henry_constant_bar > 0.0
        or column.absorber_theoretical_stages > 0.0
        or column.absorber_packed_height_m > 0.0
    )
    solids_design_present = (
        "crystall" in column_service
        or "dryer" in column_service
        or "filter" in column_service
        or column.crystallizer_yield_fraction > 0.0
        or column.filter_area_m2 > 0.0
        or column.dryer_evaporation_load_kg_hr > 0.0
    )
    if unit_operation_family is not None:
        reactor_index = {item.candidate_id: item for item in unit_operation_family.reactor_candidates}
        separation_index = {item.candidate_id: item for item in unit_operation_family.separation_candidates}
        allowed_reactors = {item.candidate_id for item in unit_operation_family.reactor_candidates if item.applicability_status != "blocked"}
        allowed_separations = {item.candidate_id for item in unit_operation_family.separation_candidates if item.applicability_status != "blocked"}
        selected_reactor_candidate = reactor_index.get(reactor_choice.selected_candidate_id or "")
        selected_separation_candidate = separation_index.get(separation_choice.selected_candidate_id or "")
        if reactor_choice.selected_candidate_id and reactor_choice.selected_candidate_id not in allowed_reactors:
            issues.append(
                ValidationIssue(
                    code="reactor_choice_family_mismatch",
                    severity=Severity.BLOCKED,
                    message="Selected reactor family is outside the allowed unit-operation family candidates for the chosen route.",
                    artifact_ref="reactor_choice",
                )
            )
        if separation_choice.selected_candidate_id and separation_choice.selected_candidate_id not in allowed_separations:
            issues.append(
                ValidationIssue(
                    code="separation_choice_family_mismatch",
                    severity=Severity.BLOCKED,
                    message="Selected separation family is outside the allowed unit-operation family candidates for the chosen route.",
                    artifact_ref="separation_choice",
                )
            )
        if selected_reactor_candidate is not None and selected_reactor_candidate.applicability_status == "fallback":
            issues.append(
                ValidationIssue(
                    code="reactor_choice_nonpreferred_family_candidate",
                    severity=Severity.WARNING,
                    message="Selected reactor family is only a fallback candidate for the chosen unit-operation family.",
                    artifact_ref="reactor_choice",
                )
            )
        if selected_separation_candidate is not None and selected_separation_candidate.applicability_status == "fallback":
            issues.append(
                ValidationIssue(
                    code="separation_choice_nonpreferred_family_candidate",
                    severity=Severity.WARNING,
                    message="Selected separation family is only a fallback candidate for the chosen unit-operation family.",
                    artifact_ref="separation_choice",
                )
            )
        if selected_reactor_candidate is not None and selected_reactor_candidate.critic_flags:
            issues.append(
                ValidationIssue(
                    code="reactor_choice_family_critic_flags_present",
                    severity=Severity.WARNING,
                    message="Selected reactor family still carries applicability critic flags: "
                    + ", ".join(selected_reactor_candidate.critic_flags[:3])
                    + ".",
                    artifact_ref="reactor_choice",
                )
            )
        if selected_separation_candidate is not None and selected_separation_candidate.critic_flags:
            issues.append(
                ValidationIssue(
                    code="separation_choice_family_critic_flags_present",
                    severity=Severity.WARNING,
                    message="Selected separation family still carries applicability critic flags: "
                    + ", ".join(selected_separation_candidate.critic_flags[:3])
                    + ".",
                    artifact_ref="separation_choice",
                )
            )
    if any(token in selected_reactor for token in ("fixed_bed", "oxidizer", "converter")) and not any(
        token in reactor_type for token in ("fixed", "bed", "oxid", "converter")
    ):
        issues.append(
            ValidationIssue(
                code="reactor_design_service_mismatch",
                severity=Severity.BLOCKED,
                message="Selected reactor choice is inconsistent with the detailed reactor design type.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if any(token in selected_reactor for token in ("cstr", "stirred")) and not any(token in reactor_type for token in ("cstr", "stirred")):
        issues.append(
            ValidationIssue(
                code="reactor_design_service_mismatch",
                severity=Severity.BLOCKED,
                message="Selected reactor choice is inconsistent with the detailed reactor design type.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if "absorption" in selected_sep and not absorption_design_present:
        issues.append(
            ValidationIssue(
                code="separation_design_service_mismatch",
                severity=Severity.BLOCKED,
                message="Selected absorber-led separation choice is inconsistent with the detailed process-unit service basis.",
                artifact_ref=column.column_id,
            )
        )
    if any(token in selected_sep for token in ("crystallizer", "drying", "filtration")) and not solids_design_present:
        issues.append(
            ValidationIssue(
                code="separation_design_service_mismatch",
                severity=Severity.BLOCKED,
                message="Selected solids-handling separation choice is inconsistent with the detailed process-unit service basis.",
                artifact_ref=column.column_id,
            )
        )
    if any(token in selected_sep for token in ("distillation", "fractionation", "column")) and (absorption_design_present or solids_design_present):
        issues.append(
            ValidationIssue(
                code="separation_design_service_mismatch",
                severity=Severity.BLOCKED,
                message="Selected distillation-led separation choice is inconsistent with the detailed process-unit service basis.",
                artifact_ref=column.column_id,
            )
        )
    if route.route_id == "eo_hydration" and not any(token in reactor.reactor_type.lower() for token in ("plug", "hydrator")):
        issues.append(
            ValidationIssue(
                code="reactor_type_route_mismatch",
                severity=Severity.BLOCKED,
                message="EO hydration route requires a plug-flow/hydrator-style conceptual reactor basis.",
                artifact_ref=reactor.reactor_id,
            )
        )
    if route.route_id == "eo_hydration" and column.light_key.lower() != "water":
        issues.append(
            ValidationIssue(
                code="column_key_mismatch",
                severity=Severity.BLOCKED,
                message="EO hydration purification should treat water as the light key in the principal column basis.",
                artifact_ref=column.column_id,
            )
        )
    if reactor_choice.selected_candidate_id and reactor_choice.selected_candidate_id not in reactor_choice.selected_summary.lower().replace(" ", "_"):
        pass
    if separation_choice.selected_summary and route.route_id not in separation_choice.selected_summary.lower() and route.route_id == "eo_hydration":
        if "water removal" not in separation_choice.selected_summary.lower():
            issues.append(
                ValidationIssue(
                    code="separation_choice_basis_weak",
                    severity=Severity.BLOCKED,
                    message="Selected separation basis does not clearly reflect the water-removal driven EG purification sequence.",
                    artifact_ref="separation_choice",
                )
            )
    if selected_case and selected_case.case_id.endswith("pinch_htm") and reactor.heat_duty_kw < selected_case.recovered_duty_kw * 0.15:
        issues.append(
            ValidationIssue(
                code="heat_recovery_vs_reactor_duty_mismatch",
                severity=Severity.BLOCKED,
                message="Chosen HTM recovery case claims more recoverable duty than the reactor basis can plausibly supply.",
                artifact_ref="utility_network_decision",
            )
        )
    if unit_operation_family is not None:
        family_id = unit_operation_family.route_family_id
        selected_sep = separation_choice.selected_candidate_id or ""
        selected_reactor = reactor_choice.selected_candidate_id or ""
        support_ops = set(unit_operation_family.supporting_unit_operations)
        if family_id in {"gas_absorption_converter_train", "regeneration_loop_train"}:
            if "absorption" not in selected_sep:
                issues.append(
                    ValidationIssue(
                        code="absorber_family_selection_missing",
                        severity=Severity.BLOCKED,
                        message="Gas absorption route families require an absorption-led separation choice.",
                        artifact_ref="separation_choice",
                    )
                )
            if "absorption" not in column.service.lower():
                issues.append(
                    ValidationIssue(
                        code="absorber_family_design_missing",
                        severity=Severity.BLOCKED,
                        message="Gas absorption route families require absorber-style process-unit design output.",
                        artifact_ref=column.column_id,
                    )
                )
            if "absorber" not in support_ops:
                issues.append(
                    ValidationIssue(
                        code="absorber_family_support_missing",
                        severity=Severity.BLOCKED,
                        message="Gas absorption route families must declare absorber support operations.",
                        artifact_ref="unit_operation_family",
                    )
                )
        if family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"}:
            if not any(token in selected_sep for token in ("crystallizer", "drying")):
                issues.append(
                    ValidationIssue(
                        code="solids_family_selection_missing",
                        severity=Severity.BLOCKED,
                        message="Solids route families require a crystallizer/filter/dryer-led separation choice.",
                        artifact_ref="separation_choice",
                    )
                )
            if "crystallizer" not in column.service.lower():
                issues.append(
                    ValidationIssue(
                        code="solids_family_design_missing",
                        severity=Severity.BLOCKED,
                        message="Solids route families require crystallizer/dryer process-unit design output.",
                        artifact_ref=column.column_id,
                    )
                )
            if not {"classifier", "dryer"} & support_ops:
                issues.append(
                    ValidationIssue(
                        code="solids_family_support_missing",
                        severity=Severity.BLOCKED,
                        message="Solids route families must declare classifier/dryer support operations.",
                        artifact_ref="unit_operation_family",
                    )
                )
        if family_id == "extraction_recovery_train" and "extract" not in selected_sep:
            issues.append(
                ValidationIssue(
                    code="extraction_family_selection_missing",
                    severity=Severity.BLOCKED,
                    message="Extraction-intensive route families require an extraction-led separation choice.",
                    artifact_ref="separation_choice",
                )
            )
        if family_id == "oxidation_recovery_train" and not any(token in selected_reactor for token in ("oxidizer", "fixed_bed")):
            issues.append(
                ValidationIssue(
                    code="oxidation_family_reactor_missing",
                    severity=Severity.BLOCKED,
                    message="Oxidation route families require oxidation- or converter-style reactor selection.",
                    artifact_ref="reactor_choice",
                )
            )
    return issues


def validate_technical_economic_critics(
    column: ColumnDesign,
    utility_network_decision: UtilityNetworkDecision,
    cost_model: CostModel,
    unit_operation_family: UnitOperationFamilyArtifact | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    family_id = (unit_operation_family.route_family_id if unit_operation_family is not None else "").lower()
    selected_case = next((item for item in utility_network_decision.cases if item.case_id == utility_network_decision.selected_case_id), None)
    selected_arch_case = None
    if utility_architecture is not None and utility_architecture.architecture is not None:
        selected_arch_case = next(
            (item for item in utility_architecture.architecture.cases if item.case_id == utility_architecture.architecture.selected_case_id),
            None,
        )
    if selected_case is not None and selected_case.recovered_duty_kw > 100.0:
        if cost_model.annual_utility_cost >= utility_network_decision.base_annual_utility_cost_inr * 0.995:
            issues.append(
                ValidationIssue(
                    code="heat_recovery_without_economic_benefit",
                    severity=Severity.WARNING,
                    message="Selected heat-recovery architecture claims meaningful recovered duty but does not reduce annual utility cost in the economic model.",
                    artifact_ref="cost_model",
                )
            )
    if selected_arch_case is not None:
        if selected_arch_case.architecture_family != "base" and cost_model.integration_capex_inr <= 0.0:
            issues.append(
                ValidationIssue(
                    code="heat_network_architecture_missing_capex_basis",
                    severity=Severity.BLOCKED,
                    message="Non-base heat-network architecture is selected but no integration CAPEX burden is carried into economics.",
                    artifact_ref="cost_model",
                )
            )
        if column.utility_architecture_family and selected_arch_case.architecture_family and column.utility_architecture_family != selected_arch_case.architecture_family:
            issues.append(
                ValidationIssue(
                    code="column_utility_architecture_mismatch",
                    severity=Severity.BLOCKED,
                    message="Detailed process-unit utility architecture does not match the selected utility-network case family.",
                    artifact_ref=column.column_id,
                )
            )
    if (family_id in {"gas_absorption_converter_train", "regeneration_loop_train"} or column.absorber_packing_family) and column.absorber_packing_family:
        if cost_model.annual_packing_replacement_cost <= 0.0:
            issues.append(
                ValidationIssue(
                    code="absorber_packing_cost_missing",
                    severity=Severity.BLOCKED,
                    message="Absorber packing is selected in design, but economics carry no explicit packing replacement burden.",
                    artifact_ref="cost_model",
                )
            )
    if family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"} or column.filter_area_m2 > 0.0 or column.dryer_evaporation_load_kg_hr > 0.0:
        if column.filter_area_m2 > 0.0 and cost_model.annual_filter_media_replacement_cost <= 0.0:
            issues.append(
                ValidationIssue(
                    code="filter_media_cost_missing",
                    severity=Severity.BLOCKED,
                    message="Filter area is present in the solids design basis, but economics carry no filter-media replacement cost.",
                    artifact_ref="cost_model",
                )
            )
        if column.dryer_evaporation_load_kg_hr > 0.0 and cost_model.annual_dryer_exhaust_treatment_cost <= 0.0:
            issues.append(
                ValidationIssue(
                    code="dryer_exhaust_cost_missing",
                    severity=Severity.BLOCKED,
                    message="Dryer duty is present in the solids design basis, but economics carry no dryer exhaust-treatment burden.",
                    artifact_ref="cost_model",
                )
            )
    return issues


def validate_cost_model(cost_model: CostModel, available_source_ids: set[str], config: ProjectConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.require_india_only_data and cost_model.currency != "INR":
        issues.append(
            ValidationIssue(
                code="non_inr_cost_model",
                severity=Severity.BLOCKED,
                message="India-only mode requires the cost model currency to be INR.",
                artifact_ref="cost_model",
            )
        )
    issues.extend(validate_india_price_data(cost_model.india_price_data, available_source_ids, config, "cost_model"))
    if cost_model.integration_capex_inr > 0.0 and not cost_model.utility_island_costs:
        issues.append(
            ValidationIssue(
                code="missing_utility_island_costs",
                severity=Severity.BLOCKED,
                message="Cost model includes utility-integration CAPEX but no utility-island economic breakdown.",
                artifact_ref="cost_model",
            )
        )
    if cost_model.utility_island_costs:
        service_total = sum(item.annual_service_cost_inr for item in cost_model.utility_island_costs)
        if abs(service_total - cost_model.annual_utility_island_service_cost) / max(cost_model.annual_utility_island_service_cost, 1.0) > 0.01:
            issues.append(
                ValidationIssue(
                    code="utility_island_service_mismatch",
                    severity=Severity.BLOCKED,
                    message="Utility-island service total does not match the cost-model aggregate.",
                    artifact_ref="cost_model",
                )
            )
        replacement_total = sum(item.annualized_replacement_cost_inr for item in cost_model.utility_island_costs)
        if abs(replacement_total - cost_model.annual_utility_island_replacement_cost) / max(cost_model.annual_utility_island_replacement_cost, 1.0) > 0.01:
            issues.append(
                ValidationIssue(
                    code="utility_island_replacement_mismatch",
                    severity=Severity.BLOCKED,
                    message="Utility-island replacement total does not match the cost-model aggregate.",
                    artifact_ref="cost_model",
                )
            )
        capex_total = sum(item.project_capex_burden_inr for item in cost_model.utility_island_costs)
        if capex_total > cost_model.total_capex * 1.01:
            issues.append(
                ValidationIssue(
                    code="utility_island_capex_exceeds_total",
                    severity=Severity.BLOCKED,
                    message="Utility-island project CAPEX burden exceeds total CAPEX.",
                    artifact_ref="cost_model",
                )
            )
        utility_share_total = sum(item.utility_cost_share_fraction for item in cost_model.utility_island_costs)
        if utility_share_total > 1.01:
            issues.append(
                ValidationIssue(
                    code="utility_island_share_exceeds_one",
                    severity=Severity.BLOCKED,
                    message="Utility-island utility-share fractions exceed unity.",
                    artifact_ref="cost_model",
                )
            )
        if any(item.maintenance_cycle_years <= 0.0 or item.replacement_event_cost_inr <= 0.0 for item in cost_model.utility_island_costs):
            issues.append(
                ValidationIssue(
                    code="utility_island_missing_maintenance_timing",
                    severity=Severity.BLOCKED,
                    message="Utility-island economics are missing maintenance-cycle or replacement-event timing.",
                    artifact_ref="cost_model",
                )
            )
    if cost_model.construction_months <= 0 or not cost_model.procurement_profile_label:
        issues.append(
            ValidationIssue(
                code="missing_procurement_timing_basis",
                severity=Severity.BLOCKED,
                message="Cost model is missing procurement timing basis fields.",
                artifact_ref="cost_model",
            )
        )
    if not cost_model.procurement_schedule:
        issues.append(
            ValidationIssue(
                code="missing_procurement_schedule",
                severity=Severity.BLOCKED,
                message="Cost model is missing a procurement capex draw schedule.",
                artifact_ref="cost_model",
            )
        )
    else:
        draw_fraction_total = sum(float(row.get("draw_fraction", 0.0)) for row in cost_model.procurement_schedule)
        if abs(draw_fraction_total - 1.0) > 0.02:
            issues.append(
                ValidationIssue(
                    code="procurement_draw_fraction_mismatch",
                    severity=Severity.BLOCKED,
                    message="Procurement schedule draw fractions do not sum to unity.",
                    artifact_ref="cost_model",
                )
            )
    if not cost_model.procurement_package_impacts:
        issues.append(
            ValidationIssue(
                code="missing_procurement_package_impacts",
                severity=Severity.BLOCKED,
                message="Cost model is missing procurement package timing detail by equipment class.",
                artifact_ref="cost_model",
            )
        )
    if cost_model.imported_equipment_fraction > 0.0 and cost_model.total_import_duty_inr <= 0.0:
        issues.append(
            ValidationIssue(
                code="missing_import_duty_basis",
                severity=Severity.BLOCKED,
                message="Cost model has imported equipment exposure but no import-duty burden.",
                artifact_ref="cost_model",
            )
        )
    route_service_total = (
        cost_model.route_solvent_recovery_service_cost_inr
        + cost_model.route_catalyst_service_cost_inr
        + cost_model.route_waste_treatment_burden_inr
    )
    if route_service_total > 0.0 and cost_model.annual_transport_service_cost + 1.0 < route_service_total:
        issues.append(
            ValidationIssue(
                code="route_service_burden_missing_from_cost_model",
                severity=Severity.BLOCKED,
                message="Route-derived service burdens exceed the total transport/service burden carried by the cost model.",
                artifact_ref="cost_model",
            )
        )
    if cost_model.route_site_fit_score < 0.0 or cost_model.route_site_fit_score > 100.0:
        issues.append(
            ValidationIssue(
                code="invalid_route_site_fit_score_in_cost_model",
                severity=Severity.BLOCKED,
                message="Route site-fit score on the cost model must lie between 0 and 100.",
                artifact_ref="cost_model",
            )
        )
    return issues


def validate_working_capital(model: WorkingCapitalModel) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if model.working_capital_inr <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_working_capital",
                severity=Severity.BLOCKED,
                message="Working capital must be positive.",
                artifact_ref="working_capital_model",
            )
        )
    if model.cash_buffer_days <= 0:
        issues.append(
            ValidationIssue(
                code="missing_cash_buffer_basis",
                severity=Severity.WARNING,
                message="Working capital has no explicit cash-buffer day basis.",
                artifact_ref="working_capital_model",
            )
        )
    if model.precommissioning_inventory_inr <= 0 or model.precommissioning_inventory_days <= 0:
        issues.append(
            ValidationIssue(
                code="missing_precommissioning_inventory_basis",
                severity=Severity.BLOCKED,
                message="Working capital must include a positive pre-commissioning inventory basis tied to the procurement/construction schedule.",
                artifact_ref="working_capital_model",
            )
        )
    if model.procurement_timing_factor <= 0 or model.peak_working_capital_month <= 0:
        issues.append(
            ValidationIssue(
                code="missing_working_capital_timing_basis",
                severity=Severity.BLOCKED,
                message="Working capital must include a procurement-linked timing factor and peak timing month.",
                artifact_ref="working_capital_model",
            )
        )
    if model.peak_working_capital_inr < model.working_capital_inr:
        issues.append(
            ValidationIssue(
                code="invalid_peak_working_capital",
                severity=Severity.BLOCKED,
                message="Peak working capital cannot be lower than steady-state working capital.",
                artifact_ref="working_capital_model",
            )
        )
    return issues


def validate_operations_planning(operations_planning: OperationsPlanningArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if operations_planning.raw_material_buffer_days <= 0 or operations_planning.finished_goods_buffer_days <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_operations_buffer_days",
                severity=Severity.BLOCKED,
                message="Operations planning must include positive raw-material and finished-goods buffer days.",
                artifact_ref="operations_planning",
            )
        )
    if operations_planning.campaign_length_days <= 0 or operations_planning.cleaning_cycle_days <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_operations_campaign_basis",
                severity=Severity.BLOCKED,
                message="Operations planning must include positive campaign and cleaning-cycle lengths.",
                artifact_ref="operations_planning",
            )
        )
    if operations_planning.restart_loss_fraction < 0 or operations_planning.throughput_loss_fraction < 0:
        issues.append(
            ValidationIssue(
                code="invalid_operations_loss_fraction",
                severity=Severity.BLOCKED,
                message="Operations planning loss fractions cannot be negative.",
                artifact_ref="operations_planning",
            )
        )
    return issues


def validate_financial_model(model: FinancialModel, config: ProjectConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.require_india_only_data and model.currency != "INR":
        issues.append(
            ValidationIssue(
                code="non_inr_financial_model",
                severity=Severity.BLOCKED,
                message="India-only mode requires the financial model currency to be INR.",
                artifact_ref="financial_model",
            )
        )
    if model.total_project_funding_inr <= 0.0 or model.construction_interest_during_construction_inr < 0.0:
        issues.append(
            ValidationIssue(
                code="missing_financing_timing_basis",
                severity=Severity.BLOCKED,
                message="Financial model is missing total funding or construction-interest basis.",
                artifact_ref="financial_model",
            )
        )
    debt_service_rows = [row for row in model.annual_schedule if float(row.get("debt_service_inr", 0.0)) > 0.0]
    if debt_service_rows and (model.minimum_dscr <= 0.0 or model.average_dscr <= 0.0):
        issues.append(
            ValidationIssue(
                code="missing_dscr_basis",
                severity=Severity.BLOCKED,
                message="Financial model includes debt service but no valid DSCR basis.",
                artifact_ref="financial_model",
            )
        )
    if debt_service_rows and not all("cfads_inr" in row for row in model.annual_schedule):
        issues.append(
            ValidationIssue(
                code="missing_lender_coverage_basis",
                severity=Severity.BLOCKED,
                message="Financial model includes debt service but no valid LLCR/PLCR basis.",
                artifact_ref="financial_model",
            )
        )
    if debt_service_rows and model.minimum_dscr < 1.0:
        issues.append(
            ValidationIssue(
                code="weak_dscr_screening",
                severity=Severity.WARNING,
                message="Financial model minimum DSCR is below 1.0 under the current screening basis.",
                artifact_ref="financial_model",
            )
        )
    if debt_service_rows and model.llcr < 1.30:
        issues.append(
            ValidationIssue(
                code="weak_llcr_screening",
                severity=Severity.WARNING,
                message="Financial model LLCR is below 1.30 under the current screening basis.",
                artifact_ref="financial_model",
            )
        )
    if debt_service_rows and model.plcr < 1.45:
        issues.append(
            ValidationIssue(
                code="weak_plcr_screening",
                severity=Severity.WARNING,
                message="Financial model PLCR is below 1.45 under the current screening basis.",
                artifact_ref="financial_model",
            )
        )
    return issues


def validate_financing_decision_alignment(
    financing_basis: DecisionRecord,
    financial_model: FinancialModel,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if (
        financing_basis.selected_candidate_id
        and financial_model.selected_financing_candidate_id
        and financing_basis.selected_candidate_id != financial_model.selected_financing_candidate_id
    ):
        issues.append(
            ValidationIssue(
                code="financing_decision_financial_model_mismatch",
                severity=Severity.BLOCKED,
                message="Selected financing decision does not match the financing basis used in the financial model.",
                artifact_ref="financing_basis_decision",
            )
        )
    if financial_model.covenant_breach_codes and not financing_basis.approval_required:
        issues.append(
            ValidationIssue(
                code="financing_decision_missing_approval_flag",
                severity=Severity.BLOCKED,
                message="Financing decision must require approval when the selected option still breaches lender screening covenants.",
                artifact_ref="financing_basis_decision",
            )
        )
    if financial_model.financing_scenario_reversal and not financing_basis.approval_required:
        issues.append(
            ValidationIssue(
                code="financing_decision_missing_scenario_reversal_flag",
                severity=Severity.BLOCKED,
                message="Financing decision must require approval when downside scenario ranking overturns the base financing preference.",
                artifact_ref="financing_basis_decision",
            )
        )
    return issues


def validate_flowsheet_graph(flowsheet: FlowsheetGraph) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not flowsheet.nodes:
        issues.append(
            ValidationIssue(
                code="flowsheet_missing_nodes",
                severity=Severity.BLOCKED,
                message="Flowsheet graph has no nodes.",
                artifact_ref="flowsheet_graph",
            )
        )
    if not flowsheet.unit_models:
        issues.append(
            ValidationIssue(
                code="flowsheet_missing_unit_models",
                severity=Severity.BLOCKED,
                message="Flowsheet graph has no unit-operation models.",
                artifact_ref="flowsheet_graph",
            )
        )
    return issues


def validate_control_architecture(control_architecture: ControlArchitectureDecision) -> list[ValidationIssue]:
    issues = validate_decision_record(control_architecture.decision, "control_architecture")
    if not control_architecture.critical_units:
        issues.append(
            ValidationIssue(
                code="control_architecture_no_critical_units",
                severity=Severity.WARNING,
                message="Control architecture did not identify any critical units.",
                artifact_ref="control_architecture",
            )
        )
    return issues


def validate_control_plan(control_plan: ControlPlanArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not control_plan.control_loops:
        issues.append(
            ValidationIssue(
                code="control_plan_empty",
                severity=Severity.BLOCKED,
                message="Control plan did not emit any control loops.",
                artifact_ref="control_plan",
            )
        )
        return issues
    missing_objective = [loop.control_id for loop in control_plan.control_loops if not loop.objective]
    missing_startup = [loop.control_id for loop in control_plan.control_loops if not loop.startup_logic]
    missing_override = [loop.control_id for loop in control_plan.control_loops if not loop.override_logic]
    if missing_objective:
        issues.append(
            ValidationIssue(
                code="control_plan_missing_objective",
                severity=Severity.WARNING,
                message=f"Control loops are missing explicit objective basis: {', '.join(missing_objective[:5])}.",
                artifact_ref="control_plan",
            )
        )
    if missing_startup:
        issues.append(
            ValidationIssue(
                code="control_plan_missing_startup_logic",
                severity=Severity.WARNING,
                message=f"Control loops are missing startup / shutdown logic: {', '.join(missing_startup[:5])}.",
                artifact_ref="control_plan",
            )
        )
    if missing_override:
        issues.append(
            ValidationIssue(
                code="control_plan_missing_override_logic",
                severity=Severity.WARNING,
                message=f"Control loops are missing override / permissive basis: {', '.join(missing_override[:5])}.",
                artifact_ref="control_plan",
            )
        )
    return issues


def validate_plant_diagram_semantics(artifact: PlantDiagramSemanticsArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    entity_ids = {entity.entity_id for entity in artifact.entities}
    entity_map = {entity.entity_id: entity for entity in artifact.entities}
    seen_entity_ids: set[str] = set()
    for entity in artifact.entities:
        if entity.entity_id in seen_entity_ids:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_duplicate_entity_id",
                    severity=Severity.BLOCKED,
                    message=f"Plant diagram semantics contains duplicate entity id '{entity.entity_id}'.",
                    artifact_ref="diagram_semantics",
                )
            )
        seen_entity_ids.add(entity.entity_id)
        if entity.kind == DiagramEntityKind.UNIT and not entity.unit_id:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_unit_missing_unit_id",
                    severity=Severity.BLOCKED,
                    message=f"Unit entity '{entity.entity_id}' is missing a unit_id.",
                    artifact_ref="diagram_semantics",
                )
            )
        if entity.kind == DiagramEntityKind.CONTROL_LOOP and entity.diagram_level != DiagramLevel.CONTROL:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_control_loop_wrong_level",
                    severity=Severity.BLOCKED,
                    message=f"Control loop entity '{entity.entity_id}' must belong to the control diagram level.",
                    artifact_ref="diagram_semantics",
                )
            )
        if entity.kind in {DiagramEntityKind.INSTRUMENT, DiagramEntityKind.VALVE} and entity.diagram_level == DiagramLevel.PFD:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_pid_content_in_pfd",
                    severity=Severity.BLOCKED,
                    message=f"{entity.kind.value.replace('_', ' ').title()} entity '{entity.entity_id}' is assigned to the PFD level.",
                    artifact_ref="diagram_semantics",
                )
            )
        if entity.diagram_level == DiagramLevel.PID_LITE:
            if entity.kind in {DiagramEntityKind.INSTRUMENT, DiagramEntityKind.VALVE} and not entity.attached_to_entity_id:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_pid_entity_missing_attachment",
                        severity=Severity.BLOCKED,
                        message=(
                            f"P&ID-lite {entity.kind.value} entity '{entity.entity_id}' must declare an attached_to_entity_id."
                        ),
                        artifact_ref="diagram_semantics",
                    )
                )
            if entity.attached_to_entity_id and entity.attached_to_entity_id not in entity_ids:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_pid_attachment_missing_entity",
                        severity=Severity.BLOCKED,
                        message=(
                            f"P&ID-lite entity '{entity.entity_id}' attaches to unknown entity '{entity.attached_to_entity_id}'."
                        ),
                        artifact_ref="diagram_semantics",
                    )
                )
            if entity.kind == DiagramEntityKind.INSTRUMENT and not entity.pid_function:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_pid_instrument_missing_function",
                        severity=Severity.BLOCKED,
                        message=f"P&ID-lite instrument entity '{entity.entity_id}' must declare a pid_function.",
                        artifact_ref="diagram_semantics",
                    )
                )
            if entity.kind == DiagramEntityKind.VALVE and not entity.pid_function:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_pid_valve_missing_function",
                        severity=Severity.BLOCKED,
                        message=f"P&ID-lite valve entity '{entity.entity_id}' must declare a pid_function.",
                        artifact_ref="diagram_semantics",
                    )
                )
            if entity.kind == DiagramEntityKind.INSTRUMENT and entity.symbol_key == "pid_controller" and not entity.pid_loop_id:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_pid_controller_missing_loop_id",
                        severity=Severity.BLOCKED,
                        message=f"P&ID-lite controller entity '{entity.entity_id}' must declare a pid_loop_id.",
                        artifact_ref="diagram_semantics",
                    )
                )

    seen_connection_ids: set[str] = set()
    for connection in artifact.connections:
        if connection.connection_id in seen_connection_ids:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_duplicate_connection_id",
                    severity=Severity.BLOCKED,
                    message=f"Plant diagram semantics contains duplicate connection id '{connection.connection_id}'.",
                    artifact_ref="diagram_semantics",
                )
            )
        seen_connection_ids.add(connection.connection_id)
        if connection.source_entity_id not in entity_ids or connection.target_entity_id not in entity_ids:
            missing_refs = [
                ref
                for ref in (connection.source_entity_id, connection.target_entity_id)
                if ref not in entity_ids
            ]
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_connection_missing_entity",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Connection '{connection.connection_id}' references unknown entities: {', '.join(missing_refs)}."
                    ),
                    artifact_ref="diagram_semantics",
                )
            )
        if connection.role == DiagramEdgeRole.CONTROL_SIGNAL and connection.diagram_level not in {
            DiagramLevel.CONTROL,
            DiagramLevel.PID_LITE,
        }:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_control_signal_wrong_level",
                    severity=Severity.BLOCKED,
                    message=f"Control-signal connection '{connection.connection_id}' must belong to the control level.",
                    artifact_ref="diagram_semantics",
                )
            )
        if connection.role in {DiagramEdgeRole.PROCESS, DiagramEdgeRole.PRODUCT, DiagramEdgeRole.RECYCLE} and connection.diagram_level == DiagramLevel.CONTROL:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_process_edge_in_control",
                    severity=Severity.BLOCKED,
                    message=f"Process connection '{connection.connection_id}' is illegally assigned to the control level.",
                    artifact_ref="diagram_semantics",
                )
            )
        if connection.diagram_level == DiagramLevel.PID_LITE:
            source = entity_map.get(connection.source_entity_id)
            target = entity_map.get(connection.target_entity_id)
            if source is not None and target is not None:
                if connection.role in {DiagramEdgeRole.PROCESS, DiagramEdgeRole.PRODUCT, DiagramEdgeRole.UTILITY} and (
                    source.kind == DiagramEntityKind.INSTRUMENT or target.kind == DiagramEntityKind.INSTRUMENT
                ):
                    issues.append(
                        ValidationIssue(
                            code="diagram_semantics_pid_material_edge_to_instrument",
                            severity=Severity.BLOCKED,
                            message=(
                                f"P&ID-lite connection '{connection.connection_id}' uses a material or utility role directly to an instrument."
                            ),
                            artifact_ref="diagram_semantics",
                        )
                    )
                if connection.role == DiagramEdgeRole.CONTROL_SIGNAL and (
                    source.kind not in {DiagramEntityKind.INSTRUMENT, DiagramEntityKind.VALVE}
                    or target.kind not in {DiagramEntityKind.INSTRUMENT, DiagramEntityKind.VALVE, DiagramEntityKind.UNIT}
                ):
                    issues.append(
                        ValidationIssue(
                            code="diagram_semantics_pid_invalid_control_signal_endpoints",
                            severity=Severity.BLOCKED,
                            message=(
                                f"P&ID-lite control-signal connection '{connection.connection_id}' has invalid endpoints."
                            ),
                            artifact_ref="diagram_semantics",
                        )
                    )
            if connection.role in {DiagramEdgeRole.PROCESS, DiagramEdgeRole.PRODUCT, DiagramEdgeRole.UTILITY} and not connection.line_class:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_pid_line_missing_class",
                        severity=Severity.BLOCKED,
                        message=(
                            f"P&ID-lite line connection '{connection.connection_id}' must declare a line_class."
                        ),
                        artifact_ref="diagram_semantics",
                    )
                )

    if not artifact.entities:
        issues.append(
            ValidationIssue(
                code="diagram_semantics_empty",
                severity=Severity.BLOCKED,
                message="Plant diagram semantics artifact has no entities.",
                artifact_ref="diagram_semantics",
            )
        )
    return issues


def _infer_diagram_unit_family(entity: PlantDiagramEntity) -> str:
    template_family = entity.metadata.get("template_family", "").strip().lower()
    if template_family:
        if template_family == "heat_exchanger":
            return "heat exchanger"
        return template_family
    text = f"{entity.metadata.get('unit_type', '')} {entity.label}".lower()
    if any(token in text for token in {"column", "distillation"}):
        return "column"
    if any(token in text for token in {"reactor", "cstr", "pfr"}):
        return "reactor"
    if any(token in text for token in {"separator", "flash", "drum"}):
        return "separator"
    if any(token in text for token in {"exchanger", "heater", "cooler", "condenser", "reboiler"}):
        return "heat exchanger"
    if any(token in text for token in {"tank", "storage"}):
        return "tank"
    if any(token in text for token in {"pump", "compressor", "blower"}):
        return "pump"
    if any(token in text for token in {"vessel"}):
        return "vessel"
    return ""


def validate_diagram_target_profile_against_domain_packs(
    target: DiagramTargetProfile,
    domain_packs: DiagramDomainPackArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_pack = next((pack for pack in domain_packs.packs if pack.pack_id == target.domain_pack_id), None)
    if selected_pack is None:
        issues.append(
            ValidationIssue(
                code="diagram_target_unknown_domain_pack",
                severity=Severity.BLOCKED,
                message=f"Diagram target profile references unknown domain pack '{target.domain_pack_id}'.",
                artifact_ref="diagram_target_profile",
            )
        )
        return issues
    if set(target.required_bfd_sections) != set(selected_pack.required_bfd_sections):
        issues.append(
            ValidationIssue(
                code="diagram_target_domain_pack_section_mismatch",
                severity=Severity.WARNING,
                message=f"Diagram target profile sections do not match the selected domain pack '{target.domain_pack_id}'.",
                artifact_ref="diagram_target_profile",
            )
        )
    if set(target.major_stream_roles) != set(selected_pack.major_stream_roles):
        issues.append(
            ValidationIssue(
                code="diagram_target_domain_pack_stream_role_mismatch",
                severity=Severity.WARNING,
                message=f"Diagram target profile stream roles do not match the selected domain pack '{target.domain_pack_id}'.",
                artifact_ref="diagram_target_profile",
            )
        )
    if set(target.allowed_pfd_symbol_keys) != set(selected_pack.allowed_pfd_symbol_keys):
        issues.append(
            ValidationIssue(
                code="diagram_target_domain_pack_symbol_policy_mismatch",
                severity=Severity.WARNING,
                message=f"Diagram target profile PFD symbol policy does not match the selected domain pack '{target.domain_pack_id}'.",
                artifact_ref="diagram_target_profile",
            )
        )
    return issues


def validate_plant_diagram_semantics_against_target_profile(
    artifact: PlantDiagramSemanticsArtifact,
    target: DiagramTargetProfile,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    pfd_unit_entities = [
        entity
        for entity in artifact.entities
        if entity.diagram_level == DiagramLevel.PFD and entity.kind == DiagramEntityKind.UNIT
    ]
    present_families = {family for family in (_infer_diagram_unit_family(entity) for entity in pfd_unit_entities) if family}
    missing_families = [family for family in target.required_pfd_unit_families if family not in present_families]
    if missing_families:
        issues.append(
            ValidationIssue(
                code="diagram_target_missing_required_pfd_family",
                severity=Severity.WARNING,
                message=(
                    f"PFD semantics for domain pack '{target.domain_pack_id}' are missing expected unit families: "
                    f"{', '.join(missing_families[:6])}."
                ),
                artifact_ref="diagram_semantics",
            )
        )
    if target.preferred_template_families:
        unexpected = [
            family
            for family in present_families
            if family not in set(target.required_pfd_unit_families) and family not in set(target.preferred_template_families)
        ]
        if unexpected:
            issues.append(
                ValidationIssue(
                    code="diagram_target_unexpected_pfd_family_for_domain_pack",
                    severity=Severity.WARNING,
                    message=(
                        f"PFD semantics include unit families outside the expected domain-pack envelope "
                        f"'{target.domain_pack_id}': {', '.join(sorted(unexpected)[:6])}."
                    ),
                    artifact_ref="diagram_semantics",
                )
            )
    return issues


def validate_diagram_symbol_library(library: DiagramSymbolLibraryArtifact) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen_symbol_keys: set[str] = set()
    for symbol in library.symbols:
        if symbol.symbol_key in seen_symbol_keys:
            issues.append(
                ValidationIssue(
                    code="diagram_symbol_library_duplicate_symbol_key",
                    severity=Severity.BLOCKED,
                    message=f"Diagram symbol library contains duplicate symbol key '{symbol.symbol_key}'.",
                    artifact_ref="diagram_symbol_library",
                )
            )
        seen_symbol_keys.add(symbol.symbol_key)
        if symbol.width_px <= 0 or symbol.height_px <= 0:
            issues.append(
                ValidationIssue(
                    code="diagram_symbol_library_invalid_symbol_size",
                    severity=Severity.BLOCKED,
                    message=f"Symbol '{symbol.symbol_key}' has invalid dimensions.",
                    artifact_ref="diagram_symbol_library",
                )
            )
        if symbol.diagram_level == DiagramLevel.PID_LITE and symbol.entity_kind in {
            DiagramEntityKind.INSTRUMENT,
            DiagramEntityKind.VALVE,
        } and not symbol.pid_family:
            issues.append(
                ValidationIssue(
                    code="diagram_symbol_library_pid_symbol_missing_family",
                    severity=Severity.BLOCKED,
                    message=f"P&ID-lite symbol '{symbol.symbol_key}' must declare a pid_family.",
                    artifact_ref="diagram_symbol_library",
                )
            )

    level_policy_map = {policy.diagram_level: policy for policy in library.level_policies}
    if len(level_policy_map) != len(library.level_policies):
        issues.append(
            ValidationIssue(
                code="diagram_symbol_library_duplicate_level_policy",
                severity=Severity.BLOCKED,
                message="Diagram symbol library contains duplicate level policies.",
                artifact_ref="diagram_symbol_library",
            )
        )

    symbol_map = {symbol.symbol_key: symbol for symbol in library.symbols}
    edge_style_pairs: set[tuple[DiagramLevel, DiagramEdgeRole]] = set()
    for edge_style in library.edge_styles:
        pair = (edge_style.diagram_level, edge_style.role)
        if pair in edge_style_pairs:
            issues.append(
                ValidationIssue(
                    code="diagram_symbol_library_duplicate_edge_style",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Diagram symbol library contains duplicate edge style for level '{edge_style.diagram_level.value}' "
                        f"and role '{edge_style.role.value}'."
                    ),
                    artifact_ref="diagram_symbol_library",
                )
            )
        edge_style_pairs.add(pair)

    required_levels = {DiagramLevel.BFD, DiagramLevel.PFD, DiagramLevel.CONTROL, DiagramLevel.PID_LITE}
    missing_levels = sorted(level.value for level in required_levels - set(level_policy_map))
    if missing_levels:
        issues.append(
            ValidationIssue(
                code="diagram_symbol_library_missing_level_policy",
                severity=Severity.BLOCKED,
                message=f"Diagram symbol library is missing level policies for: {', '.join(missing_levels)}.",
                artifact_ref="diagram_symbol_library",
            )
        )

    for policy in library.level_policies:
        for symbol_key in policy.allowed_symbol_keys:
            symbol = symbol_map.get(symbol_key)
            if symbol is None:
                issues.append(
                    ValidationIssue(
                        code="diagram_symbol_library_unknown_allowed_symbol",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Level policy '{policy.diagram_level.value}' references unknown symbol key '{symbol_key}'."
                        ),
                        artifact_ref="diagram_symbol_library",
                    )
                )
                continue
            if symbol.diagram_level != policy.diagram_level:
                issues.append(
                    ValidationIssue(
                        code="diagram_symbol_library_symbol_level_mismatch",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Level policy '{policy.diagram_level.value}' allows symbol '{symbol_key}' "
                            f"from level '{symbol.diagram_level.value}'."
                        ),
                        artifact_ref="diagram_symbol_library",
                    )
                )
        for role in policy.allowed_edge_roles:
            if (policy.diagram_level, role) not in edge_style_pairs:
                issues.append(
                    ValidationIssue(
                        code="diagram_symbol_library_missing_edge_style",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Level policy '{policy.diagram_level.value}' allows edge role '{role.value}' "
                            "without a matching edge-style rule."
                        ),
                        artifact_ref="diagram_symbol_library",
                    )
                )
    return issues


def validate_diagram_semantics_against_symbol_library(
    artifact: PlantDiagramSemanticsArtifact,
    library: DiagramSymbolLibraryArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    symbol_map = {symbol.symbol_key: symbol for symbol in library.symbols}
    level_policy_map = {policy.diagram_level: policy for policy in library.level_policies}
    edge_style_pairs = {(edge_style.diagram_level, edge_style.role) for edge_style in library.edge_styles}

    for entity in artifact.entities:
        policy = level_policy_map.get(entity.diagram_level)
        if policy is None:
            continue
        if entity.kind in set(policy.forbidden_entity_kinds):
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_forbidden_entity_kind_by_policy",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Entity '{entity.entity_id}' of kind '{entity.kind.value}' is forbidden by the "
                        f"'{entity.diagram_level.value}' style policy."
                    ),
                    artifact_ref="diagram_semantics",
                )
            )
        if entity.symbol_key:
            symbol = symbol_map.get(entity.symbol_key)
            if symbol is None:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_unknown_symbol_key",
                        severity=Severity.BLOCKED,
                        message=f"Entity '{entity.entity_id}' references unknown symbol key '{entity.symbol_key}'.",
                        artifact_ref="diagram_semantics",
                    )
                )
                continue
            if symbol.diagram_level != entity.diagram_level:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_symbol_level_mismatch",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Entity '{entity.entity_id}' uses symbol '{entity.symbol_key}' from level "
                            f"'{symbol.diagram_level.value}' but belongs to '{entity.diagram_level.value}'."
                        ),
                        artifact_ref="diagram_semantics",
                    )
                )
            if symbol.entity_kind != entity.kind:
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_symbol_kind_mismatch",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Entity '{entity.entity_id}' of kind '{entity.kind.value}' uses symbol '{entity.symbol_key}' "
                            f"for kind '{symbol.entity_kind.value}'."
                        ),
                        artifact_ref="diagram_semantics",
                    )
                )
            if entity.symbol_key not in set(policy.allowed_symbol_keys):
                issues.append(
                    ValidationIssue(
                        code="diagram_semantics_symbol_not_allowed_by_policy",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Entity '{entity.entity_id}' uses symbol '{entity.symbol_key}' which is not allowed "
                            f"by the '{entity.diagram_level.value}' style policy."
                        ),
                        artifact_ref="diagram_semantics",
                    )
                )

    for connection in artifact.connections:
        policy = level_policy_map.get(connection.diagram_level)
        if policy is None:
            continue
        if connection.role not in set(policy.allowed_edge_roles):
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_edge_role_not_allowed_by_policy",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Connection '{connection.connection_id}' uses edge role '{connection.role.value}' which is not allowed "
                        f"by the '{connection.diagram_level.value}' style policy."
                    ),
                    artifact_ref="diagram_semantics",
                )
            )
        if (connection.diagram_level, connection.role) not in edge_style_pairs:
            issues.append(
                ValidationIssue(
                    code="diagram_semantics_missing_edge_style",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Connection '{connection.connection_id}' uses edge role '{connection.role.value}' without a matching "
                        f"edge style for level '{connection.diagram_level.value}'."
                    ),
                    artifact_ref="diagram_semantics",
                )
            )
    return issues


def validate_diagram_module_artifact(
    artifact: DiagramModuleArtifact,
    semantics: PlantDiagramSemanticsArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    entity_map = {entity.entity_id: entity for entity in semantics.entities}
    connection_map = {connection.connection_id: connection for connection in semantics.connections}
    seen_module_ids: set[str] = set()

    for module in artifact.modules:
        if module.module_id in seen_module_ids:
            issues.append(
                ValidationIssue(
                    code="diagram_module_duplicate_module_id",
                    severity=Severity.BLOCKED,
                    message=f"Diagram module artifact contains duplicate module id '{module.module_id}'.",
                    artifact_ref="diagram_modules",
                )
            )
        seen_module_ids.add(module.module_id)

        if module.module_kind != artifact.module_kind:
            issues.append(
                ValidationIssue(
                    code="diagram_module_kind_mismatch",
                    severity=Severity.BLOCKED,
                    message=f"Module '{module.module_id}' has kind '{module.module_kind.value}' but artifact kind is '{artifact.module_kind.value}'.",
                    artifact_ref="diagram_modules",
                )
            )

        if module.module_kind == DiagramLevel.BFD and module.symbol_policy != DiagramSymbolPolicy.BLOCK_ONLY:
            issues.append(
                ValidationIssue(
                    code="diagram_module_bfd_symbol_policy_mismatch",
                    severity=Severity.BLOCKED,
                    message=f"BFD module '{module.module_id}' must use block-only symbol policy.",
                    artifact_ref="diagram_modules",
                )
            )
        if module.module_kind == DiagramLevel.PFD and module.symbol_policy != DiagramSymbolPolicy.PROCESS_ONLY:
            issues.append(
                ValidationIssue(
                    code="diagram_module_pfd_symbol_policy_mismatch",
                    severity=Severity.BLOCKED,
                    message=f"PFD module '{module.module_id}' must use process-only symbol policy.",
                    artifact_ref="diagram_modules",
                )
            )
        if module.module_kind == DiagramLevel.CONTROL and module.symbol_policy != DiagramSymbolPolicy.CONTROL_ONLY:
            issues.append(
                ValidationIssue(
                    code="diagram_module_control_symbol_policy_mismatch",
                    severity=Severity.BLOCKED,
                    message=f"Control module '{module.module_id}' must use control-only symbol policy.",
                    artifact_ref="diagram_modules",
                )
            )
        if module.module_kind == DiagramLevel.PID_LITE and module.symbol_policy != DiagramSymbolPolicy.PID_LITE_ONLY:
            issues.append(
                ValidationIssue(
                    code="diagram_module_pid_symbol_policy_mismatch",
                    severity=Severity.BLOCKED,
                    message=f"P&ID-lite module '{module.module_id}' must use pid-lite-only symbol policy.",
                    artifact_ref="diagram_modules",
                )
            )
        if module.module_kind == DiagramLevel.PID_LITE and not module.must_be_isolated:
            issues.append(
                ValidationIssue(
                    code="diagram_module_pid_not_isolated",
                    severity=Severity.BLOCKED,
                    message=f"P&ID-lite module '{module.module_id}' must be isolated as a local unit cluster.",
                    artifact_ref="diagram_modules",
                )
            )

        module_entity_ids = set(module.entity_ids)
        module_connection_ids = set(module.connection_ids)
        unit_entity_count = 0
        for entity_id in module.entity_ids:
            entity = entity_map.get(entity_id)
            if entity is None:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_missing_entity",
                        severity=Severity.BLOCKED,
                        message=f"Module '{module.module_id}' references unknown entity '{entity_id}'.",
                        artifact_ref="diagram_modules",
                    )
                )
                continue
            if entity.diagram_level != module.module_kind:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_entity_level_mismatch",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Entity '{entity_id}' belongs to diagram level '{entity.diagram_level.value}' "
                            f"but is included in module '{module.module_id}' of kind '{module.module_kind.value}'."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
            if entity.kind in set(module.forbidden_entity_kinds):
                issues.append(
                    ValidationIssue(
                        code="diagram_module_forbidden_entity_kind",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Module '{module.module_id}' contains forbidden entity kind '{entity.kind.value}' via entity '{entity_id}'."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
            if module.module_kind == DiagramLevel.PFD and entity.kind in {
                DiagramEntityKind.INSTRUMENT,
                DiagramEntityKind.VALVE,
                DiagramEntityKind.CONTROL_LOOP,
            }:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_pfd_contains_pid_content",
                        severity=Severity.BLOCKED,
                        message=f"PFD module '{module.module_id}' illegally contains '{entity.kind.value}' entity '{entity_id}'.",
                        artifact_ref="diagram_modules",
                    )
                )
            if module.module_kind == DiagramLevel.PID_LITE and entity.kind == DiagramEntityKind.UNIT:
                unit_entity_count += 1
            if module.module_kind == DiagramLevel.PID_LITE and entity.attached_to_entity_id:
                if entity.attached_to_entity_id not in module_entity_ids:
                    issues.append(
                        ValidationIssue(
                            code="diagram_module_pid_attachment_outside_module",
                            severity=Severity.BLOCKED,
                            message=(
                                f"P&ID-lite entity '{entity_id}' in module '{module.module_id}' attaches outside the local module."
                            ),
                            artifact_ref="diagram_modules",
                        )
                    )
                elif entity.attached_to_entity_id == entity_id:
                    issues.append(
                        ValidationIssue(
                            code="diagram_module_pid_self_attachment",
                            severity=Severity.BLOCKED,
                            message=f"P&ID-lite entity '{entity_id}' in module '{module.module_id}' may not attach to itself.",
                            artifact_ref="diagram_modules",
                        )
                    )

        for connection_id in module.connection_ids:
            connection = connection_map.get(connection_id)
            if connection is None:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_missing_connection",
                        severity=Severity.BLOCKED,
                        message=f"Module '{module.module_id}' references unknown connection '{connection_id}'.",
                        artifact_ref="diagram_modules",
                    )
                )
                continue
            if connection.diagram_level != module.module_kind:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_connection_level_mismatch",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Connection '{connection_id}' belongs to diagram level '{connection.diagram_level.value}' "
                            f"but is included in module '{module.module_id}' of kind '{module.module_kind.value}'."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
            if module.allowed_edge_roles and connection.role not in set(module.allowed_edge_roles):
                issues.append(
                    ValidationIssue(
                        code="diagram_module_forbidden_edge_role",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Module '{module.module_id}' contains disallowed edge role '{connection.role.value}' "
                            f"via connection '{connection_id}'."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
            if module.module_kind == DiagramLevel.PID_LITE and connection.role in {
                DiagramEdgeRole.PROCESS,
                DiagramEdgeRole.PRODUCT,
                DiagramEdgeRole.UTILITY,
            }:
                if connection.source_entity_id not in module_entity_ids or connection.target_entity_id not in module_entity_ids:
                    issues.append(
                        ValidationIssue(
                            code="diagram_module_pid_material_connection_external",
                            severity=Severity.BLOCKED,
                            message=(
                                f"P&ID-lite material/utility connection '{connection_id}' in module '{module.module_id}' must stay inside the local cluster."
                            ),
                            artifact_ref="diagram_modules",
                        )
                    )
                if not connection.line_class:
                    issues.append(
                        ValidationIssue(
                            code="diagram_module_pid_line_missing_class",
                            severity=Severity.BLOCKED,
                            message=(
                                f"P&ID-lite connection '{connection_id}' in module '{module.module_id}' must declare a line_class."
                            ),
                            artifact_ref="diagram_modules",
                        )
                    )
            internal_refs = {connection.source_entity_id, connection.target_entity_id} & module_entity_ids
            if not internal_refs and not connection.must_route_externally:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_disconnected_connection",
                        severity=Severity.WARNING,
                        message=(
                            f"Connection '{connection_id}' in module '{module.module_id}' does not touch any module entity "
                            "and is not marked for external routing."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
        if module.module_kind == DiagramLevel.PID_LITE and unit_entity_count == 0:
            issues.append(
                ValidationIssue(
                    code="diagram_module_pid_missing_unit_anchor",
                    severity=Severity.BLOCKED,
                    message=f"P&ID-lite module '{module.module_id}' must include at least one unit anchor entity.",
                    artifact_ref="diagram_modules",
                )
            )

        declared_port_entity_ids = {port.entity_id for port in module.boundary_ports if port.entity_id}
        if not declared_port_entity_ids.issubset(module_entity_ids):
            missing_port_entities = sorted(declared_port_entity_ids - module_entity_ids)
            issues.append(
                ValidationIssue(
                    code="diagram_module_port_missing_entity",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Module '{module.module_id}' declares boundary ports for entities not in the module: "
                        f"{', '.join(missing_port_entities)}."
                    ),
                    artifact_ref="diagram_modules",
                )
            )

    if not artifact.modules:
        issues.append(
            ValidationIssue(
                code="diagram_module_empty",
                severity=Severity.BLOCKED,
                message="Diagram module artifact has no modules.",
                artifact_ref="diagram_modules",
            )
        )
    return issues


def validate_diagram_module_symbols_against_library(
    artifact: DiagramModuleArtifact,
    semantics: PlantDiagramSemanticsArtifact,
    library: DiagramSymbolLibraryArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    entity_map = {entity.entity_id: entity for entity in semantics.entities}
    connection_map = {connection.connection_id: connection for connection in semantics.connections}
    level_policy_map = {policy.diagram_level: policy for policy in library.level_policies}
    edge_style_pairs = {(edge_style.diagram_level, edge_style.role) for edge_style in library.edge_styles}

    for module in artifact.modules:
        policy = level_policy_map.get(module.module_kind)
        if policy is None:
            continue
        if module.symbol_policy != policy.symbol_policy:
            issues.append(
                ValidationIssue(
                    code="diagram_module_symbol_policy_library_mismatch",
                    severity=Severity.BLOCKED,
                    message=(
                        f"Module '{module.module_id}' uses symbol policy '{module.symbol_policy.value}' but the "
                        f"library requires '{policy.symbol_policy.value}' for level '{module.module_kind.value}'."
                    ),
                    artifact_ref="diagram_modules",
                )
            )
        for entity_id in module.entity_ids:
            entity = entity_map.get(entity_id)
            if entity is None or not entity.symbol_key:
                continue
            if entity.symbol_key not in set(policy.allowed_symbol_keys):
                issues.append(
                    ValidationIssue(
                        code="diagram_module_symbol_not_allowed_by_library",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Module '{module.module_id}' includes entity '{entity_id}' with symbol '{entity.symbol_key}' "
                            f"which is not allowed for level '{module.module_kind.value}'."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
        for connection_id in module.connection_ids:
            connection = connection_map.get(connection_id)
            if connection is None:
                continue
            if connection.role not in set(policy.allowed_edge_roles):
                issues.append(
                    ValidationIssue(
                        code="diagram_module_edge_role_not_allowed_by_library",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Module '{module.module_id}' includes connection '{connection_id}' with edge role "
                            f"'{connection.role.value}' which is not allowed for level '{module.module_kind.value}'."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
            if (module.module_kind, connection.role) not in edge_style_pairs:
                issues.append(
                    ValidationIssue(
                        code="diagram_module_missing_edge_style_in_library",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Module '{module.module_id}' includes connection '{connection_id}' with no matching "
                            f"edge style in the symbol library."
                        ),
                        artifact_ref="diagram_modules",
                    )
                )
    return issues


def validate_diagram_sheet_composition_artifact(
    artifact: DiagramSheetCompositionArtifact,
    modules: DiagramModuleArtifact,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    module_map = {module.module_id: module for module in modules.modules}

    for sheet in artifact.sheets:
        seen_placements: set[str] = set()
        placed_module_ids = {placement.module_id for placement in sheet.module_placements}
        for placement in sheet.module_placements:
            if placement.module_id in seen_placements:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_duplicate_module_placement",
                        severity=Severity.BLOCKED,
                        message=f"Sheet '{sheet.sheet_id}' places module '{placement.module_id}' more than once.",
                        artifact_ref="diagram_sheet_composition",
                    )
                )
            seen_placements.add(placement.module_id)
            module = module_map.get(placement.module_id)
            if module is None:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_unknown_module",
                        severity=Severity.BLOCKED,
                        message=f"Sheet '{sheet.sheet_id}' references unknown module '{placement.module_id}'.",
                        artifact_ref="diagram_sheet_composition",
                    )
                )
                continue
            if module.module_kind != artifact.diagram_level:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_module_level_mismatch",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Sheet '{sheet.sheet_id}' of level '{artifact.diagram_level.value}' includes module "
                            f"'{placement.module_id}' of level '{module.module_kind.value}'."
                        ),
                        artifact_ref="diagram_sheet_composition",
                    )
                )
            if placement.x < 0 or placement.y < 0 or placement.width <= 0 or placement.height <= 0:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_invalid_placement_geometry",
                        severity=Severity.BLOCKED,
                        message=f"Sheet '{sheet.sheet_id}' contains invalid geometry for module '{placement.module_id}'.",
                        artifact_ref="diagram_sheet_composition",
                    )
                )
            if placement.x + placement.width > sheet.width_px or placement.y + placement.height > sheet.height_px:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_module_out_of_bounds",
                        severity=Severity.BLOCKED,
                        message=f"Module '{placement.module_id}' exceeds the bounds of sheet '{sheet.sheet_id}'.",
                        artifact_ref="diagram_sheet_composition",
                    )
                )
        for connector in sheet.connectors:
            if connector.source_module_id not in placed_module_ids or connector.target_module_id not in placed_module_ids:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_connector_missing_module",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Connector '{connector.connector_id}' references modules that are not both placed on sheet '{sheet.sheet_id}'."
                        ),
                        artifact_ref="diagram_sheet_composition",
                    )
                )
                continue
            source_module = module_map.get(connector.source_module_id)
            target_module = module_map.get(connector.target_module_id)
            if source_module is None or target_module is None:
                continue
            source_port_ids = {port.port_id for port in source_module.boundary_ports}
            target_port_ids = {port.port_id for port in target_module.boundary_ports}
            if connector.source_port_id not in source_port_ids or connector.target_port_id not in target_port_ids:
                issues.append(
                    ValidationIssue(
                        code="diagram_sheet_connector_missing_port",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Connector '{connector.connector_id}' uses undeclared boundary ports between "
                            f"'{connector.source_module_id}' and '{connector.target_module_id}'."
                        ),
                        artifact_ref="diagram_sheet_composition",
                    )
                )
        if not sheet.module_placements:
            issues.append(
                ValidationIssue(
                    code="diagram_sheet_empty",
                    severity=Severity.BLOCKED,
                    message=f"Sheet '{sheet.sheet_id}' contains no module placements.",
                    artifact_ref="diagram_sheet_composition",
                )
            )
    if not artifact.sheets:
        issues.append(
            ValidationIssue(
                code="diagram_sheet_composition_empty",
                severity=Severity.BLOCKED,
                message="Diagram sheet composition artifact has no sheets.",
                artifact_ref="diagram_sheet_composition",
            )
        )
    return issues


def validate_diagram_drafting_sheets(
    sheets: list[DiagramSheet],
    *,
    nodes: list[DiagramNode] | None = None,
    artifact_ref: str = "diagram_sheets",
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    node_lookup = {node.node_id: node for node in (nodes or [])}
    drawing_numbers: dict[str, str] = {}
    sheet_numbers: dict[str, str] = {}

    for sheet in sheets:
        required_fields = {
            "drawing_number": sheet.drawing_number,
            "sheet_number": sheet.sheet_number,
            "revision": sheet.revision,
            "revision_date": sheet.revision_date,
            "issue_status": sheet.issue_status,
            "prepared_by": sheet.prepared_by,
        }
        missing_fields = [field for field, value in required_fields.items() if not str(value).strip()]
        if missing_fields:
            issues.append(
                ValidationIssue(
                    code="diagram_drafting_metadata_missing",
                    severity=Severity.WARNING,
                    message=f"Sheet '{sheet.sheet_id}' is missing drafting metadata fields: {', '.join(missing_fields)}.",
                    artifact_ref=artifact_ref,
                )
            )

        normalized_drawing = sheet.drawing_number.strip().upper()
        if normalized_drawing:
            first_sheet_id = drawing_numbers.get(normalized_drawing)
            if first_sheet_id is not None:
                issues.append(
                    ValidationIssue(
                        code="diagram_duplicate_drawing_number",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Sheet '{sheet.sheet_id}' reuses drawing number '{sheet.drawing_number}' "
                            f"already assigned to sheet '{first_sheet_id}'."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )
            drawing_numbers.setdefault(normalized_drawing, sheet.sheet_id)

        normalized_sheet_number = sheet.sheet_number.strip().upper()
        if normalized_sheet_number:
            first_sheet_id = sheet_numbers.get(normalized_sheet_number)
            if first_sheet_id is not None:
                issues.append(
                    ValidationIssue(
                        code="diagram_duplicate_sheet_number",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Sheet '{sheet.sheet_id}' reuses sheet number '{sheet.sheet_number}' "
                            f"already assigned to sheet '{first_sheet_id}'."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )
            sheet_numbers.setdefault(normalized_sheet_number, sheet.sheet_id)

        if sheet.svg.strip() and "DRAFTING TITLE BLOCK" not in sheet.svg:
            issues.append(
                ValidationIssue(
                    code="diagram_title_block_missing",
                    severity=Severity.BLOCKED,
                    message=f"Rendered SVG for sheet '{sheet.sheet_id}' is missing the drafting title block.",
                    artifact_ref=artifact_ref,
                )
            )

        title_block_rect = _drafting_title_block_rect(sheet)
        for node_id in sheet.node_ids:
            node = node_lookup.get(node_id)
            if node is None:
                continue
            if _rectangles_overlap(title_block_rect, (node.x, node.y, node.width, node.height), padding=8.0):
                issues.append(
                    ValidationIssue(
                        code="diagram_title_block_overlap",
                        severity=Severity.BLOCKED,
                        message=(
                            f"Sheet '{sheet.sheet_id}' places node '{node.node_id}' inside the reserved drafting title-block area."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )

    if not sheets:
        issues.append(
            ValidationIssue(
                code="diagram_drafting_sheets_empty",
                severity=Severity.BLOCKED,
                message="No diagram sheets were provided for drafting validation.",
                artifact_ref=artifact_ref,
            )
        )
    return issues


def validate_bac_pfd_process_purity(
    nodes: list[DiagramNode],
    target: DiagramTargetProfile,
    *,
    artifact_ref: str = "process_flow_diagram",
) -> list[ValidationIssue]:
    if not _is_bac_target(target):
        return []
    issues: list[ValidationIssue] = []
    control_pattern = re.compile(r"\b(?:AIC|FIC|LIC|PIC|TIC|FC|LC|PC|TC)-?\d+\b", re.IGNORECASE)
    utility_pattern = re.compile(r"\b\d+(?:\.\d+)?\s*kW\s+(?:heat|cool)\b", re.IGNORECASE)

    for node in nodes:
        if node.node_family in {"instrument", "controller", "valve", "relief_valve"}:
            issues.append(
                ValidationIssue(
                    code="bac_pfd_contains_pid_symbol_family",
                    severity=Severity.BLOCKED,
                    message=(
                        f"BAC PFD node '{node.node_id}' uses local instrumentation/valve family '{node.node_family}', "
                        "which belongs in P&ID-lite or control diagrams."
                    ),
                    artifact_ref=artifact_ref,
                )
            )
        for label in node.labels:
            text = label.text.strip()
            if not text:
                continue
            if label.kind == "utility" and control_pattern.search(text):
                issues.append(
                    ValidationIssue(
                        code="bac_pfd_contains_control_annotation",
                        severity=Severity.BLOCKED,
                        message=(
                            f"BAC PFD node '{node.node_id}' exposes control-loop annotation '{text}' in visible labels."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )
            if label.kind == "utility" and utility_pattern.search(text):
                issues.append(
                    ValidationIssue(
                        code="bac_pfd_contains_utility_duty_annotation",
                        severity=Severity.BLOCKED,
                        message=(
                            f"BAC PFD node '{node.node_id}' exposes utility-duty annotation '{text}' in visible labels."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )
            if label.kind != "primary" and control_pattern.search(text):
                issues.append(
                    ValidationIssue(
                        code="bac_pfd_contains_control_annotation",
                        severity=Severity.BLOCKED,
                        message=(
                            f"BAC PFD node '{node.node_id}' includes control-style text '{text}' outside the control/P&ID views."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )
            if label.kind == "utility" and "loop" in text.lower():
                issues.append(
                    ValidationIssue(
                        code="bac_pfd_contains_control_annotation",
                        severity=Severity.BLOCKED,
                        message=(
                            f"BAC PFD node '{node.node_id}' includes loop annotation '{text}' in visible labels."
                        ),
                        artifact_ref=artifact_ref,
                    )
                )
    return issues


def validate_bac_bfd_structure(
    artifact: PlantDiagramSemanticsArtifact,
    target: DiagramTargetProfile,
    *,
    artifact_ref: str = "block_flow_diagram",
) -> list[ValidationIssue]:
    if not _is_bac_target(target):
        return []
    bfd_sections = [
        entity.section_id
        for entity in artifact.entities
        if entity.diagram_level == DiagramLevel.BFD and entity.kind == DiagramEntityKind.SECTION and entity.section_id
    ]
    expected_order = _bac_bfd_section_order()
    issues: list[ValidationIssue] = []
    if artifact.section_order[: len(expected_order)] != expected_order:
        issues.append(
            ValidationIssue(
                code="bac_bfd_section_order_mismatch",
                severity=Severity.BLOCKED,
                message="BAC BFD section order does not match the locked canonical BAC section spine.",
                artifact_ref=artifact_ref,
            )
        )
    missing_sections = [section for section in expected_order if section not in set(bfd_sections)]
    if missing_sections:
        issues.append(
            ValidationIssue(
                code="bac_bfd_missing_required_sections",
                severity=Severity.BLOCKED,
                message=f"BAC BFD is missing required sections: {', '.join(missing_sections)}.",
                artifact_ref=artifact_ref,
            )
        )
    expected_labels = _bac_bfd_display_label_map()
    for entity in artifact.entities:
        if entity.diagram_level != DiagramLevel.BFD or entity.kind != DiagramEntityKind.SECTION:
            continue
        expected_label = expected_labels.get(entity.section_id)
        if expected_label and entity.label != expected_label:
            issues.append(
                ValidationIssue(
                    code="bac_bfd_section_label_mismatch",
                    severity=Severity.BLOCKED,
                    message=(
                        f"BAC BFD section '{entity.section_id}' uses label '{entity.label}' instead of '{expected_label}'."
                    ),
                    artifact_ref=artifact_ref,
                )
            )
    return issues


def validate_bac_pid_cluster_coverage(
    artifact: PlantDiagramSemanticsArtifact,
    flowsheet_graph: FlowsheetGraph,
    target: DiagramTargetProfile,
    *,
    artifact_ref: str = "pid_lite_semantics",
) -> list[ValidationIssue]:
    if not _is_bac_target(target):
        return []
    unit_entities = {
        entity.unit_id: entity
        for entity in artifact.entities
        if entity.diagram_level == DiagramLevel.PID_LITE and entity.kind == DiagramEntityKind.UNIT and entity.unit_id
    }
    required_unit_ids = _bac_pid_required_unit_ids(flowsheet_graph)
    issues: list[ValidationIssue] = []
    missing_units = [unit_id for unit_id in required_unit_ids if unit_id not in unit_entities]
    if missing_units:
        issues.append(
            ValidationIssue(
                code="bac_pid_missing_required_clusters",
                severity=Severity.BLOCKED,
                message=f"BAC P&ID-lite semantics are missing required unit clusters: {', '.join(missing_units)}.",
                artifact_ref=artifact_ref,
            )
        )
    required_relief_units = {
        unit_id
        for unit_id in required_unit_ids
        if _bac_pid_requires_relief(next((node for node in flowsheet_graph.nodes if node.node_id == unit_id), None))
    }
    relief_anchors = {
        entity.attached_to_entity_id
        for entity in artifact.entities
        if entity.diagram_level == DiagramLevel.PID_LITE and entity.symbol_key == "pid_relief_valve" and entity.attached_to_entity_id
    }
    missing_relief_units = sorted(required_relief_units - relief_anchors)
    if missing_relief_units:
        issues.append(
            ValidationIssue(
                code="bac_pid_missing_relief_coverage",
                severity=Severity.WARNING,
                message=f"BAC P&ID-lite semantics are missing relief/safeguard coverage for: {', '.join(missing_relief_units)}.",
                artifact_ref=artifact_ref,
            )
        )
    return issues


def validate_bac_diagram_benchmark_artifact(
    artifact: BACDiagramBenchmarkArtifact,
    target: DiagramTargetProfile,
    *,
    artifact_ref: str = "bac_diagram_benchmark",
) -> list[ValidationIssue]:
    if not _is_bac_target(target):
        return []
    issues: list[ValidationIssue] = []
    required_rows = {"bfd", "pfd", "pid", "drawio"}
    row_kinds = {row.diagram_kind for row in artifact.rows}
    missing_rows = sorted(required_rows - row_kinds)
    if missing_rows:
        issues.append(
            ValidationIssue(
                code="bac_diagram_benchmark_missing_rows",
                severity=Severity.BLOCKED,
                message=f"BAC diagram benchmark is missing required rows: {', '.join(missing_rows)}.",
                artifact_ref=artifact_ref,
            )
        )
    if artifact.overall_status == "blocked":
        issues.append(
            ValidationIssue(
                code="bac_diagram_benchmark_blocked",
                severity=Severity.BLOCKED,
                message="BAC diagram benchmark is blocked and the drawing package is not benchmark-ready.",
                artifact_ref=artifact_ref,
            )
        )
    elif artifact.overall_status == "conditional":
        issues.append(
            ValidationIssue(
                code="bac_diagram_benchmark_conditional",
                severity=Severity.WARNING,
                message="BAC diagram benchmark is conditional and still has benchmark warnings.",
                artifact_ref=artifact_ref,
            )
        )
    for row in artifact.rows:
        if row.status == "fail":
            issues.append(
                ValidationIssue(
                    code=f"bac_diagram_benchmark_{row.diagram_kind}_failed",
                    severity=Severity.BLOCKED,
                    message=row.summary or f"BAC {row.diagram_kind.upper()} benchmark row failed.",
                    artifact_ref=artifact_ref,
                )
            )
        elif row.status == "warning":
            issues.append(
                ValidationIssue(
                    code=f"bac_diagram_benchmark_{row.diagram_kind}_warning",
                    severity=Severity.WARNING,
                    message=row.summary or f"BAC {row.diagram_kind.upper()} benchmark row is conditional.",
                    artifact_ref=artifact_ref,
                )
            )
    return issues


def validate_bac_drawing_package_artifact(
    artifact: BACDrawingPackageArtifact,
    target: DiagramTargetProfile,
    *,
    artifact_ref: str = "bac_drawing_package",
) -> list[ValidationIssue]:
    if not _is_bac_target(target):
        return []
    issues: list[ValidationIssue] = []
    required_kinds = {"bfd", "pfd", "pid"}
    row_kinds = {row.diagram_kind for row in artifact.register_rows}
    missing_kinds = sorted(required_kinds - row_kinds)
    if missing_kinds:
        issues.append(
            ValidationIssue(
                code="bac_drawing_package_missing_register_kinds",
                severity=Severity.BLOCKED,
                message=f"BAC drawing package is missing register coverage for: {', '.join(missing_kinds)}.",
                artifact_ref=artifact_ref,
            )
        )
    if artifact.review_workflow_status in {"approved", "as_built"} and not artifact.approver:
        issues.append(
            ValidationIssue(
                code="bac_drawing_package_missing_approver",
                severity=Severity.BLOCKED,
                message="BAC drawing package is marked approved/as-built without an approver.",
                artifact_ref=artifact_ref,
            )
        )
    if artifact.review_workflow_status == "as_built":
        missing_dates = [row.sheet_id for row in artifact.register_rows if row.issue_status.lower() == "as built" and not row.approved_date]
        if missing_dates:
            issues.append(
                ValidationIssue(
                    code="bac_drawing_package_missing_as_built_dates",
                    severity=Severity.BLOCKED,
                    message=f"BAC drawing package has as-built sheets without approval dates: {', '.join(missing_dates)}.",
                    artifact_ref=artifact_ref,
                )
            )
    for row in artifact.register_rows:
        lowered_status = row.issue_status.lower()
        if lowered_status in {"approved", "as built"} and not row.approved_by:
            issues.append(
                ValidationIssue(
                    code="bac_drawing_package_sheet_missing_approver",
                    severity=Severity.BLOCKED,
                    message=f"BAC drawing sheet '{row.sheet_id}' is {row.issue_status} without an approver.",
                    artifact_ref=artifact_ref,
                )
            )
        if lowered_status == "for review" and not (row.checked_by or row.reviewed_by):
            issues.append(
                ValidationIssue(
                    code="bac_drawing_package_sheet_missing_review_chain",
                    severity=Severity.WARNING,
                    message=f"BAC drawing sheet '{row.sheet_id}' is for review without checker/reviewer assignment.",
                    artifact_ref=artifact_ref,
                )
            )
    return issues


def validate_bac_rendering_audit_artifact(
    artifact: BACRenderingAuditArtifact,
    target: DiagramTargetProfile,
    *,
    artifact_ref: str = "bac_rendering_audit",
) -> list[ValidationIssue]:
    if not _is_bac_target(target):
        return []
    issues: list[ValidationIssue] = []
    required_rows = {"bfd", "pfd", "pid"}
    row_kinds = {row.diagram_kind for row in artifact.rows}
    missing_rows = sorted(required_rows - row_kinds)
    if missing_rows:
        issues.append(
            ValidationIssue(
                code="bac_rendering_audit_missing_rows",
                severity=Severity.BLOCKED,
                message=f"BAC rendering audit is missing rows for: {', '.join(missing_rows)}.",
                artifact_ref=artifact_ref,
            )
        )
    if artifact.overall_status == "blocked":
        issues.append(
            ValidationIssue(
                code="bac_rendering_audit_blocked",
                severity=Severity.BLOCKED,
                message="BAC rendering audit found blocked rendering issues in the current BAC diagrams.",
                artifact_ref=artifact_ref,
            )
        )
    elif artifact.overall_status == "conditional":
        issues.append(
            ValidationIssue(
                code="bac_rendering_audit_conditional",
                severity=Severity.WARNING,
                message="BAC rendering audit found rendering warnings that should be reviewed before wider integration.",
                artifact_ref=artifact_ref,
            )
        )
    for row in artifact.rows:
        if row.status == "fail":
            issues.append(
                ValidationIssue(
                    code=f"bac_rendering_audit_{row.diagram_kind}_failed",
                    severity=Severity.BLOCKED,
                    message=row.summary or f"BAC {row.diagram_kind.upper()} rendering audit failed.",
                    artifact_ref=artifact_ref,
                )
            )
        elif row.status == "warning":
            issues.append(
                ValidationIssue(
                    code=f"bac_rendering_audit_{row.diagram_kind}_warning",
                    severity=Severity.WARNING,
                    message=row.summary or f"BAC {row.diagram_kind.upper()} rendering audit has warnings.",
                    artifact_ref=artifact_ref,
                )
            )
    return issues


def _drafting_title_block_rect(sheet: DiagramSheet) -> tuple[float, float, float, float]:
    width = 430.0
    height = 86.0
    return (
        max(8.0, sheet.width_px - width - 16.0),
        max(8.0, sheet.height_px - height - 14.0),
        width,
        height,
    )


def _rectangles_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    *,
    padding: float = 0.0,
) -> bool:
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    return not (
        lx + lw + padding <= rx
        or rx + rw + padding <= lx
        or ly + lh + padding <= ry
        or ry + rh + padding <= ly
    )


def _is_bac_target(target: DiagramTargetProfile) -> bool:
    lowered = target.target_product.lower()
    return "benzalkonium" in lowered or lowered.strip() == "bac"


def _bac_bfd_section_order() -> list[str]:
    return [
        "feed preparation",
        "reaction",
        "cleanup",
        "concentration",
        "purification",
        "storage",
        "waste handling",
    ]


def _bac_bfd_display_label_map() -> dict[str, str]:
    return {
        "feed preparation": "Feed Preparation",
        "reaction": "Quaternization Reaction",
        "cleanup": "Primary Cleanup",
        "concentration": "Concentration",
        "purification": "Purification",
        "storage": "Product Storage",
        "waste handling": "Waste Handling",
    }


def _bac_pid_required_unit_ids(flowsheet_graph: FlowsheetGraph) -> list[str]:
    priority_sections = ["reaction", "cleanup", "purification", "storage", "waste_treatment"]
    preferred: list[str] = []
    for section_id in priority_sections:
        for node in flowsheet_graph.nodes:
            if node.section_id == section_id and node.node_id not in preferred:
                preferred.append(node.node_id)
    for node in flowsheet_graph.nodes:
        lowered = f"{node.label} {node.unit_type} {node.section_id}".lower()
        if (
            any(token in lowered for token in {"reactor", "quaternization", "column", "purification", "storage", "tank", "waste", "etp"})
            and node.node_id not in preferred
        ):
            preferred.append(node.node_id)
    return preferred


def _bac_pid_requires_relief(node) -> bool:
    if node is None:
        return False
    lowered = f"{node.label} {node.unit_type} {node.section_id}".lower()
    return any(token in lowered for token in {"reaction", "reactor", "purification", "column", "storage", "tank"})


def validate_hazop_node_register(register: HazopNodeRegister) -> list[ValidationIssue]:
    if not register.nodes:
        return [
            ValidationIssue(
                code="hazop_register_empty",
                severity=Severity.BLOCKED,
                message="HAZOP node register is empty.",
                artifact_ref="hazop_node_register",
            )
        ]
    issues: list[ValidationIssue] = []
    missing_deviation = [node.node_id for node in register.nodes if not node.deviation]
    missing_design_intent = [node.node_id for node in register.nodes if not node.design_intent]
    missing_safeguards = [node.node_id for node in register.nodes if not node.safeguards]
    missing_tracking = [node.node_id for node in register.nodes if not node.recommendation_priority or not node.recommendation_status]
    if missing_deviation:
        issues.append(
            ValidationIssue(
                code="hazop_missing_deviation_basis",
                severity=Severity.WARNING,
                message=f"HAZOP nodes are missing explicit deviation wording: {', '.join(missing_deviation[:5])}.",
                artifact_ref="hazop_node_register",
            )
        )
    if missing_design_intent:
        issues.append(
            ValidationIssue(
                code="hazop_missing_design_intent",
                severity=Severity.WARNING,
                message=f"HAZOP nodes are missing design intent basis: {', '.join(missing_design_intent[:5])}.",
                artifact_ref="hazop_node_register",
            )
        )
    if missing_safeguards:
        issues.append(
            ValidationIssue(
                code="hazop_missing_safeguards",
                severity=Severity.BLOCKED,
                message=f"HAZOP nodes are missing safeguards: {', '.join(missing_safeguards[:5])}.",
                artifact_ref="hazop_node_register",
            )
        )
    if missing_tracking:
        issues.append(
            ValidationIssue(
                code="hazop_missing_recommendation_tracking",
                severity=Severity.WARNING,
                message=f"HAZOP nodes are missing recommendation priority/status tracking: {', '.join(missing_tracking[:5])}.",
                artifact_ref="hazop_node_register",
            )
        )
    return issues


def validate_cross_chapter_consistency(
    config: ProjectConfig,
    route_selection: RouteSelectionArtifact,
    site_selection: SiteSelectionArtifact,
    utility_network_decision: UtilityNetworkDecision,
    utility_summary: UtilitySummaryArtifact,
    cost_model: CostModel,
    working_capital: WorkingCapitalModel,
    financial_model: FinancialModel,
    site_decision: DecisionRecord | None = None,
    utility_basis_decision: DecisionRecord | None = None,
    economic_basis_decision: DecisionRecord | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def _sum_utility_family(prefix: str) -> float:
        return sum(
            item.load
            for item in utility_summary.items
            if item.utility_type.lower().startswith(prefix.lower())
        )

    if site_decision and site_decision.selected_candidate_id and site_decision.selected_candidate_id != site_selection.selected_site:
        issues.append(
            ValidationIssue(
                code="site_selection_cross_mismatch",
                severity=Severity.BLOCKED,
                message="Selected site is inconsistent between the site artifact and site decision record.",
                artifact_ref="site_selection",
            )
        )
    if cost_model.selected_route_id and cost_model.selected_route_id != route_selection.selected_route_id:
        issues.append(
            ValidationIssue(
                code="route_cost_mismatch",
                severity=Severity.BLOCKED,
                message="Cost model selected route does not match the route-selection artifact.",
                artifact_ref="cost_model",
            )
        )
    if utility_summary.selected_heat_integration_case_id != utility_network_decision.selected_case_id:
        issues.append(
            ValidationIssue(
                code="utility_heat_case_mismatch",
                severity=Severity.BLOCKED,
                message="Utility summary and utility-network decision disagree on the selected heat-integration case.",
                artifact_ref="utility_summary",
            )
        )
    if cost_model.selected_heat_integration_case_id != utility_network_decision.selected_case_id:
        issues.append(
            ValidationIssue(
                code="cost_heat_case_mismatch",
                severity=Severity.BLOCKED,
                message="Cost model and utility-network decision disagree on the selected heat-integration case.",
                artifact_ref="cost_model",
            )
        )
    if utility_basis_decision and utility_summary.utility_basis is not None:
        selected_alt = next((item for item in utility_basis_decision.alternatives if item.candidate_id == utility_basis_decision.selected_candidate_id), None)
        if selected_alt is not None:
            selected_pressure = float(selected_alt.outputs.get("steam_pressure_bar", utility_summary.utility_basis.steam_pressure_bar))
            if abs(selected_pressure - utility_summary.utility_basis.steam_pressure_bar) > 1e-6:
                issues.append(
                    ValidationIssue(
                        code="utility_basis_mismatch",
                        severity=Severity.BLOCKED,
                        message="Utility basis decision does not match the stored utility basis.",
                        artifact_ref="utility_summary",
                    )
                )
    if utility_summary.utility_basis is not None:
        annual_hours = operating_hours_per_year(config.basis)
        steam_load = _sum_utility_family("Steam")
        cw_load = _sum_utility_family("Cooling water")
        power_load = _sum_utility_family("Electricity")
        expected_utility_cost = (
            steam_load * annual_hours * utility_summary.utility_basis.steam_cost_inr_per_kg
            + cw_load * annual_hours * utility_summary.utility_basis.cooling_water_cost_inr_per_m3
            + power_load * annual_hours * utility_summary.utility_basis.power_cost_inr_per_kwh
        )
        if abs(expected_utility_cost - cost_model.annual_utility_cost) / max(cost_model.annual_utility_cost, 1.0) > 0.05:
            issues.append(
                ValidationIssue(
                    code="utility_cost_cross_mismatch",
                    severity=Severity.BLOCKED,
                    message="Cost model utility OPEX is inconsistent with utility loads and selected tariff basis.",
                    artifact_ref="cost_model",
                )
            )
    if abs(financial_model.annual_operating_cost - cost_model.annual_opex) / max(cost_model.annual_opex, 1.0) > 0.005:
        issues.append(
            ValidationIssue(
                code="financial_opex_mismatch",
                severity=Severity.BLOCKED,
                message="Financial model operating cost does not match the cost model.",
                artifact_ref="financial_model",
            )
        )
    if abs(financial_model.working_capital - working_capital.working_capital_inr) / max(working_capital.working_capital_inr, 1.0) > 0.005:
        issues.append(
            ValidationIssue(
                code="financial_working_capital_mismatch",
                severity=Severity.BLOCKED,
                message="Financial model working capital does not match the working-capital model.",
                artifact_ref="financial_model",
            )
        )
    cost_scenarios = {item.scenario_name for item in cost_model.scenario_results}
    financial_scenarios = {item.scenario_name for item in financial_model.scenario_results}
    if cost_scenarios != financial_scenarios:
        issues.append(
            ValidationIssue(
                code="scenario_set_mismatch",
                severity=Severity.BLOCKED,
                message="Financial model scenarios do not match cost-model scenarios.",
                artifact_ref="financial_model",
            )
        )
    if any(cost_scenario.utility_island_impacts and not financial_scenario.utility_island_impacts for cost_scenario, financial_scenario in zip(cost_model.scenario_results, financial_model.scenario_results)):
        issues.append(
            ValidationIssue(
                code="scenario_island_breakdown_missing",
                severity=Severity.BLOCKED,
                message="Financial-model scenarios lost the utility-island economic breakdown from the cost model.",
                artifact_ref="financial_model",
            )
        )
    if economic_basis_decision and economic_basis_decision.scenario_stability == ScenarioStability.UNSTABLE and not economic_basis_decision.approval_required:
        issues.append(
            ValidationIssue(
                code="economic_basis_unstable",
                severity=Severity.BLOCKED,
                message="Economic basis decision is unstable under conservative scenarios.",
                artifact_ref="economic_basis",
            )
        )
    return issues


def apply_state_issues(state: ProjectRunState, issues: list[ValidationIssue], missing_india_coverage: list[str], stale_source_groups: list[str]) -> None:
    state.blocking_issues = [issue for issue in issues if issue.severity == Severity.BLOCKED]
    state.missing_india_coverage = missing_india_coverage
    state.stale_source_groups = stale_source_groups
