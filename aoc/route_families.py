from __future__ import annotations

from aoc.models import ChemistryFamilyAdapter, RouteFamilyArtifact, RouteFamilyProfile, RouteOption, RouteSurveyArtifact


def _route_text(route: RouteOption) -> str:
    tokens = [
        route.route_id,
        route.name,
        route.reaction_equation,
        route.scale_up_notes,
        " ".join(route.separations),
        " ".join(route.byproducts),
        " ".join(route.catalysts),
        " ".join(item.name for item in route.participants),
    ]
    return " ".join(token.lower() for token in tokens if token)


def _phases(route: RouteOption) -> set[str]:
    return {(participant.phase or "").lower() for participant in route.participants if participant.phase}


def _profile_markdown(profile: RouteFamilyProfile) -> str:
    def _join(items: list[str]) -> str:
        return ", ".join(items) if items else "none"

    return "\n".join(
        [
            f"`{profile.route_id}` is classified as `{profile.route_family_id}` ({profile.family_label}).",
            "",
            f"- Reactor basis: {profile.primary_reactor_class}",
            f"- Separation train: {profile.primary_separation_train}",
            f"- Heat recovery style: {profile.heat_recovery_style}",
            f"- Data anchors: {_join(profile.data_anchor_requirements)}",
            f"- Critic flags: {_join(profile.critic_flags)}",
            f"- India blocker: {profile.india_deployment_blocker or 'none'}",
        ]
    )


