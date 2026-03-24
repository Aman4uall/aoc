from __future__ import annotations

from aoc.calculators import operating_hours_per_year, reaction_balance_delta, reaction_is_balanced
from aoc.models import (
    ChapterArtifact,
    ColumnDesign,
    ControlArchitectureDecision,
    CostModel,
    DecisionRecord,
    EnergyBalance,
    FinancialModel,
    FlowsheetGraph,
    GeographicScope,
    HazopNodeRegister,
    HeatExchangerDesign,
    HeatIntegrationStudyArtifact,
    IndianLocationDatum,
    IndianPriceDatum,
    KineticAssessmentArtifact,
    ProcessArchetype,
    PropertyGapArtifact,
    ProvenanceTag,
    ProjectConfig,
    ProjectRunState,
    PropertyRecord,
    ReactionSystem,
    ReactorDesign,
    ResearchBundle,
    ResolvedSourceSet,
    ResolvedValueArtifact,
    RouteSelectionArtifact,
    SiteSelectionArtifact,
    ScenarioStability,
    Severity,
    SourceDomain,
    SourceRecord,
    StreamTable,
    ThermoAssessmentArtifact,
    UtilitySummaryArtifact,
    UtilityNetworkDecision,
    ValidationIssue,
    WorkingCapitalModel,
    SensitivityLevel,
)


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
    if site_selection.selected_site and site_selection.selected_site not in candidate_names:
        issues.append(
            ValidationIssue(
                code="selected_site_missing_candidate",
                severity=Severity.BLOCKED,
                message=f"Selected site '{site_selection.selected_site}' is not present in scored candidates.",
                artifact_ref="site_selection",
            )
        )
    if site_selection.selected_site and location_names and site_selection.selected_site not in location_names:
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
    if stream_table.closure_error_pct <= tolerance_pct:
        return []
    return [
        ValidationIssue(
            code="stream_closure",
            severity=Severity.BLOCKED,
            message=f"Stream table closure error {stream_table.closure_error_pct:.3f}% exceeds tolerance {tolerance_pct:.3f}%.",
            artifact_ref="stream_table",
        )
    ]


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
    return issues


def validate_equipment_applicability(
    route,
    reactor_choice: DecisionRecord,
    separation_choice: DecisionRecord,
    reactor: ReactorDesign,
    column: ColumnDesign,
    exchanger: HeatExchangerDesign,
    utility_network_decision: UtilityNetworkDecision,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selected_case = next((item for item in utility_network_decision.cases if item.case_id == utility_network_decision.selected_case_id), None)
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
    return issues


def validate_working_capital(model: WorkingCapitalModel) -> list[ValidationIssue]:
    if model.working_capital_inr > 0:
        return []
    return [
        ValidationIssue(
            code="invalid_working_capital",
            severity=Severity.BLOCKED,
            message="Working capital must be positive.",
            artifact_ref="working_capital_model",
        )
    ]


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


def validate_hazop_node_register(register: HazopNodeRegister) -> list[ValidationIssue]:
    if register.nodes:
        return []
    return [
        ValidationIssue(
            code="hazop_register_empty",
            severity=Severity.BLOCKED,
            message="HAZOP node register is empty.",
            artifact_ref="hazop_node_register",
        )
    ]


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
        steam_load = next((item.load for item in utility_summary.items if item.utility_type == "Steam"), 0.0)
        cw_load = next((item.load for item in utility_summary.items if item.utility_type == "Cooling water"), 0.0)
        power_load = next((item.load for item in utility_summary.items if item.utility_type == "Electricity"), 0.0)
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
    state.blocking_issues = issues
    state.missing_india_coverage = missing_india_coverage
    state.stale_source_groups = stale_source_groups
