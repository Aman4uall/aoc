from __future__ import annotations

from statistics import mean

from aoc.models import (
    AlternativeOption,
    AlternativeSet,
    DecisionCriterion,
    ProcessArchetype,
    ProjectConfig,
    PropertyGapArtifact,
    RouteOption,
    RouteSurveyArtifact,
    ScenarioStability,
)
from aoc.route_families import RouteFamilyArtifact, profile_for_route


ORGANIC_HINTS = {"glycol", "acid", "alcohol", "ester", "ketone", "aldehyde", "amine", "phenol"}
INORGANIC_HINTS = {"sulfuric", "hydrochloric", "nitric", "sodium", "potassium", "ammonium", "carbonate", "bicarbonate"}
SOLIDS_HINTS = {"crystall", "filtration", "filter", "dry", "solid", "salt", "cake"}
ABSORPTION_HINTS = {"absorption", "scrubbing", "stripper", "converter"}
DISTILLATION_HINTS = {"distillation", "flash", "vacuum", "purification", "dehydration"}
EXTRACTION_HINTS = {"extraction", "solvent", "wash"}
SOLUTION_FORM_HINTS = {"solution", "aqueous", "alcohol", "solvent", "formulation", "active"}


def _product_name(config: ProjectConfig) -> str:
    return config.basis.target_product.strip().lower()


def _route_text(route: RouteOption) -> str:
    tokens = [
        route.name,
        route.reaction_equation,
        route.scale_up_notes,
        " ".join(route.byproducts),
        " ".join(route.separations),
    ]
    return " ".join(token.lower() for token in tokens)


def _representative_routes(route_survey: RouteSurveyArtifact) -> list[RouteOption]:
    if not route_survey.routes:
        return []
    ranked = sorted(route_survey.routes, key=lambda item: item.route_score, reverse=True)
    top_score = ranked[0].route_score
    shortlisted = [route for route in ranked if route.route_score >= top_score - 1.5]
    return shortlisted[:2] or ranked[:1]


def _dominant_route_family(route_survey: RouteSurveyArtifact, route_families: RouteFamilyArtifact | None) -> str:
    if route_families is None or not route_survey.routes:
        return ""
    top_route = max(route_survey.routes, key=lambda item: item.route_score)
    profile = profile_for_route(route_families, top_route.route_id)
    return profile.route_family_id if profile is not None else ""


def _compound_family(config: ProjectConfig, route_survey: RouteSurveyArtifact) -> str:
    if config.compound_family_hint:
        hint = config.compound_family_hint.strip().lower()
        if hint in {"organic", "inorganic", "mixed"}:
            return hint
    text = _product_name(config)
    if any(token in text for token in ORGANIC_HINTS):
        return "organic"
    if any(token in text for token in INORGANIC_HINTS):
        return "inorganic"
    route_text = " ".join(_route_text(route) for route in _representative_routes(route_survey))
    if any(token in route_text for token in ORGANIC_HINTS):
        return "organic"
    if any(token in route_text for token in INORGANIC_HINTS):
        return "inorganic"
    return "mixed"


def _dominant_product_phase(config: ProjectConfig, route_survey: RouteSurveyArtifact, property_gap: PropertyGapArtifact) -> str:
    if config.phase_system_hint:
        hint = config.phase_system_hint.strip().lower()
        if hint in {"gas", "liquid", "solid", "mixed"}:
            return hint
    product_form = (config.basis.product_form or "").strip().lower()
    if product_form and any(token in product_form for token in SOLUTION_FORM_HINTS):
        return "liquid"
    if config.basis.nominal_active_wt_pct is not None and config.basis.carrier_components:
        return "liquid"
    melting_point = next((item for item in property_gap.values if item.name.strip().lower() == "melting point"), None)
    boiling_point = next((item for item in property_gap.values if item.name.strip().lower() == "boiling point"), None)
    try:
        if melting_point and boiling_point and melting_point.units.lower() == "c" and boiling_point.units.lower() == "c":
            mp = float(melting_point.value)
            bp = float(boiling_point.value)
            if mp <= 25.0 < bp:
                return "liquid"
            if bp <= 25.0:
                return "gas"
            if mp > 25.0:
                return "solid"
    except ValueError:
        pass
    product_phases = []
    for route in _representative_routes(route_survey):
        for participant in route.participants:
            if participant.role == "product" and participant.phase:
                product_phases.append(participant.phase.lower())
    if not product_phases:
        name = _product_name(config)
        if "acid" in name and "sulfuric" not in name:
            return "liquid"
        if "bicarbonate" in name or "carbonate" in name:
            return "solid"
        return "liquid"
    if len(set(product_phases)) == 1:
        phase = product_phases[0]
        return phase if phase in {"gas", "liquid", "solid"} else "mixed"
    return "mixed"


