from __future__ import annotations

from aoc.models import (
    AlternativeOption,
    DecisionCriterion,
    DecisionRecord,
    MarketAssessmentArtifact,
    MethodSelectionArtifact,
    ProcessArchetype,
    ProjectConfig,
    ResolvedValueArtifact,
    RouteOption,
    ScenarioStability,
    SensitivityLevel,
)


def _technical_strength(config: ProjectConfig) -> float:
    profile = (config.benchmark_profile or config.basis.target_product).lower()
    if "ethylene glycol" in profile or "ethylene_glycol" in profile:
        return 92.0
    if "acetic acid" in profile or "acetic_acid" in profile:
        return 86.0
    if "sulfuric acid" in profile or "sulfuric_acid" in profile:
        return 88.0
    if "sodium bicarbonate" in profile or "sodium_bicarbonate" in profile:
        return 82.0
    return 72.0


def _blocked_value_ids(resolved_values: ResolvedValueArtifact, keywords: tuple[str, ...]) -> list[str]:
    blocked: list[str] = []
    for item in resolved_values.values:
        lowered = item.name.lower()
        if any(keyword in lowered for keyword in keywords) and (
            item.blocking or item.resolution_status == "blocked" or item.sensitivity == SensitivityLevel.HIGH and not item.selected_source_id
        ):
            blocked.append(item.value_id)
    return sorted(set(blocked))


def build_capacity_decision(
    config: ProjectConfig,
    market: MarketAssessmentArtifact,
    resolved_values: ResolvedValueArtifact | None = None,
) -> DecisionRecord:
    candidates = config.capacity_case_candidates or [config.basis.capacity_tpa * factor for factor in (0.75, 1.0, 1.25)]
    candidates = sorted({round(candidate, 3) for candidate in candidates if candidate > 0})
    target = config.basis.capacity_tpa
    blocked_value_ids = _blocked_value_ids(resolved_values, ("price", "demand", "labor", "utility")) if resolved_values else []
    alternatives: list[AlternativeOption] = []
    for candidate in candidates:
        scale_fit = max(0.0, 100.0 - abs(candidate - target) / max(target, 1.0) * 120.0)
        if candidate < target:
            market_fit = 72.0
            operability = 88.0
            utility_fit = 64.0
        elif candidate > target:
            market_fit = 78.0
            operability = 66.0
            utility_fit = 92.0
        else:
            market_fit = 90.0
            operability = 86.0
            utility_fit = 91.0
        total = 0.35 * scale_fit + 0.30 * market_fit + 0.20 * utility_fit + 0.15 * operability
        alternatives.append(
            AlternativeOption(
                candidate_id=f"{int(candidate)}_tpa",
                candidate_type="capacity_case",
                description=f"{candidate:,.0f} TPA plant basis",
                inputs={"capacity_tpa": f"{candidate:.0f}", "market_price_inr_per_kg": f"{market.estimated_price_per_kg:.2f}"},
                outputs={
                    "scale_fit": f"{scale_fit:.1f}",
                    "market_fit": f"{market_fit:.1f}",
                    "utility_fit": f"{utility_fit:.1f}",
                    "operability": f"{operability:.1f}",
                },
                score_breakdown={
                    "scale_fit": round(scale_fit, 2),
                    "market_fit": round(market_fit, 2),
                    "utility_fit": round(utility_fit, 2),
                    "operability": round(operability, 2),
                },
                total_score=round(total, 2),
                feasible=not blocked_value_ids,
                rejected_reasons=["High-sensitivity market or tariff values remain unresolved."] if blocked_value_ids else [],
                citations=market.citations,
                assumptions=market.assumptions,
            )
        )
    selected = max(alternatives, key=lambda item: item.total_score)
    approval_required = any(item.candidate_id != selected.candidate_id and abs(item.total_score - selected.total_score) <= 5.0 for item in alternatives)
    return DecisionRecord(
        decision_id="capacity_case",
        context="Capacity selection scored against market fit, scale economy, operability, and utility-integration leverage.",
        criteria=[
            DecisionCriterion(name="Scale fit", weight=0.35, justification="Selected scale should remain close to the stated benchmark throughput."),
            DecisionCriterion(name="Market fit", weight=0.30, justification="India demand and price basis must support the chosen scale."),
            DecisionCriterion(name="Utility integration", weight=0.20, justification="Large continuous plants gain more from heat and utility integration."),
            DecisionCriterion(name="Operability", weight=0.15, justification="Overbuilt or undersized plants distort staffing and reliability assumptions."),
        ],
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=f"{selected.description} selected because it best balances the benchmark throughput, market basis, and integration leverage.",
        hard_constraint_results=["Public-data-only market basis enforced.", "India-only economic basis enforced."],
        confidence=0.82 if not blocked_value_ids else 0.42,
        scenario_stability=ScenarioStability.BORDERLINE if approval_required else ScenarioStability.STABLE,
        approval_required=approval_required or bool(blocked_value_ids),
        blocked_value_ids=blocked_value_ids,
        citations=market.citations,
        assumptions=market.assumptions + ["Capacity case scored deterministically from benchmark throughput and market basis."],
    )