def classify_route_family(route: RouteOption, adapter: ChemistryFamilyAdapter | None = None) -> RouteFamilyProfile:
    text = _route_text(route)
    phases = _phases(route)
    descriptors = [item.lower().replace(" ", "_") for item in route.separations]
    is_quaternization_train = any(
        token in text
        for token in {
            "quaternization",
            "quaternary ammonium",
            "benzalkonium",
            "benzyl chloride",
            "alkyldimethylamine",
        }
    )

    family_id = "generic_mixed_train"
    family_label = "Generic Mixed Train"
    dominant_phase_pattern = "mixed"
    primary_reactor_class = "Jacketed stirred reactor"
    primary_separation_train = "Primary separation -> product finishing"
    heat_recovery_style = "staged_utility_header_network"
    maturity_score = 72.0
    india_fit_score = 68.0
    utility_factor = 1.0
    capex_factor = 1.0
    operability_score = 76.0
    data_anchor_requirements = ["molecular_weight", "liquid_density", "liquid_heat_capacity"]
    critic_flags: list[str] = []
    india_blocker = ""

    if is_quaternization_train:
        family_id = "quaternization_liquid_train"
        family_label = "Quaternization Liquid Train"
        dominant_phase_pattern = "liquid_reactive"
        primary_reactor_class = "Jacketed liquid-phase quaternization reactor"
        primary_separation_train = "Reaction hold -> solvent/alcohol recovery -> dilution/polishing"
        heat_recovery_style = "staged_utility_header_network"
        maturity_score = 83.0
        india_fit_score = 74.0
        utility_factor = 0.98
        capex_factor = 1.02
        operability_score = 72.0
        data_anchor_requirements = [
            "liquid_density",
            "liquid_viscosity",
            "reaction_exotherm_basis",
            "quaternary_salt_solution_handling_basis",
        ]
        critic_flags = [
            "reaction_exotherm_control",
            "amine_feed_quality_window",
            "colored_impurity_control",
        ]
    elif "chlor" in text:
        family_id = "chlorinated_hydrolysis_train"
        family_label = "Chlorinated Hydrolysis Train"
        dominant_phase_pattern = "liquid_salt_slurry"
        primary_reactor_class = "Agitated hydrolysis CSTR train"
        primary_separation_train = "Salt removal -> brine handling -> water removal -> purification"
        heat_recovery_style = "utility_led_with_brine_management"
        maturity_score = 30.0
        india_fit_score = 22.0
        utility_factor = 1.18
        capex_factor = 1.22
        operability_score = 48.0
        data_anchor_requirements = ["liquid_density", "liquid_viscosity", "chloride_corrosion_basis"]
        critic_flags = ["chloride_waste_burden", "brine_handling_penalty", "corrosion_material_risk"]
        india_blocker = "Route generates chloride-heavy waste and is not preferred for India deployment under the current policy basis."
    elif "spent acid" in text or "regeneration" in text or "thermal decomposition" in text:
        family_id = "regeneration_loop_train"
        family_label = "Regeneration Loop Train"
        dominant_phase_pattern = "liquid_to_gas_cleanup"
        primary_reactor_class = "Thermal regeneration furnace loop"
        primary_separation_train = "Thermal decomposition -> gas cleanup -> absorption"
        heat_recovery_style = "waste_heat_boiler"
        maturity_score = 58.0
        india_fit_score = 55.0
        utility_factor = 1.10
        capex_factor = 1.12
        operability_score = 62.0
        data_anchor_requirements = ["gas_cleanup_basis", "henry_constants", "corrosion_material_basis"]
        critic_flags = ["regeneration_feed_specific", "offgas_cleanup_penalty"]
    elif any(token in text for token in {"interpass absorption", "final absorption", "converter", "gas drying", "absorption"}) and "gas" in phases:
        family_id = "gas_absorption_converter_train"
        family_label = "Gas Absorption and Converter Train"
        dominant_phase_pattern = "gas_liquid_absorption"
        primary_reactor_class = "Fixed-bed catalytic converter"
        primary_separation_train = "Gas drying -> catalytic conversion -> interpass/final absorption"
        heat_recovery_style = "waste_heat_boiler"
        maturity_score = 94.0
        india_fit_score = 82.0
        utility_factor = 0.86
        capex_factor = 1.05
        operability_score = 82.0
        data_anchor_requirements = ["henry_constants", "gas_liquid_mass_transfer_basis", "acid_service_moc"]
        critic_flags = ["henry_law_basis", "mist_carryover", "converter_heat_window"]
    elif any(token in text for token in {"solvay", "ammonia recovery", "ammonium chloride"}):
        family_id = "integrated_solvay_liquor_train"
        family_label = "Integrated Solvay Liquor Train"
        dominant_phase_pattern = "gas_liquid_solid"
        primary_reactor_class = "Carbonation liquor loop"
        primary_separation_train = "Crystallization -> filtration -> ammonia recovery -> drying"
        heat_recovery_style = "low_grade_steam_header"
        maturity_score = 77.0
        india_fit_score = 70.0
        utility_factor = 1.08
        capex_factor = 1.10
        operability_score = 66.0
        data_anchor_requirements = ["solubility_curve", "ammonia_recovery_basis", "mother_liquor_inventory"]
        critic_flags = ["ammonia_recycle_closure", "mother_liquor_purge", "solids_quality_drift"]
    elif any(token in text for token in {"carbonation", "carboxylation", "bicarbonation"}) and "solid" in phases:
        family_id = "solids_carboxylation_train"
        family_label = "Solids Carboxylation Train"
        dominant_phase_pattern = "gas_liquid_solid"
        primary_reactor_class = "Slurry carbonation reactor"
        primary_separation_train = "Crystallization -> filtration -> drying"
        heat_recovery_style = "dryer_heat_recovery"
        maturity_score = 88.0
        india_fit_score = 81.0
        utility_factor = 0.94
        capex_factor = 0.96
        operability_score = 78.0
        data_anchor_requirements = ["solubility_curve", "dryer_endpoint_basis", "filter_resistance_basis"]
        critic_flags = ["solubility_limit_basis", "cake_resistance", "dryer_endpoint"]
    elif any(token in text for token in {"carbonylation", " co ", "co ->"}) or ("carbon monoxide" in text and "acid" in text):
        family_id = "carbonylation_liquid_train"
        family_label = "Carbonylation Liquid Train"
        dominant_phase_pattern = "gas_liquid_reactive"
        primary_reactor_class = "High-pressure carbonylation loop"
        primary_separation_train = "Flash -> light-ends removal -> distillation"
        heat_recovery_style = "condenser_reboiler_cluster"
        maturity_score = 93.0
        india_fit_score = 85.0
        utility_factor = 0.92
        capex_factor = 1.08
        operability_score = 80.0
        data_anchor_requirements = ["binary_interaction_parameters", "light_ends_vle_basis", "corrosion_iodide_service"]
        critic_flags = ["light_ends_recovery", "catalyst_inventory_burden", "pressure_loop_complexity"]
    elif "oxidation" in text:
        family_id = "oxidation_recovery_train"
        family_label = "Oxidation and Recovery Train"
        dominant_phase_pattern = "gas_liquid_reactive"
        primary_reactor_class = "Oxidation reactor train"
        primary_separation_train = "Gas vent/quench -> recovery -> distillation"
        heat_recovery_style = "shared_htm_island_network"
        maturity_score = 73.0
        india_fit_score = 71.0
        utility_factor = 1.03
        capex_factor = 1.07
        operability_score = 70.0
        data_anchor_requirements = ["oxygen_solubility_or_gas_transfer_basis", "oxidation_selectivity_basis", "offgas_handling"]
        critic_flags = ["offgas_penalty", "byproduct_spread", "oxidation_selectivity"]
    elif "hydration" in text or ("water" in text and "oxide" in text):
        family_id = "liquid_hydration_train"
        family_label = "Liquid Hydration Train"
        dominant_phase_pattern = "liquid_reactive"
        primary_reactor_class = "Tubular plug-flow hydrator"
        primary_separation_train = "EO flash -> water removal -> vacuum glycol distillation"
        heat_recovery_style = "condenser_reboiler_cluster"
        maturity_score = 92.0
        india_fit_score = 90.0
        utility_factor = 1.12
        capex_factor = 1.00
        operability_score = 84.0
        data_anchor_requirements = ["binary_interaction_parameters", "liquid_density", "liquid_viscosity"]
        critic_flags = ["dehydration_duty", "glycol_split_vle_basis", "water_recycle_closure"]
    elif any(token in text for token in {"extraction", "solvent", "wash"}):
        family_id = "extraction_recovery_train"
        family_label = "Extraction and Recovery Train"
        dominant_phase_pattern = "liquid_liquid"
        primary_reactor_class = "Jacketed CSTR train"
        primary_separation_train = "Extraction -> solvent recovery -> polishing column"
        heat_recovery_style = "shared_htm_island_network"
        maturity_score = 75.0
        india_fit_score = 69.0
        utility_factor = 1.04
        capex_factor = 1.09
        operability_score = 68.0
        data_anchor_requirements = ["distribution_basis", "binary_interaction_parameters", "solvent_inventory_basis"]
        critic_flags = ["extractant_recycle_closure", "solvent_loss_burden", "lle_basis"]

    if adapter:
        if any(item in family_id for item in {"solids", "absorption", "carbonylation", "hydration", "extraction"}):
            critic_flags = list(dict.fromkeys([*critic_flags, *adapter.critic_focus[:2]]))
        data_anchor_requirements = list(dict.fromkeys([*data_anchor_requirements, *adapter.sparse_data_blockers[:2]]))

    profile = RouteFamilyProfile(
        route_id=route.route_id,
        route_family_id=family_id,
        family_label=family_label,
        dominant_phase_pattern=dominant_phase_pattern,
        primary_reactor_class=primary_reactor_class,
        primary_separation_train=primary_separation_train,
        heat_recovery_style=heat_recovery_style,
        maturity_score=maturity_score,
        india_fit_score=india_fit_score,
        utility_intensity_factor=utility_factor,
        capex_intensity_factor=capex_factor,
        operability_score=operability_score,
        data_anchor_requirements=data_anchor_requirements,
        critic_flags=critic_flags,
        route_descriptors=descriptors,
        india_deployment_blocker=india_blocker,
        citations=route.citations,
        assumptions=route.assumptions,
    )
    profile.markdown = _profile_markdown(profile)
    return profile