def _dominant_feed_phase(route_survey: RouteSurveyArtifact) -> str:
    phases = []
    for route in _representative_routes(route_survey):
        for participant in route.participants:
            if participant.role == "reactant" and participant.phase:
                phases.append(participant.phase.lower())
    if not phases:
        return "liquid"
    unique = {phase if phase in {"gas", "liquid", "solid"} else "mixed" for phase in phases}
    return unique.pop() if len(unique) == 1 else "mixed"


def _dominant_separation(route_survey: RouteSurveyArtifact) -> str:
    text = " ".join(_route_text(route) for route in _representative_routes(route_survey))
    if any(token in text for token in {"quaternization", "quaternary ammonium", "benzalkonium", "benzyl chloride", "alcohol recovery", "light-ends stripping"}):
        return "mixed_purification"
    if any(token in text for token in SOLIDS_HINTS):
        return "crystallization_filtration_drying"
    if any(token in text for token in ABSORPTION_HINTS):
        return "absorption_stripping"
    if any(token in text for token in EXTRACTION_HINTS):
        return "liquid_liquid_extraction"
    if any(token in text for token in DISTILLATION_HINTS):
        return "distillation_flash"
    return "mixed_purification"


def _heat_profile(route_survey: RouteSurveyArtifact) -> str:
    representative = _representative_routes(route_survey)
    avg_temp = mean(route.operating_temperature_c for route in representative) if representative else 100.0
    if avg_temp >= 220.0:
        return "high_temperature_recovery_candidate"
    if avg_temp >= 120.0:
        return "moderate_temperature_integrated"
    return "mild_temperature_utility_led"


def _hazard_intensity(route_survey: RouteSurveyArtifact) -> str:
    severities = [hazard.severity for route in _representative_routes(route_survey) for hazard in route.hazards]
    if "high" in severities:
        return "high"
    if "moderate" in severities:
        return "moderate"
    return "low"


def classify_process_archetype(
    config: ProjectConfig,
    route_survey: RouteSurveyArtifact,
    property_gap: PropertyGapArtifact,
) -> ProcessArchetype:
    compound_family = _compound_family(config, route_survey)
    product_phase = _dominant_product_phase(config, route_survey, property_gap)
    feed_phase = _dominant_feed_phase(route_survey)
    separation = _dominant_separation(route_survey)
    heat_profile = _heat_profile(route_survey)
    hazard = _hazard_intensity(route_survey)
    operating_modes = ["continuous"] if config.basis.capacity_tpa >= 50000 else ["continuous", "batch"]
    if product_phase == "solid" and "batch" not in operating_modes:
        operating_modes.append("batch")
    return ProcessArchetype(
        archetype_id=f"{compound_family}_{product_phase}_{separation}",
        compound_family=compound_family,  # type: ignore[arg-type]
        dominant_product_phase=product_phase,  # type: ignore[arg-type]
        dominant_feed_phase=feed_phase,  # type: ignore[arg-type]
        operating_mode_candidates=operating_modes,
        dominant_separation_family=separation,
        heat_management_profile=heat_profile,
        hazard_intensity=hazard,  # type: ignore[arg-type]
        rationale=(
            f"Classified from public route patterns, product/participant phase cues, and sensitivity-checked property gaps. "
            f"High-sensitivity unresolved properties: {', '.join(property_gap.unresolved_high_sensitivity) or 'none'}."
        ),
        benchmark_profile=config.benchmark_profile,
        citations=route_survey.citations,
        assumptions=route_survey.assumptions + property_gap.assumptions,
    )


