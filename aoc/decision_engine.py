from __future__ import annotations

import math

from aoc.calculators import hourly_output_kg, operating_hours_per_year, reaction_is_balanced
from aoc.models import (
    AlternativeOption,
    AssumptionRecord,
    CalcTrace,
    CostModel,
    DecisionCriterion,
    DecisionRecord,
    FinancialModel,
    FlowsheetBlueprintArtifact,
    HeatIntegrationCase,
    HeatIntegrationStudyArtifact,
    HeatMatch,
    HeatStream,
    ProcessSynthesisArtifact,
    ProjectConfig,
    PropertyGapArtifact,
    ProvenanceTag,
    ReactionParticipant,
    RoughAlternativeCase,
    RoughAlternativeSummaryArtifact,
    RouteFamilyArtifact,
    RouteFamilyProfile,
    RouteChemistryArtifact,
    RouteSelectionArtifact,
    RouteSurveyArtifact,
    ScenarioResult,
    ScenarioStability,
    SensitivityLevel,
    SiteSelectionArtifact,
    UnitTrainCandidateSet,
    UtilityBasis,
    UtilityNetworkDecision,
    UtilityTarget,
    ValueRecord,
)
from aoc.route_families import build_route_family_artifact, profile_for_route
from aoc.value_engine import make_value_record


HIGH_SENSITIVITY_PROPERTIES = {"molecular weight", "density"}
MEDIUM_SENSITIVITY_PROPERTIES = {"boiling point", "melting point"}


def _price_lookup(price_data, item_name: str, default: float) -> float:
    for datum in price_data:
        if datum.item_name.lower() == item_name.lower():
            return datum.value_inr
    return default


def _format_score(value: float) -> str:
    return f"{value:.2f}"


def _route_product(route) -> ReactionParticipant:
    for participant in route.participants:
        if participant.role == "product":
            return participant
    raise ValueError(f"Route '{route.route_id}' has no product participant.")


def _route_profile(route, route_families: RouteFamilyArtifact | None = None) -> RouteFamilyProfile:
    return profile_for_route(route_families, route.route_id) or build_route_family_artifact(
        RouteSurveyArtifact(routes=[route], markdown="", citations=route.citations, assumptions=route.assumptions)
    ).profiles[0]


def _route_water_ratio(profile: RouteFamilyProfile) -> float:
    if profile.route_family_id == "liquid_hydration_train":
        return 20.0
    if profile.route_family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"}:
        return 1.3
    if profile.route_family_id == "chlorinated_hydrolysis_train":
        return 3.5
    if profile.route_family_id == "gas_absorption_converter_train":
        return 0.8
    return 2.0


def _route_safety_score(route) -> float:
    severity_rank = {"low": 85.0, "moderate": 60.0, "high": 35.0}
    if not route.hazards:
        return 75.0
    return min(severity_rank.get(hazard.severity, 45.0) for hazard in route.hazards)


def _route_regulatory_block(profile: RouteFamilyProfile) -> str | None:
    return profile.india_deployment_blocker or None


def _route_byproduct_credit(route) -> float:
    byproducts = " ".join(route.byproducts).lower()
    if "diethylene glycol" in byproducts or "triethylene glycol" in byproducts:
        return 12.0
    return 0.0


def _candidate_id(label: str) -> str:
    sanitized = []
    for char in label.lower():
        sanitized.append(char if char.isalnum() else "_")
    return "_".join(part for part in "".join(sanitized).split("_") if part)


def _blueprint_for_route(
    unit_train_candidates: UnitTrainCandidateSet | None,
    route_id: str,
) -> FlowsheetBlueprintArtifact | None:
    if unit_train_candidates is None:
        return None
    for blueprint in unit_train_candidates.blueprints:
        if blueprint.route_id == route_id:
            return blueprint
    return None


def _blueprint_complexity_metrics(
    blueprint: FlowsheetBlueprintArtifact | None,
) -> tuple[int, int, int, bool]:
    if blueprint is None:
        return 0, 0, 0, False
    return (
        len(blueprint.steps),
        len(blueprint.separation_duties),
        len(blueprint.recycle_intents),
        blueprint.batch_capable,
    )


def _family_heat_signature(case: RoughAlternativeCase) -> dict[str, float]:
    family_id = case.route_family_id or "generic_mixed_train"
    signatures = {
        "liquid_hydration_train": {
            "reactor_hot_supply_c": 195.0,
            "reactor_hot_target_c": 135.0,
            "condensing_hot_supply_c": 150.0,
            "reboiler_cold_supply_c": 110.0,
            "reboiler_cold_target_c": 175.0,
            "feed_cold_target_c": 120.0,
            "recoverability": 0.78,
            "pinch_temp_c": 153.0,
            "multi_effect_fraction": 0.44,
            "multi_effect_capex_inr": 2.2e8,
            "htm_fraction": 0.80,
            "htm_capex_inr": 5.8e8,
        },
        "carbonylation_liquid_train": {
            "reactor_hot_supply_c": 188.0,
            "reactor_hot_target_c": 132.0,
            "condensing_hot_supply_c": 145.0,
            "reboiler_cold_supply_c": 102.0,
            "reboiler_cold_target_c": 162.0,
            "feed_cold_target_c": 112.0,
            "recoverability": 0.64,
            "pinch_temp_c": 146.0,
            "multi_effect_fraction": 0.34,
            "multi_effect_capex_inr": 1.9e8,
            "htm_fraction": 0.66,
            "htm_capex_inr": 4.8e8,
        },
        "gas_absorption_converter_train": {
            "reactor_hot_supply_c": 185.0,
            "reactor_hot_target_c": 118.0,
            "condensing_hot_supply_c": 140.0,
            "reboiler_cold_supply_c": 88.0,
            "reboiler_cold_target_c": 142.0,
            "feed_cold_target_c": 92.0,
            "recoverability": 0.56,
            "pinch_temp_c": 132.0,
            "multi_effect_fraction": 0.28,
            "multi_effect_capex_inr": 1.6e8,
            "htm_fraction": 0.54,
            "htm_capex_inr": 4.0e8,
        },
        "solids_carboxylation_train": {
            "reactor_hot_supply_c": 122.0,
            "reactor_hot_target_c": 78.0,
            "condensing_hot_supply_c": 96.0,
            "reboiler_cold_supply_c": 82.0,
            "reboiler_cold_target_c": 118.0,
            "feed_cold_target_c": 74.0,
            "recoverability": 0.26,
            "pinch_temp_c": 92.0,
            "multi_effect_fraction": 0.24,
            "multi_effect_capex_inr": 1.2e8,
            "htm_fraction": 0.22,
            "htm_capex_inr": 2.6e8,
        },
        "integrated_solvay_liquor_train": {
            "reactor_hot_supply_c": 128.0,
            "reactor_hot_target_c": 82.0,
            "condensing_hot_supply_c": 102.0,
            "reboiler_cold_supply_c": 86.0,
            "reboiler_cold_target_c": 122.0,
            "feed_cold_target_c": 78.0,
            "recoverability": 0.32,
            "pinch_temp_c": 96.0,
            "multi_effect_fraction": 0.27,
            "multi_effect_capex_inr": 1.3e8,
            "htm_fraction": 0.28,
            "htm_capex_inr": 2.9e8,
        },
        "oxidation_recovery_train": {
            "reactor_hot_supply_c": 172.0,
            "reactor_hot_target_c": 116.0,
            "condensing_hot_supply_c": 132.0,
            "reboiler_cold_supply_c": 92.0,
            "reboiler_cold_target_c": 148.0,
            "feed_cold_target_c": 96.0,
            "recoverability": 0.46,
            "pinch_temp_c": 124.0,
            "multi_effect_fraction": 0.30,
            "multi_effect_capex_inr": 1.55e8,
            "htm_fraction": 0.58,
            "htm_capex_inr": 4.2e8,
        },
        "chlorinated_hydrolysis_train": {
            "reactor_hot_supply_c": 142.0,
            "reactor_hot_target_c": 88.0,
            "condensing_hot_supply_c": 108.0,
            "reboiler_cold_supply_c": 84.0,
            "reboiler_cold_target_c": 126.0,
            "feed_cold_target_c": 82.0,
            "recoverability": 0.20,
            "pinch_temp_c": 90.0,
            "multi_effect_fraction": 0.22,
            "multi_effect_capex_inr": 1.1e8,
            "htm_fraction": 0.18,
            "htm_capex_inr": 2.3e8,
        },
        "regeneration_loop_train": {
            "reactor_hot_supply_c": 168.0,
            "reactor_hot_target_c": 112.0,
            "condensing_hot_supply_c": 126.0,
            "reboiler_cold_supply_c": 90.0,
            "reboiler_cold_target_c": 146.0,
            "feed_cold_target_c": 94.0,
            "recoverability": 0.42,
            "pinch_temp_c": 118.0,
            "multi_effect_fraction": 0.29,
            "multi_effect_capex_inr": 1.45e8,
            "htm_fraction": 0.40,
            "htm_capex_inr": 3.2e8,
        },
        "extraction_recovery_train": {
            "reactor_hot_supply_c": 156.0,
            "reactor_hot_target_c": 104.0,
            "condensing_hot_supply_c": 124.0,
            "reboiler_cold_supply_c": 92.0,
            "reboiler_cold_target_c": 138.0,
            "feed_cold_target_c": 90.0,
            "recoverability": 0.38,
            "pinch_temp_c": 112.0,
            "multi_effect_fraction": 0.26,
            "multi_effect_capex_inr": 1.35e8,
            "htm_fraction": 0.44,
            "htm_capex_inr": 3.1e8,
        },
    }
    return signatures.get(
        family_id,
        {
            "reactor_hot_supply_c": 110.0,
            "reactor_hot_target_c": 70.0,
            "condensing_hot_supply_c": 95.0,
            "reboiler_cold_supply_c": 85.0,
            "reboiler_cold_target_c": 120.0,
            "feed_cold_target_c": 80.0,
            "recoverability": 0.18,
            "pinch_temp_c": 95.0,
            "multi_effect_fraction": 0.24,
            "multi_effect_capex_inr": 1.4e8,
            "htm_fraction": 0.32,
            "htm_capex_inr": 3.0e8,
        },
    )


