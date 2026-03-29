from __future__ import annotations

from aoc.models import ChemistryFamilyAdapter, ProcessArchetype, ProjectConfig, PropertyGapArtifact, RouteOption, RouteSurveyArtifact


def _route_text(route: RouteOption) -> str:
    return " ".join(
        token.lower()
        for token in [
            route.name,
            route.reaction_equation,
            route.scale_up_notes,
            " ".join(route.byproducts),
            " ".join(route.separations),
            " ".join(route.catalysts),
        ]
        if token
    )


def _representative_routes(route_survey: RouteSurveyArtifact) -> list[RouteOption]:
    if not route_survey.routes:
        return []
    ranked = sorted(route_survey.routes, key=lambda item: item.route_score, reverse=True)
    top_score = ranked[0].route_score
    return [route for route in ranked if route.route_score >= top_score - 1.5][:2] or ranked[:1]


def _default_adapter_markdown(adapter: ChemistryFamilyAdapter) -> str:
    def _join(items: list[str]) -> str:
        return ", ".join(items) if items else "none"

    return "\n".join(
        [
            f"Adapter `{adapter.adapter_id}` supports {adapter.family_label.lower()} under a {adapter.compound_family} chemistry basis.",
            "",
            f"- Route hints: {_join(adapter.route_generation_hints)}",
            f"- Property priority: {_join(adapter.property_priority_order)}",
            f"- Preferred reactor candidates: {_join(adapter.preferred_reactor_candidates)}",
            f"- Preferred separation candidates: {_join(adapter.preferred_separation_candidates)}",
            f"- Common unit operations: {_join(adapter.common_unit_operations)}",
            f"- Corrosion cues: {_join(adapter.corrosion_cues)}",
            f"- Heat-integration patterns: {_join(adapter.heat_integration_patterns)}",
            f"- Critic focus: {_join(adapter.critic_focus)}",
            f"- Sparse-data blockers: {_join(adapter.sparse_data_blockers)}",
        ]
    )


def _build_liquid_organic_adapter(archetype: ProcessArchetype, benchmark_profile: str | None) -> ChemistryFamilyAdapter:
    adapter = ChemistryFamilyAdapter(
        adapter_id="continuous_liquid_organic_train",
        family_label="Continuous Liquid Organic Train",
        compound_family="organic",
        dominant_phase_system="liquid",
        route_generation_hints=["hydration", "carbonylation", "hydrogenation", "dehydration cleanup"],
        property_priority_order=["molecular_weight", "normal_boiling_point", "liquid_density", "liquid_viscosity", "liquid_heat_capacity", "heat_of_vaporization", "antoine_constants", "binary_interaction_parameters"],
        preferred_reactor_candidates=["tubular_plug_flow_hydrator", "jacketed_cstr_train"],
        preferred_separation_candidates=["distillation_train", "extraction_recovery_train"],
        preferred_storage_candidates=["vertical_tank_farm"],
        moc_bias_candidates=["ss316l", "carbon_steel"],
        common_unit_operations=["reactor", "flash", "distillation", "heat_exchanger", "storage"],
        corrosion_cues=["organic_acid_presence", "water_content", "chloride_trace_monitoring"],
        heat_integration_patterns=["reboiler_condenser_cluster", "shared_htm_island_network", "moderate_temperature_recovery"],
        critic_focus=["relative_volatility_claims", "water_recycle_closure", "reboiler_duty_burden"],
        sparse_data_blockers=["missing_vle_basis", "missing_density_viscosity_for_column_hydraulics"],
        benchmark_profiles=[item for item in [benchmark_profile, "ethylene_glycol", "acetic_acid"] if item],
        rationale="Adapter selected for liquid-phase organic trains where throughput, VLE basis, and thermal integration dominate the design envelope.",
    )
    adapter.markdown = _default_adapter_markdown(adapter)
    return adapter


def _build_inorganic_absorption_adapter(archetype: ProcessArchetype, benchmark_profile: str | None) -> ChemistryFamilyAdapter:
    adapter = ChemistryFamilyAdapter(
        adapter_id="inorganic_absorption_conversion_train",
        family_label="Inorganic Absorption and Conversion Train",
        compound_family="inorganic",
        dominant_phase_system="mixed",
        route_generation_hints=["gas_phase_conversion", "absorption", "drying", "converter loop"],
        property_priority_order=["molecular_weight", "henry_constants", "liquid_density", "liquid_viscosity", "liquid_heat_capacity", "thermal_conductivity"],
        preferred_reactor_candidates=["fixed_bed_converter", "jacketed_cstr_train"],
        preferred_separation_candidates=["absorption_train"],
        preferred_storage_candidates=["vertical_tank_farm"],
        moc_bias_candidates=["alloy_steel_converter_service", "rubber_lined_cs"],
        common_unit_operations=["converter", "absorber", "stripper", "cooler", "acid_storage"],
        corrosion_cues=["acid_service", "dew_point_corrosion", "mist_carryover"],
        heat_integration_patterns=["waste_heat_boiler", "acid_cooling_island", "shared_htm_island_network"],
        critic_focus=["henry_law_basis", "mass_transfer_window", "corrosion_material_match"],
        sparse_data_blockers=["missing_henry_constant", "missing_absorber_mass_transfer_basis"],
        benchmark_profiles=[item for item in [benchmark_profile, "sulfuric_acid"] if item],
        rationale="Adapter selected for inorganic gas-liquid systems where absorber service, corrosive materials, and waste-heat recovery dominate the feasibility case.",
    )
    adapter.markdown = _default_adapter_markdown(adapter)
    return adapter