def build_alternative_sets(
    config: ProjectConfig,
    archetype: ProcessArchetype,
    route_survey: RouteSurveyArtifact,
    route_families: RouteFamilyArtifact | None = None,
) -> list[AlternativeSet]:
    capacity_candidates = config.capacity_case_candidates or [
        max(1000.0, config.basis.capacity_tpa * 0.5),
        config.basis.capacity_tpa,
        config.basis.capacity_tpa * 1.5,
    ]
    capacity_rows = []
    for capacity in capacity_candidates:
        scale_penalty = abs(capacity - config.basis.capacity_tpa) / max(config.basis.capacity_tpa, 1.0)
        score = max(0.0, 100.0 - 70.0 * scale_penalty)
        capacity_rows.append(
            AlternativeOption(
                candidate_id=f"{int(capacity)}_tpa",
                candidate_type="capacity_case",
                description=f"{capacity:,.0f} TPA design basis",
                outputs={"capacity_tpa": f"{capacity:.0f}"},
                total_score=score,
                score_breakdown={"scale_fit": score},
                feasible=capacity > 0,
            )
        )
    operating_rows = []
    for mode in archetype.operating_mode_candidates:
        throughput_score = 90.0 if mode == "continuous" and config.basis.capacity_tpa >= 20000 else 70.0
        flexibility_score = 90.0 if mode == "batch" and config.basis.capacity_tpa < 10000 else 55.0
        total_score = 0.65 * throughput_score + 0.35 * flexibility_score
        operating_rows.append(
            AlternativeOption(
                candidate_id=mode,
                candidate_type="operating_mode",
                description=f"{mode.title()} operation",
                outputs={"mode": mode},
                total_score=total_score,
                score_breakdown={"throughput_support": throughput_score, "flexibility_fit": flexibility_score},
                feasible=True,
            )
        )
    route_rows = [
        AlternativeOption(
            candidate_id=route.route_id,
            candidate_type="route",
            description=route.name,
            outputs={"yield": f"{route.yield_fraction:.3f}", "selectivity": f"{route.selectivity_fraction:.3f}"},
            total_score=route.route_score * 10.0,
            score_breakdown={"route_score": route.route_score * 10.0},
            feasible=True,
            citations=route.citations,
            assumptions=route.assumptions,
        )
        for route in route_survey.routes
    ]
    dominant_route_family = _dominant_route_family(route_survey, route_families)
    reactor_family_rows = []
    if archetype.dominant_product_phase == "solid":
        reactor_family_rows.append(AlternativeOption(candidate_id="stirred_slurry", candidate_type="reactor_family", description="Agitated slurry reactor", total_score=84.0, score_breakdown={"solids_handling": 84.0}))
    cstr_score = 72.0
    pfr_score = 88.0 if "continuous" in archetype.operating_mode_candidates else 60.0
    batch_score = 58.0 if config.basis.capacity_tpa >= 20000 else 81.0
    cstr_desc = "CSTR train"
    if dominant_route_family == "quaternization_liquid_train":
        cstr_score = 95.0
        pfr_score = 38.0
        batch_score = 52.0 if config.basis.capacity_tpa >= 20000 else 68.0
        cstr_desc = "Jacketed liquid reactor train"
    elif dominant_route_family == "liquid_hydration_train":
        cstr_score = 72.0
        pfr_score = 92.0 if "continuous" in archetype.operating_mode_candidates else 64.0
    elif dominant_route_family in {"extraction_recovery_train", "generic_mixed_train"}:
        cstr_score = 84.0
        pfr_score = 62.0
    reactor_family_rows.extend(
        [
            AlternativeOption(candidate_id="cstr_train", candidate_type="reactor_family", description=cstr_desc, total_score=cstr_score, score_breakdown={"controllability": cstr_score}),
            AlternativeOption(candidate_id="pfr_tubular", candidate_type="reactor_family", description="Tubular PFR", total_score=pfr_score, score_breakdown={"throughput": pfr_score}),
            AlternativeOption(candidate_id="batch_agitated", candidate_type="reactor_family", description="Batch agitated vessel", total_score=batch_score, score_breakdown={"flexibility": batch_score}),
        ]
    )
    separation_rows = [
        AlternativeOption(
            candidate_id=archetype.dominant_separation_family,
            candidate_type="separation_family",
            description=archetype.dominant_separation_family.replace("_", " "),
            total_score=86.0,
            score_breakdown={"archetype_fit": 86.0},
        ),
        AlternativeOption(
            candidate_id="mixed_purification",
            candidate_type="separation_family",
            description="Mixed purification train",
            total_score=68.0,
            score_breakdown={"archetype_fit": 68.0},
        ),
    ]
    return [
        AlternativeSet(
            set_id="capacity_case",
            context="Early capacity screening before detailed synthesis.",
            criteria=[
                DecisionCriterion(name="Scale fit", weight=1.0, justification="Keeps conceptual design tied to requested throughput."),
            ],
            alternatives=capacity_rows,
            selected_candidate_id=max(capacity_rows, key=lambda item: item.total_score).candidate_id if capacity_rows else None,
            markdown="Capacity alternatives ranked against the requested design basis.",
            scenario_stability=ScenarioStability.STABLE,
        ),
        AlternativeSet(
            set_id="operating_mode",
            context="Operating-mode screening from throughput, flexibility, and control needs.",
            criteria=[
                DecisionCriterion(name="Throughput support", weight=0.65, justification="Large plants favor continuous operation."),
                DecisionCriterion(name="Flexibility fit", weight=0.35, justification="Low-volume or solids-heavy service may justify batch operation."),
            ],
            alternatives=operating_rows,
            selected_candidate_id=max(operating_rows, key=lambda item: item.total_score).candidate_id if operating_rows else None,
            markdown="Operating-mode candidates ranked against throughput and flexibility needs.",
            scenario_stability=ScenarioStability.STABLE,
        ),
        AlternativeSet(
            set_id="route_screen",
            context="Public-source route alternatives before architecture lock.",
            criteria=[DecisionCriterion(name="Route maturity and fit", weight=1.0, justification="Uses route survey scoring as the first deterministic route screen.")],
            alternatives=route_rows,
            selected_candidate_id=max(route_rows, key=lambda item: item.total_score).candidate_id if route_rows else None,
            markdown="Route candidates carried from the route survey into the generic architecture layer.",
            scenario_stability=ScenarioStability.STABLE,
        ),
        AlternativeSet(
            set_id="reactor_family",
            context="Generic reactor-family screening from archetype, throughput, and dominant route family.",
            criteria=[DecisionCriterion(name="Family fit", weight=1.0, justification="Scores reactor families against throughput, controllability, and phase handling.")],
            alternatives=reactor_family_rows,
            selected_candidate_id=max(reactor_family_rows, key=lambda item: item.total_score).candidate_id if reactor_family_rows else None,
            markdown="Reactor-family candidates ranked for the inferred archetype and dominant route-family cues.",
            scenario_stability=ScenarioStability.BORDERLINE if archetype.dominant_product_phase == "solid" else ScenarioStability.STABLE,
        ),
        AlternativeSet(
            set_id="separation_family",
            context="Generic separation-family screening from route and phase structure.",
            criteria=[DecisionCriterion(name="Separation fit", weight=1.0, justification="Uses archetype signals from route descriptions and phase hints.")],
            alternatives=separation_rows,
            selected_candidate_id=max(separation_rows, key=lambda item: item.total_score).candidate_id if separation_rows else None,
            markdown="Separation-family candidates ranked for the inferred archetype.",
            scenario_stability=ScenarioStability.STABLE,
        ),
    ]