def build_route_family_artifact(
    route_survey: RouteSurveyArtifact,
    adapter: ChemistryFamilyAdapter | None = None,
) -> RouteFamilyArtifact:
    profiles = [classify_route_family(route, adapter) for route in route_survey.routes]
    lines = [
        "| Route | Family | Reactor Basis | Separation Train | Heat Style | India Blocker |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for profile in profiles:
        lines.append(
            f"| {profile.route_id} | {profile.family_label} | {profile.primary_reactor_class} | "
            f"{profile.primary_separation_train} | {profile.heat_recovery_style} | "
            f"{profile.india_deployment_blocker or 'none'} |"
        )
    assumptions = list(route_survey.assumptions)
    if adapter:
        assumptions += adapter.assumptions
    assumptions.append("Route-family profiles are deterministic classifications built from route descriptors, participant phases, and chemistry-family adapter cues.")
    citations = list(route_survey.citations) + (adapter.citations if adapter else [])
    return RouteFamilyArtifact(
        profiles=profiles,
        markdown="\n".join(lines),
        citations=sorted(set(citations)),
        assumptions=assumptions,
    )


def profile_for_route(route_families: RouteFamilyArtifact | None, route_id: str) -> RouteFamilyProfile | None:
    if route_families is None:
        return None
    return next((profile for profile in route_families.profiles if profile.route_id == route_id), None)