def build_thermo_method_decision(
    config: ProjectConfig,
    route: RouteOption,
    resolved_values: ResolvedValueArtifact,
    archetype: ProcessArchetype | None = None,
) -> MethodSelectionArtifact:
    blocked_value_ids = _blocked_value_ids(resolved_values, ("boiling", "melting", "density", "molecular weight"))
    technical_strength = _technical_strength(config)
    correlation_bonus = 8.0 if archetype and archetype.heat_management_profile in {"heat_integrated", "exothermic"} else 0.0
    alternatives = [
        AlternativeOption(
            candidate_id="direct_public_data",
            candidate_type="thermo_method",
            description="Use direct public property and reaction data where available.",
            outputs={"data_strength": f"{technical_strength:.1f}"},
            score_breakdown={"data_strength": technical_strength, "auditability": 96.0, "speed": 78.0},
            total_score=0.55 * technical_strength + 0.30 * 96.0 + 0.15 * 78.0,
            feasible=technical_strength >= 75.0 and not blocked_value_ids,
            rejected_reasons=["High-sensitivity property values remain unresolved."] if blocked_value_ids else [],
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="correlation_interpolation",
            candidate_type="thermo_method",
            description="Use public correlations and interpolation around cited anchors.",
            outputs={"fit": "Best when direct thermodynamic data is incomplete but physical-property anchors exist."},
            score_breakdown={"data_strength": min(technical_strength + correlation_bonus, 95.0), "auditability": 84.0, "speed": 82.0},
            total_score=0.55 * min(technical_strength + correlation_bonus, 95.0) + 0.30 * 84.0 + 0.15 * 82.0,
            feasible=not blocked_value_ids,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="estimation_method",
            candidate_type="thermo_method",
            description="Use accepted estimation methods with conservative bounds.",
            outputs={"fit": "Fallback when public data is sparse."},
            score_breakdown={"data_strength": 62.0, "auditability": 68.0, "speed": 72.0},
            total_score=65.9,
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="analogy_basis",
            candidate_type="thermo_method",
            description="Use close-compound analogy as a provisional design basis.",
            outputs={"fit": "Last acceptable step before blocking."},
            score_breakdown={"data_strength": 48.0, "auditability": 52.0, "speed": 70.0},
            total_score=53.5,
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
    ]
    feasible = [item for item in alternatives if item.feasible]
    selected = max(feasible, key=lambda item: item.total_score) if feasible else alternatives[-1]
    decision = DecisionRecord(
        decision_id="thermo_method",
        context=f"Thermodynamic-method selection for route {route.route_id}.",
        criteria=[
            DecisionCriterion(name="Data strength", weight=0.55, justification="Method should maximize public-data support for critical thermodynamic values."),
            DecisionCriterion(name="Auditability", weight=0.30, justification="Home-paper quality requires a defendable, traceable method basis."),
            DecisionCriterion(name="Execution speed", weight=0.15, justification="Faster methods are preferred only when they do not weaken engineering credibility."),
        ],
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=f"{selected.description} selected as the primary thermodynamic basis.",
        hard_constraint_results=["High-sensitivity property gaps must be resolved or explicitly surfaced."],
        confidence=0.88 if selected.candidate_id == "direct_public_data" else 0.76,
        scenario_stability=ScenarioStability.STABLE if selected.candidate_id in {"direct_public_data", "correlation_interpolation"} else ScenarioStability.BORDERLINE,
        approval_required=selected.candidate_id not in {"direct_public_data", "correlation_interpolation"} or bool(blocked_value_ids),
        blocked_value_ids=blocked_value_ids,
        citations=route.citations,
        assumptions=route.assumptions + ["Thermo method is chosen deterministically before chapter drafting."],
    )
    rows = [
        "| Method | Feasible | Score | Rejected Reasons |",
        "| --- | --- | --- | --- |",
    ]
    for item in alternatives:
        rows.append(f"| {item.candidate_id} | {'yes' if item.feasible else 'no'} | {item.total_score:.2f} | {'; '.join(item.rejected_reasons) or '-'} |")
    return MethodSelectionArtifact(
        method_family="thermo",
        decision=decision,
        markdown="\n".join(rows),
        citations=decision.citations,
        assumptions=decision.assumptions,
    )


def build_kinetics_method_decision(
    config: ProjectConfig,
    route: RouteOption,
    resolved_values: ResolvedValueArtifact,
    archetype: ProcessArchetype | None = None,
) -> MethodSelectionArtifact:
    blocked_value_ids = _blocked_value_ids(resolved_values, ("molecular weight", "density"))
    technical_strength = _technical_strength(config)
    continuous_bonus = 7.0 if archetype and "continuous" in archetype.operating_mode_candidates else 0.0
    alternatives = [
        AlternativeOption(
            candidate_id="cited_rate_law",
            candidate_type="kinetics_method",
            description="Use cited industrial or literature rate law directly.",
            score_breakdown={"data_strength": technical_strength, "fit_quality": 90.0, "auditability": 94.0},
            total_score=0.50 * technical_strength + 0.25 * 90.0 + 0.25 * 94.0,
            feasible=technical_strength >= 80.0 and not blocked_value_ids,
            rejected_reasons=["High-sensitivity basis values remain unresolved."] if blocked_value_ids else [],
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="arrhenius_fit",
            candidate_type="kinetics_method",
            description="Use Arrhenius-style fitting around cited rate data.",
            score_breakdown={"data_strength": min(technical_strength + continuous_bonus, 94.0), "fit_quality": 84.0, "auditability": 82.0},
            total_score=0.50 * min(technical_strength + continuous_bonus, 94.0) + 0.25 * 84.0 + 0.25 * 82.0,
            feasible=not blocked_value_ids,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="apparent_order_fit",
            candidate_type="kinetics_method",
            description="Use apparent-order fitting from conversion and residence-time basis.",
            score_breakdown={"data_strength": 70.0, "fit_quality": 76.0, "auditability": 74.0},
            total_score=72.5,
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
        AlternativeOption(
            candidate_id="conservative_analogy",
            candidate_type="kinetics_method",
            description="Use close-route analogy with conservative residence-time allowance.",
            score_breakdown={"data_strength": 54.0, "fit_quality": 60.0, "auditability": 58.0},
            total_score=56.5,
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        ),
    ]
    feasible = [item for item in alternatives if item.feasible]
    selected = max(feasible, key=lambda item: item.total_score) if feasible else alternatives[-1]
    decision = DecisionRecord(
        decision_id="kinetics_method",
        context=f"Kinetics-model selection for route {route.route_id}.",
        criteria=[
            DecisionCriterion(name="Data strength", weight=0.50, justification="Method should maximize the amount of public kinetic evidence used."),
            DecisionCriterion(name="Fit quality", weight=0.25, justification="Residence-time and conversion basis must remain design-useful."),
            DecisionCriterion(name="Auditability", weight=0.25, justification="Chosen kinetics basis must be explainable and reviewable."),
        ],
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=f"{selected.description} selected as the primary kinetic basis.",
        hard_constraint_results=["Kinetics basis must remain conservative if direct fit quality is weak."],
        confidence=0.86 if selected.candidate_id in {"cited_rate_law", "arrhenius_fit"} else 0.72,
        scenario_stability=ScenarioStability.STABLE if selected.candidate_id in {"cited_rate_law", "arrhenius_fit", "apparent_order_fit"} else ScenarioStability.BORDERLINE,
        approval_required=selected.candidate_id == "conservative_analogy" or bool(blocked_value_ids),
        blocked_value_ids=blocked_value_ids,
        citations=route.citations,
        assumptions=route.assumptions + ["Kinetics method is chosen deterministically before chapter drafting."],
    )
    rows = [
        "| Method | Feasible | Score | Rejected Reasons |",
        "| --- | --- | --- | --- |",
    ]
    for item in alternatives:
        rows.append(f"| {item.candidate_id} | {'yes' if item.feasible else 'no'} | {item.total_score:.2f} | {'; '.join(item.rejected_reasons) or '-'} |")
    return MethodSelectionArtifact(
        method_family="kinetics",
        decision=decision,
        markdown="\n".join(rows),
        citations=decision.citations,
        assumptions=decision.assumptions,
    )