def _build_solids_adapter(archetype: ProcessArchetype, benchmark_profile: str | None) -> ChemistryFamilyAdapter:
    adapter = ChemistryFamilyAdapter(
        adapter_id="solids_crystallization_train",
        family_label="Solids Crystallization and Drying Train",
        compound_family=archetype.compound_family,
        dominant_phase_system="solid",
        route_generation_hints=["precipitation", "carbonation", "crystallization", "solids_cleanup"],
        property_priority_order=["molecular_weight", "solubility_curve", "slurry_density", "liquid_viscosity", "liquid_heat_capacity", "equilibrium_moisture"],
        preferred_reactor_candidates=["slurry_loop_reactor", "jacketed_cstr_train"],
        preferred_separation_candidates=["crystallization_filtration_drying"],
        preferred_storage_candidates=["silo_hopper"],
        moc_bias_candidates=["carbon_steel", "ss316l"],
        common_unit_operations=["reactor", "crystallizer", "classifier", "filter", "dryer", "silo"],
        corrosion_cues=["alkali_service", "solids_abrasion", "mother_liquor_fouling"],
        heat_integration_patterns=["dryer_heat_recovery", "mother_liquor_recycle", "low_grade_steam_header"],
        critic_focus=["solubility_limit_basis", "cake_resistance", "dryer_endpoint"],
        sparse_data_blockers=["missing_solubility_curve", "missing_dryer_moisture_basis"],
        benchmark_profiles=[item for item in [benchmark_profile, "sodium_bicarbonate"] if item],
        rationale="Adapter selected for solids routes where SLE basis, slurry handling, filtration, and drying govern the downstream feasibility picture.",
    )
    adapter.markdown = _default_adapter_markdown(adapter)
    return adapter


def _build_mixed_separation_adapter(archetype: ProcessArchetype, benchmark_profile: str | None) -> ChemistryFamilyAdapter:
    adapter = ChemistryFamilyAdapter(
        adapter_id="separation_intensive_mixed_train",
        family_label="Separation-Intensive Mixed Train",
        compound_family="mixed",
        dominant_phase_system="mixed",
        route_generation_hints=["solvent_extraction", "azeotrope_breaking", "mixed_purification", "polishing"],
        property_priority_order=["molecular_weight", "liquid_density", "liquid_viscosity", "liquid_heat_capacity", "antoine_constants", "binary_interaction_parameters", "distribution_coefficient_basis"],
        preferred_reactor_candidates=["jacketed_cstr_train", "batch_agitated"],
        preferred_separation_candidates=["extraction_recovery_train", "distillation_train"],
        preferred_storage_candidates=["vertical_tank_farm", "pressure_bullets"],
        moc_bias_candidates=["ss316l", "rubber_lined_cs"],
        common_unit_operations=["reactor", "extractor", "distillation", "flash", "recovery_column"],
        corrosion_cues=["mixed_solvent_service", "chloride_trace_monitoring", "extractant_losses"],
        heat_integration_patterns=["shared_htm_island_network", "condenser_reboiler_cluster", "staged_utility_header_network"],
        critic_focus=["lle_vle_basis", "solvent_recovery_closure", "extractant_inventory_burden"],
        sparse_data_blockers=["missing_binary_interaction_parameters", "missing_distribution_basis"],
        benchmark_profiles=[item for item in [benchmark_profile] if item],
        rationale="Adapter selected for mixed or separation-intensive systems where route choice is dominated by purification difficulty rather than one canonical reactor train.",
    )
    adapter.markdown = _default_adapter_markdown(adapter)
    return adapter


def build_chemistry_family_adapter(
    config: ProjectConfig,
    route_survey: RouteSurveyArtifact,
    property_gap: PropertyGapArtifact,
    archetype: ProcessArchetype,
) -> ChemistryFamilyAdapter:
    benchmark_profile = (config.benchmark_profile or "").strip().lower() or None
    route_text = " ".join(_route_text(route) for route in _representative_routes(route_survey))
    unresolved_text = " ".join(item.lower() for item in property_gap.unresolved_high_sensitivity)
    if archetype.dominant_product_phase == "solid" or archetype.dominant_separation_family in {"crystallization_filtration_drying", "solids", "crystallization"}:
        adapter = _build_solids_adapter(archetype, benchmark_profile)
    elif (
        archetype.compound_family == "inorganic"
        or "absorption" in archetype.dominant_separation_family
        or any(token in route_text for token in {"absorption", "scrubbing", "converter", "gas phase"})
    ):
        adapter = _build_inorganic_absorption_adapter(archetype, benchmark_profile)
    elif any(token in route_text for token in {"extraction", "solvent", "azeotrope"}) or "binary interaction" in unresolved_text:
        adapter = _build_mixed_separation_adapter(archetype, benchmark_profile)
    elif archetype.compound_family == "organic" and archetype.dominant_product_phase == "liquid":
        adapter = _build_liquid_organic_adapter(archetype, benchmark_profile)
    else:
        adapter = _build_mixed_separation_adapter(archetype, benchmark_profile)
    if benchmark_profile and benchmark_profile not in adapter.benchmark_profiles:
        adapter.benchmark_profiles.append(benchmark_profile)
    adapter.assumptions = archetype.assumptions + property_gap.assumptions + [
        f"Chemistry-family adapter '{adapter.adapter_id}' selected from archetype '{archetype.archetype_id}' and top-ranked route descriptors.",
    ]
    adapter.citations = route_survey.citations + property_gap.citations + archetype.citations
    return adapter