def _supports_htm_topology(case: RoughAlternativeCase) -> bool:
    return case.heat_recovery_style in {
        "condenser_reboiler_cluster",
        "shared_htm_island_network",
        "staged_utility_header_network",
        "waste_heat_boiler",
    }


def _normalize_scores(values: dict[str, float], reverse: bool = False) -> dict[str, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if math.isclose(lo, hi):
        return {key: 75.0 for key in values}
    scores: dict[str, float] = {}
    for key, value in values.items():
        ratio = (value - lo) / (hi - lo)
        score = 100.0 * (1.0 - ratio if reverse else ratio)
        scores[key] = max(0.0, min(100.0, score))
    return scores


def _ranking_gap(ranking: list[tuple[float, str]]) -> float:
    if len(ranking) < 2:
        return 1.0
    top = ranking[0][0]
    runner_up = ranking[1][0]
    return abs(top - runner_up) / max(abs(top), 1.0)


def resolve_property_gaps(product_profile, config: ProjectConfig) -> PropertyGapArtifact:
    value_records: list[ValueRecord] = []
    assumptions_log: list[AssumptionRecord] = []
    unresolved_high_sensitivity: list[str] = []
    for item in product_profile.properties:
        normalized_name = item.name.strip().lower()
        effective_method = item.method
        basis_text = (item.basis or "").lower()
        assumption_text = " ".join(item.assumptions).lower()
        if (
            normalized_name == "density"
            and item.method == ProvenanceTag.CALCULATED
            and ("specific gravity" in basis_text or "specific gravity" in assumption_text)
            and (item.supporting_sources or item.citations)
        ):
            effective_method = ProvenanceTag.SOURCED
            assumptions_log.append(
                AssumptionRecord(
                    assumption_id="density_from_specific_gravity",
                    statement="Density derived directly from a cited specific-gravity reference is accepted as a sourced ambient-density basis.",
                    reason="For liquid glycols near ambient conditions, a cited specific-gravity table provides a defendable density basis for preliminary design.",
                    impact_scope="property profile, storage sizing, utilities, and economics",
                    expiry_review_condition="Replace if a direct density-vs-temperature table is retrieved for the selected process conditions.",
                )
            )
        if normalized_name in HIGH_SENSITIVITY_PROPERTIES:
            sensitivity = SensitivityLevel.HIGH
        elif normalized_name in MEDIUM_SENSITIVITY_PROPERTIES:
            sensitivity = SensitivityLevel.MEDIUM
        else:
            sensitivity = SensitivityLevel.LOW
        blocking = (
            config.uncertainty_policy.high_sensitivity_blocks
            and sensitivity == SensitivityLevel.HIGH
            and effective_method not in {ProvenanceTag.SOURCED, ProvenanceTag.USER_SUPPLIED}
        )
        if blocking:
            unresolved_high_sensitivity.append(item.name)
        value_records.append(
            ValueRecord(
                value_id=normalized_name.replace(" ", "_"),
                name=item.name,
                value=item.value,
                units=item.units,
                provenance_method=effective_method,
                source_ids=item.supporting_sources or item.citations,
                uncertainty_band="tight" if effective_method in {ProvenanceTag.SOURCED, ProvenanceTag.USER_SUPPLIED} else "review",
                sensitivity=sensitivity,
                blocking=blocking,
                citations=item.citations,
                assumptions=item.assumptions,
            )
        )
    if not assumptions_log:
        assumptions_log.append(
            AssumptionRecord(
                assumption_id="property_resolution_policy",
                statement="Property values are carried into design with explicit provenance and sensitivity tagging.",
                reason="Decision and economics stages need blocking behavior for weak high-sensitivity values.",
                impact_scope="product profile, balances, utilities, economics",
                expiry_review_condition="Replace if higher-quality cited property data becomes available.",
            )
        )
    rows = [
        "| Property | Value | Units | Method | Sensitivity | Blocking |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for value in value_records:
        rows.append(
            f"| {value.name} | {value.value} | {value.units} | {value.provenance_method.value} | {value.sensitivity.value} | {'yes' if value.blocking else 'no'} |"
        )
    markdown = "\n".join(rows)
    assumptions = product_profile.assumptions + [
        "Property-gap resolution applies a single hierarchy from sourced values to conservative assumptions.",
    ]
    return PropertyGapArtifact(
        values=value_records,
        assumptions_log=assumptions_log,
        unresolved_high_sensitivity=sorted(set(unresolved_high_sensitivity)),
        markdown=markdown,
        citations=product_profile.citations,
        assumptions=assumptions,
    )


def _operating_mode_decision(config: ProjectConfig, citations: list[str]) -> DecisionRecord:
    basis = config.basis
    product_name = basis.target_product
    criteria = [
        DecisionCriterion(name="Throughput support", weight=0.35, justification="Large process plants generally favor continuous operation."),
        DecisionCriterion(name="Changeover burden", weight=0.15, justification="Single-product dedicated service does not usually need batch flexibility."),
        DecisionCriterion(name="Heat integration fit", weight=0.25, justification="Continuous service better supports stable utility targeting and recovery."),
        DecisionCriterion(name="Control and operability", weight=0.25, justification="Steady-state hazard management is preferred for most large benchmark plants."),
    ]
    alternatives = [
        AlternativeOption(
            candidate_id="continuous",
            candidate_type="operating_mode",
            description="Continuous plant basis",
            inputs={"capacity_tpa": f"{basis.capacity_tpa:.0f}"},
            outputs={"fit": f"Best for large dedicated {product_name} service and utility integration"},
            score_breakdown={"Throughput support": 97.0, "Changeover burden": 90.0, "Heat integration fit": 96.0, "Control and operability": 88.0},
            total_score=93.0,
            citations=citations,
        ),
        AlternativeOption(
            candidate_id="batch",
            candidate_type="operating_mode",
            description="Batch campaign basis",
            inputs={"capacity_tpa": f"{basis.capacity_tpa:.0f}"},
            outputs={"fit": "Useful mainly for small or campaign-based service"},
            rejected_reasons=[f"Plant scale and dedicated {product_name} service make batch operation weaker on economics and operability."],
            score_breakdown={"Throughput support": 18.0, "Changeover burden": 40.0, "Heat integration fit": 12.0, "Control and operability": 28.0},
            total_score=24.5,
            citations=citations,
        ),
    ]
    return DecisionRecord(
        decision_id="operating_mode",
        context="Plant operating mode",
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id="continuous",
        selected_summary=f"Continuous operation is selected because the {product_name} scale, utility integration need, and hazard envelope all favor steady-state operation.",
        hard_constraint_results=[f"Capacity basis: {basis.capacity_tpa:.0f} TPA"],
        confidence=0.93,
        scenario_stability=ScenarioStability.STABLE,
        approval_required=False,
        citations=citations,
        assumptions=["Operating mode is determined deterministically from plant scale and service pattern."],
    )


def build_process_synthesis(
    config: ProjectConfig,
    route_survey: RouteSurveyArtifact,
    property_gap: PropertyGapArtifact,
    operating_mode_decision: DecisionRecord | None = None,
    route_families: RouteFamilyArtifact | None = None,
) -> ProcessSynthesisArtifact:
    citations = sorted(set(route_survey.citations + property_gap.citations))
    operating_mode_decision = operating_mode_decision or _operating_mode_decision(config, citations)
    route_families = route_families or build_route_family_artifact(route_survey)
    alternatives: list[AlternativeOption] = []
    for route in route_survey.routes:
        profile = _route_profile(route, route_families)
        alternatives.append(
            AlternativeOption(
                candidate_id=f"alt_{route.route_id}",
                candidate_type="process_architecture",
                description=f"{route.name} with {operating_mode_decision.selected_candidate_id} operation",
                inputs={
                    "route_id": route.route_id,
                    "operating_mode": operating_mode_decision.selected_candidate_id or "continuous",
                    "route_family": profile.route_family_id,
                    "reactor_class": profile.primary_reactor_class,
                },
                outputs={
                    "separation_train": profile.primary_separation_train,
                    "heat_recovery_style": profile.heat_recovery_style,
                    "maturity_score": _format_score(profile.maturity_score),
                    "india_fit_score": _format_score(profile.india_fit_score),
                },
                rejected_reasons=[profile.india_deployment_blocker] if profile.india_deployment_blocker else [],
                score_breakdown={
                    "maturity": profile.maturity_score,
                    "india_fit": profile.india_fit_score,
                    "safety": _route_safety_score(route),
                    "operability": profile.operability_score,
                },
                total_score=(
                    0.35 * profile.maturity_score
                    + 0.25 * profile.india_fit_score
                    + 0.20 * _route_safety_score(route)
                    + 0.20 * profile.operability_score
                ),
                feasible=profile.india_deployment_blocker == "" and reaction_is_balanced(route),
                citations=route.citations,
                assumptions=route.assumptions + [f"Route family `{profile.route_family_id}` drives first-pass synthesis scoring."],
            )
        )
    rows = [
        "| Candidate | Reactor | Separation Train | Feasible |",
        "| --- | --- | --- | --- |",
    ]
    for option in alternatives:
        rows.append(
            f"| {option.inputs.get('route_id', option.candidate_id)} | {option.inputs.get('reactor_class', 'n/a')} | {option.outputs.get('separation_train', 'n/a')} | {'yes' if option.feasible else 'no'} |"
        )
    markdown = (
        "The synthesis layer generates route-specific process architectures before detailed sizing. "
        "At this stage the system locks operating mode and the first-pass reactor/separation families, but defers final route choice until rough duties and heat recovery have been evaluated.\n\n"
        + "\n".join(rows)
    )
    return ProcessSynthesisArtifact(
        operating_mode_decision=operating_mode_decision,
        route_candidates=alternatives,
        markdown=markdown,
        citations=citations,
        assumptions=route_survey.assumptions + property_gap.assumptions + operating_mode_decision.assumptions,
    )


def build_site_selection_decision(config: ProjectConfig, site_selection: SiteSelectionArtifact) -> DecisionRecord:
    preferred_sites = {item.lower() for item in config.preferred_site_candidates}
    preferred_states = {item.lower() for item in config.preferred_state_candidates}
    criteria = [
        DecisionCriterion(name="Feedstock and cluster fit", weight=0.35, justification="Petrochemical integration and cluster density dominate EG site practicality."),
        DecisionCriterion(name="Logistics", weight=0.25, justification="Port connectivity and outbound distribution materially affect India economics."),
        DecisionCriterion(name="Utilities", weight=0.20, justification="Utility reliability and industrial support are required for continuous EG service."),
        DecisionCriterion(name="Business and compliance fit", weight=0.20, justification="Landability, compliance maturity, and local industrial ecosystem matter at scale."),
    ]
    alternatives: list[AlternativeOption] = []
    ranking: list[tuple[float, str]] = []
    for candidate in site_selection.candidates:
        preference_bonus = 0.0
        if candidate.name.lower() in preferred_sites:
            preference_bonus += 4.0
        if candidate.state.lower() in preferred_states:
            preference_bonus += 2.0
        total_score = (
            0.35 * candidate.raw_material_score * 10.0
            + 0.25 * candidate.logistics_score * 10.0
            + 0.20 * candidate.utility_score * 10.0
            + 0.20 * candidate.business_score * 10.0
            + preference_bonus
        )
        alternatives.append(
            AlternativeOption(
                candidate_id=candidate.name,
                candidate_type="site_selection",
                description=f"{candidate.name}, {candidate.state}",
                outputs={
                    "state": candidate.state,
                    "cluster_score": f"{candidate.raw_material_score:.1f}",
                    "logistics_score": f"{candidate.logistics_score:.1f}",
                    "utilities_score": f"{candidate.utility_score:.1f}",
                },
                score_breakdown={
                    "Feedstock and cluster fit": candidate.raw_material_score * 10.0,
                    "Logistics": candidate.logistics_score * 10.0,
                    "Utilities": candidate.utility_score * 10.0,
                    "Business and compliance fit": candidate.business_score * 10.0,
                },
                total_score=round(total_score, 3),
                feasible=True,
                citations=candidate.citations,
                assumptions=candidate.assumptions,
            )
        )
        ranking.append((total_score, candidate.name))
    ranking.sort(key=lambda pair: pair[0], reverse=True)
    selected_site = ranking[0][1] if ranking else site_selection.selected_site
    gap = _ranking_gap(ranking)
    return DecisionRecord(
        decision_id="site_selection",
        context="India site selection",
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id=selected_site,
        selected_summary=f"{selected_site} is selected because it provides the strongest combined cluster, logistics, utility, and India execution fit for a 200000 TPA EG plant.",
        hard_constraint_results=["Site candidates are restricted to India-only locations."],
        confidence=0.90 if gap >= 0.08 else 0.72,
        scenario_stability=ScenarioStability.STABLE if gap >= 0.08 else ScenarioStability.BORDERLINE,
        approval_required=gap < 0.05,
        citations=site_selection.citations,
        assumptions=site_selection.assumptions + ["Site choice is ranked deterministically from scored India cluster attributes and configured preferences."],
    )


def _rough_case_for_route(
    config: ProjectConfig,
    route,
    market,
    route_families: RouteFamilyArtifact | None = None,
    unit_train_candidates: UnitTrainCandidateSet | None = None,
) -> RoughAlternativeCase:
    basis = config.basis
    product = _route_product(route)
    profile = _route_profile(route, route_families)
    blueprint = _blueprint_for_route(unit_train_candidates, route.route_id)
    blueprint_step_count, separation_duty_count, recycle_intent_count, batch_capable = _blueprint_complexity_metrics(blueprint)
    annual_hours = operating_hours_per_year(basis)
    product_mass_kg_hr = hourly_output_kg(basis)
    product_kmol_hr = product_mass_kg_hr / max(product.molecular_weight_g_mol, 1.0)
    water_ratio = _route_water_ratio(profile)
    reactant_ratio = max(route.selectivity_fraction * route.yield_fraction, 0.35)
    feed_extent_kmol_hr = product_kmol_hr / reactant_ratio
    dehydration_burden_kw = max((water_ratio - 1.0) * feed_extent_kmol_hr * 18.015 * 2200.0 / 3600.0, 0.0)
    if profile.route_family_id in {"solids_carboxylation_train", "integrated_solvay_liquor_train"}:
        dehydration_burden_kw *= 0.30
    elif profile.route_family_id == "chlorinated_hydrolysis_train":
        dehydration_burden_kw *= 0.55
    reaction_intensity = {
        "liquid_hydration_train": 90.0,
        "carbonylation_liquid_train": 70.0,
        "gas_absorption_converter_train": 82.0,
        "solids_carboxylation_train": 48.0,
        "integrated_solvay_liquor_train": 54.0,
        "oxidation_recovery_train": 62.0,
        "chlorinated_hydrolysis_train": 55.0,
        "regeneration_loop_train": 68.0,
    }.get(profile.route_family_id, 58.0)
    polishing_factor = {
        "liquid_hydration_train": 0.06,
        "carbonylation_liquid_train": 0.07,
        "gas_absorption_converter_train": 0.08,
        "solids_carboxylation_train": 0.05,
        "integrated_solvay_liquor_train": 0.09,
        "oxidation_recovery_train": 0.10,
        "chlorinated_hydrolysis_train": 0.12,
        "regeneration_loop_train": 0.11,
    }.get(profile.route_family_id, 0.09)
    cooling_multiplier = {
        "liquid_hydration_train": 0.72,
        "carbonylation_liquid_train": 0.64,
        "gas_absorption_converter_train": 0.58,
        "solids_carboxylation_train": 0.42,
        "integrated_solvay_liquor_train": 0.47,
        "oxidation_recovery_train": 0.52,
        "chlorinated_hydrolysis_train": 0.40,
        "regeneration_loop_train": 0.50,
    }.get(profile.route_family_id, 0.50)
    reaction_cooling_kw = abs(product_kmol_hr * 1000.0 * reaction_intensity / 3600.0)
    polishing_heating_kw = product_mass_kg_hr * polishing_factor
    estimated_heating_kw = dehydration_burden_kw + polishing_heating_kw
    estimated_cooling_kw = reaction_cooling_kw + estimated_heating_kw * cooling_multiplier
    if blueprint is not None:
        estimated_heating_kw *= 1.0 + 0.010 * recycle_intent_count
        estimated_cooling_kw *= 1.0 + 0.010 * recycle_intent_count
        if batch_capable and basis.operating_mode == "batch":
            estimated_heating_kw *= 1.03
            estimated_cooling_kw *= 1.02
    steam_price = _price_lookup(market.india_price_data, "Steam", 1.8)
    cooling_water_price = _price_lookup(market.india_price_data, "Cooling water", 8.0)
    power_price = _price_lookup(market.india_price_data, "Electricity", 8.5)
    steam_cost = estimated_heating_kw * 3600.0 / 2200.0 * steam_price * annual_hours
    cooling_cost = estimated_cooling_kw * 3600.0 / (4.18 * 10.0 * 1000.0) * cooling_water_price * annual_hours
    power_cost = product_mass_kg_hr * (0.010 + max(profile.utility_intensity_factor - 0.9, 0.0) * 0.015) * power_price * annual_hours
    estimated_annual_utility_cost_inr = steam_cost + cooling_cost + power_cost
    base_capex = 7.4e9 * profile.capex_intensity_factor
    estimated_capex_inr = base_capex + estimated_heating_kw * 8500.0 + estimated_cooling_kw * 6200.0
    if blueprint is not None:
        complexity_index = max(blueprint_step_count - 4, 0)
        estimated_capex_inr *= (
            1.0
            + 0.050 * complexity_index
            + 0.060 * separation_duty_count
            + 0.050 * recycle_intent_count
            + (0.080 if batch_capable else 0.0)
        )
    feedstock_factor = 5.0e9 * (0.90 + profile.capex_intensity_factor * 0.12)
    if blueprint is not None:
        feedstock_factor *= (
            1.0
            + 0.015 * max(blueprint_step_count - 4, 0)
            + 0.020 * separation_duty_count
            + 0.025 * recycle_intent_count
            + (0.040 if batch_capable else 0.0)
        )
    estimated_annual_total_opex_inr = feedstock_factor + estimated_annual_utility_cost_inr
    note = (
        f"{profile.family_label} rough balance uses route-family factors for utility and CAPEX intensity."
    )
    if blueprint is not None:
        note += (
            f" Blueprint complexity adds {blueprint_step_count} mapped steps, "
            f"{separation_duty_count} separation duties, and {recycle_intent_count} recycle intents."
        )
        if batch_capable:
            note += " Batch-capable blueprint handling is included in the rough screening."
    note += " " + (" ".join(profile.critic_flags[:2]) if profile.critic_flags else "No special critic penalties were triggered.")
    return RoughAlternativeCase(
        candidate_id=f"alt_{route.route_id}",
        route_id=route.route_id,
        route_name=route.name,
        route_family_id=profile.route_family_id,
        route_family_label=profile.family_label,
        operating_mode=config.basis.operating_mode,
        reactor_class=profile.primary_reactor_class,
        separation_train=profile.primary_separation_train,
        heat_recovery_style=profile.heat_recovery_style,
        blueprint_step_count=blueprint_step_count,
        separation_duty_count=separation_duty_count,
        recycle_intent_count=recycle_intent_count,
        batch_capable=batch_capable,
        estimated_heating_kw=round(estimated_heating_kw, 3),
        estimated_cooling_kw=round(estimated_cooling_kw, 3),
        estimated_capex_inr=round(estimated_capex_inr, 2),
        estimated_annual_utility_cost_inr=round(estimated_annual_utility_cost_inr, 2),
        estimated_annual_total_opex_inr=round(estimated_annual_total_opex_inr, 2),
        critic_flags=profile.critic_flags,
        notes=note,
        citations=route.citations + market.citations,
        assumptions=route.assumptions + market.assumptions + [f"Route family `{profile.route_family_id}` drives rough utility/CAPEX screening."],
    )


def build_rough_alternatives(
    config: ProjectConfig,
    route_survey: RouteSurveyArtifact,
    synthesis: ProcessSynthesisArtifact,
    market,
    route_families: RouteFamilyArtifact | None = None,
    unit_train_candidates: UnitTrainCandidateSet | None = None,
) -> RoughAlternativeSummaryArtifact:
    route_families = route_families or build_route_family_artifact(route_survey)
    cases = [
        _rough_case_for_route(
            config,
            route,
            market,
            route_families,
            unit_train_candidates,
        )
        for route in route_survey.routes
    ]
    rows = [
        "| Route | Family | Blueprint steps | Separation duties | Recycle intents | Heating (kW) | Cooling (kW) | CAPEX (INR bn) | Utility OPEX (INR bn/y) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        rows.append(
            f"| {case.route_id} | {case.route_family_label} | {case.blueprint_step_count} | {case.separation_duty_count} | "
            f"{case.recycle_intent_count} | {case.estimated_heating_kw:.1f} | {case.estimated_cooling_kw:.1f} | "
            f"{case.estimated_capex_inr / 1e9:.2f} | {case.estimated_annual_utility_cost_inr / 1e9:.2f} |"
        )
    return RoughAlternativeSummaryArtifact(
        cases=cases,
        markdown=(
            "Rough alternative balances and duties convert each route architecture into first-pass utility and cost intensity. "
            "When a route-derived blueprint exists, the screening now uses mapped step count, separation duty count, and recycle intent count instead of only family defaults.\n\n"
            + "\n".join(rows)
        ),
        citations=sorted(set(route_survey.citations + synthesis.citations + market.citations)),
        assumptions=synthesis.assumptions + ["Rough alternative duties are used for early process architecture and heat-integration ranking, not final equipment design."],
    )


def _build_heat_streams(case: RoughAlternativeCase) -> list[HeatStream]:
    route_id = case.route_id
    signature = _family_heat_signature(case)
    hot_streams = [
        HeatStream(
            stream_id=f"{route_id}_hot_reactor",
            name="Reactor exotherm",
            kind="hot",
            source_unit_id="R-rough",
            supply_temp_c=signature["reactor_hot_supply_c"],
            target_temp_c=signature["reactor_hot_target_c"],
            duty_kw=round(case.estimated_cooling_kw * 0.62, 3),
            notes="Dominant recoverable hot stream from reactor or hydrolyzer section.",
            citations=case.citations,
            assumptions=case.assumptions,
        ),
        HeatStream(
            stream_id=f"{route_id}_hot_condensing",
            name="Condensing overhead / hot product stream",
            kind="hot",
            source_unit_id="D-rough",
            supply_temp_c=signature["condensing_hot_supply_c"],
            target_temp_c=60.0,
            duty_kw=round(case.estimated_cooling_kw * 0.38, 3),
            notes="Secondary hot stream available for feed and water preheat.",
            citations=case.citations,
            assumptions=case.assumptions,
        ),
    ]
    cold_streams = [
        HeatStream(
            stream_id=f"{route_id}_cold_reboiler",
            name="Primary dehydration / reboiler duty",
            kind="cold",
            source_unit_id="D-rough",
            supply_temp_c=signature["reboiler_cold_supply_c"],
            target_temp_c=signature["reboiler_cold_target_c"],
            duty_kw=round(case.estimated_heating_kw * 0.78, 3),
            notes="Largest cold sink and first target for heat recovery.",
            citations=case.citations,
            assumptions=case.assumptions,
        ),
        HeatStream(
            stream_id=f"{route_id}_cold_feed",
            name="Feed and recycle preheat",
            kind="cold",
            source_unit_id="E-rough",
            supply_temp_c=30.0,
            target_temp_c=signature["feed_cold_target_c"],
            duty_kw=round(case.estimated_heating_kw * 0.22, 3),
            notes="Secondary cold sink for direct or indirect recovery.",
            citations=case.citations,
            assumptions=case.assumptions,
        ),
    ]
    return hot_streams + cold_streams


def _selected_case(cases: list[HeatIntegrationCase], selected_case_id: str | None) -> HeatIntegrationCase | None:
    if not selected_case_id:
        return None
    for item in cases:
        if item.case_id == selected_case_id:
            return item
    return None


def selected_heat_case(utility_network_decision: UtilityNetworkDecision | None) -> HeatIntegrationCase | None:
    if utility_network_decision is None:
        return None
    return _selected_case(utility_network_decision.cases, utility_network_decision.selected_case_id)


def _build_heat_cases(config: ProjectConfig, case: RoughAlternativeCase, market, heat_streams: list[HeatStream]) -> tuple[UtilityTarget, list[HeatIntegrationCase], DecisionRecord]:
    steam_price = _price_lookup(market.india_price_data, "Steam", 1.8)
    cooling_water_price = _price_lookup(market.india_price_data, "Cooling water", 8.0)
    annual_hours = operating_hours_per_year(config.basis)
    base_hot = case.estimated_heating_kw
    base_cold = case.estimated_cooling_kw
    signature = _family_heat_signature(case)
    recoverable = min(base_hot, base_cold) * signature["recoverability"]
    pinch_temp = signature["pinch_temp_c"]
    utility_target = UtilityTarget(
        base_hot_utility_kw=round(base_hot, 3),
        base_cold_utility_kw=round(base_cold, 3),
        minimum_hot_utility_kw=round(max(base_hot - recoverable, 0.0), 3),
        minimum_cold_utility_kw=round(max(base_cold - recoverable * 0.95, 0.0), 3),
        recoverable_duty_kw=round(recoverable, 3),
        pinch_temp_c=pinch_temp,
        calc_traces=[
            CalcTrace(
                trace_id=f"{case.route_id}_pinch_recoverable",
                title="Recoverable duty target",
                formula="Qrec = min(Qhot, Qcold) * recoverability",
                substitutions={"Qhot": f"{base_cold:.3f} kW", "Qcold": f"{base_hot:.3f} kW"},
                result=f"{recoverable:.3f}",
                units="kW",
                notes="Pinch-style first-pass targeting for conceptual utility minimization.",
            )
        ],
        citations=case.citations,
        assumptions=case.assumptions,
    )

    def annual_savings_for_recovered_duty(recovered_kw: float) -> float:
        steam_saved = recovered_kw * 3600.0 / 2200.0 * steam_price * annual_hours
        cooling_saved = recovered_kw * 3600.0 / (4.18 * 10.0 * 1000.0) * cooling_water_price * annual_hours * 0.85
        return steam_saved + cooling_saved

    direct_possible = (
        max(stream.supply_temp_c for stream in heat_streams if stream.kind == "hot")
        - min(stream.target_temp_c for stream in heat_streams if stream.kind == "cold")
        >= config.heat_integration.min_approach_temp_c
    )
    no_recovery = HeatIntegrationCase(
        case_id=f"{case.route_id}_no_recovery",
        title="No recovery",
        recovered_duty_kw=0.0,
        residual_hot_utility_kw=round(base_hot, 3),
        residual_cold_utility_kw=round(base_cold, 3),
        added_capex_inr=0.0,
        annual_savings_inr=0.0,
        payback_years=0.0,
        operability_penalty=0.0,
        safety_penalty=0.0,
        feasible=True,
        summary="All heating duty is met with purchased utility.",
        citations=case.citations,
        assumptions=case.assumptions,
    )
    multi_effect_recovered = min(recoverable * signature["multi_effect_fraction"], base_hot)
    multi_effect_capex = signature["multi_effect_capex_inr"]
    multi_effect_savings = annual_savings_for_recovered_duty(multi_effect_recovered)
    multi_effect = HeatIntegrationCase(
        case_id=f"{case.route_id}_multi_effect",
        title="Multi-effect only",
        recovered_duty_kw=round(multi_effect_recovered, 3),
        residual_hot_utility_kw=round(max(base_hot - multi_effect_recovered, 0.0), 3),
        residual_cold_utility_kw=round(max(base_cold - multi_effect_recovered * 0.9, 0.0), 3),
        added_capex_inr=multi_effect_capex,
        annual_savings_inr=round(multi_effect_savings, 2),
        payback_years=round(multi_effect_capex / max(multi_effect_savings, 1.0), 3),
        operability_penalty=6.0,
        safety_penalty=2.0,
        feasible=multi_effect_recovered >= config.heat_integration.min_recoverable_duty_kw * 0.4,
        heat_matches=[
            HeatMatch(
                match_id=f"{case.route_id}_me_feed",
                hot_stream_id=f"{case.route_id}_hot_condensing",
                cold_stream_id=f"{case.route_id}_cold_feed",
                recovered_duty_kw=round(multi_effect_recovered * 0.35, 3),
                direct=True,
                medium="direct",
                min_approach_temp_c=config.heat_integration.min_approach_temp_c,
                notes="Condensing and recycle heat used for feed and evaporator preheat.",
                citations=case.citations,
                assumptions=case.assumptions,
            )
        ],
        summary="Uses staged evaporation and simple feed preheat to reduce fresh steam.",
        citations=case.citations,
        assumptions=case.assumptions,
    )
    htm_recovered = min(recoverable * signature["htm_fraction"], base_hot)
    htm_capex = signature["htm_capex_inr"]
    htm_savings = annual_savings_for_recovered_duty(htm_recovered)
    htm_case = HeatIntegrationCase(
        case_id=f"{case.route_id}_pinch_htm",
        title="Pinch + HTM loop",
        recovered_duty_kw=round(htm_recovered, 3),
        residual_hot_utility_kw=round(max(base_hot - htm_recovered, 0.0), 3),
        residual_cold_utility_kw=round(max(base_cold - htm_recovered * 0.92, 0.0), 3),
        added_capex_inr=htm_capex,
        annual_savings_inr=round(htm_savings, 2),
        payback_years=round(htm_capex / max(htm_savings, 1.0), 3),
        operability_penalty=14.0,
        safety_penalty=8.0,
        feasible=(
            config.heat_integration.allow_htm_loops
            and _supports_htm_topology(case)
            and htm_recovered >= config.heat_integration.min_recoverable_duty_kw
            and direct_possible
        ),
        heat_matches=[
            HeatMatch(
                match_id=f"{case.route_id}_htm_reboiler",
                hot_stream_id=f"{case.route_id}_hot_reactor",
                cold_stream_id=f"{case.route_id}_cold_reboiler",
                recovered_duty_kw=round(htm_recovered * 0.72, 3),
                direct=False,
                medium="Dowtherm A",
                min_approach_temp_c=config.heat_integration.min_approach_temp_c,
                notes="Indirect hot-oil loop buffers reactor exotherm into the principal reboiler.",
                citations=case.citations,
                assumptions=case.assumptions,
            ),
            HeatMatch(
                match_id=f"{case.route_id}_htm_feed",
                hot_stream_id=f"{case.route_id}_hot_condensing",
                cold_stream_id=f"{case.route_id}_cold_feed",
                recovered_duty_kw=round(htm_recovered * 0.18, 3),
                direct=True,
                medium="direct",
                min_approach_temp_c=config.heat_integration.min_approach_temp_c,
                notes="Secondary recovery used for feed and recycle preheat.",
                citations=case.citations,
                assumptions=case.assumptions,
            ),
        ],
        summary="Pinch-based heat recovery with an indirect hot-oil loop materially reduces purchased steam.",
        citations=case.citations,
        assumptions=case.assumptions,
    )
    cases = [no_recovery, multi_effect, htm_case]

    criteria = [
        DecisionCriterion(name="Annual utility savings", weight=0.45, justification="Heat recovery must materially reduce India utility burden."),
        DecisionCriterion(name="Added CAPEX", weight=0.20, direction="minimize", justification="Recovery hardware should not erase OPEX gains."),
        DecisionCriterion(name="Operability", weight=0.20, direction="minimize", justification="Complex loop architectures carry control and maintenance burden."),
        DecisionCriterion(name="Safety", weight=0.15, direction="minimize", justification="Indirect high-temperature loops add hazard and containment requirements."),
    ]
    scenario_scores: dict[str, str] = {}
    viable_cases = [item for item in cases if item.feasible]
    base_case_ranking: list[tuple[float, HeatIntegrationCase]] = []
    conservative_ranking: list[tuple[float, HeatIntegrationCase]] = []
    for item in viable_cases:
        annualized_capex = item.added_capex_inr / 6.0
        base_score = item.annual_savings_inr - annualized_capex - (item.operability_penalty + item.safety_penalty) * 1_000_000.0
        conservative_savings = item.annual_savings_inr * 1.20
        conservative_score = conservative_savings - annualized_capex * 1.05 - (item.operability_penalty + item.safety_penalty) * 1_000_000.0
        scenario_scores[item.case_id] = f"{base_score:.2f}"
        base_case_ranking.append((base_score, item))
        conservative_ranking.append((conservative_score, item))
    base_case_ranking.sort(key=lambda pair: pair[0], reverse=True)
    conservative_ranking.sort(key=lambda pair: pair[0], reverse=True)
    selected_case = base_case_ranking[0][1] if base_case_ranking else no_recovery
    conservative_selected = conservative_ranking[0][1] if conservative_ranking else selected_case
    stability = (
        ScenarioStability.STABLE
        if selected_case.case_id == conservative_selected.case_id
        else ScenarioStability.BORDERLINE
    )
    second_best_gap = 1.0
    if len(base_case_ranking) > 1:
        top = base_case_ranking[0][0]
        runner_up = base_case_ranking[1][0]
        second_best_gap = abs(top - runner_up) / max(abs(top), 1.0)
    decision = DecisionRecord(
        decision_id=f"heat_integration_{case.route_id}",
        context=f"Heat-integration choice for {case.route_name}",
        criteria=criteria,
        alternatives=[
            AlternativeOption(
                candidate_id=item.case_id,
                candidate_type="heat_integration",
                description=item.title,
                outputs={
                    "recovered_duty_kw": f"{item.recovered_duty_kw:.3f}",
                    "annual_savings_inr": f"{item.annual_savings_inr:.2f}",
                    "added_capex_inr": f"{item.added_capex_inr:.2f}",
                },
                rejected_reasons=[] if item.feasible else ["Thermal level or recoverable-duty threshold not met."],
                score_breakdown={"net_savings_proxy": float(scenario_scores.get(item.case_id, "0.0"))},
                total_score=float(scenario_scores.get(item.case_id, "0.0")),
                feasible=item.feasible,
                citations=item.citations,
                assumptions=item.assumptions,
            )
            for item in cases
        ],
        selected_candidate_id=selected_case.case_id,
        selected_summary=selected_case.summary,
        hard_constraint_results=[
            f"Base hot utility: {base_hot:.3f} kW",
            f"Recoverable-duty trigger: {config.heat_integration.min_recoverable_duty_kw:.1f} kW",
        ],
        confidence=0.86 if stability == ScenarioStability.STABLE else 0.68,
        scenario_stability=stability,
        approval_required=stability != ScenarioStability.STABLE or second_best_gap < 0.05 or selected_case.case_id.endswith("pinch_htm"),
        citations=case.citations + market.citations,
        assumptions=case.assumptions + ["Heat-integration ranking uses annual savings minus annualized CAPEX and fixed operability/safety penalties."],
    )
    return utility_target, cases, decision


def build_utility_basis_decision(
    config: ProjectConfig,
    site_selection: SiteSelectionArtifact,
    utility_network_decision: UtilityNetworkDecision,
    citations: list[str],
    assumptions: list[str],
) -> tuple[UtilityBasis, DecisionRecord]:
    selected_case = selected_heat_case(utility_network_decision)
    residual_hot = selected_case.residual_hot_utility_kw if selected_case else utility_network_decision.utility_target.base_hot_utility_kw
    htm_enabled = bool(selected_case and selected_case.case_id.endswith("pinch_htm"))
    candidate_specs = [
        {
            "candidate_id": "mp_steam_15bar",
            "description": "15 bar medium-pressure steam and conventional utility header",
            "steam_pressure_bar": 15.0,
            "steam_cost_inr_per_kg": 1.65,
            "cooling_water_cost_inr_per_m3": 8.2,
            "power_cost_inr_per_kwh": 8.4,
            "thermal_fit": 58.0 if residual_hot > 12000.0 else 74.0,
            "tariff_realism": 87.0,
            "operability": 86.0,
            "integration_fit": 54.0 if htm_enabled else 72.0,
        },
        {
            "candidate_id": "hp_steam_20bar",
            "description": "20 bar high-pressure steam basis with integrated recovery support",
            "steam_pressure_bar": 20.0,
            "steam_cost_inr_per_kg": 1.80,
            "cooling_water_cost_inr_per_m3": 8.0,
            "power_cost_inr_per_kwh": 8.5,
            "thermal_fit": 92.0 if residual_hot > 5000.0 else 84.0,
            "tariff_realism": 91.0,
            "operability": 88.0,
            "integration_fit": 92.0 if htm_enabled else 86.0,
        },
        {
            "candidate_id": "htm_assisted_25bar",
            "description": "25 bar steam header with hotter utility backbone for HTM-backed recovery",
            "steam_pressure_bar": 25.0,
            "steam_cost_inr_per_kg": 1.95,
            "cooling_water_cost_inr_per_m3": 7.9,
            "power_cost_inr_per_kwh": 8.65,
            "thermal_fit": 95.0 if htm_enabled else 79.0,
            "tariff_realism": 76.0,
            "operability": 73.0,
            "integration_fit": 89.0 if htm_enabled else 68.0,
        },
    ]
    criteria = [
        DecisionCriterion(name="Thermal fit", weight=0.35, justification="Steam level must match the residual duty after route-level recovery."),
        DecisionCriterion(name="Tariff realism", weight=0.25, justification="Selected tariffs should remain defensible for India preliminary screening."),
        DecisionCriterion(name="Operability", weight=0.20, justification="The utility basis should avoid unnecessary control and maintenance burden."),
        DecisionCriterion(name="Integration compatibility", weight=0.20, justification="Selected utility level must support the chosen heat-recovery architecture."),
    ]
    alternatives: list[AlternativeOption] = []
    ranking: list[tuple[float, str]] = []
    for candidate in candidate_specs:
        total_score = (
            0.35 * candidate["thermal_fit"]
            + 0.25 * candidate["tariff_realism"]
            + 0.20 * candidate["operability"]
            + 0.20 * candidate["integration_fit"]
        )
        alternatives.append(
            AlternativeOption(
                candidate_id=candidate["candidate_id"],
                candidate_type="utility_basis",
                description=candidate["description"],
                outputs={
                    "steam_pressure_bar": f"{candidate['steam_pressure_bar']:.1f}",
                    "steam_cost_inr_per_kg": f"{candidate['steam_cost_inr_per_kg']:.2f}",
                    "cooling_water_cost_inr_per_m3": f"{candidate['cooling_water_cost_inr_per_m3']:.2f}",
                    "power_cost_inr_per_kwh": f"{candidate['power_cost_inr_per_kwh']:.2f}",
                },
                score_breakdown={
                    "Thermal fit": candidate["thermal_fit"],
                    "Tariff realism": candidate["tariff_realism"],
                    "Operability": candidate["operability"],
                    "Integration compatibility": candidate["integration_fit"],
                },
                total_score=round(total_score, 3),
                feasible=True,
                citations=citations,
                assumptions=assumptions,
            )
        )
        ranking.append((total_score, candidate["candidate_id"]))
    ranking.sort(key=lambda pair: pair[0], reverse=True)
    selected_id = ranking[0][1]
    selected = next(item for item in candidate_specs if item["candidate_id"] == selected_id)
    gap = _ranking_gap(ranking)
    basis = UtilityBasis(
        steam_pressure_bar=selected["steam_pressure_bar"],
        steam_cost_inr_per_kg=selected["steam_cost_inr_per_kg"],
        cooling_water_cost_inr_per_m3=selected["cooling_water_cost_inr_per_m3"],
        power_cost_inr_per_kwh=selected["power_cost_inr_per_kwh"],
        calc_traces=[
            CalcTrace(trace_id="ub_selected_steam_cost", title="Selected steam tariff basis", formula=f"Steam cost = {selected['steam_cost_inr_per_kg']:.2f} INR/kg", result=f"{selected['steam_cost_inr_per_kg']:.2f}", units="INR/kg"),
            CalcTrace(trace_id="ub_selected_cw_cost", title="Selected cooling-water tariff basis", formula=f"Cooling-water cost = {selected['cooling_water_cost_inr_per_m3']:.2f} INR/m3", result=f"{selected['cooling_water_cost_inr_per_m3']:.2f}", units="INR/m3"),
            CalcTrace(trace_id="ub_selected_power_cost", title="Selected power tariff basis", formula=f"Power cost = {selected['power_cost_inr_per_kwh']:.2f} INR/kWh", result=f"{selected['power_cost_inr_per_kwh']:.2f}", units="INR/kWh"),
        ],
        value_records=[
            make_value_record("utility_steam_pressure", "Steam pressure", selected["steam_pressure_bar"], "bar", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("utility_steam_cost", "Steam cost", selected["steam_cost_inr_per_kg"], "INR/kg", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("utility_cw_cost", "Cooling-water cost", selected["cooling_water_cost_inr_per_m3"], "INR/m3", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("utility_power_cost", "Power cost", selected["power_cost_inr_per_kwh"], "INR/kWh", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + [f"Utility basis is selected for {site_selection.selected_site} using route-level recovery and India tariff realism."],
    )
    decision = DecisionRecord(
        decision_id="utility_basis",
        context=f"Utility basis for {site_selection.selected_site}",
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id=selected_id,
        selected_summary=f"{selected['description']} is selected because it best balances thermal fit, India tariff realism, and compatibility with the chosen recovery case.",
        hard_constraint_results=[f"Residual hot utility to be supplied: {residual_hot:.1f} kW"],
        confidence=0.89 if gap >= 0.08 else 0.70,
        scenario_stability=ScenarioStability.STABLE if gap >= 0.08 else ScenarioStability.BORDERLINE,
        approval_required=gap < 0.05,
        citations=citations,
        assumptions=assumptions + ["Utility basis ranking is deterministic and depends on residual utility demand after the selected heat-integration case."],
    )
    return basis, decision


def _utility_scenario_results(config: ProjectConfig, market, annual_revenue_inr: float, base_total_opex_inr: float, selected_case: HeatIntegrationCase) -> list[ScenarioResult]:
    steam_price = _price_lookup(market.india_price_data, "Steam", 1.8)
    cooling_water_price = _price_lookup(market.india_price_data, "Cooling water", 8.0)
    annual_hours = operating_hours_per_year(config.basis)
    results: list[ScenarioResult] = []
    for scenario in config.scenario_policy.cases:
        annual_utility_cost = (
            selected_case.residual_hot_utility_kw * 3600.0 / 2200.0 * steam_price * scenario.steam_price_multiplier * annual_hours
            + selected_case.residual_cold_utility_kw * 3600.0 / (4.18 * 10.0 * 1000.0) * cooling_water_price * scenario.power_price_multiplier * annual_hours * 0.85
        )
        annual_opex = base_total_opex_inr - selected_case.annual_savings_inr + annual_utility_cost
        annual_revenue = annual_revenue_inr * scenario.selling_price_multiplier
        results.append(
            ScenarioResult(
                scenario_name=scenario.name,
                annual_utility_cost_inr=round(annual_utility_cost, 2),
                annual_operating_cost_inr=round(annual_opex, 2),
                annual_revenue_inr=round(annual_revenue, 2),
                gross_margin_inr=round(annual_revenue - annual_opex, 2),
                selected=scenario.name == "base",
            )
        )
    return results


def build_heat_integration_study(config: ProjectConfig, rough_summary: RoughAlternativeSummaryArtifact, market) -> HeatIntegrationStudyArtifact:
    annual_revenue_inr = hourly_output_kg(config.basis) * operating_hours_per_year(config.basis) * market.estimated_price_per_kg
    route_decisions: list[UtilityNetworkDecision] = []
    markdown_rows = [
        "| Route | Selected case | Recovered duty (kW) | Residual hot utility (kW) | Savings (INR bn/y) | Payback (y) | Stability |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in rough_summary.cases:
        heat_streams = _build_heat_streams(case)
        utility_target, heat_cases, decision = _build_heat_cases(config, case, market, heat_streams)
        selected_case = _selected_case(heat_cases, decision.selected_candidate_id) or heat_cases[0]
        scenario_results = _utility_scenario_results(config, market, annual_revenue_inr, case.estimated_annual_total_opex_inr, selected_case)
        route_decision = UtilityNetworkDecision(
            route_id=case.route_id,
            utility_target=utility_target,
            heat_streams=heat_streams,
            cases=heat_cases,
            decision=decision,
            selected_case_id=selected_case.case_id,
            base_annual_utility_cost_inr=case.estimated_annual_utility_cost_inr,
            selected_annual_utility_cost_inr=next((item.annual_utility_cost_inr for item in scenario_results if item.selected), case.estimated_annual_utility_cost_inr),
            scenario_results=scenario_results,
            markdown=f"Selected case for {case.route_name}: {selected_case.title}. {selected_case.summary}",
            citations=case.citations + market.citations,
            assumptions=case.assumptions + decision.assumptions,
        )
        route_decisions.append(route_decision)
        markdown_rows.append(
            f"| {case.route_id} | {selected_case.title} | {selected_case.recovered_duty_kw:.1f} | {selected_case.residual_hot_utility_kw:.1f} | {selected_case.annual_savings_inr / 1e9:.2f} | {selected_case.payback_years:.2f} | {decision.scenario_stability.value} |"
        )
    markdown = (
        "The heat-integration study evaluates no-recovery, multi-effect, and pinch/HTM-loop cases before final route choice. "
        "Routes that remain utility-heavy after recovery are penalized in downstream economics.\n\n"
        + "\n".join(markdown_rows)
    )
    return HeatIntegrationStudyArtifact(
        route_decisions=route_decisions,
        markdown=markdown,
        citations=rough_summary.citations,
        assumptions=rough_summary.assumptions + ["Heat-integration cases are route-specific and feed the final route choice."],
    )


def build_economic_basis_decision(
    config: ProjectConfig,
    site_selection: SiteSelectionArtifact,
    utility_network_decision: UtilityNetworkDecision,
    cost_model: CostModel,
    financial_model: FinancialModel,
    utility_basis_decision: DecisionRecord | None = None,
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None = None,
) -> DecisionRecord:
    selected_case = selected_heat_case(utility_network_decision)
    blueprint_step_count, separation_duty_count, recycle_intent_count, batch_capable = _blueprint_complexity_metrics(flowsheet_blueprint)
    base_revenue = financial_model.annual_revenue
    base_margin = financial_model.gross_profit
    base_payback = financial_model.payback_years
    base_utility = cost_model.annual_utility_cost
    no_recovery_utility = utility_network_decision.base_annual_utility_cost_inr
    no_recovery_opex = cost_model.annual_opex - base_utility + no_recovery_utility
    no_recovery_margin = base_revenue - no_recovery_opex
    no_recovery_capex = max(cost_model.total_capex - cost_model.integration_capex_inr, 1.0)
    no_recovery_payback = (no_recovery_capex + financial_model.working_capital) / max(no_recovery_margin, 1.0)
    conservative = next((item for item in financial_model.scenario_results if item.scenario_name == "conservative"), None)
    conservative_margin = conservative.gross_margin_inr if conservative else base_margin * 0.90
    conservative_opex = conservative.annual_operating_cost_inr if conservative else cost_model.annual_opex * 1.10
    conservative_payback = (cost_model.total_capex + financial_model.working_capital) / max(conservative_margin, 1.0)
    criteria = [
        DecisionCriterion(name="Gross margin", weight=0.40, justification="Economic basis should preserve material gross margin in India operation."),
        DecisionCriterion(name="Payback", weight=0.25, direction="minimize", justification="Selected basis should retain an acceptable screening payback."),
        DecisionCriterion(name="India grounding", weight=0.20, justification="Site, utility, and price basis must remain India-grounded and cited."),
        DecisionCriterion(name="Scenario resilience", weight=0.15, justification="The chosen case should remain credible under conservative assumptions."),
    ]
    margin_scores = _normalize_scores(
        {
            "selected_integrated_base": base_margin,
            "no_recovery_counterfactual": no_recovery_margin,
            "conservative_case": conservative_margin,
        }
    )
    payback_scores = _normalize_scores(
        {
            "selected_integrated_base": base_payback,
            "no_recovery_counterfactual": no_recovery_payback,
            "conservative_case": conservative_payback,
        },
        reverse=True,
    )
    resilience_scores = {
        "selected_integrated_base": 92.0 if conservative_margin > 0 else 58.0,
        "no_recovery_counterfactual": 62.0 if no_recovery_margin > 0 else 24.0,
        "conservative_case": 78.0 if conservative_margin > 0 else 35.0,
    }
    india_grounding = {
        "selected_integrated_base": 94.0,
        "no_recovery_counterfactual": 88.0,
        "conservative_case": 92.0,
    }
    if flowsheet_blueprint is not None:
        complexity_penalty = min(
            max(blueprint_step_count - 5, 0) * 1.2 + separation_duty_count * 1.0 + recycle_intent_count * 0.8,
            10.0,
        )
        if batch_capable:
            complexity_penalty += 2.0
        india_grounding["selected_integrated_base"] = max(india_grounding["selected_integrated_base"] - complexity_penalty * 0.35, 70.0)
        india_grounding["conservative_case"] = max(india_grounding["conservative_case"] - complexity_penalty * 0.25, 68.0)
        resilience_scores["selected_integrated_base"] = max(resilience_scores["selected_integrated_base"] - complexity_penalty * 0.60, 40.0)
        resilience_scores["conservative_case"] = max(resilience_scores["conservative_case"] - complexity_penalty * 0.45, 32.0)
        resilience_scores["no_recovery_counterfactual"] = max(resilience_scores["no_recovery_counterfactual"] - complexity_penalty * 0.25, 20.0)
    alt_specs = [
        {
            "candidate_id": "selected_integrated_base",
            "description": (
                f"Selected India base case at {site_selection.selected_site} with {selected_case.title if selected_case else 'selected recovery'}"
                + (
                    f"; blueprint basis = {blueprint_step_count} steps, {separation_duty_count} separations, {recycle_intent_count} recycle loops"
                    if flowsheet_blueprint is not None
                    else ""
                )
            ),
            "gross_margin": base_margin,
            "payback": base_payback,
            "feasible": True,
        },
        {
            "candidate_id": "no_recovery_counterfactual",
            "description": "Same site and route basis without selected heat-integration savings",
            "gross_margin": no_recovery_margin,
            "payback": no_recovery_payback,
            "feasible": True,
        },
        {
            "candidate_id": "conservative_case",
            "description": "Selected architecture under conservative India scenario multipliers",
            "gross_margin": conservative_margin,
            "payback": conservative_payback,
            "feasible": True,
        },
    ]
    alternatives: list[AlternativeOption] = []
    ranking: list[tuple[float, str]] = []
    for spec in alt_specs:
        candidate_id = spec["candidate_id"]
        total_score = (
            0.40 * margin_scores[candidate_id]
            + 0.25 * payback_scores[candidate_id]
            + 0.20 * india_grounding[candidate_id]
            + 0.15 * resilience_scores[candidate_id]
        )
        alternatives.append(
            AlternativeOption(
                candidate_id=candidate_id,
                candidate_type="economic_basis",
                description=spec["description"],
                outputs={
                    "gross_margin_inr": f"{spec['gross_margin']:.2f}",
                    "payback_years": f"{spec['payback']:.3f}",
                    "site": site_selection.selected_site,
                    "heat_case": selected_case.case_id if selected_case else "n/a",
                    "utility_basis": utility_basis_decision.selected_candidate_id if utility_basis_decision else "n/a",
                    "blueprint_steps": str(blueprint_step_count),
                    "recycle_intents": str(recycle_intent_count),
                    "batch_capable": "yes" if batch_capable else "no",
                },
                rejected_reasons=[] if spec["gross_margin"] > 0 else ["Gross margin is non-positive under this basis and needs analyst review."],
                score_breakdown={
                    "Gross margin": margin_scores[candidate_id],
                    "Payback": payback_scores[candidate_id],
                    "India grounding": india_grounding[candidate_id],
                    "Scenario resilience": resilience_scores[candidate_id],
                },
                total_score=round(total_score, 3),
                feasible=spec["feasible"],
                citations=cost_model.citations + financial_model.citations + site_selection.citations,
                assumptions=cost_model.assumptions + financial_model.assumptions,
            )
        )
        if spec["feasible"]:
            ranking.append((total_score, candidate_id))
    ranking.sort(key=lambda pair: pair[0], reverse=True)
    if not ranking:
        selected_id = "selected_integrated_base"
        stability = ScenarioStability.UNSTABLE
        confidence = 0.45
    else:
        selected_id = ranking[0][1]
        stability = ScenarioStability.STABLE if conservative_margin > 0 and selected_id == "selected_integrated_base" else ScenarioStability.BORDERLINE if conservative_margin > 0 else ScenarioStability.UNSTABLE
        confidence = 0.88 if stability == ScenarioStability.STABLE else 0.67 if stability == ScenarioStability.BORDERLINE else 0.45
    gap = _ranking_gap(ranking)
    return DecisionRecord(
        decision_id="economic_basis",
        context="India economic basis selection",
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id=selected_id,
        selected_summary=(
            f"The selected India economic basis keeps {site_selection.selected_site} and the chosen recovery case `{selected_case.case_id if selected_case else 'n/a'}` because it provides the strongest defendable margin and payback."
            + (
                f" The selected blueprint carries {blueprint_step_count} mapped steps, {separation_duty_count} separation duties, and {recycle_intent_count} recycle intents."
                if flowsheet_blueprint is not None
                else ""
            )
        ),
        hard_constraint_results=[
            f"Selected route: {cost_model.selected_route_id or utility_network_decision.route_id}",
            f"Selected heat case: {selected_case.case_id if selected_case else 'n/a'}",
            f"India currency basis: {cost_model.currency}",
            *(
                [
                    f"Blueprint steps: {blueprint_step_count}",
                    f"Blueprint separation duties: {separation_duty_count}",
                    f"Blueprint recycle intents: {recycle_intent_count}",
                    f"Batch-capable blueprint: {'yes' if batch_capable else 'no'}",
                ]
                if flowsheet_blueprint is not None
                else []
            ),
        ],
        confidence=confidence,
        scenario_stability=stability,
        approval_required=stability != ScenarioStability.STABLE or gap < 0.05,
        citations=cost_model.citations + financial_model.citations + site_selection.citations,
        assumptions=cost_model.assumptions + financial_model.assumptions + [
            "Economic basis compares the integrated base case against no-recovery and conservative counterfactuals.",
            *(
                [
                    "Route-derived blueprint complexity is folded into economic-basis grounding and scenario-resilience screening."
                ]
                if flowsheet_blueprint is not None
                else []
            ),
        ],
    )


def select_route_architecture(
    config: ProjectConfig,
    route_survey: RouteSurveyArtifact,
    route_chemistry: RouteChemistryArtifact | None,
    rough_summary: RoughAlternativeSummaryArtifact,
    heat_study: HeatIntegrationStudyArtifact,
    market,
    route_families: RouteFamilyArtifact | None = None,
) -> tuple[RouteSelectionArtifact, DecisionRecord, DecisionRecord, DecisionRecord, UtilityNetworkDecision]:
    routes_by_id = {route.route_id: route for route in route_survey.routes}
    route_graphs = {graph.route_id: graph for graph in route_chemistry.route_graphs} if route_chemistry is not None else {}
    rough_by_route = {case.route_id: case for case in rough_summary.cases}
    utility_by_route = {decision.route_id: decision for decision in heat_study.route_decisions}
    route_families = route_families or build_route_family_artifact(route_survey)
    revenue_base = hourly_output_kg(config.basis) * operating_hours_per_year(config.basis) * market.estimated_price_per_kg

    utility_scores = _normalize_scores(
        {
            route_id: utility.selected_annual_utility_cost_inr
            for route_id, utility in utility_by_route.items()
        },
        reverse=True,
    )
    capex_scores = _normalize_scores(
        {
            route_id: rough_by_route[route_id].estimated_capex_inr + (selected_heat_case(utility_by_route[route_id]).added_capex_inr if selected_heat_case(utility_by_route[route_id]) else 0.0)
            for route_id in rough_by_route
        },
        reverse=True,
    )
    margin_scores: dict[str, float] = {}
    for route_id, rough_case in rough_by_route.items():
        utility = utility_by_route[route_id]
        selected_case = selected_heat_case(utility)
        effective_opex = rough_case.estimated_annual_total_opex_inr - (selected_case.annual_savings_inr if selected_case else 0.0)
        margin_scores[route_id] = revenue_base - effective_opex
    economic_scores = _normalize_scores(margin_scores)
    criteria = [
        DecisionCriterion(name="Economic margin", weight=0.20, justification="Selected route must preserve gross margin after heat-integration choice."),
        DecisionCriterion(name="Utility intensity", weight=0.18, justification="Residual purchased utility is critical in India-mode economics."),
        DecisionCriterion(name="CAPEX intensity", weight=0.15, direction="minimize", justification="Route and recovery case should avoid excessive capital burden."),
        DecisionCriterion(name="Industrial maturity", weight=0.12, justification="Proven industrial precedent reduces decision risk."),
        DecisionCriterion(name="Selectivity", weight=0.13, justification="Higher selectivity reduces downstream purification burden."),
        DecisionCriterion(name="India fit", weight=0.07, justification="Feedstock, cluster fit, and byproduct handling must align with India deployment."),
        DecisionCriterion(name="Evidence quality", weight=0.08, justification="Documented or literature-backed routes should outrank generic fallbacks."),
        DecisionCriterion(name="Chemistry completeness", weight=0.07, justification="Routes with named, non-anonymous core species are required for adaptive synthesis."),
    ]
    alternatives: list[AlternativeOption] = []
    base_ranking: list[tuple[float, str]] = []
    conservative_ranking: list[tuple[float, str]] = []
    for route_id, route in routes_by_id.items():
        profile = _route_profile(route, route_families)
        graph = route_graphs.get(route_id)
        block_reason = _route_regulatory_block(profile)
        selected_case = selected_heat_case(utility_by_route[route_id])
        if selected_case is None:
            continue
        rough_case = rough_by_route[route_id]
        maturity = profile.maturity_score
        selectivity = route.selectivity_fraction * 100.0
        india_fit = profile.india_fit_score + _route_byproduct_credit(route)
        evidence_quality = max(route.evidence_score, 0.25) * 100.0
        chemistry_completeness = (
            graph.chemistry_completeness_score if graph is not None else route.chemistry_completeness_score
        ) * 100.0
        core_species_blocked = route_chemistry is not None and route_id in route_chemistry.blocking_route_ids
        major_separation_defined = bool(rough_case.separation_train or profile.primary_separation_train or route.separations)
        hazard_support_gap = any(hazard.severity == "high" for hazard in route.hazards) and evidence_quality < 55.0
        rejection_reasons = list(route.route_rejection_reasons)
        if block_reason:
            rejection_reasons.append(block_reason)
        rejection_reasons.extend(profile.critic_flags[:2])
        if core_species_blocked:
            rejection_reasons.append("Core route species remain anonymous or unresolved.")
        if not route.core_species_complete:
            rejection_reasons.append("Core route chemistry is incomplete.")
        if not major_separation_defined:
            rejection_reasons.append("Major separations are not defined for this route.")
        if hazard_support_gap:
            rejection_reasons.append("High-hazard route lacks enough evidence support.")
        score_breakdown = {
            "Economic margin": economic_scores[route_id],
            "Utility intensity": utility_scores[route_id],
            "CAPEX intensity": capex_scores[route_id],
            "Industrial maturity": maturity,
            "Selectivity": selectivity,
            "India fit": india_fit,
            "Evidence quality": evidence_quality,
            "Chemistry completeness": chemistry_completeness,
        }
        total_score = (
            0.20 * score_breakdown["Economic margin"]
            + 0.18 * score_breakdown["Utility intensity"]
            + 0.15 * score_breakdown["CAPEX intensity"]
            + 0.12 * maturity
            + 0.13 * selectivity
            + 0.07 * india_fit
            + 0.08 * evidence_quality
            + 0.07 * chemistry_completeness
        )
        if config.preferred_route_id and config.preferred_route_id == route_id:
            total_score += 2.0
        feasible = (
            block_reason is None
            and reaction_is_balanced(route)
            and not core_species_blocked
            and major_separation_defined
            and not hazard_support_gap
        )
        if not feasible:
            total_score = -1.0
        conservative_result = next((item for item in utility_by_route[route_id].scenario_results if item.scenario_name == "conservative"), None)
        conservative_margin = conservative_result.gross_margin_inr if conservative_result else margin_scores[route_id]
        conservative_score = total_score + (conservative_margin - margin_scores[route_id]) / max(abs(revenue_base), 1.0) * 100.0
        alternatives.append(
            AlternativeOption(
                candidate_id=route_id,
                candidate_type="route_selection",
                description=f"{route.name} ({profile.family_label}) with {selected_case.title}",
                outputs={
                    "route_family": profile.route_family_id,
                    "selected_heat_case": selected_case.case_id,
                    "economic_margin_inr": f"{margin_scores[route_id]:.2f}",
                    "residual_hot_utility_kw": f"{selected_case.residual_hot_utility_kw:.3f}",
                    "reactor_basis": rough_case.reactor_class,
                    "separation_train": rough_case.separation_train,
                    "evidence_score": f"{route.evidence_score:.2f}",
                    "chemistry_completeness_score": f"{(chemistry_completeness / 100.0):.2f}",
                    "route_origin": route.route_origin,
                },
                rejected_reasons=rejection_reasons,
                score_breakdown=score_breakdown,
                total_score=round(total_score, 3),
                feasible=feasible,
                citations=route.citations + utility_by_route[route_id].citations,
                assumptions=route.assumptions + utility_by_route[route_id].assumptions + [f"Route family `{profile.route_family_id}` feeds final route ranking."],
            )
        )
        if feasible:
            base_ranking.append((total_score, route_id))
            conservative_ranking.append((conservative_score, route_id))
    base_ranking.sort(key=lambda pair: pair[0], reverse=True)
    conservative_ranking.sort(key=lambda pair: pair[0], reverse=True)
    if not base_ranking:
        raise RuntimeError("No feasible route alternatives remained after decision evaluation.")
    selected_route_id = base_ranking[0][1]
    selected_route = routes_by_id[selected_route_id]
    selected_profile = _route_profile(selected_route, route_families)
    selected_utility = utility_by_route[selected_route_id]
    conservative_route_id = conservative_ranking[0][1] if conservative_ranking else selected_route_id
    scenario_stability = ScenarioStability.STABLE if conservative_route_id == selected_route_id else ScenarioStability.BORDERLINE
    second_gap = 1.0
    if len(base_ranking) > 1:
        second_gap = abs(base_ranking[0][0] - base_ranking[1][0]) / max(abs(base_ranking[0][0]), 1.0)
    route_decision = DecisionRecord(
        decision_id="route_selection",
        context="Final route and process architecture selection",
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id=selected_route_id,
        selected_summary=(
            f"{selected_route.name} is selected within the `{selected_profile.family_label}` family because it combines the strongest "
            "margin, residual utility burden, maturity, evidence quality, chemistry completeness, and India deployment fit under the selected recovery architecture."
        ),
        hard_constraint_results=(
            [f"{profile.route_id}: {profile.india_deployment_blocker}" for profile in route_families.profiles if profile.india_deployment_blocker]
            + ["Selected route must remain atom-balanced."]
        ),
        confidence=0.88 if scenario_stability == ScenarioStability.STABLE else 0.69,
        scenario_stability=scenario_stability,
        approval_required=True,
        citations=selected_route.citations + selected_utility.citations,
        assumptions=selected_route.assumptions + selected_utility.assumptions,
    )
    selected_heat_case_obj = selected_heat_case(selected_utility)
    route_selection_artifact = RouteSelectionArtifact(
        selected_route_id=selected_route_id,
        justification=(
            f"{selected_route.name} is selected because the `{selected_profile.family_label}` route family stays economically competitive after "
            f"the chosen heat-integration case `{selected_heat_case_obj.case_id if selected_heat_case_obj else 'none'}`, while retaining credible "
            "industrial maturity and India fit."
        ),
        comparison_markdown=(
            "| Route | Family | Total score | Residual hot utility (kW) | Heat case | Scenario stability |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            + "\n".join(
                f"| {option.candidate_id} | {option.outputs.get('route_family', 'n/a')} | {option.total_score:.2f} | {option.outputs.get('residual_hot_utility_kw', 'n/a')} | {option.outputs.get('selected_heat_case', 'n/a')} | {route_decision.scenario_stability.value if option.candidate_id == selected_route_id else 'reviewed'} |"
                for option in alternatives
            )
        ),
        citations=selected_route.citations + selected_utility.citations,
        assumptions=route_decision.assumptions,
    )
    reactor_candidate_id = _candidate_id(selected_profile.primary_reactor_class)
    reactor_choice = DecisionRecord(
        decision_id="reactor_choice",
        context="Selected-route reactor choice",
        criteria=[
            DecisionCriterion(name="Heat removal fit", weight=0.40, justification="Reactor type must suit the exothermic duty and chosen recovery strategy."),
            DecisionCriterion(name="Residence-time fit", weight=0.30, justification="Reactor should match the kinetic basis."),
            DecisionCriterion(name="Operability", weight=0.30, justification="Hazard control and steady-state performance matter at EG scale."),
        ],
        alternatives=[
            AlternativeOption(
                candidate_id=reactor_candidate_id,
                candidate_type="reactor_choice",
                description=selected_profile.primary_reactor_class,
                outputs={"selected_route": selected_route_id, "route_family": selected_profile.route_family_id},
                score_breakdown={"Heat removal fit": 92.0, "Residence-time fit": 88.0, "Operability": 82.0},
                total_score=87.8,
                citations=selected_route.citations,
                assumptions=selected_route.assumptions,
            )
        ],
        selected_candidate_id=reactor_candidate_id,
        selected_summary=f"{selected_profile.primary_reactor_class} is retained as the conceptual reactor basis for the selected `{selected_profile.family_label}` route family.",
        confidence=0.84,
        scenario_stability=ScenarioStability.STABLE,
        approval_required=False,
        citations=selected_route.citations,
        assumptions=selected_route.assumptions,
    )
    separation_candidate_id = _candidate_id(selected_profile.primary_separation_train)
    separation_choice = DecisionRecord(
        decision_id="separation_choice",
        context="Selected-route separation choice",
        criteria=[
            DecisionCriterion(name="Purification tractability", weight=0.45, justification="Separation train must achieve product purity without implausible complexity."),
            DecisionCriterion(name="Heat-integration compatibility", weight=0.30, justification="Selected train must expose usable hot/cold sinks."),
            DecisionCriterion(name="India operability", weight=0.25, justification="Train should be realistic for preliminary India-mode design."),
        ],
        alternatives=[
            AlternativeOption(
                candidate_id=separation_candidate_id,
                candidate_type="separation_choice",
                description=selected_profile.primary_separation_train,
                outputs={"selected_route": selected_route_id, "route_family": selected_profile.route_family_id},
                score_breakdown={"Purification tractability": 90.0, "Heat-integration compatibility": 88.0, "India operability": 82.0},
                total_score=87.4,
                citations=selected_route.citations,
                assumptions=selected_route.assumptions,
            )
        ],
        selected_candidate_id=separation_candidate_id,
        selected_summary=f"The separation train `{selected_profile.primary_separation_train}` is selected for the chosen `{selected_profile.family_label}` route family.",
        confidence=0.83,
        scenario_stability=ScenarioStability.STABLE,
        approval_required=False,
        citations=selected_route.citations,
        assumptions=selected_route.assumptions,
    )
    return route_selection_artifact, route_decision, reactor_choice, separation_choice, selected_utility
